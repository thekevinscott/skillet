"""Filter and classify skill files using Claude Agent SDK."""

import asyncio
import contextlib
import hashlib
import json
import signal
import sys
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

from .github import parse_github_url
from .utils import status, truncate_text, truncate_url


def is_symlink_content(content: str) -> bool:
    """Check if file content looks like a git symlink (path to another file)."""
    content = content.strip()
    # Symlinks in git are small files containing just a relative path
    # They don't have newlines and typically point to another file
    if "\n" in content or len(content) > 200:
        return False
    # Must look like a relative path (contains / or starts with ..)
    if "/" not in content and not content.startswith(".."):
        return False
    # Should not look like markdown or code
    return not (content.startswith("#") or content.startswith("```"))


def resolve_symlink_url(original_url: str, symlink_target: str) -> str:
    """Resolve a symlink target path relative to the original URL.

    Example:
        original_url: https://github.com/owner/repo/blob/ref/some/path/SKILL.md
        symlink_target: ../../other/location/SKILL.md
        result: https://github.com/owner/repo/blob/ref/other/location/SKILL.md
    """
    parsed = parse_github_url(original_url)
    if not parsed:
        return original_url

    owner, repo, ref, path = parsed
    # Get directory of the symlink
    path_parts = path.split("/")
    dir_parts = path_parts[:-1]  # Remove filename

    # Resolve the relative path
    target_parts = symlink_target.strip().split("/")
    for part in target_parts:
        if part == "..":
            if dir_parts:
                dir_parts.pop()
        elif part and part != ".":
            dir_parts.append(part)

    resolved_path = "/".join(dir_parts)
    return f"https://github.com/{owner}/{repo}/blob/{ref}/{resolved_path}"


def cmd_filter_skills(args, load_skill_urls):
    """Classify files as skill files using Claude Agent SDK."""
    # Handle broken pipe gracefully (e.g., when piping to head)
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    urls = load_skill_urls(args.output_dir)
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
            return json.loads(cache_file.read_text())
        return None

    def cache_result(content: str, result: dict):
        """Cache a classification result."""
        cache_file = cache_dir / f"{get_cache_key(content)}.json"
        cache_file.write_text(json.dumps(result))

    # Setup output directory and files for incremental writes
    output_dir = args.output if args.output else args.output_dir / "classified-skills"
    output_dir.mkdir(parents=True, exist_ok=True)
    valid_path = output_dir / "valid.md"
    invalid_path = output_dir / "invalid.md"

    def escape_html(text: str) -> str:
        """Escape HTML special characters."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    def make_link(url: str) -> str:
        """Create HTML link with target=_blank."""
        display = escape_html(truncate_url(url))
        return f'<a href="{url}" target="_blank">{display}</a>'

    def format_row(resolved_url: str, is_symlink: bool, reason: str) -> str:
        """Format a single table row."""
        symlink_marker = "→" if is_symlink else ""
        return f"| {make_link(resolved_url)} | {symlink_marker} | {truncate_text(reason)} |\n"

    # Initialize output files with headers
    with open(valid_path, "w") as f:
        f.write("# Valid Skills\n\n")
        f.write("| URL | Symlink | Reason |\n")
        f.write("|-----|:-------:|--------|\n")

    with open(invalid_path, "w") as f:
        f.write("# Not Skills\n\n")
        f.write("| URL | Symlink | Reason |\n")
        f.write("|-----|:-------:|--------|\n")

    # Track progress
    progress = {"completed": 0, "cached": 0, "api_calls": 0, "valid": 0, "invalid": 0, "errors": 0}
    progress_lock = asyncio.Lock()
    file_lock = asyncio.Lock()

    async def classify_and_write(url: str, file_path: Path, semaphore: asyncio.Semaphore):
        """Classify a single file and write result immediately."""
        content = file_path.read_text()

        # Skip empty files
        if not content.strip():
            async with file_lock:
                with open(invalid_path, "a") as f:
                    f.write(format_row(url, False, "empty file"))
            async with progress_lock:
                progress["completed"] += 1
                progress["invalid"] += 1
            return

        # Check if this is a symlink
        is_symlink = is_symlink_content(content)
        resolved_url = url
        if is_symlink:
            resolved_url = resolve_symlink_url(url, content)

        # Truncate very long files to avoid token limits
        if len(content) > 10000:
            content = content[:10000] + "\n\n[truncated]"

        # Check cache first
        cached = get_cached_result(content)
        if cached is not None:
            async with file_lock:
                if cached.get("is_skill_file"):
                    with open(valid_path, "a") as f:
                        f.write(format_row(resolved_url, is_symlink, cached.get("reason", "")))
                    async with progress_lock:
                        progress["valid"] += 1
                else:
                    with open(invalid_path, "a") as f:
                        f.write(format_row(resolved_url, is_symlink, cached.get("reason", "")))
                    async with progress_lock:
                        progress["invalid"] += 1
            async with progress_lock:
                progress["completed"] += 1
                progress["cached"] += 1
            return

        # Acquire semaphore for API call
        async with semaphore:
            async with progress_lock:
                progress["api_calls"] += 1

            options = ClaudeAgentOptions(
                allowed_tools=[],
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
                async for message in query(prompt=prompt, options=options):
                    if isinstance(message, ResultMessage):
                        if message.is_error:
                            print(f"Error: {message.result}", file=sys.stderr)
                        elif message.result:
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
            except Exception as e:
                print(f"Error classifying {url}: {e}", file=sys.stderr)

            # Write result immediately
            async with file_lock:
                if result_data is None:
                    with open(invalid_path, "a") as f:
                        f.write(format_row(resolved_url, is_symlink, "Failed to classify"))
                    async with progress_lock:
                        progress["errors"] += 1
                elif result_data.get("is_skill_file"):
                    with open(valid_path, "a") as f:
                        f.write(format_row(resolved_url, is_symlink, result_data.get("reason", "")))
                    async with progress_lock:
                        progress["valid"] += 1
                else:
                    with open(invalid_path, "a") as f:
                        f.write(format_row(resolved_url, is_symlink, result_data.get("reason", "")))
                    async with progress_lock:
                        progress["invalid"] += 1

            async with progress_lock:
                progress["completed"] += 1

    async def update_status():
        """Periodically update status line."""
        total = len(files_to_classify)
        while progress["completed"] < total:
            status(
                f"[{progress['completed']}/{total}] "
                f"Classifying ({progress['valid']} valid, {progress['invalid']} invalid, "
                f"{progress['cached']} cached, {progress['api_calls']} API calls)..."
            )
            await asyncio.sleep(0.1)

    async def classify_all():
        semaphore = asyncio.Semaphore(args.concurrency)
        status_task = asyncio.create_task(update_status())

        tasks = [classify_and_write(url, file_path, semaphore) for url, file_path in files_to_classify]
        await asyncio.gather(*tasks)

        status_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await status_task

    asyncio.run(classify_all())

    print()  # New line after status
    print(f"Results saved to {output_dir}/", file=sys.stderr)
    print(
        f"Total: {progress['completed']}, Valid: {progress['valid']}, Invalid: {progress['invalid']}, "
        f"Errors: {progress['errors']}, Cached: {progress['cached']}, API calls: {progress['api_calls']}",
        file=sys.stderr,
    )
