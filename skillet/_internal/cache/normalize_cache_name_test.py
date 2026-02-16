"""Tests for normalize_cache_name function."""

import tempfile
from pathlib import Path

from skillet._internal.cache import normalize_cache_name


def describe_normalize_cache_name():
    def it_returns_name_for_nonexistent_path():
        result = normalize_cache_name("nonexistent-path-12345")
        assert result == "nonexistent-path-12345"

    def it_returns_directory_name_for_existing_path():
        with tempfile.TemporaryDirectory() as tmpdir:
            result = normalize_cache_name(tmpdir)
            assert result == Path(tmpdir).name
