"""SQLite-based collection for v2 pipeline.

Provides resumable collection with multi-dimensional sharding:
1. Primary: file size ranges (existing approach)
2. Secondary: date ranges (when size ranges still exceed 1000)

Data flows into SQLite natively - existing caches make re-runs fast.
"""

from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path

from .db import get_db_context, init_db
from .github import get_client
from .models import GITHUB_SEARCH_RESULT_LIMIT, SIZE_RANGES, SizeRange

# Date range constants for secondary sharding
DATE_START = datetime(2023, 1, 1)  # Claude Code launch was ~March 2024
DATE_END = datetime.now()


def build_query(size_range: SizeRange, date_start: datetime | None = None, date_end: datetime | None = None) -> str:
    """Build a GitHub code search query with optional date constraint."""
    base = size_range.to_search_query()
    if date_start and date_end:
        # GitHub uses ISO date format without time
        start_str = date_start.strftime("%Y-%m-%d")
        end_str = date_end.strftime("%Y-%m-%d")
        return f"{base}+created:{start_str}..{end_str}"
    return base


def init_collection(db_path: Path | None = None) -> int:
    """Initialize collection by seeding shards table with initial size ranges.

    Returns the number of shards created.
    """
    init_db(db_path)

    with get_db_context(db_path) as conn:
        created = 0
        for size_range in SIZE_RANGES:
            query = build_query(size_range)
            try:
                conn.execute(
                    "INSERT INTO shards (query, started_at) VALUES (?, NULL)",
                    (query,)
                )
                created += 1
            except Exception:
                # Query already exists (resuming)
                pass
        return created


def get_next_shard(db_path: Path | None = None) -> tuple[int, str] | None:
    """Get the next incomplete shard to process.

    Returns (shard_id, query) or None if all shards are complete.
    """
    with get_db_context(db_path) as conn:
        row = conn.execute(
            "SELECT id, query FROM shards WHERE completed_at IS NULL ORDER BY id LIMIT 1"
        ).fetchone()
        if row:
            return row["id"], row["query"]
        return None


def mark_shard_started(shard_id: int, db_path: Path | None = None):
    """Mark a shard as started."""
    with get_db_context(db_path) as conn:
        conn.execute(
            "UPDATE shards SET started_at = CURRENT_TIMESTAMP WHERE id = ?",
            (shard_id,)
        )


def mark_shard_complete(shard_id: int, total_count: int, collected: int, db_path: Path | None = None):
    """Mark a shard as complete with result counts."""
    with get_db_context(db_path) as conn:
        conn.execute(
            "UPDATE shards SET total_count = ?, collected = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (total_count, collected, shard_id)
        )


def subdivide_shard(
    shard_id: int,
    query: str,
    db_path: Path | None = None
) -> list[str]:
    """Subdivide a shard that exceeded 1000 results.

    First tries size-based subdivision. If the size range is already minimal,
    falls back to date-based subdivision.

    Deletes the old shard and inserts new ones.
    Returns the list of new queries created.
    """
    # Parse the existing query to understand what we're subdividing
    # Query format: "filename:SKILL.md+size:X..Y" or "filename:SKILL.md+size:X..Y+created:DATE..DATE"
    new_queries = []

    # Try to extract the size range from the query
    size_part = None
    date_part = None
    for part in query.split("+"):
        if part.startswith("size:"):
            size_part = part
        elif part.startswith("created:"):
            date_part = part

    if size_part:
        # Parse size range
        size_str = size_part.replace("size:", "")
        if size_str.startswith(">="):
            size_range = SizeRange(int(size_str[2:]), None)
        elif ".." in size_str:
            min_str, max_str = size_str.split("..")
            size_range = SizeRange(int(min_str), int(max_str))
        else:
            # Single value - can't subdivide further by size
            size_range = SizeRange(int(size_str), int(size_str))

        # Can we subdivide by size?
        if size_range.width > 0:
            first_half, second_half = size_range.subdivide()
            if date_part:
                # Preserve existing date constraint
                new_queries.append(f"filename:SKILL.md+{first_half.to_query_param()}+{date_part}")
                new_queries.append(f"filename:SKILL.md+{second_half.to_query_param()}+{date_part}")
            else:
                new_queries.append(build_query(first_half))
                new_queries.append(build_query(second_half))
        else:
            # Size range is minimal (width=0), need to subdivide by date
            new_queries = _subdivide_by_date(size_range, date_part)

    with get_db_context(db_path) as conn:
        # Delete the old shard
        conn.execute("DELETE FROM shards WHERE id = ?", (shard_id,))

        # Insert new shards (ignore if query already exists)
        for new_query in new_queries:
            conn.execute(
                "INSERT OR IGNORE INTO shards (query, started_at) VALUES (?, NULL)",
                (new_query,)
            )

    return new_queries


