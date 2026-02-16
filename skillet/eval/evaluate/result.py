"""Evaluate result data structures."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class IterationResult:
    """Result of a single eval iteration."""

    eval_idx: int
    eval_source: str
    iteration: int
    response: str
    passed: bool
    tool_calls: list[dict] | None = None
    judgment: dict | None = None
    cached: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary, mapping 'passed' back to 'pass' for JSON compat."""
        d = asdict(self)
        d["pass"] = d.pop("passed")
        return d


@dataclass
class PerEvalMetric:
    """Per-eval pass@k and pass^k metrics."""

    eval_source: str
    pass_at_k: float | None
    pass_pow_k: float | None
    k: int
    n: int
    c: int


@dataclass
class EvaluateResult:
    """Complete result of an evaluate() call."""

    results: list[IterationResult]
    tasks: list[dict]
    pass_rate: float
    total_runs: int
    total_pass: int
    cached_count: int
    fresh_count: int
    total_evals: int
    sampled_evals: int
    per_eval_metrics: list[PerEvalMetric]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "results": [r.to_dict() for r in self.results],
            "tasks": self.tasks,
            "pass_rate": self.pass_rate,
            "total_runs": self.total_runs,
            "total_pass": self.total_pass,
            "cached_count": self.cached_count,
            "fresh_count": self.fresh_count,
            "total_evals": self.total_evals,
            "sampled_evals": self.sampled_evals,
            "per_eval_metrics": [asdict(m) for m in self.per_eval_metrics],
        }
