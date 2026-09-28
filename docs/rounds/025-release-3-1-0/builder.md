<!-- fw-report
round: 025-release-3-1-0
role: builder
branch: builder/025-release-3-1-0
head: 495962bab2eddb39905d3560261435b4ad579a94
os: macOS 27.0
python: 3.9.6
written: 2026-09-28T13:10:40Z
-->
# Round 025 — Builder report: release 3.1.0

All evidence below is at commit `495962bab2eddb39905d3560261435b4ad579a94`
(branch `builder/025-release-3-1-0`, which includes Brain's addendum merge
`0bd3227`), on macOS with Python 3.9 and git 2.55, unless stated.

## Verified

- Full suite passes: `python3 -m unittest discover -s tests -t . -v` → exit 0
  `Ran 78 tests in 81.735s` / `OK` (56 at the start of the round; 22 added, one extended).
- Lint: `ruff check --select F,E9,B,UP --target-version py39 tools templates tests` (ruff 0.15.12) → exit 0, `All checks passed!`
- CI at `495962b`, run 36426128171 → `success`: lint, tests on ubuntu/macos/windows × Python 3.9/3.12, and "framework invariants" all `success`.
- Word budgets hold (`tests.test_docs` passes). Documents copied into a project, `v3.0.0` → head:
  FRAMEWORK.md 1695 → 1709, brain.md 705 → 657, worker.md 363 → 381, verifier.md 410 → 428;
  total 3173 → 3172 (net −1, so no budget was raised). Counted with `wc -w` against `git show v3.0.0:<file>`.
- Every issue has a test that fails at `v3.0.0` and passes at head. Method: a scratch
  worktree at tag `v3.0.0` (`7f5bbc3`) with this branch's `tests/` copied over it, so the
  new tests ran against 3.0.0's `tools/`, `framework/` and `templates/`. All 22 listed
  failed there (21 FAIL, 1 ERROR) and all pass at head. The first assertion each hit at `v3.0.0`:
  - #18 `test_adopt.RealProjectLayouts.test_a_squash_merged_round_is_safe_to_leave_on_the_seats_machine` → `AssertionError: 1 != 0` (status --leaving said NO)
  - #18 (comment, archive tags) `test_adopt.RealProjectLayouts.test_archive_tags_on_the_remote_are_safe_to_leave` → `AssertionError: 1 != 0`
  - #19 `test_fw_checks.SeatStart.test_start_warns_about_uninitialised_submodules` → `'submodule(s) not initialised here: ocgcore' not found in 'seat ok: worker, ...'`
  - #20 `test_adopt.UpdateOutput.test_an_up_to_date_project_is_told_there_is_nothing_to_do` → `'nothing to do: ...' not found`
  - #20/gap `test_adopt.UpdateOutput.test_a_dry_run_prints_what_each_release_asks` → `'What each release asks of this project:' not found`
  - #21 `test_adopt.RealProjectLayouts.test_a_seat_file_named_for_the_projects_executor_is_named` → `'other   .claude/agents/builder.md' not found`
  - #22 `test_fw_checks.ScanScope.test_the_personal_data_message_says_which_documents_are_scanned` → `'docs/agents/**/*.md and docs/rounds/*/*.md' not found in 'error: ... tracked documents must work on every machine and are public'`
  - #23 `test_round.ReportChecks.test_a_report_quoting_a_personal_path_or_a_dead_link_is_refused` → `AssertionError: 0 != 2 : report committed: ...`
  - #23 second comment `test_round.ProjectReportCheck.test_the_named_check_refuses_a_report_that_breaks_it` → `AssertionError: 0 != 2 : report committed: ...`
  - #24 `test_adopt.RealProjectLayouts.test_a_round_attachment_is_not_a_report` → `'continuing earlier work' not found in '  warning: origin/worker/070-attach exists but another seat has built on it ...'`
  - #25 `test_adopt.RealProjectLayouts.test_a_deleted_seed_stays_deleted` → `'gone    .githooks/pre-push  (deleted in this project, so not re-created)' not found`
  - #26 `test_round.NextAction.test_each_seat_is_followed_from_not_started_to_judged` → `'in flight: 020-seats (Tier 2)' not found` (this test also checks that `start` pushes the seat branch and that `report` prints the final reply line)
  - #26 `test_round.NextAction.test_tier_1_expects_no_verifier_and_uses_the_projects_executor_name`, `test_a_stale_report_is_shown_as_stale`, `test_nothing_in_flight_says_so_in_the_next_line` → per-seat lines / `next:` not found
  - #26 `test_round.Prompts.test_prompt_has_the_header_the_worktree_and_the_final_line`, `test_prompt_for_the_brain_is_refused` → `fw.py: error: argument command: invalid choice: 'prompt'`
  - #26/item 5 `test_fw_checks.ReleaseCheck.test_status_reports_a_newer_release` (extended) → `'next: ask Brain to plan the update round to framework release 4.0.0' not found`
  - #27 `test_adopt.RealProjectLayouts.test_a_superseded_round_is_not_in_flight` → `'superseded: 060-a, by 061-b -- not in flight' not found`
  - #29 `test_adopt.UpdateOutput.test_seat_checkouts_inside_the_project_are_ignored` → `AssertionError: False is not true` (no `.worktrees/.gitignore`)
  - #29 `test_adopt.RealProjectLayouts.test_a_finished_seat_checkout_is_listed_as_removable` → `AssertionError: '?? .worktrees/' != ''`
  - #30 `test_round.ReReview.test_a_re_review_after_a_report_only_fix_is_the_one_to_judge` → `'most complete: origin/verifier/090-again-2' not found in 'origin/verifier/090-again (...): delivered ...'`. As the addendum asks, this reproduces #30 with a fix that only rewrites the worker report: the Worker re-runs `fw.py report` with a reworded report, and a second Verifier (branch `verifier/090-again-2`) reviews that report commit. At `v3.0.0` both review branches are "delivered" and the older one is listed first.
  - #30 `test_round.ReReview.test_two_unrelated_deliveries_get_no_recommendation` → `AttributeError: module 'fwmod' has no attribute 'most_complete'` (a unit test of the new chooser: when neither delivered branch descends from the other, it recommends nothing and says why)
