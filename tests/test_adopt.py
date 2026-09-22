"""Adoption and updates, including migrating a 2.x project that was never touched since."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

from tests.helpers import PYTHON, ROOT, TempDirTest, adopt, fw, git, run

FIXTURE = ROOT / "tests" / "fixtures" / "v2_adopter"


def remove_read_only(func, path, _exc) -> None:  # Windows: git objects are read-only
    os.chmod(path, 0o700)
    func(path)


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
        shutil.rmtree(self.target / ".git", onerror=remove_read_only)
        result = adopt(self.target, "--update")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.target / "tools/line_endings.py").exists())
        self.assertIn(".githooks/pre-push still refers to it", result.stdout)

    def test_the_new_fw_works_in_the_migrated_project(self) -> None:
        adopt(self.target, "--update")
        self.commit_all(self.target, "migrated")
        result = fw(self.target, "status", "--offline")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("pinned to agentic-framework", result.stdout)
        self.assertIn(sys.platform == "win32" and "py -3" or "python3", result.stdout)
