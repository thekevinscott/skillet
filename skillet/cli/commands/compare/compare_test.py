"""Tests for cli/commands/compare module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from skillet.cli.commands.compare import compare_command, format_delta


def describe_format_delta():
    """Tests for format_delta function."""

    @pytest.mark.parametrize(
        "baseline,skill,expected",
        [
            (None, 80.0, "-"),
            (80.0, None, "-"),
            (None, None, "-"),
        ],
    )
    def it_returns_dash_for_missing_values(baseline, skill, expected):
        assert format_delta(baseline, skill) == expected

    def it_returns_positive_delta_in_green():
        result = format_delta(50.0, 80.0)
        assert "[green]" in result
        assert "+30%" in result

    def it_returns_negative_delta_in_red():
        result = format_delta(80.0, 50.0)
        assert "[red]" in result
        assert "-30%" in result

    def it_returns_zero_for_no_change():
        result = format_delta(75.0, 75.0)
        assert result == "0%"


def describe_compare_command():
    """Tests for compare_command function."""

    def it_prints_comparison_table(capsys):
        mock_result = {
            "name": "test-evals",
            "results": [
                {"source": "001.yaml", "baseline": 80.0, "skill": 90.0},
                {"source": "002.yaml", "baseline": 60.0, "skill": 70.0},
            ],
            "overall_baseline": 70.0,
            "overall_skill": 80.0,
            "missing_baseline": [],
            "missing_skill": [],
        }

        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch("skillet.cli.commands.compare.compare.compare", return_value=mock_result),
        ):
            skill_path = Path(tmpdir)
            compare_command("test-evals", skill_path)

            captured = capsys.readouterr()
            assert "test-evals" in captured.out
            assert "001.yaml" in captured.out
            assert "002.yaml" in captured.out
            assert "Overall" in captured.out

    def it_warns_about_missing_baseline(capsys):
        mock_result = {
            "name": "test-evals",
            "results": [{"source": "001.yaml", "baseline": None, "skill": 90.0}],
            "overall_baseline": None,
            "overall_skill": 90.0,
            "missing_baseline": ["001.yaml"],
            "missing_skill": [],
        }

        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch("skillet.cli.commands.compare.compare.compare", return_value=mock_result),
        ):
            skill_path = Path(tmpdir)
            compare_command("test-evals", skill_path)

            captured = capsys.readouterr()
            assert "Warning" in captured.out
            assert "baseline" in captured.out.lower()
            assert "skillet eval" in captured.out

    def it_warns_about_missing_skill(capsys):
        mock_result = {
            "name": "test-evals",
            "results": [{"source": "001.yaml", "baseline": 80.0, "skill": None}],
            "overall_baseline": 80.0,
            "overall_skill": None,
            "missing_baseline": [],
            "missing_skill": ["001.yaml"],
        }

        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch("skillet.cli.commands.compare.compare.compare", return_value=mock_result),
        ):
            skill_path = Path(tmpdir)
            compare_command("test-evals", skill_path)

            captured = capsys.readouterr()
            assert "Warning" in captured.out
            assert "skill" in captured.out.lower()
