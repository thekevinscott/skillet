---
name: greet
description: Greets a person with a friendly message including the current date and time
parameters:
  name:
    type: string
    description: The name of the person to greet
    required: true
---

# Greet Skill

A simple test skill that greets people with the current timestamp.

## Usage

```python
result = execute({'name': 'Randy'})
```
