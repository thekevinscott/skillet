"""Unit tests for GitHub client."""

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from .github import GitHubClient


def describe_GitHubClient():
    @pytest.fixture
    def client(tmp_path: Path):
        return GitHubClient(cache_dir=tmp_path / ".cache")

    def describe_cache():
        def it_returns_none_on_cache_miss(client: GitHubClient):
            result = client._get_cached("search/code", {"q": "test"})
            assert result is None

        def it_caches_and_retrieves(client: GitHubClient):
            endpoint = "search/code"
            params = {"q": "test", "page": 1}
            data = {"total_count": 5, "items": [{"id": 1}]}

            client._set_cached(endpoint, params, data)
            result = client._get_cached(endpoint, params)

            assert result == data

        def it_creates_cache_dir_if_missing(client: GitHubClient):
            assert not client.cache_dir.exists()

            client._set_cached("test", {}, {"data": 1})

            assert client.cache_dir.exists()

        def it_generates_different_keys_for_different_params(client: GitHubClient):
            key1 = client._cache_key("search/code", {"q": "foo"})
            key2 = client._cache_key("search/code", {"q": "bar"})

            assert key1 != key2

        def it_generates_same_key_regardless_of_param_order(client: GitHubClient):
            key1 = client._cache_key("search/code", {"a": 1, "b": 2})
            key2 = client._cache_key("search/code", {"b": 2, "a": 1})

            assert key1 == key2

    def describe_rate_limiting():
        def it_initializes_with_conservative_limit(client: GitHubClient):
            # Start under the 10/min limit to avoid hitting it
            assert client.remaining == 8

        def it_updates_from_headers(client: GitHubClient):
            headers = "X-RateLimit-Remaining: 15\nX-RateLimit-Reset: 1234567890"

            client._update_rate_limit(headers)

            assert client.remaining == 15
            assert client.reset_time == 1234567890

        def it_handles_case_insensitive_headers(client: GitHubClient):
            headers = "x-ratelimit-remaining: 10\nx-ratelimit-reset: 9999"

            client._update_rate_limit(headers)

            assert client.remaining == 10

        def it_does_not_wait_when_remaining_above_threshold(client: GitHubClient):
            client.remaining = 10
            # Set last_request_time far in the past to avoid throttle wait
            client.rate_limiter.last_request_time = 0

            with patch("time.sleep") as mock_sleep:
                client._wait_if_needed()
                mock_sleep.assert_not_called()

        def it_waits_when_remaining_is_zero(client: GitHubClient):
            client.remaining = 0
            client.reset_time = int(time.time()) + 10  # 10 seconds in future

            with patch("time.sleep") as mock_sleep:
                client._wait_if_needed()
                mock_sleep.assert_called_once()

        def it_prints_status_when_waiting(client: GitHubClient):
            client.remaining = 0
            client.reset_time = int(time.time()) + 10

            with patch("time.sleep"), patch("builtins.print") as mock_print:
                client._wait_if_needed()
                mock_print.assert_called_once()

    def describe_api():
        @pytest.fixture
        def mock_subprocess(client: GitHubClient):
            with patch("subprocess.run") as mock:
                mock.return_value = MagicMock(
                    returncode=0,
                    stdout='X-RateLimit-Remaining: 29\n\n{"total_count": 10, "items": []}',
                    stderr="",
                )
                yield mock

        def it_returns_cached_result_without_api_call(
            client: GitHubClient, mock_subprocess: MagicMock
        ):
            # Pre-populate cache
            client._set_cached("search/code", {"q": "test"}, {"cached": True})

            result = client.api("search/code", {"q": "test"})

            assert result == {"cached": True}
            mock_subprocess.assert_not_called()

        def it_makes_api_call_on_cache_miss(
            client: GitHubClient, mock_subprocess: MagicMock
        ):
            result = client.api("search/code", {"q": "test"})

            assert result == {"total_count": 10, "items": []}
            mock_subprocess.assert_called_once()

        def it_caches_successful_response(
            client: GitHubClient, mock_subprocess: MagicMock
        ):
            client.api("search/code", {"q": "new_query"})

            # Should be cached now
            cached = client._get_cached("search/code", {"q": "new_query"})
            assert cached == {"total_count": 10, "items": []}

        def it_skips_cache_when_disabled(
            client: GitHubClient, mock_subprocess: MagicMock
        ):
            # Pre-populate cache
            client._set_cached("search/code", {"q": "test"}, {"cached": True})

            result = client.api("search/code", {"q": "test"}, use_cache=False)

            assert result == {"total_count": 10, "items": []}
            mock_subprocess.assert_called_once()

    def describe_search_code():
        def it_builds_correct_params(client: GitHubClient):
            with patch.object(client, "api", return_value={}) as mock_api:
                client.search_code("filename:test", per_page=50, page=2)

                mock_api.assert_called_once_with(
                    "search/code",
                    params={"q": "filename:test", "per_page": 50, "page": 2},
                )

    def describe_get_file_content():
        def it_builds_correct_endpoint(client: GitHubClient):
            with patch.object(client, "api", return_value={}) as mock_api:
                client.get_file_content("owner", "repo", "path/to/file.md")

                mock_api.assert_called_once_with(
                    "repos/owner/repo/contents/path/to/file.md",
                    params={},
                )

        def it_includes_ref_when_provided(client: GitHubClient):
            with patch.object(client, "api", return_value={}) as mock_api:
                client.get_file_content("owner", "repo", "file.md", ref="main")

                mock_api.assert_called_once_with(
                    "repos/owner/repo/contents/file.md",
                    params={"ref": "main"},
                )

    def describe_api_error_handling():
        @pytest.fixture
        def mock_subprocess(client: GitHubClient):
            with patch("subprocess.run") as mock:
                yield mock

        def it_retries_on_rate_limit_error(client: GitHubClient, mock_subprocess: MagicMock):
            # First call fails with rate limit, second succeeds
            mock_subprocess.side_effect = [
                MagicMock(returncode=1, stderr="rate limit exceeded", stdout=""),
                MagicMock(
                    returncode=0,
                    stdout='X-RateLimit-Remaining: 29\nX-RateLimit-Reset: 0\n\n{"data": "ok"}',
                    stderr="",
                ),
            ]
            client.remaining = 0
            client.reset_time = 0

            with patch("time.sleep"):
                result = client.api("test", use_cache=False)

            assert result == {"data": "ok"}
            assert mock_subprocess.call_count == 2

        def it_returns_empty_on_422_error(client: GitHubClient, mock_subprocess: MagicMock):
            mock_subprocess.return_value = MagicMock(
                returncode=1, stderr="422 Unprocessable Entity", stdout=""
            )

            result = client.api("search/code", {"q": "test"}, use_cache=False)

            assert result == {"total_count": 0, "items": []}

        def it_retries_on_other_errors(client: GitHubClient, mock_subprocess: MagicMock):
            mock_subprocess.side_effect = [
                MagicMock(returncode=1, stderr="Connection timeout", stdout=""),
                MagicMock(
                    returncode=0,
                    stdout='X-RateLimit-Remaining: 29\n\n{"data": "ok"}',
                    stderr="",
                ),
            ]
            # Disable throttle waiting by setting last_request_time far in the past
            client.rate_limiter.last_request_time = 0

            with patch("time.sleep") as mock_sleep:
                result = client.api("test", use_cache=False)

            # Should have one call for the retry wait (5s)
            assert any(call[0] == (5,) for call in mock_sleep.call_args_list)
            assert result == {"data": "ok"}
