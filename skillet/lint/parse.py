"""Parse SKILL.md files for linting."""

from pathlib import Path

import yaml

from skillet.errors import SkillParseError

from .types import SkillDocument


def parse_skill(path: Path) -> SkillDocument:
    """Parse a SKILL.md file into a SkillDocument.

    Args:
        path: Path to the SKILL.md file

    Returns:
        Parsed SkillDocument

    Raises:
        SkillParseError: If the file cannot be read or parsed
    """
    if not path.exists():
        raise SkillParseError(f"File not found: {path}")

    if not path.is_file():
        raise SkillParseError(f"Not a file: {path}")

    content = path.read_text()
    lines = content.splitlines()
    line_count = len(lines)

    # Parse frontmatter if present
    frontmatter = None
    body = content
    frontmatter_end_line = 0

    if content.startswith("---"):
        # Find the closing ---
        end_idx = content.find("\n---", 3)
        if end_idx != -1:
            frontmatter_raw = content[4:end_idx]
            try:
                frontmatter = yaml.safe_load(frontmatter_raw)
            except yaml.YAMLError as e:
                raise SkillParseError(f"Invalid YAML frontmatter: {e}") from e

            # Body starts after the closing ---
            body_start = end_idx + 4  # Skip "\n---"
            if body_start < len(content) and content[body_start] == "\n":
                body_start += 1  # Skip optional newline after ---

            body = content[body_start:]

            # Count lines for frontmatter_end_line
            frontmatter_section = content[: end_idx + 4]
            frontmatter_end_line = frontmatter_section.count("\n") + 1

    return SkillDocument(
        path=path,
        content=content,
        frontmatter=frontmatter,
        body=body,
        line_count=line_count,
        frontmatter_end_line=frontmatter_end_line,
    )
