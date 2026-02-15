"""Get the skill file path, handling both directory and file inputs."""

from pathlib import Path


def get_skill_file(skill_path: Path) -> Path:
    """Get the skill file path, handling both directory and file inputs."""
    if skill_path.is_file():
        return skill_path
    return skill_path / "SKILL.md"
