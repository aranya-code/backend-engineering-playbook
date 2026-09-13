"""Application entry point and monitoring lifecycle for the background job system."""

from __future__ import annotations

import asyncio
import logging
import signal
from contextlib import suppress

from src.config import JobSystemConfig
from src.monitoring.metrics import JobMetrics

logger = logging.getLogger(__name__)


class MonitoringService:
    """Coordinate background metrics collection and periodic reporting."""

    def __init__(
        self,
        metrics: JobMetrics,
        *,
        interval_seconds: float = 15.0,
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be greater than zero.")

        self._metrics = metrics
        self._interval_seconds = interval_seconds
        self._stop_event = asyncio.Event()

    async def run(self) -> None:
        """Periodically publish a metrics snapshot until shutdown."""
        logger.info(
            "Starting monitoring service with interval=%s seconds.",
            self._interval_seconds,
        )

        try:
            while not self._stop_event.is_set():
                self._log_snapshot()
                await self._wait_for_next_interval()
        finally:
            self._log_snapshot()
            logger.info("Monitoring service stopped.")

    def stop(self) -> None:
        """Request graceful monitoring shutdown."""
        self._stop_event.set()

    def _log_snapshot(self) -> None:
        """Log the current metrics using structured, machine-readable fields."""
        snapshot = self._metrics.snapshot()

        logger.info(
            (
                "job_metrics jobs_submitted=%d jobs_started=%d "
                "jobs_succeeded=%d jobs_failed=%d jobs_dead_lettered=%d "
                "jobs_retried=%d active_jobs=%d "
                "total_execution_time_seconds=%.3f "
                "average_execution_time_seconds=%.3f"
            ),
            snapshot.jobs_submitted,
            snapshot.jobs_started,
            snapshot.jobs_succeeded,
            snapshot.jobs_failed,
            snapshot.jobs_dead_lettered,
            snapshot.jobs_retried,
            snapshot.active_jobs,
            snapshot.total_execution_time_seconds,
            snapshot.average_execution_time_seconds,
        )

    async def _wait_for_next_interval(self) -> None:
        """Wait for either the next reporting interval or shutdown."""
        try:
            await asyncio.wait_for(
                self._stop_event.wait(),
                timeout=self._interval_seconds,
            )
        except TimeoutError:
            pass


def configure_logging(level: str) -> None:
    """Configure process-wide logging for the job system."""
    normalized_level = level.strip().upper()

    numeric_level = getattr(logging, normalized_level, None)

    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level!r}.")

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def install_signal_handlers(
    loop: asyncio.AbstractEventLoop,
    stop_callback: callable,
) -> None:
    """Register graceful-shutdown handlers where the platform supports them."""
    for signal_name in ("SIGINT", "SIGTERM"):
        signal_value = getattr(signal, signal_name, None)

        if signal_value is None:
            continue

        with suppress(NotImplementedError):
            loop.add_signal_handler(signal_value, stop_callback)


async def run() -> None:
    """Start the monitoring component and wait for graceful shutdown."""
    config = JobSystemConfig.from_environment()
    configure_logging(config.log_level)

    metrics = JobMetrics()
    monitoring = MonitoringService(
        metrics,
        interval_seconds=config.poll_interval_seconds,
    )

    loop = asyncio.get_running_loop()
    install_signal_handlers(loop, monitoring.stop)

    logger.info(
        "Background job monitoring initialized for environment=%s.",
        config.environment,
    )

    await monitoring.run()


def main() -> None:
    """Start the monitoring application."""
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Monitoring interrupted by user.")


if __name__ == "__main__":
    main()

"""Application entry point and monitoring lifecycle for the background job system."""

from __future__ import annotations

import asyncio
import logging
import signal
from contextlib import suppress

from src.config import JobSystemConfig
from src.monitoring.metrics import JobMetrics

logger = logging.getLogger(__name__)


class MonitoringService:
    """Coordinate background metrics collection and periodic reporting."""

    def __init__(
        self,
        metrics: JobMetrics,
        *,
        interval_seconds: float = 15.0,
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be greater than zero.")

        self._metrics = metrics
        self._interval_seconds = interval_seconds
        self._stop_event = asyncio.Event()

    async def run(self) -> None:
        """Periodically publish a metrics snapshot until shutdown."""
        logger.info(
            "Starting monitoring service with interval=%s seconds.",
            self._interval_seconds,
        )

        try:
            while not self._stop_event.is_set():
                self._log_snapshot()
                await self._wait_for_next_interval()
        finally:
            self._log_snapshot()
            logger.info("Monitoring service stopped.")

    def stop(self) -> None:
        """Request graceful monitoring shutdown."""
        self._stop_event.set()

    def _log_snapshot(self) -> None:
        """Log the current metrics using structured, machine-readable fields."""
        snapshot = self._metrics.snapshot()

        logger.info(
            (
                "job_metrics jobs_submitted=%d jobs_started=%d "
                "jobs_succeeded=%d jobs_failed=%d jobs_dead_lettered=%d "
                "jobs_retried=%d active_jobs=%d "
                "total_execution_time_seconds=%.3f "
                "average_execution_time_seconds=%.3f"
            ),
            snapshot.jobs_submitted,
            snapshot.jobs_started,
            snapshot.jobs_succeeded,
            snapshot.jobs_failed,
            snapshot.jobs_dead_lettered,
            snapshot.jobs_retried,
            snapshot.active_jobs,
            snapshot.total_execution_time_seconds,
            snapshot.average_execution_time_seconds,
        )

    async def _wait_for_next_interval(self) -> None:
        """Wait for either the next reporting interval or shutdown."""
        try:
            await asyncio.wait_for(
                self._stop_event.wait(),
                timeout=self._interval_seconds,
            )
        except TimeoutError:
            pass


def configure_logging(level: str) -> None:
    """Configure process-wide logging for the job system."""
    normalized_level = level.strip().upper()

    numeric_level = getattr(logging, normalized_level, None)

    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level!r}.")

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def install_signal_handlers(
    loop: asyncio.AbstractEventLoop,
    stop_callback: callable,
) -> None:
    """Register graceful-shutdown handlers where the platform supports them."""
    for signal_name in ("SIGINT", "SIGTERM"):
        signal_value = getattr(signal, signal_name, None)

        if signal_value is None:
            continue

        with suppress(NotImplementedError):
            loop.add_signal_handler(signal_value, stop_callback)


async def run() -> None:
    """Start the monitoring component and wait for graceful shutdown."""
    config = JobSystemConfig.from_environment()
    configure_logging(config.log_level)

    metrics = JobMetrics()
    monitoring = MonitoringService(
        metrics,
        interval_seconds=config.poll_interval_seconds,
    )

    loop = asyncio.get_running_loop()
    install_signal_handlers(loop, monitoring.stop)

    logger.info(
        "Background job monitoring initialized for environment=%s.",
        config.environment,
    )

    await monitoring.run()


def main() -> None:
    """Start the monitoring application."""
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Monitoring interrupted by user.")


if __name__ == "__main__":
    main()