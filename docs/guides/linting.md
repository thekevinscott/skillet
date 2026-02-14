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
