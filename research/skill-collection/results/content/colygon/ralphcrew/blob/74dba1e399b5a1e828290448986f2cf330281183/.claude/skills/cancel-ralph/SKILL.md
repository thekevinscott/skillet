# Cancel Ralph Skill

Cancel an active Ralph Wiggum loop.

## Triggers

- User runs `/cancel-ralph`
- User says "cancel ralph" or "stop the ralph loop"

## When Invoked

Delete the ralph loop state file:

```bash
rm -f .claude/ralph-loop.local.md
```

Then confirm to the user that the Ralph loop has been cancelled.
