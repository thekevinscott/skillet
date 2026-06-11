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


class LintError(SkilletError):
    """Error during linting."""


class HarnessError(SkilletError):
    """Error selecting or running an agent harness (the agent under test)."""


class UnknownHarnessError(HarnessError):
    """Raised when a harness with no registered adapter is requested."""


class HarnessNotInstalledError(HarnessError):
    """Raised when a harness's optional backend (e.g. lite-harness) is unavailable."""
