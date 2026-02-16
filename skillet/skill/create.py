"""Create a new skill from evals."""

from pathlib import Path

from skillet.errors import SkillError
from skillet.evals import load_evals

from .draft import draft_skill
from .result import CreateSkillResult


async def create_skill(
    name: str,
    output_dir: Path,
    extra_prompt: str | None = None,
    overwrite: bool = False,
) -> CreateSkillResult:
    """Create a new skill from captured evals.

    Raises:
        SkillError: If no evals found or skill exists and overwrite=False
    """
    evals = load_evals(name)

    if not evals:
        raise SkillError(f"No eval files found for '{name}'")

    skill_dir = output_dir / name

    if skill_dir.exists() and not overwrite:
        raise SkillError(f"Skill already exists at {skill_dir}")

    if skill_dir.exists():
        import shutil

        shutil.rmtree(skill_dir)

    # Generate SKILL.md content
    skill_content = await draft_skill(name, evals, extra_prompt)

    # Create directory and write SKILL.md
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(skill_content + "\n")

    return CreateSkillResult(
        skill_dir=skill_dir,
        skill_content=skill_content,
        eval_count=len(evals),
    )
