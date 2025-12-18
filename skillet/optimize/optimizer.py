"""DSPy optimizer wrapper for skill tuning."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import dspy

from .loaders import evals_to_trainset
from .metric import create_skillet_metric
from .skill_module import SkillModule


@dataclass
class OptimizeResult:
    """Result of skill optimization."""

    original_skill: str
    optimized_skill: str
    original_score: float
    optimized_score: float
    num_examples: int

    @property
    def improved(self) -> bool:
        """Whether optimization improved the score."""
        return self.optimized_score > self.original_score

    @property
    def delta(self) -> float:
        """Score improvement (positive = better)."""
        return self.optimized_score - self.original_score

    def __repr__(self) -> str:
        sign = "+" if self.delta > 0 else ""
        return (
            f"OptimizeResult(original={self.original_score:.1%}, "
            f"optimized={self.optimized_score:.1%}, "
            f"delta={sign}{self.delta:.1%})"
        )


def optimize_skill(
    eval_name: str,
    skill_path: Path,
    *,
    max_bootstrapped_demos: int = 4,
    max_labeled_demos: int = 0,
    num_trials: int = 5,
    optimizer: Literal["bootstrap", "mipro"] = "bootstrap",
) -> OptimizeResult:
    """Optimize a skill using DSPy.

    This uses DSPy's optimization framework to improve skill instructions.
    For small datasets (~10 examples), use BootstrapFewShot.
    For larger datasets (200+), use MIPROv2.

    Args:
        eval_name: Name or path to eval set
        skill_path: Path to skill file or directory
        max_bootstrapped_demos: Max demos to bootstrap (0 for instruction-only)
        max_labeled_demos: Max labeled demos (0 for instruction-only)
        num_trials: Number of trials for MIPROv2
        optimizer: "bootstrap" for BootstrapFewShot, "mipro" for MIPROv2

    Returns:
        OptimizeResult with original and optimized skill content
    """
    # Load training examples from evals
    trainset = evals_to_trainset(eval_name)
    num_examples = len(trainset)

    # Create skill module from file
    module = SkillModule.from_file(skill_path)
    original_skill = module.skill_content

    # Create metric
    metric = create_skillet_metric()

    # Choose optimizer
    if optimizer == "mipro":
        teleprompter = dspy.MIPROv2(
            metric=metric,
            num_trials=num_trials,
            max_bootstrapped_demos=max_bootstrapped_demos,
            max_labeled_demos=max_labeled_demos,
        )
    else:
        # Default to BootstrapFewShot for small datasets
        teleprompter = dspy.BootstrapFewShot(
            metric=metric,
            max_bootstrapped_demos=max_bootstrapped_demos,
            max_labeled_demos=max_labeled_demos,
        )

    # Evaluate original
    original_score = _evaluate_module(module, trainset, metric)

    # Optimize
    optimized_module = teleprompter.compile(module, trainset=trainset)

    # Evaluate optimized
    optimized_score = _evaluate_module(optimized_module, trainset, metric)

    # Extract optimized skill
    optimized_skill = optimized_module.get_optimized_skill()

    return OptimizeResult(
        original_skill=original_skill,
        optimized_skill=optimized_skill,
        original_score=original_score,
        optimized_score=optimized_score,
        num_examples=num_examples,
    )


def _evaluate_module(
    module: SkillModule,
    trainset: list[dspy.Example],
    metric,
) -> float:
    """Evaluate a module on the trainset.

    Returns:
        Average score (0.0 to 1.0)
    """
    total = 0.0
    for example in trainset:
        try:
            pred = module(prompt=example.prompt)
            score = metric(example, pred, None)
            total += score
        except Exception:
            # Failed predictions count as 0
            pass

    return total / len(trainset) if trainset else 0.0
