"""Base abstractions for durable background jobs."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class JobStatus(StrEnum):
    """Represent the lifecycle state of a background job."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DEAD_LETTERED = "dead_lettered"


@dataclass(slots=True)
class JobContext:
    """Provide execution metadata and cancellation state to a job."""

    job_id: UUID
    attempt: int
    max_retries: int
    cancelled: bool = False

    def check_cancelled(self) -> None:
        """Raise when execution has been requested to stop."""
        if self.cancelled:
            raise RuntimeError(f"Job {self.job_id} execution was cancelled.")


@dataclass(slots=True)
class Job:
    """Represent a durable unit of background work."""

    name: str
    payload: dict[str, Any]
    id: UUID = field(default_factory=uuid4)
    status: JobStatus = JobStatus.PENDING
    attempts: int = 0
    max_retries: int = 3
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    started_at: datetime | None = None
    completed_at: datetime | None = None
    last_error: str | None = None

    def mark_running(self) -> None:
        """Transition the job into the running state."""
        if self.status not in {JobStatus.PENDING, JobStatus.FAILED}:
            raise ValueError(
                f"Job {self.id} cannot start from status {self.status.value}.",
            )

        self.status = JobStatus.RUNNING
        self.attempts += 1
        self.started_at = datetime.now(timezone.utc)
        self.completed_at = None

    def mark_succeeded(self) -> None:
        """Mark the job as successfully completed."""
        if self.status != JobStatus.RUNNING:
            raise ValueError(
                f"Job {self.id} cannot succeed from status {self.status.value}.",
            )

        self.status = JobStatus.SUCCEEDED
        self.completed_at = datetime.now(timezone.utc)
        self.last_error = None

    def mark_failed(self, error: Exception | str) -> None:
        """Record a failed execution and transition to failed state."""
        if self.status != JobStatus.RUNNING:
            raise ValueError(
                f"Job {self.id} cannot fail from status {self.status.value}.",
            )

        self.status = JobStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        self.last_error = str(error)

    def mark_dead_lettered(self, error: Exception | str | None = None) -> None:
        """Move an exhausted job to the dead-letter state."""
        if self.status not in {JobStatus.FAILED, JobStatus.RUNNING}:
            raise ValueError(
                f"Job {self.id} cannot be dead-lettered from status "
                f"{self.status.value}.",
            )

        self.status = JobStatus.DEAD_LETTERED
        self.completed_at = datetime.now(timezone.utc)

        if error is not None:
            self.last_error = str(error)

    @property
    def retries_exhausted(self) -> bool:
        """Return whether no further execution attempts are permitted."""
        return self.attempts > self.max_retries


class BaseJob(ABC):
    """Define the contract implemented by executable background jobs."""

    name: str

    @abstractmethod
    async def execute(
        self,
        payload: dict[str, Any],
        context: JobContext,
    ) -> Any:
        """Execute the job using the supplied payload and execution context."""
        raise NotImplementedError

    async def run(
        self,
        job: Job,
        context: JobContext,
    ) -> Any:
        """Execute a job after validating its lifecycle state."""
        if job.status != JobStatus.PENDING:
            raise ValueError(
                f"Job {job.id} must be pending before execution; "
                f"current status is {job.status.value}.",
            )

        job.mark_running()

        try:
            result = await self.execute(job.payload, context)
        except Exception as exc:
            job.mark_failed(exc)

            if job.retries_exhausted:
                job.mark_dead_lettered(exc)

            raise

        job.mark_succeeded()
        return result

"""Base abstractions for durable background jobs."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class JobStatus(StrEnum):
    """Represent the lifecycle state of a background job."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DEAD_LETTERED = "dead_lettered"


@dataclass(slots=True)
class JobContext:
    """Provide execution metadata and cancellation state to a job."""

    job_id: UUID
    attempt: int
    max_retries: int
    cancelled: bool = False

    def check_cancelled(self) -> None:
        """Raise when execution has been requested to stop."""
        if self.cancelled:
            raise RuntimeError(f"Job {self.job_id} execution was cancelled.")


@dataclass(slots=True)
class Job:
    """Represent a durable unit of background work."""

    name: str
    payload: dict[str, Any]
    id: UUID = field(default_factory=uuid4)
    status: JobStatus = JobStatus.PENDING
    attempts: int = 0
    max_retries: int = 3
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    started_at: datetime | None = None
    completed_at: datetime | None = None
    last_error: str | None = None

    def mark_running(self) -> None:
        """Transition the job into the running state."""
        if self.status not in {JobStatus.PENDING, JobStatus.FAILED}:
            raise ValueError(
                f"Job {self.id} cannot start from status {self.status.value}.",
            )

        self.status = JobStatus.RUNNING
        self.attempts += 1
        self.started_at = datetime.now(timezone.utc)
        self.completed_at = None

    def mark_succeeded(self) -> None:
        """Mark the job as successfully completed."""
        if self.status != JobStatus.RUNNING:
            raise ValueError(
                f"Job {self.id} cannot succeed from status {self.status.value}.",
            )

        self.status = JobStatus.SUCCEEDED
        self.completed_at = datetime.now(timezone.utc)
        self.last_error = None

    def mark_failed(self, error: Exception | str) -> None:
        """Record a failed execution and transition to failed state."""
        if self.status != JobStatus.RUNNING:
            raise ValueError(
                f"Job {self.id} cannot fail from status {self.status.value}.",
            )

        self.status = JobStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        self.last_error = str(error)

    def mark_dead_lettered(self, error: Exception | str | None = None) -> None:
        """Move an exhausted job to the dead-letter state."""
        if self.status not in {JobStatus.FAILED, JobStatus.RUNNING}:
            raise ValueError(
                f"Job {self.id} cannot be dead-lettered from status "
                f"{self.status.value}.",
            )

        self.status = JobStatus.DEAD_LETTERED
        self.completed_at = datetime.now(timezone.utc)

        if error is not None:
            self.last_error = str(error)

    @property
    def retries_exhausted(self) -> bool:
        """Return whether no further execution attempts are permitted."""
        return self.attempts > self.max_retries


class BaseJob(ABC):
    """Define the contract implemented by executable background jobs."""

    name: str

    @abstractmethod
    async def execute(
        self,
        payload: dict[str, Any],
        context: JobContext,
    ) -> Any:
        """Execute the job using the supplied payload and execution context."""
        raise NotImplementedError

    async def run(
        self,
        job: Job,
        context: JobContext,
    ) -> Any:
        """Execute a job after validating its lifecycle state."""
        if job.status != JobStatus.PENDING:
            raise ValueError(
                f"Job {job.id} must be pending before execution; "
                f"current status is {job.status.value}.",
            )

        job.mark_running()

        try:
            result = await self.execute(job.payload, context)
        except Exception as exc:
            job.mark_failed(exc)

            if job.retries_exhausted:
                job.mark_dead_lettered(exc)

            raise

        job.mark_succeeded()
        return result