"""Parse a SKILL.md file into a SkillDocument."""

from pathlib import Path

from skillet.generate.analyze.parse_frontmatter import parse_frontmatter
from skillet.lint.types import SkillDocument


def parse_skill(path: Path) -> SkillDocument:
    """Read and parse a SKILL.md file into its frontmatter and body."""
    content = path.read_text()
    frontmatter, body = parse_frontmatter(content)
    return SkillDocument(path=path, content=content, frontmatter=frontmatter, body=body)
