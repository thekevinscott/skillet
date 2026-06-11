"""Tests for the query_multiturn dispatcher."""

from unittest.mock import AsyncMock, patch

import pytest

from skillet._internal.sdk.query_multiturn import query_multiturn
from skillet._internal.sdk.query_result import QueryResult
from skillet.errors import UnknownHarnessError


def describe_query_multiturn():
    @pytest.mark.asyncio
    async def it_dispatches_to_the_selected_harness_adapter():
        adapter = AsyncMock(return_value=QueryResult(text="hi", tool_calls=[]))

        with patch(
            "skillet._internal.sdk.query_multiturn.get_adapter", return_value=adapter
        ) as mock_get:
            result = await query_multiturn(["prompt"], harness="codex", cwd="/work")

            mock_get.assert_called_once_with("codex")
            adapter.assert_awaited_once()
            assert adapter.await_args.args[0] == ["prompt"]
            assert adapter.await_args.kwargs["cwd"] == "/work"
            assert result.text == "hi"

    @pytest.mark.asyncio
    async def it_defaults_to_the_claude_harness():
        adapter = AsyncMock(return_value=QueryResult(text="hi", tool_calls=[]))

        with patch(
            "skillet._internal.sdk.query_multiturn.get_adapter", return_value=adapter
        ) as mock_get:
            await query_multiturn(["prompt"])

            mock_get.assert_called_once_with("claude")

    @pytest.mark.asyncio
    async def it_raises_for_unknown_harness():
        with pytest.raises(UnknownHarnessError, match="nope"):
            await query_multiturn(["prompt"], harness="nope")
