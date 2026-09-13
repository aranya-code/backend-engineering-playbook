"""Runtime configuration for the background job system."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Final


DEFAULT_WORKER_CONCURRENCY: Final[int] = 4
DEFAULT_MAX_RETRIES: Final[int] = 3
DEFAULT_RETRY_DELAY_SECONDS: Final[float] = 1.0
DEFAULT_VISIBILITY_TIMEOUT_SECONDS: Final[int] = 300
DEFAULT_POLL_INTERVAL_SECONDS: Final[float] = 1.0
DEFAULT_JOB_TIMEOUT_SECONDS: Final[int] = 600
DEFAULT_SHUTDOWN_TIMEOUT_SECONDS: Final[int] = 30


def _get_int(name: str, default: int, *, minimum: int = 0) -> int:
    """Read and validate an integer environment variable."""
    value = os.getenv(name)

    if value is None:
        return default

    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a valid integer.") from exc

    if parsed < minimum:
        raise ValueError(f"{name} must be greater than or equal to {minimum}.")

    return parsed


def _get_float(name: str, default: float, *, minimum: float = 0.0) -> float:
    """Read and validate a floating-point environment variable."""
    value = os.getenv(name)

    if value is None:
        return default

    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a valid floating-point number.") from exc

    if parsed < minimum:
        raise ValueError(f"{name} must be greater than or equal to {minimum}.")

    return parsed


def _get_required(name: str) -> str:
    """Read a required non-empty environment variable."""
    value = os.getenv(name, "").strip()

    if not value:
        raise ValueError(f"{name} must be configured.")

    return value


@dataclass(frozen=True, slots=True)
class JobSystemConfig:
    """Immutable runtime configuration for the background job system."""

    environment: str = "development"
    queue_url: str = "memory://jobs"
    worker_concurrency: int = DEFAULT_WORKER_CONCURRENCY
    max_retries: int = DEFAULT_MAX_RETRIES
    retry_delay_seconds: float = DEFAULT_RETRY_DELAY_SECONDS
    visibility_timeout_seconds: int = DEFAULT_VISIBILITY_TIMEOUT_SECONDS
    poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS
    job_timeout_seconds: int = DEFAULT_JOB_TIMEOUT_SECONDS
    shutdown_timeout_seconds: int = DEFAULT_SHUTDOWN_TIMEOUT_SECONDS
    log_level: str = "INFO"

    def __post_init__(self) -> None:
        """Validate configuration invariants."""
        if not self.environment.strip():
            raise ValueError("environment must not be empty.")

        if not self.queue_url.strip():
            raise ValueError("queue_url must not be empty.")

        if self.worker_concurrency <= 0:
            raise ValueError("worker_concurrency must be greater than zero.")

        if self.max_retries < 0:
            raise ValueError("max_retries must not be negative.")

        if self.retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds must not be negative.")

        if self.visibility_timeout_seconds <= 0:
            raise ValueError("visibility_timeout_seconds must be greater than zero.")

        if self.poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be greater than zero.")

        if self.job_timeout_seconds <= 0:
            raise ValueError("job_timeout_seconds must be greater than zero.")

        if self.shutdown_timeout_seconds <= 0:
            raise ValueError("shutdown_timeout_seconds must be greater than zero.")

        if not self.log_level.strip():
            raise ValueError("log_level must not be empty.")

    @classmethod
    def from_environment(cls) -> JobSystemConfig:
        """Build job-system configuration from environment variables."""
        return cls(
            environment=os.getenv("APP_ENVIRONMENT", "development").strip(),
            queue_url=os.getenv("JOB_QUEUE_URL", "memory://jobs").strip(),
            worker_concurrency=_get_int(
                "JOB_WORKER_CONCURRENCY",
                DEFAULT_WORKER_CONCURRENCY,
                minimum=1,
            ),
            max_retries=_get_int(
                "JOB_MAX_RETRIES",
                DEFAULT_MAX_RETRIES,
                minimum=0,
            ),
            retry_delay_seconds=_get_float(
                "JOB_RETRY_DELAY_SECONDS",
                DEFAULT_RETRY_DELAY_SECONDS,
                minimum=0.0,
            ),
            visibility_timeout_seconds=_get_int(
                "JOB_VISIBILITY_TIMEOUT_SECONDS",
                DEFAULT_VISIBILITY_TIMEOUT_SECONDS,
                minimum=1,
            ),
            poll_interval_seconds=_get_float(
                "JOB_POLL_INTERVAL_SECONDS",
                DEFAULT_POLL_INTERVAL_SECONDS,
                minimum=0.01,
            ),
            job_timeout_seconds=_get_int(
                "JOB_TIMEOUT_SECONDS",
                DEFAULT_JOB_TIMEOUT_SECONDS,
                minimum=1,
            ),
            shutdown_timeout_seconds=_get_int(
                "JOB_SHUTDOWN_TIMEOUT_SECONDS",
                DEFAULT_SHUTDOWN_TIMEOUT_SECONDS,
                minimum=1,
            ),
            log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
        )

"""Runtime configuration for the background job system."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Final


