"""Tests for get_cached_iterations function."""

import tempfile
from pathlib import Path

from skillet._internal.cache import get_cached_iterations, save_iteration


def describe_get_cached_iterations():
    def it_returns_empty_list_for_nonexistent_dir():
        result = get_cached_iterations(Path("/nonexistent/path/12345"))
        assert result == []

    def it_loads_iteration_files():
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            save_iteration(cache_dir, 0, {"passed": True, "reasoning": "good"})
            save_iteration(cache_dir, 1, {"passed": False, "reasoning": "bad"})

            result = get_cached_iterations(cache_dir)
            assert len(result) == 2
            assert result[0]["passed"] is True
            assert result[1]["passed"] is False

    def it_returns_sorted_results():
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            save_iteration(cache_dir, 2, {"index": 2})
            save_iteration(cache_dir, 0, {"index": 0})
            save_iteration(cache_dir, 1, {"index": 1})

            result = get_cached_iterations(cache_dir)
            assert result[0]["index"] == 0
            assert result[1]["index"] == 1
            assert result[2]["index"] == 2

    def it_reads_cachetta_files():
        from cachetta import Cachetta, write_cache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            for i in range(3):
                cache = Cachetta(path=cache_dir / f"iter-{i}.cache")
                write_cache(cache, {"index": i, "passed": i % 2 == 0})

            result = get_cached_iterations(cache_dir)
            assert len(result) == 3
            assert result[0] == {"index": 0, "passed": True}
            assert result[1] == {"index": 1, "passed": False}
            assert result[2] == {"index": 2, "passed": True}
