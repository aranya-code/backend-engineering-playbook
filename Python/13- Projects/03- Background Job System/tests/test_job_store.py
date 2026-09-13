"""Tests for durable background job persistence and lifecycle operations."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from src.jobs.base import Job, JobStatus
from src.storage.job_store import JobStore


def make_job(
    *,
    name: str = "cleanup",
    payload: dict[str, object] | None = None,
    status: JobStatus = JobStatus.PENDING,
    attempts: int = 0,
    max_retries: int = 3,
) -> Job:
    """Create a deterministic job fixture for storage tests."""
    return Job(
        name=name,
        payload=payload or {"resource_ids": ["resource-1"]},
        status=status,
        attempts=attempts,
        max_retries=max_retries,
    )


def test_create_persists_job() -> None:
    """Creating a job should make it retrievable by ID."""
    store = JobStore()
    job = make_job()

    stored = store.create(job)

    assert stored is job
    assert store.get(job.id) is job


def test_create_rejects_duplicate_job_id() -> None:
    """A job identifier must uniquely identify one persisted job."""
    store = JobStore()
    job = make_job()

    store.create(job)

    with pytest.raises(ValueError, match="already exists"):
        store.create(job)


def test_get_returns_none_for_unknown_job() -> None:
    """Looking up an unknown job should return None rather than raise."""
    store = JobStore()

    assert store.get(uuid4()) is None


def test_update_persists_existing_job() -> None:
    """Updating an existing job should replace its stored state."""
    store = JobStore()
    job = make_job()

    store.create(job)

    job.mark_running()
    updated = store.update(job)

    assert updated is job
    assert store.get(job.id) is job
    assert store.get(job.id).status is JobStatus.RUNNING


def test_update_rejects_unknown_job() -> None:
    """Updating a job that was never persisted should fail explicitly."""
    store = JobStore()
    job = make_job()

    with pytest.raises(ValueError, match="not found"):
        store.update(job)


def test_delete_removes_job() -> None:
    """Deleting a persisted job should make it unavailable."""
    store = JobStore()
    job = make_job()

    store.create(job)

    assert store.delete(job.id) is True
    assert store.get(job.id) is None


def test_delete_returns_false_for_unknown_job() -> None:
    """Deleting an unknown job should be an idempotent no-op."""
    store = JobStore()

    assert store.delete(uuid4()) is False


def test_list_returns_all_jobs() -> None:
    """Listing jobs should return every persisted job."""
    store = JobStore()
    first = make_job(name="cleanup")
    second = make_job(name="send_email")

    store.create(first)
    store.create(second)

    jobs = store.list()

    assert {job.id for job in jobs} == {first.id, second.id}


def test_list_returns_empty_collection_when_store_is_empty() -> None:
    """An empty store should produce an empty result."""
    store = JobStore()

    assert store.list() == []


def test_list_filters_by_status() -> None:
    """Status filtering should return only jobs in the requested state."""
    store = JobStore()
    pending = make_job(status=JobStatus.PENDING)
    failed = make_job(status=JobStatus.FAILED)

    store.create(pending)
    store.create(failed)

    assert store.list(status=JobStatus.PENDING) == [pending]
    assert store.list(status=JobStatus.FAILED) == [failed]


def test_list_filters_by_job_name() -> None:
    """Job-name filtering should isolate one registered job type."""
    store = JobStore()
    cleanup = make_job(name="cleanup")
    email = make_job(name="send_email")

    store.create(cleanup)
    store.create(email)

    assert store.list(name="cleanup") == [cleanup]


def test_list_filters_by_status_and_name() -> None:
    """Multiple filters should be applied together."""
    store = JobStore()
    matching = make_job(
        name="cleanup",
        status=JobStatus.FAILED,
    )
    wrong_status = make_job(
        name="cleanup",
        status=JobStatus.SUCCEEDED,
    )
    wrong_name = make_job(
        name="send_email",
        status=JobStatus.FAILED,
    )

    store.create(matching)
    store.create(wrong_status)
    store.create(wrong_name)

    assert store.list(
        name="cleanup",
        status=JobStatus.FAILED,
    ) == [matching]


def test_count_returns_number_of_persisted_jobs() -> None:
    """Count should reflect the current number of stored jobs."""
    store = JobStore()
    first = make_job()
    second = make_job()

    assert store.count() == 0

    store.create(first)
    assert store.count() == 1

    store.create(second)
    assert store.count() == 2

    store.delete(first.id)
    assert store.count() == 1


def test_clear_removes_all_jobs() -> None:
    """Clearing the store should remove every persisted job."""
    store = JobStore()

    store.create(make_job())
    store.create(make_job(name="send_email"))

    store.clear()

    assert store.count() == 0
    assert store.list() == []


def test_create_preserves_job_payload() -> None:
    """The store should persist the complete job payload."""
    store = JobStore()
    payload = {
        "customer_id": "customer-123",
        "resource_ids": ["resource-1", "resource-2"],
        "metadata": {"source": "scheduler"},
    }
    job = make_job(payload=payload)

    store.create(job)

    stored = store.get(job.id)

    assert stored is not None
    assert stored.payload == payload


def test_update_preserves_lifecycle_metadata() -> None:
    """State transitions should remain intact after persistence updates."""
    store = JobStore()
    job = make_job()

    store.create(job)

    job.mark_running()
    job.mark_failed("temporary downstream failure")

    store.update(job)

    stored = store.get(job.id)

    assert stored is not None
    assert stored.status is JobStatus.FAILED
    assert stored.attempts == 1
    assert stored.last_error == "temporary downstream failure"
    assert stored.started_at is not None
    assert stored.completed_at is not None


def test_job_timestamps_are_timezone_aware() -> None:
    """Persisted job timestamps should use explicit timezone information."""
    store = JobStore()
    job = make_job()

    store.create(job)

    stored = store.get(job.id)

    assert stored is not None
    assert stored.created_at.tzinfo is not None
    assert stored.created_at.utcoffset() is not None


def test_store_returns_jobs_in_creation_order() -> None:
    """Listing should be deterministic for the in-memory implementation."""
    store = JobStore()
    first = make_job()
    second = make_job()
    third = make_job()

    store.create(first)
    store.create(second)
    store.create(third)

    assert store.list() == [first, second, third]


def test_list_returns_copy_of_collection() -> None:
    """Mutating a returned list must not mutate store membership."""
    store = JobStore()
    job = make_job()

    store.create(job)

    jobs = store.list()
    jobs.clear()

    assert store.count() == 1
    assert store.get(job.id) is job


def test_get_due_jobs_returns_pending_jobs_before_deadline() -> None:
    """Due-job queries should identify pending work whose deadline has passed."""
    store = JobStore()
    due_job = make_job(status=JobStatus.PENDING)
    future_job = make_job(status=JobStatus.PENDING)

    store.create(due_job)
    store.create(future_job)

    due_at = datetime.now(timezone.utc)
    future_at = due_at + timedelta(minutes=5)

    due_jobs = store.get_due_jobs(due_at)

    assert due_job in due_jobs
    assert future_job not in due_jobs


def test_get_due_jobs_excludes_completed_jobs() -> None:
    """Completed jobs must never be returned as executable pending work."""
    store = JobStore()
    succeeded = make_job(status=JobStatus.SUCCEEDED)
    failed = make_job(status=JobStatus.FAILED)
    dead_lettered = make_job(status=JobStatus.DEAD_LETTERED)

    store.create(succeeded)
    store.create(failed)
    store.create(dead_lettered)

    due_at = datetime.now(timezone.utc)

    assert store.get_due_jobs(due_at) == []


def test_store_rejects_naive_due_time() -> None:
    """Due-time queries should require timezone-aware timestamps."""
    store = JobStore()

    with pytest.raises(ValueError, match="timezone-aware"):
        store.get_due_jobs(datetime(2026, 1, 1, 12, 0))


def test_store_isolates_multiple_job_types() -> None:
    """Jobs with different names should coexist without overwriting each other."""
    store = JobStore()
    cleanup = make_job(name="cleanup")
    webhook = make_job(name="process_webhook")
    email = make_job(name="send_email")

    store.create(cleanup)
    store.create(webhook)
    store.create(email)

    assert store.count() == 3
    assert store.list(name="cleanup") == [cleanup]
    assert store.list(name="process_webhook") == [webhook]
    assert store.list(name="send_email") == [email]

"""Tests for durable background job persistence and lifecycle operations."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from src.jobs.base import Job, JobStatus
from src.storage.job_store import JobStore


