"""Check if there's a running event loop in the current thread."""

import asyncio


def has_running_loop() -> bool:
    """Check if there's a running event loop in the current thread."""
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False
