"""Tests for prompt_for_script_confirmation function."""

from unittest.mock import patch

import pytest

from skillet.cli.commands.eval.prompt_for_script_confirmation import (
    prompt_for_script_confirmation,
)


def describe_prompt_for_script_confirmation():
    """Tests for prompt_for_script_confirmation function."""

    @pytest.fixture
    def mock_console():
        """Mock the console for testing."""
        with patch("skillet.cli.commands.eval.prompt_for_script_confirmation.console") as mock:
            yield mock

    def it_returns_true_when_user_confirms_with_y(mock_console):
        """User typing 'y' returns True."""
        mock_console.input.return_value = "y"
        scripts = [("001.yaml", "setup", "mkdir -p /tmp/test")]
        result = prompt_for_script_confirmation(scripts)
        assert result is True

    def it_returns_true_when_user_confirms_with_yes(mock_console):
        """User typing 'yes' returns True."""
        mock_console.input.return_value = "yes"
        scripts = [("001.yaml", "setup", "mkdir -p /tmp/test")]
        result = prompt_for_script_confirmation(scripts)
        assert result is True

    def it_returns_true_when_user_confirms_with_uppercase_y(mock_console):
        """User typing 'Y' returns True."""
        mock_console.input.return_value = "Y"
        scripts = [("001.yaml", "setup", "mkdir -p /tmp/test")]
        result = prompt_for_script_confirmation(scripts)
        assert result is True

    def it_returns_false_when_user_denies_with_n(mock_console):
        """User typing 'n' returns False."""
        mock_console.input.return_value = "n"
        scripts = [("001.yaml", "setup", "mkdir -p /tmp/test")]
        result = prompt_for_script_confirmation(scripts)
        assert result is False

    def it_returns_false_when_user_presses_enter(mock_console):
        """User pressing enter (empty input) returns False."""
        mock_console.input.return_value = ""
        scripts = [("001.yaml", "setup", "mkdir -p /tmp/test")]
        result = prompt_for_script_confirmation(scripts)
        assert result is False

    def it_returns_false_on_keyboard_interrupt(mock_console):
        """Ctrl+C returns False."""
        mock_console.input.side_effect = KeyboardInterrupt
        scripts = [("001.yaml", "setup", "mkdir -p /tmp/test")]
        result = prompt_for_script_confirmation(scripts)
        assert result is False

    def it_returns_false_on_eof(mock_console):
        """EOF returns False."""
        mock_console.input.side_effect = EOFError
        scripts = [("001.yaml", "setup", "mkdir -p /tmp/test")]
        result = prompt_for_script_confirmation(scripts)
        assert result is False

    def it_displays_security_warning(mock_console):
        """Security warning is displayed."""
        mock_console.input.return_value = "n"
        scripts = [("001.yaml", "setup", "mkdir -p /tmp/test")]
        prompt_for_script_confirmation(scripts)
        # Check that security warning was printed
        calls = [str(call) for call in mock_console.print.call_args_list]
        assert any("Security Warning" in call for call in calls)

    def it_displays_script_count(mock_console):
        """Number of scripts is displayed."""
        mock_console.input.return_value = "n"
        scripts = [
            ("001.yaml", "setup", "echo 1"),
            ("002.yaml", "teardown", "echo 2"),
        ]
        prompt_for_script_confirmation(scripts)
        calls = [str(call) for call in mock_console.print.call_args_list]
        assert any("2" in call for call in calls)

    def it_truncates_long_script_lines(mock_console):
        """Long script lines are truncated to 60 chars."""
        mock_console.input.return_value = "n"
        long_script = "x" * 100
        scripts = [("001.yaml", "setup", long_script)]
        prompt_for_script_confirmation(scripts)
        calls = [str(call) for call in mock_console.print.call_args_list]
        # Should contain truncated version with "..."
        assert any("..." in call for call in calls)
        # Should not contain the full 100 char string
        assert not any(long_script in call for call in calls)

    def it_shows_trust_flag_hint(mock_console):
        """Hint about --trust flag is displayed."""
        mock_console.input.return_value = "n"
        scripts = [("001.yaml", "setup", "echo test")]
        prompt_for_script_confirmation(scripts)
        calls = [str(call) for call in mock_console.print.call_args_list]
        assert any("--trust" in call for call in calls)
