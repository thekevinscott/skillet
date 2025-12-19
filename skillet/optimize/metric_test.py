"""Tests for skillet.optimize.metric."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from skillet.optimize.metric import _run_async_in_thread, create_skillet_metric


def describe_create_skillet_metric():
    """Tests for create_skillet_metric function."""

    def it_returns_callable():
        """Should return a callable metric function."""
        metric = create_skillet_metric()
        assert callable(metric)

    @patch("skillet.optimize.metric.judge_response")
    def it_returns_1_when_judgment_passes(mock_judge: AsyncMock):
        """Should return 1.0 when judge_response passes."""
        mock_judge.return_value = {"pass": True, "reasoning": "Correct"}

        metric = create_skillet_metric()

        # Create mock DSPy objects
        class MockExample:
            prompt = "test prompt"
            expected = "test expected"

        class MockPrediction:
            response = "test response"
            tool_calls: list = []  # noqa: RUF012

        result = metric(MockExample(), MockPrediction())

        assert result == 1.0
        mock_judge.assert_called_once_with(
            prompt="test prompt",
            response="test response",
            expected="test expected",
            tool_calls=[],
        )

    @patch("skillet.optimize.metric.judge_response")
    def it_returns_0_when_judgment_fails(mock_judge: AsyncMock):
        """Should return 0.0 when judge_response fails."""
        mock_judge.return_value = {"pass": False, "reasoning": "Incorrect"}

        metric = create_skillet_metric()

        class MockExample:
            prompt = "test prompt"
            expected = "test expected"

        class MockPrediction:
            response = "wrong response"
            tool_calls: list = []  # noqa: RUF012

        result = metric(MockExample(), MockPrediction())

        assert result == 0.0

    @patch("skillet.optimize.metric.judge_response")
    def it_handles_missing_attributes(mock_judge: AsyncMock):
        """Should handle objects missing expected attributes."""
        mock_judge.return_value = {"pass": True, "reasoning": "OK"}

        metric = create_skillet_metric()

        # Objects without expected attributes
        class EmptyExample:
            pass

        class EmptyPrediction:
            pass

        result = metric(EmptyExample(), EmptyPrediction())

        assert result == 1.0
        # Should use empty strings for missing attributes
        # response falls back to str(pred) which includes class path
        call_kwargs = mock_judge.call_args.kwargs
        assert call_kwargs["prompt"] == ""
        assert call_kwargs["expected"] == ""
        assert call_kwargs["tool_calls"] == []
        assert "EmptyPrediction" in call_kwargs["response"]

    @patch("skillet.optimize.metric.judge_response")
    def it_accepts_trace_parameter(mock_judge: AsyncMock):
        """Should accept optional trace parameter (unused)."""
        mock_judge.return_value = {"pass": True, "reasoning": "OK"}

        metric = create_skillet_metric()

        class MockExample:
            prompt = "test"
            expected = "test"

        class MockPrediction:
            response = "test"

        # Should not raise with trace parameter
        result = metric(MockExample(), MockPrediction(), _trace={"some": "trace"})
        assert result == 1.0

    @patch("skillet.optimize.metric.judge_response")
    @pytest.mark.asyncio
    async def it_works_inside_async_context(mock_judge: AsyncMock):
        """Should work when called from within an async context.

        This tests the fix for issue #159 - asyncio.run() fails with
        'RuntimeError: This event loop is already running' when called
        from within an existing async context.
        """
        mock_judge.return_value = {"pass": True, "reasoning": "OK"}

        metric = create_skillet_metric()

        class MockExample:
            prompt = "test"
            expected = "test"

        class MockPrediction:
            response = "test"

        # This should NOT raise RuntimeError even though we're in an async context
        result = metric(MockExample(), MockPrediction())
        assert result == 1.0


def describe_run_async_in_thread():
    """Tests for _run_async_in_thread helper."""

    def it_runs_coroutine_and_returns_result():
        """Should run async coroutine and return its result."""

        async def sample_coro():
            return 42

        result = _run_async_in_thread(sample_coro())
        assert result == 42

    @pytest.mark.asyncio
    async def it_works_inside_async_context():
        """Should work when called from within an async context."""

        async def sample_coro():
            await asyncio.sleep(0.001)
            return "success"

        # This would fail with asyncio.run() but works with thread pool
        result = _run_async_in_thread(sample_coro())
        assert result == "success"

    def it_propagates_exceptions():
        """Should propagate exceptions from the coroutine."""

        async def failing_coro():
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            _run_async_in_thread(failing_coro())
