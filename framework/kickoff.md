# Starting and running a round

The owner's side of the loop, written so a project can be picked up from
**completely fresh sessions** with no conversation history anywhere.

Everything else in this framework describes what the roles do. This describes
what the *owner* does, and it is deliberately short: three things to paste, and
nothing to remember between them.

## The loop

```
Brain ──> Builder ──> Verifier ──> Brain ──> …
  │          │            │          │
  │          └── does the work       └── adjudicates both, merges what it
  │                       └── reviews it            accepts, starts the next round
  └── decides what is next, writes both prompts
```

Brain issues **both** the Builder prompt and the Verifier prompt in the same
turn, so the owner can open both sessions immediately without coming back in
between. The two run independently: the Verifier never sees the Builder's
report before forming its own view, which is the whole reason the seat exists.

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
  4. the Verifier prompt, as a separate self-contained block I can paste.

I will run those two in fresh sessions and come back when they report.
```

That is the entire kickoff. It names no tool, no model and no provider, and it
works on any seat that can read the repository and run git.

**If Brain's session cannot read the repository**, say so — it cannot hold this
seat, because rehydration is the first thing its contract requires. Move Brain
to a session with repository access rather than pasting state in by hand.

## 2. Running the Builder and the Verifier

Paste each block Brain produced into its own fresh session, in its own
checkout — see [`git-and-isolation.md`](git-and-isolation.md). Nothing else is
required of the owner here.

The Verifier's prompt names the branch rather than a commit that may not exist
yet, and its contract tells it to resolve the exact head SHA itself, confirm
ancestry, and stop and say so if the branch is missing or has moved. That is
what lets both sessions start at the same time without weakening the
exact-SHA discipline in [`evidence.md`](evidence.md): the Verifier still
reviews one literal commit, it just establishes which one rather than being
told.

## 3. Coming back to Brain

Return to the same Brain session — or a completely fresh one, which is the
point of all this — and paste:

```
The Builder and the Verifier have both finished. Re-derive the current state
and adjudicate the round: accept it and merge, or reject it with a corrective
brief. Then give me the next round's two prompts.
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
