---
name: refactor-safe
description: Safe refactoring workflow (small steps, tests, diagnostics)
---

# Safe Refactor

1. Add/confirm tests (golden tests if needed).
2. Make one mechanical change at a time.
3. Run typecheck + tests after each step.
4. Avoid large cross-cutting rewrites.
