"""Tests for make_task_key."""

from .make_task_key import make_task_key


def describe_make_task_key():
    def it_formats_eval_idx_and_iteration():
        assert make_task_key({"eval_idx": 0, "iteration": 3}) == "0:3"

    def it_handles_large_indices():
        assert make_task_key({"eval_idx": 42, "iteration": 99}) == "42:99"
