"""Run the background-job scheduler process."""

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
from src.scheduler.scheduler import Scheduler
from src.storage.job_store import JobStore


logger = logging.getLogger(__name__)


def configure_logging(level: str) -> None:
    """Configure process-wide logging for the scheduler."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


async def run_scheduler() -> None:
    """Run the scheduler until a termination signal is received."""
    config = JobSystemConfig.from_environment()
    store = JobStore()
    scheduler = Scheduler(
        store=store,
        poll_interval=config.poll_interval_seconds,
    )

    shutdown_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def request_shutdown() -> None:
        """Request graceful scheduler shutdown."""
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
        "Starting background-job scheduler with poll_interval=%.2f seconds.",
        config.poll_interval_seconds,
    )

    scheduler_task = asyncio.create_task(scheduler.run())

    try:
        await shutdown_event.wait()
    finally:
        logger.info("Stopping background-job scheduler.")

        await scheduler.stop()

        try:
            await asyncio.wait_for(
                scheduler_task,
                timeout=config.shutdown_timeout_seconds,
            )
        except TimeoutError:
            logger.warning(
                "Scheduler did not stop within %d seconds; cancelling.",
                config.shutdown_timeout_seconds,
            )
            scheduler_task.cancel()

            try:
                await scheduler_task
            except asyncio.CancelledError:
                pass
        except asyncio.CancelledError:
            scheduler_task.cancel()
            raise

    logger.info("Background-job scheduler stopped cleanly.")


def main() -> int:
    """Configure logging and start the scheduler process."""
    try:
        config = JobSystemConfig.from_environment()
    except ValueError:
        logging.basicConfig(
            level=logging.ERROR,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
        logger.exception("Invalid scheduler configuration.")
        return 2

    configure_logging(config.log_level)

    try:
        asyncio.run(run_scheduler())
    except KeyboardInterrupt:
        logger.info("Scheduler interrupted.")
        return 130
    except Exception:
        logger.exception("Scheduler terminated unexpectedly.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Run the background-job scheduler process."""

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
from src.scheduler.scheduler import Scheduler
from src.storage.job_store import JobStore


logger = logging.getLogger(__name__)


def configure_logging(level: str) -> None:
    """Configure process-wide logging for the scheduler."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


async def run_scheduler() -> None:
    """Run the scheduler until a termination signal is received."""
    config = JobSystemConfig.from_environment()
    store = JobStore()
    scheduler = Scheduler(
        store=store,
        poll_interval=config.poll_interval_seconds,
    )

    shutdown_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def request_shutdown() -> None:
        """Request graceful scheduler shutdown."""
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
        "Starting background-job scheduler with poll_interval=%.2f seconds.",
        config.poll_interval_seconds,
    )

    scheduler_task = asyncio.create_task(scheduler.run())

    try:
        await shutdown_event.wait()
    finally:
        logger.info("Stopping background-job scheduler.")

        await scheduler.stop()

        try:
            await asyncio.wait_for(
                scheduler_task,
                timeout=config.shutdown_timeout_seconds,
            )
        except TimeoutError:
            logger.warning(
                "Scheduler did not stop within %d seconds; cancelling.",
                config.shutdown_timeout_seconds,
            )
            scheduler_task.cancel()

            try:
                await scheduler_task
            except asyncio.CancelledError:
                pass
        except asyncio.CancelledError:
            scheduler_task.cancel()
            raise

    logger.info("Background-job scheduler stopped cleanly.")


def main() -> int:
    """Configure logging and start the scheduler process."""
    try:
        config = JobSystemConfig.from_environment()
    except ValueError:
        logging.basicConfig(
            level=logging.ERROR,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
        logger.exception("Invalid scheduler configuration.")
        return 2

    configure_logging(config.log_level)

    try:
        asyncio.run(run_scheduler())
    except KeyboardInterrupt:
        logger.info("Scheduler interrupted.")
        return 130
    except Exception:
        logger.exception("Scheduler terminated unexpectedly.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())