"""
Notification system for sync events.
"""

import os
import requests
from .models import WebhookPayload


class Notifier:
    """
    Send notifications about sync events.

    Supports:
    - Webhook (HTTP POST)
    - Slack (via webhook)
    - Email (SMTP) - TODO
    - Console (stdout)

    Examples:
        notifier = Notifier()

        payload = WebhookPayload(
            event="change_detected",
            skill_name="react",
            changes=report
        )

        notifier.send(payload)
    """

    def __init__(
        self,
        webhook_url: str | None = None,
        slack_webhook: str | None = None,
        email_recipients: list[str] | None = None,
        console: bool = True,
    ):
        """
        Initialize notifier.

        Args:
            webhook_url: Webhook URL for HTTP notifications
            slack_webhook: Slack webhook URL
            email_recipients: List of email recipients
            console: Whether to print to console
        """
        self.webhook_url = webhook_url or os.getenv("SYNC_WEBHOOK_URL")
        self.slack_webhook = slack_webhook or os.getenv("SLACK_WEBHOOK_URL")
        self.email_recipients = email_recipients or []
        self.console = console

    def send(self, payload: WebhookPayload):
        """
        Send notification via all configured channels.

        Args:
            payload: Notification payload
        """
        if self.console:
            self._send_console(payload)

        if self.webhook_url:
            self._send_webhook(payload)

        if self.slack_webhook:
            self._send_slack(payload)

        if self.email_recipients:
            self._send_email(payload)

    def _send_console(self, payload: WebhookPayload):
        """Print to console."""
        print(f"\n📢 {payload.event.upper()}: {payload.skill_name}")

        if payload.changes:
            changes = payload.changes
            if changes.has_changes:
                print(f"   Changes detected: {changes.change_count}")
                if changes.added:
                    print(f"   ✅ Added: {len(changes.added)} pages")
                if changes.modified:
                    print(f"   ✏️  Modified: {len(changes.modified)} pages")
                if changes.deleted:
                    print(f"   ❌ Deleted: {len(changes.deleted)} pages")
            else:
                print("   No changes detected")

    def _send_webhook(self, payload: WebhookPayload):
        """Send to generic webhook."""
        try:
            response = requests.post(
                self.webhook_url,
                json=payload.dict(),
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            response.raise_for_status()
            print(f"✅ Webhook notification sent to {self.webhook_url}")
        except Exception as e:
            print(f"❌ Failed to send webhook: {e}")

    def _send_slack(self, payload: WebhookPayload):
        """Send to Slack via webhook."""
        try:
            # Format Slack message
            text = f"*{payload.event.upper()}*: {payload.skill_name}"

            if payload.changes and payload.changes.has_changes:
                changes = payload.changes
                text += f"\n• Changes: {changes.change_count}"
                text += f"\n• Added: {len(changes.added)}"
                text += f"\n• Modified: {len(changes.modified)}"
                text += f"\n• Deleted: {len(changes.deleted)}"

                # Add URLs of changed pages
                if changes.modified:
                    text += "\n\n*Modified Pages:*"
                    for change in changes.modified[:5]:  # Limit to 5
                        text += f"\n• {change.url}"
                    if len(changes.modified) > 5:
                        text += f"\n• ...and {len(changes.modified) - 5} more"

            slack_payload = {
                "text": text,
                "username": "Yonyou Doc2Skill Sync",
                "icon_emoji": ":books:",
            }

            response = requests.post(self.slack_webhook, json=slack_payload, timeout=10)
            response.raise_for_status()
            print("✅ Slack notification sent")
        except Exception as e:
            print(f"❌ Failed to send Slack notification: {e}")

    def _send_email(self, payload: WebhookPayload):
        """Send email notification."""
        # TODO: Implement SMTP email sending
        print(f"📧 Email notification (not implemented): {self.email_recipients}")
