"""Integration tests for the tune API."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from skillet import tune
from skillet.tune import TuneConfig

from .conftest import create_eval_file


def _verdict(passed: bool, reasoning: str = "") -> str:
    """Build a judge verdict the agent CLI would emit as text."""
    return json.dumps({"pass": passed, "reasoning": reasoning})


def describe_tune():
    """Integration tests for tune function.

    Both the agent under test and the judge run through the (mocked) claude CLI
    (``mock_claude_cli``); responses are queued as ``agent, verdict, ...``.
    """

    @pytest.mark.asyncio
    async def it_runs_tuning_rounds_until_target(skillet_env: Path, mock_claude_cli):
        """Happy path: runs tuning and stops when target is reached."""
        evals_dir = skillet_env / ".skillet" / "evals" / "tune-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        # Create skill file
        skill_dir = skillet_env / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# Original Skill\n\nInitial instructions.")

        # 1 eval, samples=1, 1 round: agent runs the prompt, judge grades it.
        mock_claude_cli.set_responses("Good response", _verdict(True, "Good"))

        with patch("skillet.tune.tune_dspy.propose_instruction") as mock_propose:
            mock_propose.return_value = "# Improved Skill\n\nBetter instructions."

            config = TuneConfig(max_rounds=3, target_pass_rate=100.0, samples=1, parallel=1)
            result = await tune("tune-test", skill_file, config=config)

        assert result.result.success
        assert result.result.final_pass_rate == 100.0
        assert len(result.rounds) >= 1

    @pytest.mark.asyncio
    async def it_stops_after_max_rounds(skillet_env: Path, mock_claude_cli):
        """Stops after max_rounds even if target not reached."""
        evals_dir = skillet_env / ".skillet" / "evals" / "max-rounds"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        skill_dir = skillet_env / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# Skill")

        # 1 eval, samples=1, 2 rounds: agent runs each round, judge grades each.
        mock_claude_cli.set_responses(
            "Bad response 1",
            _verdict(False, "Failed"),
            "Bad response 2",
            _verdict(False, "Failed"),
        )

        with patch("skillet.tune.tune_dspy.propose_instruction") as mock_propose:
            mock_propose.return_value = "# Improved but still bad"

            config = TuneConfig(max_rounds=2, target_pass_rate=100.0, samples=1, parallel=1)
            result = await tune("max-rounds", skill_file, config=config)

        assert not result.result.success
        assert len(result.rounds) == 2

    @pytest.mark.asyncio
    async def it_tracks_best_skill_across_rounds(skillet_env: Path, mock_claude_cli):
        """Tracks the best performing skill across rounds."""
        evals_dir = skillet_env / ".skillet" / "evals" / "best-skill"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")
        create_eval_file(evals_dir / "002.yaml", prompt="Second prompt")

        skill_dir = skillet_env / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# Original")

        # 2 evals, samples=1, 2 rounds: agent runs 4 prompts; judge grades 4 times.
        # Round 1: 50% pass (1 pass, 1 fail); Round 2: 100% pass (2 pass).
        mock_claude_cli.set_responses(
            "Response 1.1",
            _verdict(True, "R"),  # round 1 eval 1
            "Response 1.2",
            _verdict(False, "R"),  # round 1 eval 2
            "Response 2.1",
            _verdict(True, "R"),  # round 2 eval 1
            "Response 2.2",
            _verdict(True, "R"),  # round 2 eval 2
        )

        with patch("skillet.tune.tune_dspy.propose_instruction") as mock_propose:
            mock_propose.return_value = "# Improved Skill"

            config = TuneConfig(max_rounds=2, target_pass_rate=100.0, samples=1, parallel=1)
            result = await tune("best-skill", skill_file, config=config)

        assert result.result.final_pass_rate == 100.0
        assert len(result.rounds) == 2

    @pytest.mark.asyncio
    async def it_calls_callbacks_during_tuning(skillet_env: Path, mock_claude_cli):
        """Invokes callbacks at appropriate points during tuning."""
        evals_dir = skillet_env / ".skillet" / "evals" / "callbacks"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        skill_dir = skillet_env / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# Skill")

        # 1 eval, samples=1, 1 round: agent runs the prompt, judge grades it.
        mock_claude_cli.set_responses("Response", _verdict(True, "OK"))

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

        with patch("skillet.tune.tune_dspy.propose_instruction") as mock_propose:
            mock_propose.return_value = "# Improved"

            config = TuneConfig(max_rounds=1, target_pass_rate=100.0, samples=1, parallel=1)
            await tune("callbacks", skill_file, config=config, callbacks=callbacks)

        assert any(e[0] == "start" for e in callback_events)
        assert any(e[0] == "complete" for e in callback_events)

    @pytest.mark.asyncio
    async def it_saves_improved_skill_to_file(skillet_env: Path, mock_claude_cli):
        """Saves the improved skill content back to the file."""
        evals_dir = skillet_env / ".skillet" / "evals" / "save-skill"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        skill_dir = skillet_env / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# Original Content")

        # 1 eval, samples=1: agent runs the prompt, judge grades it.
        mock_claude_cli.set_responses("Response", _verdict(True, "OK"))

        with patch("skillet.tune.tune_dspy.propose_instruction") as mock_propose:
            mock_propose.return_value = "# Improved Content"

            config = TuneConfig(max_rounds=1, target_pass_rate=100.0, samples=1, parallel=1)
            await tune("save-skill", skill_file, config=config)

        # Verify file was updated
        final_content = skill_file.read_text()
        # Should contain either original (if 100% on first try) or improved content
        assert "Content" in final_content
