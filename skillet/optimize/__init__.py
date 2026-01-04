"""Prompt optimization using DSPy."""

from .claude_lm import ClaudeAgentLM
from .configure import configure_dspy
from .loaders import evals_to_trainset
from .metric import create_skillet_metric
from .mipro import SkilletMIPRO, TrialResult
from .optimizer import optimize_skill
from .skill_module import SkillModule

__all__ = [
    "ClaudeAgentLM",
    "SkillModule",
    "SkilletMIPRO",
    "TrialResult",
    "configure_dspy",
    "create_skillet_metric",
    "evals_to_trainset",
    "optimize_skill",
]
