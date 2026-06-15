"""Tests for the skill models."""

from skillet.skill.models import SkillContent


def describe_skill_content():
    def it_holds_markdown_content():
        skill = SkillContent(content="# SKILL\n\nbody")
        assert skill.content == "# SKILL\n\nbody"

    def it_round_trips_through_validation():
        skill = SkillContent.model_validate({"content": "x"})
        assert skill.model_dump() == {"content": "x"}
