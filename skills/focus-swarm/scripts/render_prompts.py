#!/usr/bin/env python3
"""
Render one self-contained prompt file per persona.

    python render_prompts.py <outdir> [--wave-size 8] [--retry id1,id2]
                             [--tools-note-file note.md] [--only id1,id2]

Reads   <outdir>/run.config.json, <outdir>/personas.json, references/panels.json,
        references/agent-brief.md (the template)
Writes  <outdir>/prompts/<id>.md        one prompt per persona
        <outdir>/prompts/<id>.retry.md  with --retry, a second-attempt prompt
        <outdir>/roster.json            ids, names, prompt and report paths (relative to <outdir>), waves

Each prompt embeds only that persona's own card, so an agent never sees the
rest of the cast. The orchestrator starts one subagent per prompt file.
"""

import argparse
import os
import re
import sys

import _common as C

SECTION = re.compile(r"\{\{([#^])(\w+)\}\}(.*?)\{\{/\2\}\}", re.S)
VAR = re.compile(r"\{\{(\w+)\}\}")


def load_template(path=None):
    with open(path or C.BRIEF_TEMPLATE_PATH, encoding="utf-8") as fh:
        text = fh.read()
    m = re.search(r"<!-- TEMPLATE START -->\n(.*?)<!-- TEMPLATE END -->", text, re.S)
    if not m:
        raise SystemExit("agent-brief.md has no TEMPLATE START / TEMPLATE END markers")
    return m.group(1)


