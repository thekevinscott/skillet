---
name: code-review
description: Code review checklist for changes made by an agent.
---

# Code Review Checklist

- Does it match requirements / DoD?
- Are tests added/updated and meaningful?
- Any security footguns (secrets, SSRF, injection, unsafe file ops)?
- Any obvious performance regressions?
- Is the diff minimal and well-structured?
