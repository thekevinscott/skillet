"""Async utilities for bridging sync and async code."""

import asyncio
import concurrent.futures
from collections.abc import Coroutine
from typing import Any


def _has_running_loop() -> bool:
    """Check if there's a running event loop in the current thread."""
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False


def run_sync[T](coro: Coroutine[Any, Any, T]) -> T:
    """Run an async coroutine synchronously, even from within an async context.

    This function safely bridges async code to sync code by detecting whether
    we're already inside an async event loop. If so, it runs the coroutine
    in a separate thread with its own event loop to avoid the
    "RuntimeError: This event loop is already running" error.

    Args:
        coro: The coroutine to run

    Returns:
        The result of the coroutine

    Raises:
        Any exception raised by the coroutine

    Example:
        async def fetch_data():
            return await some_async_call()

        # Works from sync context
        result = run_sync(fetch_data())

        # Also works from async context
        async def main():
            result = run_sync(fetch_data())
    """
    if _has_running_loop():
        # Already in async context - run in separate thread with its own event loop
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, coro)  # type: ignore[arg-type]
            return future.result()  # type: ignore[return-value]
    else:
        # No running loop - safe to use asyncio.run()
        return asyncio.run(coro)
