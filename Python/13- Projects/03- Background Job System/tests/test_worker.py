"""Unit tests for background job worker execution, concurrency, and shutdown."""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from src.jobs.base import Job, JobStatus
from src.queue.worker import InMemoryJobQueue, JobQueue, Worker


@pytest.mark.asyncio
async def test_in_memory_queue_publishes_and_receives_jobs() -> None:
    """A published job should be available to the worker queue."""
    queue = InMemoryJobQueue()
    job = Job(name="cleanup", payload={"resource_ids": ["resource-1"]})

    await queue.publish(job)

    received = await queue.receive()

    assert received is job


@pytest.mark.asyncio
async def test_in_memory_queue_returns_none_when_empty() -> None:
    """An empty queue should not block a polling worker."""
    queue = InMemoryJobQueue()

    assert await queue.receive() is None


@pytest.mark.asyncio
async def test_in_memory_queue_applies_bounded_capacity() -> None:
    """A full queue should apply backpressure to publishers."""
    queue = InMemoryJobQueue(max_size=1)
    first = Job(name="cleanup", payload={})
    second = Job(name="cleanup", payload={})

    await queue.publish(first)

    publish_task = asyncio.create_task(queue.publish(second))
    await asyncio.sleep(0)

    assert not publish_task.done()

    received = await queue.receive()
    assert received is first

    await asyncio.wait_for(publish_task, timeout=1)
    assert await queue.receive() is second


@pytest.mark.asyncio
async def test_worker_executes_registered_job() -> None:
    """The worker should dispatch a queued job to its registered implementation."""
    queue = InMemoryJobQueue()
    job = Job(
        name="cleanup",
        payload={"resource_ids": ["resource-1", "resource-2"]},
    )

    await queue.publish(job)

    worker = Worker(
        queue,
        poll_interval=0.01,
    )

    worker_task = asyncio.create_task(worker.run())

    for _ in range(100):
        if job.status == JobStatus.SUCCEEDED:
            break
        await asyncio.sleep(0.01)

    worker.stop()
    await asyncio.wait_for(worker_task, timeout=1)

    assert job.status == JobStatus.SUCCEEDED
    assert job.attempts == 1
    assert job.last_error is None


@pytest.mark.asyncio
async def test_worker_requeues_retryable_failure() -> None:
    """A failed job with remaining retries should be returned to the queue."""
    class FailingQueue(InMemoryJobQueue):
        """Queue that records rejected jobs."""

        def __init__(self) -> None:
            super().__init__()
            self.rejections: list[tuple[Job, bool]] = []

        async def reject(self, job: Job, *, requeue: bool) -> None:
            """Record rejection while preserving queue semantics."""
            self.rejections.append((job, requeue))
            await super().reject(job, requeue=requeue)

    queue = FailingQueue()
    job = Job(
        name="unknown-job",
        payload={},
        max_retries=2,
    )

    await queue.publish(job)

    worker = Worker(queue)

    task = asyncio.create_task(worker._process_job(job))

    await asyncio.wait_for(task, timeout=1)

    assert len(queue.rejections) == 1
    rejected_job, requeue = queue.rejections[0]

    assert rejected_job is job
    assert requeue is True
    assert job.status == JobStatus.PENDING


@pytest.mark.asyncio
async def test_worker_does_not_requeue_exhausted_job() -> None:
    """A job with no remaining retries should not be requeued."""
    class RecordingQueue(InMemoryJobQueue):
        """Queue that records rejection decisions."""

        def __init__(self) -> None:
            super().__init__()
            self.rejections: list[tuple[Job, bool]] = []

        async def reject(self, job: Job, *, requeue: bool) -> None:
            """Record the rejection decision."""
            self.rejections.append((job, requeue))
            self._queue.task_done()

    queue = RecordingQueue()
    job = Job(
        name="unknown-job",
        payload={},
        max_retries=0,
    )

    await queue.publish(job)

    worker = Worker(queue)

    await asyncio.wait_for(worker._process_job(job), timeout=1)

    assert len(queue.rejections) == 1
    assert queue.rejections[0][1] is False


