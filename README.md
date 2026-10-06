<p align="center">
  <img src="docs/assets/banner.svg" alt="agentic-framework — You decide. AI agents build. Evidence decides what is done." width="100%">
</p>

<h1 align="center">agentic-framework</h1>

<p align="center"><strong>You decide. AI agents build. Evidence decides what is done.</strong></p>

<p align="center">
  <a href="https://github.com/cntrl-alt-lenny/agentic-framework/actions/workflows/ci.yml"><img src="https://github.com/cntrl-alt-lenny/agentic-framework/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/cntrl-alt-lenny/agentic-framework/releases"><img src="https://img.shields.io/github/v/release/cntrl-alt-lenny/agentic-framework?style=flat" alt="release"></a>
  <a href="https://github.com/cntrl-alt-lenny/agentic-framework/actions/workflows/ci.yml"><img src="https://img.shields.io/badge/python-3.9%2B-3776AB?style=flat&logo=python&logoColor=white" alt="python 3.9+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/cntrl-alt-lenny/agentic-framework?style=flat" alt="license"></a>
</p>

## What is this?

A small operating model for building projects with AI agents when the person in
charge is not a programmer. You say what you want. A **Brain** agent plans the
work and checks it, a **Worker** does it in short batches and checks its own
work, and a **Verifier** joins only for mistakes the automatic checks cannot
catch. Nothing counts as done until the evidence shows it, and everything lives
in git, so work started in one tool or on one machine can finish on another,
even weeks later.

```mermaid
flowchart LR
  you([You]) -- what you want --> brain[Brain<br/>plans and checks]
  brain -- short prompt --> worker[Worker<br/>does and checks the work]
  worker -- summary in git --> brain
  worker -. Checked path only .-> verifier[Verifier<br/>reviews the commit]
  verifier -. findings .-> brain
  brain -- merge card --> you
```

## Quick start

1. From a clone of this repository, install it into your project:

   ```bash
   python3 tools/adopt.py <your-project> --project "My Project" --adapter claude-code
   ```

2. Write your project's own rules in its `AGENTS.md`.
3. Open a fresh chat in the project and say *"You are the Brain for this
   project. Follow AGENTS.md."* (in Claude Code, type `/status`). The Brain
   writes every prompt after that.
4. Coming back after a break? `python3 tools/fw.py status` ends with a `next:`
   line saying exactly what to send.

## What works

- **Where am I?** One command shows every batch not yet merged, what it waits
  on, and your next action.
- **Any tool, any machine.** Claude Code, Codex, Gemini or any tool that runs
  git and Python 3.9+, on Windows, macOS and Linux.
- **Light by default.** About 1,340 words of rules, summaries capped at 500
  words, and a two-week scorecard that says whether it is paying for itself.
- **Independent review.** The Brain re-checks the exact commit itself, and a
  Verifier joins for costly mistakes the checks cannot catch.
- **Safe updates.** Projects see new releases on their own, and an update never
  overwrites a file you edited.
- **Honest limits.** It guides agents; it cannot force them. That is why every
  claim needs evidence.

<details>
<summary><strong>What a project gets</strong></summary>

| File | What it is |
|---|---|
| `AGENTS.md` | The project's own rules and its merge rule. Every tool reads this first. |
| `docs/agents/FRAMEWORK.md` | The operating model: 10 rules, how a batch runs, the merge rule, updates. |
| `docs/agents/roles/` | One short card each for Brain, Worker and Verifier. |
| `docs/state.md` | The owner's standing decisions. Short, and checked to stay short. |
| `docs/batches/` | One short summary per batch, and a review when a Verifier was called. |
| `tools/fw.py` | The one tool: `status` and `check`. |
| `docs/agents/framework.json` | The pinned release and a fingerprint of every framework file. |

</details>

<details>
<summary><strong>What is in this repository</strong></summary>

| Folder | What it holds |
|---|---|
| [`framework/`](framework/) | Exactly what projects copy: the core and the three role cards. |
| [`tools/`](tools/) | `fw.py` (installed into projects) and `adopt.py` (installs and updates). |
| [`templates/`](templates/) | Starting versions of the project-owned files. |
| [`adapters/`](adapters/) | Optional pointer files for particular tools. |
| [`docs/`](docs/) | This repository's own state, batches, 3.x rounds and feedback process. |
| [`history/`](history/) | The failures and case studies the framework grew from. |
| [`tests/`](tests/) | Batches run across separate clones, and a 2.x project migrated. |

</details>

## Documentation

- [The operating model](framework/FRAMEWORK.md) and the [role cards](framework/roles/)
- [Which tool can hold which seat](adapters/README.md)
- [What changed in each release](CHANGELOG.md)
- [Reporting a problem or an idea](https://github.com/cntrl-alt-lenny/agentic-framework/issues/new/choose), and [how feedback becomes a release](docs/feedback.md)
- [The README house style](standards/readme.md)

## Credits and license

MIT. See [LICENSE](LICENSE). Tool names are trademarks of their owners.
