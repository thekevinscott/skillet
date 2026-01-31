"""Collect SKILL.md files from GitHub using size-sharded queries.

GitHub's code search API limits results to 1000 per query. By sharding
queries by file size, we can collect more results (up to 1000 per size range).
"""

import argparse
import json
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .github import get_client, parse_github_url

DEFAULT_CHUNK_SIZE = 100  # Default chunk size for subdivision ranges


def status(msg: str):
    """Print a status message, overwriting the current line."""
    sys.stdout.write(f"\r\033[K{msg}")
    sys.stdout.flush()


@dataclass
class SizeRange:
    """A file size range for sharding queries."""

    min_bytes: int
    max_bytes: int | None = None  # None means no upper bound

    @property
    def width(self) -> int:
        """Width of the range in bytes."""
        if self.max_bytes is None:
            return self.min_bytes  # Use min as width for unbounded
        return self.max_bytes - self.min_bytes

    def to_query_param(self) -> str:
        """Convert to GitHub size qualifier."""
        if self.max_bytes is None:
            return f"size:>={self.min_bytes}"
        return f"size:{self.min_bytes}..{self.max_bytes}"

    def to_search_query(self, filename: str = "SKILL.md") -> str:
        """Build a GitHub code search query for this range."""
        return f"filename:{filename}+{self.to_query_param()}"

    def subdivide(self, chunk_size: int = DEFAULT_CHUNK_SIZE) -> tuple["SizeRange", "SizeRange"]:
        """Split into first half and a chunk_size range starting at midpoint.

        For bounded ranges: after multiple subdivisions, the next range always
        uses chunk_size to maintain consistent chunking (rather than progressively
        smaller ranges).

        For unbounded ranges: doubles the starting point (exponential exploration
        for very large files).

        Returns:
            Tuple of (first_half, next_range)
        """
        if self.max_bytes is None:
            # Unbounded: use exponential doubling for large files
            mid = self.min_bytes * 2
            return (
                SizeRange(self.min_bytes, mid - 1),
                SizeRange(mid, None),
            )

        mid = self.min_bytes + self.width // 2
        return (
            SizeRange(self.min_bytes, mid),
            SizeRange(mid + 1, mid + chunk_size),
        )

    def __str__(self) -> str:
        if self.max_bytes is None:
            return f">{self.min_bytes}"
        return f"{self.min_bytes}-{self.max_bytes}"


