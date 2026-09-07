"""The owner-facing loop has to survive being started from nothing.

`framework/kickoff.md` is what makes Brain -> Builder -> Verifier -> Brain
runnable from completely fresh sessions: the owner pastes a fixed block, gets
two prompts back, runs them, and pastes a second fixed block to come back. The
value of that depends on properties no prose review reliably catches, so they
are asserted here.

The point is not that the words stay the same -- they should be free to
improve. It is that the *mechanism* cannot quietly lose a load-bearing half:
Brain issuing only one prompt again, or the Verifier gaining permission to
review a branch without pinning the commit it actually reviewed.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import adopt  # noqa: E402

KICKOFF = ROOT / "framework" / "kickoff.md"
BRAIN = ROOT / "framework" / "roles" / "brain.md"
VERIFIER = ROOT / "framework" / "roles" / "verifier.md"

FENCED = re.compile(r"^```\n(.*?)^```", re.S | re.M)


class TestTheKickoffReachesProjects(unittest.TestCase):
    def test_it_exists(self):
        self.assertTrue(KICKOFF.is_file())

    def test_adoption_installs_it(self):
        """A loop document only this repository has does not help any project."""
        self.assertIn(
            "kickoff.md", adopt.VERBATIM_DOCS,
            "kickoff.md must be copied into adopting projects; it is the one "
            "document the owner actually opens",
        )


class TestThePasteableBlocksAreUsable(unittest.TestCase):
    """Fresh sessions have no history, so the blocks must carry everything."""

    def setUp(self):
        self.text = KICKOFF.read_text(encoding="utf-8")
        self.blocks = FENCED.findall(self.text)

    def test_there_are_blocks_to_paste(self):
        # Fail closed: prose describing a paste-able block is not one.
        self.assertGreaterEqual(
            len(self.blocks), 2,
            "the loop needs at least two paste-able blocks: one to start a "
            "round and one to come back from it",
        )

    def test_the_starting_block_points_the_session_at_its_contract(self):
        """A seat that never reads its contract is not holding it."""
        start = next(
            (b for b in self.blocks if "You are the Brain" in b), None
        )
        self.assertIsNotNone(start, "no block starts a Brain session")
        self.assertIn("AGENTS.md", start)
        self.assertIn("roles/brain.md", start)

    def test_the_starting_block_asks_for_both_prompts(self):
        start = next(b for b in self.blocks if "You are the Brain" in b)
        self.assertIn("Builder prompt", start)
        self.assertIn("Verifier prompt", start)

    def test_a_returning_block_exists_so_the_owner_need_not_improvise(self):
        self.assertTrue(
            any("finished" in b and "adjudicate" in b for b in self.blocks),
            "no block covers coming back to Brain once the round has run",
        )


class TestBrainStillIssuesBothPrompts(unittest.TestCase):
    """The regression this exists to prevent: silently going back to one."""

    def test_the_contract_requires_a_separate_verifier_prompt(self):
        text = BRAIN.read_text(encoding="utf-8")
        self.assertIn("Verifier prompt", text)
        self.assertIn(
            "same* turn", text,
            "the Verifier prompt must be issued in the same turn as the "
            "executor prompt, or the owner is back to three round trips",
        )


class TestEarlyVerifierPromptsKeepExactShaDiscipline(unittest.TestCase):
    """Both halves, because dropping either one is a real defect.

    Allowing a branch without requiring the resolved SHA turns exact-SHA review
    into review of a moving target -- which `evidence.md` treats as the thing
    that makes review mean anything.
    """

    def setUp(self):
        # Prose here is hard-wrapped, so a phrase spanning a line break would
        # fail a naive substring check. Collapse whitespace first -- the same
        # reason `tools/textblocks.py` gives the scanners logical lines.
        self.text = " ".join(VERIFIER.read_text(encoding="utf-8").split())

    def test_a_branch_may_be_given_instead_of_a_head_sha(self):
        self.assertIn("branch", self.text)
        self.assertIn("resolve it yourself", self.text)

    def test_but_the_literal_sha_must_still_be_recorded(self):
        self.assertIn(
            "literal SHA", self.text,
            "resolving a branch is only acceptable if the SHA actually "
            "reviewed is pinned and reported",
        )

    def test_a_missing_branch_stops_the_review_rather_than_widening_it(self):
        self.assertIn("does not exist yet", self.text)
        self.assertIn(
            "never a reason to review the base", self.text,
            "a Verifier that falls back to the default branch when the work "
            "has not landed reports on the wrong thing",
        )


if __name__ == "__main__":
    unittest.main()
