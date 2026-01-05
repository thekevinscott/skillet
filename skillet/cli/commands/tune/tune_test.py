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

    @pytest.fixture(autouse=True)
    def mock_console():
        """Mock console."""
        with patch("skillet.cli.commands.tune.tune.console") as mock:
            yield mock

    @pytest.fixture(autouse=True)
    def mock_load_evals():
        """Mock load_evals."""
        with patch("skillet.cli.commands.tune.tune.load_evals") as mock:
            mock.return_value = [{"_source": "test.yaml"}]
            yield mock

    @pytest.fixture(autouse=True)
    def mock_live_display():
        """Mock LiveDisplay."""
        with patch("skillet.cli.commands.tune.tune.LiveDisplay") as mock_cls:
            mock_display = MagicMock()
            mock_display.start = AsyncMock()
            mock_display.stop = AsyncMock()
            mock_display.update = AsyncMock()
            mock_cls.return_value = mock_display
            yield mock_display

    @pytest.fixture
    def mock_tune_result():
        """Create a mock TuneResult."""
        result = MagicMock()
        result.save = MagicMock()
        return result

    @pytest.fixture(autouse=True)
    def mock_tune(mock_tune_result):
        """Mock tune function."""
        with patch("skillet.cli.commands.tune.tune.tune") as mock:
            mock.return_value = mock_tune_result
            yield mock

    @pytest.fixture(autouse=True)
    def mock_get_rate_color():
        """Mock get_rate_color."""
        with patch("skillet.cli.commands.tune.tune.get_rate_color") as mock:
            mock.return_value = "yellow"
            yield mock

    @pytest.fixture(autouse=True)
    def mock_print_result():
        """Mock print_tune_result."""
        with patch("skillet.cli.commands.tune.tune.print_tune_result") as mock:
            yield mock

    @pytest.fixture(autouse=True)
    def mock_get_output_path():
        """Mock get_default_output_path."""
        with patch("skillet.cli.commands.tune.tune.get_default_output_path") as mock:
            mock.return_value = Path("/tmp/output.json")
            yield mock

    @pytest.mark.asyncio
    async def it_loads_evals_by_name(mock_load_evals):
        """Loads evals using the provided name."""
        await tune_command("my-evals", Path("/path/to/skill.md"))
        mock_load_evals.assert_called_once_with("my-evals")

    @pytest.mark.asyncio
    async def it_runs_tune_with_correct_params(mock_tune):
        """Passes parameters to tune function."""
        await tune_command(
            "my-evals",
            Path("/path/to/skill.md"),
            max_rounds=10,
            target_pass_rate=90.0,
            samples=3,
            parallel=5,
        )
        mock_tune.assert_called_once()
        call_args = mock_tune.call_args
        assert call_args[0][0] == "my-evals"
        assert call_args[0][1] == Path("/path/to/skill.md")
        # Config is passed as a dataclass
        config = call_args[1]["config"]
        assert config.max_rounds == 10
        assert config.target_pass_rate == 90.0
        assert config.samples == 3
        assert config.parallel == 5
        # Callbacks are passed as a dataclass
        assert "callbacks" in call_args[1]

    @pytest.mark.asyncio
    async def it_calls_print_tune_result(mock_print_result, mock_tune_result):
        """Calls print_tune_result with the result."""
        await tune_command("my-evals", Path("/path/to/skill.md"))
        mock_print_result.assert_called_once_with(mock_tune_result)

    @pytest.mark.asyncio
    async def it_saves_result_to_output_path(mock_tune_result):
        """Saves result to the output path."""
        await tune_command("my-evals", Path("/path/to/skill.md"))
        mock_tune_result.save.assert_called_once_with(Path("/tmp/output.json"))

    @pytest.mark.asyncio
    async def it_uses_custom_output_path(mock_tune_result):
        """Uses custom output path when provided."""
        custom_path = Path("/custom/output.json")
        await tune_command("my-evals", Path("/path/to/skill.md"), output_path=custom_path)
        mock_tune_result.save.assert_called_once_with(custom_path)

    @pytest.mark.asyncio
    async def it_mocks_get_rate_color(mock_get_rate_color):
        """get_rate_color is mocked in tests."""
        mock_get_rate_color.return_value = "red"
        await tune_command("my-evals", Path("/path/to/skill.md"))
        assert mock_get_rate_color.return_value == "red"

    @pytest.mark.asyncio
    async def it_returns_tune_result(mock_tune_result):
        """Returns the TuneResult from tune function."""
        result = await tune_command("my-evals", Path("/path/to/skill.md"))
        assert result == mock_tune_result