def render(template, ctx):
    """Tiny logic-less renderer: {{var}}, {{#flag}}...{{/flag}}, {{^flag}}...{{/flag}}."""
    def section(m):
        kind, name, body = m.group(1), m.group(2), m.group(3)
        on = bool(ctx.get(name))
        return body if (on if kind == "#" else not on) else ""

    prev = None
    out = template
    while prev != out:  # repeat so that sections inside sections resolve
        prev = out
        out = SECTION.sub(section, out)
    out = VAR.sub(lambda m: str(ctx.get(m.group(1), "")), out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip() + "\n"


def persona_card(p):
    """Render a persona as plain prose plus a short attribute list."""
    head = ", ".join(str(x) for x in [p.get("name"), p.get("age"), p.get("role")] if x)
    if p.get("org"):
        head += " at " + str(p["org"])
    if p.get("location"):
        head += ", " + str(p["location"])
    lines = ["**" + head + "**", ""]
    for key in ("background", "history"):
        if p.get(key):
            lines.append(str(p[key]))
            lines.append("")
    attrs = [
        ("Disposition toward this kind of product", p.get("disposition")),
        ("Your lens (the angle nobody else covers)", p.get("lens")),
        ("Seat on the panel", p.get("seat")),
        ("Language you use", p.get("language")),
        ("Device", p.get("device")),
        ("Tech literacy", p.get("tech_literacy")),
        ("Access needs", ", ".join(p.get("access_needs") or [])),
        ("Tool you use today", p.get("current_tool")),
        ("Field", p.get("field")),
        ("Stage focus", p.get("stage_focus")),
        ("Typical ticket", p.get("ticket_range")),
        ("What public sources establish", p.get("research_notes")),
        ("Sources", ", ".join(p.get("sources") or [])),
    ]
    for label, val in attrs:
        if val:
            lines.append("- %s: %s" % (label, val))
    return "\n".join(lines).strip()


def extra_fields_text(block):
    rows = []
    for f in block.get("fields") or []:
        kind = {"string": "text"}.get(f.get("type", "string"), f.get("type"))
        rows.append('- key "%s", label "%s", type %s' % (f.get("key"), f.get("label"), kind))
    return "\n".join(rows)


def context_for(p, run, lib, outdir, brief_path, tools_note, retry=False):
    panel = lib.get(p.get("group"), {})
    block = panel.get("extra_block") or {}
    key = block.get("key")
    target_type = run.get("target_type", "live")
    real = bool(p.get("real_person")) and p.get("group") in (run.get("real_people") or [])
    sees_brief = bool(panel.get("sees_brief")) and os.path.exists(brief_path)
    return {
        "persona_card": persona_card(p),
        "id": p.get("id"),
        "group": p.get("group"),
        "target": run.get("target", ""),
        "target_type": target_type,
        "live": target_type == "live",
        "repo": target_type == "repo",
        "document": target_type == "document",
        "brief": os.path.abspath(brief_path) if sees_brief else "",
        "report_path": os.path.abspath(os.path.join(outdir, "agents", "%s.json" % p.get("id"))),
        "schema_path": C.SCHEMA_PATH,
        "deal": key == "deal",
        "science": key == "science",
        "extra": bool(block.get("fields")),
        "extra_label": block.get("label", ""),
        "extra_fields": extra_fields_text(block),
        "real": real,
        "notes": (run.get("notes") or "").strip(),
        "tools_note": (tools_note or "").strip(),
        "retry": retry,
    }


def main(argv=None):
    C.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[1].strip())
    ap.add_argument("outdir")
    ap.add_argument("--wave-size", type=int, default=8,
                    help="agents to start per wave (default 8)")
    ap.add_argument("--retry", default="", help="comma-separated ids that need a second attempt")
    ap.add_argument("--only", default="", help="render only these comma-separated ids")
    ap.add_argument("--tools-note-file", default="",
                    help="markdown appended to every prompt under 'Tools available in this run'")
    ns = ap.parse_args(argv)

    outdir = os.path.abspath(ns.outdir)
    run = C.load_run(outdir)
    personas = C.load_personas(outdir)
    if not run.get("target"):
        sys.exit("run.config.json has no target: focus-swarm evaluates a real product, not a description")
    if not personas:
        sys.exit("personas.json has no personas: cast the swarm first")

    lib = C.panels_by_id()
    unknown = sorted({p.get("group") for p in personas if p.get("group") not in lib})
    if unknown:
        print("warning: panels not in panels.json, rendered without a panel block: %s" % ", ".join(unknown))

    opted = set(run.get("real_people") or [])
    stray = [p.get("id") for p in personas if p.get("real_person") and p.get("group") not in opted]
    if stray:
        sys.exit("real_person is true for %s, but their panels were not opted in to real-people research "
                 "(run.config.json real_people). Recast them as fictional personas." % ", ".join(map(str, stray)))

    seen = set()
    for p in personas:
        pid = p.get("id")
        if not pid or pid in seen:
            sys.exit("every persona needs a unique id (problem: %r)" % pid)
        seen.add(pid)

    tools_note = ""
    if ns.tools_note_file:
        with open(ns.tools_note_file, encoding="utf-8") as fh:
            tools_note = fh.read()

    template = load_template()
    brief_path = os.path.join(outdir, "brief.md")
    pdir = os.path.join(outdir, "prompts")
    os.makedirs(pdir, exist_ok=True)
    os.makedirs(os.path.join(outdir, "agents"), exist_ok=True)

    retry_ids = [x.strip() for x in ns.retry.split(",") if x.strip()]
    only_ids = set(x.strip() for x in ns.only.split(",") if x.strip())
    by_id = {p["id"]: p for p in personas}

    if retry_ids:
        missing = [i for i in retry_ids if i not in by_id]
        if missing:
            sys.exit("unknown ids for --retry: %s" % ", ".join(missing))
        for pid in retry_ids:
            ctx = context_for(by_id[pid], run, lib, outdir, brief_path, tools_note, retry=True)
            path = os.path.join(pdir, "%s.retry.md" % pid)
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(render(template, ctx))
            print("retry prompt  %s" % path)
        return 0

    roster = []
    wave = max(1, ns.wave_size)
    for i, p in enumerate(x for x in personas if not only_ids or x["id"] in only_ids):
        ctx = context_for(p, run, lib, outdir, brief_path, tools_note)
        path = os.path.join(pdir, "%s.md" % p["id"])
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(render(template, ctx))
        roster.append({"id": p["id"], "group": p.get("group"), "name": p.get("name"),
                       "prompt": os.path.relpath(path, outdir).replace(os.sep, "/"),
                       "report": "agents/%s.json" % p["id"], "wave": i // wave + 1})

    C.write_json(os.path.join(outdir, "roster.json"), roster)
    waves = max([r["wave"] for r in roster] or [0])
    print("rendered %d prompts in %d wave(s) of up to %d -> %s" % (len(roster), waves, wave, pdir))
    for r in roster:
        print("  wave %d  %-14s %s" % (r["wave"], r["id"], r["name"] or ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
