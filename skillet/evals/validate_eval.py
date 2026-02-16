"""Validate eval file format."""

from typing import cast

from skillet.errors import EvalValidationError

# Required fields for a valid eval file
REQUIRED_EVAL_FIELDS = {"timestamp", "prompt", "expected", "name"}

VALID_ASSERTION_TYPES = {
    "contains",
    "not_contains",
    "regex",
    "starts_with",
    "ends_with",
    "tool_called",
    "tool_not_called",
}


def validate_eval(eval_data: dict, source: str) -> None:
    """Validate that an eval has all required fields."""
    if not isinstance(eval_data, dict):
        raise EvalValidationError(f"Eval {source} is not a valid YAML dictionary")

    missing = REQUIRED_EVAL_FIELDS - set(eval_data.keys())
    if missing:
        missing_str = ", ".join(sorted(missing))
        raise EvalValidationError(f"Eval {source} missing required fields: {missing_str}")

    if "assertions" in eval_data:
        raw = eval_data["assertions"]
        if not isinstance(raw, list):
            raise EvalValidationError(f"Eval {source}: 'assertions' must be a list")
        _validate_assertions(raw, source)


def _validate_assertions(assertions: list[object], source: str) -> None:
    """Validate the assertions field of an eval."""
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
