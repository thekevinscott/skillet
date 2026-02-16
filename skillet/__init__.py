"""skillet: Evaluation-driven Claude Code skill development."""

from importlib.metadata import version as _version

__version__ = _version("pyskillet")

# Errors are lightweight — import eagerly for isinstance/except usage
from skillet.errors import (
    EmptyFolderError,
    EvalError,
    EvalValidationError,
    SkillError,
    SkilletError,
)

# Lazy imports (PEP 562) for heavy function imports to avoid pulling in
# DSPy/numpy/optuna on `import skillet`.
_LAZY_IMPORTS: dict[str, str] = {
    "compare": "skillet.compare",
    "CompareEvalResult": "skillet.compare",
    "CompareResult": "skillet.compare",
    "create_skill": "skillet.skill",
    "CreateSkillResult": "skillet.skill",
    "evaluate": "skillet.eval",
    "EvaluateResult": "skillet.eval",
    "IterationResult": "skillet.eval",
    "PerEvalMetric": "skillet.eval",
    "generate_evals": "skillet.generate",
    "load_evals": "skillet.evals",
    "show": "skillet.show",
    "ShowEvalResult": "skillet.show",
    "ShowResult": "skillet.show",
    "tune": "skillet.tune",
}

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


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        import importlib

        module = importlib.import_module(_LAZY_IMPORTS[name])
        value = getattr(module, name)
        # Cache on module to avoid repeated __getattr__ calls
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
