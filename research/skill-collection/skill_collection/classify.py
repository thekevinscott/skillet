"""Classify skills using Claude to extract structured taxonomy."""

import asyncio
import contextlib
import json
import signal
import sys
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

from .analyze import parse_valid_md
from .cache import CacheManager
from .github import parse_github_url
from .models import MAX_FILE_CONTENT_LENGTH
from .utils import status, truncate_for_analysis


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
    cache: CacheManager,
    semaphore: asyncio.Semaphore,
    verbose: bool = False,
) -> dict | None:
    """Classify a single skill using Claude."""
    # Truncate very long files to avoid token limits
    content = truncate_for_analysis(content, MAX_FILE_CONTENT_LENGTH)

    # Check cache first
    cached = cache.get(content)
    if cached is not None:
        return {"url": url, "cached": True, **cached}

    # Acquire semaphore for API call
    async with semaphore:
        options = ClaudeAgentOptions(
            allowed_tools=[],
            max_turns=1,
        )

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

        try:
            async for message in query(prompt=prompt, options=options):
                if isinstance(message, ResultMessage):
                    if message.is_error:
                        if verbose:
                            print(f"Error: {message.result}", file=sys.stderr)
                        return None
                    if message.result:
                        try:
                            # Try to extract JSON from the response
                            result_text = message.result.strip()
                            # Handle markdown code blocks
                            if result_text.startswith("```"):
                                result_text = result_text.split("```")[1]
                                if result_text.startswith("json"):
                                    result_text = result_text[4:]
                                result_text = result_text.strip()

                            parsed = json.loads(result_text)
                            cache.set(content, parsed)
                            return {"url": url, "cached": False, **parsed}
                        except json.JSONDecodeError as e:
                            if verbose:
                                print(f"JSON parse error for {url}: {e}", file=sys.stderr)
                                print(f"Response: {message.result[:200]}...", file=sys.stderr)
                            return None
        except Exception as e:
            if verbose:
                print(f"Error classifying {url}: {e}", file=sys.stderr)
            return None

    return None


def cmd_classify(args):
    """Classify skills using Claude."""
    # Handle broken pipe gracefully
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    valid_md_path = args.output_dir / "classified-skills" / "valid.md"
    content_dir = args.output_dir / "content"
    cache_dir = args.output_dir / ".taxonomy_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = CacheManager(cache_dir=cache_dir, skip_cache=args.skip_cache)

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
        local_path = content_dir / owner / repo / "blob" / ref / path
        if local_path.exists():
            content = local_path.read_text()
            if content.strip():
                files_to_classify.append((url, content))

    print(f"Found {len(files_to_classify)} files with content", file=sys.stderr)

    # Track progress
    progress = {"completed": 0, "cached": 0, "api_calls": 0, "errors": 0}
    results: list[dict] = []
    results_lock = asyncio.Lock()
    progress_lock = asyncio.Lock()

    async def classify_and_collect(url: str, content: str, semaphore: asyncio.Semaphore):
        result = await classify_skill(url, content, cache, semaphore, args.verbose)

        async with progress_lock:
            progress["completed"] += 1
            if result is None:
                progress["errors"] += 1
            elif result.get("cached"):
                progress["cached"] += 1
            else:
                progress["api_calls"] += 1

        if result is not None:
            async with results_lock:
                results.append(result)

    async def update_status():
        total = len(files_to_classify)
        while progress["completed"] < total:
            status(
                f"[{progress['completed']}/{total}] "
                f"Classifying ({progress['cached']} cached, {progress['api_calls']} API, "
                f"{progress['errors']} errors)..."
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
        f"Total: {progress['completed']}, Cached: {progress['cached']}, "
        f"API calls: {progress['api_calls']}, Errors: {progress['errors']}",
        file=sys.stderr,
    )

    # Print summary stats
    if results:
        print("\n=== Classification Summary ===", file=sys.stderr)

        # Primary purpose distribution
        purposes = {}
        for r in results:
            p = r.get("primary_purpose", "unknown")
            purposes[p] = purposes.get(p, 0) + 1
        print("\nPrimary Purpose:", file=sys.stderr)
        for p, count in sorted(purposes.items(), key=lambda x: x[1], reverse=True):
            print(f"  {p}: {count}", file=sys.stderr)

        # Knowledge domain distribution
        domains = {}
        for r in results:
            d = r.get("knowledge_domain", "unknown")
            domains[d] = domains.get(d, 0) + 1
        print("\nKnowledge Domain:", file=sys.stderr)
        for d, count in sorted(domains.items(), key=lambda x: x[1], reverse=True):
            print(f"  {d}: {count}", file=sys.stderr)

        # Sophistication distribution
        sophistication = {}
        for r in results:
            s = r.get("sophistication", "unknown")
            sophistication[s] = sophistication.get(s, 0) + 1
        print("\nSophistication:", file=sys.stderr)
        for s, count in sorted(sophistication.items(), key=lambda x: x[1], reverse=True):
            print(f"  {s}: {count}", file=sys.stderr)


