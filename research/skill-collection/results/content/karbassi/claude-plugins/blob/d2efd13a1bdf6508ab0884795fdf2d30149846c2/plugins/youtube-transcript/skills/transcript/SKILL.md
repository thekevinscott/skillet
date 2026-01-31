---
description: Fetch and present transcripts from YouTube videos
allowed-tools: Bash(yt-dlp:*), Read
---

Fetch, process, and present transcripts from YouTube videos using yt-dlp.

## Extract Video ID

From the URL or use provided ID directly:
- Full URL: `https://www.youtube.com/watch?v=VIDEO_ID`
- Short: `https://youtu.be/VIDEO_ID`
- Direct ID: Use as-is (e.g., "HwLaKBHIT7w")

## Fetch Transcript

**Primary approach** - Auto-generated English captions:
```bash
yt-dlp --write-auto-sub --skip-download --sub-lang en --output "/tmp/%(id)s" "https://www.youtube.com/watch?v=VIDEO_ID"
```
Then read `/tmp/VIDEO_ID.en.vtt` (or `.srt`).

**Fallback** - Manual captions:
```bash
yt-dlp --write-sub --skip-download --sub-lang en --output "/tmp/%(id)s" "https://www.youtube.com/watch?v=VIDEO_ID"
```

**List available languages** if English unavailable:
```bash
yt-dlp --list-subs "https://www.youtube.com/watch?v=VIDEO_ID"
```

## Process and Present

1. Read the subtitle file
2. Remove duplicate lines and clean up timestamps
3. Provide a brief summary of the video content
4. Format for easy reading

## Error Handling

- **No captions**: Inform the user clearly
- **Age-restricted**: Explain the limitation
- **Geo-blocked/Private/Deleted**: Notify the user

## Process

1. Extract video ID from the provided URL
2. Run the fetch command immediately
3. Read and clean up the transcript
4. Present with a brief summary
