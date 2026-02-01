# Task Skill

Manage long-running background tasks.

## Actions

- `create` — Create a new task
- `start` — Start a pending task
- `status` — Get task status
- `list` — List all tasks
- `complete` — Mark task complete

## Usage

```python
skill.execute("create", description="Research topic X")
skill.execute("list")
skill.execute("status", task_id="abc-123")
```
