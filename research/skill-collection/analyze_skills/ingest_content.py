"""Ingest content files into a SQLite database for fast repeated access.

Reads all content files referenced by files.parquet and stores them in a
single SQLite database. Subsequent pipeline scripts read from SQLite instead
of hitting the filesystem for 385k individual file reads.

Usage:
    python -m analyze_skills.ingest_content [--content-dir PATH] [--files PATH] [--output PATH]

Defaults:
    --content-dir data/content/
    --files       data/github-skill-files/files.parquet
    --output      data/analyzed/content.db
"""

import argparse
import sqlite3
import sys
from pathlib import Path

import polars as pl

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CONTENT_DIR_DEFAULT = _DATA_DIR / "content"
FILES_DEFAULT = _DATA_DIR / "github-skill-files" / "files.parquet"
OUTPUT_DEFAULT = _DATA_DIR / "analyzed" / "content.db"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--content-dir",
        type=Path,
        default=CONTENT_DIR_DEFAULT,
    )
    parser.add_argument(
        "--files",
        type=Path,
        default=FILES_DEFAULT,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DEFAULT,
    )
    args = parser.parse_args()

    content_dir: Path = args.content_dir.expanduser().resolve()
    files_path: Path = args.files
    output: Path = args.output

    if not content_dir.exists():
        print(f"Content directory not found: {content_dir}", file=sys.stderr)
        sys.exit(1)
    if not files_path.exists():
        print(f"Files parquet not found: {files_path}", file=sys.stderr)
        sys.exit(1)

    urls = pl.read_parquet(files_path, columns=["url"])["url"].to_list()
    print(f"Loaded {len(urls):,} URLs from {files_path}")

    output.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(output))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=OFF")
    conn.execute("CREATE TABLE IF NOT EXISTS content (url TEXT PRIMARY KEY, raw BLOB)")

    # Check how many are already ingested
    existing = conn.execute("SELECT COUNT(*) FROM content").fetchone()[0]
    if existing >= len(urls):
        print(f"Already have {existing:,} rows (>= {len(urls):,} URLs). Nothing to do.")
        conn.close()
        return

    # Batch insert
    batch_size = 5000
    inserted = 0
    skipped = 0
    for i in range(0, len(urls), batch_size):
        batch = urls[i : i + batch_size]
        rows = []
        for url in batch:
            rel = url.replace("https://github.com/", "")
            path = content_dir / rel
            if path.exists():
                try:
                    rows.append((url, path.read_bytes()))
                except OSError:
                    skipped += 1
            else:
                skipped += 1
        conn.executemany("INSERT OR IGNORE INTO content (url, raw) VALUES (?, ?)", rows)
        conn.commit()
        inserted += len(rows)
        if (i // batch_size) % 10 == 0:
            print(
                f"  {inserted:,} inserted, {skipped:,} skipped "
                f"({100 * (i + len(batch)) / len(urls):.0f}%)...",
                flush=True,
            )

    conn.execute("PRAGMA optimize")
    conn.close()
    db_size = output.stat().st_size / 1024 / 1024
    print(f"Done. {inserted:,} files in {output} ({db_size:.0f} MB)")


if __name__ == "__main__":
    main()
