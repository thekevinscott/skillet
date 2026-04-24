# Migration Guide

Upgrade instructions for Skillet consumers. Start here when bumping your pinned version.

Skillet does not strictly follow semantic versioning — any release (patch, minor,
or major) may contain behavior changes worth reading before upgrading. Entries
below are most-recent first. If there is no section for a version you are
crossing, no consumer action is required.

Each release with migration impact gets a section using the template at the
bottom of this file. "Migration impact" means anything a downstream consumer
needs to be aware of to upgrade smoothly: breaking API changes, removed
deprecations, changed defaults, new required config, or same-API/new-runtime
behavior. Pure additions and bug fixes with no required consumer action do not
need a section.

## [Unreleased]

_No migration steps for the next release yet._

---

## Template

Copy the block below when documenting a new release. Delete sections that do not
apply — do not leave empty headings. Keep the most recent release at the top.

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Summary

One paragraph describing what changed and why. Readers should be able to decide
from this paragraph alone whether this release affects them.

### Required changes

Before/after for anything a consumer must update: config keys, CLI flags,
SDK function signatures, action inputs, environment variables.

| Area | Before | After |
|------|--------|-------|
| CLI flag | `skillet eval -t foo` | `skillet eval --tools foo` |
| SDK | `evaluate(...) -> dict` | `evaluate(...) -> EvaluateResult` |
| Config | `model: claude-3` | `model: claude-sonnet-4-6` |

### Deprecations removed

Items previously warned about that are now gone. Each entry names the
replacement.

- `old_function()` → use `new_function()`
- `--legacy-flag` → use `--new-flag`

### Behavior changes without code changes

Same public API, different runtime behavior. Tag format changes, exit codes,
default values, output shape, cache invalidation, etc.

- Exit code on judge failure changed from `1` to `2`. CI checks matching `== 1`
  must be updated.
- Cache hashes switched from MD5 to SHA-256 — existing caches are invalidated on
  first run.

### Verification

How a consumer confirms the upgrade worked. Prefer a single command whose output
they can check.

```bash
skillet --version   # expect X.Y.Z
skillet eval --dry-run ./my-suite.yaml
```

Expected output: `... PASS rate: <unchanged from previous release> ...`
```
