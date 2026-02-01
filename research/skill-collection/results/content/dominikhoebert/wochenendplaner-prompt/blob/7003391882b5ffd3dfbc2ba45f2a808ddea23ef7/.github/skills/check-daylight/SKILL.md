---
name: check-daylight
description: Check sunrise and sunset times for planning outdoor activities
parameters:
  type: object
  properties:
    city:
      type: string
      description: City name to check daylight hours
  required:
    - city
command: curl -s 'wttr.in/{{city}}?format=%S+%s'
---
