"""Tests for the evaluate function."""

from unittest.mock import AsyncMock, patch

import pytest

from skillet.eval.evaluate import evaluate

_EVAL = "skillet.eval.evaluate.evaluate"


def describe_evaluate():
    """Tests for evaluate function."""

    @pytest.mark.asyncio
    async def it_loads_evals_by_name():
        with (
            patch(f"{_EVAL}.load_evals") as mock_load,
            patch(f"{_EVAL}.run_single_eval", new_callable=AsyncMock) as mock_run,
        ):
            mock_load.return_value = [
                {"prompt": "p1", "expected": "e1", "_source": "test.md", "_content": "c1"}
            ]
            mock_run.return_value = {
                "pass": True,
                "cached": False,
                "eval_source": "test.md",
                "eval_idx": 0,
                "iteration": 1,
                "response": "r",
            }

            await evaluate("test-evals", samples=1)

            mock_load.assert_called_once_with("test-evals")

    @pytest.mark.asyncio
    async def it_calculates_pass_rate():
        with (
            patch(f"{_EVAL}.load_evals") as mock_load,
            patch(f"{_EVAL}.run_single_eval", new_callable=AsyncMock) as mock_run,
        ):
            mock_load.return_value = [
                {"prompt": "p1", "expected": "e1", "_source": "1.md", "_content": "c1"},
                {"prompt": "p2", "expected": "e2", "_source": "2.md", "_content": "c2"},
            ]
            # 1 pass, 1 fail
            mock_run.side_effect = [
                {
                    "pass": True,
                    "cached": False,
                    "eval_source": "1.md",
                    "eval_idx": 0,
                    "iteration": 1,
                    "response": "r1",
                },
                {
                    "pass": False,
                    "cached": False,
                    "eval_source": "2.md",
                    "eval_idx": 1,
                    "iteration": 1,
                    "response": "r2",
                },
            ]

            result = await evaluate("test-evals", samples=1)

            assert result.pass_rate == 50.0
            assert result.total_pass == 1
            assert result.total_runs == 2

    @pytest.mark.asyncio
    async def it_respects_max_evals():
        with (
            patch(f"{_EVAL}.load_evals") as mock_load,
            patch(f"{_EVAL}.run_single_eval", new_callable=AsyncMock) as mock_run,
            patch("random.sample") as mock_sample,
        ):
            evals = [
                {"prompt": f"p{i}", "expected": f"e{i}", "_source": f"{i}.md", "_content": f"c{i}"}
                for i in range(10)
            ]
            mock_load.return_value = evals
            mock_sample.return_value = evals[:2]
            mock_run.return_value = {
                "pass": True,
                "cached": False,
                "eval_source": "0.md",
                "eval_idx": 0,
                "iteration": 1,
                "response": "r",
            }

            result = await evaluate("test-evals", samples=1, max_evals=2)

            mock_sample.assert_called_once()
            assert result.sampled_evals == 2
            assert result.total_evals == 10

    @pytest.mark.asyncio
    async def it_skips_load_evals_when_evals_list_provided():
        with (
            patch(f"{_EVAL}.load_evals") as mock_load,
            patch(f"{_EVAL}.run_single_eval", new_callable=AsyncMock) as mock_run,
        ):
            evals = [{"prompt": "p1", "expected": "e1", "_source": "test.md", "_content": "c1"}]
            mock_run.return_value = {
                "pass": True,
                "cached": False,
                "eval_source": "test.md",
                "eval_idx": 0,
                "iteration": 1,
                "response": "r",
            }

            await evaluate("test-evals", samples=1, evals_list=evals)

            mock_load.assert_not_called()

    @pytest.mark.asyncio
    async def it_tracks_cached_vs_fresh_counts():
        with (
            patch(f"{_EVAL}.load_evals") as mock_load,
            patch(f"{_EVAL}.run_single_eval", new_callable=AsyncMock) as mock_run,
        ):
            mock_load.return_value = [
                {"prompt": "p1", "expected": "e1", "_source": "1.md", "_content": "c1"},
                {"prompt": "p2", "expected": "e2", "_source": "2.md", "_content": "c2"},
            ]
            mock_run.side_effect = [
                {
                    "pass": True,
                    "cached": True,
                    "eval_source": "1.md",
                    "eval_idx": 0,
                    "iteration": 1,
                    "response": "r1",
                },
                {
                    "pass": True,
                    "cached": False,
                    "eval_source": "2.md",
                    "eval_idx": 1,
                    "iteration": 1,
                    "response": "r2",
                },
            ]

            result = await evaluate("test-evals", samples=1)

            assert result.cached_count == 1
            assert result.fresh_count == 1

    @pytest.mark.asyncio
    async def it_includes_setup_in_task():
        with (
            patch(f"{_EVAL}.load_evals") as mock_load,
            patch(f"{_EVAL}.run_single_eval", new_callable=AsyncMock) as mock_run,
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
            mock_run.return_value = {
                "pass": True,
                "cached": False,
                "eval_source": "1.md",
                "eval_idx": 0,
                "iteration": 1,
                "response": "r",
            }

            await evaluate("test-evals", samples=1)

            call_args = mock_run.call_args
            task = call_args[0][0]
            assert task.get("setup") == "echo setup"

    @pytest.mark.asyncio
    async def it_includes_assertions_in_task():
        with (
            patch(f"{_EVAL}.load_evals") as mock_load,
            patch(f"{_EVAL}.run_single_eval", new_callable=AsyncMock) as mock_run,
        ):
            assertions = [{"type": "contains", "value": "hello"}]
            mock_load.return_value = [
                {
                    "prompt": "p1",
                    "expected": "e1",
                    "_source": "1.md",
                    "_content": "c1",
                    "assertions": assertions,
                }
            ]
            mock_run.return_value = {
                "pass": True,
                "cached": False,
                "eval_source": "1.md",
                "eval_idx": 0,
                "iteration": 1,
                "response": "r",
            }

            await evaluate("test-evals", samples=1)

            call_args = mock_run.call_args
            task = call_args[0][0]
            assert task.get("assertions") == assertions

    @pytest.mark.asyncio
    async def it_includes_teardown_in_task():
        with (
            patch(f"{_EVAL}.load_evals") as mock_load,
            patch(f"{_EVAL}.run_single_eval", new_callable=AsyncMock) as mock_run,
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
            mock_run.return_value = {
                "pass": True,
                "cached": False,
                "eval_source": "1.md",
                "eval_idx": 0,
                "iteration": 1,
                "response": "r",
            }

            await evaluate("test-evals", samples=1)

            call_args = mock_run.call_args
            task = call_args[0][0]
            assert task.get("teardown") == "echo teardown"
