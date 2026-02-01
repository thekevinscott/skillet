---
name: watch-archive
description: Watch the archive directory and rebuild on changes
---

Run the archive watcher in the background:

```bash
sh scripts/watch-archive.sh &
```

This watches /Users/carlson/Desktop/ARCHIVE for changes and triggers a site rebuild when files are modified.

Use `/kill` to stop the watcher.
