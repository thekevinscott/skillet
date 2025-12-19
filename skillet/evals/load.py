"""Load evals from disk."""

from pathlib import Path

import yaml

from skillet.config import SKILLET_DIR
from skillet.errors import EmptyFolderError, EvalValidationError

# Required fields for a valid eval file
REQUIRED_EVAL_FIELDS = {"timestamp", "prompt", "expected", "name"}


def validate_eval(eval_data: dict, source: str) -> None:
    """Validate that an eval has all required fields.

    Args:
        eval_data: Parsed eval dictionary
        source: Source filename for error messages

    Raises:
        EvalValidationError: If required fields are missing or format is invalid
    """
    if not isinstance(eval_data, dict):
        raise EvalValidationError(f"Eval {source} is not a valid YAML dictionary")

    missing = REQUIRED_EVAL_FIELDS - set(eval_data.keys())
    if missing:
        missing_str = ", ".join(sorted(missing))
        raise EvalValidationError(f"Eval {source} missing required fields: {missing_str}")


def load_evals(name: str) -> list[dict]:
    """Load eval files for an eval set.

    Args:
        name: One of:
            - A name (looks in ~/.skillet/evals/<name>/)
            - A path to a directory (loads all .yaml files recursively)
            - A path to a single .yaml file

    Returns:
        List of eval dicts with _source and _content fields added

    Raises:
        EvalError: If evals directory doesn't exist, is empty, or contains invalid files
    """
    name_path = Path(name)

    # Handle single file case
    if name_path.is_file():
        if not name_path.suffix == ".yaml":
            raise EvalValidationError(f"Expected .yaml file, got: {name_path}")

        content = name_path.read_text()
        eval_data = yaml.safe_load(content)
        validate_eval(eval_data, name_path.name)
        eval_data["_source"] = name_path.name
        eval_data["_content"] = content
        return [eval_data]

    # Handle directory case
    evals_dir = name_path if name_path.is_dir() else SKILLET_DIR / "evals" / name

    if not evals_dir.exists():
        raise EmptyFolderError(f"No evals found for '{name}'. Expected: {evals_dir}")

    if not evals_dir.is_dir():
        raise EmptyFolderError(f"Not a directory: {evals_dir}")

    evals = []
    # Use rglob to recursively find all yaml files in subdirectories too
    for eval_file in sorted(evals_dir.rglob("*.yaml")):
        content = eval_file.read_text()
        eval_data = yaml.safe_load(content)
        # Use relative path from evals_dir as source for better identification
        relative_path = eval_file.relative_to(evals_dir)
        validate_eval(eval_data, str(relative_path))
        eval_data["_source"] = str(relative_path)
        eval_data["_content"] = content
        evals.append(eval_data)

    if not evals:
        raise EmptyFolderError(f"No eval files found in {evals_dir}")

    return evals
