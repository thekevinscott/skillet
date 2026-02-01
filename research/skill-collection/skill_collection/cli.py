"""CLI commands for skill collection."""

import argparse
import base64
from pathlib import Path

from .collect import (
    append_urls,
    collect_shard,
    deduplicate_items,
    needs_subdivision,
    print_summary,
    save_results,
    write_progress_md,
)
from .filter import cmd_filter_skills as _cmd_filter_skills
from .github import get_client, parse_github_url
from .models import EXPECTED_TOTAL, SIZE_RANGES, ShardResult
from .utils import status


def load_skill_urls(output_dir: Path) -> list[str]:
    """Load skill URLs from the output directory."""
    urls_path = output_dir / "skill_urls.txt"
    if not urls_path.exists():
        raise FileNotFoundError(f"{urls_path} not found. Run 'fetch-files' first.")
    with open(urls_path) as f:
        return [line.strip() for line in f if line.strip()]


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
            result, items = collect_shard(size_range, dry_run=True)
        else:
            # Track in-progress state for live updates
            in_progress = {"range": str(size_range), "collected": 0, "pages": {}}

            def on_page(page_num: int, count: int, total_count: int):
                in_progress["pages"][page_num] = count
                in_progress["collected"] = sum(in_progress["pages"].values())
                in_progress["total_count"] = total_count
                current_total = total_files + in_progress["collected"]
                status(
                    f"[{current_total:,} / {EXPECTED_TOTAL:,}] Fetching {size_range} (page {page_num})..."
                )
                # Don't show in_progress if we hit 1000 (will be subdivided)
                # Note: unique_count only includes completed shards (deduplicated)
                # The in_progress row shows raw collected, but isn't added to total
                if in_progress["collected"] >= 1000:
                    write_progress_md(
                        args.output_dir, list(completed_results.values()), unique_count=total_files
                    )
                else:
                    write_progress_md(
                        args.output_dir,
                        list(completed_results.values()),
                        in_progress,
                        unique_count=total_files,
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
        write_progress_md(
            args.output_dir, list(completed_results.values()), unique_count=len(unique_items)
        )

    print()  # New line after status updates

    results_list = list(completed_results.values())
    print_summary(results_list)
    save_results(args.output_dir, results_list, unique_items if not args.dry_run else None)


def cmd_fetch_content(args):
    """Fetch SKILL.md content from URLs and store locally."""
    urls = load_skill_urls(args.output_dir)
    print(f"Found {len(urls):,} URLs")

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
    """Classify files using Claude to determine if they are valid SKILL.md files."""
    _cmd_filter_skills(args, load_skill_urls)


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
    parser.add_argument(
        "--skip-cache",
        action="store_true",
        help="Skip reading from cache (still writes to cache)",
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

    # fetch-content subcommand
    subparsers.add_parser(
        "fetch-content",
        help="Fetch SKILL.md content from collected URLs",
    )

    # filter-skills subcommand
    filter_skills_parser = subparsers.add_parser(
        "filter-skills",
        help="Classify files using Claude to determine if they are valid SKILL.md files",
    )
    filter_skills_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output directory for valid.md/invalid.md (default: <output-dir>/classified-skills/)",
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
        default=1,
        help="Maximum concurrent API calls (default: 1)",
    )
    filter_skills_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose debug output",
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
