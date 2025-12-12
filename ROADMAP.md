# Roadmap

Future work and ideas for skillet. Not planned for immediate implementation.

## Under Consideration

### `skillet lint` - Skill package validation ([#20](https://github.com/thekevinscott/skillet/issues/20))

Validate Claude Code skill packages before evaluation. Proposed checks:

- **Schema validation** - YAML frontmatter, required fields, tool name validation
- **Structural checks** - File existence, size limits, secret detection
- **Content quality** - Dead links, markdown lint, whitespace
- **Plugin format** - plugin.json schema validation

```bash
skillet lint ~/.claude/skills/browser-fallback
skillet lint ~/.claude/skills/ --format json --strict
```

### Backup/restore

Save original SKILL.md before tuning, add `--restore` flag.

### Watch mode

Live reload on SKILL.md changes (`skillet watch`).

### Tool mocking

Mock tool responses to test behavioral skills (force WebFetch to fail, etc.).

### Tool usage assertions

Check that Claude called specific tools (or didn't).

## Maybe Someday

### DSPy integration

Use DSPy optimizers for more sophisticated prompt tuning.

### Bayesian optimization

Search instruction/example combinations like MIPROv2.

### Bootstrap examples

Keep passing responses as few-shot examples.

### Synthetic gaps

LLM-generated gaps to pad out the eval set (`skillet generate`).

### Multi-model testing

Run evals across Haiku/Sonnet/Opus to ensure consistency.

### Confidence intervals

Wilson score intervals instead of simple pass rates.
