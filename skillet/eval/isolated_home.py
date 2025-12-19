"""Context manager for isolated HOME directory."""

import os
import shutil
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def isolated_home() -> Generator[str, None, None]:
    """Context manager for isolated HOME directory.

    Creates a temporary HOME directory for isolated eval execution,
    and ensures cleanup after the eval completes.

    Symlinks ~/.claude to the isolated HOME so Claude CLI can find
    credentials while still isolating other HOME contents like ~/.skillet.

    Yields:
        Path to the temporary HOME directory
    """
    home_dir = tempfile.mkdtemp(prefix="skillet-eval-")
    real_home = os.environ.get("HOME", "")
    try:
        # Symlink ~/.claude for credentials
        real_claude_dir = Path(real_home) / ".claude"
        if real_claude_dir.exists():
            isolated_claude_dir = Path(home_dir) / ".claude"
            isolated_claude_dir.symlink_to(real_claude_dir)
        yield home_dir
    finally:
        if Path(home_dir).exists():
            shutil.rmtree(home_dir, ignore_errors=True)
