"""Tests for save_iteration function."""

import tempfile
from pathlib import Path

from skillet._internal.cache import save_iteration


def describe_save_iteration():
    def it_creates_directory_if_needed():
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "new" / "nested" / "dir"
            save_iteration(cache_dir, 0, {"passed": True})

            assert cache_dir.exists()
            assert len(list(cache_dir.glob("iter-0.*"))) == 1

    def it_round_trips_data():
        from cachetta import Cachetta, read_cache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            data = {"passed": True, "reasoning": "looks good"}
            save_iteration(cache_dir, 5, data)

            iter_files = sorted(cache_dir.glob("iter-5.*"))
            assert len(iter_files) == 1

            cache = Cachetta(path=iter_files[0])
            with read_cache(cache) as cached_data:
                assert cached_data == data

    def it_overwrites_existing_file():
        from cachetta import Cachetta, read_cache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            save_iteration(cache_dir, 0, {"version": 1})
            save_iteration(cache_dir, 0, {"version": 2})

            iter_files = sorted(cache_dir.glob("iter-0.*"))
            assert len(iter_files) == 1

            cache = Cachetta(path=iter_files[0])
            with read_cache(cache) as cached_data:
                assert cached_data == {"version": 2}

    def it_stores_data_readable_by_cachetta():
        from cachetta import Cachetta, read_cache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            data = {"passed": True, "reasoning": "looks good", "iteration": 1}
            save_iteration(cache_dir, 1, data)

            # The saved file should be readable by cachetta
            iter_files = sorted(cache_dir.glob("iter-*"))
            assert len(iter_files) == 1

            cache = Cachetta(path=iter_files[0])
            with read_cache(cache) as cached_data:
                assert cached_data == data
