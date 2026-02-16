"""Compare result data structures."""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class CompareEvalResult:
    """Per-eval comparison result."""

    source: str
    baseline: float | None
    skill: float | None


@dataclass
class CompareResult:
    """Complete result of a compare() call."""

    name: str
    skill_path: Path
    results: list[CompareEvalResult]
    overall_baseline: float | None
    overall_skill: float | None
    baseline_total: int
    baseline_pass: int
    skill_total: int
    skill_pass: int
    missing_baseline: list[str]
    missing_skill: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        d = asdict(self)
        d["skill_path"] = self.skill_path
        return d
