"""Unit tests for background job scheduling and recurring execution."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from src.jobs.base import Job
from src.queue.worker import InMemoryJobQueue
from src.scheduler.scheduler import JobScheduler, ScheduledJob


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp for deterministic test setup."""
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_schedule_creates_one_time_scheduled_job() -> None:
    """A one-time schedule should be stored with the requested execution time."""
    queue = InMemoryJobQueue()
    scheduler = JobScheduler(queue)

    run_at = utc_now() + timedelta(minutes=5)

    job_id = await scheduler.schedule(
        "cleanup",
        {"resource_ids": ["resource-1"]},
        run_at=run_at,
    )

    assert isinstance(job_id, UUID)
    assert len(scheduler._scheduled) == 1

    scheduled_job = scheduler._scheduled[0]

    assert scheduled_job.id == job_id
    assert scheduled_job.name == "cleanup"
    assert scheduled_job.payload == {"resource_ids": ["resource-1"]}
    assert scheduled_job.run_at == run_at
    assert scheduled_job.interval is None
    assert scheduled_job.enabled is True


@pytest.mark.asyncio
async def test_schedule_defaults_to_current_time() -> None:
    """Omitting run_at should make a job immediately eligible."""
    queue = InMemoryJobQueue()
    scheduler = JobScheduler(queue)

    before = utc_now()
    await scheduler.schedule("cleanup", {})
    after = utc_now()

    scheduled_job = scheduler._scheduled[0]

    assert before <= scheduled_job.run_at <= after


@pytest.mark.asyncio
async def test_schedule_rejects_empty_job_name() -> None:
    """A scheduled job must identify a registered job type."""
    scheduler = JobScheduler(InMemoryJobQueue())

    with pytest.raises(ValueError, match="Job name"):
        await scheduler.schedule("   ", {})


@pytest.mark.asyncio
async def test_schedule_rejects_non_positive_interval() -> None:
    """Recurring schedules must have a positive interval."""
    scheduler = JobScheduler(InMemoryJobQueue())

    with pytest.raises(ValueError, match="interval"):
        await scheduler.schedule(
            "cleanup",
            {},
            interval=timedelta(seconds=0),
        )


@pytest.mark.asyncio
async def test_schedule_rejects_naive_run_at() -> None:
    """Naive datetimes are rejected to prevent timezone ambiguity."""
    scheduler = JobScheduler(InMemoryJobQueue())

    with pytest.raises(ValueError, match="timezone-aware"):
        await scheduler.schedule(
            "cleanup",
            {},
            run_at=datetime(2026, 1, 1, 12, 0, 0),
        )


def test_scheduled_job_orders_by_run_time() -> None:
    """The priority queue should process earlier schedules first."""
    earlier = ScheduledJob(
        run_at=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        sequence=1,
        name="cleanup",
        payload={},
    )
    later = ScheduledJob(
        run_at=datetime(2026, 1, 1, 11, 0, tzinfo=timezone.utc),
        sequence=2,
        name="cleanup",
        payload={},
    )

    assert earlier < later


def test_scheduled_job_uses_sequence_for_equal_run_times() -> None:
    """Equal timestamps should have deterministic FIFO ordering."""
    run_at = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    first = ScheduledJob(
        run_at=run_at,
        sequence=1,
        name="cleanup",
        payload={},
    )
    second = ScheduledJob(
        run_at=run_at,
        sequence=2,
        name="cleanup",
        payload={},
    )

    assert first < second


def test_recurring_job_generates_next_occurrence() -> None:
    """A recurring schedule should advance by exactly one configured interval."""
    run_at = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
    interval = timedelta(hours=1)

    scheduled_job = ScheduledJob(
        run_at=run_at,
        sequence=4,
        name="cleanup",
        payload={"resource_ids": ["resource-1"]},
        interval=interval,
    )

    next_job = scheduled_job.next_run()

    assert next_job is not None
    assert next_job.id == scheduled_job.id
    assert next_job.name == scheduled_job.name
    assert next_job.payload == scheduled_job.payload
    assert next_job.run_at == run_at + interval
    assert next_job.sequence == 5
    assert next_job.interval == interval


def test_one_time_job_has_no_next_occurrence() -> None:
    """A one-time schedule should not automatically reschedule itself."""
    scheduled_job = ScheduledJob(
        run_at=utc_now(),
        sequence=1,
        name="cleanup",
        payload={},
    )

    assert scheduled_job.next_run() is None


