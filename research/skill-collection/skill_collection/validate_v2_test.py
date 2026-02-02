"""Tests for validate_v2.py."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from .db import get_db_context, init_db
from .validate_v2 import (
    build_validation_prompt,
    get_unvalidated_content,
    run_validation,
    store_validation,
    validate_skill,
)


def describe_get_unvalidated_content():
    def it_returns_content_without_validation(tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        with get_db_context(db_path) as conn:
            conn.execute("INSERT INTO skills (sha, url) VALUES ('sha1', 'url1')")
            conn.execute("INSERT INTO skills (sha, url) VALUES ('sha2', 'url2')")
            conn.execute("INSERT INTO content (sha, body, byte_size) VALUES ('sha1', 'body1', 5)")
            conn.execute("INSERT INTO content (sha, body, byte_size) VALUES ('sha2', 'body2', 5)")
            # sha1 has validation, sha2 does not
            conn.execute(
                "INSERT INTO validations (sha, is_valid, reason) VALUES ('sha1', 1, 'valid')"
            )

        result = get_unvalidated_content(db_path)

        assert len(result) == 1
        sha, url, body = result[0]
        assert sha == "sha2"
        assert body == "body2"

    def it_only_returns_skills_with_content(tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        with get_db_context(db_path) as conn:
            conn.execute("INSERT INTO skills (sha, url) VALUES ('sha1', 'url1')")
            conn.execute("INSERT INTO skills (sha, url) VALUES ('sha2', 'url2')")
            # Only sha1 has content
            conn.execute("INSERT INTO content (sha, body, byte_size) VALUES ('sha1', 'body1', 5)")

        result = get_unvalidated_content(db_path)

        assert len(result) == 1
        sha, _, _ = result[0]
        assert sha == "sha1"

    def it_respects_limit(tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        with get_db_context(db_path) as conn:
            for i in range(10):
                conn.execute(f"INSERT INTO skills (sha, url) VALUES ('sha{i}', 'url{i}')")
                conn.execute(
                    f"INSERT INTO content (sha, body, byte_size) VALUES ('sha{i}', 'body{i}', 5)"
                )

        result = get_unvalidated_content(db_path, limit=3)

        assert len(result) == 3


def describe_store_validation():
    def it_stores_validation_result(tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        with get_db_context(db_path) as conn:
            conn.execute("INSERT INTO skills (sha, url) VALUES ('sha1', 'url1')")

        store_validation("sha1", True, "valid skill", db_path=db_path)

        with get_db_context(db_path) as conn:
            row = conn.execute("SELECT * FROM validations WHERE sha = 'sha1'").fetchone()
            assert row["is_valid"] == 1
            assert row["reason"] == "valid skill"
            assert row["model_version"] is not None
            assert row["validated_at"] is not None


def describe_build_validation_prompt():
    def it_includes_content():
        content = "# My Skill\n\nDo something cool"
        prompt = build_validation_prompt(content)

        assert content in prompt
        assert "is_skill_file" in prompt

    def it_truncates_long_content():
        content = "x" * 20000
        prompt = build_validation_prompt(content)

        assert len(prompt) < 15000
        assert "[truncated]" in prompt


def describe_validate_skill():
    @pytest.fixture
    def mock_query_json():
        with patch("skill_collection.validate_v2.query_json", new_callable=AsyncMock) as mock:
            yield mock

    @pytest.mark.asyncio
    async def it_validates_valid_skill(mock_query_json, tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        with get_db_context(db_path) as conn:
            conn.execute("INSERT INTO skills (sha, url) VALUES ('sha1', 'url1')")

        mock_query_json.return_value = ({"is_skill_file": True, "reason": "valid"}, False)

        is_valid, from_cache, had_error = await validate_skill(
            "sha1",
            "https://github.com/owner/repo/blob/main/SKILL.md",
            "# My Skill",
            db_path=db_path,
        )

        assert is_valid is True
        assert had_error is False

        with get_db_context(db_path) as conn:
            row = conn.execute("SELECT * FROM validations WHERE sha = 'sha1'").fetchone()
            assert row["is_valid"] == 1

    @pytest.mark.asyncio
    async def it_handles_empty_content(mock_query_json, tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        with get_db_context(db_path) as conn:
            conn.execute("INSERT INTO skills (sha, url) VALUES ('sha1', 'url1')")

        is_valid, from_cache, had_error = await validate_skill(
            "sha1",
            "https://github.com/owner/repo/blob/main/SKILL.md",
            "   ",  # Empty content
            db_path=db_path,
        )

        assert is_valid is False
        assert had_error is False
        mock_query_json.assert_not_called()

    @pytest.mark.asyncio
    async def it_handles_symlinks(mock_query_json, tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        with get_db_context(db_path) as conn:
            conn.execute("INSERT INTO skills (sha, url) VALUES ('sha1', 'url1')")

        is_valid, from_cache, had_error = await validate_skill(
            "sha1",
            "https://github.com/owner/repo/blob/main/SKILL.md",
            "../other/SKILL.md",  # Symlink content
            db_path=db_path,
        )

        assert is_valid is False
        assert had_error is False
        mock_query_json.assert_not_called()

        with get_db_context(db_path) as conn:
            row = conn.execute("SELECT * FROM validations WHERE sha = 'sha1'").fetchone()
            assert "symlink" in row["reason"]

    @pytest.mark.asyncio
    async def it_handles_validation_errors(mock_query_json, tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        with get_db_context(db_path) as conn:
            conn.execute("INSERT INTO skills (sha, url) VALUES ('sha1', 'url1')")

        mock_query_json.return_value = (None, False)  # Error case

        is_valid, from_cache, had_error = await validate_skill(
            "sha1",
            "https://github.com/owner/repo/blob/main/SKILL.md",
            "# Some content",
            db_path=db_path,
        )

        assert is_valid is False
        assert had_error is True


def describe_run_validation():
    @pytest.fixture
    def mock_query_json():
        with patch("skill_collection.validate_v2.query_json", new_callable=AsyncMock) as mock:
            yield mock

    @pytest.mark.asyncio
    async def it_validates_all_unvalidated_content(mock_query_json, tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        with get_db_context(db_path) as conn:
            for i in range(3):
                conn.execute(
                    "INSERT INTO skills (sha, url) VALUES (?, ?)",
                    (f"sha{i}", f"https://github.com/owner/repo/blob/main/SKILL{i}.md"),
                )
                conn.execute(
                    "INSERT INTO content (sha, body, byte_size) VALUES (?, ?, ?)",
                    (f"sha{i}", f"# Skill {i}", 10),
                )

        mock_query_json.return_value = ({"is_skill_file": True, "reason": "valid"}, False)

        stats = await run_validation(db_path, concurrency=1)

        assert stats["total"] == 3
        assert stats["valid"] == 3

    @pytest.mark.asyncio
    async def it_returns_zero_stats_when_nothing_to_validate(mock_query_json, tmp_path: Path):
        db_path = tmp_path / "test.db"
        init_db(db_path)

        stats = await run_validation(db_path)

        assert stats["total"] == 0
        assert stats["valid"] == 0
        mock_query_json.assert_not_called()
