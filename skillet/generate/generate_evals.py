"""Generate candidate evals from SKILL.md files."""

from pathlib import Path

from .analyze import analyze_skill
from .generate import generate_candidates
from .resolve_skill_path import resolve_skill_path
from .types import GenerateResult
from .write import write_candidates


async def generate_evals(
    skill_path: Path,
    *,
    output_dir: Path | None = None,
    use_lint: bool = True,
    max_per_category: int = 5,
) -> GenerateResult:
    """Generate candidate eval files from a SKILL.md.

    Analyzes the skill to extract goals, prohibitions, and examples,
    then uses an LLM to generate test cases for each. Optionally
    incorporates lint findings to target weak spots.
    """
    # Resolve path to SKILL.md
    skill_file = resolve_skill_path(skill_path)

    # Analyze the skill
    analysis = analyze_skill(skill_file)

    # Generate candidates
    candidates = await generate_candidates(
        analysis,
        use_lint=use_lint,
        max_per_category=max_per_category,
    )

    # Build result
    result = GenerateResult(
        skill_path=skill_file,
        candidates=candidates,
        analysis={
            "name": analysis.name,
            "description": analysis.description,
            "goals": analysis.goals,
            "prohibitions": analysis.prohibitions,
            "example_count": len(analysis.examples),
        },
    )

    # Write candidates if output_dir specified
    if output_dir is not None:
        write_candidates(candidates, output_dir, skill_name=analysis.name)

    return result
