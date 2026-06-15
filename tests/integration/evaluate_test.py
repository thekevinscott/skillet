"""Integration tests for the evaluate API."""

import json
from pathlib import Path

import pytest

from skillet import evaluate
from skillet.agent import Agent
from skillet.errors import EmptyFolderError
from skillet.eval.evaluate.result import EvaluateResult, IterationResult

from .conftest import create_eval_file


def _verdict(passed: bool, reasoning: str = "") -> str:
    """Build a judge verdict the agent CLI would emit as text."""
    return json.dumps({"pass": passed, "reasoning": reasoning})


def describe_evaluate():
    """Integration tests for evaluate function.

    Both the agent under test and the judge run through the (mocked) claude CLI
    (``mock_claude_cli``). Under ``parallel=1`` the CLI is driven once per agent
    run and once per judge call, in that order, so responses are queued as
    ``agent, verdict, agent, verdict, ...``.
    """

    @pytest.mark.asyncio
    async def it_evaluates_evals_and_returns_results(skillet_env: Path, mock_claude_cli):
        """Happy path: agent answers each prompt, judge grades each via the CLI."""
        evals_dir = skillet_env / ".skillet" / "evals" / "test-evals"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml", prompt="Test prompt 1")
        create_eval_file(evals_dir / "002.yaml", prompt="Test prompt 2")

        mock_claude_cli.set_responses(
            "Test response 1",
            _verdict(True, "Response meets expectations"),
            "Test response 2",
            _verdict(True, "Response meets expectations"),
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
    async def it_evaluates_with_skill_path(skillet_env: Path, mock_claude_cli):
        """Evaluates using a skill file."""
        evals_dir = skillet_env / ".skillet" / "evals" / "skill-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        # Create a skill file
        skill_dir = skillet_env / "skills" / "test"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# Test Skill\n\nInstructions here.")

        mock_claude_cli.set_responses("Response with skill", _verdict(True, "Good"))

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
    async def it_handles_failing_judgments(skillet_env: Path, mock_claude_cli):
        """Returns proper pass_rate when judge returns failures."""
        evals_dir = skillet_env / ".skillet" / "evals" / "failing-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")
        create_eval_file(evals_dir / "002.yaml")

        mock_claude_cli.set_responses(
            "Wrong response 1",
            _verdict(False, "Did not meet expectations"),
            "Wrong response 2",
            _verdict(False, "Did not meet expectations"),
        )

        result = await evaluate(
            "failing-test", samples=1, parallel=1, skip_cache=True, agent=Agent.CLAUDE
        )

        assert result.total_runs == 2
        assert result.pass_rate == 0.0
        assert all(not r.passed for r in result.results)

    @pytest.mark.asyncio
    async def it_judges_a_verdict_wrapped_in_a_code_fence(skillet_env: Path, mock_claude_cli):
        """A verdict wrapped in a markdown fence is still parsed."""
        evals_dir = skillet_env / ".skillet" / "evals" / "fenced-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        fenced = '```json\n{"pass": true, "reasoning": "Fenced but fine"}\n```'
        mock_claude_cli.set_responses("Agent response", fenced)

        result = await evaluate(
            "fenced-test", samples=1, parallel=1, skip_cache=True, agent=Agent.CLAUDE
        )

        assert result.total_runs == 1
        assert result.pass_rate == 100.0

    @pytest.mark.asyncio
    async def it_retries_the_judge_once_on_invalid_json(skillet_env: Path, mock_claude_cli):
        """A first unparseable verdict is retried once; the retry succeeds."""
        evals_dir = skillet_env / ".skillet" / "evals" / "retry-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        mock_claude_cli.set_responses(
            "Agent response",
            "I think it passed, honestly.",  # not JSON -> retry
            _verdict(True, "Recovered on retry"),
        )

        result = await evaluate(
            "retry-test", samples=1, parallel=1, skip_cache=True, agent=Agent.CLAUDE
        )

        assert result.total_runs == 1
        assert result.pass_rate == 100.0
        # 1 agent run + 2 judge attempts.
        assert mock_claude_cli.call_count == 3

    @pytest.mark.asyncio
    async def it_fails_loudly_when_the_judge_never_returns_valid_json(
        skillet_env: Path, mock_claude_cli
    ):
        """Two unparseable verdicts fail the eval loudly instead of silently passing."""
        evals_dir = skillet_env / ".skillet" / "evals" / "bad-judge"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        mock_claude_cli.set_responses(
            "Agent response",
            "not json",  # attempt 1
            "still not json",  # attempt 2 (retry)
        )

        result = await evaluate(
            "bad-judge", samples=1, parallel=1, skip_cache=True, agent=Agent.CLAUDE
        )

        assert result.total_runs == 1
        assert result.pass_rate == 0.0
        assert not result.results[0].passed
        assert "JudgeError" in result.results[0].judgment["reasoning"]

    @pytest.mark.asyncio
    async def it_respects_max_evals_parameter(skillet_env: Path, mock_claude_cli):
        """Limits number of evals when max_evals is set."""
        evals_dir = skillet_env / ".skillet" / "evals" / "many-evals"
        evals_dir.mkdir(parents=True)
        for i in range(5):
            create_eval_file(evals_dir / f"{i:03d}.yaml", prompt=f"Prompt {i}")

        mock_claude_cli.set_responses(
            "Response 1",
            _verdict(True, "OK"),
            "Response 2",
            _verdict(True, "OK"),
        )

        result = await evaluate(
            "many-evals", max_evals=2, samples=1, parallel=1, skip_cache=True, agent=Agent.CLAUDE
        )

        assert result.sampled_evals == 2
        assert result.total_evals == 5
        assert result.total_runs == 2

    @pytest.mark.asyncio
    async def it_respects_samples_parameter(skillet_env: Path, mock_claude_cli):
        """Runs multiple samples per eval."""
        evals_dir = skillet_env / ".skillet" / "evals" / "samples-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        mock_claude_cli.set_responses(
            "Response 1",
            _verdict(True, "OK"),
            "Response 2",
            _verdict(True, "OK"),
            "Response 3",
            _verdict(True, "OK"),
        )

        result = await evaluate(
            "samples-test", samples=3, parallel=1, skip_cache=True, agent=Agent.CLAUDE
        )

        assert result.sampled_evals == 1
        assert result.total_runs == 3

    @pytest.mark.asyncio
    async def it_calls_on_status_callback(skillet_env: Path, mock_claude_cli):
        """Invokes on_status callback during evaluation."""
        evals_dir = skillet_env / ".skillet" / "evals" / "callback-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        mock_claude_cli.set_responses("Response", _verdict(True, "OK"))

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
    async def it_returns_per_eval_pass_at_k_and_pass_pow_k(skillet_env: Path, mock_claude_cli):
        """Returns per-eval pass@k and pass^k metrics when samples > 1."""
        evals_dir = skillet_env / ".skillet" / "evals" / "metrics-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml", prompt="Prompt 1")
        create_eval_file(evals_dir / "002.yaml", prompt="Prompt 2")

        # 2 evals, 3 samples each, eval-major order. Each run is agent then judge.
        # Eval 001: pass, fail, pass (2/3); Eval 002: pass, pass, pass (3/3).
        mock_claude_cli.set_responses(
            "R1",
            _verdict(True, "OK"),  # eval 001 sample 1
            "R2",
            _verdict(False, "Bad"),  # eval 001 sample 2
            "R3",
            _verdict(True, "OK"),  # eval 001 sample 3
            "R4",
            _verdict(True, "OK"),  # eval 002 sample 1
            "R5",
            _verdict(True, "OK"),  # eval 002 sample 2
            "R6",
            _verdict(True, "OK"),  # eval 002 sample 3
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
    async def it_uses_assertions_instead_of_judge(skillet_env: Path, mock_claude_cli):
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
        # Agent ran exactly once; the judge CLI was never invoked.
        assert mock_claude_cli.call_count == 1

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
