---
description: Capture notes from the current conversation
allowed-tools: Read, Write, Edit, Glob
disable-model-invocation: true
---

Review the current conversation and capture key insights to the `docs/` directory.

## What to Capture

Extract insights into these files:

### Decisions & Rationale (`docs/decisions.md`)

Key decisions made with reasoning.

```markdown
## [YYYY-MM-DD] Brief title

**Decision:** What was decided

**Rationale:** Why this choice

**Alternatives considered:**
- Option A (rejected: reason)
- Option B (rejected: reason)
```

### Action Items (`docs/action-items.md`)

Tasks and follow-ups identified.

```markdown
## [YYYY-MM-DD]

- [ ] Task description
- [ ] Another task
```

### Blockers & Issues (`docs/blockers.md`)

Problems encountered and unresolved questions.

```markdown
## [YYYY-MM-DD] Brief title

**Issue:** The problem

**Status:** Current state

**Waiting on:** What's needed to resolve
```

### Findings (`docs/findings.md`)

Important discoveries and insights.

```markdown
## [YYYY-MM-DD] Brief title

**Finding:** What was discovered

**Details:** Context and evidence

**Implications:** What this means going forward
```

## Process

1. **Review conversation context**
   - Look through the recent conversation
   - Identify decisions, action items, blockers, and findings

2. **Check existing files**
   - Use Glob to find existing note files in `docs/`
   - Read any existing files to avoid duplicates

3. **Write notes**
   - For each category with content, either:
     - Create the file with a header if it doesn't exist (e.g., `# Decisions`)
     - Append new entries to existing files
   - Use today's date for all entries
   - Never overwrite existing content

4. **Report completion**
   Output a summary:
   ```
   Notes captured:
   - decisions.md: [N] new entries
   - action-items.md: [N] new items
   - blockers.md: [N] new entries
   - findings.md: [N] new entries
   ```

## Guidelines

- Be concise - capture the essence, not verbatim logs
- Skip categories with no new content
- Focus on what's actionable and important
- If unsure whether something is notable, include it
- Group related items under a single date header

## Edge Cases

- If no notable content found, report "No new insights to capture"
- If docs/ doesn't exist, create it first
- Skip routine operations like file edits and searches
