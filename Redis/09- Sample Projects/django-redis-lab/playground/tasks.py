"""
Celery tasks for background processing.

These tasks are queued in Redis and executed by Celery workers.
Start the worker with: celery -A config worker --loglevel=info
"""

from __future__ import annotations

import logging
import time

from config.celery import app

logger = logging.getLogger(__name__)


@app.task(name="playground.tasks.send_otp_email")
def send_otp_email(email: str, otp_code: str) -> dict[str, str]:
    """
    Simulate sending an OTP email.

    In production, this would integrate with an email service
    (SES, SendGrid, Mailgun, etc.). Here we simulate the delay
    and log the result.

    Args:
        email: Recipient email address.
        otp_code: The OTP code to include in the email.

    Returns:
        Dict with status and details.
    """
    logger.info("Sending OTP email to %s ...", email)

    # Simulate email sending delay (1-3 seconds)
    time.sleep(2)

    logger.info(
        "OTP email sent successfully: to=%s otp=%s",
        email, otp_code,
    )

    return {
        "status": "sent",
        "email": email,
        "message": f"OTP {otp_code} sent to {email}",
    }


@app.task(name="playground.tasks.send_notification")
def send_notification(channel: str, message: str) -> dict[str, str]:
    """
    Simulate sending a notification via an external service.

    Args:
        channel: Notification channel/topic.
        message: Notification content.

    Returns:
        Dict with status and details.
    """
    logger.info("Sending notification: channel=%s message=%s", channel, message[:50])

    # Simulate processing delay
    time.sleep(1)

    logger.info("Notification sent: channel=%s", channel)

    return {
        "status": "sent",
        "channel": channel,
        "message": message,
    }
