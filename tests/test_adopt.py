"""Adoption is tested by doing it, not by checking that files exist.

`framework/evidence.md` says to test behaviour rather than installation. So this
runs the real script against a real temporary directory and then **runs the
guard it installed there**, in that tree, with that tree's role set. An adopted
project whose installed test cannot even import is the exact "hooks installed
but never executed" failure this framework catalogues.
"""

from __future__ import annotations

import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import adopt  # noqa: E402
import docset  # noqa: E402


def run_adopt(target: Path, *extra: str) -> int:
    return adopt.main([str(target), "--project", "Test Project", *extra])


class AdoptionCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.target = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=self.target, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=self.target, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.target, check=True)
        (self.target / ".seed").write_text("seed\n", encoding="utf-8")
        subprocess.run(["git", "add", ".seed"], cwd=self.target, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=self.target, check=True)
        self.addCleanup(self._tmp.cleanup)


class TestDefaultAdoption(AdoptionCase):
    def setUp(self):
        super().setUp()
        self.assertEqual(run_adopt(self.target), 0)

    def test_expected_tree_is_created(self):
        for rel in (
            "AGENTS.md",
            "docs/agents/CONSTITUTION.md",
            "docs/agents/roles/brain.md",
            "docs/agents/roles/worker.md",
            "docs/agents/roles/verifier.md",
            "docs/agents/lifecycle.md",
            "docs/agents/evidence.md",
            "docs/agents/reports.md",
            "docs/state.md",
            "docs/briefs/README.md",
            "docs/briefs/active.md",
            "tools/neutrality.py",
            "tools/authority.py",
            "tools/textblocks.py",
            "tools/checkout.py",
            "tools/report.py",
            "tools/line_endings.py",
            "tests/test_role_neutrality.py",
            "tests/test_checkout.py",
            "tests/test_report.py",
        ):
            with self.subTest(path=rel):
                self.assertTrue((self.target / rel).is_file(), rel)

    def test_framework_state_guidance_is_not_a_second_project_state_file(self):
        self.assertFalse((self.target / "docs/agents/state.md").exists())
        self.assertTrue((self.target / "docs/state.md").is_file())

    def test_report_py_is_installed_with_no_adapter_at_all(self):
        """The baseline mechanism must not depend on choosing an adapter.

        `--adapter` was not passed in `setUp`; this default-topology adoption
        is exactly the "no adapter, including for a provider that does not
        exist yet" case `reports.md` promises to cover.
        """
        self.assertTrue((self.target / "tools" / "report.py").is_file())
        self.assertTrue((self.target / "docs" / "agents" / "reports.md").is_file())

    def test_shebang_tools_are_installed_executable(self):
        if os.name == "nt":
            self.skipTest(
                "Windows cannot preserve POSIX executable bits; adopt.py warns "
                "and the committed-mode guard runs from the Git index"
            )
        for rel in (
            "tools/authority.py",
            "tools/neutrality.py",
            "tools/textblocks.py",
            "tools/checkout.py",
            "tools/report.py",
            "tools/line_endings.py",
        ):
            with self.subTest(path=rel):
                self.assertTrue((self.target / rel).stat().st_mode & 0o111)

    def test_history_is_not_copied(self):
        # The catalogue and case studies are this repository's evidence, not the
        # adopting project's — and they deliberately contain text the guards
        # reject, which would fail the installed test on day one.
        for rel in ("docs/agents/failure-catalogue.md",
                    "docs/agents/case-studies.md",
                    "docs/agents/adoption.md"):
            with self.subTest(path=rel):
                self.assertFalse((self.target / rel).exists(), rel)

    def test_standards_are_not_copied(self):
        """The repository's presentation reference is outside the framework copy."""
        self.assertFalse((self.target / "standards").exists())

    def test_worktrees_are_ignored_without_reordering_existing_rules(self):
        original = "# local rules\ncache/\n"
        (self.target / ".gitignore").write_text(original, encoding="utf-8")
        self.assertEqual(run_adopt(self.target), 0)
        updated = (self.target / ".gitignore").read_text(encoding="utf-8")
        self.assertEqual(updated, original + ".worktrees/\n")
        self.assertEqual(run_adopt(self.target), 0)
        self.assertEqual((self.target / ".gitignore").read_text(encoding="utf-8"), updated)

    def test_no_unresolved_placeholders(self):
        leftovers = []
        for path in self.target.rglob("*"):
            if path.is_file() and path.suffix in (".md", ".py"):
                text = path.read_text(encoding="utf-8")
                if "{{" in text and "}}" in text:
                    leftovers.append(path.relative_to(self.target).as_posix())
        self.assertEqual(leftovers, [], f"unrendered placeholders: {leftovers}")

    def test_project_name_reaches_the_coordination_document(self):
        text = (self.target / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("Test Project", text)
        self.assertIn("worker", text.lower())

    def test_the_installed_guard_actually_runs_and_passes(self):
        """The whole point: the guard works in the tree it was installed into."""
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
            cwd=self.target, capture_output=True, text=True,
        )
        self.assertEqual(
            proc.returncode, 0,
            f"installed guard failed in the adopted tree:\n{proc.stdout}\n{proc.stderr}",
        )
        self.assertIn("OK", proc.stderr + proc.stdout)

    def test_the_installed_guard_is_not_vacuous(self):
        """It must have actually scanned something, and it must be able to fail.

        Red-before-green, in the adopted tree: introduce a provider-shaped
        branch namespace into the project's own coordination document and prove
        the installed guard rejects it.
        """
        agents = self.target / "AGENTS.md"
        original = agents.read_text(encoding="utf-8")
        agents.write_text(
            original + "\n\nCut the branch: `someprovider/task-scope` for this "
            "round.\n",
            encoding="utf-8",
        )
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", "tests",
                 "-t", "."],
                cwd=self.target, capture_output=True, text=True,
            )
            self.assertNotEqual(
                proc.returncode, 0,
                "the installed guard passed against a provider-shaped branch "
                "namespace; it is not guarding anything",
            )
            self.assertIn("branch-namespace", proc.stdout + proc.stderr)
        finally:
            agents.write_text(original, encoding="utf-8")

    def test_stale_authority_language_is_rejected_in_the_adopted_tree(self):
        agents = self.target / "AGENTS.md"
        original = agents.read_text(encoding="utf-8")
        agents.write_text(
            original + "\n\nBrain reviews the work and will offer to merge; "
            "execute on OK.\n",
            encoding="utf-8",
        )
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", "tests",
                 "-t", "."],
                cwd=self.target, capture_output=True, text=True,
            )
            self.assertNotEqual(
                proc.returncode, 0,
                "the installed guard accepted v1's stale authority language",
            )
            self.assertIn("routine-approval", proc.stdout + proc.stderr)
        finally:
            agents.write_text(original, encoding="utf-8")


