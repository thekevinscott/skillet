---
name: hello
description: hello world
context: fork
agent: search-summarizer
user-invocable: true
allowed-tools:
  - WebSearch
  - Write
  - Edit
  - Bash
---

# Workflow

1. run `sleep 3s`
2. `{search_result}`: search about $ARGUMENTS
3. append `{search_result}` to result.txt
4. run `echo DONE`
