# Framework state

The durable state of this repository: the owner's standing decisions, what is
queued and why, and what was deliberately decided against. It exists so that a
Brain opened on any machine, in any tool, can continue without this repository's
chat history. Keep it short; point at documents rather than repeating them.

Live state — current commit, open pull requests, CI, branches, worktrees — is
**derived**, never stored here. Anything below that carries a date is a historical
anchor, not a claim about now.

Last updated: 2026-09-21, by the framework's Brain.

## Starting the framework's Brain

Paste this into a fresh session opened in this repository's primary checkout:

```
You are the Brain for the agentic-framework repository (remote cntrl-alt-lenny/agentic-framework, default branch main). This repository is the framework itself and has not fully adopted itself yet: your contract is framework/roles/brain.md, and this repository's durable state is docs/state.md. Read both in full, then framework/CONSTITUTION.md, framework/kickoff.md, framework/git-and-isolation.md and framework/reports.md. Pull first. Derive the live state yourself: open pull requests, branches, CI, and the shared completion-report inbox. Then check the Dev Hub's framework-feedback folder for anything newer than the last reply there. Then tell me in plain English where things stand and what the next step is.
```

## The owner's standing decisions

These override the framework's defaults for this owner's projects. Each was made
explicitly by the owner.

- **Merges need the owner's explicit approval** (2026-09-16). Brain reviews,
  recommends accepting or rejecting, and merges with `gh pr merge --merge` only
  after the owner says yes. This departs from framework/roles/brain.md, which lets
  Brain merge routine work itself; a sanctioned way to record such an override is
  queued below.
- **The owner is not a programmer.** Explain in plain English, briefly, without
  commit hashes or git jargon unless they matter.
- **Prompts** are code blocks with each paragraph on one line. Always say the send
  order: the Verifier prompt goes only after the executor has finished, because no
  session waits on its own.
- **Chats** (2026-09-16). One standing chat per seat, reused across rounds. Ask for
  a fresh or cleared chat only for a correction after a rejected round, or a chat
  that has grown very long, and say why next to that prompt. Never send a Verifier
  prompt into another seat's chat.
- **One machine at a time** (2026-09-21). The owner alternates between a Mac and a
  Windows 11 desktop in blocks, and switches only between rounds. Before leaving a
  machine: "I'm switching machines. Make sure nothing is left behind and update
  the state file." On arrival: "I've switched to this machine. Catch up from
  GitHub and the Dev Hub, then tell me where we are."
- **The README standard** lives in this repository at `standards/readme.md`. Do not
  suggest a GitHub profile repository for it.

## Where things live

- **Dev Hub**, the shared folder the project Brains use to message each other and
  report framework problems: Google Drive for desktop, account
  leonardohrubino@gmail.com, `Software/Dev Hub`. On the Mac:
  `~/Library/CloudStorage/GoogleDrive-leonardohrubino@gmail.com/My Drive/Software/Dev Hub`.
  On the Windows desktop: `D:\Google Drive\Software\Dev Hub`. Its `README.md` holds
  the rules; `framework-feedback/` is this Brain's inbox; replies are new files.
  Read it only when the owner says to. Sync between machines can take minutes.
- **Projects using the framework** (2026-09-21): edopro-retro-formats (first
  adopter, on an older framework copy), edopro-next (adopted; guard to be installed
  against fed26f36), gx-spirit-caller (adoption under way in three rounds). Each
  runs its own Brain; see the Dev Hub's `projects.md`.

## Queued, in order

1. **A sanctioned way to record an owner override.** `tools/authority.py` judges
   wording rather than meaning, so the owner's approval rule is flagged in one
   phrasing and passes in another, and there is no official format for recording
   it. Reported by gx-spirit-caller, reproduced here.
2. **Adoption bootstrap.** A project's own adoption round must run
   `tools/checkout.py` and `tools/report.py` before they exist in the project;
   document running the framework's copies by absolute path. Hit by two projects.
3. **The Brains' mailbox and upstream feedback,** written into the framework as an
   optional convention that names no particular storage.
4. **Releases and updates.** Numbered framework releases, a written procedure for
   a project to update to a pinned release as a normal reviewed round, and the
   adopted framework version recorded in the project. Then ask
   edopro-retro-formats to update.
5. **Name a task mismatch in the delivery check.** When a report for the role
   exists at the exact head under a different task, say so rather than pointing
   at another clone. Seen in round 18.
6. **This repository adopts itself fully.** This file is the first step.
7. **Housekeeping as a routine.** Brain deletes branches whose work is merged, as
   part of closing a round. Removing files is a reviewed round like any other
   change, and nothing that is the only record of something is deleted.

## Deliberately not done

- **Detecting vendor names in declared branch namespaces.** Impossible without a
  list of provider names, which the constitution forbids. A declared namespace is
  documented as a reviewed human decision instead.
<!-- guard:counterexample -->
<!-- guard:violation branch-namespace roles=builder text="nebula/builder-task" -->
- **A rule catching role-first branch scopes** such as `nebula/builder-task`.
  Deferred until edopro-next reports how the guard behaves against its real
  convention. Counterexample: `meta/builder-contract-update` is legitimate work
  about the Builder contract. The honest distinction is subject versus lane.
<!-- /guard:counterexample -->

- **Detecting branch names written in prose without backticks or wrapped across
  lines.** Also missing on main before round 18; deferred.
- **Making the Windows and macOS CI jobs required.** The owner's decision, once
  they have run cleanly on more changes.
- **Brain launching executor and Verifier sessions itself.** Offered; the owner
  keeps the relay.
- **Recording which model ran each seat.** Declined by the owner; reports record
  the operating system automatically instead.

## Lessons that shape briefs

- Executors tend to fix the listed examples rather than the class. Every brief
  asks for adversarial cases beyond its examples, and Brain re-derives with cases
  of its own.
- Check every Verifier finding yourself; some are over-strict. In round 18 one
  was caused by Brain's own prompt contradicting an earlier decision, so check a
  set of corrections against each other before issuing it.
- When a review comes back clean, break a guard in a scratch copy and confirm the
  tests fail.
- A reused chat can carry the previous round's labels into a report. The delivery
  check catches it; the fix is the executor rewriting its own report, never Brain
  writing it for them.
