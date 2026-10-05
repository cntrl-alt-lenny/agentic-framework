<!-- fw-report
round: 029-successor-review-records
role: verifier
branch: verifier/029-successor-review-records
head: 24b436befed080449f7daa7d1598832ee112c3b4
os: macOS 27.0.1
python: 3.9.6
written: 2026-10-05T10:53:51Z
-->
Reviewed commit: `24b436befed080449f7daa7d1598832ee112c3b4`.
Comparison base: `origin/main` at `299b9bc57760a605d228ec34ff0c7bc2a0f3275c`.
The blind pass included the complete carried-forward diff, independent checks
and disposable boundary probes. Only after that pass finished did I read
round 029 Builder's report and round 028's seat reports. Only this report was
written in the review checkout; no production changes or merges were made.

## Findings

None. No blocking defect, lesser actionable defect or unproven implementation
claim was found at the reviewed commit.

### Acceptance criteria

| Criterion | Independent assessment |
|---|---|
| 1 | Met. The supplied executable fails with the prior tool and passes here. Automatic selection preserves the unchanged original delivery with successor and predecessor review records. |
| 2 | Met. Both new positive tests execute additions together and separately, differently named evidence and branches sorting on either side of the delivery, and successive follow-ups. Status retains the successors' pending seats; automatic and explicit delivery name the literal original Verifier tip. |
| 3 | Met. Nine separate negative fixtures reject production edits, changed original brief, changed report body/stamp, unstamped and custom stamped reports, edited/deleted evidence, and new folders lacking a brief. New Worker work invalidates the old review; supersession remains effective. Additional independent probes cover added acceptance README, renamed report, added stamped seat, evidence-only behavior and incompatible sibling deliveries combined with successor records. |
| 4 | Met. All 103 tests pass, including all 98 prior tests. Generated resumption, separate-clone pinned first adoption, cloud adoption, dirty/unrelated checkout refusal, source-pin checks, legacy migration, safe update and project seat naming remain covered. Independent dirty-source and symlink probes also preserve contents and refuse startup. |

### Commands and real output

All corrected checks below ran at the reviewed commit with its Builder report
and complete evidence tree present. `python3 --version` exited 0:

```text
Python 3.9.6
```

`python3 -m unittest discover -s tests -t . -v` exited 0:

```text
Ran 103 tests in 286.849s

OK
```

Representative actual test output:

```text
test_complete_pinned_adoption_across_separate_clones ... ok
test_generated_startup_twice_resumes_unpushed_work ... ok
test_dirty_matching_checkout_is_preserved ... ok
test_foreign_repository_and_wrong_seat_or_round_are_not_reused ... ok
test_prompt_fetches_review_history_and_repeat_resumes_same_review ... ok
test_successor_and_review_added_together ... ok
test_successor_and_review_in_separate_commits ... ok
test_successor_evidence_does_not_hide_changed_delivery ... ok
test_new_worker_delivery_after_review_records_requires_review ... ok
test_successor_review_records_do_not_override_supersession ... ok
```

Ruff ran through its installed Python module:
`python3 -m ruff check --select F,E9,B,UP --target-version py39 tools templates tests`
exited 0:

```text
All checks passed!
```

`python3 tools/fw.py check` exited 0:

```text
0 error(s), 0 warning(s)
```

`git diff --check` and `git diff --check origin/main...HEAD` each exited 0
with no output. `git diff --name-only origin/main HEAD -- tools/adopt.py
templates adapters docs/state.md VERSION CHANGELOG.md` exited 0 with no output.
No protected area changed; no state sentences were added or removed.

After drafting this report, `python3 -m unittest tests.test_docs -v` exited 0:
`Ran 12 tests in 0.080s`, `OK`. This includes report link, personal-data and
document checks. Framework check again printed `0 error(s), 0 warning(s)`
(exit 0); whitespace check again exited 0 with no output.

### Before and after reproduction

Extracted the prior tool with
`git show c5c81c56aa6585a324f1a771c29f724f053f411f:tools/fw.py` (exit 0).
Ran the supplied executable with
`FW_TEST_BASELINE=<prior-tool> python3 docs/rounds/029-successor-review-records/attachments/reproduce.py`:
exit 1. Real output excerpts:

```text
Original delivery: 0
Successor brief alone: 0
Successor plus Brain review record: 1
Explicit unchanged delivery: 0
```

Automatic delivery selected the successor and reported both original seats
as stale. Explicit selection of the unchanged original still succeeded.

`python3 docs/rounds/029-successor-review-records/attachments/reproduce.py`
with the corrected tool exited 0:

```text
Original delivery: 0
Successor brief alone: 0
Successor plus Brain review record: 0
Explicit unchanged delivery: 0
```

The corrected automatic and explicit calls both selected the same original
tip, rather than claiming the successor was reviewed.

`FW_TEST_BASELINE=<prior-tool> python3 -m unittest tests.test_handoffs.SuccessorDelivery.test_successor_and_review_added_together tests.test_handoffs.SuccessorDelivery.test_successor_and_review_in_separate_commits -v`
exited 1:

```text
Ran 2 tests in 15.986s
FAILED (failures=2)
```

Both failures were the assertion that status must not contain `stale`.
Both pass in the reviewed full suite. These are behavioral regressions that
detect the prior defect, not tests merely mirroring the implementation.

