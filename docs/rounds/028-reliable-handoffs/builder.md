<!-- fw-report
round: 028-reliable-handoffs
role: builder
branch: builder/028-reliable-handoffs
head: 8beb13849e238a928d6cd312209531503e622ee0
os: macOS 27.0
python: 3.9.6
written: 2026-10-03T19:29:15Z
-->
## Verified

Implementation and tests: `419779a7d4d225e7389ebbb3a4efc791b95dbbe5`.
Evidence-only commit: `8beb13849e238a928d6cd312209531503e622ee0`.
The stamp identifies the work described by this report. Fixture commits shown
in logs are disposable project commits, not framework delivery commits.

### Required local checks

`python3 -m unittest discover -s tests -t . -v` at the implementation commit,
with Python 3.9.6 — exit 0. Real output:

```text
Ran 97 tests in 276.509s

OK
```

Full output is in `attachments/implementation-tests.log`. This includes all
existing adoption, legacy migration, safe update, role-name, stale-report,
changed-brief, newer-work/re-review, supersession and unrelated-delivery tests,
plus 14 handoff tests. No real adopter was contacted or changed.

The following commands at the implementation commit exited 0:

```text
ruff check --select F,E9,B,UP --target-version py39 tools templates tests
All checks passed!

python3 tools/fw.py check
0 error(s), 0 warning(s)

git diff --check
(no output)

git diff 7f29a13162a8 HEAD --check
(no output)
```

Ruff 0.15.12 ran from a temporary virtual environment. Commands and statuses
are recorded in `attachments/implementation-checks.log`. After packaging
attachments, `git diff --cached --check` also exited 0 with no output.
Log files retain their relevant output, with private paths replaced by
`<fixture>` or `<framework>` and excess terminal blank lines removed.

### Regression evidence and issue dispositions

All three issues are **implemented**. The baseline is v3.1.0, commit
`eca1306dc43cb81f0df3ee42f841812da68e8b1e`. Its `tools/fw.py` blob and the
brief baseline's blob are both `926cd49a480134328d70c08c7bc0032dd5869592`,
checked with `git rev-parse v3.1.0:tools/fw.py` and
`git rev-parse 7f29a13162a8:tools/fw.py` (both exit 0).

The baseline run substitutes that exact tool into the disposable fixtures;
it does not claim that the entire historical framework tree was installed.
The templates/installer remain unchanged by this implementation.

Actual baseline command (temporary filenames replaced by placeholders):

```text
FW_TEST_BASELINE=<baseline-tool> FW_EVIDENCE_LOG=<log> python3 -m unittest tests.test_handoffs.SeatResumption.test_generated_startup_twice_resumes_unpushed_work tests.test_handoffs.FirstAdoption.test_external_status_routes_first_adoption_without_green_checks tests.test_handoffs.SuccessorDelivery.test_successor_brief_does_not_invalidate_original_delivery -v
Ran 3 tests in 13.122s
FAILED (failures=3)
exit 1
```

Each named case passes in the implementation's full suite. Reproduce those
baseline failures with `python3 docs/rounds/028-reliable-handoffs/attachments/reproduce.py --baseline`
(exit 1 expected; separately executed, three failures in 10.781s). Without
`--baseline`, the script runs the new handoff cases against this implementation.
The script uses only disposable repositories. Git redirects the fixture's
public-shaped source URL to its local repository; it never contacts that host.

- **#32:** the actual old generated worktree instruction exits 0 once, then
  128 on resend. The new generated startup command exits 0 twice, preserving
  an unpushed commit. Dirty matching work exits 2 with an uncommitted-changes
  diagnosis and unchanged contents/HEAD. Foreign repository, wrong seat and
  wrong round paths exit 2 without being reused. Interrupted named worktree
  creation resumes successfully. Fresh prompt generation fetches previously
  unseen review history; changed work gets `verifier-124-2`, and repeating
  that prompt resumes the same review. Offline prompt history is disclosed;
  unreachable-origin worktree startup exits 2 before creating the seat.
- **#38:** baseline external status prints `all project checks pass` for an
  unadopted project and gives the idle next action. The implementation prints
  `installation new: project configuration is not verified` and routes to a
  first-adoption round. A committed, pinned adoption brief is prepared without
  installation by Brain. Worker and Verifier in separate clean clones execute
  the actual generated source clone, exact checkout and startup commands;
  installation/report, independent exact-commit Verifier startup/report and
  Brain delivery all exit 0. Once the fixture adoption is merged, installed
  status and prompts use the normal tool. Cloud startup and an early-stop
  external report also exit 0. Wrong pin/product mode/offline bootstrap,
  damaged history and partial/invalid manifests are diagnosed. A pinned
  ancestor remains usable after the source's branch tip moves.
- **#40:** baseline successor branches make both earlier reports stale;
  automatic original delivery exits 1 while the named original exits 0.
  The implementation retains both original reports and automatic/named
  delivery exit 0. Both successor rounds still show their own seats. A sibling
  successor uses an ordinary `z-inherited` branch, so selection does not depend
  on a Brain branch name. Later work outside new round folders still exits 1.
  Freshness evaluation itself is unchanged; only candidate selection excludes
  inherited copies when later differences exclusively add new round folders
  with briefs. The original unchanged commit is selected, not the successor.

Relevant before/after status, delivery, generated prompts, actual executions,
exit statuses and safety diagnoses are recorded in
`attachments/baseline-commands.log` and `attachments/implementation-commands.log`.
Example real implementation output:

