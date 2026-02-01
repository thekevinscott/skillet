"""Collect SKILL.md files from GitHub using size-sharded queries.

GitHub's code search API limits results to 1000 per query. By sharding
queries by file size, we can collect more results (up to 1000 per size range).
"""

from .cli import main
from .collect import (
    append_urls,
    collect_shard,
    deduplicate_items,
    extract_file_info,
    needs_subdivision,
    print_summary,
    save_results,
    write_progress_md,
)
from .models import (
    EXPECTED_TOTAL,
    SIZE_RANGES,
    ProgressRow,
    ShardResult,
    SizeRange,
)

__all__ = [
    # Models
    "SizeRange",
    "ShardResult",
    "ProgressRow",
    "SIZE_RANGES",
    "EXPECTED_TOTAL",
    # Collection functions
    "collect_shard",
    "needs_subdivision",
    "extract_file_info",
    "deduplicate_items",
    "write_progress_md",
    "append_urls",
    "print_summary",
    "save_results",
    # CLI
    "main",
]

if __name__ == "__main__":
    main()
