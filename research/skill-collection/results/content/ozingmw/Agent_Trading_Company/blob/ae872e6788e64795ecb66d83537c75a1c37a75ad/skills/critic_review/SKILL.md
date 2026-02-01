---
name: critic_review
description: Review an analyst signal and recommend approve/reject.
---

Inputs:
- confidence: number

Rules:
- If confidence < 0.3 -> REJECT
- Else -> APPROVE

Return JSON:
{
  "recommendation": "APPROVE"|"REJECT",
  "notes": string
}
