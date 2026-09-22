# Changelog

Each entry states what changed, why, and what an adopting project must do to
move to it. `tools/adopt.py --update` prints the "What an adopter must do"
section of every release between a project's pinned release and the new one.
Releases are tagged by Brain after the round that produces them merges.

## 3.0.0 — lean core, handoffs in git, one-command updates

An independent audit found the framework cost more time than it saved. Its
reports stayed on the machine where they were written; Workers could not run
in cloud tools or fresh clones; dormant projects had no way to learn a newer
release existed; updates were reconciled by hand; and agents read 10,000 to
21,000 words before starting. This release keeps the operating model — roles,
independent review, evidence over narrative, git as memory — and replaces the
machinery.

- **One core document and three role cards** (about 3,100 words in total)
  replace 14 copied documents (about 21,000 words). Word budgets are tested.
- **Rounds live in `docs/rounds/<id>/`:** the brief and each seat's report,
  committed and pushed. A round can start on one machine or tool and finish
  on another. The private report inbox, `leave-check` and the carry-the-report
  procedure are gone; `fw.py status --leaving` checks what matters (anything
  not pushed) and works with squash merges.
- **Seats are not tied to a folder.** `fw.py start` puts any clone, cloud
  workspace or tool-named branch on the right commit.
- **`tools/fw.py` replaces** `checkout.py`, `report.py` and `line_endings.py`.
  Reports are files with required sections, stamped with the exact commit.
- **`fw.py status`** reports the pinned release against the latest, local
  edits to framework files, rounds in flight, unpushed work and uninitialised
  submodules. **`fw.py check`** (and the installed `tests/test_framework.py`)
  keeps `docs/state.md` short and free of stored commit ids, makes tool entry
  files point at `AGENTS.md`, and keeps personal paths and email addresses
  out of the documents agents read.
- **Updates are one command:** `tools/adopt.py <project> --update`, guided by
  a fingerprint of every installed file in `docs/agents/framework.json`.
- **The merge rule is a project setting**, `owner-approves` (default) or
  `brain-merges`, with a four-line merge card. The wording scanners
  (`neutrality.py`, `authority.py`, `textblocks.py`) and their declaration
  grammar are removed.
- **Tiers** 0, 1 and 2 scale the ceremony to the risk.
- **Commands are shell-neutral:** no heredocs; `python3`, `py -3` or `python`.
- **Framework feedback goes to GitHub issues**, with triage, reproduction,
  batching and a freeze after each release (`docs/feedback.md`).
- **Adapters only point.** The Claude Code adapter now installs `CLAUDE.md`
  (importing `AGENTS.md`), seat files and `/status`; its Stop hook is retired
  because reports are now committed by the seat itself. A `gemini` adapter adds
  a `GEMINI.md` pointer.

Net change: framework documents copied into a project fall from about 21,000
to about 3,100 words; installed Python falls from about 4,500 lines (with
tests) to about 1,000; this repository loses about 15,000 lines and gains
about 4,000, and its suite runs in about 20 seconds instead of 4 minutes.

### What an adopter must do

Run this as one Tier 2 round, with no other round in flight.

1. From a clone of the framework at `v3.0.0`, run
   `python3 tools/adopt.py <project> --update --dry-run`, read the plan, then
   run it without `--dry-run`. It installs the new files, replaces and
   removes 2.x copies it can prove were never edited, and keeps everything
   else, saying why. It also lists documents that would be left linking to a
   removed file; fix those links.
2. **Merge edited copies.** For each `<file>.framework` it wrote, move any
   project-specific content into `AGENTS.md` (or `docs/agents/local/`), then
   replace the file with the `.framework` copy.
3. **Retire what it kept on purpose.** For each file listed as "still refers
   to it", remove the reference (usually the Stop hook entry in
   `.claude/settings.json`, or a project hook calling `tools/line_endings.py`
   or `tools/report.py`), then delete the file. Delete the project's own
   2.x-only documents that restate the framework (for example a local
   `reports.md` or `push-gate.md`) once their project-specific content is in
   `AGENTS.md`.
