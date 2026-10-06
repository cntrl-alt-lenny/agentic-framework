# 01-slim-framework: Worker summary

Release 4.0.0, at the owner's request (2026-10-06, project thread "Tidy the
issue list and state page"). Path: Checked (changes `framework/`, `tools/`
and `templates/`).

## Done

- `framework/`: the core and role cards rewritten around batches; 3,144 words
  became about 1,340. Issue #44's wording folded in; #37's seat-name rule kept.
- `tools/fw.py`: `start`, `report`, `delivery` and `prompt` removed; `status`
  lists unmerged branches by their batch files; `check` warns about batch
  files over 500 words of prose. `tools/adopt.py` seeds `docs/batches/`.
- `templates/`, `adapters/`, `README.md`, `CHANGELOG.md` (4.0.0 with adopter
  steps), `AGENTS.md`, `docs/feedback.md`, `docs/state.md`: batch wording, the
  release freeze lifted, a two-week scorecard.
- Tests: round tests replaced by `tests/test_status.py`.

## Checked

- `python3 -m unittest discover -s tests -t . -v` -> exit 0, `Ran 68 tests`, `OK`
- `ruff check --select F,E9,B,UP --target-version py39 tools templates tests`
  -> exit 0, `All checks passed!`
- `python3 tools/fw.py check` -> exit 0, `0 error(s), 0 warning(s)`
- Each new status test fails against the first reviewed version of `fw.py`.
- `tools/adopt.py <project> --update --dry-run` on fresh clones of
  edopro-next, fire-emblem-awakening-assistant, mgs-mc-modkit,
  edopro-retro-formats and gx-spirit-caller -> exit 0; only framework files
  are replaced, project-owned files kept. A real update of three of them
  passes their `tests/test_framework.py`.

## Not checked

- fe6-next (private) was not dry-run.
- No Python 3.9 interpreter here; 3.9 rests on ruff's py39 rules and CI.

## Failed or blocked

None open. Every project's own `AGENTS.md` still names the removed commands;
adopter step 3 covers it.
