#!/usr/bin/env python3
"""Copy this framework into a target repository.

This does the **mechanical** half of adoption. The judgement half — choosing a
topology, writing the project's invariants and its evidence table — is described
in `framework/adoption.md` and is not automatable.

    python tools/adopt.py <target> --project "Name" [options]

Options:
    --project NAME     Human-readable project name. Required.
    --workers a,b      Executor role names (default: worker). Brain is always
                       present; a specialist is the Worker contract plus a scope
                       statement, not a new contract.
    --verifier         Include the independent reviewer seat.
    --coordinator NAME Name of the coordinating role (default: brain).
    --hooks            Install the sample git pre-push hook.
    --no-neutrality    Do not install the optional provider-neutrality guard.
    --adapter NAME     Install a bundled provider adapter (repeatable). Its
                       destination comes from that adapter's own `adapter.json`
                       manifest — never from its name. See `tools/adapters.py`.
    --dry-run          Print the plan; write nothing.

Safety: an existing file is never overwritten. A file is reported as already
current only when its bytes and any required executable mode already make it
usable; anything else gets the framework version alongside it as
`<name>.framework` and is reported as a collision to merge by hand. Re-running
is therefore safe and idempotent.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import adapters as adapter_manifests  # noqa: E402
import line_endings  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FRAMEWORK = ROOT / "framework"
TEMPLATES = ROOT / "templates"
ADAPTERS = ROOT / "adapters"


def framework_version() -> str:
    """This framework's own release, read from its `VERSION` file.

    Never typed by whoever runs adoption: an adopting project must be able to
    tell which release it is on without asking anyone, and a hand-typed
    value can be wrong or stale the moment it is written. `VERSION` is this
    repository's own record of what it currently is.
    """
    path = ROOT / "VERSION"
    try:
        text = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise SystemExit(f"adopt: cannot read {path}: {exc}") from exc
    if not text:
        raise SystemExit(f"adopt: {path} is empty")
    return text


def framework_repository() -> str:
    """This framework's own remote repository address, derived from Git.

    Never typed: a hand-typed URL can name the wrong fork or go stale the
    moment the remote changes. Falls back to a plain, honest placeholder
    when this clone has no `origin` remote configured (a local-only copy,
    or one cloned without a name for its remote) rather than inventing one.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(ROOT), "remote", "get-url", "origin"],
            capture_output=True, text=True, check=False,
        )
    except (FileNotFoundError, OSError):
        result = None
    if result is not None and result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return "<no origin remote configured on this framework clone>"

#: Framework documents copied verbatim into the target. Generic by design: a
#: project does not edit them, so they cannot drift from this repository.
#:
#: THEY MUST ALSO MEAN THE SAME THING IN THE COPY. A markdown relative link is a
#: claim that the file it names is in the repository the reader is holding, so a
#: document in this tuple may link only to another document in it. Anything else
#: — this repository's implementation, its tests, its history — is a reference
#: rather than a link: a plain path, in a sentence that says which repository it
#: is in. Enforced by `tests/test_adopted_doc_references.py`, which adopts into a
#: real tree and resolves the links there.
VERBATIM_DOCS = (
    "CONSTITUTION.md",
    "adapters.md",
    "briefs.md",
    "evidence.md",
    "git-and-isolation.md",
    "kickoff.md",
    "lifecycle.md",
    "reports.md",
    "topologies.md",
    "update.md",
    "roles/README.md",
    "roles/brain.md",
    "roles/worker.md",
    "roles/verifier.md",
)

#: Historical to this repository, never copied: they are its evidence, not the
#: adopting project's.
NOT_COPIED = ("failure-catalogue.md", "case-studies.md", "adoption.md", "state.md")

DOCS_DEST = "docs/agents"