def make_job(
    *,
    name: str = "cleanup",
    payload: dict[str, object] | None = None,
    status: JobStatus = JobStatus.PENDING,
    attempts: int = 0,
    max_retries: int = 3,
) -> Job:
    """Create a deterministic job fixture for storage tests."""
    return Job(
        name=name,
        payload=payload or {"resource_ids": ["resource-1"]},
        status=status,
        attempts=attempts,
        max_retries=max_retries,
    )


def test_create_persists_job() -> None:
    """Creating a job should make it retrievable by ID."""
    store = JobStore()
    job = make_job()

    stored = store.create(job)

    assert stored is job
    assert store.get(job.id) is job


def test_create_rejects_duplicate_job_id() -> None:
    """A job identifier must uniquely identify one persisted job."""
    store = JobStore()
    job = make_job()

    store.create(job)

    with pytest.raises(ValueError, match="already exists"):
        store.create(job)


def test_get_returns_none_for_unknown_job() -> None:
    """Looking up an unknown job should return None rather than raise."""
    store = JobStore()

    assert store.get(uuid4()) is None


def test_update_persists_existing_job() -> None:
    """Updating an existing job should replace its stored state."""
    store = JobStore()
    job = make_job()

    store.create(job)

    job.mark_running()
    updated = store.update(job)

    assert updated is job
    assert store.get(job.id) is job
    assert store.get(job.id).status is JobStatus.RUNNING


