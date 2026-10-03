"""Execute canonical dispatches in disposable clones; no real adopter access."""
from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path

from tests.helpers import (ROOT, VERIFIER_REPORT, WORKER_REPORT, RoundTest,
                           TempDirTest, fw, git, run)


def evidence(case, label, command, result):
    destination = os.environ.get("FW_EVIDENCE_LOG")
    if destination:
        text = f"{label}\n$ {' '.join(command)}\nexit {result.returncode}\n{result.stdout}{result.stderr}\n"
        for source, replacement in ((str(case.tmp), "<fixture>"), (str(ROOT), "<framework>"),
                                    (sys.executable, "python3")):
            text = text.replace(source, replacement)
        with open(destination, "a", encoding="utf-8") as stream:
            stream.write(text)


def dispatch_start(case, repo, prompt):
    """Execute the actual local startup instructions, including the old template."""
    old = re.search(r"run (git worktree add --detach (\S+) \S+)", prompt)
    if old:
        args = old.group(1).split()
        result = run(args, repo, check=False)
        evidence(case, "generated worktree command", args, result)
        if result.returncode:
            return result, repo / old.group(2)
        target = repo / old.group(2)
    else:
        target = repo
    match = re.search(r"python3 (\S+) start --role (\S+) --round (\S+)(?: --worktree (\S+))?", prompt)
    case.assertIsNotNone(match, prompt)
    tool, role, round_id, folder = match.groups()
    args = [sys.executable, tool, "start", "--role", role, "--round", round_id]
    if folder:
        args += ["--worktree", folder]
    result = run(args, target, check=False)
    evidence(case, "generated startup command", args, result)
    return result, repo / folder if folder else target


class HandoffRound(RoundTest):
    def adopted_origin(self):
        origin = super().adopted_origin()
        baseline = os.environ.get("FW_TEST_BASELINE")
        if baseline:
            seed = self.tmp / "seed"
            (seed / "tools/fw.py").write_text(Path(baseline).read_text(), encoding="utf-8")
            self.commit_all(seed, "Use baseline tool")
            git(seed, "push", "-q", str(origin), "main")
        return origin

    def prompt(self, round_id, role="worker", repo=None):
        repo = repo or self.brain
        result = fw(repo, "prompt", "--round", round_id, "--role", role)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        evidence(self, "generated prompt", ["python3", "tools/fw.py", "prompt", "--round", round_id,
                                           "--role", role], result)
        return result.stdout


