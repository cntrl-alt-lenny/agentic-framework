# 027-explicit-seat-names: Make dispatch seat names unmistakable

Tier: 2
Mode: documentation
Supersedes: none

## Goal

An owner reading a dispatch can immediately identify its framework seat.
Two specialist Worker assignments cannot be mistaken for a Worker and
Verifier pair. Address issue #37 with a small wording refinement.

## Context

Read `AGENTS.md`, `framework/FRAMEWORK.md`, `framework/roles/brain.md`,
`docs/state.md`, `docs/feedback.md`, and issue #37. Inspect `seat_prompt` in
`tools/fw.py` and the prompt tests in `tests/test_round.py` as evidence of
existing behavior; they already generate an explicit role header and seat
introduction.

In a supplied exchange, a project Brain opened prompts with "interface
implementation agent" and "campaign implementation agent". Both were
Workers, but the owner had to ask which framework seats they represented.
The owner clarified that recognizable seat names were the concern and
explicitly requested this refinement. The project's installed framework
release and commit are unknown; do not claim a reproduced tool defect.

## Scope and non-goals

Refine the Brain card's dispatch guidance so it explicitly distinguishes
the framework seat from its task specialty. Use the project's declared
role name, including a project name such as Builder where applicable.
Keep prompts exactly as the tool generates them; assignment detail belongs
in the brief and may appear in the surrounding explanation.

Only `framework/roles/brain.md` and this round's reports or attachments may
change. No new roles, mandatory chats, commands, prompt formats, or
implementation work. Do not change `tools/`, templates, other cards,
`VERSION`, or the CHANGELOG. Do not include personal details from the source
exchange in tracked files.

This round prepares the refinement. It does not authorize a tag, release,
adopter update, or exception to the release freeze. Brain will decide how
to include accepted wording in the next eligible release batch.

## Invariants

- All repository rules in `AGENTS.md` hold, including independent Verifier
  review for framework changes and owner approval before merge.
- Generated seat prompts remain the canonical dispatch (`brain.md`,
  "Writing a round"); no handwritten specialty prompt substitutes for one.
- Seat authority remains unchanged (`FRAMEWORK.md`, rule 1).
- Remove at least as many words as the change adds and keep the Brain card
  within its existing budget (`AGENTS.md`, `tests/test_docs.py`).
- Brain plans and judges; Builder implements (`brain.md`, "Never").

## Acceptance criteria

1. The Brain card explicitly says a task specialty cannot replace the
   framework seat name in a dispatch. It also preserves project role names.
2. The owner-facing distinction is clear for two Worker assignments and
   for a Worker/Verifier pair, without implying that every round needs a
   Verifier or that each specialty creates a standing role.
3. The report gives illustrative opening labels for both cases, and
   checks the actual generated Worker, Builder, and Verifier wording in
   existing tests or disposable project fixtures. Examples are evidence,
   not a second prompt template or new required format.
4. Existing prompt behavior and the existing word budgets stay intact;
   report before/after word counts and the real diff.
5. Required checks pass at the delivered commit. Do not add tests that
   merely search for the new prose; existing prompt tests cover the tool.

## Required evidence

```
python3 -m unittest discover -s tests -t . -v
python3 tools/fw.py check
git diff --check
```

Also show the Brain card's before/after word counts, the relevant generated
prompt openings, and the final diff. Distinguish local checks from any CI
result actually observed. Report even if blocked, using the normal seat
report command.
