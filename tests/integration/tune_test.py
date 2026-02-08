"""Integration tests for the tune API."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from skillet import tune
from skillet.tune import TuneConfig

from .conftest import create_eval_file


def describe_tune():
    """Integration tests for tune function."""

    @pytest.mark.asyncio
    async def it_runs_tuning_rounds_until_target(skillet_env: Path, mock_claude_query):
        """Happy path: runs tuning and stops when target is reached."""
        evals_dir = skillet_env / ".skillet" / "evals" / "tune-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        # Create skill file
        skill_dir = skillet_env / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# Original Skill\n\nInitial instructions.")

        # 1 eval, samples=1, 1 round: need 2 responses (prompt + judgment)
        mock_claude_query.set_responses(
            "Good response",
            {"pass": True, "reasoning": "Good"},
        )

        with patch("skillet.tune.tune_dspy.propose_instruction") as mock_propose:
            mock_propose.return_value = "# Improved Skill\n\nBetter instructions."

            config = TuneConfig(max_rounds=3, target_pass_rate=100.0, samples=1, parallel=1)
            result = await tune("tune-test", skill_file, config=config)

        assert result.result.success
        assert result.result.final_pass_rate == 100.0
        assert len(result.rounds) >= 1

    @pytest.mark.asyncio
    async def it_stops_after_max_rounds(skillet_env: Path, mock_claude_query):
        """Stops after max_rounds even if target not reached."""
        evals_dir = skillet_env / ".skillet" / "evals" / "max-rounds"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        skill_dir = skillet_env / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# Skill")

        # 1 eval, samples=1, 2 rounds: need 4 responses (2 rounds * 2 calls each)
        mock_claude_query.set_responses(
            "Bad response 1",
            {"pass": False, "reasoning": "Failed"},
            "Bad response 2",
            {"pass": False, "reasoning": "Failed"},
        )

        with patch("skillet.tune.tune_dspy.propose_instruction") as mock_propose:
            mock_propose.return_value = "# Improved but still bad"

            config = TuneConfig(max_rounds=2, target_pass_rate=100.0, samples=1, parallel=1)
            result = await tune("max-rounds", skill_file, config=config)

        assert not result.result.success
        assert len(result.rounds) == 2

    @pytest.mark.asyncio
    async def it_tracks_best_skill_across_rounds(skillet_env: Path, mock_claude_query):
        """Tracks the best performing skill across rounds."""
        evals_dir = skillet_env / ".skillet" / "evals" / "best-skill"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")
        create_eval_file(evals_dir / "002.yaml", prompt="Second prompt")

        skill_dir = skillet_env / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# Original")

        # 2 evals, samples=1, 2 rounds: need 8 responses total
        # Round 1: 50% pass (1 pass, 1 fail)
        # Round 2: 100% pass (2 pass)
        mock_claude_query.set_responses(
            # Round 1
            "Response 1.1",
            {"pass": True, "reasoning": "R"},
            "Response 1.2",
            {"pass": False, "reasoning": "R"},
            # Round 2
            "Response 2.1",
            {"pass": True, "reasoning": "R"},
            "Response 2.2",
            {"pass": True, "reasoning": "R"},
        )

        with patch("skillet.tune.tune_dspy.propose_instruction") as mock_propose:
            mock_propose.return_value = "# Improved Skill"

            config = TuneConfig(max_rounds=2, target_pass_rate=100.0, samples=1, parallel=1)
            result = await tune("best-skill", skill_file, config=config)

        assert result.result.final_pass_rate == 100.0
        assert len(result.rounds) == 2

    @pytest.mark.asyncio
    async def it_calls_callbacks_during_tuning(skillet_env: Path, mock_claude_query):
        """Invokes callbacks at appropriate points during tuning."""
        evals_dir = skillet_env / ".skillet" / "evals" / "callbacks"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        skill_dir = skillet_env / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# Skill")

        # 1 eval, samples=1, 1 round: need 2 responses
        mock_claude_query.set_responses(
            "Response",
            {"pass": True, "reasoning": "OK"},
        )

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
    async def it_saves_improved_skill_to_file(skillet_env: Path, mock_claude_query):
        """Saves the improved skill content back to the file."""
        evals_dir = skillet_env / ".skillet" / "evals" / "save-skill"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        skill_dir = skillet_env / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# Original Content")

        # 1 eval, samples=1: need 2 responses
        mock_claude_query.set_responses(
            "Response",
            {"pass": True, "reasoning": "OK"},
        )

        with patch("skillet.tune.tune_dspy.propose_instruction") as mock_propose:
            mock_propose.return_value = "# Improved Content"

            config = TuneConfig(max_rounds=1, target_pass_rate=100.0, samples=1, parallel=1)
            await tune("save-skill", skill_file, config=config)

        # Verify file was updated
        final_content = skill_file.read_text()
        # Should contain either original (if 100% on first try) or improved content
        assert "Content" in final_content
