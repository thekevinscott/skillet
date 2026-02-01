---
name: check
description: Run repo checks (ruff + pytest).
disable-model-invocation: true
---

Run:
- Windows: powershell -ExecutionPolicy Bypass -File scripts/check.ps1
- Linux/WSL: bash scripts/check.sh

If a check fails:
- capture the error output
- propose the smallest safe fix
- re-run checks