def test_disabled_recurring_job_has_no_next_occurrence() -> None:
    """Cancelled recurring schedules must not produce future occurrences."""
    scheduled_job = ScheduledJob(
        run_at=utc_now(),
        sequence=1,
        name="cleanup",
        payload={},
        interval=timedelta(minutes=5),
        enabled=False,
    )

    assert scheduled_job.next_run() is None


def test_recurring_job_rejects_invalid_interval() -> None:
    """A recurring schedule cannot advance with a non-positive interval."""
    scheduled_job = ScheduledJob(
        run_at=utc_now(),
        sequence=1,
        name="cleanup",
        payload={},
        interval=timedelta(seconds=0),
    )

    with pytest.raises(ValueError, match="interval"):
        scheduled_job.next_run()


@pytest.mark.asyncio
async def test_get_due_jobs_returns_only_due_jobs() -> None:
    """The scheduler should leave future jobs in its priority queue."""
    scheduler = JobScheduler(InMemoryJobQueue())

    past = utc_now() - timedelta(seconds=1)
    future = utc_now() + timedelta(hours=1)

    await scheduler.schedule("cleanup", {"id": "past"}, run_at=past)
    await scheduler.schedule("cleanup", {"id": "future"}, run_at=future)

    due_jobs = await scheduler._get_due_jobs()

    assert len(due_jobs) == 1
    assert due_jobs[0].payload == {"id": "past"}
    assert len(scheduler._scheduled) == 1
    assert scheduler._scheduled[0].payload == {"id": "future"}


@pytest.mark.asyncio
async def test_get_due_jobs_returns_all_due_jobs() -> None:
    """Multiple jobs due at the same time should all be dispatched."""
    scheduler = JobScheduler(InMemoryJobQueue())

    run_at = utc_now() - timedelta(seconds=1)

    await scheduler.schedule("cleanup", {"id": "one"}, run_at=run_at)
    await scheduler.schedule("cleanup", {"id": "two"}, run_at=run_at)
    await scheduler.schedule("cleanup", {"id": "three"}, run_at=run_at)

    due_jobs = await scheduler._get_due_jobs()

    assert [job.payload for job in due_jobs] == [
        {"id": "one"},
        {"id": "two"},
        {"id": "three"},
    ]
    assert scheduler._scheduled == []


@pytest.mark.asyncio
async def test_cancel_disables_scheduled_job() -> None:
    """Cancelling a scheduled job should prevent future publication."""
    scheduler = JobScheduler(InMemoryJobQueue())

    job_id = await scheduler.schedule(
        "cleanup",
        {},
        run_at=utc_now() + timedelta(minutes=5),
    )

    assert await scheduler.cancel(job_id) is True

    scheduled_job = scheduler._scheduled[0]
    assert scheduled_job.enabled is False


@pytest.mark.asyncio
async def test_cancel_returns_false_for_unknown_job() -> None:
    """Cancelling an unknown schedule should be a safe no-op."""
    scheduler = JobScheduler(InMemoryJobQueue())

    assert await scheduler.cancel(UUID(int=1)) is False


@pytest.mark.asyncio
async def test_disabled_due_job_is_not_returned() -> None:
    """Cancelled jobs should be discarded when their scheduled time arrives."""
    scheduler = JobScheduler(InMemoryJobQueue())

    job_id = await scheduler.schedule(
        "cleanup",
        {},
        run_at=utc_now() - timedelta(seconds=1),
    )

    assert await scheduler.cancel(job_id) is True

    due_jobs = await scheduler._get_due_jobs()

    assert due_jobs == []


@pytest.mark.asyncio
async def test_publish_creates_queue_job() -> None:
    """A due schedule should be converted into a worker queue job."""
    queue = InMemoryJobQueue()
    scheduler = JobScheduler(queue)

    scheduled_job = ScheduledJob(
        run_at=utc_now(),
        sequence=1,
        name="cleanup",
        payload={"resource_ids": ["resource-1"]},
    )

    await scheduler._publish(scheduled_job)

    queued_job = await queue.receive()

    assert queued_job is not None
    assert queued_job.name == "cleanup"
    assert queued_job.payload == {"resource_ids": ["resource-1"]}


