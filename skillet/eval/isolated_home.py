"""Context manager for isolated HOME directory."""

import logging
import os
import shutil
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from skillet.agent import Agent

logger = logging.getLogger(__name__)


@contextmanager
def isolated_home(agent: Agent) -> Generator[str, None, None]:
    """Context manager for an isolated HOME directory for one eval.

    Creates a temporary HOME for isolated eval execution and cleans it up
    afterwards. Copies only root-level *files* from the agent's config dir
    (``~/.claude`` for claude, ``~/.codex`` for codex) — credentials and config —
    without exposing subdirectories like ``commands/``, ``agents/``, ``sessions/``,
    or ``projects/``.

    Args:
        agent: The agent under test; selects which ``~/<dot_dir>`` to copy.

    Yields:
        Path to the temporary HOME directory
    """
    real_home = os.environ.get("HOME", "")
    dot_dir = agent.dot_dir

    with tempfile.TemporaryDirectory(prefix="skillet-eval-") as home_dir:
        real_config_dir = Path(real_home) / dot_dir
        if real_config_dir.is_dir():
            isolated_config_dir = Path(home_dir) / dot_dir
            isolated_config_dir.mkdir()
            try:
                for item in real_config_dir.iterdir():
                    if item.is_file():
                        shutil.copy2(item, isolated_config_dir / item.name)
            except OSError as e:
                logger.warning(f"Could not copy {dot_dir} files: {e}")
        yield home_dir
