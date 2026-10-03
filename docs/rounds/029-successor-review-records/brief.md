# 029-successor-review-records: Preserve delivery through Brain review records

Tier: 2
Mode: implementation
Supersedes: 028-reliable-handoffs; automatic delivery still becomes stale when a successor brief accompanies a prior-round Brain review record.

## Goal

Complete issue #40's handoff fix: unchanged exact deliveries remain recognizable
when Brain records the review and prepares the next round. Preserve all work
and safety checks delivered for issues #32 and #38 in round 028.

## Context

Read AGENTS.md, framework/FRAMEWORK.md, the role cards, docs/state.md,
docs/feedback.md, issue #40 and the round 028 brief and reports. The starting
delivery is c5c81c56aa6585a324f1a771c29f724f053f411f. Its full suite passes
(98 tests), ruff and hygiene pass, and final CI is green. Brain rejected it for
the independently reproduced gap recorded at
docs/rounds/028-reliable-handoffs/attachments/brain-review.md.

Run attachments/reproduce.py from this round. It creates disposable adopted
projects and cleans them up. The unchanged original delivery succeeds. Adding
a successor brief alone succeeds. Adding a normal Brain review attachment in
the predecessor alongside that successor makes automatic delivery exit 1 while
the explicitly selected original still exits 0. No production code, acceptance
brief or seat report has changed. Review records are ordinary round evidence.

Understand the class rather than special-casing one attachment name, branch
name or ordering. Existing exact report freshness must continue rejecting real
work that is newer than the stamped reports.

## Scope and non-goals

Allowed: tools/fw.py and focused tests for delivery/status candidate selection.
Carry the complete round 028 implementation and evidence forward. Keep its
startup, first-adoption and role-name behavior intact. Put new reports and
evidence in this round. Minimal guidance changes are permitted only if needed
for the supported behavior and within existing word budgets.

Do not change tools/adopt.py, templates, adapters, docs/state.md, VERSION,
CHANGELOG, merge rules, repository settings or role names. Do not implement
unrelated issues, launch agents, publish a release or update adopting projects.
The owner retains the relay. The release freeze remains in force.

## Invariants

- Every installed Python file uses Python 3.9 and the standard library.
- Preserve dirty and unrelated checkouts; no reset, force-push or work loss.
- Exact seat reports and acceptance briefs remain strict. No general exemption
  for documentation, later branches or inherited reports.
- Brain judges, Builder implements, Verifier independently reviews one exact
  commit. Merge needs the owner's yes.
- No personal paths, addresses or account details in tracked evidence.

## Acceptance criteria

1. Automatic status and delivery preserve the completed predecessor when the
   next brief is accompanied by normal Brain review evidence in that predecessor.
   Demonstrate the executable supplied case failing before and passing after.
2. Cover additions in one commit and in separate commits, a different evidence
   filename and branch ordering, and successive follow-up rounds. The successor
   remains separately visible with its own pending seats. The chosen original
   delivery stays exact and valid; do not guess that a later branch was reviewed.
3. Production work after report, an edited predecessor brief, modified seat
   report/stamp, newer Worker work after review, incompatible deliveries and
   supersession retain their rejection or unknown behavior. Add meaningful
   negative cases around the boundary introduced here.
4. All round 028 regressions and prior tests remain green. Actual generated
   resumption and first-adoption instructions still execute successfully, with
   their dirty/unrelated/source-pin safety cases retained.

## Required evidence

- `python3 docs/rounds/029-successor-review-records/attachments/reproduce.py`
  before and after the fix, with actual exit status and output. The initial
  delivery exhibits the failure; the corrected delivery must pass.
- `python3 -m unittest discover -s tests -t . -v`
- `ruff check --select F,E9,B,UP --target-version py39 tools templates tests`
  or `python3 -m ruff` if the executable is unavailable; state which ran.
- `python3 tools/fw.py check` and `git diff --check`.
- Full final-head CI, sanitized evidence and exact report/review stamps.

Verifier: investigate independently before reading Builder's report. Check the
full carried-forward diff against main, not just the corrective commit. Verify
every claimed safety boundary and identify remaining unproven behavior.
