"""Iterative skill tuning using DSPy."""

from .dspy_tune import tune_dspy
from .result import EvalResult, RoundResult, TuneConfig, TuneResult

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
