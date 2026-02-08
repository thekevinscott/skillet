"""Base class for lint rules."""

from abc import ABC, abstractmethod

from skillet.lint.types import LintFinding, SkillDocument


class LintRule(ABC):
    """A single lint rule that checks a SkillDocument for issues."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @abstractmethod
    def check(self, doc: SkillDocument) -> list[LintFinding]: ...
