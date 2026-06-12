"""Validate eval file format."""

from skillet.errors import EvalValidationError

from .validate_assertions import validate_assertions

# Required fields for a valid eval file
REQUIRED_EVAL_FIELDS = {"timestamp", "prompt", "expected", "name"}


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
        validate_assertions(raw, source)
