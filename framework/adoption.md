# Adopting this framework

Written for an **agent** applying this framework to a repository. The owner's
side of this is one sentence: *"Apply the framework at `<path or URL>` to this
project."*

## What adoption produces

| In the target repository | What it is |
|---|---|
| `AGENTS.md` | The project's coordination document: its declared topology, its authority statement, its own invariants, and pointers. **This is the only file that needs real thought.** |
| `docs/agents/CONSTITUTION.md` | The authority model and operating principles, copied verbatim. |
| `docs/agents/adapters.md` | Provider-adapter boundary, copied verbatim. |
| `docs/agents/briefs.md` | Brief format and identifier rules, copied verbatim. |
| `docs/agents/evidence.md` | Evidence discipline, copied verbatim. |
| `docs/agents/git-and-isolation.md` | Checkout and branch isolation rules, copied verbatim. |
| `docs/agents/kickoff.md` | The owner's kickoff loop, copied verbatim. |
| `docs/agents/lifecycle.md` | Round lifecycle, copied verbatim. |
| `docs/agents/reports.md` | Completion-report mechanism, copied verbatim. |
| `docs/agents/topologies.md` | Topology choices, copied verbatim. |
| `docs/agents/roles/README.md` | Role vocabulary guidance, copied verbatim. |
| `docs/agents/roles/brain.md` | Brain contract, copied verbatim. |
| `docs/agents/roles/worker.md` | Worker contract, copied verbatim. |
| `docs/agents/roles/verifier.md` | Optional Verifier contract, copied verbatim. |
| `docs/state.md` | The durable state document, starting nearly empty. |
| `docs/briefs/` | `README.md` (lifecycle), `active.md`, `delivered/`, `archive/`. |
| `tests/test_role_neutrality.py` *(when neutrality is enabled)* | The optional neutrality guard, pointed at the project's declared role set. |
| `tests/test_checkout.py` | The first-action checkout guard. |
| `tests/test_report.py` | Behavioural tests for the installed completion-report tool. |
| `tools/neutrality.py` *(when neutrality is enabled)* | The scanner used by the optional neutrality guard. |
| `tools/authority.py` *(when neutrality is enabled)* | The authority scanner used by the optional installed guard. |
| `tools/textblocks.py` *(when neutrality is enabled)* | Shared counterexample parsing used by the optional installed guards. |
| `tools/checkout.py` | The first-action checkout check. |
| `tools/report.py` | The provider-neutral completion-report writer every Worker and Verifier contract requires — installed unconditionally, with no `--adapter` needed. See `reports.md`. |
| `tools/line_endings.py` | Detects and safely refreshes tracked executable text files whose working-tree bytes are CRLF or mixed. It discovers paths from Git and the files themselves, not from an adapter list. |
| `.gitattributes` | LF normalization for installed scripts and hooks. |
| `.gitignore` | Adoption appends `.worktrees/` without changing existing rules. |
| `.githooks/pre-push` *(optional)* | A client-side gate, if the project has validation worth running early. |
| A provider adapter's files *(optional)* | Installed **where that adapter declares**, which is a property of the tool and not of the adapter's name — see [`adapters.md`](adapters.md). `adopt.py` prints the destination and the seats it installed. |

The mechanical copy can be done by [`../tools/adopt.py`](../tools/adopt.py). The
judgement cannot. Adoption installs the neutrality guard by default and prints
that choice in its plan. An adopter that deliberately defers it can pass
`--no-neutrality`; the four guard files above are then omitted, and the plan
prints that the guard is not installed. The copied documents below describe
the conditional state, not an installation that did not happen.

The framework's own `framework/state.md` is author guidance for this repository
and is deliberately not copied. An adopting project has one durable state file:
`docs/state.md`; this avoids confusing framework guidance with project state.

## Counterexample declarations

