"""Classify skills using Claude to extract structured taxonomy."""

import asyncio
import contextlib
import json
import signal
import sys
from collections import Counter
from pathlib import Path

from .agent import query_json
from .analyze import parse_valid_md
from .github import parse_github_url
from .models import MAX_FILE_CONTENT_LENGTH
from .utils import resolve_content_path, status, truncate_for_analysis


def _print_distribution(results: list[dict], field: str, label: str):
    """Print a sorted distribution of field values."""
    counts = Counter(r.get(field, "unknown") for r in results)
    print(f"\n{label}:", file=sys.stderr)
    for value, count in counts.most_common():
        print(f"  {value}: {count}", file=sys.stderr)

CLASSIFICATION_SCHEMA = """{
  "summary": "1-sentence description of what this skill enables",
  "primary_purpose": "teaching|automation|enforcement|documentation|debugging|refactoring|integration|meta",
  "knowledge_domain": "framework|language|tooling|architecture|process|meta|general",
  "domain_specifics": ["specific tools/frameworks mentioned, e.g., 'zod', 'typescript'"],
  "scope": "universal|language-bound|framework-bound|project-specific",
  "trigger_mechanism": "keyword|intent|context|manual|always-on|unknown",
  "claude_role": "generator|advisor|enforcer|teacher|translator|mixed",
  "output_modality": ["code", "commands", "files", "text", "structured"],
  "sophistication": "minimal|standard|comprehensive|system-grade",
  "has_examples": true,
  "has_explicit_rules": true,
  "has_external_refs": true,
  "quality_score": 3,
  "notable_features": ["optional list of interesting aspects"],
  "anti_patterns": ["optional list of issues"]
}"""


async def classify_skill(
    url: str,
    content: str,
    cache_dir: Path,
    semaphore: asyncio.Semaphore,
    skip_cache: bool = False,
    verbose: bool = False,
) -> dict | None:
    """Classify a single skill using Claude."""
    # Truncate very long files to avoid token limits
    content = truncate_for_analysis(content, MAX_FILE_CONTENT_LENGTH)

    prompt = f"""Analyze this Claude Code SKILL.md file and extract a structured classification.

File content:
```
{content}
```

Return a JSON object with this exact schema:
{CLASSIFICATION_SCHEMA}

Guidelines:
- primary_purpose: Choose the MOST dominant purpose
  - teaching: Explains concepts, best practices
  - automation: Generates code/files, runs commands
  - enforcement: Code style, conventions, quality gates
  - documentation: Generates docs, changelogs
  - debugging: Troubleshooting, error handling
  - refactoring: Code transformation patterns
  - integration: Connects tools, APIs, services
  - meta: About Claude Code itself, skill authoring

- knowledge_domain: What domain of knowledge?
  - framework: Specific library (react, zod, prisma)
  - language: Language patterns (typescript, python)
  - tooling: git, docker, CI/CD, testing
  - architecture: API design, state management
  - process: Code review, commits, PR workflows
  - meta: Claude Code, AI tools
  - general: General purpose, not domain-specific

- scope: How broadly applicable?
  - universal: Any project
  - language-bound: Specific language ecosystem
  - framework-bound: Specific framework
  - project-specific: Custom to one repo

- trigger_mechanism: How is this skill activated?
  - keyword: Triggers on specific terms
  - intent: Triggers on detected user intent
  - context: Triggers based on file type, project structure
  - manual: Explicitly invoked (slash command)
  - always-on: Background guidance
  - unknown: Cannot determine

- claude_role: What role does Claude play?
  - generator: Produces artifacts
  - advisor: Provides guidance
  - enforcer: Validates, rejects non-compliant work
  - teacher: Explains concepts
  - translator: Converts between formats
  - mixed: Multiple roles

- sophistication: How comprehensive?
  - minimal: Few lines, simple reminder
  - standard: Clear structure, some examples
  - comprehensive: Multiple sections, extensive examples
  - system-grade: Complex workflows, error handling

- quality_score: 1-5 (1=poor, 5=excellent)

IMPORTANT: Respond with ONLY the JSON object, no other text."""

    # Acquire semaphore for API call
    async with semaphore:
        result = await query_json(
            prompt,
            cache_dir=cache_dir,
            skip_cache=skip_cache,
            verbose=verbose,
        )
        if result is not None:
            return {"url": url, **result}
        return None


def cmd_classify(args):
    """Classify skills using Claude."""
    # Handle broken pipe gracefully
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    valid_md_path = args.output_dir / "classified-skills" / "valid.md"
    content_dir = args.output_dir / "content"
    cache_dir = args.output_dir / ".taxonomy_cache"

    if not valid_md_path.exists():
        raise FileNotFoundError(f"{valid_md_path} not found. Run 'filter-skills' first.")

    # Parse valid.md to get URLs
    urls = parse_valid_md(valid_md_path)
    if args.limit:
        urls = urls[: args.limit]

    print(f"Classifying {len(urls)} skills...", file=sys.stderr)

    # Collect files with content
    files_to_classify: list[tuple[str, str]] = []
    for url in urls:
        parsed = parse_github_url(url)
        if not parsed:
            continue
        owner, repo, ref, path = parsed
        local_path = resolve_content_path(content_dir, owner, repo, ref, path)
        if local_path.exists():
            content = local_path.read_text()
            if content.strip():
                files_to_classify.append((url, content))

    print(f"Found {len(files_to_classify)} files with content", file=sys.stderr)

    # Track progress
    progress = {"completed": 0, "errors": 0}
    results: list[dict] = []
    results_lock = asyncio.Lock()
    progress_lock = asyncio.Lock()

    async def classify_and_collect(url: str, content: str, semaphore: asyncio.Semaphore):
        result = await classify_skill(
            url, content, cache_dir, semaphore, skip_cache=args.skip_cache, verbose=args.verbose
        )

        async with progress_lock:
            progress["completed"] += 1
            if result is None:
                progress["errors"] += 1

        if result is not None:
            async with results_lock:
                results.append(result)

    async def update_status():
        total = len(files_to_classify)
        while progress["completed"] < total:
            status(
                f"[{progress['completed']}/{total}] Classifying ({progress['errors']} errors)..."
            )
            await asyncio.sleep(0.1)

    async def classify_all():
        semaphore = asyncio.Semaphore(args.concurrency)
        status_task = asyncio.create_task(update_status())

        tasks = [
            classify_and_collect(url, content, semaphore) for url, content in files_to_classify
        ]
        await asyncio.gather(*tasks)

        status_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await status_task

    asyncio.run(classify_all())

    print(file=sys.stderr)  # New line after status

    # Save results
    output_path = args.output if args.output else args.output_dir / "skill_classifications.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Saved {len(results)} classifications to {output_path}", file=sys.stderr)
    print(
        f"Total: {progress['completed']}, Errors: {progress['errors']}",
        file=sys.stderr,
    )

    # Print summary stats
    if results:
        print("\n=== Classification Summary ===", file=sys.stderr)
        _print_distribution(results, "primary_purpose", "Primary Purpose")
        _print_distribution(results, "knowledge_domain", "Knowledge Domain")
        _print_distribution(results, "sophistication", "Sophistication")
