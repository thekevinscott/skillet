"""Tests for hash_content function."""

from skillet._internal.cache import hash_content


def describe_hash_content():
    def it_returns_12_char_hash():
        result = hash_content("test content")
        assert len(result) == 12

    def it_is_deterministic():
        assert hash_content("hello") == hash_content("hello")

    def it_differs_for_different_content():
        assert hash_content("hello") != hash_content("world")