@dataclass
class ShardResult:
    """Result of collecting a single shard."""

    range: SizeRange
    total_count: int
    collected: int
    pages: dict[int, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {
            "range": str(self.range),
            "range_query": self.range.to_query_param(),
            "total_count": self.total_count,
            "collected": self.collected,
            "pages": self.pages,
        }

    def to_progress_row(self, bold: bool = False) -> "ProgressRow":
        """Convert to a progress row for display."""
        return ProgressRow(
            min_bytes=self.range.min_bytes,
            range_str=str(self.range),
            collected=self.collected,
            pages=self.pages,
            bold=bold,
        )


@dataclass
class ProgressRow:
    """A row in the progress table, sortable by min_bytes."""

    min_bytes: int
    range_str: str
    collected: int
    pages: dict[int, int]
    bold: bool = False

    def format(self) -> str:
        """Format as markdown table row."""
        range_cell = f"**{self.range_str}**" if self.bold else self.range_str
        page_cells = [str(self.pages.get(i, "")) for i in range(1, 11)]
        return f"| {range_cell} | {self.collected:,} | " + " | ".join(page_cells) + " |\n"


# Size ranges chosen to keep each shard under 1000 results
SIZE_RANGES = [
    SizeRange(0, 99),
    SizeRange(100, 199),
    SizeRange(200, 299),
    SizeRange(300, 399),
    SizeRange(400, 499),
    SizeRange(500, 599),
    SizeRange(600, 699),
    SizeRange(700, 799),
    SizeRange(800, 899),
    SizeRange(900, 999),
    SizeRange(1000, 1249),
    SizeRange(1250, 1499),
    SizeRange(1500, 1749),
    SizeRange(1750, 1999),
    SizeRange(2000, 2499),
    SizeRange(2500, 2999),
    SizeRange(3000, 3499),
    SizeRange(3500, 3999),
    SizeRange(4000, 4499),
    SizeRange(4500, 4999),
    SizeRange(5000, 5999),
    SizeRange(6000, 6999),
    SizeRange(7000, 7999),
    SizeRange(8000, 8999),
    SizeRange(9000, 9999),
    SizeRange(10000, 12499),
    SizeRange(12500, 14999),
    SizeRange(15000, 17499),
    SizeRange(17500, 19999),
    SizeRange(20000, 24999),
    SizeRange(25000, 29999),
    SizeRange(30000, 34999),
    SizeRange(35000, 39999),
    SizeRange(40000, 44999),
    SizeRange(45000, 49999),
    SizeRange(50000, 74999),
    SizeRange(75000, 99999),
    SizeRange(100000, None),
]


def collect_shard(
    size_range: SizeRange,
    max_results: int = 1000,
    on_page: Callable[[int, int], None] | None = None,
) -> tuple["ShardResult", list[dict]]:
    """Collect all results for a size range shard."""
    client = get_client()
    query = size_range.to_search_query()
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
            on_page(page, len(new_items))

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
    return result.collected >= 1000 and result.total_count > result.collected


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
    """Deduplicate items by SHA, extracting file info.

    Args:
        items: Raw API response items to deduplicate.
        seen_shas: Optional set of already-seen SHAs for incremental deduplication.

    Returns:
        Tuple of (unique items with extracted info, updated seen_shas set).
    """
    if seen_shas is None:
        seen_shas = set()

    unique = []
    for item in items:
        sha = item.get("sha")
        if sha and sha not in seen_shas:
            seen_shas.add(sha)
            unique.append(extract_file_info(item))
    return unique, seen_shas


EXPECTED_TOTAL = 113_066  # Approximate based on GitHub search across all size ranges


def write_progress_md(
    output_dir: Path,
    results: list[ShardResult],
    in_progress: dict | None = None,
):
    """Write current progress to markdown file."""
    total_collected = sum(r.collected for r in results)
    if in_progress:
        total_collected += in_progress.get("collected", 0)

    md_path = output_dir / "progress.md"
    with open(md_path, "w") as f:
        f.write("# SKILL.md Collection Progress\n\n")
        pct = (total_collected / EXPECTED_TOTAL * 100) if EXPECTED_TOTAL else 0
        f.write(f"**Total collected:** {total_collected:,} / {EXPECTED_TOTAL:,} ({pct:.1f}%)\n\n")
        f.write("| Range | # | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |\n")
        f.write("|-------|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|\n")

        # Build list of all rows (completed + in-progress) for sorting
        rows: list[ProgressRow] = [result.to_progress_row() for result in results]

        if in_progress:
            # Parse min_bytes from range string (e.g., "500-599" -> 500, ">100000" -> 100000)
            range_str = in_progress["range"]
            min_bytes = int(range_str.split("-")[0].lstrip(">"))
            rows.append(
                ProgressRow(
                    min_bytes=min_bytes,
                    range_str=f"-> {range_str}",  # Arrow indicates in-progress
                    collected=in_progress["collected"],
                    pages=in_progress.get("pages", {}),
                    bold=True,
                )
            )

        # Sort by min_bytes descending (largest at top)
        rows.sort(key=lambda r: r.min_bytes, reverse=True)

        for row in rows:
            f.write(row.format())


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


def process_range_dry_run(size_range: SizeRange) -> ShardResult:
    """Process a range in dry-run mode (count only)."""
    client = get_client()
    query = size_range.to_search_query()
    response = client.search_code(query, per_page=1, page=1)
    return ShardResult(
        range=size_range,
        total_count=response.get("total_count", 0),
        collected=0,
        pages={},
    )


def cmd_fetch_files(args):
    """Fetch SKILL.md file URLs from GitHub."""
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Clear/initialize the URLs file for incremental writes
    if not args.dry_run:
        (args.output_dir / "skill_urls.txt").write_text("")

    # Determine which ranges to collect
    if args.ranges:
        range_indices = [int(i) for i in args.ranges.split(",")]
        ranges_to_collect = [SIZE_RANGES[i] for i in range_indices]
    else:
        ranges_to_collect = SIZE_RANGES

    # Collection state
    seen_shas: set[str] = set()
    unique_items: list[dict] = []
    completed_results: dict[str, ShardResult] = {}
    pending_ranges = list(ranges_to_collect)

    while pending_ranges:
        size_range = pending_ranges.pop(0)
        total_files = len(unique_items)
        status(f"[{total_files:,} / {EXPECTED_TOTAL:,}] Fetching {size_range}...")

        if args.dry_run:
            result = process_range_dry_run(size_range)
            items: list[dict] = []
        else:
            # Track in-progress state for live updates
            in_progress = {"range": str(size_range), "collected": 0, "pages": {}}

            def on_page(page_num: int, count: int):
                in_progress["pages"][page_num] = count
                in_progress["collected"] = sum(in_progress["pages"].values())
                current_total = total_files + in_progress["collected"]
                status(
                    f"[{current_total:,} / {EXPECTED_TOTAL:,}] Fetching {size_range} (page {page_num})..."
                )
                # Don't show in_progress if we hit 1000 (will be subdivided)
                if in_progress["collected"] >= 1000:
                    write_progress_md(args.output_dir, list(completed_results.values()))
                else:
                    write_progress_md(
                        args.output_dir, list(completed_results.values()), in_progress
                    )

            result, items = collect_shard(size_range, on_page=on_page)

        if needs_subdivision(result):
            first_half, next_range = size_range.subdivide()
            pending_ranges = [first_half, next_range] + pending_ranges
            continue

        # Range complete - record results
        completed_results[str(result.range)] = result

        if not args.dry_run:
            new_items, seen_shas = deduplicate_items(items, seen_shas)
            unique_items.extend(new_items)
            append_urls(args.output_dir, new_items)

        status(
            f"[{len(unique_items):,} / {EXPECTED_TOTAL:,}] Completed {size_range} ({len(completed_results)} shards)"
        )
        write_progress_md(args.output_dir, list(completed_results.values()))

    print()  # New line after status updates

    results_list = list(completed_results.values())
    print_summary(results_list)
    save_results(args.output_dir, results_list, unique_items if not args.dry_run else None)


def cmd_fetch_content(args):
    """Fetch SKILL.md content from URLs and store locally."""
    import base64

    urls_path = args.output_dir / "skill_urls.txt"

    if not urls_path.exists():
        raise FileNotFoundError(f"{urls_path} not found. Run 'fetch-files' first.")

    with open(urls_path) as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"Found {len(urls):,} URLs in {urls_path}")

    content_dir = args.output_dir / "content"
    content_dir.mkdir(parents=True, exist_ok=True)

    client = get_client()
    fetched = 0
    cached = 0
    errors = 0

    for i, url in enumerate(urls):
        parsed = parse_github_url(url)
        if not parsed:
            errors += 1
            status(
                f"[{i + 1}/{len(urls)}] {fetched:,} fetched, {cached:,} cached, {errors:,} errors"
            )
            continue

        owner, repo, ref, path = parsed
        # Build local path: content/{owner}/{repo}/blob/{ref}/{path}
        local_path = content_dir / owner / repo / "blob" / ref / path

        # Skip if already fetched (on-disk cache)
        if local_path.exists():
            cached += 1
        else:
            try:
                data = client.get_file_content(owner, repo, path, ref=ref)
                if "content" in data:
                    content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    local_path.write_text(content)
                    fetched += 1
                else:
                    errors += 1
            except Exception:
                errors += 1

        status(f"[{i + 1}/{len(urls)}] {fetched:,} fetched, {cached:,} cached, {errors:,} errors")

    print(f"\n\nDone: {fetched:,} fetched, {cached:,} cached, {errors:,} errors")