def _subdivide_by_date(size_range: SizeRange, date_part: str | None) -> list[str]:
    """Create date-based subdivisions for a size range."""
    if date_part:
        # Parse existing date range and split it
        date_str = date_part.replace("created:", "")
        start_str, end_str = date_str.split("..")
        start = datetime.strptime(start_str, "%Y-%m-%d")
        end = datetime.strptime(end_str, "%Y-%m-%d")
    else:
        # First time using dates - use full range
        start = DATE_START
        end = DATE_END

    # Split the date range in half
    mid = start + (end - start) / 2

    new_queries = []
    size_param = size_range.to_query_param()

    # First half
    first_start = start.strftime("%Y-%m-%d")
    first_end = mid.strftime("%Y-%m-%d")
    new_queries.append(f"filename:SKILL.md+{size_param}+created:{first_start}..{first_end}")

    # Second half
    second_start = (mid + timedelta(days=1)).strftime("%Y-%m-%d")
    second_end = end.strftime("%Y-%m-%d")
    new_queries.append(f"filename:SKILL.md+{size_param}+created:{second_start}..{second_end}")

    return new_queries


def record_results(
    shard_id: int,
    items: list[dict],
    db_path: Path | None = None
) -> int:
    """Record collected items to the skills table.

    Uses INSERT OR IGNORE to handle duplicates (by SHA).
    Returns the number of new items inserted.
    """
    with get_db_context(db_path) as conn:
        inserted = 0
        for item in items:
            sha = item.get("sha")
            url = item.get("html_url")
            if sha and url:
                cursor = conn.execute(
                    "INSERT OR IGNORE INTO skills (sha, url, shard_id) VALUES (?, ?, ?)",
                    (sha, url, shard_id)
                )
                if cursor.rowcount > 0:
                    inserted += 1
        return inserted


def collect_shard_v2(
    shard_id: int,
    query: str,
    on_page: Callable[[int, int, int], None] | None = None,
    db_path: Path | None = None,
) -> tuple[int, int, list[dict]]:
    """Collect results for a single shard.

    Returns (total_count, collected_count, items).
    Items are the raw GitHub API response items.
    """
    client = get_client()

    items = []
    page = 1
    total_count = 0
    per_page = 100

    while len(items) < GITHUB_SEARCH_RESULT_LIMIT:
        response = client.search_code(query, per_page=per_page, page=page)
        total_count = response.get("total_count", 0)

        new_items = response.get("items", [])
        if not new_items:
            break

        items.extend(new_items)

        if on_page:
            on_page(page, len(new_items), total_count)

        # Early exit if this range needs subdivision
        if total_count > GITHUB_SEARCH_RESULT_LIMIT:
            break

        # Last page
        if len(new_items) < per_page:
            break

        page += 1
        if page > 10:  # GitHub hard limit
            break

    return total_count, len(items), items


def run_collection(
    db_path: Path | None = None,
    on_progress: Callable[[str, int, int], None] | None = None,
) -> dict:
    """Run the full collection process.

    Processes shards until all are complete. Handles subdivision automatically.
    Returns stats about the collection run.
    """
    stats = {
        "shards_processed": 0,
        "shards_subdivided": 0,
        "skills_collected": 0,
        "skills_new": 0,
    }

    while True:
        shard = get_next_shard(db_path)
        if not shard:
            break

        shard_id, query = shard
        mark_shard_started(shard_id, db_path)

        if on_progress:
            on_progress(query, stats["skills_collected"], stats["shards_processed"])

        total_count, collected, items = collect_shard_v2(shard_id, query, db_path=db_path)

        if total_count > GITHUB_SEARCH_RESULT_LIMIT:
            # Need to subdivide
            subdivide_shard(shard_id, query, db_path)
            stats["shards_subdivided"] += 1
            continue

        # Record results
        new_count = record_results(shard_id, items, db_path)
        mark_shard_complete(shard_id, total_count, collected, db_path)

        stats["shards_processed"] += 1
        stats["skills_collected"] += collected
        stats["skills_new"] += new_count

    return stats
