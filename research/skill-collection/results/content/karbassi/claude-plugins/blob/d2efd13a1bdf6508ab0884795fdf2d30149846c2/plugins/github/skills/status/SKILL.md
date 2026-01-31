---
description: Show local git and GitHub repository status
allowed-tools: Bash, Task, AskUserQuestion
user-invocable: true
---

Display a combined status of the local git repository and GitHub remote, including branch info, working tree status, open PRs, and open issues. Offer contextual suggestions and quick actions.

## Process

Use the Task tool with `run_in_background: true` to spawn a background agent that collects all the status information. This allows the user to continue working while the status is gathered.

The background agent should run these commands and compile the results:

### 1. Local Git Status

```bash
# Basic status
git status

# Last 5 commits
git log --oneline -5

# Stashed changes
git stash list

# Ahead/behind count
git rev-list --left-right --count HEAD...@{upstream} 2>/dev/null
```

Report:
- Current branch and tracking status
- Working tree status (clean/dirty, staged/unstaged changes)
- Stashed changes count (if any)
- Commits ahead/behind remote
- Last 5 commits

### 2. GitHub Repository Status

```bash
# Repo info
gh repo view --json name,owner,url,defaultBranchRef --jq '{name, owner: .owner.login, url, defaultBranch: .defaultBranchRef.name}'

# Current branch's PR (if exists)
gh pr view --json number,title,state,reviewDecision,statusCheckRollup --jq '{number, title, state, reviewDecision, checks: [.statusCheckRollup[]? | {name: .name, status: .status, conclusion: .conclusion}]}'

# Open PRs (authored by current user)
gh pr list --author @me --limit 10

# All open PRs
gh pr list --limit 10

# Assigned issues
gh issue list --assignee @me --limit 10

# All open issues
gh issue list --limit 10
```

Report:
- Repository name and owner
- Current branch's PR status (if exists):
  - Review decision (approved, changes requested, review required)
  - CI/CD check status (passing, failing, pending)
- Your open PRs (number, title, branch)
- All open PRs (number, title, branch)
- Your assigned issues (number, title)
- All open issues (number, title)

### 3. Cleanup Check

```bash
# Merged local branches
git branch --merged main | grep -v '^\*' | grep -v 'main'

# Stale remote tracking branches
git remote prune origin --dry-run

# Remote branches for merged PRs
gh pr list --state merged --author @me --limit 10 --json headRefName --jq '.[].headRefName'
```

Report any cleanup opportunities found:
- Merged local branches that can be deleted
- Stale remote tracking branches that can be pruned
- Remote branches from your merged PRs that can be deleted

## Output Format

The background agent should compile results in this format:

**Local Git:**
- Branch: `branch-name`
- Tracking: up to date / X commits ahead / X commits behind / X ahead, Y behind
- Working tree: clean / X files modified (list them)
- Stashes: X stashed changes (if any)

**Current Branch PR:** (if exists)
- PR #X: title
- Review: approved / changes requested / review required / no reviews
- Checks: passing / failing (list failures) / pending

**GitHub (owner/repo):**
- Your open PRs: X
- All open PRs: X
- Your assigned issues: X
- All open issues: X

List the PRs and issues with their numbers and titles.

**Cleanup Opportunities:**
- Merged local branches
- Stale remote tracking branches
- Remote branches from merged PRs
- Or state "None" if nothing to clean up

## Background Execution

1. Launch the Task agent with `run_in_background: true` and `subagent_type: "Bash"`
2. Tell the user the status check is running in the background
3. When the agent completes, present the compiled results to the user

Example Task invocation:
```
Task tool with:
  - subagent_type: "Bash"
  - run_in_background: true
  - allowed_tools: ["Bash(git *)", "Bash(gh *)"]
  - description: "Gather git/GitHub status"
  - prompt: <the commands and output format above>
```

Note: The `allowed_tools` parameter grants the background agent permission to run git and gh commands without prompting.

## Workflow Suggestions

After displaying the status, analyze the results and provide contextual suggestions:

### Dirty Working Tree
If there are uncommitted changes:
> "You have uncommitted changes. Consider committing or stashing them."

### Behind Remote
If the branch is behind the remote:
> "Your branch is X commits behind. Consider pulling: `git pull`"

### Unpushed Commits
If the branch is ahead of remote:
> "You have X unpushed commits. Consider pushing: `git push`"

### Failing CI Checks
If the current PR has failing checks:
> "CI checks are failing:"
> - List each failing check with its name

### Pending Reviews
If the PR needs review:
> "PR #X is awaiting review."

### Changes Requested
If the PR has changes requested:
> "PR #X has changes requested. Run `/github:fix-pr` to address review comments."

### Unresolved Review Comments
If there are unresolved review threads:
> "PR #X has unresolved review comments. Run `/github:fix-pr` to address them."

## Cleanup Actions

After displaying the status, if there are any cleanup opportunities, use the `AskUserQuestion` tool to offer them to the user.

### Possible Cleanup Actions

1. **Merged local branches**: Local branches that have been merged into main
   - Command: `git branch -d <branch-name>`

2. **Stale remote tracking branches**: Remote branches that no longer exist on the remote
   - Detect with: `git remote prune origin --dry-run`
   - Command: `git remote prune origin`

3. **Remote branches from merged PRs**: Your remote branches that had PRs merged
   - Command: `git push origin --delete <branch-name>`

4. **Push uncommitted changes**: If working tree is dirty and changes are staged
   - Suggest: commit and push

5. **Pull from remote**: If branch is behind
   - Command: `git pull`

### Using AskUserQuestion

Only show this if there are actionable items. Build options dynamically based on what was found:

```
AskUserQuestion with:
  - header: "Actions"
  - question: "Would you like to perform any of these actions?"
  - multiSelect: true
  - options: [dynamically built based on findings]
```

Example options:
- `Delete merged branch 'feature/old-branch'` - "This branch has been merged into main"
- `Prune stale remote branches` - "Remove local references to deleted remote branches"
- `Delete remote branch 'feature/merged-pr'` - "This branch's PR was merged"
- `Pull latest changes` - "Your branch is X commits behind remote"
- `Push commits` - "You have X unpushed commits"
- `Skip` - "Don't perform any actions" (required: AskUserQuestion needs at least 2 options)

If the user selects actions, execute them and report the results.

If there are no cleanup opportunities, do not ask - just end after showing the status.

## Quick Actions

After cleanup, offer quick actions if relevant:

### Open Current PR in Browser
If current branch has a PR:
```bash
gh pr view --web
```

### Switch to PR Branch
If user wants to work on a different PR:
```bash
gh pr checkout <pr-number>
```

### Create PR for Current Branch
If current branch has no PR and has unpushed commits:
```bash
gh pr create
```

Include these in the AskUserQuestion options when applicable.

## No Actions Needed

If there are no cleanup opportunities, no workflow issues, and no relevant quick actions, do not ask - just end after showing the status with a summary like:

> "Everything looks good! No actions needed."
