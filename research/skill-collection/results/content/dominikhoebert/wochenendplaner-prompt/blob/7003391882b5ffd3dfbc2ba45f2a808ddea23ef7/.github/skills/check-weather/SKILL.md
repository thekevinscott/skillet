---
name: check-weather
description: Check current weather for a city using wttr.in API
parameters:
  type: object
  properties:
    city:
      type: string
      description: City name to check weather for
  required:
    - city
command: curl -s 'wttr.in/{{city}}?format=3'
---
