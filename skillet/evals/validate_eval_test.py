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

    def it_passes_with_valid_assertions():
        eval_data = {
            "timestamp": "2024-01-01",
            "prompt": "test",
            "expected": "expected",
            "name": "test",
            "assertions": [{"type": "contains", "value": "hello"}],
        }
        validate_eval(eval_data, "test.yaml")

    def it_raises_for_non_list_assertions():
        eval_data = {
            "timestamp": "2024-01-01",
            "prompt": "test",
            "expected": "expected",
            "name": "test",
            "assertions": "not a list",
        }
        with pytest.raises(EvalValidationError, match="must be a list"):
            validate_eval(eval_data, "test.yaml")

    def it_raises_for_assertion_missing_type():
        eval_data = {
            "timestamp": "2024-01-01",
            "prompt": "test",
            "expected": "expected",
            "name": "test",
            "assertions": [{"value": "hello"}],
        }
        with pytest.raises(EvalValidationError, match="missing required field 'type'"):
            validate_eval(eval_data, "test.yaml")

    def it_raises_for_assertion_missing_value():
        eval_data = {
            "timestamp": "2024-01-01",
            "prompt": "test",
            "expected": "expected",
            "name": "test",
            "assertions": [{"type": "contains"}],
        }
        with pytest.raises(EvalValidationError, match="missing required field 'value'"):
            validate_eval(eval_data, "test.yaml")

    def it_raises_for_invalid_assertion_type():
        eval_data = {
            "timestamp": "2024-01-01",
            "prompt": "test",
            "expected": "expected",
            "name": "test",
            "assertions": [{"type": "invalid_type", "value": "x"}],
        }
        with pytest.raises(EvalValidationError, match="invalid type 'invalid_type'"):
            validate_eval(eval_data, "test.yaml")
