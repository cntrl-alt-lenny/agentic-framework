"""Every Python file this framework installs into an adopted project must
pass a baseline lint, at this framework's minimum supported Python and at
newer targets adopting projects commonly use -- otherwise a project with its
own required lint check cannot merge its own adoption. Reported directly:
`python3 -m ruff check tools/authority.py tools/neutrality.py tools/report.py
--select F` found five F821s (a quoted `"Path"` return annotation with no
module-level import to back it) and one F401 at the framework's base SHA.

Skips, never fails, when `ruff` is not available on this host: an absent lint
dependency is UNKNOWN coverage, not proof the code is clean -- the same
principle this framework applies to every guard whose tool might be missing.
CI installs ruff explicitly in a dedicated job and always runs this.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

#: Every Python file adoption installs into a project as a byte copy, never
#: hand-edited by the project -- see framework/adoption.md and
#: tools/adopt.py's build_plan. Excludes
#: templates/tests/test_role_neutrality.py, which is rendered per project
#: before installation; its RENDERED form is checked separately below,
#: because the raw template's `{{ROLES}}` placeholder is not meaningful
#: Python on its own -- see TestInstalledFilesAreLintClean's last test.
INSTALLED_PYTHON_FILES = (
    "tools/checkout.py",
    "tools/report.py",
    "tools/line_endings.py",
    "tools/neutrality.py",
    "tools/textblocks.py",
    "tools/authority.py",
    "templates/tests/test_checkout.py",
    "tests/test_report.py",
    "adapters/claude-code/hooks/save_agent_reply.py",
)

#: Real defects (F), a real syntax error (E9), likely bugs (B), and needless
#: pre-modern-Python idioms (UP) -- not style or formatting, which is a
#: separate, opinionated concern this framework does not impose on adopters.
SELECT = "F,E9,B,UP"

#: This framework's own floor -- see framework/adoption.md's "Python
#: compatibility". Every installed tool must run correctly here.
MINIMUM_PYTHON = "py39"
#: Targets newer than the floor that adopting projects commonly run.
NEWER_TARGETS = ("py311", "py313")


def _ruff_available() -> bool:
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "ruff", "--version"],
            capture_output=True, text=True,
        )
    except (FileNotFoundError, OSError):
        return False
    return proc.returncode == 0


def _run_ruff(paths, *, target_version: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "ruff", "check", f"--select={SELECT}",
         f"--target-version={target_version}", *[str(p) for p in paths]],
        cwd=ROOT, capture_output=True, text=True,
    )


def _rendered_role_neutrality_test(tmp_dir: Path) -> Path:
    """The templated installed test, rendered with sample project values --
    what an adopting project actually receives and must lint clean, never
    the raw `{{ROLES}}` placeholder source."""
    import adopt
    values = {"ROLES": repr(("worker",)), "COORDINATOR": "brain"}
    text = (ROOT / "templates" / "tests" / "test_role_neutrality.py").read_text(
        encoding="utf-8"
    )
    out = tmp_dir / "test_role_neutrality_rendered.py"
    out.write_text(adopt.render(text, values), encoding="utf-8")
    return out


class TestInstalledFilesAreLintClean(unittest.TestCase):
    def setUp(self):
        if not _ruff_available():
            self.skipTest(
                "ruff is not available on this host; lint coverage is "
                "UNKNOWN here, not proven clean -- CI installs it explicitly"
            )
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.rendered = _rendered_role_neutrality_test(Path(self._tmp.name))

    def _paths(self) -> list[Path]:
        return [ROOT / rel for rel in INSTALLED_PYTHON_FILES] + [self.rendered]

    def test_clean_at_the_minimum_supported_python(self):
        proc = _run_ruff(self._paths(), target_version=MINIMUM_PYTHON)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_clean_at_newer_targets_adopters_commonly_use(self):
        for target in NEWER_TARGETS:
            with self.subTest(target=target):
                proc = _run_ruff(self._paths(), target_version=target)
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_the_rendered_template_is_what_gets_linted_not_the_raw_placeholder(self):
        """`{{ROLES}}` parses as a set literal referencing the undefined name
        `ROLES` -- proving the rendered form, never the raw source text, is
        what the tests above actually certify."""
        raw = ROOT / "templates" / "tests" / "test_role_neutrality.py"
        proc = _run_ruff([raw], target_version=MINIMUM_PYTHON)
        self.assertNotEqual(
            proc.returncode, 0,
            "the raw template unexpectedly passed ruff on its own; this "
            "test's premise (it needs rendering first) no longer holds",
        )
        self.assertIn("ROLES", proc.stdout)


class TestThePy39FloorIsReal(unittest.TestCase):
    """The one documented exception: UP017 (`datetime.UTC`) is not applied
    in tools/report.py because that name does not exist before Python 3.11,
    and this framework's installed tools support 3.9 -- see
    framework/adoption.md. Proves the exception is real: the suppressed line
    WOULD be flagged at a newer target without it, rather than a blanket
    ignore silently covering something else too.
    """

    def setUp(self):
        if not _ruff_available():
            self.skipTest("ruff is not available on this host")

    def test_report_py_is_clean_at_py311_with_the_documented_suppression(self):
        proc = _run_ruff([ROOT / "tools" / "report.py"], target_version="py311")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_the_suppressed_line_would_otherwise_be_flagged_at_py311(self):
        text = (ROOT / "tools" / "report.py").read_text(encoding="utf-8")
        marker = (
            '    stamp = datetime.now(timezone.utc).isoformat('
            'timespec="seconds")  # noqa: UP017'
        )
        self.assertIn(marker, text, "fixture out of sync with tools/report.py")
        without_noqa = text.replace(marker, marker.replace("  # noqa: UP017", ""))
        with tempfile.TemporaryDirectory() as tmp:
            scratch = Path(tmp) / "report.py"
            scratch.write_text(without_noqa, encoding="utf-8")
            proc = _run_ruff([scratch], target_version="py311")
        self.assertNotEqual(
            proc.returncode, 0,
            "UP017 did not fire without the suppression; the documented "
            "exception may no longer be real",
        )
        self.assertIn("UP017", proc.stdout)

    def test_python_compatibility_is_stated_in_adoption_documentation(self):
        text = (ROOT / "framework" / "adoption.md").read_text(encoding="utf-8")
        self.assertIn("3.9", text)


if __name__ == "__main__":
    unittest.main()
