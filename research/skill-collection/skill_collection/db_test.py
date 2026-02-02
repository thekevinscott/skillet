"""Tests for db.py."""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from .db import get_db, get_db_context, get_stats, init_db


def describe_init_db():
    def it_creates_database_file(tmp_path: Path):
        db_path = tmp_path / "test.db"
        result = init_db(db_path)

        assert result == db_path
        assert db_path.exists()

    def it_creates_all_tables(tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        assert "shards" in tables
        assert "skills" in tables
        assert "content" in tables
        assert "validations" in tables

    def it_is_idempotent(tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)
        init_db(db_path)  # Should not raise

        conn = sqlite3.connect(db_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        assert "shards" in tables

    def it_creates_parent_directories(tmp_path: Path):
        db_path = tmp_path / "nested" / "dir" / "test.db"
        init_db(db_path)

        assert db_path.exists()


def describe_get_db():
    def it_returns_connection_with_row_factory(tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        conn = get_db(db_path)
        conn.execute("INSERT INTO shards (query) VALUES ('test')")
        row = conn.execute("SELECT * FROM shards WHERE query = 'test'").fetchone()

        assert row["query"] == "test"
        conn.close()

    def it_enables_foreign_keys(tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        conn = get_db(db_path)
        result = conn.execute("PRAGMA foreign_keys").fetchone()
        assert result[0] == 1
        conn.close()


def describe_get_db_context():
    def it_commits_on_success(tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        with get_db_context(db_path) as conn:
            conn.execute("INSERT INTO shards (query) VALUES ('test')")

        # Verify data persisted
        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT * FROM shards WHERE query = 'test'").fetchone()
        assert row is not None
        conn.close()

    def it_rolls_back_on_error(tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        with pytest.raises(ValueError):
            with get_db_context(db_path) as conn:
                conn.execute("INSERT INTO shards (query) VALUES ('test')")
                raise ValueError("Test error")

        # Verify data was not persisted
        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT * FROM shards WHERE query = 'test'").fetchone()
        assert row is None
        conn.close()


def describe_get_stats():
    def it_returns_zero_counts_for_empty_db(tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        stats = get_stats(db_path)

        assert stats["shards_total"] == 0
        assert stats["shards_completed"] == 0
        assert stats["skills_total"] == 0
        assert stats["content_fetched"] == 0
        assert stats["validations_total"] == 0
        assert stats["validations_valid"] == 0

    def it_counts_records_correctly(tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        with get_db_context(db_path) as conn:
            # Add shards (1 completed, 1 pending)
            conn.execute(
                "INSERT INTO shards (query, completed_at) VALUES ('q1', CURRENT_TIMESTAMP)"
            )
            conn.execute("INSERT INTO shards (query) VALUES ('q2')")

            # Add skills
            conn.execute("INSERT INTO skills (sha, url, shard_id) VALUES ('sha1', 'url1', 1)")
            conn.execute("INSERT INTO skills (sha, url, shard_id) VALUES ('sha2', 'url2', 1)")

            # Add content for one skill
            conn.execute("INSERT INTO content (sha, body, byte_size) VALUES ('sha1', 'body', 4)")

            # Add validations (1 valid, 1 invalid)
            conn.execute(
                "INSERT INTO validations (sha, is_valid, reason) VALUES ('sha1', 1, 'valid')"
            )
            conn.execute(
                "INSERT INTO validations (sha, is_valid, reason) VALUES ('sha2', 0, 'invalid')"
            )

        stats = get_stats(db_path)

        assert stats["shards_total"] == 2
        assert stats["shards_completed"] == 1
        assert stats["skills_total"] == 2
        assert stats["content_fetched"] == 1
        assert stats["validations_total"] == 2
        assert stats["validations_valid"] == 1


def describe_schema():
    def it_enforces_unique_query_constraint(tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        with get_db_context(db_path) as conn:
            conn.execute("INSERT INTO shards (query) VALUES ('test')")
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute("INSERT INTO shards (query) VALUES ('test')")

    def it_enforces_unique_sha_constraint(tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        with get_db_context(db_path) as conn:
            conn.execute("INSERT INTO skills (sha, url) VALUES ('sha1', 'url1')")
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute("INSERT INTO skills (sha, url) VALUES ('sha1', 'url2')")