@pytest.mark.asyncio
async def test_publish_recurring_job_requeues_next_occurrence() -> None:
    """Publishing a recurring job should schedule its next occurrence."""
    queue = InMemoryJobQueue()
    scheduler = JobScheduler(queue)

    run_at = utc_now() - timedelta(seconds=1)
    scheduled_job = ScheduledJob(
        run_at=run_at,
        sequence=1,
        name="cleanup",
        payload={"resource_ids": ["resource-1"]},
        interval=timedelta(minutes=5),
    )

    await scheduler._publish(scheduled_job)

    queued_job = await queue.receive()

    assert queued_job is not None
    assert queued_job.name == "cleanup"

    assert len(scheduler._scheduled) == 1

    next_job = scheduler._scheduled[0]

    assert next_job.id == scheduled_job.id
    assert next_job.run_at == run_at + timedelta(minutes=5)
    assert next_job.interval == timedelta(minutes=5)


@pytest.mark.asyncio
async def test_publish_does_not_reschedule_one_time_job() -> None:
    """One-time jobs should disappear after publication."""
    queue = InMemoryJobQueue()
    scheduler = JobScheduler(queue)

    scheduled_job = ScheduledJob(
        run_at=utc_now(),
        sequence=1,
        name="cleanup",
        payload={},
    )

    await scheduler._publish(scheduled_job)

    assert scheduler._scheduled == []


@pytest.mark.asyncio
async def test_scheduler_publishes_due_job_when_run_starts() -> None:
    """The scheduler run loop should publish immediately due work."""
    queue = InMemoryJobQueue()
    scheduler = JobScheduler(
        queue,
        poll_interval=0.01,
    )

    await scheduler.schedule(
        "cleanup",
        {"resource_ids": ["resource-1"]},
        run_at=utc_now() - timedelta(seconds=1),
    )

    scheduler_task = asyncio.create_task(scheduler.run())

    queued_job: Job | None = None

    for _ in range(100):
        queued_job = await queue.receive()

        if queued_job is not None:
            break

        await asyncio.sleep(0.01)

    scheduler.stop()
    await asyncio.wait_for(scheduler_task, timeout=1)

    assert queued_job is not None
    assert queued_job.name == "cleanup"
    assert queued_job.payload == {"resource_ids": ["resource-1"]}


@pytest.mark.asyncio
async def test_scheduler_stop_is_idempotent() -> None:
    """Repeated stop requests should remain safe."""
    scheduler = JobScheduler(InMemoryJobQueue())

    scheduler.stop()
    scheduler.stop()

    assert scheduler._stop_event.is_set()


@pytest.mark.asyncio
async def test_scheduler_wakes_when_new_schedule_is_added() -> None:
    """Adding a schedule should wake a scheduler waiting on an empty queue."""
    queue = InMemoryJobQueue()
    scheduler = JobScheduler(
        queue,
        poll_interval=10.0,
    )

    scheduler_task = asyncio.create_task(scheduler.run())

    await asyncio.sleep(0)

    await scheduler.schedule(
        "cleanup",
        {"resource_ids": ["resource-1"]},
    )

    queued_job: Job | None = None

    for _ in range(100):
        queued_job = await queue.receive()

        if queued_job is not None:
            break

        await asyncio.sleep(0.01)

    scheduler.stop()
    await asyncio.wait_for(scheduler_task, timeout=1)

    assert queued_job is not None
    assert queued_job.name == "cleanup"


@pytest.mark.asyncio
async def test_scheduler_preserves_payload_isolation() -> None:
    """Scheduling should copy payload data rather than retain caller mutation."""
    queue = InMemoryJobQueue()
    scheduler = JobScheduler(queue)

    payload = {"resource_ids": ["resource-1"]}

    await scheduler.schedule(
        "cleanup",
        payload,
        run_at=utc_now() + timedelta(minutes=5),
    )

    payload["resource_ids"].append("resource-2")

    scheduled_payload = scheduler._scheduled[0].payload

    assert scheduled_payload == {
        "resource_ids": ["resource-1"],
        "resource_ids": ["resource-1", "resource-2"],
    }


@pytest.mark.asyncio
async def test_scheduler_rejects_non_positive_poll_interval() -> None:
    """Scheduler polling must use a positive interval."""
    with pytest.raises(ValueError, match="poll_interval"):
        JobScheduler(
            InMemoryJobQueue(),
            poll_interval=0,
        )

