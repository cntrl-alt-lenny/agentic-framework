# 028-reliable-handoffs: Make startup, resends and follow-up delivery reliable

Tier: 2
Mode: implementation
Supersedes: none

## Goal

The owner can send the generated seat prompts and trust the next-action
diagnosis through first adoption, interrupted sessions and follow-up rounds.
Resolve triaged issues #32, #38 and #40 as one coherent handoff improvement.
The owner authorized preparing these fixes on 2026-10-03.

## Context

Read `AGENTS.md`, `framework/FRAMEWORK.md`, the role cards, `docs/state.md`,
`docs/feedback.md`, and issues #32, #38 and #40 in full. Inspect the relevant
startup, prompt, status and delivery code in `tools/fw.py`, and the existing
disposable-project fixtures and round tests. Read installer code only where
needed to understand first adoption and fingerprints.

Brain reproduced all three classes using disposable repositories:

- A resent prompt's worktree command succeeded once and then exited 128
  because the seat folder already existed (#32).
- An unadopted project's external status reported a missing manifest, then
  "all project checks pass" and an idle next action. Its generated prompt
  required the absent installed tool. Both FE6 Workers stopped on this
  prerequisite; MGS needed a handwritten bootstrap exception (#38).
- After both seats delivered round 110, adding round 111's brief from its
  Verifier delivery made automatic status call both earlier reports stale.
  Automatic delivery exited 1; selecting the unchanged original Verifier
  branch exited 0 (#40). The issue includes a portable reproduction.

The installed `fw.py` at v3.1.0 has the same code as this brief's baseline.
Do not use active product checkouts as test fixtures or interrupt their work.
Historical project reports establish the failure shapes; reproduce behavior
in disposable clones rather than treating those reports as proof.

## Scope and non-goals

Allowed: `tools/fw.py`, focused regression tests and fixtures, and the minimal
framework/README guidance required to explain supported first adoption and
seat resumption. Round reports and supporting evidence belong in this folder.
Change wording within the existing budgets, removing at least as many words
as are added. Do not raise a budget without further owner agreement.

Keep `tools/adopt.py`, adapters and templates unchanged unless a scoped failure
cannot be resolved without them; report that need rather than expanding.
This round does not change `docs/state.md`, role names, merge rules, repository
settings, licensing, model selection, or the owner relay. No new standing seat,
automation, unrelated cleanup, or fixes for issues #31 and #36.

Do not change VERSION or CHANGELOG, tag, publish, or update adopting projects.
The changes are prepared for the next eligible release batch. The release
freeze remains in force; this authorization is not an early-release exception.

## Invariants

- Every installed Python file runs on Python 3.9 using only the standard
  library (`AGENTS.md`); shell instructions must work across supported systems.
- Brain briefs and judges, Builder implements, Verifier independently reviews
  one exact commit; only Brain merges after owner approval (role cards).
- No personal paths, addresses or account details enter tracked evidence
  (`AGENTS.md`). Use generic placeholders and sanitize actual outputs.
- Never discard dirty work, reset a seat's work, overwrite an unrelated
  checkout, force-push, or change repository settings (framework rule 12).
- Report freshness and exact-commit review remain strict. No blanket exemption
  for later branches, documentation changes or inherited reports (rules 7-11).
- Safe adoption, edited/project-owned files, legacy migration and existing
  round shapes remain supported (`AGENTS.md`, `tests/test_adopt.py`).
- Preserve round 027's explicit seat naming and canonical generated dispatch.

## Acceptance criteria

### Resent and re-review prompts (#32)

1. A generated prompt sent again to the same role and round successfully
   resumes its matching checkout without requiring the owner to remove folders
   or edit commands. Demonstrate the actual generated instructions twice.
2. A dirty matching seat is preserved and diagnosed; a path holding another
   repository/round/seat is not silently reused, deleted or reset. Show these
   negative cases and an interrupted matching session.
3. Prompt generation accounts for pushed review history that this clone has
   not fetched. A fresh re-review of changed work receives a usable location;
   repeating that prompt resumes the same review. Offline behavior is explicit
   and safe, without claiming remote freshness. Preserve cloud-workspace use.

### First adoption (#38)

4. External status against a clean, unadopted project names adoption as the
   next action and does not imply missing project configuration passed checks.
   Distinguish a new project from an adopted project with damaged/missing
   installation using available evidence; disclose ambiguous cases.
5. Brain can prepare first adoption, and generated Worker/Verifier prompts can
   perform the supported startup and report path before main contains fw.py.
   Demonstrate a complete round across separate clones with a pinned framework
   source, a pushed brief, Worker adoption/report, independent Verifier startup
   and report, and Brain delivery. The owner performs no installation commands
   and carries no private filesystem paths between seats.
6. Bootstrap uses a concrete, verified source/ref and becomes the normal
   installed workflow after adoption. It does not silently run unpinned main,
   weaken startup failure handling, make Brain implement adoption, or confuse
   first adoption with a product round. Existing adopted-project prompts and
   framework-repository prompts remain usable. Do not auto-launch seats.

### Successor briefs and existing delivery (#40)

7. After a Worker/Verifier delivery, a successor Brain branch adding a distinct
   round brief and its records does not make the original unchanged delivery
   stale. Automatic status and delivery find the valid original reports while
   showing the successor's own seats separately. Demonstrate before and after.
8. Genuine work after a stamped report, an edited original brief, newer Worker
   work after review, incompatible deliveries and superseded rounds retain
   their existing rejection/unknown behavior. Test at least the supplied shape
   and a different branch ordering; do not solve it by special branch names.

### Evidence and boundaries

9. Each issue has meaningful regression evidence failing at v3.1.0 and passing
   at the delivered implementation. Existing tests stay green. Demonstrate the
   generated startup/resume commands, not only matching strings or helper APIs.
10. Existing word budgets hold, with per-file before/after counts for changed
    guidance. Explain any externally visible command/output change and why
    existing projects remain compatible. Do not claim a release classification
    or migration has been published.
11. Required local checks and CI pass at the final delivery, including report
    commits. Report any unobserved platform result under Not verified.

## Required evidence

```
python3 -m unittest discover -s tests -t . -v
ruff check --select F,E9,B,UP --target-version py39 tools templates tests
python3 tools/fw.py check
git diff --check
```

Also show each named regression failing against v3.1.0 and passing after the
fix, before/after status and delivery excerpts, actual generated prompt
execution results in disposable clones, guidance word counts, and CI for the
exact final commit. Evidence scripts/logs may be committed under attachments
without personal data. Test commands must not contact or mutate real adopters.

Builder: report one disposition per issue and acceptance criterion, commands,
real relevant output, exit statuses and verification limits. Commit work before
using the normal stamped report command; push on every exit, including a stop.

Verifier: make the blind first pass before opening Builder's report. Run the
required checks independently, inspect the actual diff, reproduce one positive
and one safety case for each class, and check that freshness is not weakened.
Commit only the Verifier report. Neither seat merges or publishes.
