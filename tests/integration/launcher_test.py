"""Integration tests for run-time agent selection via a launcher command.

The agent under test is chosen at run time with ``evaluate(launcher=...)`` (or
the ``--launcher`` CLI flag), never from the eval file, so the same evals stay
portable. The judge always stays on the Claude Agent SDK regardless of the
launcher, for score comparability.
"""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from skillet import evaluate
from skillet._internal.sdk import QueryResult

from .conftest import create_eval_file


def describe_launcher_selection():
    """Integration tests for the ``launcher`` run-time argument."""

    @pytest.mark.asyncio
    async def it_routes_runs_through_the_launcher(skillet_env: Path, mock_claude_query):
        """``evaluate(launcher=...)`` runs the agent under test via the launcher.

        The same eval file carries no agent field. The judge still uses the
        Claude Agent SDK (mocked here), so only one structured judgment response
        is configured on the Claude mock.
        """
        evals_dir = skillet_env / ".skillet" / "evals" / "portable-evals"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml", prompt="Summarize the repo")

        # Only the judge runs on the Claude SDK: a single structured judgment.
        mock_claude_query.set_responses(
            {"pass": True, "reasoning": "Launcher response meets expectations"},
        )

        with patch(
            "skillet._internal.sdk.query_multiturn.run_launcher",
            new_callable=AsyncMock,
        ) as mock_launcher:
            mock_launcher.return_value = QueryResult(text="Ahoy from Codex", tool_calls=[])

            result = await evaluate(
                "portable-evals", samples=1, parallel=1, skip_cache=True, launcher="codex exec"
            )

        # The agent under test went through the launcher runner.
        mock_launcher.assert_awaited_once()
        call = mock_launcher.await_args
        assert call.args[0] == ["Summarize the repo"]
        assert call.kwargs["launcher"] == "codex exec"

        # The eval result reflects the launcher response, not the Claude SDK.
        assert result.results[0].response == "Ahoy from Codex"
        assert result.pass_rate == 100.0
