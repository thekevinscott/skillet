# Release Process

This document describes how pyskillet is versioned and released to PyPI.

## Overview

Releases are fully automated. Every night at 2am UTC, if there are new commits since the last release, a new version is calculated, tagged, built, and published to PyPI - no manual intervention required.

## How It Works

1. **Nightly at 2am UTC**: The release workflow runs automatically
2. **Check for changes**: Compares commits since the last version tag
3. **Calculate version**: Analyzes commit messages using [Conventional Commits](https://www.conventionalcommits.org/) to determine the version bump
4. **Create tag**: Pushes a new version tag (e.g., `v0.1.3`)
5. **Build & publish**: Builds the package and publishes to PyPI via trusted publishing

All commits merged during the day are batched into a single nightly release.

## Version Calculation

Versions follow [Semantic Versioning](https://semver.org/):

| Release Type | How to Trigger |
|--------------|----------------|
| Patch (1.0.0 → 1.0.1) | Automatic nightly, or manual via "Patch Release" workflow |
| Minor (1.0.0 → 1.1.0) | Manual via "Minor Release" workflow |
| Major (1.0.0 → 2.0.0) | Manual tag creation |

## Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat:` - New user-facing feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `chore:` - Maintenance tasks, CI, internal tooling
- `refactor:` - Code refactoring
- `test:` - Adding/updating tests, evals, test infrastructure

**Note:** Commit types are for categorization only. They do NOT determine version bumps.

## Triggering Releases

### Patch Release (automatic)
Runs nightly at 2am UTC if there are new commits. Can also be triggered manually:
1. Go to [Actions → Patch Release](../../actions/workflows/patch-release.yml)
2. Click "Run workflow"

### Minor Release
1. Go to [Actions → Minor Release](../../actions/workflows/minor-release.yml)
2. Click "Run workflow"

### Major Release
Create and push a tag manually:
```bash
git tag -a v2.0.0 -m "Release v2.0.0"
git push origin v2.0.0
```
Then build and publish manually or create a workflow if needed.

## Dynamic Versioning

The package uses `hatch-vcs` for dynamic versioning:

- **No hardcoded version** in `pyproject.toml`
- Version is derived from git tags at build time
- Release builds get clean versions like `0.1.2` (built from a tag)
- Dev builds get versions like `0.1.2.dev3` (commits after a tag)

## PyPI Trusted Publishing

Publishing uses [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/) - no API tokens needed. Authentication happens via GitHub's OIDC token.

## Troubleshooting

### No release created
- Check if there are commits since the last tag
- Verify commit messages follow Conventional Commits format

### Tag already exists
If the calculated version tag already exists, the workflow skips to prevent duplicate releases.

### Version mismatch
Ensure `fetch-depth: 0` is set in checkout to get full git history for `hatch-vcs`.

### Publish fails
Check that PyPI trusted publishing is configured for the repository with `id-token: write` permission.
