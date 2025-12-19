"""Generate default output paths for tune results."""

from datetime import datetime
from pathlib import Path


def get_default_output_path(name: str) -> Path:
    """Generate default output path for tune results.

    Returns ~/.skillet/tunes/{eval_name}/{timestamp}.json
    """
    # Extract eval name from path if it's a path
    eval_name = Path(name).name if "/" in name or "\\" in name else name

    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    return Path.home() / ".skillet" / "tunes" / eval_name / f"{timestamp}.json"
