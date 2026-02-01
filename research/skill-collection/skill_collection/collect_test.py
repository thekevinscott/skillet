"""Unit tests for collection logic."""

from unittest.mock import MagicMock, patch

import pytest

from . import (
    ShardResult,
    SizeRange,
    collect_shard,
    deduplicate_items,
    extract_file_info,
    needs_subdivision,
    write_progress_md,
)
from .github import parse_github_url


def describe_SizeRange():
    def describe_width():
        def it_returns_difference_for_bounded_range():
            r = SizeRange(100, 199)
            assert r.width == 99

        def it_returns_min_bytes_for_unbounded_range():
            r = SizeRange(50000, None)
            assert r.width == 50000

    def describe_to_query_param():
        def it_formats_bounded_range():
            r = SizeRange(100, 199)
            assert r.to_query_param() == "size:100..199"

        def it_formats_unbounded_range():
            r = SizeRange(50000, None)
            assert r.to_query_param() == "size:>=50000"

    def describe_str():
        def it_formats_bounded_range():
            r = SizeRange(100, 199)
            assert str(r) == "100-199"

        def it_formats_unbounded_range():
            r = SizeRange(50000, None)
            assert str(r) == ">50000"


def describe_SizeRange_subdivide():
    def it_splits_bounded_range_in_half():
        r = SizeRange(200, 299)
        first_half, next_range = r.subdivide()

        assert first_half.min_bytes == 200
        assert first_half.max_bytes == 249
        assert next_range.min_bytes == 250

    def it_handles_odd_width():
        r = SizeRange(0, 100)  # width 101
        first_half, next_range = r.subdivide()

        assert first_half.min_bytes == 0
        assert first_half.max_bytes == 50
        assert next_range.min_bytes == 51

    def it_handles_unbounded_range():
        r = SizeRange(100000, None)
        first_half, next_range = r.subdivide()

        assert first_half.min_bytes == 100000
        assert first_half.max_bytes == 199999
        assert next_range.min_bytes == 200000
        assert next_range.max_bytes is None

    def it_uses_chunk_size_for_next_range():
        original = SizeRange(200, 299)
        first_half, next_range = original.subdivide()

        # First half is 200-249
        assert first_half == SizeRange(200, 249)
        # Next range is 250-349 (100 bytes using DEFAULT_CHUNK_SIZE)
        assert next_range == SizeRange(250, 349)

    def it_allows_custom_chunk_size():
        original = SizeRange(200, 299)
        first_half, next_range = original.subdivide(chunk_size=50)

        assert first_half == SizeRange(200, 249)
        # Next range uses custom chunk_size=50 (covers 50 bytes: 250-299)
        assert next_range == SizeRange(250, 299)

    def it_maintains_chunk_size_after_multiple_subdivisions():
        # Start with a narrow range (like one that was already subdivided)
        narrow_range = SizeRange(0, 49)  # width=49, already subdivided from 0-99
        first_half, next_range = narrow_range.subdivide()

        # First half is 0-24
        assert first_half == SizeRange(0, 24)
        # Next range should use chunk_size=100, NOT the narrow width=49
        # This ensures consistent 100-byte chunks after subdivision
        assert next_range == SizeRange(25, 124)  # 100 bytes starting at 25
        assert next_range.width == 99  # 100 bytes = width of 99


def describe_extract_file_info():
    def it_extracts_relevant_fields():
        item = {
            "name": "SKILL.md",
            "path": "docs/SKILL.md",
            "sha": "abc123",
            "html_url": "https://github.com/user/repo/blob/main/docs/SKILL.md",
            "repository": {
                "full_name": "user/repo",
                "html_url": "https://github.com/user/repo",
                "description": "A cool project",
            },
            "extra_field": "ignored",
        }

        result = extract_file_info(item)

        assert result["name"] == "SKILL.md"
        assert result["path"] == "docs/SKILL.md"
        assert result["sha"] == "abc123"
        assert result["html_url"] == "https://github.com/user/repo/blob/main/docs/SKILL.md"
        assert result["repository"]["full_name"] == "user/repo"
        assert "extra_field" not in result

    def it_handles_missing_fields():
        item = {"name": "SKILL.md"}

        result = extract_file_info(item)

        assert result["name"] == "SKILL.md"
        assert result["path"] is None
        assert result["sha"] is None


