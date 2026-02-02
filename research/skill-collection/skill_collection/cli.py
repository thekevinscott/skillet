"""CLI commands for skill collection."""

import argparse
import base64
from pathlib import Path

from .analyze import cmd_analyze as _cmd_analyze
from .classify import cmd_classify as _cmd_classify
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
from .github import get_client
from .models import EXPECTED_TOTAL, SIZE_RANGES, ShardResult
from .utils import parse_github_url, resolve_content_path, status


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

    # Determine which ranges to collect
    if args.ranges:
        range_indices = [int(i) for i in args.ranges.split(",")]
        ranges_to_collect = [SIZE_RANGES[i] for i in range_indices]
    else:
        ranges_to_collect = SIZE_RANGES

    # Load existing results to enable resumable collection
    urls_path = args.output_dir / "skill_urls.txt"
    files_path = args.output_dir / "skill_files.json"

    if not args.dry_run and files_path.exists():
        # Resume from previous run: load existing items and SHAs
        import json

        with open(files_path) as f:
            unique_items = json.load(f)
        seen_shas = {item.get("sha") for item in unique_items if item.get("sha")}
        # Rebuild skill_urls.txt from the loaded items to avoid duplicates
        with open(urls_path, "w") as f:
            for item in unique_items:
                if item.get("html_url"):
                    f.write(item["html_url"] + "\n")
        print(f"Resuming: loaded {len(unique_items):,} existing items")
    else:
        # Fresh start
        seen_shas: set[str] = set()
        unique_items: list[dict] = []
        if not args.dry_run:
            urls_path.write_text("")

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

            # Save progress incrementally with atomic write to prevent corruption
            import json
            import os
            import tempfile

            fd, tmp_path = tempfile.mkstemp(dir=args.output_dir, suffix=".json.tmp")
            try:
                with os.fdopen(fd, "w") as f:
                    json.dump(unique_items, f)
                os.replace(tmp_path, files_path)
            except Exception:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                raise

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
    import threading
    from concurrent.futures import ThreadPoolExecutor, as_completed

    urls = load_skill_urls(args.output_dir)
    print(f"Found {len(urls):,} URLs")

    content_dir = args.output_dir / "content"
    content_dir.mkdir(parents=True, exist_ok=True)

    client = get_client()
    counters = {"fetched": 0, "cached": 0, "errors": 0, "processed": 0}
    lock = threading.Lock()

    def fetch_one(url: str) -> None:
        parsed = parse_github_url(url)
        if not parsed:
            with lock:
                counters["errors"] += 1
                counters["processed"] += 1
            return

        owner, repo, ref, path = parsed
        local_path = resolve_content_path(content_dir, owner, repo, ref, path)

        # Skip if already fetched (on-disk cache)
        if local_path.exists():
            with lock:
                counters["cached"] += 1
                counters["processed"] += 1
            return

        try:
            data = client.get_file_content(owner, repo, path, ref=ref)
            if "content" in data:
                content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
                local_path.parent.mkdir(parents=True, exist_ok=True)
                local_path.write_text(content)
                with lock:
                    counters["fetched"] += 1
            else:
                with lock:
                    counters["errors"] += 1
        except Exception:
            with lock:
                counters["errors"] += 1

        with lock:
            counters["processed"] += 1

    # Use 10 workers - rate limiter handles actual API throttling
    concurrency = getattr(args, "concurrency", 10)
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {executor.submit(fetch_one, url): url for url in urls}

        for future in as_completed(futures):
            future.result()  # Propagate exceptions
            with lock:
                processed = counters["processed"]
                fetched = counters["fetched"]
                cached = counters["cached"]
                errors = counters["errors"]
            status(
                f"[{processed}/{len(urls)}] {fetched:,} fetched, {cached:,} cached, {errors:,} errors"
            )

    print(
        f"\n\nDone: {counters['fetched']:,} fetched, {counters['cached']:,} cached, {counters['errors']:,} errors"
    )


def cmd_filter_skills(args):
    """Classify files using Claude to determine if they are valid SKILL.md files."""
    _cmd_filter_skills(args, load_skill_urls)


def cmd_analyze(args):
    """Extract features from valid skills for analysis."""
    _cmd_analyze(args)


def cmd_classify(args):
    """Classify skills using Claude to extract structured taxonomy."""
    _cmd_classify(args)


