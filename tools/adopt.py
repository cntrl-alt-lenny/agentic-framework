#!/usr/bin/env python3
"""Install this framework into a project, or update a project to this release.

    python3 tools/adopt.py <project> --project "Name" [--workers worker]
                           [--verifier] [--adapter NAME]... [--hooks] [--dry-run]
    python3 tools/adopt.py <project> --update [--adapter NAME]... [--dry-run]

Run it from a clone of the framework checked out at the release you want.

What it installs is recorded in the project's docs/agents/framework.json: the
release, the repository, the options chosen, and a SHA-256 fingerprint of every
framework file. That record is what makes an update safe:

- a framework file whose fingerprint still matches is replaced by the new one;
- a framework file someone edited is left alone, and the new version is written
  beside it as `<name>.framework` for review;
- a file the new release no longer ships is removed only when it provably was
  never edited, and never while another kept file still refers to it;
- project-owned files (AGENTS.md, docs/state.md, rounds, CLAUDE.md, ...) are
  created when missing and otherwise never touched.

A project adopted before release 3.0.0 has no record; for it, the fingerprints
of every file a 2.x release ever installed (tools/legacy_installs.json) prove
which files are unedited copies.

It then prints every release's "what an adopter must do" steps between the old
and new release, and the project checks that still fail. Nothing is committed:
the result is reviewed and merged like any other round.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRAMEWORK = ROOT / "framework"
TEMPLATES = ROOT / "templates"
ADAPTERS = ROOT / "adapters"
MANIFEST = "docs/agents/framework.json"
CANONICAL_REPOSITORY = "https://github.com/cntrl-alt-lenny/agentic-framework"

#: Legacy (2.x) files this release no longer ships. Removed when unedited.
RETIRED_PREFIXES = ("docs/agents/", ".claude/")
RETIRED_EXACT = {
    "tools/checkout.py", "tools/report.py", "tools/line_endings.py",
    "tools/neutrality.py", "tools/authority.py", "tools/textblocks.py",
    "tests/test_checkout.py", "tests/test_report.py", "tests/test_role_neutrality.py",
}
#: Where the updater looks for files that still use a retired file. Documents
#: are not holders: a document mentioning a file does not break without it.
HOLDER_SUFFIXES = {".py", ".sh", ".json", ".toml", ".yml", ".yaml", ".cfg", ".ini", ".ps1", ".bat", ".cmd"}
HOLDER_NAMES = {"Makefile", "justfile"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".tox", ".wine-lane", ".worktrees"}
MAX_HOLDER_BYTES = 2_000_000


def _load_fw():
    spec = importlib.util.spec_from_file_location("fw", ROOT / "tools" / "fw.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fw = _load_fw()


def digest(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def framework_version() -> str:
    text = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not fw.version_tuple(text):
        raise SystemExit(f"adopt: VERSION {text!r} is not X.Y.Z")
    return text


def framework_repository() -> str:
    """The framework's public address. A clone's origin is used only when it is
    a plain GitHub URL, so a proxy or local path never ends up in a project."""
    result = subprocess.run(
        ["git", "-C", str(ROOT), "remote", "get-url", "origin"],
        capture_output=True, text=True, check=False,
    )
    url = result.stdout.strip()
    if result.returncode == 0 and re.match(r"^(https://github\.com/|git@github\.com:)", url):
        return url[:-4] if url.endswith(".git") else url
    return CANONICAL_REPOSITORY


def legacy_fingerprints() -> tuple[dict[str, list[str]], dict[str, dict]]:
    data = json.loads((ROOT / "tools" / "legacy_installs.json").read_text(encoding="utf-8"))
    return data["files"], data.get("rendered", {})


def masked_digest(data: bytes, mask: str) -> str:
    text = data.replace(b"\r\n", b"\n").decode("utf-8", errors="replace")
    return hashlib.sha256(re.sub(mask, r"\1", text, flags=re.M).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------
# what this release ships


@dataclass
class Item:
    rel: str
    content: str
    kind: str  # "copy" (framework-owned) or "seed" (project-owned once created)
    executable: bool = False

    @property
    def data(self) -> bytes:
        return self.content.replace("\r\n", "\n").encode("utf-8")


def role_table(workers: list[str], verifier: bool) -> str:
    rows = ["| Seat | Card | Scope |", "|---|---|---|",
            "| Brain | `docs/agents/roles/brain.md` | Plans, briefs, judges, merges under the merge rule. |"]
    for name in workers:
        rows.append(
            f"| {name.capitalize()} | `docs/agents/roles/worker.md` | "
            "<!-- what this executor may change --> |"
        )
    if verifier:
        rows.append("| Verifier | `docs/agents/roles/verifier.md` | Reviews Tier 2 rounds at one exact commit. |")
    return "\n".join(rows)


def adapter_dirs() -> list[str]:
    return sorted(p.name for p in ADAPTERS.iterdir() if (p / "adapter.json").is_file())


def release_items(*, project: str, workers: list[str], verifier: bool,
                  adapters: list[str], hooks: bool, tests_dir_exists: bool) -> list[Item]:
    items = [Item("docs/agents/FRAMEWORK.md", (FRAMEWORK / "FRAMEWORK.md").read_text(encoding="utf-8"), "copy")]
    for role in ("brain", "worker", "verifier"):
        items.append(Item(f"docs/agents/roles/{role}.md",
                          (FRAMEWORK / "roles" / f"{role}.md").read_text(encoding="utf-8"), "copy"))
    items.append(Item("tools/fw.py", (ROOT / "tools" / "fw.py").read_text(encoding="utf-8"), "copy", True))
    items.append(Item("tests/test_framework.py",
                      (TEMPLATES / "tests" / "test_framework.py").read_text(encoding="utf-8"), "copy"))
    agents = (TEMPLATES / "AGENTS.md").read_text(encoding="utf-8")
    agents = agents.replace("{{PROJECT}}", project).replace("{{ROLE_TABLE}}", role_table(workers, verifier))
    items.append(Item("AGENTS.md", agents, "seed"))
    items.append(Item("docs/state.md", (TEMPLATES / "docs" / "state.md").read_text(encoding="utf-8"), "seed"))
    items.append(Item("docs/rounds/README.md",
                      (TEMPLATES / "docs" / "rounds" / "README.md").read_text(encoding="utf-8"), "seed"))
    items.append(Item(".gitattributes", (TEMPLATES / "gitattributes").read_text(encoding="utf-8"), "seed"))
    if not tests_dir_exists:
        items.append(Item("tests/__init__.py", "", "seed"))
    if hooks:
        items.append(Item(".githooks/pre-push", (TEMPLATES / "githooks" / "pre-push").read_text(encoding="utf-8"), "seed", True))
    for name in adapters:
        src = ADAPTERS / name
        if not (src / "adapter.json").is_file():
            raise SystemExit(f"adopt: unknown adapter {name!r}; available: {', '.join(adapter_dirs())}")
        meta = json.loads((src / "adapter.json").read_text(encoding="utf-8"))
        seeds = set(meta.get("seeds", []))
        for path in sorted((src / "files").rglob("*")):
            if path.is_file():
                rel = path.relative_to(src / "files").as_posix()
                items.append(Item(rel, path.read_text(encoding="utf-8"), "seed" if rel in seeds else "copy"))
    return items


# --------------------------------------------------------------------------
# planning


@dataclass
class Plan:
    target: Path
    writes: list[tuple[Item, Path, str]] = field(default_factory=list)  # item, path, reason
    current: list[str] = field(default_factory=list)
    kept: list[str] = field(default_factory=list)
    sidecars: list[tuple[str, str]] = field(default_factory=list)
    removals: list[str] = field(default_factory=list)
    retained: list[tuple[str, str]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    manifest: dict = field(default_factory=dict)


def load_manifest(target: Path) -> dict | None:
    path = target / MANIFEST
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def is_legacy(target: Path) -> bool:
    return (target / "docs/agents/CONSTITUTION.md").is_file() or (target / "tools/checkout.py").is_file()


def sidecar_path(path: Path, data: bytes) -> Path:
    candidate = path.with_name(path.name + ".framework")
    while candidate.exists() and candidate.read_bytes().replace(b"\r\n", b"\n") != data:
        candidate = candidate.with_name(candidate.name + ".framework")
    return candidate


class Holders:
    """The project's code and configuration files, read once, for finding
    files that still use something the update would remove. It reads the
    working tree directly, so untracked files count and git is not needed.
    If the tree cannot be read, every removal is refused."""

    def __init__(self, target: Path, planned: dict[str, str], framework_files: set[str]):
        self.target = target
        self.files: dict[str, str] = {}
        self.error: str | None = None
        try:
            for folder, dirs, names in os.walk(target, onerror=self._fail):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".venv")]
                rel_dir = Path(folder).relative_to(target).as_posix()
                for name in names:
                    path = Path(folder) / name
                    in_hooks = rel_dir.split("/")[0] == ".githooks"
                    if path.suffix not in HOLDER_SUFFIXES and name not in HOLDER_NAMES and not in_hooks:
                        continue
                    if path.stat().st_size > MAX_HOLDER_BYTES:
                        continue
                    rel = path.relative_to(target).as_posix()
                    self.files[rel] = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            self._fail(exc)
        # Files this update writes are judged by what they will contain, and the
        # framework's own files never depend on the files it retires.
        for rel, text in planned.items():
            if Path(rel).suffix in HOLDER_SUFFIXES or Path(rel).name in HOLDER_NAMES:
                self.files[rel] = text
        for rel in framework_files:
            self.files.pop(rel, None)

    def _fail(self, exc: OSError) -> None:
        self.error = f"could not read the project to check what uses it ({exc})"

    def user_of(self, rel: str, removing: set[str]) -> str | None:
        if self.error:
            return self.error
        name = Path(rel).name
        patterns = [re.escape(rel), re.escape(rel.replace("/", "\\")), rf"[\"']{re.escape(name)}[\"']"]
        if rel.startswith("tools/") and rel.endswith(".py"):
            module = re.escape(Path(rel).stem)
            patterns += [
                rf"^\s*import\s+(tools\.)?{module}\b",
                rf"^\s*from\s+(tools\.)?{module}\s+import\b",
                rf"^\s*from\s+tools\s+import\s+[^\n]*\b{module}\b",
            ]
        found = re.compile("|".join(f"(?:{p})" for p in patterns), re.M)
        for holder, text in sorted(self.files.items()):
            if holder in (rel, MANIFEST) or holder in removing or holder.endswith(".framework"):
                continue
            if found.search(text):
                return f"{holder} still refers to it"
        return None


def broken_links(target: Path, removed: set[str], planned: dict[str, str]) -> list[str]:
    """Documents that would be left linking to a removed file, judged by the
    content they will have after the update."""
    hits = []
    for folder, dirs, names in os.walk(target):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in names:
            if not name.endswith(".md"):
                continue
            path = Path(folder) / name
            rel = path.relative_to(target).as_posix()
            if rel in removed:
                continue
            text = planned.get(rel) or path.read_text(encoding="utf-8", errors="replace")
            for link in re.findall(r"\]\(([^)#\s]+)", text):
                linked = os.path.normpath((Path(rel).parent / link).as_posix()).replace("\\", "/")
                if linked in removed:
                    hits.append(f"{rel} links to {linked}")
    return hits


def build_plan(target: Path, *, update: bool, project: str | None, workers: list[str],
               verifier: bool, adapters: list[str] | None, hooks: bool) -> Plan:
    plan = Plan(target=target)
    old = load_manifest(target)
    legacy = old is None and is_legacy(target)
    if update and old is None and not legacy:
        raise SystemExit("adopt: this project has no framework record to update; adopt it first (without --update)")
    if not update and old is not None:
        raise SystemExit(f"adopt: {MANIFEST} exists; use --update")

    options = (old or {}).get("options", {})
    # On update, --adapter adds to the recorded set; it never drops one.
    adapters = list(options.get("adapters", [])) + list(adapters or [])
    if update:
        if legacy:
            if (target / ".claude").is_dir():
                adapters.append("claude-code")
            if (target / "GEMINI.md").is_file():
                adapters.append("gemini")
    hooks = hooks or bool(options.get("hooks")) or (legacy and (target / ".githooks/pre-push").is_file())
    items = release_items(
        project=project or target.name, workers=workers, verifier=verifier,
        adapters=sorted(set(adapters)), hooks=hooks,
        tests_dir_exists=(target / "tests").is_dir(),
    )
    old_files = (old or {}).get("files", {})
    known, rendered = legacy_fingerprints()

    def unedited(rel: str, data: bytes) -> bool:
        h = digest(data)
        entry = old_files.get(rel)
        if entry and entry.get("kind") == "copy":
            return entry.get("sha256") == h
        if rel in rendered:
            return masked_digest(data, rendered[rel]["mask"]) in rendered[rel]["sha256"]
        return h in known.get(rel, ())

    files_record = {}
    for item in items:
        path = target / item.rel
        new = item.data
        if item.kind == "copy":
            files_record[item.rel] = {"kind": "copy", "sha256": digest(new)}
        else:
            files_record[item.rel] = {"kind": "seed"}
        if not path.exists():
            plan.writes.append((item, path, "new"))
            continue
        existing = path.read_bytes()
        if existing.replace(b"\r\n", b"\n") == new:
            plan.current.append(item.rel)
            continue
        if item.kind == "seed":
            if update:
                plan.kept.append(item.rel)
            else:
                side = sidecar_path(path, new)
                plan.writes.append((item, side, "sidecar"))
                plan.sidecars.append((item.rel, side.relative_to(target).as_posix()))
            continue
        if update and unedited(item.rel, existing):
            plan.writes.append((item, path, "replace"))
        else:
            side = sidecar_path(path, new)
            plan.writes.append((item, side, "sidecar"))
            plan.sidecars.append((item.rel, side.relative_to(target).as_posix()))

    # Project-owned files installed by an earlier run stay recorded as such.
    for rel, entry in old_files.items():
        if entry.get("kind") == "seed" and rel not in files_record:
            files_record[rel] = {"kind": "seed"}

    if update:
        shipped = {item.rel for item in items}
        candidates = set()
        for rel, entry in old_files.items():
            if rel not in shipped and entry.get("kind") == "copy":
                candidates.add(rel)
        if legacy:
            for rel in [*known, *rendered]:
                if rel not in shipped and (rel in RETIRED_EXACT or rel.startswith(RETIRED_PREFIXES)):
                    candidates.add(rel)
        removing = set()
        for rel in sorted(candidates):
            path = target / rel
            if not path.is_file():
                continue
            if unedited(rel, path.read_bytes()):
                removing.add(rel)
            else:
                plan.retained.append((rel, "edited in this project, so kept; delete it once nothing needs it"))
        planned = {
            item.rel: item.content for item, path, reason in plan.writes if reason in ("new", "replace")
        }
        holders = Holders(target, planned, {item.rel for item in items if item.kind == "copy"})
        changed = True
        while changed:
            changed = False
            for rel in sorted(removing):
                user = holders.user_of(rel, removing)
                if user:
                    removing.discard(rel)
                    plan.retained.append((rel, f"unedited, but {user}; remove that use, then delete it"))
                    changed = True
        # A kept framework document must not be left linking to a removed one.
        changed = True
        while changed:
            changed = False
            kept_docs = [r for r, _why in plan.retained if r.endswith(".md")]
            for holder in kept_docs:
                text = (target / holder).read_text(encoding="utf-8", errors="replace")
                for link in re.findall(r"\]\(([^)#\s]+)", text):
                    linked = (Path(holder).parent / link).as_posix()
                    linked = os.path.normpath(linked).replace("\\", "/")
                    if linked in removing:
                        removing.discard(linked)
                        plan.retained.append((linked, f"{holder}, which is kept, links to it; delete both together"))
                        changed = True
        plan.removals = sorted(removing)
        for hit in sorted(set(broken_links(target, removing, planned)))[:20]:
            plan.notes.append(f"fix this link after the update: {hit}")

    plan.manifest = {
        "about": "Written by the agentic framework's tools/adopt.py. Do not edit by hand, except 'settings'.",
        "framework": {"repository": framework_repository(), "release": framework_version()},
        "options": {"adapters": sorted(set(adapters)), "hooks": hooks},
        "settings": (old or {}).get("settings", {}),
        "files": files_record,
    }
    if not plan.manifest["settings"]:
        plan.manifest["settings"] = {"state_words": fw.DEFAULT_STATE_WORDS}
    return plan


# --------------------------------------------------------------------------
# changelog


def changelog_steps(since: str | None) -> list[tuple[str, str]]:
    """(version, steps) for every release newer than ``since``, oldest first."""
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    current = fw.version_tuple(framework_version())
    low = fw.version_tuple(since) if since else None
    entries = []
    for block in re.split(r"^## ", text, flags=re.M)[1:]:
        version = block.split()[0]
        parsed = fw.version_tuple(version)
        if not parsed or parsed > current:
            continue
        if (low is not None and parsed <= low) or (low is None and parsed < (3, 0, 0)):
            continue
        match = re.search(r"^### What an adopter must do\s*\n(.*?)(?=^##|\Z)", block, flags=re.M | re.S)
        entries.append((parsed, version, match.group(1).strip() if match else "Nothing beyond the update itself."))
    return [(v, s) for _, v, s in sorted(entries)]


# --------------------------------------------------------------------------
# output and apply


def describe(plan: Plan, *, update: bool, old_release: str | None) -> str:
    lines = []
    verb = "update" if update else "adopt"
    lines.append(f"{verb}: {plan.target} -> agentic-framework {plan.manifest['framework']['release']}"
                 + (f" (from {old_release})" if update else ""))
    for _item, path, reason in plan.writes:
        rel = path.relative_to(plan.target).as_posix()
        label = {"new": "create ", "replace": "replace", "sidecar": "beside "}[reason]
        lines.append(f"  {label} {rel}")
    for rel in plan.removals:
        lines.append(f"  remove  {rel}  (unedited copy from an earlier release)")
    for rel in plan.current:
        lines.append(f"  same    {rel}")
    for rel in plan.kept:
        lines.append(f"  keep    {rel}  (project-owned)")
    for rel, why in plan.retained:
        lines.append(f"  keep    {rel}  ({why})")
    lines.append(f"  record  {MANIFEST}")
    if plan.notes:
        lines.append("")
        lines.extend(plan.notes)
    if plan.sidecars:
        lines.append("")
        lines.append("Edited framework files were left alone. Review each difference, move any")
        lines.append("project-specific content into AGENTS.md or docs/agents/local/, then replace the")
        lines.append("file with its .framework copy:")
        for rel, side in plan.sidecars:
            lines.append(f"  {rel}  <-  {side}")
    return "\n".join(lines)


def apply(plan: Plan) -> None:
    for item, path, _reason in plan.writes:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(item.data)
        if item.executable and os.name != "nt":
            path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    for rel in plan.removals:
        (plan.target / rel).unlink()
        parent = (plan.target / rel).parent
        while parent != plan.target and parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()
            parent = parent.parent
    manifest = plan.target / MANIFEST
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(plan.manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    hook = plan.target / ".githooks/pre-push"
    if any(item.rel == ".githooks/pre-push" for item, _p, r in plan.writes if r == "new") and (plan.target / ".git").exists():
        # Windows cannot record the executable bit on disk; record it in git.
        subprocess.run(["git", "-C", str(plan.target), "add", "--chmod=+x", "--", str(hook)],
                       capture_output=True, check=False)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("target")
    parser.add_argument("--project", help="project name (adoption only)")
    parser.add_argument("--workers", default="worker", help="executor role names, comma-separated (adoption only)")
    parser.add_argument("--verifier", action="store_true", help="list the Verifier seat in AGENTS.md (adoption only)")
    parser.add_argument("--adapter", action="append", default=None, help=f"tool adapter to install: {', '.join(adapter_dirs())}")
    parser.add_argument("--hooks", action="store_true", help="install a sample pre-push hook")
    parser.add_argument("--update", action="store_true", help="update an adopted project to this release")
    parser.add_argument("--dry-run", action="store_true", help="print the plan and write nothing")
    args = parser.parse_args(argv)

    target = Path(args.target).resolve()
    if not target.is_dir():
        raise SystemExit(f"adopt: {target} is not a directory")
    if not args.update and not args.project:
        raise SystemExit("adopt: --project is required when adopting")
    workers = [w.strip() for w in args.workers.split(",") if w.strip()]
    for name in workers:
        fw.check_role(name)
    old = load_manifest(target)
    old_release = (old or {}).get("framework", {}).get("release") if old else ("2.x (no record)" if is_legacy(target) else None)

    plan = build_plan(target, update=args.update, project=args.project, workers=workers,
                      verifier=args.verifier, adapters=args.adapter, hooks=args.hooks)
    print(describe(plan, update=args.update, old_release=old_release))
    if args.dry_run:
        print("\ndry run: nothing written")
        return 0
    apply(plan)

    if args.update:
        since = old_release if old and fw.version_tuple(old_release or "") else None
        steps = changelog_steps(since)
        if steps:
            print("\nWhat each release asks of this project:")
            for version, text in steps:
                print(f"\n--- {version} ---\n{text}")
    findings = fw.check_project(target)
    if findings:
        print("\nProject checks still to satisfy (python3 tools/fw.py check):")
        for level, message in findings:
            print(f"  {level}: {message}")
    if not args.update:
        print("\nNext: fill in AGENTS.md (what the project is, roles, invariants, evidence,")
        print("what is enforced), then commit this as the project's first round.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