When normative text must quote a provider-shaped form in order to prohibit it,
put the quote inside a `guard:counterexample` block and declare the exact
structural violation it demonstrates. The declaration syntax is:

<!-- guard:counterexample -->
<!-- guard:violation compound-lane roles=builder text="Acme Builder" -->
Hand this to the Acme Builder.
<!-- /guard:counterexample -->

The rule is the scanner rule name, `roles=` is the comma-separated role set
against which the example is invalid, and `text=` is that rule's complete
canonical matched text. Matching collapses whitespace and removes balanced
outer backticks, but otherwise requires exact equality: a partial role suffix
cannot name a longer matched token, and a surrounding sentence cannot name the
shorter matched token. The canonical matched text is:

- `compound-lane`: the complete proper-noun-plus-role token;
- `prefixed-lane`: the complete prefixed role token;
- `branch-namespace`: the complete `namespace`/`scope` branch name, whether it
  was written in a Git command or as a backticked branch in prose;
- `queue-identity`: the complete matched queue path; and
- `lane-count`: the complete phrase that quantifies the lanes.

The probe runs the block through the real structural scanner with the declared
roles, independently of the adopting project's role set. Only that declared
rule and matched text are exempted; another finding in the same block remains
visible. A missing, malformed, absent, or unflagged declaration is inert. A
declaration is a visible, reviewable claim, not a magic exemption: a made-up
role in a declaration can make harmless prose appear to be a real violation,
so review declarations as carefully as the text they exempt.

## Updating an adopted framework consistently

The canonical documents and installed tools are one versioned surface. For a
consistent framework update, move these together in one change:

1. Every document in `tools/adopt.py`'s `VERBATIM_DOCS`, installed under
   `docs/agents/` — the complete set is listed in the adoption table above.
2. The baseline installed tools `tools/checkout.py`, `tools/report.py`,
   `tools/line_endings.py`, and `tests/test_checkout.py` and
   `tests/test_report.py`.
3. When neutrality is enabled, `tools/neutrality.py`, `tools/textblocks.py`,
   `tools/authority.py`, and `tests/test_role_neutrality.py`.
4. The installed root `.gitattributes`, and `.githooks/pre-push` when the
   project opted into that hook.

The framework repository's `tools/adopt.py` is the installer and is not copied
into an adopted project; update it by using the same framework revision that
supplies the files above. Updating only the scanner or report tool leaves
copied canonical documents stale; updating only the documents leaves the
installed guard or report mechanism stale. Either mixed state can report
findings caused by the framework's old copies rather than by project-authored
text, or can make a new delivery/line-ending rule unavailable to the adopter.
This is a migration constraint for a consistent update, not a synchronisation
mechanism.

### Existing working trees and line endings

The `.gitattributes` rule is installed unconditionally, but Git does not
rewrite an unchanged working file merely because a new attribute now applies
to it. After adoption, check every checkout in this clone that can run a
framework hook. A separate clone has a separate Git index and must be checked
there independently; the adoption warning cannot inspect it. From each
checkout run:

```
python3 tools/line_endings.py check
```

The detector discovers every tracked executable text file (including adapter
hooks) from Git's executable mode and the file's shebang, and always includes
the `.githooks/` root because Git treats it as a hook topology even before its
mode is committed correctly. It does not claim to inspect another clone.
Treat `w/crlf` or `w/mixed` on a tracked framework script as a portability hazard. The
effect depends on the platform and the shell: on macOS the framework's CRLF
`#!/bin/sh` hook was refused by Git with `cannot exec ... No such file or
directory`; on Windows 11 Pro 10.0.26200 with Git 2.54.0.windows.1 and its
bundled GNU bash 5.3.9 (`igncr` off), the same hook executed its real logic and
rejected a protected-branch push normally. WSL Git, Cygwin Git, and other
Windows shells were not tested. This is not evidence of a Windows guard
bypass; it is why a clone that later moves to macOS or Linux must be repaired.

