# Capture with /skillet:add

The `/skillet:add` slash command is the primary way to capture evals during your Claude Code sessions.

## When to Use It

Use `/skillet:add` immediately after Claude produces a response that doesn't match your expectations:

- Wrong format or structure
- Missing information
- Incorrect behavior
- Suboptimal approach

Capture failures as they happen—don't wait until later.

## How It Works

### 1. Notice a Problem

```
> Write a commit message for: added user authentication

Claude: Added user authentication feature with login, logout,
and session management.
```

### 2. Run the Command

```
> /skillet:add
```

### 3. Describe What You Expected

Claude will ask what you expected:

```
Claude: What behavior or format did you expect?

> Should use conventional commits format like "feat(auth): add user authentication"
```

### 4. Choose a Category

Claude checks existing eval categories and presents options:

```
Claude: Where should I save this eval?

1. conventional-commits (existing, 3 evals)
2. commit-messages — New category for commit format
3. git-conventions — New category for git conventions
4. Other
```

### 5. Confirm

```
Claude: Eval saved to ~/.skillet/evals/conventional-commits/004.yaml

  ├─ Prompt: "Write a commit message for: added user authentication"
  ├─ Actual: "Added user authentication feature..."
  ├─ Expected: "Should use conventional commits format..."

You now have 4 evals for this skill.
```

## What Gets Captured

The slash command creates a YAML file with:

```yaml
timestamp: "2025-01-22T10:30:45.123Z"
name: conventional-commits
prompt: "Write a commit message for: added user authentication"
actual: "Added user authentication feature with login, logout, and session management."
expected: "Should use conventional commits format like feat(auth): add user authentication"
```

| Field | Source |
|-------|--------|
| `timestamp` | Current time |
| `name` | Your category choice |
| `prompt` | From conversation history |
| `actual` | Claude's response (summarized if long) |
| `expected` | What you described |

## Tips for Good Evals

### Be Specific

Instead of:
> "Should be better formatted"

Say:
> "Should use markdown headers for sections and code blocks for examples"

### Focus on Observable Behavior

Instead of:
> "Should understand the context better"

Say:
> "Should check for existing files before creating new ones"

### One Issue Per Eval

Don't combine multiple problems:
> "Should use conventional commits AND add a scope AND be shorter"

Split into separate evals if needed.

### Group Related Evals

Use the same category name for related issues. 5+ evals per category gives the skill generator more to work with.

## Storage Location

Evals are saved to:

```
~/.skillet/evals/<category>/
  001.yaml
  002.yaml
  ...
```

This location can be changed with the `SKILLET_DIR` environment variable.

## Next Steps

After capturing 3-5 evals:

1. Run baseline: `skillet eval <category>`
2. Create skill: `skillet create <category>`
3. Test skill: `skillet eval <category> ~/.claude/skills/<category>`
4. Tune: `skillet tune <category> ~/.claude/skills/<category>`
