"""Load gaps from disk."""

from pathlib import Path

import yaml

from skillet.config import SKILLET_DIR
from skillet.errors import EvalError

# Required fields for a valid gap file
REQUIRED_GAP_FIELDS = {"timestamp", "prompt", "expected", "name"}


def validate_eval(eval_data: dict, source: str) -> None:
    """Validate that an eval has all required fields.

    Args:
        eval_data: Parsed eval dictionary
        source: Source filename for error messages

    Raises:
        EvalError: If required fields are missing
    """
    if not isinstance(eval_data, dict):
        raise EvalError(f"Eval {source} is not a valid YAML dictionary")

    missing = REQUIRED_GAP_FIELDS - set(eval_data.keys())
    if missing:
        raise EvalError(f"Eval {source} missing required fields: {', '.join(sorted(missing))}")


def load_gaps(name: str) -> list[dict]:
    """Load all eval files for an eval set.

    Args:
        name: Either a name (looks in ~/.skillet/evals/<name>/) or a path to a directory

    Returns:
        List of eval dicts with _source and _content fields added

    Raises:
        EvalError: If evals directory doesn't exist, is empty, or contains invalid files
    """
    name_path = Path(name)
    evals_dir = name_path if name_path.is_dir() else SKILLET_DIR / "evals" / name

    if not evals_dir.exists():
        raise EvalError(f"No evals found for '{name}'. Expected: {evals_dir}")

    if not evals_dir.is_dir():
        raise EvalError(f"Not a directory: {evals_dir}")

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
        raise EvalError(f"No eval files found in {evals_dir}")

    return evals
