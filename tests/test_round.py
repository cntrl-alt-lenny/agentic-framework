"""A whole round, with every seat in a different clone.

Each clone stands for a different machine or a cloud tool's fresh workspace.
Nothing may pass between them except through the shared remote -- which is the
property the framework's continuity promise rests on.
"""

from __future__ import annotations

from tests.helpers import TempDirTest, fw, git

WORKER_REPORT = """## Verified
- feature works -- `python3 -c "print(1)"` -> exit 0
  1

## Not verified
None.

## Changed
- feature.txt: the feature.

## Open questions
None.
"""

VERIFIER_REPORT = """Reviewed commit: see stamp.

## Findings
None.

## Not verified
None.

## Verdict
The change does what the brief asks.
"""


class RoundAcrossMachines(TempDirTest):
    def setUp(self) -> None:
        super().setUp()
        self.origin = self.adopted_origin()
        self.brain = self.clone(self.origin, "brain-mac")

    def write_brief(self, round_id: str) -> None:
        git(self.brain, "switch", "-q", "-c", f"brain/{round_id}")
        folder = self.brain / "docs" / "rounds" / round_id
        folder.mkdir(parents=True)
        (folder / "brief.md").write_text(f"# {round_id}\n\nTier: 2\n", encoding="utf-8")
        git(self.brain, "add", "-A")
        git(self.brain, "commit", "-q", "-m", f"Brief {round_id}")
        git(self.brain, "push", "-q", "-u", "origin", f"brain/{round_id}")
        git(self.brain, "switch", "-q", "main")

    def deliver_worker(self, clone: str, round_id: str) -> tuple:
        worker = self.clone(self.origin, clone)
        result = fw(worker, "start", "--role", "worker", "--round", round_id)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        (worker / "feature.txt").write_text("feature\n", encoding="utf-8")
        git(worker, "add", "feature.txt")
        git(worker, "commit", "-q", "-m", "Add the feature")
        (worker / "docs" / "rounds" / round_id / "worker.md").write_text(WORKER_REPORT, encoding="utf-8")
        result = fw(worker, "report", "--role", "worker", "--round", round_id, "--push")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return worker, result

    def test_full_round_on_three_machines_with_squash_merge(self) -> None:
        self.write_brief("001-feature")
        worker, _ = self.deliver_worker("worker-windows", "001-feature")
        self.assertEqual(git(worker, "branch", "--show-current"), "worker/001-feature")

        verifier = self.clone(self.origin, "verifier-cloud")
        result = fw(verifier, "start", "--role", "verifier", "--round", "001-feature")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("do not open docs/rounds/001-feature/worker.md", result.stdout)
        self.assertEqual(git(verifier, "rev-parse", "HEAD"), git(worker, "rev-parse", "HEAD"))
        (verifier / "docs" / "rounds" / "001-feature" / "verifier.md").write_text(VERIFIER_REPORT, encoding="utf-8")
        result = fw(verifier, "report", "--role", "verifier", "--round", "001-feature", "--push")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        # Brain, on the first machine, sees both reports without anyone carrying text.
        result = fw(self.brain, "delivery", "--round", "001-feature")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("origin/verifier/001-feature", result.stdout)
        self.assertIn("worker: report describes", result.stdout)
        self.assertIn("verifier: report describes", result.stdout)

        # Squash-merge the complete round (the case that fooled 2.x's leave-check).
        git(self.brain, "merge", "-q", "--squash", "origin/verifier/001-feature")
        git(self.brain, "commit", "-q", "-m", "Round 001 (squashed)")
        git(self.brain, "push", "-q", "origin", "main")
        for branch in ("brain/001-feature", "worker/001-feature", "verifier/001-feature"):
            git(self.brain, "push", "-q", "origin", "--delete", branch)
        git(self.brain, "branch", "-q", "-D", "brain/001-feature")

        result = fw(self.brain, "status", "--offline", "--leaving")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("nothing in flight", result.stdout)
        self.assertIn("safe to leave this machine: yes", result.stdout)
        self.assertIn("latest by name: 001-feature", result.stdout)

    def test_tool_chosen_branch_name_is_accepted(self) -> None:
        self.write_brief("002-cloud")
        worker = self.clone(self.origin, "cloud")
        git(worker, "switch", "-q", "-c", "claude/some-session-name")
        result = fw(worker, "start", "--role", "worker", "--round", "002-cloud")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("chosen by your tool", result.stdout)
        self.assertTrue((worker / "docs" / "rounds" / "002-cloud" / "brief.md").is_file())

    def test_verifier_waits_for_delivery(self) -> None:
        self.write_brief("003-wait")
        verifier = self.clone(self.origin, "verifier")
        result = fw(verifier, "start", "--role", "verifier", "--round", "003-wait")
        self.assertEqual(result.returncode, 1)
        self.assertIn("not delivered yet", result.stdout)

    def test_work_after_the_report_makes_it_stale(self) -> None:
        self.write_brief("004-stale")
        worker, _ = self.deliver_worker("worker", "004-stale")
        (worker / "extra.txt").write_text("late change\n", encoding="utf-8")
        git(worker, "add", "extra.txt")
        git(worker, "commit", "-q", "-m", "Late change")
        git(worker, "push", "-q")
        result = fw(self.brain, "delivery", "--round", "004-stale")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("changed after the worker report (extra.txt)", result.stdout)

    def test_a_fresh_clone_continues_the_seats_own_pushed_work(self) -> None:
        self.write_brief("007-resume")
        first, _ = self.deliver_worker("worker-mac", "007-resume")
        second = self.clone(self.origin, "worker-cloud")
        result = fw(second, "start", "--role", "worker", "--round", "007-resume")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("continuing earlier work", result.stdout)
        self.assertEqual(git(second, "rev-parse", "HEAD"), git(first, "rev-parse", "HEAD"))
        self.assertTrue((second / "feature.txt").is_file())

    def test_a_tool_named_branch_starts_after_the_default_branch_moved(self) -> None:
        self.write_brief("008-moved")
        (self.brain / "housekeeping.txt").write_text("x\n", encoding="utf-8")
        git(self.brain, "add", "housekeeping.txt")
        git(self.brain, "commit", "-q", "-m", "Tier 0 housekeeping")
        git(self.brain, "push", "-q", "origin", "main")
        worker = self.clone(self.origin, "cloud")
        git(worker, "switch", "-q", "-c", "codex/session")
        result = fw(worker, "start", "--role", "worker", "--round", "008-moved")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((worker / "docs/rounds/008-moved/brief.md").is_file())

    def test_a_stale_report_can_be_rewritten_in_the_same_clone(self) -> None:
        self.write_brief("009-rewrite")
        worker, _ = self.deliver_worker("worker", "009-rewrite")
        (worker / "fix.txt").write_text("fix\n", encoding="utf-8")
        git(worker, "add", "fix.txt")
        git(worker, "commit", "-q", "-m", "Fix")
        path = worker / "docs/rounds/009-rewrite/worker.md"
        path.write_text(WORKER_REPORT.replace("- feature.txt", "- fix.txt: the fix.\n- feature.txt"), encoding="utf-8")
        result = fw(worker, "report", "--role", "worker", "--round", "009-rewrite", "--push")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(fw(self.brain, "delivery", "--round", "009-rewrite").returncode, 0)

    def test_a_changed_brief_makes_the_report_stale(self) -> None:
        self.write_brief("010-brief")
        worker, _ = self.deliver_worker("worker", "010-brief")
        with open(worker / "docs/rounds/010-brief/brief.md", "a", encoding="utf-8") as stream:
            stream.write("New acceptance criterion.\n")
        git(worker, "commit", "-q", "-am", "Edit the brief")
        git(worker, "push", "-q")
        result = fw(self.brain, "delivery", "--round", "010-brief")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("brief.md", result.stdout)

    def test_a_review_of_older_work_is_flagged_and_a_new_review_starts_beside_it(self) -> None:
        self.write_brief("011-again")
        worker, _ = self.deliver_worker("worker", "011-again")
        verifier = self.clone(self.origin, "verifier")
        fw(verifier, "start", "--role", "verifier", "--round", "011-again")
        (verifier / "docs/rounds/011-again/verifier.md").write_text(VERIFIER_REPORT, encoding="utf-8")
        self.assertEqual(fw(verifier, "report", "--role", "verifier", "--round", "011-again", "--push").returncode, 0)
        # The Worker changes the work and reports again.
        (worker / "fix.txt").write_text("fix\n", encoding="utf-8")
        git(worker, "add", "fix.txt")
        git(worker, "commit", "-q", "-m", "Fix")
        path = worker / "docs/rounds/011-again/worker.md"
        path.write_text(WORKER_REPORT, encoding="utf-8")
        self.assertEqual(fw(worker, "report", "--role", "worker", "--round", "011-again", "--push").returncode, 0)
        result = fw(self.brain, "delivery", "--round", "011-again")
        self.assertIn("this review is of an older commit", result.stdout)
        second = self.clone(self.origin, "verifier-2")
        result = fw(second, "start", "--role", "verifier", "--round", "011-again")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(git(second, "branch", "--show-current"), "verifier/011-again-2")
        self.assertEqual(git(second, "rev-parse", "HEAD"), git(worker, "rev-parse", "HEAD"))

    def test_report_rules(self) -> None:
        self.write_brief("005-rules")
        worker = self.clone(self.origin, "worker")
        fw(worker, "start", "--role", "worker", "--round", "005-rules")
        path = worker / "docs" / "rounds" / "005-rules" / "worker.md"

        result = fw(worker, "report", "--role", "worker", "--round", "005-rules")
        self.assertEqual(result.returncode, 2)
        self.assertIn("write your report to", result.stderr)

        path.write_text("## Verified\n- something\n", encoding="utf-8")
        result = fw(worker, "report", "--role", "worker", "--round", "005-rules")
        self.assertEqual(result.returncode, 2)
        self.assertIn("## Not verified", result.stderr)

        path.write_text(WORKER_REPORT, encoding="utf-8")
        (worker / "uncommitted.txt").write_text("x\n", encoding="utf-8")
        result = fw(worker, "report", "--role", "worker", "--round", "005-rules")
        self.assertEqual(result.returncode, 2)
        self.assertIn("uncommitted.txt", result.stderr)
        (worker / "uncommitted.txt").unlink()

        result = fw(worker, "report", "--role", "worker", "--round", "005-rules")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("not pushed yet", result.stdout)
        header = path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(header[0], "<!-- fw-report")
        self.assertIn("role: worker", header)

    def test_report_is_refused_on_the_default_branch(self) -> None:
        folder = self.brain / "docs" / "rounds" / "006-main"
        folder.mkdir(parents=True)
        (folder / "worker.md").write_text(WORKER_REPORT, encoding="utf-8")
        result = fw(self.brain, "report", "--role", "worker", "--round", "006-main")
        self.assertEqual(result.returncode, 2)
        self.assertIn("never on the default branch", result.stderr)

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

    def test_bad_names_are_refused(self) -> None:
        for args in (("--role", "Worker", "--round", "001"), ("--role", "con", "--round", "001"),
                     ("--role", "worker", "--round", "../escape")):
            result = fw(self.brain, "start", *args)
            self.assertEqual(result.returncode, 2, args)
