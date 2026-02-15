"""Tests for evals/validate_eval module."""

import pytest

from skillet.errors import EvalValidationError
from skillet.evals.validate_eval import validate_eval


def describe_validate_eval():
    """Tests for validate_eval function."""

    def it_passes_for_valid_eval():
        eval_data = {
            "timestamp": "2024-01-01",
            "prompt": "test prompt",
            "expected": "expected response",
            "name": "test-eval",
        }
        # Should not raise
        validate_eval(eval_data, "test.yaml")

    def it_raises_for_non_dict():
        with pytest.raises(EvalValidationError, match="not a valid YAML dictionary"):
            validate_eval("not a dict", "test.yaml")  # type: ignore[arg-type]

    def it_raises_for_missing_fields():
        eval_data = {"prompt": "test"}  # missing timestamp, expected, name
        with pytest.raises(EvalValidationError, match="missing required fields"):
            validate_eval(eval_data, "test.yaml")

    def it_includes_missing_field_names_in_error():
        eval_data = {"prompt": "test", "timestamp": "2024-01-01"}
        with pytest.raises(EvalValidationError, match="expected") as exc_info:
            validate_eval(eval_data, "test.yaml")
        assert "name" in str(exc_info.value)
