---
name: social-monitor
description: Build social monitor module with filters/export/notifications and urgency scoring.
---

## Must implement
- /social-monitor/posts (filters)
- /social-monitor/trends
- /social-monitor/stats
- /social-monitor/keywords
- /social-monitor/notifications (CRUD)

## Push rule
If urgency>=7 or severity>=70, must emit fused_event and notify.
