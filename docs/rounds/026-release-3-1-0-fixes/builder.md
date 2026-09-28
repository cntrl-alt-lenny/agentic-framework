<!-- fw-report
round: 026-release-3-1-0-fixes
role: builder
branch: builder/026-release-3-1-0-fixes
head: ba57557b12f88f9c50514ff44b95f298e5f5afba
os: macOS 27.0
python: 3.9.6
written: 2026-09-28T14:26:21Z
-->
# Round 026 — Builder report: release 3.1.0 fixes

All evidence is at commit `248f1928a8b0abe1ba21bb97d0ccd4639892e88d` (branch
`builder/026-release-3-1-0-fixes`, cut by `fw.py start` from Brain's brief
commit `a18f360`, which sits on round 025's reviewed commit `6f2d062`), on
macOS 27.0 with Python 3.9.6, unless stated.

## Verified

- Full suite: `python3 -m unittest discover -s tests -t . -v` → exit 0
  `Ran 83 tests in 188.075s` / `OK` (78 at `6f2d062`; 5 added, 1 changed). This includes every round 025 per-issue test (criterion 4).
- Lint: `ruff check --select F,E9,B,UP --target-version py39 tools templates tests` (ruff 0.16.9, scratch venv) → exit 0, `All checks passed!`
- `python3 tools/fw.py check` in this repository → `0 error(s), 0 warning(s)`.
- CI at `248f192`: `gh run view 36435218763` → `success`; lint, tests on ubuntu/macos/windows × Python 3.9/3.12 and "framework invariants" all `success`.
- Criterion 2, each item's test fails at `6f2d062` and passes at head. Method: a scratch worktree at `6f2d062` with this branch's `tests/*.py` copied over it, so the tests ran against `6f2d062`'s `tools/`. At `6f2d062` → `Ran 17 tests`, `FAILED (failures=5)`; all pass at head:
  - Item 1: `6f2d062`'s own `tests.test_docs` → `FAIL: test_every_documented_command_exists` with `'and' not found in {...}`, naming round 025's `builder.md` and the word `and`. At head it passes with that report unchanged. The new `test_docs.Consistency.test_a_command_is_told_from_prose` pins the rule: the misspelling `prmpt` is caught in eight written forms (in a code span, with flags, after `python3` or `py -3`, wrapped across a line, in a fenced block, before a placeholder or `…`); five prose forms are not flagged, including round 025's sentence and the verifier's quotation of it. Because the rule lives in the test file, this test cannot fail at `6f2d062`'s tools; the failing evidence for item 1 is the suite itself.
  - Item 2: `test_round.Prompts.test_the_header_names_the_repository_not_the_agents_heading` → `AssertionError: 'AGENTS.md — coordination model for demo · ROUND 031 · BUILDER' != 'edopro-retro-formats · ROUND 031 · BUILDER'`.
  - Item 3: `test_fw_checks.ScanScope.test_round_attachments_are_scanned` → `'docs/rounds/001-x/attachments/logs/run.log:2 contains' not found in '0 error(s), 0 warning(s)\n'`. Also the changed `test_the_personal_data_message_says_which_documents_are_scanned` fails there on the old scope text.
  - Item 4: `test_round.Prompts.test_a_re_review_prompt_names_a_new_folder` → `AssertionError: '.worktrees/verifier-032' != '.worktrees/verifier-032-2'`.
  - Item 5: `test_round.NextAction.test_a_tier_0_round_asks_for_a_merge_not_a_judgement` → `'every seat has reported' unexpectedly found in '...next: ask Brain to judge round 023-tiny: every seat has reported\n'`.
- The new command rule finds exactly what the old pattern found in every Markdown file the test reads, except the two prose mentions in round 025's builder and verifier reports (a scratch script compared the two per file).
- Criterion 3: `python3 tools/fw.py --cwd <scratch clone> prompt --round 033-demo --role verifier`, first line, for fresh clones of the three projects (their `AGENTS.md` headings are `AGENTS.md — coordination model for edopro-retro-formats`, `AGENTS.md — edopro-next` and `Yu-Gi-Oh! GX Spirit Caller decomp`):
  - `edopro-retro-formats · ROUND 033 · VERIFIER`
  - `edopro-next · ROUND 033 · VERIFIER`
  - `gx-spirit-caller · ROUND 033 · VERIFIER`
  - This repository: `agentic-framework · ROUND 026 · BUILDER`.
- Item 4 on this repository: `fw.py prompt --round 026-release-3-1-0-fixes --role verifier` names `.worktrees/verifier-026` (no review branch yet).
- Item 7: `docs/state.md` already names both rounds (`rounds 025-release-3-1-0 and 026-release-3-1-0-fixes`) in Brain's brief commit `a18f360`, so this branch does not change it.

## Not verified

- CI for the commit that adds this report. It was not seen when this was written; the Builder watches it after pushing and says what it showed in the final reply.
- The re-review folder on a real project's branches: only the test covers it (no project has a second review in flight).
- A `--message 2` prompt for a seat that already has its folder: still says `git worktree add`, which fails when the folder exists. Not in this brief; see Open questions.

## Changed

- `tools/fw.py`:
  - `project_name`: the repository name from origin's address, without `.git`; else the folder name. No longer reads `AGENTS.md`.
  - New `review_suffix`: a Verifier prompt names `.worktrees/verifier-<number>` for the first review and `-2`, `-3` … for later ones, numbered like the review branches. A review branch with no verifier report yet is the review in progress, so its prompt keeps the same folder.
  - `next_action`: a round with no seats (Tier 0) says `ask Brain to merge round <id>: it is Tier 0, so no seat works on it`.
  - `_live_docs` also reads `docs/rounds/*/attachments/**`, skipping binary files (a NUL byte in the first 8 KiB); `SCANNED` says so.
- `templates/tests/test_framework.py`: docstring names the attachments folder.
- `tests/test_docs.py`: `written_commands` and the rule above; new `test_a_command_is_told_from_prose`.
- `tests/helpers.py`: the test remote is `Demo.git`, so headers keep reading `Demo` now that they come from the repository name.
- `tests/test_round.py`, `tests/test_fw_checks.py`: the four tests named above; the scope message test updated to the new text.
- `docs/state.md`: not changed (see item 7).

## Open questions

- Item 1's rule treats `fw.py <word>` as a command only when it comes after `python3`, `python` or `py -3`, sits in a fenced block, or is followed by a flag, a placeholder, `…` or a closing backtick. A misspelt command written in bare prose with none of those (for example ending a sentence) is not caught. Every command in the current documents has one of these forms.
- Quoting the old failure message inside a code span still counts as a written command, because the word is followed by a closing backtick. My first report commit (`e92cace`) did exactly that and fails the suite; this commit rewords the quote. I left the rule as it is: a code span ending in a command is the commonest way commands are written.
- The resent prompt (`--message 2`) has the same folder clash as item 4 if the seat's folder still exists. The brief limits item 4 to a second review; changing the resend wording is Brain's call.
- The attachments scan reads any non-binary file, not only Markdown, because logs are the likely case.