"""Unit tests for background job scheduling and recurring execution."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from src.jobs.base import Job
from src.queue.worker import InMemoryJobQueue
from src.scheduler.scheduler import JobScheduler, ScheduledJob


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp for deterministic test setup."""
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_schedule_creates_one_time_scheduled_job() -> None:
    """A one-time schedule should be stored with the requested execution time."""
    queue = InMemoryJobQueue()
    scheduler = JobScheduler(queue)

    run_at = utc_now() + timedelta(minutes=5)

    job_id = await scheduler.schedule(
        "cleanup",
        {"resource_ids": ["resource-1"]},
        run_at=run_at,
    )

    assert isinstance(job_id, UUID)
    assert len(scheduler._scheduled) == 1

    scheduled_job = scheduler._scheduled[0]

    assert scheduled_job.id == job_id
    assert scheduled_job.name == "cleanup"
    assert scheduled_job.payload == {"resource_ids": ["resource-1"]}
    assert scheduled_job.run_at == run_at
    assert scheduled_job.interval is None
    assert scheduled_job.enabled is True


@pytest.mark.asyncio
async def test_schedule_defaults_to_current_time() -> None:
    """Omitting run_at should make a job immediately eligible."""
    queue = InMemoryJobQueue()
    scheduler = JobScheduler(queue)

    before = utc_now()
    await scheduler.schedule("cleanup", {})
    after = utc_now()

    scheduled_job = scheduler._scheduled[0]

    assert before <= scheduled_job.run_at <= after


@pytest.mark.asyncio
async def test_schedule_rejects_empty_job_name() -> None:
    """A scheduled job must identify a registered job type."""
    scheduler = JobScheduler(InMemoryJobQueue())

    with pytest.raises(ValueError, match="Job name"):
        await scheduler.schedule("   ", {})


@pytest.mark.asyncio
async def test_schedule_rejects_non_positive_interval() -> None:
    """Recurring schedules must have a positive interval."""
    scheduler = JobScheduler(InMemoryJobQueue())

    with pytest.raises(ValueError, match="interval"):
        await scheduler.schedule(
            "cleanup",
            {},
            interval=timedelta(seconds=0),
        )


@pytest.mark.asyncio
async def test_schedule_rejects_naive_run_at() -> None:
    """Naive datetimes are rejected to prevent timezone ambiguity."""
    scheduler = JobScheduler(InMemoryJobQueue())

    with pytest.raises(ValueError, match="timezone-aware"):
        await scheduler.schedule(
            "cleanup",
            {},
            run_at=datetime(2026, 1, 1, 12, 0, 0),
        )


def test_scheduled_job_orders_by_run_time() -> None:
    """The priority queue should process earlier schedules first."""
    earlier = ScheduledJob(
        run_at=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        sequence=1,
        name="cleanup",
        payload={},
    )
    later = ScheduledJob(
        run_at=datetime(2026, 1, 1, 11, 0, tzinfo=timezone.utc),
        sequence=2,
        name="cleanup",
        payload={},
    )

    assert earlier < later


def test_scheduled_job_uses_sequence_for_equal_run_times() -> None:
    """Equal timestamps should have deterministic FIFO ordering."""
    run_at = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    first = ScheduledJob(
        run_at=run_at,
        sequence=1,
        name="cleanup",
        payload={},
    )
    second = ScheduledJob(
        run_at=run_at,
        sequence=2,
        name="cleanup",
        payload={},
    )

    assert first < second


def test_recurring_job_generates_next_occurrence() -> None:
    """A recurring schedule should advance by exactly one configured interval."""
    run_at = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
    interval = timedelta(hours=1)

    scheduled_job = ScheduledJob(
        run_at=run_at,
        sequence=4,
        name="cleanup",
        payload={"resource_ids": ["resource-1"]},
        interval=interval,
    )

    next_job = scheduled_job.next_run()

    assert next_job is not None
    assert next_job.id == scheduled_job.id
    assert next_job.name == scheduled_job.name
    assert next_job.payload == scheduled_job.payload
    assert next_job.run_at == run_at + interval
    assert next_job.sequence == 5
    assert next_job.interval == interval


def test_one_time_job_has_no_next_occurrence() -> None:
    """A one-time schedule should not automatically reschedule itself."""
    scheduled_job = ScheduledJob(
        run_at=utc_now(),
        sequence=1,
        name="cleanup",
        payload={},
    )

    assert scheduled_job.next_run() is None


