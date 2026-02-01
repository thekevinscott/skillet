# Skill: fair-exhibitors
## Goal
Collect exhibitor lists from trade fair directories/PDFs and normalize into lead records.

## Inputs
- config/sources.yaml (fair endpoints, pdf links)
- policies.yaml

## Outputs
- staging/fairs_exhibitors.parquet
- logs/fairs.log

## Notes
Prefer public exhibitor pages and PDFs. Respect robots and rate limits.
