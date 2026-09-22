"""The framework's text stays small, consistent with its tool, and portable.

The word budgets are the brake on growth: every feedback round that adds a
sentence must fit it or remove one. Raising a budget is a visible, reviewed
change to this file.
"""

from __future__ import annotations

import importlib.util
import json
import re
import unittest

from tests.helpers import ROOT

BUDGETS = {
    "framework/FRAMEWORK.md": 2500,
    "framework/roles/brain.md": 750,
    "framework/roles/worker.md": 750,
    "framework/roles/verifier.md": 750,
    "templates/AGENTS.md": 600,
    "templates/docs/state.md": 200,
    "docs/state.md": 1000,
    "AGENTS.md": 1000,
}
ADAPTER_FILE_WORDS = 80

_SPEC = importlib.util.spec_from_file_location("fw", ROOT / "tools" / "fw.py")
fw = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(fw)


def markdown_files():
    for base in ("framework", "templates", "adapters", "docs"):
        yield from sorted((ROOT / base).rglob("*.md"))
    yield from (ROOT / name for name in ("README.md", "AGENTS.md", "CLAUDE.md", "CHANGELOG.md"))


class Budgets(unittest.TestCase):
    def test_word_budgets(self) -> None:
        for rel, budget in BUDGETS.items():
            count = len((ROOT / rel).read_text(encoding="utf-8").split())
            self.assertLessEqual(count, budget, f"{rel} is {count} words; budget {budget}")

    def test_adapters_only_point(self) -> None:
        for path in sorted((ROOT / "adapters").rglob("files/**/*")):
            if path.is_file():
                text = path.read_text(encoding="utf-8")
                self.assertLessEqual(len(text.split()), ADAPTER_FILE_WORDS, path)
                self.assertRegex(text, r"AGENTS\.md|docs/agents/", f"{path} must point at the contracts")

    def test_copied_set_is_small(self) -> None:
        copied = [ROOT / "framework/FRAMEWORK.md", *sorted((ROOT / "framework/roles").glob("*.md"))]
        self.assertEqual(sorted(p.name for p in (ROOT / "framework").rglob("*.md")),
                         sorted(p.name for p in copied), "framework/ holds only what projects copy")


class Consistency(unittest.TestCase):
    def test_every_documented_command_exists(self) -> None:
        commands = {"status", "start", "report", "delivery", "check"}
        for path in markdown_files():
            for match in re.finditer(r"fw\.py (\w+)", path.read_text(encoding="utf-8")):
                self.assertIn(match.group(1), commands, f"{path}: fw.py {match.group(1)}")

    def test_relative_links_resolve(self) -> None:
        for path in markdown_files():
            if "templates" in path.parts:
                continue  # template links resolve inside the adopting project
            text = path.read_text(encoding="utf-8")
            if path.name == "CHANGELOG.md":
                text = text.split("\n## 2.1.0", 1)[0]  # older entries describe files since removed
            for target in re.findall(r"\]\(([^)#\s]+)", text):
                if "://" in target:
                    continue
                self.assertTrue((path.parent / target).exists(), f"{path}: {target}")

    def test_changelog_has_this_release_with_adopter_steps(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        match = re.search(rf"^## {re.escape(version)} .*?(?=^## |\Z)", text, re.M | re.S)
        self.assertIsNotNone(match, f"CHANGELOG.md has no entry for {version}")
        self.assertIn("### What an adopter must do", match.group(0))

    def test_report_sections_match_the_role_cards(self) -> None:
        for role, card in (("worker", "worker"), ("verifier", "verifier")):
            text = (ROOT / f"framework/roles/{card}.md").read_text(encoding="utf-8")
            for section in fw.sections_for(role):
                self.assertIn(f"## {section}", text, f"{card}.md report template lacks ## {section}")

    def test_legacy_fingerprints_are_well_formed(self) -> None:
        data = json.loads((ROOT / "tools/legacy_installs.json").read_text(encoding="utf-8"))
        self.assertIn("docs/agents/CONSTITUTION.md", data["files"])
        for rel, hashes in data["files"].items():
            for value in hashes:
                self.assertRegex(value, r"^[0-9a-f]{64}$", rel)


class Portability(unittest.TestCase):
    def test_no_personal_paths_or_addresses(self) -> None:
        for path in markdown_files():
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                for pattern, what in fw.PERSONAL:
                    self.assertIsNone(pattern.search(line), f"{path}:{number} contains {what}")

    def test_framework_repository_passes_its_own_project_checks(self) -> None:
        errors = [m for level, m in fw.check_project(ROOT) if level == "error"]
        self.assertEqual(errors, [])

    def test_no_shell_heredocs_in_instructions(self) -> None:
        for path in markdown_files():
            self.assertNotIn("<<'", path.read_text(encoding="utf-8"), f"{path} tells an agent to use a bash heredoc")


if __name__ == "__main__":
    unittest.main()
