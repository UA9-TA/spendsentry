import json
import sqlite3
from datetime import datetime

from spendsentry.config import CONFIG_DIR

DB_PATH = CONFIG_DIR / "spendsentry.db"


def get_connection():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS spend_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            hourly_cost REAL NOT NULL,
            daily_cost REAL NOT NULL,
            provider TEXT NOT NULL,
            raw_json TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS deployment_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            commit_hash TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            spend_at_deploy REAL,
            peak_spend REAL
        )
    """)
    conn.commit()
    conn.close()


def insert_spend_snapshot(
    timestamp: datetime, hourly_cost: float, daily_cost: float, provider: str, raw_json: dict = None
):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO spend_snapshots (timestamp, hourly_cost, daily_cost, provider, raw_json) VALUES (?, ?, ?, ?, ?)",
        (
            timestamp.isoformat(),
            hourly_cost,
            daily_cost,
            provider,
            json.dumps(raw_json) if raw_json else None,
        ),
    )
    conn.commit()
    conn.close()


def get_recent_snapshots(limit=168):  # 7 days * 24 hours
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM spend_snapshots ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows


def insert_deployment(
    commit_hash: str, message: str, timestamp: datetime, spend_at_deploy: float = None
):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO deployment_log (commit_hash, message, timestamp, spend_at_deploy) VALUES (?, ?, ?, ?)",
        (commit_hash, message, timestamp.isoformat(), spend_at_deploy),
    )
    conn.commit()
    conn.close()


def get_recent_deployments(limit=20):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM deployment_log ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows


init_db()
