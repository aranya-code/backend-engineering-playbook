from __future__ import annotations

import logging
import random
import time
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urljoin

import requests
from requests import Response
from requests.adapters import HTTPAdapter

from .config import PipelineConfig, config


logger = logging.getLogger(__name__)


class APIClientError(RuntimeError):
    """Raised when an API request cannot be completed successfully."""


class APIHTTPError(APIClientError):
    """Raised when the API returns an unrecoverable HTTP error."""

    def __init__(
        self,
        status_code: int,
        message: str,
        *,
        response: Response | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response = response


@dataclass(frozen=True, slots=True)
class APIPage:
    """Represent one page returned by a paginated API."""

    items: list[dict[str, Any]]
    next_page: int | None
    raw: Mapping[str, Any]


class APIClient:
    """Production-oriented HTTP client for paginated JSON APIs."""

    _RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})

    def __init__(
        self,
        pipeline_config: PipelineConfig = config,
        *,
        session: requests.Session | None = None,
    ) -> None:
        self.config = pipeline_config
        self.session = session or requests.Session()

        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": (
                    "api-data-processing-pipeline/1.0"
                ),
            }
        )
        self.session.headers.update(
            self.config.authorization_headers
        )

        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=0,
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    @property
    def base_url(self) -> str:
        """Return the normalized API base URL."""
        value = self.config.api_base_url.strip()

        if not value:
            raise APIClientError("API base URL cannot be empty.")

        if not value.startswith(("http://", "https://")):
            raise APIClientError(
                "API base URL must use HTTP or HTTPS."
            )

        return value.rstrip("/") + "/"

    def build_url(self, endpoint: str) -> str:
        """Resolve an API endpoint against the configured base URL."""
        normalized_endpoint = endpoint.strip()

        if not normalized_endpoint:
            raise APIClientError(
                "API endpoint cannot be empty."
            )

        if normalized_endpoint.startswith(("http://", "https://")):
            return normalized_endpoint

        return urljoin(
            self.base_url,
            normalized_endpoint.lstrip("/"),
        )

    def _retry_delay(
        self,
        attempt: int,
        response: Response | None,
    ) -> float:
        """Calculate bounded exponential backoff with jitter."""
        if response is not None:
            retry_after = response.headers.get("Retry-After")

            if retry_after:
                try:
                    return max(
                        0.0,
                        min(
                            float(retry_after),
                            300.0,
                        ),
                    )
                except ValueError:
                    try:
                        retry_at = parsedate_to_datetime(
                            retry_after,
                        ).timestamp()
                    except (TypeError, ValueError, OverflowError):
                        retry_at = 0.0

                    if retry_at:
                        return max(
                            0.0,
                            min(
                                retry_at - time.time(),
                                300.0,
                            ),
                        )

        base_delay = self.config.api_backoff_factor * (
            2 ** max(attempt - 1, 0)
        )
        jitter = random.uniform(0.0, 0.25)

        return min(
            base_delay + jitter,
            300.0,
        )

    def _raise_for_status(
        self,
        response: Response,
    ) -> None:
        """Raise an API-specific exception for unsuccessful responses."""
        if response.ok:
            return

        message = (
            f"API request failed with HTTP "
            f"{response.status_code}: "
            f"{response.reason or 'unknown error'}"
        )

        if response.status_code == 401:
            message = "API authentication failed."
        elif response.status_code == 403:
            message = "API authorization failed."
        elif response.status_code == 404:
            message = "API endpoint was not found."
        elif response.status_code == 429:
            message = "API rate limit exceeded."

        raise APIHTTPError(
            response.status_code,
            message,
            response=response,
        )

    def request_json(
        self,
        endpoint: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a GET request and decode a JSON object response."""
        url = self.build_url(endpoint)

        for attempt in range(
            1,
            self.config.api_max_retries + 2,
        ):
            response: Response | None = None

            try:
                response = self.session.get(
                    url,
                    params=dict(params or {}),
                    timeout=self.config.request_timeout,
                )
            except requests.Timeout as exc:
                if attempt > self.config.api_max_retries:
                    raise APIClientError(
                        f"API request timed out after "
                        f"{attempt} attempt(s): {url}"
                    ) from exc

                delay = self._retry_delay(
                    attempt,
                    None,
                )
                logger.warning(
                    "API request timed out; retrying in %.2f seconds "
                    "(attempt %d/%d).",
                    delay,
                    attempt,
                    self.config.api_max_retries + 1,
                )
                time.sleep(delay)
                continue
            except requests.RequestException as exc:
                if attempt > self.config.api_max_retries:
                    raise APIClientError(
                        f"API request failed after "
                        f"{attempt} attempt(s): {url}"
                    ) from exc

                delay = self._retry_delay(
                    attempt,
                    None,
                )
                logger.warning(
                    "API request failed; retrying in %.2f seconds "
                    "(attempt %d/%d).",
                    delay,
                    attempt,
                    self.config.api_max_retries + 1,
                )
                time.sleep(delay)
                continue

            if (
                response.status_code
                in self._RETRYABLE_STATUS_CODES
                and attempt <= self.config.api_max_retries
            ):
                delay = self._retry_delay(
                    attempt,
                    response,
                )
                logger.warning(
                    "Received HTTP %d; retrying in %.2f seconds "
                    "(attempt %d/%d).",
                    response.status_code,
                    delay,
                    attempt,
                    self.config.api_max_retries + 1,
                )
                time.sleep(delay)
                continue

            self._raise_for_status(response)

            try:
                payload = response.json()
            except ValueError as exc:
                raise APIClientError(
                    f"API returned invalid JSON: {url}"
                ) from exc

            if not isinstance(payload, dict):
                raise APIClientError(
                    "API response must be a JSON object."
                )

            return payload

        raise APIClientError(
            f"API request failed unexpectedly: {url}"
        )

    def _extract_items(
        self,
        payload: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        """Extract and validate a list of records from an API payload."""
        raw_items = payload.get("data")

        if raw_items is None:
            raw_items = payload.get("items")

        if raw_items is None:
            raise APIClientError(
                "API response does not contain 'data' or 'items'."
            )

        if not isinstance(raw_items, list):
            raise APIClientError(
                "API response 'data' or 'items' field must be a list."
            )

        items: list[dict[str, Any]] = []

        for index, item in enumerate(raw_items):
            if not isinstance(item, dict):
                raise APIClientError(
                    "API record at index "
                    f"{index} is not a JSON object."
                )

            items.append(item)

        return items

    def _extract_next_page(
        self,
        payload: Mapping[str, Any],
        current_page: int,
    ) -> int | None:
        """Resolve the next page number from common API pagination shapes."""
        pagination = payload.get("pagination")

        if isinstance(pagination, Mapping):
            next_page = pagination.get("next_page")

            if next_page is None:
                return None

            try:
                value = int(next_page)
            except (TypeError, ValueError) as exc:
                raise APIClientError(
                    "API pagination.next_page must be an integer."
                ) from exc

            if value <= current_page:
                raise APIClientError(
                    "API returned a non-forward pagination cursor."
                )

            return value

        next_page = payload.get("next_page")

        if next_page is None:
            return None

        try:
            value = int(next_page)
        except (TypeError, ValueError) as exc:
            raise APIClientError(
                "API next_page must be an integer."
            ) from exc

        if value <= current_page:
            raise APIClientError(
                "API returned a non-forward pagination cursor."
            )

        return value

    def fetch_page(
        self,
        endpoint: str,
        *,
        page: int = 1,
        page_size: int | None = None,
        extra_params: Mapping[str, Any] | None = None,
    ) -> APIPage:
        """Fetch and normalize one paginated API response."""
        if page < 1:
            raise ValueError("page must be greater than or equal to 1.")

        resolved_page_size = (
            self.config.api_page_size
            if page_size is None
            else page_size
        )

        if resolved_page_size < 1:
            raise ValueError(
                "page_size must be greater than or equal to 1."
            )

        params: dict[str, Any] = {
            "page": page,
            "page_size": resolved_page_size,
        }

        if extra_params:
            params.update(extra_params)

        payload = self.request_json(
            endpoint,
            params=params,
        )

        return APIPage(
            items=self._extract_items(payload),
            next_page=self._extract_next_page(
                payload,
                page,
            ),
            raw=payload,
        )

    def iter_pages(
        self,
        endpoint: str,
        *,
        page_size: int | None = None,
        extra_params: Mapping[str, Any] | None = None,
    ) -> Iterator[APIPage]:
        """Yield API pages until the service reports there are no more pages."""
        page = 1

        for _ in range(self.config.api_max_pages):
            result = self.fetch_page(
                endpoint,
                page=page,
                page_size=page_size,
                extra_params=extra_params,
            )

            yield result

            if result.next_page is None:
                return

            page = result.next_page

        raise APIClientError(
            "API pagination exceeded the configured maximum page count."
        )

    def iter_records(
        self,
        endpoint: str,
        *,
        page_size: int | None = None,
        extra_params: Mapping[str, Any] | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Yield individual API records without accumulating all pages."""
        for page in self.iter_pages(
            endpoint,
            page_size=page_size,
            extra_params=extra_params,
        ):
            yield from page.items

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self.session.close()

    def __enter__(self) -> APIClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any,
    ) -> None:
        self.close()