class TestTopologyOptions(AdoptionCase):
    def test_neutrality_plan_names_the_canonical_document_coupling(self):
        plan = adopt.build_plan(
            self.target, project="Test Project", coordinator="brain",
            workers=["worker"], verifier=False, hooks=False, adapters=[],
        )
        notes = "\n".join(plan.notes)
        self.assertIn("every docs/agents document copied from VERBATIM_DOCS", notes)
        for module in (
            "tools/neutrality.py", "tools/textblocks.py", "tools/authority.py",
            "tests/test_role_neutrality.py",
        ):
            self.assertIn(module, notes)

    def test_neutrality_installation_can_be_deferred_explicitly(self):
        plan = adopt.build_plan(
            self.target, project="Test Project", coordinator="brain",
            workers=["worker"], verifier=False, hooks=False, adapters=[],
            neutrality=False,
        )
        self.assertTrue(
            any("deferred by --no-neutrality" in note for note in plan.notes)
        )
        self.assertEqual(run_adopt(self.target, "--no-neutrality"), 0)
        for rel in (
            "tools/neutrality.py",
            "tools/authority.py",
            "tools/textblocks.py",
            "tests/test_role_neutrality.py",
        ):
            with self.subTest(path=rel):
                self.assertFalse((self.target / rel).exists())

        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
            cwd=self.target, capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_declared_milestone_namespace_is_installed_and_bounded(self):
        self.assertEqual(
            run_adopt(self.target, "--workers", "builder", "--verifier"),
            0,
        )
        agents = self.target / "AGENTS.md"
        original = agents.read_text(encoding="utf-8")
        declared = (
            original
            + '\n<!-- guard:branch-namespaces prefixes="m<N>,meta" -->\n'
            + "Create `m3/feature-work` and `meta/coordination` as project "
              "branch namespaces.\n"
        )
        agents.write_text(declared, encoding="utf-8")
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
                cwd=self.target, capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

            agents.write_text(
                declared.replace('prefixes="m<N>,meta"', 'prefixes="m<N>,vendor-ai"'),
                encoding="utf-8",
            )
            proc = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
                cwd=self.target, capture_output=True, text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("unsupported branch namespace", proc.stdout + proc.stderr)
        finally:
            agents.write_text(original, encoding="utf-8")

    def test_declared_custom_namespaces_need_tracked_structure(self):
        self.assertEqual(
            run_adopt(self.target, "--workers", "builder", "--verifier"),
            0,
        )
        evidence = self.target / "docs" / "branch-namespaces"
        evidence.mkdir(parents=True)
        for name in ("release", "feature"):
            (evidence / f"{name}.md").write_text(
                f"This project owns the {name} branch namespace.\n",
                encoding="utf-8",
            )
        subprocess.run(["git", "add", "docs/branch-namespaces"], cwd=self.target, check=True)
        subprocess.run(
            ["git", "commit", "-m", "namespace evidence"],
            cwd=self.target, check=True, capture_output=True, text=True,
        )
        agents = self.target / "AGENTS.md"
        original = agents.read_text(encoding="utf-8")
        declared = (
            original
            + '\n<!-- guard:branch-namespaces prefixes="release,feature" -->\n'
            + "Create branch `release/next` and branch `feature/queue` here.\n"
        )
        agents.write_text(declared, encoding="utf-8")
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
                cwd=self.target, capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

            agents.write_text(
                declared + "Create branch `vendor/release` for this round.\n",
                encoding="utf-8",
            )
            proc = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
                cwd=self.target, capture_output=True, text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("branch-namespace", proc.stdout + proc.stderr)
        finally:
            agents.write_text(original, encoding="utf-8")

    def test_builder_verifier_adoption_runs_the_installed_guard(self):
        self.assertEqual(
            run_adopt(self.target, "--workers", "builder", "--verifier"),
            0,
        )
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
            cwd=self.target, capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_unusual_single_role_adoption_runs_the_installed_guard(self):
        """Coverage for a legal topology, not evidence of the blocker fix."""
        self.assertEqual(
            run_adopt(self.target, "--workers", "orthogonalist"),
            0,
        )
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
            cwd=self.target, capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_specialists_and_verifier_reach_the_declared_role_set(self):
        self.assertEqual(
            run_adopt(self.target, "--workers", "decomper,scaffolder", "--verifier"),
            0,
        )
        test_file = (self.target / "tests/test_role_neutrality.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("'decomper'", test_file)
        self.assertIn("'scaffolder'", test_file)
        self.assertIn("'verifier'", test_file)

        agents = (self.target / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("Decomper", agents)
        self.assertIn("Scaffolder", agents)
        self.assertIn("Verifier", agents)

        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
            cwd=self.target, capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_executor_name_clashing_with_a_reserved_role_is_refused(self):
        for bad in ("brain", "verifier", "owner"):
            with self.subTest(name=bad):
                self.assertEqual(run_adopt(self.target, "--workers", bad), 2)

    def test_empty_worker_list_is_refused(self):
        self.assertEqual(run_adopt(self.target, "--workers", ","), 2)

    def test_unknown_adapter_is_refused(self):
        with self.assertRaises(SystemExit):
            run_adopt(self.target, "--adapter", "no-such-tool")

    def test_known_adapter_installs_and_points_at_the_contract(self):
        # The destination is the adapter's declared one, not one built from its
        # name. `tests/test_adapter_install_layout.py` guards that mechanism;
        # this only checks the seat is usable once it is there.
        self.assertEqual(run_adopt(self.target, "--adapter", "claude-code"), 0)
        adapter = self.target / ".claude" / "agents" / "worker.md"
        self.assertTrue(adapter.is_file())
        self.assertIn("docs/agents/roles/worker.md", adapter.read_text(encoding="utf-8"))

    def test_adapter_shebang_files_are_installed_executable(self):
        if os.name == "nt":
            self.skipTest(
                "Windows cannot preserve POSIX executable bits; adopt.py warns "
                "and the committed-mode guard runs from the Git index"
            )
        self.assertEqual(run_adopt(self.target, "--adapter", "claude-code"), 0)
        for rel in (
            ".claude/hooks/run_python.sh",
            ".claude/hooks/save_agent_reply.py",
        ):
            with self.subTest(path=rel):
                self.assertTrue((self.target / rel).stat().st_mode & 0o111)

    def test_a_specialist_topology_still_gets_the_generic_executor_seat(self):
        self.assertEqual(
            run_adopt(self.target, "--adapter", "claude-code",
                      "--workers", "decomper,scaffolder"),
            0,
        )
        agents_dir = self.target / ".claude" / "agents"
        self.assertEqual(
            sorted(p.name for p in agents_dir.glob("*.md")),
            ["brain.md", "verifier.md", "worker.md"],
            "an adapter ships one seat per role contract; a specialist is the "
            "executor contract plus a scope statement, not a new one",
        )

    def test_hooks_are_installed_only_when_asked(self):
        self.assertEqual(run_adopt(self.target, "--hooks"), 0)
        self.assertTrue((self.target / ".githooks/pre-push").is_file())


class TestLineEndingWarnings(AdoptionCase):
    def test_adoption_warns_on_existing_crlf_hooks_using_git_ls_files_eol(self):
        attributes = self.target / ".gitattributes"
        attributes.write_text("* text=auto eol=lf\n", encoding="utf-8")
        hook = self.target / ".githooks/pre-push"
        hook.parent.mkdir()
        hook.write_bytes(b"#!/bin/sh\r\nexit 0\r\n")
        subprocess.run(["git", "add", ".gitattributes", ".githooks"], cwd=self.target, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "old hook"], cwd=self.target, check=True,
        )
        # Reproduce the real migration hazard: the index is normalized, but an
        # unchanged pre-existing worktree file remains CRLF.
        hook.write_bytes(b"#!/bin/sh\r\nexit 0\r\n")
        linked = self.target / ".worktrees" / "old"
        subprocess.run(
            ["git", "worktree", "add", "-q", str(linked), "HEAD"],
            cwd=self.target, check=True,
        )
        linked_hook = linked / ".githooks" / "pre-push"
        linked_hook.write_bytes(b"#!/bin/sh\r\nexit 0\r\n")
        eol = subprocess.run(
            ["git", "ls-files", "--eol", "--", ".githooks"],
            cwd=self.target, capture_output=True, text=True, check=True,
        ).stdout
        self.assertIn("i/lf", eol)
        self.assertIn("w/crlf", eol)
        self.assertIn("attr/text=auto eol=lf", eol)

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(run_adopt(self.target), 0)
        self.assertIn("tracked executable framework text file(s)", output.getvalue())
        self.assertIn("tools/line_endings.py check", output.getvalue())
        self.assertIn(str(linked.resolve()), output.getvalue())

    def test_adoption_warns_on_a_tracked_adapter_script_not_in_githooks(self):
        script = self.target / ".claude" / "hooks" / "run_python.sh"
        script.parent.mkdir(parents=True)
        script.write_bytes(b"#!/bin/sh\r\nexit 0\r\n")
        script.chmod(0o755)
        subprocess.run(["git", "add", ".claude"], cwd=self.target, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "old adapter hook"],
            cwd=self.target, check=True,
        )

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(run_adopt(self.target, "--adapter", "claude-code"), 0)
        self.assertIn(".claude/hooks/run_python.sh", output.getvalue())

    def test_adoption_discovers_an_executable_script_outside_known_hook_roots(self):
        script = self.target / "future-adapter" / "hooks" / "stop.sh"
        script.parent.mkdir(parents=True)
        script.write_bytes(b"#!/bin/sh\r\nexit 0\r\n")
        script.chmod(0o755)
        subprocess.run(["git", "add", "future-adapter"], cwd=self.target, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "future adapter hook"],
            cwd=self.target, check=True,
        )

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(run_adopt(self.target), 0)
        self.assertIn("future-adapter/hooks/stop.sh", output.getvalue())


