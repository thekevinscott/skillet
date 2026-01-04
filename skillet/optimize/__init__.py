"""Prompt optimization using DSPy."""

from .dspy_integration.claude_lm import ClaudeAgentLM
from .dspy_integration.configure import configure_dspy
from .dspy_integration.mipro import SkilletMIPRO, TrialResult
from .loaders import evals_to_trainset
from .metric import create_skillet_metric
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
