"""Tests for skillet.optimize.loaders."""

import dspy

from skillet.optimize.loaders import evals_to_trainset


def describe_evals_to_trainset():
    """Tests for evals_to_trainset function."""

    def it_returns_list_of_dspy_examples():
        """Should return a list of DSPy Examples."""
        evals = [{"prompt": "test prompt", "expected": "test expected", "_source": "test.yaml"}]

        result = evals_to_trainset(evals)

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], dspy.Example)

    def it_sets_prompt_and_expected_fields():
        """Should set prompt and expected fields on Examples."""
        evals = [{"prompt": "What is 2+2?", "expected": "4", "_source": "math.yaml"}]

        result = evals_to_trainset(evals)

        assert result[0].prompt == "What is 2+2?"
        assert result[0].expected == "4"

    def it_marks_prompt_as_input():
        """Should mark prompt as the input field."""
        evals = [{"prompt": "test", "expected": "test", "_source": "test.yaml"}]

        result = evals_to_trainset(evals)

        # DSPy Examples with inputs have _input_keys set
        input_keys = result[0]._input_keys
        assert input_keys is not None
        assert "prompt" in input_keys

    def it_handles_multiple_evals():
        """Should convert multiple evals to Examples."""
        evals = [
            {"prompt": "p1", "expected": "e1", "_source": "1.yaml"},
            {"prompt": "p2", "expected": "e2", "_source": "2.yaml"},
            {"prompt": "p3", "expected": "e3", "_source": "3.yaml"},
        ]

        result = evals_to_trainset(evals)

        assert len(result) == 3
        assert result[0].prompt == "p1"
        assert result[1].prompt == "p2"
        assert result[2].prompt == "p3"

    def it_handles_empty_evals():
        """Should return empty list for empty evals."""
        result = evals_to_trainset([])

        assert result == []
