---
name: cloud-deploy
description: Cloud deployment automation
metadata:
  pryx:
    emoji: "☁️"
    requires:
      bins: ["kubectl", "aws"]
      env: ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
---

# Cloud Deploy

Automates cloud deployments to Kubernetes and AWS.
