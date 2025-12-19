"""DSPy metric adapter for skillet's LLM-as-judge."""

from collections.abc import Callable
from typing import Any

from skillet._internal.async_utils import run_sync
from skillet.eval.judge import judge_response


def create_skillet_metric() -> Callable[..., float]:
    """Create a DSPy-compatible metric from skillet's judge.

    Returns a metric function that:
    - Takes (example, prediction, trace) as DSPy expects
    - Returns 1.0 for pass, 0.0 for fail
    - Bridges async judge_response to sync DSPy

    Example:
        metric = create_skillet_metric()
        score = metric(example, prediction, trace=None)
    """

    def metric(example: Any, pred: Any, _trace: Any = None) -> float:
        """Evaluate a prediction against expected behavior.

        Args:
            example: DSPy Example with 'prompt' and 'expected' fields
            pred: DSPy prediction with 'response' field
            trace: Optional trace for optimization (unused for now)

        Returns:
            1.0 if response meets expectations, 0.0 otherwise
        """
        # Extract fields from DSPy objects
        prompt = getattr(example, "prompt", "")
        expected = getattr(example, "expected", "")
        response = getattr(pred, "response", str(pred))
        tool_calls = getattr(pred, "tool_calls", [])

        # Bridge async to sync - run_sync handles both sync and async contexts
        judgment = run_sync(
            judge_response(
                prompt=prompt,
                response=response,
                expected=expected,
                tool_calls=tool_calls,
            )
        )

        return 1.0 if judgment["pass"] else 0.0

    return metric
