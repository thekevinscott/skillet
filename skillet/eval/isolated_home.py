"""Context manager for isolated HOME directory."""

import logging
import os
import shutil
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

    Copies only root-level *files* from ~/.claude (credentials, config)
    into the isolated HOME, without exposing subdirectories like
    commands/, agents/, or projects/.

    Yields:
        Path to the temporary HOME directory
    """
    real_home = os.environ.get("HOME", "")

    with tempfile.TemporaryDirectory(prefix="skillet-eval-") as home_dir:
        real_claude_dir = Path(real_home) / ".claude"
        if real_claude_dir.is_dir():
            isolated_claude_dir = Path(home_dir) / ".claude"
            isolated_claude_dir.mkdir()
            try:
                for item in real_claude_dir.iterdir():
                    if item.is_file():
                        shutil.copy2(item, isolated_claude_dir / item.name)
            except OSError as e:
                logger.warning(f"Could not copy .claude files: {e}")
        yield home_dir
