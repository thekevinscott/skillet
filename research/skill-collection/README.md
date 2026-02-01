# Collecting SKILL.md Files from GitHub

## Summary

**Goal**: Find all files named `SKILL.md` across GitHub.

**Result**: GitHub API reports **~113,000** matching files, but only 1000 are accessible per query.

## Approach: Size-Sharded Collection

GitHub code search supports the `size:` qualifier. By querying non-overlapping size ranges, we can get up to 1000 results per shard. The collector automatically subdivides ranges when they exceed 1000 results.

## Installation

```bash
uv sync
```

## Usage

```bash
# Fetch file URLs from GitHub (subdivides ranges automatically)
uv run collect-skills fetch-files

# Dry run (count only, no files saved)
uv run collect-skills fetch-files --dry-run

# Fetch specific range indices
uv run collect-skills fetch-files --ranges 0,1,2,3

# Fetch actual file content from URLs
uv run collect-skills fetch-content

# Classify files as valid skill files using Claude
uv run collect-skills filter-skills

# Classify with custom output path (useful for testing)
uv run collect-skills filter-skills -o /tmp/classified_skills.md --limit 10

# Skip cache for fresh classifications
uv run collect-skills filter-skills --skip-cache
```

## Output Files

- `results/progress.md` - Live progress table during collection
- `results/summary.json` - Counts per shard, totals
- `results/skill_files.json` - All collected file metadata (deduplicated)
- `results/skill_urls.txt` - URLs of all collected files (one per line)
- `results/content/` - Downloaded file content (cached)
- `results/classified_skills.md` - Classification results from filter-skills

## GitHub API Constraints

### Pagination Limit (Hard Wall at 1000)
```bash
# Page 10 works
gh api "search/code?q=filename:SKILL.md&per_page=100&page=10"

# Page 11 fails (HTTP 422)
gh api "search/code?q=filename:SKILL.md&per_page=100&page=11"
# Error: "Cannot access beyond the first 1000 results"
```

The collector handles this by subdividing ranges: when a query returns >1000 results, it splits the size range in half and retries.

### Valid Code Search Qualifiers
- `size:<n`, `size:>n`, `size:n..m` - file size in bytes
- `filename:` - filename match
- `path:` - path match
- `repo:`, `user:`, `org:` - scope to repos

**Not valid for code search**: `created:`, `pushed:`, `stars:` (repo search only)

### Rate Limits
- Authenticated: 30 requests/minute for search
- Collection script uses delays between requests

## Development

```bash
# Run tests
uv run pytest

# Run linter
uv run ruff check .

# Format code
uv run ruff format .
```

## References

- [GitHub Search API Docs](https://docs.github.com/en/rest/search)
- [PyGithub Issue #824](https://github.com/PyGithub/PyGithub/issues/824) - 1000 result limit
