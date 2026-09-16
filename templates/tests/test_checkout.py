"""The installed first-action checkout check must fail closed."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class TestCheckoutCheck(unittest.TestCase):
    def _run(self, seat: str):
        return subprocess.run(
            [sys.executable, str(ROOT / "tools" / "checkout.py"), "--seat", seat],
            cwd=ROOT, capture_output=True, text=True,
        )

    def setUp(self):
        probe = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=ROOT, capture_output=True, text=True,
        )
        if probe.returncode:
            self.skipTest("adoption target is not a Git checkout")

    def test_primary_or_separate_coordinating_checkout_passes(self):
        proc = self._run("brain")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_claiming_another_seat_fails_with_locations(self):
        proc = self._run("unusual-seat")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("current checkout", proc.stderr)
        self.assertIn("unusual-seat", proc.stderr)


if __name__ == "__main__":
    unittest.main()
