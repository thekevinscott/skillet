# Skill Collection Development

## Project Structure

```
skill_collection/
  __init__.py       # Re-exports, entry point
  cli.py            # CLI commands

  # Legacy (file-based)
  collect.py        # Collection functions (collect_shard, deduplicate, write_progress)
  filter.py         # Claude-based skill classification

  # v2 (SQLite-based)
  db.py             # SQLite schema and connection helpers
  collect_v2.py     # Collection with multi-dimensional sharding
  fetch_v2.py       # Content fetching to SQLite
  validate_v2.py    # Async validation with Claude

  # Shared
  models.py         # Data models (SizeRange, ShardResult, ProgressRow)
  github.py         # GitHub API client with caching and rate limiting
  utils.py          # Shared utilities (status output, URL parsing)
```

## Key Concepts

### Size Sharding
GitHub limits code search results to 1000 per query. We work around this by querying non-overlapping file size ranges (`size:0..99`, `size:100..199`, etc.).

### Automatic Subdivision
When a size range has >1000 results, `collect_shard` returns early after page 1. The main loop detects this via `needs_subdivision()` and splits the range in half, continuing collection with narrower ranges.

### Deduplication
Files are deduplicated by SHA across all shards. The progress display shows deduplicated unique counts, not raw collected counts.

## Running Tests

```bash
uv run pytest skill_collection/collect_test.py -v
```

## Testing filter-skills

Use `-o` to write to a temp file instead of clobbering results:

```bash
uv run collect-skills filter-skills -o /tmp/classified_skills.md --limit 10
```

## Data Flow (Legacy)

1. `fetch-files` queries GitHub, writes `skill_urls.txt` incrementally
2. `fetch-content` downloads file content to `content/` directory (cached)
3. `filter-skills` classifies files using Claude, writes `classified_skills.md`

## v2 Pipeline (SQLite-based)

The v2 pipeline uses SQLite for all collection data, providing resumable collection and proper state tracking.

### Commands

```bash
# Initialize database and seed shards
uv run collect-skills v2 init

# Run collection (resumable)
uv run collect-skills v2 collect

# Fetch content for skills
uv run collect-skills v2 fetch-content [--use-cache] [--limit N]

# Validate skills using Claude
uv run collect-skills v2 validate [--use-cache] [--limit N] [--concurrency N]

# Show database statistics
uv run collect-skills v2 stats
```

### Database Schema

- `shards`: Tracks collection progress by query
- `skills`: Discovered files (deduplicated by SHA)
- `content`: File content stored in DB
- `validations`: Claude classification results

### Multi-dimensional Sharding

v2 supports fallback to date-based sharding when size ranges still exceed 1000 results (e.g., for very common file sizes).

### Cache Integration

During transition, `--use-cache` flags allow using existing file caches:
- `fetch-content --use-cache`: Reads from `content/` directory first
- `validate --use-cache`: Reads from `.classify_cache/` directory first
