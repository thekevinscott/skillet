"""Iterative skill tuning using DSPy."""

from .result import EvalResult, RoundResult, TuneConfig, TuneResult
from .tune_dspy import tune_dspy

# tune is an alias for tune_dspy (the only implementation)
tune = tune_dspy

__all__ = [
    "EvalResult",
    "RoundResult",
    "TuneConfig",
    "TuneResult",
    "tune",
    "tune_dspy",
]
