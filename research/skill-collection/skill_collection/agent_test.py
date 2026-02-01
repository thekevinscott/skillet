"""Unit tests for agent module."""

from skill_collection.agent import _parse_json_response


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
