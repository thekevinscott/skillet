"""Context manager for isolated HOME directory."""

import logging
import os
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)


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
    real_home = os.environ.get("HOME", "")

    with tempfile.TemporaryDirectory(prefix="skillet-eval-") as home_dir:
        # Symlink ~/.claude for credentials
        real_claude_dir = Path(real_home) / ".claude"
        if real_claude_dir.exists():
            isolated_claude_dir = Path(home_dir) / ".claude"
            try:
                isolated_claude_dir.symlink_to(real_claude_dir)
            except OSError as e:
                # Log warning but continue - eval might work without .claude
                logger.warning(f"Could not symlink .claude directory: {e}")
        yield home_dir
