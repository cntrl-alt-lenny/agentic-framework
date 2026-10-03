# agentic-framework

The repository's presentation house standard is [standards/readme.md](standards/readme.md).

An operating model for software and research work with AI agents, for an
owner who is not a programmer. Brain plans and judges; Workers implement;
an optional Verifier reviews. Evidence decides what is done.

Any tool with git and Python 3.9+ works on Windows, macOS and Linux.
Committed evidence lets another session resume work, even weeks later.

## What a project gets

| File | What it is |
|---|---|
| `AGENTS.md` | The project's own rules and its merge rule. Every tool reads this first. |
| `docs/agents/FRAMEWORK.md` | The operating model: 14 rules, the round, tiers, reports, updates. About 1,700 words. |
| `docs/agents/roles/` | One short card each for Brain, Worker and Verifier. |
| `docs/state.md` | The owner's standing decisions. Short, and checked to stay short. |
| `docs/rounds/<id>/` | One folder per round: the brief and each seat's committed report. |
| `tools/fw.py` | The one tool: `status`, `start`, `report`, `delivery`, `prompt`, `check`. |
| `tests/test_framework.py` | Runs the project checks with the project's own tests. |
| `docs/agents/framework.json` | The pinned release and a fingerprint of every framework file. |

Optional adapters add pointer files for particular tools. See
[adapters/README.md](adapters/README.md), which also says which of your tools
can hold which seat.

## Using it

**Adopt:** Brain uses a clean framework clone at a verified commit to run
`python3 <framework>/tools/fw.py --cwd <project> status`. It pushes a dedicated
`Mode: adoption` brief naming `Framework-source:` (public URL) and
`Framework-commit:` (full id), then generates seat prompts with that external
tool. Worker installs from the pin; Verifier reviews; Brain judges. The owner
only relays prompts. Damaged installations need diagnosis first.

Worker's mechanical installation, from the pinned framework clone:

```
python3 tools/adopt.py <project> --project "My Project" --adapter claude-code
```

Options: `--verifier`, `--workers builder`, `--hooks`, `--dry-run`.
Existing files are preserved; Worker fills in `AGENTS.md`.

**Run:** open a fresh session in the project and paste the start prompt from
[FRAMEWORK.md](framework/FRAMEWORK.md#the-round). Brain gives you every prompt
after that.

**Update:** `python3 tools/fw.py status` in a project says when a newer
release exists. The update is one command, from a clone of this repository at
the new release, run as a reviewed round:

```
python3 tools/adopt.py <project> --update
```

It replaces framework files nobody edited, leaves edited ones alone with the
new version beside them, removes retired files only when it can prove they
were never edited, and prints what each release asks of the project. Projects
from before 3.0.0 migrate with the same command.

## This repository

| | |
|---|---|
| [`framework/`](framework/) | Exactly what projects copy: the core and the three role cards. |
| [`tools/`](tools/) | `fw.py` (installed into projects) and `adopt.py` (installs and updates). |
| [`templates/`](templates/) | Starting versions of the project-owned files. |
| [`adapters/`](adapters/) | Optional pointer files for particular tools. |
| [`docs/`](docs/) | This repository's own state and its feedback process. |
| [`history/`](history/) | The failures and case studies the framework grew from. Record, not rules. |
| [`tests/`](tests/) | Includes a whole round run across three separate clones, and a 2.x project migrated to this release. |

`python3 -m unittest discover -s tests -t .` runs everything in under a
minute. Framework problems found in projects are reported as issues, handled
as described in [docs/feedback.md](docs/feedback.md).

## Honest limits

Everything here guides agents; nothing forces them. The tool checks what can
be checked mechanically: that a report exists, has the required sections, and
describes the exact commit under review; that state documents stay small; that
tool entry files point at the rules. Whether an agent obeys the rules is shown
only by the evidence it leaves, which is why Brain re-checks it. When every
agent uses the owner's GitHub account, GitHub cannot tell them apart.

## License

MIT. See [LICENSE](LICENSE).
