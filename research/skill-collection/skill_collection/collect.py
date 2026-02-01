"""Collection functions for gathering SKILL.md files from GitHub."""

import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from .github import get_client
from .models import (
    EXPECTED_TOTAL,
    GITHUB_SEARCH_RESULT_LIMIT,
    ProgressRow,
    ShardResult,
    SizeRange,
)


def collect_shard(
    size_range: SizeRange,
    max_results: int = GITHUB_SEARCH_RESULT_LIMIT,
    on_page: Callable[[int, int, int], None] | None = None,
    dry_run: bool = False,
) -> tuple[ShardResult, list[dict]]:
    """Collect all results for a size range shard.

    If dry_run=True, only fetches count (no items collected).
    """
    client = get_client()
    query = size_range.to_search_query()

    # Dry run: just get the count
    if dry_run:
        response = client.search_code(query, per_page=1, page=1)
        return ShardResult(
            range=size_range,
            total_count=response.get("total_count", 0),
            collected=0,
            pages={},
        ), []

    items = []
    page_counts: dict[int, int] = {}
    page = 1
    total_count = 0

    per_page = 100
    while len(items) < max_results:
        response = client.search_code(query, per_page=per_page, page=page)
        total_count = response.get("total_count", 0)

        new_items = response.get("items", [])
        if not new_items:
            break

        page_counts[page] = len(new_items)
        items.extend(new_items)

        if on_page is not None:
            on_page(page, len(new_items), total_count)

        # Early exit: if total_count exceeds limit, this range needs subdivision.
        # No point fetching more pages - we'll discard and re-query with smaller ranges.
        if total_count > GITHUB_SEARCH_RESULT_LIMIT:
            break

        # Stop if we got fewer than requested (last page)
        if len(new_items) < per_page:
            break

        page += 1

        # GitHub hard limit at page 10 (1000 results)
        if page > 10:
            break

    return ShardResult(
        range=size_range,
        total_count=total_count,
        collected=len(items),
        pages=page_counts,
    ), items


def needs_subdivision(result: ShardResult) -> bool:
    """Check if a shard result indicates the range needs subdivision."""
    if result.total_count > GITHUB_SEARCH_RESULT_LIMIT:
        if result.range.width == 0:
            raise ValueError(
                f"Cannot subdivide single-byte range {result.range} "
                f"but it has {result.total_count} results (limit {GITHUB_SEARCH_RESULT_LIMIT}). "
                f"Data will be lost."
            )
        return True
    return False


def extract_file_info(item: dict) -> dict:
    """Extract relevant fields from a search result item."""
    return {
        "name": item.get("name"),
        "path": item.get("path"),
        "sha": item.get("sha"),
        "html_url": item.get("html_url"),
        "repository": {
            "full_name": item.get("repository", {}).get("full_name"),
            "html_url": item.get("repository", {}).get("html_url"),
            "description": item.get("repository", {}).get("description"),
        },
    }


def deduplicate_items(
    items: list[dict],
    seen_shas: set[str] | None = None,
) -> tuple[list[dict], set[str]]:
    """Deduplicate items by SHA, extracting file info."""
    if seen_shas is None:
        seen_shas = set()

    unique = []
    for item in items:
        sha = item.get("sha")
        if sha and sha not in seen_shas:
            seen_shas.add(sha)
            unique.append(extract_file_info(item))
    return unique, seen_shas


def write_progress_md(
    output_dir: Path,
    results: list[ShardResult],
    in_progress: dict | None = None,
    unique_count: int | None = None,
):
    """Write current progress to markdown file.

    Only completed shards are included in the total and table.
    In-progress work is shown separately at the top.
    Uses atomic write (write to temp file, then rename) to avoid empty file reads.
    """
    import os
    import tempfile

    # Use unique_count if provided (deduplicated), otherwise sum raw collected
    # Note: in_progress is NOT included in the total - only completed shards count
    if unique_count is not None:
        total_collected = unique_count
    else:
        total_collected = sum(r.collected for r in results)

    md_path = output_dir / "progress.md"

    # Build content in memory first
    lines = []
    lines.append("# SKILL.md Collection Progress\n\n")
    pct = (total_collected / EXPECTED_TOTAL * 100) if EXPECTED_TOTAL else 0
    lines.append(f"**Total collected:** {total_collected:,} / {EXPECTED_TOTAL:,} ({pct:.1f}%)\n\n")

    # Show in-progress shard at the top, separate from the completed table
    if in_progress:
        range_str = in_progress["range"]
        collected = in_progress.get("collected", 0)
        total_count = in_progress.get("total_count", 0)
        pages = in_progress.get("pages", {})
        page_count = len(pages)
        line = f"**Currently fetching:** {range_str} (page {page_count}, {collected:,} items"
        if total_count > 0:
            line += f" / {total_count:,} reported"
        line += ")\n\n"
        lines.append(line)

    lines.append("| Range | total_count | # |\n")
    lines.append("|-------|------------:|--:|\n")

    # Only include completed shards in the table
    rows: list[ProgressRow] = [result.to_progress_row() for result in results]

    # Sort by min_bytes descending (largest at top)
    rows.sort(key=lambda r: r.min_bytes, reverse=True)

    for row in rows:
        lines.append(row.format())

    content = "".join(lines)

    # Atomic write: write to temp file, then rename
    fd, tmp_path = tempfile.mkstemp(dir=output_dir, suffix=".md.tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        os.replace(tmp_path, md_path)
    except Exception:
        # Clean up temp file on error
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def append_urls(output_dir: Path, items: list[dict]):
    """Append URLs to skill_urls.txt incrementally."""
    urls_path = output_dir / "skill_urls.txt"
    with open(urls_path, "a") as f:
        for item in items:
            if item.get("html_url"):
                f.write(item["html_url"] + "\n")


def print_summary(results: list[ShardResult]):
    """Print collection summary to stdout."""
    total_reported = sum(r.total_count for r in results)
    total_collected = sum(r.collected for r in results)

    print()
    print("=" * 60)
    print(f"Total shards:    {len(results)}")
    print(f"Total reported:  {total_reported}")
    print(f"Total collected: {total_collected}")
    print("=" * 60)


def save_results(
    output_dir: Path,
    results: list[ShardResult],
    unique_items: list[dict] | None = None,
):
    """Save collection results to JSON files."""
    total_reported = sum(r.total_count for r in results)
    total_collected = sum(r.collected for r in results)

    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_shards": len(results),
        "total_reported": total_reported,
        "total_collected": total_collected,
        "shards": [r.to_dict() for r in results],
    }

    summary_path = output_dir / "summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSaved summary to {summary_path}")

    if unique_items is not None:
        files_path = output_dir / "skill_files.json"
        with open(files_path, "w") as f:
            json.dump(unique_items, f, indent=2)
        print(f"Saved {len(unique_items)} unique files to {files_path}")

        # Write URLs to text file (one per line)
        urls_path = output_dir / "skill_urls.txt"
        with open(urls_path, "w") as f:
            for item in unique_items:
                if item.get("html_url"):
                    f.write(item["html_url"] + "\n")
        print(f"Saved URLs to {urls_path}")
