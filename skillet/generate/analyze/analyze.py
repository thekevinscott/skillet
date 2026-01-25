"""Static analysis of SKILL.md files."""

from dataclasses import dataclass, field
from pathlib import Path

from .extract_examples import extract_examples
from .extract_section_items import extract_section_items
from .parse_frontmatter import parse_frontmatter


@dataclass
class SkillAnalysis:
    """Results from analyzing a SKILL.md."""

    path: Path
    name: str | None = None
    description: str | None = None
    goals: list[str] = field(default_factory=list)
    prohibitions: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    frontmatter: dict = field(default_factory=dict)
    body: str = ""


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
