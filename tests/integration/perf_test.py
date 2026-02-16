"""Integration tests for performance invariants.

These tests enforce that performance optimizations remain in place:
- load_evals() called at most once per evaluate/tune invocation
- hash_directory() caches results across eval iterations
- --no-summary skips the summarize_responses LLM call
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from skillet import evaluate
from skillet._internal.cache.hash_directory import hash_directory
from skillet.cli.commands.eval.eval import eval_command

from .conftest import create_eval_file


def describe_load_evals_call_count():
    """Enforce that load_evals is called at most once per operation."""

    @pytest.mark.asyncio
    async def it_skips_load_evals_when_evals_list_provided(skillet_env: Path, mock_claude_query):
        """evaluate() with evals_list should not call load_evals."""
        evals_dir = skillet_env / ".skillet" / "evals" / "perf-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        from skillet.evals import load_evals

        evals = load_evals("perf-test")

        mock_claude_query.set_responses(
            "Response",
            {"pass": True, "reasoning": "OK"},
        )

        with patch("skillet.eval.evaluate.evaluate.load_evals") as spy:
            await evaluate(
                "perf-test",
                samples=1,
                parallel=1,
                skip_cache=True,
                evals_list=evals,
            )
            spy.assert_not_called()

    @pytest.mark.asyncio
    async def it_calls_load_evals_exactly_once_without_evals_list(
        skillet_env: Path, mock_claude_query
    ):
        """evaluate() without evals_list should call load_evals exactly once."""
        evals_dir = skillet_env / ".skillet" / "evals" / "once-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")
        create_eval_file(evals_dir / "002.yaml", prompt="Second prompt")

        mock_claude_query.set_responses(
            "Response 1",
            {"pass": True, "reasoning": "OK"},
            "Response 2",
            {"pass": True, "reasoning": "OK"},
        )

        with patch(
            "skillet.eval.evaluate.evaluate.load_evals",
            wraps=__import__("skillet.evals", fromlist=["load_evals"]).load_evals,
        ) as spy:
            await evaluate(
                "once-test",
                samples=1,
                parallel=1,
                skip_cache=True,
            )
            spy.assert_called_once()


def describe_hash_directory_caching():
    """Enforce that hash_directory() caches across eval iterations."""

    @pytest.mark.asyncio
    async def it_caches_hash_directory_across_samples(skillet_env: Path, mock_claude_query):
        """hash_directory should be called once per unique path, not per sample."""
        evals_dir = skillet_env / ".skillet" / "evals" / "hash-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        skill_dir = skillet_env / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# Test Skill\n")

        # 1 eval x 3 samples = 6 responses (3 prompts + 3 judgments)
        mock_claude_query.set_responses(
            "R1",
            {"pass": True, "reasoning": "OK"},
            "R2",
            {"pass": True, "reasoning": "OK"},
            "R3",
            {"pass": True, "reasoning": "OK"},
        )

        hash_directory.cache_clear()

        await evaluate(
            "hash-test",
            skill_path=skill_file,
            samples=3,
            parallel=1,
            skip_cache=True,
        )

        info = hash_directory.cache_info()
        # The skill path should be hashed once, then served from cache
        assert info.misses >= 1
        assert info.hits >= 2, f"Expected at least 2 cache hits for 3 samples, got {info.hits}"


def describe_no_summary_flag():
    """Enforce that --no-summary skips the summarize_responses LLM call."""

    @pytest.fixture(autouse=True)
    def mock_console():
        with patch("skillet.cli.commands.eval.eval.console"):
            yield

    @pytest.fixture(autouse=True)
    def mock_live_display():
        with patch("skillet.cli.commands.eval.eval.LiveDisplay") as mock_cls:
            mock_display = MagicMock()
            mock_display.start = AsyncMock()
            mock_display.stop = AsyncMock()
            mock_display.update = AsyncMock()
            mock_cls.return_value = mock_display
            yield

    @pytest.mark.asyncio
    async def it_skips_summarize_when_no_summary_is_true(skillet_env: Path, mock_claude_query):
        """eval_command with no_summary=True should not call summarize_responses."""
        evals_dir = skillet_env / ".skillet" / "evals" / "summary-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        # Make the eval fail so summarize would normally be called
        mock_claude_query.set_responses(
            "Bad response",
            {"pass": False, "reasoning": "Failed"},
        )

        with patch("skillet.cli.commands.eval.eval.summarize_responses") as mock_summarize:
            mock_summarize.return_value = "Summary text"
            await eval_command(
                "summary-test",
                samples=1,
                parallel=1,
                skip_cache=True,
                no_summary=True,
            )
            mock_summarize.assert_not_called()

    @pytest.mark.asyncio
    async def it_calls_summarize_when_no_summary_is_false(skillet_env: Path, mock_claude_query):
        """eval_command without no_summary should call summarize_responses on failures."""
        evals_dir = skillet_env / ".skillet" / "evals" / "summary-test-2"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        mock_claude_query.set_responses(
            "Bad response",
            {"pass": False, "reasoning": "Failed"},
        )

        with patch("skillet.cli.commands.eval.eval.summarize_responses") as mock_summarize:
            mock_summarize.return_value = "Summary text"
            await eval_command(
                "summary-test-2",
                samples=1,
                parallel=1,
                skip_cache=True,
            )
            mock_summarize.assert_called_once()
