"""Tests for run_sync/has_running_loop module."""

import pytest

from skillet._internal.run_sync.has_running_loop import has_running_loop


def describe_has_running_loop():
    def it_returns_false_from_sync_context():
        assert has_running_loop() is False

    @pytest.mark.asyncio
    async def it_returns_true_from_async_context():
        assert has_running_loop() is True
