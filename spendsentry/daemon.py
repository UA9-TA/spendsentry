import logging
import os
import signal
import sys
import time
from datetime import datetime, timezone

import schedule

from spendsentry.alerter import send_alert
from spendsentry.config import get_config
from spendsentry.correlator import find_culprit_commit
from spendsentry.providers.aws import AWSSpendProvider
from spendsentry.storage import get_recent_snapshots, insert_deployment, insert_spend_snapshot
from spendsentry.velocity import calculate_velocity

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

PID_FILE = os.path.expanduser("~/.spendsentry/daemon.pid")


class SpendsentryDaemon:
    def __init__(self):
        config = get_config()
        provider_name = config.get("cloud", {}).get("provider", "aws")

        if provider_name == "aws":
            self.provider = AWSSpendProvider()
        else:
            raise ValueError(f"Unsupported provider: {provider_name}")

        self.limits = config.get("limits", {})
        self.last_alert_time = None

    def poll(self):
        logger.info("Polling spend data...")
        try:
            spend_data = self.provider.get_current_spend()

            insert_spend_snapshot(
                timestamp=spend_data.timestamp,
                hourly_cost=spend_data.hourly_cost,
                daily_cost=spend_data.daily_cost,
                provider="aws",
                raw_data=spend_data.raw_data,
            )

            # Analyze velocity
            snapshots = get_recent_snapshots(limit=168)
            velocity = calculate_velocity(snapshots)

            if velocity.is_spiking:
                self.handle_spike(spend_data, velocity)

        except Exception as e:
            logger.error(f"Error during polling: {e}")

    def handle_spike(self, spend_data, velocity):
        # Rate limit alerts (1 per 30 minutes)
        now = datetime.now(timezone.utc)
        if self.last_alert_time and (now - self.last_alert_time).total_seconds() < 1800:
            logger.info("Spike detected, but alert suppressed due to rate limiting.")
            return

        culprit = find_culprit_commit(velocity.spike_started_at)

        msg = (
            f"🚨 SPEND SPIKE DETECTED 🚨\n"
            f"Current hourly rate: ${velocity.current_hourly_rate:.2f}/hr "
            f"({velocity.acceleration_factor:.1f}x baseline)\n"
        )

        if culprit:
            msg += f"Probable cause: {culprit['hash'][:7]} - {culprit['message']}\n"
            # Log deployment spike correlation
            insert_deployment(
                culprit["hash"],
                culprit["message"],
                culprit["timestamp"],
                velocity.baseline_hourly_rate,
            )
        else:
            msg += "Probable cause: Unknown (no recent commits found)\n"

        msg += "Recommendation: Rollback recent deployment or investigate immediately."

        send_alert(msg)
        self.last_alert_time = now

    def run(self):
        logger.info("Starting SpendSentry daemon...")
        self.poll()  # Run once immediately
        schedule.every(5).minutes.do(self.poll)

        while True:
            schedule.run_pending()
            time.sleep(1)


def start_daemon():
    if os.path.exists(PID_FILE):
        print("Daemon is already running or PID file exists.")
        return

    pid = os.fork()
    if pid > 0:
        sys.exit(0)

    # Decouple from parent environment
    os.setsid()

    # Fork second time
    pid = os.fork()
    if pid > 0:
        sys.exit(0)

    # Write PID of the actual daemon process
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))
    print(f"Daemon started with PID {os.getpid()}")

    daemon = SpendsentryDaemon()
    daemon.run()


def stop_daemon():
    if not os.path.exists(PID_FILE):
        print("Daemon is not running.")
        return

    with open(PID_FILE, "r") as f:
        pid = int(f.read().strip())

    try:
        os.kill(pid, signal.SIGTERM)
        print("Daemon stopped.")
    except ProcessLookupError:
        print("Daemon process not found. Removing stale PID file.")
    finally:
        os.remove(PID_FILE)


def status_daemon():
    if os.path.exists(PID_FILE):
        with open(PID_FILE, "r") as f:
            pid = f.read().strip()
        print(f"Daemon is running (PID {pid}).")
    else:
        print("Daemon is not running.")
