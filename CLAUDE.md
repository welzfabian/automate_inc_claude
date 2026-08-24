# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
./start_game.sh                  # play; creates .venv/ and installs on first run
pytest                           # all tests (pyproject sets pythonpath=["src"])
pytest tests/test_turn.py::test_bankruptcy_ends_the_game    # a single test
PYTHONPATH=src python3 -m automate_inc                      # run without the launcher
```

`ruff` is configured in `pyproject.toml` but is not installed in the environment, so
linting has never actually run. Install it with `pip install -e ".[dev]"` before
claiming a change is lint-clean. There is no CI.

## Language convention

Player-facing text is **German**, code identifiers, comments and commit messages are
**English**. Every German string belongs in `src/automate_inc/strings.py` — it sits at
package root, not under `ui/`, because `core` produces player messages too and must not
depend on the UI layer.

## Architecture

**`core/` never renders and never reads input.** Every player action returns an
`ActionResult(ok, message)`; every turn returns a `TurnReport`. The UI only renders
those. This is deliberate: the planned AI takeover (see `docs/VISION.md`) hooks into
that seam so the AI can intercept, block or fake an action's result without the UI
knowing. Do not let `core` import `rich` or call `input()`, and do not move game logic
into `ui/`.

**Actions validate before they mutate.** A failed action must leave the state byte-identical
(`test_failed_action_leaves_state_untouched` enforces this). That is what will later make
"genuinely blocked" distinguishable from "the AI lied to you".

**Randomness is derived, never carried.** `Game._turn_rng()` builds a fresh
`random.Random(f"{seed}:{turn}")` each turn. No module may call `random.*` at module
level. This is why a loaded save resolves the next turn exactly as the original run
would have — do not replace it with a live generator.

**`resolve_turn()` has a fixed step order** (worker effects → side effects → income →
costs → settle → token price → project lifecycle → phase → end conditions). Each step is
its own private method. Reordering changes the balance.

**Endings extend `END_CONDITIONS`** in `core/game.py` — a list of `EndCondition`. It holds
bankruptcy and misalignment; the twist endings are meant to be appended, not special-cased.

**Technologies never appear in engine code.** `core/tech.py` aggregates everything
researched into one `Modifiers` value object, and the rest of the engine asks that object
questions instead of checking technology IDs. A new technology that reuses an existing
modifier field is pure configuration in `data/technologies.json`; a new field needs an
entry in the `AGGREGATION` table (max / multiplicative / additive) and nothing else.

**Alignment is deterministic.** `economy.alignment_delta()` derives it from agent levels,
human headcount and research — no RNG (`BALANCING.md` 8). The player has to be able to
read the balance before deciding, which is why the dashboard shows it as `(±n/Runde)`.

## Balancing data is not in code

All tunable numbers live in `src/automate_inc/data/*.json` (`projects.json`,
`roles.json`). Adding a project or changing a cost must not require a code change.

**The spec documents in `docs/` are the original design, not the current truth.** Their
numbers made every staffing option run at a loss, and their income formula zeroed any
project without a designer. `docs/BALANCING.md` records all six deviations and why.
When docs and `data/*.json` disagree, the JSON wins — and any new deviation goes into
`BALANCING.md`.

Two rules there are easy to break by accident:
- **Humans have `effective_level == 2`**, so a project can be started at all on turn 0.
- **Attributes a project never required are neutral** (factor 1.0) in the income
  formula, not zero.

## Process

`docs/milestones/` holds one document per milestone. Create the file when planning a
milestone (status "in Arbeit"), complete it when the milestone closes. It is a
chronicle: it links to the specs and `BALANCING.md` rather than restating rules.

Bump `SAVE_FORMAT_VERSION` in `core/state.py` whenever `GameState` gains or loses a
serialised field — `from_dict` rejects unknown versions on purpose.
