# Framework state

The durable state of this repository: the owner's standing decisions, what is
queued and why, and what was deliberately decided against. It exists so that a
Brain opened on any machine, in any tool, can continue without this repository's
chat history. Keep it short; point at documents rather than repeating them.

Live state — current commit, open pull requests, CI, branches, worktrees — is
**derived**, never stored here. Anything below that carries a date is a historical
anchor, not a claim about now.

Last updated: 2026-09-22, by the Builder (round-024-conventions-and-lessons).

## Starting the framework's Brain

Paste this into a fresh session opened in this repository's primary checkout:

```
Before anything else, run python3 tools/checkout.py --seat brain from this repository's primary checkout; if it fails, stop and tell me where you are and where the primary checkout is. You are the Brain for the agentic-framework repository (remote cntrl-alt-lenny/agentic-framework, default branch main). As of 2026-09-22, this repository has not fully adopted itself; verify that against queued item 3 rather than treating this paste as live state. Your contract is framework/roles/brain.md, and this repository's durable state is docs/state.md. Read both in full, then framework/CONSTITUTION.md, framework/kickoff.md, framework/git-and-isolation.md and framework/reports.md. Pull first. Derive the live state yourself: open pull requests, branches, CI, and the shared completion-report inbox. This paste is my instruction to read the Dev Hub once now: check its framework-feedback folder for anything newer than the framework's last reply there, and otherwise read the Dev Hub only when I ask. Then tell me in plain English where things stand and what the next step is.
```

## The owner's standing decisions

These override the framework's defaults for this owner's projects. Each was made
explicitly by the owner.

- **Merges need the owner's explicit approval** (2026-09-16). This departs from
  framework/roles/brain.md, which lets Brain merge routine work itself, and is
  now recorded in the recognised, machine-checked form `tools/authority.py`
  understands — see `framework/CONSTITUTION.md`'s "Recording an override":

  <!-- guard:owner-override routine-approval text="Brain reviews and adjudicates, then merges reviewed work only on the owner's approval, using `gh pr merge --merge` once the owner says yes." -->
  Brain reviews and adjudicates, then merges reviewed work only on the
  owner's approval, using `gh pr merge --merge` once the owner says yes.
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
  the state file." That instruction means: run
  `python3 tools/report.py leave-check --base main` from a clone that can see
  this repository's inbox (see `framework/reports.md`'s "Leaving a machine")
  before saying it is safe to go. A clean result means every local report is
  confirmed merged; anything else names the round still waiting and tells the
  owner, in plain words, which round to wait for or ask about before switching —
  never "it's probably fine". On arrival: "I've switched to this machine. Catch
  up from GitHub and the Dev Hub, then tell me where we are."
- **The README standard** lives in this repository at `standards/readme.md`. Do not
  suggest a GitHub profile repository for it.

## Where things live

- **Dev Hub**, the shared folder the project Brains use to message each other and
  report framework problems: Google Drive for desktop, account
  leonardohrubino@gmail.com, `Software/Dev Hub`. On the Mac:
  `~/Library/CloudStorage/GoogleDrive-leonardohrubino@gmail.com/My Drive/Software/Dev Hub`.
  On the Windows desktop: `D:\Google Drive\Software\Dev Hub`. Its `README.md` holds
  the rules; `framework-feedback/` is this Brain's inbox; replies are new files.
  Read it only when the owner says to, which includes the startup paste above and
  the machine-switching instructions. Sync between machines can take minutes.
- **Projects using the framework** (2026-09-21): edopro-retro-formats (first
  adopter, on an older framework copy), edopro-next (adopted; guard to be installed
  against fed26f36), gx-spirit-caller (adoption under way in three rounds). Each
  runs its own Brain; see the Dev Hub's `projects.md`.

## Queued, in order

2. **DONE (2026-09-22): ask edopro-retro-formats to update.** Numbered releases, an update
   procedure, and adopted-version recording now exist (round-022); the first
   numbered releases 2.0.0 and 2.0.1 were tagged and announced to every project,
   including edopro-retro-formats. The project still needs to be asked to update
   from its older, pre-release framework copy.
3. **This repository adopts itself fully.** This file is the first step.

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
