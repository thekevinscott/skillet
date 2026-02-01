---
name: beautiful-reader
description: Use when the user wants to read some markdown in a beautiful way
license: MIT
compatibility: opencode
metadata:
  audience: tools
---

# View a markdown file
beautiful-reader README.md

# Pipe from stdin
cat README.md | beautiful-reader

# Options
beautiful-reader README.md --theme dark --fullscreen