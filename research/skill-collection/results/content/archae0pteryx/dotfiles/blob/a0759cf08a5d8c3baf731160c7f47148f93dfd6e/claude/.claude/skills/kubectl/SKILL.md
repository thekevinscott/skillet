---
name: kubectl-cli
description: How to use kubectl
---

- For kustomization related things: `kubectl kustomize ...` do not use `kustomize` directly. this is depreciated
- All kubectl commands should have the `--context` and `-n` explicitly set
- Always look at the diffs before considering applying anything first. Same for patches