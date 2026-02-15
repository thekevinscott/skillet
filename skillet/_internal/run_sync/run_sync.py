"""Run an async coroutine synchronously, even from within an async context."""

import asyncio
import concurrent.futures
from collections.abc import Coroutine
from typing import Any

from .has_running_loop import has_running_loop


def run_sync[T](coro: Coroutine[Any, Any, T]) -> T:
    """Run an async coroutine synchronously, even from within an async context.

    This function safely bridges async code to sync code by detecting whether
    we're already inside an async event loop. If so, it runs the coroutine
    in a separate thread with its own event loop to avoid the
    "RuntimeError: This event loop is already running" error.
    """
    if has_running_loop():
        # Already in async context - run in separate thread with its own event loop
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, coro)  # type: ignore[arg-type]
            return future.result()  # type: ignore[return-value]
    else:
        # No running loop - safe to use asyncio.run()
        return asyncio.run(coro)
