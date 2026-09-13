"""Scheduler for creating background jobs at scheduled times and intervals."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from heapq import heappop, heappush
from typing import Any
from uuid import UUID, uuid4

from src.jobs.base import Job
from src.queue.worker import InMemoryJobQueue, JobQueue

logger = logging.getLogger(__name__)


@dataclass(order=True, slots=True)
class ScheduledJob:
    """Represent a job that becomes eligible for queueing at a given time."""

    run_at: datetime
    sequence: int
    name: str = field(compare=False)
    payload: dict[str, Any] = field(compare=False)
    interval: timedelta | None = field(default=None, compare=False)
    id: UUID = field(default_factory=uuid4, compare=False)
    enabled: bool = field(default=True, compare=False)

    def next_run(self) -> ScheduledJob | None:
        """Return the next occurrence for a recurring job."""
        if not self.enabled or self.interval is None:
            return None

        if self.interval.total_seconds() <= 0:
            raise ValueError("Recurring job interval must be greater than zero.")

        return ScheduledJob(
            run_at=self.run_at + self.interval,
            sequence=self.sequence + 1,
            name=self.name,
            payload=self.payload.copy(),
            interval=self.interval,
            id=self.id,
            enabled=True,
        )


class JobScheduler:
    """Schedule one-time and recurring jobs and publish them to a queue."""

    def __init__(
        self,
        queue: JobQueue | None = None,
        *,
        poll_interval: float = 1.0,
    ) -> None:
        if poll_interval <= 0:
            raise ValueError("poll_interval must be greater than zero.")

        self._queue = queue or InMemoryJobQueue()
        self._poll_interval = poll_interval
        self._scheduled: list[ScheduledJob] = []
        self._sequence = 0
        self._stop_event = asyncio.Event()
        self._wake_event = asyncio.Event()
        self._lock = asyncio.Lock()

    async def schedule(
        self,
        name: str,
        payload: dict[str, Any],
        *,
        run_at: datetime | None = None,
        interval: timedelta | None = None,
    ) -> UUID:
        """Schedule a one-time or recurring job."""
        if not name.strip():
            raise ValueError("Job name must not be empty.")

        if interval is not None and interval.total_seconds() <= 0:
            raise ValueError("Recurring job interval must be greater than zero.")

        scheduled_at = run_at or datetime.now(timezone.utc)

        if scheduled_at.tzinfo is None:
            raise ValueError("run_at must be timezone-aware.")

        async with self._lock:
            self._sequence += 1

            scheduled_job = ScheduledJob(
                run_at=scheduled_at,
                sequence=self._sequence,
                name=name,
                payload=payload.copy(),
                interval=interval,
            )

            heappush(self._scheduled, scheduled_job)

        self._wake_event.set()

        logger.info(
            "Scheduled job %s (%s) for %s.",
            scheduled_job.id,
            name,
            scheduled_at.isoformat(),
        )

        return scheduled_job.id

    async def cancel(self, job_id: UUID) -> bool:
        """Disable a scheduled job and return whether it was found."""
        async with self._lock:
            for scheduled_job in self._scheduled:
                if scheduled_job.id == job_id:
                    scheduled_job.enabled = False
                    self._wake_event.set()
                    return True

        return False

    async def run(self) -> None:
        """Run the scheduler until shutdown is requested."""
        logger.info("Starting job scheduler.")

        try:
            while not self._stop_event.is_set():
                due_jobs = await self._get_due_jobs()

                for scheduled_job in due_jobs:
                    await self._publish(scheduled_job)

                await self._wait_until_next_job()
        finally:
            logger.info("Job scheduler stopped.")

    def stop(self) -> None:
        """Request graceful scheduler shutdown."""
        self._stop_event.set()
        self._wake_event.set()

    async def _get_due_jobs(self) -> list[ScheduledJob]:
        """Remove and return all enabled jobs whose execution time has arrived."""
        now = datetime.now(timezone.utc)
        due_jobs: list[ScheduledJob] = []

        async with self._lock:
            while self._scheduled and self._scheduled[0].run_at <= now:
                scheduled_job = heappop(self._scheduled)

                if scheduled_job.enabled:
                    due_jobs.append(scheduled_job)

        return due_jobs

    async def _publish(self, scheduled_job: ScheduledJob) -> None:
        """Create a queue job and publish it for worker execution."""
        job = Job(
            name=scheduled_job.name,
            payload=scheduled_job.payload.copy(),
        )

        await self._queue.publish(job)

        logger.info(
            "Published scheduled job %s (%s) as queue job %s.",
            scheduled_job.id,
            scheduled_job.name,
            job.id,
        )

        next_job = scheduled_job.next_run()

        if next_job is not None and not self._stop_event.is_set():
            async with self._lock:
                heappush(self._scheduled, next_job)

    async def _wait_until_next_job(self) -> None:
        """Wait for a new schedule, the next due job, or shutdown."""
        if self._stop_event.is_set():
            return

        async with self._lock:
            if not self._scheduled:
                timeout = self._poll_interval
            else:
                delay = (
                    self._scheduled[0].run_at
                    - datetime.now(timezone.utc)
                ).total_seconds()
                timeout = max(0.0, min(delay, self._poll_interval))

        self._wake_event.clear()

        try:
            await asyncio.wait_for(
                self._wake_event.wait(),
                timeout=timeout,
            )
        except TimeoutError:
            pass

"""Scheduler for creating background jobs at scheduled times and intervals."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from heapq import heappop, heappush
from typing import Any
from uuid import UUID, uuid4

