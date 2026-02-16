"""Tests for hash_file function."""

import tempfile
from pathlib import Path

from skillet._internal.cache import hash_file


def describe_hash_file():
    def it_hashes_file_contents():
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.txt"
            path.write_text("test content")
            result = hash_file(path)
            assert len(result) == 12

    def it_is_deterministic():
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.txt"
            path.write_text("test content")
            assert hash_file(path) == hash_file(path)
