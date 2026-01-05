"""Tests for tune/run module."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from skillet._internal.sdk import QueryResult
from skillet.tune.run import run_tune_eval, tune


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


def describe_tune():
    """Tests for tune function."""

    @pytest.mark.asyncio
    async def it_returns_tune_result_on_success():
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch("skillet.tune.run.load_evals") as mock_load,
            patch("skillet.tune.run.run_tune_eval", new_callable=AsyncMock) as mock_eval,
        ):
            skill_path = Path(tmpdir) / "SKILL.md"
            skill_path.write_text("# Original Skill")

            mock_load.return_value = [
                {"_source": "a.md", "_content": "c", "prompt": "p", "expected": "e"}
            ]
            # First round passes
            mock_eval.return_value = (
                100.0,
                [{"pass": True, "eval_source": "a.md", "judgment": {"reasoning": "OK"}}],
            )

            result = await tune("test-evals", skill_path, max_rounds=3)

            assert result.result.success is True
            assert result.result.rounds_completed == 1
            assert result.result.final_pass_rate == 100.0

    @pytest.mark.asyncio
    async def it_improves_skill_on_failure():
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch("skillet.tune.run.load_evals") as mock_load,
            patch("skillet.tune.run.run_tune_eval", new_callable=AsyncMock) as mock_eval,
            patch("skillet.tune.run.improve_skill", new_callable=AsyncMock) as mock_improve,
        ):
            skill_path = Path(tmpdir) / "SKILL.md"
            skill_path.write_text("# Original Skill")

            mock_load.return_value = [
                {"_source": "a.md", "_content": "c", "prompt": "p", "expected": "e"}
            ]
            # First round fails, second passes
            mock_eval.side_effect = [
                (50.0, [{"pass": False, "eval_source": "a.md", "judgment": {"reasoning": "bad"}}]),
                (100.0, [{"pass": True, "eval_source": "a.md", "judgment": {"reasoning": "OK"}}]),
            ]
            mock_improve.return_value = "# Improved Skill"

            result = await tune("test-evals", skill_path, max_rounds=3)

            mock_improve.assert_called_once()
            assert result.result.rounds_completed == 2

    @pytest.mark.asyncio
    async def it_respects_max_rounds():
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch("skillet.tune.run.load_evals") as mock_load,
            patch("skillet.tune.run.run_tune_eval", new_callable=AsyncMock) as mock_eval,
            patch("skillet.tune.run.improve_skill", new_callable=AsyncMock) as mock_improve,
        ):
            skill_path = Path(tmpdir) / "SKILL.md"
            skill_path.write_text("# Original Skill")

            mock_load.return_value = [
                {"_source": "a.md", "_content": "c", "prompt": "p", "expected": "e"}
            ]
            # Always fails
            mock_eval.return_value = (
                50.0,
                [{"pass": False, "eval_source": "a.md", "judgment": {"reasoning": "bad"}}],
            )
            mock_improve.return_value = "# Still Bad Skill"

            result = await tune("test-evals", skill_path, max_rounds=2)

            assert result.result.success is False
            assert result.result.rounds_completed == 2

    @pytest.mark.asyncio
    async def it_calls_callbacks():
        callbacks = {"round_start": [], "round_complete": [], "improving": [], "improved": []}

        async def on_round_start(r, _t):
            callbacks["round_start"].append(r)

        async def on_round_complete(r, _p, _res):
            callbacks["round_complete"].append(r)

        async def on_improving(tip):
            callbacks["improving"].append(tip)

        async def on_improved(_c):
            callbacks["improved"].append(True)

        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch("skillet.tune.run.load_evals") as mock_load,
            patch("skillet.tune.run.run_tune_eval", new_callable=AsyncMock) as mock_eval,
            patch("skillet.tune.run.improve_skill", new_callable=AsyncMock) as mock_improve,
        ):
            skill_path = Path(tmpdir) / "SKILL.md"
            skill_path.write_text("# Original")

            mock_load.return_value = [
                {"_source": "a.md", "_content": "c", "prompt": "p", "expected": "e"}
            ]
            mock_eval.side_effect = [
                (50.0, [{"pass": False, "eval_source": "a.md", "judgment": {"reasoning": "bad"}}]),
                (100.0, [{"pass": True, "eval_source": "a.md", "judgment": {"reasoning": "OK"}}]),
            ]
            mock_improve.return_value = "# Improved"

            await tune(
                "test-evals",
                skill_path,
                max_rounds=2,
                on_round_start=on_round_start,
                on_round_complete=on_round_complete,
                on_improving=on_improving,
                on_improved=on_improved,
            )

            assert len(callbacks["round_start"]) == 2
            assert len(callbacks["round_complete"]) == 2
            assert len(callbacks["improving"]) == 1
            assert len(callbacks["improved"]) == 1

    @pytest.mark.asyncio
    async def it_preserves_claude_path_structure_in_temp():
        """Test that .claude path structure is preserved in temp directory."""
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch("skillet.tune.run.load_evals") as mock_load,
            patch("skillet.tune.run.run_tune_eval", new_callable=AsyncMock) as mock_eval,
        ):
            # Create skill at .claude/commands/skill/SKILL.md
            skill_dir = Path(tmpdir) / ".claude" / "commands" / "skill"
            skill_dir.mkdir(parents=True)
            skill_path = skill_dir / "SKILL.md"
            skill_path.write_text("# Original Skill")

            mock_load.return_value = [
                {"_source": "a.md", "_content": "c", "prompt": "p", "expected": "e"}
            ]
            mock_eval.return_value = (
                100.0,
                [{"pass": True, "eval_source": "a.md", "judgment": {"reasoning": "OK"}}],
            )

            result = await tune("test-evals", skill_path, max_rounds=1)

            assert result.result.success is True
            # The temp skill path should have been used (verify via mock call)
            mock_eval.assert_called_once()
            call_args = mock_eval.call_args
            temp_skill_path = call_args[0][1]
            # Should preserve .claude/commands/skill structure
            assert ".claude" in str(temp_skill_path)
            assert "commands" in str(temp_skill_path)
            assert "skill" in str(temp_skill_path)
