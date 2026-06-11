"""Tests for the harness adapter registry."""

from unittest.mock import AsyncMock, patch

import pytest

from skillet._internal.sdk.harness.registry import (
    HARNESS_NAMES,
    get_adapter,
    run_claude,
)
from skillet._internal.sdk.query_result import QueryResult
from skillet.errors import UnknownHarnessError


def describe_get_adapter():
    def it_returns_the_native_claude_adapter():
        assert get_adapter("claude") is run_claude

    def it_lists_claude_and_codex_as_known_harnesses():
        assert "claude" in HARNESS_NAMES
        assert "codex" in HARNESS_NAMES

    def it_raises_for_an_unknown_harness():
        with pytest.raises(UnknownHarnessError, match="Available harnesses"):
            get_adapter("bogus")

    @pytest.mark.asyncio
    async def it_routes_the_codex_adapter_to_lite_harness():
        with patch(
            "skillet._internal.sdk.harness.lite_harness.run_lite_harness", new_callable=AsyncMock
        ) as mock_lite:
            mock_lite.return_value = QueryResult(text="ok", tool_calls=[])

            adapter = get_adapter("codex")
            await adapter(["prompt"], cwd="/work")

            mock_lite.assert_awaited_once_with(["prompt"], harness="codex", cwd="/work")
