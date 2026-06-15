"""Tests for judge/parse_judgment module."""

import pytest

from skillet.eval.judge.parse_judgment import parse_judgment
from skillet.eval.judge.types import Judgment


def describe_parse_judgment():
    def it_parses_raw_json_object():
        result = parse_judgment('{"pass": true, "reasoning": "Looks good"}')

        assert isinstance(result, Judgment)
        assert result.passed is True
        assert result.reasoning == "Looks good"

    def it_parses_passed_field_name():
        result = parse_judgment('{"passed": false, "reasoning": "Nope"}')

        assert result.passed is False
        assert result.reasoning == "Nope"

    def it_strips_json_code_fence():
        text = '```json\n{"pass": true, "reasoning": "Fenced"}\n```'

        result = parse_judgment(text)

        assert result.passed is True
        assert result.reasoning == "Fenced"

    def it_strips_bare_code_fence():
        text = '```\n{"pass": false, "reasoning": "Bare fence"}\n```'

        result = parse_judgment(text)

        assert result.passed is False
        assert result.reasoning == "Bare fence"

    def it_extracts_json_embedded_in_prose():
        text = 'Here is my verdict: {"pass": true, "reasoning": "Embedded"} — done.'

        result = parse_judgment(text)

        assert result.passed is True
        assert result.reasoning == "Embedded"

    def it_defaults_missing_reasoning_to_empty_string():
        result = parse_judgment('{"pass": true}')

        assert result.passed is True
        assert result.reasoning == ""

    def it_raises_on_non_json_text():
        with pytest.raises(ValueError, match="valid JSON"):
            parse_judgment("I think the response was fine, honestly.")

    def it_raises_when_json_is_not_an_object():
        with pytest.raises(ValueError, match="object"):
            parse_judgment("[1, 2, 3]")

    def it_raises_when_schema_does_not_match():
        # Missing the required pass/passed field.
        with pytest.raises(ValueError, match="schema"):
            parse_judgment('{"reasoning": "no verdict field"}')