class SeatResumption(HandoffRound):
    def test_generated_startup_twice_resumes_unpushed_work(self):
        self.write_brief("120-resume")
        prompt = self.prompt("120-resume")
        first, seat = dispatch_start(self, self.brain, prompt)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        (seat / "local.txt").write_text("unpublished work\n", encoding="utf-8")
        self.commit_all(seat, "Unpushed seat work")
        head = git(seat, "rev-parse", "HEAD")
        again, _ = dispatch_start(self, self.brain, prompt)
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)
        self.assertEqual(git(seat, "rev-parse", "HEAD"), head)

    def test_dirty_matching_checkout_is_preserved(self):
        self.write_brief("121-dirty")
        prompt = self.prompt("121-dirty")
        first, seat = dispatch_start(self, self.brain, prompt)
        self.assertEqual(first.returncode, 0, first.stderr)
        head = git(seat, "rev-parse", "HEAD")
        (seat / "dirty.txt").write_text("keep this\n", encoding="utf-8")
        again, _ = dispatch_start(self, self.brain, prompt)
        self.assertEqual(again.returncode, 2, again.stderr)
        self.assertIn("uncommitted changes", again.stderr)
        self.assertEqual((seat / "dirty.txt").read_text(), "keep this\n")
        self.assertEqual(git(seat, "rev-parse", "HEAD"), head)

    def test_foreign_repository_and_wrong_seat_or_round_are_not_reused(self):
        self.write_brief("122-safety")
        prompt = self.prompt("122-safety")
        folder = self.brain / ".worktrees/worker-122"
        foreign = self.init_repo(folder)
        (foreign / "keep.txt").write_text("foreign\n", encoding="utf-8")
        self.commit_all(foreign, "Foreign work")
        head = git(foreign, "rev-parse", "HEAD")
        result, _ = dispatch_start(self, self.brain, prompt)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(git(foreign, "rev-parse", "HEAD"), head)
        # Move our disposable foreign fixture aside; startup never moves it.
        folder.rename(self.tmp / "foreign-kept")
        for branch in ("verifier/122-safety", "worker/999-other"):
            git(self.brain, "worktree", "add", "-q", "-b", branch, str(folder), "origin/brain/122-safety")
            result, _ = dispatch_start(self, self.brain, prompt)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("was not touched", result.stderr)
            self.assertEqual(git(folder, "branch", "--show-current"), branch)
            git(self.brain, "worktree", "remove", str(folder))

    def test_interrupted_creation_of_matching_branch_resumes(self):
        self.write_brief("123-interrupted")
        prompt = self.prompt("123-interrupted")
        git(self.brain, "worktree", "add", "-q", "-b", "worker/123-interrupted",
            ".worktrees/worker-123", "origin/brain/123-interrupted")
        result, _ = dispatch_start(self, self.brain, prompt)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("resuming", result.stdout)

    def test_prompt_fetches_review_history_and_repeat_resumes_same_review(self):
        self.write_brief("124-review")
        worker, _ = self.deliver_worker("worker", "124-review")
        observer = self.clone(self.origin, "observer")
        self.deliver_verifier("verifier", "124-review")
        (worker / "fix.txt").write_text("fix\n", encoding="utf-8")
        self.commit_all(worker, "Fix after review")
        (worker / "docs/rounds/124-review/worker.md").write_text(WORKER_REPORT, encoding="utf-8")
        self.assertEqual(fw(worker, "report", "--role", "worker", "--round", "124-review", "--push").returncode, 0)
        self.assertNotIn("origin/verifier/124-review", git(observer, "branch", "-r"))
        prompt = self.prompt("124-review", "verifier", observer)
        self.assertIn(".worktrees/verifier-124-2", prompt)
        first, seat = dispatch_start(self, observer, prompt)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.assertEqual(git(seat, "rev-parse", "HEAD"), git(worker, "rev-parse", "HEAD"))
        again, _ = dispatch_start(self, observer, prompt)
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)

    def test_offline_prompt_discloses_history_and_startup_refuses_unreachable_origin(self):
        self.write_brief("125-offline")
        git(self.brain, "remote", "set-url", "origin", str(self.tmp / "unreachable"))
        result = fw(self.brain, "prompt", "--round", "125-offline", "--role", "worker", "--offline")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Remote history was not checked", result.stdout)
        startup, seat = dispatch_start(self, self.brain, result.stdout)
        self.assertEqual(startup.returncode, 2, startup.stderr)
        self.assertIn("without remote history", startup.stderr)
        self.assertFalse(seat.exists())


