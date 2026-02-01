---
name: release-prep
description: Prepare a release: run checks, update changelog, verify docs, summarize notes.
---

1) Run:
   - `uv run pytest -q`
   - `uv run ruff check .`
   - `uv run ruff format . --check`
   - `uv run mypy src`
2) Update `spec/changelog.md`.
3) Verify `README.md` is accurate.
4) Summarize release notes.
