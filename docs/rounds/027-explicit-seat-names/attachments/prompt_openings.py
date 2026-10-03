"""Show actual CLI prompt openings in a disposable adopted project."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from tests.helpers import RoundTest, fw

fixture = RoundTest()
fixture.setUp()
try:
    fixture.write_brief("027-seat-labels")
    for role in ("worker", "builder", "verifier"):
        if role == "builder":
            agents = fixture.brain / "AGENTS.md"
            text = agents.read_text(encoding="utf-8")
            assert "| Worker |" in text
            agents.write_text(text.replace("| Worker |", "| Builder |"), encoding="utf-8")
            fixture.commit_all(fixture.brain, "Declare Builder executor")
        result = fw(fixture.brain, "prompt", "--round", "027-seat-labels", "--role", role)
        assert result.returncode == 0, result.stderr
        lines = result.stdout.splitlines()
        expected = f"Demo · ROUND 027 · {role.upper()}"
        opening = f"You are the {role.capitalize()} for Demo, round 027-seat-labels."
        assert lines[0] == expected
        assert lines[2].startswith(opening)
        print(f"python3 tools/fw.py prompt --round 027-seat-labels --role {role} → exit {result.returncode}")
        print(lines[0])
        print(lines[2].split(". ", 1)[0] + ".")
        print()
finally:
    fixture.tearDown()
