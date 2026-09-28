<!-- fw-report
round: 025-release-3-1-0
role: verifier
branch: verifier/025-release-3-1-0
head: 2994f2d4657e3165302171a45e2bd5427a540660
os: macOS 27.0
python: 3.9.6
written: 2026-09-28T14:01:30Z
-->
# Round 025 — Verifier report: release 3.1.0

Reviewed commit: `2994f2d4657e3165302171a45e2bd5427a540660` (branch `builder/025-release-3-1-0`, as `fw.py start` named it).

Commands I ran myself (macOS, Python 3.9.6):

- `python3 -m unittest discover -s tests -t .` at the reviewed commit → exit 1, `Ran 78 tests`, `FAILED (failures=1)`: `test_every_documented_command_exists` (see the blocker).
- `ruff check --select F,E9,B,UP --target-version py39 tools templates tests` (ruff in a scratch venv) → exit 0, `All checks passed!`
- `gh run list --commit 2994f2d…` → run 36426773611, `failure`; the log shows the same test failing on ubuntu, macos and windows, Python 3.9 and 3.12. CI at `495962b` (before the two report commits) was `success`.
- The head's `tests/` against `v3.0.0`'s `tools/` (a scratch copy of the head tree with `tools/` taken from the tag): all 25 new or extended tests in `test_round`, `test_adopt` and `test_fw_checks` fail there (24 FAIL, 1 ERROR), including every test for #18, #26, #27 and #29; all pass at the head. I read the first assertion of each #18/#26/#27/#29/#30 failure: each fails on the behaviour it names, not on a harness difference.
- Break-then-fix for the one test that failed at `v3.0.0` for an earlier reason (`test_a_finished_seat_checkout_is_listed_as_removable` failed there on the missing ignore rule): I removed the line that lists a removable checkout in the head's `tools/fw.py`; the test then fails. So it guards #29's listing too.
- `python3 tools/adopt.py <fresh clone> --update --dry-run` for edopro-retro-formats, edopro-next and gx-spirit-caller → exit 0 each. Each plans `replace` for FRAMEWORK.md, the three role cards, `tools/fw.py` and `tests/test_framework.py`; `keep` for project-owned files; `record`; the 3.1.0 adopter steps; `dry run: nothing written`. edopro-retro-formats adds `other   .claude/commands/atlas.md` and `other   .claude/commands/report.md`; gx-spirit-caller adds `gone    .githooks/pre-push  (deleted in this project, so not re-created)`. None plans `.worktrees/.gitignore`: `git check-ignore` confirms each project's `.gitignore` already covers `.worktrees/`.
- A real `--update` on each clone, then: a second dry run prints `nothing to do: this project already matches agentic-framework 3.1.0` and no `record` line; `python3 -m unittest tests.test_framework` → OK; `python3 tools/fw.py check` → `0 error(s), 0 warning(s)`; `delivery --round 032-derived-scripts-licence` (retro-formats) and `delivery --round 022-deck-builder-filters` (edopro-next) → `delivered`, exit 0, on their existing branches and round folders; `delivery --round 031-shared-historical-scripts` → says it was superseded by 032, exit 1.
- `python3 tools/fw.py --cwd <fresh clone> status` from the head, all three → exit 0: retro-formats shows 031 as superseded, 032 in flight with builder and verifier reported, `next: ask Brain to judge round 032…`; edopro-next shows 022 with both reported and the same kind of `next:`; gx-spirit-caller shows 004 with worker and verifier `not started` (origin holds only `brain/004-…` for it) and `next: send the Worker prompt…`. All say `safe to leave this machine: yes`. These match the remote branches I listed.
- A scratch repository with an unpushed branch and re-tagged local tags: `status` still reports the unpushed branch and `safe to leave … NO`.
- `fw.py prompt` on the updated clones: correct round, role, worktree folder and final line; `--message 2` adds `· message 2`; a superseded round is refused.
- `tests.test_docs.Budgets` → OK; `python3 tools/fw.py check` in this repository → 0 errors; a scan of every added line in the diff for home-folder paths and email addresses finds only the test fixtures' made-up macOS home folder for a user named "someone".

## Findings

