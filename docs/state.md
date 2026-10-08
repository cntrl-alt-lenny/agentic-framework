# State

The owner's standing decisions for this repository, what is queued, and what
was decided against. No live state: run `python3 tools/fw.py status`.

## Where we are going

Release 4.0 replaces rounds with batches: a short prompt, a Worker that
checks its own work, Brain's review, and a Verifier only on the Checked path.
The rules shrank from about 3,100 words to about 1,300. The next job is
rolling it out and measuring whether it pays for itself in each project.

## Owner decisions

- **Merges need the owner's yes** (2026-09-16). This is now the framework's
  default merge rule, `owner-approves`, with a four-line merge card.
- **The owner is not a programmer.** Plain English, no commit ids or git
  jargon unless they matter. Prompts are code blocks, one line per paragraph,
  with the send order stated.
- **Devices** (2026-09-22): a MacBook (Apple Silicon), a Windows 11 desktop, a
  Fedora machine, and two Steam Decks running SteamOS, switched without
  warning. Tools in use: Claude Code, ChatGPT and Codex, Google Antigravity;
  others may replace them. See `adapters/README.md`.
- **Framework feedback goes to GitHub issues** on this repository
  (2026-09-22), triaged as `docs/feedback.md` says. The shared Drive folder
  is no longer part of the framework: it cannot be reached from Linux or the
  Steam Decks, and its location differed per machine. Anything still in it is
  moved to issues when next read.
- **Slim the framework** (2026-10-06). Under 3.x, six projects wrote about
  206,000 words of briefs and reports in 39 rounds, and gx-spirit-caller's
  progress stood still for five weeks; its light batches then moved it in a
  day. The owner chose to slim rather than drop the framework, and lifted the
  release freeze: releases ship when the owner says yes.
- **The README standard** lives here at `standards/readme.md`.
- **One standing chat per seat** may be reused across batches; a fresh chat is
  better after a rejected batch or when a chat has grown long.

## Scorecard

The framework's scorecard is its projects' scorecards. First review due
2026-10-20, two weeks after 4.0.0.

## Queued, in order

1. **Finish release-pin alignment between product batches.** Each project's
   Brain applies published releases from their exact clean tag, preserves
   project-owned guidance, checks the result, and seeks its owner's merge
   approval. Do not duplicate another Brain's update.
2. **Recheck outstanding feedback against 4.0.1**, without changing shared
   tools or shipping a release: UTF-16 privacy scanning (#31), retired-hook
   manifest wording (#36), and submodule checkout cleanup (#43). Keep
   reproductions synthetic and separate a missed scan from actual disclosure.
   Brain judges the evidence before proposing any fix.
3. **Two-week scorecards** in each project decide what changes next. Keep
   2026-10-20 as the first evaluation date, including Spirit Caller's light
   workflow results. Product progress, owner relay counts and corrective
   batches are separate measures; missing measurements remain unknown.

## Historical anchors

- **Rollout refresh, 2026-10-08.** GitHub's default branches for edopro-next,
  edopro-retro-formats, fe6-next, fire-emblem-awakening-assistant,
  gx-spirit-caller and mgs-mc-modkit all recorded 4.0.0 when inspected.
  Spirit Caller has adopted 4.0; the earlier instruction to defer adoption
  until 20 October is obsolete. Its evaluation date still stands.
- **Published release, 2026-10-07.** 4.0.1 aligns release records with the
  rollout's files and restricts installation to a clean release tag.
- **Old rounds closed, 2026-10-06.** Rounds 028 and 029 were closed unmerged
  when 4.0 removed the commands they repaired, as recorded in issue #32.
  Their branches remain historical evidence, even when `status` lists them.
  Preserve their work and checkouts; deletion needs the owner's decision.
- **Pilot evidence.** The separate Spirit Caller findings branch records
  early results before the 4.0 decision. It is historical evidence, not a
  pending instruction to repeat or delay adoption. It remains preserved.

## Parked, and why

- **Server-enforced owner approval.** GitHub cannot tell the owner from an
  agent that uses the same account. A separate account for agents would
  enforce it; not worth the setup unless an agent ever merges without a yes.
- **Wording scanners** (`neutrality.py`, `authority.py`, removed in 3.0.0).
  They checked phrasing, not behaviour, missed paraphrases, and blocked real
  rounds with false alarms.
- **A per-clone report inbox** (removed in 3.0.0). Reports are committed with
  the work instead, so they reach every machine.
- **Automatic launching of seats by Brain.** The owner keeps the relay.
- **Recording which model ran each seat.** It does not change what the
  evidence shows.

## Lessons that shape prompts

- Executors fix the listed examples rather than the class: ask for cases
  beyond the examples, and re-derive with cases of your own.
- Check every Verifier finding yourself; some are over-strict.
- When a review comes back clean, break the change in a scratch copy and
  confirm the tests fail.
