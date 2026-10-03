<!-- fw-report
round: 028-reliable-handoffs
role: verifier
branch: verifier/028-reliable-handoffs
head: 2d2a49e141549efe1482b032dacf8185cfee0157
os: macOS 27.0
python: 3.9.6
written: 2026-10-03T20:08:38Z
-->
Reviewed commit: `2d2a49e141549efe1482b032dacf8185cfee0157`.
The blind first pass, independent checks and additional disposable probes
finished before opening `builder.md`. Only this report was written in the
review checkout; no production files were changed.

## Findings

None. The implementation meets the brief at the reviewed commit.

### Acceptance criteria

| Criterion | Independent assessment |
|---|---|
| 1 | Met. Actual generated startup executes twice and retains unpushed seat work. An additional independent resend probe also succeeded twice. |
| 2 | Met. Dirty content and HEAD are preserved; foreign repositories and wrong round/seat worktrees are refused. Interrupted matching creation resumes. |
| 3 | Met. Prompt generation fetches unseen review history, changed work gets the second review location, and repeating startup resumes it. Offline prompts disclose cached history; unreachable origin blocks local creation. Cloud startup remains supported. |
| 4 | Met. Clean first adoption gets an adoption next action without green configuration wording. Partial, malformed and previously installed-but-missing configurations receive diagnosis. Legacy installations retain an update route. |
| 5 | Met mechanically. The complete adoption test executes generated clone, pinned checkout and startup commands across separate Worker and Verifier clones, installs, reports, and obtains Brain delivery. Fixture reports simulate seat judgments; this review independently assesses the framework implementation. |
| 6 | Met. Dedicated adoption metadata, exact full pin, clean source and source reachability are checked. Unverified pins and product mode are refused. A separate dirty-source probe also refused dispatch. Installed routing resumes after adoption. |
| 7 | Met. Original status/delivery survive two successor branches, including an ordinary sibling branch; successors retain their own seat diagnoses. Independent successor delivery also stayed valid. |
| 8 | Met. Freshness evaluation is unchanged. Real work, edited original briefs, newer Worker work, incompatible deliveries and supersession retain rejection or ambiguity behavior. Independent original-brief mutation returned delivery exit 1. |
| 9 | Met. All three named regressions failed with the exact v3.1.0 tool and passed in the reviewed full suite. Tests execute startup commands rather than merely asserting strings. |
| 10 | Met. Guidance counts decrease overall, budgets remain unchanged, and round 027 naming remains intact. Optional startup/offline flags preserve existing direct startup and report commands. No release or adopter update occurred. |
| 11 | Met at the exact reviewed delivery, including its Builder report. All local checks passed, and completed CI run 37148827286 succeeded in all eight jobs at this commit. An additional CI run was still in progress when observed. |

### Independent commands and real output

`python3 tools/fw.py start --role verifier --round 028-reliable-handoffs`
— exit 0; selected exactly the reviewed commit from the delivered Builder
branch. `python3 --version` — exit 0:

```text
Python 3.9.6
```

`python3 -m unittest discover -s tests -t . -v` — exit 0 at the reviewed
commit, including its report and attachments:

```text
Ran 98 tests in 229.921s

OK
```

The full suite includes all fifteen new handoff cases and the existing
adoption, migration, safe-update, portability, budgets, stale-report,
changed-brief, supersession, incompatible-delivery and exact-review cases.
The new tests exercise each issue's failure class and safety boundaries.
The baseline substitutions use the historical tool with the unchanged
installer/templates, rather than claiming a complete historical installation.

`ruff check --select F,E9,B,UP --target-version py39 tools templates tests`
initially exited 127 because the executable was not on PATH. The same
installed Ruff 0.15.12 was then run through its Python module:
`python3 -m ruff check --select F,E9,B,UP --target-version py39 tools templates tests`
— exit 0:

```text
All checks passed!
```

`python3 tools/fw.py check` — exit 0:

```text
0 error(s), 0 warning(s)
```

`git diff --check` and `git diff --check origin/main HEAD` — each exit 0,
no output. Read the real diffs for the tool, all changed guidance and both
test files. `git diff --name-only origin/main HEAD -- tools/adopt.py adapters
templates docs/state.md VERSION CHANGELOG.md` — exit 0, no output.
No protected area changed; there are no state sentences to reconcile.
The installed tool uses only standard-library imports and the suite actually
ran on Python 3.9.

### Baseline regression reproduction

`python3 docs/rounds/028-reliable-handoffs/attachments/reproduce.py --baseline`
— exit 1, as expected. Independently confirmed that the v3.1.0 tool and
`origin/main` tool are byte-identical. Real excerpts:

```text
generated worktree command
$ git worktree add --detach .worktrees/worker-120 origin/main
exit 128
fatal: '.worktrees/worker-120' already exists

external framework command
exit 0
Checks
  all project checks pass
next: nothing is waiting on you; ask Brain for the next round

after successor status
  in flight: 110-audit (Tier 2)
    worker: stale -- its report no longer describes its branch
    verifier: stale -- its report no longer describes its branch

automatic original delivery
exit 1
named unchanged delivery
exit 0

Ran 3 tests in 26.392s
FAILED (failures=3)
Process exit: 1
```

