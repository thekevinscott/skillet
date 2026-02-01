---
name: explore-task
description: Template for explore agent task delegation
---

```jinja2
{# search_scope: one of "quick", "medium", or "very thorough" #}

**Goal:** {{goal|required}}

**Search Scope:** {{search_scope|required}}

**Questions to Answer:**
{{questions|required|multiline}}
```
