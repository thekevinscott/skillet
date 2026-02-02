# Data Collection Pipeline

This document describes how the skill-collection project discovers and downloads SKILL.md files from GitHub. Analysis stages are summarized briefly at the end.

## Overview

```
GitHub Code Search API
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│  Stage 1: fetch files                                   │
│  - Query by file size ranges to bypass 1000-result cap  │
│  - Adaptive subdivision when ranges overflow            │
│  - Deduplicate by SHA across all shards                 │
└─────────────────────────────────────────────────────────┘
        │
        ▼
   skill_urls.txt (URLs)
   skill_files.json (full metadata)
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│  Stage 2: fetch content                                 │
│  - Download file content via GitHub Contents API        │
│  - Detect and resolve git symlinks                      │
│  - Optional: validate with Claude (is this a skill?)    │
└─────────────────────────────────────────────────────────┘
        │
        ▼
   content/{owner}/{repo}/blob/{ref}/{path}
   classified-skills/valid.md, invalid.md
```

---

## Stage 1: Discover Files

**Command:** `collect-skills fetch files [--dry-run] [--ranges 0,1,2]`

### The Problem: GitHub's 1000-Result Limit

GitHub Code Search API returns at most 1000 results per query. A naive `filename:SKILL.md` query would miss most files.

### The Solution: Size-Based Sharding

Query non-overlapping file size ranges. Each range stays under 1000 results.

```python
# models.py:154-193
SIZE_RANGES = [
    SizeRange(0, 99),       # 0-99 bytes
    SizeRange(100, 199),    # 100-199 bytes
    SizeRange(200, 299),
    # ... 38 total ranges
    SizeRange(100000, None),  # 100KB+ (unbounded)
]
```

### Adaptive Subdivision

When a range returns >1000 results, split it.

> **Known Limitation:** If a single byte value (e.g., all files exactly 500 bytes) has >1000 results, subdivision cannot help. The code detects this and raises `ValueError` rather than silently losing data:
>
> ```python
> # collect.py:84-94
> if result.range.width == 0:
>     raise ValueError(
>         f"Cannot subdivide single-byte range {result.range} "
>         f"but it has {result.total_count} results (limit {GITHUB_SEARCH_RESULT_LIMIT}). "
>         f"Data will be lost."
>     )
> ```
>
> In practice this hasn't occurred for SKILL.md files (file sizes are distributed), but it's a fundamental limitation of the size-sharding approach. Alternative strategies if this becomes a problem:
> - Shard by additional dimensions (language, repo creation date, path prefix)
> - Accept sampling for oversized single-byte buckets
> - Use GitHub's GraphQL API (different pagination model)

```python
# models.py:59-81
def subdivide(self, chunk_size: int = 100) -> tuple[SizeRange, SizeRange]:
    if self.max_bytes is None:
        # Unbounded: exponential doubling
        mid = self.min_bytes * 2
        return (
            SizeRange(self.min_bytes, mid - 1),
            SizeRange(mid, None),
        )
    # Bounded: split at midpoint
    mid = self.min_bytes + self.width // 2
    return (
        SizeRange(self.min_bytes, mid),
        SizeRange(mid + 1, mid + chunk_size),
    )
```

The main loop (`cli.py:90-174`):

```python
while pending_ranges:
    size_range = pending_ranges.pop(0)
    result, items = collect_shard(size_range)

    if needs_subdivision(result):  # total_count > 1000
        first, second = size_range.subdivide(chunk_size=adaptive_chunk_size)
        pending_ranges = [first, second] + pending_ranges
        adaptive_chunk_size = max(adaptive_chunk_size // 2, 1)  # shrink
        continue

    # Success: deduplicate and save
    new_items, seen_shas = deduplicate_items(items, seen_shas)
    unique_items.extend(new_items)
    append_urls(output_dir, new_items)
```

Chunk size adapts: shrinks after hitting limits, grows after consecutive successes.

### Deduplication

The same file content (same SHA) can appear in multiple repositories (forks, vendored copies). Deduplicate globally:

```python
# collect.py:112-126
def deduplicate_items(items, seen_shas):
    unique = []
    for item in items:
        sha = item.get("sha")
        if sha and sha not in seen_shas:
            seen_shas.add(sha)
            unique.append(extract_file_info(item))
    return unique, seen_shas
```

### Resumability

Collection can take hours. The pipeline supports restart mid-run:

