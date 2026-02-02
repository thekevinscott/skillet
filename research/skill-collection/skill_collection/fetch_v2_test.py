"""Tests for fetch_v2.py."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from .db import get_db_context, init_db
from .fetch_v2 import (
    fetch_content_from_cache,
    fetch_content_from_url,
    get_unfetched_skills,
    run_fetch,
    store_content,
)


def describe_get_unfetched_skills():
    def it_returns_skills_without_content(tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        with get_db_context(db_path) as conn:
            conn.execute("INSERT INTO skills (sha, url) VALUES ('sha1', 'url1')")
            conn.execute("INSERT INTO skills (sha, url) VALUES ('sha2', 'url2')")
            # sha1 has content, sha2 does not
            conn.execute("INSERT INTO content (sha, body, byte_size) VALUES ('sha1', 'body', 4)")

        result = get_unfetched_skills(db_path)

        assert len(result) == 1
        assert result[0] == ("sha2", "url2")

    def it_respects_limit(tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        with get_db_context(db_path) as conn:
            for i in range(10):
                conn.execute(f"INSERT INTO skills (sha, url) VALUES ('sha{i}', 'url{i}')")

        result = get_unfetched_skills(db_path, limit=3)

        assert len(result) == 3

    def it_returns_empty_list_when_all_fetched(tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        with get_db_context(db_path) as conn:
            conn.execute("INSERT INTO skills (sha, url) VALUES ('sha1', 'url1')")
            conn.execute("INSERT INTO content (sha, body, byte_size) VALUES ('sha1', 'body', 4)")

        result = get_unfetched_skills(db_path)

        assert len(result) == 0


def describe_fetch_content_from_cache():
    def it_returns_content_from_cache(tmp_path: Path):
        content_dir = tmp_path / "content"
        owner, repo, ref, path = "owner", "repo", "main", "SKILL.md"

        # Create cached file
        cache_path = content_dir / owner / repo / "blob" / ref / path
        cache_path.parent.mkdir(parents=True)
        cache_path.write_text("cached content")

        url = f"https://github.com/{owner}/{repo}/blob/{ref}/{path}"
        content, byte_size = fetch_content_from_cache(url, content_dir)

        assert content == "cached content"
        assert byte_size == len("cached content".encode())

    def it_returns_none_when_not_cached(tmp_path: Path):
        content_dir = tmp_path / "content"
        url = "https://github.com/owner/repo/blob/main/SKILL.md"

        content, byte_size = fetch_content_from_cache(url, content_dir)

        assert content is None
        assert byte_size == 0


def describe_fetch_content_from_url():
    @pytest.fixture
    def mock_client():
        with patch("skill_collection.fetch_v2.get_client") as mock:
            client = MagicMock()
            mock.return_value = client
            yield client

    def it_fetches_and_decodes_content(mock_client):
        import base64

        content = "# SKILL.md content"
        encoded = base64.b64encode(content.encode()).decode()
        mock_client.get_file_content.return_value = {"content": encoded}

        url = "https://github.com/owner/repo/blob/main/SKILL.md"
        result_content, byte_size = fetch_content_from_url(url)

        assert result_content == content
        assert byte_size == len(content.encode())

    def it_returns_none_on_error(mock_client):
        mock_client.get_file_content.side_effect = Exception("API error")

        url = "https://github.com/owner/repo/blob/main/SKILL.md"
        content, byte_size = fetch_content_from_url(url)

        assert content is None
        assert byte_size == 0


def describe_store_content():
    def it_stores_content_in_database(tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        with get_db_context(db_path) as conn:
            conn.execute("INSERT INTO skills (sha, url) VALUES ('sha1', 'url1')")

        store_content("sha1", "body content", 12, db_path)

        with get_db_context(db_path) as conn:
            row = conn.execute("SELECT * FROM content WHERE sha = 'sha1'").fetchone()
            assert row["body"] == "body content"
            assert row["byte_size"] == 12
            assert row["fetched_at"] is not None


def describe_run_fetch():
    @pytest.fixture
    def mock_client():
        with patch("skill_collection.fetch_v2.get_client") as mock:
            client = MagicMock()
            mock.return_value = client
            yield client

    def it_fetches_unfetched_skills(mock_client, tmp_path: Path):
        import base64

        db_path = tmp_path / "test.db"
        init_db(db_path)

        with get_db_context(db_path) as conn:
            conn.execute(
                "INSERT INTO skills (sha, url) VALUES (?, ?)",
                ("sha1", "https://github.com/owner/repo/blob/main/SKILL.md"),
            )

        content = "# Content"
        mock_client.get_file_content.return_value = {
            "content": base64.b64encode(content.encode()).decode()
        }

        stats = run_fetch(db_path, concurrency=1)

        assert stats["total"] == 1
        assert stats["fetched"] == 1
        assert stats["errors"] == 0

        # Verify content was stored
        with get_db_context(db_path) as conn:
            row = conn.execute("SELECT * FROM content WHERE sha = 'sha1'").fetchone()
            assert row["body"] == content

    def it_uses_cache_when_available(mock_client, tmp_path: Path):
        db_path = tmp_path / "test.db"
        content_dir = tmp_path / "content"
        init_db(db_path)

        # Create cached file
        cache_path = content_dir / "owner" / "repo" / "blob" / "main" / "SKILL.md"
        cache_path.parent.mkdir(parents=True)
        cache_path.write_text("cached content")

        with get_db_context(db_path) as conn:
            conn.execute(
                "INSERT INTO skills (sha, url) VALUES (?, ?)",
                ("sha1", "https://github.com/owner/repo/blob/main/SKILL.md"),
            )

        stats = run_fetch(db_path, content_dir=content_dir, concurrency=1)

        assert stats["cached"] == 1
        assert stats["fetched"] == 0

        # API should not be called
        mock_client.get_file_content.assert_not_called()

    def it_returns_zero_stats_when_nothing_to_fetch(mock_client, tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        stats = run_fetch(db_path)

        assert stats["total"] == 0
        assert stats["fetched"] == 0
