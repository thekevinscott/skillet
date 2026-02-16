"""Tests for status symbol constants."""

from .status_symbols import CACHED, FAIL, PASS, PENDING, RUNNING


def describe_status_symbols():
    """Tests for status symbol constants."""

    def it_has_all_status_symbols():
        assert PENDING is not None
        assert CACHED is not None
        assert RUNNING is not None
        assert PASS is not None
        assert FAIL is not None

    def it_uses_rich_markup():
        assert "[" in PENDING and "]" in PENDING
        assert "[green]" in PASS
        assert "[red]" in FAIL
