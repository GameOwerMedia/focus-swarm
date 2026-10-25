#!/usr/bin/env python3
"""
Check the agent reports after a wave and roll them up.

    python collect.py <outdir> [--json]

Reads   <outdir>/personas.json (or roster.json), <outdir>/agents/*.json
Writes  <outdir>/summary.json
Prints  a per-panel table, then the ids that need a retry.

Exit code 0 when every persona filed a valid report that reached the product,
2 when some need a retry (missing, invalid, or visited: false), 1 on bad input.
Validation is a focused check of the fields the board and the synthesis rely
on, not a full JSON Schema validator, so it needs nothing beyond the standard
library.
"""

import argparse
import json
import os
import sys

import _common as C

REQUIRED = ["id", "group", "visited", "name", "disposition", "first_10s", "usability",
            "works", "fails", "missing", "said", "unsaid", "verdict"]
LISTS = ["works", "fails", "missing", "said", "unsaid"]
DEAL_REQUIRED = ["entry", "ticket", "valuation", "instrument", "conditions", "red_lines",
                 "offers", "wants", "refuses"]
SCIENCE_REQUIRED = ["claims", "novelty", "validity_concerns", "would_cite", "would_collaborate"]


def validate(r, panel, real_people=()):
    """Return a list of human-readable problems with one report.

    real_people is the list of panel ids the user opted in to real-people
    research (run.config.json). A real_person report anywhere else is invalid.
    """
    errs = []
    for k in REQUIRED:
        if k not in r:
            errs.append("missing field '%s'" % k)
    if "visited" in r and not isinstance(r["visited"], bool):
        errs.append("'visited' must be true or false")
    if r.get("visit_method") not in (None, "browser", "http", "files", "document"):
        errs.append("'visit_method' must be browser, http, files or document")
    if r.get("disposition") and r["disposition"] not in C.DISPOSITIONS:
        errs.append("'disposition' must be one of %s" % ", ".join(C.DISPOSITIONS))
    for k in LISTS:
        if k in r and not isinstance(r[k], list):
            errs.append("'%s' must be a list" % k)
    u = r.get("usability")
    if u is not None:
        if not isinstance(u, dict):
            errs.append("'usability' must be an object")
        else:
            s = u.get("score")
            if not isinstance(s, int) or isinstance(s, bool) or not 0 <= s <= 100:
                errs.append("'usability.score' must be an integer 0-100")
            for k in ("blockers", "friction"):
                if not isinstance(u.get(k, []), list):
                    errs.append("'usability.%s' must be a list" % k)
    v = r.get("verdict")
    if v is not None:
        if not isinstance(v, dict) or v.get("decision") not in C.VERDICTS:
            errs.append("'verdict.decision' must be yes, maybe or no")
    block = (panel or {}).get("extra_block") or {}
    if r.get("visited") is not False:
        if block.get("key") == "deal":
            d = r.get("deal")
            if not isinstance(d, dict):
                errs.append("capital report without a 'deal' block")
            else:
                errs += ["deal block missing '%s'" % k for k in DEAL_REQUIRED if k not in d]
                if d.get("entry") not in C.ENTRIES:
                    errs.append("'deal.entry' must be YES, CONDITIONAL or NO")
        elif block.get("key") == "science":
            s = r.get("science")
            if not isinstance(s, dict):
                errs.append("research report without a 'science' block")
            else:
                errs += ["science block missing '%s'" % k for k in SCIENCE_REQUIRED if k not in s]
        elif block.get("fields"):
            got = {str(x.get("key")) for x in (r.get("extra") or []) if isinstance(x, dict)}
            want = [f["key"] for f in block["fields"]]
            miss = [k for k in want if k not in got]
            if miss:
                errs.append("extra block missing fields: %s" % ", ".join(miss))
    if r.get("real_person") and r.get("group") not in (real_people or ()):
        errs.append("real_person is true in panel '%s', which was not opted in to real-people "
                    "research (run.config.json real_people); recast it as a fictional persona"
                    % r.get("group"))
    if r.get("real_person"):
        if len(r.get("sources") or []) < 2:
            errs.append("real-person report needs at least 2 sources")
        for q in r.get("public_record") or []:
            if not (isinstance(q, dict) and q.get("quote") and q.get("url")):
                errs.append("every public_record entry needs a quote and a url")
                break
    return errs


