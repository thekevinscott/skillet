"""GitHub API client with built-in caching and rate limiting."""

import hashlib
import json
import subprocess
import time
from pathlib import Path

DEFAULT_CACHE_DIR = Path(__file__).parent.parent / ".cache"

# GitHub Code Search API has a separate rate limit of 10 requests per minute
# (regardless of authentication). General API is 5000/hour but search is stricter.
# https://docs.github.com/en/rest/search#rate-limit
# Start slightly under the limit to avoid ever hitting it
INITIAL_REQUESTS_PER_MINUTE = 8  # 7.5s between requests
MIN_REQUESTS_PER_MINUTE = 4  # Floor for backoff (15s between requests)
BACKOFF_FACTOR = 0.75  # Reduce by 25% on each rate limit hit


class RateLimiter:
    """Track rate limiting from both GitHub headers and our own request timing.

    Uses adaptive throttling: starts at the documented limit and backs off
    if we hit rate limits. This maximizes throughput while staying under limits.
    """

    def __init__(self, requests_per_minute: int = INITIAL_REQUESTS_PER_MINUTE):
        self.requests_per_minute = requests_per_minute
        self.min_interval = 60.0 / requests_per_minute

        # GitHub's reported limits (from response headers)
        self.remaining = requests_per_minute
        self.reset_time = 0

        # Our own tracking (backup when headers aren't available)
        self.last_request_time = 0.0
        self.request_count = 0
        self.rate_limit_hits = 0  # Count how many times we've hit limits

    def update_from_headers(self, headers: str):
        """Parse rate limit info from GitHub response headers."""
        for line in headers.split("\n"):
            lower = line.lower()
            if lower.startswith("x-ratelimit-remaining:"):
                self.remaining = int(line.split(":")[1].strip())
            elif lower.startswith("x-ratelimit-reset:"):
                self.reset_time = int(line.split(":")[1].strip())

    def record_request(self):
        """Record that a request was made."""
        self.last_request_time = time.time()
        self.request_count += 1
        if self.remaining > 0:
            self.remaining -= 1

    def wait_if_needed(self):
        """Wait if we're about to hit the rate limit. Returns immediately if OK to proceed."""
        now = time.time()

        # Check if we're rate limited by GitHub's reported remaining count
        if self.remaining == 0 and self.reset_time > now:
            wait_time = self.reset_time - now + 1
            self._wait(wait_time, "GitHub rate limit")
            self.remaining = self.requests_per_minute
            return

        # Always ensure minimum interval between requests
        # This includes the first request (last_request_time starts at 0, so first request
        # won't wait unless we've made recent requests in this session)
        if self.last_request_time > 0:
            elapsed = now - self.last_request_time
            if elapsed < self.min_interval:
                wait_time = self.min_interval - elapsed
                # Only log if waiting more than a trivial amount
                if wait_time > 0.5:
                    self._wait(wait_time, "throttle")
                else:
                    time.sleep(wait_time)

    def force_wait(self):
        """Force a wait until the rate limit resets (called after hitting a limit).

        Also backs off the request rate to reduce future hits.
        """
        self.rate_limit_hits += 1

        # Back off: reduce requests per minute
        old_interval = self.min_interval
        new_rpm = max(MIN_REQUESTS_PER_MINUTE, self.requests_per_minute * BACKOFF_FACTOR)
        self.requests_per_minute = new_rpm
        self.min_interval = 60.0 / new_rpm

        print(
            f"[BACKOFF] Hit rate limit #{self.rate_limit_hits}, "
            f"increasing interval from {old_interval:.1f}s to {self.min_interval:.1f}s"
        )

        now = time.time()
        if self.reset_time > now:
            wait_time = self.reset_time - now + 1
        else:
            # If reset_time is in the past, wait a full minute
            wait_time = 60

        self._wait(wait_time, "rate limited")
        self.remaining = int(self.requests_per_minute)

    def _wait(self, seconds: float, reason: str):
        """Wait with status update."""
        print(f"[{reason}] waiting {seconds:.0f}s...")
        time.sleep(seconds)


class Cache:
    """Simple file-based cache for API responses."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir

    def _key(self, endpoint: str, params: dict) -> str:
        """Generate cache key for an API call."""
        key = f"{endpoint}|{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def get(self, endpoint: str, params: dict) -> dict | None:
        """Get cached API response."""
        path = self.cache_dir / f"{self._key(endpoint, params)}.json"
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return None

    def set(self, endpoint: str, params: dict, data: dict):
        """Cache an API response."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        path = self.cache_dir / f"{self._key(endpoint, params)}.json"
        with open(path, "w") as f:
            json.dump(data, f)


class GitHubClient:
    """GitHub API client using gh CLI with caching and rate limiting."""

    def __init__(self, cache_dir: Path | None = None):
        self.cache = Cache(cache_dir or DEFAULT_CACHE_DIR)
        self.rate_limiter = RateLimiter()

    def api(
        self,
        endpoint: str,
        params: dict | None = None,
        use_cache: bool = True,
    ) -> dict:
        """Make a GitHub API call with caching and rate limiting."""
        params = params or {}

        # Check cache first
        if use_cache:
            cached = self.cache.get(endpoint, params)
            if cached is not None:
                return cached

        # Build URL with params
        if params:
            query_string = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{endpoint}?{query_string}"
        else:
            url = endpoint

        while True:
            self.rate_limiter.wait_if_needed()

            result = subprocess.run(
                ["gh", "api", url, "--include"],
                capture_output=True,
                text=True,
            )

            self.rate_limiter.record_request()

            if result.returncode != 0:
                stderr = result.stderr.lower()
                if "rate limit" in stderr or "403" in stderr or "secondary rate limit" in stderr:
                    # Log the specific error for debugging
                    print(f"[RATE LIMIT] {result.stderr.strip()}")
                    self.rate_limiter.remaining = 0
                    self.rate_limiter.force_wait()
                    continue
                elif "422" in result.stderr:
                    # Hit pagination limit
                    return {"total_count": 0, "items": []}
                else:
                    print(f"API error: {result.stderr.strip()}, retrying...")
                    time.sleep(5)
                    continue

            # Parse response (--include adds headers before body)
            parts = result.stdout.split("\n\n", 1)
            headers = parts[0] if parts else ""
            body = parts[1] if len(parts) > 1 else "{}"

            self.rate_limiter.update_from_headers(headers)

            data = json.loads(body)

            if use_cache:
                self.cache.set(endpoint, params, data)

            return data

    def search_code(
        self,
        query: str,
        per_page: int = 100,
        page: int = 1,
    ) -> dict:
        """Search code on GitHub."""
        return self.api(
            "search/code",
            params={"q": query, "per_page": per_page, "page": page},
        )

    def get_file_content(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: str | None = None,
    ) -> dict:
        """Get file content from a repository."""
        endpoint = f"repos/{owner}/{repo}/contents/{path}"
        params = {"ref": ref} if ref else {}
        return self.api(endpoint, params=params)


# Default client instance
_client: GitHubClient | None = None


def get_client(cache_dir: Path | None = None) -> GitHubClient:
    """Get or create the default GitHub client."""
    global _client
    if _client is None or (cache_dir and _client.cache.cache_dir != cache_dir):
        _client = GitHubClient(cache_dir)
    return _client
