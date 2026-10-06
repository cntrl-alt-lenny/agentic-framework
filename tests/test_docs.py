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
    "framework/FRAMEWORK.md": 800,
    "framework/roles/brain.md": 400,
    "framework/roles/worker.md": 250,
    "framework/roles/verifier.md": 200,
    "templates/AGENTS.md": 600,
    "templates/docs/state.md": 200,
    "docs/state.md": 1000,
    "AGENTS.md": 1000,
}
ADAPTER_FILE_WORDS = 80

_SPEC = importlib.util.spec_from_file_location("fw", ROOT / "tools" / "fw.py")
fw = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(fw)


COMMANDS = {"status", "check"}
FENCE = re.compile(r"^```.*?^```", re.S | re.M)
#: fw.py's command where one is written: after an interpreter, or followed by
#: a flag, a placeholder or the end of a code span. Prose that names the file
#: ("tools/fw.py and tests/...") is not a command.
WRITTEN = re.compile(r"fw\.py[ \t]+(\w+)(?=[ \t]*(?:`|--|…|<|\.\.\.))|(?:python3?|py -3)\s+\S*fw\.py\s+(\w+)")


def written_commands(text: str) -> list[str]:
    found = [word for block in FENCE.findall(text) for word in re.findall(r"fw\.py\s+(\w+)", block)]
    return found + [a or b for a, b in WRITTEN.findall(FENCE.sub(" ", text))]


def markdown_files():
    for base in ("framework", "templates", "adapters", "docs"):
        yield from sorted((ROOT / base).rglob("*.md"))
    yield from (ROOT / name for name in ("README.md", "AGENTS.md", "CLAUDE.md", "CHANGELOG.md"))


def current_instructions():
    """What agents act on today: not past rounds, and only this release's
    CHANGELOG entry (older entries name commands since removed)."""
    for path in markdown_files():
        if "rounds" in path.relative_to(ROOT).parts:
            continue
        text = path.read_text(encoding="utf-8")
        if path.name == "CHANGELOG.md":
            text = text.split("\n## ", 2)[1] if "\n## " in text else text
        yield path, text


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
        for path, text in current_instructions():
            for word in written_commands(text):
                self.assertIn(word, COMMANDS, f"{path}: fw.py {word}")

    def test_a_command_is_told_from_prose(self) -> None:
        # Round 026: prose naming the file tripped the check twice.
        for text in ("Run `tools/fw.py prmpt --round 001-x`.", "`fw.py prmpt`", "python3 tools/fw.py prmpt",
                     "py -3 tools/fw.py prmpt", "use `python3 tools/fw.py\nprmpt`", "```\nfw.py prmpt\n```",
                     "`tools/fw.py prmpt <id>`", "`fw.py prmpt …`"):
            self.assertEqual(written_commands(text), ["prmpt"], text)
        for text in ("the three role cards, tools/fw.py and tests/test_framework.py",
                     "`tools/fw.py and tests/test_framework.py`", "`tools/fw.py` and `tests/x.py`",
                     "what fw.py itself does.", "`fw.py`'s output"):
            self.assertEqual(written_commands(text), [], text)

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

    def test_summary_parts_match_the_worker_card(self) -> None:
        core = (ROOT / "framework/FRAMEWORK.md").read_text(encoding="utf-8")
        card = " ".join((ROOT / "framework/roles/worker.md").read_text(encoding="utf-8").split())
        for part in ("Done", "Checked", "Not checked", "Failed or blocked"):
            self.assertIn(f"**{part}**", core)
            self.assertIn(part, card)

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
