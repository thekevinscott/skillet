"""Tests for _stderr_callback function."""

from skillet._internal.sdk.stderr import _stderr_callback


def describe_stderr_callback():
    def it_prints_to_stderr(capsys):
        _stderr_callback("test message")
        captured = capsys.readouterr()
        assert "test message" in captured.err

    def it_handles_empty_string(capsys):
        _stderr_callback("")
        captured = capsys.readouterr()
        assert captured.err == "\n"
