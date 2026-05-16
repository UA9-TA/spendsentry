import logging
import time
from datetime import datetime, timezone

import schedule

from spendsentry.alerter import format_alert_message, send_slack_alert, send_telegram_alert
from spendsentry.config import load_config
from spendsentry.correlator import correlate_spike_to_commit, get_recent_commits
from spendsentry.providers.aws import AWSProvider
from spendsentry.storage import Storage
from spendsentry.velocity import calculate_velocity

logger = logging.getLogger(__name__)


def run_check():
    config = load_config()
    storage = Storage()

    # Init provider
    provider_name = config.get("provider", {}).get("name", "aws")
    if provider_name == "aws":
        provider = AWSProvider()
    else:
        logger.error(f"Unsupported provider: {provider_name}")
        return

    try:
        current_hourly = provider.get_current_hourly_spend()
        spend_today = provider.get_todays_spend()
    except Exception as e:
        logger.error(f"Error fetching spend data: {e}")
        return

    now = datetime.now(timezone.utc)
    storage.add_spend_snapshot(now, current_hourly, spend_today, provider_name, {})

    # Velocity calculation
    recent_snapshots = storage.get_recent_snapshots(limit=168)
    # Simple history based on previous snapshots of similar hour
    historical_rates = [
        s[1] for s in recent_snapshots if datetime.fromisoformat(s[0]).hour == now.hour
    ]

    velocity = calculate_velocity(current_hourly, historical_rates, now)

    if velocity.is_spiking:
        logger.warning(
            f"Spike detected! Rate: {velocity.current_hourly_rate}, Baseline: {velocity.baseline_hourly_rate}"
        )
        commits = get_recent_commits()
        culprit = correlate_spike_to_commit(velocity.spike_started_at, commits)

        limits = config.get("limits", {})
        limit_hourly = limits.get("hourly")

        recommendation = (
            f"Roll back {culprit['hash'][:7]}" if culprit else "Investigate recent changes"
        )
        msg = format_alert_message(current_hourly, limit_hourly, culprit, recommendation)

        alert_config = config.get("alert", {})
        if "telegram_token" in alert_config and "telegram_chat_id" in alert_config:
            send_telegram_alert(
                alert_config["telegram_token"], alert_config["telegram_chat_id"], msg
            )

        if "slack_webhook" in alert_config:
            send_slack_alert(alert_config["slack_webhook"], msg)


def start_daemon():
    logger.info("Starting SpendSentry daemon...")
    schedule.every(5).minutes.do(run_check)

    # Run once on startup
    run_check()

    while True:
        schedule.run_pending()
        time.sleep(1)
