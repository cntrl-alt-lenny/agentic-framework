#!/usr/bin/env python3
"""Which documents in this repository are normative, and which record history.

The split matters: normative documents define policy and must be
provider-neutral and free of stale authority language. Historical documents —
the failure catalogue and the case studies — deliberately quote broken forms and
name the tools that actually ran, because that is the evidence.

**The normative set is derived from the tree, never enumerated.** A new document
under `framework/` is therefore scanned by default. Escaping the scan requires
adding the file to `HISTORICAL` *and* writing "historical document" inside it —
a visible act, not an omission.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: This repository's own role vocabulary, declared once. Its normative documents
#: use Brain plus these executor names -- including the specialist names that
#: appear as topology examples, so those examples are held to the same rules as
#: everything else.
ROLES: tuple[str, ...] = (
    "worker", "builder", "verifier", "decomper", "scaffolder", "researcher",
)
COORDINATOR = "brain"

#: Documents that record what happened rather than defining policy. Each must
#: declare itself as such in its own text; `tests/test_provider_neutrality.py`
#: enforces that, so this list cannot be used to quietly exempt a policy file.
HISTORICAL: tuple[str, ...] = (
    "framework/failure-catalogue.md",
    "framework/case-studies.md",
    "CHANGELOG.md",
)

#: Not policy and not history: a test fixture preserving known-bad text on
#: purpose. Named explicitly so it cannot become an unnoticed third category.
FIXTURES: tuple[str, ...] = (
    "tests/fixtures/v1_stale_authority.md",
)

# Reference material belongs in the repository for authors to read, but is not
# normative policy or historical evidence. It is classified explicitly so an
# untracked or ignored copy cannot change the guard's surface.
REFERENCES: tuple[str, ...] = (
    "standards/readme.md",
)

HISTORICAL_MARKER = "historical document"


def tracked_paths() -> set[Path]:
    """Return paths Git tracks, never whatever happens to be on disk."""
    try:
        output = subprocess.check_output(
            ["git", "ls-files", "-z"], cwd=ROOT,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        # Mutation tests copy the repository without its .git directory. Keep
        # those isolated checks usable, while still excluding the exact class
        # of untracked role checkout that the Git-backed path rejects.
        return {
            path.resolve() for path in ROOT.rglob("*")
            if path.is_file() and ".worktrees" not in path.parts
        }
    return {
        (ROOT / raw).resolve()
        for raw in output.decode().split("\0")
        if raw
    }


def tracked_markdown_files() -> list[Path]:
    """Every tracked Markdown file, including historical and reference text."""
    return sorted(
        path for path in tracked_paths()
        if path.suffix.lower() == ".md"
    )


def tracked_directories(paths: set[Path] | None = None) -> set[Path]:
    """Directories that contain tracked content at any depth."""
    paths = tracked_paths() if paths is None else {
        path.resolve() for path in paths
    }
    directories: set[Path] = set()
    for path in paths:
        current = path.parent
        while current == ROOT or ROOT in current.parents:
            directories.add(current)
            if current == ROOT:
                break
            current = current.parent
    return directories


def historical_files() -> list[Path]:
    tracked = tracked_paths()
    return [ROOT / rel for rel in HISTORICAL if (ROOT / rel).resolve() in tracked]


def reference_files() -> list[Path]:
    tracked = tracked_paths()
    return [ROOT / rel for rel in REFERENCES if (ROOT / rel).resolve() in tracked]


def normative_files() -> list[Path]:
    """Every policy-defining document, derived from the tree."""
    tracked = tracked_paths()
    excluded = {
        (ROOT / rel).resolve()
        for rel in HISTORICAL + REFERENCES
    }
    roots = (
        ROOT / "framework",
        ROOT / "templates",
        ROOT / "adapters",
    )
    paths = sorted(
        path for path in tracked
        if path.suffix.lower() == ".md"
        and any(path.is_relative_to(root.resolve()) for root in roots)
    )
    readme = (ROOT / "README.md").resolve()
    if readme in tracked:
        paths.append(readme)
    return [
        p for p in paths if p.resolve() not in excluded
    ]


def all_documents() -> list[Path]:
    return normative_files() + historical_files() + reference_files()


def classified() -> set[Path]:
    """Every document this repository has made a deliberate decision about."""
    return (
        {p.resolve() for p in normative_files()}
        | {p.resolve() for p in historical_files()}
        | {p.resolve() for p in reference_files()}
        | {(ROOT / rel).resolve() for rel in FIXTURES}
    )


def unclassified() -> list[Path]:
    """Markdown that is neither normative, historical, nor a declared fixture.

    Fails closed: a new document is normative by default, so this should only
    ever be non-empty when one lands outside every scanned directory.
    """
    known = classified()
    out = []
    for path in tracked_markdown_files():
        if ".git" in path.parts or path.name.startswith("."):
            continue
        if path.resolve() not in known:
            out.append(path)
    return out
