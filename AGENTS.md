# agentic-framework

Instructions for every AI agent working on this repository. It is the
framework itself, and it runs on itself: the operating model is
[`framework/FRAMEWORK.md`](framework/FRAMEWORK.md), the role cards are in
[`framework/roles/`](framework/roles/) (in adopted projects they live under
`docs/agents/`), and the tool is `tools/fw.py`. This file adds this
repository's own rules, which take precedence.

Merge rule: owner-approves

## What this repository is

The operating model, its one installed tool, and the installer that adopts
and updates projects. Its product is used by several of the owner's projects,
so a mistake here spreads.

## Roles

| Seat | Card | Scope |
|---|---|---|
| Brain | `framework/roles/brain.md` | Triages feedback, plans releases, judges, merges after the owner's yes. |
| Builder | `framework/roles/worker.md` | Changes the framework as one brief says. |
| Verifier | `framework/roles/verifier.md` | Reviews every round that changes `framework/`, `tools/` or `templates/` (all Tier 2). |

## Invariants

- **The framework serves the projects, not itself.** Change it only for a
  triaged issue, as [`docs/feedback.md`](docs/feedback.md) describes. After a
  release, no further release for ten product rounds unless an issue is
  marked `required`.
- **The word budgets hold** (`tests/test_docs.py`). A change that adds words
  removes as many, or raises a budget visibly with the owner's agreement.
- **Updates stay safe.** `tools/adopt.py --update` never overwrites an edited
  file or a project-owned file. `tests/test_adopt.py` migrates a 2.x-shaped
  project on every run; it must stay green.
- **Every installed Python file runs on Python 3.9** and the standard library
  only.
- **No personal data** — paths, email addresses, account names — in tracked
  files. The repository is public.

## Evidence

| Changed | Required evidence |
|---|---|
| anything | `python3 -m unittest discover -s tests -t . -v` |
| `tools/`, `templates/tests/` | also `ruff check --select F,E9,B,UP --target-version py39 tools templates tests` |
| `tools/adopt.py` | also a `--dry-run` update against a fresh clone of each adopting project, output pasted |

## What is actually enforced

CI runs the suite on Linux, Windows and macOS, plus ruff. Which checks are
required on `main` is the owner's setting; check it with the GitHub settings
page rather than trusting this line. Every agent uses the owner's GitHub
account, so GitHub cannot tell roles apart.

## Where to look

- Standing decisions and the queue: [`docs/state.md`](docs/state.md)
- How feedback becomes a release: [`docs/feedback.md`](docs/feedback.md)
- Rounds: `docs/rounds/`
