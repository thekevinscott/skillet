# Release Process

This document describes how pyskillet is versioned and released to PyPI.

## Overview

Releases are automated via two GitHub Actions workflows:

1. **Nightly Release** (`version-bump.yml`) - Runs at 2am UTC daily (or manually), analyzes commits since the last tag, calculates the next version using [Conventional Commits](https://www.conventionalcommits.org/), and creates a git tag.

2. **Release** (`release.yml`) - Triggered manually after a tag is pushed, builds the package using `hatch-vcs` (which derives the version from the git tag), and publishes to PyPI via trusted publishing.

## Why Two Workflows?

Tags created by `GITHUB_TOKEN` don't trigger other workflows (a GitHub security limitation). So after the nightly workflow creates and pushes a tag, someone must manually trigger the Release workflow to publish to PyPI.

## Version Calculation

Versions follow [Semantic Versioning](https://semver.org/). The nightly workflow analyzes all commits since the last tag and picks the highest-priority bump:

| Commit Type | Example | Version Bump |
|-------------|---------|--------------|
| Breaking change | `feat!: remove deprecated API` or `BREAKING CHANGE:` in body | Major (1.0.0 → 2.0.0) |
| Feature | `feat: add new command` | Minor (1.0.0 → 1.1.0) |
| Fix/chore/other | `fix: correct typo`, `chore: update deps` | Patch (1.0.0 → 1.0.1) |

All commits in a batch are analyzed together - the highest-priority bump type wins.

## How to Release

### Automatic (Nightly)

1. Merge PRs with proper conventional commit messages
2. Wait for the nightly run at 2am UTC
3. If new commits exist, a tag is created automatically
4. Go to [Actions → Release](../../actions/workflows/release.yml) and manually trigger the workflow

### Manual

1. Go to [Actions → Nightly Release](../../actions/workflows/version-bump.yml)
2. Click "Run workflow" to create a tag immediately
3. Go to [Actions → Release](../../actions/workflows/release.yml) and trigger the publish

## Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat:` - New feature (minor bump)
- `fix:` - Bug fix (patch bump)
- `docs:` - Documentation only
- `chore:` - Maintenance tasks
- `refactor:` - Code refactoring
- `test:` - Adding/updating tests

**Breaking changes:**
- Add `!` after type: `feat!: remove old API`
- Or include `BREAKING CHANGE:` in the commit body

## Dynamic Versioning

The package uses `hatch-vcs` for dynamic versioning:

- **No hardcoded version** in `pyproject.toml`
- Version is derived from git tags at build time
- Dev builds get versions like `0.1.dev1` (commits after a tag)
- Release builds get clean versions like `0.1.2` (built from a tag)

This means:
- `uv build` on a tagged commit → `pyskillet-0.1.2`
- `uv build` between tags → `pyskillet-0.1.2.dev3`

## PyPI Trusted Publishing

The Release workflow uses [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/) - no API tokens needed. Authentication happens via GitHub's OIDC token.

## Troubleshooting

### Tag already exists
If the nightly workflow detects the calculated version tag already exists on the remote, it skips creating a new tag. This prevents duplicate releases.

### Version mismatch
If the built package has an unexpected version, ensure:
1. The release workflow has `fetch-depth: 0` to get full git history
2. You're building from a tagged commit, not between tags

### Publish fails
Check that PyPI trusted publishing is configured for the repository. The workflow needs `id-token: write` permission.
