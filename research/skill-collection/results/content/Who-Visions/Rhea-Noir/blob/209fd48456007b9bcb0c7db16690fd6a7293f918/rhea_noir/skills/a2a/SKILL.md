# A2A Skill

Agent-to-Agent communication and fleet discovery.

## Actions

- `discover` — Discover agents via /.well-known/agent.json
- `list` — List all known agents
- `chat` — Send message to another agent

## Usage

```python
skill.execute("discover", url="https://dav1d-*.run.app")
skill.execute("list")
skill.execute("chat", agent="dav1d", message="Hello!")
```
