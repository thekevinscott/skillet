#!/usr/bin/env python3
"""Check database content format."""

import sqlite3
import zlib

conn = sqlite3.connect("data/analyzed/content.db")
cursor = conn.cursor()

# Get schema
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
print("Schema:")
print(cursor.fetchone()[0])
print()

# Get total count
cursor.execute("SELECT COUNT(*) FROM content")
print(f"Total skills: {cursor.fetchone()[0]}")

# Try different offset ranges
for offset in [0, 50, 100, 150, 200]:
    print(f"\n--- Testing OFFSET {offset} ---")
    cursor.execute(f"SELECT url, raw FROM content ORDER BY url LIMIT 5 OFFSET {offset}")
    rows = cursor.fetchall()

    success_count = 0
    for url, raw in rows:
        try:
            text = zlib.decompress(raw).decode("utf-8", errors="replace")
            success_count += 1
            print(f"✓ {url[:80]} ({len(text)} chars)")
        except Exception as e:
            print(f"✗ {url[:80]}: {e}")

    print(f"Success rate: {success_count}/{len(rows)}")

conn.close()
