# {{PROJECT}}

Instructions for every AI agent working in this repository, whatever tool it
runs in. Tool-specific files (`CLAUDE.md`, `GEMINI.md` and similar) only point
here.

This project runs the agentic framework: read
[`docs/agents/FRAMEWORK.md`](docs/agents/FRAMEWORK.md) and your role card in
[`docs/agents/roles/`](docs/agents/roles/). This file adds the project's own
rules, which take precedence over the framework's.

Merge rule: owner-approves

<!-- The merge rule is owner-approves (Brain merges after the owner says yes to
     the merge card) or brain-merges (Brain merges accepted work itself). Only
     the owner changes it. -->

## What this project is

<!-- Two or three sentences: what it produces and for whom. -->

## Roles

{{ROLE_TABLE}}

## Invariants

<!-- The things that must never break, each with where it comes from, so it can
     be checked rather than trusted. For example: what is authoritative and
     must not be modified, licensing limits, what must never be claimed as
     done. Delete this comment. -->

## Evidence

Run what is relevant to what you changed and paste the real output with its
exit status (see the framework's rule 7).

| Changed | Required evidence |
|---|---|
| <!-- path or area --> | <!-- the exact command(s) --> |

<!-- If a check cannot fail for some kind of change, say so here: citing it as
     evidence for that kind of change is then a blocking finding. -->

## What is actually enforced

<!-- The truth, kept true. For example: "GitHub requires pull requests and the
     'tests' check on main (checked <date>). Every agent uses the owner's
     GitHub account, so GitHub cannot tell roles apart; that executors never
     merge is a rule the agents keep, not a lock." -->

## Where to look

- Standing decisions and what is parked: [`docs/state.md`](docs/state.md)
- Rounds, one folder each: [`docs/rounds/`](docs/rounds/)
