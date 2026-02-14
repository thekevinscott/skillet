"""Type definitions for the generate module."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class EvalDomain(Enum):
    """The testing domain an eval targets."""

    TRIGGERING = "triggering"
    FUNCTIONAL = "functional"
    PERFORMANCE = "performance"


@dataclass
class CandidateEval:
    """A generated candidate eval."""

    prompt: str | list[str]
    expected: str
    name: str
    category: str  # "positive", "negative", "ambiguity"
    source: str  # "goal:1", "lint:vague-language:5", etc.
    confidence: float  # 0.0-1.0
    rationale: str
    domain: EvalDomain | None = None


@dataclass
class GenerateResult:
    """Result from generating evals for a skill."""

    skill_path: Path
    candidates: list[CandidateEval]
    analysis: dict = field(default_factory=dict)  # Extracted goals, prohibitions, etc.