class SuccessorDelivery(HandoffRound):
    def test_successor_brief_does_not_invalidate_original_delivery(self):
        self.write_brief("110-audit")
        self.deliver_worker("worker", "110-audit")
        verifier = self.deliver_verifier("verifier", "110-audit")
        before = fw(self.brain, "status")
        evidence(self, "before successor status", ["python3", "tools/fw.py", "status"], before)
        self.assertIn("worker: reported at", before.stdout)
        self.assertIn("verifier: reported at", before.stdout)
        self.write_brief("111-followup", start="origin/verifier/110-audit")
        # Different names and sibling ordering; neither is a magic brain branch.
        git(self.brain, "switch", "-q", "-c", "z-inherited", "origin/verifier/110-audit")
        folder = self.brain / "docs/rounds/112-sibling"
        folder.mkdir()
        (folder / "brief.md").write_text("Tier: 1\nMode: implementation\n", encoding="utf-8")
        (folder / "notes.md").write_text("Successor records\n", encoding="utf-8")
        self.commit_all(self.brain, "Sibling successor")
        git(self.brain, "push", "-q", "origin", "z-inherited")
        after = fw(self.brain, "status")
        evidence(self, "after successor status", ["python3", "tools/fw.py", "status"], after)
        automatic = fw(self.brain, "delivery", "--round", "110-audit")
        evidence(self, "automatic original delivery", ["python3", "tools/fw.py", "delivery", "--round", "110-audit"], automatic)
        named = fw(self.brain, "delivery", "--round", "110-audit", "--branch", "origin/verifier/110-audit")
        evidence(self, "named unchanged delivery", ["python3", "tools/fw.py", "delivery", "--round", "110-audit",
                                                   "--branch", "origin/verifier/110-audit"], named)
        self.assertNotIn("worker: stale", after.stdout)
        self.assertNotIn("verifier: stale", after.stdout)
        self.assertIn("in flight: 111-followup", after.stdout)
        self.assertIn("in flight: 112-sibling", after.stdout)
        self.assertEqual(automatic.returncode, 0, automatic.stdout)
        self.assertIn(git(verifier, "rev-parse", "HEAD")[:12], automatic.stdout)
        self.assertEqual(named.returncode, 0, named.stdout)

    def test_later_work_outside_new_round_folders_is_still_stale(self):
        self.write_brief("113-strict")
        self.deliver_worker("worker", "113-strict")
        self.deliver_verifier("verifier", "113-strict")
        self.write_brief("114-next", start="origin/verifier/113-strict")
        git(self.brain, "switch", "-q", "brain/114-next")
        (self.brain / "README.md").write_text("Changed production-facing guidance\n", encoding="utf-8")
        self.commit_all(self.brain, "Extra work after review")
        git(self.brain, "push", "-q")
        result = fw(self.brain, "delivery", "--round", "113-strict")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("changed after", result.stdout)


