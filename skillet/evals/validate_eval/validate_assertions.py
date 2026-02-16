"""Validate the assertions field of an eval."""

from typing import cast

from skillet.errors import EvalValidationError

VALID_ASSERTION_TYPES = {
    "contains",
    "not_contains",
    "regex",
    "starts_with",
    "ends_with",
    "tool_called",
    "tool_not_called",
}


def validate_assertions(assertions: list[object], source: str) -> None:
    """Validate each assertion has a valid type and value."""
    for i, raw_assertion in enumerate(assertions):
        if not isinstance(raw_assertion, dict):
            raise EvalValidationError(f"Eval {source}: assertion {i} must be a dictionary")

        assertion = cast(dict[str, object], raw_assertion)

        if "type" not in assertion:
            raise EvalValidationError(f"Eval {source}: assertion {i} missing required field 'type'")

        if assertion["type"] not in VALID_ASSERTION_TYPES:
            valid_str = ", ".join(sorted(VALID_ASSERTION_TYPES))
            raise EvalValidationError(
                f"Eval {source}: assertion {i} has invalid type '{assertion['type']}'. "
                f"Valid types: {valid_str}"
            )

        if "value" not in assertion:
            raise EvalValidationError(
                f"Eval {source}: assertion {i} missing required field 'value'"
            )
