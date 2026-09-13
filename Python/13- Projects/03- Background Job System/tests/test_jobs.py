"""Unit tests for background job lifecycle and concrete job implementations."""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.jobs.base import BaseJob, Job, JobContext, JobStatus
from src.jobs.tasks import CleanupJob, ProcessWebhookJob, SendEmailJob, get_job


class SuccessfulJob(BaseJob):
    """Test job that completes successfully."""

    name = "successful"

    async def execute(
        self,
        payload: dict[str, object],
        context: JobContext,
    ) -> object:
        """Return the supplied payload."""
        context.check_cancelled()
        return payload


class FailingJob(BaseJob):
    """Test job that always raises an execution error."""

    name = "failing"

    async def execute(
        self,
        payload: dict[str, object],
        context: JobContext,
    ) -> object:
        """Raise a deterministic test failure."""
        raise RuntimeError("job execution failed")


@pytest.mark.asyncio
async def test_successful_job_transitions_to_succeeded() -> None:
    """A successful execution should update the complete job lifecycle."""
    job = Job(
        name=SuccessfulJob.name,
        payload={"value": "test"},
    )
    context = JobContext(
        job_id=job.id,
        attempt=1,
        max_retries=3,
    )

    result = await SuccessfulJob().run(job, context)

    assert result == {"value": "test"}
    assert job.status == JobStatus.SUCCEEDED
    assert job.attempts == 1
    assert job.started_at is not None
    assert job.completed_at is not None
    assert job.last_error is None


@pytest.mark.asyncio
async def test_failed_job_records_error_and_transitions_to_failed() -> None:
    """A retryable failure should record the error and retain failed state."""
    job = Job(
        name=FailingJob.name,
        payload={},
        max_retries=3,
    )
    context = JobContext(
        job_id=job.id,
        attempt=1,
        max_retries=3,
    )

    with pytest.raises(RuntimeError, match="job execution failed"):
        await FailingJob().run(job, context)

    assert job.status == JobStatus.FAILED
    assert job.attempts == 1
    assert job.last_error == "job execution failed"
    assert job.completed_at is not None


@pytest.mark.asyncio
async def test_failed_job_is_dead_lettered_after_retry_exhaustion() -> None:
    """A failure beyond the retry budget should become dead-lettered."""
    job = Job(
        name=FailingJob.name,
        payload={},
        max_retries=0,
    )
    context = JobContext(
        job_id=job.id,
        attempt=1,
        max_retries=0,
    )

    with pytest.raises(RuntimeError, match="job execution failed"):
        await FailingJob().run(job, context)

    assert job.status == JobStatus.DEAD_LETTERED
    assert job.retries_exhausted is True
    assert job.last_error == "job execution failed"


@pytest.mark.asyncio
async def test_job_cancellation_is_not_swallowed() -> None:
    """Cancellation should propagate instead of being converted to failure."""
    class CancelledJob(BaseJob):
        """Test job that observes cancellation through its context."""

        name = "cancelled"

        async def execute(
            self,
            payload: dict[str, object],
            context: JobContext,
        ) -> object:
            """Raise cancellation when requested."""
            context.check_cancelled()
            return payload

    job = Job(name=CancelledJob.name, payload={})
    context = JobContext(
        job_id=job.id,
        attempt=1,
        max_retries=3,
        cancelled=True,
    )

    with pytest.raises(RuntimeError, match="execution was cancelled"):
        await CancelledJob().run(job, context)

    assert job.status == JobStatus.FAILED
    assert job.last_error is not None


def test_job_mark_running_increments_attempt_count() -> None:
    """Starting a job should increment its execution attempt."""
    job = Job(name="example", payload={})

    job.mark_running()

    assert job.status == JobStatus.RUNNING
    assert job.attempts == 1
    assert job.started_at is not None


def test_job_mark_succeeded_requires_running_state() -> None:
    """A job cannot transition directly from pending to succeeded."""
    job = Job(name="example", payload={})

    with pytest.raises(ValueError, match="cannot succeed"):
        job.mark_succeeded()


def test_job_mark_failed_requires_running_state() -> None:
    """A job cannot record failure before execution starts."""
    job = Job(name="example", payload={})

    with pytest.raises(ValueError, match="cannot fail"):
        job.mark_failed("failure")


def test_job_mark_dead_lettered_requires_failed_or_running_state() -> None:
    """Dead-lettering should reject invalid lifecycle transitions."""
    job = Job(name="example", payload={})

    with pytest.raises(ValueError, match="cannot be dead-lettered"):
        job.mark_dead_lettered()


def test_retries_exhausted_is_false_when_retries_remain() -> None:
    """A job with remaining retry capacity should not be exhausted."""
    job = Job(
        name="example",
        payload={},
        max_retries=3,
    )

    job.mark_running()

    assert job.attempts == 1
    assert job.retries_exhausted is False


