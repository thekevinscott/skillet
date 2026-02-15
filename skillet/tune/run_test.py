"""Tests for run_tune_eval."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from skillet._internal.sdk import QueryResult
from skillet.tune.run import run_tune_eval


def describe_run_tune_eval():
    """Tests for run_tune_eval function."""

    @pytest.mark.asyncio
    async def it_calculates_pass_rate():
        with (
            patch("skillet.tune.run.run_prompt", new_callable=AsyncMock) as mock_run,
            patch("skillet.tune.run.judge_response", new_callable=AsyncMock) as mock_judge,
        ):
            mock_run.return_value = QueryResult(text="response", tool_calls=[])
            mock_judge.side_effect = [
                {"pass": True, "reasoning": "OK"},
                {"pass": False, "reasoning": "bad"},
            ]

            evals = [
                {"_source": "a.md", "_content": "c1", "prompt": "p1", "expected": "e1"},
                {"_source": "b.md", "_content": "c2", "prompt": "p2", "expected": "e2"},
            ]

            pass_rate, results = await run_tune_eval(evals, Path("/skill.md"), samples=1)

            assert pass_rate == 50.0
            assert len(results) == 2
            assert results[0]["pass"] is True
            assert results[1]["pass"] is False

    @pytest.mark.asyncio
    async def it_handles_multiple_samples():
        with (
            patch("skillet.tune.run.run_prompt", new_callable=AsyncMock) as mock_run,
            patch("skillet.tune.run.judge_response", new_callable=AsyncMock) as mock_judge,
        ):
            mock_run.return_value = QueryResult(text="response", tool_calls=[])
            mock_judge.return_value = {"pass": True, "reasoning": "OK"}

            evals = [{"_source": "a.md", "_content": "c", "prompt": "p", "expected": "e"}]

            pass_rate, results = await run_tune_eval(evals, Path("/skill.md"), samples=3)

            assert len(results) == 3
            assert pass_rate == 100.0

    @pytest.mark.asyncio
    async def it_calls_status_callback():
        status_calls = []

        async def on_status(task, state, _result):
            status_calls.append((task["eval_source"], state))

        with (
            patch("skillet.tune.run.run_prompt", new_callable=AsyncMock) as mock_run,
            patch("skillet.tune.run.judge_response", new_callable=AsyncMock) as mock_judge,
        ):
            mock_run.return_value = QueryResult(text="response", tool_calls=[])
            mock_judge.return_value = {"pass": True, "reasoning": "OK"}

            evals = [{"_source": "test.md", "_content": "c", "prompt": "p", "expected": "e"}]

            await run_tune_eval(evals, Path("/skill.md"), samples=1, on_status=on_status)

            assert ("test.md", "running") in status_calls
            assert ("test.md", "done") in status_calls

    @pytest.mark.asyncio
    async def it_handles_exceptions():
        with (
            patch("skillet.tune.run.run_prompt", new_callable=AsyncMock) as mock_run,
        ):
            mock_run.side_effect = RuntimeError("network error")

            evals = [{"_source": "test.md", "_content": "c", "prompt": "p", "expected": "e"}]

            pass_rate, results = await run_tune_eval(evals, Path("/skill.md"), samples=1)

            assert pass_rate == 0.0
            assert results[0]["pass"] is False
            assert "network error" in results[0]["response"]

    @pytest.mark.asyncio
    async def it_calls_status_callback_on_exception():
        """Test that on_status is called even when an exception occurs."""
        status_calls = []

        async def on_status(task, state, result):
            status_calls.append((task["eval_source"], state, result))

        with (
            patch("skillet.tune.run.run_prompt", new_callable=AsyncMock) as mock_run,
        ):
            mock_run.side_effect = RuntimeError("network error")

            evals = [{"_source": "test.md", "_content": "c", "prompt": "p", "expected": "e"}]

            await run_tune_eval(evals, Path("/skill.md"), samples=1, on_status=on_status)

            # Should have both running and done calls
            assert ("test.md", "running", None) in status_calls
            # done call should have the error result
            done_calls = [c for c in status_calls if c[1] == "done"]
            assert len(done_calls) == 1
            assert done_calls[0][2]["pass"] is False
