# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-10-25

### Added
- `focus-swarm` skill: one subagent per persona, each visiting a live URL, a
  repository or a document and filing a structured JSON report.
- Panel library with 16 panels, 7 presets and per-panel report blocks.
- Cast picker (`picker.py`): local page, non-interactive `--write` and an
  offline `--static` page.
- `render_prompts.py`: one isolated prompt per persona from a single template,
  with waves and retries.
- `collect.py`: report validation, per-panel roll-up and retry list.
- `build_board.py`: a self-contained HTML board with light and dark themes,
  filters, deep links, rendered synthesis and a deal table.
- Opt-in real-people research for the research, capital and press panels, with
  strict labelling; fictional personas by default. `render_prompts.py` refuses
  and `collect.py` rejects a real-person persona in a panel that was not opted in.
- A demo product site and a complete example run.
- Unit tests and CI on Linux, Windows and macOS.
