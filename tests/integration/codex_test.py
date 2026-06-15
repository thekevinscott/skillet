"""Integration tests for evaluating through the codex CLI (``--agent codex``).

The codex agent under test and the codex judge both run through the (mocked)
codex CLI (``mock_codex_cli``). Under ``parallel=1`` the CLI is driven once per
agent run and once per judge call, in that order, so responses are queued as
``agent, verdict, agent, verdict, ...`` — exactly as for the claude path.
"""

import json
from pathlib import Path

import pytest

from skillet import evaluate
from skillet.agent import Agent
from skillet.eval.evaluate.result import EvaluateResult

from .conftest import _FakeClaudeProc, create_eval_file


def _verdict(passed: bool, reasoning: str = "") -> str:
    """Build a judge verdict the codex CLI would emit as its agent_message text."""
    return json.dumps({"pass": passed, "reasoning": reasoning})


def describe_evaluate_with_codex():
    """Integration tests for evaluate(agent=Agent.CODEX)."""

    @pytest.mark.asyncio
    async def it_runs_and_judges_through_the_codex_cli(skillet_env: Path, mock_codex_cli):
        """Happy path: codex answers each prompt, codex judge grades each."""
        evals_dir = skillet_env / ".skillet" / "evals" / "codex-evals"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml", prompt="Test prompt 1")
        create_eval_file(evals_dir / "002.yaml", prompt="Test prompt 2")

        mock_codex_cli.set_responses(
            "Codex response 1",
            _verdict(True, "Meets expectations"),
            "Codex response 2",
            _verdict(True, "Meets expectations"),
        )

        result = await evaluate(
            "codex-evals",
            samples=1,
            parallel=1,
            skip_cache=True,
            agent=Agent.CODEX,
            skillet_dir=skillet_env / ".skillet",
        )

        assert isinstance(result, EvaluateResult)
        assert result.total_runs == 2
        assert result.pass_rate == 100.0

    @pytest.mark.asyncio
    async def it_evaluates_with_a_codex_skill_path(skillet_env: Path, mock_codex_cli):
        """Evaluates a skill staged under .codex/skills."""
        evals_dir = skillet_env / ".skillet" / "evals" / "codex-skill"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        skill_dir = skillet_env / ".codex" / "skills" / "test"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Test Skill\n\nInstructions here.")

        mock_codex_cli.set_responses("Response with skill", _verdict(True, "Good"))

        result = await evaluate(
            "codex-skill",
            skill_path=skill_dir,
            samples=1,
            parallel=1,
            skip_cache=True,
            agent=Agent.CODEX,
            skillet_dir=skillet_env / ".skillet",
        )

        assert result.total_runs == 1
        assert result.pass_rate == 100.0

    @pytest.mark.asyncio
    async def it_reports_failing_codex_judgments(skillet_env: Path, mock_codex_cli):
        """A failing codex verdict yields a 0% pass rate."""
        evals_dir = skillet_env / ".skillet" / "evals" / "codex-fail"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        mock_codex_cli.set_responses("Wrong answer", _verdict(False, "Did not meet expectations"))

        result = await evaluate(
            "codex-fail",
            samples=1,
            parallel=1,
            skip_cache=True,
            agent=Agent.CODEX,
            skillet_dir=skillet_env / ".skillet",
        )

        assert result.total_runs == 1
        assert result.pass_rate == 0.0
        assert not result.results[0].passed

    @pytest.mark.asyncio
    async def it_parses_a_codex_verdict_in_a_code_fence(skillet_env: Path, mock_codex_cli):
        """A verdict wrapped in a markdown fence is still parsed."""
        evals_dir = skillet_env / ".skillet" / "evals" / "codex-fenced"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        fenced = '```json\n{"pass": true, "reasoning": "Fenced but fine"}\n```'
        mock_codex_cli.set_responses("Codex response", fenced)

        result = await evaluate(
            "codex-fenced",
            samples=1,
            parallel=1,
            skip_cache=True,
            agent=Agent.CODEX,
            skillet_dir=skillet_env / ".skillet",
        )

        assert result.total_runs == 1
        assert result.pass_rate == 100.0

    @pytest.mark.asyncio
    async def it_captures_codex_tool_calls(skillet_env: Path, mock_codex_cli):
        """Tool calls from the codex run are captured on the result."""
        evals_dir = skillet_env / ".skillet" / "evals" / "codex-tools"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        mock_codex_cli.set_responses(
            (
                "Ran a command",
                [{"name": "command_execution", "input": {"command": "ls", "exit_code": 0}}],
            ),
            _verdict(True, "OK"),
        )

        result = await evaluate(
            "codex-tools",
            samples=1,
            parallel=1,
            skip_cache=True,
            agent=Agent.CODEX,
            skillet_dir=skillet_env / ".skillet",
        )

        assert result.total_runs == 1
        assert result.results[0].tool_calls == [
            {"name": "command_execution", "input": {"command": "ls", "exit_code": 0}}
        ]

    @pytest.mark.asyncio
    async def it_fails_loudly_when_codex_turn_fails(skillet_env: Path, mock_codex_cli):
        """A codex ``turn.failed`` (e.g. unsupported model) fails the eval, not silently passes."""
        evals_dir = skillet_env / ".skillet" / "evals" / "codex-turn-failed"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        failed_stream = "\n".join(
            [
                json.dumps({"type": "thread.started", "thread_id": "t"}),
                json.dumps({"type": "turn.failed", "error": {"message": "model not supported"}}),
            ]
        ).encode()
        mock_codex_cli.side_effect = [_FakeClaudeProc(failed_stream)]

        result = await evaluate(
            "codex-turn-failed",
            samples=1,
            parallel=1,
            skip_cache=True,
            agent=Agent.CODEX,
            skillet_dir=skillet_env / ".skillet",
        )

        assert result.total_runs == 1
        assert result.pass_rate == 0.0
        assert not result.results[0].passed
        assert "model not supported" in result.results[0].judgment["reasoning"]
