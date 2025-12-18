"""Run tuning using DSPy optimization."""

from pathlib import Path
from typing import Literal

from skillet.optimize import optimize_skill

from .result import TuneConfig, TuneResult


def get_skill_file(skill_path: Path) -> Path:
    """Get the skill file path, handling both directory and file inputs.

    Args:
        skill_path: Path to skill directory or direct .md file

    Returns:
        Path to the actual skill file
    """
    if skill_path.is_file():
        return skill_path
    return skill_path / "SKILL.md"


def tune(
    name: str,
    skill_path: Path,
    *,
    num_trials: int = 5,
    optimizer: Literal["bootstrap", "mipro"] = "bootstrap",
) -> TuneResult:
    """Tune a skill using DSPy optimization.

    The original skill file is NOT modified. The optimized skill content
    is returned in the TuneResult.

    For small datasets (~10 evals), use BootstrapFewShot (default).
    For larger datasets (200+), use MIPROv2.

    Args:
        name: Name or path to eval set
        skill_path: Path to skill file or directory
        num_trials: Number of optimization trials (for MIPROv2)
        optimizer: "bootstrap" for BootstrapFewShot, "mipro" for MIPROv2

    Returns:
        TuneResult with optimization results
    """
    # Read original skill content
    original_skill_file = get_skill_file(skill_path)
    original_skill_content = original_skill_file.read_text()

    # Create TuneResult to track results
    tune_result = TuneResult.create(
        eval_set=name,
        skill_path=skill_path,
        original_skill=original_skill_content,
        config=TuneConfig(
            num_trials=num_trials,
            optimizer=optimizer,
        ),
    )

    # Run DSPy optimization
    result = optimize_skill(
        eval_name=name,
        skill_path=skill_path,
        num_trials=num_trials,
        optimizer=optimizer,
    )

    # Update tune result
    tune_result.finalize(
        success=result.improved,
        original_score=result.original_score,
        optimized_score=result.optimized_score,
        optimized_skill=result.optimized_skill,
    )

    return tune_result
