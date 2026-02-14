# Linting Skills

Skillet includes a built-in linter that checks your `SKILL.md` files for common issues before you publish or share them.

## Quick start

```bash
skillet lint path/to/SKILL.md
```

If there are no issues, you'll see:

```
No issues found
```

If there are problems, each finding is printed with its location and severity:

```
SKILL.md:1: [warning] Frontmatter missing required field: name
SKILL.md: [warning] Missing recommended field: license

2 finding(s)
```

## What gets checked

The linter runs 14 rules organized into four categories:

### Naming conventions

Skills should follow a consistent naming scheme. The linter checks that:

- The file is named exactly `SKILL.md` (not `skill.md` or `Skill.md`)
- The parent folder uses kebab-case (e.g., `my-skill/`, not `MySkill/`)
- The `name` field in frontmatter is also kebab-case
- The `name` field matches the parent folder name
- The name doesn't contain reserved words (`claude` or `anthropic`)

### Frontmatter structure

Valid frontmatter is essential for skill discovery and loading. The linter checks:

- Frontmatter has proper `---` delimiters
- Required fields `name` and `description` are present
- No XML angle brackets (`< >`) appear in frontmatter values
- The `description` field is under 1,024 characters

### Body constraints

- The skill body should be under 5,000 words to stay within context limits
- No `README.md` should exist alongside `SKILL.md` in the same folder

### Recommended fields

These produce warnings (not errors) to encourage best practices:

- `license` — specify the skill's license
- `compatibility` — declare what the skill is compatible with
- `metadata` — additional structured metadata

## LLM-assisted rules

By default, the linter also runs LLM-assisted rules that perform semantic analysis on your skill content. To skip these (e.g., in CI or offline environments):

```bash
skillet lint --no-llm path/to/SKILL.md
```

## Listing rules

To see all available rules:

```bash
skillet lint --list-rules
```

Each rule includes a link to its documentation.

## Severity levels

| Severity | Meaning |
|----------|---------|
| **error** | Must be fixed — the skill may not work correctly |
| **warning** | Should be fixed — improves quality and discoverability |

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | No issues found |
| 1 | One or more findings |
| 2 | Error (file not found, invalid input) |

## Rule reference

### filename-case

**Severity:** warning

The skill file must be named exactly `SKILL.md`. Other casings like `skill.md` or `Skill.md` are not recognized.

### folder-kebab-case

**Severity:** warning

The parent folder must use kebab-case: lowercase letters, digits, and hyphens only (e.g., `my-skill/`, not `MySkill/` or `my_skill/`).

### name-kebab-case

**Severity:** warning

The `name` field in frontmatter must be kebab-case, matching the same pattern as folder names.

### name-matches-folder

**Severity:** warning

The `name` field must match the parent folder name. For example, if the skill lives in `browser-fallback/SKILL.md`, the name must be `browser-fallback`.

### name-no-reserved

**Severity:** error

The skill name must not contain the words `claude` or `anthropic`. These are reserved to avoid confusion with official Anthropic skills.

### frontmatter-valid

**Severity:** warning

Frontmatter must include both `name` and `description` fields. These are required for skill discovery and loading.

### frontmatter-delimiters

**Severity:** error

The file must start with `---` and have a matching closing `---` delimiter. Without proper delimiters, frontmatter cannot be parsed.

### frontmatter-no-xml

**Severity:** error

Frontmatter values must not contain XML angle brackets (`<` or `>`). These can cause parsing issues in YAML frontmatter.

### description-length

**Severity:** warning

The `description` field must be under 1,024 characters. Longer descriptions may be truncated in skill listings.

### body-word-count

**Severity:** warning

The skill body (everything after frontmatter) should be under 5,000 words. Longer skills consume more context window and may be less effective.

### no-readme

**Severity:** warning

A `README.md` file should not exist alongside `SKILL.md` in the same folder. The skill file itself serves as documentation.

### field-license

**Severity:** warning

The `license` field should be present in frontmatter to declare the skill's license (e.g., `MIT`, `Apache-2.0`).

### field-compatibility

**Severity:** warning

The `compatibility` field should be present to declare what environment the skill targets (e.g., `claude-code`).

### field-metadata

**Severity:** warning

The `metadata` field should be present for additional structured data like version numbers.

## Example: a clean skill

```markdown
---
name: my-skill
description: A brief description of what this skill does.
license: MIT
compatibility: claude-code
metadata:
  version: 1
---

# Instructions

Your skill instructions go here.
```

Running `skillet lint` against this file (in a folder named `my-skill/`) produces zero findings.
