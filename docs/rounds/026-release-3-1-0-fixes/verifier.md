<!-- fw-report
round: 026-release-3-1-0-fixes
role: verifier
branch: verifier/026-release-3-1-0-fixes
head: 46bc2476ec81a6b6b31aaa7c45946bd6957db725
os: macOS 27.0
python: 3.9.6
written: 2026-09-28T14:39:59Z
-->
# Round 026 — Verifier report: release 3.1.0 fixes

Reviewed commit: `46bc2476ec81a6b6b31aaa7c45946bd6957db725`
(`origin/builder/026-release-3-1-0-fixes`), macOS 27.0, Python 3.9.6.
Commands I ran myself:

- `python3 tools/fw.py start --role verifier --round 026-release-3-1-0-fixes` → exit 0, reviewing `46bc2476ec81`.
- `python3 -m unittest discover -s tests -t .` → `Ran 83 tests in 176.386s`, `OK`.
- `python3 -m ruff check --select F,E9,B,UP --target-version py39 tools templates tests` → exit 0, `All checks passed!`
- `python3 tools/fw.py check` → exit 0, `0 error(s), 0 warning(s)`.
- A scratch worktree at `6f2d062`, `6f2d062`'s own `tests/test_docs.py` → `FAIL: test_every_documented_command_exists`, `'and' not found in {...}` naming round 025's `builder.md` (`FAILED (failures=1)`).
- Same worktree with the reviewed commit's `tests/*.py` copied in, running the new and changed tests for items 1–5 (7 tests) → `FAILED (failures=5)`: `test_round_attachments_are_scanned`, `test_the_personal_data_message_says_which_documents_are_scanned`, `test_a_tier_0_round_asks_for_a_merge_not_a_judgement`, `test_the_header_names_the_repository_not_the_agents_heading`, `test_a_re_review_prompt_names_a_new_folder`. The two item 1 tests pass there, as they must: item 1's rule lives in the test file.
- The prompt command against fresh clones of the three projects (round `099-x`, role verifier), first lines: `edopro-retro-formats · ROUND 099 · VERIFIER`, `edopro-next · ROUND 099 · VERIFIER`, `gx-spirit-caller · ROUND 099 · VERIFIER`; each names `.worktrees/verifier-099`. In this repository: `agentic-framework · ROUND 026 · VERIFIER`.
- A scratch script comparing the old pattern with `written_commands` on every Markdown file the test reads: the only differences are the prose `and` in round 025's builder and verifier reports.
- `gh run list` / `gh run view` on the builder branch: run `36435981721` at `46bc247` → `success`, all 8 jobs (lint, tests on ubuntu/macos/windows × 3.9/3.12, framework invariants). Run `36435933115` at `e92cace` → `failure` (the Builder's first report quoted the old error message; see findings). Run `36435218763` at `248f192` → `success`.

Acceptance criteria: 1 met (suite and CI green at the reviewed commit, which is the commit adding the Builder's report). 2 met, with item 1's failing evidence being the suite itself. 3 met. 4 met (the full suite, which holds round 025's tests, passes). Items 1–5 and 7 are done; item 7's line was changed in Brain's brief commit `a18f360`, which is in this range. Item 6: the Builder's report says plainly that CI for its report commit was not seen; I saw it green.

## Findings

- [NOTE] `tests/test_docs.py:39` — the command rule is a heuristic with two known gaps. A misspelt command in bare prose is not caught (`Run fw.py prmpt to list.` gives `[]`), and a code span that ends with an ordinary word after `fw.py` still counts as a command. The second one already fired once in this round (CI failure at `e92cace`). It fails safe (a red suite, not a missed error), and both gaps are in the Builder's open questions.
- [NOTE] `tools/fw.py:969` — `review_suffix` numbers the folder from the refs this clone already has; the prompt command does not fetch. If Brain prints a re-review prompt without fetching after the first review reported, it gets the old folder name and the clash of item 4 returns. In the normal flow Brain has run status or delivery (which fetch) first.
- [NOTE] `tools/fw.py:1391` — the binary test reads each whole file to look at its first 8 KiB, and a UTF-16 log (common from Windows tools) contains NUL bytes, so it is skipped as binary and not scanned.
- [NOTE] A resent prompt (`--message 2`) still names a folder that already exists. Outside this brief; the Builder lists it too.

## Not verified

- CI for the commit that adds this report: not seen when this was written.
- A real second review on a project: only the test covers `review_suffix`.
- Windows behaviour of `project_name` with a local-path origin: only CI's Windows jobs, which use a local bare remote, exercise it.
- Independence: while checking why CI failed at `e92cace`, I read the diff of that commit to `ba57557`, which shows part of the Builder's report, before my first pass was complete. My four findings and the checks above were already done; the Builder's report agrees on the first and fourth.

## Verdict

The change does what the brief asks and nothing more: the suite and CI are green at the reviewed commit, each of items 1–5 has a test that fails at `6f2d062` (item 1 through the suite, which is the honest form for a fix that lives in a test), the three projects' headers are right, and no invariant is touched. The Builder's claims that I re-ran match. The findings are notes: none makes merging wrong. I am confident in this.