from src.jobs.base import Job
from src.queue.worker import InMemoryJobQueue, JobQueue

logger = logging.getLogger(__name__)


@dataclass(order=True, slots=True)
class ScheduledJob:
    """Represent a job that becomes eligible for queueing at a given time."""

    run_at: datetime
    sequence: int
    name: str = field(compare=False)
    payload: dict[str, Any] = field(compare=False)
    interval: timedelta | None = field(default=None, compare=False)
    id: UUID = field(default_factory=uuid4, compare=False)
    enabled: bool = field(default=True, compare=False)

    def next_run(self) -> ScheduledJob | None:
        """Return the next occurrence for a recurring job."""
        if not self.enabled or self.interval is None:
            return None

        if self.interval.total_seconds() <= 0:
            raise ValueError("Recurring job interval must be greater than zero.")

        return ScheduledJob(
            run_at=self.run_at + self.interval,
            sequence=self.sequence + 1,
            name=self.name,
            payload=self.payload.copy(),
            interval=self.interval,
            id=self.id,
            enabled=True,
        )


class JobScheduler:
    """Schedule one-time and recurring jobs and publish them to a queue."""

    def __init__(
        self,
        queue: JobQueue | None = None,
        *,
        poll_interval: float = 1.0,
    ) -> None:
        if poll_interval <= 0:
            raise ValueError("poll_interval must be greater than zero.")

        self._queue = queue or InMemoryJobQueue()
        self._poll_interval = poll_interval
        self._scheduled: list[ScheduledJob] = []
        self._sequence = 0
        self._stop_event = asyncio.Event()
        self._wake_event = asyncio.Event()
        self._lock = asyncio.Lock()

    async def schedule(
        self,
        name: str,
        payload: dict[str, Any],
        *,
        run_at: datetime | None = None,
        interval: timedelta | None = None,
    ) -> UUID:
        """Schedule a one-time or recurring job."""
        if not name.strip():
            raise ValueError("Job name must not be empty.")

        if interval is not None and interval.total_seconds() <= 0:
            raise ValueError("Recurring job interval must be greater than zero.")

        scheduled_at = run_at or datetime.now(timezone.utc)

        if scheduled_at.tzinfo is None:
            raise ValueError("run_at must be timezone-aware.")

        async with self._lock:
            self._sequence += 1

            scheduled_job = ScheduledJob(
                run_at=scheduled_at,
                sequence=self._sequence,
                name=name,
                payload=payload.copy(),
                interval=interval,
            )

            heappush(self._scheduled, scheduled_job)

        self._wake_event.set()

        logger.info(
            "Scheduled job %s (%s) for %s.",
            scheduled_job.id,
            name,
            scheduled_at.isoformat(),
        )

        return scheduled_job.id

    async def cancel(self, job_id: UUID) -> bool:
        """Disable a scheduled job and return whether it was found."""
        async with self._lock:
            for scheduled_job in self._scheduled:
                if scheduled_job.id == job_id:
                    scheduled_job.enabled = False
                    self._wake_event.set()
                    return True

        return False

    async def run(self) -> None:
        """Run the scheduler until shutdown is requested."""
        logger.info("Starting job scheduler.")

        try:
            while not self._stop_event.is_set():
                due_jobs = await self._get_due_jobs()

                for scheduled_job in due_jobs:
                    await self._publish(scheduled_job)

                await self._wait_until_next_job()
        finally:
            logger.info("Job scheduler stopped.")

    def stop(self) -> None:
        """Request graceful scheduler shutdown."""
        self._stop_event.set()
        self._wake_event.set()

    async def _get_due_jobs(self) -> list[ScheduledJob]:
        """Remove and return all enabled jobs whose execution time has arrived."""
        now = datetime.now(timezone.utc)
        due_jobs: list[ScheduledJob] = []

        async with self._lock:
            while self._scheduled and self._scheduled[0].run_at <= now:
                scheduled_job = heappop(self._scheduled)

                if scheduled_job.enabled:
                    due_jobs.append(scheduled_job)

        return due_jobs

    async def _publish(self, scheduled_job: ScheduledJob) -> None:
        """Create a queue job and publish it for worker execution."""
        job = Job(
            name=scheduled_job.name,
            payload=scheduled_job.payload.copy(),
        )

        await self._queue.publish(job)

        logger.info(
            "Published scheduled job %s (%s) as queue job %s.",
            scheduled_job.id,
            scheduled_job.name,
            job.id,
        )

        next_job = scheduled_job.next_run()

        if next_job is not None and not self._stop_event.is_set():
            async with self._lock:
                heappush(self._scheduled, next_job)

    async def _wait_until_next_job(self) -> None:
        """Wait for a new schedule, the next due job, or shutdown."""
        if self._stop_event.is_set():
            return

        async with self._lock:
            if not self._scheduled:
                timeout = self._poll_interval
            else:
                delay = (
                    self._scheduled[0].run_at
                    - datetime.now(timezone.utc)
                ).total_seconds()
                timeout = max(0.0, min(delay, self._poll_interval))

        self._wake_event.clear()

        try:
            await asyncio.wait_for(
                self._wake_event.wait(),
                timeout=timeout,
            )
        except TimeoutError:
            pass