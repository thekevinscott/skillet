"""Tests for type utilities."""

import pytest

from skillet._internal.types import matches_type


def describe_matches_type():
    """Tests for matches_type function."""

    @pytest.mark.parametrize(
        "obj,accepted_type,expected",
        [
            ("hello", str, True),
            (123, int, True),
            ([], list, True),
            ("hello", int, False),
            (123, str, False),
            (True, int, True),  # bool is subclass of int
        ],
    )
    def it_matches_single_type(obj, accepted_type, expected):
        assert matches_type(obj, accepted_type) is expected

    @pytest.mark.parametrize(
        "obj,accepted_types,expected",
        [
            ("hello", [str, int], True),
            (123, [str, int], True),
            ([], [str, int], False),
        ],
    )
    def it_matches_list_of_types(obj, accepted_types, expected):
        assert matches_type(obj, accepted_types) is expected
