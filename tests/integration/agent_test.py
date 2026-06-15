"""Integration tests for the required --agent flag and CLI-routed agent under test."""

from pathlib import Path
from unittest.mock import patch

import pytest
from cyclopts.exceptions import MissingArgumentError

from skillet import evaluate
from skillet._internal.cache import build_iteration_cache
from skillet.agent import Agent
from skillet.cli.main import app

from .conftest import create_eval_file


def describe_agent_flag():
    """The --agent flag is required and selects the CLI-routed agent under test."""

    def it_errors_when_agent_flag_is_omitted():
        """Omitting --agent is a parse error — there is no default."""
        with pytest.raises(MissingArgumentError, match="--agent"):
            app(["eval", "my-evals"], exit_on_error=False)

    def it_rejects_unknown_agent_value():
        """An unrecognized agent value is rejected at parse time."""
        with pytest.raises(Exception, match=r"(?i)agent"):
            app(["eval", "my-evals", "--agent", "not-an-agent"], exit_on_error=False)

    @pytest.mark.asyncio
    async def it_folds_agent_into_the_cache_key(
        skillet_env: Path, mock_claude_cli, mock_claude_query
    ):
        """evaluate threads the selected agent into the cache builder, so cached
        results live under an agent-specific path and agents never collide.

        The agent's exact placement in the path is unit-tested in
        build_iteration_cache_test; integration tests neutralize cachetta's disk
        I/O, so we assert the agent reaches the builder here.
        """
        evals_dir = skillet_env / ".skillet" / "evals" / "cache-key-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        mock_claude_cli.set_responses("A response")
        mock_claude_query.set_responses({"pass": True, "reasoning": "OK"})

        with patch(
            "skillet.eval.evaluate.evaluate.build_iteration_cache",
            wraps=build_iteration_cache,
        ) as spy:
            await evaluate("cache-key-test", samples=1, parallel=1, agent=Agent.CLAUDE)

        spy.assert_called_once()
        assert Agent.CLAUDE in spy.call_args.args

    @pytest.mark.asyncio
    async def it_parses_stream_json_into_text_and_tool_calls(skillet_env: Path, mock_claude_cli):
        """The CLI stream-json output is parsed into response text and tool calls."""
        evals_dir = skillet_env / ".skillet" / "evals" / "stream-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(
            evals_dir / "001.yaml",
            prompt="Use the skill",
            expected="Uses the skill",
            assertions=[{"type": "contains", "value": "skill"}],
        )

        # The mocked subprocess emits stream-json; parse_claude_stream runs for real.
        mock_claude_cli.set_responses(
            ("Used the skill", [{"name": "Skill", "input": {"skill": "demo"}}])
        )

        result = await evaluate(
            "stream-test", samples=1, parallel=1, skip_cache=True, agent=Agent.CLAUDE
        )

        assert result.total_runs == 1
        assert result.results[0].passed
        assert result.results[0].tool_calls == [{"name": "Skill", "input": {"skill": "demo"}}]