def cmd_filter_skills(args):
    """Classify files as skill files using Claude Agent SDK."""
    import asyncio
    import contextlib
    import hashlib
    import signal

    from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

    # Handle broken pipe gracefully (e.g., when piping to head)
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    urls_path = args.output_dir / "skill_urls.txt"

    if not urls_path.exists():
        raise FileNotFoundError(f"{urls_path} not found. Run 'fetch-files' first.")

    with open(urls_path) as f:
        urls = [line.strip() for line in f if line.strip()]

    content_dir = args.output_dir / "content"
    cache_dir = args.output_dir / ".classify_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Collect files with content
    files_to_classify: list[tuple[str, Path]] = []
    for url in urls:
        if args.limit is not None and len(files_to_classify) >= args.limit:
            break
        parsed = parse_github_url(url)
        if not parsed:
            continue
        owner, repo, ref, path = parsed
        local_path = content_dir / owner / repo / "blob" / ref / path
        if local_path.exists():
            files_to_classify.append((url, local_path))

    print(f"Classifying {len(files_to_classify)} files...", file=sys.stderr)

    def get_cache_key(content: str) -> str:
        """Generate cache key from content hash."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def get_cached_result(content: str) -> dict | None:
        """Check if we have a cached classification result."""
        if args.skip_cache:
            return None
        cache_file = cache_dir / f"{get_cache_key(content)}.json"
        if cache_file.exists():
            import json

            return json.loads(cache_file.read_text())
        return None

    def cache_result(content: str, result: dict):
        """Cache a classification result."""
        import json

        cache_file = cache_dir / f"{get_cache_key(content)}.json"
        cache_file.write_text(json.dumps(result))

    # Track progress
    progress = {"completed": 0, "cached": 0, "api_calls": 0}
    progress_lock = asyncio.Lock()

    async def classify_file(
        url: str, file_path: Path, semaphore: asyncio.Semaphore
    ) -> tuple[str, dict | None, bool]:
        """Classify a single file using Claude. Returns (url, result_dict, was_cached)."""
        content = file_path.read_text()

        # Skip empty files
        if not content.strip():
            async with progress_lock:
                progress["completed"] += 1
            return url, {"is_skill_file": False, "reason": "empty file"}, False

        # Truncate very long files to avoid token limits
        if len(content) > 10000:
            content = content[:10000] + "\n\n[truncated]"

        # Check cache first (no semaphore needed for cache check)
        cached = get_cached_result(content)
        if cached is not None:
            async with progress_lock:
                progress["completed"] += 1
                progress["cached"] += 1
            return url, cached, True

        # Acquire semaphore for API call
        async with semaphore:
            async with progress_lock:
                progress["api_calls"] += 1

            options = ClaudeAgentOptions(
                allowed_tools=[],  # No tools, just respond
                max_turns=1,
            )

            prompt = f"""Analyze this file and determine if it is a valid Claude Code SKILL.md file.

