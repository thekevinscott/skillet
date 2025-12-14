# Roadmap

## Completed

- Single eval file support (`skillet eval ./evals/my-skill/001.yaml`)

## Planned

### Eval filtering with regex/glob patterns

Support filtering evals by pattern:

```bash
skillet eval ./evals/add-command/ --filter "001-*"
skillet eval ./evals/add-command/ --filter "*ask*"
```

