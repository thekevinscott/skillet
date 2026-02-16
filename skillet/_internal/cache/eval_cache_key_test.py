"""Tests for eval_cache_key function."""

import pytest

from skillet._internal.cache import eval_cache_key


def describe_eval_cache_key():
    def it_is_deterministic():
        key1 = eval_cache_key("test.yaml", "prompt: hello\nexpected: world")
        key2 = eval_cache_key("test.yaml", "prompt: hello\nexpected: world")
        assert key1 == key2

    @pytest.mark.parametrize(
        "content1,content2",
        [
            ("prompt: hello", "prompt: goodbye"),
            ("expected: foo", "expected: bar"),
            ("a: 1", "a: 2"),
        ],
    )
    def it_differs_on_content(content1, content2):
        key1 = eval_cache_key("test.yaml", content1)
        key2 = eval_cache_key("test.yaml", content2)
        assert key1 != key2

    @pytest.mark.parametrize(
        "source1,source2",
        [
            ("test1.yaml", "test2.yaml"),
            ("a.yaml", "b.yaml"),
        ],
    )
    def it_differs_on_source(source1, source2):
        key1 = eval_cache_key(source1, "prompt: hello")
        key2 = eval_cache_key(source2, "prompt: hello")
        assert key1 != key2

    def it_strips_yaml_extension():
        key = eval_cache_key("myeval.yaml", "content")
        assert "myeval-" in key
        assert ".yaml" not in key