class FirstAdoption(TempDirTest):
    def setUp(self):
        super().setUp()
        self.source = self.init_repo(self.tmp / "framework")
        for name in ("framework", "tools", "templates", "adapters"):
            shutil.copytree(ROOT / name, self.source / name, ignore=shutil.ignore_patterns("__pycache__"))
        for name in ("VERSION", "CHANGELOG.md", ".gitignore"):
            shutil.copyfile(ROOT / name, self.source / name)
        baseline = os.environ.get("FW_TEST_BASELINE")
        if baseline:
            shutil.copyfile(baseline, self.source / "tools/fw.py")
        self.commit_all(self.source, "Pinned framework fixture")
        self.pin = git(self.source, "rev-parse", "HEAD")
        self.project = self.init_repo(self.tmp / "seed")
        (self.project / "README.md").write_text("# Demo\n", encoding="utf-8")
        self.commit_all(self.project, "Unadopted project")
        self.origin = self.tmp / "Demo.git"
        git(self.tmp, "clone", "-q", "--bare", str(self.project), str(self.origin))
        self.brain = self.clone(self.origin, "brain")

    def external(self, repo, *args):
        command = [sys.executable, str(self.source / "tools/fw.py"), "--cwd", str(repo), *args]
        result = run(command, repo, check=False)
        evidence(self, "external framework command", command, result)
        return result

    def adoption_brief(self, mode="adoption", pin=None, source=None):
        git(self.brain, "switch", "-q", "-c", "brain/130-adopt")
        folder = self.brain / "docs/rounds/130-adopt"
        folder.mkdir(parents=True)
        (folder / "brief.md").write_text(
            f"# 130-adopt\nTier: 2\nMode: {mode}\nSupersedes: none\n"
            f"Framework-source: {source or self.source}\nFramework-commit: {pin or self.pin}\n"
            "Install the pinned framework and adapt AGENTS.md.\n", encoding="utf-8")
        self.commit_all(self.brain, "First-adoption brief only")
        git(self.brain, "push", "-q", "-u", "origin", "brain/130-adopt")
        git(self.brain, "switch", "-q", "main")

    def bootstrap_from_prompt(self, repo, prompt):
        # Execute the actual clone and pinned checkout commands, not an API stand-in.
        match = re.search(r"run (git clone --no-checkout \S+ \S+), then (git -C \S+ checkout --detach [0-9a-f]{40})", prompt)
        self.assertIsNotNone(match, prompt)
        for command in match.groups():
            args = command.split()
            result = run(args, repo, check=False)
            evidence(self, "generated bootstrap instruction", args, result)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_external_status_routes_first_adoption_without_green_checks(self):
        result = self.external(self.brain, "status", "--offline")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("all project checks pass", result.stdout)
        self.assertIn("next: ask Brain to prepare a first-adoption round", result.stdout)
        self.assertIn("configuration is not verified", result.stdout)
        self.assertIn("Command form before adoption", result.stdout)

    def test_complete_pinned_adoption_across_separate_clones(self):
        self.adoption_brief()
        worker_prompt = self.external(self.brain, "prompt", "--round", "130-adopt", "--role", "worker")
        self.assertEqual(worker_prompt.returncode, 0, worker_prompt.stderr)
        # Brain still has neither installed code nor project rules.
        self.assertFalse((self.brain / "tools/fw.py").exists())
        worker_main = self.clone(self.origin, "worker")
        self.bootstrap_from_prompt(worker_main, worker_prompt.stdout)
        first, worker = dispatch_start(self, worker_main, worker_prompt.stdout)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        again, _ = dispatch_start(self, worker_main, worker_prompt.stdout)
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)
        checkout = worker_main / f".worktrees/framework-{self.pin[:12]}"
        result = run([sys.executable, str(checkout / "tools/adopt.py"), str(worker),
                      "--project", "Demo", "--verifier"], worker, check=False)
        evidence(self, "Worker adopts from exact pinned source", ["python3", "<pinned-source>/tools/adopt.py", "<seat>",
                                                                 "--project", "Demo", "--verifier"], result)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.commit_all(worker, "Adopt pinned framework")
        (worker / "docs/rounds/130-adopt/worker.md").write_text(WORKER_REPORT, encoding="utf-8")
        result = fw(worker, "report", "--role", "worker", "--round", "130-adopt", "--push")
        evidence(self, "normal installed Worker report", ["python3", "tools/fw.py", "report", "--role", "worker",
                                                        "--round", "130-adopt", "--push"], result)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        handoff = self.external(self.brain, "status")
        self.assertIn("next: send the Verifier prompt", handoff.stdout)
        self.assertIn("first adoption: use the pinned external framework tool", handoff.stdout)
        verifier_prompt = self.external(self.brain, "prompt", "--round", "130-adopt", "--role", "verifier")
        self.assertEqual(verifier_prompt.returncode, 0, verifier_prompt.stderr)
        verifier_main = self.clone(self.origin, "verifier")
        self.bootstrap_from_prompt(verifier_main, verifier_prompt.stdout)
        started, verifier = dispatch_start(self, verifier_main, verifier_prompt.stdout)
        self.assertEqual(started.returncode, 0, started.stdout + started.stderr)
        self.assertIn("do not open", started.stdout)
        self.assertEqual(git(verifier, "rev-parse", "HEAD"), git(worker, "rev-parse", "HEAD"))
        (verifier / "docs/rounds/130-adopt/verifier.md").write_text(VERIFIER_REPORT, encoding="utf-8")
        result = fw(verifier, "report", "--role", "verifier", "--round", "130-adopt", "--push")
        evidence(self, "normal installed Verifier report", ["python3", "tools/fw.py", "report", "--role", "verifier",
                                                          "--round", "130-adopt", "--push"], result)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        result = self.external(self.brain, "delivery", "--round", "130-adopt")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("verifier: report describes", result.stdout)
        git(self.brain, "merge", "--ff-only", "origin/verifier/130-adopt")
        git(self.brain, "push", "-q", "origin", "main")
        status = fw(self.brain, "status", "--offline")
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertIn("all project checks pass", status.stdout)
        normal = fw(self.brain, "prompt", "--round", "130-adopt", "--role", "worker")
        self.assertEqual(normal.returncode, 0, normal.stderr)
        self.assertIn("run python3 tools/fw.py start", normal.stdout)
        self.assertNotIn("git clone --no-checkout", normal.stdout)
        evidence(self, "adoption becomes normal installed routing", ["python3", "tools/fw.py", "prompt",
                                                                    "--round", "130-adopt", "--role", "worker"], normal)

    def test_cloud_bootstrap_preserves_private_source_and_reports_early_stop(self):
        self.adoption_brief()
        prompt = self.external(self.brain, "prompt", "--round", "130-adopt", "--role", "worker")
        self.assertEqual(prompt.returncode, 0, prompt.stderr)
        cloud = self.clone(self.origin, "cloud")
        self.bootstrap_from_prompt(cloud, prompt.stdout)
        command = re.search(r"python3 (\S+) start --role worker --round 130-adopt", prompt.stdout).group(1)
        args = [sys.executable, command, "start", "--role", "worker", "--round", "130-adopt"]
        result = run(args, cloud, check=False)
        evidence(self, "generated cloud startup without worktree", args, result)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(git(cloud, "branch", "--show-current"), "worker/130-adopt")
        (cloud / "docs/rounds/130-adopt/worker.md").write_text(WORKER_REPORT, encoding="utf-8")
        result = run([sys.executable, command, "--cwd", ".", "report", "--role", "worker",
                      "--round", "130-adopt", "--push"], cloud, check=False)
        evidence(self, "external report after early adoption stop", ["python3", command, "--cwd", ".", "report",
                                                                   "--role", "worker", "--round", "130-adopt", "--push"], result)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((cloud / "tools/fw.py").exists())

    def test_pinned_source_remains_usable_after_remote_tip_moves(self):
        remote = self.tmp / "framework.git"
        git(self.tmp, "clone", "-q", "--bare", str(self.source), str(remote))
        publisher = self.clone(remote, "publisher")
        (publisher / "later.txt").write_text("later source work\n", encoding="utf-8")
        self.commit_all(publisher, "Advance source branch")
        git(publisher, "push", "-q")
        self.adoption_brief(source=remote)
        result = self.external(self.brain, "prompt", "--round", "130-adopt", "--role", "worker")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(self.pin, result.stdout)
        self.bootstrap_from_prompt(self.brain, result.stdout)
        startup, _ = dispatch_start(self, self.brain, result.stdout)
        self.assertEqual(startup.returncode, 0, startup.stdout + startup.stderr)

    def test_missing_pin_wrong_pin_and_product_mode_do_not_bootstrap(self):
        self.adoption_brief(mode="implementation")
        result = self.external(self.brain, "prompt", "--round", "130-adopt", "--role", "worker")
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("dedicated Mode: adoption", result.stderr)
        offline = self.external(self.brain, "prompt", "--round", "130-adopt", "--role", "worker", "--offline")
        self.assertEqual(offline.returncode, 2, offline.stdout)
        self.assertIn("offline first-adoption dispatch cannot verify", offline.stderr)
        git(self.brain, "switch", "-q", "brain/130-adopt")
        brief = self.brain / "docs/rounds/130-adopt/brief.md"
        brief.write_text(brief.read_text().replace("Mode: implementation", "Mode: adoption").replace(self.pin, "0" * 40))
        self.commit_all(self.brain, "Unverified pin")
        git(self.brain, "push", "-q")
        result = self.external(self.brain, "prompt", "--round", "130-adopt", "--role", "worker")
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("does not contain Framework-commit", result.stderr)

    def test_damaged_and_ambiguous_installations_are_diagnosed(self):
        (self.brain / "docs/agents").mkdir(parents=True)
        (self.brain / "docs/agents/FRAMEWORK.md").write_text("Partial installation\n", encoding="utf-8")
        result = self.external(self.brain, "status", "--offline")
        self.assertIn("ambiguous framework installation", result.stdout)
        self.assertNotIn("all project checks pass", result.stdout)
        (self.brain / "docs/agents/framework.json").write_text('{"files": null}\n', encoding="utf-8")
        malformed = self.external(self.brain, "status", "--offline")
        self.assertEqual(malformed.returncode, 0, malformed.stderr)
        self.assertIn("damaged framework installation", malformed.stdout)
        self.assertNotIn("all project checks pass", malformed.stdout)
        (self.brain / "docs/agents/framework.json").write_text('{"files": {}}\n', encoding="utf-8")
        self.commit_all(self.brain, "Installation evidence")
        (self.brain / "docs/agents/framework.json").unlink()
        shutil.rmtree(self.brain / "docs/agents")
        result = self.external(self.brain, "status", "--offline")
        self.assertIn("damaged framework installation", result.stdout)
        self.assertNotIn("all project checks pass", result.stdout)
