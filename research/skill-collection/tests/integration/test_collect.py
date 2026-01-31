"""Integration tests for the skill collection script."""

import json
import sys
from unittest.mock import MagicMock, patch

import pytest


def make_gh_response(total_count: int, items: list[dict]) -> str:
    """Create a mock gh CLI response with headers and JSON body."""
    headers = "X-RateLimit-Remaining: 29\nX-RateLimit-Reset: 9999999999"
    body = json.dumps({"total_count": total_count, "items": items})
    return f"{headers}\n\n{body}"


def make_item(sha: str, repo: str = "user/repo", path: str = "SKILL.md") -> dict:
    """Create a mock search result item."""
    return {
        "name": "SKILL.md",
        "path": path,
        "sha": sha,
        "html_url": f"https://github.com/{repo}/blob/main/{path}",
        "repository": {
            "full_name": repo,
            "html_url": f"https://github.com/{repo}",
            "description": "A project",
        },
    }


def describe_main():
    @pytest.fixture
    def output_dir(tmp_path):
        return tmp_path / "output"

    @pytest.fixture(autouse=True)
    def reset_client_and_cache(tmp_path):
        """Reset the global client and use a fresh cache directory."""
        import skill_collection.github as github_module

        github_module._client = None
        # Override the default cache directory
        original_default = github_module.DEFAULT_CACHE_DIR
        github_module.DEFAULT_CACHE_DIR = tmp_path / ".cache"
        yield
        github_module._client = None
        github_module.DEFAULT_CACHE_DIR = original_default

    @pytest.fixture
    def mock_gh_cli():
        """Mock the gh CLI subprocess calls and time.sleep for speed."""
        with (
            patch("subprocess.run") as mock_run,
            patch("time.sleep"),
        ):  # Don't actually sleep in tests
            yield mock_run

    def it_collects_files_and_writes_output(output_dir, mock_gh_cli):
        # Set up mock responses for a small subset of ranges
        items_range_0 = [make_item(f"sha{i}", f"user/repo{i}") for i in range(50)]
        items_range_1 = [make_item(f"sha{i + 50}", f"user/repo{i + 50}") for i in range(30)]

        def mock_subprocess(*args, **kwargs):
            cmd = args[0] if args else kwargs.get("args", [])
            url = cmd[2] if len(cmd) > 2 else ""

            result = MagicMock()
            result.returncode = 0
            result.stderr = ""

            # URL format: search/code?q=filename:SKILL.md+size:0..99&per_page=100&page=1
            if "size%3A0..99" in url or "size:0..99" in url:
                result.stdout = make_gh_response(50, items_range_0)
            elif "size%3A100..199" in url or "size:100..199" in url:
                result.stdout = make_gh_response(30, items_range_1)
            else:
                result.stdout = make_gh_response(0, [])

            return result

        mock_gh_cli.side_effect = mock_subprocess

        # Run main with only ranges 0 and 1
        with patch.object(
            sys,
            "argv",
            ["collect-skills", "--output-dir", str(output_dir), "fetch-files", "--ranges", "0,1"],
        ):
            from skill_collection import main

            main()

        # Verify output files were created
        assert (output_dir / "summary.json").exists()
        assert (output_dir / "skill_files.json").exists()
        assert (output_dir / "progress.md").exists()

        # Verify summary content
        with open(output_dir / "summary.json") as f:
            summary = json.load(f)

        assert summary["total_shards"] == 2
        assert summary["total_collected"] == 80

        # Verify skill files
        with open(output_dir / "skill_files.json") as f:
            files = json.load(f)

        assert len(files) == 80

        # Verify progress.md format
        progress = (output_dir / "progress.md").read_text()
        assert "**Total collected:** 80" in progress
        assert "| 0-99 | 50 |" in progress
        assert "| 100-199 | 30 |" in progress

    def it_handles_subdivision_when_hitting_limit(output_dir, mock_gh_cli):
        """Test that ranges hitting 1000 limit are subdivided and not shown."""
        # We need to return 1000 results across 10 pages to trigger subdivision
        items_page = [make_item(f"sha{i}") for i in range(100)]
        items_first_half = [make_item(f"sha_first_{i}") for i in range(50)]
        items_second_half = [make_item(f"sha_second_{i}") for i in range(50)]

        def mock_subprocess(*args, **kwargs):
            cmd = args[0] if args else kwargs.get("args", [])
            url = cmd[2] if len(cmd) > 2 else ""

            result = MagicMock()
            result.returncode = 0
            result.stderr = ""

            # Original range 0-99: return 100 items per page, total_count > 1000
            if "size%3A0..99" in url or "size:0..99" in url:
                result.stdout = make_gh_response(1500, items_page)
            # First half of subdivision (0-49): return < 1000
            elif "size%3A0..49" in url or "size:0..49" in url:
                result.stdout = make_gh_response(50, items_first_half)
            # Second half (50-149): return < 1000
            elif "size%3A50..149" in url or "size:50..149" in url:
                result.stdout = make_gh_response(50, items_second_half)
            else:
                result.stdout = make_gh_response(0, [])

            return result

        mock_gh_cli.side_effect = mock_subprocess

        with patch.object(
            sys,
            "argv",
            ["collect-skills", "--output-dir", str(output_dir), "fetch-files", "--ranges", "0"],
        ):
            from skill_collection import main

            main()

        # Verify the subdivided ranges appear in output, not the original
        progress = (output_dir / "progress.md").read_text()

        # Original range should NOT appear with 1000 count
        assert "| 0-99 | 1,000 |" not in progress
        assert "| 0-99 | 1000 |" not in progress

        # Subdivided ranges should appear
        assert "0-49" in progress
        assert "50-149" in progress

    def it_runs_in_dry_run_mode(output_dir, mock_gh_cli):
        """Test that dry run mode only counts without collecting."""

        def mock_subprocess(*args, **kwargs):
            result = MagicMock()
            result.returncode = 0
            result.stderr = ""
            result.stdout = make_gh_response(500, [])  # Just return count, no items needed
            return result

        mock_gh_cli.side_effect = mock_subprocess

        with patch.object(
            sys,
            "argv",
            [
                "collect-skills",
                "--output-dir",
                str(output_dir),
                "fetch-files",
                "--ranges",
                "0",
                "--dry-run",
            ],
        ):
            from skill_collection import main

            main()

        # Verify summary exists but skill_files does not
        assert (output_dir / "summary.json").exists()
        assert not (output_dir / "skill_files.json").exists()

        with open(output_dir / "summary.json") as f:
            summary = json.load(f)

        assert summary["total_collected"] == 0


