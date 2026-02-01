---
name: github-mcp-with-retry
description: Try reconnecting Github MCP until connection succeeds. Use when using Github MCP tools.
---

Since the Github MCP server is not stable, always retry calling the target Github MCP tool until succeed, or after 10 turns' failure.