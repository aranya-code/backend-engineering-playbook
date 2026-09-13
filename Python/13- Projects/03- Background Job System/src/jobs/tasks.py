"""Concrete background jobs used by the job system."""

from __future__ import annotations

import asyncio
from typing import Any

from src.jobs.base import BaseJob, JobContext


class SendEmailJob(BaseJob):
    """Send an email using the supplied recipient and message payload."""

    name = "send_email"

    async def execute(
        self,
        payload: dict[str, Any],
        context: JobContext,
    ) -> dict[str, Any]:
        """Execute an email delivery operation."""
        context.check_cancelled()

        recipient = payload.get("recipient")
        subject = payload.get("subject")
        body = payload.get("body")

        if not isinstance(recipient, str) or not recipient.strip():
            raise ValueError("Email recipient must be a non-empty string.")

        if not isinstance(subject, str) or not subject.strip():
            raise ValueError("Email subject must be a non-empty string.")

        if not isinstance(body, str) or not body.strip():
            raise ValueError("Email body must be a non-empty string.")

        await asyncio.sleep(0)

        return {
            "job": self.name,
            "recipient": recipient.strip(),
            "subject": subject.strip(),
            "attempt": context.attempt,
            "status": "sent",
        }


class ProcessWebhookJob(BaseJob):
    """Process a webhook event asynchronously and return its processing result."""

    name = "process_webhook"

    async def execute(
        self,
        payload: dict[str, Any],
        context: JobContext,
    ) -> dict[str, Any]:
        """Validate and process a webhook payload."""
        context.check_cancelled()

        event_id = payload.get("event_id")
        event_type = payload.get("event_type")

        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError("Webhook event_id must be a non-empty string.")

        if not isinstance(event_type, str) or not event_type.strip():
            raise ValueError("Webhook event_type must be a non-empty string.")

        await asyncio.sleep(0)

        return {
            "job": self.name,
            "event_id": event_id.strip(),
            "event_type": event_type.strip(),
            "attempt": context.attempt,
            "status": "processed",
        }


class CleanupJob(BaseJob):
    """Execute cleanup work for expired or temporary resources."""

    name = "cleanup"

    async def execute(
        self,
        payload: dict[str, Any],
        context: JobContext,
    ) -> dict[str, Any]:
        """Perform a bounded cleanup operation."""
        context.check_cancelled()

        resource_ids = payload.get("resource_ids", [])

        if not isinstance(resource_ids, list):
            raise ValueError("resource_ids must be a list.")

        if not all(isinstance(resource_id, str) for resource_id in resource_ids):
            raise ValueError("Every resource_id must be a string.")

        await asyncio.sleep(0)

        return {
            "job": self.name,
            "resources_processed": len(resource_ids),
            "attempt": context.attempt,
            "status": "completed",
        }


JOB_REGISTRY: dict[str, type[BaseJob]] = {
    SendEmailJob.name: SendEmailJob,
    ProcessWebhookJob.name: ProcessWebhookJob,
    CleanupJob.name: CleanupJob,
}


def get_job(job_name: str) -> BaseJob:
    """Create a registered job implementation by name."""
    try:
        job_type = JOB_REGISTRY[job_name]
    except KeyError as exc:
        raise ValueError(f"Unknown job type: {job_name}") from exc

    return job_type()

"""Concrete background jobs used by the job system."""

from __future__ import annotations

import asyncio
from typing import Any

from src.jobs.base import BaseJob, JobContext


class SendEmailJob(BaseJob):
    """Send an email using the supplied recipient and message payload."""

    name = "send_email"

    async def execute(
        self,
        payload: dict[str, Any],
        context: JobContext,
    ) -> dict[str, Any]:
        """Execute an email delivery operation."""
        context.check_cancelled()

        recipient = payload.get("recipient")
        subject = payload.get("subject")
        body = payload.get("body")

        if not isinstance(recipient, str) or not recipient.strip():
            raise ValueError("Email recipient must be a non-empty string.")

        if not isinstance(subject, str) or not subject.strip():
            raise ValueError("Email subject must be a non-empty string.")

        if not isinstance(body, str) or not body.strip():
            raise ValueError("Email body must be a non-empty string.")

        await asyncio.sleep(0)

        return {
            "job": self.name,
            "recipient": recipient.strip(),
            "subject": subject.strip(),
            "attempt": context.attempt,
            "status": "sent",
        }


class ProcessWebhookJob(BaseJob):
    """Process a webhook event asynchronously and return its processing result."""

    name = "process_webhook"

    async def execute(
        self,
        payload: dict[str, Any],
        context: JobContext,
    ) -> dict[str, Any]:
        """Validate and process a webhook payload."""
        context.check_cancelled()

        event_id = payload.get("event_id")
        event_type = payload.get("event_type")

        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError("Webhook event_id must be a non-empty string.")

        if not isinstance(event_type, str) or not event_type.strip():
            raise ValueError("Webhook event_type must be a non-empty string.")

        await asyncio.sleep(0)

        return {
            "job": self.name,
            "event_id": event_id.strip(),
            "event_type": event_type.strip(),
            "attempt": context.attempt,
            "status": "processed",
        }


class CleanupJob(BaseJob):
    """Execute cleanup work for expired or temporary resources."""

    name = "cleanup"

    async def execute(
        self,
        payload: dict[str, Any],
        context: JobContext,
    ) -> dict[str, Any]:
        """Perform a bounded cleanup operation."""
        context.check_cancelled()

        resource_ids = payload.get("resource_ids", [])

        if not isinstance(resource_ids, list):
            raise ValueError("resource_ids must be a list.")

        if not all(isinstance(resource_id, str) for resource_id in resource_ids):
            raise ValueError("Every resource_id must be a string.")

        await asyncio.sleep(0)

        return {
            "job": self.name,
            "resources_processed": len(resource_ids),
            "attempt": context.attempt,
            "status": "completed",
        }


JOB_REGISTRY: dict[str, type[BaseJob]] = {
    SendEmailJob.name: SendEmailJob,
    ProcessWebhookJob.name: ProcessWebhookJob,
    CleanupJob.name: CleanupJob,
}


def get_job(job_name: str) -> BaseJob:
    """Create a registered job implementation by name."""
    try:
        job_type = JOB_REGISTRY[job_name]
    except KeyError as exc:
        raise ValueError(f"Unknown job type: {job_name}") from exc

    return job_type()