DEFAULT_WORKER_CONCURRENCY: Final[int] = 4
DEFAULT_MAX_RETRIES: Final[int] = 3
DEFAULT_RETRY_DELAY_SECONDS: Final[float] = 1.0
DEFAULT_VISIBILITY_TIMEOUT_SECONDS: Final[int] = 300
DEFAULT_POLL_INTERVAL_SECONDS: Final[float] = 1.0
DEFAULT_JOB_TIMEOUT_SECONDS: Final[int] = 600
DEFAULT_SHUTDOWN_TIMEOUT_SECONDS: Final[int] = 30


def _get_int(name: str, default: int, *, minimum: int = 0) -> int:
    """Read and validate an integer environment variable."""
    value = os.getenv(name)

    if value is None:
        return default

    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a valid integer.") from exc

    if parsed < minimum:
        raise ValueError(f"{name} must be greater than or equal to {minimum}.")

    return parsed


def _get_float(name: str, default: float, *, minimum: float = 0.0) -> float:
    """Read and validate a floating-point environment variable."""
    value = os.getenv(name)

    if value is None:
        return default

    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a valid floating-point number.") from exc

    if parsed < minimum:
        raise ValueError(f"{name} must be greater than or equal to {minimum}.")

    return parsed


def _get_required(name: str) -> str:
    """Read a required non-empty environment variable."""
    value = os.getenv(name, "").strip()

    if not value:
        raise ValueError(f"{name} must be configured.")

    return value


@dataclass(frozen=True, slots=True)
class JobSystemConfig:
    """Immutable runtime configuration for the background job system."""

    environment: str = "development"
    queue_url: str = "memory://jobs"
    worker_concurrency: int = DEFAULT_WORKER_CONCURRENCY
    max_retries: int = DEFAULT_MAX_RETRIES
    retry_delay_seconds: float = DEFAULT_RETRY_DELAY_SECONDS
    visibility_timeout_seconds: int = DEFAULT_VISIBILITY_TIMEOUT_SECONDS
    poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS
    job_timeout_seconds: int = DEFAULT_JOB_TIMEOUT_SECONDS
    shutdown_timeout_seconds: int = DEFAULT_SHUTDOWN_TIMEOUT_SECONDS
    log_level: str = "INFO"

    def __post_init__(self) -> None:
        """Validate configuration invariants."""
        if not self.environment.strip():
            raise ValueError("environment must not be empty.")

        if not self.queue_url.strip():
            raise ValueError("queue_url must not be empty.")

        if self.worker_concurrency <= 0:
            raise ValueError("worker_concurrency must be greater than zero.")

        if self.max_retries < 0:
            raise ValueError("max_retries must not be negative.")

        if self.retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds must not be negative.")

        if self.visibility_timeout_seconds <= 0:
            raise ValueError("visibility_timeout_seconds must be greater than zero.")

        if self.poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be greater than zero.")

        if self.job_timeout_seconds <= 0:
            raise ValueError("job_timeout_seconds must be greater than zero.")

        if self.shutdown_timeout_seconds <= 0:
            raise ValueError("shutdown_timeout_seconds must be greater than zero.")

        if not self.log_level.strip():
            raise ValueError("log_level must not be empty.")

    @classmethod
    def from_environment(cls) -> JobSystemConfig:
        """Build job-system configuration from environment variables."""
        return cls(
            environment=os.getenv("APP_ENVIRONMENT", "development").strip(),
            queue_url=os.getenv("JOB_QUEUE_URL", "memory://jobs").strip(),
            worker_concurrency=_get_int(
                "JOB_WORKER_CONCURRENCY",
                DEFAULT_WORKER_CONCURRENCY,
                minimum=1,
            ),
            max_retries=_get_int(
                "JOB_MAX_RETRIES",
                DEFAULT_MAX_RETRIES,
                minimum=0,
            ),
            retry_delay_seconds=_get_float(
                "JOB_RETRY_DELAY_SECONDS",
                DEFAULT_RETRY_DELAY_SECONDS,
                minimum=0.0,
            ),
            visibility_timeout_seconds=_get_int(
                "JOB_VISIBILITY_TIMEOUT_SECONDS",
                DEFAULT_VISIBILITY_TIMEOUT_SECONDS,
                minimum=1,
            ),
            poll_interval_seconds=_get_float(
                "JOB_POLL_INTERVAL_SECONDS",
                DEFAULT_POLL_INTERVAL_SECONDS,
                minimum=0.01,
            ),
            job_timeout_seconds=_get_int(
                "JOB_TIMEOUT_SECONDS",
                DEFAULT_JOB_TIMEOUT_SECONDS,
                minimum=1,
            ),
            shutdown_timeout_seconds=_get_int(
                "JOB_SHUTDOWN_TIMEOUT_SECONDS",
                DEFAULT_SHUTDOWN_TIMEOUT_SECONDS,
                minimum=1,
            ),
            log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
        )