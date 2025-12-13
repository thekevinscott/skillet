"""CLI for skillet."""

from rich.console import Console

from .main import app, main

console = Console()

__all__ = ["app", "console", "main"]
