"""Repository information collection commands."""

import base64
import json
import os
import re
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path

from .github import get_client
from .utils import parse_github_url, status


@dataclass
class RepoMetadata:
    """Repository metadata from GitHub API."""

    owner: str
    repo: str
    stars: int
    forks: int
    watchers: int
    language: str | None
    topics: list[str]
    created_at: str
    updated_at: str
    pushed_at: str
    default_branch: str
    license: str | None
    is_org: bool
    description: str | None


CLAUDE_MD_PATHS = [
    "CLAUDE.md",
    ".claude/CLAUDE.md",
    "docs/CLAUDE.md",
    ".github/CLAUDE.md",
]


def atomic_write_json(path: Path, data: dict):
    """Write JSON atomically using temp file + rename."""
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".json.tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def extract_unique_repos(urls: list[str]) -> dict[tuple[str, str], list[str]]:
    """Extract unique (owner, repo) pairs from URLs, tracking which URLs belong to each.

    Returns dict mapping (owner, repo) -> list of URLs in that repo.
    """
    repos: dict[tuple[str, str], list[str]] = {}
    for url in urls:
        parsed = parse_github_url(url)
        if parsed:
            owner, repo, _, _ = parsed
            key = (owner, repo)
            if key not in repos:
                repos[key] = []
            repos[key].append(url)
    return repos


def load_valid_skill_urls(output_dir: Path) -> list[str]:
    """Load validated skill URLs from valid.md.

    Parses the markdown table and extracts URLs from anchor tags.
    """
    valid_md = output_dir / "classified-skills" / "valid.md"
    if not valid_md.exists():
        raise FileNotFoundError(f"{valid_md} not found. Run 'filter-skills' first.")

    content = valid_md.read_text()
    # Match URLs in anchor tags: <a href="URL"
    pattern = r'<a href="(https://github\.com/[^"]+)"'
    return re.findall(pattern, content)


def fetch_repo_metadata(client, owner: str, repo: str) -> RepoMetadata:
    """Fetch repository metadata via GitHub API."""
    data = client.api(f"repos/{owner}/{repo}")
    return RepoMetadata(
        owner=owner,
        repo=repo,
        stars=data["stargazers_count"],
        forks=data["forks_count"],
        watchers=data["watchers_count"],
        language=data.get("language"),
        topics=data.get("topics", []),
        created_at=data["created_at"],
        updated_at=data["updated_at"],
        pushed_at=data["pushed_at"],
        default_branch=data["default_branch"],
        license=data.get("license", {}).get("spdx_id") if data.get("license") else None,
        is_org=data["owner"]["type"] == "Organization",
        description=data.get("description"),
    )


def fetch_claude_md_files(client, owner: str, repo: str, ref: str) -> dict[str, str]:
    """Check for CLAUDE.md in common locations, return {path: content}."""
    found = {}
    for path in CLAUDE_MD_PATHS:
        try:
            data = client.get_file_content(owner, repo, path, ref=ref)
            if "content" in data:
                content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
                found[path] = content
        except FileNotFoundError:
            continue
    return found


def fetch_skill_commits(client, owner: str, repo: str, path: str) -> list[dict]:
    """Fetch commit history for a specific file (up to 100 commits)."""
    commits = client.api(f"repos/{owner}/{repo}/commits", params={"path": path, "per_page": "100"})
    # commits is a list
    if isinstance(commits, dict) and "message" in commits:
        # API error
        return []
    return [
        {
            "sha": c["sha"][:7],
            "author": c["commit"]["author"]["name"],
            "date": c["commit"]["author"]["date"],
            "message": c["commit"]["message"].split("\n")[0][:80],
        }
        for c in commits
    ]


def cmd_fetch_repo_metadata(args):
    """Fetch repository metadata (stars, forks, language, etc.)."""
    output_dir = args.output_dir
    client = get_client()

    urls = load_valid_skill_urls(output_dir)
    repos = extract_unique_repos(urls)

    if args.limit:
        repos = dict(list(repos.items())[: args.limit])

    print(f"Fetching metadata for {len(repos)} repositories...")

    # Load existing progress if resuming
    output_file = output_dir / "repo_metadata.json"
    if output_file.exists():
        with open(output_file) as f:
            metadata = json.load(f)
        print(f"Resuming: loaded {len(metadata)} existing entries")
    else:
        metadata = {}

    counters = {"processed": 0, "fetched": 0, "cached": 0, "errors": 0}
    lock = threading.Lock()

    def fetch_one(key: tuple[str, str]):
        owner, repo = key
        repo_key = f"{owner}/{repo}"

        # Skip if already fetched
        if repo_key in metadata:
            with lock:
                counters["cached"] += 1
                counters["processed"] += 1
            return

        try:
            meta = fetch_repo_metadata(client, owner, repo)
            with lock:
                metadata[repo_key] = asdict(meta)
                counters["fetched"] += 1
        except Exception as e:
            with lock:
                metadata[repo_key] = {"error": str(e)}
                counters["errors"] += 1

        with lock:
            counters["processed"] += 1

    # Use 10 concurrent workers
    concurrency = getattr(args, "concurrency", 10)
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {executor.submit(fetch_one, key): key for key in repos}

        for future in as_completed(futures):
            future.result()  # Propagate exceptions
            with lock:
                processed = counters["processed"]
                fetched = counters["fetched"]
                cached = counters["cached"]
                errors = counters["errors"]
            status(
                f"[{processed}/{len(repos)}] {fetched} fetched, {cached} cached, {errors} errors"
            )

            # Save periodically
            if processed % 50 == 0:
                with lock:
                    atomic_write_json(output_file, metadata)

    atomic_write_json(output_file, metadata)
    print(
        f"\n\nDone: {counters['fetched']} fetched, {counters['cached']} cached, {counters['errors']} errors"
    )
    print(f"Saved to {output_file}")


