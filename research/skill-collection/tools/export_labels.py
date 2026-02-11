"""Export labeled examples from labels.db to JSON for prompt optimization."""

import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "analyzed" / "labels.db"
DEFAULT_OUTPUT = "/tmp/skill-labels.json"


def main():
    output_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUTPUT

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM tags ORDER BY name")
    labels = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT selected_text, tag FROM labels ORDER BY id")
    examples = [{"text": row[0], "tag": row[1]} for row in cursor.fetchall()]

    conn.close()

    data = {
        "task": "Classify sections of SKILL.md files into anatomy categories",
        "labels": labels,
        "examples": examples,
    }

    Path(output_path).write_text(json.dumps(data, indent=2))
    print(f"Exported {len(examples)} examples with {len(labels)} labels to {output_path}")


if __name__ == "__main__":
    main()
