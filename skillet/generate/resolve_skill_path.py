"""Resolve skill paths to SKILL.md files."""

from pathlib import Path

from skillet.errors import SkillError


def resolve_skill_path(skill_path: Path) -> Path:
    """Resolve skill path to the SKILL.md file."""
    skill_path = Path(skill_path).expanduser().resolve()

    if not skill_path.exists():
        raise SkillError(f"Skill path does not exist: {skill_path}")

    if skill_path.is_file():
        if skill_path.name != "SKILL.md":
            raise SkillError(f"Expected SKILL.md file, got: {skill_path.name}")
        return skill_path

    # It's a directory - look for SKILL.md
    skill_file = skill_path / "SKILL.md"
    if not skill_file.exists():
        raise SkillError(f"SKILL.md not found in directory: {skill_path}")

    return skill_file
