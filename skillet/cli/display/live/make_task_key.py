"""Build the status-dict key for a task."""


def make_task_key(task: dict) -> str:
    """Build the status-dict key for a task."""
    return f"{task['eval_idx']}:{task['iteration']}"
