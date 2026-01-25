"""Parse YAML frontmatter from markdown content."""

import yaml


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from markdown content."""
    frontmatter: dict = {}
    body = content

    if not content.startswith("---"):
        return frontmatter, body

    end_idx = content.find("\n---", 3)
    if end_idx == -1:
        return frontmatter, body

    frontmatter_raw = content[4:end_idx]
    try:
        frontmatter = yaml.safe_load(frontmatter_raw) or {}
    except yaml.YAMLError:
        frontmatter = {}

    body_start = end_idx + 4
    if body_start < len(content) and content[body_start] == "\n":
        body_start += 1
    body = content[body_start:]

    return frontmatter, body
