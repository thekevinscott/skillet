"""Integration tests for the required --agent flag and CLI-routed agent under test."""

from pathlib import Path

import pytest
from cyclopts.exceptions import MissingArgumentError

from skillet import evaluate
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
        """Cached results live under an agent-specific path so agents never collide."""
        evals_dir = skillet_env / ".skillet" / "evals" / "cache-key-test"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml")

        mock_claude_cli.set_responses("A response")
        mock_claude_query.set_responses({"pass": True, "reasoning": "OK"})

        await evaluate("cache-key-test", samples=1, parallel=1, agent=Agent.CLAUDE)

        cache_dir = skillet_env / ".skillet" / "cache"
        claude_dirs = [p for p in cache_dir.rglob("claude") if p.is_dir()]
        codex_dirs = [p for p in cache_dir.rglob("codex") if p.is_dir()]
        assert claude_dirs, "expected a 'claude' segment in the cache path"
        assert not codex_dirs, "claude run must not write under a 'codex' path"

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
