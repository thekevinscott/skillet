---
name: build-error-resolver
description: Fix Python build/type/test errors with minimal code changes.
---

# Build Error Resolver

Tools:
- python -m pytest
- python -m mypy .
- python -m ruff check .
- python -m build

Workflow:
1. Reproduce the error
2. Make the smallest change to fix it
3. Re-run the failing command