__all__ = [
    "APIClient",
    "APIClientError",
    "APIHTTPError",
    "APIPage",
]

from __future__ import annotations

import logging
import random
import time
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urljoin

import requests
from requests import Response
from requests.adapters import HTTPAdapter

from .config import PipelineConfig, config


logger = logging.getLogger(__name__)


class APIClientError(RuntimeError):
    """Raised when an API request cannot be completed successfully."""


class APIHTTPError(APIClientError):
    """Raised when the API returns an unrecoverable HTTP error."""

    def __init__(
        self,
        status_code: int,
        message: str,
        *,
        response: Response | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response = response


@dataclass(frozen=True, slots=True)
class APIPage:
    """Represent one page returned by a paginated API."""

    items: list[dict[str, Any]]
    next_page: int | None
    raw: Mapping[str, Any]


class APIClient:
    """Production-oriented HTTP client for paginated JSON APIs."""

    _RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})

    def __init__(
        self,
        pipeline_config: PipelineConfig = config,
        *,
        session: requests.Session | None = None,
    ) -> None:
        self.config = pipeline_config
        self.session = session or requests.Session()

        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": (
                    "api-data-processing-pipeline/1.0"
                ),
            }
        )
        self.session.headers.update(
            self.config.authorization_headers
        )

        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=0,
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    @property
    def base_url(self) -> str:
        """Return the normalized API base URL."""
        value = self.config.api_base_url.strip()

        if not value:
            raise APIClientError("API base URL cannot be empty.")

        if not value.startswith(("http://", "https://")):
            raise APIClientError(
                "API base URL must use HTTP or HTTPS."
            )

        return value.rstrip("/") + "/"

    def build_url(self, endpoint: str) -> str:
        """Resolve an API endpoint against the configured base URL."""
        normalized_endpoint = endpoint.strip()

        if not normalized_endpoint:
            raise APIClientError(
                "API endpoint cannot be empty."
            )

        if normalized_endpoint.startswith(("http://", "https://")):
            return normalized_endpoint

        return urljoin(
            self.base_url,
            normalized_endpoint.lstrip("/"),
        )

    def _retry_delay(
        self,
        attempt: int,
        response: Response | None,
    ) -> float:
        """Calculate bounded exponential backoff with jitter."""
        if response is not None:
            retry_after = response.headers.get("Retry-After")

            if retry_after:
                try:
                    return max(
                        0.0,
                        min(
                            float(retry_after),
                            300.0,
                        ),
                    )
                except ValueError:
                    try:
                        retry_at = parsedate_to_datetime(
                            retry_after,
                        ).timestamp()
                    except (TypeError, ValueError, OverflowError):
                        retry_at = 0.0

                    if retry_at:
                        return max(
                            0.0,
                            min(
                                retry_at - time.time(),
                                300.0,
                            ),
                        )

        base_delay = self.config.api_backoff_factor * (
            2 ** max(attempt - 1, 0)
        )
        jitter = random.uniform(0.0, 0.25)

        return min(
            base_delay + jitter,
            300.0,
        )

    def _raise_for_status(
        self,
        response: Response,
    ) -> None:
        """Raise an API-specific exception for unsuccessful responses."""
        if response.ok:
            return

        message = (
            f"API request failed with HTTP "
            f"{response.status_code}: "
            f"{response.reason or 'unknown error'}"
        )

        if response.status_code == 401:
            message = "API authentication failed."
        elif response.status_code == 403:
            message = "API authorization failed."
        elif response.status_code == 404:
            message = "API endpoint was not found."
        elif response.status_code == 429:
            message = "API rate limit exceeded."

        raise APIHTTPError(
            response.status_code,
            message,
            response=response,
        )

    def request_json(
        self,
        endpoint: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a GET request and decode a JSON object response."""
        url = self.build_url(endpoint)

        for attempt in range(
            1,
            self.config.api_max_retries + 2,
        ):
            response: Response | None = None

            try:
                response = self.session.get(
                    url,
                    params=dict(params or {}),
                    timeout=self.config.request_timeout,
                )
            except requests.Timeout as exc:
                if attempt > self.config.api_max_retries:
                    raise APIClientError(
                        f"API request timed out after "
                        f"{attempt} attempt(s): {url}"
                    ) from exc

                delay = self._retry_delay(
                    attempt,
                    None,
                )
                logger.warning(
                    "API request timed out; retrying in %.2f seconds "
                    "(attempt %d/%d).",
                    delay,
                    attempt,
                    self.config.api_max_retries + 1,
                )
                time.sleep(delay)
                continue
            except requests.RequestException as exc:
                if attempt > self.config.api_max_retries:
                    raise APIClientError(
                        f"API request failed after "
                        f"{attempt} attempt(s): {url}"
                    ) from exc

                delay = self._retry_delay(
                    attempt,
                    None,
                )
                logger.warning(
                    "API request failed; retrying in %.2f seconds "
                    "(attempt %d/%d).",
                    delay,
                    attempt,
                    self.config.api_max_retries + 1,
                )
                time.sleep(delay)
                continue

            if (
                response.status_code
                in self._RETRYABLE_STATUS_CODES
                and attempt <= self.config.api_max_retries
            ):
                delay = self._retry_delay(
                    attempt,
                    response,
                )
                logger.warning(
                    "Received HTTP %d; retrying in %.2f seconds "
                    "(attempt %d/%d).",
                    response.status_code,
                    delay,
                    attempt,
                    self.config.api_max_retries + 1,
                )
                time.sleep(delay)
                continue

            self._raise_for_status(response)

            try:
                payload = response.json()
            except ValueError as exc:
                raise APIClientError(
                    f"API returned invalid JSON: {url}"
                ) from exc

            if not isinstance(payload, dict):
                raise APIClientError(
                    "API response must be a JSON object."
                )

            return payload

        raise APIClientError(
            f"API request failed unexpectedly: {url}"
        )

    def _extract_items(
        self,
        payload: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        """Extract and validate a list of records from an API payload."""
        raw_items = payload.get("data")

        if raw_items is None:
            raw_items = payload.get("items")

        if raw_items is None:
            raise APIClientError(
                "API response does not contain 'data' or 'items'."
            )

        if not isinstance(raw_items, list):
            raise APIClientError(
                "API response 'data' or 'items' field must be a list."
            )

        items: list[dict[str, Any]] = []

        for index, item in enumerate(raw_items):
            if not isinstance(item, dict):
                raise APIClientError(
                    "API record at index "
                    f"{index} is not a JSON object."
                )

            items.append(item)

        return items

    def _extract_next_page(
        self,
        payload: Mapping[str, Any],
        current_page: int,
    ) -> int | None:
        """Resolve the next page number from common API pagination shapes."""
        pagination = payload.get("pagination")

        if isinstance(pagination, Mapping):
            next_page = pagination.get("next_page")

            if next_page is None:
                return None

            try:
                value = int(next_page)
            except (TypeError, ValueError) as exc:
                raise APIClientError(
                    "API pagination.next_page must be an integer."
                ) from exc

            if value <= current_page:
                raise APIClientError(
                    "API returned a non-forward pagination cursor."
                )

            return value

        next_page = payload.get("next_page")

        if next_page is None:
            return None

        try:
            value = int(next_page)
        except (TypeError, ValueError) as exc:
            raise APIClientError(
                "API next_page must be an integer."
            ) from exc

        if value <= current_page:
            raise APIClientError(
                "API returned a non-forward pagination cursor."
            )

        return value

    def fetch_page(
        self,
        endpoint: str,
        *,
        page: int = 1,
        page_size: int | None = None,
        extra_params: Mapping[str, Any] | None = None,
    ) -> APIPage:
        """Fetch and normalize one paginated API response."""
        if page < 1:
            raise ValueError("page must be greater than or equal to 1.")

        resolved_page_size = (
            self.config.api_page_size
            if page_size is None
            else page_size
        )

        if resolved_page_size < 1:
            raise ValueError(
                "page_size must be greater than or equal to 1."
            )

        params: dict[str, Any] = {
            "page": page,
            "page_size": resolved_page_size,
        }

        if extra_params:
            params.update(extra_params)

        payload = self.request_json(
            endpoint,
            params=params,
        )

        return APIPage(
            items=self._extract_items(payload),
            next_page=self._extract_next_page(
                payload,
                page,
            ),
            raw=payload,
        )

    def iter_pages(
        self,
        endpoint: str,
        *,
        page_size: int | None = None,
        extra_params: Mapping[str, Any] | None = None,
    ) -> Iterator[APIPage]:
        """Yield API pages until the service reports there are no more pages."""
        page = 1

        for _ in range(self.config.api_max_pages):
            result = self.fetch_page(
                endpoint,
                page=page,
                page_size=page_size,
                extra_params=extra_params,
            )

            yield result

            if result.next_page is None:
                return

            page = result.next_page

        raise APIClientError(
            "API pagination exceeded the configured maximum page count."
        )

    def iter_records(
        self,
        endpoint: str,
        *,
        page_size: int | None = None,
        extra_params: Mapping[str, Any] | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Yield individual API records without accumulating all pages."""
        for page in self.iter_pages(
            endpoint,
            page_size=page_size,
            extra_params=extra_params,
        ):
            yield from page.items

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self.session.close()

    def __enter__(self) -> APIClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any,
    ) -> None:
        self.close()


__all__ = [
    "APIClient",
    "APIClientError",
    "APIHTTPError",
    "APIPage",
]