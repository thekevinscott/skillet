"""Tests for collect_v2.py."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from .collect_v2 import (
    build_query,
    collect_shard_v2,
    get_next_shard,
    init_collection,
    mark_shard_complete,
    mark_shard_started,
    record_results,
    run_collection,
    subdivide_shard,
)
from .db import get_db_context, init_db
from .models import SizeRange


def describe_build_query():
    def it_builds_basic_query():
        size_range = SizeRange(100, 199)
        query = build_query(size_range)
        assert query == "filename:SKILL.md+size:100..199"

    def it_builds_query_with_date_range():
        from datetime import datetime

        size_range = SizeRange(100, 199)
        start = datetime(2024, 1, 1)
        end = datetime(2024, 6, 30)
        query = build_query(size_range, start, end)
        assert query == "filename:SKILL.md+size:100..199+created:2024-01-01..2024-06-30"

    def it_handles_unbounded_range():
        size_range = SizeRange(100000, None)
        query = build_query(size_range)
        assert query == "filename:SKILL.md+size:>=100000"


def describe_init_collection():
    def it_creates_shards_for_all_size_ranges(tmp_path: Path):
        db_path = tmp_path / "test.db"
        count = init_collection(db_path)

        assert count > 0

        with get_db_context(db_path) as conn:
            row = conn.execute("SELECT COUNT(*) as count FROM shards").fetchone()
            assert row["count"] == count

    def it_is_idempotent(tmp_path: Path):
        db_path = tmp_path / "test.db"
        first_count = init_collection(db_path)
        second_count = init_collection(db_path)

        assert second_count == 0

        with get_db_context(db_path) as conn:
            row = conn.execute("SELECT COUNT(*) as count FROM shards").fetchone()
            assert row["count"] == first_count


def describe_get_next_shard():
    def it_returns_first_incomplete_shard(tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        with get_db_context(db_path) as conn:
            conn.execute("INSERT INTO shards (query) VALUES ('q1')")
            conn.execute("INSERT INTO shards (query) VALUES ('q2')")

        result = get_next_shard(db_path)

        assert result is not None
        shard_id, query = result
        assert query == "q1"

    def it_skips_completed_shards(tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        with get_db_context(db_path) as conn:
            conn.execute(
                "INSERT INTO shards (query, completed_at) VALUES ('q1', CURRENT_TIMESTAMP)"
            )
            conn.execute("INSERT INTO shards (query) VALUES ('q2')")

        result = get_next_shard(db_path)

        assert result is not None
        _, query = result
        assert query == "q2"

    def it_returns_none_when_all_complete(tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        with get_db_context(db_path) as conn:
            conn.execute(
                "INSERT INTO shards (query, completed_at) VALUES ('q1', CURRENT_TIMESTAMP)"
            )

        result = get_next_shard(db_path)
        assert result is None


def describe_mark_shard_started():
    def it_sets_started_at_timestamp(tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        with get_db_context(db_path) as conn:
            conn.execute("INSERT INTO shards (query) VALUES ('q1')")

        mark_shard_started(1, db_path)

        with get_db_context(db_path) as conn:
            row = conn.execute("SELECT started_at FROM shards WHERE id = 1").fetchone()
            assert row["started_at"] is not None


def describe_mark_shard_complete():
    def it_sets_completion_fields(tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        with get_db_context(db_path) as conn:
            conn.execute("INSERT INTO shards (query) VALUES ('q1')")

        mark_shard_complete(1, total_count=500, collected=500, db_path=db_path)

        with get_db_context(db_path) as conn:
            row = conn.execute("SELECT * FROM shards WHERE id = 1").fetchone()
            assert row["total_count"] == 500
            assert row["collected"] == 500
            assert row["completed_at"] is not None


def describe_subdivide_shard():
    def it_creates_two_new_shards_from_size_range(tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        with get_db_context(db_path) as conn:
            conn.execute("INSERT INTO shards (query) VALUES ('filename:SKILL.md+size:0..99')")

        new_queries = subdivide_shard(1, "filename:SKILL.md+size:0..99", db_path)

        assert len(new_queries) == 2
        # First half should be smaller range
        assert "size:0.." in new_queries[0]
        # Second half should be after midpoint
        assert "size:" in new_queries[1]

        # Old shard should be deleted
        with get_db_context(db_path) as conn:
            row = conn.execute("SELECT COUNT(*) as count FROM shards WHERE id = 1").fetchone()
            assert row["count"] == 0

            # New shards should exist
            row = conn.execute("SELECT COUNT(*) as count FROM shards").fetchone()
            assert row["count"] == 2

    def it_preserves_date_constraint_when_subdividing_by_size(tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        query = "filename:SKILL.md+size:0..99+created:2024-01-01..2024-06-30"
        with get_db_context(db_path) as conn:
            conn.execute("INSERT INTO shards (query) VALUES (?)", (query,))

        new_queries = subdivide_shard(1, query, db_path)

        # Both new queries should preserve the date constraint
        for q in new_queries:
            assert "created:2024-01-01..2024-06-30" in q


def describe_record_results():
    def it_inserts_new_skills(tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        with get_db_context(db_path) as conn:
            conn.execute("INSERT INTO shards (query) VALUES ('q1')")

        items = [
            {"sha": "sha1", "html_url": "url1"},
            {"sha": "sha2", "html_url": "url2"},
        ]

        inserted = record_results(1, items, db_path)

        assert inserted == 2

        with get_db_context(db_path) as conn:
            row = conn.execute("SELECT COUNT(*) as count FROM skills").fetchone()
            assert row["count"] == 2

    def it_ignores_duplicates(tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        with get_db_context(db_path) as conn:
            conn.execute("INSERT INTO shards (query) VALUES ('q1')")
            conn.execute("INSERT INTO skills (sha, url) VALUES ('sha1', 'url1')")

        items = [
            {"sha": "sha1", "html_url": "url_new"},  # Duplicate SHA
            {"sha": "sha2", "html_url": "url2"},  # New
        ]

        inserted = record_results(1, items, db_path)

        assert inserted == 1  # Only sha2 should be inserted


def describe_collect_shard_v2():
    @pytest.fixture
    def mock_client():
        with patch("skill_collection.collect_v2.get_client") as mock:
            client = MagicMock()
            mock.return_value = client
            yield client

    def it_collects_all_pages_under_limit(mock_client, tmp_path: Path):
        mock_client.search_code.side_effect = [
            {"total_count": 150, "items": [{"sha": f"sha{i}"} for i in range(100)]},
            {"total_count": 150, "items": [{"sha": f"sha{i}"} for i in range(100, 150)]},
        ]

        total, collected, items = collect_shard_v2(1, "test_query")

        assert total == 150
        assert collected == 150
        assert len(items) == 150

    def it_stops_early_when_over_limit(mock_client, tmp_path: Path):
        mock_client.search_code.return_value = {
            "total_count": 1500,  # Over 1000 limit
            "items": [{"sha": f"sha{i}"} for i in range(100)],
        }

        total, collected, items = collect_shard_v2(1, "test_query")

        assert total == 1500
        assert collected == 100  # Stopped after first page
        assert len(items) == 100


def describe_run_collection():
    @pytest.fixture
    def mock_client():
        with patch("skill_collection.collect_v2.get_client") as mock:
            client = MagicMock()
            mock.return_value = client
            yield client

    def it_processes_all_shards(mock_client, tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        # Add two simple shards
        with get_db_context(db_path) as conn:
            conn.execute("INSERT INTO shards (query) VALUES ('filename:SKILL.md+size:0..99')")
            conn.execute("INSERT INTO shards (query) VALUES ('filename:SKILL.md+size:100..199')")

        # Each shard returns 50 results
        mock_client.search_code.return_value = {
            "total_count": 50,
            "items": [{"sha": f"sha{i}", "html_url": f"url{i}"} for i in range(50)],
        }

        stats = run_collection(db_path)

        assert stats["shards_processed"] == 2
        # First shard gets all 50, second shard duplicates are ignored
        # (since we use same sha values in mock)
        assert stats["skills_collected"] == 100
        assert stats["skills_new"] == 50  # Duplicates filtered

    def it_subdivides_large_shards(mock_client, tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        with get_db_context(db_path) as conn:
            conn.execute("INSERT INTO shards (query) VALUES ('filename:SKILL.md+size:0..99')")

        # First call: over limit, triggers subdivision
        # Subsequent calls: under limit
        call_count = [0]
        def search_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return {
                    "total_count": 1500,
                    "items": [{"sha": f"sha{i}", "html_url": f"url{i}"} for i in range(100)],
                }
            return {
                "total_count": 50,
                "items": [{"sha": f"sha{call_count[0]}_{i}", "html_url": f"url{call_count[0]}_{i}"} for i in range(50)],
            }

        mock_client.search_code.side_effect = search_side_effect

        stats = run_collection(db_path)

        assert stats["shards_subdivided"] >= 1
