# 025-release-3-1-0: Release 3.1.0 — the coordination fixes

Tier: 2
Mode: implementation
Supersedes: none

## Goal

Every open framework issue (#18–#27, #29) is fixed as a class, each proven by a
test that fails before the fix and passes after it. After a break, the owner
can see in one command which seat of which round is waiting on them. Taking a
minor or patch release costs a project one light round, and no project can
miss that a release exists. The result is released as 3.1.0 (a minor release:
no contract a project relies on is broken).

## Context

Read first: `AGENTS.md`, `framework/FRAMEWORK.md`, `framework/roles/*.md`,
`docs/feedback.md`, `docs/state.md`, `tools/fw.py`, `tools/adopt.py`, and each
issue in full, comments included (`gh issue view <n> --comments`). Every issue
carries commands that reproduce it; the owner's projects
(`cntrl-alt-lenny/edopro-retro-formats`, `edopro-next`, `gx-spirit-caller`) are
public and can be cloned for evidence. Not worth reading: `history/`, older
CHANGELOG entries beyond 3.0.0.

What the owner actually experiences, in their words: after a break it takes a
long time to work out which chat is waiting for which paste; a Verifier paste
was missed in one round; the status output shows rounds that are not really in
flight and counts like "(+9 more)" nobody can interpret; seat copies of a
project piled up to 8 GB; "not safe to leave this machine" fires on every run in
one project. The fixes must remove these, not add new things to learn.

## Scope and non-goals

In scope, one class per item (the issue says more):

1. **Next action after a break (#26, #27).**
   - `fw.py status` prints, per round in flight, one line per expected seat
     (from the brief's `Tier:` — Tier 2: executor and verifier; Tier 1:
     executor; Tier 0: none), each `not started` / `started` / `reported at
     <sha>` / `stale`, and ends with one line `next: …` naming the single next
     thing the owner should do (a prompt to send, or "ask Brain to judge").
   - `fw.py start` pushes the seat's branch as soon as it creates it, so
     "started" is distinguishable from "never sent".
   - A round named in a later brief's `Supersedes:` is shown as superseded (by
     which round), never as in flight; `delivery --round <old>` says it was
     superseded and never tells a seat to rewrite a rejected report (#27).
   - Replace the unexplained `(+N more)` counts with something a non-programmer
     can read, or drop them.
   - A new `prompt` command in `tools/fw.py`, taking `--round <id> --role <role>`,
     prints the exact prompt for a seat from the same template the Brain card
     uses, header included. Add it to the command list in
     `tests/test_docs.py` (`test_every_documented_command_exists`).
   - The prompt header convention becomes framework text: first line
     `<project> · ROUND <number> · <ROLE>` (`· message N` for a repeat), and every
     seat ends its final reply with `<project> · ROUND <number> · <ROLE> · DONE —
     report pushed at <sha>` (or `STOPPED` / `BLOCKED` with the reason). Brain's
     "Every session" opens with the next-action line. Remove the interim
     "Prompt headers" section from this repository's `AGENTS.md` once the
     framework text covers it.
2. **Round attachments (#24).** Only files named for a role are reports; state
   where a round's supporting files go (for example `docs/rounds/<id>/attachments/`)
   in `docs/rounds/README.md` and the report section of `FRAMEWORK.md`.
3. **"Not safe to leave" false alarms (#18, including its comment).** Work that is
   on GitHub counts as on GitHub: a local branch whose changes are in the default
   branch by squash or rebase merge, a branch whose remote branch was deleted
   after its pull request merged, and a tag the remote holds at the same object.
   Genuinely unpushed work must still be reported (keep a test for that).
4. **Seat checkouts (#29, #19).** The seat prompt template says where a local
   checkout goes (a linked worktree under `.worktrees/<role>-<round>` inside the
   project, git-ignored; or a cloud workspace), `adopt.py` makes sure
   `.worktrees/` is ignored, the Brain card's merge step removes that round's
   worktrees after checking they are clean and pushed, and `fw.py status` lists
   linked worktrees whose branch is merged or gone as removable. `fw.py start`
   warns about uninitialised submodules, as `status` already does (#19).
5. **Updates (#20, #21, #25, plus two gaps found in review).**
   - `adopt.py --update` says plainly when there is nothing to do, and prints
     `record` only when the manifest would change (#20).
   - It names files it did not install in folders an adapter installs into
     (for example a project's own `.claude/agents/builder.md`) (#21).
   - A seed file the project deleted stays deleted, with a documented way to say
     so (#25).
   - `--dry-run` prints the "What an adopter must do" steps too (the CHANGELOG
     says it does; today only the real run does).
   - **No release can be missed:** the Brain card proposes an update round for
     any newer release that `status` reports, not only major ones.
   - **Minor and patch updates are a light round:** Tier 1 (executor only; Brain
     re-derives), because `adopt.py` never overwrites an edited file and the
     project's own checks run. Major updates stay Tier 2. Update
     `FRAMEWORK.md` "Framework releases" to match.
6. **Checks (#22, #23).** The personal-data scan either covers every tracked
   Markdown file or its message and documentation say exactly what it covers;
   decide which, from the evidence in #22. `fw.py report` runs the project's
   checks on the report it is about to commit and refuses a report that would
   fail them, saying how to describe a finding without repeating it (#23).
7. **An "Idea or question" issue form** beside "Framework feedback", for
   proposals and questions that are not defects (the owner asked where ideas
   like #26 belong).
8. **Addendum, 28 Sept (two findings from gx-spirit-caller while this round ran).**
   - **A re-review must win (#30).** When two review branches of the same round
     are both delivered, `delivery` recommends the one whose reviewed commit
     descends from the other's, never the older one by name order; if neither
     descends from the other, it recommends nothing and says why. Reproduce it
     with a fix that only rewrites the worker report (the shape in #30's
     comment), not only with a code fix.
   - **A report must not break the project's own checks (#23, second comment).**
     Extend item 6: besides `fw.py check`, a project can name one fast check
     command (for example in `docs/agents/framework.json` `settings`) that
     `fw.py report` runs on the tree it is about to commit, refusing on
     failure. The Worker and Verifier cards say that text quoted in a report
     carries no live relative links and no personal paths (quote it as code).
9. **Release mechanics.** `VERSION` 3.1.0; a CHANGELOG entry saying what changed,
   why, words and lines added and removed, and "What an adopter must do";
   `tests/test_adopt.py` extended with a fixture for each defect that came from a
   real project's layout (a seat file named for the project's executor, a
   deleted seed, a squash-merged round, archive tags, a superseded round, a
   round attachment).

Not in scope: new roles, new seats, any change to the merge rule or tiers other
than item 5, anything that makes a project edit framework files, anything that
adds a required step for the owner. Do not tag the release: Brain tags after
the owner's yes.

## Invariants

- Rules and invariants in `AGENTS.md`: Python 3.9 and the standard library only
  for installed files; no personal data in tracked files; updates never
  overwrite an edited or project-owned file; `tests/test_adopt.py` still
  migrates a 2.x-shaped project.
- Word budgets (`tests/test_docs.py`): stay within them by removing as many words
  as you add. `framework/roles/brain.md` is at 705 of 750; if it truly cannot fit,
  raise that one budget by at most 100 words, visibly, and justify it in the
  report. No other budget changes.
- Rule 12: do not push to `main`; work on your seat branch.
- Nothing already working in the owner's projects may break: every fix is
  backwards compatible with 3.0.0 projects and their existing round folders.

## Acceptance criteria

1. Each issue #18–#27, #29 and #30 (and #23's second comment) has at least one test that fails at `v3.0.0` and
   passes at your head. The report names each test and shows it failing at the
   old commit (break-then-fix or run against `v3.0.0`'s `tools/`).
2. On a scratch copy of each of the three projects, `fw.py status` (from your
   head) shows no false "not safe to leave", no superseded round as in flight,
   and a correct `next:` line for the rounds actually in flight today.
3. `adopt.py <project> --update --dry-run` against a fresh clone of each of the
   three projects: output pasted; it plans only the intended changes, prints the
   adopter steps, and reports nothing to do where nothing changes.
4. The full suite passes on your machine; ruff passes; CI passes on Linux,
   Windows and macOS at the head you report.
5. Word budgets hold (or the one permitted raise is justified).
6. The CHANGELOG entry's "What an adopter must do" is a short list a project's
   Brain can follow in one Tier 1 round.
7. The report lists every item in scope as done, or not done with the reason.

## Required evidence

```
python3 -m unittest discover -s tests -t . -v
ruff check --select F,E9,B,UP --target-version py39 tools templates tests
python3 tools/adopt.py <fresh clone of each project> --update --dry-run
python3 tools/fw.py --cwd <scratch copy of each project> status
```

plus, for every issue, the named test failing at `v3.0.0` and passing at your
head, and the CI run for your final commit.
