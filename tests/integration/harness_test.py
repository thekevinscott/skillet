"""Integration tests for run-time harness selection (the agent under test).

The harness is chosen at run time via ``evaluate(harness=...)`` (or the
``--harness`` CLI flag), never from the eval file, so the same evals stay
portable. The judge always stays on the Claude Agent SDK regardless of the
harness under test, for score comparability.
"""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from skillet import evaluate
from skillet._internal.sdk import QueryResult

from .conftest import create_eval_file


def describe_harness_selection():
    """Integration tests for the ``harness`` run-time argument."""

    @pytest.mark.asyncio
    async def it_routes_codex_runs_through_lite_harness(skillet_env: Path, mock_claude_query):
        """``evaluate(harness="codex")`` runs the agent under test via lite-harness.

        The same eval file carries no harness field. The judge still uses the
        Claude Agent SDK (mocked here), so only one structured judgment response
        is configured on the Claude mock.
        """
        evals_dir = skillet_env / ".skillet" / "evals" / "portable-evals"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml", prompt="Summarize the repo")

        # Only the judge runs on the Claude SDK: a single structured judgment.
        mock_claude_query.set_responses(
            {"pass": True, "reasoning": "Codex response meets expectations"},
        )

        with patch(
            "skillet._internal.sdk.harness.lite_harness.run_lite_harness",
            new_callable=AsyncMock,
        ) as mock_lite:
            mock_lite.return_value = QueryResult(text="Ahoy from Codex", tool_calls=[])

            result = await evaluate(
                "portable-evals", samples=1, parallel=1, skip_cache=True, harness="codex"
            )

        # The agent under test went through the lite-harness adapter as "codex".
        mock_lite.assert_awaited_once()
        call = mock_lite.await_args
        assert call.args[0] == ["Summarize the repo"]
        assert call.kwargs["harness"] == "codex"

        # The eval result reflects the Codex response, not the Claude SDK.
        assert result.results[0].response == "Ahoy from Codex"
        assert result.pass_rate == 100.0
