"""Static analysis of SKILL.md files."""

from pathlib import Path

from .extract_examples import extract_examples
from .extract_section_items import extract_section_items
from .parse_frontmatter import parse_frontmatter
from .types import SkillAnalysis


def analyze_skill(path: Path) -> SkillAnalysis:
    """Analyze a SKILL.md file to extract structured information."""
    content = path.read_text()

    # Parse frontmatter
    frontmatter, body = parse_frontmatter(content)

    analysis = SkillAnalysis(
        path=path,
        name=frontmatter.get("name"),
        description=frontmatter.get("description"),
        frontmatter=frontmatter,
        body=body,
    )

    # Extract goals section
    analysis.goals = extract_section_items(body, "goals")

    # Extract prohibitions section
    analysis.prohibitions = extract_section_items(body, "prohibitions")

    # Extract examples (code blocks after "Example" headers)
    analysis.examples = extract_examples(body)

    return analysis
