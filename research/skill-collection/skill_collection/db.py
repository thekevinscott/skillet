"""SQLite database module for skill collection.

Provides schema definition and connection management for the v2 collection pipeline.
"""

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).parent.parent / "results" / "skills.db"

SCHEMA = """
-- Shard tracking for resumable collection
CREATE TABLE IF NOT EXISTS shards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT UNIQUE NOT NULL,
    total_count INTEGER,
    collected INTEGER DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Discovered files (dedupe by SHA)
CREATE TABLE IF NOT EXISTS skills (
    sha TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    shard_id INTEGER REFERENCES shards(id)
);

-- Content storage (in DB, not filesystem)
CREATE TABLE IF NOT EXISTS content (
    sha TEXT PRIMARY KEY REFERENCES skills(sha),
    body TEXT NOT NULL,
    byte_size INTEGER,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Validation results
CREATE TABLE IF NOT EXISTS validations (
    sha TEXT PRIMARY KEY REFERENCES skills(sha),
    is_valid BOOLEAN,
    reason TEXT,
    model_version TEXT,
    validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_skills_shard ON skills(shard_id);
CREATE INDEX IF NOT EXISTS idx_validations_is_valid ON validations(is_valid);
"""


def get_db(db_path: Path | None = None) -> sqlite3.Connection:
    """Get a database connection.

    Returns a connection with row_factory set to sqlite3.Row for dict-like access.
    """
    path = db_path or DEFAULT_DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_db_context(db_path: Path | None = None) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database connections with automatic commit/rollback."""
    conn = get_db(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Path | None = None) -> Path:
    """Initialize the database with the schema.

    Creates the database file and tables if they don't exist.
    Returns the path to the database file.
    """
    path = db_path or DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = get_db(path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()

    return path


def get_stats(db_path: Path | None = None) -> dict:
    """Get basic statistics from the database."""
    with get_db_context(db_path) as conn:
        stats = {}

        # Shard counts
        row = conn.execute(
            "SELECT COUNT(*) as total, "
            "COALESCE(SUM(CASE WHEN completed_at IS NOT NULL THEN 1 ELSE 0 END), 0) as completed "
            "FROM shards"
        ).fetchone()
        stats["shards_total"] = row["total"]
        stats["shards_completed"] = row["completed"]

        # Skill counts
        row = conn.execute("SELECT COUNT(*) as count FROM skills").fetchone()
        stats["skills_total"] = row["count"]

        # Content counts
        row = conn.execute("SELECT COUNT(*) as count FROM content").fetchone()
        stats["content_fetched"] = row["count"]

        # Validation counts
        row = conn.execute(
            "SELECT COUNT(*) as total, "
            "COALESCE(SUM(CASE WHEN is_valid = 1 THEN 1 ELSE 0 END), 0) as valid "
            "FROM validations"
        ).fetchone()
        stats["validations_total"] = row["total"]
        stats["validations_valid"] = row["valid"]

        return stats
