"""Integration tests for the evaluate API."""

from pathlib import Path

import pytest

from skillet import evaluate
from skillet.errors import EmptyFolderError

from .conftest import create_eval_file


def describe_evaluate():
    """Integration tests for evaluate function."""

    @pytest.mark.asyncio
    async def it_evaluates_evals_and_returns_results(skillet_env: Path, mock_claude_query):
        """Happy path: evaluates evals with mocked LLM and returns results."""
        evals_dir = skillet_env / ".skillet" / "evals" / "test-evals"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml", prompt="Test prompt 1")
        create_eval_file(evals_dir / "002.yaml", prompt="Test prompt 2")

        # For 2 evals with samples=1: need 4 responses (2 prompts + 2 judgments)
        mock_claude_query.set_responses(
            "Test response 1",  # First prompt execution
            {"pass": True, "reasoning": "Response meets expectations"},  # First judgment
            "Test response 2",  # Second prompt execution
            {"pass": True, "reasoning": "Response meets expectations"},  # Second judgment
        )

        result = await evaluate("test-evals", samples=1, parallel=1, skip_cache=True)

        assert result["total_runs"] == 2
        assert result["sampled_evals"] == 2
        assert result["pass_rate"] == 100.0
        assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def it_evaluates_with_skill_path(skillet_env: Path, mock_claude_query):
        """Evaluates using a skill file."""
        evals_dir = skillet_env / ".skillet" / "evals" / "skill-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        # Create a skill file
        skill_dir = skillet_env / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# Test Skill\n\nInstructions here.")

        # 1 eval with samples=1: need 2 responses
        mock_claude_query.set_responses(
            "Response with skill",
            {"pass": True, "reasoning": "Good"},
        )

        result = await evaluate(
            "skill-test",
            skill_path=skill_file,
            samples=1,
            parallel=1,
            skip_cache=True,
        )

        assert result["total_runs"] == 1
        assert result["pass_rate"] == 100.0

    @pytest.mark.asyncio
    async def it_handles_failing_judgments(skillet_env: Path, mock_claude_query):
        """Returns proper pass_rate when judge returns failures."""
        evals_dir = skillet_env / ".skillet" / "evals" / "failing-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")
        create_eval_file(evals_dir / "002.yaml")

        # 2 evals with samples=1, both failing
        mock_claude_query.set_responses(
            "Wrong response 1",
            {"pass": False, "reasoning": "Did not meet expectations"},
            "Wrong response 2",
            {"pass": False, "reasoning": "Did not meet expectations"},
        )

        result = await evaluate("failing-test", samples=1, parallel=1, skip_cache=True)

        assert result["total_runs"] == 2
        assert result["pass_rate"] == 0.0
        assert all(not r["pass"] for r in result["results"])

    @pytest.mark.asyncio
    async def it_respects_max_evals_parameter(skillet_env: Path, mock_claude_query):
        """Limits number of evals when max_evals is set."""
        evals_dir = skillet_env / ".skillet" / "evals" / "many-evals"
        evals_dir.mkdir(parents=True)
        for i in range(5):
            create_eval_file(evals_dir / f"{i:03d}.yaml", prompt=f"Prompt {i}")

        # max_evals=2, samples=1: need 4 responses (2 evals * 2 calls each)
        mock_claude_query.set_responses(
            "Response 1",
            {"pass": True, "reasoning": "OK"},
            "Response 2",
            {"pass": True, "reasoning": "OK"},
        )

        result = await evaluate("many-evals", max_evals=2, samples=1, parallel=1, skip_cache=True)

        assert result["sampled_evals"] == 2
        assert result["total_evals"] == 5
        assert result["total_runs"] == 2

    @pytest.mark.asyncio
    async def it_respects_samples_parameter(skillet_env: Path, mock_claude_query):
        """Runs multiple samples per eval."""
        evals_dir = skillet_env / ".skillet" / "evals" / "samples-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        # 1 eval with samples=3: need 6 responses (3 samples * 2 calls each)
        mock_claude_query.set_responses(
            "Response 1",
            {"pass": True, "reasoning": "OK"},
            "Response 2",
            {"pass": True, "reasoning": "OK"},
            "Response 3",
            {"pass": True, "reasoning": "OK"},
        )

        result = await evaluate("samples-test", samples=3, parallel=1, skip_cache=True)

        assert result["sampled_evals"] == 1
        assert result["total_runs"] == 3

    @pytest.mark.asyncio
    async def it_calls_on_status_callback(skillet_env: Path, mock_claude_query):
        """Invokes on_status callback during evaluation."""
        evals_dir = skillet_env / ".skillet" / "evals" / "callback-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        mock_claude_query.set_responses(
            "Response",
            {"pass": True, "reasoning": "OK"},
        )

        status_calls = []

        async def on_status(task, state, _result):
            status_calls.append((task["eval_source"], state))

        await evaluate(
            "callback-test",
            samples=1,
            parallel=1,
            on_status=on_status,
            skip_cache=True,
        )

        # Should have running and done states
        states = [s[1] for s in status_calls]
        assert "running" in states
        assert "done" in states

    @pytest.mark.asyncio
    async def it_raises_error_for_nonexistent_evals(skillet_env: Path):  # noqa: ARG001
        """Raises EmptyFolderError for missing eval directory."""
        with pytest.raises(EmptyFolderError):
            await evaluate("nonexistent-evals")

    @pytest.mark.asyncio
    async def it_handles_llm_errors_gracefully(skillet_env: Path, mock_claude_query):
        """Returns failure result when LLM call fails."""
        evals_dir = skillet_env / ".skillet" / "evals" / "error-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        # First call (run_prompt) raises error
        mock_claude_query.set_responses(
            RuntimeError("API error"),
        )

        result = await evaluate("error-test", samples=1, parallel=1, skip_cache=True)

        # Should still return results, but marked as failed
        assert result["total_runs"] == 1
        assert result["pass_rate"] == 0.0
        assert not result["results"][0]["pass"]
