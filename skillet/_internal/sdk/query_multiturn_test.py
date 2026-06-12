"""Tests for the query_multiturn dispatcher."""

from unittest.mock import AsyncMock, patch

import pytest

from skillet._internal.sdk.query_multiturn import query_multiturn
from skillet._internal.sdk.query_result import QueryResult


def describe_query_multiturn():
    @pytest.mark.asyncio
    async def it_runs_on_the_native_claude_sdk_by_default():
        with patch(
            "skillet._internal.sdk.query_multiturn.run_claude", new_callable=AsyncMock
        ) as mock_claude:
            mock_claude.return_value = QueryResult(text="hi", tool_calls=[])

            result = await query_multiturn(["prompt"], max_turns=10)

            mock_claude.assert_awaited_once_with(["prompt"], max_turns=10)
            assert result.text == "hi"

    @pytest.mark.asyncio
    async def it_runs_through_the_launcher_when_provided():
        with patch(
            "skillet._internal.sdk.query_multiturn.run_launcher", new_callable=AsyncMock
        ) as mock_launcher:
            mock_launcher.return_value = QueryResult(text="codex", tool_calls=[])

            result = await query_multiturn(["prompt"], launcher="codex exec", cwd="/work")

            mock_launcher.assert_awaited_once_with(["prompt"], launcher="codex exec", cwd="/work")
            assert result.text == "codex"
