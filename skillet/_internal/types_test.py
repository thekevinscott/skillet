"""Tests for type utilities."""

from skillet._internal.types import matches_type


def describe_matches_type():
    """Tests for matches_type function."""

    def it_matches_single_type():
        assert matches_type("hello", str) is True
        assert matches_type(123, int) is True
        assert matches_type([], list) is True

    def it_rejects_wrong_type():
        assert matches_type("hello", int) is False
        assert matches_type(123, str) is False

    def it_matches_list_of_types():
        assert matches_type("hello", [str, int]) is True
        assert matches_type(123, [str, int]) is True

    def it_rejects_when_none_match():
        assert matches_type([], [str, int]) is False

    def it_handles_subclasses():
        assert matches_type(True, int) is True  # bool is subclass of int
