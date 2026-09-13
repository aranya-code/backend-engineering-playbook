"""Runtime configuration for the Webhook Processing Service."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Final


DEFAULT_HOST: Final[str] = "127.0.0.1"
DEFAULT_PORT: Final[int] = 8000
DEFAULT_LOG_LEVEL: Final[str] = "INFO"
DEFAULT_WEBHOOK_PATH: Final[str] = "/webhooks"
DEFAULT_QUEUE_URL: Final[str] = "memory://webhooks"
DEFAULT_MAX_WORKERS: Final[int] = 4
DEFAULT_MAX_RETRIES: Final[int] = 3
DEFAULT_RETRY_DELAY_SECONDS: Final[float] = 1.0
DEFAULT_REPLAY_WINDOW_SECONDS: Final[int] = 300
DEFAULT_REQUEST_TIMEOUT_SECONDS: Final[float] = 10.0


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


def _get_bool(name: str, default: bool) -> bool:
    """Read a boolean environment variable using explicit accepted values."""
    value = os.getenv(name)

    if value is None:
        return default

    normalized = value.strip().lower()

    if normalized in {"1", "true", "yes", "on"}:
        return True

    if normalized in {"0", "false", "no", "off"}:
        return False

    raise ValueError(
        f"{name} must be one of: true, false, yes, no, 1, 0, on, off."
    )


@dataclass(frozen=True, slots=True)
class WebhookServiceConfig:
    """Immutable runtime configuration for webhook processing."""

    environment: str = "development"
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    webhook_path: str = DEFAULT_WEBHOOK_PATH
    queue_url: str = DEFAULT_QUEUE_URL
    max_workers: int = DEFAULT_MAX_WORKERS
    max_retries: int = DEFAULT_MAX_RETRIES
    retry_delay_seconds: float = DEFAULT_RETRY_DELAY_SECONDS
    replay_window_seconds: int = DEFAULT_REPLAY_WINDOW_SECONDS
    request_timeout_seconds: float = DEFAULT_REQUEST_TIMEOUT_SECONDS
    signature_validation_enabled: bool = True
    idempotency_enabled: bool = True
    graceful_shutdown: bool = True
    log_level: str = DEFAULT_LOG_LEVEL

    def __post_init__(self) -> None:
        """Validate configuration invariants."""
        if not self.environment.strip():
            raise ValueError("environment must not be empty.")

        if not self.host.strip():
            raise ValueError("host must not be empty.")

        if not 1 <= self.port <= 65535:
            raise ValueError("port must be between 1 and 65535.")

        normalized_path = self.webhook_path.strip()

        if not normalized_path.startswith("/"):
            raise ValueError("webhook_path must start with '/'.")

        if not self.queue_url.strip():
            raise ValueError("queue_url must not be empty.")

        if self.max_workers <= 0:
            raise ValueError("max_workers must be greater than zero.")

        if self.max_retries < 0:
            raise ValueError("max_retries must not be negative.")

        if self.retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds must not be negative.")

        if self.replay_window_seconds <= 0:
            raise ValueError("replay_window_seconds must be greater than zero.")

        if self.request_timeout_seconds <= 0:
            raise ValueError("request_timeout_seconds must be greater than zero.")

        if not self.log_level.strip():
            raise ValueError("log_level must not be empty.")

        object.__setattr__(self, "webhook_path", normalized_path)
        object.__setattr__(self, "log_level", self.log_level.strip().upper())

    @classmethod
    def from_environment(cls) -> WebhookServiceConfig:
        """Build service configuration from environment variables."""
        return cls(
            environment=os.getenv("APP_ENVIRONMENT", "development").strip(),
            host=os.getenv("WEBHOOK_HOST", DEFAULT_HOST).strip(),
            port=_get_int("WEBHOOK_PORT", DEFAULT_PORT, minimum=1),
            webhook_path=os.getenv(
                "WEBHOOK_PATH",
                DEFAULT_WEBHOOK_PATH,
            ).strip(),
            queue_url=os.getenv(
                "WEBHOOK_QUEUE_URL",
                DEFAULT_QUEUE_URL,
            ).strip(),
            max_workers=_get_int(
                "WEBHOOK_MAX_WORKERS",
                DEFAULT_MAX_WORKERS,
                minimum=1,
            ),
            max_retries=_get_int(
                "WEBHOOK_MAX_RETRIES",
                DEFAULT_MAX_RETRIES,
                minimum=0,
            ),
            retry_delay_seconds=_get_float(
                "WEBHOOK_RETRY_DELAY_SECONDS",
                DEFAULT_RETRY_DELAY_SECONDS,
                minimum=0.0,
            ),
            replay_window_seconds=_get_int(
                "WEBHOOK_REPLAY_WINDOW_SECONDS",
                DEFAULT_REPLAY_WINDOW_SECONDS,
                minimum=1,
            ),
            request_timeout_seconds=_get_float(
                "WEBHOOK_REQUEST_TIMEOUT_SECONDS",
                DEFAULT_REQUEST_TIMEOUT_SECONDS,
                minimum=0.1,
            ),
            signature_validation_enabled=_get_bool(
                "WEBHOOK_SIGNATURE_VALIDATION",
                True,
            ),
            idempotency_enabled=_get_bool(
                "WEBHOOK_IDEMPOTENCY_ENABLED",
                True,
            ),
            graceful_shutdown=_get_bool(
                "WEBHOOK_GRACEFUL_SHUTDOWN",
                True,
            ),
            log_level=os.getenv(
                "LOG_LEVEL",
                DEFAULT_LOG_LEVEL,
            ).strip().upper(),
        )

"""Runtime configuration for the Webhook Processing Service."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Final


