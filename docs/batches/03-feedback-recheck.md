# 03-feedback-recheck — Builder

## Done

Investigated feedback #31, #36 and #43 against published Framework 4.0.1,
literal source commit `06a7d45e45751c40809d6644ea4503ec61cef709`.
Dispatch: `origin/brain/project-refresh-2026-10-08` at
`738c700e3e0a29b0856ef83302f6d16e899027b7`. Work began from latest
`origin/main`, which matched the release. Existing work was preserved.

Committed a reproducible standard-library script and sanitized command
transcript under `docs/batches/03-feedback-recheck/`. Run:

```sh
python3 docs/batches/03-feedback-recheck/reproduce.py
```

It clones the local source into a temporary release checkout, asserts the
exact tag and clean baseline, adopts synthetic projects, checks outcomes,
and discards only its temporary fixtures. No network is needed.

## Checked

- **#31 reproduces: missed scan.** Independently tested UTF-8 and BOM-bearing
  UTF-16LE/BE attachments in batch and legacy-round locations. UTF-8 finds
  both the synthetic Windows user path and reserved-domain email, returning
  1. Both UTF-16 variants return 0 with no findings, although the original
  payload remains decodable. This demonstrates false reassurance if such
  evidence is committed; the checker itself neither publishes nor removes
  attachments. It does not demonstrate an actual disclosure.
- **#36 reproduces: misleading record.** After committed hook deletion, two
  successive dry-run/apply update cycles leave it absent, while retaining
  `options.hooks: true` and the seed record. No restoration or loss occurred.
- **#43 reproduces: unusable cleanup advice.** A tracked initialized
  submodule in a clean seat whose tip is an ancestor of main is listed as
  removable. Normal removal exits 128, including after successful non-forced
  deinitialization. The current Brain card refers to status's cleanup list.
  A dirty-submodule control is reported dirty, omitted from the removable
  list, and retains its contents after refused removal. No force was tried.

Required checks passed at evidence snapshot
`228c8fdc304c05c4624a84926c2e6f1f6cc210b2`: 69 tests, required ruff selection,
and framework check (zero errors/warnings). `checks.txt` retains commands,
outputs and exit statuses; `status.txt` records the same snapshot's status.
Initial status also passed; historical branches were preserved as instructed
by Brain's state. The final documentation commit adds these transcripts and
this validation paragraph; it changes no reproduction or product code.

## Not checked

Windows/Linux execution, adopter repositories, no-BOM UTF-16, actual personal
data disclosure, remote publishing of fixtures, and forced cleanup safety.
No implementation, release, repository settings, issue labels or existing
project files changed. Brain must triage these findings; independent
verification remains pending.

## Failed or blocked

The issue-triggering nonzero results are expected and retained in the
transcript. One initial inspection attempted nonexistent `tests/test_fw.py`;
the shell reported it missing. It was not used as evidence. No blocker.
