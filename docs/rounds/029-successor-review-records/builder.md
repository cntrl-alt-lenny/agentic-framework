<!-- fw-report
round: 029-successor-review-records
role: builder
branch: builder/029-successor-review-records
head: c9fa472a43c4c25af132114f5960760399854e48
os: macOS 27.0.1
python: 3.9.6
written: 2026-10-05T09:55:24Z
-->
## Verified

Implementation: `c9519eb3b53f8145ca97a10710d556029d96c286`.
Evidence: `c9fa472a43c4c25af132114f5960760399854e48`.
The report stamp identifies the complete work described. Fixture commit ids
in the logs belong to disposable projects, not framework deliveries.

### Reproduction and regression evidence

`python3 docs/rounds/029-successor-review-records/attachments/reproduce.py`
ran before the fix at starting commit `4ba497da078e` — exit 1. Real output:

```text
Original delivery: 0
Successor brief alone: 0
Successor plus Brain review record: 1
Explicit unchanged delivery: 0
```

The saved before log reruns that same tool via `FW_TEST_BASELINE` against
disposable adopted fixtures. The after run uses the corrective implementation
— exit 0, with all four delivery calls exiting 0 and selecting the same exact
original Verifier tip. Actual output is in `attachments/before-reproduction.log`
and `attachments/after-reproduction.log`.

`FW_TEST_BASELINE=<starting-tool> python3 -m unittest tests.test_handoffs.SuccessorDelivery.test_successor_and_review_added_together tests.test_handoffs.SuccessorDelivery.test_successor_and_review_in_separate_commits -v`
— exit 1 against the starting tool. Real output:

```text
Ran 2 tests in 14.289s
FAILED (failures=2)
```

Both failures show predecessor reports becoming stale. The baseline is read
with `git show 4ba497d:tools/fw.py`; only the tool in disposable fixtures is
substituted. No adopter checkout is used. The complete sanitized failure
output is in `attachments/before-regressions.log`.

The full corrected suite below passes both cases, asserting automatic and
explicit delivery select the literal original Verifier tip. These cases
exercise review and successor additions in one commit and separate commits,
different evidence filenames, arbitrary branches sorting before and after
the original branch, and successive follow-ups with evidence in both earlier
rounds. Both successor rounds remain visible with their own pending seats.

Nine independent negative fixtures retain automatic delivery exit 1 while
the explicitly selected unchanged original exits 0: production edits,
predecessor brief edits, report body edits, report stamp edits, an unstamped
seat report, an added custom stamped report, evidence edits, evidence deletion,
and a new round folder without a brief. Additional tests show newer reported
Worker work makes the existing review stale, and a corrective successor still
supersedes the original (delivery exit 1).

### Required checks

`python3 -m unittest discover -s tests -t . -v` — exit 0, at the implementation
tree above. Real output:

```text
Ran 103 tests in 563.533s
OK
```

Full output is in `attachments/implementation-tests.log`. All 98 prior tests
remain, including round 028's actual generated startup/resumption and pinned
first-adoption instructions, dirty/unrelated/source-pin refusal cases,
safe adoption/update migration, role naming, changed-brief/report freshness,
newer work/re-review, incompatible delivery, supersession and word budgets.
The five added tests include the nine negative subcases.

`python3 --version` — exit 0: `Python 3.9.6`.
Ruff ran through its module:
`python3 -m ruff check --select F,E9,B,UP --target-version py39 tools templates tests`
— exit 0: `All checks passed!`.
`python3 tools/fw.py check` — exit 0: `0 error(s), 0 warning(s)`.
`git diff --check` and `git diff --check origin/main...HEAD` — exit 0, no output.
Commands and real output are in `attachments/local-checks.log`. After packaging
evidence, framework check and whitespace check were repeated: exit 0.

`git diff --name-only origin/main -- tools/adopt.py templates adapters docs/state.md VERSION CHANGELOG.md`
— exit 0, no output. These protected areas remain unchanged across the complete
carried-forward delivery. No guidance changed in this correction, no budgets
rose, and no state sentences were added or removed.

## Not verified

- Final report-commit CI is pending at this stamp. After pushing this report,
  Builder will observe full CI at that literal final commit and give its result
  in the final reply. The local suite above predates the report itself.
- Independent Verifier review, Brain judgment and owner-approved merge remain
  due. No merge, release, tag or adopter update was performed.
- No execution on active adopter checkouts, external product data or physical
  devices. All behavioral probes use disposable repositories; platform coverage
  beyond local Python 3.9 depends on final CI.

## Changed

- `tools/fw.py`: candidate selection recognizes descendants that only add new
  rounds with briefs and new non-report evidence in existing round folders.
  Existing files must remain unchanged. Briefs, README acceptance records and
  seat reports in existing rounds cannot receive the exemption. Known role
  names and custom stamped reports use the existing report classifier.
  At least one new round is required; evidence alone keeps the prior selection
  behavior. Report freshness itself is unchanged and checks the original tip.
- `tests/test_handoffs.py`: five focused regression/safety tests described above.
- This round's report and attachments: sanitized executable before/after and
  check evidence. Round 028's implementation, guidance and evidence are carried
  forward intact through branch ancestry.

## Open questions

None for implementation. Final-head CI, independent review and Brain judgment
are the remaining handoff gates; owner approval is required before merge.
