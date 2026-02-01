# Skill Collection Development

## Project Structure

```
skill_collection/
  __init__.py     # Re-exports, entry point
  cli.py          # CLI commands (fetch-files, fetch-content, filter-skills)
  collect.py      # Collection functions (collect_shard, deduplicate, write_progress)
  models.py       # Data models (SizeRange, ShardResult, ProgressRow)
  github.py       # GitHub API client
  filter.py       # Claude-based skill classification
  utils.py        # Shared utilities (status output)
  collect_test.py # Unit tests
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

## Data Flow

1. `fetch-files` queries GitHub, writes `skill_urls.txt` incrementally
2. `fetch-content` downloads file content to `content/` directory (cached)
3. `filter-skills` classifies files using Claude, writes `classified_skills.md`
