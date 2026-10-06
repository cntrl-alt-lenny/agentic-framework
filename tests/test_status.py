"""Where things stand, with every seat in a different clone.

Each clone stands for a different machine or a cloud tool's fresh workspace.
Nothing may pass between them except through the shared remote -- which is the
property the framework's continuity promise rests on.
"""

from __future__ import annotations

from tests.helpers import BatchTest, fw, git


class WorkNotMerged(BatchTest):
    def status(self) -> str:
        git(self.brain, "fetch", "-q", "--prune", "origin")
        result = fw(self.brain, "status", "--offline")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def test_nothing_waiting_says_so(self) -> None:
        out = self.status()
        self.assertIn("nothing waiting: every branch is merged", out)
        self.assertIn("next: nothing is waiting on you; ask Brain for the next batch", out)

    def test_each_batch_is_followed_from_working_to_judged(self) -> None:
        worker = self.deliver_worker("worker-pc", "01-menus", summary=False)
        out = self.status()
        self.assertIn("worker/01-menus: 1 commit(s)", out)
        self.assertIn("no summary yet", out)
        (worker / "docs/batches").mkdir(parents=True, exist_ok=True)
        (worker / "docs/batches/01-menus.md").write_text("# Summary\n", encoding="utf-8")
        git(worker, "add", "-A")
        git(worker, "commit", "-q", "-m", "summary")
        git(worker, "push", "-q")
        out = self.status()
        self.assertIn("Worker summary in", out)
        self.assertIn("next: ask Brain to review batch 01-menus", out)
        self.deliver_review("verifier-mac", "01-menus")
        out = self.status()
        self.assertIn("Verifier review in", out)
        self.assertIn("next: ask Brain to judge batch 01-menus", out)

    def test_a_squash_merged_batch_is_not_listed(self) -> None:
        self.deliver_worker("worker", "02-done")
        self.assertIn("worker/02-done", self.status())
        self.squash_merge("worker/02-done")
        self.assertIn("nothing waiting", self.status())

    def test_a_branch_here_and_on_github_is_listed_once(self) -> None:
        self.deliver_worker("worker", "03-twice")
        git(self.brain, "fetch", "-q", "origin")
        git(self.brain, "switch", "-q", "worker/03-twice")
        git(self.brain, "switch", "-q", "main")
        self.assertEqual(self.status().count("worker/03-twice:"), 1)

    def test_a_release_3_round_is_named_as_one(self) -> None:
        git(self.brain, "switch", "-q", "-c", "worker/027-old")
        (self.brain / "docs/rounds/027-old").mkdir(parents=True)
        (self.brain / "docs/rounds/027-old/worker.md").write_text("## Verified\nNone.\n", encoding="utf-8")
        self.commit_all(self.brain, "old round report")
        git(self.brain, "push", "-q", "-u", "origin", "worker/027-old")
        git(self.brain, "switch", "-q", "main")
        out = self.status()
        self.assertIn("a release 3.x round", out)
        self.assertIn("next: ask Brain what to do with worker/027-old", out)


class LeavingAMachine(BatchTest):
    def test_leaving_with_unpushed_work_is_not_safe(self) -> None:
        git(self.brain, "switch", "-q", "-c", "brain/notes")
        (self.brain / "notes.txt").write_text("x\n", encoding="utf-8")
        git(self.brain, "add", "notes.txt")
        git(self.brain, "commit", "-q", "-m", "Notes")
        result = fw(self.brain, "status", "--offline", "--leaving")
        self.assertEqual(result.returncode, 1)
        self.assertIn("not on GitHub yet: brain/notes", result.stdout)
        git(self.brain, "push", "-q", "-u", "origin", "brain/notes")
        result = fw(self.brain, "status", "--offline", "--leaving")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_commits_on_a_detached_head_are_not_safe_to_leave(self) -> None:
        git(self.brain, "switch", "-q", "--detach")
        (self.brain / "z.txt").write_text("z\n", encoding="utf-8")
        git(self.brain, "add", "z.txt")
        git(self.brain, "commit", "-q", "-m", "Detached work")
        result = fw(self.brain, "status", "--offline", "--leaving")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("the detached HEAD", result.stdout)
