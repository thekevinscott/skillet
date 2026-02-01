"""Unit tests for filter module."""

import pytest

from .filter import (
    ClassificationProgress,
    SkillFileClassifier,
    is_symlink_content,
    resolve_symlink_url,
)


def describe_is_symlink_content():
    def it_returns_true_for_relative_path():
        assert is_symlink_content("../../other/SKILL.md") is True

    def it_returns_true_for_path_with_slash():
        assert is_symlink_content("../shared/skill.md") is True

    def it_returns_false_for_markdown_content():
        assert is_symlink_content("# Title\n\nSome content") is False

    def it_returns_false_for_code_block():
        assert is_symlink_content("```python\nprint('hello')\n```") is False

    def it_returns_false_for_long_content():
        assert is_symlink_content("x" * 201) is False

    def it_returns_false_for_plain_text():
        assert is_symlink_content("just some text without slashes") is False

    def it_returns_false_for_chezmoi_template():
        # Real example from levonk/dotfiles that was incorrectly classified as symlink
        content = '{{ includeTemplate "dot_config/ai/skills/content/youtube/SKILL.md" . }}'
        assert is_symlink_content(content) is False

    def it_returns_false_for_go_template_syntax():
        assert is_symlink_content("{{ .Path }}/file.md") is False


def describe_resolve_symlink_url():
    def it_resolves_parent_directory():
        url = "https://github.com/owner/repo/blob/main/skills/web/SKILL.md"
        target = "../shared/SKILL.md"
        result = resolve_symlink_url(url, target)
        assert result == "https://github.com/owner/repo/blob/main/skills/shared/SKILL.md"

    def it_resolves_multiple_parent_dirs():
        url = "https://github.com/owner/repo/blob/abc123/a/b/c/SKILL.md"
        target = "../../other/SKILL.md"
        result = resolve_symlink_url(url, target)
        assert result == "https://github.com/owner/repo/blob/abc123/a/other/SKILL.md"

    def it_returns_original_for_non_github_url():
        url = "https://gitlab.com/owner/repo/blob/main/SKILL.md"
        result = resolve_symlink_url(url, "../other.md")
        assert result == url


def describe_SkillFileClassifier():
    @pytest.fixture
    def classifier(tmp_path):
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir(parents=True)
        return SkillFileClassifier(
            cache_dir=cache_dir,
            valid_path=tmp_path / "valid.md",
            invalid_path=tmp_path / "invalid.md",
        )

    def describe_formatting():
        def it_formats_row_with_link(classifier):
            row = classifier.format_row(
                "https://github.com/user/repo/blob/main/SKILL.md", False, "Valid"
            )
            assert '<a href="https://github.com/user/repo/blob/main/SKILL.md"' in row
            assert 'target="_blank"' in row
            assert "| Valid |" in row

        def it_shows_symlink_marker(classifier):
            row = classifier.format_row("https://example.com", True, "reason")
            assert "| → |" in row

        def it_escapes_reason_text(classifier):
            row = classifier.format_row("https://example.com", False, "has <tags> & pipes |")
            assert "&lt;tags&gt;" in row
            assert "&amp;" in row
            assert "&#124;" in row


def describe_ClassificationProgress():
    def it_initializes_with_zeros():
        progress = ClassificationProgress()
        assert progress.completed == 0
        assert progress.valid == 0
        assert progress.invalid == 0
        assert progress.errors == 0
        assert progress.cached == 0

    def it_allows_updating_fields():
        progress = ClassificationProgress()
        progress.valid = 5
        progress.completed = 10
        progress.cached = 3
        assert progress.valid == 5
        assert progress.completed == 10
        assert progress.cached == 3
