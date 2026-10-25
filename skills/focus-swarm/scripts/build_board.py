#!/usr/bin/env python3
"""
Build the HTML board for a focus-swarm run.

    python build_board.py <outdir> [--title "Product name"]

Reads   <outdir>/agents/*.json, personas.json, run.config.json, report.md
Writes  <outdir>/index.html  one self-contained file: no external requests, works
                             offline and from file://, light and dark themes
        <outdir>/README.md   only if missing, with the disclaimer banner

Deep links: index.html#overview, #agents, #synthesis, #deals, #agent-<id>.
"""

import argparse
import html
import json
import os
import re
import sys
from datetime import date

import _common as C
import _theme as T

FALLBACK_COLOURS = ["#6c7cff", "#14b8a6", "#a855f7", "#f59e0b", "#ec4899", "#f97316",
                    "#22c55e", "#0ea5e9", "#818cf8", "#3b82f6", "#ef4444", "#10b981",
                    "#eab308", "#d946ef", "#06b6d4", "#94a3b8"]

BANNER_FICTIONAL = ("<b>Fictional personas.</b> Every persona in this run is fictional. They were "
                    "built from category research and do not portray specific, identifiable people. "
                    "Their reactions are simulations by independent model agents, not research data.")
BANNER_REAL = ("<b>Internal simulation of real people.</b> The %s panel%s based on real, named "
               "professionals, profiled only from public sources (linked per person). Anything marked "
               "SIMULATION is model output inferred from those sources and is <b>not a statement by "
               "that person</b>. PUBLIC RECORD sections contain only verbatim, sourced quotes. "
               "Internal use only: not for publication, distribution or citation.")

DISP_LABEL = {"hostile": "hostile", "skeptical": "skeptical", "neutral": "neutral", "interested": "interested"}
VERDICT_LABEL = {"yes": "Yes", "maybe": "Maybe", "no": "No"}


def e(x):
    return html.escape(str(x if x is not None else ""), quote=True)


# --------------------------------------------------------------------------- data

def load(outdir):
    reports, problems = C.load_reports(outdir)
    for fn, why in problems:
        print("skipped %s: %s" % (fn, why))
    personas = {p.get("id"): p for p in C.load_personas(outdir)}
    run = C.load_run(outdir)
    report = ""
    rpath = os.path.join(outdir, "report.md")
    if os.path.exists(rpath):
        with open(rpath, encoding="utf-8") as fh:
            report = fh.read()
    for a in reports:  # persona fields fill what an agent left blank
        p = personas.get(a.get("id"), {})
        for k in ("name", "age", "role", "org", "location", "background", "history",
                  "disposition", "group", "real_person", "sources", "device", "lens"):
            if a.get(k) in (None, "", []) and p.get(k) not in (None, "", []):
                a[k] = p[k]
    return reports, report, run, personas


def group_meta(agents, run):
    lib = C.panels_by_id()
    present = [a.get("group") for a in agents if a.get("group")]
    order = C.panel_order(run, present)
    meta = {}
    for i, g in enumerate(order):
        p = lib.get(g, {})
        label = p.get("label")
        if isinstance(label, dict):  # older libraries carried per-language labels
            label = label.get(run.get("lang")) or label.get("en")
        meta[g] = {"label": label or g, "accent": p.get("accent") or FALLBACK_COLOURS[i % len(FALLBACK_COLOURS)],
                   "order": i, "question": p.get("question", "")}
    return meta


