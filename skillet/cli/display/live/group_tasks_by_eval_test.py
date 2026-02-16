"""Tests for group_tasks_by_eval and make_task_key."""

from .group_tasks_by_eval import group_tasks_by_eval
from .make_task_key import make_task_key


def describe_make_task_key():
    def it_formats_eval_idx_and_iteration():
        assert make_task_key({"eval_idx": 0, "iteration": 3}) == "0:3"

    def it_handles_large_indices():
        assert make_task_key({"eval_idx": 42, "iteration": 99}) == "42:99"


def describe_group_tasks_by_eval():
    def it_groups_tasks_by_eval_idx():
        tasks = [
            {"eval_idx": 0, "iteration": 0, "eval_source": "a.yaml"},
            {"eval_idx": 0, "iteration": 1, "eval_source": "a.yaml"},
            {"eval_idx": 1, "iteration": 0, "eval_source": "b.yaml"},
        ]
        status = {
            "0:0": {"state": "done", "result": {"pass": True}},
            "0:1": {"state": "pending", "result": None},
            "1:0": {"state": "running", "result": None},
        }
        result = group_tasks_by_eval(tasks, status)

        assert set(result.keys()) == {0, 1}
        assert result[0]["source"] == "a.yaml"
        assert len(result[0]["iterations"]) == 2
        assert result[1]["source"] == "b.yaml"
        assert len(result[1]["iterations"]) == 1

    def it_attaches_correct_status_to_iterations():
        tasks = [
            {"eval_idx": 0, "iteration": 0, "eval_source": "x.yaml"},
            {"eval_idx": 0, "iteration": 1, "eval_source": "x.yaml"},
        ]
        status = {
            "0:0": {"state": "done", "result": {"pass": True}},
            "0:1": {"state": "cached", "result": {"pass": False}},
        }
        result = group_tasks_by_eval(tasks, status)

        iterations = result[0]["iterations"]
        assert iterations[0]["state"] == "done"
        assert iterations[1]["state"] == "cached"

    def it_returns_empty_dict_for_no_tasks():
        assert group_tasks_by_eval([], {}) == {}
