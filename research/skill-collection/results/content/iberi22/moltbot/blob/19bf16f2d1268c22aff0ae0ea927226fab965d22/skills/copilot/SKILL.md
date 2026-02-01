---
name: copilot
description: "GitHub Copilot in the CLI. Requires GitHub CLI (gh) to be installed."
metadata:
  moltbot:
    emoji: "✈️"
    category: "development"
    requires:
      bins: ["gh"]
    install:
      - id: "node"
        kind: "node"
        package: "@githubnext/github-copilot-cli"
---