def initials(name):
    parts = [x for x in re.split(r"[\s\-]+", str(name or "")) if x and x[0].isalpha()]
    if not parts:
        return "?"
    return (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()


# --------------------------------------------------------------------------- markdown

def inline(s, ids=None):
    s = e(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"<em>\1</em>", s)
    s = re.sub(r"(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+|#[\w-]+)\)",
               lambda m: '<a href="%s"%s>%s</a>' % (m.group(2), "" if m.group(2).startswith("#") else
                                                    ' target="_blank" rel="noopener"', m.group(1)), s)
    s = re.sub(r'(?<![">=/])(https?://[^\s<)\]]+)', r'<a href="\1" target="_blank" rel="noopener">\1</a>', s)
    if ids:
        pat = re.compile(r"(?<![\w#/-])(%s)(?![\w-])" % "|".join(re.escape(i) for i in sorted(ids, key=len, reverse=True)))
        # link agent ids outside of tags and existing links
        parts = re.split(r"(<a\b.*?</a>|<[^>]+>)", s)
        s = "".join(p if p.startswith("<") else pat.sub(r'<a class="aid" href="#agent-\1">\1</a>', p) for p in parts)
    return s


def md(text, ids=None):
    """Markdown subset: headings, paragraphs, quotes, nested lists, tables, code fences, rules."""
    if not text:
        return ""
    lines = text.replace("\r\n", "\n").split("\n")
    out, i, n = [], 0, len(lines)
    stack = []  # open list tags with their indent: [(tag, indent)]

    def close_lists(to_indent=-1):
        while stack and stack[-1][1] > to_indent:
            out.append("</li></%s>" % stack.pop()[0])

    while i < n:
        ln = lines[i].rstrip()
        if ln.lstrip().startswith("```"):
            close_lists()
            buf, i = [], i + 1
            while i < n and not lines[i].lstrip().startswith("```"):
                buf.append(lines[i])
                i += 1
            out.append("<pre><code>%s</code></pre>" % e("\n".join(buf)))
            i += 1
            continue
        if not ln.strip():
            i += 1
            if not (i < n and re.match(r"^\s*([-*+]|\d+\.)\s+", lines[i]) and stack):
                close_lists()
            continue
        if re.match(r"^\s*(---|\*\*\*|___)\s*$", ln):
            close_lists()
            out.append("<hr>")
            i += 1
            continue
        h = re.match(r"^(#{1,6})\s+(.*?)\s*#*$", ln)
        if h:
            close_lists()
            lvl = min(len(h.group(1)) + 1, 6)
            slug = re.sub(r"[^a-z0-9]+", "-", h.group(2).lower()).strip("-")
            out.append('<h%d id="s-%s">%s</h%d>' % (lvl, slug, inline(h.group(2), ids), lvl))
            i += 1
            continue
        if ln.lstrip().startswith(">"):
            close_lists()
            buf = []
            while i < n and lines[i].lstrip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append("<blockquote>%s</blockquote>" % md("\n".join(buf), ids))
            continue
        if ln.lstrip().startswith("|") and i + 1 < n and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            close_lists()
            head = [c.strip() for c in ln.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < n and lines[i].lstrip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            out.append('<div class="tw"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (
                "".join("<th>%s</th>" % inline(c, ids) for c in head),
                "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c, ids) for c in r) for r in rows)))
            continue
        li = re.match(r"^(\s*)([-*+]|\d+\.)\s+(.*)$", ln)
        if li:
            indent = len(li.group(1).replace("\t", "    "))
            tag = "ol" if li.group(2)[0].isdigit() else "ul"
            if stack and indent > stack[-1][1]:
                out.append("<%s>" % tag)
                stack.append((tag, indent))
            else:
                close_lists(indent)
                if stack and stack[-1][1] == indent:
                    if stack[-1][0] != tag:
                        out.append("</li></%s><%s>" % (stack[-1][0], tag))
                        stack[-1] = (tag, indent)
                    else:
                        out.append("</li>")
                else:
                    out.append("<%s>" % tag)
                    stack.append((tag, indent))
            body = [li.group(3)]
            i += 1
            while i < n and lines[i].strip() and not re.match(r"^\s*([-*+]|\d+\.)\s+", lines[i]) \
                    and not lines[i].lstrip().startswith(("#", "|", ">", "```")) \
                    and len(lines[i]) - len(lines[i].lstrip()) > indent:
                body.append(lines[i].strip())
                i += 1
            out.append("<li>%s" % "<br>".join(inline(b, ids) for b in body))
            continue
        close_lists()
        para = [ln.strip()]
        i += 1
        while i < n and lines[i].strip() and not re.match(r"^\s*([-*+>#|]|\d+\.\s|```)", lines[i]):
            para.append(lines[i].strip())
            i += 1
        out.append("<p>%s</p>" % inline(" ".join(para), ids))
    close_lists()
    return "\n".join(out)


def md_section(text, pattern):
    """Return the markdown under the first heading matching pattern, up to the next heading of equal or higher level."""
    lines = (text or "").split("\n")
    for idx, ln in enumerate(lines):
        h = re.match(r"^(#{1,6})\s+(.*)$", ln)
        if h and re.search(pattern, h.group(2), re.I):
            level, body = len(h.group(1)), []
            for nxt in lines[idx + 1:]:
                h2 = re.match(r"^(#{1,6})\s+", nxt)
                if h2 and len(h2.group(1)) <= level:
                    break
                body.append(nxt)
            return "\n".join(body).strip()
    return ""


# --------------------------------------------------------------------------- pieces

def ul(items, cls=""):
    items = [x for x in (items or []) if x not in (None, "")]
    if not items:
        return ""
    return '<ul class="%s">%s</ul>' % (cls, "".join("<li>%s</li>" % e(x) for x in items))


def kv(label, value):
    if value in (None, "", []):
        return ""
    if isinstance(value, list):
        value = "; ".join(str(v) for v in value)
    if isinstance(value, bool):
        value = "yes" if value else "no"
    return '<div class="kv"><span>%s</span><div>%s</div></div>' % (e(label), e(value))


def blk(title, body, cls=""):
    if not body:
        return ""
    return '<section class="blk %s"><h4>%s</h4>%s</section>' % (cls, title, body)


def meter(score, cls=""):
    if not isinstance(score, int) or isinstance(score, bool):
        return ""
    s = max(0, min(100, score))
    tone = "bad" if s < 40 else ("warn" if s < 70 else "good")
    return ('<span class="meter %s %s" title="Usability %d of 100: could this person complete the main '
            'promise unaided"><i style="width:%d%%"></i></span><b class="mnum">%d</b>') % (cls, tone, s, s, s)


def stack_bar(yes, maybe, no, show_numbers=True):
    total = yes + maybe + no
    if not total:
        return '<span class="sbar empty"></span>'
    segs = "".join('<i class="%s" style="flex:%d" title="%s: %d">%s</i>' % (k, v, VERDICT_LABEL[k], v,
                                                                          v if show_numbers else "")
                   for k, v in (("yes", yes), ("maybe", maybe), ("no", no)) if v)
    return '<span class="sbar">%s</span>' % segs


def card(a, gm):
    gid = a.get("group") or "?"
    g = gm.get(gid, {"label": gid, "accent": "#888"})
    disp = a.get("disposition") or "neutral"
    verd = (a.get("verdict") or {}).get("decision") or "maybe"
    usab = a.get("usability") or {}
    visited = a.get("visited", True) is not False
    aid = str(a.get("id") or "")

    meta = " &middot; ".join(e(x) for x in [a.get("age"), a.get("role"), a.get("org"), a.get("location")] if x)
    badges = ['<span class="b grp" style="--a:%s">%s</span>' % (e(g["accent"]), e(g["label"])),
              '<span class="b d-%s">%s</span>' % (e(disp), e(DISP_LABEL.get(disp, disp)))]
    if a.get("real_person"):
        badges.append('<span class="b real" title="Profiled from public sources; speech is simulated">real person</span>')
    if not visited:
        badges.append('<span class="b gap">never reached the product</span>')
    if a.get("visit_method"):
        badges.append('<span class="b vm" title="How this agent reached the product">%s</span>' % e(a["visit_method"]))
    entry = (a.get("deal") or {}).get("entry")
    if entry:
        badges.append('<span class="b e-%s">%s</span>' % (e(str(entry).lower()), e(entry)))

    left, right = [], []
    if a.get("first_10s"):
        left.append(blk("First 10 seconds", '<p class="first">%s</p>' % e(a["first_10s"])))
    if a.get("journey"):
        left.append(blk("What they did", ul(a.get("journey"), "steps").replace("<ul", "<ol").replace("</ul>", "</ol>")))
    if a.get("said"):
        left.append(blk('What they said <em class="tag sim">simulation</em>', ul(a["said"], "said")))
    if a.get("unsaid"):
        left.append(blk('What they did not say <em class="tag sim">simulation</em>', ul(a["unsaid"], "unsaid")))
    pr = a.get("public_record") or []
    if pr:
        rows = "".join('<li><span class="q">%s</span><a href="%s" target="_blank" rel="noopener">%s</a></li>'
                       % (e(r.get("quote")), e(r.get("url")), e(r.get("date") or r.get("url", "")[:60]))
                       for r in pr if isinstance(r, dict))
        left.append(blk('Public record <em class="tag rec">verbatim, sourced</em>', '<ul class="record">%s</ul>' % rows))

    right.append(blk("Blockers", ul(usab.get("blockers"), "bad")))
    right.append(blk("Friction", ul(usab.get("friction"), "warn")))
    right.append(blk("Works", ul(a.get("works"), "good")))
    right.append(blk("Fails", ul(a.get("fails"), "bad")))
    right.append(blk("Missing", ul(a.get("missing"), "warn")))

    d = a.get("deal") or {}
    if d:
        inner = "".join([kv("Entry", d.get("entry")), kv("Ticket", d.get("ticket")), kv("Valuation", d.get("valuation")),
                         kv("Instrument", d.get("instrument")), kv("Board", d.get("board_terms")),
                         kv("Conviction", ("%s / 10" % d["conviction"]) if isinstance(d.get("conviction"), int) else None),
                         kv("Conditions", d.get("conditions")), kv("Red lines", d.get("red_lines")),
                         kv("Brings", d.get("offers")), kv("Wants", d.get("wants")), kv("Refuses", d.get("refuses"))])
        right.append(blk("Deal terms", '<div class="box">%s</div>' % inner))
    s = a.get("science") or {}
    if s:
        claims = "".join('<li><span class="st %s">%s</span>%s%s</li>' % (
            e(c.get("status")), e(c.get("status")), e(c.get("claim")),
            (' <span class="note">%s</span>' % e(c["note"])) if c.get("note") else "")
            for c in (s.get("claims") or []) if isinstance(c, dict))
        flags = "".join('<li><span class="st %s">%s</span>%s</li>' % (e(f.get("severity")), e(f.get("severity")), e(f.get("flag")))
                        for f in (s.get("ethics_flags") or []) if isinstance(f, dict))
        inner = ('<ul class="claims">%s</ul>' % claims if claims else "") + "".join([
            kv("Novelty", s.get("novelty")), kv("How to prove it", s.get("how_to_prove_it")),
            kv("Validity concerns", s.get("validity_concerns")), kv("Prior art", s.get("prior_art")),
            kv("Would cite", s.get("would_cite")), kv("Would collaborate", s.get("would_collaborate")),
            kv("Would criticise publicly", s.get("would_criticise_publicly"))])
        if flags:
            inner += '<h5>Ethics flags</h5><ul class="claims">%s</ul>' % flags
        right.append(blk("Scientific assessment", '<div class="box">%s</div>' % inner))
    extra = [x for x in (a.get("extra") or []) if isinstance(x, dict)]
    if extra:
        rows = []
        for x in extra:
            val = x.get("value")
            if isinstance(val, dict):
                rows.append("".join(kv(k, v) for k, v in val.items()))
            else:
                rows.append(kv(x.get("label") or x.get("key"), val))
        right.append(blk(e(gm.get(gid, {}).get("extra_label") or "Panel read"), '<div class="box">%s</div>' % "".join(rows)))

    v = a.get("verdict") or {}
    foot = ""
    if v.get("why") or v.get("what_would_flip"):
        foot = '<div class="vfull"><span class="v v-%s">%s</span><p>%s</p>%s</div>' % (
            e(verd), e(VERDICT_LABEL.get(verd, verd)), e(v.get("why")),
            ('<p class="flip"><span>What would flip it</span>%s</p>' % e(v["what_would_flip"])) if v.get("what_would_flip") else "")
    src = a.get("sources") or []
    if src:
        foot += blk("Sources", '<ul class="src">%s</ul>' % "".join(
            '<li><a href="%s" target="_blank" rel="noopener">%s</a></li>' % (e(u), e(u)) for u in src))
    ev = a.get("evidence") or []
    if ev:
        foot += '<p class="ev"><span>Evidence</span>%s</p>' % " &rarr; ".join(e(x) for x in ev)

    bg = " ".join(x for x in [a.get("background"), a.get("history")] if x)
    lens = ('<p class="lens"><span>Lens</span>%s</p>' % e(a["lens"])) if a.get("lens") else ""
    search = " ".join(json.dumps(a, ensure_ascii=False).split()).lower()

    return """
<article class="card" id="agent-%s" data-group="%s" data-disp="%s" data-verdict="%s" data-search="%s" style="--a:%s">
  <button class="ch" type="button" aria-expanded="false">
    <span class="av">%s</span>
    <span class="who"><span class="nm">%s <span class="aid2">%s</span></span><span class="mt">%s</span></span>
    <span class="badges">%s</span>
    <span class="score">%s</span>
    <span class="v v-%s">%s</span>
    <svg class="chev" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>
  </button>
  <div class="cb">
    %s%s
    <div class="cols"><div>%s</div><div>%s</div></div>
    %s
  </div>
</article>""" % (
        e(aid), e(gid), e(disp), e(verd), e(search), e(g["accent"]),
        e(initials(a.get("name"))), e(a.get("name") or aid), e(aid), meta,
        "".join(badges), meter(usab.get("score")), e(verd), e(VERDICT_LABEL.get(verd, verd)),
        ('<p class="bg">%s</p>' % e(bg)) if bg else "", lens,
        "".join(x for x in left if x), "".join(x for x in right if x), foot)


def items(values):
    values = [v for v in (values or []) if v]
    if not values:
        return ""
    return "<ul class='dl'>%s</ul>" % "".join("<li>%s</li>" % e(v) for v in values)


def deal_table(agents):
    caps = [a for a in agents if (a.get("deal") or {}).get("entry")]
    if not caps:
        return ""
    order = {"YES": 0, "CONDITIONAL": 1, "NO": 2}
    caps.sort(key=lambda a: (order.get(a["deal"].get("entry"), 3), -(a["deal"].get("conviction") or 0)))
    rows = "".join(
        "<tr><td><a href='#agent-%s'><b>%s</b></a><span class='who'>%s</span></td><td><span class='b e-%s'>%s</span></td>"
        "<td class='num'>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            e(a.get("id")), e(a.get("name")), e(a.get("role") or a.get("org") or ""), e(str(a["deal"].get("entry")).lower()),
            e(a["deal"].get("entry")), e(a["deal"].get("conviction") if a["deal"].get("conviction") is not None else ""),
            e(a["deal"].get("ticket")), e(a["deal"].get("valuation")), e(a["deal"].get("instrument")),
            items(a["deal"].get("conditions")), items(a["deal"].get("red_lines")))
        for a in caps)
    return ('<div class="tw"><table class="deals"><thead><tr><th>Investor</th><th>Entry</th><th>Conviction</th>'
            '<th>Ticket</th><th>Valuation</th><th>Instrument</th><th>Conditions</th><th>Red lines</th></tr></thead>'
            '<tbody>%s</tbody></table></div>' % rows)


def panel_rows(agents, gm):
    rows = []
    for g in sorted(gm, key=lambda x: gm[x]["order"]):
        members = [a for a in agents if a.get("group") == g and a.get("visited", True) is not False]
        if not members:
            continue
        vc = {k: sum(1 for a in members if (a.get("verdict") or {}).get("decision") == k) for k in ("yes", "maybe", "no")}
        scores = [(a.get("usability") or {}).get("score") for a in members]
        scores = [s for s in scores if isinstance(s, int)]
        avg = round(sum(scores) / len(scores)) if scores else None
        done = sum(1 for a in members if (a.get("usability") or {}).get("completed_main_task"))
        worst = min(members, key=lambda a: (a.get("usability") or {}).get("score", 101))
        blocker = ((worst.get("usability") or {}).get("blockers") or worst.get("fails") or [""])[0]
        rows.append("""<tr data-g="%s">
  <td><span class="pl"><span class="swatch" style="--a:%s"></span>%s</span><span class="pq">%s</span></td>
  <td class="num">%d</td><td class="barcell">%s</td><td class="num">%d / %d</td>
  <td class="mcell">%s</td>
  <td class="blocker">%s<a class="aid" href="#agent-%s">%s</a></td></tr>""" % (
            e(g), e(gm[g]["accent"]), e(gm[g]["label"]), e(gm[g]["question"]), len(members),
            stack_bar(vc["yes"], vc["maybe"], vc["no"]), done, len(members), meter(avg) if avg is not None else "",
            ("%s " % e(blocker)) if blocker else "", e(worst.get("id")), e(worst.get("id"))))
    return "".join(rows)


def voices(agents, gm, field, limit=12):
    items = []
    for a in agents:
        vals = a.get(field) or []
        if not vals or a.get("visited", True) is False:
            continue
        g = gm.get(a.get("group"), {"accent": "#888", "label": a.get("group")})
        items.append('<figure class="voice" style="--a:%s"><blockquote>%s</blockquote><figcaption>'
                     '<span class="av sm">%s</span><a href="#agent-%s">%s</a><span>%s</span></figcaption></figure>' % (
                         e(g["accent"]), e(vals[0]), e(initials(a.get("name"))), e(a.get("id")),
                         e(a.get("name")), e(g["label"])))
    return "".join(items[:limit])


# --------------------------------------------------------------------------- page

def build(outdir, title=""):
    agents, report, run, personas = load(outdir)
    gm = group_meta(agents, run)
    lib = C.panels_by_id()
    for g in gm:
        gm[g]["extra_label"] = ((lib.get(g) or {}).get("extra_block") or {}).get("label")
    agents.sort(key=lambda a: (gm.get(a.get("group"), {}).get("order", 99), str(a.get("id", ""))))

    title = title or run.get("product") or os.path.basename(os.path.abspath(outdir))
    reached = [a for a in agents if a.get("visited", True) is not False]
    expected = len(personas) or sum((run.get("panels") or {}).values()) or len(agents)
    done = sum(1 for a in reached if (a.get("usability") or {}).get("completed_main_task"))
    scores = [(a.get("usability") or {}).get("score") for a in reached]
    scores = [s for s in scores if isinstance(s, int) and not isinstance(s, bool)]
    avg = round(sum(scores) / len(scores)) if scores else 0
    vc = {k: sum(1 for a in reached if (a.get("verdict") or {}).get("decision") == k) for k in ("yes", "maybe", "no")}
    entries = [(a.get("deal") or {}).get("entry") for a in reached if (a.get("deal") or {}).get("entry")]
    ec = {k: entries.count(k) for k in ("YES", "CONDITIONAL", "NO")}

    real_groups = [gm[g]["label"] for g in sorted(gm, key=lambda x: gm[x]["order"])
                   if any(a.get("group") == g and a.get("real_person") for a in agents)]
    if real_groups:
        banner = '<div class="banner real" role="note">%s</div>' % (
            BANNER_REAL % (", ".join(e(x) for x in real_groups), "s are" if len(real_groups) > 1 else " is"))
    else:
        banner = '<div class="banner" role="note">%s</div>' % BANNER_FICTIONAL

    ids = [str(a.get("id")) for a in agents if a.get("id")]
    plan = md_section(report, r"action plan|ranked")
    power = md_section(report, r"power move")
    when = run.get("date") or date.today().isoformat()

    chips = ['<button class="chip on" data-k="group" data-v="all" type="button">All panels</button>']
    chips += ['<button class="chip" data-k="group" data-v="%s" style="--a:%s" type="button"><span class="swatch"></span>%s <span class="c">%d</span></button>'
              % (e(g), e(gm[g]["accent"]), e(gm[g]["label"]), sum(1 for a in agents if a.get("group") == g))
              for g in sorted(gm, key=lambda x: gm[x]["order"])]
    vchips = ['<button class="chip on" data-k="verdict" data-v="all" type="button">Any verdict</button>']
    vchips += ['<button class="chip vc-%s" data-k="verdict" data-v="%s" type="button">%s <span class="c">%d</span></button>'
               % (k, k, VERDICT_LABEL[k], sum(1 for a in agents if (a.get("verdict") or {}).get("decision") == k))
               for k in ("yes", "maybe", "no")]
    dchips = ['<button class="chip on" data-k="disp" data-v="all" type="button">Any disposition</button>']
    dchips += ['<button class="chip" data-k="disp" data-v="%s" type="button">%s</button>' % (k, DISP_LABEL[k])
               for k in ("hostile", "skeptical", "neutral", "interested")
               if any(a.get("disposition") == k for a in agents)]

    tabs = [("overview", "Overview", ""), ("agents", "Agents", str(len(agents))), ("synthesis", "Synthesis", "")]
    if entries:
        tabs.append(("deals", "Deals", str(len(entries))))
    tab_html = "".join('<a class="tab" href="#%s" data-tab="%s">%s%s</a>' % (
        t, t, lbl, (' <span class="c">%s</span>' % n) if n else "") for t, lbl, n in tabs)

    kpi_capital = ""
    if entries:
        kpi_capital = """<div class="kpi"><span class="eyebrow">Capital entry</span>
  <div class="kv3"><b class="good">%d</b><span>yes</span><b class="warn">%d</b><span>conditional</span><b class="bad">%d</b><span>no</span></div>
  <a class="kpilink" href="#deals">Deal table</a></div>""" % (ec["YES"], ec["CONDITIONAL"], ec["NO"])

    gaps = [p for pid, p in personas.items() if pid not in {a.get("id") for a in reached}]
    gap_html = ""
    if gaps:
        gap_html = '<section class="panel gaps"><h3>Gaps</h3><p>%d persona%s filed no usable report and %s excluded from every count: %s.</p></section>' % (
            len(gaps), "" if len(gaps) == 1 else "s", "is" if len(gaps) == 1 else "are",
            ", ".join(e("%s (%s)" % (p.get("name"), p.get("id"))) for p in gaps))

    doc = PAGE % {
        "title": e(title), "tokens": T.TOKENS, "css": CSS, "theme_js": T.THEME_JS, "mark": T.MARK_SVG,
        "theme_btn": T.THEME_BUTTON, "when": e(when), "target": e(run.get("target", "")),
        "ttype": e(run.get("target_type", "")), "n_agents": len(agents),
        "n_panels": len(gm), "banner": banner, "tabs": tab_html,
        "filed": len(reached), "expected": expected,
        "done": done, "done_pct": round(100 * done / len(reached)) if reached else 0,
        "avg": avg, "avg_meter": meter(avg, "lg"),
        "vy": vc["yes"], "vm": vc["maybe"], "vn": vc["no"], "vbar": stack_bar(vc["yes"], vc["maybe"], vc["no"], False),
        "kpi_capital": kpi_capital,
        "panel_rows": panel_rows(agents, gm),
        "plan": ('<section class="panel"><div class="ph"><h3>Ranked action plan</h3><a href="#synthesis">Full synthesis</a></div><div class="md">%s</div>%s</section>' % (
            md(plan, ids), ('<div class="power"><span class="eyebrow">Power move</span><div class="md">%s</div></div>' % md(power, ids)) if power else ""))
        if plan else "",
        "said": voices(agents, gm, "said"), "unsaid": voices(agents, gm, "unsaid"),
        "chips": "".join(chips), "vchips": "".join(vchips), "dchips": "".join(dchips),
        "cards": "".join(card(a, gm) for a in agents) or '<p class="emptyall">No reports found in agents/.</p>',
        "report": md(report, ids) if report else '<p class="emptyall">No report.md yet. Write the synthesis, then rebuild the board.</p>',
        "deals": deal_table(agents), "gaps": gap_html,
        "js": JS,
    }
    out = os.path.join(outdir, "index.html")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)
    write_readme(outdir, title, agents, gm, real_groups, when)
    print("built %s (%d agents, %d KB)" % (out, len(agents), len(doc.encode("utf-8")) // 1024))
    return out


def write_readme(outdir, title, agents, gm, real_groups, when):
    """A package that leaves this folder must carry the disclaimer with it."""
    path = os.path.join(outdir, "README.md")
    if os.path.exists(path):
        return
    if real_groups:
        banner = re.sub(r"<[^>]+>", "", BANNER_REAL % (", ".join(real_groups), "s are" if len(real_groups) > 1 else " is"))
    else:
        banner = re.sub(r"<[^>]+>", "", BANNER_FICTIONAL)
    counts = {}
    for a in agents:
        counts[a.get("group")] = counts.get(a.get("group"), 0) + 1
    lines = ["# focus-swarm run: %s" % title, "", "> %s" % banner, "",
             "%d agents, %s." % (len(agents), when), ""]
    lines += ["- %s: %d" % (gm.get(g, {}).get("label", g), n) for g, n in
              sorted(counts.items(), key=lambda kv: gm.get(kv[0], {}).get("order", 99))]
    lines += ["", "```", "index.html       the board, open it in any browser",
              "report.md        the synthesis", "brief.md         recon notes",
              "run.config.json  the cast as picked", "personas.json    the cast as built",
              "agents/*.json    one raw report per agent", "```", ""]
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="generator" content="focus-swarm build_board.py">
<title>%(title)s: swarm report</title>
<style>%(tokens)s%(css)s</style>
<script>%(theme_js)s</script>
</head><body>
<header class="top"><div class="wrap row">
  <span class="brand">%(mark)sfocus-swarm</span><span class="crumb">%(title)s</span>
  <span class="grow"></span>
  <nav class="tabs" aria-label="Sections">%(tabs)s</nav>
  %(theme_btn)s
</div></header>

<main class="wrap">
<section class="hero">
  <p class="eyebrow">Swarm report &middot; %(when)s</p>
  <h1>%(title)s</h1>
  <p class="sub"><span class="ttype">%(ttype)s</span><code>%(target)s</code><span class="dot"></span>%(n_agents)d independent agents across %(n_panels)d panels</p>
  %(banner)s
</section>

<section class="kpis">
  <div class="kpi"><span class="eyebrow">Reports filed</span><div class="kbig">%(filed)d<small>/ %(expected)d</small></div><span class="khint">each from its own context</span></div>
  <div class="kpi"><span class="eyebrow" style="display:block;padding-right:52px">Completed the main task</span><div class="kbig">%(done)d<small>/ %(filed)d</small></div>
    <span class="ring" style="--p:%(done_pct)d"><i></i></span><span class="khint">unaided, %(done_pct)d%%</span></div>
  <div class="kpi"><span class="eyebrow">Average usability</span><div class="kbig">%(avg)d<small>/ 100</small></div>%(avg_meter)s</div>
  <div class="kpi"><span class="eyebrow">Verdicts</span>
    <div class="kv3"><b class="good">%(vy)d</b><span>yes</span><b class="warn">%(vm)d</b><span>maybe</span><b class="bad">%(vn)d</b><span>no</span></div>%(vbar)s</div>
  %(kpi_capital)s
</section>

<div class="view" data-view="overview">
  <section class="panel"><div class="ph"><h3>Panels at a glance</h3><a href="#agents">All agents</a></div>
    <div class="tw"><table class="glance"><thead><tr><th>Panel</th><th class="num">Agents</th><th>Yes / maybe / no</th><th class="num">Completed</th><th>Usability</th><th>Hardest stop (lowest-scoring agent)</th></tr></thead>
    <tbody>%(panel_rows)s</tbody></table></div></section>
  %(plan)s
  <section class="panel"><div class="ph"><h3>What they said out loud</h3><span class="tag sim">simulation</span></div>
    <div class="voices">%(said)s</div></section>
  <section class="panel"><div class="ph"><h3>What they did not say</h3><span class="tag sim">simulation</span></div>
    <p class="phint">Each agent also reports what it noticed but would not say in the room. Read together, these are often the most useful lines in the run.</p>
    <div class="voices unsaid">%(unsaid)s</div></section>
  %(gaps)s
</div>

<div class="view" data-view="agents" hidden>
  <div class="filters">
    <div class="frow">%(chips)s</div>
    <div class="frow">%(vchips)s<span class="sep"></span>%(dchips)s</div>
    <div class="frow"><input class="search" type="search" placeholder="Search every report" aria-label="Search reports">
      <span class="count"><b id="shown">0</b> shown</span>
      <button class="chip" id="expand" type="button">Expand all</button></div>
  </div>
  <div class="cards">%(cards)s</div>
  <p class="emptyall" id="empty" hidden>No agent matches these filters.</p>
</div>

<div class="view" data-view="synthesis" hidden>
  <article class="panel md doc">%(report)s</article>
</div>

<div class="view" data-view="deals" hidden>
  <section class="panel"><div class="ph"><h3>Deal table</h3><span class="phint">sorted by entry, then conviction</span></div>%(deals)s</section>
</div>
</main>
<footer class="foot"><div class="wrap">Built by focus-swarm from %(n_agents)d agent reports. Personas and their words are simulations.</div></footer>
<script>%(js)s</script>
</body></html>
"""

CSS = r"""
.wrap{max-width:1180px;margin:0 auto;padding:0 24px}
.top{position:sticky;top:0;z-index:20;border-bottom:1px solid var(--line);
  background:color-mix(in srgb,var(--bg) 84%,transparent);backdrop-filter:saturate(1.4) blur(10px)}
.row{display:flex;align-items:center;gap:14px;height:58px}
.grow{flex:1}
.crumb{color:var(--text-3);font-size:13px;padding-left:14px;border-left:1px solid var(--line);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:240px}
.tabs{display:flex;gap:2px;background:var(--surface-2);border:1px solid var(--line);border-radius:11px;padding:3px}
.tab{padding:6px 12px;border-radius:8px;color:var(--text-2);text-decoration:none;font-size:13.5px;font-weight:550;white-space:nowrap}
.tab:hover{color:var(--text)}
.tab.on{background:var(--surface);color:var(--text);box-shadow:0 1px 2px rgba(0,0,0,.08)}
.tab .c,.chip .c{font-family:var(--mono);font-size:11px;color:var(--text-3);margin-left:2px}
.hero{padding:38px 0 8px}
.hero h1{font-size:40px;line-height:1.08;letter-spacing:-.03em;margin:8px 0 12px}
.sub{display:flex;align-items:center;flex-wrap:wrap;gap:10px;color:var(--text-2);font-size:14px;margin:0 0 20px}
.sub code{font-family:var(--mono);font-size:13px;color:var(--text-2);background:var(--surface);border:1px solid var(--line);padding:3px 9px;border-radius:7px}
.ttype{font-size:10.5px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;background:var(--accent-soft);color:var(--accent);padding:4px 9px;border-radius:999px}
.dot{width:4px;height:4px;border-radius:50%;background:var(--text-3)}
.banner{border:1px solid var(--line);border-left:3px solid var(--accent);background:var(--surface);border-radius:10px;
  padding:12px 16px;font-size:13.5px;color:var(--text-2);line-height:1.5;max-width:900px}
.banner b{color:var(--text)}
.banner.real{border-left-color:var(--warn);background:var(--warn-soft)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:26px 0 22px}
.kpi{position:relative;background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:16px 18px 16px;box-shadow:var(--shadow);min-height:118px;display:flex;flex-direction:column;gap:8px}
.kbig{font-size:36px;font-weight:700;letter-spacing:-.035em;line-height:1;font-variant-numeric:tabular-nums}
.kbig small{font-size:15px;font-weight:500;color:var(--text-3);letter-spacing:0;margin-left:5px}
.khint{font-size:12px;color:var(--text-3)}
.kpilink{font-size:12.5px;margin-top:auto}
.kv3{display:grid;grid-template-columns:auto 1fr auto 1fr auto 1fr;align-items:baseline;gap:4px 6px}
.kv3 b{font-size:28px;letter-spacing:-.03em;line-height:1;font-variant-numeric:tabular-nums}
.kv3 span{font-size:12px;color:var(--text-3)}
b.good{color:var(--good)} b.warn{color:var(--warn)} b.bad{color:var(--bad)}
table.deals .who{display:block;color:var(--text-3);font-size:12.5px;margin-top:2px}
table.deals a{text-decoration:none}
table.deals ul.dl{margin:0;padding-left:16px}
table.deals ul.dl li{margin:0 0 6px}
table.deals td:nth-child(3){width:1%}
table.deals td:nth-child(7),table.deals td:nth-child(8){min-width:220px}
.ring{position:absolute;right:16px;top:16px;width:42px;height:42px;border-radius:50%;
  background:conic-gradient(var(--good) calc(var(--p)*1%),var(--surface-3) 0)}
.ring i{position:absolute;inset:6px;border-radius:50%;background:var(--surface)}
.meter{display:inline-block;position:relative;width:84px;height:6px;border-radius:99px;background:var(--surface-3);vertical-align:middle;overflow:hidden}
.meter i{position:absolute;inset:0 auto 0 0;border-radius:99px}
.meter.good i{background:var(--good)} .meter.warn i{background:var(--warn)} .meter.bad i{background:var(--bad)}
.meter.lg{width:100%;height:8px;margin-top:auto}
.mnum{font-family:var(--mono);font-size:12px;color:var(--text-2);margin-left:7px;font-weight:500}
.kpi .mnum{display:none}
.sbar{display:flex;gap:2px;height:22px;border-radius:7px;overflow:hidden;min-width:120px}
.kpi .sbar{height:8px;margin-top:auto;border-radius:99px}
.sbar i{display:flex;align-items:center;justify-content:center;font-style:normal;font-size:11px;font-weight:700;font-family:var(--mono);color:#fff}
.sbar i.yes{background:var(--good)} .sbar i.maybe{background:var(--warn)} .sbar i.no{background:var(--bad)}
:root[data-theme="dark"] .sbar i{color:#0b0c10}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .sbar i{color:#0b0c10}}
.sbar.empty{background:var(--surface-2)}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:20px 22px;margin:0 0 16px;box-shadow:var(--shadow)}
.ph{display:flex;align-items:baseline;justify-content:space-between;gap:12px;margin:0 0 14px}
.ph h3,.panel h3{margin:0;font-size:16px;letter-spacing:-.01em}
.ph a{font-size:13px}
.phint{color:var(--text-3);font-size:13px;margin:-6px 0 14px}
.ph .phint{margin:0}
.tw{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th{text-align:left;font-size:11px;letter-spacing:.07em;text-transform:uppercase;color:var(--text-3);font-weight:600;padding:9px 12px;border-bottom:1px solid var(--line);white-space:nowrap}
td{padding:12px;border-bottom:1px solid var(--line);vertical-align:top}
tr:last-child td{border-bottom:0}
td.num,th.num{text-align:right;font-family:var(--mono);white-space:nowrap}
table.glance{min-width:820px}
table.glance td{vertical-align:middle}
.pl{display:flex;align-items:center;gap:9px;font-weight:600}
.pq{display:block;color:var(--text-3);font-size:12px;margin:3px 0 0 19px;max-width:300px}
.barcell{width:190px}
.mcell{white-space:nowrap}
.blocker{color:var(--text-2);font-size:13px;max-width:360px}
.swatch{display:inline-block;width:10px;height:10px;border-radius:3px;background:var(--a);flex:none}
a.aid{font-family:var(--mono);font-size:11.5px;color:var(--text-3);text-decoration:none;border:1px solid var(--line);border-radius:5px;padding:0 5px;margin-left:2px;white-space:nowrap}
a.aid:hover{color:var(--accent);border-color:var(--accent)}
.voices{columns:3 260px;column-gap:12px}
.voice{break-inside:avoid;margin:0 0 12px;background:var(--surface-2);border:1px solid var(--line);border-radius:12px;padding:14px 14px 12px;position:relative}
.voice::before{content:"";position:absolute;left:0;top:12px;bottom:12px;width:3px;border-radius:0 3px 3px 0;background:var(--a)}
.voice blockquote{margin:0 0 10px;font-size:14px;line-height:1.5}
.voices.unsaid blockquote{font-style:italic;color:var(--text-2)}
.voice figcaption{display:flex;align-items:center;gap:8px;font-size:12px;color:var(--text-3)}
.voice figcaption a{color:var(--text);font-weight:600;text-decoration:none}
.voice figcaption span:last-child{margin-left:auto}
.power{margin-top:16px;padding:14px 16px;border-radius:12px;background:var(--accent-soft)}
.gaps p{color:var(--text-2);margin:8px 0 0}
.filters{position:sticky;top:58px;z-index:10;background:color-mix(in srgb,var(--bg) 92%,transparent);backdrop-filter:blur(8px);
  padding:14px 0 12px;margin:0 0 6px;display:flex;flex-direction:column;gap:8px;border-bottom:1px solid var(--line)}
.frow{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.sep{width:1px;height:20px;background:var(--line);margin:0 6px}
.chip{display:inline-flex;align-items:center;gap:6px;background:var(--surface);border:1px solid var(--line);color:var(--text-2);
  border-radius:999px;padding:5px 12px;font-size:13px;cursor:pointer;user-select:none}
.chip:hover{color:var(--text);border-color:var(--line-2)}
.chip.on{background:var(--text);color:var(--bg);border-color:var(--text)}
.chip.on .c{color:inherit;opacity:.7}
.chip[style*="--a"].on{background:var(--a);border-color:var(--a);color:#0b0c10}
.search{flex:1;min-width:220px;background:var(--surface);border:1px solid var(--line);border-radius:999px;padding:7px 14px;font-size:13.5px;outline:none}
.search:focus{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
.count{font-size:13px;color:var(--text-3)}
.cards{display:flex;flex-direction:column;gap:8px;padding-top:8px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);overflow:hidden;scroll-margin-top:190px;transition:box-shadow .15s,border-color .15s}
.card.open{box-shadow:var(--shadow);border-color:var(--line-2)}
.card.flash{animation:flash 1.6s ease}
@keyframes flash{0%{box-shadow:0 0 0 4px var(--accent-soft)}100%{box-shadow:var(--shadow)}}
.ch{all:unset;box-sizing:border-box;width:100%;display:grid;grid-template-columns:auto minmax(0,1fr) auto auto auto auto;gap:14px;align-items:center;padding:12px 16px;cursor:pointer}
.ch:hover{background:var(--surface-2)}
.ch:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
.av{width:36px;height:36px;border-radius:11px;display:inline-flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;
  color:var(--a);background:color-mix(in srgb,var(--a) 15%,var(--surface));border:1px solid color-mix(in srgb,var(--a) 35%,transparent);flex:none}
.av.sm{width:24px;height:24px;border-radius:7px;font-size:10px;--a:inherit}
.voice .av.sm{color:var(--a);background:color-mix(in srgb,var(--a) 15%,var(--surface))}
.who{display:flex;flex-direction:column;min-width:0}
.nm{font-weight:650;font-size:15px;letter-spacing:-.01em}
.aid2{font-family:var(--mono);font-size:11px;color:var(--text-3);font-weight:400;margin-left:4px}
.mt{font-size:12.5px;color:var(--text-3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.badges{display:flex;gap:5px;flex-wrap:wrap;justify-content:flex-end}
.b{font-size:11px;padding:2px 8px;border-radius:6px;border:1px solid var(--line);color:var(--text-2);white-space:nowrap;background:var(--surface)}
.b.grp{color:color-mix(in srgb,var(--a) 75%,var(--text));border-color:color-mix(in srgb,var(--a) 40%,var(--line));background:color-mix(in srgb,var(--a) 8%,var(--surface))}
.b.d-hostile{color:var(--bad);border-color:color-mix(in srgb,var(--bad) 40%,var(--line));background:var(--bad-soft)}
.b.d-skeptical{color:var(--warn);border-color:color-mix(in srgb,var(--warn) 40%,var(--line))}
.b.d-interested{color:var(--good);border-color:color-mix(in srgb,var(--good) 35%,var(--line))}
.b.real{color:var(--warn);background:var(--warn-soft);border-color:color-mix(in srgb,var(--warn) 45%,var(--line));font-weight:600}
.b.gap{color:var(--bad);background:var(--bad-soft);font-weight:600}
.b.vm{font-family:var(--mono);font-size:10.5px;color:var(--text-3)}
.b.e-yes{color:var(--good);background:var(--good-soft);font-weight:700}
.b.e-conditional{color:var(--warn);background:var(--warn-soft);font-weight:700}
.b.e-no{color:var(--bad);background:var(--bad-soft);font-weight:700}
.score{display:flex;align-items:center;min-width:120px;justify-content:flex-end}
.v{font-size:12px;font-weight:700;padding:4px 10px;border-radius:7px;min-width:58px;text-align:center}
.v-yes{background:var(--good-soft);color:var(--good)} .v-maybe{background:var(--warn-soft);color:var(--warn)} .v-no{background:var(--bad-soft);color:var(--bad)}
.chev{color:var(--text-3);transition:transform .2s}
.card.open .chev{transform:rotate(180deg)}
.cb{display:none;padding:2px 20px 20px 66px;border-top:1px solid var(--line)}
.card.open .cb{display:block}
p.bg{color:var(--text-2);margin:16px 0 0;font-size:14px;max-width:90ch}
p.lens{margin:8px 0 0;font-size:13px;color:var(--text-2)}
p.lens span,p.ev span,p.flip span{font-size:10.5px;letter-spacing:.09em;text-transform:uppercase;color:var(--text-3);font-weight:600;margin-right:8px}
.cols{display:grid;grid-template-columns:1.1fr .9fr;gap:12px 28px}
.blk{margin:18px 0 0}
.blk h4{margin:0 0 8px;font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:var(--text-3);font-weight:650;display:flex;align-items:center;gap:8px}
.blk h5{margin:12px 0 6px;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--text-3)}
.tag{font-style:normal;font-size:10px;letter-spacing:.08em;text-transform:uppercase;padding:2px 7px;border-radius:5px;font-weight:650}
.tag.sim{background:var(--accent-soft);color:var(--accent)}
.tag.rec{background:var(--good-soft);color:var(--good)}
.blk ul,.blk ol{margin:0;padding-left:18px;font-size:14px}
.blk li{margin:4px 0}
ul.good li::marker{color:var(--good)} ul.bad li::marker{color:var(--bad)} ul.warn li::marker{color:var(--warn)}
ol.steps{color:var(--text-2);font-size:13.5px}
p.first{margin:0;padding:12px 14px;background:var(--surface-2);border-radius:10px;font-size:14.5px;line-height:1.55}
ul.said,ul.unsaid,ul.record{list-style:none;padding:0}
ul.said li,ul.unsaid li,ul.record li{padding:9px 12px;border-radius:0 9px 9px 0;margin:0 0 6px;background:var(--surface-2);border-left:2px solid var(--accent)}
ul.unsaid li{border-left-color:var(--a);font-style:italic;color:var(--text-2)}
ul.record li{border-left-color:var(--good)}
ul.record .q{display:block}
ul.record a,ul.src{font-family:var(--mono);font-size:11.5px;word-break:break-all}
ul.src{list-style:none;padding:0}
.box{background:var(--surface-2);border-radius:10px;padding:8px 14px}
.kv{display:grid;grid-template-columns:140px 1fr;gap:12px;padding:7px 0;font-size:13.5px;border-bottom:1px solid var(--line)}
.kv:last-child{border-bottom:0}
.kv span{color:var(--text-3);font-size:12px}
ul.claims{list-style:none;padding:0;margin:6px 0}
ul.claims li{font-size:13.5px;margin:6px 0}
.note{color:var(--text-3)}
.st{display:inline-block;font-size:10px;letter-spacing:.06em;text-transform:uppercase;padding:2px 7px;border-radius:5px;margin-right:8px;font-weight:700}
.st.demonstrated,.st.low{background:var(--good-soft);color:var(--good)}
.st.plausible,.st.medium{background:var(--warn-soft);color:var(--warn)}
.st.unsupported,.st.high,.st.critical{background:var(--bad-soft);color:var(--bad)}
.vfull{margin:20px 0 0;padding:14px 16px;border-radius:12px;background:var(--surface-2);display:grid;grid-template-columns:auto 1fr;gap:6px 14px;align-items:start}
.vfull p{margin:0;font-size:14px}
.vfull .flip{grid-column:2;color:var(--text-2);font-size:13.5px}
p.ev{margin:14px 0 0;font-size:12px;color:var(--text-3);font-family:var(--mono);line-height:1.6}
.emptyall{color:var(--text-3);text-align:center;padding:40px 0}
.md{font-size:15px;line-height:1.65}
.doc{padding:30px 38px}
.md h2{font-size:24px;letter-spacing:-.02em;margin:30px 0 10px}
.md h2:first-child,.md blockquote:first-child{margin-top:0}
.md h3{font-size:18px;margin:26px 0 8px;letter-spacing:-.01em}
.md h4,.md h5{font-size:15px;margin:20px 0 6px}
.md p,.md li{color:var(--text-2)}
.md strong{color:var(--text)}
.md blockquote{margin:14px 0;padding:10px 16px;border-left:3px solid var(--accent);background:var(--surface-2);border-radius:0 10px 10px 0}
.md blockquote p{margin:4px 0}
.md hr{border:0;border-top:1px solid var(--line);margin:28px 0}
.md code{font-family:var(--mono);font-size:12.5px;background:var(--surface-2);padding:1px 6px;border-radius:5px}
.md pre{background:var(--surface-2);border:1px solid var(--line);border-radius:10px;padding:12px 14px;overflow:auto}
.md pre code{background:none;padding:0}
.md table{margin:12px 0;min-width:640px}
.md ol,.md ul{padding-left:22px}
.md li{margin:5px 0}
.foot{border-top:1px solid var(--line);margin-top:40px;padding:22px 0 40px;color:var(--text-3);font-size:12.5px}
@media (max-width:900px){.cols{grid-template-columns:1fr}.cb{padding-left:20px}.ch{grid-template-columns:auto minmax(0,1fr) auto auto}.badges,.score{display:none}.tabs .tab{padding:6px 9px}.crumb{display:none}}
@media (max-width:620px){.wrap{padding:0 16px}.hero h1{font-size:30px}.doc{padding:20px}.tabs{overflow-x:auto;max-width:calc(100vw - 150px)}.voices{columns:1}.filters{position:static}}
@media print{.top,.filters{position:static}.view{display:block!important}.view[hidden]{display:block!important}.card .cb{display:block}.chev,#theme{display:none}}
"""

JS = r"""
(function(){
  var views = document.querySelectorAll('.view'), tabs = document.querySelectorAll('.tab');
  function show(name){
    if (!document.querySelector('.view[data-view="' + name + '"]')) name = 'overview';
    views.forEach(function(v){ v.hidden = v.dataset.view !== name; });
    tabs.forEach(function(t){ t.classList.toggle('on', t.dataset.tab === name); });
  }
  function route(){
    var h = decodeURIComponent(location.hash.replace(/^#/, ''));
    if (h.indexOf('agent-') === 0){
      show('agents');
      var c = document.getElementById(h);
      if (c){
        c.style.display = '';
        open(c, true);
        setTimeout(function(){ c.scrollIntoView({block: 'start'}); c.classList.remove('flash'); void c.offsetWidth; c.classList.add('flash'); }, 30);
      }
      return;
    }
    show(h || 'overview');
    if (!h || h === 'overview' || h === 'agents' || h === 'synthesis' || h === 'deals') window.scrollTo(0, 0);
  }
  function open(c, on){
    c.classList.toggle('open', on);
    var b = c.querySelector('.ch'); if (b) b.setAttribute('aria-expanded', on ? 'true' : 'false');
  }
  document.querySelectorAll('.ch').forEach(function(b){
    b.addEventListener('click', function(){ var c = b.parentNode; open(c, !c.classList.contains('open')); });
  });
  var S = {group: 'all', disp: 'all', verdict: 'all', q: ''};
  function apply(){
    var shown = 0;
    document.querySelectorAll('.card').forEach(function(c){
      var ok = (S.group === 'all' || c.dataset.group === S.group) && (S.disp === 'all' || c.dataset.disp === S.disp)
            && (S.verdict === 'all' || c.dataset.verdict === S.verdict) && (!S.q || c.dataset.search.indexOf(S.q) >= 0);
      c.style.display = ok ? '' : 'none'; if (ok) shown++;
    });
    var n = document.getElementById('shown'); if (n) n.textContent = shown;
    var em = document.getElementById('empty'); if (em) em.hidden = shown > 0;
  }
  document.querySelectorAll('.chip[data-k]').forEach(function(ch){
    ch.addEventListener('click', function(){
      var k = ch.dataset.k;
      document.querySelectorAll('.chip[data-k="' + k + '"]').forEach(function(o){ o.classList.remove('on'); });
      ch.classList.add('on'); S[k] = ch.dataset.v; apply();
    });
  });
  var q = document.querySelector('.search');
  if (q) q.addEventListener('input', function(){ S.q = q.value.toLowerCase().trim(); apply(); });
  var ex = document.getElementById('expand');
  if (ex) ex.addEventListener('click', function(){
    var vis = Array.prototype.filter.call(document.querySelectorAll('.card'), function(c){ return c.style.display !== 'none'; });
    var any = vis.some(function(c){ return !c.classList.contains('open'); });
    vis.forEach(function(c){ open(c, any); });
    ex.textContent = any ? 'Collapse all' : 'Expand all';
  });
  document.querySelectorAll('.glance tr[data-g]').forEach(function(r){
    r.style.cursor = 'pointer';
    r.addEventListener('click', function(ev){
      if (ev.target.closest('a')) return;
      var chip = document.querySelector('.chip[data-k="group"][data-v="' + r.dataset.g + '"]');
      location.hash = 'agents'; if (chip) chip.click();
    });
  });
  window.addEventListener('hashchange', route);
  apply(); route();
})();
"""


def main(argv=None):
    C.utf8_stdout()
    ap = argparse.ArgumentParser(description="Build the focus-swarm HTML board.")
    ap.add_argument("outdir")
    ap.add_argument("--title", default="", help="product name shown on the board")
    ns = ap.parse_args(argv)
    if not os.path.isdir(ns.outdir):
        print("no such directory: %s" % ns.outdir, file=sys.stderr)
        return 1
    build(os.path.abspath(ns.outdir), ns.title)
    return 0


if __name__ == "__main__":
    sys.exit(main())