1. **Atomic writes** - JSON written to temp file, then `os.replace()` (`cli.py:159-167`)
2. **Incremental appends** - URLs appended to `skill_urls.txt` after each shard
3. **Resume detection** - On start, load `skill_files.json` and rebuild `seen_shas`

```python
# cli.py:61-73
if files_path.exists():
    with open(files_path) as f:
        unique_items = json.load(f)
    seen_shas = {item.get("sha") for item in unique_items if item.get("sha")}
    print(f"Resuming: loaded {len(unique_items):,} existing items")
```

### Rate Limiting

GitHub Search API allows ~10 requests/minute. The client uses adaptive throttling:

```python
# github.py:14-27
RATE_LIMITS = {
    "search": {"requests_per_minute": 8, "min_requests_per_minute": 4},
    "contents": {"requests_per_minute": 60, "min_requests_per_minute": 30},
}
BACKOFF_FACTOR = 0.75  # Reduce by 25% on each rate limit hit
```

On 403/rate-limit response: back off, wait for reset, retry.

### Output Files

| File | Format | Purpose |
|------|--------|---------|
| `skill_urls.txt` | Text (one URL/line) | Simple list for downstream stages |
| `skill_files.json` | JSON array | Full metadata, used for resume |
| `summary.json` | JSON | Collection stats per shard |
| `progress.md` | Markdown | Live progress table |

**skill_files.json entry:**
```json
{
  "name": "SKILL.md",
  "path": ".claude/commands/review.md",
  "sha": "a1b2c3d4...",
  "html_url": "https://github.com/owner/repo/blob/main/.claude/commands/review.md",
  "repository": {
    "full_name": "owner/repo",
    "html_url": "https://github.com/owner/repo",
    "description": "Repo description"
  }
}
```

---

## Stage 2: Download Content

**Command:** `collect-skills fetch content [--limit N] [--skip-validation] [--validation-concurrency N]`

### URL Parsing

GitHub blob URLs have a consistent structure:

```
https://github.com/{owner}/{repo}/blob/{ref}/{path}
```

```python
# utils.py:60-77
def parse_github_url(url: str) -> tuple[str, str, str, str] | None:
    # https://github.com/owner/repo/blob/ref/path/to/file.md
    # Returns: ('owner', 'repo', 'ref', 'path/to/file.md')
    rest = url[19:]  # strip "https://github.com/"
    parts = rest.split("/")
    if len(parts) < 5 or parts[2] != "blob":
        return None
    return parts[0], parts[1], parts[3], "/".join(parts[4:])
```

### Local Storage Structure

Content mirrors the GitHub URL structure:

```python
# utils.py:55-57
def resolve_content_path(content_dir, owner, repo, ref, path) -> Path:
    return content_dir / owner / repo / "blob" / ref / path
```

Example: `content/anthropics/claude-code/blob/main/.claude/commands/commit.md`

### Symlink Detection

Git stores symlinks as small text files containing a relative path. These need to be detected and resolved:

```python
# filter.py:24-38
def is_symlink_content(content: str) -> bool:
    content = content.strip()
    # Symlinks are small, single-line, contain path separators
    if "\n" in content or len(content) > 200:
        return False
    if "/" not in content and not content.startswith(".."):
        return False
    # Exclude template syntax (chezmoi, jinja)
    if content.startswith("#") or content.startswith("```"):
        return False
    return "{{" not in content
```

Resolution walks the relative path:

```python
# filter.py:42-68
def resolve_symlink_url(original_url: str, symlink_target: str) -> str:
    owner, repo, ref, path = parse_github_url(original_url)
    dir_parts = path.split("/")[:-1]  # directory of symlink

    for part in symlink_target.split("/"):
        if part == "..":
            dir_parts.pop()
        elif part and part != ".":
            dir_parts.append(part)

    return f"https://github.com/{owner}/{repo}/blob/{ref}/{'/'.join(dir_parts)}"
