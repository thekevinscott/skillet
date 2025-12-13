"""Load gaps from disk."""

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
    """Load all gap files for a skill from ~/.skillet/gaps/<name>/.

    Returns:
        List of gap dicts with _source and _content fields added

    Raises:
        GapError: If gaps directory doesn't exist, is empty, or contains invalid files
    """
    gaps_dir = SKILLET_DIR / "gaps" / name

    if not gaps_dir.exists():
        raise GapError(f"No gaps found for '{name}'. Expected: {gaps_dir}")

    if not gaps_dir.is_dir():
        raise GapError(f"Not a directory: {gaps_dir}")

    gaps = []
    for gap_file in sorted(gaps_dir.glob("*.yaml")):
        content = gap_file.read_text()
        gap = yaml.safe_load(content)
        validate_gap(gap, gap_file.name)
        gap["_source"] = gap_file.name
        gap["_content"] = content
        gaps.append(gap)

    if not gaps:
        raise GapError(f"No gap files found in {gaps_dir}")

    return gaps
