"""skillet: Evaluation-driven Claude Code skill development."""

__version__ = "0.1.0"

# Public API
from skillet.compare import run_compare
from skillet.errors import EvalError, GapError, SkillError, SkilletError
from skillet.eval import judge_response, run_eval
from skillet.gaps import load_gaps
from skillet.skill import create_skill, draft_skill
from skillet.tune import run_tune

__all__ = [
    "EvalError",
    "GapError",
    "SkillError",
    "SkilletError",
    "create_skill",
    "draft_skill",
    "judge_response",
    "load_gaps",
    "run_compare",
    "run_eval",
    "run_tune",
]
