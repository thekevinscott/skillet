"""Eval loading and management."""

from .load import load_gaps

# Alias for cleaner API - prefer load_evals in new code
load_evals = load_gaps

__all__ = ["load_evals", "load_gaps"]
