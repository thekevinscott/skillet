"""skillet: Evaluation-driven Claude Code skill development."""

from importlib.metadata import version as _version

__version__ = _version("pyskillet")

# Public API
from skillet.compare import CompareEvalResult, CompareResult, compare
from skillet.errors import (
    EmptyFolderError,
    EvalError,
    EvalValidationError,
    SkillError,
    SkilletError,
)
from skillet.eval import EvaluateResult, IterationResult, PerEvalMetric, evaluate
from skillet.evals import load_evals
from skillet.generate import generate_evals
from skillet.show import ShowEvalResult, ShowResult, show
from skillet.skill import CreateSkillResult, create_skill
from skillet.tune import tune

__all__ = [
    "CompareEvalResult",
    "CompareResult",
    "CreateSkillResult",
    "EmptyFolderError",
    "EvalError",
    "EvalValidationError",
    "EvaluateResult",
    "IterationResult",
    "PerEvalMetric",
    "ShowEvalResult",
    "ShowResult",
    "SkillError",
    "SkilletError",
    "compare",
    "create_skill",
    "evaluate",
    "generate_evals",
    "load_evals",
    "show",
    "tune",
]