def describe_fetch_content():
    @pytest.fixture
    def output_dir(tmp_path):
        return tmp_path / "output"

    @pytest.fixture(autouse=True)
    def reset_client_and_cache(tmp_path):
        """Reset the global client and use a fresh cache directory."""
        import skill_collection.github as github_module

        github_module._client = None
        original_default = github_module.DEFAULT_CACHE_DIR
        github_module.DEFAULT_CACHE_DIR = tmp_path / ".cache"
        yield
        github_module._client = None
        github_module.DEFAULT_CACHE_DIR = original_default

    @pytest.fixture
    def mock_gh_cli():
        """Mock the gh CLI subprocess calls and time.sleep for speed."""
        with (
            patch("subprocess.run") as mock_run,
            patch("time.sleep"),
        ):
            yield mock_run

    def it_fetches_content_and_stores_on_disk(output_dir, mock_gh_cli):
        import base64

        # Create skill_urls.txt with test URLs
        output_dir.mkdir(parents=True)
        urls_file = output_dir / "skill_urls.txt"
        urls_file.write_text(
            "https://github.com/owner/repo/blob/abc123/SKILL.md\n"
            "https://github.com/other/project/blob/def456/path/SKILL.md\n"
        )

        # Mock API responses for file content
        def mock_subprocess(*args, **kwargs):
            result = MagicMock()
            result.returncode = 0
            result.stderr = ""

            content = base64.b64encode(b"# Test Skill\nDescription here").decode()
            result.stdout = f'X-RateLimit-Remaining: 29\n\n{{"content": "{content}"}}'
            return result

        mock_gh_cli.side_effect = mock_subprocess

        with patch.object(
            sys,
            "argv",
            ["collect-skills", "--output-dir", str(output_dir), "fetch-content"],
        ):
            from skill_collection import main

            main()

        # Verify files were created on disk
        content_dir = output_dir / "content"
        assert (content_dir / "owner/repo/blob/abc123/SKILL.md").exists()
        assert (content_dir / "other/project/blob/def456/path/SKILL.md").exists()

        # Verify content
        content = (content_dir / "owner/repo/blob/abc123/SKILL.md").read_text()
        assert "# Test Skill" in content


def describe_filter_skills():
    @pytest.fixture
    def output_dir(tmp_path):
        return tmp_path / "output"

    def it_reports_which_files_exist_on_disk(output_dir, capsys):
        # Create skill_urls.txt with test URLs
        output_dir.mkdir(parents=True)
        urls_file = output_dir / "skill_urls.txt"
        urls_file.write_text(
            "https://github.com/owner/repo/blob/abc123/SKILL.md\n"
            "https://github.com/missing/repo/blob/def456/SKILL.md\n"
        )

        # Create content for first URL only
        content_dir = output_dir / "content"
        (content_dir / "owner/repo/blob/abc123").mkdir(parents=True)
        (content_dir / "owner/repo/blob/abc123/SKILL.md").write_text("# Skill")

        with patch.object(
            sys,
            "argv",
            ["collect-skills", "--output-dir", str(output_dir), "filter-skills"],
        ):
            from skill_collection import main

            main()

        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")

        assert "owner/repo/blob/abc123/SKILL.md 1" in lines[0]  # exists
        assert "missing/repo/blob/def456/SKILL.md 2" in lines[1]  # missing
