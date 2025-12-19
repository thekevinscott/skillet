"""skillet: Evaluation-driven Claude Code skill development."""

__version__ = "0.1.0"

# Public API
from skillet.compare import compare
from skillet.errors import (
    EmptyFolderError,
    EvalError,
    EvalValidationError,
    SkillError,
    SkilletError,
)
from skillet.eval import evaluate
from skillet.evals import load_evals
from skillet.skill import create_skill
from skillet.tune import tune

__all__ = [
    "EmptyFolderError",
    "EvalError",
    "EvalValidationError",
    "SkillError",
    "SkilletError",
    "compare",
    "create_skill",
    "evaluate",
    "load_evals",
    "tune",
]
