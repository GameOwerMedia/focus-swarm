"""Shared helpers for the focus-swarm scripts. Standard library only."""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
REFERENCES = os.path.join(SKILL_DIR, "references")
PANELS_PATH = os.path.join(REFERENCES, "panels.json")
SCHEMA_PATH = os.path.join(REFERENCES, "schema.json")
BRIEF_TEMPLATE_PATH = os.path.join(REFERENCES, "agent-brief.md")

DISPOSITIONS = ("hostile", "skeptical", "neutral", "interested")
VERDICTS = ("yes", "maybe", "no")
ENTRIES = ("YES", "CONDITIONAL", "NO")


def utf8_stdout():
    """Windows consoles default to a legacy code page; force UTF-8 output."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass


def read_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path, data):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def load_library(path=None):
    """Return the panel library: {"panels": [...], "presets": [...]}."""
    return read_json(path or PANELS_PATH, {"panels": [], "presets": []})


def panels_by_id(lib=None):
    lib = lib or load_library()
    return {p["id"]: p for p in lib.get("panels", [])}


def load_run(outdir):
    """Merge run.config.json (what the user picked) with personas.json's run block."""
    run = dict(read_json(os.path.join(outdir, "run.config.json"), {}) or {})
    blob = read_json(os.path.join(outdir, "personas.json"), {}) or {}
    if isinstance(blob, dict):
        for k, v in (blob.get("run") or {}).items():
            run.setdefault(k, v)
    run.setdefault("real_people", [])
    run.setdefault("lang", "en")
    return run


def load_personas(outdir):
    blob = read_json(os.path.join(outdir, "personas.json"), {}) or {}
    if isinstance(blob, list):
        return blob
    return list(blob.get("personas") or [])


def load_reports(outdir):
    """Return (reports, problems). problems lists files that could not be parsed."""
    reports, problems = [], []
    adir = os.path.join(outdir, "agents")
    if not os.path.isdir(adir):
        return reports, problems
    for fn in sorted(os.listdir(adir)):
        if not fn.endswith(".json"):
            continue
        path = os.path.join(adir, fn)
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except (ValueError, OSError) as exc:
            problems.append((fn, "unreadable JSON: %s" % exc))
            continue
        if not isinstance(data, dict):
            problems.append((fn, "top level is not an object"))
            continue
        data.setdefault("id", fn[:-5])
        reports.append(data)
    return reports, problems


def panel_order(run, present_ids):
    """Display order: the run's declared order, then anything else that appeared."""
    order = []
    declared = list(run.get("panel_order") or []) + list((run.get("panels") or {}).keys())
    for g in declared + list(present_ids):
        if g and g not in order and g in present_ids:
            order.append(g)
    return order
