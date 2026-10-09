#!/usr/bin/env python3
"""Evidence only. Run from any checkout; fixtures exist only in a temporary tree.

Usage: python3 docs/batches/03-feedback-recheck/reproduce.py > evidence.txt
Requires Git and Python 3.9+. No network or existing project writes.
Synthetic scan strings are constructed to keep this public evidence scan-clean.
"""
import codecs
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

BASELINE = "06a7d45e45751c40809d6644ea4503ec61cef709"
ROOT = Path(__file__).resolve().parents[3]
ENV = dict(os.environ, GIT_AUTHOR_NAME="Fixture", GIT_COMMITTER_NAME="Fixture",
           GIT_AUTHOR_EMAIL="fixture" + "@example.invalid",
           GIT_COMMITTER_EMAIL="fixture" + "@example.invalid",
           GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)


def main():
    with tempfile.TemporaryDirectory(prefix="fw03-") as tmp:
        scratch = Path(tmp)
        replacements = [(str(scratch), "<FIXTURES>"), (str(ROOT), "<SOURCE>")]

        def clean(value):
            for old, new in replacements:
                value = value.replace(old, new)
            return value

        def run(args, cwd, expected=0):
            args = [str(a) for a in args]
            print("$ (cwd=" + clean(str(cwd)) + ") " + clean(subprocess.list2cmdline(args)))
            result = subprocess.run(args, cwd=cwd, env=ENV, text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            print(clean(result.stdout), end="" if result.stdout.endswith("\n") else "\n")
            print("exit:", result.returncode)
            if expected is not None:
                assert result.returncode == expected, (args, result.returncode, expected)
            return result

        print("Source baseline:", BASELINE)
        print("Platform:", platform.system(), platform.machine(), "Python", platform.python_version())
        run(["git", "--version"], ROOT)
        release = scratch / "release"
        run(["git", "clone", "--local", "--no-hardlinks", ROOT, release], scratch)
        run(["git", "checkout", "--detach", "v4.0.1"], release)
        assert run(["git", "rev-parse", "HEAD"], release).stdout.strip() == BASELINE
        assert not run(["git", "status", "--porcelain"], release).stdout.strip()
        adopt = [sys.executable, release / "tools/adopt.py"]

        def project(name, hooks=False):
            path = scratch / name
            path.mkdir()
            run(["git", "init", "-b", "main"], path)
            run(adopt + [path, "--project", "Synthetic fixture"] + (["--hooks"] if hooks else []), release)
            run(["git", "add", "."], path)
            run(["git", "commit", "-m", "Adopt published baseline"], path)
            return path

        print("\nISSUE 31: one payload per independent check; BOM on both UTF-16 variants")
        p = project("privacy")
        payload = "C:" + "\\" + "Users" + "\\" + "SyntheticPerson" + "\\" + "log.txt\n"
        payload += "synthetic.person" + "@fixture.invalid\n"
        for i, location in enumerate(("docs/batches/03-probe/attachments/log.txt",
                                      "docs/rounds/003-probe/attachments/log.txt")):
            for encoding, bom in (("utf-8", b""), ("utf-16-le", codecs.BOM_UTF16_LE),
                                  ("utf-16-be", codecs.BOM_UTF16_BE)):
                attachment = p / location
                attachment.parent.mkdir(parents=True, exist_ok=True)
                attachment.write_bytes(bom + payload.encode(encoding))
                print("CASE:", location, encoding, "synthetic Windows path and reserved-domain email")
                result = run([sys.executable, "tools/fw.py", "check"], p,
                             expected=1 if encoding == "utf-8" else 0)
                if encoding == "utf-8":
                    assert "contains a Windows user folder" in result.stdout
                    assert "contains an email address" in result.stdout
                else:
                    assert "contains" not in result.stdout
                    assert attachment.read_bytes()[2:].decode(encoding) == payload
                attachment.unlink()
        print("Payload remains decodable; check neither publishes nor removes it. No real disclosure tested.")

        print("\nISSUE 36: deletion followed by two dry-run/apply cycles")
        p = project("hooks", hooks=True)
        hook = p / ".githooks/pre-push"
        hook.unlink()
        run(["git", "add", "-u"], p)
        run(["git", "commit", "-m", "Retire synthetic hook"], p)
        for cycle in (1, 2):
            print("UPDATE CYCLE:", cycle)
            run(adopt + [p, "--update", "--dry-run"], release)
            run(adopt + [p, "--update"], release)
            record = json.loads((p / "docs/agents/framework.json").read_text())
            print("hook exists:", hook.exists(), "hooks option:", record["options"]["hooks"],
                  "hook record:", record["files"].get(".githooks/pre-push"))
            assert not hook.exists()
            assert record["options"]["hooks"] is True
            assert record["files"][".githooks/pre-push"] == {"kind": "seed"}
        run(["git", "status", "--porcelain"], p)

        print("\nISSUE 43: tracked initialized submodule, clean merged seat")
        sub = scratch / "sub-source"
        sub.mkdir()
        run(["git", "init", "-b", "main"], sub)
        (sub / "data.txt").write_text("Synthetic data\n")
        run(["git", "add", "."], sub)
        run(["git", "commit", "-m", "Submodule fixture"], sub)
        p = project("submodules")
        run(["git", "-c", "protocol.file.allow=always", "submodule", "add", sub, "module"], p)
        run(["git", "commit", "-am", "Track submodule"], p)
        # Ignore all fixture worktrees; leave no project dirty-state ambiguity.
        with (p / ".gitignore").open("a") as f:
            f.write(".worktrees/\n")
        run(["git", "add", ".gitignore"], p)
        run(["git", "commit", "-m", "Ignore fixture seats"], p)
        seat = p / ".worktrees/worker-03-probe"
        run(["git", "worktree", "add", "-b", "worker/03-probe", seat], p)
        run(["git", "-c", "protocol.file.allow=always", "submodule", "update", "--init"], seat)
        (p / "advance.txt").write_text("Advance main past merged seat\n")
        run(["git", "add", "."], p)
        run(["git", "commit", "-m", "Advance main"], p)
        assert not run(["git", "status", "--porcelain", "--untracked-files=all"], seat).stdout.strip()
        head = run(["git", "rev-parse", "HEAD"], seat).stdout.strip()
        run(["git", "merge-base", "--is-ancestor", head, "main"], p)
        result = run([sys.executable, "tools/fw.py", "status", "--offline"], p)
        assert "finished checkouts (clean, and their work is merged)" in result.stdout
        run(["git", "worktree", "remove", seat], p, expected=128)
        run(["git", "submodule", "deinit", "module"], seat)
        run(["git", "worktree", "remove", seat], p, expected=128)
        run(["git", "-c", "protocol.file.allow=always", "submodule", "update", "--init"], seat)
        dirty = seat / "module/data.txt"
        dirty.write_text("Uncommitted synthetic work\n")
        run(["git", "status", "--porcelain", "--untracked-files=all"], seat)
        result = run([sys.executable, "tools/fw.py", "status", "--offline"], p)
        assert "uncommitted changes in linked checkout" in result.stdout
        assert "finished checkouts" not in result.stdout
        run(["git", "worktree", "remove", seat], p, expected=128)
        assert dirty.read_text() == "Uncommitted synthetic work\n"
        print("Dirty work preserved; no forced worktree removal attempted.")
        print("Guidance in release Brain card:")
        lines = (release / "framework/roles/brain.md").read_text().splitlines()
        print("\n".join(lines[33:35]))
        print("All issue assertions passed. Temporary synthetic fixtures are discarded on exit.")


if __name__ == "__main__":
    main()
