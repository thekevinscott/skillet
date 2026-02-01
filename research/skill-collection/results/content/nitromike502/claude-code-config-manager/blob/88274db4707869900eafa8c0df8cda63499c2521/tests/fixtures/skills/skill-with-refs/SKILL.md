---
name: skill-with-refs
description: Skill with external file references for testing external reference detection
allowed-tools:
  - bash
---

This skill references external files:
- Absolute path: /home/user/external/file.txt
- Home directory: ~/shared/script.py
- Parent escape: ../../shared/data.json
