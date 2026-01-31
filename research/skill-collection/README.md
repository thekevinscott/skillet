# Collecting SKILL.md Files from GitHub

## Summary

**Goal**: Find all files named `SKILL.md` across GitHub.

**Result**: GitHub API reports **113,664** matching files, but only 1000 are accessible per query.

## Approach: Size-Sharded Collection

GitHub code search supports the `size:` qualifier. By querying non-overlapping size ranges, we can get up to 1000 results per shard.

### Files

- `collect_skills.py` - Main collection script with size-sharded queries
- `explore.py` - Marimo notebook for interactive exploration
- `results/` - Output directory for collected data

### Usage

```bash
# Install marimo if needed
pip install marimo

# Interactive exploration
marimo run explore.py --host 0.0.0.0 --port 8080

# Dry run (count only)
python collect_skills.py --dry-run

# Full collection
python collect_skills.py

# Collect specific shards (by index)
python collect_skills.py --ranges 0,1,2,3
```

### Output

- `results/summary.json` - Counts per shard, totals
- `results/skill_files.json` - All collected file metadata (deduplicated)

## GitHub API Constraints

### Pagination Limit (Hard Wall at 1000)
```bash
# Page 10 works
gh api "search/code?q=filename:SKILL.md&per_page=100&page=10"

# Page 11 fails (HTTP 422)
gh api "search/code?q=filename:SKILL.md&per_page=100&page=11"
# Error: "Cannot access beyond the first 1000 results"
```

### Valid Code Search Qualifiers
- `size:<n`, `size:>n`, `size:n..m` - file size in bytes
- `filename:` - filename match
- `path:` - path match
- `repo:`, `user:`, `org:` - scope to repos

**Not valid for code search**: `created:`, `pushed:`, `stars:` (repo search only)

### Rate Limits
- Authenticated: 30 requests/minute for search
- Collection script uses 2.5s delay between requests

## Size Distribution (Observed)

| Range | Count | Accessible? |
|-------|-------|-------------|
| <100 bytes | ~320 | Yes |
| 100..500 | ~900 | Yes |
| 500..1000 | ~900 | Yes |
| 1000..2000 | ~820 | Yes |
| 2000..5000 | ~850 | Yes |
| 5000..10000 | ~920 | Yes |
| 10000..20000 | ~4,300 | Subdivided |
| 20000..50000 | ~780 | Yes |
| >50000 | ~560 | Yes |

Note: The sum of size ranges (~10k) doesn't match the reported total (113k). This discrepancy may be due to:
- `filename:SKILL.md` matching partial names
- GitHub's eventually consistent search index
- Files without size metadata

## Alternative: BigQuery (Stale)

BigQuery's GitHub dataset only returned 258 results (2016-2017 snapshot), making it not viable for current collection.

## References

- [GitHub Search API Docs](https://docs.github.com/en/rest/search)
- [PyGithub Issue #824](https://github.com/PyGithub/PyGithub/issues/824) - 1000 result limit