@pytest.mark.asyncio
async def test_worker_supports_bounded_concurrency() -> None:
    """The worker should never execute more jobs concurrently than configured."""
    queue = InMemoryJobQueue()

    running = 0
    maximum_running = 0
    completed = 0
    lock = asyncio.Lock()

    async def handler(job: Job, context: object) -> None:
        nonlocal running, maximum_running, completed

        async with lock:
            running += 1
            maximum_running = max(maximum_running, running)

        await asyncio.sleep(0.03)

        async with lock:
            running -= 1
            completed += 1

        job.status = JobStatus.SUCCEEDED

    jobs = [
        Job(name="custom", payload={})
        for _ in range(8)
    ]

    for job in jobs:
        await queue.publish(job)

    worker = Worker(
        queue,
        concurrency=2,
        poll_interval=0.01,
        handler=handler,
    )

    worker_task = asyncio.create_task(worker.run())

    for _ in range(200):
        if completed == len(jobs):
            break
        await asyncio.sleep(0.01)

    worker.stop()
    await asyncio.wait_for(worker_task, timeout=2)

    assert completed == len(jobs)
    assert maximum_running <= 2


@pytest.mark.asyncio
async def test_worker_stop_allows_graceful_shutdown() -> None:
    """Stopping an idle worker should terminate its run loop cleanly."""
    queue = InMemoryJobQueue()
    worker = Worker(
        queue,
        poll_interval=0.01,
    )

    worker_task = asyncio.create_task(worker.run())

    await asyncio.sleep(0.02)
    worker.stop()

    await asyncio.wait_for(worker_task, timeout=1)

    assert worker_task.done()
    assert worker_task.exception() is None


@pytest.mark.asyncio
async def test_worker_shutdown_waits_for_active_jobs() -> None:
    """Shutdown should allow active work to complete before returning."""
    started = asyncio.Event()
    finished = asyncio.Event()

    async def handler(job: Job, context: object) -> None:
        started.set()
        await asyncio.sleep(0.03)
        job.status = JobStatus.SUCCEEDED
        finished.set()

    queue = InMemoryJobQueue()
    job = Job(name="custom", payload={})
    await queue.publish(job)

    worker = Worker(
        queue,
        poll_interval=0.01,
        handler=handler,
    )

    worker_task = asyncio.create_task(worker.run())

    await asyncio.wait_for(started.wait(), timeout=1)

    worker.stop()
    await asyncio.wait_for(worker_task, timeout=1)

    assert finished.is_set()
    assert job.status == JobStatus.SUCCEEDED


@pytest.mark.asyncio
async def test_worker_propagates_active_task_cancellation() -> None:
    """Cancellation should not be silently converted into job failure."""
    started = asyncio.Event()
    cancelled = asyncio.Event()

    async def handler(job: Job, context: object) -> None:
        started.set()

        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            cancelled.set()
            raise

    queue = InMemoryJobQueue()
    job = Job(name="custom", payload={})
    await queue.publish(job)

    worker = Worker(
        queue,
        handler=handler,
        poll_interval=0.01,
    )

    worker_task = asyncio.create_task(worker.run())

    await asyncio.wait_for(started.wait(), timeout=1)

    active_tasks = tuple(worker._tasks)
    assert active_tasks

    for task in active_tasks:
        task.cancel()

    worker.stop()

    await asyncio.wait_for(worker_task, timeout=1)

    assert cancelled.is_set()


@pytest.mark.asyncio
async def test_worker_rejects_invalid_concurrency() -> None:
    """Worker concurrency must be positive."""
    queue = InMemoryJobQueue()

    with pytest.raises(ValueError, match="concurrency"):
        Worker(queue, concurrency=0)


@pytest.mark.asyncio
async def test_worker_rejects_invalid_poll_interval() -> None:
    """Polling intervals must be positive."""
    queue = InMemoryJobQueue()

    with pytest.raises(ValueError, match="poll_interval"):
        Worker(queue, poll_interval=0)


@pytest.mark.asyncio
async def test_worker_can_use_custom_handler() -> None:
    """Dependency injection should allow workers to use custom execution logic."""
    queue = InMemoryJobQueue()
    job = Job(name="custom", payload={"value": 42})

    received: list[Job] = []

    async def handler(received_job: Job, context: object) -> None:
        received.append(received_job)
        received_job.status = JobStatus.SUCCEEDED

    await queue.publish(job)

    worker = Worker(
        queue,
        handler=handler,
        poll_interval=0.01,
    )

    worker_task = asyncio.create_task(worker.run())

    for _ in range(100):
        if job.status == JobStatus.SUCCEEDED:
            break
        await asyncio.sleep(0.01)

    worker.stop()
    await asyncio.wait_for(worker_task, timeout=1)

    assert received == [job]


