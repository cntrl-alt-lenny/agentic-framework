"""Shared helpers: throwaway git repositories that behave like real projects."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable
ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@example.com",
    "GIT_CONFIG_NOSYSTEM": "1",
    # No background maintenance: it can still be writing inside .git while a
    # test removes its temporary directory (seen with git 2.55 on macOS).
    "GIT_CONFIG_COUNT": "2",
    "GIT_CONFIG_KEY_0": "maintenance.auto", "GIT_CONFIG_VALUE_0": "false",
    "GIT_CONFIG_KEY_1": "gc.auto", "GIT_CONFIG_VALUE_1": "0",
}


def run(args: list[str], cwd: Path, *, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True,
                            encoding="utf-8", errors="replace", env=ENV)
    if check and result.returncode != 0:
        raise AssertionError(f"{args} failed ({result.returncode}):\n{result.stdout}\n{result.stderr}")
    return result


def git(cwd: Path, *args: str, check: bool = True) -> str:
    return run(["git", *args], cwd, check=check).stdout.strip()


def adopt(target: Path, *extra: str) -> subprocess.CompletedProcess:
    return run([PYTHON, str(ROOT / "tools" / "adopt.py"), str(target), *extra], ROOT, check=False)


def fw(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return run([PYTHON, str(cwd / "tools" / "fw.py"), *args], cwd, check=False)


class TempDirTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="fwtest-"))

    def tearDown(self) -> None:
        def unlock(func, path, _exc):  # Windows: git objects are read-only
            try:
                os.chmod(path, 0o700)
                func(path)
            except FileNotFoundError:
                pass  # already gone
        shutil.rmtree(self.tmp, onerror=unlock)

    def init_repo(self, path: Path) -> Path:
        path.mkdir(parents=True, exist_ok=True)
        git(path, "init", "-q", "-b", "main")
        git(path, "config", "core.autocrlf", "false")
        return path

    def commit_all(self, repo: Path, message: str) -> None:
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", message)

    def adopted_origin(self) -> Path:
        """A bare 'GitHub' holding an adopted project, and nothing else."""
        seed = self.init_repo(self.tmp / "seed")
        (seed / "README.md").write_text("# Demo\n", encoding="utf-8")
        result = adopt(seed, "--project", "Demo", "--verifier", "--adapter", "claude-code")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.commit_all(seed, "Adopt the framework")
        origin = self.tmp / "origin.git"
        git(self.tmp, "clone", "-q", "--bare", str(seed), str(origin))
        return origin

    def clone(self, origin: Path, name: str) -> Path:
        path = self.tmp / name
        git(self.tmp, "clone", "-q", str(origin), str(path))
        git(path, "config", "core.autocrlf", "false")
        return path
