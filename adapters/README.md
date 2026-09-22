# Adapters, tools and devices

The framework needs one thing from an AI tool: that it can run `git` and
`python3` (or `py -3`) in the project folder. Everything else is convenience,
and conveniences live here, in adapters, which only ever point at `AGENTS.md`
and the role cards.

| Adapter | Installs | For |
|---|---|---|
| `claude-code` | `CLAUDE.md` pointing at `AGENTS.md`; `.claude/agents/` seat files; a `/status` command | Claude Code (terminal, desktop, web) |
| `gemini` | `GEMINI.md` pointing at `AGENTS.md` | Gemini CLI, and Antigravity versions that load `GEMINI.md` rather than `AGENTS.md` |

Codex (CLI and cloud) reads `AGENTS.md` directly and needs no adapter.

## Which tool can hold which seat

| Tool | Brain | Worker / Verifier | Notes |
|---|---|---|---|
| Claude Code (terminal or desktop) | yes | yes | any OS |
| Claude Code on the web | yes | yes | starts from a fresh clone; `fw.py start` handles that |
| Codex CLI / Codex cloud | yes | yes | reads `AGENTS.md` natively |
| Google Antigravity | yes | yes | not tested by this repository; install the `gemini` adapter if it ignores `AGENTS.md` |
| ChatGPT in a browser | advisor only | no | cannot run commands; with a GitHub connection it can read a round's brief and reports |

## Which device can run what

| Device | Local seats | Notes |
|---|---|---|
| macOS (Apple Silicon) | yes | Apple's own `python3` may be 3.9; the framework supports it, some projects need newer |
| Windows 11 | yes | use `py -3`; Git for Windows provides `git` |
| Fedora | yes | `git` and `python3` are standard |
| SteamOS (Steam Deck) | via a cloud tool; locally inside a container | the system is read-only, so install tools in a `distrobox` container rather than the base system; not tested by this repository |

Any seat can also run in a cloud tool from any device with a browser, because
everything a round needs is on GitHub.

## Writing an adapter

Put the files under `adapters/<name>/files/` exactly as they should appear in
a project, and list in `adapter.json` which ones the project owns afterwards
(`seeds`). Each file stays under 80 words and points at `AGENTS.md` or
`docs/agents/`; `tests/test_docs.py` checks both.
