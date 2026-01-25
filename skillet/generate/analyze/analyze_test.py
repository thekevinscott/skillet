"""Tests for analyze_skill function."""

from pathlib import Path
from textwrap import dedent

from .analyze import SkillAnalysis, analyze_skill


def describe_analyze_skill():
    """Tests for analyze_skill function."""

    def it_returns_skill_analysis_object(tmp_path: Path):
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("# Simple Skill")

        result = analyze_skill(skill_file)

        assert isinstance(result, SkillAnalysis)
        assert result.path == skill_file

    def it_extracts_name_from_frontmatter(tmp_path: Path):
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            dedent("""\
            ---
            name: my-skill
            description: A test skill
            ---
            # Body
            """)
        )

        result = analyze_skill(skill_file)

        assert result.name == "my-skill"
        assert result.description == "A test skill"

    def it_extracts_goals(tmp_path: Path):
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            dedent("""\
            ---
            name: skill
            ---
            ## Goals

            1. First goal
            2. Second goal
            """)
        )

        result = analyze_skill(skill_file)

        assert result.goals == ["First goal", "Second goal"]

    def it_extracts_prohibitions(tmp_path: Path):
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            dedent("""\
            ## Prohibitions

            - Don't do bad things
            - Avoid mistakes
            """)
        )

        result = analyze_skill(skill_file)

        assert result.prohibitions == ["Don't do bad things", "Avoid mistakes"]

    def it_extracts_code_examples(tmp_path: Path):
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            dedent("""\
            ## Examples

            ```python
            print("hello")
            ```
            """)
        )

        result = analyze_skill(skill_file)

        assert len(result.examples) == 1
        assert 'print("hello")' in result.examples[0]

    def it_handles_skill_without_frontmatter(tmp_path: Path):
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            dedent("""\
            # Just a heading

            ## Goals

            1. Do something
            """)
        )

        result = analyze_skill(skill_file)

        assert result.name is None
        assert result.frontmatter == {}
        assert result.goals == ["Do something"]

    def it_stores_body_content(tmp_path: Path):
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            dedent("""\
            ---
            name: test
            ---
            # Body Content

            This is the body.
            """)
        )

        result = analyze_skill(skill_file)

        assert "# Body Content" in result.body
        assert "This is the body." in result.body


def describe_skill_analysis():
    """Tests for SkillAnalysis dataclass."""

    def it_has_default_values():
        analysis = SkillAnalysis(path=Path("/test"))

        assert analysis.name is None
        assert analysis.goals == []
        assert analysis.prohibitions == []
        assert analysis.examples == []
        assert analysis.frontmatter == {}
        assert analysis.body == ""
