#!/usr/bin/env python3
"""Validate the skills repo. Exits non-zero on any error."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from tbskills import validate_repo  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main() -> int:
    report = validate_repo(ROOT)

    for warning in report.warnings:
        print(f"warning: {warning}")
    for error in report.errors:
        print(f"ERROR: {error}", file=sys.stderr)

    skills = len(list((ROOT / "skills").glob("*/SKILL.md")))
    print(f"\n{skills} skills, {len(report.errors)} errors, {len(report.warnings)} warnings")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
