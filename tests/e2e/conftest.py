"""E2E test configuration and fixtures."""

import sys
from collections.abc import Generator
from pathlib import Path

import pytest

# Add scripts to path for imports
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from build_claude_config import build_claude_config  # noqa: E402


def _template_mtime(template_dir: Path) -> float:
    """Get the most recent modification time of any file in template_dir."""
    mtimes = [f.stat().st_mtime for f in template_dir.rglob("*") if f.is_file()]
    return max(mtimes) if mtimes else 0


def _output_mtime(output_dir: Path) -> float:
    """Get the oldest modification time of any file in output_dir."""
    mtimes = [f.stat().st_mtime for f in output_dir.rglob("*") if f.is_file()]
    return min(mtimes) if mtimes else 0


def _ensure_claude_config_built():
    """Build .claude/commands/ from template if needed.

    Rebuilds if:
    - .claude/commands/ doesn't exist
    - Any template file is newer than the oldest output file
    """
    template_dir = REPO_ROOT / ".claude-template"
    output_dir = REPO_ROOT / ".claude"
    commands_dir = output_dir / "commands"

    if not template_dir.exists():
        return  # No template, nothing to build

    needs_build = not commands_dir.exists() or _template_mtime(template_dir) > _output_mtime(
        commands_dir
    )

    if needs_build:
        build_claude_config(template_dir, output_dir)
        print(f"Built {commands_dir} from {template_dir}")


# Auto-build on test collection
_ensure_claude_config_built()


@pytest.fixture
def skillet_env(tmp_path: Path) -> Generator[Path, None, None]:
    """Create an isolated skillet environment for testing.

    Builds .claude/commands/ from templates with SKILLET_DIR pointing to
    tmp_path/.skillet/. Returns the cwd to use for Conversation.

    Usage:
        from .helpers import Conversation, add_evals, list_evals

        async def test_something(skillet_env):
            add_evals(skillet_env, "browser-fallback", count=2)

            async with Conversation(cwd=str(skillet_env)) as chat:
                async with chat.turn("/skillet:add"):
                    chat.expect("expect")

            # Check saved evals
            evals = list_evals(skillet_env, "conventional-commits")
            assert len(evals) == 1
    """
    skillet_dir = tmp_path / ".skillet"
    skillet_dir.mkdir()

    # Build .claude/commands/ with custom SKILLET_DIR
    template_dir = REPO_ROOT / ".claude-template"
    output_dir = tmp_path / ".claude"
    build_claude_config(template_dir, output_dir, skillet_dir=str(skillet_dir))

    yield tmp_path
