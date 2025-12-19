"""Tests for errors module."""

import pytest

from skillet.errors import (
    EmptyFolderError,
    EvalError,
    EvalValidationError,
    SkillError,
    SkilletError,
)


def describe_exception_hierarchy():
    """Tests for exception class hierarchy."""

    def it_has_skillet_error_as_base():
        assert issubclass(EvalError, SkilletError)
        assert issubclass(SkillError, SkilletError)

    def it_has_eval_error_subclasses():
        assert issubclass(EvalValidationError, EvalError)
        assert issubclass(EmptyFolderError, EvalError)

    def it_can_catch_all_with_skillet_error():
        errors = [
            SkilletError("base"),
            EvalError("eval"),
            EvalValidationError("validation"),
            EmptyFolderError("empty"),
            SkillError("skill"),
        ]
        for error in errors:
            assert isinstance(error, SkilletError)


def describe_error_messages():
    """Tests for error message handling."""

    @pytest.mark.parametrize(
        "error_class,message",
        [
            (SkilletError, "Base error message"),
            (EvalError, "Eval processing failed"),
            (EvalValidationError, "Missing required field: prompt"),
            (EmptyFolderError, "No evals found in /path/to/evals"),
            (SkillError, "Skill already exists"),
        ],
    )
    def it_preserves_error_messages(error_class, message):
        error = error_class(message)
        assert str(error) == message

    def it_can_be_raised_and_caught():
        with pytest.raises(EvalValidationError) as exc_info:
            raise EvalValidationError("test error")
        assert "test error" in str(exc_info.value)