class TestLineEndingRefresh(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name) / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.repo, check=True)
        for rel in (".githooks/pre-push", ".claude/hooks/run_python.sh"):
            path = self.repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"#!/bin/sh\r\nexit 0\r\n")
            path.chmod(0o755)
        (self.repo / "seat.txt").write_text("seat\n", encoding="utf-8")
        (self.repo / ".gitignore").write_text(".worktrees/\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=self.repo, check=True)
        (self.repo / ".gitattributes").write_text("* text=auto eol=lf\n", encoding="utf-8")
        subprocess.run(["git", "add", ".gitattributes"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "adopt attributes"], cwd=self.repo, check=True)
        self.addCleanup(self._tmp.cleanup)

    def _stash_list(self, cwd=None):
        return subprocess.run(
            ["git", "stash", "list"], cwd=cwd or self.repo,
            capture_output=True, text=True, check=True,
        ).stdout

    def test_refresh_does_not_pop_an_older_stash_from_a_clean_tree(self):
        (self.repo / "seat.txt").write_text("older local work\n", encoding="utf-8")
        subprocess.run(["git", "stash", "push", "-q", "-m", "older unrelated stash"], cwd=self.repo, check=True)
        self.assertEqual(
            subprocess.run(["git", "status", "--short"], cwd=self.repo,
                           capture_output=True, text=True, check=True).stdout,
            "",
            "the CRLF worktree bytes are clean under eol=lf",
        )
        before = self._stash_list()
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "line_endings.py"), "refresh"],
            cwd=self.repo, capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self._stash_list(), before)
        self.assertEqual((self.repo / ".claude/hooks/run_python.sh").read_bytes(), b"#!/bin/sh\nexit 0\n")
        self.assertEqual((self.repo / ".githooks/pre-push").read_bytes(), b"#!/bin/sh\nexit 0\n")
        self.assertEqual((self.repo / "seat.txt").read_text(encoding="utf-8"), "seat\n")

    def test_refresh_is_safe_in_a_worktree_while_another_seat_holds_a_stash(self):
        other = self.repo / ".worktrees" / "other"
        subprocess.run(["git", "worktree", "add", "-q", str(other), "HEAD"], cwd=self.repo, check=True)
        (other / "seat.txt").write_text("other seat work\n", encoding="utf-8")
        subprocess.run(["git", "stash", "push", "-q", "-m", "other seat stash"], cwd=other, check=True)
        self.assertEqual(
            subprocess.run(["git", "status", "--short"], cwd=other,
                           capture_output=True, text=True, check=True).stdout,
            "",
            "the CRLF worktree bytes are clean under eol=lf",
        )
        for rel in (".githooks/pre-push", ".claude/hooks/run_python.sh"):
            (self.repo / rel).write_bytes(b"#!/bin/sh\r\nexit 0\r\n")
        self.assertEqual(
            subprocess.run(["git", "status", "--short"], cwd=self.repo,
                           capture_output=True, text=True, check=True).stdout,
            "",
            "the primary CRLF worktree bytes are clean under eol=lf",
        )
        before = self._stash_list(other)
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "line_endings.py"), "refresh"],
            cwd=self.repo, capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self._stash_list(other), before)
        self.assertEqual((self.repo / ".claude/hooks/run_python.sh").read_bytes(), b"#!/bin/sh\nexit 0\n")
        self.assertEqual((self.repo / ".githooks/pre-push").read_bytes(), b"#!/bin/sh\nexit 0\n")


