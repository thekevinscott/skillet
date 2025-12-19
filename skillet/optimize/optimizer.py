"""Skill optimization using DSPy."""

from pathlib import Path

import dspy
from dspy.teleprompt.teleprompt import Teleprompter

from .loaders import evals_to_trainset
from .metric import create_skillet_metric
from .skill_module import SkillModule


def optimize_skill(
    skill_path: Path | str,
    eval_name: str,
    optimizer: Teleprompter | None = None,
) -> str:
    """Optimize a skill using DSPy.

    Args:
        skill_path: Path to skill directory (with SKILL.md) or direct .md file
        eval_name: Name/path of evals to optimize against
        optimizer: DSPy Teleprompter instance (default: BootstrapFewShot with skillet metric)

    Returns:
        Optimized skill content (SKILL.md text)

    Example:
        # Using default optimizer
        optimized = optimize_skill(
            skill_path="path/to/skill",
            eval_name="add-command",
        )

        # Using custom optimizer
        from skillet.optimize import create_skillet_metric
        import dspy

        optimizer = dspy.MIPROv2(
            metric=create_skillet_metric(),
            num_candidates=10,
        )
        optimized = optimize_skill(
            skill_path="path/to/skill",
            eval_name="add-command",
            optimizer=optimizer,
        )
    """
    # Load skill as DSPy module
    skill = SkillModule.from_file(skill_path)

    # Load evals as training data
    trainset = evals_to_trainset(eval_name)

    # Use default optimizer if none provided
    if optimizer is None:
        metric = create_skillet_metric()
        optimizer = dspy.BootstrapFewShot(metric=metric)

    # Run optimization
    optimized_skill = optimizer.compile(skill, trainset=trainset)

    # Extract optimized instructions
    return optimized_skill.get_optimized_skill()
