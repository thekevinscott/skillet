"""Tests for lock module."""

import tempfile
from pathlib import Path

import pytest

from skillet._internal.lock import cache_lock


def describe_cache_lock():
    """Tests for cache_lock function."""

    def it_creates_directory_if_needed():
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "new" / "nested" / "cache"
            assert not cache_dir.exists()

            with cache_lock(cache_dir):
                pass

            assert cache_dir.exists()

    def it_creates_lock_file():
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"

            with cache_lock(cache_dir):
                lock_file = cache_dir / ".lock"
                assert lock_file.exists()

    def it_allows_sequential_access():
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            counter = []

            with cache_lock(cache_dir):
                counter.append(1)

            with cache_lock(cache_dir):
                counter.append(2)

            assert counter == [1, 2]

    def it_blocks_on_nested_lock_attempt():
        """FileLock blocks on nested lock attempts (non-reentrant).

        This is expected behavior - our usage pattern in evaluate.py
        never nests locks, so this is fine.
        """
        from filelock import FileLock, Timeout

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"

            with cache_lock(cache_dir):
                # Nested lock with 0 timeout should fail immediately
                lock = FileLock(cache_dir / ".lock", timeout=0)
                with pytest.raises(Timeout):
                    lock.acquire()
