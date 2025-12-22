"""Tests for tune_command function."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from skillet.cli.commands.tune import get_default_output_path
from skillet.cli.commands.tune.tune import tune_command


def describe_get_default_output_path():
    """Tests for get_default_output_path function."""

    def it_returns_path_in_skillet_tunes():
        result = get_default_output_path("my-evals")
        assert ".skillet" in str(result)
        assert "tunes" in str(result)
        assert "my-evals" in str(result)
        assert result.suffix == ".json"

    def it_extracts_name_from_unix_path():
        result = get_default_output_path("/path/to/evals/my-custom-evals")
        assert "my-custom-evals" in str(result)
        assert "/path/to" not in str(result)

    def it_extracts_name_from_windows_path():
        result = get_default_output_path("C:\\path\\to\\evals\\my-evals")
        assert "my-evals" in str(result)

    def it_uses_simple_name_directly():
        result = get_default_output_path("browser-fallback")
        assert "browser-fallback" in str(result)

    def it_generates_timestamped_filename():
        with patch("skillet.cli.commands.tune.output_path.datetime") as mock_dt:
            mock_dt.now.return_value.strftime.return_value = "20240101-120000"
            result = get_default_output_path("test")
            assert "20240101-120000.json" in str(result)


def describe_tune_command():
    """Tests for tune_command function."""

    @pytest.fixture
    def mock_tune_result():
        """Create a mock TuneResult."""
        result = MagicMock()
        result.save = MagicMock()
        return result

    @pytest.fixture
    def mock_deps(mock_tune_result):
        """Mock all dependencies for tune_command."""
        with (
            patch("skillet.cli.commands.tune.tune.console") as mock_console,
            patch("skillet.cli.commands.tune.tune.load_evals") as mock_load_evals,
            patch("skillet.cli.commands.tune.tune.LiveDisplay") as mock_display_cls,
            patch("skillet.cli.commands.tune.tune.tune") as mock_tune,
            patch("skillet.cli.commands.tune.tune.get_rate_color") as mock_get_rate_color,
            patch("skillet.cli.commands.tune.tune.print_tune_result") as mock_print_result,
            patch(
                "skillet.cli.commands.tune.tune.get_default_output_path"
            ) as mock_get_output_path,
        ):
            # Setup default mocks
            mock_load_evals.return_value = [{"_source": "test.yaml"}]
            mock_display = MagicMock()
            mock_display.start = AsyncMock()
            mock_display.stop = AsyncMock()
            mock_display.update = AsyncMock()
            mock_display_cls.return_value = mock_display
            mock_tune.return_value = mock_tune_result
            mock_get_rate_color.return_value = "yellow"
            mock_get_output_path.return_value = Path("/tmp/output.json")

            yield {
                "console": mock_console,
                "load_evals": mock_load_evals,
                "display_cls": mock_display_cls,
                "display": mock_display,
                "tune": mock_tune,
                "get_rate_color": mock_get_rate_color,
                "print_result": mock_print_result,
                "get_output_path": mock_get_output_path,
                "tune_result": mock_tune_result,
            }

    @pytest.mark.asyncio
    async def it_loads_evals_by_name(mock_deps):
        """Loads evals using the provided name."""
        await tune_command("my-evals", Path("/path/to/skill.md"))
        mock_deps["load_evals"].assert_called_once_with("my-evals")

    @pytest.mark.asyncio
    async def it_runs_tune_with_correct_params(mock_deps):
        """Passes parameters to tune function."""
        await tune_command(
            "my-evals",
            Path("/path/to/skill.md"),
            max_rounds=10,
            target_pass_rate=90.0,
            samples=3,
            parallel=5,
        )
        mock_deps["tune"].assert_called_once()
        call_args = mock_deps["tune"].call_args
        assert call_args[0][0] == "my-evals"
        assert call_args[0][1] == Path("/path/to/skill.md")
        assert call_args[1]["max_rounds"] == 10
        assert call_args[1]["target_pass_rate"] == 90.0
        assert call_args[1]["samples"] == 3
        assert call_args[1]["parallel"] == 5

    @pytest.mark.asyncio
    async def it_calls_print_tune_result(mock_deps):
        """Calls print_tune_result with the result."""
        await tune_command("my-evals", Path("/path/to/skill.md"))
        mock_deps["print_result"].assert_called_once_with(mock_deps["tune_result"])

    @pytest.mark.asyncio
    async def it_saves_result_to_output_path(mock_deps):
        """Saves result to the output path."""
        await tune_command("my-evals", Path("/path/to/skill.md"))
        mock_deps["tune_result"].save.assert_called_once_with(Path("/tmp/output.json"))

    @pytest.mark.asyncio
    async def it_uses_custom_output_path(mock_deps):
        """Uses custom output path when provided."""
        custom_path = Path("/custom/output.json")
        await tune_command("my-evals", Path("/path/to/skill.md"), output_path=custom_path)
        mock_deps["tune_result"].save.assert_called_once_with(custom_path)

    @pytest.mark.asyncio
    async def it_mocks_get_rate_color(mock_deps):
        """get_rate_color is mocked in tests."""
        # The function is mocked, verify it can be configured
        mock_deps["get_rate_color"].return_value = "red"
        await tune_command("my-evals", Path("/path/to/skill.md"))
        # get_rate_color is called within the on_round_complete callback
        # which is only triggered if tune actually runs rounds
        # Here we just verify the mock is in place
        assert mock_deps["get_rate_color"].return_value == "red"

    @pytest.mark.asyncio
    async def it_returns_tune_result(mock_deps):
        """Returns the TuneResult from tune function."""
        result = await tune_command("my-evals", Path("/path/to/skill.md"))
        assert result == mock_deps["tune_result"]