class TestLineEndingGuidance(unittest.TestCase):
    def test_guidance_is_stash_free_and_uses_the_complete_refresh_tool(self):
        for rel in ("framework/adoption.md", "framework/git-and-isolation.md"):
            text = (ROOT / rel).read_text(encoding="utf-8")
            with self.subTest(document=rel):
                self.assertIn("python3 tools/line_endings.py check", text)
                self.assertIn("python3 tools/line_endings.py refresh", text)
                self.assertNotIn("git stash push", text)
                self.assertNotIn("git stash pop", text)
                self.assertIn("separate clone", text)


class TestSafety(AdoptionCase):
    def test_dry_run_writes_nothing(self):
        before = sorted(p.name for p in self.target.iterdir())
        self.assertEqual(run_adopt(self.target, "--dry-run"), 0)
        self.assertEqual(sorted(p.name for p in self.target.iterdir()), before)

    def test_existing_files_are_never_overwritten(self):
        agents = self.target / "AGENTS.md"
        agents.write_text("PROJECT'S OWN FILE\n", encoding="utf-8")
        self.assertEqual(run_adopt(self.target), 0)
        self.assertEqual(agents.read_text(encoding="utf-8"), "PROJECT'S OWN FILE\n")
        self.assertTrue((self.target / "AGENTS.md.framework").is_file())

    def test_rerunning_is_safe(self):
        self.assertEqual(run_adopt(self.target), 0)
        first = (self.target / "docs/agents/CONSTITUTION.md").read_text(
            encoding="utf-8"
        )
        self.assertEqual(run_adopt(self.target), 0)
        # Second run collides with itself and writes siblings rather than
        # clobbering; the original is untouched either way.
        self.assertEqual(
            (self.target / "docs/agents/CONSTITUTION.md").read_text(encoding="utf-8"),
            first,
        )

    def test_missing_target_is_refused(self):
        self.assertEqual(
            run_adopt(self.target / "does-not-exist"), 2
        )

    def test_adoption_fails_when_executable_bit_does_not_take(self):
        plan = adopt.Plan(writes=[
            (self.target / "hook", "#!/bin/sh\n", True),
        ])
        with mock.patch.object(adopt.os, "name", "nt"):
            self.assertEqual(adopt.apply_plan(plan), [self.target / "hook"])

    def test_real_mode_postcondition_rejects_a_nonexecutable_file(self):
        path = self.target / "not-executable"
        path.write_text("content\n", encoding="utf-8")
        path.chmod(0o644)
        self.assertFalse(adopt.executable_bit_took(path))

    def test_adoption_writes_lf_without_path_write_text(self):
        plan = adopt.Plan(writes=[
            (self.target / "nested" / "script.sh", "#!/bin/sh\nrun\n", False),
        ])
        with mock.patch.object(
            Path, "write_text", side_effect=AssertionError("use explicit LF I/O")
        ):
            self.assertEqual(adopt.apply_plan(plan), [])
        self.assertEqual(
            (self.target / "nested" / "script.sh").read_bytes(),
            b"#!/bin/sh\nrun\n",
        )