def test_update_rejects_unknown_job() -> None:
    """Updating a job that was never persisted should fail explicitly."""
    store = JobStore()
    job = make_job()

    with pytest.raises(ValueError, match="not found"):
        store.update(job)


def test_delete_removes_job() -> None:
    """Deleting a persisted job should make it unavailable."""
    store = JobStore()
    job = make_job()

    store.create(job)

    assert store.delete(job.id) is True
    assert store.get(job.id) is None


def test_delete_returns_false_for_unknown_job() -> None:
    """Deleting an unknown job should be an idempotent no-op."""
    store = JobStore()

    assert store.delete(uuid4()) is False


def test_list_returns_all_jobs() -> None:
    """Listing jobs should return every persisted job."""
    store = JobStore()
    first = make_job(name="cleanup")
    second = make_job(name="send_email")

    store.create(first)
    store.create(second)

    jobs = store.list()

    assert {job.id for job in jobs} == {first.id, second.id}


def test_list_returns_empty_collection_when_store_is_empty() -> None:
    """An empty store should produce an empty result."""
    store = JobStore()

    assert store.list() == []


def test_list_filters_by_status() -> None:
    """Status filtering should return only jobs in the requested state."""
    store = JobStore()
    pending = make_job(status=JobStatus.PENDING)
    failed = make_job(status=JobStatus.FAILED)

    store.create(pending)
    store.create(failed)

    assert store.list(status=JobStatus.PENDING) == [pending]
    assert store.list(status=JobStatus.FAILED) == [failed]


def test_list_filters_by_job_name() -> None:
    """Job-name filtering should isolate one registered job type."""
    store = JobStore()
    cleanup = make_job(name="cleanup")
    email = make_job(name="send_email")

    store.create(cleanup)
    store.create(email)

    assert store.list(name="cleanup") == [cleanup]


def test_list_filters_by_status_and_name() -> None:
    """Multiple filters should be applied together."""
    store = JobStore()
    matching = make_job(
        name="cleanup",
        status=JobStatus.FAILED,
    )
    wrong_status = make_job(
        name="cleanup",
        status=JobStatus.SUCCEEDED,
    )
    wrong_name = make_job(
        name="send_email",
        status=JobStatus.FAILED,
    )

    store.create(matching)
    store.create(wrong_status)
    store.create(wrong_name)

    assert store.list(
        name="cleanup",
        status=JobStatus.FAILED,
    ) == [matching]


