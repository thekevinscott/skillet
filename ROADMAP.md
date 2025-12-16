# Roadmap

## Completed

- Single eval file support (`skillet eval ./evals/my-skill/001.yaml`)
- Skip cache flag (`skillet eval my-skill --skip-cache`)

## Planned

### Standalone cache management command

Add `skillet cache` command for cache inspection and management:

```bash
skillet cache list                     # list all cached evals
skillet cache clear my-skill           # clear cache for eval
skillet cache clear my-skill --skill   # clear only skill cache, keep baseline
skillet cache info my-skill            # show cache size/stats
```

### Eval filtering with regex/glob patterns

Support filtering evals by pattern:

```bash
skillet eval ./evals/add-command/ --filter "001-*"
skillet eval ./evals/add-command/ --filter "*ask*"
```

