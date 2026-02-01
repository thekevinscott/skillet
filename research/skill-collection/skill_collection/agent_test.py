"""Unit tests for agent module."""

import asyncio
from unittest.mock import patch

import pytest

from skill_collection.agent import _parse_json_response, query_json


def describe_parse_json_response():
    def it_parses_plain_json():
        result = _parse_json_response('{"key": "value"}')
        assert result == {"key": "value"}

    def it_parses_json_in_code_block():
        result = _parse_json_response('```json\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def it_parses_json_in_code_block_without_language():
        result = _parse_json_response('```\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def it_handles_whitespace():
        result = _parse_json_response('  \n{"key": "value"}\n  ')
        assert result == {"key": "value"}

    def it_returns_none_for_invalid_json():
        result = _parse_json_response("not json")
        assert result is None

    def it_returns_none_for_empty_code_block():
        result = _parse_json_response("```")
        assert result is None

    def it_returns_none_for_empty_string():
        result = _parse_json_response("")
        assert result is None

    def it_handles_nested_json():
        result = _parse_json_response('{"outer": {"inner": 1}}')
        assert result == {"outer": {"inner": 1}}


def describe_query_json():
    @pytest.fixture(autouse=True)
    def mock_sdk_query():
        with patch("skill_collection.agent.query") as mock:
            yield mock

    def it_returns_cached_result_when_available(tmp_path, mock_sdk_query):
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()

        # Pre-populate cache
        from skill_collection.cache import CacheManager

        cache = CacheManager(cache_dir=cache_dir)
        prompt = "test prompt"
        expected = {"cached": True}
        cache.set(prompt, expected)

        result, from_cache = asyncio.run(query_json(prompt, cache_dir=cache_dir))

        assert result == expected
        assert from_cache is True
        mock_sdk_query.assert_not_called()

    def it_caches_successful_api_result(tmp_path, mock_sdk_query):
        from claude_agent_sdk import ResultMessage

        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()

        async def mock_query(**kwargs):
            yield ResultMessage(
                subtype="result",
                duration_ms=0,
                duration_api_ms=0,
                is_error=False,
                num_turns=1,
                session_id="test",
                result='{"success": true}',
            )

        mock_sdk_query.side_effect = mock_query

        result, from_cache = asyncio.run(query_json("new prompt", cache_dir=cache_dir))

        assert result == {"success": True}
        assert from_cache is False

        # Verify it was cached
        from skill_collection.cache import CacheManager

        cache = CacheManager(cache_dir=cache_dir)
        cached = cache.get("new prompt")
        assert cached == {"success": True}

    def it_returns_none_on_api_error(tmp_path, mock_sdk_query):
        from claude_agent_sdk import ResultMessage

        async def mock_query(**kwargs):
            yield ResultMessage(
                subtype="result",
                duration_ms=0,
                duration_api_ms=0,
                is_error=True,
                num_turns=1,
                session_id="test",
                result="Error occurred",
            )

        mock_sdk_query.side_effect = mock_query

        result, from_cache = asyncio.run(query_json("prompt", cache_dir=tmp_path))

        assert result is None
        assert from_cache is False

    def it_returns_none_on_exception(mock_sdk_query):
        async def mock_query(**kwargs):
            raise RuntimeError("Network error")
            yield  # Make it a generator

        mock_sdk_query.side_effect = mock_query

        result, from_cache = asyncio.run(query_json("prompt"))

        assert result is None
        assert from_cache is False

    def it_returns_none_on_invalid_json_response(mock_sdk_query):
        from claude_agent_sdk import ResultMessage

        async def mock_query(**kwargs):
            yield ResultMessage(
                subtype="result",
                duration_ms=0,
                duration_api_ms=0,
                is_error=False,
                num_turns=1,
                session_id="test",
                result="not valid json",
            )

        mock_sdk_query.side_effect = mock_query

        result, from_cache = asyncio.run(query_json("prompt"))

        assert result is None
        assert from_cache is False

    def it_works_without_cache_dir(mock_sdk_query):
        from claude_agent_sdk import ResultMessage

        async def mock_query(**kwargs):
            yield ResultMessage(
                subtype="result",
                duration_ms=0,
                duration_api_ms=0,
                is_error=False,
                num_turns=1,
                session_id="test",
                result='{"no_cache": true}',
            )

        mock_sdk_query.side_effect = mock_query

        result, from_cache = asyncio.run(query_json("prompt"))

        assert result == {"no_cache": True}
        assert from_cache is False