def test_retries_exhausted_is_true_when_retry_budget_is_consumed() -> None:
    """A job should report exhaustion after its final permitted attempt."""
    job = Job(
        name="example",
        payload={},
        max_retries=1,
    )

    job.mark_running()
    job.mark_failed("first failure")
    job.mark_running()

    assert job.attempts == 2
    assert job.retries_exhausted is True


@pytest.mark.asyncio
async def test_send_email_job_validates_required_fields() -> None:
    """Email jobs should reject incomplete delivery payloads."""
    job = SendEmailJob()
    context = JobContext(
        job_id=uuid4(),
        attempt=1,
        max_retries=3,
    )

    with pytest.raises(ValueError, match="recipient"):
        await job.execute(
            {
                "subject": "Subject",
                "body": "Body",
            },
            context,
        )


@pytest.mark.asyncio
async def test_send_email_job_returns_delivery_result() -> None:
    """A valid email payload should produce a normalized result."""
    context = JobContext(
        job_id=uuid4(),
        attempt=2,
        max_retries=3,
    )

    result = await SendEmailJob().execute(
        {
            "recipient": "  user@example.com ",
            "subject": "  Welcome ",
            "body": "  Hello ",
        },
        context,
    )

    assert result == {
        "job": "send_email",
        "recipient": "user@example.com",
        "subject": "Welcome",
        "attempt": 2,
        "status": "sent",
    }


@pytest.mark.asyncio
async def test_process_webhook_job_validates_event_fields() -> None:
    """Webhook jobs should reject missing event identifiers."""
    context = JobContext(
        job_id=uuid4(),
        attempt=1,
        max_retries=3,
    )

    with pytest.raises(ValueError, match="event_id"):
        await ProcessWebhookJob().execute(
            {"event_type": "payment.created"},
            context,
        )


@pytest.mark.asyncio
async def test_process_webhook_job_returns_processing_result() -> None:
    """A valid webhook payload should produce a processing result."""
    context = JobContext(
        job_id=uuid4(),
        attempt=1,
        max_retries=3,
    )

    result = await ProcessWebhookJob().execute(
        {
            "event_id": "evt_123",
            "event_type": "payment.created",
        },
        context,
    )

    assert result == {
        "job": "process_webhook",
        "event_id": "evt_123",
        "event_type": "payment.created",
        "attempt": 1,
        "status": "processed",
    }


@pytest.mark.asyncio
async def test_cleanup_job_validates_resource_ids() -> None:
    """Cleanup jobs should require a list of string resource identifiers."""
    context = JobContext(
        job_id=uuid4(),
        attempt=1,
        max_retries=3,
    )

    with pytest.raises(ValueError, match="resource_ids must be a list"):
        await CleanupJob().execute(
            {"resource_ids": "resource-1"},
            context,
        )


@pytest.mark.asyncio
async def test_cleanup_job_returns_processed_resource_count() -> None:
    """Cleanup jobs should report the number of processed resources."""
    context = JobContext(
        job_id=uuid4(),
        attempt=1,
        max_retries=3,
    )

    result = await CleanupJob().execute(
        {
            "resource_ids": [
                "resource-1",
                "resource-2",
                "resource-3",
            ],
        },
        context,
    )

    assert result == {
        "job": "cleanup",
        "resources_processed": 3,
        "attempt": 1,
        "status": "completed",
    }


@pytest.mark.asyncio
async def test_job_context_check_cancelled_allows_active_job() -> None:
    """An active context should not raise a cancellation error."""
    context = JobContext(
        job_id=uuid4(),
        attempt=1,
        max_retries=3,
        cancelled=False,
    )

    context.check_cancelled()


def test_get_job_resolves_registered_job() -> None:
    """Registered job names should resolve to fresh job instances."""
    first = get_job("send_email")
    second = get_job("send_email")

    assert isinstance(first, SendEmailJob)
    assert isinstance(second, SendEmailJob)
    assert first is not second


def test_get_job_rejects_unknown_job_name() -> None:
    """Unknown job names should fail explicitly rather than silently dispatch."""
    with pytest.raises(ValueError, match="Unknown job type"):
        get_job("unknown-job")


def test_job_default_values_are_initialized_per_instance() -> None:
    """Mutable job payloads must not be shared between Job instances."""
    first = Job(name="example", payload={})
    second = Job(name="example", payload={})

    first.payload["key"] = "value"

    assert second.payload == {}


def test_job_identifiers_are_unique_by_default() -> None:
    """Jobs should receive independent identifiers by default."""
    first = Job(name="example", payload={})
    second = Job(name="example", payload={})

    assert first.id != second.id

