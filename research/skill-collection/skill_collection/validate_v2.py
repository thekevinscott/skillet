"""Validation module for v2 pipeline.

Validates skill content using Claude and stores results in SQLite.
Uses existing .classify_cache/ for transition period.
"""

import asyncio
from collections.abc import Callable
from pathlib import Path

from .agent import query_json
from .db import get_db_context
from .filter import is_symlink_content, resolve_symlink_url
from .models import MAX_FILE_CONTENT_LENGTH
from .utils import truncate_for_analysis

# Model version for reproducibility tracking
MODEL_VERSION = "claude-3-5-sonnet"


def get_unvalidated_content(
    db_path: Path | None = None,
    limit: int | None = None,
) -> list[tuple[str, str, str]]:
    """Get skills with content but no validation.

    Returns list of (sha, url, body) tuples.
    """
    with get_db_context(db_path) as conn:
        query = """
            SELECT s.sha, s.url, c.body
            FROM skills s
            JOIN content c ON s.sha = c.sha
            LEFT JOIN validations v ON s.sha = v.sha
            WHERE v.sha IS NULL
            ORDER BY s.discovered_at
        """
        if limit:
            query += f" LIMIT {limit}"

        rows = conn.execute(query).fetchall()
        return [(row["sha"], row["url"], row["body"]) for row in rows]


def store_validation(
    sha: str,
    is_valid: bool,
    reason: str,
    model_version: str = MODEL_VERSION,
    db_path: Path | None = None,
):
    """Store validation result in database."""
    with get_db_context(db_path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO validations (sha, is_valid, reason, model_version, validated_at) "
            "VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
            (sha, is_valid, reason, model_version),
        )


def build_validation_prompt(content: str) -> str:
    """Build the validation prompt for Claude."""
    truncated = truncate_for_analysis(content, MAX_FILE_CONTENT_LENGTH)

    return f"""Analyze this file and determine if it is a valid Claude Code SKILL.md file.

A valid SKILL.md file should:
- Define a skill/capability for Claude Code
- Have clear instructions or prompts
- Not be a generic README or documentation file
- Not be an empty placeholder

File content:
```
{truncated}
```

IMPORTANT: Respond with ONLY a JSON object, no other text.
Format: {{"is_skill_file": true/false, "reason": "brief explanation"}}"""


async def validate_skill(
    sha: str,
    url: str,
    body: str,
    cache_dir: Path | None = None,
    skip_cache: bool = False,
    verbose: bool = False,
    db_path: Path | None = None,
) -> tuple[bool, bool, bool]:
    """Validate a single skill.

    Returns (is_valid, from_cache, had_error).
    """
    # Handle empty content
    if not body.strip():
        store_validation(sha, False, "empty file", db_path=db_path)
        return False, False, False

    # Handle symlinks
    if is_symlink_content(body):
        # For symlinks, we treat them as invalid since we can't follow them
        # The resolved URL is stored in the reason
        resolved = resolve_symlink_url(url, body)
        store_validation(sha, False, f"symlink to {resolved}", db_path=db_path)
        return False, False, False

    # Build and run validation
    prompt = build_validation_prompt(body)

    result_data, from_cache = await query_json(
        prompt,
        cache_dir=cache_dir,
        skip_cache=skip_cache,
        verbose=verbose,
    )

    if result_data is None:
        store_validation(sha, False, "validation failed", db_path=db_path)
        return False, False, True

    is_valid = result_data.get("is_skill_file", False)
    reason = result_data.get("reason", "")
    store_validation(sha, is_valid, reason, db_path=db_path)

    return is_valid, from_cache, False


async def run_validation(
    db_path: Path | None = None,
    cache_dir: Path | None = None,
    limit: int | None = None,
    concurrency: int = 1,
    skip_cache: bool = False,
    verbose: bool = False,
    on_progress: Callable[[int, int, int, int, int], None] | None = None,
) -> dict:
    """Validate skills that have content but no validation.

    Returns stats about the validation run.
    """
    skills = get_unvalidated_content(db_path, limit)
    total = len(skills)

    if total == 0:
        return {
            "total": 0,
            "valid": 0,
            "invalid": 0,
            "cached": 0,
            "errors": 0,
        }

    counters = {"valid": 0, "invalid": 0, "cached": 0, "errors": 0, "processed": 0}
    lock = asyncio.Lock()

    async def validate_one(sha: str, url: str, body: str, semaphore: asyncio.Semaphore):
        async with semaphore:
            is_valid, from_cache, had_error = await validate_skill(
                sha,
                url,
                body,
                cache_dir=cache_dir,
                skip_cache=skip_cache,
                verbose=verbose,
                db_path=db_path,
            )

            async with lock:
                counters["processed"] += 1
                if had_error:
                    counters["errors"] += 1
                elif is_valid:
                    counters["valid"] += 1
                else:
                    counters["invalid"] += 1
                if from_cache:
                    counters["cached"] += 1

                if on_progress:
                    on_progress(
                        counters["processed"],
                        counters["valid"],
                        counters["invalid"],
                        counters["cached"],
                        counters["errors"],
                    )

    semaphore = asyncio.Semaphore(concurrency)
    tasks = [
        validate_one(sha, url, body, semaphore)
        for sha, url, body in skills
    ]
    await asyncio.gather(*tasks)

    return {
        "total": total,
        "valid": counters["valid"],
        "invalid": counters["invalid"],
        "cached": counters["cached"],
        "errors": counters["errors"],
    }
