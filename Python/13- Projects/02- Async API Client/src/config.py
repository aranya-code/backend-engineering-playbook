"""Configuration models for the asynchronous API client."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Final


DEFAULT_TIMEOUT_SECONDS: Final[float] = 10.0
DEFAULT_MAX_RETRIES: Final[int] = 3
DEFAULT_MAX_CONCURRENCY: Final[int] = 10
DEFAULT_RATE_LIMIT_PER_SECOND: Final[float] = 10.0


def _get_positive_float(name: str, default: float) -> float:
    """Read a positive floating-point environment variable."""
    value = os.getenv(name)

    if value is None:
        return default

    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a valid floating-point number.") from exc

    if parsed <= 0:
        raise ValueError(f"{name} must be greater than zero.")

    return parsed


def _get_non_negative_int(name: str, default: int) -> int:
    """Read a non-negative integer environment variable."""
    value = os.getenv(name)

    if value is None:
        return default

    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a valid integer.") from exc

    if parsed < 0:
        raise ValueError(f"{name} must not be negative.")

    return parsed


def _get_positive_int(name: str, default: int) -> int:
    """Read a positive integer environment variable."""
    value = os.getenv(name)

    if value is None:
        return default

    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a valid integer.") from exc

    if parsed <= 0:
        raise ValueError(f"{name} must be greater than zero.")

    return parsed


@dataclass(frozen=True, slots=True)
class ClientConfig:
    """Immutable runtime configuration for the asynchronous API client."""

    base_url: str
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    max_retries: int = DEFAULT_MAX_RETRIES
    max_concurrency: int = DEFAULT_MAX_CONCURRENCY
    rate_limit_per_second: float = DEFAULT_RATE_LIMIT_PER_SECOND
    api_key: str | None = None

    def __post_init__(self) -> None:
        """Validate configuration invariants."""
        normalized_base_url = self.base_url.strip().rstrip("/")

        if not normalized_base_url:
            raise ValueError("base_url must not be empty.")

        if not normalized_base_url.startswith(("http://", "https://")):
            raise ValueError("base_url must use HTTP or HTTPS.")

        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero.")

        if self.max_retries < 0:
            raise ValueError("max_retries must not be negative.")

        if self.max_concurrency <= 0:
            raise ValueError("max_concurrency must be greater than zero.")

        if self.rate_limit_per_second <= 0:
            raise ValueError("rate_limit_per_second must be greater than zero.")

        object.__setattr__(self, "base_url", normalized_base_url)

    @classmethod
    def from_environment(cls) -> ClientConfig:
        """Build client configuration from environment variables."""
        base_url = os.getenv("API_BASE_URL", "").strip()

        if not base_url:
            raise ValueError("API_BASE_URL must be configured.")

        return cls(
            base_url=base_url,
            timeout_seconds=_get_positive_float(
                "API_TIMEOUT_SECONDS",
                DEFAULT_TIMEOUT_SECONDS,
            ),
            max_retries=_get_non_negative_int(
                "API_MAX_RETRIES",
                DEFAULT_MAX_RETRIES,
            ),
            max_concurrency=_get_positive_int(
                "API_MAX_CONCURRENCY",
                DEFAULT_MAX_CONCURRENCY,
            ),
            rate_limit_per_second=_get_positive_float(
                "API_RATE_LIMIT_PER_SECOND",
                DEFAULT_RATE_LIMIT_PER_SECOND,
            ),
            api_key=os.getenv("API_KEY"),
        )

"""Configuration models for the asynchronous API client."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Final


DEFAULT_TIMEOUT_SECONDS: Final[float] = 10.0
DEFAULT_MAX_RETRIES: Final[int] = 3
DEFAULT_MAX_CONCURRENCY: Final[int] = 10
DEFAULT_RATE_LIMIT_PER_SECOND: Final[float] = 10.0


def _get_positive_float(name: str, default: float) -> float:
    """Read a positive floating-point environment variable."""
    value = os.getenv(name)

    if value is None:
        return default

    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a valid floating-point number.") from exc

    if parsed <= 0:
        raise ValueError(f"{name} must be greater than zero.")

    return parsed


def _get_non_negative_int(name: str, default: int) -> int:
    """Read a non-negative integer environment variable."""
    value = os.getenv(name)

    if value is None:
        return default

    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a valid integer.") from exc

    if parsed < 0:
        raise ValueError(f"{name} must not be negative.")

    return parsed


def _get_positive_int(name: str, default: int) -> int:
    """Read a positive integer environment variable."""
    value = os.getenv(name)

    if value is None:
        return default

    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a valid integer.") from exc

    if parsed <= 0:
        raise ValueError(f"{name} must be greater than zero.")

    return parsed


@dataclass(frozen=True, slots=True)
class ClientConfig:
    """Immutable runtime configuration for the asynchronous API client."""

    base_url: str
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    max_retries: int = DEFAULT_MAX_RETRIES
    max_concurrency: int = DEFAULT_MAX_CONCURRENCY
    rate_limit_per_second: float = DEFAULT_RATE_LIMIT_PER_SECOND
    api_key: str | None = None

    def __post_init__(self) -> None:
        """Validate configuration invariants."""
        normalized_base_url = self.base_url.strip().rstrip("/")

        if not normalized_base_url:
            raise ValueError("base_url must not be empty.")

        if not normalized_base_url.startswith(("http://", "https://")):
            raise ValueError("base_url must use HTTP or HTTPS.")

        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero.")

        if self.max_retries < 0:
            raise ValueError("max_retries must not be negative.")

        if self.max_concurrency <= 0:
            raise ValueError("max_concurrency must be greater than zero.")

        if self.rate_limit_per_second <= 0:
            raise ValueError("rate_limit_per_second must be greater than zero.")

        object.__setattr__(self, "base_url", normalized_base_url)

    @classmethod
    def from_environment(cls) -> ClientConfig:
        """Build client configuration from environment variables."""
        base_url = os.getenv("API_BASE_URL", "").strip()

        if not base_url:
            raise ValueError("API_BASE_URL must be configured.")

        return cls(
            base_url=base_url,
            timeout_seconds=_get_positive_float(
                "API_TIMEOUT_SECONDS",
                DEFAULT_TIMEOUT_SECONDS,
            ),
            max_retries=_get_non_negative_int(
                "API_MAX_RETRIES",
                DEFAULT_MAX_RETRIES,
            ),
            max_concurrency=_get_positive_int(
                "API_MAX_CONCURRENCY",
                DEFAULT_MAX_CONCURRENCY,
            ),
            rate_limit_per_second=_get_positive_float(
                "API_RATE_LIMIT_PER_SECOND",
                DEFAULT_RATE_LIMIT_PER_SECOND,
            ),
            api_key=os.getenv("API_KEY"),
        )