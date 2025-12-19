"""Tests for skillet.optimize.loaders."""

from unittest.mock import patch

import dspy

from skillet.optimize.loaders import evals_to_trainset


def describe_evals_to_trainset():
    """Tests for evals_to_trainset function."""

    @patch("skillet.optimize.loaders.load_evals")
    def it_returns_list_of_dspy_examples(mock_load_evals):
        """Should return a list of DSPy Examples."""
        mock_load_evals.return_value = [
            {"prompt": "test prompt", "expected": "test expected", "_source": "test.yaml"}
        ]

        result = evals_to_trainset("test-evals")

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], dspy.Example)

    @patch("skillet.optimize.loaders.load_evals")
    def it_sets_prompt_and_expected_fields(mock_load_evals):
        """Should set prompt and expected fields on Examples."""
        mock_load_evals.return_value = [
            {"prompt": "What is 2+2?", "expected": "4", "_source": "math.yaml"}
        ]

        result = evals_to_trainset("math-evals")

        assert result[0].prompt == "What is 2+2?"
        assert result[0].expected == "4"

    @patch("skillet.optimize.loaders.load_evals")
    def it_marks_prompt_as_input(mock_load_evals):
        """Should mark prompt as the input field."""
        mock_load_evals.return_value = [
            {"prompt": "test", "expected": "test", "_source": "test.yaml"}
        ]

        result = evals_to_trainset("test")

        # DSPy Examples with inputs have _input_keys set
        input_keys = result[0]._input_keys
        assert input_keys is not None
        assert "prompt" in input_keys

    @patch("skillet.optimize.loaders.load_evals")
    def it_handles_multiple_evals(mock_load_evals):
        """Should convert multiple evals to Examples."""
        mock_load_evals.return_value = [
            {"prompt": "p1", "expected": "e1", "_source": "1.yaml"},
            {"prompt": "p2", "expected": "e2", "_source": "2.yaml"},
            {"prompt": "p3", "expected": "e3", "_source": "3.yaml"},
        ]

        result = evals_to_trainset("multi")

        assert len(result) == 3
        assert result[0].prompt == "p1"
        assert result[1].prompt == "p2"
        assert result[2].prompt == "p3"

    @patch("skillet.optimize.loaders.load_evals")
    def it_handles_empty_evals(mock_load_evals):
        """Should return empty list for empty evals."""
        mock_load_evals.return_value = []

        result = evals_to_trainset("empty")

        assert result == []

    @patch("skillet.optimize.loaders.load_evals")
    def it_passes_name_to_load_evals(mock_load_evals):
        """Should pass eval name to load_evals."""
        mock_load_evals.return_value = []

        evals_to_trainset("my-eval-set")

        mock_load_evals.assert_called_once_with("my-eval-set")
