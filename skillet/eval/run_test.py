"""Tests for eval/run module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from skillet._internal.sdk import QueryResult
from skillet.eval.run import evaluate, isolated_home, run_prompt, run_script, run_single_eval


def describe_isolated_home():
    """Tests for isolated_home context manager."""

    def it_creates_temp_directory():
        with isolated_home() as home_dir:
            assert Path(home_dir).exists()
            assert Path(home_dir).is_dir()
            assert "skillet-eval-" in home_dir

    def it_cleans_up_after_context():
        with isolated_home() as home_dir:
            temp_path = Path(home_dir)
        # After context exits, directory should be gone
        assert not temp_path.exists()

    def it_symlinks_claude_dir_if_exists():
        with tempfile.TemporaryDirectory() as fake_home:
            # Create a fake .claude directory
            claude_dir = Path(fake_home) / ".claude"
            claude_dir.mkdir()
            (claude_dir / "config.json").write_text("{}")

            original_home = os.environ.get("HOME", "")
            try:
                os.environ["HOME"] = fake_home
                with isolated_home() as home_dir:
                    isolated_claude = Path(home_dir) / ".claude"
                    assert isolated_claude.exists()
                    assert isolated_claude.is_symlink()
                    assert isolated_claude.resolve() == claude_dir.resolve()
            finally:
                os.environ["HOME"] = original_home


def describe_run_script():
    """Tests for run_script function."""

    def it_runs_simple_script():
        with tempfile.TemporaryDirectory() as home_dir:
            returncode, stdout, _stderr = run_script("echo hello", home_dir)
            assert returncode == 0
            assert "hello" in stdout

    def it_uses_provided_home_dir():
        with tempfile.TemporaryDirectory() as home_dir:
            returncode, stdout, _stderr = run_script("echo $HOME", home_dir)
            assert returncode == 0
            assert home_dir in stdout

    def it_captures_stderr():
        with tempfile.TemporaryDirectory() as home_dir:
            returncode, _stdout, stderr = run_script("echo error >&2", home_dir)
            assert returncode == 0
            assert "error" in stderr

    def it_returns_nonzero_for_failed_script():
        with tempfile.TemporaryDirectory() as home_dir:
            returncode, _stdout, _stderr = run_script("exit 1", home_dir)
            assert returncode == 1

    def it_uses_cwd_when_provided():
        with (
            tempfile.TemporaryDirectory() as home_dir,
            tempfile.TemporaryDirectory() as cwd,
        ):
            returncode, stdout, _stderr = run_script("pwd", home_dir, cwd)
            assert returncode == 0
            assert cwd in stdout


def describe_run_prompt():
    """Tests for run_prompt function."""

    @pytest.mark.asyncio
    async def it_normalizes_string_prompt_to_list():
        with patch("skillet.eval.run.query_multiturn", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = QueryResult(text="response", tool_calls=[])

            await run_prompt("single prompt")

            mock_query.assert_called_once()
            # First positional arg should be a list
            call_args = mock_query.call_args
            assert call_args[0][0] == ["single prompt"]

    @pytest.mark.asyncio
    async def it_passes_list_prompts_unchanged():
        with patch("skillet.eval.run.query_multiturn", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = QueryResult(text="response", tool_calls=[])

            await run_prompt(["first", "second"])

            call_args = mock_query.call_args
            assert call_args[0][0] == ["first", "second"]

    @pytest.mark.asyncio
    async def it_sets_cwd_from_skill_path():
        with patch("skillet.eval.run.query_multiturn", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = QueryResult(text="response", tool_calls=[])

            skill_path = Path("/project/.claude/skills/test")
            await run_prompt("test", skill_path=skill_path)

            call_args = mock_query.call_args
            assert call_args[1]["cwd"] == "/project"

    @pytest.mark.asyncio
    async def it_adds_skill_tool_when_skill_path_provided():
        with patch("skillet.eval.run.query_multiturn", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = QueryResult(text="response", tool_calls=[])

            skill_path = Path("/project/.claude/skills/test")
            await run_prompt("test", skill_path=skill_path, allowed_tools=["Read"])

            call_args = mock_query.call_args
            assert "Skill" in call_args[1]["allowed_tools"]
            assert "Read" in call_args[1]["allowed_tools"]

    @pytest.mark.asyncio
    async def it_uses_default_tools_when_none_provided():
        with patch("skillet.eval.run.query_multiturn", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = QueryResult(text="response", tool_calls=[])

            skill_path = Path("/project/.claude/skills/test")
            await run_prompt("test", skill_path=skill_path)

            call_args = mock_query.call_args
            # Should have tools from DEFAULT_SKILL_TOOLS
            assert call_args[1]["allowed_tools"] is not None

    @pytest.mark.asyncio
    async def it_sets_custom_home_dir():
        with (
            patch("skillet.eval.run.query_multiturn", new_callable=AsyncMock) as mock_query,
            tempfile.TemporaryDirectory() as home_dir,
        ):
            mock_query.return_value = QueryResult(text="response", tool_calls=[])

            await run_prompt("test", home_dir=home_dir)

            call_args = mock_query.call_args
            assert "env" in call_args[1]
            assert call_args[1]["env"]["HOME"] == home_dir

    @pytest.mark.asyncio
    async def it_handles_empty_response():
        with patch("skillet.eval.run.query_multiturn", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = QueryResult(text="", tool_calls=[])

            result = await run_prompt("test")

            assert "(no text response" in result.text


def describe_run_single_eval():
    """Tests for run_single_eval function."""

    @pytest.mark.asyncio
    async def it_returns_cached_result_when_available():
        with (
            patch("skillet.eval.run.get_cache_dir"),
            patch(
                "skillet.eval.run.get_cached_iterations",
                return_value=[{"pass": True, "response": "cached response"}],
            ),
        ):
            task = {
                "gap_source": "test.md",
                "gap_content": "content",
                "gap_idx": 0,
                "iteration": 1,
                "prompt": "test",
                "expected": "result",
            }

            result = await run_single_eval(task, "test-evals", None, None)

            assert result["cached"] is True
            assert result["response"] == "cached response"

    @pytest.mark.asyncio
    async def it_calls_status_callback_for_cached():
        status_calls = []

        async def on_status(_task, state, result):
            status_calls.append((state, result))

        with (
            patch("skillet.eval.run.get_cache_dir"),
            patch(
                "skillet.eval.run.get_cached_iterations",
                return_value=[{"pass": True, "response": "cached"}],
            ),
        ):
            task = {
                "gap_source": "test.md",
                "gap_content": "content",
                "gap_idx": 0,
                "iteration": 1,
                "prompt": "test",
                "expected": "result",
            }

            await run_single_eval(task, "test-evals", None, None, on_status=on_status)

            assert len(status_calls) == 1
            assert status_calls[0][0] == "cached"

    @pytest.mark.asyncio
    async def it_skips_cache_when_flag_set():
        with (
            patch("skillet.eval.run.get_cache_dir"),
            patch("skillet.eval.run.get_cached_iterations") as mock_cache,
            patch("skillet.eval.run.run_prompt", new_callable=AsyncMock) as mock_run,
            patch("skillet.eval.run.judge_response", new_callable=AsyncMock) as mock_judge,
            patch("skillet.eval.run.save_iteration"),
        ):
            mock_cache.return_value = [{"pass": True, "response": "cached"}]
            mock_run.return_value = QueryResult(text="fresh response", tool_calls=[])
            mock_judge.return_value = {"pass": True, "reasoning": "OK"}

            task = {
                "gap_source": "test.md",
                "gap_content": "content",
                "gap_idx": 0,
                "iteration": 1,
                "prompt": "test",
                "expected": "result",
            }

            result = await run_single_eval(task, "test-evals", None, None, skip_cache=True)

            assert result["cached"] is False
            assert result["response"] == "fresh response"

    @pytest.mark.asyncio
    async def it_handles_setup_script_failure():
        with (
            patch("skillet.eval.run.get_cache_dir"),
            patch("skillet.eval.run.get_cached_iterations", return_value=[]),
            patch("skillet.eval.run.run_script", return_value=(1, "", "setup failed")),
        ):
            task = {
                "gap_source": "test.md",
                "gap_content": "content",
                "gap_idx": 0,
                "iteration": 1,
                "prompt": "test",
                "expected": "result",
                "setup": "exit 1",
            }

            result = await run_single_eval(task, "test-evals", None, None)

            assert result["pass"] is False
            assert "Setup failed" in result["response"]

    @pytest.mark.asyncio
    async def it_runs_teardown_after_prompt():
        teardown_called = []

        def track_run_script(script, _home_dir, _cwd=None):
            if "teardown" in script:
                teardown_called.append(True)
            return (0, "", "")

        with (
            patch("skillet.eval.run.get_cache_dir"),
            patch("skillet.eval.run.get_cached_iterations", return_value=[]),
            patch("skillet.eval.run.run_script", side_effect=track_run_script),
            patch("skillet.eval.run.run_prompt", new_callable=AsyncMock) as mock_run,
            patch("skillet.eval.run.judge_response", new_callable=AsyncMock) as mock_judge,
            patch("skillet.eval.run.save_iteration"),
        ):
            mock_run.return_value = QueryResult(text="response", tool_calls=[])
            mock_judge.return_value = {"pass": True, "reasoning": "OK"}

            task = {
                "gap_source": "test.md",
                "gap_content": "content",
                "gap_idx": 0,
                "iteration": 1,
                "prompt": "test",
                "expected": "result",
                "teardown": "echo teardown",
            }

            await run_single_eval(task, "test-evals", None, None)

            assert len(teardown_called) == 1


def describe_evaluate():
    """Tests for evaluate function."""

    @pytest.mark.asyncio
    async def it_loads_evals_by_name():
        with (
            patch("skillet.eval.run.load_evals") as mock_load,
            patch("skillet.eval.run.run_single_eval", new_callable=AsyncMock) as mock_run,
        ):
            mock_load.return_value = [
                {"prompt": "p1", "expected": "e1", "_source": "test.md", "_content": "c1"}
            ]
            mock_run.return_value = {"pass": True, "cached": False}

            await evaluate("test-evals", samples=1)

            mock_load.assert_called_once_with("test-evals")

    @pytest.mark.asyncio
    async def it_calculates_pass_rate():
        with (
            patch("skillet.eval.run.load_evals") as mock_load,
            patch("skillet.eval.run.run_single_eval", new_callable=AsyncMock) as mock_run,
        ):
            mock_load.return_value = [
                {"prompt": "p1", "expected": "e1", "_source": "1.md", "_content": "c1"},
                {"prompt": "p2", "expected": "e2", "_source": "2.md", "_content": "c2"},
            ]
            # 1 pass, 1 fail
            mock_run.side_effect = [
                {"pass": True, "cached": False},
                {"pass": False, "cached": False},
            ]

            result = await evaluate("test-evals", samples=1)

            assert result["pass_rate"] == 50.0
            assert result["total_pass"] == 1
            assert result["total_runs"] == 2

    @pytest.mark.asyncio
    async def it_respects_max_gaps():
        with (
            patch("skillet.eval.run.load_evals") as mock_load,
            patch("skillet.eval.run.run_single_eval", new_callable=AsyncMock) as mock_run,
            patch("random.sample") as mock_sample,
        ):
            evals = [
                {"prompt": f"p{i}", "expected": f"e{i}", "_source": f"{i}.md", "_content": f"c{i}"}
                for i in range(10)
            ]
            mock_load.return_value = evals
            mock_sample.return_value = evals[:2]
            mock_run.return_value = {"pass": True, "cached": False}

            result = await evaluate("test-evals", samples=1, max_gaps=2)

            mock_sample.assert_called_once()
            assert result["sampled_gaps"] == 2
            assert result["total_gaps"] == 10

    @pytest.mark.asyncio
    async def it_tracks_cached_vs_fresh_counts():
        with (
            patch("skillet.eval.run.load_evals") as mock_load,
            patch("skillet.eval.run.run_single_eval", new_callable=AsyncMock) as mock_run,
        ):
            mock_load.return_value = [
                {"prompt": "p1", "expected": "e1", "_source": "1.md", "_content": "c1"},
                {"prompt": "p2", "expected": "e2", "_source": "2.md", "_content": "c2"},
            ]
            mock_run.side_effect = [
                {"pass": True, "cached": True},
                {"pass": True, "cached": False},
            ]

            result = await evaluate("test-evals", samples=1)

            assert result["cached_count"] == 1
            assert result["fresh_count"] == 1
