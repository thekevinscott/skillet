"""Custom exceptions for skillet."""


class SkilletError(Exception):
    """Base exception for skillet errors."""


class EvalError(SkilletError):
    """Error loading or processing evals."""


class EvalValidationError(EvalError):
    """Error validating eval file format."""


class EmptyFolderError(EvalError):
    """Error when eval folder is empty or doesn't exist."""


class SkillError(SkilletError):
    """Error during skill creation."""
