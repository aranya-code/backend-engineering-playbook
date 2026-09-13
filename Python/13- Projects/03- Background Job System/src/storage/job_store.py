"""Persistent job-state storage for the background job system."""

from __future__ import annotations

from datetime import datetime, timezone
from threading import RLock
from typing import Final
from uuid import UUID

from src.jobs.base import Job, JobStatus


class JobNotFoundError(LookupError):
    """Raised when a requested job does not exist in the job store."""


class JobStateError(ValueError):
    """Raised when an invalid job-state transition is requested."""


class JobStore:
    """Provide thread-safe persistence semantics for background job state.

    This implementation uses process-local memory so the project can run
    without an external database. Production deployments should replace this
    implementation with a durable store such as PostgreSQL or Redis while
    preserving the repository-style interface used by workers and services.
    """

    _TERMINAL_STATES: Final[frozenset[JobStatus]] = frozenset(
        {
            JobStatus.SUCCEEDED,
            JobStatus.DEAD_LETTERED,
        }
    )

    def __init__(self) -> None:
        self._jobs: dict[UUID, Job] = {}
        self._lock = RLock()

    def create(self, job: Job) -> Job:
        """Persist a new job and reject duplicate identifiers."""
        with self._lock:
            if job.id in self._jobs:
                raise JobStateError(f"Job {job.id} already exists.")

            self._jobs[job.id] = job
            return job

    def get(self, job_id: UUID) -> Job:
        """Return a job by identifier or raise JobNotFoundError."""
        with self._lock:
            try:
                return self._jobs[job_id]
            except KeyError as exc:
                raise JobNotFoundError(f"Job {job_id} was not found.") from exc

    def get_optional(self, job_id: UUID) -> Job | None:
        """Return a job by identifier, or None when it does not exist."""
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job: Job) -> Job:
        """Persist an existing job after validating its identity."""
        with self._lock:
            if job.id not in self._jobs:
                raise JobNotFoundError(f"Job {job.id} was not found.")

            self._jobs[job.id] = job
            return job

    def mark_running(self, job_id: UUID) -> Job:
        """Transition a pending or failed job to running."""
        with self._lock:
            job = self.get(job_id)

            if job.status not in {JobStatus.PENDING, JobStatus.FAILED}:
                raise JobStateError(
                    f"Job {job_id} cannot start from {job.status.value}."
                )

            job.mark_running()
            return self.update(job)

    def mark_succeeded(self, job_id: UUID) -> Job:
        """Transition a running job to succeeded."""
        with self._lock:
            job = self.get(job_id)

            if job.status != JobStatus.RUNNING:
                raise JobStateError(
                    f"Job {job_id} cannot succeed from {job.status.value}."
                )

            job.mark_succeeded()
            return self.update(job)

    def mark_failed(
        self,
        job_id: UUID,
        error: Exception | str,
    ) -> Job:
        """Record a failed attempt and retain the job for retry processing."""
        with self._lock:
            job = self.get(job_id)

            if job.status != JobStatus.RUNNING:
                raise JobStateError(
                    f"Job {job_id} cannot fail from {job.status.value}."
                )

            job.mark_failed(error)
            return self.update(job)

    def mark_dead_lettered(
        self,
        job_id: UUID,
        error: Exception | str | None = None,
    ) -> Job:
        """Permanently move a failed job into the dead-letter state."""
        with self._lock:
            job = self.get(job_id)

            if job.status not in {JobStatus.FAILED, JobStatus.RUNNING}:
                raise JobStateError(
                    f"Job {job_id} cannot be dead-lettered "
                    f"from {job.status.value}."
                )

            job.mark_dead_lettered(error)
            return self.update(job)

    def list_by_status(
        self,
        status: JobStatus,
        *,
        limit: int = 100,
    ) -> list[Job]:
        """Return jobs with a given status, bounded by the requested limit."""
        if limit <= 0:
            raise ValueError("limit must be greater than zero.")

        with self._lock:
            return [
                job
                for job in self._jobs.values()
                if job.status == status
            ][:limit]

    def list_retryable(self, *, limit: int = 100) -> list[Job]:
        """Return failed jobs that have remaining retry attempts."""
        if limit <= 0:
            raise ValueError("limit must be greater than zero.")

        with self._lock:
            return [
                job
                for job in self._jobs.values()
                if job.status == JobStatus.FAILED
                and not job.retries_exhausted
            ][:limit]

    def count(self, status: JobStatus | None = None) -> int:
        """Return the number of stored jobs, optionally filtered by status."""
        with self._lock:
            if status is None:
                return len(self._jobs)

            return sum(job.status == status for job in self._jobs.values())

    def delete(self, job_id: UUID) -> None:
        """Delete a job only when it is in a terminal state."""
        with self._lock:
            job = self.get(job_id)

            if job.status not in self._TERMINAL_STATES:
                raise JobStateError(
                    f"Job {job_id} cannot be deleted from {job.status.value}."
                )

            del self._jobs[job_id]

    def cleanup_completed(
        self,
        *,
        older_than: datetime,
        limit: int = 1000,
    ) -> int:
        """Delete terminal jobs completed before the supplied timestamp."""
        if limit <= 0:
            raise ValueError("limit must be greater than zero.")

        if older_than.tzinfo is None:
            raise ValueError("older_than must be timezone-aware.")

        with self._lock:
            candidates = [
                job
                for job in self._jobs.values()
                if job.status in self._TERMINAL_STATES
                and job.completed_at is not None
                and job.completed_at < older_than
            ]

            deleted = 0

            for job in candidates[:limit]:
                del self._jobs[job.id]
                deleted += 1

            return deleted

    def clear(self) -> None:
        """Remove all jobs from the local store.

        Intended for tests and local development only. A production
        implementation should use explicit retention and archival policies.
        """
        with self._lock:
            self._jobs.clear()

    @staticmethod
    def utcnow() -> datetime:
        """Return a timezone-aware UTC timestamp for store operations."""
        return datetime.now(timezone.utc)

