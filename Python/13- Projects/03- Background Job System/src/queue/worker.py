"""Worker implementation for consuming and executing background jobs."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from src.jobs.base import Job, JobContext, JobStatus
from src.jobs.tasks import get_job

logger = logging.getLogger(__name__)

JobHandler = Callable[[Job, JobContext], Awaitable[Any]]


class JobQueue:
    """Define the minimal asynchronous queue contract required by a worker."""

    async def receive(self) -> Job | None:
        """Receive the next available job, or None when no job is available."""
        raise NotImplementedError

    async def acknowledge(self, job: Job) -> None:
        """Acknowledge successful processing of a job."""
        raise NotImplementedError

    async def reject(self, job: Job, *, requeue: bool) -> None:
        """Reject a job and optionally return it to the queue."""
        raise NotImplementedError


class InMemoryJobQueue(JobQueue):
    """Provide a bounded in-memory queue for local development and testing."""

    def __init__(self, max_size: int = 1000) -> None:
        if max_size <= 0:
            raise ValueError("max_size must be greater than zero.")

        self._queue: asyncio.Queue[Job] = asyncio.Queue(maxsize=max_size)

    async def publish(self, job: Job) -> None:
        """Publish a job, applying backpressure when the queue is full."""
        await self._queue.put(job)

    async def receive(self) -> Job | None:
        """Receive the next queued job without blocking indefinitely."""
        try:
            return self._queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

    async def acknowledge(self, job: Job) -> None:
        """Mark a dequeued job as completed in the local queue."""
        self._queue.task_done()

    async def reject(self, job: Job, *, requeue: bool) -> None:
        """Requeue failed work when requested."""
        self._queue.task_done()

        if requeue:
            await self.publish(job)


class Worker:
    """Consume jobs with bounded concurrency and graceful shutdown."""

    def __init__(
        self,
        queue: JobQueue,
        *,
        concurrency: int = 4,
        poll_interval: float = 1.0,
        handler: JobHandler | None = None,
    ) -> None:
        if concurrency <= 0:
            raise ValueError("concurrency must be greater than zero.")

        if poll_interval <= 0:
            raise ValueError("poll_interval must be greater than zero.")

        self._queue = queue
        self._concurrency = concurrency
        self._poll_interval = poll_interval
        self._handler = handler or self._execute_job
        self._stop_event = asyncio.Event()
        self._tasks: set[asyncio.Task[None]] = set()

    async def run(self) -> None:
        """Run worker consumers until shutdown is requested."""
        logger.info(
            "Starting worker with concurrency=%d",
            self._concurrency,
        )

        try:
            while not self._stop_event.is_set():
                self._remove_completed_tasks()

                if len(self._tasks) >= self._concurrency:
                    await self._wait_for_worker_task()
                    continue

                job = await self._queue.receive()

                if job is None:
                    await self._wait_for_poll_interval()
                    continue

                task = asyncio.create_task(
                    self._process_job(job),
                    name=f"job-worker-{job.id}",
                )
                self._tasks.add(task)
                task.add_done_callback(self._tasks.discard)
        finally:
            await self.shutdown()

    def stop(self) -> None:
        """Request graceful worker shutdown."""
        self._stop_event.set()

    async def shutdown(self) -> None:
        """Stop accepting new jobs and wait for active jobs to finish."""
        self._stop_event.set()

        if not self._tasks:
            return

        tasks = tuple(self._tasks)
        logger.info("Waiting for %d active job(s) to finish.", len(tasks))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, BaseException):
                logger.exception(
                    "Worker task terminated with an exception.",
                    exc_info=result,
                )

        self._tasks.clear()

    async def _process_job(self, job: Job) -> None:
        """Execute one job and determine whether it should be acknowledged."""
        context = JobContext(
            job_id=job.id,
            attempt=job.attempts + 1,
            max_retries=job.max_retries,
        )

        try:
            await self._handler(job, context)
        except asyncio.CancelledError:
            logger.warning("Job %s was cancelled.", job.id)
            raise
        except Exception:
            logger.exception(
                "Job %s failed on attempt %d.",
                job.id,
                context.attempt,
            )

            await self._queue.reject(
                job,
                requeue=not job.retries_exhausted,
            )
            return

        await self._queue.acknowledge(job)

        logger.info(
            "Job %s completed successfully.",
            job.id,
        )

    async def _execute_job(
        self,
        job: Job,
        context: JobContext,
    ) -> Any:
        """Resolve and execute the registered implementation for a job."""
        if job.status not in {JobStatus.PENDING, JobStatus.FAILED}:
            raise ValueError(
                f"Job {job.id} cannot be processed from status "
                f"{job.status.value}.",
            )

        job_handler = get_job(job.name)
        return await job_handler.run(job, context)

    def _remove_completed_tasks(self) -> None:
        """Remove completed worker tasks from the active task set."""
        self._tasks.difference_update(
            task for task in self._tasks if task.done()
        )

    async def _wait_for_worker_task(self) -> None:
        """Wait until at least one active worker task completes."""
        if not self._tasks:
            return

        done, _ = await asyncio.wait(
            self._tasks,
            return_when=asyncio.FIRST_COMPLETED,
        )

        self._tasks.difference_update(done)

        for task in done:
            if task.cancelled():
                continue

            exception = task.exception()

            if exception is not None:
                logger.error(
                    "Worker task failed unexpectedly: %s",
                    exception,
                )

    async def _wait_for_poll_interval(self) -> None:
        """Sleep between empty-queue polls while remaining cancellation-friendly."""
        try:
            await asyncio.wait_for(
                self._stop_event.wait(),
                timeout=self._poll_interval,
            )
        except TimeoutError:
            pass

"""Worker implementation for consuming and executing background jobs."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from src.jobs.base import Job, JobContext, JobStatus
from src.jobs.tasks import get_job

