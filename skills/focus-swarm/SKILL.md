---
name: focus-swarm
description: >
  Evaluate a real product with a swarm of independent persona agents. You pick a
  cast from 16 panels (everyday users, commercial users, consumers, marketing,
  advertising, retail, B2B buyers, enterprise IT, regulators, education,
  researchers, investors, press, creators, community, talent) in a local cast
  picker; then one subagent per persona visits the actual product (a live URL, a
  repository or a document) on its own, never sees the others, and files a
  structured JSON report with usability, what they said, what they did not say,
  and the panel's own verdict block (deal terms, claim validity, price,
  positioning, legal exposure). Output: an offline HTML board, a markdown
  synthesis and the raw JSON. Use when the user types /focus-swarm, asks for a
  swarm, a panel of agents or a persona test against a live site, repo or
  document, or wants independent reviews before a launch, raise, press push or
  pitch. `/focus-swarm lite` runs a 15-agent preset without the picker.
argument-hint: "[target] [lite|full|<preset>]"
---

# focus-swarm

You are the director of an evaluation swarm, usually 10 to 40 agents. Unlike a
single-context focus group, where one model voices every persona in turn, here
**every persona is a separate subagent with its own context**. They never see
each other's answers. That is the point: no drift toward consensus, no single
voice bleeding through every review, and real contradictions you did not plan.

The swarm evaluates a **real product**, not a description of one.

`<skill-dir>` below is the folder that holds this SKILL.md (Claude Code shows
it as the skill's base directory when the skill loads; for a plugin install it
is `${CLAUDE_PLUGIN_ROOT}/skills/focus-swarm`). `references/...` paths are
inside it. The session's working directory is the user's project, so always
call the scripts by their full path (quoted if it contains spaces). Scripts need Python 3.9+ and nothing
else: use `python3` on macOS and Linux, `python` or `py` on Windows.

---

## Phase 0: target

Find a concrete target in the conversation:

| Type | What it looks like | How agents reach it |
|---|---|---|
| `live` | a URL | browser tools if the session has them (Playwright MCP, a browser extension), otherwise WebFetch or curl |
| `repo` | a directory | Read, Grep, Glob, and running it when it is runnable |
| `document` | a deck, PDF, HTML export, spec | Read |

**No target, no swarm.** Do not invent one and do not evaluate from the
conversation. Reply with: "focus-swarm evaluates a real product, not a
description. Give me a URL, a repository path or a file." and stop.

If the URL is unreachable (dead host, login wall, 403), say so and ask whether
to use a local build, a staging URL or test credentials. Never fall back to
imagination: a swarm reporting on a page it never loaded is worse than no
swarm.

Pick a run folder, by default `./focus-swarm-runs/<product-slug>-<YYYY-MM-DD>/`
in the current project, and create `agents/` inside it.

## Phase 1: the cast picker

The user composes the cast before the swarm runs. Do not decide it for them.

```bash
python3 <skill-dir>/scripts/picker.py --outdir <run> --target "<target>" \
       --targettype live --product "<name>" --port 8137
```

Run it in the background and give the user the printed URL (add `--open` to
open their default browser). The page offers the whole panel library from
`references/panels.json`, seven ready-made casts, a headcount stepper per panel,
an opt-in switch for real-people research on the panels that allow it, a report
language and a notes field. When the user presses **Run the swarm**, the server
writes `<run>/run.config.json` and stops.

Wait for that file, then read it: `panels` (id to headcount), `panel_order`,
`real_people` (panel ids, usually empty), `lang`, `notes`, `target`,
`target_type`. Everything downstream follows it.

Shortcuts that skip the page:

- `/focus-swarm <target> lite` or `full` or any preset id: write the config
  directly with `python3 <skill-dir>/scripts/picker.py ... --preset lite --write`.
- The user names panels in the prompt ("consumers and marketing, 6 each"): use
  `--panels consumers=6,marketing=6 --write`, state the cast in one line, run.
- No local server possible: `--static` writes `picker.html`, which downloads
  `run.config.json` when the user presses Run.

If a `run.config.json` already exists in the folder, offer to reuse it.

## Phase 2: recon

One pass, by you or one subagent, before casting. Write `<run>/brief.md`
(about 400 words): what the product is, what it claims, what it actually does,
main screens or sections, pricing and access, apparent stage, audience, tech
and business model, domain vocabulary, and anything broken.

The brief exists to cast the swarm correctly, not to pre-chew opinions. Only
panels with `sees_brief: true` in `panels.json` (researchers, capital, press:
people who would really arrive informed) get its path. User-side agents arrive
cold, like real visitors.

## Phase 3: casting

Read the entries for the selected panels in `references/panels.json`, then
`references/casting.md` for the spread rules. Write `<run>/personas.json`
matching `references/schema.json`: `{ "run": {...}, "personas": [...] }`, ids
like `general01`, `capital03`. Cast to each panel's seats, spread rules and
disposition floors (`min_hostile`, `min_skeptical`).

**Personas are fictional by default.** They are built from category research
but do not portray identifiable people, and fictional investors, researchers
and journalists sit at invented organisations.

