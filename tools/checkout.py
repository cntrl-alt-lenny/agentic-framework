#!/usr/bin/env python3
"""Verify that this process started in the checkout for its declared seat.

Run this as the first action in every role prompt::

    python3 tools/checkout.py --seat <seat>

A linked worktree at ``.worktrees/<role>`` belongs to its final path component.
An ordinary primary checkout or separate clone is the coordinating seat unless
the owner assigns a separate clone a local, untracked Git setting with::

    git config --local framework.checkout-seat <seat>

Git gives a separate clone the same structural shape as the primary checkout,
so that local assignment is the only honest way to distinguish it. The command
does not change the repository and reports both locations when it fails.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


class CheckoutError(Exception):
    """The current directory is not a usable Git checkout."""


def _git(args: list[str], cwd: str | Path | None = None) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=cwd, stderr=subprocess.DEVNULL, text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _path(raw: str, cwd: str | Path | None) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        path = (Path(cwd) if cwd else Path.cwd()) / path
    return path.resolve()


def checkout_seat(cwd: str | Path | None = None, *, coordinator: str = "brain") -> str:
    """Return the seat structurally assigned to ``cwd``."""
    top_raw = _git(["rev-parse", "--show-toplevel"], cwd)
    if not top_raw:
        raise CheckoutError("not inside a Git repository")
    top = _path(top_raw, cwd)
    if top.parent.name == ".worktrees" and top.name:
        return top.name
    assigned = _git(["config", "--local", "--get", "framework.checkout-seat"], cwd)
    return assigned or coordinator


def check(
    seat: str, cwd: str | Path | None = None, *, coordinator: str = "brain"
) -> tuple[int, str]:
    """Return zero only when ``seat`` owns the current checkout."""
    try:
        top_raw = _git(["rev-parse", "--show-toplevel"], cwd)
        if not top_raw:
            raise CheckoutError("not inside a Git repository")
        top = _path(top_raw, cwd)
        actual = checkout_seat(cwd, coordinator=coordinator)
    except CheckoutError as exc:
        location = Path(cwd or Path.cwd()).resolve()
        return 1, f"checkout check failed: {exc}; current location is {location}"

    if actual == seat:
        return 0, f"checkout ok: seat={seat} checkout={top}"
    expected = (
        f".worktrees/{seat}"
        if seat != coordinator
        else "the primary checkout or a clone assigned to the coordinating seat"
    )
    return 1, (
        f"checkout check failed: current checkout is {top} (seat={actual}); "
        f"seat={seat} must run in {expected}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seat", required=True, help="the role this session was assigned")
    parser.add_argument("--coordinator", default="brain", help="coordinating seat name")
    parser.add_argument("--cwd", default=None, help="checkout to check (default: current directory)")
    args = parser.parse_args(argv)
    code, message = check(args.seat, args.cwd, coordinator=args.coordinator)
    print(message, file=sys.stderr if code else sys.stdout)
    return code


if __name__ == "__main__":
    sys.exit(main())
