import logging

import httpx

logger = logging.getLogger(__name__)


def send_telegram_alert(token: str, chat_id: str, message: str):
    if not token or not chat_id:
        logger.warning("Telegram credentials missing, skipping alert.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}

    try:
        response = httpx.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except httpx.HTTPError as e:
        logger.error(f"Failed to send Telegram alert: {e}")
        return False


def send_slack_alert(webhook_url: str, message: str):
    if not webhook_url:
        logger.warning("Slack webhook URL missing, skipping alert.")
        return False

    payload = {"text": message}

    try:
        response = httpx.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except httpx.HTTPError as e:
        logger.error(f"Failed to send Slack alert: {e}")
        return False


def format_alert_message(rate: float, limit: float, commit: dict, recommendation: str) -> str:
    msg = "🚨 *SpendSentry Alert: High Spend Velocity*\n\n"
    msg += f"• Current Rate: ${rate:.2f}/hr\n"
    if limit:
        msg += f"• Limit: ${limit:.2f}/hr\n"

    if commit:
        msg += "\n*Probable Cause:*\n"
        msg += f"Commit `{commit['hash'][:7]}`: {commit['message']}\n"

    if recommendation:
        msg += f"\n*Recommendation:* {recommendation}"

    return msg
