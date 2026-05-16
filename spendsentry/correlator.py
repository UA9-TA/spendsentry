import subprocess
from datetime import datetime


def get_recent_commits(limit=20):
    """Returns a list of recent commits: [{'hash': str, 'timestamp': datetime, 'message': str}]"""
    try:
        # Get recent git commits: %H=hash, %ai=author date, %s=subject
        output = subprocess.check_output(
            ["git", "log", "--format=%H|%ai|%s", "-n", str(limit)],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return []

    commits = []
    for line in output.strip().split("\n"):
        if not line:
            continue
        parts = line.split("|", 2)
        if len(parts) == 3:
            commit_hash, date_str, message = parts
            try:
                # e.g. 2023-05-15 14:31:00 +0000
                timestamp = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S %z")
                commits.append({"hash": commit_hash, "timestamp": timestamp, "message": message})
            except ValueError:
                pass
    return commits


def correlate_spike_to_commit(spike_started_at: datetime, commits: list):
    """Finds the most recent commit before the spike started."""
    if not commits:
        return None

    # Sort commits by timestamp descending (newest first)
    sorted_commits = sorted(commits, key=lambda c: c["timestamp"], reverse=True)

    for commit in sorted_commits:
        # Compare timestamps (assuming both are timezone aware or both naive)
        # Using simple string comparison for ISO format or convert if needed
        # Assuming spike_started_at is timezone aware
        if commit["timestamp"] <= spike_started_at:
            return commit

    return None
