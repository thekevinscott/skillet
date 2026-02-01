# `load_tool_from_skill`

- What: Load a skill-backed tool.
- When: Reuse approved tools.
- Example:
```python
from orchestrator import load_tool_from_skill
tool = load_tool_from_skill("echo", org="acme")
print(tool)
```
- Links: [Skill Bridge](../../skill-bridge.md)