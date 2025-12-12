"""Internal type utilities."""

from typing import TypeVar

T = TypeVar("T")


def matches_type(obj: object, accepted_types: type[T] | list[type[T]]) -> bool:
    """Check if obj is an instance of any of the accepted types."""
    if not isinstance(accepted_types, list):
        accepted_types = [accepted_types]
    return any(isinstance(obj, t) for t in accepted_types)
