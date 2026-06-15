"""Tests for tune output path generation."""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from skillet.cli.commands.tune.output_path import get_default_output_path

_MODULE = "skillet.cli.commands.tune.output_path"


def describe_get_default_output_path():
    @pytest.fixture(autouse=True)
    def mock_datetime():
        with patch(f"{_MODULE}.datetime") as mock:
            mock.now.return_value = datetime(2026, 6, 15, 12, 30, 45)
            yield mock

    def it_builds_a_timestamped_json_path_under_home():
        result = get_default_output_path("my-eval")
        assert result == Path.home() / ".skillet" / "tunes" / "my-eval" / "20260615-123045.json"

    def it_extracts_the_eval_name_from_a_path():
        result = get_default_output_path("evals/my-eval.yaml")
        expected = Path.home() / ".skillet" / "tunes" / "my-eval.yaml" / "20260615-123045.json"
        assert result == expected