logger = logging.getLogger(__name__)

JobHandler = Callable[[Job, JobContext], Awaitable[Any]]


class JobQueue:
    """Define the minimal asynchronous queue contract required by a worker."""

    async def receive(self) -> Job | None:
        """Receive the next available job, or None when no job is available."""
        raise NotImplementedError

    async def acknowledge(self, job: Job) -> None:
        """Acknowledge successful processing of a job."""
        raise NotImplementedError

    async def reject(self, job: Job, *, requeue: bool) -> None:
        """Reject a job and optionally return it to the queue."""
        raise NotImplementedError


class InMemoryJobQueue(JobQueue):
    """Provide a bounded in-memory queue for local development and testing."""

    def __init__(self, max_size: int = 1000) -> None:
        if max_size <= 0:
            raise ValueError("max_size must be greater than zero.")

        self._queue: asyncio.Queue[Job] = asyncio.Queue(maxsize=max_size)

    async def publish(self, job: Job) -> None:
        """Publish a job, applying backpressure when the queue is full."""
        await self._queue.put(job)

    async def receive(self) -> Job | None:
        """Receive the next queued job without blocking indefinitely."""
        try:
            return self._queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

    async def acknowledge(self, job: Job) -> None:
        """Mark a dequeued job as completed in the local queue."""
        self._queue.task_done()

    async def reject(self, job: Job, *, requeue: bool) -> None:
        """Requeue failed work when requested."""
        self._queue.task_done()

        if requeue:
            await self.publish(job)


class Worker:
    """Consume jobs with bounded concurrency and graceful shutdown."""

    def __init__(
        self,
        queue: JobQueue,
        *,
        concurrency: int = 4,
        poll_interval: float = 1.0,
        handler: JobHandler | None = None,
    ) -> None:
        if concurrency <= 0:
            raise ValueError("concurrency must be greater than zero.")

        if poll_interval <= 0:
            raise ValueError("poll_interval must be greater than zero.")

        self._queue = queue
        self._concurrency = concurrency
        self._poll_interval = poll_interval
        self._handler = handler or self._execute_job
        self._stop_event = asyncio.Event()
        self._tasks: set[asyncio.Task[None]] = set()

    async def run(self) -> None:
        """Run worker consumers until shutdown is requested."""
        logger.info(
            "Starting worker with concurrency=%d",
            self._concurrency,
        )

        try:
            while not self._stop_event.is_set():
                self._remove_completed_tasks()

                if len(self._tasks) >= self._concurrency:
                    await self._wait_for_worker_task()
                    continue

                job = await self._queue.receive()

                if job is None:
                    await self._wait_for_poll_interval()
                    continue

                task = asyncio.create_task(
                    self._process_job(job),
                    name=f"job-worker-{job.id}",
                )
                self._tasks.add(task)
                task.add_done_callback(self._tasks.discard)
        finally:
            await self.shutdown()

    def stop(self) -> None:
        """Request graceful worker shutdown."""
        self._stop_event.set()

    async def shutdown(self) -> None:
        """Stop accepting new jobs and wait for active jobs to finish."""
        self._stop_event.set()

        if not self._tasks:
            return

        tasks = tuple(self._tasks)
        logger.info("Waiting for %d active job(s) to finish.", len(tasks))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, BaseException):
                logger.exception(
                    "Worker task terminated with an exception.",
                    exc_info=result,
                )

        self._tasks.clear()

    async def _process_job(self, job: Job) -> None:
        """Execute one job and determine whether it should be acknowledged."""
        context = JobContext(
            job_id=job.id,
            attempt=job.attempts + 1,
            max_retries=job.max_retries,
        )

        try:
            await self._handler(job, context)
        except asyncio.CancelledError:
            logger.warning("Job %s was cancelled.", job.id)
            raise
        except Exception:
            logger.exception(
                "Job %s failed on attempt %d.",
                job.id,
                context.attempt,
            )

            await self._queue.reject(
                job,
                requeue=not job.retries_exhausted,
            )
            return

        await self._queue.acknowledge(job)

        logger.info(
            "Job %s completed successfully.",
            job.id,
        )

    async def _execute_job(
        self,
        job: Job,
        context: JobContext,
    ) -> Any:
        """Resolve and execute the registered implementation for a job."""
        if job.status not in {JobStatus.PENDING, JobStatus.FAILED}:
            raise ValueError(
                f"Job {job.id} cannot be processed from status "
                f"{job.status.value}.",
            )

        job_handler = get_job(job.name)
        return await job_handler.run(job, context)

    def _remove_completed_tasks(self) -> None:
        """Remove completed worker tasks from the active task set."""
        self._tasks.difference_update(
            task for task in self._tasks if task.done()
        )

    async def _wait_for_worker_task(self) -> None:
        """Wait until at least one active worker task completes."""
        if not self._tasks:
            return

        done, _ = await asyncio.wait(
            self._tasks,
            return_when=asyncio.FIRST_COMPLETED,
        )

        self._tasks.difference_update(done)

        for task in done:
            if task.cancelled():
                continue

            exception = task.exception()

            if exception is not None:
                logger.error(
                    "Worker task failed unexpectedly: %s",
                    exception,
                )

    async def _wait_for_poll_interval(self) -> None:
        """Sleep between empty-queue polls while remaining cancellation-friendly."""
        try:
            await asyncio.wait_for(
                self._stop_event.wait(),
                timeout=self._poll_interval,
            )
        except TimeoutError:
            pass