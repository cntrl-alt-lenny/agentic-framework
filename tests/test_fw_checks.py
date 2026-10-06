"""fw.py's project checks and its release check."""

from __future__ import annotations

import json

from tests.helpers import TempDirTest, adopt, fw, git


class ProjectChecks(TempDirTest):
    def setUp(self) -> None:
        super().setUp()
        self.project = self.init_repo(self.tmp / "project")
        adopt(self.project, "--project", "Demo", "--adapter", "claude-code")

    def errors(self) -> str:
        result = fw(self.project, "check")
        return result.stdout if result.returncode == 1 else ""

    def test_clean_project_passes(self) -> None:
        result = fw(self.project, "check")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_state_budget(self) -> None:
        (self.project / "docs/state.md").write_text("word " * 1200, encoding="utf-8")
        self.assertIn("is 1200 words; its budget is 1000", self.errors())
        path = self.project / "docs/agents/framework.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record["settings"]["state_words"] = 1500
        path.write_text(json.dumps(record), encoding="utf-8")
        self.assertEqual(fw(self.project, "check").returncode, 0)

    def test_commit_ids_only_under_historical_anchors(self) -> None:
        sha = "0123456789abcdef0123456789abcdef01234567"
        (self.project / "docs/state.md").write_text(f"# State\n\nMain is at {sha}.\n", encoding="utf-8")
        self.assertIn("full commit id", self.errors())
        (self.project / "docs/state.md").write_text(f"# State\n\n## Historical anchors\n\n- {sha}\n", encoding="utf-8")
        self.assertEqual(fw(self.project, "check").returncode, 0)

    def test_tool_entry_files_must_point_at_agents(self) -> None:
        (self.project / "GEMINI.md").write_text("# Gemini rules\n", encoding="utf-8")
        self.assertIn("GEMINI.md does not point at AGENTS.md", self.errors())

    def test_personal_paths_and_emails(self) -> None:
        for text, what in (("see /Users/leo/Dev/x", "macOS home"), ("D:\\Google Drive\\Hub", "drive path"),
                           ("mail me@gmail.com", "email")):
            (self.project / "docs/state.md").write_text(f"# State\n\n{text}\n", encoding="utf-8")
            self.assertIn(what, self.errors(), text)
        (self.project / "docs/state.md").write_text(
            "# State\n\nClone git@github.com:o/r and see /Users/<name>/.\n", encoding="utf-8")
        self.assertEqual(fw(self.project, "check").returncode, 0)

    def test_personal_pattern_edge_cases(self) -> None:
        for text, what in (("C:/Users/x/Dev", "Windows user folder"), ('"C:\\\\Users\\\\x"', "Windows user folder"),
                           ("E:/Projects/x", "drive path")):
            (self.project / "docs/state.md").write_text(f"# State\n\n{text}\n", encoding="utf-8")
            self.assertIn(what, self.errors(), text)
        (self.project / "docs/state.md").write_text(
            "# State\n\nCo-Authored-By: Claude <noreply@anthropic.com>; printf('%s:\\n')\n", encoding="utf-8")
        self.assertEqual(fw(self.project, "check").returncode, 0, fw(self.project, "check").stdout)

    def test_only_the_historical_anchors_section_is_exempt(self) -> None:
        sha = "0123456789abcdef0123456789abcdef01234567"
        (self.project / "docs/state.md").write_text(
            f"# State\n\n## Historical anchors\n\n- {sha}\n\n## Now\n\nMain is {sha}.\n", encoding="utf-8")
        self.assertIn("full commit id", self.errors())

    def test_merge_rule_must_be_known(self) -> None:
        agents = self.project / "AGENTS.md"
        agents.write_text(agents.read_text(encoding="utf-8").replace("owner-approves", "whenever"), encoding="utf-8")
        self.assertIn("merge rule 'whenever'", self.errors())

    def test_status_names_uninitialised_submodules(self) -> None:
        sub = self.init_repo(self.tmp / "engine")
        (sub / "rules.txt").write_text("x\n", encoding="utf-8")
        self.commit_all(sub, "engine")
        self.commit_all(self.project, "adopt")
        git(self.project, "-c", "protocol.file.allow=always", "submodule", "add", "-q", str(sub), "engine")
        self.commit_all(self.project, "add engine")
        clone = self.tmp / "clone"
        git(self.tmp, "clone", "-q", str(self.project), str(clone))
        result = fw(clone, "status", "--offline")
        self.assertIn("submodule(s) not initialised here: engine", result.stdout)


