"""Reproduce round 028 on disposable clones; --baseline expects three failures."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
REGRESSIONS = [
    "tests.test_handoffs.SeatResumption.test_generated_startup_twice_resumes_unpushed_work",
    "tests.test_handoffs.FirstAdoption.test_external_status_routes_first_adoption_without_green_checks",
    "tests.test_handoffs.SuccessorDelivery.test_successor_brief_does_not_invalidate_original_delivery",
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", action="store_true")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="fw028-evidence-") as directory:
        scratch = Path(directory)
        env = {**os.environ, "FW_EVIDENCE_LOG": str(scratch / "commands.log")}
        if args.baseline:
            baseline = subprocess.run(["git", "show", "v3.1.0:tools/fw.py"], cwd=ROOT,
                                      capture_output=True, check=True)
            path = scratch / "baseline.py"
            path.write_bytes(baseline.stdout)
            env["FW_TEST_BASELINE"] = str(path)
        command = [sys.executable, "-m", "unittest", *(REGRESSIONS if args.baseline else ["tests.test_handoffs"]), "-v"]
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", check=False)
        log = scratch / "commands.log"
        text = (log.read_text(encoding="utf-8") if log.exists() else "")
        text += "\nUnittest output:\n" + result.stdout + result.stderr + f"\nProcess exit: {result.returncode}\n"
        for value in (str(ROOT), ROOT.as_posix(), str(ROOT.resolve()), str(scratch), sys.executable):
            text = text.replace(value, "<framework>" if value != sys.executable else "python3")
        print(text.replace("/private<fixture>", "<fixture>"))
        return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