After the adoption change containing `.gitattributes` is committed, refresh
without a stash. The refresh tool changes only line-ending bytes in the files
it identifies and stages only those paths; it never pops an older stash, drops
local content, or changes another linked worktree. Run it once in each
checkout:

```
python3 tools/line_endings.py refresh
git diff --check
git diff --cached --check
```

Review the staged diff before committing, then commit only the intended
normalization. `tools/adopt.py` also warns during its plan when it detects an
existing unsafe tracked framework script in this clone or one of its linked
worktrees. No stash operation is part of this recovery, so an older stash in
this clone — including one held by another seat's worktree — is neither read
nor dropped.

## Branch namespace declarations

The scanner accepts role names and the coordinator as branch namespaces. A
project whose established branch structure also has milestone, coordination, or
other project-owned namespaces may declare them in its root `AGENTS.md`:

```text
<!-- guard:branch-namespaces prefixes="m<N>,meta" -->
```

`m<N>` means a literal `m` followed by one or more decimal digits; `meta` means
the literal `meta/` namespace. A custom namespace must be a lower-case project
namespace made of letters, digits, and single hyphens, and must have a tracked
project-structure witness at `docs/branch-namespaces/<name>.md`. A namespace
carrying any declared role or coordinator, including a hyphenated one such as
`acme-lead-brain` for `lead-brain`, remains refused. The witness must explain
which established project-owned structure uses the namespace, where that
structure is visible, and why the namespace is not a role or provider identity;
a filename-only formality is not sufficient review. The tracked witness establishes
project-owned structure, but the scanner does not identify providers or prove
that a label is not provider-shaped. Declaring a custom namespace is therefore
a reviewed human decision, not a machine-verified neutrality guarantee. When
neutrality is enabled, its test and command-line scanner discover the same
declaration using the project's declared roles and coordinator and apply it to
every normative document. A malformed, duplicate,
unsupported, role-bearing, or unsupported-by-evidence declaration fails the
installed guard.
Declarations inside fenced or four-space-indented Markdown code, and inside
raw HTML `pre`, `code`, `textarea`, `script`, or `style` blocks, are treated as
examples and are inert. This is a deliberately common-construct boundary: a
declaration embedded in arbitrary inline HTML or a non-standard renderer block
can still look live and needs human review.

## Procedure

### 1. Read the framework first

At minimum [`CONSTITUTION.md`](CONSTITUTION.md), [`topologies.md`](topologies.md)
and [`roles/README.md`](roles/README.md). The rest can be consulted as needed.

### 2. Establish what the project actually is

Before choosing anything, work out from the repository:

- what the project is trying to produce;
- what must never break — its real invariants;
- what its **defects actually look like**. This drives the topology more than
  anything else. If defects are caught by the test suite, a reviewer seat is
  overhead. If defects pass every local check, a reviewer seat is the only thing
  that will find them;
- what validation exists, and what evidence a change should therefore produce;
- whether the hosting provides a merge gate.

### 3. Choose the smallest topology that works

Default to `Owner → Brain → Worker`. Justify anything larger with a reason from
step 2, and write the reason down. See [`topologies.md`](topologies.md).

Do not create a role because a capability exists.

### 4. Run the copy

```bash
python tools/adopt.py <target-repo> \
    --project "<Project Name>" \
    --workers worker \
    [--verifier] \
    [--hooks] \
    [--dry-run]
```

`--workers` takes the executor role names, comma-separated. `worker` for the
default topology; `decomper,scaffolder` or similar for specialists. Brain is
always present. `--verifier` adds the reviewer seat.

Add `--adapter <name>` only if a bundled adapter earns its place. Read the plan
it prints: it names the destination and the seats installed. An adapter ships
one seat per role contract, so a specialist executor is normally launched on the
generic executor seat and scoped by `AGENTS.md` — do not expect a file named
after each declared role.

