"""Generate candidate evals from SKILL.md files.

Usage:
    from skillet import generate_evals

    result = await generate_evals(
        Path("~/.claude/skills/browser-fallback"),
        output_dir=Path("./candidates"),
    )
"""

from .generate_evals import generate_evals
from .types import CandidateEval, EvalDomain, GenerateResult

__all__ = [
    "CandidateEval",
    "EvalDomain",
    "GenerateResult",
    "generate_evals",
]
