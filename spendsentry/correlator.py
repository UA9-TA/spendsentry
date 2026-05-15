import subprocess
from datetime import datetime


def get_recent_commits(n=20):
    try:
        # Format: %H (hash) %ai (author date, ISO 8601-like format) %s (subject)
        result = subprocess.run(
            ["git", "log", "--format=%H %aI %s", "-n", str(n)],
            capture_output=True,
            text=True,
            check=True,
        )
        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split(" ", 2)
            if len(parts) >= 3:
                commits.append(
                    {
                        "hash": parts[0],
                        "timestamp": datetime.fromisoformat(parts[1]),
                        "message": parts[2],
                    }
                )
        return commits
    except subprocess.CalledProcessError:
        return []
    except Exception:
        return []


def find_culprit_commit(spike_started_at: datetime, commits=None):
    if not commits:
        commits = get_recent_commits()

    # Find the most recent commit before the spike started
    culprit = None
    for commit in commits:
        if commit["timestamp"] <= spike_started_at:
            if culprit is None or commit["timestamp"] > culprit["timestamp"]:
                culprit = commit

    return culprit
