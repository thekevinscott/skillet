"""Core types for the lint module."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class LintSeverity(Enum):
    """Severity level for lint findings."""

    ERROR = "error"  # Must fix
    WARNING = "warning"  # Should fix
    SUGGESTION = "suggestion"  # Consider


@dataclass
class LintFinding:
    """A single lint finding."""

    rule_id: str
    message: str
    severity: LintSeverity
    line: int | None = None
    suggestion: str | None = None


@dataclass
class LintResult:
    """Result of linting a skill file."""

    path: Path
    findings: list[LintFinding] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        """Count of ERROR severity findings."""
        return sum(1 for f in self.findings if f.severity == LintSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        """Count of WARNING severity findings."""
        return sum(1 for f in self.findings if f.severity == LintSeverity.WARNING)

    @property
    def suggestion_count(self) -> int:
        """Count of SUGGESTION severity findings."""
        return sum(1 for f in self.findings if f.severity == LintSeverity.SUGGESTION)


@dataclass
class SkillDocument:
    """Parsed SKILL.md document."""

    path: Path
    content: str
    frontmatter: dict | None
    body: str
    line_count: int
    frontmatter_end_line: int
