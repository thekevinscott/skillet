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

Versions follow [Semantic Versioning](https://semver.org/). The workflow analyzes all commits since the last tag and picks the highest-priority bump:

| Commit Type | Example | Version Bump |
|-------------|---------|--------------|
| Breaking change | `feat!: remove deprecated API` or `BREAKING CHANGE:` in body | Major (1.0.0 → 2.0.0) |
| Feature | `feat: add new command` | Minor (1.0.0 → 1.1.0) |
| Fix/chore/other | `fix: correct typo`, `chore: update deps` | Patch (1.0.0 → 1.0.1) |

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
