"""Tests for instruction proposer."""

from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest


@dataclass
class MockExample:
    """Mock training example."""

    prompt: str
    expected: str


@pytest.fixture(autouse=True)
def mock_get_claude_lm():
    """Mock get_claude_lm."""
    with patch("skillet.tune.proposer.get_claude_lm") as mock:
        mock.return_value = MagicMock()
        yield mock


@pytest.fixture(autouse=True)
def mock_dspy():
    """Mock dspy.context to avoid actual LM calls."""
    with patch("skillet.tune.proposer.dspy") as mock_dspy:
        # Mock the Predict result
        mock_result = MagicMock()
        mock_result.improved_instruction = "  Improved instruction  "
        mock_dspy.Predict.return_value.return_value = mock_result
        mock_dspy.context.return_value.__enter__ = MagicMock()
        mock_dspy.context.return_value.__exit__ = MagicMock()
        yield mock_dspy


def describe_propose_instruction():
    def it_returns_stripped_instruction(mock_dspy):
        from skillet.tune.proposer import propose_instruction

        result = propose_instruction(
            current_instruction="Be helpful",
            trainset=[],
            failures=[],
            instruction_history=[],
        )
        assert result == "Improved instruction"
        assert mock_dspy.context.called

    def it_formats_failures_summary(mock_dspy):
        from skillet.tune.proposer import propose_instruction

        failures = [
            {"prompt": "Q1", "expected": "A1", "response": "Wrong1"},
            {"prompt": "Q2", "expected": "A2", "response": "Wrong2"},
        ]

        propose_instruction(
            current_instruction="Test",
            trainset=[],
            failures=failures,
            instruction_history=[],
        )

        # Verify Predict was called with formatted failures
        call_kwargs = mock_dspy.Predict.return_value.call_args[1]
        assert "Q1" in call_kwargs["failures"]
        assert "A1" in call_kwargs["failures"]

    def it_formats_history_summary(mock_dspy):
        from skillet.tune.proposer import propose_instruction

        history = [
            {"instruction": "First try", "score": 0.5},
            {"instruction": "Second try", "score": 0.75},
        ]

        propose_instruction(
            current_instruction="Test",
            trainset=[],
            failures=[],
            instruction_history=history,
        )

        call_kwargs = mock_dspy.Predict.return_value.call_args[1]
        assert "50%" in call_kwargs["history"]
        assert "75%" in call_kwargs["history"]

    def it_formats_examples_summary(mock_dspy):
        from skillet.tune.proposer import propose_instruction

        trainset = [
            MockExample(prompt="Input 1", expected="Output 1"),
            MockExample(prompt="Input 2", expected="Output 2"),
        ]

        propose_instruction(
            current_instruction="Test",
            trainset=trainset,
            failures=[],
            instruction_history=[],
        )

        call_kwargs = mock_dspy.Predict.return_value.call_args[1]
        assert "Input 1" in call_kwargs["examples"]
        assert "Output 1" in call_kwargs["examples"]

    def it_limits_to_3_failures(mock_dspy):
        from skillet.tune.proposer import propose_instruction

        failures = [
            {"prompt": f"Q{i}", "expected": f"A{i}", "response": f"Wrong{i}"} for i in range(10)
        ]

        propose_instruction(
            current_instruction="Test",
            trainset=[],
            failures=failures,
            instruction_history=[],
        )

        call_kwargs = mock_dspy.Predict.return_value.call_args[1]
        # Should only have Q0, Q1, Q2 (first 3)
        assert "Q0" in call_kwargs["failures"]
        assert "Q2" in call_kwargs["failures"]
        assert "Q3" not in call_kwargs["failures"]

    def it_uses_dspy_context(mock_dspy):
        from skillet.tune.proposer import propose_instruction

        propose_instruction(
            current_instruction="Test",
            trainset=[],
            failures=[],
            instruction_history=[],
        )

        mock_dspy.context.assert_called_once()
