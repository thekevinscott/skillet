"""Resolve skill paths to skill files."""

from pathlib import Path

from skillet.errors import SkillError


def resolve_skill_path(skill_path: Path) -> Path:
    """Resolve a skill path to a concrete file.

    Files are accepted as-is. Directories are resolved to SKILL.md by convention.
    """
    skill_path = Path(skill_path).expanduser().resolve()

    if not skill_path.exists():
        raise SkillError(f"Skill path does not exist: {skill_path}")

    if skill_path.is_file():
        return skill_path

    # It's a directory - look for SKILL.md
    skill_file = skill_path / "SKILL.md"
    if not skill_file.exists():
        raise SkillError(f"SKILL.md not found in directory: {skill_path}")

    return skill_file
