---
name: fusion-engine
description: Fuse market/news/social into fused_event with title+severity and evidence.
---

## Fusion rules
- Sliding window: 10 minutes
- Dedup: same instrument + title similarity >= 0.85 -> merge
- severity = max(input severities) + bonus for multi-source
- Must output JSON matching docs/event-schema.md
