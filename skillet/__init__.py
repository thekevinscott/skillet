"""skillet: Evaluation-driven Claude Code skill development."""

from importlib.metadata import version as _version

__version__ = _version("pyskillet")

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
from skillet.generate import generate_evals
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
    "generate_evals",
    "load_evals",
    "tune",
]