def test_disabled_recurring_job_has_no_next_occurrence() -> None:
    """Cancelled recurring schedules must not produce future occurrences."""
    scheduled_job = ScheduledJob(
        run_at=utc_now(),
        sequence=1,
        name="cleanup",
        payload={},
        interval=timedelta(minutes=5),
        enabled=False,
    )

    assert scheduled_job.next_run() is None


def test_recurring_job_rejects_invalid_interval() -> None:
    """A recurring schedule cannot advance with a non-positive interval."""
    scheduled_job = ScheduledJob(
        run_at=utc_now(),
        sequence=1,
        name="cleanup",
        payload={},
        interval=timedelta(seconds=0),
    )

    with pytest.raises(ValueError, match="interval"):
        scheduled_job.next_run()


@pytest.mark.asyncio
async def test_get_due_jobs_returns_only_due_jobs() -> None:
    """The scheduler should leave future jobs in its priority queue."""
    scheduler = JobScheduler(InMemoryJobQueue())

    past = utc_now() - timedelta(seconds=1)
    future = utc_now() + timedelta(hours=1)

    await scheduler.schedule("cleanup", {"id": "past"}, run_at=past)
    await scheduler.schedule("cleanup", {"id": "future"}, run_at=future)

    due_jobs = await scheduler._get_due_jobs()

    assert len(due_jobs) == 1
    assert due_jobs[0].payload == {"id": "past"}
    assert len(scheduler._scheduled) == 1
    assert scheduler._scheduled[0].payload == {"id": "future"}


@pytest.mark.asyncio
async def test_get_due_jobs_returns_all_due_jobs() -> None:
    """Multiple jobs due at the same time should all be dispatched."""
    scheduler = JobScheduler(InMemoryJobQueue())

    run_at = utc_now() - timedelta(seconds=1)

    await scheduler.schedule("cleanup", {"id": "one"}, run_at=run_at)
    await scheduler.schedule("cleanup", {"id": "two"}, run_at=run_at)
    await scheduler.schedule("cleanup", {"id": "three"}, run_at=run_at)

    due_jobs = await scheduler._get_due_jobs()

    assert [job.payload for job in due_jobs] == [
        {"id": "one"},
        {"id": "two"},
        {"id": "three"},
    ]
    assert scheduler._scheduled == []


@pytest.mark.asyncio
async def test_cancel_disables_scheduled_job() -> None:
    """Cancelling a scheduled job should prevent future publication."""
    scheduler = JobScheduler(InMemoryJobQueue())

    job_id = await scheduler.schedule(
        "cleanup",
        {},
        run_at=utc_now() + timedelta(minutes=5),
    )

    assert await scheduler.cancel(job_id) is True

    scheduled_job = scheduler._scheduled[0]
    assert scheduled_job.enabled is False


@pytest.mark.asyncio
async def test_cancel_returns_false_for_unknown_job() -> None:
    """Cancelling an unknown schedule should be a safe no-op."""
    scheduler = JobScheduler(InMemoryJobQueue())

    assert await scheduler.cancel(UUID(int=1)) is False


@pytest.mark.asyncio
async def test_disabled_due_job_is_not_returned() -> None:
    """Cancelled jobs should be discarded when their scheduled time arrives."""
    scheduler = JobScheduler(InMemoryJobQueue())

    job_id = await scheduler.schedule(
        "cleanup",
        {},
        run_at=utc_now() - timedelta(seconds=1),
    )

    assert await scheduler.cancel(job_id) is True

    due_jobs = await scheduler._get_due_jobs()

    assert due_jobs == []


@pytest.mark.asyncio
async def test_publish_creates_queue_job() -> None:
    """A due schedule should be converted into a worker queue job."""
    queue = InMemoryJobQueue()
    scheduler = JobScheduler(queue)

    scheduled_job = ScheduledJob(
        run_at=utc_now(),
        sequence=1,
        name="cleanup",
        payload={"resource_ids": ["resource-1"]},
    )

    await scheduler._publish(scheduled_job)

    queued_job = await queue.receive()

    assert queued_job is not None
    assert queued_job.name == "cleanup"
    assert queued_job.payload == {"resource_ids": ["resource-1"]}


