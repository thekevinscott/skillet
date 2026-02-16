"""Tests for create skill result dataclass."""

from pathlib import Path

from skillet.skill.result import CreateSkillResult


def describe_create_skill_result():
    def it_constructs_with_all_fields():
        r = CreateSkillResult(
            skill_dir=Path("/tmp/my-skill"),
            skill_content="# My Skill",
            eval_count=3,
        )
        assert r.skill_dir == Path("/tmp/my-skill")
        assert r.skill_content == "# My Skill"
        assert r.eval_count == 3

    def it_serializes_with_path_preserved():
        r = CreateSkillResult(
            skill_dir=Path("/tmp/my-skill"),
            skill_content="# Skill",
            eval_count=1,
        )
        d = r.to_dict()
        assert isinstance(d["skill_dir"], Path)
        assert d["skill_content"] == "# Skill"
        assert d["eval_count"] == 1
