"""Prompt optimization using DSPy."""

from .dspy_integration.claude_lm import ClaudeAgentLM
from .dspy_integration.configure import get_claude_lm
from .dspy_integration.dataclasses import TrialResult
from .dspy_integration.skillet_mipro import SkilletMIPRO
from .loaders import evals_to_trainset
from .metric import create_skillet_metric
from .optimizer import optimize_skill
from .skill_module import SkillModule

__all__ = [
    "ClaudeAgentLM",
    "SkillModule",
    "SkilletMIPRO",
    "TrialResult",
    "create_skillet_metric",
    "evals_to_trainset",
    "get_claude_lm",
    "optimize_skill",
]
