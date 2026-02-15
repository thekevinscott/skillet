"""Tests for text/truncate_response module."""

import pytest

from skillet._internal.text.truncate_response import truncate_response


def describe_truncate_response():
    @pytest.mark.parametrize(
        "input_text,max_length,expected_len",
        [
            ("short text", 500, 10),
            ("a" * 600, 500, 500),
            ("hello world", 5, 5),
        ],
    )
    def it_truncates_to_max_length(input_text, max_length, expected_len):
        result = truncate_response(input_text, max_length=max_length)
        assert len(result) == expected_len

    @pytest.mark.parametrize(
        "input_text,expected",
        [
            (None, ""),
            ("", ""),
        ],
    )
    def it_handles_empty_values(input_text, expected):
        assert truncate_response(input_text) == expected
