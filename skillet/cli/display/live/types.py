"""Type definitions for the live display module."""

from typing import TypedDict


class EvalGroup(TypedDict):
    source: str
    iterations: list[dict]
