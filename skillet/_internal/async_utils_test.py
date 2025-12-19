"""Tests for async_utils module."""

import asyncio

import pytest

from skillet._internal.async_utils import run_sync


def describe_run_sync():
    """Tests for run_sync function."""

    def it_runs_coroutine_from_sync_context():
        """Should run async coroutine and return its result."""

        async def sample_coro():
            return 42

        result = run_sync(sample_coro())
        assert result == 42

    def it_handles_coroutines_with_await():
        """Should handle coroutines that use await internally."""

        async def sample_coro():
            await asyncio.sleep(0.001)
            return "success"

        result = run_sync(sample_coro())
        assert result == "success"

    @pytest.mark.asyncio
    async def it_works_inside_async_context():
        """Should work when called from within an async context."""

        async def sample_coro():
            await asyncio.sleep(0.001)
            return "from async"

        # This would fail with plain asyncio.run() but works with run_sync
        result = run_sync(sample_coro())
        assert result == "from async"

    @pytest.mark.asyncio
    async def it_works_with_nested_async_calls():
        """Should work with nested async operations."""

        async def inner():
            return "inner result"

        async def outer():
            return await inner()

        result = run_sync(outer())
        assert result == "inner result"

    def it_propagates_exceptions():
        """Should propagate exceptions from the coroutine."""

        async def failing_coro():
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            run_sync(failing_coro())

    @pytest.mark.asyncio
    async def it_propagates_exceptions_from_async_context():
        """Should propagate exceptions when called from async context."""

        async def failing_coro():
            raise RuntimeError("async error")

        with pytest.raises(RuntimeError, match="async error"):
            run_sync(failing_coro())

    def it_returns_none_for_void_coroutines():
        """Should handle coroutines that return None."""

        async def void_coro():
            pass

        result = run_sync(void_coro())
        assert result is None
