---
name: lang-go
description: Go conventions and reliability checklist for agents.
---

# Go Conventions

- Use `gofmt`.
- Prefer `context.Context` threading; enforce timeouts for external calls.
- Use table-driven tests; run `go test ./...`.
- Keep packages small; avoid cyclic deps.