```text
created .worktrees/worker-130
seat ok: worker, round 130-adopt, branch worker/130-adopt at 788bfaba5826
work in: .worktrees/worker-130

resuming .worktrees/worker-130
seat ok: worker, round 130-adopt, branch worker/130-adopt at 788bfaba5826
work in: .worktrees/worker-130

in flight: 110-audit (Tier 2)
  worker: reported at 68d57ce03933
  verifier: reported at c11a93a26ad5
in flight: 111-followup (Tier 2)
  worker: not started
  verifier: not started
in flight: 112-sibling (Tier 1)
  worker: not started

automatic original delivery: exit 0
origin/verifier/110-audit (34931b98b905): delivered
```

### Acceptance criteria

| Criterion | Disposition and evidence |
|---|---|
| 1 | Met: generated local startup executed twice; unpushed work preserved. |
| 2 | Met: dirty, foreign repository, wrong seat/round and interrupted-creation cases executed. |
| 3 | Met: previously unfetched review history, usable fresh re-review location, repeat, and offline refusal/disclosure executed; existing cloud case and new bootstrap cloud case pass. |
| 4 | Met: new versus damaged/ambiguous/legacy diagnosis; no green configuration claim when installation is missing. History is taken from the checkout/default lineage so an in-flight adoption branch does not falsely damage main. |
| 5 | Met mechanically: pinned source, pushed brief, separate Worker/Verifier clones, adoption, stamped reports and Brain delivery; fixture reports simulate the seats. Actual independent review of this framework delivery remains due. |
| 6 | Met: full verified commit and clean source required; dedicated adoption mode; installed workflow resumes after adoption; no automatic launch. |
| 7 | Met: before/after original status/delivery and two distinct successor branches executed. |
| 8 | Met: additional non-round work stays stale; existing real-work, changed-brief, newer-review, incompatible-delivery and supersession tests remain green. |
| 9 | Met: all three named tests fail at the unchanged v3.1.0 tool and pass here; startup commands are executed, not only compared as strings. |
| 10 | Met: counts below; optional command changes below; no release or migration published. |
| 11 | Passed at implementation: local suite/checks and all eight CI jobs. Final report-commit checks/CI will be observed after its push; pending at this stamp, reported in the final reply. |

### Word counts and compatibility

Counted with `len(text.split())`, matching the word-budget tests, against
`7f29a13162a8`:

```text
framework/FRAMEWORK.md: 1707 -> 1707; delta 0; budget 2500
framework/roles/brain.md: 656 -> 651; delta -5; budget 750
framework/roles/worker.md: 381 -> 370; delta -11; budget 750
README.md: 652 -> 634; delta -18; no test budget
Total guidance delta: -34
```

The source of these counts is `attachments/word-counts.txt`. No budget rose.
Round 027's explicit seat naming and exact generated-dispatch guidance remain.

Externally visible changes: `start --worktree .worktrees/<seat-folder>` now
owns safe local creation/resumption; `prompt` fetches by default and supports
`--offline`; first adoption requires `Mode: adoption`, `Framework-source` and
full `Framework-commit` metadata and emits pinned external-tool bootstrap.
Missing installation changes status's next action and check wording, not its
normal exit-code contract. Unusable bootstrap/unsafe startup exits 2.
Cloud seats omit `--worktree`; existing direct `start`, reports, installed
project prompts and framework-repository prompts remain supported. Report
format, role authority, default branch protection and freshness rules are
unchanged. The installed code uses Python 3.9 and the standard library only.

### CI actually observed

`gh run view 37147431850 --json headSha,status,conclusion,jobs` — exit 0.
The observed run is at `419779a7d4d225e7389ebbb3a4efc791b95dbbe5`:
`status: completed`, `conclusion: success`. All six Linux/macOS/Windows test
jobs (Python 3.9 and 3.12), lint, and framework invariants succeeded.
The compact snapshot is in `attachments/implementation-ci.json`.

Earlier development runs were red: a test expected unfetched history from
`status --offline`, then Windows rejected a private fixture source address.
The test now fetches for the live relay; source metadata now uses a URL
redirected locally by Git. Both corrections are committed, and the observed
implementation CI above is green.

## Not verified

- Final report-commit local checks and CI are pending at the report's stamp;
  they will run after push. The final reply will identify that commit and result.
- An actual independent Verifier review, Brain acceptance and owner-approved
  merge have not happened. Fixture reports test mechanics, not acceptance.
- No active adopter was tested or updated. No release classification, tag,
  publication, migration or freeze exception is claimed.
- Real offline remote state is inherently unknown; cached prompt generation
  says so and safe worktree startup requires fetching origin.

## Changed

- `tools/fw.py`: safe local worktree startup, fetched/cached prompt handling,
  pinned first-adoption startup/report support, installation diagnosis,
  and original delivery candidate selection without relaxing freshness.
- `tests/test_handoffs.py`: 14 disposable regression and safety cases,
  including actual generated command execution and a complete adoption relay.
- `tests/test_round.py`: retain prompt assertions for the supported startup
  command, unchanged-review resumption, and offline repository-name fixtures.
- `framework/FRAMEWORK.md`, `framework/roles/brain.md`,
  `framework/roles/worker.md`, `README.md`: minimal supported bootstrap/resume
  guidance, with trims offsetting all additions.
- This round's report and attachments: sanitized reproducible evidence.
- `tools/adopt.py`, templates, adapters, other role cards, `docs/state.md`,
  VERSION and CHANGELOG are unchanged. No state sentences were added/removed.

## Open questions

None for implementation. Final report-commit validation, independent Verifier
review and Brain judgment remain the normal handoff. Release inclusion belongs
to Brain in the next eligible batch; this round authorizes no publication.
