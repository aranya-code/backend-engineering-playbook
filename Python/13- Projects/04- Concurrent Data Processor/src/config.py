"""Runtime configuration for the concurrent data processor."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Final


DEFAULT_WORKER_COUNT: Final[int] = 4
DEFAULT_BATCH_SIZE: Final[int] = 100
DEFAULT_QUEUE_SIZE: Final[int] = 1_000
DEFAULT_CHUNK_SIZE: Final[int] = 10_000
DEFAULT_TASK_TIMEOUT_SECONDS: Final[float] = 300.0
DEFAULT_LOG_LEVEL: Final[str] = "INFO"


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
        raise ValueError(
            f"{name} must be greater than or equal to {minimum}.",
        )

    return parsed


def _get_float(name: str, default: float, *, minimum: float = 0.0) -> float:
    """Read and validate a floating-point environment variable."""
    value = os.getenv(name)

    if value is None:
        return default

    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(
            f"{name} must be a valid floating-point number.",
        ) from exc

    if parsed < minimum:
        raise ValueError(
            f"{name} must be greater than or equal to {minimum}.",
        )

    return parsed


@dataclass(frozen=True, slots=True)
class ProcessorConfig:
    """Immutable runtime configuration for data-processing workloads."""

    input_path: str = "data/input"
    output_path: str = "data/output"
    worker_count: int = DEFAULT_WORKER_COUNT
    batch_size: int = DEFAULT_BATCH_SIZE
    queue_size: int = DEFAULT_QUEUE_SIZE
    chunk_size: int = DEFAULT_CHUNK_SIZE
    task_timeout_seconds: float = DEFAULT_TASK_TIMEOUT_SECONDS
    log_level: str = DEFAULT_LOG_LEVEL

    def __post_init__(self) -> None:
        """Validate configuration invariants."""
        if not self.input_path.strip():
            raise ValueError("input_path must not be empty.")

        if not self.output_path.strip():
            raise ValueError("output_path must not be empty.")

        if self.worker_count <= 0:
            raise ValueError("worker_count must be greater than zero.")

        if self.batch_size <= 0:
            raise ValueError("batch_size must be greater than zero.")

        if self.queue_size <= 0:
            raise ValueError("queue_size must be greater than zero.")

        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero.")

        if self.task_timeout_seconds <= 0:
            raise ValueError("task_timeout_seconds must be greater than zero.")

        if not self.log_level.strip():
            raise ValueError("log_level must not be empty.")

    @classmethod
    def from_environment(cls) -> ProcessorConfig:
        """Build processor configuration from environment variables."""
        return cls(
            input_path=os.getenv("PROCESSOR_INPUT_PATH", "data/input").strip(),
            output_path=os.getenv("PROCESSOR_OUTPUT_PATH", "data/output").strip(),
            worker_count=_get_int(
                "PROCESSOR_WORKER_COUNT",
                DEFAULT_WORKER_COUNT,
                minimum=1,
            ),
            batch_size=_get_int(
                "PROCESSOR_BATCH_SIZE",
                DEFAULT_BATCH_SIZE,
                minimum=1,
            ),
            queue_size=_get_int(
                "PROCESSOR_QUEUE_SIZE",
                DEFAULT_QUEUE_SIZE,
                minimum=1,
            ),
            chunk_size=_get_int(
                "PROCESSOR_CHUNK_SIZE",
                DEFAULT_CHUNK_SIZE,
                minimum=1,
            ),
            task_timeout_seconds=_get_float(
                "PROCESSOR_TASK_TIMEOUT_SECONDS",
                DEFAULT_TASK_TIMEOUT_SECONDS,
                minimum=0.01,
            ),
            log_level=os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).strip().upper(),
        )

"""Runtime configuration for the concurrent data processor."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Final


DEFAULT_WORKER_COUNT: Final[int] = 4
DEFAULT_BATCH_SIZE: Final[int] = 100
DEFAULT_QUEUE_SIZE: Final[int] = 1_000
DEFAULT_CHUNK_SIZE: Final[int] = 10_000
DEFAULT_TASK_TIMEOUT_SECONDS: Final[float] = 300.0
DEFAULT_LOG_LEVEL: Final[str] = "INFO"


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
        raise ValueError(
            f"{name} must be greater than or equal to {minimum}.",
        )

    return parsed


def _get_float(name: str, default: float, *, minimum: float = 0.0) -> float:
    """Read and validate a floating-point environment variable."""
    value = os.getenv(name)

    if value is None:
        return default

    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(
            f"{name} must be a valid floating-point number.",
        ) from exc

    if parsed < minimum:
        raise ValueError(
            f"{name} must be greater than or equal to {minimum}.",
        )

    return parsed


@dataclass(frozen=True, slots=True)
class ProcessorConfig:
    """Immutable runtime configuration for data-processing workloads."""

    input_path: str = "data/input"
    output_path: str = "data/output"
    worker_count: int = DEFAULT_WORKER_COUNT
    batch_size: int = DEFAULT_BATCH_SIZE
    queue_size: int = DEFAULT_QUEUE_SIZE
    chunk_size: int = DEFAULT_CHUNK_SIZE
    task_timeout_seconds: float = DEFAULT_TASK_TIMEOUT_SECONDS
    log_level: str = DEFAULT_LOG_LEVEL

    def __post_init__(self) -> None:
        """Validate configuration invariants."""
        if not self.input_path.strip():
            raise ValueError("input_path must not be empty.")

        if not self.output_path.strip():
            raise ValueError("output_path must not be empty.")

        if self.worker_count <= 0:
            raise ValueError("worker_count must be greater than zero.")

        if self.batch_size <= 0:
            raise ValueError("batch_size must be greater than zero.")

        if self.queue_size <= 0:
            raise ValueError("queue_size must be greater than zero.")

        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero.")

        if self.task_timeout_seconds <= 0:
            raise ValueError("task_timeout_seconds must be greater than zero.")

        if not self.log_level.strip():
            raise ValueError("log_level must not be empty.")

    @classmethod
    def from_environment(cls) -> ProcessorConfig:
        """Build processor configuration from environment variables."""
        return cls(
            input_path=os.getenv("PROCESSOR_INPUT_PATH", "data/input").strip(),
            output_path=os.getenv("PROCESSOR_OUTPUT_PATH", "data/output").strip(),
            worker_count=_get_int(
                "PROCESSOR_WORKER_COUNT",
                DEFAULT_WORKER_COUNT,
                minimum=1,
            ),
            batch_size=_get_int(
                "PROCESSOR_BATCH_SIZE",
                DEFAULT_BATCH_SIZE,
                minimum=1,
            ),
            queue_size=_get_int(
                "PROCESSOR_QUEUE_SIZE",
                DEFAULT_QUEUE_SIZE,
                minimum=1,
            ),
            chunk_size=_get_int(
                "PROCESSOR_CHUNK_SIZE",
                DEFAULT_CHUNK_SIZE,
                minimum=1,
            ),
            task_timeout_seconds=_get_float(
                "PROCESSOR_TASK_TIMEOUT_SECONDS",
                DEFAULT_TASK_TIMEOUT_SECONDS,
                minimum=0.01,
            ),
            log_level=os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).strip().upper(),
        )