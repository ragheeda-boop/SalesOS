"""Slack integration plugin — sends notifications to Slack channels."""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from domains.marketplace.manifest_schema import PluginManifest


SLACK_MANIFEST: dict[str, Any] = {
    "id": "salesos-slack",
    "name": "Slack Integration",
    "version": "1.0.0",
    "description": "Send SalesOS notifications and alerts to Slack channels. "
                   "Supports deal updates, pipeline changes, and custom alerts.",
    "author": "SalesOS",
    "license": "MIT",
    "icon": "https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/slack.svg",
    "tags": ["notifications", "messaging", "collaboration"],
    "permissions": ["notifications", "webhooks"],
    "hooks": [
        "after.decision.evaluated",
        "after.company.enriched",
        "after.company.merged",
    ],
    "dependencies": [],
    "config_schema": {
        "type": "object",
        "required": ["webhook_url"],
        "properties": {
            "webhook_url": {
                "type": "string",
                "description": "Slack Incoming Webhook URL",
                "pattern": "^https://hooks\\.slack\\.com/services/",
            },
            "channel": {
                "type": "string",
                "description": "Override channel (e.g., #sales-alerts)",
                "default": "#sales-alerts",
            },
            "notify_on": {
                "type": "array",
                "items": {"type": "string", "enum": ["deals", "companies", "decisions", "alerts"]},
                "description": "Event types to notify on",
                "default": ["deals", "companies"],
            },
            "bot_name": {
                "type": "string",
                "description": "Bot display name",
                "default": "SalesOS Bot",
            },
        },
    },
    "resource_limits": {
        "max_calls_per_sec": 10,
        "max_memory_mb": 20,
        "max_timeout_ms": 10000,
    },
}


@dataclass
class SlackNotification:
    channel: str
    text: str
    attachments: list[dict] = field(default_factory=list)
    bot_name: str = "SalesOS Bot"


def format_slack_message(event_type: str, payload: dict) -> SlackNotification:
    """Format a domain event into a Slack message."""
    if event_type == "after.decision.evaluated":
        decision = payload.get("decision", {})
        score = decision.get("score", "N/A")
        text = f"*Decision Evaluated* — Score: {score}"
        attachments = [
            {
                "color": "#36a64f" if isinstance(score, (int, float)) and score > 70 else "#ffcc00",
                "fields": [
                    {"title": "Decision ID", "value": decision.get("id", "N/A"), "short": True},
                    {"title": "Score", "value": str(score), "short": True},
                    {"title": "Reason", "value": decision.get("reason", ""), "short": False},
                ],
            }
        ]
        return SlackNotification(channel="#sales-alerts", text=text, attachments=attachments)

    if event_type == "after.company.enriched":
        company = payload.get("company", {})
        text = f"*Company Enriched* — {company.get('name', 'Unknown')}"
        attachments = [
            {
                "color": "#36a64f",
                "fields": [
                    {"title": "Company", "value": company.get("name", "N/A"), "short": True},
                    {"title": "Domain", "value": company.get("domain", "N/A"), "short": True},
                    {"title": "Industry", "value": company.get("industry", "N/A"), "short": False},
                ],
            }
        ]
        return SlackNotification(channel="#data-pipeline", text=text, attachments=attachments)

    if event_type == "after.company.merged":
        merge = payload.get("merge", {})
        text = f"*Companies Merged* — {merge.get('target_name', 'Unknown')}"
        return SlackNotification(channel="#data-pipeline", text=text)

    return SlackNotification(
        channel="#general",
        text=f"*SalesOS Event*: {event_type}",
    )


async def send_slack_notification(config: dict, notification: SlackNotification) -> dict:
    """Send a notification to Slack via webhook."""
    import httpx

    webhook_url = config.get("webhook_url")
    if not webhook_url:
        return {"success": False, "error": "No webhook URL configured"}

    payload: dict[str, Any] = {
        "text": notification.text,
        "username": notification.bot_name,
    }
    if notification.channel:
        payload["channel"] = notification.channel
    if notification.attachments:
        payload["attachments"] = notification.attachments

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(webhook_url, json=payload)

    if response.status_code == 200:
        return {"success": True, "status_code": response.status_code}
    return {"success": False, "status_code": response.status_code, "body": response.text}


def verify_slack_signature(body: bytes, signature: str, secret: str) -> bool:
    """Verify Slack request signature for slash commands and events."""
    if not signature or not secret:
        return False
    computed = hmac.new(
        secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(f"v0={computed}", signature)
