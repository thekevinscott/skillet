"""Scan skill content files and extract structural features to parquet.

Reads content from the SQLite database (built by ingest_content) and
computes per-file metrics: byte size, word/line/paragraph counts, markdown
structure, frontmatter fields.

Usage:
    python -m analyze_skills.extract_features [--db PATH] [--output PATH]

Defaults:
    --db      data/analyzed/content.db
    --output  data/analyzed/content_features.parquet
"""

import argparse
import hashlib
import re
import sqlite3
import sys
from pathlib import Path

import polars as pl

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_DEFAULT = _DATA_DIR / "analyzed" / "content.db"
OUTPUT_DEFAULT = _DATA_DIR / "analyzed" / "content_features.parquet"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
HEADING_RE = re.compile(r"^(#{1,6})\s", re.MULTILINE)
CODE_BLOCK_RE = re.compile(r"^```", re.MULTILINE)
URL_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
YAML_KEY_RE = re.compile(r"^(\w[\w_-]*):", re.MULTILINE)


def extract_features(url: str, raw: bytes) -> dict:
    """Extract structural features from a single skill file."""
    byte_size = len(raw)
    content_hash = hashlib.sha256(raw).hexdigest()

    try:
        text = raw.decode("utf-8", errors="replace")
    except Exception:
        text = ""

    # Normalized hash: strip frontmatter, collapse whitespace
    normalized = FRONTMATTER_RE.sub("", text.lstrip(), count=1)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    normalized_hash = hashlib.sha256(normalized.encode()).hexdigest()

    # Basic counts
    words = len(text.split())
    # Split on ``` fences: even-indexed parts are prose, odd-indexed are code
    _parts = CODE_BLOCK_RE.split(text)
    _prose = " ".join(_parts[::2])
    prose_words = len(_prose.split())
    code_words = words - prose_words
    lines = text.count("\n") + 1 if text else 0
    # Counts blank-line-separated blocks, including code blocks and headings
    paragraphs = len([b for b in re.split(r"\n\s*\n", text) if b.strip()])

    # Heading analysis
    headings = HEADING_RE.findall(text)
    heading_count = len(headings)
    max_heading_depth = max((len(h) for h in headings), default=0)

    # Code blocks (``` pairs)
    # Assumes balanced fences. Odd fence count -> last block uncounted.
    code_fences = len(CODE_BLOCK_RE.findall(text))
    code_block_count = code_fences // 2

    # URL count
    url_count = len(URL_RE.findall(text))

    # Frontmatter
    has_frontmatter = text.lstrip().startswith("---")
    frontmatter_fields: list[str] = []
    if has_frontmatter:
        fm_match = FRONTMATTER_RE.match(text.lstrip())
        if fm_match:
            fm_text = fm_match.group(1)
            frontmatter_fields = YAML_KEY_RE.findall(fm_text)

    return {
        "url": url,
        "content_hash": content_hash,
        "normalized_hash": normalized_hash,
        "bytes": byte_size,
        "words": words,
        "prose_words": prose_words,
        "code_words": code_words,
        "lines": lines,
        "paragraphs": paragraphs,
        "heading_count": heading_count,
        "max_heading_depth": max_heading_depth,
        "code_block_count": code_block_count,
        "url_count": url_count,
        "has_frontmatter": has_frontmatter,
        "frontmatter_fields": frontmatter_fields,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db",
        type=Path,
        default=DB_DEFAULT,
        help=f"SQLite content database (default: {DB_DEFAULT})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DEFAULT,
        help=f"Output parquet path (default: {OUTPUT_DEFAULT})",
    )
    args = parser.parse_args()

    db_path: Path = args.db
    output: Path = args.output

    if not db_path.exists():
        print(f"Content database not found: {db_path}", file=sys.stderr)
        print("Run `python -m analyze_skills.ingest_content` first.", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(str(db_path))
    total = conn.execute("SELECT COUNT(*) FROM content").fetchone()[0]
    print(f"Reading {total:,} files from {db_path}")

    rows: list[dict] = []
    cursor = conn.execute("SELECT url, raw FROM content")
    for i, (url, raw) in enumerate(cursor):
        if i % 50_000 == 0:
            print(f"  Processing {i:,}/{total:,} ({100 * i / total:.0f}%)...", flush=True)
        result = extract_features(url, raw)
        rows.append(result)

    conn.close()
    print(f"Extracted features from {len(rows):,} files")

    df = pl.DataFrame(rows)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(output)
    print(f"Wrote {output} ({output.stat().st_size / 1024 / 1024:.1f} MB)")
    print(f"Schema: {df.schema}")


if __name__ == "__main__":
    main()