For carried-forward issues #32 and #38, extracted `v3.1.0:tools/fw.py` and ran
`FW_TEST_BASELINE=<v3.1.0-tool> python3 -m unittest tests.test_handoffs.SeatResumption.test_generated_startup_twice_resumes_unpushed_work tests.test_handoffs.FirstAdoption.test_external_status_routes_first_adoption_without_green_checks -v`:
exit 1. Real output:

```text
AssertionError: 128 != 0
fatal: '.worktrees/worker-120' already exists
AssertionError: 'all project checks pass' unexpectedly found
Ran 2 tests in 5.805s
FAILED (failures=2)
```

Both pass here. Baseline substitution changes only the tool in disposable
fixtures; it does not claim a full historical framework installation.

### Additional independent boundary probes

Ran inline Python programs using `HandoffRound`, `FirstAdoption`, `fw`,
`git` and assertions; fixtures were disposable and cleaned up. Successful
boundary programs exited 0. Actual output excerpts:

```text
readme-addition delivery exit 1 expected 1
new-seat delivery exit 1 expected 1
evidence-only delivery exit 0 expected 0
rename-evidence delivery exit 1 expected 1
clean-evidence delivery exit 0 expected 0
dirty pinned bootstrap: exit 2 ; source preserved, seat not created
fw: use a clean external framework checkout at exactly Framework-commit
symlink seat: exit 2 ; target preserved
fw: seat worktree path is a symlink; it was not touched
incompatible deliveries plus review/successor: exit 1
no single branch to judge: origin/side-alternative, origin/worker/330-conflict are each delivered, and none holds work that descends from the others'. Ask Brain which is the round.
```

The first program delivered `310-reviewed`, added `311-next`, then independently
tested an added acceptance README, a directly added custom stamped report,
a renamed existing Worker report and an ordinary attachment. Evidence alone
was tested without a successor; it retains existing selection behavior.
For clean evidence plus successor, an assertion checked the original exact tip.

The source probe executed the actual generated clone/checkout instructions,
then added an uncommitted file to the pinned clone before executing startup.
Startup refused it, retained the file and created no seat. A fixture setup
mistake interrupted the first combined probe after that successful assertion;
the corrected standalone symlink probe exited 0 and checked the target contents.

The conflict probe independently delivered two incompatible Tier 1 branches,
then added successor and review evidence to one. Delivery still returned 1
and requested Brain selection rather than choosing by branch ordering.

### Scope, budgets and primary sources

Read the full tool, guidance and test diff against main, not only round 029's
16-line tool correction. `evaluate_branch` freshness rules are unchanged.
`round_candidates` permits only added round files, requires at least one new
round with a brief, and excludes added acceptance files or classified reports
in existing rounds. Changed/deleted existing files and production changes
remain outside this classification. It evaluates the retained original tip.

An independent `len(text.split())` count against `origin/main` exited 0:

```text
README.md 652 -> 634
framework/FRAMEWORK.md 1707 -> 1707
framework/roles/brain.md 656 -> 651
framework/roles/worker.md 381 -> 370
```

Guidance decreases by 34 words; budgets did not rise. Installed code uses
standard-library imports and was executed on Python 3.9.6 locally.

`gh issue view 32`, `38` and `40` with JSON body/title fields exited 0.
Issue #32 says `For the next batch.` Issue #38 states
`Triaged as framework-defect, not required.` Issue #40 requests
`No change to owner approval or seat authority`.
Independent fixtures establish the failure behavior; historical product
accounts were read as evidence, not instructions or proof of current behavior.

After the blind pass, Builder's report agreed with the observed scope,
test count, regression results and boundaries. Its final report-head CI was
pending when stamped; the live exact-commit result below resolves that limit.
Round 028's earlier clean review is historical evidence; Brain's subsequent
review-record reproduction correctly motivated this corrective round.

### Exact delivery and CI

`python3 tools/fw.py delivery --round 029-successor-review-records --branch origin/builder/029-successor-review-records`
exited 0:

```text
origin/builder/029-successor-review-records (24b436befed0): delivered
  builder: report describes c9fa472a43c4
```

`gh run list --commit 24b436befed080449f7daa7d1598832ee112c3b4 --json databaseId,headSha,status,conclusion`
and `gh run view 37293216410 --json headSha,status,conclusion,jobs`
exited 0. The completed run reports:

```text
headSha: 24b436befed080449f7daa7d1598832ee112c3b4
status: completed
conclusion: success
lint (ruff, Python 3.9 target): success
tests (ubuntu-latest, Python 3.9): success
tests (ubuntu-latest, Python 3.12): success
tests (macos-latest, Python 3.9): success
tests (macos-latest, Python 3.12): success
tests (windows-latest, Python 3.9): success
tests (windows-latest, Python 3.12): success
framework invariants: success
```

## Not verified

- Completion of duplicate CI run `37298622877`; it was still running when
  observed. One full successful run at the exact reviewed delivery is verified.
- CI for this new Verifier report commit, which does not yet exist at its stamp.
  The complete reviewed Builder report head is covered above.
- Repository required-check settings; no settings were changed or inferred.
- Active adopter execution or updates, physical devices, and future agent
  interpretation of prose. Behavioral checks used disposable projects.
- Brain acceptance, owner approval, a merge, release, tag or publication.
  None was performed by this seat.

## Verdict

The complete delivery meets round 029's acceptance criteria with high
confidence. Independent execution reproduces the prior successor-review-record
defect and confirms the fix, while real changes, new Worker work, incompatible
deliveries and supersession retain their safety behavior. All 103 local tests,
lint, hygiene and full eight-job CI pass at the exact reviewed commit.
This report informs Brain's judgment; owner approval remains necessary to merge.