A valid SKILL.md file should:
- Define a skill/capability for Claude Code
- Have clear instructions or prompts
- Not be a generic README or documentation file
- Not be an empty placeholder

File content:
```
{content}
```

IMPORTANT: Respond with ONLY a JSON object, no other text.
Format: {{"is_skill_file": true/false, "reason": "brief explanation"}}"""

            result_data = None
            try:
                # IMPORTANT: We must consume the entire generator, not break early.
                # The SDK uses anyio task groups internally, and breaking triggers
                # GeneratorExit which tries to close the task group from a different
                # task context (due to asyncio.gather), causing RuntimeError.
                async for message in query(prompt=prompt, options=options):
                    if isinstance(message, ResultMessage):
                        if message.is_error:
                            print(f"Error: {message.result}", file=sys.stderr)
                        elif message.result:
                            import json

                            try:
                                parsed = json.loads(message.result)
                                if parsed.get("is_skill_file") is not None:
                                    cache_result(content, parsed)
                                    result_data = parsed
                            except json.JSONDecodeError:
                                if args.verbose:
                                    print(
                                        f"DEBUG: Could not parse JSON from: {message.result}",
                                        file=sys.stderr,
                                    )
                    # Don't break - let the generator complete naturally
            except Exception as e:
                print(f"Error classifying {url}: {e}", file=sys.stderr)

            async with progress_lock:
                progress["completed"] += 1
            return url, result_data, False

    async def update_status():
        """Periodically update status line."""
        total = len(files_to_classify)
        while progress["completed"] < total:
            status(
                f"[{progress['completed']}/{total}] "
                f"Classifying ({progress['cached']} cached, {progress['api_calls']} API calls)..."
            )
            await asyncio.sleep(0.1)

    async def classify_all():
        # Limit concurrent API calls
        semaphore = asyncio.Semaphore(args.concurrency)

        # Start status updater
        status_task = asyncio.create_task(update_status())

        # Run all classifications in parallel
        tasks = [classify_file(url, file_path, semaphore) for url, file_path in files_to_classify]
        results = await asyncio.gather(*tasks)

        # Stop status updater
        status_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await status_task

        return results

    results = asyncio.run(classify_all())

    print()  # New line after status

    # Separate valid and invalid skills
    valid_skills = []
    invalid_skills = []
    errors = []

    for url, result, _was_cached in results:
        if result is None:
            errors.append((url, "error", "Failed to classify"))
        elif result.get("is_skill_file"):
            valid_skills.append((url, result.get("reason", "")))
        else:
            invalid_skills.append((url, result.get("reason", "")))

    # Write markdown file to results directory
    output_file = args.output_dir / "classified_skills.md"

    def truncate_url(url: str, max_len: int = 50) -> str:
        """Truncate URL for display, keeping the end visible."""
        if len(url) <= max_len:
            return url
        return url[:20] + "..." + url[-(max_len - 23) :]

    with open(output_file, "w") as f:
        f.write("# Skill Classification Results\n\n")
        f.write(f"**Total:** {len(results)} files\n")
        f.write(f"**Valid skills:** {len(valid_skills)}\n")
        f.write(f"**Not skills:** {len(invalid_skills)}\n")
        f.write(f"**Errors:** {len(errors)}\n\n")

        # Add CSS for responsive table with ellipsis truncation
        f.write("<style>\n")
        f.write("table { width: 100%; table-layout: fixed; }\n")
        f.write("td:first-child { width: 50%; }\n")
        f.write("td:last-child { word-wrap: break-word; }\n")
        f.write(".truncate-url { display: block; overflow: hidden; ")
        f.write("text-overflow: ellipsis; white-space: nowrap; }\n")
        f.write("</style>\n\n")

        # Valid skills table
        f.write("## Valid Skills\n\n")
        if valid_skills:
            f.write("| URL | Reason |\n")
            f.write("|-----|--------|\n")
            for url, reason in valid_skills:
                # Use span with CSS class for truncation, title shows full URL on hover
                f.write(
                    f'| <span class="truncate-url" title="{url}">[{truncate_url(url)}]({url})</span> '
                    f"| {reason} |\n"
                )
        else:
            f.write("*No valid skills found.*\n")

        f.write("\n")

        # Invalid skills table
        f.write("## Not Skills\n\n")
        if invalid_skills:
            f.write("| URL | Reason |\n")
            f.write("|-----|--------|\n")
            for url, reason in invalid_skills:
                f.write(
                    f'| <span class="truncate-url" title="{url}">[{truncate_url(url)}]({url})</span> '
                    f"| {reason} |\n"
                )
        else:
            f.write("*No invalid skills found.*\n")

        # Errors table (if any)
        if errors:
            f.write("\n## Errors\n\n")
            f.write("| URL | Error |\n")
            f.write("|-----|-------|\n")
            for url, _, reason in errors:
                f.write(
                    f'| <span class="truncate-url" title="{url}">[{truncate_url(url)}]({url})</span> '
                    f"| {reason} |\n"
                )

    print(f"Results saved to {output_file}", file=sys.stderr)
    print(
        f"Total: {len(results)}, Valid: {len(valid_skills)}, Invalid: {len(invalid_skills)}, "
        f"Errors: {len(errors)}, Cached: {progress['cached']}, API calls: {progress['api_calls']}",
        file=sys.stderr,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Collect SKILL.md files from GitHub",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent.parent / "results",
        help="Output directory for results",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # fetch-files subcommand
    fetch_files_parser = subparsers.add_parser(
        "fetch-files",
        help="Fetch SKILL.md file URLs from GitHub",
    )
    fetch_files_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only count results, don't collect",
    )
    fetch_files_parser.add_argument(
        "--ranges",
        type=str,
        help="Comma-separated list of range indices to collect (e.g., '0,1,2')",
    )
    fetch_files_parser.add_argument(
        "--skip-cache",
        action="store_true",
        help="Skip reading from cache (still writes to cache)",
    )

    # fetch-content subcommand
    fetch_content_parser = subparsers.add_parser(
        "fetch-content",
        help="Fetch SKILL.md content from collected URLs",
    )
    fetch_content_parser.add_argument(
        "--skip-cache",
        action="store_true",
        help="Skip reading from cache (still writes to cache)",
    )

    # filter-skills subcommand
    filter_skills_parser = subparsers.add_parser(
        "filter-skills",
        help="Classify files using Claude to determine if they are valid SKILL.md files",
    )
    filter_skills_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of files to classify (default: all)",
    )
    filter_skills_parser.add_argument(
        "--concurrency",
        type=int,
        default=10,
        help="Maximum concurrent API calls (default: 10)",
    )
    filter_skills_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose debug output",
    )
    filter_skills_parser.add_argument(
        "--skip-cache",
        action="store_true",
        help="Skip reading from cache (still writes to cache)",
    )

    args = parser.parse_args()

    if args.command == "fetch-files":
        cmd_fetch_files(args)
    elif args.command == "fetch-content":
        cmd_fetch_content(args)
    elif args.command == "filter-skills":
        cmd_filter_skills(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
