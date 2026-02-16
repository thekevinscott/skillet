"""Show result data structures."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class ShowEvalResult:
    """Per-eval show result."""

    source: str
    iterations: list[dict]
    pass_rate: float | None


@dataclass
class ShowResult:
    """Complete result of a show() call."""

    name: str
    evals: list[ShowEvalResult]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
