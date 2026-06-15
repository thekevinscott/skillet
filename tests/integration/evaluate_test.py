"""Integration tests for the evaluate API."""

from pathlib import Path

import pytest

from skillet import evaluate
from skillet.agent import Agent
from skillet.errors import EmptyFolderError
from skillet.eval.evaluate.result import EvaluateResult, IterationResult

from .conftest import create_eval_file


def describe_evaluate():
    """Integration tests for evaluate function.

    The agent under test runs the prompt through the (mocked) claude CLI
    (``mock_claude_cli``); the judge runs through the (mocked) SDK
    (``mock_claude_query``).
    """

    @pytest.mark.asyncio
    async def it_evaluates_evals_and_returns_results(
        skillet_env: Path, mock_claude_cli, mock_claude_query
    ):
        """Happy path: evaluates evals with mocked agent + judge and returns results."""
        evals_dir = skillet_env / ".skillet" / "evals" / "test-evals"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml", prompt="Test prompt 1")
        create_eval_file(evals_dir / "002.yaml", prompt="Test prompt 2")

        # 2 evals, samples=1: agent runs each prompt, judge grades each.
        mock_claude_cli.set_responses("Test response 1", "Test response 2")
        mock_claude_query.set_responses(
            {"pass": True, "reasoning": "Response meets expectations"},
            {"pass": True, "reasoning": "Response meets expectations"},
        )

        result = await evaluate(
            "test-evals", samples=1, parallel=1, skip_cache=True, agent=Agent.CLAUDE
        )

        assert isinstance(result, EvaluateResult)
        assert result.total_runs == 2
        assert result.sampled_evals == 2
        assert result.pass_rate == 100.0
        assert len(result.results) == 2
        assert all(isinstance(r, IterationResult) for r in result.results)

    @pytest.mark.asyncio
    async def it_evaluates_with_skill_path(skillet_env: Path, mock_claude_cli, mock_claude_query):
        """Evaluates using a skill file."""
        evals_dir = skillet_env / ".skillet" / "evals" / "skill-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        # Create a skill file
        skill_dir = skillet_env / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# Test Skill\n\nInstructions here.")

        mock_claude_cli.set_responses("Response with skill")
        mock_claude_query.set_responses({"pass": True, "reasoning": "Good"})

        result = await evaluate(
            "skill-test",
            skill_path=skill_file,
            samples=1,
            parallel=1,
            skip_cache=True,
            agent=Agent.CLAUDE,
        )

        assert result.total_runs == 1
        assert result.pass_rate == 100.0

    @pytest.mark.asyncio
    async def it_handles_failing_judgments(skillet_env: Path, mock_claude_cli, mock_claude_query):
        """Returns proper pass_rate when judge returns failures."""
        evals_dir = skillet_env / ".skillet" / "evals" / "failing-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")
        create_eval_file(evals_dir / "002.yaml")

        mock_claude_cli.set_responses("Wrong response 1", "Wrong response 2")
        mock_claude_query.set_responses(
            {"pass": False, "reasoning": "Did not meet expectations"},
            {"pass": False, "reasoning": "Did not meet expectations"},
        )

        result = await evaluate(
            "failing-test", samples=1, parallel=1, skip_cache=True, agent=Agent.CLAUDE
        )

        assert result.total_runs == 2
        assert result.pass_rate == 0.0
        assert all(not r.passed for r in result.results)

    @pytest.mark.asyncio
    async def it_respects_max_evals_parameter(
        skillet_env: Path, mock_claude_cli, mock_claude_query
    ):
        """Limits number of evals when max_evals is set."""
        evals_dir = skillet_env / ".skillet" / "evals" / "many-evals"
        evals_dir.mkdir(parents=True)
        for i in range(5):
            create_eval_file(evals_dir / f"{i:03d}.yaml", prompt=f"Prompt {i}")

        mock_claude_cli.set_responses("Response 1", "Response 2")
        mock_claude_query.set_responses(
            {"pass": True, "reasoning": "OK"},
            {"pass": True, "reasoning": "OK"},
        )

        result = await evaluate(
            "many-evals", max_evals=2, samples=1, parallel=1, skip_cache=True, agent=Agent.CLAUDE
        )

        assert result.sampled_evals == 2
        assert result.total_evals == 5
        assert result.total_runs == 2

    @pytest.mark.asyncio
    async def it_respects_samples_parameter(skillet_env: Path, mock_claude_cli, mock_claude_query):
        """Runs multiple samples per eval."""
        evals_dir = skillet_env / ".skillet" / "evals" / "samples-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        mock_claude_cli.set_responses("Response 1", "Response 2", "Response 3")
        mock_claude_query.set_responses(
            {"pass": True, "reasoning": "OK"},
            {"pass": True, "reasoning": "OK"},
            {"pass": True, "reasoning": "OK"},
        )

        result = await evaluate(
            "samples-test", samples=3, parallel=1, skip_cache=True, agent=Agent.CLAUDE
        )

        assert result.sampled_evals == 1
        assert result.total_runs == 3

    @pytest.mark.asyncio
    async def it_calls_on_status_callback(skillet_env: Path, mock_claude_cli, mock_claude_query):
        """Invokes on_status callback during evaluation."""
        evals_dir = skillet_env / ".skillet" / "evals" / "callback-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        mock_claude_cli.set_responses("Response")
        mock_claude_query.set_responses({"pass": True, "reasoning": "OK"})

        status_calls = []

        async def on_status(task, state, _result):
            status_calls.append((task["eval_source"], state))

        await evaluate(
            "callback-test",
            samples=1,
            parallel=1,
            on_status=on_status,
            skip_cache=True,
            agent=Agent.CLAUDE,
        )

        # Should have running and done states
        states = [s[1] for s in status_calls]
        assert "running" in states
        assert "done" in states

    @pytest.mark.asyncio
    async def it_raises_error_for_nonexistent_evals(skillet_env: Path):  # noqa: ARG001
        """Raises EmptyFolderError for missing eval directory."""
        with pytest.raises(EmptyFolderError):
            await evaluate("nonexistent-evals", agent=Agent.CLAUDE)

    @pytest.mark.asyncio
    async def it_returns_per_eval_pass_at_k_and_pass_pow_k(
        skillet_env: Path, mock_claude_cli, mock_claude_query
    ):
        """Returns per-eval pass@k and pass^k metrics when samples > 1."""
        evals_dir = skillet_env / ".skillet" / "evals" / "metrics-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml", prompt="Prompt 1")
        create_eval_file(evals_dir / "002.yaml", prompt="Prompt 2")

        # 2 evals, 3 samples each. Agent runs 6 prompts; judge grades 6 times.
        # Eval 001: pass, fail, pass (2/3)
        # Eval 002: pass, pass, pass (3/3)
        mock_claude_cli.set_responses("R1", "R2", "R3", "R4", "R5", "R6")
        mock_claude_query.set_responses(
            {"pass": True, "reasoning": "OK"},  # eval 001 sample 1
            {"pass": False, "reasoning": "Bad"},  # eval 001 sample 2
            {"pass": True, "reasoning": "OK"},  # eval 001 sample 3
            {"pass": True, "reasoning": "OK"},  # eval 002 sample 1
            {"pass": True, "reasoning": "OK"},  # eval 002 sample 2
            {"pass": True, "reasoning": "OK"},  # eval 002 sample 3
        )

        result = await evaluate(
            "metrics-test", samples=3, parallel=1, skip_cache=True, agent=Agent.CLAUDE
        )

        metrics = result.per_eval_metrics
        assert len(metrics) == 2

        # Eval 001: n=3, c=2, k=3 -> pass@3 = 1.0, pass^3 = 0.0
        eval_001 = metrics[0]
        assert eval_001.pass_at_k == 1.0
        assert eval_001.pass_pow_k == 0.0

        # Eval 002: n=3, c=3, k=3 -> pass@3 = 1.0, pass^3 = 1.0
        eval_002 = metrics[1]
        assert eval_002.pass_at_k == 1.0
        assert eval_002.pass_pow_k == 1.0

    @pytest.mark.asyncio
    async def it_uses_assertions_instead_of_judge(
        skillet_env: Path, mock_claude_cli, mock_claude_query
    ):
        """When assertions are present, grades deterministically without calling the judge."""
        evals_dir = skillet_env / ".skillet" / "evals" / "assert-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(
            evals_dir / "001.yaml",
            prompt="What is 2+2?",
            expected="Returns 4",
            assertions=[
                {"type": "contains", "value": "4"},
                {"type": "not_contains", "value": "5"},
            ],
        )

        # Only the agent runs; no judge call expected.
        mock_claude_cli.set_responses("The answer is 4.")

        result = await evaluate(
            "assert-test", samples=1, parallel=1, skip_cache=True, agent=Agent.CLAUDE
        )

        assert result.total_runs == 1
        assert result.pass_rate == 100.0
        assert result.results[0].passed
        # Agent ran once; judge (SDK) was never called.
        assert mock_claude_cli.call_count == 1
        assert mock_claude_query.call_count == 0

    @pytest.mark.asyncio
    async def it_handles_assertion_failures(skillet_env: Path, mock_claude_cli):
        """When assertions fail, returns pass=False with reasoning."""
        evals_dir = skillet_env / ".skillet" / "evals" / "assert-fail"
        evals_dir.mkdir(parents=True)
        create_eval_file(
            evals_dir / "001.yaml",
            prompt="What is 2+2?",
            expected="Returns 4",
            assertions=[
                {"type": "contains", "value": "42"},
            ],
        )

        mock_claude_cli.set_responses("The answer is 4.")

        result = await evaluate(
            "assert-fail", samples=1, parallel=1, skip_cache=True, agent=Agent.CLAUDE
        )

        assert result.total_runs == 1
        assert result.pass_rate == 0.0
        assert not result.results[0].passed

    @pytest.mark.asyncio
    async def it_handles_llm_errors_gracefully(skillet_env: Path, mock_claude_cli):
        """Returns failure result when the agent CLI call fails."""
        evals_dir = skillet_env / ".skillet" / "evals" / "error-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        # The agent run raises before the judge is reached.
        mock_claude_cli.set_responses(RuntimeError("API error"))

        result = await evaluate(
            "error-test", samples=1, parallel=1, skip_cache=True, agent=Agent.CLAUDE
        )

        # Should still return results, but marked as failed
        assert result.total_runs == 1
        assert result.pass_rate == 0.0
        assert not result.results[0].passed
