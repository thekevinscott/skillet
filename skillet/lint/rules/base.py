"""Base class for lint rules."""

from abc import ABC, abstractmethod

from skillet.lint.types import LintFinding, SkillDocument


class LintRule(ABC):
    """Base class for all lint rules."""

    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Unique identifier for this rule (e.g., 'frontmatter-valid')."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this rule checks."""
        ...

    @abstractmethod
    def check(self, doc: SkillDocument) -> list[LintFinding]:
        """Check a skill document and return any findings.

        Args:
            doc: The parsed skill document to check

        Returns:
            List of findings (empty if no issues found)
        """
        ...
