"""Content fetcher for v2 pipeline.

Fetches file content from GitHub and stores in SQLite content table.
Uses existing content/ directory as cache for transition period.
"""

import base64
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .db import get_db, get_db_context
from .github import get_client
from .utils import parse_github_url, resolve_content_path


def get_unfetched_skills(db_path: Path | None = None, limit: int | None = None) -> list[tuple[str, str]]:
    """Get skills that don't have content fetched yet.

    Returns list of (sha, url) tuples.
    """
    with get_db_context(db_path) as conn:
        query = """
            SELECT s.sha, s.url
            FROM skills s
            LEFT JOIN content c ON s.sha = c.sha
            WHERE c.sha IS NULL
            ORDER BY s.discovered_at
        """
        if limit:
            query += f" LIMIT {limit}"

        rows = conn.execute(query).fetchall()
        return [(row["sha"], row["url"]) for row in rows]


def fetch_content_from_url(url: str) -> tuple[str | None, int]:
    """Fetch content from a GitHub URL.

    Returns (content, byte_size) or (None, 0) on error.
    """
    parsed = parse_github_url(url)
    if not parsed:
        return None, 0

    owner, repo, ref, path = parsed
    client = get_client()

    try:
        data = client.get_file_content(owner, repo, path, ref=ref)
        if "content" in data:
            content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
            return content, len(content.encode("utf-8"))
    except Exception:
        pass

    return None, 0


def fetch_content_from_cache(
    url: str,
    content_dir: Path,
) -> tuple[str | None, int]:
    """Try to fetch content from local cache directory.

    Returns (content, byte_size) or (None, 0) if not cached.
    """
    parsed = parse_github_url(url)
    if not parsed:
        return None, 0

    owner, repo, ref, path = parsed
    local_path = resolve_content_path(content_dir, owner, repo, ref, path)

    if local_path.exists():
        content = local_path.read_text()
        return content, len(content.encode("utf-8"))

    return None, 0


def store_content(
    sha: str,
    body: str,
    byte_size: int,
    db_path: Path | None = None,
):
    """Store fetched content in the database."""
    with get_db_context(db_path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO content (sha, body, byte_size, fetched_at) "
            "VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
            (sha, body, byte_size),
        )


def run_fetch(
    db_path: Path | None = None,
    content_dir: Path | None = None,
    limit: int | None = None,
    concurrency: int = 10,
    on_progress: Callable[[int, int, int, int], None] | None = None,
) -> dict:
    """Fetch content for skills without content.

    If content_dir is provided, checks there first before making API calls.
    This allows using the existing content/ cache during transition.

    Returns stats about the fetch run.
    """
    skills = get_unfetched_skills(db_path, limit)
    total = len(skills)

    if total == 0:
        return {
            "total": 0,
            "fetched": 0,
            "cached": 0,
            "errors": 0,
        }

    counters = {"fetched": 0, "cached": 0, "errors": 0, "processed": 0}
    lock = threading.Lock()

    def fetch_one(sha: str, url: str):
        content = None
        byte_size = 0
        from_cache = False

        # Try cache first if available
        if content_dir:
            content, byte_size = fetch_content_from_cache(url, content_dir)
            if content:
                from_cache = True

        # Fall back to API
        if not content:
            content, byte_size = fetch_content_from_url(url)

        if content:
            store_content(sha, content, byte_size, db_path)
            with lock:
                if from_cache:
                    counters["cached"] += 1
                else:
                    counters["fetched"] += 1
        else:
            with lock:
                counters["errors"] += 1

        with lock:
            counters["processed"] += 1
            if on_progress:
                on_progress(
                    counters["processed"],
                    counters["fetched"],
                    counters["cached"],
                    counters["errors"],
                )

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {executor.submit(fetch_one, sha, url): (sha, url) for sha, url in skills}
        for future in as_completed(futures):
            future.result()  # Propagate exceptions

    return {
        "total": total,
        "fetched": counters["fetched"],
        "cached": counters["cached"],
        "errors": counters["errors"],
    }
