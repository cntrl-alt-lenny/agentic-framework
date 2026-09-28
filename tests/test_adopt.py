"""Adoption and updates, including migrating a 2.x project that was never touched since."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

from tests.helpers import PYTHON, ROOT, WORKER_REPORT, RoundTest, TempDirTest, adopt, fw, git, run

FIXTURE = ROOT / "tests" / "fixtures" / "v2_adopter"


def manifest(target: Path) -> dict:
    return json.loads((target / "docs/agents/framework.json").read_text(encoding="utf-8"))


class FreshAdoption(TempDirTest):
    def test_adopt_installs_a_working_project(self) -> None:
        target = self.init_repo(self.tmp / "project")
        result = adopt(target, "--project", "Demo", "--workers", "builder", "--verifier",
                       "--adapter", "claude-code", "--adapter", "gemini", "--hooks")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for rel in ("AGENTS.md", "CLAUDE.md", "GEMINI.md", "docs/agents/FRAMEWORK.md",
                    "docs/agents/roles/brain.md", "docs/agents/roles/worker.md",
                    "docs/agents/roles/verifier.md", "tools/fw.py", "tests/test_framework.py",
                    "docs/state.md", "docs/rounds/README.md", ".claude/agents/worker.md",
                    ".githooks/pre-push", ".gitattributes"):
            self.assertTrue((target / rel).is_file(), rel)
        agents = (target / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("# Demo", agents)
        self.assertIn("| Builder |", agents)
        self.assertIn("Merge rule: owner-approves", agents)
        record = manifest(target)
        self.assertEqual(record["framework"]["release"], (ROOT / "VERSION").read_text().strip())
        self.assertEqual(record["options"], {"adapters": ["claude-code", "gemini"], "hooks": True})
        self.assertEqual(record["files"]["AGENTS.md"], {"kind": "seed"})
        self.assertEqual(
            record["files"]["tools/fw.py"]["sha256"],
            hashlib.sha256((target / "tools/fw.py").read_bytes()).hexdigest(),
        )
        # The installed checks pass on a freshly adopted project, run the way a project runs them.
        result = run([PYTHON, "-m", "unittest", "discover", "-s", "tests", "-t", "."], target, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(fw(target, "check").returncode, 0)
        # The hook's executable bit is recorded in git, so it survives Windows.
        self.assertTrue(git(target, "ls-files", "-s", ".githooks/pre-push").startswith("100755"))

    def test_existing_files_are_never_overwritten(self) -> None:
        target = self.init_repo(self.tmp / "project")
        (target / "AGENTS.md").write_text("# Mine\n", encoding="utf-8")
        result = adopt(target, "--project", "Demo")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((target / "AGENTS.md").read_text(encoding="utf-8"), "# Mine\n")
        self.assertTrue((target / "AGENTS.md.framework").is_file())

    def test_adopting_twice_asks_for_update(self) -> None:
        target = self.init_repo(self.tmp / "project")
        adopt(target, "--project", "Demo")
        result = adopt(target, "--project", "Demo")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("use --update", result.stderr)


class Updates(TempDirTest):
    def adopted(self) -> Path:
        target = self.init_repo(self.tmp / "project")
        self.assertEqual(adopt(target, "--project", "Demo", "--adapter", "claude-code").returncode, 0)
        self.commit_all(target, "adopt")
        return target

    def test_update_with_nothing_changed_writes_nothing(self) -> None:
        target = self.adopted()
        result = adopt(target, "--update")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("replace", result.stdout)
        self.assertNotIn("create", result.stdout)
        self.assertEqual(git(target, "status", "--porcelain"), "")

    def test_unedited_copies_are_replaced_and_edited_ones_kept(self) -> None:
        target = self.adopted()
        record = manifest(target)
        # Pretend the project was adopted from an older release of two files.
        for rel in ("docs/agents/roles/worker.md", "docs/agents/roles/brain.md"):
            (target / rel).write_text("old release text\n", encoding="utf-8")
            record["files"][rel]["sha256"] = hashlib.sha256(b"old release text\n").hexdigest()
        # ...and someone then edited one of them by hand.
        (target / "docs/agents/roles/brain.md").write_text("old release text\nlocal edit\n", encoding="utf-8")
        (target / "docs/agents/framework.json").write_text(json.dumps(record), encoding="utf-8")
        (target / "AGENTS.md").write_text("# Project rules the update must not touch\n", encoding="utf-8")

        result = adopt(target, "--update")
        self.assertEqual(result.returncode, 0, result.stderr)
        fresh = (ROOT / "framework/roles/worker.md").read_text(encoding="utf-8")
        self.assertEqual((target / "docs/agents/roles/worker.md").read_text(encoding="utf-8"), fresh)
        self.assertIn("local edit", (target / "docs/agents/roles/brain.md").read_text(encoding="utf-8"))
        self.assertTrue((target / "docs/agents/roles/brain.md.framework").is_file())
        self.assertEqual((target / "AGENTS.md").read_text(encoding="utf-8"),
                         "# Project rules the update must not touch\n")

    def test_crlf_checkout_of_an_unedited_file_counts_as_unedited(self) -> None:
        target = self.adopted()
        record = manifest(target)
        record["files"]["docs/agents/roles/worker.md"]["sha256"] = hashlib.sha256(b"a\nb\n").hexdigest()
        (target / "docs/agents/roles/worker.md").write_bytes(b"a\r\nb\r\n")
        (target / "docs/agents/framework.json").write_text(json.dumps(record), encoding="utf-8")
        result = adopt(target, "--update")
        self.assertIn("replace docs/agents/roles/worker.md", result.stdout)

    def test_files_a_release_drops_are_removed_only_when_provably_unedited(self) -> None:
        target = self.adopted()
        record = manifest(target)
        for rel, text in (("docs/agents/old-a.md", "a\n"), ("docs/agents/old-b.md", "b\n"),
                          ("docs/agents/old-c.md", "c\n")):
            (target / rel).write_text(text, encoding="utf-8")
            record["files"][rel] = {"kind": "copy", "sha256": hashlib.sha256(text.encode()).hexdigest()}
        (target / "docs/agents/old-b.md").write_text("b, edited\n", encoding="utf-8")
        (target / "build.json").write_text('{"doc": "docs/agents/old-c.md"}\n', encoding="utf-8")
        (target / "docs/agents/framework.json").write_text(json.dumps(record), encoding="utf-8")
        self.commit_all(target, "state before update")

        result = adopt(target, "--update")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((target / "docs/agents/old-a.md").exists())
        self.assertTrue((target / "docs/agents/old-b.md").exists())
        self.assertTrue((target / "docs/agents/old-c.md").exists())
        self.assertIn("build.json still refers to it", result.stdout)

    def test_a_kept_document_keeps_the_documents_it_links_to(self) -> None:
        target = self.adopted()
        record = manifest(target)
        docs = {"docs/agents/old-d.md": "See [e](old-e.md).\n", "docs/agents/old-e.md": "e\n"}
        for rel, text in docs.items():
            (target / rel).write_text(text, encoding="utf-8")
            record["files"][rel] = {"kind": "copy", "sha256": hashlib.sha256(text.encode()).hexdigest()}
        (target / "tool.py").write_text('DOC = "docs/agents/old-d.md"\n', encoding="utf-8")
        (target / "docs/agents/framework.json").write_text(json.dumps(record), encoding="utf-8")
        self.commit_all(target, "state before update")
        result = adopt(target, "--update")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((target / "docs/agents/old-e.md").exists(), result.stdout)
        self.assertIn("old-d.md, which is kept, links to it", result.stdout)

    def test_adding_an_adapter_keeps_the_ones_already_installed(self) -> None:
        target = self.adopted()
        result = adopt(target, "--update", "--adapter", "gemini")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("remove", result.stdout)
        self.assertTrue((target / ".claude/agents/brain.md").exists())
        self.assertTrue((target / "GEMINI.md").exists())
        self.assertEqual(manifest(target)["options"]["adapters"], ["claude-code", "gemini"])

    def test_dry_run_writes_nothing(self) -> None:
        target = self.adopted()
        (target / "docs/agents/roles/worker.md").unlink()
        result = adopt(target, "--update", "--dry-run")
        self.assertIn("create  docs/agents/roles/worker.md", result.stdout)
        self.assertFalse((target / "docs/agents/roles/worker.md").exists())


class LegacyMigration(TempDirTest):
    """A project last touched under release 2.x, opened again after 3.0.0 shipped."""

    def setUp(self) -> None:
        super().setUp()
        self.target = self.tmp / "dormant"
        shutil.copytree(FIXTURE, self.target)
        self.init_repo(self.target)
        self.commit_all(self.target, "2.x project")

    def test_status_in_a_dormant_2x_project_says_it_must_migrate(self) -> None:
        # A 2.x project has no fw.py; the new one, run against it, explains.
        result = run([PYTHON, str(ROOT / "tools/fw.py"), "--cwd", str(self.target), "status", "--offline"],
                     ROOT, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("predates release 3.0.0", result.stdout)

    def test_migration_keeps_everything_owned_or_edited(self) -> None:
        result = adopt(self.target, "--update")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        t = self.target
        # new release installed
        for rel in ("docs/agents/FRAMEWORK.md", "tools/fw.py", "tests/test_framework.py",
                    "docs/agents/framework.json", ".claude/agents/verifier.md"):
            self.assertTrue((t / rel).is_file(), rel)
        # unedited 2.x copies replaced or removed
        self.assertEqual((t / "docs/agents/roles/brain.md").read_text(encoding="utf-8"),
                         (ROOT / "framework/roles/brain.md").read_text(encoding="utf-8"))
        self.assertEqual((t / ".claude/agents/worker.md").read_text(encoding="utf-8"),
                         (ROOT / "adapters/claude-code/files/.claude/agents/worker.md").read_text(encoding="utf-8"))
        for rel in ("docs/agents/CONSTITUTION.md", "docs/agents/kickoff.md", "tools/textblocks.py",
                    "tests/test_role_neutrality.py"):
            self.assertFalse((t / rel).exists(), rel)
        # edited copies kept, with the new version beside them
        self.assertIn("Project note", (t / "docs/agents/roles/worker.md").read_text(encoding="utf-8"))
        self.assertTrue((t / "docs/agents/roles/worker.md.framework").is_file())
        self.assertTrue((t / ".claude/agents/brain.md.framework").is_file())
        # project-owned files untouched
        for rel in ("AGENTS.md", "CLAUDE.md", "docs/state.md", "docs/agents/model-notes.md",
                    ".claude/settings.json", ".githooks/pre-push"):
            self.assertEqual((t / rel).read_bytes(), (FIXTURE / rel).read_bytes(), rel)
        # retired but still wired in: kept, and the output says why
        self.assertTrue((t / ".claude/hooks/run_python.sh").exists())
        self.assertTrue((t / "tools/line_endings.py").exists())
        self.assertIn(".claude/settings.json still refers to it", result.stdout)
        self.assertIn(".githooks/pre-push still refers to it", result.stdout)
        # a link from a project document to a removed file is pointed out, but not
        # one from a file the update rewrites without that link
        self.assertIn("fix this link after the update: docs/state.md links to docs/agents/kickoff.md", result.stdout)
        self.assertNotIn("docs/agents/roles/brain.md links to", result.stdout)
        # the migration steps and the checks still to satisfy are printed
        self.assertIn("--- 3.0.0 ---", result.stdout)
        self.assertIn("CLAUDE.md does not point at AGENTS.md", result.stdout)
        # a second run changes nothing
        self.commit_all(t, "migrated")
        again = adopt(t, "--update")
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual(git(t, "status", "--porcelain"), "")

    def test_an_edited_rendered_file_is_kept(self) -> None:
        path = self.target / "tests/test_role_neutrality.py"
        path.write_text(path.read_text(encoding="utf-8") + "\n\nclass ProjectOwn: pass\n", encoding="utf-8")
        self.commit_all(self.target, "project test added to the rendered file")
        result = adopt(self.target, "--update")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(path.exists())
        self.assertIn("keep    tests/test_role_neutrality.py  (edited in this project", result.stdout)

    def test_users_git_cannot_see_still_protect_a_file(self) -> None:
        # untracked user, package-style import, path built in code
        (self.target / "tools/mine.py").write_text("from tools.textblocks import x\n", encoding="utf-8")
        (self.target / "build.py").write_text('p = Path("tools") / "line_endings.py"\n', encoding="utf-8")
        result = adopt(self.target, "--update")
        self.assertTrue((self.target / "tools/textblocks.py").exists(), result.stdout)
        self.assertIn("tools/mine.py still refers to it", result.stdout)

    def test_a_project_file_left_beside_its_framework_copy_still_counts_as_a_user(self) -> None:
        (self.target / "tests/test_framework.py").write_text("from tools import textblocks\n", encoding="utf-8")
        self.commit_all(self.target, "project's own test_framework.py")
        result = adopt(self.target, "--update")
        self.assertIn("beside  tests/test_framework.py.framework", result.stdout)
        self.assertTrue((self.target / "tools/textblocks.py").exists(), result.stdout)

    def test_a_project_that_is_not_a_git_repository_is_still_protected(self) -> None:
        plain = self.tmp / "plain-copy"
        shutil.copytree(FIXTURE, plain)
        result = adopt(plain, "--update")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((plain / "tools/line_endings.py").exists())
        self.assertIn(".githooks/pre-push still refers to it", result.stdout)

    def test_the_new_fw_works_in_the_migrated_project(self) -> None:
        adopt(self.target, "--update")
        self.commit_all(self.target, "migrated")
        result = fw(self.target, "status", "--offline")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("pinned to agentic-framework", result.stdout)
        self.assertIn(sys.platform == "win32" and "py -3" or "python3", result.stdout)


class UpdateOutput(TempDirTest):
    def adopted(self, *extra: str) -> Path:
        target = self.init_repo(self.tmp / "project")
        self.assertEqual(adopt(target, "--project", "Demo", "--adapter", "claude-code", *extra).returncode, 0)
        self.commit_all(target, "adopt")
        return target

    def test_an_up_to_date_project_is_told_there_is_nothing_to_do(self) -> None:
        # Issue #20: 'record' only when the manifest would change.
        target = self.adopted()
        before = (target / "docs/agents/framework.json").read_bytes()
        for args in (("--update", "--dry-run"), ("--update",)):
            result = adopt(target, *args)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("nothing to do: this project already matches agentic-framework", result.stdout)
            self.assertNotIn("record", result.stdout)
        self.assertEqual((target / "docs/agents/framework.json").read_bytes(), before)
        self.assertEqual(git(target, "status", "--porcelain"), "")

    def test_a_dry_run_prints_what_each_release_asks(self) -> None:
        target = self.adopted()
        record = manifest(target)
        record["framework"]["release"] = "2.99.0"
        (target / "docs/agents/framework.json").write_text(json.dumps(record), encoding="utf-8")
        result = adopt(target, "--update", "--dry-run")
        self.assertIn("record  docs/agents/framework.json", result.stdout)
        self.assertIn("What each release asks of this project:", result.stdout)
        self.assertIn("--- 3.0.0 ---", result.stdout)
        self.assertIn("dry run: nothing written", result.stdout)

    def test_seat_checkouts_inside_the_project_are_ignored(self) -> None:
        # Issue #29: .worktrees/ is where local seats work, and git ignores it.
        target = self.adopted()
        self.assertTrue((target / ".worktrees/.gitignore").is_file())
        git(target, "worktree", "add", "-q", "--detach", ".worktrees/worker-001")
        self.assertEqual(git(target, "status", "--porcelain"), "")
        own = self.init_repo(self.tmp / "own-ignore")
        (own / ".gitignore").write_text(".worktrees/\n", encoding="utf-8")
        adopt(own, "--project", "Own")
        self.assertFalse((own / ".worktrees/.gitignore").exists())


class RealProjectLayouts(RoundTest):
    """The layouts real projects had when these defects were found, each
    rebuilt here: a seat file named for the project's executor (#21), a
    deleted seed (#25), a squash-merged round on a seat's machine (#18),
    archive tags (#18), a superseded round (#27), a round attachment (#24) and
    a finished seat checkout (#29)."""

    def test_a_seat_file_named_for_the_projects_executor_is_named(self) -> None:
        (self.brain / ".claude/agents/builder.md").write_text("Builder seat: see AGENTS.md.\n", encoding="utf-8")
        self.commit_all(self.brain, "the project's own seat file")
        result = adopt(self.brain, "--update", "--dry-run")
        self.assertIn("other   .claude/agents/builder.md", result.stdout)
        self.assertIn("delete one of the two", result.stdout)
        # Deleting the framework's own seat file is a decision the update keeps.
        git(self.brain, "rm", "-q", ".claude/agents/worker.md")
        self.commit_all(self.brain, "keep builder.md, drop worker.md")
        result = adopt(self.brain, "--update")
        self.assertIn("gone    .claude/agents/worker.md", result.stdout)
        self.assertFalse((self.brain / ".claude/agents/worker.md").exists())
        self.assertNotIn(".claude/agents/worker.md (missing)", fw(self.brain, "status", "--offline").stdout)

    def test_a_deleted_seed_stays_deleted(self) -> None:
        self.assertEqual(adopt(self.brain, "--update", "--hooks").returncode, 0)
        self.commit_all(self.brain, "hook")
        git(self.brain, "rm", "-q", ".githooks/pre-push")
        self.commit_all(self.brain, "retire the hook")
        for args in (("--update", "--dry-run"), ("--update",)):
            result = adopt(self.brain, *args)
            self.assertIn("gone    .githooks/pre-push  (deleted in this project, so not re-created)", result.stdout)
            self.assertNotIn("create  .githooks/pre-push", result.stdout)
        self.assertFalse((self.brain / ".githooks/pre-push").exists())
        # Asking for it again brings it back.
        result = adopt(self.brain, "--update", "--hooks", "--dry-run")
        self.assertIn("create  .githooks/pre-push", result.stdout)

    def squash_merge(self, round_id: str, branch: str) -> None:
        git(self.brain, "fetch", "-q", "origin")
        git(self.brain, "merge", "-q", "--squash", f"origin/{branch}")
        git(self.brain, "commit", "-q", "-m", f"Round {round_id} (squashed)")
        git(self.brain, "push", "-q", "origin", "main")
        for name in git(self.brain, "ls-remote", "--heads", "origin").split("\n"):
            ref = name.split("refs/heads/")[-1]
            if ref.endswith(round_id):
                git(self.brain, "push", "-q", "origin", "--delete", ref)

    def test_a_squash_merged_round_is_safe_to_leave_on_the_seats_machine(self) -> None:
        self.write_brief("050-squash", tier=1)
        worker, _ = self.deliver_worker("worker-mac", "050-squash")
        self.squash_merge("050-squash", "worker/050-squash")
        git(worker, "switch", "-q", "main")
        git(worker, "pull", "-q")
        git(worker, "fetch", "-q", "--prune")
        result = fw(worker, "status", "--offline", "--leaving")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("safe to leave this machine: yes", result.stdout)
        # Work that is genuinely not on GitHub is still reported.
        git(worker, "switch", "-q", "worker/050-squash")
        (worker / "after.txt").write_text("after the merge\n", encoding="utf-8")
        git(worker, "add", "after.txt")
        git(worker, "commit", "-q", "-m", "Unpushed follow-up")
        result = fw(worker, "status", "--offline", "--leaving")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("not on GitHub yet: worker/050-squash", result.stdout)

    def test_archive_tags_on_the_remote_are_safe_to_leave(self) -> None:
        git(self.brain, "switch", "-q", "-c", "old")
        (self.brain / "old.txt").write_text("old\n", encoding="utf-8")
        git(self.brain, "add", "old.txt")
        git(self.brain, "commit", "-q", "-m", "Old work")
        git(self.brain, "tag", "-a", "archive/branch-old", "-m", "archived")
        git(self.brain, "push", "-q", "origin", "archive/branch-old")
        git(self.brain, "switch", "-q", "main")
        git(self.brain, "branch", "-q", "-D", "old")
        result = fw(self.brain, "status", "--leaving")
        self.assertEqual(result.returncode, 0, result.stdout)
        # A tag that exists only here is still reported.
        git(self.brain, "switch", "-q", "--detach")
        (self.brain / "new.txt").write_text("new\n", encoding="utf-8")
        git(self.brain, "add", "new.txt")
        git(self.brain, "commit", "-q", "-m", "Tagged, never pushed")
        git(self.brain, "tag", "local-only")
        git(self.brain, "switch", "-q", "main")
        result = fw(self.brain, "status", "--leaving")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("not on GitHub yet: tag local-only", result.stdout)

    def test_a_superseded_round_is_not_in_flight(self) -> None:
        self.write_brief("060-a", tier=1)
        self.deliver_worker("worker", "060-a")
        self.write_brief("061-b", tier=1, supersedes="060-a, rejected: the export was wrong", start="origin/worker/060-a")
        git(self.brain, "fetch", "-q", "origin")
        result = fw(self.brain, "status", "--offline")
        self.assertIn("superseded: 060-a, by 061-b -- not in flight", result.stdout)
        self.assertNotIn("in flight: 060-a", result.stdout)
        self.assertIn("in flight: 061-b (Tier 1)", result.stdout)
        self.assertIn("worker: not started", result.stdout)
        result = fw(self.brain, "delivery", "--round", "060-a")
        self.assertIn("superseded by round 061-b", result.stdout)
        self.assertNotIn("must rewrite", result.stdout)
        seat = self.clone(self.origin, "late-seat")
        result = fw(seat, "start", "--role", "worker", "--round", "060-a")
        self.assertEqual(result.returncode, 2)
        self.assertIn("superseded by round 061-b", result.stderr)

    def test_a_round_attachment_is_not_a_report(self) -> None:
        self.write_brief("070-attach")
        worker = self.clone(self.origin, "worker")
        fw(worker, "start", "--role", "worker", "--round", "070-attach")
        folder = worker / "docs/rounds/070-attach"
        (folder / "state-changes.md").write_text("# Every sentence\n\nA long list.\n", encoding="utf-8")
        (folder / "attachments").mkdir()
        (folder / "attachments/log.md").write_text("log\n", encoding="utf-8")
        self.commit_all(worker, "Attachments")
        git(worker, "push", "-q")
        second = self.clone(self.origin, "worker-2")
        result = fw(second, "start", "--role", "worker", "--round", "070-attach")
        self.assertIn("continuing earlier work", result.stdout)
        (second / "docs/rounds/070-attach/worker.md").write_text(WORKER_REPORT, encoding="utf-8")
        self.assertEqual(fw(second, "report", "--role", "worker", "--round", "070-attach", "--push").returncode, 0)
        result = fw(self.brain, "delivery", "--round", "070-attach")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("state-changes", result.stdout)
        verifier = self.deliver_verifier("verifier", "070-attach")
        self.assertTrue((verifier / "docs/rounds/070-attach/state-changes.md").is_file())

    def test_a_finished_seat_checkout_is_listed_as_removable(self) -> None:
        self.write_brief("080-tree", tier=1)
        seat = self.brain / ".worktrees/worker-080"
        git(self.brain, "worktree", "add", "-q", "--detach", ".worktrees/worker-080", "origin/main")
        self.assertEqual(fw(seat, "start", "--role", "worker", "--round", "080-tree").returncode, 0)
        (seat / "docs/rounds/080-tree/worker.md").write_text(WORKER_REPORT, encoding="utf-8")
        self.assertEqual(fw(seat, "report", "--role", "worker", "--round", "080-tree", "--push").returncode, 0)
        self.assertEqual(git(self.brain, "status", "--porcelain"), "")
        result = fw(self.brain, "status", "--offline")
        self.assertNotIn("can be removed", result.stdout)
        self.squash_merge("080-tree", "worker/080-tree")
        result = fw(self.brain, "status", "--offline", "--leaving")
        self.assertIn("can be removed: .worktrees/worker-080", result.stdout)
        self.assertEqual(result.returncode, 0, result.stdout)
