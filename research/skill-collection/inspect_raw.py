#!/usr/bin/env python3
"""Inspect raw data format in database."""

import sqlite3

conn = sqlite3.connect("data/analyzed/content.db")
cursor = conn.cursor()

# Get a sample
cursor.execute("SELECT url, raw FROM content ORDER BY url LIMIT 1")
url, raw = cursor.fetchone()

print(f"URL: {url}")
print(f"Raw type: {type(raw)}")
print(f"Raw length: {len(raw)}")
print(f"First 100 bytes (hex): {raw[:100].hex()}")
print(f"First 100 bytes (repr): {repr(raw[:100])}")

# Try to decode as plain text
try:
    text = raw.decode("utf-8", errors="replace")
    print("\nDirect UTF-8 decode successful!")
    print(f"Text length: {len(text)} chars")
    print(f"First 500 chars:\n{text[:500]}")
except Exception as e:
    print(f"\nDirect UTF-8 decode failed: {e}")

conn.close()
