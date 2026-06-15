"""End-to-end guards asserting removed CLI commands no longer exist.

The `compare` and `show` commands were removed as part of the cachetta
cache consolidation (they were the only consumers of cache enumeration).
These guards prove the commands are gone from the CLI surface: invoking
them errors with an "Unknown command" message instead of running.
"""

from collections.abc import Callable

import pytest
from curtaincall import Terminal, expect

SKILLET = "skillet"


def describe_removed_commands():
    """Tests that removed CLI commands report as unknown."""

    @pytest.mark.parametrize("command", ["compare", "show"])
    def it_no_longer_exists(terminal: Callable[..., Terminal], command: str):
        """Removed commands exit non-zero with an 'Unknown command' error."""
        term = terminal(f"{SKILLET} {command} some-eval some-skill")
        expect(term).to_have_exited()
        assert term.exit_code != 0
        expect(term.get_by_text("Unknown command")).to_be_visible()