4. **Make `AGENTS.md` the entry point.** Add `Merge rule: owner-approves` (or
   `brain-merges`), point it at `docs/agents/FRAMEWORK.md`, and move rules
   that live only in `CLAUDE.md` into it. Replace `CLAUDE.md` with a pointer
   (`@AGENTS.md`), or keep its project facts and add that line at the top.
5. **Trim `docs/state.md`** to decisions, parked items and pointers (1,000
   words by default). Move history into an archive document. Keep any commit
   ids under `## Historical anchors`. If project tools genuinely need a longer
   file, raise `settings.state_words` in `docs/agents/framework.json` and say
   why in `AGENTS.md`.
6. **Start new rounds in `docs/rounds/`.** Leave `docs/briefs/` as history,
   and delete `docs/briefs/active.md` once its round is finished
   (`fw.py status` mentions it until then).
7. Run the project's full test suite and `python3 tools/fw.py check`, paste
   both outputs, and remove personal paths the check reports.

## 2.1.0 — conventions, lessons and the active README standard

This release documents an optional, provider-neutral convention for project
Brains to exchange standalone, append-only evidence and report suspected
framework defects upstream. It also makes self-reported tool, model and
operating-system details claims to verify, warns that Windows PowerShell can
change captured line endings, records Brain's routine housekeeping boundary,
and requires sentence-level accounting for durable-state edits and review of
every removal. The active README standard is now part of the framework's
normative scan, and its license guidance matches the live Shields.io wording
and supplies a generic static-badge template for legally fixed upstream
licenses.

### What an adopter must do

Update the installed canonical contracts and documents through
[`framework/update.md`](framework/update.md)'s ordinary reviewed procedure,
then run the project's full validation and both guards. Executors and
Verifiers must verify self-reported environment facts from commands, inspect
line endings in captured text, and list every sentence added and removed when
changing durable state. A project may adopt the optional Brain-feedback
convention using an owner-designated location; that location is configuration,
not a tracked framework path. `standards/readme.md` remains outside `framework/`
and is not copied by adoption; projects using it should read and apply its
active rules, including the generic static-license-badge template, without
editing LICENSE files or repository settings as part of adoption.

## 2.0.1 — scope authority counterexample exemptions exactly

`tools/authority.py`'s `guard:counterexample` handling suppressed every
finding inside a wrapped block unconditionally, regardless of what — if
anything — the block declared. A block declaring only a `tools/neutrality.py`
rule, or declaring nothing at all, silently hid any stale-authority idiom
quoted alongside it from `scan()`, the command line, and CI. `README.md`'s own
counterexample block, which quotes the actual v1 stale-authority phrases
under a `compound-lane`-only declaration, was a live instance of this on
`main`. `tools/neutrality.py` already exempted only a validated finding whose
rule and matched text equal a declaration's; `tools/authority.py` now does the
same — see `_counterexample_exemptions()` and the module docstring's
"COUNTEREXAMPLE BLOCKS" section.

### What an adopter must do

Update the installed `tools/authority.py` (and `tools/textblocks.py`,
`tools/neutrality.py` if not already current) to this release, then run both
scanners over the project's normative documents. A block that used to declare
only one scanner's rule while quoting another scanner's banned form will now
report the previously-hidden finding; add the missing `guard:violation`
declaration for the finding actually present, in its own `guard:counterexample`
block — see `framework/adoption.md`'s "Counterexample declarations": mixing
declarations for different scanners in one block defeats
`tools/neutrality.py`'s own all-or-nothing validation for that block, so keep
each block's declarations owned by one scanner.

### Fixed

- **`tools/authority.py` no longer blanket-suppresses a counterexample
  block's contents.** A block now exempts only a finding whose rule and
  matched text — under the same whitespace/backtick normalisation
  `tools/neutrality.py` already documents — equal a validated
  `guard:violation` declaration inside it; every other finding in the block,
  including one sharing a block with a declaration naming a different
  scanner's rule, is reported normally.
- **`README.md`'s counterexample block**, which quoted v1's real
  stale-authority phrases under a declaration naming only a neutrality
  violation, now carries the matching `routine-approval` and
  `executor-self-merge` declarations, split into per-scanner blocks.

## 2.0.0 — first numbered release

