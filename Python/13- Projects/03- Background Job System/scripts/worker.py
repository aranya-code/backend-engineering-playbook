"""Run a background-job worker process."""

from __future__ import annotations

import asyncio
import logging
import signal
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import JobSystemConfig
from src.queue.worker import Worker
from src.storage.job_store import JobStore


logger = logging.getLogger(__name__)


def configure_logging(level: str) -> None:
    """Configure process-wide logging for the worker."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


async def run_worker() -> None:
    """Create and run a worker until shutdown is requested."""
    config = JobSystemConfig.from_environment()
    store = JobStore()
    worker = Worker(
        store=store,
        concurrency=config.worker_concurrency,
        poll_interval=config.poll_interval_seconds,
        visibility_timeout=config.visibility_timeout_seconds,
        job_timeout=config.job_timeout_seconds,
        max_retries=config.max_retries,
        retry_delay=config.retry_delay_seconds,
    )

    shutdown_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def request_shutdown() -> None:
        """Request graceful worker shutdown."""
        if not shutdown_event.is_set():
            logger.info("Shutdown signal received.")
            shutdown_event.set()

    for signal_name in ("SIGINT", "SIGTERM"):
        signal_value = getattr(signal, signal_name, None)

        if signal_value is not None:
            try:
                loop.add_signal_handler(signal_value, request_shutdown)
            except (NotImplementedError, RuntimeError):
                logger.debug(
                    "Signal handler registration is unavailable for %s.",
                    signal_name,
                )

    logger.info(
        "Starting background worker with concurrency=%d.",
        config.worker_concurrency,
    )

    worker_task = asyncio.create_task(worker.run())

    try:
        await shutdown_event.wait()
    finally:
        logger.info("Stopping background worker.")

        await worker.stop()

        try:
            await asyncio.wait_for(
                worker_task,
                timeout=config.shutdown_timeout_seconds,
            )
        except TimeoutError:
            logger.warning(
                "Worker did not stop within %d seconds; cancelling.",
                config.shutdown_timeout_seconds,
            )
            worker_task.cancel()

            try:
                await worker_task
            except asyncio.CancelledError:
                pass
        except asyncio.CancelledError:
            worker_task.cancel()
            raise

    logger.info("Background worker stopped cleanly.")


def main() -> int:
    """Configure the worker process and run it."""
    try:
        config = JobSystemConfig.from_environment()
    except ValueError:
        logging.basicConfig(
            level=logging.ERROR,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
        logger.exception("Invalid worker configuration.")
        return 2

    configure_logging(config.log_level)

    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Worker interrupted.")
        return 130
    except Exception:
        logger.exception("Background worker terminated unexpectedly.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Run a background-job worker process."""

from __future__ import annotations

import asyncio
import logging
import signal
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import JobSystemConfig
from src.queue.worker import Worker
from src.storage.job_store import JobStore


logger = logging.getLogger(__name__)


def configure_logging(level: str) -> None:
    """Configure process-wide logging for the worker."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


async def run_worker() -> None:
    """Create and run a worker until shutdown is requested."""
    config = JobSystemConfig.from_environment()
    store = JobStore()
    worker = Worker(
        store=store,
        concurrency=config.worker_concurrency,
        poll_interval=config.poll_interval_seconds,
        visibility_timeout=config.visibility_timeout_seconds,
        job_timeout=config.job_timeout_seconds,
        max_retries=config.max_retries,
        retry_delay=config.retry_delay_seconds,
    )

    shutdown_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def request_shutdown() -> None:
        """Request graceful worker shutdown."""
        if not shutdown_event.is_set():
            logger.info("Shutdown signal received.")
            shutdown_event.set()

    for signal_name in ("SIGINT", "SIGTERM"):
        signal_value = getattr(signal, signal_name, None)

        if signal_value is not None:
            try:
                loop.add_signal_handler(signal_value, request_shutdown)
            except (NotImplementedError, RuntimeError):
                logger.debug(
                    "Signal handler registration is unavailable for %s.",
                    signal_name,
                )

    logger.info(
        "Starting background worker with concurrency=%d.",
        config.worker_concurrency,
    )

    worker_task = asyncio.create_task(worker.run())

    try:
        await shutdown_event.wait()
    finally:
        logger.info("Stopping background worker.")

        await worker.stop()

        try:
            await asyncio.wait_for(
                worker_task,
                timeout=config.shutdown_timeout_seconds,
            )
        except TimeoutError:
            logger.warning(
                "Worker did not stop within %d seconds; cancelling.",
                config.shutdown_timeout_seconds,
            )
            worker_task.cancel()

            try:
                await worker_task
            except asyncio.CancelledError:
                pass
        except asyncio.CancelledError:
            worker_task.cancel()
            raise

    logger.info("Background worker stopped cleanly.")


def main() -> int:
    """Configure the worker process and run it."""
    try:
        config = JobSystemConfig.from_environment()
    except ValueError:
        logging.basicConfig(
            level=logging.ERROR,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
        logger.exception("Invalid worker configuration.")
        return 2

    configure_logging(config.log_level)

    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Worker interrupted.")
        return 130
    except Exception:
        logger.exception("Background worker terminated unexpectedly.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())