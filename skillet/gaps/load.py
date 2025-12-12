"""Load gaps from disk."""

import yaml

from skillet.config import SKILLET_DIR
from skillet.errors import GapError


def load_gaps(name: str) -> list[dict]:
    """Load all gap files for a skill from ~/.skillet/gaps/<name>/.

    Returns:
        List of gap dicts with _source and _content fields added
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
        gap["_source"] = gap_file.name
        gap["_content"] = content
        gaps.append(gap)

    if not gaps:
        raise GapError(f"No gap files found in {gaps_dir}")

    return gaps
