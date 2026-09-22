# State

The owner's standing decisions for this repository, what is queued, and what
was decided against. No live state: run `python3 tools/fw.py status`.

## Where we are going

Release 3.0.0 cut the framework to one core document, three role cards and
one tool, moved every handoff into git, and added safe one-command updates.
The next job is not more framework: it is migrating the three projects and
then running real product rounds on it.

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
- **Releases are batched**: at most one every two weeks, and none for ten
  product rounds after a release, unless an issue is marked `required`.
- **The README standard** lives here at `standards/readme.md`.
- **One standing chat per seat** may be reused across rounds; a fresh chat is
  better after a rejected round or when a chat has grown long.

## Queued, in order

1. **Migrate each project to 3.0.0** — each project's own Tier 2 round, run
   there, using `python3 tools/adopt.py <project> --update` from a clone of
   this repository at `v3.0.0`. Order: edopro-retro-formats, edopro-next,
   gx-spirit-caller (its large state document and its pre-framework queue
   need a decision first: which one is the project's real state model).
2. **Ten product rounds with no framework release.** Then review where time
   actually went, with numbers.

## Deliberately not done

- **Server-enforced owner approval.** GitHub cannot tell the owner from an
  agent that uses the same account. A separate account for agents would
  enforce it; not worth the setup unless an agent ever merges without a yes.
- **Wording scanners** (`neutrality.py`, `authority.py`, removed in 3.0.0).
  They checked phrasing, not behaviour, missed paraphrases, and blocked real
  rounds with false alarms.
- **A per-clone report inbox** (removed in 3.0.0). Reports are committed with
  the work instead, so they reach every machine.
- **Automatic launching of seats by Brain.** The owner keeps the relay.
- **Recording which model ran each seat.** Reports record the operating
  system automatically instead.

## Lessons that shape briefs

- Executors fix the listed examples rather than the class: ask for cases
  beyond the examples, and re-derive with cases of your own.
- Check every Verifier finding yourself; some are over-strict.
- When a review comes back clean, break the change in a scratch copy and
  confirm the tests fail.
