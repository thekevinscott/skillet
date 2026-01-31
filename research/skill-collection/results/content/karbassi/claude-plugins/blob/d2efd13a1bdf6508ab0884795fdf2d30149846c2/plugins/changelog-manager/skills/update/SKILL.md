---
description: Update CHANGELOG.md with recent changes following Keep a Changelog format
user-invocable: true
allowed-tools: Bash, Read, Grep, Glob, Edit, Write
---

Update the project's CHANGELOG.md with recent changes, following [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.

## When to Use

- Before creating a PR
- After completing a feature or fix
- When preparing a release

## Process

1. **Gather recent changes**
   ```bash
   # Get commits since last tag or recent commits
   git log --oneline $(git describe --tags --abbrev=0 2>/dev/null || echo HEAD~10)..HEAD
   ```

2. **Analyze each commit**
   - Determine if it's user-facing (skip internal refactors, CI changes, etc.)
   - Categorize: Added, Changed, Deprecated, Removed, Fixed, Security

3. **Read existing CHANGELOG.md**
   - Check for existing [Unreleased] section
   - Understand current format and style

4. **Update the changelog**
   - Add entries under [Unreleased] section
   - Include commit SHA reference
   - Link to PR/issue if available
   - Use present tense, imperative mood

5. **Verify the update**
   - Ensure proper formatting
   - No duplicate entries

## Entry Format

```markdown
## [Unreleased]

### Added
- New feature description (abc1234)

### Changed
- Updated behavior description (#123)

### Fixed
- Bug fix description (def5678, fixes #456)
```

Note: Use short commit SHAs (7 chars). GitHub auto-links #123 to issues/PRs.

## Categories (Keep a Changelog)

- **Added** - New features
- **Changed** - Changes in existing functionality
- **Deprecated** - Soon-to-be removed features
- **Removed** - Removed features
- **Fixed** - Bug fixes
- **Security** - Vulnerability fixes

## What to Include

- New features users can use
- Breaking changes
- Bug fixes affecting users
- Security patches
- Deprecation notices

## What to Exclude

- Internal refactoring (no user impact)
- CI/CD changes
- Documentation-only updates (unless significant)
- Dependency bumps (unless security-related)
- Code style/formatting changes

## Release Workflow

When releasing a version:

1. **Update version header**
   ```markdown
   ## [1.2.0] - 2026-01-24
   ```

2. **Add new [Unreleased] section**
   ```markdown
   ## [Unreleased]

   ## [1.2.0] - 2026-01-24
   ```

3. **Update comparison links** (if used)
   ```markdown
   [Unreleased]: https://github.com/user/repo/compare/v1.2.0...HEAD
   [1.2.0]: https://github.com/user/repo/compare/v1.1.0...v1.2.0
   ```

## Guidelines

- Never commit directly to main - work on feature branches
- One changelog entry per logical change (not per commit)
- Be concise but descriptive
- Use consistent formatting with existing entries
- Include migration notes for breaking changes