```

### Validation (Optional)

With `--skip-validation` omitted, each file is sent to Claude for classification:

```python
# filter.py:89-103 (prompt excerpt)
prompt = f"""Analyze this file and determine if it is a valid Claude Code SKILL.md file.

A valid SKILL.md file should:
- Define a skill/capability for Claude Code
- Have clear instructions or prompts
- Not be a generic README or documentation file
- Not be an empty placeholder

Format: {{"is_skill_file": true/false, "reason": "brief explanation"}}"""
```

Results written incrementally to `classified-skills/valid.md` and `invalid.md`.

### Parallel Metadata Fetches

Three additional commands can run after Stage 1 (independent of Stage 2):

| Command | Output | Content |
|---------|--------|---------|
| `fetch metadata` | `repo_metadata.json` | Stars, forks, language, dates |
| `fetch claude-md` | `claude-md/` | CLAUDE.md files from same repos |
| `fetch history` | `skill_history.json` | Commit history per skill file |

---

## Upstream Decisions That Affect Analysis

These collection-phase choices have downstream implications:

### SHA-Based Deduplication

Deduplication keeps one copy per unique content hash, discarding duplicates across repos.

**Impact:** Analysis sees unique *content*, not unique *instances*. A skill copied to 100 forks appears once. This:
- Undercounts popular skills in repo distribution analysis
- Makes "skill propagation" analysis impossible without the raw `skill_files.json`
- Is intentional: we want content diversity, not fork counts

### Symlink Resolution

Symlinks are resolved to their target URLs before storage.

**Impact:** Analysis sees the *resolved* URL, not the symlink. If `repo-a/SKILL.md` is a symlink to `repo-b/SKILL.md`, we store content under repo-b's path. The symlink marker in `valid.md` preserves this information if needed.

### Validation Gate

Only files passing Claude validation reach `valid.md`. The validation prompt's criteria become the dataset filter:
- "Define a skill/capability" - excludes READMEs, documentation
- "Have clear instructions" - excludes placeholders
- "Not be empty" - excludes stubs

**Impact:** Analysis operates on pre-filtered data. If the validation prompt is too strict, legitimate skills are excluded. If too lenient, noise enters analysis.

### Content Truncation

Files >10KB are truncated for LLM classification (`MAX_FILE_CONTENT_LENGTH = 10_000`):

```python
# models.py:9
MAX_FILE_CONTENT_LENGTH = 10_000
```

**Impact:** Very long skills may be misclassified if the truncated portion lacks key signals. Feature extraction uses full content, but LLM analysis sees truncated versions.

### Ref in Path

Content is stored with the git ref (branch/tag) in the path:
```
content/{owner}/{repo}/blob/{ref}/{path}
```

**Impact:** Same file at different refs is stored separately. Most skills use `main`/`master`, but some use tags or commit SHAs. Analysis grouping by "same skill" needs to account for this.

---

## Analysis Stages (Summary)

These consume the collected data:

| Stage | Command | Input | Output |
|-------|---------|-------|--------|
| 3. Filter | `analyze filter` | valid.md, content/ | filtered-skills/*.md |
| 4. Features | `analyze features` | valid.md, content/ | skill_features.parquet |
| 5. Classify | `analyze classify` | valid.md, content/ | skill_classifications.json |
| 6. Cluster | `python -m skill_collection.compute_embeddings` | parquet, content/ | embeddings.npy, cluster_info.json |
| 7. Archetypes | `python -m skill_collection.analyze_archetypes` | cluster_info.json | archetype_analysis.json |

See `DATA_PIPELINE_full.md` for detailed documentation of these stages.

---

## Quick Reference

### Full Collection Run

```bash
# Stage 1: Discover (~1-2 hours with rate limiting)
uv run collect-skills fetch files

# Stage 2: Download + validate (~30 min per 1000 files)
uv run collect-skills fetch content

# Optional parallel fetches
uv run collect-skills fetch metadata &
uv run collect-skills fetch claude-md &
uv run collect-skills fetch history &
```

### Testing/Development

```bash
# Dry run - count results without collecting
uv run collect-skills fetch files --dry-run

# Limit to specific size ranges
uv run collect-skills fetch files --ranges 0,1,2

# Download without validation (fast)
uv run collect-skills fetch content --skip-validation --limit 100

# Download with validation
uv run collect-skills fetch content --limit 100 --validation-concurrency 3
```

### Key Source Files

| File | Purpose |
|------|---------|
| `cli.py` | Command dispatch, main collection loop |
| `collect.py` | Shard collection, deduplication, progress |
| `models.py` | SizeRange, SIZE_RANGES, ShardResult |
| `github.py` | API client, rate limiting, caching |
| `filter.py` | Symlink detection, Claude validation |
| `utils.py` | URL parsing, path resolution |