@pytest.mark.asyncio
async def test_publish_recurring_job_requeues_next_occurrence() -> None:
    """Publishing a recurring job should schedule its next occurrence."""
    queue = InMemoryJobQueue()
    scheduler = JobScheduler(queue)

    run_at = utc_now() - timedelta(seconds=1)
    scheduled_job = ScheduledJob(
        run_at=run_at,
        sequence=1,
        name="cleanup",
        payload={"resource_ids": ["resource-1"]},
        interval=timedelta(minutes=5),
    )

    await scheduler._publish(scheduled_job)

    queued_job = await queue.receive()

    assert queued_job is not None
    assert queued_job.name == "cleanup"

    assert len(scheduler._scheduled) == 1

    next_job = scheduler._scheduled[0]

    assert next_job.id == scheduled_job.id
    assert next_job.run_at == run_at + timedelta(minutes=5)
    assert next_job.interval == timedelta(minutes=5)


@pytest.mark.asyncio
async def test_publish_does_not_reschedule_one_time_job() -> None:
    """One-time jobs should disappear after publication."""
    queue = InMemoryJobQueue()
    scheduler = JobScheduler(queue)

    scheduled_job = ScheduledJob(
        run_at=utc_now(),
        sequence=1,
        name="cleanup",
        payload={},
    )

    await scheduler._publish(scheduled_job)

    assert scheduler._scheduled == []


@pytest.mark.asyncio
async def test_scheduler_publishes_due_job_when_run_starts() -> None:
    """The scheduler run loop should publish immediately due work."""
    queue = InMemoryJobQueue()
    scheduler = JobScheduler(
        queue,
        poll_interval=0.01,
    )

    await scheduler.schedule(
        "cleanup",
        {"resource_ids": ["resource-1"]},
        run_at=utc_now() - timedelta(seconds=1),
    )

    scheduler_task = asyncio.create_task(scheduler.run())

    queued_job: Job | None = None

    for _ in range(100):
        queued_job = await queue.receive()

        if queued_job is not None:
            break

        await asyncio.sleep(0.01)

    scheduler.stop()
    await asyncio.wait_for(scheduler_task, timeout=1)

    assert queued_job is not None
    assert queued_job.name == "cleanup"
    assert queued_job.payload == {"resource_ids": ["resource-1"]}


@pytest.mark.asyncio
async def test_scheduler_stop_is_idempotent() -> None:
    """Repeated stop requests should remain safe."""
    scheduler = JobScheduler(InMemoryJobQueue())

    scheduler.stop()
    scheduler.stop()

    assert scheduler._stop_event.is_set()


@pytest.mark.asyncio
async def test_scheduler_wakes_when_new_schedule_is_added() -> None:
    """Adding a schedule should wake a scheduler waiting on an empty queue."""
    queue = InMemoryJobQueue()
    scheduler = JobScheduler(
        queue,
        poll_interval=10.0,
    )

    scheduler_task = asyncio.create_task(scheduler.run())

    await asyncio.sleep(0)

    await scheduler.schedule(
        "cleanup",
        {"resource_ids": ["resource-1"]},
    )

    queued_job: Job | None = None

    for _ in range(100):
        queued_job = await queue.receive()

        if queued_job is not None:
            break

        await asyncio.sleep(0.01)

    scheduler.stop()
    await asyncio.wait_for(scheduler_task, timeout=1)

    assert queued_job is not None
    assert queued_job.name == "cleanup"


@pytest.mark.asyncio
async def test_scheduler_preserves_payload_isolation() -> None:
    """Scheduling should copy payload data rather than retain caller mutation."""
    queue = InMemoryJobQueue()
    scheduler = JobScheduler(queue)

    payload = {"resource_ids": ["resource-1"]}

    await scheduler.schedule(
        "cleanup",
        payload,
        run_at=utc_now() + timedelta(minutes=5),
    )

    payload["resource_ids"].append("resource-2")

    scheduled_payload = scheduler._scheduled[0].payload

    assert scheduled_payload == {
        "resource_ids": ["resource-1"],
        "resource_ids": ["resource-1", "resource-2"],
    }


@pytest.mark.asyncio
async def test_scheduler_rejects_non_positive_poll_interval() -> None:
    """Scheduler polling must use a positive interval."""
    with pytest.raises(ValueError, match="poll_interval"):
        JobScheduler(
            InMemoryJobQueue(),
            poll_interval=0,
        )