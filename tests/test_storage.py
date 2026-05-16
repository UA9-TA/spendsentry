import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from spendsentry.storage import Storage


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    yield Path(path)
    os.unlink(path)


def test_add_and_get_snapshot(temp_db):
    storage = Storage(db_path=temp_db)
    now = datetime.now(timezone.utc)

    storage.add_spend_snapshot(now, 1.5, 30.0, "aws", {"foo": "bar"})
    snapshots = storage.get_recent_snapshots(limit=10)

    assert len(snapshots) == 1
    assert snapshots[0][1] == 1.5
    assert snapshots[0][2] == 30.0


def test_deployment_log(temp_db):
    storage = Storage(db_path=temp_db)
    now = datetime.now(timezone.utc)

    storage.add_deployment("abc1234", "test commit", now, 1.0)
    storage.update_deployment_peak("abc1234", 2.5)

    deps = storage.get_deployments()
    assert len(deps) == 1
    assert deps[0][0] == "abc1234"
    assert deps[0][3] == 1.0
    assert deps[0][4] == 2.5