"""Unit tests for background job lifecycle and concrete job implementations."""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.jobs.base import BaseJob, Job, JobContext, JobStatus
from src.jobs.tasks import CleanupJob, ProcessWebhookJob, SendEmailJob, get_job


class SuccessfulJob(BaseJob):
    """Test job that completes successfully."""

    name = "successful"

    async def execute(
        self,
        payload: dict[str, object],
        context: JobContext,
    ) -> object:
        """Return the supplied payload."""
        context.check_cancelled()
        return payload


class FailingJob(BaseJob):
    """Test job that always raises an execution error."""

    name = "failing"

    async def execute(
        self,
        payload: dict[str, object],
        context: JobContext,
    ) -> object:
        """Raise a deterministic test failure."""
        raise RuntimeError("job execution failed")


@pytest.mark.asyncio
async def test_successful_job_transitions_to_succeeded() -> None:
    """A successful execution should update the complete job lifecycle."""
    job = Job(
        name=SuccessfulJob.name,
        payload={"value": "test"},
    )
    context = JobContext(
        job_id=job.id,
        attempt=1,
        max_retries=3,
    )

    result = await SuccessfulJob().run(job, context)

    assert result == {"value": "test"}
    assert job.status == JobStatus.SUCCEEDED
    assert job.attempts == 1
    assert job.started_at is not None
    assert job.completed_at is not None
    assert job.last_error is None


@pytest.mark.asyncio
async def test_failed_job_records_error_and_transitions_to_failed() -> None:
    """A retryable failure should record the error and retain failed state."""
    job = Job(
        name=FailingJob.name,
        payload={},
        max_retries=3,
    )
    context = JobContext(
        job_id=job.id,
        attempt=1,
        max_retries=3,
    )

    with pytest.raises(RuntimeError, match="job execution failed"):
        await FailingJob().run(job, context)

    assert job.status == JobStatus.FAILED
    assert job.attempts == 1
    assert job.last_error == "job execution failed"
    assert job.completed_at is not None


@pytest.mark.asyncio
async def test_failed_job_is_dead_lettered_after_retry_exhaustion() -> None:
    """A failure beyond the retry budget should become dead-lettered."""
    job = Job(
        name=FailingJob.name,
        payload={},
        max_retries=0,
    )
    context = JobContext(
        job_id=job.id,
        attempt=1,
        max_retries=0,
    )

    with pytest.raises(RuntimeError, match="job execution failed"):
        await FailingJob().run(job, context)

    assert job.status == JobStatus.DEAD_LETTERED
    assert job.retries_exhausted is True
    assert job.last_error == "job execution failed"


@pytest.mark.asyncio
async def test_job_cancellation_is_not_swallowed() -> None:
    """Cancellation should propagate instead of being converted to failure."""
    class CancelledJob(BaseJob):
        """Test job that observes cancellation through its context."""

        name = "cancelled"

        async def execute(
            self,
            payload: dict[str, object],
            context: JobContext,
        ) -> object:
            """Raise cancellation when requested."""
            context.check_cancelled()
            return payload

    job = Job(name=CancelledJob.name, payload={})
    context = JobContext(
        job_id=job.id,
        attempt=1,
        max_retries=3,
        cancelled=True,
    )

    with pytest.raises(RuntimeError, match="execution was cancelled"):
        await CancelledJob().run(job, context)

    assert job.status == JobStatus.FAILED
    assert job.last_error is not None


def test_job_mark_running_increments_attempt_count() -> None:
    """Starting a job should increment its execution attempt."""
    job = Job(name="example", payload={})

    job.mark_running()

    assert job.status == JobStatus.RUNNING
    assert job.attempts == 1
    assert job.started_at is not None


def test_job_mark_succeeded_requires_running_state() -> None:
    """A job cannot transition directly from pending to succeeded."""
    job = Job(name="example", payload={})

    with pytest.raises(ValueError, match="cannot succeed"):
        job.mark_succeeded()


def test_job_mark_failed_requires_running_state() -> None:
    """A job cannot record failure before execution starts."""
    job = Job(name="example", payload={})

    with pytest.raises(ValueError, match="cannot fail"):
        job.mark_failed("failure")


def test_job_mark_dead_lettered_requires_failed_or_running_state() -> None:
    """Dead-lettering should reject invalid lifecycle transitions."""
    job = Job(name="example", payload={})

    with pytest.raises(ValueError, match="cannot be dead-lettered"):
        job.mark_dead_lettered()


def test_retries_exhausted_is_false_when_retries_remain() -> None:
    """A job with remaining retry capacity should not be exhausted."""
    job = Job(
        name="example",
        payload={},
        max_retries=3,
    )

    job.mark_running()

    assert job.attempts == 1
    assert job.retries_exhausted is False


