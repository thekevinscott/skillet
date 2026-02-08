"""Integration tests for the evaluate API."""

from pathlib import Path
from unittest.mock import patch

import pytest

from skillet import evaluate
from skillet._internal.sdk import QueryResult
from skillet.errors import EmptyFolderError

from .conftest import create_eval_file


def describe_evaluate():
    """Integration tests for evaluate function."""

    @pytest.mark.asyncio
    async def it_evaluates_evals_and_returns_results(skillet_env: Path, mock_llm_calls):
        """Happy path: evaluates evals with mocked LLM and returns results."""
        evals_dir = skillet_env / ".skillet" / "evals" / "test-evals"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml", prompt="Test prompt 1")
        create_eval_file(evals_dir / "002.yaml", prompt="Test prompt 2")

        # Configure mocks for this test - query_multiturn for run_prompt
        mock_llm_calls["query_multiturn"].return_value = QueryResult(
            text="Test response", tool_calls=[]
        )
        # query_assistant_text for judge
        mock_llm_calls[
            "query_assistant_text"
        ].return_value = '{"pass": true, "reasoning": "Response meets expectations"}'

        judge_mock = mock_llm_calls["query_assistant_text"]
        with (
            patch(
                "skillet.eval.run_prompt.query_multiturn",
                mock_llm_calls["query_multiturn"],
            ),
            patch("skillet.eval.judge.query_assistant_text", judge_mock),
        ):
            result = await evaluate("test-evals", samples=1, parallel=1, skip_cache=True)

        assert result["total_runs"] == 2
        assert result["sampled_evals"] == 2
        assert result["pass_rate"] == 100.0
        assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def it_evaluates_with_skill_path(skillet_env: Path, mock_llm_calls):
        """Evaluates using a skill file."""
        evals_dir = skillet_env / ".skillet" / "evals" / "skill-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        # Create a skill file
        skill_dir = skillet_env / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# Test Skill\n\nInstructions here.")

        mock_llm_calls["query_multiturn"].return_value = QueryResult(
            text="Response with skill", tool_calls=[]
        )
        mock_llm_calls["query_assistant_text"].return_value = '{"pass": true, "reasoning": "Good"}'

        judge_mock = mock_llm_calls["query_assistant_text"]
        with (
            patch(
                "skillet.eval.run_prompt.query_multiturn",
                mock_llm_calls["query_multiturn"],
            ),
            patch("skillet.eval.judge.query_assistant_text", judge_mock),
        ):
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
    async def it_handles_failing_judgments(skillet_env: Path, mock_llm_calls):
        """Returns proper pass_rate when judge returns failures."""
        evals_dir = skillet_env / ".skillet" / "evals" / "failing-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")
        create_eval_file(evals_dir / "002.yaml")

        mock_llm_calls["query_multiturn"].return_value = QueryResult(
            text="Wrong response", tool_calls=[]
        )
        mock_llm_calls[
            "query_assistant_text"
        ].return_value = '{"pass": false, "reasoning": "Did not meet expectations"}'

        judge_mock = mock_llm_calls["query_assistant_text"]
        with (
            patch(
                "skillet.eval.run_prompt.query_multiturn",
                mock_llm_calls["query_multiturn"],
            ),
            patch("skillet.eval.judge.query_assistant_text", judge_mock),
        ):
            result = await evaluate("failing-test", samples=1, parallel=1, skip_cache=True)

        assert result["total_runs"] == 2
        assert result["pass_rate"] == 0.0
        assert all(not r["pass"] for r in result["results"])

    @pytest.mark.asyncio
    async def it_respects_max_evals_parameter(skillet_env: Path, mock_llm_calls):
        """Limits number of evals when max_evals is set."""
        evals_dir = skillet_env / ".skillet" / "evals" / "many-evals"
        evals_dir.mkdir(parents=True)
        for i in range(5):
            create_eval_file(evals_dir / f"{i:03d}.yaml", prompt=f"Prompt {i}")

        mock_llm_calls["query_multiturn"].return_value = QueryResult(text="Response", tool_calls=[])
        mock_llm_calls["query_assistant_text"].return_value = '{"pass": true, "reasoning": "OK"}'

        judge_mock = mock_llm_calls["query_assistant_text"]
        with (
            patch(
                "skillet.eval.run_prompt.query_multiturn",
                mock_llm_calls["query_multiturn"],
            ),
            patch("skillet.eval.judge.query_assistant_text", judge_mock),
        ):
            result = await evaluate(
                "many-evals", max_evals=2, samples=1, parallel=1, skip_cache=True
            )

        assert result["sampled_evals"] == 2
        assert result["total_evals"] == 5
        assert result["total_runs"] == 2

    @pytest.mark.asyncio
    async def it_respects_samples_parameter(skillet_env: Path, mock_llm_calls):
        """Runs multiple samples per eval."""
        evals_dir = skillet_env / ".skillet" / "evals" / "samples-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        mock_llm_calls["query_multiturn"].return_value = QueryResult(text="Response", tool_calls=[])
        mock_llm_calls["query_assistant_text"].return_value = '{"pass": true, "reasoning": "OK"}'

        judge_mock = mock_llm_calls["query_assistant_text"]
        with (
            patch(
                "skillet.eval.run_prompt.query_multiturn",
                mock_llm_calls["query_multiturn"],
            ),
            patch("skillet.eval.judge.query_assistant_text", judge_mock),
        ):
            result = await evaluate("samples-test", samples=3, parallel=1, skip_cache=True)

        assert result["sampled_evals"] == 1
        assert result["total_runs"] == 3

    @pytest.mark.asyncio
    async def it_calls_on_status_callback(skillet_env: Path, mock_llm_calls):
        """Invokes on_status callback during evaluation."""
        evals_dir = skillet_env / ".skillet" / "evals" / "callback-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        mock_llm_calls["query_multiturn"].return_value = QueryResult(text="Response", tool_calls=[])
        mock_llm_calls["query_assistant_text"].return_value = '{"pass": true, "reasoning": "OK"}'

        status_calls = []

        async def on_status(task, state, _result):
            status_calls.append((task["eval_source"], state))

        judge_mock = mock_llm_calls["query_assistant_text"]
        with (
            patch(
                "skillet.eval.run_prompt.query_multiturn",
                mock_llm_calls["query_multiturn"],
            ),
            patch("skillet.eval.judge.query_assistant_text", judge_mock),
        ):
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
    async def it_handles_llm_errors_gracefully(skillet_env: Path, mock_llm_calls):
        """Returns failure result when LLM call fails."""
        evals_dir = skillet_env / ".skillet" / "evals" / "error-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        mock_llm_calls["query_multiturn"].side_effect = RuntimeError("API error")

        with patch(
            "skillet.eval.run_prompt.query_multiturn",
            mock_llm_calls["query_multiturn"],
        ):
            result = await evaluate("error-test", samples=1, parallel=1, skip_cache=True)

        # Should still return results, but marked as failed
        assert result["total_runs"] == 1
        assert result["pass_rate"] == 0.0
        assert not result["results"][0]["pass"]
