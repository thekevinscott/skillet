"""Base class for lint rules."""

from abc import ABC, abstractmethod

from skillet.lint.types import LintFinding, SkillDocument

_DOCS_BASE = "https://skillet.run/guides/linting"

# Source: Anthropic's "The Complete Guide to Building Skills for Claude" (Jan 2026)
GUIDE_REFERENCE = "https://skillet.run/guide/skill-authoring"


class LintRule(ABC):
    """A single lint rule that checks a SkillDocument for issues."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @property
    def url(self) -> str:
        """URL to documentation for this rule."""
        return f"{_DOCS_BASE}#{self.name}"

    @abstractmethod
    def check(self, doc: SkillDocument) -> list[LintFinding]: ...


class AsyncLintRule(ABC):
    """A lint rule that requires async execution (e.g. LLM calls)."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @property
    def url(self) -> str:
        """URL to documentation for this rule."""
        return f"{_DOCS_BASE}#{self.name}"

    @abstractmethod
    async def check(self, doc: SkillDocument) -> list[LintFinding]: ...
