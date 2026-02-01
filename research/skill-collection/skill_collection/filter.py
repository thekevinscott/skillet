"""Filter and classify skill files using Claude Agent SDK."""

import asyncio
import contextlib
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .agent import query_json
from .github import parse_github_url
from .models import MAX_FILE_CONTENT_LENGTH
from .utils import (
    escape_html,
    escape_table_cell,
    resolve_content_path,
    setup_sigpipe_handler,
    status,
    truncate_for_analysis,
    truncate_text,
    truncate_url,
)


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
    # Should not look like markdown, code, or template syntax
    if content.startswith("#") or content.startswith("```"):
        return False
    # Exclude chezmoi/Go template syntax (e.g., {{ includeTemplate "..." }})
    return "{{" not in content


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


@dataclass
class ClassificationProgress:
    """Track classification progress."""

    completed: int = 0
    valid: int = 0
    invalid: int = 0
    errors: int = 0


@dataclass
class SkillFileClassifier:
    """Classifies skill files using Claude and writes results incrementally."""

    cache_dir: Path
    valid_path: Path
    invalid_path: Path
    skip_cache: bool = False
    verbose: bool = False
    concurrency: int = 1
    progress: ClassificationProgress = field(default_factory=ClassificationProgress)
    _progress_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _file_lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def make_link(self, url: str) -> str:
        """Create HTML link with target=_blank."""
        display = escape_html(truncate_url(url))
        return f'<a href="{url}" target="_blank">{display}</a>'

    def format_row(self, resolved_url: str, is_symlink: bool, reason: str) -> str:
        """Format a single table row."""
        symlink_marker = "→" if is_symlink else ""
        escaped_reason = escape_table_cell(truncate_text(reason))
        return f"| {self.make_link(resolved_url)} | {symlink_marker} | {escaped_reason} |\n"

    def initialize_output_files(self):
        """Write headers to output files."""
        with open(self.valid_path, "w") as f:
            f.write("# Valid Skills\n\n")
            f.write("| URL | Symlink | Reason |\n")
            f.write("|-----|:-------:|--------|\n")

        with open(self.invalid_path, "w") as f:
            f.write("# Not Skills\n\n")
            f.write("| URL | Symlink | Reason |\n")
            f.write("|-----|:-------:|--------|\n")

    async def write_result(self, is_valid: bool, resolved_url: str, is_symlink: bool, reason: str):
        """Write a classification result to the appropriate file."""
        path = self.valid_path if is_valid else self.invalid_path
        async with self._file_lock:
            with open(path, "a") as f:
                f.write(self.format_row(resolved_url, is_symlink, reason))

    async def update_progress(self, **kwargs):
        """Update progress counters."""
        async with self._progress_lock:
            for key, value in kwargs.items():
                setattr(self.progress, key, getattr(self.progress, key) + value)

    async def classify_file(self, url: str, file_path: Path, semaphore: asyncio.Semaphore):
        """Classify a single file and write result immediately."""
        content = file_path.read_text()

        # Skip empty files
        if not content.strip():
            await self.write_result(False, url, False, "empty file")
            await self.update_progress(completed=1, invalid=1)
            return

        # Check if this is a symlink
        is_symlink = is_symlink_content(content)
        resolved_url = resolve_symlink_url(url, content) if is_symlink else url

        # Truncate very long files to avoid token limits
        content = truncate_for_analysis(content, MAX_FILE_CONTENT_LENGTH)

        # Build prompt for classification
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

        # Acquire semaphore for API call
        async with semaphore:
            result_data = await query_json(
                prompt,
                cache_dir=self.cache_dir,
                skip_cache=self.skip_cache,
                verbose=self.verbose,
            )

            if result_data is None:
                await self.write_result(False, resolved_url, is_symlink, "Failed to classify")
                await self.update_progress(completed=1, errors=1)
            else:
                is_valid = result_data.get("is_skill_file", False)
                await self.write_result(
                    is_valid, resolved_url, is_symlink, result_data.get("reason", "")
                )
                await self.update_progress(
                    completed=1, valid=1 if is_valid else 0, invalid=0 if is_valid else 1
                )

    async def run(self, files_to_classify: list[tuple[str, Path]]):
        """Run classification on all files."""
        self.initialize_output_files()

        semaphore = asyncio.Semaphore(self.concurrency)

        async def update_status_loop():
            total = len(files_to_classify)
            while self.progress.completed < total:
                status(
                    f"[{self.progress.completed}/{total}] "
                    f"Classifying ({self.progress.valid} valid, {self.progress.invalid} invalid, "
                    f"{self.progress.errors} errors)..."
                )
                await asyncio.sleep(0.1)

        status_task = asyncio.create_task(update_status_loop())

        tasks = [
            self.classify_file(url, file_path, semaphore) for url, file_path in files_to_classify
        ]
        await asyncio.gather(*tasks)

        status_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await status_task


def cmd_filter_skills(args, load_skill_urls):
    """Classify files as skill files using Claude Agent SDK."""
    setup_sigpipe_handler()

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
        local_path = resolve_content_path(content_dir, owner, repo, ref, path)
        if local_path.exists():
            files_to_classify.append((url, local_path))

    print(f"Classifying {len(files_to_classify)} files...", file=sys.stderr)

    # Setup output directory
    output_dir = args.output if args.output else args.output_dir / "classified-skills"
    output_dir.mkdir(parents=True, exist_ok=True)

    classifier = SkillFileClassifier(
        cache_dir=cache_dir,
        valid_path=output_dir / "valid.md",
        invalid_path=output_dir / "invalid.md",
        skip_cache=args.skip_cache,
        verbose=args.verbose,
        concurrency=args.concurrency,
    )

    asyncio.run(classifier.run(files_to_classify))

    print()  # New line after status
    print(f"Results saved to {output_dir}/", file=sys.stderr)
    p = classifier.progress
    print(
        f"Total: {p.completed}, Valid: {p.valid}, Invalid: {p.invalid}, Errors: {p.errors}",
        file=sys.stderr,
    )
