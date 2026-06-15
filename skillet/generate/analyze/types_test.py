"""Tests for the analyze types."""

from pathlib import Path

from skillet.generate.analyze.types import SkillAnalysis


def describe_skill_analysis():
    def it_defaults_optional_fields():
        analysis = SkillAnalysis(path=Path("SKILL.md"))
        assert analysis.name is None
        assert analysis.description is None
        assert analysis.goals == []
        assert analysis.prohibitions == []
        assert analysis.examples == []
        assert analysis.frontmatter == {}
        assert analysis.body == ""

    def it_uses_independent_default_collections():
        a = SkillAnalysis(path=Path("a.md"))
        b = SkillAnalysis(path=Path("b.md"))
        a.goals.append("ship it")
        a.frontmatter["name"] = "a"
        assert b.goals == []
        assert b.frontmatter == {}

    def it_stores_provided_values():
        analysis = SkillAnalysis(
            path=Path("SKILL.md"),
            name="my-skill",
            goals=["g1"],
            body="# Heading",
        )
        assert analysis.name == "my-skill"
        assert analysis.goals == ["g1"]
        assert analysis.body == "# Heading"