DEFAULT_HOST: Final[str] = "127.0.0.1"
DEFAULT_PORT: Final[int] = 8000
DEFAULT_LOG_LEVEL: Final[str] = "INFO"
DEFAULT_WEBHOOK_PATH: Final[str] = "/webhooks"
DEFAULT_QUEUE_URL: Final[str] = "memory://webhooks"
DEFAULT_MAX_WORKERS: Final[int] = 4
DEFAULT_MAX_RETRIES: Final[int] = 3
DEFAULT_RETRY_DELAY_SECONDS: Final[float] = 1.0
DEFAULT_REPLAY_WINDOW_SECONDS: Final[int] = 300
DEFAULT_REQUEST_TIMEOUT_SECONDS: Final[float] = 10.0


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


def _get_bool(name: str, default: bool) -> bool:
    """Read a boolean environment variable using explicit accepted values."""
    value = os.getenv(name)

    if value is None:
        return default

    normalized = value.strip().lower()

    if normalized in {"1", "true", "yes", "on"}:
        return True

    if normalized in {"0", "false", "no", "off"}:
        return False

    raise ValueError(
        f"{name} must be one of: true, false, yes, no, 1, 0, on, off."
    )


@dataclass(frozen=True, slots=True)
class WebhookServiceConfig:
    """Immutable runtime configuration for webhook processing."""

    environment: str = "development"
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    webhook_path: str = DEFAULT_WEBHOOK_PATH
    queue_url: str = DEFAULT_QUEUE_URL
    max_workers: int = DEFAULT_MAX_WORKERS
    max_retries: int = DEFAULT_MAX_RETRIES
    retry_delay_seconds: float = DEFAULT_RETRY_DELAY_SECONDS
    replay_window_seconds: int = DEFAULT_REPLAY_WINDOW_SECONDS
    request_timeout_seconds: float = DEFAULT_REQUEST_TIMEOUT_SECONDS
    signature_validation_enabled: bool = True
    idempotency_enabled: bool = True
    graceful_shutdown: bool = True
    log_level: str = DEFAULT_LOG_LEVEL

    def __post_init__(self) -> None:
        """Validate configuration invariants."""
        if not self.environment.strip():
            raise ValueError("environment must not be empty.")

        if not self.host.strip():
            raise ValueError("host must not be empty.")

        if not 1 <= self.port <= 65535:
            raise ValueError("port must be between 1 and 65535.")

        normalized_path = self.webhook_path.strip()

        if not normalized_path.startswith("/"):
            raise ValueError("webhook_path must start with '/'.")

        if not self.queue_url.strip():
            raise ValueError("queue_url must not be empty.")

        if self.max_workers <= 0:
            raise ValueError("max_workers must be greater than zero.")

        if self.max_retries < 0:
            raise ValueError("max_retries must not be negative.")

        if self.retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds must not be negative.")

        if self.replay_window_seconds <= 0:
            raise ValueError("replay_window_seconds must be greater than zero.")

        if self.request_timeout_seconds <= 0:
            raise ValueError("request_timeout_seconds must be greater than zero.")

        if not self.log_level.strip():
            raise ValueError("log_level must not be empty.")

        object.__setattr__(self, "webhook_path", normalized_path)
        object.__setattr__(self, "log_level", self.log_level.strip().upper())

    @classmethod
    def from_environment(cls) -> WebhookServiceConfig:
        """Build service configuration from environment variables."""
        return cls(
            environment=os.getenv("APP_ENVIRONMENT", "development").strip(),
            host=os.getenv("WEBHOOK_HOST", DEFAULT_HOST).strip(),
            port=_get_int("WEBHOOK_PORT", DEFAULT_PORT, minimum=1),
            webhook_path=os.getenv(
                "WEBHOOK_PATH",
                DEFAULT_WEBHOOK_PATH,
            ).strip(),
            queue_url=os.getenv(
                "WEBHOOK_QUEUE_URL",
                DEFAULT_QUEUE_URL,
            ).strip(),
            max_workers=_get_int(
                "WEBHOOK_MAX_WORKERS",
                DEFAULT_MAX_WORKERS,
                minimum=1,
            ),
            max_retries=_get_int(
                "WEBHOOK_MAX_RETRIES",
                DEFAULT_MAX_RETRIES,
                minimum=0,
            ),
            retry_delay_seconds=_get_float(
                "WEBHOOK_RETRY_DELAY_SECONDS",
                DEFAULT_RETRY_DELAY_SECONDS,
                minimum=0.0,
            ),
            replay_window_seconds=_get_int(
                "WEBHOOK_REPLAY_WINDOW_SECONDS",
                DEFAULT_REPLAY_WINDOW_SECONDS,
                minimum=1,
            ),
            request_timeout_seconds=_get_float(
                "WEBHOOK_REQUEST_TIMEOUT_SECONDS",
                DEFAULT_REQUEST_TIMEOUT_SECONDS,
                minimum=0.1,
            ),
            signature_validation_enabled=_get_bool(
                "WEBHOOK_SIGNATURE_VALIDATION",
                True,
            ),
            idempotency_enabled=_get_bool(
                "WEBHOOK_IDEMPOTENCY_ENABLED",
                True,
            ),
            graceful_shutdown=_get_bool(
                "WEBHOOK_GRACEFUL_SHUTDOWN",
                True,
            ),
            log_level=os.getenv(
                "LOG_LEVEL",
                DEFAULT_LOG_LEVEL,
            ).strip().upper(),
        )