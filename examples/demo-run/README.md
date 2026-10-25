# focus-swarm run: Larder

> Fictional personas. Every persona in this run is fictional. They were built from category research and do not portray specific, identifiable people. Their reactions are simulations by independent model agents, not research data.

A complete recorded run of focus-swarm against the fictional
[Larder demo site](../demo-site/): 15 agents in 6 panels.

- Everyday users: 4
- Commercial users 16-49: 2
- Consumers: 3
- Regulators and counsel: 2
- Press and critics: 1
- Capital: 3

The cast was composed in the picker; the persona agents ran on a mid-size
model in two waves. No interactive browser was available, so `tools-note.md`
told every agent to fetch pages over HTTP and look at the pre-rendered
screenshots in `site-shots/`; every report records `visit_method: http`.

One difference from what the agents saw: during the run, `styles.css` in the
demo site carried two comments naming the deliberate flaws (a header and an
inline note on the low-contrast colour), and one agent (regulators01) read
them. Both were moved to
[`../demo-site/README.md`](../demo-site/README.md) after the run, so the
shipped site no longer gives the answers away. Nothing else in the site changed.

In `prompts/`, `<run>` stands for this folder and `<skill>` for
`skills/focus-swarm`; a real run writes absolute paths there.

```
index.html       the board, open it in any browser
report.md        the synthesis
brief.md         recon notes
run.config.json  the cast as picked
personas.json    the cast as built
prompts/*.md     what each agent was told
agents/*.json    one raw report per agent
roster.json      ids, prompt files and waves
summary.json     the collect.py roll-up
tools-note.md    the extra visiting instructions for this run
site-shots/      desktop and phone screenshots of the demo site
```

Rebuild the board from the raw files:

```bash
python skills/focus-swarm/scripts/collect.py examples/demo-run
python skills/focus-swarm/scripts/build_board.py examples/demo-run --title Larder
```
