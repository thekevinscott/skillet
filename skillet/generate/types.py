"""Type definitions for the generate module."""

from dataclasses import dataclass, field
from pathlib import Path


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


@dataclass
class GenerateResult:
    """Result from generating evals for a skill."""

    skill_path: Path
    candidates: list[CandidateEval]
    analysis: dict = field(default_factory=dict)  # Extracted goals, prohibitions, etc.