@pytest.mark.asyncio
async def test_worker_processes_multiple_jobs() -> None:
    """A worker should continue consuming jobs after successful executions."""
    queue = InMemoryJobQueue()

    jobs = [
        Job(name="cleanup", payload={"resource_ids": [str(index)]})
        for index in range(5)
    ]

    for job in jobs:
        await queue.publish(job)

    worker = Worker(
        queue,
        concurrency=2,
        poll_interval=0.01,
    )

    worker_task = asyncio.create_task(worker.run())

    for _ in range(200):
        if all(job.status == JobStatus.SUCCEEDED for job in jobs):
            break
        await asyncio.sleep(0.01)

    worker.stop()
    await asyncio.wait_for(worker_task, timeout=1)

    assert all(job.status == JobStatus.SUCCEEDED for job in jobs)
    assert all(job.attempts == 1 for job in jobs)


@pytest.mark.asyncio
async def test_worker_shutdown_is_idempotent() -> None:
    """Calling shutdown repeatedly should not fail or duplicate cleanup."""
    queue = InMemoryJobQueue()
    worker = Worker(queue)

    await worker.shutdown()
    await worker.shutdown()

    assert worker._stop_event.is_set()


def test_job_queue_contract_requires_implementation() -> None:
    """The base queue abstraction should fail when methods are not implemented."""
    queue = JobQueue()
    job = Job(name="cleanup", payload={})

    with pytest.raises(NotImplementedError):
        asyncio.run(queue.receive())

    with pytest.raises(NotImplementedError):
        asyncio.run(queue.acknowledge(job))

    with pytest.raises(NotImplementedError):
        asyncio.run(queue.reject(job, requeue=False))


def test_job_ids_are_unique_for_worker_inputs() -> None:
    """Independent jobs should retain distinct identifiers."""
    first = Job(name="cleanup", payload={}, id=uuid4())
    second = Job(name="cleanup", payload={}, id=uuid4())

    assert first.id != second.id

"""Unit tests for background job worker execution, concurrency, and shutdown."""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from src.jobs.base import Job, JobStatus
from src.queue.worker import InMemoryJobQueue, JobQueue, Worker


@pytest.mark.asyncio
async def test_in_memory_queue_publishes_and_receives_jobs() -> None:
    """A published job should be available to the worker queue."""
    queue = InMemoryJobQueue()
    job = Job(name="cleanup", payload={"resource_ids": ["resource-1"]})

    await queue.publish(job)

    received = await queue.receive()

    assert received is job


@pytest.mark.asyncio
async def test_in_memory_queue_returns_none_when_empty() -> None:
    """An empty queue should not block a polling worker."""
    queue = InMemoryJobQueue()

    assert await queue.receive() is None


@pytest.mark.asyncio
async def test_in_memory_queue_applies_bounded_capacity() -> None:
    """A full queue should apply backpressure to publishers."""
    queue = InMemoryJobQueue(max_size=1)
    first = Job(name="cleanup", payload={})
    second = Job(name="cleanup", payload={})

    await queue.publish(first)

    publish_task = asyncio.create_task(queue.publish(second))
    await asyncio.sleep(0)

    assert not publish_task.done()

    received = await queue.receive()
    assert received is first

    await asyncio.wait_for(publish_task, timeout=1)
    assert await queue.receive() is second


@pytest.mark.asyncio
async def test_worker_executes_registered_job() -> None:
    """The worker should dispatch a queued job to its registered implementation."""
    queue = InMemoryJobQueue()
    job = Job(
        name="cleanup",
        payload={"resource_ids": ["resource-1", "resource-2"]},
    )

    await queue.publish(job)

    worker = Worker(
        queue,
        poll_interval=0.01,
    )

    worker_task = asyncio.create_task(worker.run())

    for _ in range(100):
        if job.status == JobStatus.SUCCEEDED:
            break
        await asyncio.sleep(0.01)

    worker.stop()
    await asyncio.wait_for(worker_task, timeout=1)

    assert job.status == JobStatus.SUCCEEDED
    assert job.attempts == 1
    assert job.last_error is None