def describe_write_progress_md():
    @pytest.fixture
    def output_dir(tmp_path):
        return tmp_path

    def it_writes_markdown_table_with_page_columns(output_dir):
        results = [
            ShardResult(
                SizeRange(0, 99),
                total_count=416,
                collected=416,
                pages={1: 100, 2: 100, 3: 100, 4: 100, 5: 16},
            ),
            ShardResult(
                SizeRange(100, 199),
                total_count=312,
                collected=312,
                pages={1: 100, 2: 100, 3: 100, 4: 12},
            ),
        ]

        write_progress_md(output_dir, results)

        content = (output_dir / "progress.md").read_text()
        assert "**Total collected:** 728 / 113,066" in content
        # Format: Range (width) | total_count | #
        assert "| 0-99 (99) | 416 | 416 |" in content
        assert "| 100-199 (99) | 312 | 312 |" in content

    def it_sorts_results_by_range_descending(output_dir):
        # Results collected out of order (due to subdivision)
        results = [
            ShardResult(SizeRange(0, 99), total_count=100, collected=100, pages={1: 100}),
            ShardResult(SizeRange(500, 599), total_count=50, collected=50, pages={1: 50}),
            ShardResult(SizeRange(200, 299), total_count=75, collected=75, pages={1: 75}),
        ]

        write_progress_md(output_dir, results)

        content = (output_dir / "progress.md").read_text()
        # Should be sorted: 500-599, 200-299, 0-99 (largest to smallest)
        assert content.index("500-599") < content.index("200-299") < content.index("0-99")

    def it_handles_empty_pages(output_dir):
        results = [
            ShardResult(SizeRange(0, 99), total_count=0, collected=0, pages={}),
        ]

        write_progress_md(output_dir, results)

        content = (output_dir / "progress.md").read_text()
        # Format: Range (width) | total_count | #
        assert "| 0-99 (99) | 0 | 0 |" in content

    def it_includes_in_progress_shard_with_arrow(output_dir):
        results = [
            ShardResult(
                SizeRange(0, 99),
                total_count=416,
                collected=416,
                pages={1: 100, 2: 100, 3: 100, 4: 100, 5: 16},
            )
        ]
        in_progress = {"range": "100-199", "collected": 200, "pages": {1: 100, 2: 100}}

        write_progress_md(output_dir, results, in_progress)

        content = (output_dir / "progress.md").read_text()
        # In-progress rows are bold with arrow (total_count=0 since not set, #=200)
        assert "| **-> 100-199 (99)** | 0 | 200 |" in content


def describe_collect_shard():
    @pytest.fixture
    def mock_client():
        with patch("skill_collection.collect.get_client") as mock_get:
            client = MagicMock()
            mock_get.return_value = client
            yield client

    def it_returns_shard_result_and_items(mock_client):
        mock_client.search_code.side_effect = [
            {"total_count": 250, "items": [{"id": i} for i in range(100)]},
            {"total_count": 250, "items": [{"id": i} for i in range(100, 200)]},
            {"total_count": 250, "items": [{"id": i} for i in range(200, 250)]},
        ]

        result, items = collect_shard(SizeRange(0, 99))

        assert result.total_count == 250
        assert result.collected == 250
        assert len(items) == 250
        assert result.pages == {1: 100, 2: 100, 3: 50}

    def it_stops_at_partial_page(mock_client):
        mock_client.search_code.side_effect = [
            {"total_count": 50, "items": [{"id": i} for i in range(50)]},
        ]

        result, items = collect_shard(SizeRange(0, 99))

        assert len(items) == 50
        assert result.pages == {1: 50}
        assert mock_client.search_code.call_count == 1

    def it_stops_early_when_total_count_exceeds_1000(mock_client):
        # total_count > 1000 triggers early exit after page 1
        mock_client.search_code.return_value = {
            "total_count": 2000,
            "items": [{"id": i} for i in range(100)],
        }

        result, items = collect_shard(SizeRange(0, 99))

        # Should stop after page 1 since total_count > 1000
        assert len(items) == 100
        assert len(result.pages) == 1
        assert mock_client.search_code.call_count == 1
        assert result.total_count == 2000

    def it_stops_at_page_10_when_under_limit(mock_client):
        # total_count exactly 1000 - fetch all pages
        mock_client.search_code.return_value = {
            "total_count": 1000,
            "items": [{"id": i} for i in range(100)],
        }

        result, items = collect_shard(SizeRange(0, 99))

        assert len(items) == 1000
        assert len(result.pages) == 10
        assert mock_client.search_code.call_count == 10

    def it_calls_on_page_callback(mock_client):
        mock_client.search_code.side_effect = [
            {"total_count": 150, "items": [{"id": i} for i in range(100)]},
            {"total_count": 150, "items": [{"id": i} for i in range(100, 150)]},
        ]
        callback = MagicMock()

        collect_shard(SizeRange(0, 99), on_page=callback)

        assert callback.call_count == 2
        # Callback receives (page_num, count, total_count)
        callback.assert_any_call(1, 100, 150)
        callback.assert_any_call(2, 50, 150)

    def it_handles_empty_first_page(mock_client):
        mock_client.search_code.return_value = {"total_count": 0, "items": []}

        result, items = collect_shard(SizeRange(0, 99))

        assert result.total_count == 0
        assert len(items) == 0
        assert result.pages == {}


