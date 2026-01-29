"""Types for the SKILL.md linter."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class LintSeverity(Enum):
    """Severity level for lint findings."""

    WARNING = "warning"
    ERROR = "error"


@dataclass
class LintFinding:
    """A single lint finding."""

    rule: str
    message: str
    severity: LintSeverity
    line: int | None = None


@dataclass
class LintResult:
    """Result of linting a SKILL.md file."""

    path: Path
    findings: list[LintFinding] = field(default_factory=list)


@dataclass
class SkillDocument:
    """Parsed SKILL.md with frontmatter and body separated."""

    path: Path
    content: str
    frontmatter: dict
    body: str