def cmd_fetch_claude_md(args):
    """Fetch CLAUDE.md files from skill repositories."""
    output_dir = args.output_dir
    client = get_client()

    urls = load_valid_skill_urls(output_dir)
    repos = extract_unique_repos(urls)

    if args.limit:
        repos = dict(list(repos.items())[: args.limit])

    print(f"Checking CLAUDE.md in {len(repos)} repositories...")

    claude_md_dir = output_dir / "claude_md"
    claude_md_dir.mkdir(exist_ok=True)

    # Load existing index if resuming
    index_file = output_dir / "claude_md_index.json"
    if index_file.exists():
        with open(index_file) as f:
            index = json.load(f)
        print(f"Resuming: loaded {len(index)} existing entries")
    else:
        index = {}

    # Load repo metadata to get default branches
    meta_file = output_dir / "repo_metadata.json"
    repo_meta = {}
    if meta_file.exists():
        with open(meta_file) as f:
            repo_meta = json.load(f)

    counters = {"processed": 0, "found": 0, "not_found": 0, "errors": 0}
    lock = threading.Lock()

    def fetch_one(key: tuple[str, str]):
        owner, repo = key
        repo_key = f"{owner}/{repo}"

        # Skip if already processed
        if repo_key in index:
            with lock:
                counters["processed"] += 1
            return

        # Get default branch from metadata or use main
        ref = repo_meta.get(repo_key, {}).get("default_branch", "main")

        try:
            found = fetch_claude_md_files(client, owner, repo, ref)
            with lock:
                if found:
                    index[repo_key] = list(found.keys())
                    counters["found"] += 1

                    # Save files
                    repo_dir = claude_md_dir / owner / repo
                    repo_dir.mkdir(parents=True, exist_ok=True)
                    for path, content in found.items():
                        safe_path = path.replace("/", "_")
                        (repo_dir / safe_path).write_text(content)
                else:
                    index[repo_key] = []
                    counters["not_found"] += 1
        except Exception as e:
            with lock:
                index[repo_key] = {"error": str(e)}
                counters["errors"] += 1

        with lock:
            counters["processed"] += 1

    # Use 10 concurrent workers
    concurrency = getattr(args, "concurrency", 10)
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {executor.submit(fetch_one, key): key for key in repos}

        for future in as_completed(futures):
            future.result()
            with lock:
                processed = counters["processed"]
                found = counters["found"]
                not_found = counters["not_found"]
                errors = counters["errors"]
            status(
                f"[{processed}/{len(repos)}] {found} found, {not_found} not found, {errors} errors"
            )

            # Save periodically
            if processed % 50 == 0:
                with lock:
                    atomic_write_json(index_file, index)

    atomic_write_json(index_file, index)
    repos_with_claude_md = sum(1 for v in index.values() if isinstance(v, list) and v)
    print(f"\n\nDone: {repos_with_claude_md} repos with CLAUDE.md files")
    print(f"Saved index to {index_file}")
    print(f"Files saved to {claude_md_dir}/")


def cmd_fetch_skill_history(args):
    """Fetch commit history for skill files."""
    output_dir = args.output_dir
    client = get_client()

    urls = load_valid_skill_urls(output_dir)

    if args.limit:
        urls = urls[: args.limit]

    print(f"Fetching commit history for {len(urls)} skills...")

    # Load existing progress if resuming
    output_file = output_dir / "skill_history.json"
    if output_file.exists():
        with open(output_file) as f:
            history = json.load(f)
        print(f"Resuming: loaded {len(history)} existing entries")
    else:
        history = {}

    counters = {"processed": 0, "fetched": 0, "cached": 0, "errors": 0}
    lock = threading.Lock()

    def fetch_one(url: str):
        # Skip if already fetched
        if url in history:
            with lock:
                counters["cached"] += 1
                counters["processed"] += 1
            return

        parsed = parse_github_url(url)
        if not parsed:
            with lock:
                history[url] = {"error": "Invalid URL"}
                counters["errors"] += 1
                counters["processed"] += 1
            return

        owner, repo, _, path = parsed

        try:
            commits = fetch_skill_commits(client, owner, repo, path)
            with lock:
                history[url] = commits
                counters["fetched"] += 1
        except Exception as e:
            with lock:
                history[url] = {"error": str(e)}
                counters["errors"] += 1

        with lock:
            counters["processed"] += 1

    # Use 10 concurrent workers
    concurrency = getattr(args, "concurrency", 10)
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {executor.submit(fetch_one, url): url for url in urls}

        for future in as_completed(futures):
            future.result()
            with lock:
                processed = counters["processed"]
                fetched = counters["fetched"]
                cached = counters["cached"]
                errors = counters["errors"]
            status(f"[{processed}/{len(urls)}] {fetched} fetched, {cached} cached, {errors} errors")

            # Save periodically
            if processed % 100 == 0:
                with lock:
                    atomic_write_json(output_file, history)

    atomic_write_json(output_file, history)
    print(
        f"\n\nDone: {counters['fetched']} fetched, {counters['cached']} cached, {counters['errors']} errors"
    )
    print(f"Saved to {output_file}")