class TestVerbatimDocsStayInSync(unittest.TestCase):
    def test_every_copied_document_exists_here(self):
        for rel in adopt.VERBATIM_DOCS:
            with self.subTest(doc=rel):
                self.assertTrue((ROOT / "framework" / rel).is_file(), rel)

    def test_adoption_table_lists_every_verbatim_document(self):
        table = (ROOT / "framework" / "adoption.md").read_text(encoding="utf-8")
        for rel in adopt.VERBATIM_DOCS:
            with self.subTest(doc=rel):
                self.assertIn(f"`docs/agents/{rel}`", table)

    def test_adoption_table_lists_the_default_guard_files(self):
        table = (ROOT / "framework" / "adoption.md").read_text(encoding="utf-8")
        copied = (
            "tests/test_role_neutrality.py",
            "tests/test_checkout.py",
            "tests/test_report.py",
            "tools/neutrality.py",
            "tools/authority.py",
            "tools/textblocks.py",
            "tools/checkout.py",
            "tools/report.py",
            "tools/line_endings.py",
        )
        for rel in copied:
            with self.subTest(path=rel):
                self.assertIn(f"`{rel}`", table)

    def test_nothing_normative_is_silently_left_behind(self):
        """A new framework document must be a deliberate copy-or-not decision.

        Without this, adding a document here would silently fail to reach any
        adopting project, and nobody would notice until it was needed.
        """
        copied = set(adopt.VERBATIM_DOCS)
        excluded = set(adopt.NOT_COPIED)
        tracked = docset.tracked_paths()
        for path in sorted(
            p for p in tracked
            if p.suffix == ".md" and ROOT / "framework" in p.parents
        ):
            rel = path.relative_to(ROOT / "framework").as_posix()
            with self.subTest(doc=rel):
                self.assertTrue(
                    rel in copied or rel in excluded or path.name in excluded,
                    f"{rel} is neither copied on adoption nor explicitly "
                    f"excluded; decide which and record it in adopt.py",
                )


