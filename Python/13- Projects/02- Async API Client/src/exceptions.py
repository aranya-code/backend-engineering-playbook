"""Exception hierarchy for the asynchronous API client."""

from __future__ import annotations

from typing import Any


class APIClientError(Exception):
    """Base exception for client-side API failures."""


class APIResponseError(APIClientError):
    """Raised when an external API returns an unsuccessful or invalid response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_data: Any = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data
        self.request_id = request_id


class APITimeoutError(APIClientError):
    """Raised when an API request exceeds its configured timeout."""


class APINetworkError(APIClientError):
    """Raised when a network-level failure prevents an API request."""


class APIRateLimitError(APIResponseError):
    """Raised when the external API rejects a request because of rate limits."""

    def __init__(
        self,
        message: str = "The API rate limit was exceeded.",
        *,
        retry_after: float | None = None,
        status_code: int = 429,
        response_data: Any = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=status_code,
            response_data=response_data,
            request_id=request_id,
        )
        self.retry_after = retry_after


class APIRetryExhaustedError(APIClientError):
    """Raised when all configured retry attempts have been exhausted."""

    def __init__(
        self,
        message: str,
        *,
        attempts: int,
        last_error: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.attempts = attempts
        self.last_error = last_error


class APIResponseValidationError(APIResponseError):
    """Raised when a successful API response fails schema validation."""

"""Exception hierarchy for the asynchronous API client."""

from __future__ import annotations

from typing import Any


class APIClientError(Exception):
    """Base exception for client-side API failures."""


class APIResponseError(APIClientError):
    """Raised when an external API returns an unsuccessful or invalid response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_data: Any = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data
        self.request_id = request_id


class APITimeoutError(APIClientError):
    """Raised when an API request exceeds its configured timeout."""


class APINetworkError(APIClientError):
    """Raised when a network-level failure prevents an API request."""


class APIRateLimitError(APIResponseError):
    """Raised when the external API rejects a request because of rate limits."""

    def __init__(
        self,
        message: str = "The API rate limit was exceeded.",
        *,
        retry_after: float | None = None,
        status_code: int = 429,
        response_data: Any = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=status_code,
            response_data=response_data,
            request_id=request_id,
        )
        self.retry_after = retry_after


class APIRetryExhaustedError(APIClientError):
    """Raised when all configured retry attempts have been exhausted."""

    def __init__(
        self,
        message: str,
        *,
        attempts: int,
        last_error: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.attempts = attempts
        self.last_error = last_error


class APIResponseValidationError(APIResponseError):
    """Raised when a successful API response fails schema validation."""