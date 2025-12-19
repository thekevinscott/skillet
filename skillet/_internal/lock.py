"""File locking utilities for cache operations."""

from contextlib import contextmanager
from pathlib import Path

from filelock import FileLock

# Lock timeout in seconds - fail fast if another process holds the lock too long
LOCK_TIMEOUT = 30


@contextmanager
def cache_lock(cache_dir: Path):
    """Acquire an exclusive lock for a cache directory.

    Uses a .lock file in the cache directory to coordinate access
    across parallel workers. The lock is held for both read and write
    operations to prevent TOCTOU race conditions.

    Args:
        cache_dir: The cache directory to lock

    Yields:
        None - the lock is held for the duration of the context
    """
    # Ensure parent directory exists for the lock file
    cache_dir.mkdir(parents=True, exist_ok=True)
    lock_path = cache_dir / ".lock"

    lock = FileLock(lock_path, timeout=LOCK_TIMEOUT)
    with lock:
        yield
