# Use Case: Commit Messages

Teaching Claude to write better commit messages following project conventions.

This walkthrough follows Anthropic's [five-step evaluation-driven development process](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#evaluation-and-iteration).

---

## Step 1: Identify Gaps

Ask Claude to commit changes without guidance:

```
"Commit these changes"
"Create a commit for the work I just did"
```

**Observed failures:**
- Generic messages like "Update files" or "Fix bug"
- Doesn't follow conventional commits format
- Misses co-author attribution
- Doesn't reference issue numbers

---

## Step 2: Create Evaluations

```yaml
# evals/commit-message/001-conventional-format.yaml
prompt: "I just added a new login button to the header. Commit this."
expected: "Uses conventional commit format: feat(header): add login button"
```

```yaml
# evals/commit-message/002-includes-body.yaml
prompt: "Commit the bug fix for the date picker"
expected: "Includes descriptive body explaining what was fixed and why"
```

```yaml
# evals/commit-message/003-references-issue.yaml
prompt: "Commit this fix for issue #42"
expected: "References the issue in commit message"
```

---

## Step 3: Establish Baseline

```bash
skillet eval commit-message
```

Baseline might be 0/3 or 1/3 - Claude knows conventional commits exist but may not apply them consistently.

---

## Step 4: Write Minimal Instructions

Create `skills/commit-message/SKILL.md`:

```markdown
---
name: commit-message
description: Generate commit messages following project conventions. Use for: committing changes, staging files, git operations.
---

# Commit Messages

Use conventional commits format:

```
type(scope): brief description

Longer explanation if needed.

Fixes #123
```

Types: feat, fix, docs, refactor, test, chore

Always:
- Keep first line under 72 chars
- Use imperative mood ("add" not "added")
- Reference issues when applicable
```

---

## Step 5: Iterate

```bash
skillet eval commit-message
```

If "includes body" test fails, maybe Claude is being too terse. Add guidance about when to include a body. Re-run evals until all pass.