@dataclass
class Plan:
    writes: list[tuple[Path, str, bool]] = field(default_factory=list)
    current: list[Path] = field(default_factory=list)
    collisions: list[tuple[Path, Path]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    ensure_worktrees_ignore: bool = False
    target: Path = Path(".")


def _file_matches(path: Path, content: bytes, executable: bool) -> bool:
    """Whether an existing file is complete for the installed framework use.

    A byte-identical executable script with mode 0644 is not current: adoption
    would still need to make it runnable. Read failures deliberately mean
    "collision", never "current" and never an exception that aborts the plan.
    """
    try:
        if not path.is_file() or path.read_bytes() != content:
            return False
        # Windows cannot represent POSIX execute bits. Its existing-file
        # equivalence is therefore byte-based, while newly written executable
        # files still go through apply_plan's explicit postcondition warning.
        return not executable or os.name == "nt" or executable_bit_took(path)
    except (OSError, ValueError):
        return False


def tracked_hook_line_endings(target: Path) -> list[str]:
    """Return unsafe tracked executable text paths in this clone's worktrees.

    The paths are discovered from Git's executable mode and the files'
    shebangs, not from a directory or adapter-name allowlist. ``.githooks``
    remains a fixed Git hook root even when a pre-existing file has not yet
    recorded its executable mode.
    """
    unsafe: list[str] = []
    target = target.resolve()
    worktrees = [target]
    try:
        listed = subprocess.run(
            ["git", "-C", str(target), "worktree", "list", "--porcelain"],
            capture_output=True, text=True, check=False,
        )
    except (FileNotFoundError, OSError):
        listed = None
    if listed is not None and listed.returncode == 0:
        for line in listed.stdout.splitlines():
            if line.startswith("worktree "):
                checkout = Path(line.removeprefix("worktree ")).resolve()
                if checkout not in worktrees:
                    worktrees.append(checkout)

    for checkout in worktrees:
        try:
            paths = line_endings.tracked_unsafe_paths(checkout)
        except (FileNotFoundError, OSError):
            continue
        for path in paths:
            label = path
            if checkout != target:
                label = f"{checkout}: {path}"
            unsafe.append(label)
    return unsafe


def topology_diagram(coordinator: str, workers: list[str], verifier: bool) -> str:
    seats = list(workers) + (["verifier"] if verifier else [])
    lines = ["```", "Owner", f"└── {coordinator.capitalize()}"]
    for i, seat in enumerate(seats):
        connector = "└──" if i == len(seats) - 1 else "├──"
        lines.append(f"    {connector} {seat.capitalize()}")
    lines.append("```")
    return "\n".join(lines)


def role_table(coordinator: str, workers: list[str], verifier: bool) -> str:
    rows = [
        "| Role | Holds | Scope |",
        "|---|---|---|",
        "| **Owner** | Direction, priorities, scope. Veto and reversal. | — |",
        f"| **{coordinator.capitalize()}** | Project context, sequencing, briefs, "
        f"adjudication, and the routine merge. "
        f"([contract](docs/agents/roles/brain.md)) | <!-- what it owns --> |",
    ]
    for w in workers:
        rows.append(
            f"| **{w.capitalize()}** | One bounded brief at a time. Never "
            f"self-accepts, never merges. "
            f"([contract](docs/agents/roles/worker.md)) | <!-- disjoint scope --> |"
        )
    if verifier:
        rows.append(
            "| **Verifier** | Independent review of an exact SHA. Writes "
            "findings, never merges. "
            "([contract](docs/agents/roles/verifier.md)) | Read-only. |"
        )
    if len(workers) > 1:
        rows.append("")
        rows.append(
            "Executor scopes must not overlap. Each concurrently-active role "
            "gets its own checkout."
        )
    return "\n".join(rows)


def render(text: str, values: dict[str, str]) -> str:
    for key, val in values.items():
        text = text.replace("{{" + key + "}}", val)
    return text


def adapter_notes(
    adapter, *, workers: list[str], verifier: bool
) -> list[str]:
    """State what this adapter actually installed, and what it did not.

    Derived from the files on disk, not from a claim in a document. An adapter
    ships one seat per *role contract*; a project-declared specialist executor
    is the Worker contract plus a scope statement, so it gets no seat of its
    own. Saying so here stops the adopted layout being read as offering a file
    per declared role that it does not contain.
    """
    seats = adapter.seat_roles()
    notes = [
        f"adapter '{adapter.name}' ({adapter.tool}) installs at "
        f"{adapter.install_root}/"
        + (f", seats: {', '.join(seats)}." if seats else ".")
    ]
    declared = list(workers) + (["verifier"] if verifier else [])
    unseated = [r for r in declared if r not in seats]
    if unseated and "worker" in seats:
        notes.append(
            f"no seat file is generated for {', '.join(unseated)}: each is the "
            f"executor contract plus a scope statement, so they share the "
            f"'worker' seat. The specialism is the scope in AGENTS.md."
        )
    elif unseated:
        notes.append(
            f"this adapter ships no seat for {', '.join(unseated)}; launch "
            f"those with the universal procedure in docs/agents/adapters.md."
        )
    return notes


def build_plan(
    target: Path,
    *,
    project: str,
    coordinator: str,
    workers: list[str],
    verifier: bool,
    hooks: bool,
    adapters: list[str],
    neutrality: bool = True,
) -> Plan:
    plan = Plan(target=target)

    def add(rel: str, content: str, executable: bool = False) -> None:
        dst = target / rel
        installed = content.replace("\r\n", "\n").replace("\r", "\n")
        installed_bytes = installed.encode("utf-8")
        if dst.exists():
            if _file_matches(dst, installed_bytes, executable):
                plan.current.append(dst)
                return
            sibling = dst.with_name(dst.name + ".framework")
            while sibling.exists():
                if _file_matches(sibling, installed_bytes, executable):
                    plan.collisions.append((dst, sibling))
                    plan.current.append(sibling)
                    return
                sibling = sibling.with_name(sibling.name + ".framework")
            plan.collisions.append((dst, sibling))
            plan.writes.append((sibling, content, executable))
        else:
            plan.writes.append((dst, content, executable))

    for rel in VERBATIM_DOCS:
        src = FRAMEWORK / rel
        if not src.is_file():
            raise SystemExit(f"framework file missing: {src}")
        add(f"{DOCS_DEST}/{rel}", src.read_text(encoding="utf-8"))

    values = {
        "PROJECT": project,
        "TOPOLOGY_DIAGRAM": topology_diagram(coordinator, workers, verifier),
        "ROLE_TABLE": role_table(coordinator, workers, verifier),
        "ROLES": repr(tuple(workers + (["verifier"] if verifier else []))),
        "COORDINATOR": coordinator,
        "FRAMEWORK_VERSION": framework_version(),
        "FRAMEWORK_REPO": framework_repository(),
    }

    add("AGENTS.md", render((TEMPLATES / "AGENTS.md").read_text(encoding="utf-8"), values))
    add("docs/state.md", (TEMPLATES / "docs/state.md").read_text(encoding="utf-8"))
    add("docs/briefs/README.md",
        (TEMPLATES / "docs/briefs/README.md").read_text(encoding="utf-8"))
    add("docs/briefs/active.md",
        (TEMPLATES / "docs/briefs/active.md").read_text(encoding="utf-8"))
    for sub in ("delivered", "archive"):
        add(f"docs/briefs/{sub}/.gitkeep",
            (TEMPLATES / f"docs/briefs/{sub}/.gitkeep").read_text(encoding="utf-8"))

    if neutrality:
        # Every module the installed test imports, or it fails on import in the
        # target rather than guarding anything there. These are executable
        # tools: the shebang is a promise that an adopting project can run them
        # directly, just like the adapter hooks below.
        for module in ("neutrality.py", "authority.py", "textblocks.py"):
            src = ROOT / "tools" / module
            with src.open("rb") as stream:
                executable = stream.readline().startswith(b"#!")
            add(
                f"tools/{module}", src.read_text(encoding="utf-8"),
                executable=executable,
            )
    # Without this, `unittest discover -s tests` refuses the directory and the
    # installed guard never runs at all. Caught by tests/test_adopt.py, which
    # runs the guard in the adopted tree rather than checking it exists.
    add("tests/__init__.py", "")
    if neutrality:
        add("tests/test_role_neutrality.py",
            render((TEMPLATES / "tests/test_role_neutrality.py").read_text(encoding="utf-8"),
                   values))
    add("tests/test_checkout.py",
        (TEMPLATES / "tests/test_checkout.py").read_text(encoding="utf-8"))
    add("tests/test_report.py",
        (ROOT / "tests" / "test_report.py").read_text(encoding="utf-8"))

    checkout_src = ROOT / "tools" / "checkout.py"
    with checkout_src.open("rb") as stream:
        checkout_executable = stream.readline().startswith(b"#!")
    add(
        "tools/checkout.py", checkout_src.read_text(encoding="utf-8"),
        executable=checkout_executable,
    )

    # Preserve every existing project rule and append the required isolation
    # entry only when neither common spelling is already present.
    ignore = target / ".gitignore"
    existing_ignore = ignore.read_text(encoding="utf-8") if ignore.is_file() else ""
    ignored_lines = {line.strip() for line in existing_ignore.splitlines()}
    if ".worktrees/" not in ignored_lines and "/.worktrees/" not in ignored_lines:
        plan.ensure_worktrees_ignore = True

    # The cross-provider completion-report writer -- see framework/reports.md.
    # Installed unconditionally, with no `--adapter` required: it is the
    # baseline every filesystem-capable role uses regardless of which tool runs
    # it, and it must exist even when no adapter is installed at all, since
    # that is the case for a provider this project has never seen.
    report_src = ROOT / "tools" / "report.py"
    with report_src.open("rb") as stream:
        report_executable = stream.readline().startswith(b"#!")
    add(
        "tools/report.py", report_src.read_text(encoding="utf-8"),
        executable=report_executable,
    )

    plan.notes.append(
        "Neutrality guard installed (tools/neutrality.py, tools/textblocks.py, "
        "tools/authority.py and tests/test_role_neutrality.py). Update these "
        "together with every docs/agents document copied from VERBATIM_DOCS."
        if neutrality else
        "Neutrality guard deferred by --no-neutrality; no neutrality scanner, "
        "shared parser, authority scanner or installed neutrality test was "
        "written."
    )

    # Installed unconditionally: a project receives executable framework text
    # content from this framework whenever it takes the hooks or an adapter,
    # and a CRLF checkout makes those inert. Cheap, and wrong to make
    # conditional on remembering a flag.
    line_endings_src = ROOT / "tools" / "line_endings.py"
    with line_endings_src.open("rb") as stream:
        line_endings_executable = stream.readline().startswith(b"#!")
    add(
        "tools/line_endings.py", line_endings_src.read_text(encoding="utf-8"),
        executable=line_endings_executable,
    )

    # Installed unconditionally: a project receives `#!/bin/sh` content from
    # this framework whenever it takes the hooks or an adapter, and a CRLF
    # checkout makes those inert. Cheap, and wrong to make conditional on
    # remembering a flag.
    add(".gitattributes", (TEMPLATES / "gitattributes").read_text(encoding="utf-8"))

    stale_hooks = tracked_hook_line_endings(target)
    if stale_hooks:
        plan.notes.append(
            "WARNING: tracked executable framework text file(s) still have "
            "CRLF or mixed working-tree line endings: " + ", ".join(stale_hooks)
            + ". Run `python3 tools/line_endings.py check`, then follow "
            "docs/agents/git-and-isolation.md's stash-free refresh steps before "
            "relying on the script. The effect depends on the platform and shell."
        )

    if hooks:
        add(".githooks/pre-push",
            (TEMPLATES / "githooks/pre-push").read_text(encoding="utf-8"),
            executable=True)
        plan.notes.append(
            "The pre-push hook is opt-in per clone and fails silently until "
            "`git config core.hooksPath .githooks` is run. It is early "
            "feedback, never a control."
        )

    for name in adapters:
        src_dir = ADAPTERS / name
        if not src_dir.is_dir():
            raise SystemExit(
                f"unknown adapter '{name}'; available: "
                f"{', '.join(adapter_manifests.available(ADAPTERS))}"
            )
        # The destination comes from the adapter's own manifest, never from its
        # name. See tools/adapters.py for why that distinction is load-bearing.
        try:
            adapter = adapter_manifests.load(src_dir)
        except adapter_manifests.AdapterError as exc:
            raise SystemExit(f"adopt: {exc}") from exc
        for src in adapter.source_files():
            rel = src.relative_to(src_dir).as_posix()
            with src.open("rb") as stream:
                executable = stream.readline().startswith(b"#!")
            add(
                adapter.destination(rel),
                src.read_text(encoding="utf-8"),
                executable=executable,
            )
        plan.notes += adapter_notes(adapter, workers=workers, verifier=verifier)

    plan.notes.append(
        "Now do the judgement half: write AGENTS.md's invariants, evidence "
        "table and enforcement section. See framework/adoption.md."
    )
    return plan


def render_plan(plan: Plan, target: Path) -> str:
    out = []
    for dst, _, executable in plan.writes:
        rel = dst.relative_to(target)
        out.append(f"  write  {rel}{' (exec)' if executable else ''}")
    for dst in plan.current:
        out.append(f"  current {dst.relative_to(target)} (already current)")
    for existing, sibling in plan.collisions:
        out.append(
            f"  KEEP   {existing.relative_to(target)} (exists) — framework "
            f"version written to {sibling.name}, merge by hand"
        )
    for note in plan.notes:
        out.append(f"  note   {note}")
    if plan.ensure_worktrees_ignore:
        out.append("  append .gitignore (ignore .worktrees/; existing content stays in order)")
    return "\n".join(out) or "  (nothing to do)"


def executable_bit_took(path: Path) -> bool:
    """Return whether this platform can represent an executable file mode.

    Windows Python deliberately ignores ``X_OK`` and Windows ``chmod`` cannot
    preserve POSIX execute bits. Treat that capability as absent explicitly;
    otherwise a successful-looking adoption leaves a hook that Git will skip
    after a later POSIX clone.
    """
    if os.name == "nt":
        return False
    try:
        return bool(path.stat().st_mode & 0o111)
    except OSError:
        return False


def apply_plan(plan: Plan) -> list[Path]:
    """Write the plan. Returns the files whose executable bit did not take.

    `chmod` is asked for, never assumed. On Windows it honours only the
    read-only flag and silently discards execute bits, so the platform is
    reported as unable to complete adoption instead of claiming success.
    """
    unset: list[Path] = []
    for dst, content, executable in plan.writes:
        dst.parent.mkdir(parents=True, exist_ok=True)
        # Disable platform newline translation explicitly. `Path.write_text`
        # does not provide that guarantee on Python versions still supported by
        # adopting projects, so normalize the source and write LF bytes here.
        with dst.open("w", encoding="utf-8", newline="") as stream:
            stream.write(content.replace("\r\n", "\n").replace("\r", "\n"))
        if executable:
            try:
                dst.chmod(dst.stat().st_mode | 0o111)
            except OSError:
                pass
            if not executable_bit_took(dst):
                unset.append(dst)
    if plan.ensure_worktrees_ignore:
        ignore = plan.target / ".gitignore"
        prior = ignore.read_text(encoding="utf-8") if ignore.is_file() else ""
        lines = {line.strip() for line in prior.splitlines()}
        if ".worktrees/" not in lines and "/.worktrees/" not in lines:
            separator = "" if not prior or prior.endswith(("\n", "\r")) else "\n"
            with ignore.open("a", encoding="utf-8", newline="") as stream:
                stream.write(separator + ".worktrees/\n")
    return unset


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("target")
    ap.add_argument("--project", required=True)
    ap.add_argument("--workers", default="worker")
    ap.add_argument("--verifier", action="store_true")
    ap.add_argument("--coordinator", default="brain")
    ap.add_argument("--hooks", action="store_true")
    ap.add_argument(
        "--no-neutrality", action="store_false", dest="neutrality",
        help="defer installation of the optional provider-neutrality guard",
    )
    ap.add_argument("--adapter", action="append", default=[])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    target = Path(args.target).expanduser().resolve()
    if not target.is_dir():
        print(f"adopt: target is not a directory: {target}", file=sys.stderr)
        return 2

    workers = [w.strip() for w in args.workers.split(",") if w.strip()]
    if not workers:
        print("adopt: --workers needs at least one role", file=sys.stderr)
        return 2
    reserved = {args.coordinator, "verifier", "owner"}
    clash = sorted(set(workers) & reserved)
    if clash:
        print(f"adopt: executor role name(s) clash with a reserved role: {clash}",
              file=sys.stderr)
        return 2

    plan = build_plan(
        target,
        project=args.project,
        coordinator=args.coordinator,
        workers=workers,
        verifier=args.verifier,
        hooks=args.hooks,
        neutrality=args.neutrality,
        adapters=args.adapter,
    )

    print(f"adopt: plan for {target}")
    print(render_plan(plan, target))
    if args.dry_run:
        print("\nadopt: --dry-run; nothing written.")
        return 0
    unset = apply_plan(plan)
    if unset:
        print(
            "\nadopt: WARNING -- the executable bit did not take on these "
            "files. This host cannot set it (Windows discards it silently). "
            "Windows can use the installed files, but a POSIX clone would "
            "receive them inert. Fix before committing:",
            file=sys.stderr,
        )
        for dst in unset:
            print(f"  git update-index --chmod=+x {dst.relative_to(target)}",
                  file=sys.stderr)
        if os.name == "nt":
            print(
                "adopt: Windows completed the local copy with this warning; "
                "set the Git executable mode before a POSIX clone consumes it.",
                file=sys.stderr,
            )
            print("\nadopt: done.")
            return 0
        return 1
    print("\nadopt: done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
