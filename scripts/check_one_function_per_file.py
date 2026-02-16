"""Enforce one-public-callable-per-file convention.

Walks the skillet/ source tree, parses each Python file, and flags any
file that exports more than one public callable (function or class).

Exempt files: __init__.py, conftest.py, *_test.py, types.py, models.py,
result.py, errors.py, base.py, config.py, dataclasses.py
Exempt directories: tests/

Per-file opt-out: place ``# skillet: allow-multiple-public-callables``
in the first 20 lines.
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

EXEMPT_FILENAMES = frozenset(
    {
        "__init__.py",
        "conftest.py",
        "types.py",
        "models.py",
        "result.py",
        "errors.py",
        "base.py",
        "config.py",
        "dataclasses.py",
    }
)

EXEMPT_DIRS = frozenset({"tests"})

SUPPRESSION_COMMENT = "# skillet: allow-multiple-public-callables"

SUPPRESSION_SCAN_LINES = 20


def get_public_callables(source: str) -> list[str]:
    """Return names of top-level public callables in *source*."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    names: list[str] = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(
            node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
        ) and not node.name.startswith("_"):
            names.append(node.name)
    return names


def has_suppression_comment(source: str) -> bool:
    """Check whether *source* opts out via suppression comment in the first N lines."""
    for i, line in enumerate(source.splitlines()):
        if i >= SUPPRESSION_SCAN_LINES:
            break
        if SUPPRESSION_COMMENT in line:
            return True
    return False


def is_exempt(path: Path) -> bool:
    """Return True if *path* should be skipped by convention."""
    if path.name in EXEMPT_FILENAMES:
        return True
    if path.name.endswith("_test.py"):
        return True
    return any(part in EXEMPT_DIRS for part in path.parts)


def check_directory(root: Path) -> dict[Path, list[str]]:
    """Walk *root* and return a mapping of violating files to their public callables."""
    violations: dict[Path, list[str]] = {}
    for py_file in sorted(root.rglob("*.py")):
        rel = py_file.relative_to(root)
        if is_exempt(rel):
            continue

        source = py_file.read_text()
        if has_suppression_comment(source):
            continue

        callables = get_public_callables(source)
        if len(callables) > 1:
            violations[rel] = callables

    return violations


def format_violations(violations: dict[Path, list[str]]) -> str:
    """Format violation map into a human-readable report."""
    lines: list[str] = []
    for path, names in violations.items():
        lines.append(f"  {path}: {', '.join(names)}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check one-public-callable-per-file convention.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("skillet"),
        help="Root directory to check (default: skillet/)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show all files, not just violations",
    )
    args = parser.parse_args()

    if not args.root.is_dir():
        print(f"Error: {args.root} is not a directory", file=sys.stderr)
        return 1

    violations = check_directory(args.root)

    if args.verbose:
        for py_file in sorted(args.root.rglob("*.py")):
            rel = py_file.relative_to(args.root)
            if is_exempt(rel):
                status = "skip"
            elif has_suppression_comment(py_file.read_text()):
                status = "suppressed"
            else:
                callables = get_public_callables(py_file.read_text())
                status = f"ok ({len(callables)})" if len(callables) <= 1 else "VIOLATION"
            print(f"  {rel}: {status}")

    if violations:
        print(f"Found {len(violations)} file(s) with multiple public callables:")
        print(format_violations(violations))
        print(f"\nAdd '{SUPPRESSION_COMMENT}' to opt out, or split the file.")
        return 1

    print("All files follow one-public-callable-per-file convention.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