class TestInstalledCheckoutSuiteRunsFromAnyRoleWorktree(unittest.TestCase):
    """`templates/tests/test_checkout.py` is installed into every adopted
    project's own test suite, so it must pass wherever that suite is
    actually run from -- the primary, coordinating checkout, and every
    role's own linked worktree (e.g. `.worktrees/worker`) alike. A prior
    version hardcoded the coordinating seat `brain` as the one to claim,
    which made `python3 -m unittest discover` fail outright the moment it
    was run from a role worktree -- see `framework/git-and-isolation.md` for
    why that is the normal, expected place to run it from.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.target = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=self.target, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=self.target, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.target, check=True)
        (self.target / ".seed").write_text("seed\n", encoding="utf-8")
        subprocess.run(["git", "add", ".seed"], cwd=self.target, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=self.target, check=True)
        self.assertEqual(run_adopt(self.target, "--workers", "worker"), 0)
        subprocess.run(["git", "add", "-A"], cwd=self.target, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "adopt"], cwd=self.target, check=True)
        self.addCleanup(self._tmp.cleanup)
        self.worker = self.target / ".worktrees" / "worker"
        subprocess.run(
            ["git", "worktree", "add", "--detach", str(self.worker), "HEAD"],
            cwd=self.target, check=True, capture_output=True,
        )

    def _run_installed_suite(self, cwd: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", "unittest", "tests.test_checkout"],
            cwd=cwd, capture_output=True, text=True,
        )

    def test_passes_from_the_primary_checkout(self):
        proc = self._run_installed_suite(self.target)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_passes_from_a_role_worktree(self):
        proc = self._run_installed_suite(self.worker)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_the_pre_fix_hardcoded_seat_fails_from_a_role_worktree(self):
        """Red-before-green: the exact regression this closes, reproduced by
        restoring the one line the fix replaced -- claiming the hardcoded
        seat `brain` instead of this checkout's own, structurally-derived
        seat -- rather than by asserting against a description of it.
        """
        marker = "self.actual_seat = checkout.checkout_seat(ROOT)"
        for cwd in (self.target, self.worker):
            installed = cwd / "tests" / "test_checkout.py"
            text = installed.read_text(encoding="utf-8")
            self.assertIn(marker, text, "fixture out of sync with the template")
            installed.write_text(
                text.replace(marker, 'self.actual_seat = "brain"'),
                encoding="utf-8",
            )

        # The primary checkout IS the coordinator, so hardcoding "brain" is
        # still correct there -- this is not a vacuous mutation.
        proc = self._run_installed_suite(self.target)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

        proc = self._run_installed_suite(self.worker)
        self.assertNotEqual(
            proc.returncode, 0,
            "the pre-fix hardcoded seat unexpectedly passed from a role "
            "worktree; this does not reproduce the incident",
        )
        self.assertIn("seat=brain", proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
