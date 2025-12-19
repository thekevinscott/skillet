"""DSPy metric adapter for skillet's LLM-as-judge."""

import asyncio
import concurrent.futures
from collections.abc import Callable
from typing import Any

from skillet.eval.judge import judge_response


def _run_async_in_thread(coro):
    """Run an async coroutine in a new thread with its own event loop.

    This allows calling async code from sync contexts, even when
    already inside an async event loop (which would cause asyncio.run()
    to raise RuntimeError).
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(asyncio.run, coro)
        return future.result()


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

        coro = judge_response(
            prompt=prompt,
            response=response,
            expected=expected,
            tool_calls=tool_calls,
        )

        # Bridge async to sync - use thread pool to avoid "event loop already running"
        try:
            asyncio.get_running_loop()
            # Already in async context - run in separate thread
            judgment = _run_async_in_thread(coro)
        except RuntimeError:
            # No running loop - safe to use asyncio.run()
            judgment = asyncio.run(coro)

        return 1.0 if judgment["pass"] else 0.0

    return metric
