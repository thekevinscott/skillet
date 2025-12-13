#!/usr/bin/env python3
"""Build .claude/ directory from .claude-template/ with variable substitution.

Usage:
    # Build with default ~/.skillet
    python scripts/build_claude_config.py

    # Build with custom skillet dir (for tests)
    python scripts/build_claude_config.py --skillet-dir /tmp/test-skillet

    # Build to custom output (for tests)
    python scripts/build_claude_config.py --output /tmp/test/.claude
"""

import argparse
import shutil
from pathlib import Path

DEFAULT_SKILLET_DIR = "~/.skillet"


def build_claude_config(
    template_dir: Path,
    output_dir: Path,
    skillet_dir: str = DEFAULT_SKILLET_DIR,
) -> None:
    """Render .claude-template to .claude with variable substitution.

    Only renders the commands/ subdirectory. Other files in .claude/
    (like CLAUDE.md) are kept as-is and checked into git.

    Args:
        template_dir: Path to .claude-template/
        output_dir: Path to output .claude/
        skillet_dir: Value to substitute for {{SKILLET_DIR}}
    """
    # Only clean the commands/ subdirectory, preserve other files like CLAUDE.md
    commands_output = output_dir / "commands"
    if commands_output.exists():
        shutil.rmtree(commands_output)

    # Walk template directory and copy/render files
    for template_file in template_dir.rglob("*"):
        if template_file.is_dir():
            continue

        # Compute output path
        relative_path = template_file.relative_to(template_dir)
        output_file = output_dir / relative_path
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Read, substitute, write
        content = template_file.read_text()
        content = content.replace("{{SKILLET_DIR}}", skillet_dir)
        output_file.write_text(content)


def main():
    parser = argparse.ArgumentParser(description="Build .claude/ from template")
    parser.add_argument(
        "--template",
        type=Path,
        default=Path(__file__).parent.parent / ".claude-template",
        help="Template directory (default: .claude-template/)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent.parent / ".claude",
        help="Output directory (default: .claude/)",
    )
    parser.add_argument(
        "--skillet-dir",
        type=str,
        default=DEFAULT_SKILLET_DIR,
        help=f"Skillet directory (default: {DEFAULT_SKILLET_DIR})",
    )
    args = parser.parse_args()

    build_claude_config(
        template_dir=args.template,
        output_dir=args.output,
        skillet_dir=args.skillet_dir,
    )
    print(f"Built {args.output} from {args.template}")


if __name__ == "__main__":
    main()
