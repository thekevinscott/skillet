"""Type definitions for the analyze module."""

from dataclasses import dataclass, field
from pathlib import Path


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
