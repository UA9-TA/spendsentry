from datetime import datetime, timezone

import pytest

from spendsentry.storage import get_recent_snapshots, init_db, insert_spend_snapshot


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    monkeypatch.setattr("spendsentry.storage.DB_PATH", tmp_path / "test.db")
    init_db()


def test_storage():
    now = datetime.now(timezone.utc)
    insert_spend_snapshot(now, 1.5, 10.0, "aws", {"test": "data"})

    snapshots = get_recent_snapshots(limit=10)
    assert len(snapshots) == 1
    assert float(snapshots[0]["hourly_cost"]) == 1.5
    assert float(snapshots[0]["daily_cost"]) == 10.0
    assert snapshots[0]["provider"] == "aws"
