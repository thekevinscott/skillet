"""Tests for sanitize_filename module."""

import pytest

from .sanitize_filename import get_name_part


def describe_get_name_part():
    @pytest.mark.parametrize(
        ("name", "index", "expected"),
        [
            ("positive-goal1", 0, "positive-goal1"),
            ("simple name", 0, "simple-name"),
            ("path/to:file.yaml", 0, "path-to-file-yaml"),
            ("a---b", 0, "a-b"),
            ("--leading-trailing--", 0, "leading-trailing"),
            ("///", 0, "candidate-1"),
            ("...", 2, "candidate-3"),
            ("", 0, "candidate-1"),
            ("", 4, "candidate-5"),
            ("under_score", 0, "under_score"),
        ],
        ids=[
            "valid-passthrough",
            "spaces-become-hyphens",
            "slashes-colons-dots-become-hyphens",
            "consecutive-hyphens-collapse",
            "leading-trailing-hyphens-stripped",
            "all-invalid-fallback",
            "all-dots-fallback-with-index",
            "empty-string-fallback",
            "empty-string-fallback-nonzero-index",
            "underscores-preserved",
        ],
    )
    def it_sanitizes(name: str, index: int, expected: str):
        assert get_name_part(name, index) == expected
