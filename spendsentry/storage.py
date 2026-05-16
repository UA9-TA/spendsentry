import json
import sqlite3
from datetime import datetime
from pathlib import Path

from spendsentry.config import get_config_dir


def get_db_path() -> Path:
    return get_config_dir() / "spendsentry.db"


class Storage:
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or get_db_path()
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spend_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    hourly_cost REAL,
                    daily_cost REAL,
                    provider TEXT,
                    raw_json TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS deployment_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    commit_hash TEXT,
                    message TEXT,
                    timestamp TEXT,
                    spend_at_deploy REAL,
                    peak_spend REAL
                )
            """)
            conn.commit()

    def add_spend_snapshot(
        self,
        timestamp: datetime,
        hourly_cost: float,
        daily_cost: float,
        provider: str,
        raw_data: dict,
    ):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO spend_snapshots (timestamp, hourly_cost, daily_cost, provider, raw_json) VALUES (?, ?, ?, ?, ?)",
                (timestamp.isoformat(), hourly_cost, daily_cost, provider, json.dumps(raw_data)),
            )
            conn.commit()

    def add_deployment(
        self, commit_hash: str, message: str, timestamp: datetime, spend_at_deploy: float
    ):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO deployment_log (commit_hash, message, timestamp, spend_at_deploy, peak_spend) VALUES (?, ?, ?, ?, ?)",
                (commit_hash, message, timestamp.isoformat(), spend_at_deploy, spend_at_deploy),
            )
            conn.commit()

    def update_deployment_peak(self, commit_hash: str, new_peak: float):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE deployment_log SET peak_spend = ? WHERE commit_hash = ? AND peak_spend < ?",
                (new_peak, commit_hash, new_peak),
            )
            conn.commit()

    def get_recent_snapshots(self, limit=168):
        # Default to roughly 7 days of hourly data
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT timestamp, hourly_cost, daily_cost FROM spend_snapshots ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            )
            return cursor.fetchall()

    def get_deployments(self, limit=20):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT commit_hash, message, timestamp, spend_at_deploy, peak_spend FROM deployment_log ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            )
            return cursor.fetchall()
