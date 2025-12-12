"""Create a new skill from gaps."""

from pathlib import Path

from skillet.errors import SkillError
from skillet.gaps import load_gaps

from .draft import draft_skill


async def create_skill(
    name: str,
    output_dir: Path,
    extra_prompt: str | None = None,
    overwrite: bool = False,
) -> dict:
    """Create a new skill from captured gaps.

    Args:
        name: Skill name (gaps loaded from ~/.skillet/gaps/<name>/)
        output_dir: Where to create the skill directory
        extra_prompt: Additional instructions for generating the SKILL.md
        overwrite: Whether to overwrite existing skill

    Returns:
        dict with skill_dir, skill_content, and gap_count

    Raises:
        SkillError: If no gaps found or skill exists and overwrite=False
    """
    gaps = load_gaps(name)

    if not gaps:
        raise SkillError(f"No gap files found for '{name}'")

    skill_dir = output_dir / name

    if skill_dir.exists() and not overwrite:
        raise SkillError(f"Skill already exists at {skill_dir}")

    if skill_dir.exists():
        import shutil

        shutil.rmtree(skill_dir)

    # Generate SKILL.md content
    skill_content = await draft_skill(name, gaps, extra_prompt)

    # Create directory and write SKILL.md
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(skill_content + "\n")

    return {
        "skill_dir": skill_dir,
        "skill_content": skill_content,
        "gap_count": len(gaps),
    }