"""Persistent job-state storage for the background job system."""

from __future__ import annotations

from datetime import datetime, timezone
from threading import RLock
from typing import Final
from uuid import UUID

from src.jobs.base import Job, JobStatus


class JobNotFoundError(LookupError):
    """Raised when a requested job does not exist in the job store."""


class JobStateError(ValueError):
    """Raised when an invalid job-state transition is requested."""


class JobStore:
    """Provide thread-safe persistence semantics for background job state.

    This implementation uses process-local memory so the project can run
    without an external database. Production deployments should replace this
    implementation with a durable store such as PostgreSQL or Redis while
    preserving the repository-style interface used by workers and services.
    """

    _TERMINAL_STATES: Final[frozenset[JobStatus]] = frozenset(
        {
            JobStatus.SUCCEEDED,
            JobStatus.DEAD_LETTERED,
        }
    )

    def __init__(self) -> None:
        self._jobs: dict[UUID, Job] = {}
        self._lock = RLock()

    def create(self, job: Job) -> Job:
        """Persist a new job and reject duplicate identifiers."""
        with self._lock:
            if job.id in self._jobs:
                raise JobStateError(f"Job {job.id} already exists.")

            self._jobs[job.id] = job
            return job

    def get(self, job_id: UUID) -> Job:
        """Return a job by identifier or raise JobNotFoundError."""
        with self._lock:
            try:
                return self._jobs[job_id]
            except KeyError as exc:
                raise JobNotFoundError(f"Job {job_id} was not found.") from exc

    def get_optional(self, job_id: UUID) -> Job | None:
        """Return a job by identifier, or None when it does not exist."""
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job: Job) -> Job:
        """Persist an existing job after validating its identity."""
        with self._lock:
            if job.id not in self._jobs:
                raise JobNotFoundError(f"Job {job.id} was not found.")

            self._jobs[job.id] = job
            return job

    def mark_running(self, job_id: UUID) -> Job:
        """Transition a pending or failed job to running."""
        with self._lock:
            job = self.get(job_id)

            if job.status not in {JobStatus.PENDING, JobStatus.FAILED}:
                raise JobStateError(
                    f"Job {job_id} cannot start from {job.status.value}."
                )

            job.mark_running()
            return self.update(job)

    def mark_succeeded(self, job_id: UUID) -> Job:
        """Transition a running job to succeeded."""
        with self._lock:
            job = self.get(job_id)

            if job.status != JobStatus.RUNNING:
                raise JobStateError(
                    f"Job {job_id} cannot succeed from {job.status.value}."
                )

            job.mark_succeeded()
            return self.update(job)

    def mark_failed(
        self,
        job_id: UUID,
        error: Exception | str,
    ) -> Job:
        """Record a failed attempt and retain the job for retry processing."""
        with self._lock:
            job = self.get(job_id)

            if job.status != JobStatus.RUNNING:
                raise JobStateError(
                    f"Job {job_id} cannot fail from {job.status.value}."
                )

            job.mark_failed(error)
            return self.update(job)

    def mark_dead_lettered(
        self,
        job_id: UUID,
        error: Exception | str | None = None,
    ) -> Job:
        """Permanently move a failed job into the dead-letter state."""
        with self._lock:
            job = self.get(job_id)

            if job.status not in {JobStatus.FAILED, JobStatus.RUNNING}:
                raise JobStateError(
                    f"Job {job_id} cannot be dead-lettered "
                    f"from {job.status.value}."
                )

            job.mark_dead_lettered(error)
            return self.update(job)

    def list_by_status(
        self,
        status: JobStatus,
        *,
        limit: int = 100,
    ) -> list[Job]:
        """Return jobs with a given status, bounded by the requested limit."""
        if limit <= 0:
            raise ValueError("limit must be greater than zero.")

        with self._lock:
            return [
                job
                for job in self._jobs.values()
                if job.status == status
            ][:limit]

    def list_retryable(self, *, limit: int = 100) -> list[Job]:
        """Return failed jobs that have remaining retry attempts."""
        if limit <= 0:
            raise ValueError("limit must be greater than zero.")

        with self._lock:
            return [
                job
                for job in self._jobs.values()
                if job.status == JobStatus.FAILED
                and not job.retries_exhausted
            ][:limit]

    def count(self, status: JobStatus | None = None) -> int:
        """Return the number of stored jobs, optionally filtered by status."""
        with self._lock:
            if status is None:
                return len(self._jobs)

            return sum(job.status == status for job in self._jobs.values())

    def delete(self, job_id: UUID) -> None:
        """Delete a job only when it is in a terminal state."""
        with self._lock:
            job = self.get(job_id)

            if job.status not in self._TERMINAL_STATES:
                raise JobStateError(
                    f"Job {job_id} cannot be deleted from {job.status.value}."
                )

            del self._jobs[job_id]

    def cleanup_completed(
        self,
        *,
        older_than: datetime,
        limit: int = 1000,
    ) -> int:
        """Delete terminal jobs completed before the supplied timestamp."""
        if limit <= 0:
            raise ValueError("limit must be greater than zero.")

        if older_than.tzinfo is None:
            raise ValueError("older_than must be timezone-aware.")

        with self._lock:
            candidates = [
                job
                for job in self._jobs.values()
                if job.status in self._TERMINAL_STATES
                and job.completed_at is not None
                and job.completed_at < older_than
            ]

            deleted = 0

            for job in candidates[:limit]:
                del self._jobs[job.id]
                deleted += 1

            return deleted

    def clear(self) -> None:
        """Remove all jobs from the local store.

        Intended for tests and local development only. A production
        implementation should use explicit retention and archival policies.
        """
        with self._lock:
            self._jobs.clear()

    @staticmethod
    def utcnow() -> datetime:
        """Return a timezone-aware UTC timestamp for store operations."""
        return datetime.now(timezone.utc)