@pytest.mark.asyncio
async def test_worker_requeues_retryable_failure() -> None:
    """A failed job with remaining retries should be returned to the queue."""
    class FailingQueue(InMemoryJobQueue):
        """Queue that records rejected jobs."""

        def __init__(self) -> None:
            super().__init__()
            self.rejections: list[tuple[Job, bool]] = []

        async def reject(self, job: Job, *, requeue: bool) -> None:
            """Record rejection while preserving queue semantics."""
            self.rejections.append((job, requeue))
            await super().reject(job, requeue=requeue)

    queue = FailingQueue()
    job = Job(
        name="unknown-job",
        payload={},
        max_retries=2,
    )

    await queue.publish(job)

    worker = Worker(queue)

    task = asyncio.create_task(worker._process_job(job))

    await asyncio.wait_for(task, timeout=1)

    assert len(queue.rejections) == 1
    rejected_job, requeue = queue.rejections[0]

    assert rejected_job is job
    assert requeue is True
    assert job.status == JobStatus.PENDING


@pytest.mark.asyncio
async def test_worker_does_not_requeue_exhausted_job() -> None:
    """A job with no remaining retries should not be requeued."""
    class RecordingQueue(InMemoryJobQueue):
        """Queue that records rejection decisions."""

        def __init__(self) -> None:
            super().__init__()
            self.rejections: list[tuple[Job, bool]] = []

        async def reject(self, job: Job, *, requeue: bool) -> None:
            """Record the rejection decision."""
            self.rejections.append((job, requeue))
            self._queue.task_done()

    queue = RecordingQueue()
    job = Job(
        name="unknown-job",
        payload={},
        max_retries=0,
    )

    await queue.publish(job)

    worker = Worker(queue)

    await asyncio.wait_for(worker._process_job(job), timeout=1)

    assert len(queue.rejections) == 1
    assert queue.rejections[0][1] is False


@pytest.mark.asyncio
async def test_worker_supports_bounded_concurrency() -> None:
    """The worker should never execute more jobs concurrently than configured."""
    queue = InMemoryJobQueue()

    running = 0
    maximum_running = 0
    completed = 0
    lock = asyncio.Lock()

    async def handler(job: Job, context: object) -> None:
        nonlocal running, maximum_running, completed

        async with lock:
            running += 1
            maximum_running = max(maximum_running, running)

        await asyncio.sleep(0.03)

        async with lock:
            running -= 1
            completed += 1

        job.status = JobStatus.SUCCEEDED

    jobs = [
        Job(name="custom", payload={})
        for _ in range(8)
    ]

    for job in jobs:
        await queue.publish(job)

    worker = Worker(
        queue,
        concurrency=2,
        poll_interval=0.01,
        handler=handler,
    )

    worker_task = asyncio.create_task(worker.run())

    for _ in range(200):
        if completed == len(jobs):
            break
        await asyncio.sleep(0.01)

    worker.stop()
    await asyncio.wait_for(worker_task, timeout=2)

    assert completed == len(jobs)
    assert maximum_running <= 2


@pytest.mark.asyncio
async def test_worker_stop_allows_graceful_shutdown() -> None:
    """Stopping an idle worker should terminate its run loop cleanly."""
    queue = InMemoryJobQueue()
    worker = Worker(
        queue,
        poll_interval=0.01,
    )

    worker_task = asyncio.create_task(worker.run())

    await asyncio.sleep(0.02)
    worker.stop()

    await asyncio.wait_for(worker_task, timeout=1)

    assert worker_task.done()
    assert worker_task.exception() is None


@pytest.mark.asyncio
async def test_worker_shutdown_waits_for_active_jobs() -> None:
    """Shutdown should allow active work to complete before returning."""
    started = asyncio.Event()
    finished = asyncio.Event()

    async def handler(job: Job, context: object) -> None:
        started.set()
        await asyncio.sleep(0.03)
        job.status = JobStatus.SUCCEEDED
        finished.set()

    queue = InMemoryJobQueue()
    job = Job(name="custom", payload={})
    await queue.publish(job)

    worker = Worker(
        queue,
        poll_interval=0.01,
        handler=handler,
    )

    worker_task = asyncio.create_task(worker.run())

    await asyncio.wait_for(started.wait(), timeout=1)

    worker.stop()
    await asyncio.wait_for(worker_task, timeout=1)

    assert finished.is_set()
    assert job.status == JobStatus.SUCCEEDED


