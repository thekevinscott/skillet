# Use Case: MCP Server Builder

Teaching Claude to build high-quality Model Context Protocol (MCP) servers.

This walkthrough follows Anthropic's [five-step evaluation-driven development process](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#evaluation-and-iteration).

---

## The Problem

When asked to create an MCP server, Claude often:
- Creates a basic implementation missing key features
- Doesn't follow MCP best practices for tool naming and discovery
- Misses error handling and pagination
- Forgets to create evaluations to verify the server works

An MCP server's quality is measured by how well it enables LLMs to accomplish real-world tasks—not just whether it technically runs.

---

## Step 1: Identify Gaps

Ask Claude to create an MCP server without any skill:

```
"Create an MCP server that integrates with the GitHub API"
"Build an MCP server for Notion"
"Make an MCP server that can query my Postgres database"
```

**Observed failures:**

- Implements only 2-3 tools instead of comprehensive API coverage
- Inconsistent tool naming (mixes `create_issue` with `listRepos`)
- No pagination for list endpoints
- Generic error messages that don't help LLMs recover
- No structured output schemas
- Missing tool annotations (readOnlyHint, destructiveHint)
- No evaluations to verify it actually works

---

## Step 2: Create Evaluations

```yaml
# evals/mcp-builder/001-comprehensive-tools.yaml
prompt: "Create an MCP server for the GitHub API"
expected: |
  Implements major endpoint categories:
  - Repositories (list, create, get, update)
  - Issues (list, create, get, update, close)
  - Pull requests (list, create, get, merge)
  - Users (get, list repos)
  Not just 2-3 basic tools.
```

```yaml
# evals/mcp-builder/002-consistent-naming.yaml
prompt: "Create an MCP server for Slack"
expected: |
  Uses consistent naming convention with prefix:
  - slack_send_message
  - slack_list_channels
  - slack_get_user
  Not mixed styles like sendMessage, list_channels, GetUser
```

```yaml
# evals/mcp-builder/003-pagination.yaml
prompt: "Create an MCP server for a REST API that returns lists of items"
expected: |
  List endpoints support pagination:
  - cursor or page parameter
  - hasMore indicator in response
  - Handles large result sets gracefully
```

```yaml
# evals/mcp-builder/004-error-handling.yaml
prompt: "Create an MCP server for an API. Include proper error handling."
expected: |
  Errors are actionable, not generic:
  - "Repository not found. Check the owner/repo format: owner/repo-name"
  - Not just "Error: 404"
  Includes suggestions for how to fix the problem.
```

```yaml
# evals/mcp-builder/005-creates-evals.yaml
prompt: "Create an MCP server for the HackerNews API and verify it works"
expected: |
  Creates evaluation questions to test the server:
  - 10 realistic, complex questions
  - Questions require multiple tool calls
  - Answers are verifiable
  Uses the MCP Inspector to test.
```

---

## Step 3: Establish Baseline

```bash
skillet eval mcp-builder
```

Expected baseline: 1-2/5 passing. Claude can create a basic MCP server but misses quality aspects.

---

## Step 4: Write Minimal Instructions

Create `skills/mcp-builder/SKILL.md`:

```markdown
---
name: mcp-builder
description: Build high-quality MCP servers. Triggers on: MCP server, Model Context Protocol, create tools for Claude, API integration.
---

# MCP Server Development

## Quality Principles

1. **Comprehensive coverage** - Implement major API operations, not just basics
2. **Consistent naming** - Use prefix convention: `service_action_target`
3. **Pagination support** - All list endpoints should paginate
4. **Actionable errors** - Guide the LLM toward solutions
5. **Verify with evals** - Create 10 test questions

## Four-Phase Process

### Phase 1: Research
- Study the API documentation thoroughly
- List all endpoints to implement
- Identify authentication method

### Phase 2: Implement
- Set up TypeScript project with MCP SDK
- Create shared API client with auth
- Implement tools with:
  - Clear input schemas (Zod)
  - Output schemas where possible
  - Tool annotations (readOnlyHint, etc.)

### Phase 3: Test
```bash
npm run build
npx @modelcontextprotocol/inspector
```

### Phase 4: Evaluate
Create 10 complex questions that require multiple tool calls:
```xml
<evaluation>
  <qa_pair>
    <question>Find the most starred TypeScript repo created in 2024</question>
    <answer>repo-name</answer>
  </qa_pair>
</evaluation>
```

## Tool Naming Convention

```
github_create_issue      ✓ (prefix_action_target)
github_list_repositories ✓
createIssue              ✗ (no prefix)
list_repos               ✗ (inconsistent abbreviation)
```

## Error Messages

```
❌ "Error: 404"
✓ "Repository 'owner/repo' not found. Verify the repository exists and you have access. Format: owner/repo-name"
```

## Pagination Pattern

```typescript
{
  items: [...],
  hasMore: true,
  cursor: "abc123"
}
```

Tools should accept optional `cursor` parameter and return `hasMore` + next cursor.
```

---

## Step 5: Iterate

Run evals, identify gaps, refine the skill. The meta-goal: Claude should be able to build MCP servers that Claude can use effectively.

---

## Why This Matters

- **MCP is the protocol** for extending Claude's capabilities
- **Tool quality directly impacts** Claude's ability to help users
- **Bad MCP servers** create frustrating experiences (vague errors, missing features)
- **Good MCP servers** feel like magic (Claude just works)

This skill is meta: teaching Claude to build better tools for Claude (and other LLMs).
