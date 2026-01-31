---
description: Address PR review feedback by fixing issues and resolving comment threads
allowed-tools: Bash, Read, Grep, Glob, Edit, Write, AskUserQuestion
---

Address PR code review feedback systematically. Fetch both review threads (line comments) and general PR comments (issue comments), evaluate each, make fixes, and resolve/reply as appropriate.

## Process

### For review threads (line-specific comments)

1. **Mark as in-progress**
   - Add 👀 reaction to the comment to signal you're working on it
   - Use the comment's `databaseId` with the REST API

2. **Evaluate the comment**
   - Understand what's being suggested
   - Determine if the feedback is valid
   - Add 👍 reaction if you agree with the feedback
   - Add 👎 reaction if you disagree
   - If valid: proceed to step 3
   - If you disagree: Use AskUserQuestion to present options:
     - Accept the feedback anyway
     - Push back with reasoning (explain why in the reply)
     - Skip this comment for now

3. **Make the change**
   - Implement the requested fix
   - Follow the codebase's existing patterns

4. **Test the change**
   - Run relevant tests or verify the fix works
   - Ensure no regressions

5. **Commit**
   - Create a commit with a descriptive message
   - Reference the PR in the commit if appropriate

6. **Push to branch**
   - Push the changes to the PR branch

7. **Reply to the reviewer**
   - Reply to the comment thread explaining what was changed
   - Always link to the commit SHA (e.g., "Fixed in abc1234")

8. **Remove the 👀 reaction**
   - Remove the eyes reaction now that you've addressed and replied

9. **Resolve the thread**
   ```bash
   gh api graphql -f query='
   mutation($threadId: ID!) {
     resolveReviewThread(input: { threadId: $threadId }) {
       thread { isResolved }
     }
   }' -f threadId='THREAD_ID'
   ```

10. **Move to next comment**

### For general PR comments (issue comments)

General PR comments cannot be "resolved" like review threads. Handle them as follows:

1. **Mark as in-progress**
   - Add 👀 reaction to the comment to signal you're working on it
   - Use the comment's database ID with the REST API

2. **Evaluate the comment**
   - Determine if it's actionable feedback, a question, or just a note
   - Add 👍 reaction if you agree with the feedback
   - Add 👎 reaction if you disagree
   - If actionable: proceed to step 3
   - If a question: answer it by replying
   - If just acknowledgment/note: no action needed

3. **Make any requested changes** (if applicable)
   - Same process as review threads: fix, test, commit, push

4. **Reply to the comment**
   - Post a new PR comment that clearly references the original (e.g., by quoting or linking it)
   - Always link to the commit SHA (e.g., "Fixed in abc1234")
   - Use the REST API to create this new comment on the same pull request

5. **Remove the 👀 reaction**
   - Remove the eyes reaction now that you've addressed and replied

## Getting Started

### Determine the PR number

If not provided, get it from the current branch:
```bash
gh pr view --json number -q '.number'
```

### Fetch unresolved review threads

First get the owner and repo separately:
```bash
OWNER=$(gh repo view --json owner -q '.owner.login')
REPO=$(gh repo view --json name -q '.name')
PR_NUMBER=$(gh pr view --json number -q '.number')
```

Then fetch review threads:
```bash
gh api graphql -f query='
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          isOutdated
          path
          line
          comments(first: 10) {
            nodes {
              id
              databaseId
              body
              author { login }
              createdAt
            }
          }
        }
      }
    }
  }
}' -f owner="$OWNER" -f repo="$REPO" -F number="$PR_NUMBER"
```

### Fetch general PR comments (issue comments)

These are comments on the PR itself, not on specific lines of code:
```bash
gh api repos/$OWNER/$REPO/issues/$PR_NUMBER/comments
```

Or using GraphQL:
```bash
gh api graphql -f query='
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      comments(first: 100) {
        nodes {
          id
          databaseId
          body
          author { login }
          createdAt
        }
      }
    }
  }
}' -f owner="$OWNER" -f repo="$REPO" -F number="$PR_NUMBER"
```

### Add reactions to a comment

Reaction values: `eyes`, `+1`, `-1`, `laugh`, `confused`, `heart`, `hooray`, `rocket`

**Note:** Use the numeric `databaseId` from the GraphQL response, not the GraphQL node `id`.

For review thread comments:
```bash
# COMMENT_DATABASE_ID is the numeric databaseId (e.g., 2724647402)
gh api repos/$OWNER/$REPO/pulls/comments/$COMMENT_DATABASE_ID/reactions -f content='eyes'
gh api repos/$OWNER/$REPO/pulls/comments/$COMMENT_DATABASE_ID/reactions -f content='+1'
gh api repos/$OWNER/$REPO/pulls/comments/$COMMENT_DATABASE_ID/reactions -f content='-1'
```

For general PR comments:
```bash
gh api repos/$OWNER/$REPO/issues/comments/$COMMENT_DATABASE_ID/reactions -f content='eyes'
gh api repos/$OWNER/$REPO/issues/comments/$COMMENT_DATABASE_ID/reactions -f content='+1'
gh api repos/$OWNER/$REPO/issues/comments/$COMMENT_DATABASE_ID/reactions -f content='-1'
```

### Remove 👀 reaction from a comment

First, get the reaction ID:
```bash
# For review thread comments
gh api repos/$OWNER/$REPO/pulls/comments/$COMMENT_DATABASE_ID/reactions

# For general PR comments
gh api repos/$OWNER/$REPO/issues/comments/$COMMENT_DATABASE_ID/reactions
```

Then delete the reaction:
```bash
gh api -X DELETE repos/$OWNER/$REPO/issues/comments/$COMMENT_DATABASE_ID/reactions/$REACTION_ID
# or for pull request review comments:
gh api -X DELETE repos/$OWNER/$REPO/pulls/comments/$COMMENT_DATABASE_ID/reactions/$REACTION_ID
```

### Reply to a general PR comment

GitHub issue comments don't support threading. Post a new comment that references the original:
```bash
gh api repos/$OWNER/$REPO/issues/$PR_NUMBER/comments -f body='> Original comment quote

Your reply here'
```

### Reply to a review thread

```bash
gh api graphql -f query='
mutation($threadId: ID!, $body: String!) {
  addPullRequestReviewThreadReply(input: {
    pullRequestReviewThreadId: $threadId,
    body: $body
  }) {
    comment { id }
  }
}' -f threadId='PRRT_...' -f body='Fixed in latest commit'
```

## Guidelines

- Fetch both review threads AND general PR comments
- Process comments one at a time for clarity
- Read the relevant file before making changes
- Keep commits focused on individual feedback items
- Be respectful when disagreeing with feedback
- Skip already-resolved or outdated threads
- Report progress: "Fixed 3/5 review threads, addressed 2 PR comments, 1 skipped"

## Edge Cases

- **No feedback**: Report "No unresolved review threads or PR comments to address"
- **Outdated threads**: Skip with note "Thread is outdated (code has changed)"
- **Cannot fix**: Ask user how to proceed
- **Test failures**: Stop and report the issue before continuing
- **Bot comments**: Skip automated comments from bots (e.g., CI status, coverage reports)
- **Stale PR comments**: If a general comment has already been addressed in a later commit, note this in your reply
