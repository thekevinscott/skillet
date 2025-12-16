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

Versions follow [Semantic Versioning](https://semver.org/). **All releases default to patch.** Minor and major releases require explicit markers in the commit body:

| Marker | Example | Version Bump |
|--------|---------|--------------|
| `BREAKING CHANGE:` in body | See below | Major (1.0.0 → 2.0.0) |
| `[minor]` in body | See below | Minor (1.0.0 → 1.1.0) |
| (default) | Any commit type | Patch (1.0.0 → 1.0.1) |

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

**Note:** The commit type does NOT determine the version bump. Use explicit markers for minor/major releases.

**Minor release** - include `[minor]` in the commit body:
```
feat: add CSV export support

Adds ability to export data in CSV format.

[minor]
```

**Major release** - include `BREAKING CHANGE:` in the commit body:
```
feat: redesign configuration format

BREAKING CHANGE: config.yaml structure has changed, see migration guide.
```

## Manual Release

To trigger a release immediately (without waiting for the nightly run):

1. Go to [Actions → Nightly Release](../../actions/workflows/version-bump.yml)
2. Click "Run workflow"

The workflow handles everything - version calculation, tagging, building, and publishing.

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