**Real-people research is opt-in** and only for panels listed in
`run.config.json` under `real_people`. Then follow the protocol in
`references/casting.md` exactly: public professional sources only, at least two
source links per person, verbatim quotes only in `public_record`, simulated
speech clearly labelled, drop anyone without a solid public record, and mark
the package internal. Run that research in parallel subagents.

## Phase 4: the swarm

Render one prompt per persona:

```bash
python3 <skill-dir>/scripts/render_prompts.py <run> --wave-size 8
```

This writes `<run>/prompts/<id>.md` (the persona's own card, the target, how to
visit it, the output contract and its panel block, from the template in
`references/agent-brief.md`) and `<run>/roster.json` with wave numbers.

Then start **one subagent per persona with the Agent tool**, a whole wave in a
single message so they run in parallel:

```
Agent(description: "<id> <name>",
      subagent_type: "general-purpose",
      prompt: "Read <run>/prompts/<id>.md and do exactly what it says.")
```

- Use an agent type that can reach the target: for `live`, one with browser or
  web-fetch tools; for `repo`, one that can read files and run commands.
- A cheaper model (`model: "sonnet"`) is a sensible default for persona agents;
  keep the synthesis on the strongest model available.
- Several agents sharing one browser can fight over tabs. If the session has a
  single shared browser, keep waves small or let agents fall back to HTTP
  fetches; each report records its `visit_method`.
- Do not pass anything else to the agents: not the brief (the prompt already
  says whether they may read it), not the other personas, not your opinion.

Each agent writes `<run>/agents/<id>.json` and returns one line. After each
wave, and once at the end:

```bash
python3 <skill-dir>/scripts/collect.py <run>
```

It validates every report (required fields, the panel's block, the real-person
rules), prints a per-panel table and the ids that need a retry: missing,
invalid, or `visited: false`. Retry those once:

```bash
python3 <skill-dir>/scripts/render_prompts.py <run> --retry id1,id2
```

and start one agent per `<run>/prompts/<id>.retry.md`. Anyone still failing is
dropped from the synthesis and listed as a gap. Report progress as a plain
status line per wave ("Wave 2 of 3: 8 of 8 filed"), and say once up front how
long a cast of that size takes.

## Phase 5: synthesis

Read `references/synthesis.md`, then every agent JSON. Write `<run>/report.md`:
the banner, one section per panel that actually ran (in `panel_order`), the
capital and research sections when those ran, the cross-group section with the
ranked action plan and the power move, gaps, and the outreach list only when
real-people research was on. Name agents by id and name so the board can link
them.

## Phase 6: the board

```bash
python3 <skill-dir>/scripts/build_board.py <run> --title "<product>"
```

This writes `<run>/index.html`: one self-contained file that works offline and
from disk, in light and dark themes, with an overview (panels at a glance,
action plan, what people said and did not say), filterable agent cards, the
rendered synthesis and a deal table when capital ran. It also writes a package
`README.md` with the disclaimer if none exists. Deep links:
`index.html#agent-<id>`, `#synthesis`, `#deals`.

Tell the user where the board is and give a one-paragraph summary in the
conversation: the completion rate, the verdict split, the top three actions.

Final layout:

```
<run>/
  index.html        the board, open this
  report.md         the synthesis
  brief.md          recon notes
  run.config.json   the cast the user picked
  personas.json     the cast as built
  prompts/*.md      what each agent was told
  agents/*.json     one raw report per agent
  summary.json      collect.py roll-up
  README.md         what this is, with the disclaimer
```

---

## Rules for every phase

- **Language.** Report and board follow `lang` (English by default). Personas
  speak in their own register and, where natural, their own language. A
  seed investor in Seoul and a teenager in a small town do not sound alike;
  flattening them is the failure this skill exists to avoid.
- **No comfort.** If 30 of 42 would bounce, say 30 and name them.
- **Disposition spread is enforced, not hoped for.** Cast to the floors in
  `panels.json`, then check the returned reports. An all-friendly room is a
  casting bug.
- **Contradictions survive.** Do not resolve a real split into a bland middle.
  Name both sides and say which one you would follow and why.
- **Simulation, labelled.** Every artifact says that personas and their words
  are simulations. Real-people runs are internal and say so on every page.
- **Cost honesty.** The picker shows the headcount. Do not renegotiate it
  afterwards.

## Relationship to focus

| Skill | Cast | Context | Visits the product | Use when |
|---|---|---|---|---|
| `focus lite` | 3 + 3 | one | no | a 30-second sanity check of an idea |
| `focus` | 10 + 10 | one | no | concept, positioning and pitch pressure test |
| `focus-swarm lite` | 15 agents | one per persona | **yes** | there is a build and you want signal fast |
| `focus-swarm` | any cast | one per persona | **yes** | before a launch, a raise, a press push or a pitch |

## Files

- `references/panels.json`: the panel library (16 panels, 7 presets)
- `references/casting.md`: spread rules and the real-people protocol
- `references/agent-brief.md`: the prompt template every agent receives
- `references/synthesis.md`: report structure and banner texts
- `references/schema.json`: persona and report shapes
- `scripts/picker.py`: the cast picker, writes `run.config.json`
- `scripts/render_prompts.py`: one prompt per persona, plus retries
- `scripts/collect.py`: validation, roll-up, retry list
- `scripts/build_board.py`: the HTML board
