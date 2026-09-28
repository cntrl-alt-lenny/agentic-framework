# 026-release-3-1-0-fixes: Release 3.1.0 — corrections before merge

Tier: 2
Mode: implementation
Supersedes: 025-release-3-1-0, rejected at its reviewed commit because the test
suite and CI fail there and the new prompt header shows a wrong project name.

## Goal

Round 025's work is merged-ready: the suite and CI are green, and every finding
from its review is resolved. Nothing else changes. Round 025's code was reviewed
and its per-issue tests were independently re-run by Brain (each fails at
`v3.0.0` and passes at the reviewed head); this round builds on that commit and
must not redo or reshape it.

## Context

Start from the reviewed commit of round 025 (this brief's branch is cut from
it). Read `docs/rounds/025-release-3-1-0/brief.md`, `builder.md` and
`verifier.md`, and this brief. The findings below were each checked by Brain.

## Scope and non-goals

1. **The suite is red at the reviewed commit.** `tests/test_docs.py`
   `test_every_documented_command_exists` reads a sentence in round 025's
   report (`tools/fw.py`, then the word "and", then another file name) as an
   undocumented command `and`. This is the second time the pattern has fired on prose (the round 025
   brief tripped it too). Fix the class: the test must still fail on a genuinely
   undocumented or misspelt command where a command is written (for example
   `tools/fw.py` followed by the misspelling `prmpt`), and must not fail on
   prose that mentions `fw.py` followed by an ordinary word. Leave round 025's report text as it is.
2. **Wrong project name in prompt headers.** `project_name` takes the first `# `
   heading of `AGENTS.md`, which in the owner's projects gives
   "AGENTS.md — coordination model for edopro-retro-formats" and
   "AGENTS.md — edopro-next". The header must show a short, stable project name:
   the repository name from `origin` (without `.git`), else the folder name.
   Check it against all three projects and this repository.
3. **Attachments are not scanned for personal data.** The scan reads
   `docs/rounds/*/*.md` only, so `docs/rounds/<id>/attachments/`, where logs and
   long lists go, is never checked. Include it.
4. **A re-review prompt fails at its first command.** The Verifier prompt always
   names `.worktrees/verifier-<number>`; after a first review that folder usually
   exists, so `git worktree add` fails. A prompt for a second review of the same
   round must work as written.
5. **Tier 0 wording.** An unmerged Tier 0 round (no seats) must not be described
   as "every seat has reported"; say what the owner should do (for example, ask
   Brain to merge it).
6. **Report accuracy.** Do not claim that a report-only commit cannot change CI:
   this round's evidence must include CI at the final report commit, or say
   plainly that it was not seen.
7. `docs/state.md`: the queue line names round `025-release-3-1-0`; make it name
   rounds 025 and 026.

Non-goals: anything not listed. No new features, no rewording of framework text
beyond what an item needs, no budget changes.

## Invariants

All of round 025's invariants (see its brief): Python 3.9 and the standard
library for installed files; no personal data in tracked files; updates never
overwrite edited or project-owned files; word budgets hold; no push to `main`.

## Acceptance criteria

1. The full suite passes locally, and CI passes on all jobs at the final commit
   you report, including the commit that adds your report. Show the run.
2. Each of items 1–5 has a test that fails at round 025's reviewed commit
   (`6f2d062`) and passes at your head; name each and show both results.
3. `fw.py prompt` output for each of the three projects (scratch clones) shows
   the header `edopro-retro-formats · ROUND …`, `edopro-next · ROUND …`,
   `gx-spirit-caller · ROUND …`; paste the first line of each.
4. Round 025's per-issue tests still pass.

## Required evidence

```
python3 -m unittest discover -s tests -t . -v
ruff check --select F,E9,B,UP --target-version py39 tools templates tests
python3 tools/fw.py --cwd <scratch clone of each project> prompt --round <an id> --role verifier
```

plus each item's test failing at `6f2d062` and passing at your head, and the CI
run for your report commit.
