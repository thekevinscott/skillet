"""Integration tests for per-eval harness selection (the agent under test).

An eval may declare a ``harness`` (e.g. ``codex``) to choose which agent
harness executes the prompt. The judge always stays on the Claude Agent SDK
regardless of the harness under test, for score comparability.
"""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from skillet import evaluate
from skillet._internal.sdk import QueryResult

from .conftest import create_eval_file


def describe_harness_selection():
    """Integration tests for the ``harness`` eval-config field."""

    @pytest.mark.asyncio
    async def it_routes_codex_evals_through_lite_harness(skillet_env: Path, mock_claude_query):
        """An eval with ``harness: codex`` runs the agent under test via lite-harness.

        The judge still uses the Claude Agent SDK (mocked here), so only one
        structured judgment response is configured on the Claude mock.
        """
        evals_dir = skillet_env / ".skillet" / "evals" / "codex-evals"
        evals_dir.mkdir(parents=True)
        create_eval_file(evals_dir / "001.yaml", prompt="Summarize the repo", harness="codex")

        # Only the judge runs on the Claude SDK: a single structured judgment.
        mock_claude_query.set_responses(
            {"pass": True, "reasoning": "Codex response meets expectations"},
        )

        with patch(
            "skillet._internal.sdk.harness.lite_harness.run_lite_harness",
            new_callable=AsyncMock,
        ) as mock_lite:
            mock_lite.return_value = QueryResult(text="Ahoy from Codex", tool_calls=[])

            result = await evaluate("codex-evals", samples=1, parallel=1, skip_cache=True)

        # The agent under test went through the lite-harness adapter as "codex".
        mock_lite.assert_awaited_once()
        call = mock_lite.await_args
        assert call.args[0] == ["Summarize the repo"]
        assert call.kwargs["harness"] == "codex"

        # The eval result reflects the Codex response, not the Claude SDK.
        assert result.results[0].response == "Ahoy from Codex"
        assert result.pass_rate == 100.0
