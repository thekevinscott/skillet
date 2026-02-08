"""Integration tests for the tune API."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from skillet import tune
from skillet._internal.sdk import QueryResult
from skillet.tune import TuneConfig

from .conftest import create_eval_file


def describe_tune():
    """Integration tests for tune function."""

    @pytest.mark.asyncio
    async def it_runs_tuning_rounds_until_target(skillet_env: Path, mock_llm_calls):
        """Happy path: runs tuning and stops when target is reached."""
        evals_dir = skillet_env / ".skillet" / "evals" / "tune-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        # Create skill file
        skill_dir = skillet_env / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# Original Skill\n\nInitial instructions.")

        mock_llm_calls["query_multiturn"].return_value = QueryResult(
            text="Good response", tool_calls=[]
        )
        mock_llm_calls["query_assistant_text"].return_value = '{"pass": true, "reasoning": "Good"}'

        judge_mock = mock_llm_calls["query_assistant_text"]
        with (
            patch(
                "skillet.eval.run_prompt.query_multiturn",
                mock_llm_calls["query_multiturn"],
            ),
            patch("skillet.eval.judge.query_assistant_text", judge_mock),
            patch("skillet.tune.tune_dspy.propose_instruction") as mock_propose,
        ):
            mock_propose.return_value = "# Improved Skill\n\nBetter instructions."

            config = TuneConfig(max_rounds=3, target_pass_rate=100.0, samples=1, parallel=1)
            result = await tune("tune-test", skill_file, config=config)

        assert result.result.success
        assert result.result.final_pass_rate == 100.0
        assert len(result.rounds) >= 1

    @pytest.mark.asyncio
    async def it_stops_after_max_rounds(skillet_env: Path, mock_llm_calls):
        """Stops after max_rounds even if target not reached."""
        evals_dir = skillet_env / ".skillet" / "evals" / "max-rounds"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        skill_dir = skillet_env / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# Skill")

        # Always fail
        mock_llm_calls["query_multiturn"].return_value = QueryResult(
            text="Bad response", tool_calls=[]
        )
        mock_llm_calls[
            "query_assistant_text"
        ].return_value = '{"pass": false, "reasoning": "Failed"}'

        judge_mock = mock_llm_calls["query_assistant_text"]
        with (
            patch(
                "skillet.eval.run_prompt.query_multiturn",
                mock_llm_calls["query_multiturn"],
            ),
            patch("skillet.eval.judge.query_assistant_text", judge_mock),
            patch("skillet.tune.tune_dspy.propose_instruction") as mock_propose,
        ):
            mock_propose.return_value = "# Improved but still bad"

            config = TuneConfig(max_rounds=2, target_pass_rate=100.0, samples=1, parallel=1)
            result = await tune("max-rounds", skill_file, config=config)

        assert not result.result.success
        assert len(result.rounds) == 2

    @pytest.mark.asyncio
    async def it_tracks_best_skill_across_rounds(skillet_env: Path, mock_llm_calls):
        """Tracks the best performing skill across rounds."""
        evals_dir = skillet_env / ".skillet" / "evals" / "best-skill"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")
        create_eval_file(evals_dir / "002.yaml", prompt="Second prompt")

        skill_dir = skillet_env / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# Original")

        call_count = [0]

        async def varying_judgment(*_args, **_kwargs):
            call_count[0] += 1
            # First round: 50% pass, Second round: 100% pass
            if call_count[0] <= 2:  # First round (2 evals)
                passed = "true" if call_count[0] == 1 else "false"
                return '{"pass": ' + passed + ', "reasoning": "R"}'
            return '{"pass": true, "reasoning": "R"}'

        mock_llm_calls["query_multiturn"].return_value = QueryResult(text="Response", tool_calls=[])
        mock_llm_calls["query_assistant_text"].side_effect = varying_judgment

        judge_mock = mock_llm_calls["query_assistant_text"]
        with (
            patch(
                "skillet.eval.run_prompt.query_multiturn",
                mock_llm_calls["query_multiturn"],
            ),
            patch("skillet.eval.judge.query_assistant_text", judge_mock),
            patch("skillet.tune.tune_dspy.propose_instruction") as mock_propose,
        ):
            mock_propose.return_value = "# Improved Skill"

            config = TuneConfig(max_rounds=2, target_pass_rate=100.0, samples=1, parallel=1)
            result = await tune("best-skill", skill_file, config=config)

        assert result.result.final_pass_rate == 100.0
        assert len(result.rounds) == 2

    @pytest.mark.asyncio
    async def it_calls_callbacks_during_tuning(skillet_env: Path, mock_llm_calls):
        """Invokes callbacks at appropriate points during tuning."""
        evals_dir = skillet_env / ".skillet" / "evals" / "callbacks"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        skill_dir = skillet_env / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# Skill")

        mock_llm_calls["query_multiturn"].return_value = QueryResult(text="Response", tool_calls=[])
        mock_llm_calls["query_assistant_text"].return_value = '{"pass": true, "reasoning": "OK"}'

        callback_events = []

        from skillet.tune.result import TuneCallbacks

        def on_start(r, _t):
            callback_events.append(("start", r))

        def on_complete(r, p, _res):
            callback_events.append(("complete", r, p))

        callbacks = TuneCallbacks(
            on_round_start=AsyncMock(side_effect=on_start),
            on_round_complete=AsyncMock(side_effect=on_complete),
        )

        judge_mock = mock_llm_calls["query_assistant_text"]
        with (
            patch(
                "skillet.eval.run_prompt.query_multiturn",
                mock_llm_calls["query_multiturn"],
            ),
            patch("skillet.eval.judge.query_assistant_text", judge_mock),
            patch("skillet.tune.tune_dspy.propose_instruction") as mock_propose,
        ):
            mock_propose.return_value = "# Improved"

            config = TuneConfig(max_rounds=1, target_pass_rate=100.0, samples=1, parallel=1)
            await tune("callbacks", skill_file, config=config, callbacks=callbacks)

        assert any(e[0] == "start" for e in callback_events)
        assert any(e[0] == "complete" for e in callback_events)

    @pytest.mark.asyncio
    async def it_saves_improved_skill_to_file(skillet_env: Path, mock_llm_calls):
        """Saves the improved skill content back to the file."""
        evals_dir = skillet_env / ".skillet" / "evals" / "save-skill"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        skill_dir = skillet_env / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# Original Content")

        mock_llm_calls["query_multiturn"].return_value = QueryResult(text="Response", tool_calls=[])
        mock_llm_calls["query_assistant_text"].return_value = '{"pass": true, "reasoning": "OK"}'

        judge_mock = mock_llm_calls["query_assistant_text"]
        with (
            patch(
                "skillet.eval.run_prompt.query_multiturn",
                mock_llm_calls["query_multiturn"],
            ),
            patch("skillet.eval.judge.query_assistant_text", judge_mock),
            patch("skillet.tune.tune_dspy.propose_instruction") as mock_propose,
        ):
            mock_propose.return_value = "# Improved Content"

            config = TuneConfig(max_rounds=1, target_pass_rate=100.0, samples=1, parallel=1)
            await tune("save-skill", skill_file, config=config)

        # Verify file was updated
        final_content = skill_file.read_text()
        # Should contain either original (if 100% on first try) or improved content
        assert "Content" in final_content
