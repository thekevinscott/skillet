# YouTube Skill

Ingest YouTube video transcripts into memory.

## Actions

- `ingest` — Fetch and store video transcript
- `info` — Get video metadata

## Usage

```python
skill.execute("ingest", url="https://youtube.com/watch?v=...")
skill.execute("info", url="https://youtube.com/watch?v=...")
```
