"""Type definitions for the generate module."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class EvalDomain(Enum):
    """Testing domains for generated evals.

    Based on Anthropic's guide:
    - triggering: does the skill load at the right times?
    - functional: does the skill produce correct outputs?
    - performance: does the skill improve over baseline?
    """

    TRIGGERING = "triggering"
    FUNCTIONAL = "functional"
    PERFORMANCE = "performance"


ALL_DOMAINS: frozenset[EvalDomain] = frozenset(EvalDomain)


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
    domain: str = "functional"  # "triggering", "functional", "performance"


@dataclass
class SkippedDomain:
    """A domain the model couldn't generate viable evals for."""

    domain: str
    reason: str


@dataclass
class GenerateResult:
    """Result from generating evals for a skill."""

    skill_path: Path
    candidates: list[CandidateEval]
    analysis: dict = field(default_factory=dict)  # Extracted goals, prohibitions, etc.
    skipped_domains: list[SkippedDomain] = field(default_factory=list)