def cmd_v2(args):
    """Handle v2 subcommands."""
    from .collect_v2 import init_collection, run_collection
    from .db import get_stats

    if args.v2_command == "init":
        db_path = args.db or (args.output_dir / "skills.db")
        count = init_collection(db_path)
        print(f"Initialized database at {db_path}")
        print(f"Created {count} shards")

    elif args.v2_command == "collect":
        db_path = args.db or (args.output_dir / "skills.db")

        def on_progress(query: str, collected: int, shards: int):
            # Truncate query for display
            display_query = query if len(query) < 60 else query[:57] + "..."
            status(f"[{shards} shards, {collected:,} skills] {display_query}")

        print(f"Starting collection from {db_path}")
        stats = run_collection(db_path, on_progress=on_progress)
        print()  # New line after status
        print(f"Shards processed: {stats['shards_processed']}")
        print(f"Shards subdivided: {stats['shards_subdivided']}")
        print(f"Skills collected: {stats['skills_collected']}")
        print(f"New skills: {stats['skills_new']}")

    elif args.v2_command == "stats":
        db_path = args.db or (args.output_dir / "skills.db")
        stats = get_stats(db_path)
        print(f"Database: {db_path}")
        print(f"Shards: {stats['shards_completed']}/{stats['shards_total']} complete")
        print(f"Skills: {stats['skills_total']:,}")
        print(f"Content: {stats['content_fetched']:,}")
        print(f"Validations: {stats['validations_valid']}/{stats['validations_total']} valid")

    else:
        print("Usage: collect-skills v2 {init,collect,stats}")
        print("  init     - Initialize database and seed shards")
        print("  collect  - Run collection (resumable)")
        print("  stats    - Show database statistics")


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
    fetch_content_parser = subparsers.add_parser(
        "fetch-content",
        help="Fetch SKILL.md content from collected URLs",
    )
    fetch_content_parser.add_argument(
        "--concurrency",
        type=int,
        default=10,
        help="Number of concurrent fetches (default: 10)",
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

    # analyze subcommand
    subparsers.add_parser(
        "analyze",
        help="Extract features from valid skills for analysis",
    )

    # classify subcommand
    classify_parser = subparsers.add_parser(
        "classify",
        help="Classify skills using Claude to extract structured taxonomy",
    )
    classify_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output file for classifications (default: skill_classifications.json)",
    )
    classify_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of skills to classify",
    )
    classify_parser.add_argument(
        "--concurrency",
        type=int,
        default=3,
        help="Maximum concurrent API calls (default: 3)",
    )
    classify_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose debug output",
    )
    classify_parser.add_argument(
        "--skip-cache",
        action="store_true",
        help="Skip reading from cache (still writes to cache)",
    )

    # fetch-repo-metadata subcommand
    repo_metadata_parser = subparsers.add_parser(
        "fetch-repo-metadata",
        help="Fetch repository metadata (stars, forks, language, etc.)",
    )
    repo_metadata_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of repositories to process",
    )
    repo_metadata_parser.add_argument(
        "--concurrency",
        type=int,
        default=10,
        help="Number of concurrent fetches (default: 10)",
    )

    # fetch-claude-md subcommand
    claude_md_parser = subparsers.add_parser(
        "fetch-claude-md",
        help="Fetch CLAUDE.md files from skill repositories",
    )
    claude_md_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of repositories to process",
    )
    claude_md_parser.add_argument(
        "--concurrency",
        type=int,
        default=10,
        help="Number of concurrent fetches (default: 10)",
    )

    # fetch-skill-history subcommand
    skill_history_parser = subparsers.add_parser(
        "fetch-skill-history",
        help="Fetch commit history for skill files",
    )
    skill_history_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of skills to process",
    )
    skill_history_parser.add_argument(
        "--concurrency",
        type=int,
        default=10,
        help="Number of concurrent fetches (default: 10)",
    )

    # v2 subcommand (SQLite-based pipeline)
    v2_parser = subparsers.add_parser(
        "v2",
        help="SQLite-based collection pipeline (v2)",
    )
    v2_subparsers = v2_parser.add_subparsers(dest="v2_command", help="v2 commands")

    # v2 init subcommand
    v2_init_parser = v2_subparsers.add_parser(
        "init",
        help="Initialize database and seed shards",
    )
    v2_init_parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="Database path (default: results/skills.db)",
    )

    # v2 collect subcommand
    v2_collect_parser = v2_subparsers.add_parser(
        "collect",
        help="Run collection (resumable)",
    )
    v2_collect_parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="Database path (default: results/skills.db)",
    )

    # v2 stats subcommand
    v2_stats_parser = v2_subparsers.add_parser(
        "stats",
        help="Show database statistics",
    )
    v2_stats_parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="Database path (default: results/skills.db)",
    )

    args = parser.parse_args()

    if args.command == "fetch-files":
        cmd_fetch_files(args)
    elif args.command == "fetch-content":
        cmd_fetch_content(args)
    elif args.command == "filter-skills":
        cmd_filter_skills(args)
    elif args.command == "analyze":
        cmd_analyze(args)
    elif args.command == "classify":
        cmd_classify(args)
    elif args.command == "fetch-repo-metadata":
        from .repo_info import cmd_fetch_repo_metadata

        cmd_fetch_repo_metadata(args)
    elif args.command == "fetch-claude-md":
        from .repo_info import cmd_fetch_claude_md

        cmd_fetch_claude_md(args)
    elif args.command == "fetch-skill-history":
        from .repo_info import cmd_fetch_skill_history

        cmd_fetch_skill_history(args)
    elif args.command == "v2":
        cmd_v2(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