def describe_needs_subdivision():
    def it_returns_true_when_total_count_exceeds_1000():
        result = ShardResult(
            range=SizeRange(0, 99),
            total_count=1500,
            collected=100,  # Only fetched page 1 before early exit
            pages={1: 100},
        )
        assert needs_subdivision(result) is True

    def it_returns_false_when_total_count_at_or_below_1000():
        result = ShardResult(
            range=SizeRange(0, 99),
            total_count=500,
            collected=500,
            pages={},
        )
        assert needs_subdivision(result) is False

    def it_returns_false_when_total_count_exactly_1000():
        result = ShardResult(
            range=SizeRange(0, 99),
            total_count=1000,
            collected=1000,
            pages={},
        )
        assert needs_subdivision(result) is False


def describe_deduplicate_items():
    def it_removes_duplicates_by_sha():
        items = [
            {"sha": "abc", "name": "first"},
            {"sha": "def", "name": "second"},
            {"sha": "abc", "name": "duplicate"},
        ]

        result, seen = deduplicate_items(items)

        assert len(result) == 2
        shas = [item["sha"] for item in result]
        assert "abc" in shas
        assert "def" in shas
        assert seen == {"abc", "def"}

    def it_skips_items_without_sha():
        items = [
            {"sha": "abc", "name": "first"},
            {"name": "no sha"},
            {"sha": None, "name": "null sha"},
        ]

        result, seen = deduplicate_items(items)

        assert len(result) == 1
        assert result[0]["sha"] == "abc"

    def it_extracts_file_info():
        items = [
            {
                "sha": "abc",
                "name": "SKILL.md",
                "path": "docs/SKILL.md",
                "html_url": "https://github.com/user/repo/blob/main/docs/SKILL.md",
                "repository": {
                    "full_name": "user/repo",
                    "html_url": "https://github.com/user/repo",
                    "description": "A project",
                },
                "extra": "ignored",
            }
        ]

        result, _ = deduplicate_items(items)

        assert result[0]["name"] == "SKILL.md"
        assert result[0]["path"] == "docs/SKILL.md"
        assert "extra" not in result[0]

    def it_supports_incremental_deduplication():
        # First batch
        batch1 = [{"sha": "abc", "name": "first"}]
        result1, seen = deduplicate_items(batch1)
        assert len(result1) == 1

        # Second batch with overlapping SHA
        batch2 = [{"sha": "abc", "name": "dupe"}, {"sha": "def", "name": "new"}]
        result2, seen = deduplicate_items(batch2, seen)

        # Only the new item should be added
        assert len(result2) == 1
        assert result2[0]["sha"] == "def"
        assert seen == {"abc", "def"}


def describe_parse_github_url():
    def it_parses_valid_blob_url():
        url = "https://github.com/owner/repo/blob/abc123/path/to/file.md"
        result = parse_github_url(url)

        assert result == ("owner", "repo", "abc123", "path/to/file.md")

    def it_returns_none_for_non_github_url():
        assert parse_github_url("https://gitlab.com/owner/repo/blob/main/file.md") is None

    def it_returns_none_for_non_blob_url():
        assert parse_github_url("https://github.com/owner/repo/tree/main/path") is None
