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
        self.squash_merge("worker/02-done", delete=False)
        self.assertIn("nothing waiting", self.status())

    def test_a_merged_branch_left_behind_is_not_shown_as_working(self) -> None:
        # Review of 4.0: once main changes the same file, content no longer matches.
        self.deliver_worker("worker", "12-sq")
        self.squash_merge("worker/12-sq", delete=False)
        (self.brain / "feature.txt").write_text("changed later on main\n", encoding="utf-8")
        self.commit_all(self.brain, "later change")
        git(self.brain, "push", "-q", "origin", "main")
        out = self.status()
        self.assertIn("worker/12-sq: merged earlier", out)
        self.assertIn("next: nothing is waiting on you", out)

    def test_a_cloud_named_branch_is_read_by_its_files(self) -> None:
        # Review of 4.0: cloud tools pick their own branch names.
        self.deliver_worker("cloud", "07-menus", branch="claude/project-thread-abc")
        out = self.status()
        self.assertIn("claude/project-thread-abc: 2 commit(s)", out)
        self.assertIn("batch 07-menus: Worker summary in", out)
        self.assertIn("next: ask Brain to review batch 07-menus", out)

    def test_a_branch_editing_an_existing_batch_file_is_not_called_merged(self) -> None:
        # Re-review of 4.0: an edit to a merged summary is new, unmerged work.
        self.deliver_worker("worker", "05-old")
        self.squash_merge("worker/05-old")
        fixer = self.clone(self.origin, "fixer")
        git(fixer, "switch", "-q", "-c", "brain/fix-05")
        (fixer / "docs/batches/05-old.md").write_text("# Corrected summary\n", encoding="utf-8")
        self.commit_all(fixer, "Correct the summary")
        git(fixer, "push", "-q", "-u", "origin", "brain/fix-05")
        out = self.status()
        self.assertNotIn("merged earlier", out)
        self.assertIn("next: ask Brain to review batch 05-old", out)

    def test_a_verifier_on_its_own_branch_is_found(self) -> None:
        self.deliver_worker("worker", "08-split")
        verifier = self.clone(self.origin, "verifier")
        git(verifier, "switch", "-q", "-c", "claude/verify-xyz", "origin/worker/08-split")
        (verifier / "docs/batches/08-split-review.md").write_text("# Review\n", encoding="utf-8")
        self.commit_all(verifier, "Review")
        git(verifier, "push", "-q", "-u", "origin", "claude/verify-xyz")
        self.assertIn("claude/verify-xyz: 3 commit(s)", self.status())
        self.assertIn("batch 08-split: Verifier review in", self.status())

    def test_fixes_after_a_review_are_not_shown_as_judged(self) -> None:
        self.deliver_worker("worker", "09-fix")
        self.deliver_review("verifier", "09-fix")
        fixer = self.clone(self.origin, "fixer")
        git(fixer, "switch", "-q", "worker/09-fix")
        (fixer / "feature.txt").write_text("fixed\n", encoding="utf-8")
        self.commit_all(fixer, "Fix the finding")
        git(fixer, "push", "-q")
        out = self.status()
        self.assertIn("batch 09-fix: 1 commit(s) after the Verifier's review", out)
        self.assertIn("next: ask Brain to check the fixes in batch 09-fix", out)

    def test_brains_own_branch_waits_for_the_owner(self) -> None:
        # Review of 4.0: a Small-path branch must never read as "nothing waiting".
        git(self.brain, "switch", "-q", "-c", "brain/state-notes")
        (self.brain / "docs/state.md").write_text("# State\n\nA decision.\n", encoding="utf-8")
        self.commit_all(self.brain, "state")
        git(self.brain, "push", "-q", "-u", "origin", "brain/state-notes")
        git(self.brain, "switch", "-q", "main")
        self.assertIn("next: ask Brain whether brain/state-notes is ready for your yes", self.status())

    def test_work_in_progress_is_not_called_nothing(self) -> None:
        self.deliver_worker("worker", "10-wip", summary=False)
        self.assertIn("next: nothing needs you yet: 1 branch(es) still being worked on", self.status())

    def test_this_machines_copy_ahead_of_a_merged_github_copy_is_listed(self) -> None:
        worker = self.deliver_worker("worker", "11-ahead")
        self.squash_merge("worker/11-ahead", delete=False)
        (worker / "more.txt").write_text("more\n", encoding="utf-8")
        self.commit_all(worker, "More, never pushed")
        git(worker, "fetch", "-q", "origin")
        result = fw(worker, "status", "--offline")
        self.assertIn("worker/11-ahead (this machine's copy): 3 commit(s)", result.stdout)
        self.assertIn("its batch was merged, but 1 later commit(s) are not", result.stdout)

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
