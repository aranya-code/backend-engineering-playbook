"""Asynchronous HTTP client with bounded concurrency and reliable request handling."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from types import TracebackType
from typing import Any, Self

import httpx

from src.config import ClientConfig
from src.exceptions import APIClientError, APIResponseError


class AsyncAPIClient:
    """Provide an asynchronous client for an external HTTP API."""

    def __init__(self, config: ClientConfig) -> None:
        self._config = config
        self._client: httpx.AsyncClient | None = None
        self._semaphore = asyncio.Semaphore(config.max_concurrency)

    async def __aenter__(self) -> Self:
        """Open the underlying HTTP client."""
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the underlying HTTP client."""
        await self.close()

    async def start(self) -> None:
        """Initialize the reusable HTTP connection pool."""
        if self._client is not None:
            return

        headers = {
            "Accept": "application/json",
            "User-Agent": "async-api-client/0.1.0",
        }

        if self._config.api_key:
            headers["Authorization"] = f"Bearer {self._config.api_key}"

        timeout = httpx.Timeout(self._config.timeout_seconds)

        self._client = httpx.AsyncClient(
            base_url=self._config.base_url,
            headers=headers,
            timeout=timeout,
            follow_redirects=True,
        )

    async def close(self) -> None:
        """Close the HTTP client and release pooled connections."""
        if self._client is None:
            return

        await self._client.aclose()
        self._client = None

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        """Send an HTTP request with bounded concurrency and retry handling."""
        if self._client is None:
            raise APIClientError(
                "AsyncAPIClient must be started before making requests."
            )

        if not path.startswith("/"):
            path = f"/{path}"

        async with self._semaphore:
            return await self._request_with_retries(
                method,
                path,
                params=params,
                json=json,
                headers=headers,
            )

    async def get(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        """Send an asynchronous GET request."""
        return await self.request("GET", path, params=params)

    async def post(
        self,
        path: str,
        *,
        json: Any = None,
    ) -> Any:
        """Send an asynchronous POST request."""
        return await self.request("POST", path, json=json)

    async def _request_with_retries(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None,
        json: Any,
        headers: Mapping[str, str] | None,
    ) -> Any:
        """Execute a request and retry only transient failures."""
        assert self._client is not None

        attempts = self._config.max_retries + 1

        for attempt in range(attempts):
            try:
                response = await self._client.request(
                    method,
                    path,
                    params=params,
                    json=json,
                    headers=headers,
                )

                if response.status_code < 400:
                    return self._decode_response(response)

                if not self._is_retryable_status(response.status_code):
                    self._raise_response_error(response)

                if attempt == attempts - 1:
                    self._raise_response_error(response)

            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                if attempt == attempts - 1:
                    raise APIClientError(
                        f"Request failed after {attempts} attempts: {exc}"
                    ) from exc

            delay = min(2**attempt, 30)
            await asyncio.sleep(delay)

        raise APIClientError("Request failed without a response.")

    @staticmethod
    def _is_retryable_status(status_code: int) -> bool:
        """Return whether an HTTP status normally represents a transient failure."""
        return status_code == 408 or status_code == 429 or 500 <= status_code < 600

    @staticmethod
    def _decode_response(response: httpx.Response) -> Any:
        """Decode a successful JSON response or return an empty result."""
        if response.status_code == 204 or not response.content:
            return None

        content_type = response.headers.get("content-type", "").lower()

        if "application/json" in content_type:
            try:
                return response.json()
            except ValueError as exc:
                raise APIResponseError(
                    "The API returned invalid JSON."
                ) from exc

        return response.text

    @staticmethod
    def _raise_response_error(response: httpx.Response) -> None:
        """Raise a structured exception for an unsuccessful response."""
        try:
            detail = response.json()
        except ValueError:
            detail = response.text

        raise APIResponseError(
            f"API request failed with HTTP {response.status_code}: {detail}"
        )

"""Asynchronous HTTP client with bounded concurrency and reliable request handling."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from types import TracebackType
from typing import Any, Self

import httpx

from src.config import ClientConfig
from src.exceptions import APIClientError, APIResponseError


class AsyncAPIClient:
    """Provide an asynchronous client for an external HTTP API."""

    def __init__(self, config: ClientConfig) -> None:
        self._config = config
        self._client: httpx.AsyncClient | None = None
        self._semaphore = asyncio.Semaphore(config.max_concurrency)

    async def __aenter__(self) -> Self:
        """Open the underlying HTTP client."""
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the underlying HTTP client."""
        await self.close()

    async def start(self) -> None:
        """Initialize the reusable HTTP connection pool."""
        if self._client is not None:
            return

        headers = {
            "Accept": "application/json",
            "User-Agent": "async-api-client/0.1.0",
        }

        if self._config.api_key:
            headers["Authorization"] = f"Bearer {self._config.api_key}"

        timeout = httpx.Timeout(self._config.timeout_seconds)

        self._client = httpx.AsyncClient(
            base_url=self._config.base_url,
            headers=headers,
            timeout=timeout,
            follow_redirects=True,
        )

    async def close(self) -> None:
        """Close the HTTP client and release pooled connections."""
        if self._client is None:
            return

        await self._client.aclose()
        self._client = None

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        """Send an HTTP request with bounded concurrency and retry handling."""
        if self._client is None:
            raise APIClientError(
                "AsyncAPIClient must be started before making requests."
            )

        if not path.startswith("/"):
            path = f"/{path}"

        async with self._semaphore:
            return await self._request_with_retries(
                method,
                path,
                params=params,
                json=json,
                headers=headers,
            )

    async def get(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        """Send an asynchronous GET request."""
        return await self.request("GET", path, params=params)

    async def post(
        self,
        path: str,
        *,
        json: Any = None,
    ) -> Any:
        """Send an asynchronous POST request."""
        return await self.request("POST", path, json=json)

    async def _request_with_retries(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None,
        json: Any,
        headers: Mapping[str, str] | None,
    ) -> Any:
        """Execute a request and retry only transient failures."""
        assert self._client is not None

        attempts = self._config.max_retries + 1

        for attempt in range(attempts):
            try:
                response = await self._client.request(
                    method,
                    path,
                    params=params,
                    json=json,
                    headers=headers,
                )

                if response.status_code < 400:
                    return self._decode_response(response)

                if not self._is_retryable_status(response.status_code):
                    self._raise_response_error(response)

                if attempt == attempts - 1:
                    self._raise_response_error(response)

            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                if attempt == attempts - 1:
                    raise APIClientError(
                        f"Request failed after {attempts} attempts: {exc}"
                    ) from exc

            delay = min(2**attempt, 30)
            await asyncio.sleep(delay)

        raise APIClientError("Request failed without a response.")

    @staticmethod
    def _is_retryable_status(status_code: int) -> bool:
        """Return whether an HTTP status normally represents a transient failure."""
        return status_code == 408 or status_code == 429 or 500 <= status_code < 600

    @staticmethod
    def _decode_response(response: httpx.Response) -> Any:
        """Decode a successful JSON response or return an empty result."""
        if response.status_code == 204 or not response.content:
            return None

        content_type = response.headers.get("content-type", "").lower()

        if "application/json" in content_type:
            try:
                return response.json()
            except ValueError as exc:
                raise APIResponseError(
                    "The API returned invalid JSON."
                ) from exc

        return response.text

    @staticmethod
    def _raise_response_error(response: httpx.Response) -> None:
        """Raise a structured exception for an unsuccessful response."""
        try:
            detail = response.json()
        except ValueError:
            detail = response.text

        raise APIResponseError(
            f"API request failed with HTTP {response.status_code}: {detail}"
        )