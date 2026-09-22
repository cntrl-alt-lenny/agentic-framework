"""Provider neutrality for this project's normative surface (rendered 2.x template, trimmed for the fixture)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import neutrality  # noqa: E402,F401
ROLES = ("builder", "verifier")
