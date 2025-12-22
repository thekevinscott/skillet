"""Tests for eval/evaluate module."""

from contextlib import nullcontext
from unittest.mock import AsyncMock, patch

import pytest

from skillet._internal.sdk import QueryResult
from skillet.eval.evaluate import evaluate, run_single_eval


def describe_run_single_eval():
    """Tests for run_single_eval function."""

    @pytest.fixture(autouse=True)
    def mock_cache_lock():
        """Mock cache_lock to avoid creating MagicMock directories."""
        with patch("skillet.eval.evaluate.cache_lock", lambda _: nullcontext()):
            yield

    @pytest.fixture(autouse=True)
    def mock_cache_dir():
        """Mock get_cache_dir."""
        with patch("skillet.eval.evaluate.get_cache_dir"):
            yield

    @pytest.mark.asyncio
    async def it_returns_cached_result_when_available():
        with patch(
            "skillet.eval.evaluate.get_cached_iterations",
            return_value=[{"pass": True, "response": "cached response"}],
        ):
            task = {
                "eval_source": "test.md",
                "eval_content": "content",
                "eval_idx": 0,
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

        with patch(
            "skillet.eval.evaluate.get_cached_iterations",
            return_value=[{"pass": True, "response": "cached"}],
        ):
            task = {
                "eval_source": "test.md",
                "eval_content": "content",
                "eval_idx": 0,
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
            patch("skillet.eval.evaluate.get_cached_iterations") as mock_cache,
            patch("skillet.eval.evaluate.run_prompt", new_callable=AsyncMock) as mock_run,
            patch("skillet.eval.evaluate.judge_response", new_callable=AsyncMock) as mock_judge,
            patch("skillet.eval.evaluate.save_iteration"),
        ):
            mock_cache.return_value = [{"pass": True, "response": "cached"}]
            mock_run.return_value = QueryResult(text="fresh response", tool_calls=[])
            mock_judge.return_value = {"pass": True, "reasoning": "OK"}

            task = {
                "eval_source": "test.md",
                "eval_content": "content",
                "eval_idx": 0,
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
            patch("skillet.eval.evaluate.get_cached_iterations", return_value=[]),
            patch("skillet.eval.evaluate.run_script", return_value=(1, "", "setup failed")),
        ):
            task = {
                "eval_source": "test.md",
                "eval_content": "content",
                "eval_idx": 0,
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
            patch("skillet.eval.evaluate.get_cached_iterations", return_value=[]),
            patch("skillet.eval.evaluate.run_script", side_effect=track_run_script),
            patch("skillet.eval.evaluate.run_prompt", new_callable=AsyncMock) as mock_run,
            patch("skillet.eval.evaluate.judge_response", new_callable=AsyncMock) as mock_judge,
            patch("skillet.eval.evaluate.save_iteration"),
        ):
            mock_run.return_value = QueryResult(text="response", tool_calls=[])
            mock_judge.return_value = {"pass": True, "reasoning": "OK"}

            task = {
                "eval_source": "test.md",
                "eval_content": "content",
                "eval_idx": 0,
                "iteration": 1,
                "prompt": "test",
                "expected": "result",
                "teardown": "echo teardown",
            }

            await run_single_eval(task, "test-evals", None, None)

            assert len(teardown_called) == 1

    @pytest.mark.asyncio
    async def it_calls_status_callback_for_running():
        """Test that on_status is called with 'running' when not cached."""
        status_calls = []

        async def on_status(_task, state, result):
            status_calls.append((state, result))

        with (
            patch("skillet.eval.evaluate.get_cached_iterations", return_value=[]),
            patch("skillet.eval.evaluate.run_prompt", new_callable=AsyncMock) as mock_run,
            patch("skillet.eval.evaluate.judge_response", new_callable=AsyncMock) as mock_judge,
            patch("skillet.eval.evaluate.save_iteration"),
        ):
            mock_run.return_value = QueryResult(text="response", tool_calls=[])
            mock_judge.return_value = {"pass": True, "reasoning": "OK"}

            task = {
                "eval_source": "test.md",
                "eval_content": "content",
                "eval_idx": 0,
                "iteration": 1,
                "prompt": "test",
                "expected": "result",
            }

            await run_single_eval(task, "test-evals", None, None, on_status=on_status)

            assert ("running", None) in status_calls
            # Should also have a done call
            done_calls = [c for c in status_calls if c[0] == "done"]
            assert len(done_calls) == 1

    @pytest.mark.asyncio
    async def it_calls_status_callback_on_setup_failure():
        """Test that on_status is called when setup script fails."""
        status_calls = []

        async def on_status(_task, state, result):
            status_calls.append((state, result))

        with (
            patch("skillet.eval.evaluate.get_cached_iterations", return_value=[]),
            patch("skillet.eval.evaluate.run_script", return_value=(1, "", "setup error")),
        ):
            task = {
                "eval_source": "test.md",
                "eval_content": "content",
                "eval_idx": 0,
                "iteration": 1,
                "prompt": "test",
                "expected": "result",
                "setup": "exit 1",
            }

            await run_single_eval(task, "test-evals", None, None, on_status=on_status)

            # Should have running and done calls
            assert ("running", None) in status_calls
            done_calls = [c for c in status_calls if c[0] == "done"]
            assert len(done_calls) == 1
            assert done_calls[0][1]["pass"] is False

    @pytest.mark.asyncio
    async def it_handles_exception_and_runs_teardown():
        """Test that teardown is called even when prompt raises exception."""
        run_script_calls = []

        def track_run_script(script, _home_dir, _cwd=None):
            run_script_calls.append(script)
            return (0, "", "")

        with (
            patch("skillet.eval.evaluate.get_cached_iterations", return_value=[]),
            patch("skillet.eval.evaluate.run_script", side_effect=track_run_script),
            patch("skillet.eval.evaluate.run_prompt", new_callable=AsyncMock) as mock_run,
        ):
            mock_run.side_effect = RuntimeError("prompt failed")

            task = {
                "eval_source": "test.md",
                "eval_content": "content",
                "eval_idx": 0,
                "iteration": 1,
                "prompt": "test",
                "expected": "result",
                "teardown": "echo cleanup",
            }

            result = await run_single_eval(task, "test-evals", None, None)

            assert result["pass"] is False
            assert "prompt failed" in result["response"]
            # Teardown should be called with the cleanup script
            assert "echo cleanup" in run_script_calls

    @pytest.mark.asyncio
    async def it_calls_status_callback_on_exception():
        """Test on_status is called with done when exception occurs."""
        status_calls = []

        async def on_status(_task, state, result):
            status_calls.append((state, result))

        with (
            patch("skillet.eval.evaluate.get_cached_iterations", return_value=[]),
            patch("skillet.eval.evaluate.run_prompt", new_callable=AsyncMock) as mock_run,
        ):
            mock_run.side_effect = RuntimeError("prompt failed")

            task = {
                "eval_source": "test.md",
                "eval_content": "content",
                "eval_idx": 0,
                "iteration": 1,
                "prompt": "test",
                "expected": "result",
            }

            await run_single_eval(task, "test-evals", None, None, on_status=on_status)

            # Should have running and done calls
            assert ("running", None) in status_calls
            done_calls = [c for c in status_calls if c[0] == "done"]
            assert len(done_calls) == 1
            assert done_calls[0][1]["pass"] is False
            assert "prompt failed" in done_calls[0][1]["response"]

    @pytest.mark.asyncio
    async def it_calculates_script_cwd_from_skill_path():
        """Test that script_cwd is derived from skill path."""
        from pathlib import Path

        script_cwd_captured = []

        def capture_run_script(_script, _home_dir, cwd=None):
            script_cwd_captured.append(cwd)
            return (0, "", "")

        with (
            patch("skillet.eval.evaluate.get_cached_iterations", return_value=[]),
            patch("skillet.eval.evaluate.run_script", side_effect=capture_run_script),
            patch("skillet.eval.evaluate.run_prompt", new_callable=AsyncMock) as mock_run,
            patch("skillet.eval.evaluate.judge_response", new_callable=AsyncMock) as mock_judge,
            patch("skillet.eval.evaluate.save_iteration"),
        ):
            mock_run.return_value = QueryResult(text="response", tool_calls=[])
            mock_judge.return_value = {"pass": True, "reasoning": "OK"}

            task = {
                "eval_source": "test.md",
                "eval_content": "content",
                "eval_idx": 0,
                "iteration": 1,
                "prompt": "test",
                "expected": "result",
                "setup": "echo setup",
            }

            skill_path = Path("/project/.claude/skills/test")
            await run_single_eval(task, "test-evals", skill_path, None)

            # cwd should be /project (parent of .claude)
            assert script_cwd_captured[0] == "/project"


def describe_evaluate():
    """Tests for evaluate function."""

    @pytest.mark.asyncio
    async def it_loads_evals_by_name():
        with (
            patch("skillet.eval.evaluate.load_evals") as mock_load,
            patch("skillet.eval.evaluate.run_single_eval", new_callable=AsyncMock) as mock_run,
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
            patch("skillet.eval.evaluate.load_evals") as mock_load,
            patch("skillet.eval.evaluate.run_single_eval", new_callable=AsyncMock) as mock_run,
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
    async def it_respects_max_evals():
        with (
            patch("skillet.eval.evaluate.load_evals") as mock_load,
            patch("skillet.eval.evaluate.run_single_eval", new_callable=AsyncMock) as mock_run,
            patch("random.sample") as mock_sample,
        ):
            evals = [
                {"prompt": f"p{i}", "expected": f"e{i}", "_source": f"{i}.md", "_content": f"c{i}"}
                for i in range(10)
            ]
            mock_load.return_value = evals
            mock_sample.return_value = evals[:2]
            mock_run.return_value = {"pass": True, "cached": False}

            result = await evaluate("test-evals", samples=1, max_evals=2)

            mock_sample.assert_called_once()
            assert result["sampled_evals"] == 2
            assert result["total_evals"] == 10

    @pytest.mark.asyncio
    async def it_tracks_cached_vs_fresh_counts():
        with (
            patch("skillet.eval.evaluate.load_evals") as mock_load,
            patch("skillet.eval.evaluate.run_single_eval", new_callable=AsyncMock) as mock_run,
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

    @pytest.mark.asyncio
    async def it_includes_setup_in_task():
        with (
            patch("skillet.eval.evaluate.load_evals") as mock_load,
            patch("skillet.eval.evaluate.run_single_eval", new_callable=AsyncMock) as mock_run,
        ):
            mock_load.return_value = [
                {
                    "prompt": "p1",
                    "expected": "e1",
                    "_source": "1.md",
                    "_content": "c1",
                    "setup": "echo setup",
                }
            ]
            mock_run.return_value = {"pass": True, "cached": False}

            await evaluate("test-evals", samples=1)

            # Check that task includes setup
            call_args = mock_run.call_args
            task = call_args[0][0]
            assert task.get("setup") == "echo setup"

    @pytest.mark.asyncio
    async def it_includes_teardown_in_task():
        with (
            patch("skillet.eval.evaluate.load_evals") as mock_load,
            patch("skillet.eval.evaluate.run_single_eval", new_callable=AsyncMock) as mock_run,
        ):
            mock_load.return_value = [
                {
                    "prompt": "p1",
                    "expected": "e1",
                    "_source": "1.md",
                    "_content": "c1",
                    "teardown": "echo teardown",
                }
            ]
            mock_run.return_value = {"pass": True, "cached": False}

            await evaluate("test-evals", samples=1)

            # Check that task includes teardown
            call_args = mock_run.call_args
            task = call_args[0][0]
            assert task.get("teardown") == "echo teardown"


def describe_exception_handling():
    """Tests for exception handling in run_single_eval."""

    @pytest.fixture(autouse=True)
    def mock_cache_lock():
        """Mock cache_lock to avoid creating MagicMock directories."""
        with patch("skillet.eval.evaluate.cache_lock", lambda _: nullcontext()):
            yield

    @pytest.fixture(autouse=True)
    def mock_cache_dir():
        """Mock get_cache_dir."""
        with patch("skillet.eval.evaluate.get_cache_dir"):
            yield

    @pytest.mark.asyncio
    async def it_propagates_keyboard_interrupt():
        """KeyboardInterrupt should not be caught - let user cancel."""
        with (
            patch("skillet.eval.evaluate.get_cached_iterations", return_value=[]),
            patch("skillet.eval.evaluate.run_prompt", new_callable=AsyncMock) as mock_run,
        ):
            mock_run.side_effect = KeyboardInterrupt()

            task = {
                "eval_source": "test.md",
                "eval_content": "content",
                "eval_idx": 0,
                "iteration": 1,
                "prompt": "test",
                "expected": "result",
            }

            with pytest.raises(KeyboardInterrupt):
                await run_single_eval(task, "test-evals", None, None)

    @pytest.mark.asyncio
    async def it_propagates_system_exit():
        """SystemExit should not be caught - let process exit."""
        with (
            patch("skillet.eval.evaluate.get_cached_iterations", return_value=[]),
            patch("skillet.eval.evaluate.run_prompt", new_callable=AsyncMock) as mock_run,
        ):
            mock_run.side_effect = SystemExit(1)

            task = {
                "eval_source": "test.md",
                "eval_content": "content",
                "eval_idx": 0,
                "iteration": 1,
                "prompt": "test",
                "expected": "result",
            }

            with pytest.raises(SystemExit):
                await run_single_eval(task, "test-evals", None, None)

    @pytest.mark.asyncio
    async def it_runs_teardown_on_keyboard_interrupt():
        """Teardown should still run when KeyboardInterrupt is raised."""
        teardown_called = []

        def track_run_script(script, _home_dir, _cwd=None):
            if "teardown" in script:
                teardown_called.append(True)
            return (0, "", "")

        with (
            patch("skillet.eval.evaluate.get_cached_iterations", return_value=[]),
            patch("skillet.eval.evaluate.run_script", side_effect=track_run_script),
            patch("skillet.eval.evaluate.run_prompt", new_callable=AsyncMock) as mock_run,
        ):
            mock_run.side_effect = KeyboardInterrupt()

            task = {
                "eval_source": "test.md",
                "eval_content": "content",
                "eval_idx": 0,
                "iteration": 1,
                "prompt": "test",
                "expected": "result",
                "teardown": "echo teardown",
            }

            with pytest.raises(KeyboardInterrupt):
                await run_single_eval(task, "test-evals", None, None)

            assert len(teardown_called) == 1

    @pytest.mark.asyncio
    async def it_includes_exception_type_in_error_message():
        """Error message should include exception type for debugging."""
        with (
            patch("skillet.eval.evaluate.get_cached_iterations", return_value=[]),
            patch("skillet.eval.evaluate.run_prompt", new_callable=AsyncMock) as mock_run,
        ):
            mock_run.side_effect = ValueError("invalid value")

            task = {
                "eval_source": "test.md",
                "eval_content": "content",
                "eval_idx": 0,
                "iteration": 1,
                "prompt": "test",
                "expected": "result",
            }

            result = await run_single_eval(task, "test-evals", None, None)

            assert result["pass"] is False
            assert "ValueError" in result["judgment"]["reasoning"]
            assert "invalid value" in result["judgment"]["reasoning"]