- Criterion 2: `fw.py status` from head (online) on fresh clones of the three projects → exit 0 for each:
  - edopro-retro-formats `b50dc4966de5`: `superseded: 031-shared-historical-scripts, by 032-derived-scripts-licence -- not in flight`; `in flight: 032-derived-scripts-licence (Tier 2)` with `builder: reported at 62191ed24de3` and `verifier: reported at bcf1419916b4`; `safe to leave this machine: yes`; `next: ask Brain to judge round 032-derived-scripts-licence: every seat has reported`.
  - edopro-next `a1306f93883e`: `in flight: 022-deck-builder-filters (Tier 2)` with builder and verifier both reported; `safe to leave this machine: yes`; `next: ask Brain to judge round 022-deck-builder-filters: every seat has reported`.
  - gx-spirit-caller `1cd6ffa81a03` (13 local tags): `in flight: 004-trustworthy-checker (Tier 2)`, `worker: not started`, `verifier: not started` (origin holds only `brain/004-trustworthy-checker` for that round); `safe to leave this machine: yes`; `next: send the Worker prompt for round 004-trustworthy-checker (Brain prints it with: python3 tools/fw.py prompt --round 004-trustworthy-checker --role worker)`.
  - For comparison, earlier today 3.0.0's status on a gx clone listed 11 `archive/*` tags as "not on GitHub yet" and said `safe to leave this machine: NO`. It also listed retro-formats' 031 as in flight with "(+5 more)"-style counts.