The first framework release with a number a project can pin to. Everything
below the "v2" heading further down this file happened first, under no
release number at all — every adopted project has effectively been tracking
an unpinned, unversioned copy of the framework since v2 replaced v1. This
release is the point where that stops: `VERSION` at this repository's root
now names the current release, `tools/adopt.py` derives it (and this
repository's own remote address) automatically into an adopting project's
`AGENTS.md`, and [`framework/update.md`](framework/update.md) gives that
project a written procedure to move to a newer pinned release later, as an
ordinary reviewed round rather than an ad hoc copy.

### What an adopter must do

A project adopted before this release has no recorded framework version or
repository address in its `AGENTS.md`, and no `docs/agents/update.md`. Bring
it current the same way any later update works —
[`framework/update.md`](framework/update.md)'s procedure, run once against
this release — which installs `docs/agents/update.md` itself, adds the
"Framework" section recording `2.0.0` and this repository's address to
`AGENTS.md`, and leaves every other project-authored file untouched.

### Added

- **Numbered releases.** `VERSION` at this repository's root; this file's new
  per-release structure, each entry stating what changed and what an
  adopter must do.
- **The adopted release and repository address recorded automatically.**
  `tools/adopt.py` derives both — `VERSION`'s content and this clone's Git
  `origin` remote — and writes them into `AGENTS.md`'s new "Framework"
  section. Neither is ever typed by whoever runs adoption.
- **[`framework/update.md`](framework/update.md)**, copied verbatim to every
  adopting project, describing the update procedure: what moves together,
  how to reconcile a diverged file instead of overwriting it, checking line
  endings, and running the round as an ordinary Worker-and-Verifier change
  that never starts mid-round. How a project learns a new release exists is
  left to the owner's own channel; this document does not prescribe one.
- **A recognised, reviewable form for an owner's standing override of the
  routine-merge gate.** `<!-- guard:owner-override <rule>
  text="<sentence>" -->`, validated by `tools/authority.py` against the real
  scanner rather than judged by wording alone — see
  [`framework/CONSTITUTION.md`](framework/CONSTITUTION.md)'s "Recording an
  override" and `templates/AGENTS.md`'s "Owner overrides".
- **A sanctioned route for the round that performs a project's own
  adoption**, before `tools/checkout.py` and `tools/report.py` exist in the
  target — the framework repository's own copies, invoked by path and
  pointed at the target checkout with `--cwd` — and the requirement that
  every framework command run pointed at the seat's own worktree, documented
  in [`framework/adoption.md`](framework/adoption.md). `tools/report.py
  write` gained `--cwd` to make this possible.
- **The delivery check names a task mismatch instead of blaming an
  unavailable report.** When a report for the requested role exists at the
  exact delivered head under a different Brief-ID, `tools/report.py
  delivery` says so by name and still never reports delivery — see
  [`framework/reports.md`](framework/reports.md).
- **A leave-machine check.** `tools/report.py leave-check --base
  <default-branch>` reports every local completion report describing work
  not yet merged into the default branch, so switching machines mid-round is
  visible before it happens rather than discovered cold on the other
  machine. Unresolvable state is reported as unknown, never as safe.

## v2 — general-purpose agentic project framework

v1 was `decomp-agent-framework`: a three-agent, decompilation-specific,
single-vendor coordination layer. v2 keeps the mechanisms that survived
production use across three projects, and replaces the architecture around them.

**This is a historical document.** It quotes v1's text, which the current guards
reject.

### What changed, and why

| v1 | v2 | Why |
|---|---|---|
| Brain reviewed, summarized, then asked the owner to authorise the merge | **Brain merges what it accepts** | v1 made the coordinator a recommender and the owner a merge button. The owner keeps direction, veto, reversal and a reserved list; routine technical acceptance is delegated. |
| Owner listed as merging pull requests and adding agents | Owner sets direction; is not expected to read a diff | The whole point of the framework. |
| Coordinator could self-merge "when the owner is away" | Authority does not depend on who is at the keyboard | Absence-based authority gives different outcomes for identical changes. |
| An executor role held emergency self-merge rights | **No executor ever accepts or merges its own work** | Urgency is exactly when that boundary bends, and exactly when it must not. |
| Exactly three agents, named for one problem domain | **Three role *contracts*; topology is a project decision** | Three real projects settled on three different topologies. What must not vary is authority. |
| Roles defined partly by what tooling a session had | Roles defined by **capabilities** | "Runs locally with the toolchain" is a capability requirement, not a role. |
| Vendor mechanics mixed into the role definitions | **Contract / adapter split**, with adapters that point rather than paraphrase | A vendor adapter in a real project kept describing a superseded authority model after the contracts moved on. |
| Neutrality asserted in prose | **Neutrality enforced structurally**, proved against a novel provider name | Prose drifts; a blacklist is stale on the next provider's launch day. |
| Push guard as a tool-level command-text hook | **Git `pre-push` layer**, with honest limits documented | The tool-level guard was defeated seven ways in one project and fired for one vendor only. |
| Churn-heavy state log | **Durable state only; live state derived** | A state document grew past a thousand lines and started contradicting the repository. |
| Interactive installer with six domain placeholders | **Adoption is a documented procedure for an agent**, plus a small non-interactive copy script | Telling an agent "apply this framework here" is simpler and more robust than an installer for a human. |

### Removed

- `framework/docs/decomp-workflow.md` — the byte-matching walkthrough. Entirely
  domain-specific.
- `decomper` and `scaffolder` as *the* role set. They survive as topology
  examples in [`framework/case-studies.md`](framework/case-studies.md).
- `pre_bash.py` — the tool-level push guard. Wrong layer; replaced by a sample
  git `pre-push` hook with its limits stated.
- `post_edit.py` — a lint-and-test-on-edit hook with domain-named configuration.
  Project-specific, and it was configuration surface rather than framework.
- The six domain placeholders (`GAME_NAME`, `TOOLCHAIN_NAME`, `BASEROM_PATH`,
  `REGIONS`, and the rest). Role contracts now have **no placeholders at all**,
  so they cannot drift per project.
- `install.py`'s interactive prompting, YAML config and update mode.

### Kept, generalized

- `AGENTS.md` as the project's coordination document.
- `<role>/<scope>` branch naming — now enforced structurally.
- The brief directory and the separation of stable manifest from churning state.
- Isolated checkouts per concurrently-active role.
- "Slugs are roles, not providers" — v1 said this in prose. v2 makes it a rule
  with a test.
- The session-reply inbox hook, demoted to an explicitly optional adapter
  convenience whose absence means **unknown**.
- The installer's fork-safety instinct: never overwrite, write a sibling,
  support a dry run.

### Added

- A [constitution](framework/CONSTITUTION.md) as the single normative root.
- Three provider-neutral [role contracts](framework/roles/).
- [Topology guidance](framework/topologies.md) with three worked shapes.
- [Evidence standards](framework/evidence.md) — exact-SHA discipline,
  re-derivation, what makes a guard real.
- A [failure catalogue](framework/failure-catalogue.md) of 34 patterns observed
  in production, each with its general lesson.
- [Case studies](framework/case-studies.md) of the three projects this was
  derived from.
- An invariant suite: provider neutrality, authority, adapter boundaries,
  adoption behaviour, guard honesty, repository integrity.
- `tools/neutrality.py`, `tools/authority.py` and `tools/textblocks.py` —
  shipped to adopting projects so the guards travel with the framework.

### Migration from v1

There are no known external consumers, so no compatibility shims were kept.

For a project on v1:

1. Run `tools/adopt.py` against it. Existing files are never overwritten; the
   framework version lands beside them as `.framework` siblings.
2. Merge each collision by hand, then delete the sibling.
3. Delete `.claude/hooks/pre_bash.py` and `post_edit.py`, and their `settings.json`
   entries. Replace with a git `pre-push` hook if the project has validation
   worth running early.
4. Sweep for stale authority language. The installed guard finds it: any text
   routing a routine merge back to the owner, or granting an executor
   self-merge rights.
5. Keep active branches as they are. Apply the role-based convention to new ones.
6. Move round-by-round history out of the state document into archived briefs.

### Repository name

`decomp-agent-framework` describes a domain the framework no longer has. See
the README for the current name and the reasoning.
