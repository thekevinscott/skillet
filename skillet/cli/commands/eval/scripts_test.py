"""Tests for script detection and confirmation."""

from unittest.mock import patch

import pytest

from skillet.cli.commands.eval.scripts import (
    get_scripts_from_evals,
    prompt_for_script_confirmation,
)


def describe_get_scripts_from_evals():
    """Tests for get_scripts_from_evals function."""

    def it_returns_empty_list_for_evals_without_scripts():
        """Evals without setup/teardown return empty list."""
        evals = [
            {"_source": "001.yaml", "prompt": "test", "expected": "result"},
            {"_source": "002.yaml", "prompt": "test2", "expected": "result2"},
        ]
        result = get_scripts_from_evals(evals)
        assert result == []

    def it_extracts_setup_scripts():
        """Setup scripts are extracted with source and type."""
        evals = [
            {"_source": "001.yaml", "setup": "mkdir -p /tmp/test"},
        ]
        result = get_scripts_from_evals(evals)
        assert result == [("001.yaml", "setup", "mkdir -p /tmp/test")]

    def it_extracts_teardown_scripts():
        """Teardown scripts are extracted with source and type."""
        evals = [
            {"_source": "001.yaml", "teardown": "rm -rf /tmp/test"},
        ]
        result = get_scripts_from_evals(evals)
        assert result == [("001.yaml", "teardown", "rm -rf /tmp/test")]

    def it_extracts_both_setup_and_teardown():
        """Both setup and teardown are extracted from same eval."""
        evals = [
            {
                "_source": "001.yaml",
                "setup": "mkdir -p /tmp/test",
                "teardown": "rm -rf /tmp/test",
            },
        ]
        result = get_scripts_from_evals(evals)
        assert len(result) == 2
        assert ("001.yaml", "setup", "mkdir -p /tmp/test") in result
        assert ("001.yaml", "teardown", "rm -rf /tmp/test") in result

    def it_extracts_scripts_from_multiple_evals():
        """Scripts from multiple evals are all extracted."""
        evals = [
            {"_source": "001.yaml", "setup": "echo first"},
            {"_source": "002.yaml", "setup": "echo second"},
            {"_source": "003.yaml", "teardown": "echo third"},
        ]
        result = get_scripts_from_evals(evals)
        assert len(result) == 3

    def it_uses_unknown_source_when_missing():
        """Missing _source defaults to 'unknown'."""
        evals = [{"setup": "echo test"}]
        result = get_scripts_from_evals(evals)
        assert result == [("unknown", "setup", "echo test")]


def describe_prompt_for_script_confirmation():
    """Tests for prompt_for_script_confirmation function."""

    @pytest.fixture
    def mock_console():
        """Mock the console for testing."""
        with patch("skillet.cli.commands.eval.scripts.console") as mock:
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
