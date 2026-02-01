"""Unit tests for utils module."""

from pathlib import Path

from skill_collection.utils import (
    escape_html,
    escape_table_cell,
    resolve_content_path,
    truncate_for_analysis,
    truncate_text,
    truncate_url,
)


def describe_truncate_url():
    def it_returns_short_urls_unchanged():
        url = "https://github.com/user/repo"
        assert truncate_url(url) == "user/repo"

    def it_truncates_long_urls():
        url = "https://github.com/user/very-long-repo-name/blob/main/path/to/some/file.md"
        result = truncate_url(url, max_len=30)
        assert len(result) <= 30
        assert "..." in result

    def it_strips_github_prefix():
        url = "https://github.com/user/repo/blob/main/file.md"
        result = truncate_url(url)
        assert not result.startswith("https://github.com/")


def describe_truncate_text():
    def it_returns_short_text_unchanged():
        assert truncate_text("short text") == "short text"

    def it_truncates_at_word_boundary():
        text = "word1 word2 word3 word4 word5"
        result = truncate_text(text, max_len=15)
        assert result.endswith("...")
        assert len(result) <= 15

    def it_handles_text_without_spaces():
        text = "a" * 200
        result = truncate_text(text, max_len=50)
        assert len(result) <= 50
        assert result.endswith("...")

    def it_handles_empty_string():
        assert truncate_text("") == ""


def describe_escape_html():
    def it_escapes_ampersand():
        assert escape_html("foo & bar") == "foo &amp; bar"

    def it_escapes_angle_brackets():
        assert escape_html("<script>") == "&lt;script&gt;"

    def it_escapes_quotes():
        assert escape_html('"quoted"') == "&quot;quoted&quot;"


def describe_escape_table_cell():
    def it_escapes_pipes():
        assert escape_table_cell("a | b") == "a &#124; b"

    def it_escapes_html_and_pipes():
        assert escape_table_cell("<a> | <b>") == "&lt;a&gt; &#124; &lt;b&gt;"


def describe_truncate_for_analysis():
    def it_returns_short_content_unchanged():
        content = "short"
        assert truncate_for_analysis(content, 100) == content

    def it_truncates_and_adds_marker():
        content = "a" * 200
        result = truncate_for_analysis(content, 50)
        assert len(result) == 50 + len("\n\n[truncated]")
        assert result.endswith("[truncated]")


def describe_resolve_content_path():
    def it_builds_correct_path():
        content_dir = Path("/data/content")
        result = resolve_content_path(content_dir, "owner", "repo", "abc123", "path/file.md")
        assert result == Path("/data/content/owner/repo/blob/abc123/path/file.md")
