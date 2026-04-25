# Remote Environment Workflow

This file applies whenever Claude Code is running in a remote/managed environment (detected via `CLAUDE_CODE_REMOTE=true`). See `agents.md` at the repository root for how the environment is detected.

## Every unit of work needs a GitHub issue

- Before starting any task, ensure there is a GitHub issue that describes the work. If one does not exist, create it.
- The issue is the source of truth for scope. If the work grows beyond the issue, either update the issue or split off additional issues.

## Every unit of work ends with a PR

- All changes must land via a pull request — never push directly to `main`.
- The PR description must reference its issue using a GitHub closing keyword (e.g. `Closes #123`, `Fixes #123`) so the issue is auto-closed when the PR is merged.
- If a single issue requires multiple PRs, use `Refs #123` on the intermediate PRs and `Closes #123` on the final one.

## The PR must be green and mergeable before you stop

A task is not done until **both** of the following are true on the PR:

1. **All CI checks pass.** Watch the checks (e.g. `gh pr checks <number> --watch`) and fix any failures immediately. Do not hand the PR off red.
2. **The PR is in a mergeable state.** No merge conflicts with the base branch, no requested changes blocking merge, branch up to date with base if the repo requires it. If conflicts appear, rebase or merge the base branch in and resolve them.

If you cannot get CI green or cannot resolve conflicts, surface the blocker explicitly rather than leaving the PR in a broken state.