@pytest.mark.asyncio
async def test_worker_propagates_active_task_cancellation() -> None:
    """Cancellation should not be silently converted into job failure."""
    started = asyncio.Event()
    cancelled = asyncio.Event()

    async def handler(job: Job, context: object) -> None:
        started.set()

        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            cancelled.set()
            raise

    queue = InMemoryJobQueue()
    job = Job(name="custom", payload={})
    await queue.publish(job)

    worker = Worker(
        queue,
        handler=handler,
        poll_interval=0.01,
    )

    worker_task = asyncio.create_task(worker.run())

    await asyncio.wait_for(started.wait(), timeout=1)

    active_tasks = tuple(worker._tasks)
    assert active_tasks

    for task in active_tasks:
        task.cancel()

    worker.stop()

    await asyncio.wait_for(worker_task, timeout=1)

    assert cancelled.is_set()


@pytest.mark.asyncio
async def test_worker_rejects_invalid_concurrency() -> None:
    """Worker concurrency must be positive."""
    queue = InMemoryJobQueue()

    with pytest.raises(ValueError, match="concurrency"):
        Worker(queue, concurrency=0)


@pytest.mark.asyncio
async def test_worker_rejects_invalid_poll_interval() -> None:
    """Polling intervals must be positive."""
    queue = InMemoryJobQueue()

    with pytest.raises(ValueError, match="poll_interval"):
        Worker(queue, poll_interval=0)


@pytest.mark.asyncio
async def test_worker_can_use_custom_handler() -> None:
    """Dependency injection should allow workers to use custom execution logic."""
    queue = InMemoryJobQueue()
    job = Job(name="custom", payload={"value": 42})

    received: list[Job] = []

    async def handler(received_job: Job, context: object) -> None:
        received.append(received_job)
        received_job.status = JobStatus.SUCCEEDED

    await queue.publish(job)

    worker = Worker(
        queue,
        handler=handler,
        poll_interval=0.01,
    )

    worker_task = asyncio.create_task(worker.run())

    for _ in range(100):
        if job.status == JobStatus.SUCCEEDED:
            break
        await asyncio.sleep(0.01)

    worker.stop()
    await asyncio.wait_for(worker_task, timeout=1)

    assert received == [job]


@pytest.mark.asyncio
async def test_worker_processes_multiple_jobs() -> None:
    """A worker should continue consuming jobs after successful executions."""
    queue = InMemoryJobQueue()

    jobs = [
        Job(name="cleanup", payload={"resource_ids": [str(index)]})
        for index in range(5)
    ]

    for job in jobs:
        await queue.publish(job)

    worker = Worker(
        queue,
        concurrency=2,
        poll_interval=0.01,
    )

    worker_task = asyncio.create_task(worker.run())

    for _ in range(200):
        if all(job.status == JobStatus.SUCCEEDED for job in jobs):
            break
        await asyncio.sleep(0.01)

    worker.stop()
    await asyncio.wait_for(worker_task, timeout=1)

    assert all(job.status == JobStatus.SUCCEEDED for job in jobs)
    assert all(job.attempts == 1 for job in jobs)


@pytest.mark.asyncio
async def test_worker_shutdown_is_idempotent() -> None:
    """Calling shutdown repeatedly should not fail or duplicate cleanup."""
    queue = InMemoryJobQueue()
    worker = Worker(queue)

    await worker.shutdown()
    await worker.shutdown()

    assert worker._stop_event.is_set()


def test_job_queue_contract_requires_implementation() -> None:
    """The base queue abstraction should fail when methods are not implemented."""
    queue = JobQueue()
    job = Job(name="cleanup", payload={})

    with pytest.raises(NotImplementedError):
        asyncio.run(queue.receive())

    with pytest.raises(NotImplementedError):
        asyncio.run(queue.acknowledge(job))

    with pytest.raises(NotImplementedError):
        asyncio.run(queue.reject(job, requeue=False))


def test_job_ids_are_unique_for_worker_inputs() -> None:
    """Independent jobs should retain distinct identifiers."""
    first = Job(name="cleanup", payload={}, id=uuid4())
    second = Job(name="cleanup", payload={}, id=uuid4())

    assert first.id != second.id