def expected_ids(outdir):
    personas = C.load_personas(outdir)
    if personas:
        return [(p["id"], p.get("group"), p.get("name")) for p in personas if p.get("id")]
    roster = C.read_json(os.path.join(outdir, "roster.json"), []) or []
    return [(r["id"], r.get("group"), r.get("name")) for r in roster]


def collect(outdir):
    lib = C.panels_by_id()
    real_people = C.load_run(outdir).get("real_people") or []
    expected = expected_ids(outdir)
    reports, unreadable = C.load_reports(outdir)
    by_id = {r.get("id"): r for r in reports}

    rows, retry, invalid = [], [], {}
    for fn, why in unreadable:
        invalid[fn[:-5]] = [why]
    for pid, group, name in expected:
        r = by_id.get(pid)
        if r is None:
            if pid not in invalid:
                retry.append(pid)
                rows.append({"id": pid, "group": group, "name": name, "status": "missing"})
            else:
                retry.append(pid)
                rows.append({"id": pid, "group": group, "name": name, "status": "invalid"})
            continue
        errs = validate(dict(r, group=r.get("group") or group), lib.get(r.get("group") or group), real_people)
        if errs:
            invalid[pid] = errs
        if r.get("visited") is False:
            status = "not visited"
            retry.append(pid)
        elif errs:
            status = "invalid"
            retry.append(pid)
        else:
            status = "ok"
        rows.append({"id": pid, "group": r.get("group") or group, "name": r.get("name") or name,
                     "status": status,
                     "verdict": (r.get("verdict") or {}).get("decision"),
                     "usability": (r.get("usability") or {}).get("score"),
                     "completed": bool((r.get("usability") or {}).get("completed_main_task")),
                     "entry": (r.get("deal") or {}).get("entry")})

    extra_reports = sorted(set(by_id) - {e[0] for e in expected})
    ok = [x for x in rows if x["status"] == "ok"]
    panels = {}
    for x in ok:
        g = panels.setdefault(x["group"], {"n": 0, "yes": 0, "maybe": 0, "no": 0,
                                           "completed": 0, "usability": []})
        g["n"] += 1
        if x["verdict"] in ("yes", "maybe", "no"):
            g[x["verdict"]] += 1
        g["completed"] += 1 if x["completed"] else 0
        if isinstance(x["usability"], int):
            g["usability"].append(x["usability"])
    for g in panels.values():
        s = g.pop("usability")
        g["usability_avg"] = round(sum(s) / len(s)) if s else None

    return {
        "expected": len(expected),
        "filed": len(ok),
        "retry": retry,
        "invalid": invalid,
        "unexpected_reports": extra_reports,
        "panels": panels,
        "agents": rows,
    }


def main(argv=None):
    C.utf8_stdout()
    ap = argparse.ArgumentParser(description="Check and roll up focus-swarm agent reports.")
    ap.add_argument("outdir")
    ap.add_argument("--json", action="store_true", help="print the summary as JSON")
    ns = ap.parse_args(argv)
    outdir = os.path.abspath(ns.outdir)
    if not os.path.isdir(outdir):
        print("no such directory: %s" % outdir, file=sys.stderr)
        return 1
    s = collect(outdir)
    if not s["expected"]:
        print("no personas found in personas.json or roster.json", file=sys.stderr)
        return 1
    C.write_json(os.path.join(outdir, "summary.json"), s)
    if ns.json:
        print(json.dumps(s, ensure_ascii=False, indent=2))
    else:
        print("%d of %d reports filed and valid" % (s["filed"], s["expected"]))
        print("%-22s %4s %4s %6s %4s %10s %8s" % ("panel", "n", "yes", "maybe", "no", "completed", "usab."))
        for g, v in s["panels"].items():
            print("%-22s %4d %4d %6d %4d %10d %8s" % (g, v["n"], v["yes"], v["maybe"], v["no"],
                                                     v["completed"], v["usability_avg"]))
        for pid, errs in s["invalid"].items():
            print("invalid  %s: %s" % (pid, "; ".join(errs)))
        if s["unexpected_reports"]:
            print("reports with no matching persona: %s" % ", ".join(s["unexpected_reports"]))
        if s["retry"]:
            print("retry: %s" % ",".join(s["retry"]))
    return 2 if s["retry"] else 0


if __name__ == "__main__":
    sys.exit(main())
