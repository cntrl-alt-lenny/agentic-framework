"""A block declaring one scanner's rule must never hide another's finding.

`tools/authority.py` and `tools/neutrality.py` share the `guard:counterexample`
wrapper and `guard:violation <rule> roles=<roles> text="<text>"` declaration
syntax (`tools/textblocks.py`'s `counterexample_blocks()`). Round 023 fixed
`tools/authority.py`'s own blanket suppression -- see
`tests/test_authority_invariants.py`'s `TestCounterexampleExemptionIsPreciselyScoped`
for that scanner's own proof -- but the brief also asks for cases constructed
against the OTHER direction and against a block naming both scanners' rules
together, not assumed. These are those cases, run against both scanners from
one place so the two proofs cannot silently drift apart.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import authority  # noqa: E402
import docset  # noqa: E402
import neutrality  # noqa: E402

ROLES = docset.ROLES
COORDINATOR = docset.COORDINATOR


def _neutrality_scan(text: str):
    return neutrality.scan(text, ROLES, coordinator=COORDINATOR)


class TestAScannerNeverHidesTheOtherScannersFinding(unittest.TestCase):
    """A block whose ONLY declaration names the other scanner's rule must
    still surface real, undeclared content of its own kind -- in both
    directions.
    """

    def test_a_block_declaring_only_authoritys_rule_still_surfaces_a_real_neutrality_finding(self):
        text = (
            "# Doc\n\n"
            "<!-- guard:counterexample -->\n"
            '<!-- guard:violation routine-approval roles=builder '
            'text="offer to merge" -->\n'
            "Hand this to the Acme Builder, who will offer to merge it.\n"
            "<!-- /guard:counterexample -->\n"
        )
        result = _neutrality_scan(text)
        matched = [f.matched for f in result.findings]
        self.assertIn(
            "Acme Builder", matched,
            "a block declaring only tools/authority.py's rule hid a real, "
            "undeclared tools/neutrality.py finding sharing the same block",
        )

    def test_a_block_declaring_only_neutralitys_rule_still_surfaces_a_real_authority_finding(self):
        text = (
            "# Doc\n\n"
            "<!-- guard:counterexample -->\n"
            '<!-- guard:violation compound-lane roles=builder '
            'text="Acme Builder" -->\n'
            "Hand this to the Acme Builder, who will offer to merge it.\n"
            "<!-- /guard:counterexample -->\n"
        )
        findings = authority.scan(text)
        matched = [f.matched for f in findings]
        self.assertIn(
            "offer to merge", matched,
            "a block declaring only tools/neutrality.py's rule hid a real, "
            "undeclared tools/authority.py finding sharing the same block "
            "-- this is the exact defect round 023 fixed",
        )

    def test_a_completely_undeclared_block_hides_nothing_in_either_scanner(self):
        text = (
            "# Doc\n\n"
            "<!-- guard:counterexample -->\n"
            "Hand this to the Acme Builder, who will offer to merge it.\n"
            "<!-- /guard:counterexample -->\n"
        )
        self.assertIn("offer to merge", [f.matched for f in authority.scan(text)])
        self.assertIn(
            "Acme Builder", [f.matched for f in _neutrality_scan(text).findings]
        )


class TestMixingScannersInOneBlockFailsSafeNotSilent(unittest.TestCase):
    """`framework/adoption.md` now says: keep a block's declarations owned by
    one scanner, because `tools/neutrality.py`'s own probe re-validates every
    declaration present against its own rules before exempting any of them.
    This proves the failure mode of ignoring that advice is SAFE -- the
    content becomes visible and the block is flagged inert for review -- not
    a silent, wider hole.
    """

    def test_a_foreign_declaration_sharing_a_block_breaks_only_that_blocks_own_exemption_never_widens_it(self):
        text = (
            "# Doc\n\n"
            "<!-- guard:counterexample -->\n"
            '<!-- guard:violation compound-lane roles=builder '
            'text="Acme Builder" -->\n'
            '<!-- guard:violation routine-approval roles=builder '
            'text="offer to merge" -->\n'
            "Hand this to the Acme Builder, who will offer to merge it.\n"
            "<!-- /guard:counterexample -->\n"
        )
        result = _neutrality_scan(text)
        self.assertIn(
            "Acme Builder", [f.matched for f in result.findings],
            "a block mixing a foreign (authority) declaration alongside a "
            "genuine, otherwise-valid neutrality declaration silently kept "
            "the neutrality finding suppressed instead of failing safe",
        )
        self.assertTrue(
            result.inert_counterexamples(),
            "the broken mixed-scanner exemption was not flagged as inert, "
            "so a reviewer would never learn the block needs splitting",
        )
        # authority.py, meanwhile, still exempts its OWN declared+matched
        # finding from the same mixed block -- validation is per-declaration,
        # not blocked by a foreign declaration sharing the block.
        self.assertEqual(
            authority.scan(text), [],
            "a foreign (neutrality) declaration sharing the block stopped "
            "authority.py from exempting its own validated declaration",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
