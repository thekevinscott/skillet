"""Custom exceptions for skillet."""


class SkilletError(Exception):
    """Base exception for skillet errors."""


class GapError(SkilletError):
    """Error loading or processing gaps."""


class EvalError(SkilletError):
    """Error during evaluation."""


class SkillError(SkilletError):
    """Error during skill creation."""
