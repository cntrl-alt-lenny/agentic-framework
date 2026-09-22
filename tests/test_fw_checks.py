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
