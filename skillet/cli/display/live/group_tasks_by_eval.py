"""Group eval tasks by eval index with attached status."""
# skillet: allow-multiple-public-callables

from typing import TypedDict


class EvalGroup(TypedDict):
    source: str
    iterations: list[dict]


def make_task_key(task: dict) -> str:
    """Build the status-dict key for a task."""
    return f"{task['eval_idx']}:{task['iteration']}"


def group_tasks_by_eval(tasks: list[dict], status: dict[str, dict]) -> dict[int, EvalGroup]:
    """Bucket tasks by eval_idx, attaching each iteration's status."""
    evals: dict[int, EvalGroup] = {}
    for task in tasks:
        eval_idx = task["eval_idx"]
        if eval_idx not in evals:
            evals[eval_idx] = {"source": task["eval_source"], "iterations": []}
        key = make_task_key(task)
        evals[eval_idx]["iterations"].append(status[key])
    return evals
