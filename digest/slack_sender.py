import os

import httpx

from digest.renderer import render_slack_blocks


def send_digest(candidates: list[dict], run_stats: dict) -> None:
    """Send the daily digest to the #dealradar Slack channel."""
    webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook:
        raise ValueError("SLACK_WEBHOOK_URL not set")

    blocks = render_slack_blocks(candidates, run_stats)
    r = httpx.post(
        webhook,
        json={"blocks": blocks},
        timeout=10,
    )
    r.raise_for_status()


def send_alert(message: str) -> None:
    """Send a plain-text alert to the personal Slack DM webhook."""
    webhook = os.environ.get("SLACK_ALERT_WEBHOOK_URL")
    if not webhook:
        return
    try:
        httpx.post(webhook, json={"text": message}, timeout=5)
    except Exception:
        pass
