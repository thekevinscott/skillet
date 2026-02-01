# Skill: pdf-extract
## Goal
Extract exhibitor/company tables or contact blocks from PDFs (catalogs, lists).

## Inputs
- data/inputs/**/*.pdf

## Outputs
- staging/pdf_extract.parquet (row-level)
- outputs/pdf_extract_report.md

## Tools
- pdfplumber first (text + table heuristics)
- camelot only if needed and PDF is tabular (archived project risk)
