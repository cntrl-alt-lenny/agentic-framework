"""The owner-facing loop has to survive being started from nothing.

`framework/kickoff.md` is what makes Brain -> Builder -> Verifier -> Brain
runnable from completely fresh sessions: the owner pastes a fixed block, gets
two prompts back, runs them, and pastes a second fixed block to come back. The
value of that depends on properties no prose review reliably catches, so they
are asserted here.

The point is not that the words stay the same -- they should be free to
improve. It is that the *mechanism* cannot quietly lose a load-bearing half:
Brain issuing only one prompt again, or the Verifier gaining permission to
review a branch without pinning the commit it actually reviewed.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import adopt  # noqa: E402

KICKOFF = ROOT / "framework" / "kickoff.md"
BRAIN = ROOT / "framework" / "roles" / "brain.md"
VERIFIER = ROOT / "framework" / "roles" / "verifier.md"
LIFECYCLE = ROOT / "framework" / "lifecycle.md"

FENCED = re.compile(r"^```\n(.*?)^```", re.S | re.M)


class TestTheKickoffReachesProjects(unittest.TestCase):
    def test_it_exists(self):
        self.assertTrue(KICKOFF.is_file())

    def test_adoption_installs_it(self):
        """A loop document only this repository has does not help any project."""
        self.assertIn(
            "kickoff.md", adopt.VERBATIM_DOCS,
            "kickoff.md must be copied into adopting projects; it is the one "
            "document the owner actually opens",
        )


class TestThePasteableBlocksAreUsable(unittest.TestCase):
    """Fresh sessions have no history, so the blocks must carry everything."""

    def setUp(self):
        self.text = KICKOFF.read_text(encoding="utf-8")
        self.blocks = FENCED.findall(self.text)

    def test_there_are_blocks_to_paste(self):
        # Fail closed: prose describing a paste-able block is not one.
        self.assertGreaterEqual(
            len(self.blocks), 2,
            "the loop needs at least two paste-able blocks: one to start a "
            "round and one to come back from it",
        )

    def test_the_starting_block_points_the_session_at_its_contract(self):
        """A seat that never reads its contract is not holding it."""
        start = next(
            (b for b in self.blocks if "You are the Brain" in b), None
        )
        self.assertIsNotNone(start, "no block starts a Brain session")
        self.assertIn("AGENTS.md", start)
        self.assertIn("roles/brain.md", start)

    def test_the_brain_prompt_starts_with_the_checkout_check(self):
        start = next(b for b in self.blocks if "You are the Brain" in b)
        first_instruction = next(
            line.strip() for line in start.splitlines() if line.strip()
        )
        self.assertEqual(
            first_instruction, "Before anything else, run:",
            "the first prompt action must be the mechanical checkout check",
        )
        self.assertIn("python3 tools/checkout.py --seat brain", start)

    def test_brain_requires_each_generated_prompt_to_start_with_its_check(self):
        text = " ".join(BRAIN.read_text(encoding="utf-8").split())
        self.assertIn(
            "Every prompt Brain writes for another seat must put that seat's "
            "corresponding checkout check before its first other instruction",
            text,
        )

    def test_the_starting_block_asks_for_both_prompts(self):
        start = next(b for b in self.blocks if "You are the Brain" in b)
        self.assertIn("Builder prompt", start)
        self.assertIn("if and only if this project has a standing Verifier", start)
        self.assertIn("no Verifier prompt is needed", start)

    def test_a_returning_block_exists_so_the_owner_need_not_improvise(self):
        self.assertTrue(
            any("finished" in b and "adjudicate" in b for b in self.blocks),
            "no block covers coming back to Brain once the round has run",
        )

    def test_the_owner_order_is_next_to_the_prompt_blocks(self):
        text = " ".join(self.text.split())
        self.assertIn("sends the Builder prompt first", text)
        self.assertIn(
            "sends the Verifier prompt only after the Builder has finished",
            text,
        )
        self.assertIn(
            "I sent the Verifier prompt only after the Builder finished",
            text,
        )


class TestBrainStillIssuesBothPrompts(unittest.TestCase):
    """The regression this exists to prevent: silently going back to one."""

    def test_the_contract_requires_a_separate_verifier_prompt(self):
        text = BRAIN.read_text(encoding="utf-8")
        self.assertIn("Verifier prompt", text)
        self.assertIn(
            "same turn", text,
            "Brain may prepare both prompt blocks in one response",
        )
        self.assertIn("sends the Builder prompt first", text)
        self.assertIn("only after the Builder has finished", text)

    def test_the_contract_makes_the_verifier_topology_conditional(self):
        text = " ".join(BRAIN.read_text(encoding="utf-8").split())
        self.assertIn("Do not issue a Verifier prompt at all where the topology has no Verifier seat", text)
        self.assertIn("strictly ahead of the base", text)
        self.assertIn('"not delivered yet"', text)

    def test_all_loop_documents_make_owner_order_explicit(self):
        for path in (KICKOFF, BRAIN, LIFECYCLE, VERIFIER):
            with self.subTest(path=path):
                text = " ".join(path.read_text(encoding="utf-8").split())
                expected = (
                    "only after the executor has finished"
                    if path == VERIFIER
                    else "only after the Builder has finished"
                )
                self.assertIn(expected, text)
                self.assertNotIn("opens both sessions at once", text)
                self.assertNotIn("starts both sessions at the same time", text)
                self.assertNotIn("Verifier waits for mechanical delivery", text)


class TestEarlyVerifierPromptsKeepExactShaDiscipline(unittest.TestCase):
    """Both halves, because dropping either one is a real defect.

    Allowing a branch without requiring the resolved SHA turns exact-SHA review
    into review of a moving target -- which `evidence.md` treats as the thing
    that makes review mean anything.
    """

    def setUp(self):
        # Prose here is hard-wrapped, so a phrase spanning a line break would
        # fail a naive substring check. Collapse whitespace first -- the same
        # reason `tools/textblocks.py` gives the scanners logical lines.
        self.text = " ".join(VERIFIER.read_text(encoding="utf-8").split())

    def test_a_branch_may_be_given_instead_of_a_head_sha(self):
        self.assertIn("branch", self.text)
        self.assertIn("resolve it yourself", self.text)

    def test_but_the_literal_sha_must_still_be_recorded(self):
        self.assertIn(
            "literal SHA", self.text,
            "resolving a branch is only acceptable if the SHA actually "
            "reviewed is pinned and reported",
        )

    def test_a_missing_branch_stops_the_review_rather_than_widening_it(self):
        self.assertIn("not delivered yet", self.text)
        self.assertIn(
            "never a reason to review the base", self.text,
            "a Verifier that falls back to the default branch when the work "
            "has not landed reports on the wrong thing",
        )


class TestDeliveryCommand(unittest.TestCase):
    """The Verifier gate must distinguish branch existence from delivery."""

    TASK = "round-002"

    def _git(self, repo: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", *args], cwd=repo, capture_output=True, text=True, check=True,
        )
        return result.stdout.strip()

    def _repo(self) -> tuple[tempfile.TemporaryDirectory, Path, str]:
        tmp = tempfile.TemporaryDirectory()
        repo = Path(tmp.name)
        self._git(repo, "init", "-q", "-b", "main")
        self._git(repo, "config", "user.email", "test@example.invalid")
        self._git(repo, "config", "user.name", "Test")
        (repo / "README.md").write_text("base\n", encoding="utf-8")
        self._git(repo, "add", "README.md")
        self._git(repo, "commit", "-q", "-m", "base")
        return tmp, repo, self._git(repo, "rev-parse", "HEAD")

    def _check(self, repo: Path, base: str):
        return subprocess.run(
            [
                sys.executable, str(ROOT / "tools" / "report.py"), "delivery",
                "--branch", "worker/task", "--base", base,
                "--role", "builder", "--task", self.TASK,
            ],
            cwd=repo, capture_output=True, text=True,
        )

    def test_not_yet_pushed_branch_is_not_delivered(self):
        tmp, repo, base = self._repo()
        self.addCleanup(tmp.cleanup)
        proc = self._check(repo, base)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("not delivered yet", proc.stdout)

    def test_pushed_at_base_branch_is_not_delivered(self):
        tmp, repo, base = self._repo()
        self.addCleanup(tmp.cleanup)
        self._git(repo, "branch", "worker/task", base)
        proc = self._check(repo, base)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("still at the base", proc.stdout)

    def test_report_and_advanced_branch_are_delivered(self):
        tmp, repo, base = self._repo()
        self.addCleanup(tmp.cleanup)
        self._git(repo, "branch", "worker/task", base)
        builder = repo / ".worktrees" / "builder"
        self._git(repo, "worktree", "add", "-q", str(builder), "worker/task")
        (builder / "change.txt").write_text("delivered\n", encoding="utf-8")
        self._git(builder, "add", "change.txt")
        self._git(builder, "commit", "-q", "-m", "deliver")
        report = subprocess.run(
            [
                sys.executable, str(ROOT / "tools" / "report.py"), "write",
                "--task", self.TASK,
            ],
            cwd=builder, input="Builder delivered.\n", capture_output=True, text=True,
        )
        self.assertEqual(report.returncode, 0, report.stdout + report.stderr)
        proc = self._check(repo, base)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("delivered:", proc.stdout)

    def test_separate_clones_discover_delivery_only_after_builder_pushes(self):
        """The fetch is exercised against a real bare remote and two clones."""
        tmp, seed, base = self._repo()
        self.addCleanup(tmp.cleanup)
        remote = Path(tmp.name) / "origin.git"
        self._git(seed, "init", "--bare", "-q", str(remote))
        self._git(seed, "remote", "add", "origin", str(remote))
        self._git(seed, "push", "-q", "origin", "main")

        builder = Path(tmp.name) / "builder"
        verifier = Path(tmp.name) / "verifier"
        subprocess.run(
            ["git", "clone", "-q", "-b", "main", str(remote), str(builder)],
            check=True,
        )
        subprocess.run(
            ["git", "clone", "-q", "-b", "main", str(remote), str(verifier)],
            check=True,
        )
        for clone in (builder, verifier):
            self._git(clone, "config", "user.email", "test@example.invalid")
            self._git(clone, "config", "user.name", "Test")
        self._git(verifier, "branch", "worker/task", base)

        self._git(builder, "switch", "-c", "worker/task")
        self._git(builder, "switch", "main")
        builder_checkout = builder / ".worktrees" / "builder"
        self._git(builder, "worktree", "add", "-q", str(builder_checkout), "worker/task")
        (builder_checkout / "change.txt").write_text(
            "delivered\n", encoding="utf-8"
        )
        self._git(builder_checkout, "add", "change.txt")
        self._git(builder_checkout, "commit", "-q", "-m", "deliver")
        report = subprocess.run(
            [
                sys.executable, str(ROOT / "tools" / "report.py"), "write",
                "--task", self.TASK,
            ],
            cwd=builder_checkout, input="Builder delivered.\n",
            capture_output=True, text=True,
        )
        self.assertEqual(report.returncode, 0, report.stdout + report.stderr)

        verifier_inbox = verifier / ".git" / "agent-inbox"
        verifier_inbox.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(
            builder / ".git" / "agent-inbox" / "builder-latest.md",
            verifier_inbox / "builder-latest.md",
        )

        before_push = self._check(verifier, base)
        self.assertEqual(before_push.returncode, 1, before_push.stdout)
        self.assertIn("not delivered yet", before_push.stdout)

        self._git(builder_checkout, "push", "-q", "-u", "origin", "worker/task")
        after_push = self._check(verifier, base)
        self.assertEqual(after_push.returncode, 0, after_push.stdout + after_push.stderr)
        self.assertIn("delivered:", after_push.stdout)

    def test_diverged_local_branch_is_retryable_and_explains_the_conflict(self):
        tmp, seed, base = self._repo()
        self.addCleanup(tmp.cleanup)
        remote = Path(tmp.name) / "origin.git"
        self._git(seed, "init", "--bare", "-q", str(remote))
        self._git(seed, "remote", "add", "origin", str(remote))
        self._git(seed, "push", "-q", "origin", "main")

        builder = Path(tmp.name) / "builder"
        verifier = Path(tmp.name) / "verifier"
        for clone in (builder, verifier):
            subprocess.run(
                ["git", "clone", "-q", "-b", "main", str(remote), str(clone)],
                check=True,
            )
            self._git(clone, "config", "user.email", "test@example.invalid")
            self._git(clone, "config", "user.name", "Test")

        self._git(builder, "switch", "-c", "worker/task")
        (builder / "remote.txt").write_text("remote\n", encoding="utf-8")
        self._git(builder, "add", "remote.txt")
        self._git(builder, "commit", "-q", "-m", "remote delivery")
        remote_head = self._git(builder, "rev-parse", "HEAD")
        self._git(builder, "push", "-q", "-u", "origin", "worker/task")

        self._git(verifier, "switch", "-c", "worker/task")
        (verifier / "local.txt").write_text("local\n", encoding="utf-8")
        self._git(verifier, "add", "local.txt")
        self._git(verifier, "commit", "-q", "-m", "local divergence")
        proc = self._check(verifier, base)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("diverges", proc.stdout)
        self.assertIn(remote_head, proc.stdout)

    def test_unreachable_remote_stays_retryable(self):
        """Regression coverage: this passed before the fetch/reconciliation fix."""
        tmp, repo, base = self._repo()
        self.addCleanup(tmp.cleanup)
        self._git(repo, "remote", "add", "origin", str(Path(tmp.name) / "missing.git"))
        proc = self._check(repo, base)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("not delivered yet", proc.stdout)
        self.assertNotIn("Traceback", proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