def test_retries_exhausted_is_true_when_retry_budget_is_consumed() -> None:
    """A job should report exhaustion after its final permitted attempt."""
    job = Job(
        name="example",
        payload={},
        max_retries=1,
    )

    job.mark_running()
    job.mark_failed("first failure")
    job.mark_running()

    assert job.attempts == 2
    assert job.retries_exhausted is True


@pytest.mark.asyncio
async def test_send_email_job_validates_required_fields() -> None:
    """Email jobs should reject incomplete delivery payloads."""
    job = SendEmailJob()
    context = JobContext(
        job_id=uuid4(),
        attempt=1,
        max_retries=3,
    )

    with pytest.raises(ValueError, match="recipient"):
        await job.execute(
            {
                "subject": "Subject",
                "body": "Body",
            },
            context,
        )


@pytest.mark.asyncio
async def test_send_email_job_returns_delivery_result() -> None:
    """A valid email payload should produce a normalized result."""
    context = JobContext(
        job_id=uuid4(),
        attempt=2,
        max_retries=3,
    )

    result = await SendEmailJob().execute(
        {
            "recipient": "  user@example.com ",
            "subject": "  Welcome ",
            "body": "  Hello ",
        },
        context,
    )

    assert result == {
        "job": "send_email",
        "recipient": "user@example.com",
        "subject": "Welcome",
        "attempt": 2,
        "status": "sent",
    }


@pytest.mark.asyncio
async def test_process_webhook_job_validates_event_fields() -> None:
    """Webhook jobs should reject missing event identifiers."""
    context = JobContext(
        job_id=uuid4(),
        attempt=1,
        max_retries=3,
    )

    with pytest.raises(ValueError, match="event_id"):
        await ProcessWebhookJob().execute(
            {"event_type": "payment.created"},
            context,
        )


@pytest.mark.asyncio
async def test_process_webhook_job_returns_processing_result() -> None:
    """A valid webhook payload should produce a processing result."""
    context = JobContext(
        job_id=uuid4(),
        attempt=1,
        max_retries=3,
    )

    result = await ProcessWebhookJob().execute(
        {
            "event_id": "evt_123",
            "event_type": "payment.created",
        },
        context,
    )

    assert result == {
        "job": "process_webhook",
        "event_id": "evt_123",
        "event_type": "payment.created",
        "attempt": 1,
        "status": "processed",
    }


@pytest.mark.asyncio
async def test_cleanup_job_validates_resource_ids() -> None:
    """Cleanup jobs should require a list of string resource identifiers."""
    context = JobContext(
        job_id=uuid4(),
        attempt=1,
        max_retries=3,
    )

    with pytest.raises(ValueError, match="resource_ids must be a list"):
        await CleanupJob().execute(
            {"resource_ids": "resource-1"},
            context,
        )


@pytest.mark.asyncio
async def test_cleanup_job_returns_processed_resource_count() -> None:
    """Cleanup jobs should report the number of processed resources."""
    context = JobContext(
        job_id=uuid4(),
        attempt=1,
        max_retries=3,
    )

    result = await CleanupJob().execute(
        {
            "resource_ids": [
                "resource-1",
                "resource-2",
                "resource-3",
            ],
        },
        context,
    )

    assert result == {
        "job": "cleanup",
        "resources_processed": 3,
        "attempt": 1,
        "status": "completed",
    }


@pytest.mark.asyncio
async def test_job_context_check_cancelled_allows_active_job() -> None:
    """An active context should not raise a cancellation error."""
    context = JobContext(
        job_id=uuid4(),
        attempt=1,
        max_retries=3,
        cancelled=False,
    )

    context.check_cancelled()


def test_get_job_resolves_registered_job() -> None:
    """Registered job names should resolve to fresh job instances."""
    first = get_job("send_email")
    second = get_job("send_email")

    assert isinstance(first, SendEmailJob)
    assert isinstance(second, SendEmailJob)
    assert first is not second


def test_get_job_rejects_unknown_job_name() -> None:
    """Unknown job names should fail explicitly rather than silently dispatch."""
    with pytest.raises(ValueError, match="Unknown job type"):
        get_job("unknown-job")


def test_job_default_values_are_initialized_per_instance() -> None:
    """Mutable job payloads must not be shared between Job instances."""
    first = Job(name="example", payload={})
    second = Job(name="example", payload={})

    first.payload["key"] = "value"

    assert second.payload == {}


def test_job_identifiers_are_unique_by_default() -> None:
    """Jobs should receive independent identifiers by default."""
    first = Job(name="example", payload={})
    second = Job(name="example", payload={})

    assert first.id != second.id