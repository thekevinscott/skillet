---
name: code-review
version: 1.0
---

# Code Review SKILL

## 3-Layer Validation

1. **Type-check:** mypy . or npm run type-check
2. **Lint:** ruff check . or npm run lint
3. **Test:** pytest tests/ (unit only, not E2E)
