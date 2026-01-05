"""Tests for tune_dspy module."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from skillet.tune.result import TuneCallbacks, TuneConfig
from skillet.tune.tune_dspy import tune_dspy

# Common test data
PASS_RESULT = {
    "eval_source": "test.yaml",
    "pass": True,
    "judgment": {"reasoning": "Good"},
}
FAIL_RESULT = {
    "eval_source": "test.yaml",
    "pass": False,
    "judgment": {"reasoning": "Bad"},
    "response": "wrong",
}


@pytest.fixture(autouse=True)
def mock_load_evals():
    """Mock load_evals to avoid filesystem access."""
    with patch("skillet.tune.tune_dspy.load_evals") as mock:
        mock.return_value = [
            {
                "_source": "test.yaml",
                "_content": "test content",
                "prompt": "test prompt",
                "expected": "test expected",
            }
        ]
        yield mock


@pytest.fixture(autouse=True)
def mock_evals_to_trainset():
    """Mock evals_to_trainset."""
    with patch("skillet.tune.tune_dspy.evals_to_trainset") as mock:
        mock.return_value = []
        yield mock


@pytest.fixture(autouse=True)
def mock_run_tune_eval():
    """Mock run_tune_eval to avoid actual eval runs."""
    with patch("skillet.tune.tune_dspy.run_tune_eval") as mock:
        mock.return_value = (100.0, [PASS_RESULT])
        yield mock


@pytest.fixture(autouse=True)
def mock_propose_instruction():
    """Mock propose_instruction to avoid DSPy calls."""
    with patch("skillet.tune.tune_dspy.propose_instruction") as mock:
        mock.return_value = "Improved instruction"
        yield mock


@pytest.fixture
def skill_file():
    """Create a temporary skill file for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        skill_path = Path(temp_dir) / ".claude" / "commands" / "skill.md"
        skill_path.parent.mkdir(parents=True)
        skill_path.write_text("Original instruction")
        yield skill_path


def describe_tune_dspy():
    @pytest.mark.asyncio
    async def it_returns_tune_result_on_success(skill_file):
        result = await tune_dspy(
            name="test-evals",
            skill_path=skill_file,
        )
        assert result is not None
        assert result.result.success is True
        assert len(result.rounds) == 1

    @pytest.mark.asyncio
    async def it_uses_default_config_when_none_provided(
        skill_file,
        mock_run_tune_eval,
    ):
        await tune_dspy(
            name="test-evals",
            skill_path=skill_file,
        )
        # Default config has samples=1, parallel=3
        call_args = mock_run_tune_eval.call_args
        assert call_args[0][2] == 1  # samples
        assert call_args[0][3] == 3  # parallel

    @pytest.mark.asyncio
    async def it_respects_custom_config(skill_file, mock_run_tune_eval):
        config = TuneConfig(max_rounds=3, samples=2, parallel=5)
        await tune_dspy(
            name="test-evals",
            skill_path=skill_file,
            config=config,
        )
        call_args = mock_run_tune_eval.call_args
        assert call_args[0][2] == 2  # samples
        assert call_args[0][3] == 5  # parallel

    @pytest.mark.asyncio
    async def it_calls_on_round_start_callback(skill_file):
        on_round_start = AsyncMock()
        callbacks = TuneCallbacks(on_round_start=on_round_start)

        await tune_dspy(
            name="test-evals",
            skill_path=skill_file,
            callbacks=callbacks,
        )
        on_round_start.assert_called_once_with(1, 5)

    @pytest.mark.asyncio
    async def it_calls_on_complete_callback(skill_file):
        on_complete = AsyncMock()
        callbacks = TuneCallbacks(on_complete=on_complete)

        await tune_dspy(
            name="test-evals",
            skill_path=skill_file,
            callbacks=callbacks,
        )
        on_complete.assert_called_once()
        # Verify it was called with the skill file path
        assert on_complete.call_args[0][0] == skill_file

    @pytest.mark.asyncio
    async def it_improves_skill_when_pass_rate_below_target(
        skill_file,
        mock_run_tune_eval,
        mock_propose_instruction,
    ):
        # First round fails, second succeeds
        mock_run_tune_eval.side_effect = [
            (50.0, [FAIL_RESULT]),
            (100.0, [PASS_RESULT]),
        ]

        result = await tune_dspy(
            name="test-evals",
            skill_path=skill_file,
        )

        assert result.result.success is True
        assert len(result.rounds) == 2
        mock_propose_instruction.assert_called_once()

    @pytest.mark.asyncio
    async def it_respects_max_rounds(
        skill_file,
        mock_run_tune_eval,
        mock_propose_instruction,
    ):
        # Always fail so we hit max rounds
        mock_run_tune_eval.return_value = (50.0, [FAIL_RESULT])
        mock_propose_instruction.return_value = "New instruction"

        config = TuneConfig(max_rounds=3)
        result = await tune_dspy(
            name="test-evals",
            skill_path=skill_file,
            config=config,
        )

        assert result.result.success is False
        assert len(result.rounds) == 3

    @pytest.mark.asyncio
    async def it_passes_instruction_history_to_proposer(
        skill_file,
        mock_run_tune_eval,
        mock_propose_instruction,
    ):
        # Fail once so propose_instruction is called
        mock_run_tune_eval.side_effect = [
            (50.0, [FAIL_RESULT]),
            (100.0, [PASS_RESULT]),
        ]

        await tune_dspy(
            name="test-evals",
            skill_path=skill_file,
        )

        # Verify propose_instruction was called with expected args
        mock_propose_instruction.assert_called_once()
        call_kwargs = mock_propose_instruction.call_args[1]
        assert "instruction_history" in call_kwargs
        assert "current_instruction" in call_kwargs
        assert "trainset" in call_kwargs
        assert "failures" in call_kwargs
        # History should contain at least the first round's result
        history = call_kwargs["instruction_history"]
        assert len(history) >= 1
        assert history[0]["instruction"] == "Original instruction"

    @pytest.mark.asyncio
    async def it_preserves_claude_path_structure_in_temp(skill_file, mock_run_tune_eval):
        # Verify temp path preserves .claude structure
        await tune_dspy(
            name="test-evals",
            skill_path=skill_file,
        )
        # run_tune_eval should receive a path with .claude in it
        call_args = mock_run_tune_eval.call_args
        temp_path = call_args[0][1]
        assert ".claude" in str(temp_path)
