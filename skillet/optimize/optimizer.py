"""Skill optimization using DSPy."""

from pathlib import Path
from typing import Literal

import dspy

from .loaders import evals_to_trainset
from .metric import create_skillet_metric
from .skill_module import SkillModule


def optimize_skill(
    skill_path: Path | str,
    eval_name: str,
    optimizer: Literal["bootstrap", "mipro"] = "bootstrap",
    trials: int = 5,
) -> str:
    """Optimize a skill using DSPy.

    Args:
        skill_path: Path to skill directory (with SKILL.md) or direct .md file
        eval_name: Name/path of evals to optimize against
        optimizer: Which DSPy optimizer to use ("bootstrap" or "mipro")
        trials: Number of optimization trials

    Returns:
        Optimized skill content (SKILL.md text)

    Example:
        optimized = optimize_skill(
            skill_path="path/to/skill",
            eval_name="add-command",
            optimizer="bootstrap",
            trials=5,
        )
        print(optimized)
    """
    # Load skill as DSPy module
    skill = SkillModule.from_file(skill_path)

    # Load evals as training data
    trainset = evals_to_trainset(eval_name)

    # Create metric
    metric = create_skillet_metric()

    # Select optimizer
    if optimizer == "bootstrap":
        dspy_optimizer = dspy.BootstrapFewShot(
            metric=metric,
            max_bootstrapped_demos=trials,
        )
    elif optimizer == "mipro":
        dspy_optimizer = dspy.MIPROv2(
            metric=metric,
            num_candidates=trials,
            init_temperature=1.0,
        )
    else:
        raise ValueError(f"Unknown optimizer: {optimizer}")

    # Run optimization
    optimized_skill = dspy_optimizer.compile(skill, trainset=trainset)

    # Extract optimized instructions
    return optimized_skill.get_optimized_skill()
