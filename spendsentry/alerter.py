import logging

import httpx

from spendsentry.config import get_config

logger = logging.getLogger(__name__)


def send_alert(message: str):
    config = get_config()
    alert_channel = config.get("alerts", {}).get("channel")

    if alert_channel == "telegram":
        token = config.get("alerts", {}).get("telegram_token")
        chat_id = config.get("alerts", {}).get("telegram_chat_id")
        if not token or not chat_id:
            logger.error("Telegram token or chat_id not configured")
            return

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            httpx.post(url, json={"chat_id": chat_id, "text": message})
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")

    elif alert_channel == "slack":
        webhook_url = config.get("alerts", {}).get("slack_webhook_url")
        if not webhook_url:
            logger.error("Slack webhook_url not configured")
            return

        try:
            httpx.post(webhook_url, json={"text": message})
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
    else:
        logger.warning(f"Unknown or unconfigured alert channel: {alert_channel}")
        print(f"ALERT: {message}")
