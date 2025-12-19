"""Tests for cli/commands/tune module."""

from unittest.mock import patch

from skillet.cli.commands.tune import _get_default_output_path


def describe_get_default_output_path():
    """Tests for _get_default_output_path function."""

    def it_returns_path_in_skillet_tunes():
        result = _get_default_output_path("my-evals")
        assert ".skillet" in str(result)
        assert "tunes" in str(result)
        assert "my-evals" in str(result)
        assert result.suffix == ".json"

    def it_extracts_name_from_unix_path():
        result = _get_default_output_path("/path/to/evals/my-custom-evals")
        assert "my-custom-evals" in str(result)
        assert "/path/to" not in str(result)

    def it_extracts_name_from_windows_path():
        result = _get_default_output_path("C:\\path\\to\\evals\\my-evals")
        assert "my-evals" in str(result)

    def it_uses_simple_name_directly():
        result = _get_default_output_path("browser-fallback")
        assert "browser-fallback" in str(result)

    def it_generates_timestamped_filename():
        with patch("skillet.cli.commands.tune.datetime") as mock_dt:
            mock_dt.now.return_value.strftime.return_value = "20240101-120000"
            result = _get_default_output_path("test")
            assert "20240101-120000.json" in str(result)
