"""Tests for the focus-swarm scripts. Standard library only: python -m unittest discover -s tests"""

import json
import os
import re
import shutil
import sys
import tempfile
import threading
import unittest
import urllib.request
from contextlib import redirect_stdout
from io import StringIO

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "skills", "focus-swarm")
SCRIPTS = os.path.join(SKILL, "scripts")
FIXTURE = os.path.join(ROOT, "tests", "fixtures", "run")
sys.path.insert(0, SCRIPTS)

import _common as C  # noqa: E402
import build_board  # noqa: E402
import collect  # noqa: E402
import picker  # noqa: E402
import render_prompts  # noqa: E402


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def quiet(fn, *a, **kw):
    with redirect_stdout(StringIO()):
        return fn(*a, **kw)


class RunDir(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="focus-swarm-test-")
        self.run = os.path.join(self.tmp, "run")
        shutil.copytree(FIXTURE, self.run)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


class TestLibrary(unittest.TestCase):
    def test_panels_are_consistent(self):
        lib = C.load_library()
        ids = [p["id"] for p in lib["panels"]]
        self.assertEqual(len(ids), len(set(ids)), "duplicate panel ids")
        self.assertEqual(len(ids), 16)
        fams = {f["id"] for f in lib["families"]}
        for p in lib["panels"]:
            self.assertRegex(p["id"], r"^[a-z][a-z0-9_]{1,13}$")
            self.assertRegex(p["accent"], r"^#[0-9a-f]{6}$")
            self.assertIn(p["family"], fams)
            for k in ("label", "question", "size", "min_hostile", "min_skeptical", "can_cast_real_people", "sees_brief"):
                self.assertIn(k, p, "%s lacks %s" % (p["id"], k))
            self.assertTrue(p.get("seats") or p.get("spread"), p["id"])
            blk = p.get("extra_block")
            if blk and blk["key"] not in ("deal", "science"):
                self.assertTrue(blk["fields"], p["id"])
                for f in blk["fields"]:
                    self.assertIn(f["type"], ("int", "string", "list", "bool"))
        for preset in lib["presets"]:
            for pid in preset["panels"]:
                self.assertIn(pid, ids, "preset %s uses unknown panel %s" % (preset["id"], pid))

    def test_only_research_capital_press_can_be_real(self):
        lib = C.load_library()
        real = sorted(p["id"] for p in lib["panels"] if p["can_cast_real_people"])
        self.assertEqual(real, ["capital", "press", "research"])

    def test_schema_is_valid_json_with_defs(self):
        s = C.read_json(C.SCHEMA_PATH)
        self.assertIn("AgentReport", s["$defs"])
        self.assertIn("visit_method", s["$defs"]["AgentReport"]["required"])

    def test_template_markers_present(self):
        tpl = render_prompts.load_template()
        self.assertIn("{{persona_card}}", tpl)
        self.assertIn("{{report_path}}", tpl)


class TestRender(unittest.TestCase):
    def test_sections_and_vars(self):
        tpl = "A{{#x}} X={{v}}{{/x}}{{^x}} notx{{/x}} B{{#y}} Y{{/y}}"
        self.assertEqual(render_prompts.render(tpl, {"x": True, "v": 1}).strip(), "A X=1 B")
        self.assertEqual(render_prompts.render(tpl, {"x": False, "y": "1"}).strip(), "A notx B Y")


