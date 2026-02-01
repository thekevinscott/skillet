---
name: music
description: Toggle background music loop
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/skills/music/scripts/*)
---

# Music Control

Toggle background music on/off. Run:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/music/scripts/toggle.sh
```

Output:
- If started: "Music: PLAYING"
- If stopped: "Music: STOPPED"
