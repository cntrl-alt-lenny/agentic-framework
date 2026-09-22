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
    "tests/test_checkout.py", "tests/test_report.py",
}
#: Generated from a template per project, so it has no fixed fingerprint. It is
#: recognised by content and removed together with the scanner it imports.
RENDERED_LEGACY = {"tests/test_role_neutrality.py": ("import neutrality", "tools/neutrality.py")}


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


def legacy_fingerprints() -> dict[str, list[str]]:
    data = json.loads((ROOT / "tools" / "legacy_installs.json").read_text(encoding="utf-8"))
    return data["files"]


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


def referenced_by_kept(target: Path, rel: str, removing: set[str]) -> str | None:
    """A kept configuration or code file that still refers to ``rel``, if any."""
    if not (target / ".git").exists():
        return None
    patterns = [re.escape(rel)]
    if rel.startswith("tools/") and rel.endswith(".py"):
        module = Path(rel).stem
        patterns.append(rf"^[[:space:]]*(from {module} import|import {module}([[:space:]]|,|$))")
    for pattern in patterns:
        result = subprocess.run(
            ["git", "-C", str(target), "grep", "-l", "-E", pattern, "--",
             "*.py", "*.sh", "*.json", "*.toml", "*.yml", "*.yaml", ".githooks/*"],
            capture_output=True, text=True, check=False,
        )
        for hit in result.stdout.splitlines():
            if hit != rel and hit != MANIFEST and hit not in removing and not hit.endswith(".framework"):
                return hit
    return None


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
    if adapters is None:
        adapters = list(options.get("adapters", []))
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
    known = legacy_fingerprints()

    def unedited(rel: str, data: bytes) -> bool:
        h = digest(data)
        entry = old_files.get(rel)
        if entry and entry.get("kind") == "copy":
            return entry.get("sha256") == h
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
            for rel in known:
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
        for rel, (marker, depends) in RENDERED_LEGACY.items():
            path = target / rel
            if path.is_file() and marker in path.read_text(encoding="utf-8", errors="replace"):
                if depends in removing or not (target / depends).exists():
                    removing.add(rel)
                else:
                    plan.retained.append((rel, f"kept because {depends} is kept"))
        changed = True
        while changed:
            changed = False
            for rel in sorted(removing):
                holder = referenced_by_kept(target, rel, removing)
                if holder:
                    removing.discard(rel)
                    plan.retained.append((rel, f"unedited, but {holder} still refers to it; remove that reference, then delete it"))
                    changed = True
        plan.removals = sorted(removing)

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
