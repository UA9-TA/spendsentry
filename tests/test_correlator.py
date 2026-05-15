from datetime import datetime
from pathlib import Path

from spendsentry.correlator import find_culprit_commit

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_correlator():
    # Mock get_recent_commits to read from fixture
    commits = []
    with open(FIXTURES_DIR / "sample_git_log.txt") as f:
        for line in f:
            parts = line.strip().split(" ", 2)
            if len(parts) >= 3:
                commits.append(
                    {
                        "hash": parts[0],
                        "timestamp": datetime.fromisoformat(parts[1]),
                        "message": parts[2],
                    }
                )

    # Spike started at 09:00:00. The commit right before this is 08:31:00
    spike_started_at = datetime.fromisoformat("2023-10-25T09:00:00+00:00")
    culprit = find_culprit_commit(spike_started_at, commits)

    assert culprit is not None
    assert culprit["hash"] == "abc1234"
    assert culprit["message"] == "feat: add image processor"