- Criterion 3: `python3 tools/adopt.py <fresh clone> --update --dry-run` for each project → exit 0. Output with the unchanged `same` lines omitted:
  - All three: `replace` docs/agents/FRAMEWORK.md, the three role cards, tools/fw.py and tests/test_framework.py; `keep` for AGENTS.md, docs/state.md, docs/rounds/README.md, CLAUDE.md (plus .gitattributes and .githooks/pre-push where present); `record  docs/agents/framework.json`; then `What each release asks of this project:` with the 3.1.0 steps; `dry run: nothing written`.
  - edopro-retro-formats also prints `other   .claude/commands/atlas.md` and `other   .claude/commands/report.md` (the project's own commands).
  - gx-spirit-caller also prints `gone    .githooks/pre-push  (deleted in this project, so not re-created)`; 3.0.0 planned `create` there (#25).
  - No project gets `.worktrees/.gitignore`, because each project's `.gitignore` already ignores `.worktrees/`.
  - After a real `--update` on a copy of each clone, a second dry run prints `nothing to do: this project already matches agentic-framework 3.1.0` and no `record` line, for all three.
- Before Brain's addendum, `fw.py prompt --round 025-release-3-1-0 --role builder` in this repository printed the prompt this seat received, word for word apart from the `· message 2` header.

## Not verified

- CI for the report commit itself. The report commit changes only this file; CI for `495962b` is shown above.
- The #30 case on gx-spirit-caller's real branches: round 003 merged before I could re-run it (`delivery` now says `round 003-housekeeping-research-and-tools is already merged`). The shape is covered by the test above.
- `merged_by_content` has a fallback for git older than 2.38 (no `merge-tree --write-tree`). That fallback compares every file a branch changed with the default branch. No test exercises it, because CI's git is newer.
- The start-time push for a tool-named branch (it also pushes `<role>/<id>`) was tested only against local bare remotes. A cloud tool that refuses pushes other than its own branch gets a printed note, not a failure; that path was not run.
- Console encoding: `fw.py` sets `errors="replace"` on its output so the header's `·` and `—` cannot crash it. Tests pass on Windows CI with `PYTHONIOENCODING=utf-8`. A Windows console with a legacy code page was not tried by hand.
- An actual update round in any of the three projects: not in scope.

## Changed

- `tools/fw.py`:
  - `status` shows each round in flight seat by seat, using the brief's `Tier:` to decide which seats are expected and the project's executor name from AGENTS.md's role table. Each seat is `not started`, `started`, `reported at <commit>` or `stale`.
  - `status` ends with one `next:` line: the owner's next action, or the framework update to plan when nothing is in flight.
  - A round named under a later brief's `Supersedes:` is shown as superseded. `delivery`, `start` and `prompt` refuse it and name the round that replaced it.
  - The "(+N more)" counts are gone.
  - New `prompt` command prints a seat's prompt: the header, the `.worktrees/<role>-<number>` checkout location, and the final reply line (`--message N` for a repeat).
  - `start` pushes the seat's branch, and warns about uninitialised submodules.
  - `report` refuses a report that contains personal data or a relative link that does not resolve. It also runs the project's `settings.report_check` if one is named, and restores the unstamped file on refusal. With `--push` it prints the header line for the seat's final reply.
  - Only files named for a role, or carrying an `fw.py` stamp, are reports. Other files in a round folder are attachments, in `delivery`, `start` and `status` alike.
  - The leave check counts squash- and rebase-merged work (`merge-tree` against origin's default branch) and tags that origin holds at the same object as pushed.
  - `status` lists clean linked checkouts whose work is merged as removable.
  - `delivery` prefers a re-review whose reviewed commit descends from the other's, flags the older review, and recommends nothing when neither descends from the other.
  - The personal-data message names what it scans.
- `tools/adopt.py`:
  - A seed or adapter file that an earlier run installed and the project then deleted stays deleted. `--hooks` or `--adapter` brings it back.
  - Files the framework did not install, in folders an adapter installs into, are listed as `other`, with one note on what to do.
  - It prints `nothing to do` when nothing changes, prints and writes `record` only when the manifest changes, and prints each release's adopter steps in dry runs too.
  - It installs `.worktrees/.gitignore` unless the project already ignores `.worktrees/`.
- `framework/FRAMEWORK.md`: prompt headers and `fw.py prompt`; `start` pushes; seat checkouts live in `.worktrees/`; the `next:` line; report refusals, including `settings.report_check`; attachments; the release policy (Brain proposes every release; major is Tier 2, minor or patch Tier 1); the Tier table says "major framework updates"; "Idea or question". Wording trimmed elsewhere to hold the word count.
- `framework/roles/brain.md`: the session opens with the `next:` line and the seat states, and re-prints due prompts; any newer release is proposed; the pasted prompt template is replaced by `fw.py prompt`; the merge step removes the round's seat checkouts.
- `framework/roles/worker.md` and `framework/roles/verifier.md`: quote text as code, with no live links or personal paths; end the reply with the line `fw.py report` prints.
- `templates/docs/rounds/README.md`: `attachments/`. `templates/tests/test_framework.py`: its docstring states the scan scope.
- `AGENTS.md`: removed the interim "Prompt headers" section, now framework text.
- `.github/ISSUE_TEMPLATE/idea-or-question.yml`: new form. `docs/feedback.md` and `README.md`: mention the form and the `prompt` command.
- `VERSION` 3.1.0. `CHANGELOG.md` has a 3.1.0 entry with net words and lines and a four-step "What an adopter must do" for one Tier 1 round.
- Tests:
  - `tests/helpers.py`: a shared `RoundTest` base and report constants; the test project's manifest points at this checkout, so status makes no network call.
  - Tests added in `test_adopt.py` (`UpdateOutput`, `RealProjectLayouts`: executor seat file, deleted seed, squash-merged round, archive tags, superseded round, attachment, finished checkout), `test_round.py` (`NextAction`, `Prompts`, `ReportChecks`, `ReReview`, `ProjectReportCheck`) and `test_fw_checks.py` (`SeatStart`, `ScanScope`, extended `ReleaseCheck`); `test_docs.py` knows the `prompt` command.
- `docs/state.md`: not changed.

## Open questions

- #22, the scope decision: I kept the scan to the documents agents read and made the message and docstring name them exactly. Scanning every tracked Markdown file finds 14 lines in edopro-retro-formats (archived briefs), 1 in edopro-next (a path with no name in it) and 49 in gx-spirit-caller (research documents). Widening the scan would have turned all three projects' CI red in a minor release. Those lines are still in public repositories: cleaning them up is the projects' decision.
- The seat checkout folder is `.worktrees/<role>-<number>` (for example `builder-025`), matching the prompt this seat received. The brief says `<role>-<round>`; I read "round" as its number. A one-word change in `seat_prompt` if Brain prefers the full id.
- To make "started" visible for a seat on a tool-named branch, `start` also pushes the seat's own name (`worker/<id>`) at the starting commit, unless origin already has that name. That leaves one more branch to delete after merging.
- `adopt.py` names `.claude/commands/*.md` files a project added as `other`. That follows the brief ("folders an adapter installs into"), but it adds two or three lines to every update in retro-formats and gx-spirit-caller.
- When a round's executor seat is not yet known, status takes its name from AGENTS.md rows that point at `roles/worker.md`, falling back to `worker`. A project whose role table names its executor differently from its branches is shown by the name found in its reports or branches, once those exist.
- Not tagged, as the brief says: Brain tags `v3.1.0` after the owner's yes.
