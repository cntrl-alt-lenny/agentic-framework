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

    def test_nonportable_role_names_are_refused_before_work_starts(self):
        """Checkout identity and report paths must share one portable rule."""
        for role in ("vérifier", "Builder", "bad?role", "con"):
            with self.subTest(role=role):
                path = self._worktree(role)
                code, message = checkout.check(role, path)
                self.assertEqual(code, 1)
                self.assertIn("invalid role name", message)
                self.assertIn(role, message)

    def test_unassigned_separate_clone_is_the_coordinating_seat(self):
        clone = Path(self.tmp.name) / "separate-clone"
        subprocess.run(["git", "clone", "-q", str(self.repo), str(clone)], check=True)
        self.assertEqual(checkout.check("brain", clone)[0], 0)
        code, message = checkout.check("researcher", clone)
        self.assertEqual(code, 1)

    def test_separate_clone_cannot_be_assigned_a_non_coordinator_seat(self):
        """A separate clone's completion-report inbox is private to it.

        Reports written by `role_tag` (`tools/report.py`) into a non-shared
        `git-common-dir` are invisible to a delivery check run from any other
        checkout -- see `framework/git-and-isolation.md`. Granting the seat
        here anyway would pass the checkout check and then silently fail
        every downstream delivery check, which is exactly the mis-tag this
        must refuse instead of committing. Both the seat it names, and the
        coordinator itself, must fail while the clone carries this setting --
        the clone is unusable until the setting is removed or corrected.
        """
        clone = Path(self.tmp.name) / "separate-clone"
        subprocess.run(["git", "clone", "-q", str(self.repo), str(clone)], check=True)
        git(clone, "config", "--local", "framework.checkout-seat", "researcher")

        code, message = checkout.check("researcher", clone)
        self.assertEqual(code, 1)
        self.assertIn("not supported", message)
        self.assertIn("researcher", message)

        code, message = checkout.check("brain", clone)
        self.assertEqual(
            code, 1,
            "a misconfigured clone must not quietly pass as the coordinator "
            "either -- the stray setting must be resolved, not ignored",
        )
        self.assertIn("not supported", message)

    def test_separate_clone_explicitly_assigned_the_coordinator_seat_passes(self):
        """Explicitly naming the coordinator is not the same as misassigning
        a role; it must keep working exactly like the unassigned case."""
        clone = Path(self.tmp.name) / "separate-clone"
        subprocess.run(["git", "clone", "-q", str(self.repo), str(clone)], check=True)
        git(clone, "config", "--local", "framework.checkout-seat", "brain")
        self.assertEqual(checkout.check("brain", clone)[0], 0)


if __name__ == "__main__":
    unittest.main()
