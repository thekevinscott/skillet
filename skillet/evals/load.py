"""Load evals from disk."""

from pathlib import Path

import yaml

from skillet import config
from skillet.errors import EmptyFolderError, EvalValidationError

from .validate_eval import validate_eval


def load_evals(name: str, skillet_dir: Path | None = None) -> list[dict]:
    """Load eval files for an eval set.

    Args:
        name: One of:
            - A name (looks in ``<skillet_dir>/evals/<name>/``)
            - A path to a directory (loads all .yaml files recursively)
            - A path to a single .yaml file
        skillet_dir: Root holding ``evals/`` when ``name`` is a bare name.
            Injected by entry points; when ``None`` it falls back to the
            configured ``SKILLET_DIR`` (the ``SKILLET_DIR`` env var, else
            ``~/.skillet``).

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
    root = skillet_dir if skillet_dir is not None else config.SKILLET_DIR
    evals_dir = name_path if name_path.is_dir() else root / "evals" / name

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