class ReleaseCheck(TempDirTest):
    def test_status_reports_a_newer_release(self) -> None:
        framework = self.init_repo(self.tmp / "framework")
        (framework / "x").write_text("x\n", encoding="utf-8")
        self.commit_all(framework, "x")
        for tag in ("v3.0.0", "v3.1.0", "v4.0.0"):
            git(framework, "tag", tag)
        project = self.init_repo(self.tmp / "project")
        adopt(project, "--project", "Demo")
        path = project / "docs/agents/framework.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record["framework"] = {"repository": str(framework), "release": "3.0.0"}
        path.write_text(json.dumps(record), encoding="utf-8")
        result = fw(project, "status")
        self.assertIn("newer release available: 4.0.0 -- major", result.stdout)
        self.assertIn("next: ask Brain to plan the update to framework release 4.0.0", result.stdout)
        record["framework"]["release"] = "4.0.0"
        tag = self.tmp / "framework"
        git(tag, "tag", "v4.0.1")
        path.write_text(json.dumps(record), encoding="utf-8")
        result = fw(project, "status")
        # A patch release is proposed too, as a light round (no release is missed).
        self.assertIn("newer release available: 4.0.1 -- minor or patch: update between batches; Brain proposes it",
                      result.stdout)

    def test_unreachable_framework_is_unknown_not_an_error(self) -> None:
        project = self.init_repo(self.tmp / "project")
        adopt(project, "--project", "Demo")
        path = project / "docs/agents/framework.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record["framework"]["repository"] = str(self.tmp / "missing")
        path.write_text(json.dumps(record), encoding="utf-8")
        result = fw(project, "status")
        self.assertEqual(result.returncode, 0)
        self.assertIn("newer releases: unknown", result.stdout)

    def test_local_edits_to_framework_files_are_listed(self) -> None:
        project = self.init_repo(self.tmp / "project")
        adopt(project, "--project", "Demo")
        with open(project / "docs/agents/FRAMEWORK.md", "a", encoding="utf-8") as stream:
            stream.write("\nA local rule.\n")
        result = fw(project, "status", "--offline")
        self.assertIn("framework files changed locally", result.stdout)
        self.assertIn("docs/agents/FRAMEWORK.md", result.stdout)


class ScanScope(TempDirTest):
    def test_the_personal_data_message_says_which_documents_are_scanned(self) -> None:
        # Issue #22: "0 errors" must not read as "the whole repository is clean".
        project = self.init_repo(self.tmp / "project")
        adopt(project, "--project", "Demo")
        (project / "docs/state.md").write_text("# State\n\nsee /Users/someone/Dev/x\n", encoding="utf-8")
        result = fw(project, "check")
        self.assertIn("docs/agents/**/*.md, docs/batches/**, and 3.x rounds", result.stdout)
        self.assertNotIn("tracked documents", result.stdout)

    def test_round_attachments_are_scanned(self) -> None:
        # Round 026: logs and long lists go in attachments/, where home folders are likeliest.
        project = self.init_repo(self.tmp / "project")
        adopt(project, "--project", "Demo")
        folder = project / "docs/rounds/001-x/attachments/logs"
        folder.mkdir(parents=True)
        (folder / "run.log").write_text("ok\nread C:\\Users\\someone\\x.txt\n", encoding="utf-8")
        (folder / "shot.png").write_bytes(b"\x89PNG\0\0/Users/someone/")
        result = fw(project, "check")
        self.assertIn("docs/rounds/001-x/attachments/logs/run.log:2 contains", result.stdout)
        self.assertNotIn("shot.png", result.stdout)

    def test_batch_files_are_scanned(self) -> None:
        project = self.init_repo(self.tmp / "project")
        adopt(project, "--project", "Demo")
        (project / "docs/batches/04-x.md").write_text("ran /home/someone/x\n", encoding="utf-8")
        result = fw(project, "check")
        self.assertIn("docs/batches/04-x.md:1 contains", result.stdout)
