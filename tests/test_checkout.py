"""The first-action checkout check fails closed without provider metadata."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(ROOT / "tools"))
import checkout  # noqa: E402


def git(path: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=path, check=True, capture_output=True, text=True,
    ).stdout.strip()


class TestCheckoutCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "project"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.email", "test@example.invalid")
        git(self.repo, "config", "user.name", "Test")
        (self.repo / "README.md").write_text("base\n", encoding="utf-8")
        git(self.repo, "add", "README.md")
        git(self.repo, "commit", "-q", "-m", "base")
        self.addCleanup(self.tmp.cleanup)

    def _worktree(self, role: str) -> Path:
        path = self.repo / ".worktrees" / role
        git(self.repo, "worktree", "add", "--detach", "-q", str(path), "HEAD")
        self.addCleanup(lambda: subprocess.run(
            ["git", "worktree", "remove", "--force", str(path)],
            cwd=self.repo, capture_output=True,
        ))
        return path

    def test_primary_checkout_passes_only_for_coordinator(self):
        self.assertEqual(checkout.check("brain", self.repo)[0], 0)
        code, message = checkout.check("builder", self.repo)
        self.assertEqual(code, 1)
        self.assertIn(str(self.repo), message)
        self.assertIn(".worktrees/builder", message)

    def test_linked_worktrees_match_unusual_role_names_and_reject_cross_claims(self):
        role = "orthogonalist"
        path = self._worktree(role)
        self.assertEqual(checkout.check(role, path)[0], 0)
        code, message = checkout.check("verifier", path)
        self.assertEqual(code, 1)
        self.assertIn(role, message)

    def test_separate_clone_uses_local_assignment_because_it_looks_primary(self):
        clone = Path(self.tmp.name) / "separate-clone"
        subprocess.run(["git", "clone", "-q", str(self.repo), str(clone)], check=True)
        self.assertEqual(checkout.check("brain", clone)[0], 0)
        git(clone, "config", "--local", "framework.checkout-seat", "researcher")
        self.assertEqual(checkout.check("researcher", clone)[0], 0)
        self.assertEqual(checkout.check("brain", clone)[0], 1)


if __name__ == "__main__":
    unittest.main()