The script never overwrites an existing file: it writes a `.framework` sibling
and reports the collision instead. Re-running it is safe.

On Windows, the script may complete with a warning because Windows does not
preserve POSIX executable bits. That warning is not a claim that a later POSIX
clone is safe: apply each printed `git update-index --chmod=+x <path>` command
before committing, and check the committed mode from a POSIX environment.

### 5. Write `AGENTS.md` properly

The template gives the structure. The project-specific parts are yours to write:

- **The topology table** — roles and their scopes. Scopes must not overlap.
- **Non-negotiable project invariants** — the things that outrank process.
  Restate them here because they are what an executor most often needs at hand.
- **Evidence per layer** — what validation a change to each part of the
  repository must produce. Be concrete: exact commands, not "run the tests".
- **Where to look** — the project's own map.

Do **not** rewrite the authority model. It is stated once, in the constitution,
and pointed at from here.

### 6. Set up isolation

One isolated checkout per concurrently-active role. See
[`git-and-isolation.md`](git-and-isolation.md).

Adoption ensures `.worktrees/` is present in `.gitignore`, appending one entry
only when neither `.worktrees/` nor `/.worktrees/` is already present. It never
rewrites or reorders an existing ignore file. Launch every role but the
coordinator from a linked worktree:

```bash
git worktree add --detach .worktrees/<role> <default-branch>
python3 tools/checkout.py --seat <role>
```

The check is the first action in every role prompt. A linked worktree derives
its seat from `.worktrees/<role>`. A separate clone can only ever be the
coordinating seat -- its `framework.checkout-seat` must stay unset or name the
coordinator -- because its completion-report inbox is private to it; see
[`git-and-isolation.md`](git-and-isolation.md).

### 7. Make the guard real

If neutrality is enabled, run the test suite and confirm the neutrality test
passes against the project's declared roles. Then **prove it fails** on a
mutation — add a structurally invalid branch example to a normative document,
watch it go red, and remove it. If `--no-neutrality` was selected, record that
the neutrality guard was intentionally deferred; the framework documents do
not imply that it is present.

### 8. Configure protections honestly

Where the hosting supports it, require pull requests, require the checks that
actually matter, enforce for administrators, and constrain force-push and
deletion.

**Do not require a human approval count.** That reinstates the owner as the merge
button, which is the thing this framework exists to remove.

Then write down what is actually enforced — and, explicitly, what is not. If
every agent authenticates with the same credentials, say so.

### 9. Hand over

Brain's first output to the owner is a plain-English statement of what the
project is set up to do and the first ready-to-paste prompt. Not a tour of the
files.

## Adapting an existing project that already has agent conventions

Migrate, do not bulldoze.

- **Keep the project's existing branch convention** if it already derives from
  roles or project structure. Declare the bounded structural forms `m<N>`
  and/or `meta` in `AGENTS.md` using the marker above; a milestone prefix is
  fine. A custom namespace needs the tracked project-structure witness and a
  human review of its meaning; the scanner cannot determine whether the label
  itself came from a provider.
- **Do not rename active branches.** Preserve in-flight work; apply the
  convention to new branches.
- **Retire, do not delete.** Move superseded queues and roles to a clearly
  read-only archive so nobody mistakes history for current policy.
- **Sweep the class.** If one provider-shaped identifier turns up, check
  queues, branches, dispatch prompts, adapters and topology statements before
  concluding it was isolated.
- **Check for stale authority language**, which is the most common thing an older
  setup carries: any text routing routine merge approval back to the human.

## What not to do

- Do not copy the case studies or the failure catalogue into the target. They are
  this repository's history, not the project's.
- Do not edit the role contracts per project. If a contract genuinely does not
  fit, that is a framework finding — raise it here.
- Do not add a provider adapter unless it earns its place. The universal launch
  procedure works without one.
- Do not build project-specific process before the project has produced a real
  problem that needs it.
