"""Tests for the Agent enum."""

from skillet.agent import Agent


def describe_agent():
    """Tests for the Agent enum."""

    def it_has_claude_and_codex_members():
        assert {a.value for a in Agent} == {"claude", "codex"}

    def it_is_a_string_enum():
        # StrEnum members compare equal to their string value
        assert Agent.CLAUDE == "claude"
        assert Agent.CODEX == "codex"

    def it_round_trips_from_value():
        assert Agent("claude") is Agent.CLAUDE
        assert Agent("codex") is Agent.CODEX