Those three failures were respectively:
`SeatResumption.test_generated_startup_twice_resumes_unpushed_work`,
`FirstAdoption.test_external_status_routes_first_adoption_without_green_checks`,
and `SuccessorDelivery.test_successor_brief_does_not_invalidate_original_delivery`.
All three passed at the reviewed commit in the full suite above.

### Additional independent positive and safety probes

Ran one inline Python program with `HandoffRound`, `FirstAdoption`,
`dispatch_start`, `fw` and `git`, using only disposable repositories
and assertions; process exit 0. It executed the actual generated instructions
and independently checked each class's positive and safety behavior:

```text
RESUME actual generated command: first=0 repeat=0
DIRTY refusal=2 content_preserved=True head_preserved=True
NEW status exit=0
  installation new: project configuration is not verified
Command form before adoption: python3 <pinned-framework>/tools/fw.py --cwd <project> <command>
next: ask Brain to prepare a first-adoption round with a verified framework source and commit

PINNED bootstrap/start exit=0
DIRTY SOURCE refusal=2
fw: use a clean external framework checkout at exactly Framework-commit
SUCCESSOR delivery before=0 after=0
EDITED ORIGINAL BRIEF delivery exit=1
  problem: origin/brain/204-next changed after the verifier report (docs/rounds/203-original/brief.md, docs/rounds/204-next/brief.md); the report describes an older commit, so the verifier must rewrite it
  problem: origin/brain/204-next changed after the worker report (docs/rounds/203-original/brief.md, docs/rounds/204-next/brief.md); the report describes an older commit, so the worker must rewrite it
```

The resumption probe used round `201-probe`, invoked its generated prompt
twice, then added an uncommitted file and checked both its contents and HEAD.
The adoption probe executed generated source clone/checkout and startup,
then dirtied the external source before requesting another prompt.
The successor probe delivered `203-original`, added `204-next` from that
delivery, then changed the original brief and pushed that fixture branch.
No active product checkout was read or mutated as a test fixture.

The candidate-selection change at `tools/fw.py:671-698` only ignores a
descendant when its entire difference adds previously absent round folders
with briefs. It then evaluates the original tip. It does not exempt later
work from report freshness: `evaluate_branch` is unchanged, and both the
independent edited-brief probe and the suite's extra-work case reject it.

### Guidance and compatibility

An inline Python count using `len(text.split())` and
`git show origin/main:<file>` — exit 0:

```text
README.md: 652 -> 634
framework/FRAMEWORK.md: 1707 -> 1707
framework/roles/brain.md: 656 -> 651
framework/roles/worker.md: 381 -> 370
baseline tool equals main: True
```

Guidance decreases by 34 words; the framework and role budgets remain 2500
and 750. The normal installed workflow retains its command forms. Generated
local prompts now call `start --worktree` instead of unconditional worktree
creation; cloud prompts retain direct startup. `prompt` fetches by default
and `--offline` makes cached-state use explicit. First adoption uses dedicated
metadata and a pinned external tool; missing installation receives a different
next action and unverified-check wording. These changes need a future eligible
release before adopters receive them; this round publishes nothing.

### Primary-source and Builder comparison

Read issues #32, #38 and #40 directly on GitHub and through `gh api`, including
their available comment responses (issue-body/comment API commands exited 0).
Issue #32 places the problem `For the next batch.` Issue #38 says
`Triaged as framework-defect, not required.` Issue #40 requests
`No change to owner approval or seat authority`.
The disposable baseline results independently establish all three failure
shapes; historical product reports were not treated as proof or instructions.

After the blind pass, the Builder report agreed with the independent findings,
word counts, command changes, regression outcomes and scope. It distinguishes
97-test evidence from its earlier implementation and the later compatibility
correction. The reviewed delivery passes 98 tests, including that correction.
Its final-delivery evidence was pending at the report stamp; this review
supplies checks and observed CI at that exact delivery. No contradictory
implementation claim was found.

### CI observed at the exact reviewed commit

`gh run list --commit 2d2a49e141549efe1482b032dacf8185cfee0157 --json databaseId,workflowName,status,conclusion,headSha`
— exit 0; identified one completed successful run and one additional run
in progress. `gh run view 37148827286 --json headSha,status,conclusion,jobs`
with compact job output — exit 0. Observed:

```text
headSha: 2d2a49e141549efe1482b032dacf8185cfee0157
status: completed
conclusion: success
lint (ruff, Python 3.9 target): success
tests (windows-latest, Python 3.9): success
tests (macos-latest, Python 3.12): success
tests (ubuntu-latest, Python 3.9): success
tests (macos-latest, Python 3.9): success
tests (windows-latest, Python 3.12): success
tests (ubuntu-latest, Python 3.12): success
framework invariants: success
```

## Not verified

- Completion of additional CI run 37150050689; its Windows jobs were still
  running when observed. Required-check settings were not inspected.
- Behavior on active adopters or historical product commits. All execution
  probes used disposable repositories; no adopter was updated.
- Human interpretation and future agent compliance with generated prose.
- A release, tag, publication, migration classification or freeze exception.
  None was performed. Brain acceptance and owner approval remain pending.

## Verdict

The three handoff fixes meet the brief with high confidence. Independent
execution reproduced each original defect, checked positive and safety cases,
and confirmed that real work and original-brief changes still invalidate
reports. All required local checks and a complete eight-job CI run pass at
the exact reviewed delivery. This informs Brain's decision; it neither merges
the work nor authorizes an early release.
