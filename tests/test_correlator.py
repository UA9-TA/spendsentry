from datetime import datetime, timezone

from spendsentry.correlator import correlate_spike_to_commit


def test_correlate_spike_to_commit():
    now = datetime(2023, 5, 14, 1, 0, 0, tzinfo=timezone.utc)

    commits = [
        {
            "hash": "abc",
            "timestamp": datetime(2023, 5, 14, 0, 30, 0, tzinfo=timezone.utc),
            "message": "feat: add image processor",
        },
        {
            "hash": "def",
            "timestamp": datetime(2023, 5, 13, 14, 0, 0, tzinfo=timezone.utc),
            "message": "fix: update dependencies",
        },
    ]

    culprit = correlate_spike_to_commit(now, commits)

    assert culprit is not None
    assert culprit["hash"] == "abc"


def test_correlate_spike_no_commits():
    now = datetime.now(timezone.utc)
    assert correlate_spike_to_commit(now, []) is None