- [BLOCKER] `docs/rounds/025-release-3-1-0/builder.md:55` — the report's text `tools/fw.py and tests/test_framework.py` matches `test_every_documented_command_exists`'s pattern `fw\.py (\w+)`, which reads `and` as an undocumented command. — The suite fails at the reviewed commit, locally and in CI on all six jobs (run 36426773611). Merging puts a red suite on `main`, and acceptance criterion 4 ("CI passes … at the head you report") is not met. A one-word rewording of that line (for example `` `tools/fw.py`, `tests/test_framework.py` ``) fixes it.
- [SHOULD FIX] `tools/fw.py:310-316` — `project_name` takes the first `# ` heading of `AGENTS.md` verbatim. — In edopro-retro-formats that heading is `AGENTS.md — coordination model for edopro-retro-formats`, so every prompt header there reads `AGENTS.md — coordination model for edopro-retro-formats · ROUND 032 · BUILDER`, and seats end their replies with the same. The header is what the owner compares across chats; a long, misleading project name defeats it. The other two projects give `Yu-Gi-Oh! GX Spirit Caller decomp` and a plain name. Use the repository name from origin (or `root.name`) unless the manifest names the project.
- [NOTE] `tools/fw.py:1367` — the personal-data scan reads `docs/rounds/*/*.md` only, and `report_problems` reads only the report, so the new `docs/rounds/<id>/attachments/` folder — meant for logs and long lists, where home-folder paths are likeliest — is never scanned. The message states the scope correctly (#22's chosen option), so nothing is claimed that is not true; it is a gap in a public repository.
- [NOTE] The blocker is the #23-second-comment failure in this repository: a report broke the project's own test. `settings.report_check` cannot prevent it here, because this repository has no `docs/agents/framework.json`. Tightening the test's pattern to real command positions, or giving this repository an equivalent pre-report check, would stop a recurrence.
- [NOTE] `tools/fw.py:1111` and `:1149` — an unmerged Tier 0 round is listed as `in flight` with no seats, and its `next:` line says `every seat has reported`. Harmless, but odd wording for a round that has no seats.
- [NOTE] `tools/fw.py:985` — the Verifier prompt always names `.worktrees/verifier-<number>`. For a re-review of the same round (the #30 case) that folder usually still exists, so `git worktree add` fails and the seat stops at its first command. The Brain card's merge-time clean-up does not cover this mid-round case.
- [UNPROVEN CLAIM] The builder's report, under Not verified: "CI for the report commit itself. The report commit changes only this file; CI for `495962b` is shown above." — implies the report commit cannot change CI's result. It did: CI fails at `a77de44` and at `2994f2d` because of that file.

Pass two, agreements: I reproduced the builder's per-issue failures at `v3.0.0` (same first assertions for the ones I read), the three `status` outputs, the three dry runs and the second-run `nothing to do`, and the word counts holding without a budget raise. Its open questions (`<role>-<number>` for the folder name, `.claude/commands` files listed as `other`, the extra start-time push) are reasonable readings of the brief; none is a defect.

## Not verified

- The `merge-tree` fallback for git older than 2.38 (no test runs it; my git is newer).
- A Windows console with a legacy code page printing the `·` header.
- The start-time push on a cloud tool that refuses extra pushes. My own seat was started by `main`'s older `fw.py`, so this review did not exercise the push either.
- The full own test suites of the three projects after the update (I ran only their `tests/test_framework.py` and `fw.py check`).
- The #30 case on real gx-spirit-caller branches: that round has merged; only the test covers it.

## Verdict

The code does what the brief asks, and I am fairly confident of it: every issue's test fails at `v3.0.0` for the named reason and passes at the head; the three projects update cleanly, keep their deleted and project-owned files, keep working with their existing round folders and branches, and their `status` shows the right rounds, seats and `next:` line with no false "not safe to leave". The word budgets hold and no personal data entered a tracked file. It should not merge as reviewed only because the builder's own report makes the suite and CI fail at this commit; a one-line rewording of that report, and a green CI run at the new head, clear it. The prompt-header project name in edopro-retro-formats is worth fixing in the same pass, since the header is the thing this release exists to make reliable.
