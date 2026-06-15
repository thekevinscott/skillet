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

    def it_exposes_the_per_agent_config_dot_dir():
        # The dot-dir is where each CLI auto-discovers skills and reads config:
        # claude -> .claude/skills, codex -> .codex/skills.
        assert Agent.CLAUDE.dot_dir == ".claude"
        assert Agent.CODEX.dot_dir == ".codex"