def test_count_returns_number_of_persisted_jobs() -> None:
    """Count should reflect the current number of stored jobs."""
    store = JobStore()
    first = make_job()
    second = make_job()

    assert store.count() == 0

    store.create(first)
    assert store.count() == 1

    store.create(second)
    assert store.count() == 2

    store.delete(first.id)
    assert store.count() == 1


def test_clear_removes_all_jobs() -> None:
    """Clearing the store should remove every persisted job."""
    store = JobStore()

    store.create(make_job())
    store.create(make_job(name="send_email"))

    store.clear()

    assert store.count() == 0
    assert store.list() == []


def test_create_preserves_job_payload() -> None:
    """The store should persist the complete job payload."""
    store = JobStore()
    payload = {
        "customer_id": "customer-123",
        "resource_ids": ["resource-1", "resource-2"],
        "metadata": {"source": "scheduler"},
    }
    job = make_job(payload=payload)

    store.create(job)

    stored = store.get(job.id)

    assert stored is not None
    assert stored.payload == payload


def test_update_preserves_lifecycle_metadata() -> None:
    """State transitions should remain intact after persistence updates."""
    store = JobStore()
    job = make_job()

    store.create(job)

    job.mark_running()
    job.mark_failed("temporary downstream failure")

    store.update(job)

    stored = store.get(job.id)

    assert stored is not None
    assert stored.status is JobStatus.FAILED
    assert stored.attempts == 1
    assert stored.last_error == "temporary downstream failure"
    assert stored.started_at is not None
    assert stored.completed_at is not None


def test_job_timestamps_are_timezone_aware() -> None:
    """Persisted job timestamps should use explicit timezone information."""
    store = JobStore()
    job = make_job()

    store.create(job)

    stored = store.get(job.id)

    assert stored is not None
    assert stored.created_at.tzinfo is not None
    assert stored.created_at.utcoffset() is not None


def test_store_returns_jobs_in_creation_order() -> None:
    """Listing should be deterministic for the in-memory implementation."""
    store = JobStore()
    first = make_job()
    second = make_job()
    third = make_job()

    store.create(first)
    store.create(second)
    store.create(third)

    assert store.list() == [first, second, third]


def test_list_returns_copy_of_collection() -> None:
    """Mutating a returned list must not mutate store membership."""
    store = JobStore()
    job = make_job()

    store.create(job)

    jobs = store.list()
    jobs.clear()

    assert store.count() == 1
    assert store.get(job.id) is job


def test_get_due_jobs_returns_pending_jobs_before_deadline() -> None:
    """Due-job queries should identify pending work whose deadline has passed."""
    store = JobStore()
    due_job = make_job(status=JobStatus.PENDING)
    future_job = make_job(status=JobStatus.PENDING)

    store.create(due_job)
    store.create(future_job)

    due_at = datetime.now(timezone.utc)
    future_at = due_at + timedelta(minutes=5)

    due_jobs = store.get_due_jobs(due_at)

    assert due_job in due_jobs
    assert future_job not in due_jobs


def test_get_due_jobs_excludes_completed_jobs() -> None:
    """Completed jobs must never be returned as executable pending work."""
    store = JobStore()
    succeeded = make_job(status=JobStatus.SUCCEEDED)
    failed = make_job(status=JobStatus.FAILED)
    dead_lettered = make_job(status=JobStatus.DEAD_LETTERED)

    store.create(succeeded)
    store.create(failed)
    store.create(dead_lettered)

    due_at = datetime.now(timezone.utc)

    assert store.get_due_jobs(due_at) == []


def test_store_rejects_naive_due_time() -> None:
    """Due-time queries should require timezone-aware timestamps."""
    store = JobStore()

    with pytest.raises(ValueError, match="timezone-aware"):
        store.get_due_jobs(datetime(2026, 1, 1, 12, 0))


def test_store_isolates_multiple_job_types() -> None:
    """Jobs with different names should coexist without overwriting each other."""
    store = JobStore()
    cleanup = make_job(name="cleanup")
    webhook = make_job(name="process_webhook")
    email = make_job(name="send_email")

    store.create(cleanup)
    store.create(webhook)
    store.create(email)

    assert store.count() == 3
    assert store.list(name="cleanup") == [cleanup]
    assert store.list(name="process_webhook") == [webhook]
    assert store.list(name="send_email") == [email]