"""Tests for validate_assertions function."""

import pytest

from skillet.errors import EvalValidationError
from skillet.evals.validate_eval.validate_assertions import validate_assertions


def describe_validate_assertions():
    def it_passes_valid_assertions():
        validate_assertions([{"type": "contains", "value": "hello"}], "test.yaml")

    def it_raises_for_non_dict_assertion():
        with pytest.raises(EvalValidationError, match="must be a dictionary"):
            validate_assertions(["not a dict"], "test.yaml")

    def it_raises_for_missing_type():
        with pytest.raises(EvalValidationError, match="missing required field 'type'"):
            validate_assertions([{"value": "hello"}], "test.yaml")

    def it_raises_for_missing_value():
        with pytest.raises(EvalValidationError, match="missing required field 'value'"):
            validate_assertions([{"type": "contains"}], "test.yaml")

    def it_raises_for_invalid_type():
        with pytest.raises(EvalValidationError, match="invalid type 'invalid_type'"):
            validate_assertions([{"type": "invalid_type", "value": "x"}], "test.yaml")

    def it_validates_all_valid_types():
        valid_types = [
            "contains",
            "not_contains",
            "regex",
            "starts_with",
            "ends_with",
            "tool_called",
            "tool_not_called",
        ]
        for atype in valid_types:
            validate_assertions([{"type": atype, "value": "test"}], "test.yaml")

    def it_passes_empty_list():
        validate_assertions([], "test.yaml")
