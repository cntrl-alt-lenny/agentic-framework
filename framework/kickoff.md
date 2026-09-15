# Starting and running a round

The owner's side of the loop, written so a project can be picked up from
**completely fresh sessions** with no conversation history anywhere.

Everything else in this framework describes what the roles do. This describes
what the *owner* does, and it is deliberately short: two or three things to
paste, depending on whether the project has a standing Verifier, and nothing to
remember between them.

## The loop

```
Brain ──> Builder ──> [Verifier] ──> Brain ──> …
  │          │             │              │
  │          └── does the work            └── adjudicates, merges what it
  │                        └── reviews delivered work  accepts, starts the next round
  └── decides what is next, writes the prompts the topology needs
```

Where the topology has a standing Verifier, Brain issues **both** the Builder
prompt and the Verifier prompt in the same turn, so the owner opens both
sessions immediately without coming back in between. Where it does not, Brain
issues only the Builder prompt. The Verifier waits for the Builder's mechanical
delivery signal: a completion report whose task and head match the branch,
and a branch strictly advanced beyond the base. It never reviews the base. The
two sessions otherwise run independently; the Verifier does not read the
Builder's report body before forming its own view.

## 1. Starting Brain

Open a fresh session in the project and paste this. It is the same text for
every project and every tool:

```
You are the Brain for this project.

Read AGENTS.md first, then docs/agents/roles/brain.md, which is your contract
— follow it. Then rehydrate: derive the live repository state yourself rather
than trusting any document's claims about it, and check whether a round is
already in flight.

Then tell me, in plain English:
  1. where the project actually stands;
  2. what the next round should be, and why that one;
  3. the Builder prompt, as a single self-contained block I can paste;
  4. if and only if this project has a standing Verifier seat, the Verifier
     prompt as a separate self-contained block I can paste; otherwise say that
     no Verifier prompt is needed.

I will run those two in fresh sessions and come back when they report.
```

That is the entire kickoff. It names no tool, no model and no provider, and it
works on any seat that can read the repository and run git.

**If Brain's session cannot read the repository**, say so — it cannot hold this
seat, because rehydration is the first thing its contract requires. Move Brain
to a session with repository access rather than pasting state in by hand.

## 2. Running the Builder and the Verifier

Paste each block Brain produced into its own fresh session, in its own
checkout — see [`git-and-isolation.md`](git-and-isolation.md). If there is no
standing Verifier seat, paste only the Builder block.

The Verifier's prompt names the branch and base rather than a commit that may
not exist yet. Its contract tells it to run the delivery check, which requires
the Builder's report provenance and a branch strictly advanced beyond the base,
then resolve the exact head SHA itself. If delivery is not established within
its session, it stops and says **"not delivered yet"**; the owner pastes the
Verifier prompt again later. That is what lets both sessions start at the same
time without weakening exact-SHA discipline: the Verifier reviews one literal
delivered commit, never the base merely because the branch exists.

## 3. Coming back to Brain

Return to the same Brain session — or a completely fresh one, which is the
point of all this — and paste:

```
The Builder has finished. If this project has a standing Verifier, the Verifier
has also finished; if it said "not delivered yet", I pasted its prompt again
later and waited for its review. Re-derive the current state and adjudicate the
round: accept it and merge, or reject it with a corrective brief. Then give me
the next prompt or prompts this topology needs.
```

Brain re-derives rather than trusting what it remembers, reads both reports as
evidence rather than as verdicts, independently re-checks the load-bearing
claims, and then merges or rejects. It reports what it did in plain English.

**A fresh Brain works as well as a continuing one.** If a session is lost, or
the context is stale, or you would rather start clean, open a new one and paste
the kickoff from step 1 — Brain reconstructs everything from the repository.
That is a designed property, not a fallback: see *The repository is the memory*
in the [constitution](CONSTITUTION.md).

## If a report never arrives

A missing report means **unknown** — never that the work failed. Tell Brain
what you know and let it check; [`reports.md`](reports.md) sets out what it
does then, and why "no commit and no report" cannot be read as failure.

## Naming

This document says **Builder** because that is the common case: one executor
seat that implements. The name is the project's to choose in its `AGENTS.md` —
`Builder`, `Worker`, `Decomper`, `Researcher`, or several specialists at once.
Whatever it is called, it holds the executor contract in
[`roles/worker.md`](roles/worker.md), unchanged. Brain uses the project's
declared name in the prompts it writes, so the owner never has to translate.

## What the owner never has to do

Read a diff. Understand a SHA, a branch, or a worktree. Interpret CI. Decide
whether an implementation is technically correct. Approve a routine merge.

If any of those turns up in the loop, that is a defect in the framework rather
than a task for the owner — see the constitution's *operating model*. The
owner decides what gets built and can veto or reverse anything; deciding
whether the work is *correct* is Brain's job.
