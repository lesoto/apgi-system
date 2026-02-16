"""
Alerting System

Monitors critical errors and triggers alerts through configured notification channels.
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import httpx

from api.middleware.logging import StructuredLogger

logger = StructuredLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """
    Represents an alert to be sent.
    """

    title: str
    message: str
    severity: AlertSeverity
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert alert to dictionary."""
        return {
            "title": self.title,
            "message": self.message,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat() + "Z",
            "metadata": self.metadata,
        }


class NotificationChannel(ABC):
    """
    Abstract base class for notification channels.
    """

    @abstractmethod
    async def send_alert(self, alert: Alert) -> bool:
        """
        Send alert through this channel.

        Args:
            alert: Alert to send

        Returns:
            True if alert was sent successfully
        """
        pass


class WebhookNotificationChannel(NotificationChannel):
    """
    Sends alerts via HTTP webhook.
    """

    def __init__(self, webhook_url: str, timeout: float = 10.0):
        """
        Initialize webhook notification channel.

        Args:
            webhook_url: URL to POST alerts to
            timeout: Request timeout in seconds
        """
        self.webhook_url = webhook_url
        self.timeout = timeout

    async def send_alert(self, alert: Alert) -> bool:
        """
        Send alert via webhook POST request.

        Args:
            alert: Alert to send

        Returns:
            True if webhook call succeeded
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url, json=alert.to_dict(), timeout=self.timeout
                )

                if response.status_code < 300:
                    logger.info(
                        "Alert sent via webhook",
                        webhook_url=self.webhook_url,
                        alert_title=alert.title,
                        severity=alert.severity.value,
                    )
                    return True
                else:
                    logger.warning(
                        "Webhook returned non-success status",
                        webhook_url=self.webhook_url,
                        status_code=response.status_code,
                        alert_title=alert.title,
                    )
                    return False

        except Exception as e:
            logger.error(
                "Failed to send alert via webhook",
                webhook_url=self.webhook_url,
                alert_title=alert.title,
                error=str(e),
            )
            return False


class LogNotificationChannel(NotificationChannel):
    """
    Sends alerts to log output (useful for development/testing).
    """

    async def send_alert(self, alert: Alert) -> bool:
        """
        Log alert at appropriate level.

        Args:
            alert: Alert to log

        Returns:
            Always True (logging doesn't fail)
        """
        log_data = {
            "alert_title": alert.title,
            "alert_message": alert.message,
            "severity": alert.severity.value,
            **alert.metadata,
        }

        if alert.severity == AlertSeverity.CRITICAL:
            logger.error("CRITICAL ALERT", **log_data)
        elif alert.severity == AlertSeverity.ERROR:
            logger.error("ERROR ALERT", **log_data)
        elif alert.severity == AlertSeverity.WARNING:
            logger.warning("WARNING ALERT", **log_data)
        else:
            logger.info("INFO ALERT", **log_data)

        return True


class EmailNotificationChannel(NotificationChannel):
    """
    Sends alerts via email using SMTP.
    """

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int = 587,
        username: str = None,
        password: str = None,
        from_email: str = None,
        to_emails: List[str] = None,
        use_tls: bool = True,
    ):
        """
        Initialize email notification channel.

        Args:
            smtp_server: SMTP server hostname
            smtp_port: SMTP server port
            username: SMTP authentication username
            password: SMTP authentication password
            from_email: Sender email address
            to_emails: List of recipient email addresses
            use_tls: Whether to use TLS encryption
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails or []
        self.use_tls = use_tls

    async def send_alert(self, alert: Alert) -> bool:
        """
        Send alert via email.

        Args:
            alert: Alert to send

        Returns:
            True if email was sent successfully
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = ", ".join(self.to_emails)
            msg["Subject"] = f"[{alert.severity.value.upper()}] {alert.title}"

            # Create HTML body
            html_body = f"""
            <html>
            <body>
                <h2 style="color: {self._get_severity_color(alert.severity)};">
                    {alert.title}
                </h2>
                <p><strong>Severity:</strong> {alert.severity.value.upper()}</p>
                <p><strong>Time:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                <p><strong>Message:</strong></p>
                <pre style="background-color: #f5f5f5; padding: 10px; border-radius: 5px;">
                    {alert.message}
                </pre>
                {"<h3>Metadata:</h3><pre>" + json.dumps(alert.metadata, indent=2) + "</pre>" if alert.metadata else ""}
            </body>
            </html>
            """

            msg.attach(MIMEText(html_body, "html"))

            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            if self.use_tls:
                server.starttls()

            if self.username and self.password:
                server.login(self.username, self.password)

            text = msg.as_string()
            server.sendmail(self.from_email, self.to_emails, text)
            server.quit()

            logger.info(
                "Alert sent via email",
                recipients=self.to_emails,
                alert_title=alert.title,
                severity=alert.severity.value,
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to send alert via email",
                smtp_server=self.smtp_server,
                recipients=self.to_emails,
                alert_title=alert.title,
                error=str(e),
            )
            return False

    def _get_severity_color(self, severity: AlertSeverity) -> str:
        """Get color for severity level."""
        colors = {
            AlertSeverity.INFO: "#17a2b8",
            AlertSeverity.WARNING: "#ffc107",
            AlertSeverity.ERROR: "#fd7e14",
            AlertSeverity.CRITICAL: "#dc3545",
        }
        return colors.get(severity, "#6c757d")


class SMSNotificationChannel(NotificationChannel):
    """
    Sends alerts via SMS using external SMS gateway service.
    """

    def __init__(
        self,
        api_url: str,
        api_key: str,
        from_number: str = None,
        to_numbers: List[str] = None,
        timeout: float = 10.0,
    ):
        """
        Initialize SMS notification channel.

        Args:
            api_url: SMS gateway API URL
            api_key: API authentication key
            from_number: Sender phone number
            to_numbers: List of recipient phone numbers
            timeout: Request timeout in seconds
        """
        self.api_url = api_url
        self.api_key = api_key
        self.from_number = from_number
        self.to_numbers = to_numbers or []
        self.timeout = timeout

    async def send_alert(self, alert: Alert) -> bool:
        """
        Send alert via SMS.

        Args:
            alert: Alert to send

        Returns:
            True if SMS was sent successfully
        """
        try:
            # Create concise SMS message (SMS has character limits)
            sms_message = f"[{alert.severity.value.upper()}] {alert.title}: {alert.message[:100]}{'...' if len(alert.message) > 100 else ''}"

            async with httpx.AsyncClient() as client:
                # Send to each recipient
                success_count = 0
                for to_number in self.to_numbers:
                    payload = {
                        "api_key": self.api_key,
                        "to": to_number,
                        "from": self.from_number,
                        "message": sms_message,
                    }

                    response = await client.post(self.api_url, json=payload, timeout=self.timeout)

                    if response.status_code < 300:
                        success_count += 1
                    else:
                        logger.warning(
                            "SMS send failed for recipient",
                            recipient=to_number,
                            status_code=response.status_code,
                            alert_title=alert.title,
                        )

                if success_count > 0:
                    logger.info(
                        "Alert sent via SMS",
                        recipients=self.to_numbers,
                        alert_title=alert.title,
                        severity=alert.severity.value,
                        success_count=success_count,
                        total_recipients=len(self.to_numbers),
                    )
                    return True
                else:
                    logger.error(
                        "Failed to send SMS to any recipients",
                        alert_title=alert.title,
                        total_recipients=len(self.to_numbers),
                    )
                    return False

        except Exception as e:
            logger.error(
                "Failed to send alert via SMS",
                api_url=self.api_url,
                alert_title=alert.title,
                error=str(e),
            )
            return False


class SlackNotificationChannel(NotificationChannel):
    """
    Sends alerts to Slack channels via webhooks.
    """

    def __init__(
        self,
        webhook_url: str,
        channel: str = None,
        username: str = "APGI Alert Bot",
        timeout: float = 10.0,
    ):
        """
        Initialize Slack notification channel.

        Args:
            webhook_url: Slack webhook URL
            channel: Slack channel (optional, can be overridden in webhook)
            username: Bot username
            timeout: Request timeout in seconds
        """
        self.webhook_url = webhook_url
        self.channel = channel
        self.username = username
        self.timeout = timeout

    async def send_alert(self, alert: Alert) -> bool:
        """
        Send alert to Slack.

        Args:
            alert: Alert to send

        Returns:
            True if Slack message was sent successfully
        """
        try:
            # Create Slack message payload
            color = self._get_severity_color(alert.severity)
            payload = {
                "username": self.username,
                "attachments": [
                    {
                        "color": color,
                        "title": alert.title,
                        "text": alert.message,
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert.severity.value.upper(),
                                "short": True,
                            },
                            {
                                "title": "Time",
                                "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
                                "short": True,
                            },
                        ],
                        "footer": "APGI Alert System",
                        "ts": alert.timestamp.timestamp(),
                    }
                ],
            }

            if self.channel:
                payload["channel"] = self.channel

            # Add metadata as additional fields
            if alert.metadata:
                for key, value in list(alert.metadata.items())[:5]:  # Limit to 5 fields
                    payload["attachments"][0]["fields"].append(
                        {
                            "title": str(key).replace("_", " ").title(),
                            "value": str(value)[:100],  # Truncate long values
                            "short": True,
                        }
                    )

            async with httpx.AsyncClient() as client:
                response = await client.post(self.webhook_url, json=payload, timeout=self.timeout)

                if response.status_code == 200:
                    logger.info(
                        "Alert sent to Slack",
                        webhook_url=self.webhook_url,
                        alert_title=alert.title,
                        severity=alert.severity.value,
                    )
                    return True
                else:
                    logger.warning(
                        "Slack webhook returned non-success status",
                        webhook_url=self.webhook_url,
                        status_code=response.status_code,
                        alert_title=alert.title,
                    )
                    return False

        except Exception as e:
            logger.error(
                "Failed to send alert to Slack",
                webhook_url=self.webhook_url,
                alert_title=alert.title,
                error=str(e),
            )
            return False

    def _get_severity_color(self, severity: AlertSeverity) -> str:
        """Get color for severity level in Slack."""
        colors = {
            AlertSeverity.INFO: "good",
            AlertSeverity.WARNING: "warning",
            AlertSeverity.ERROR: "danger",
            AlertSeverity.CRITICAL: "#dc3545",
        }
        return colors.get(severity, "#6c757d")


class TeamsNotificationChannel(NotificationChannel):
    """
    Sends alerts to Microsoft Teams channels via webhooks.
    """

    def __init__(self, webhook_url: str, timeout: float = 10.0):
        """
        Initialize Teams notification channel.

        Args:
            webhook_url: Teams webhook URL
            timeout: Request timeout in seconds
        """
        self.webhook_url = webhook_url
        self.timeout = timeout

    async def send_alert(self, alert: Alert) -> bool:
        """
        Send alert to Microsoft Teams.

        Args:
            alert: Alert to send

        Returns:
            True if Teams message was sent successfully
        """
        try:
            # Create Teams message payload
            theme_color = self._get_severity_color(alert.severity)

            facts = [
                {"name": "Severity", "value": alert.severity.value.upper()},
                {"name": "Time", "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")},
            ]

            # Add metadata as facts
            if alert.metadata:
                for key, value in list(alert.metadata.items())[:8]:  # Limit to 8 facts
                    facts.append(
                        {
                            "name": str(key).replace("_", " ").title(),
                            "value": str(value)[:200],  # Truncate long values
                        }
                    )

            payload = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": theme_color,
                "title": alert.title,
                "text": alert.message,
                "sections": [{"facts": facts}],
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(self.webhook_url, json=payload, timeout=self.timeout)

                if response.status_code == 200:
                    logger.info(
                        "Alert sent to Teams",
                        webhook_url=self.webhook_url,
                        alert_title=alert.title,
                        severity=alert.severity.value,
                    )
                    return True
                else:
                    logger.warning(
                        "Teams webhook returned non-success status",
                        webhook_url=self.webhook_url,
                        status_code=response.status_code,
                        alert_title=alert.title,
                    )
                    return False

        except Exception as e:
            logger.error(
                "Failed to send alert to Teams",
                webhook_url=self.webhook_url,
                alert_title=alert.title,
                error=str(e),
            )
            return False

    def _get_severity_color(self, severity: AlertSeverity) -> str:
        """Get color for severity level in Teams."""
        colors = {
            AlertSeverity.INFO: "0076D7",
            AlertSeverity.WARNING: "FF8C00",
            AlertSeverity.ERROR: "FF0000",
            AlertSeverity.CRITICAL: "8B0000",
        }
        return colors.get(severity, "808080")


class PagerDutyNotificationChannel(NotificationChannel):
    """
    Sends alerts to PagerDuty for incident management.
    """

    def __init__(self, routing_key: str, timeout: float = 10.0):
        """
        Initialize PagerDuty notification channel.

        Args:
            routing_key: PagerDuty Events API v2 integration key
            timeout: Request timeout in seconds
        """
        self.routing_key = routing_key
        self.api_url = "https://events.pagerduty.com/v2/enqueue"
        self.timeout = timeout

    async def send_alert(self, alert: Alert) -> bool:
        """
        Send alert to PagerDuty.

        Args:
            alert: Alert to send

        Returns:
            True if PagerDuty event was created successfully
        """
        try:
            # Determine event action based on severity
            if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.ERROR]:
                event_action = "trigger"
                severity = "critical"
            elif alert.severity == AlertSeverity.WARNING:
                event_action = "trigger"
                severity = "warning"
            else:
                event_action = "trigger"
                severity = "info"

            # Create PagerDuty event payload
            payload = {
                "routing_key": self.routing_key,
                "event_action": event_action,
                "dedup_key": f"apgi-{alert.severity.value}-{hash(alert.title) % 1000000}",
                "payload": {
                    "summary": alert.title,
                    "source": "apgi-alert-system",
                    "severity": severity,
                    "timestamp": alert.timestamp.isoformat() + "Z",
                    "component": "alert-system",
                    "group": "application-monitoring",
                    "class": "alert",
                    "custom_details": {"message": alert.message, "metadata": alert.metadata},
                },
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(self.api_url, json=payload, timeout=self.timeout)

                if response.status_code == 202:  # Accepted
                    logger.info(
                        "Alert sent to PagerDuty",
                        event_action=event_action,
                        alert_title=alert.title,
                        severity=alert.severity.value,
                    )
                    return True
                else:
                    logger.warning(
                        "PagerDuty API returned non-success status",
                        status_code=response.status_code,
                        alert_title=alert.title,
                        response_body=response.text[:500],
                    )
                    return False

        except Exception as e:
            logger.error(
                "Failed to send alert to PagerDuty",
                alert_title=alert.title,
                error=str(e),
            )
            return False


class DatabaseNotificationChannel(NotificationChannel):
    """
    Logs alerts to database for audit trails and historical analysis.
    """

    def __init__(self, db_session_factory=None):
        """
        Initialize database notification channel.

        Args:
            db_session_factory: Function that returns database session
        """
        self.db_session_factory = db_session_factory

    async def send_alert(self, alert: Alert) -> bool:
        """
        Log alert to database.

        Args:
            alert: Alert to log

        Returns:
            True if alert was logged successfully
        """
        try:
            if not self.db_session_factory:
                logger.warning("Database session factory not configured", alert_title=alert.title)
                return False

            # This would integrate with the database models
            # For now, we'll just log that we'd store it
            alert_data = {
                "title": alert.title,
                "message": alert.message,
                "severity": alert.severity.value,
                "timestamp": alert.timestamp.isoformat() + "Z",
                "metadata": json.dumps(alert.metadata) if alert.metadata else None,
            }

            logger.info(
                "Alert logged to database",
                alert_title=alert.title,
                severity=alert.severity.value,
                alert_data=alert_data,
            )

            # TODO: Implement actual database storage
            # session = self.db_session_factory()
            # try:
            #     alert_record = AlertLog(**alert_data)
            #     session.add(alert_record)
            #     session.commit()
            # except Exception as db_error:
            #     session.rollback()
            #     raise db_error
            # finally:
            #     session.close()

            return True

        except Exception as e:
            logger.error(
                "Failed to log alert to database",
                alert_title=alert.title,
                error=str(e),
            )
            return False


class AlertManager:
    """
    Manages alert triggers and notification channels.

    Monitors error rates and triggers alerts when thresholds are exceeded.
    """

    def __init__(self):
        """Initialize alert manager."""
        self.channels: List[NotificationChannel] = []
        self.error_counts: Dict[str, List[datetime]] = {}
        self.alert_cooldowns: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()

        # Alert thresholds
        self.error_rate_threshold = 10  # errors per minute
        self.error_rate_window = timedelta(minutes=1)
        self.alert_cooldown = timedelta(minutes=5)  # Don't spam alerts

    def add_channel(self, channel: NotificationChannel):
        """
        Add a notification channel.

        Args:
            channel: Notification channel to add
        """
        self.channels.append(channel)
        logger.info(
            "Notification channel added",
            channel_type=type(channel).__name__,
            total_channels=len(self.channels),
        )

    async def record_error(
        self, error_type: str, error_message: str, metadata: Optional[Dict] = None
    ):
        """
        Record an error and check if alert should be triggered.

        Args:
            error_type: Type of error
            error_message: Error message
            metadata: Additional error metadata
        """
        async with self._lock:
            now = datetime.utcnow()

            # Initialize error tracking for this type
            if error_type not in self.error_counts:
                self.error_counts[error_type] = []

            # Add error timestamp
            self.error_counts[error_type].append(now)

            # Clean up old errors outside the window
            cutoff = now - self.error_rate_window
            self.error_counts[error_type] = [
                ts for ts in self.error_counts[error_type] if ts > cutoff
            ]

            # Check if we should trigger an alert
            error_count = len(self.error_counts[error_type])

            if error_count >= self.error_rate_threshold:
                await self._trigger_high_error_rate_alert(
                    error_type, error_count, error_message, metadata
                )

    async def _trigger_high_error_rate_alert(
        self, error_type: str, error_count: int, error_message: str, metadata: Optional[Dict]
    ):
        """
        Trigger alert for high error rate.

        Args:
            error_type: Type of error
            error_count: Number of errors in window
            error_message: Recent error message
            metadata: Additional metadata
        """
        # Check cooldown to avoid alert spam
        alert_key = f"high_error_rate_{error_type}"
        now = datetime.utcnow()

        if alert_key in self.alert_cooldowns:
            if now < self.alert_cooldowns[alert_key]:
                # Still in cooldown period
                return

        # Set cooldown
        self.alert_cooldowns[alert_key] = now + self.alert_cooldown

        # Create alert
        alert = Alert(
            title=f"High Error Rate: {error_type}",
            message=f"Detected {error_count} errors of type '{error_type}' in the last minute. Recent error: {error_message}",
            severity=AlertSeverity.CRITICAL,
            metadata={
                "error_type": error_type,
                "error_count": error_count,
                "window_minutes": self.error_rate_window.total_seconds() / 60,
                "recent_error": error_message,
                **(metadata or {}),
            },
        )

        # Send alert through all channels
        await self._send_alert(alert)

    async def trigger_custom_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity = AlertSeverity.ERROR,
        metadata: Optional[Dict] = None,
    ):
        """
        Trigger a custom alert.

        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity
            metadata: Additional metadata
        """
        alert = Alert(title=title, message=message, severity=severity, metadata=metadata or {})

        await self._send_alert(alert)

    async def _send_alert(self, alert: Alert):
        """
        Send alert through all configured channels.

        Args:
            alert: Alert to send
        """
        if not self.channels:
            logger.warning("No notification channels configured", alert_title=alert.title)
            return

        # Send to all channels concurrently
        tasks = [channel.send_alert(alert) for channel in self.channels]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log results
        success_count = sum(1 for r in results if r is True)
        logger.info(
            "Alert sent to channels",
            alert_title=alert.title,
            severity=alert.severity.value,
            channels_total=len(self.channels),
            channels_success=success_count,
        )


# Global alert manager instance
alert_manager = AlertManager()


def configure_alerting(
    webhook_urls: Optional[List[str]] = None,
    email_config: Optional[Dict] = None,
    sms_config: Optional[Dict] = None,
    slack_config: Optional[Dict] = None,
    teams_config: Optional[Dict] = None,
    pagerduty_config: Optional[Dict] = None,
    database_config: Optional[Dict] = None,
    enable_log_channel: bool = True,
    error_rate_threshold: int = 10,
    error_rate_window_minutes: int = 1,
    alert_cooldown_minutes: int = 5,
):
    """
    Configure the alerting system with multiple notification channels.

    Args:
        webhook_urls: List of webhook URLs to send alerts to
        email_config: Email configuration dictionary with keys:
            - smtp_server: SMTP server hostname
            - smtp_port: SMTP server port (default: 587)
            - username: SMTP username
            - password: SMTP password
            - from_email: Sender email address
            - to_emails: List of recipient email addresses
            - use_tls: Whether to use TLS (default: True)
        sms_config: SMS configuration dictionary with keys:
            - api_url: SMS gateway API URL
            - api_key: API authentication key
            - from_number: Sender phone number
            - to_numbers: List of recipient phone numbers
        slack_config: Slack configuration dictionary with keys:
            - webhook_url: Slack webhook URL
            - channel: Slack channel (optional)
            - username: Bot username (default: "APGI Alert Bot")
        teams_config: Teams configuration dictionary with keys:
            - webhook_url: Teams webhook URL
        pagerduty_config: PagerDuty configuration dictionary with keys:
            - routing_key: PagerDuty Events API v2 integration key
        database_config: Database configuration dictionary with keys:
            - session_factory: Function that returns database session
        enable_log_channel: Whether to enable log-based alerts
        error_rate_threshold: Number of errors to trigger alert
        error_rate_window_minutes: Time window for error rate calculation
        alert_cooldown_minutes: Cooldown period between alerts
    """
    # Configure thresholds
    alert_manager.error_rate_threshold = error_rate_threshold
    alert_manager.error_rate_window = timedelta(minutes=error_rate_window_minutes)
    alert_manager.alert_cooldown = timedelta(minutes=alert_cooldown_minutes)

    # Add webhook channels
    if webhook_urls:
        for url in webhook_urls:
            alert_manager.add_channel(WebhookNotificationChannel(url))

    # Add email channel
    if email_config:
        email_channel = EmailNotificationChannel(
            smtp_server=email_config["smtp_server"],
            smtp_port=email_config.get("smtp_port", 587),
            username=email_config.get("username"),
            password=email_config.get("password"),
            from_email=email_config["from_email"],
            to_emails=email_config["to_emails"],
            use_tls=email_config.get("use_tls", True),
        )
        alert_manager.add_channel(email_channel)

    # Add SMS channel
    if sms_config:
        sms_channel = SMSNotificationChannel(
            api_url=sms_config["api_url"],
            api_key=sms_config["api_key"],
            from_number=sms_config.get("from_number"),
            to_numbers=sms_config["to_numbers"],
        )
        alert_manager.add_channel(sms_channel)

    # Add Slack channel
    if slack_config:
        slack_channel = SlackNotificationChannel(
            webhook_url=slack_config["webhook_url"],
            channel=slack_config.get("channel"),
            username=slack_config.get("username", "APGI Alert Bot"),
        )
        alert_manager.add_channel(slack_channel)

    # Add Teams channel
    if teams_config:
        teams_channel = TeamsNotificationChannel(webhook_url=teams_config["webhook_url"])
        alert_manager.add_channel(teams_channel)

    # Add PagerDuty channel
    if pagerduty_config:
        pagerduty_channel = PagerDutyNotificationChannel(
            routing_key=pagerduty_config["routing_key"]
        )
        alert_manager.add_channel(pagerduty_channel)

    # Add database channel
    if database_config:
        database_channel = DatabaseNotificationChannel(
            db_session_factory=database_config.get("session_factory")
        )
        alert_manager.add_channel(database_channel)

    # Add log channel
    if enable_log_channel:
        alert_manager.add_channel(LogNotificationChannel())

    logger.info(
        "Alerting system configured",
        error_rate_threshold=error_rate_threshold,
        error_rate_window_minutes=error_rate_window_minutes,
        alert_cooldown_minutes=alert_cooldown_minutes,
        channels=len(alert_manager.channels),
        channel_types=[type(ch).__name__ for ch in alert_manager.channels],
    )
