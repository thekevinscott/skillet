"""Load gaps from disk."""

from pathlib import Path

import yaml

from skillet.config import SKILLET_DIR
from skillet.errors import GapError

# Required fields for a valid gap file
REQUIRED_GAP_FIELDS = {"timestamp", "prompt", "expected", "name"}


def validate_gap(gap: dict, source: str) -> None:
    """Validate that a gap has all required fields.

    Args:
        gap: Parsed gap dictionary
        source: Source filename for error messages

    Raises:
        GapError: If required fields are missing
    """
    if not isinstance(gap, dict):
        raise GapError(f"Gap {source} is not a valid YAML dictionary")

    missing = REQUIRED_GAP_FIELDS - set(gap.keys())
    if missing:
        raise GapError(f"Gap {source} missing required fields: {', '.join(sorted(missing))}")


def load_gaps(name: str) -> list[dict]:
    """Load all gap files for a skill.

    Args:
        name: Either a name (looks in ~/.skillet/gaps/<name>/) or a path to a directory

    Returns:
        List of gap dicts with _source and _content fields added

    Raises:
        GapError: If gaps directory doesn't exist, is empty, or contains invalid files
    """
    name_path = Path(name)
    gaps_dir = name_path if name_path.is_dir() else SKILLET_DIR / "gaps" / name

    if not gaps_dir.exists():
        raise GapError(f"No gaps found for '{name}'. Expected: {gaps_dir}")

    if not gaps_dir.is_dir():
        raise GapError(f"Not a directory: {gaps_dir}")

    gaps = []
    # Use rglob to recursively find all yaml files in subdirectories too
    for gap_file in sorted(gaps_dir.rglob("*.yaml")):
        content = gap_file.read_text()
        gap = yaml.safe_load(content)
        # Use relative path from gaps_dir as source for better identification
        relative_path = gap_file.relative_to(gaps_dir)
        validate_gap(gap, str(relative_path))
        gap["_source"] = str(relative_path)
        gap["_content"] = content
        gaps.append(gap)

    if not gaps:
        raise GapError(f"No gap files found in {gaps_dir}")

    return gaps
