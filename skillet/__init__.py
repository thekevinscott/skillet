"""skillet: Evaluation-driven Claude Code skill development."""

__version__ = "0.1.0"

# Public API
from skillet.compare import compare
from skillet.errors import EvalError, GapError, SkillError, SkilletError
from skillet.eval import evaluate
from skillet.gaps import load_gaps
from skillet.skill import create_skill
from skillet.tune import tune

__all__ = [
    "EvalError",
    "GapError",
    "SkillError",
    "SkilletError",
    "compare",
    "create_skill",
    "evaluate",
    "load_gaps",
    "tune",
]