class TestRenderPrompts(RunDir):
    def test_one_prompt_per_persona_and_isolation(self):
        quiet(render_prompts.main, [self.run, "--wave-size", "2"])
        roster = C.read_json(os.path.join(self.run, "roster.json"))
        self.assertEqual([r["id"] for r in roster], ["general01", "consumers01", "capital01"])
        self.assertEqual([r["wave"] for r in roster], [1, 1, 2])
        self.assertEqual(roster[0]["prompt"], "prompts/general01.md", "roster paths stay relative and portable")
        self.assertEqual(roster[0]["report"], "agents/general01.json")
        names = {"general01": "Ada Example", "consumers01": "Ben Sample", "capital01": "Cleo Placeholder"}
        for pid, name in names.items():
            with open(os.path.join(self.run, "prompts", pid + ".md"), encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn(name, text)
            self.assertIn("https://example.com/", text)
            self.assertIn(pid + ".json", text)
            self.assertNotIn("{{", text)
            for other, oname in names.items():
                if other != pid:
                    self.assertNotIn(oname, text, "prompt for %s leaks %s" % (pid, other))
            self.assertIn("Check the sign-up flow on a phone.", text)
            self.assertIn('Set "real_person" to false', text)

    def test_panel_blocks(self):
        with open(os.path.join(self.run, "brief.md"), "w", encoding="utf-8") as fh:
            fh.write("recon")
        quiet(render_prompts.main, [self.run])
        p = lambda pid: read(os.path.join(self.run, "prompts", pid + ".md"))
        self.assertIn('The "deal" block', p("capital01"))
        self.assertIn("brief.md", p("capital01"))  # capital arrives informed
        self.assertNotIn("brief.md", p("general01"))  # users arrive cold
        self.assertIn("arrive cold", p("general01"))
        self.assertIn('"walk_away_price"', p("consumers01"))
        self.assertNotIn('The "deal" block', p("general01"))

    def test_real_person_rules_only_when_opted_in(self):
        blob = C.read_json(os.path.join(self.run, "personas.json"))
        blob["personas"][2].update({"real_person": True, "sources": ["https://example.org/a", "https://example.org/b"]})
        C.write_json(os.path.join(self.run, "personas.json"), blob)
        with self.assertRaises(SystemExit):  # panel not opted in: refuse to render
            quiet(render_prompts.main, [self.run])
        self.assertFalse(os.path.exists(os.path.join(self.run, "prompts", "capital01.md")))
        cfg = C.read_json(os.path.join(self.run, "run.config.json"))
        cfg["real_people"] = ["capital"]
        C.write_json(os.path.join(self.run, "run.config.json"), cfg)
        quiet(render_prompts.main, [self.run])
        text = read(os.path.join(self.run, "prompts", "capital01.md"))
        self.assertIn("simulating a real, named person", text)

    def test_retry_prompt(self):
        quiet(render_prompts.main, [self.run, "--retry", "general01"])
        text = read(os.path.join(self.run, "prompts", "general01.retry.md"))
        self.assertIn("Second attempt", text)

    def test_refuses_without_target(self):
        cfg = C.read_json(os.path.join(self.run, "run.config.json"))
        cfg["target"] = ""
        C.write_json(os.path.join(self.run, "run.config.json"), cfg)
        blob = C.read_json(os.path.join(self.run, "personas.json"))
        blob["run"]["target"] = ""
        C.write_json(os.path.join(self.run, "personas.json"), blob)
        with self.assertRaises(SystemExit):
            quiet(render_prompts.main, [self.run])


class TestCollect(RunDir):
    def test_flags_incomplete_extra_block(self):
        s = collect.collect(self.run)
        self.assertEqual(s["expected"], 3)
        self.assertEqual(s["retry"], ["consumers01"])
        self.assertTrue(any("extra block missing" in x for x in s["invalid"]["consumers01"]))
        self.assertEqual(s["panels"]["capital"]["no"], 1)

    def test_missing_and_not_visited(self):
        os.remove(os.path.join(self.run, "agents", "general01.json"))
        r = C.read_json(os.path.join(self.run, "agents", "capital01.json"))
        r["visited"] = False
        C.write_json(os.path.join(self.run, "agents", "capital01.json"), r)
        s = collect.collect(self.run)
        self.assertIn("general01", s["retry"])
        self.assertIn("capital01", s["retry"])

    def test_exit_codes(self):
        self.assertEqual(quiet(collect.main, [self.run]), 2)
        r = C.read_json(os.path.join(self.run, "agents", "consumers01.json"))
        fields = C.panels_by_id()["consumers"]["extra_block"]["fields"]
        r["extra"] = [{"key": f["key"], "label": f["label"], "type": "text", "value": "x"} for f in fields]
        C.write_json(os.path.join(self.run, "agents", "consumers01.json"), r)
        self.assertEqual(quiet(collect.main, [self.run]), 0)
        self.assertTrue(os.path.exists(os.path.join(self.run, "summary.json")))

    def test_validate_catches_bad_types(self):
        errs = collect.validate({"id": "x", "group": "general", "visited": "yes", "usability": {"score": 140},
                                 "verdict": {"decision": "perhaps"}}, {})
        joined = " ".join(errs)
        self.assertIn("visited", joined)
        self.assertIn("usability.score", joined)
        self.assertIn("verdict.decision", joined)

    def test_real_person_outside_opted_in_panel_is_invalid(self):
        r = C.read_json(os.path.join(self.run, "agents", "capital01.json"))
        r.update({"real_person": True, "sources": ["https://example.org/a", "https://example.org/b"]})
        C.write_json(os.path.join(self.run, "agents", "capital01.json"), r)
        s = collect.collect(self.run)
        self.assertIn("capital01", s["retry"])
        self.assertTrue(any("not opted in" in x for x in s["invalid"]["capital01"]))
        cfg = C.read_json(os.path.join(self.run, "run.config.json"))
        cfg["real_people"] = ["capital"]
        C.write_json(os.path.join(self.run, "run.config.json"), cfg)
        s = collect.collect(self.run)
        self.assertNotIn("capital01", s["retry"])


class TestBoard(RunDir):
    def build(self):
        quiet(build_board.build, self.run)
        with open(os.path.join(self.run, "index.html"), encoding="utf-8") as fh:
            return fh.read()

    def test_board_is_self_contained(self):
        doc = self.build()
        self.assertNotRegex(doc, r'<(script|link|img)[^>]+(src|href)="https?://')
        self.assertNotIn("@import", doc)
        self.assertNotRegex(doc, r"fetch\(")

    def test_board_content(self):
        doc = self.build()
        for name in ("Ada Example", "Ben Sample", "Cleo Placeholder"):
            self.assertIn(name, doc)
        self.assertIn('id="agent-capital01"', doc)
        self.assertIn("Deal table", doc)
        self.assertIn("Fictional personas", doc)
        self.assertIn("Ranked action plan", doc)
        self.assertIn('href="#agent-general01"', doc)  # ids in the synthesis become links
        self.assertTrue(os.path.exists(os.path.join(self.run, "README.md")))

    def test_board_escapes_agent_text(self):
        doc = self.build()
        self.assertNotIn("<script>alert(1)</script>", doc)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", doc)

    def test_real_people_banner(self):
        r = C.read_json(os.path.join(self.run, "agents", "capital01.json"))
        r.update({"real_person": True, "sources": ["https://example.org/a", "https://example.org/b"],
                  "public_record": [{"quote": "Retention is everything.", "url": "https://example.org/a"}]})
        C.write_json(os.path.join(self.run, "agents", "capital01.json"), r)
        doc = self.build()
        self.assertIn("Internal simulation of real people", doc)
        self.assertIn("Retention is everything.", doc)

    def test_board_without_report_or_agents(self):
        os.remove(os.path.join(self.run, "report.md"))
        shutil.rmtree(os.path.join(self.run, "agents"))
        doc = self.build()
        self.assertIn("No reports found", doc)

    def test_markdown_renderer(self):
        html = build_board.md("# T\n\n- a\n  - b\n- c\n\n1. one\n2. two\n\n> quote\n\n`code` **bold** [x](https://example.com)")
        self.assertIn("<h2", html)
        self.assertEqual(html.count("<ul>"), 2)
        self.assertIn("<ol>", html)
        self.assertIn("<blockquote>", html)
        self.assertIn('<a href="https://example.com"', html)
        self.assertNotIn("javascript:", build_board.md("[x](javascript:alert(1))").replace("[x](javascript:alert(1))", ""))


class TestPicker(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="focus-swarm-picker-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_write_preset(self):
        quiet(picker.main, ["--outdir", self.tmp, "--target", "https://example.com/", "--preset", "lite", "--write"])
        cfg = C.read_json(os.path.join(self.tmp, "run.config.json"))
        self.assertEqual(sum(cfg["panels"].values()), 15)
        self.assertEqual(cfg["mode"], "lite")
        self.assertEqual(cfg["real_people"], [])

    def test_write_panels_and_real_people_guard(self):
        quiet(picker.main, ["--outdir", self.tmp, "--target", "x", "--panels", "general=2,capital=3",
                            "--real-people", "capital", "--write"])
        cfg = C.read_json(os.path.join(self.tmp, "run.config.json"))
        self.assertEqual(cfg["panels"], {"general": 2, "capital": 3})
        self.assertEqual(cfg["real_people"], ["capital"])
        with self.assertRaises(SystemExit):
            quiet(picker.main, ["--outdir", self.tmp, "--target", "x", "--panels", "general=2",
                                "--real-people", "general", "--write"])

    def test_static_page(self):
        quiet(picker.main, ["--outdir", self.tmp, "--target", "https://example.com/", "--static"])
        with open(os.path.join(self.tmp, "picker.html"), encoding="utf-8") as fh:
            page = fh.read()
        self.assertIn("Run the swarm", page)
        self.assertNotRegex(page, r'<(script|link)[^>]+(src|href)="https?://')

    def test_server_round_trip(self):
        lib = C.load_library()
        picker.Handler.page = picker.render({"target": "https://example.com/", "target_type": "live",
                                             "product": "Acme </script><b>"}, lib).encode("utf-8")
        self.assertNotIn(b"Acme </script>", picker.Handler.page)
        picker.Handler.outdir = self.tmp
        picker.Handler.lib = lib
        srv = picker.ThreadingHTTPServer(("127.0.0.1", 0), picker.Handler)
        picker.Handler.on_saved = srv.shutdown
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        base = "http://127.0.0.1:%d" % srv.server_address[1]
        try:
            with urllib.request.urlopen(base + "/") as r:
                self.assertIn(b"Cast picker", r.read())
            bad = urllib.request.Request(base + "/run", data=b'{"panels":{"nope":1}}',
                                         headers={"Content-Type": "application/json"})
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                with redirect_stdout(StringIO()):
                    urllib.request.urlopen(bad)
            self.assertEqual(ctx.exception.code, 400)
            ctx.exception.close()
            body = json.dumps({"target": "https://example.com/", "panels": {"general": 3}}).encode()
            req = urllib.request.Request(base + "/run", data=body, headers={"Content-Type": "application/json"})
            with redirect_stdout(StringIO()):
                with urllib.request.urlopen(req) as r:
                    self.assertEqual(json.loads(r.read())["ok"], True)
        finally:
            t.join(timeout=5)
            srv.server_close()
        self.assertEqual(C.read_json(os.path.join(self.tmp, "run.config.json"))["panels"], {"general": 3})


class TestRepoHygiene(unittest.TestCase):
    def test_skill_frontmatter(self):
        with open(os.path.join(SKILL, "SKILL.md"), encoding="utf-8") as fh:
            text = fh.read()
        m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        self.assertTrue(m)
        self.assertRegex(m.group(1), r"(?m)^name: focus-swarm$")
        self.assertIn("description:", m.group(1))

    def test_plugin_manifests_agree(self):
        plugin = C.read_json(os.path.join(ROOT, ".claude-plugin", "plugin.json"))
        market = C.read_json(os.path.join(ROOT, ".claude-plugin", "marketplace.json"))
        self.assertEqual(plugin["name"], "focus-swarm")
        self.assertIn("focus-swarm", [p["name"] for p in market["plugins"]])


if __name__ == "__main__":
    unittest.main()
