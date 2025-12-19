"""Tests for skillet.optimize.metric."""

from unittest.mock import AsyncMock, patch

from skillet.optimize.metric import create_skillet_metric


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
