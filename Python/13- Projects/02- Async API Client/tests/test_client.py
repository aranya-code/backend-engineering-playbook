"""Tests for the asynchronous API client."""

from __future__ import annotations

import asyncio

import httpx
import pytest

from src.client import AsyncAPIClient
from src.config import ClientConfig
from src.exceptions import (
    APIClientError,
    APINetworkError,
    APIResponseError,
    APIRateLimitError,
    APIRetryExhaustedError,
    APITimeoutError,
)


def build_config(**overrides: object) -> ClientConfig:
    """Build a deterministic client configuration for tests."""
    values: dict[str, object] = {
        "base_url": "https://api.example.com",
        "timeout_seconds": 1.0,
        "max_retries": 2,
        "max_concurrency": 2,
        "rate_limit_per_second": 100.0,
    }
    values.update(overrides)
    return ClientConfig(**values)


@pytest.mark.asyncio
async def test_start_creates_reusable_http_client() -> None:
    """Starting the client should initialize its underlying HTTP client."""
    client = AsyncAPIClient(build_config())

    assert client._client is None

    await client.start()

    try:
        assert client._client is not None
        assert client._client.base_url == httpx.URL("https://api.example.com")
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_start_is_idempotent() -> None:
    """Calling start repeatedly should preserve the existing HTTP client."""
    client = AsyncAPIClient(build_config())

    await client.start()

    try:
        first_client = client._client

        await client.start()

        assert client._client is first_client
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_close_releases_http_client() -> None:
    """Closing the client should release the underlying HTTP resources."""
    client = AsyncAPIClient(build_config())
    await client.start()

    await client.close()

    assert client._client is None


@pytest.mark.asyncio
async def test_request_requires_started_client() -> None:
    """Requests should fail clearly when the client has not been started."""
    client = AsyncAPIClient(build_config())

    with pytest.raises(APIClientError, match="must be started"):
        await client.get("/users")


@pytest.mark.asyncio
async def test_get_returns_json_response() -> None:
    """Successful JSON responses should be decoded into Python objects."""
    config = build_config()
    client = AsyncAPIClient(config)

    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={"users": [{"id": 1, "name": "Alice"}]},
        )
    )

    await client.start()
    assert client._client is not None
    await client._client.aclose()
    client._client = httpx.AsyncClient(
        base_url=config.base_url,
        transport=transport,
    )

    try:
        response = await client.get("/users")

        assert response == {"users": [{"id": 1, "name": "Alice"}]}
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_get_normalizes_relative_path() -> None:
    """Requests without a leading slash should still target the expected path."""
    config = build_config()
    client = AsyncAPIClient(config)
    requested_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_paths.append(request.url.path)
        return httpx.Response(200, json={"status": "ok"})

    await client.start()
    assert client._client is not None
    await client._client.aclose()
    client._client = httpx.AsyncClient(
        base_url=config.base_url,
        transport=httpx.MockTransport(handler),
    )

    try:
        response = await client.get("health")

        assert response == {"status": "ok"}
        assert requested_paths == ["/health"]
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_request_returns_none_for_no_content() -> None:
    """A successful 204 response should produce None."""
    client = AsyncAPIClient(build_config())

    transport = httpx.MockTransport(lambda _: httpx.Response(204))

    await client.start()
    assert client._client is not None
    await client._client.aclose()
    client._client = httpx.AsyncClient(
        base_url=client._config.base_url,
        transport=transport,
    )

    try:
        assert await client.get("/users/1") is None
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_non_retryable_error_raises_response_error() -> None:
    """Non-transient HTTP failures should not be retried."""
    client = AsyncAPIClient(build_config(max_retries=3))
    request_count = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(400, json={"error": "invalid request"})

    await client.start()
    assert client._client is not None
    await client._client.aclose()
    client._client = httpx.AsyncClient(
        base_url=client._config.base_url,
        transport=httpx.MockTransport(handler),
    )

    try:
        with pytest.raises(APIResponseError) as exc_info:
            await client.get("/users")

        assert exc_info.value.status_code == 400
        assert request_count == 1
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_retryable_server_error_is_retried() -> None:
    """Transient server failures should be retried up to the configured limit."""
    client = AsyncAPIClient(build_config(max_retries=2))
    request_count = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1

        if request_count < 3:
            return httpx.Response(503, json={"error": "temporarily unavailable"})

        return httpx.Response(200, json={"status": "ok"})

    await client.start()
    assert client._client is not None
    await client._client.aclose()
    client._client = httpx.AsyncClient(
        base_url=client._config.base_url,
        transport=httpx.MockTransport(handler),
    )

    try:
        response = await client.get("/health")

        assert response == {"status": "ok"}
        assert request_count == 3
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_retry_exhaustion_raises_last_response_error() -> None:
    """Exhausted retries should surface the final HTTP failure."""
    client = AsyncAPIClient(build_config(max_retries=2))
    request_count = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(503, json={"error": "unavailable"})

    await client.start()
    assert client._client is not None
    await client._client.aclose()
    client._client = httpx.AsyncClient(
        base_url=client._config.base_url,
        transport=httpx.MockTransport(handler),
    )

    try:
        with pytest.raises(APIResponseError) as exc_info:
            await client.get("/health")

        assert exc_info.value.status_code == 503
        assert request_count == 3
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_timeout_is_retried_then_raises_client_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Network timeouts should be retried and eventually surfaced."""
    client = AsyncAPIClient(build_config(max_retries=2))
    request_count = 0

    async def failing_request(*args: object, **kwargs: object) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        raise httpx.ReadTimeout("request timed out")

    await client.start()
    assert client._client is not None
    monkeypatch.setattr(client._client, "request", failing_request)

    async def no_wait(_: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", no_wait)

    try:
        with pytest.raises(APIClientError, match="after 3 attempts"):
            await client.get("/slow")

        assert request_count == 3
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_context_manager_starts_and_closes_client() -> None:
    """The async context manager should manage client lifecycle."""
    client = AsyncAPIClient(build_config())

    async with client as active_client:
        assert active_client is client
        assert client._client is not None

    assert client._client is None

"""Tests for the asynchronous API client."""

from __future__ import annotations

import asyncio

import httpx
import pytest

from src.client import AsyncAPIClient
from src.config import ClientConfig
from src.exceptions import (
    APIClientError,
    APINetworkError,
    APIResponseError,
    APIRateLimitError,
    APIRetryExhaustedError,
    APITimeoutError,
)


def build_config(**overrides: object) -> ClientConfig:
    """Build a deterministic client configuration for tests."""
    values: dict[str, object] = {
        "base_url": "https://api.example.com",
        "timeout_seconds": 1.0,
        "max_retries": 2,
        "max_concurrency": 2,
        "rate_limit_per_second": 100.0,
    }
    values.update(overrides)
    return ClientConfig(**values)


@pytest.mark.asyncio
async def test_start_creates_reusable_http_client() -> None:
    """Starting the client should initialize its underlying HTTP client."""
    client = AsyncAPIClient(build_config())

    assert client._client is None

    await client.start()

    try:
        assert client._client is not None
        assert client._client.base_url == httpx.URL("https://api.example.com")
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_start_is_idempotent() -> None:
    """Calling start repeatedly should preserve the existing HTTP client."""
    client = AsyncAPIClient(build_config())

    await client.start()

    try:
        first_client = client._client

        await client.start()

        assert client._client is first_client
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_close_releases_http_client() -> None:
    """Closing the client should release the underlying HTTP resources."""
    client = AsyncAPIClient(build_config())
    await client.start()

    await client.close()

    assert client._client is None


@pytest.mark.asyncio
async def test_request_requires_started_client() -> None:
    """Requests should fail clearly when the client has not been started."""
    client = AsyncAPIClient(build_config())

    with pytest.raises(APIClientError, match="must be started"):
        await client.get("/users")


@pytest.mark.asyncio
async def test_get_returns_json_response() -> None:
    """Successful JSON responses should be decoded into Python objects."""
    config = build_config()
    client = AsyncAPIClient(config)

    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={"users": [{"id": 1, "name": "Alice"}]},
        )
    )

    await client.start()
    assert client._client is not None
    await client._client.aclose()
    client._client = httpx.AsyncClient(
        base_url=config.base_url,
        transport=transport,
    )

    try:
        response = await client.get("/users")

        assert response == {"users": [{"id": 1, "name": "Alice"}]}
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_get_normalizes_relative_path() -> None:
    """Requests without a leading slash should still target the expected path."""
    config = build_config()
    client = AsyncAPIClient(config)
    requested_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_paths.append(request.url.path)
        return httpx.Response(200, json={"status": "ok"})

    await client.start()
    assert client._client is not None
    await client._client.aclose()
    client._client = httpx.AsyncClient(
        base_url=config.base_url,
        transport=httpx.MockTransport(handler),
    )

    try:
        response = await client.get("health")

        assert response == {"status": "ok"}
        assert requested_paths == ["/health"]
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_request_returns_none_for_no_content() -> None:
    """A successful 204 response should produce None."""
    client = AsyncAPIClient(build_config())

    transport = httpx.MockTransport(lambda _: httpx.Response(204))

    await client.start()
    assert client._client is not None
    await client._client.aclose()
    client._client = httpx.AsyncClient(
        base_url=client._config.base_url,
        transport=transport,
    )

    try:
        assert await client.get("/users/1") is None
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_non_retryable_error_raises_response_error() -> None:
    """Non-transient HTTP failures should not be retried."""
    client = AsyncAPIClient(build_config(max_retries=3))
    request_count = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(400, json={"error": "invalid request"})

    await client.start()
    assert client._client is not None
    await client._client.aclose()
    client._client = httpx.AsyncClient(
        base_url=client._config.base_url,
        transport=httpx.MockTransport(handler),
    )

    try:
        with pytest.raises(APIResponseError) as exc_info:
            await client.get("/users")

        assert exc_info.value.status_code == 400
        assert request_count == 1
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_retryable_server_error_is_retried() -> None:
    """Transient server failures should be retried up to the configured limit."""
    client = AsyncAPIClient(build_config(max_retries=2))
    request_count = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1

        if request_count < 3:
            return httpx.Response(503, json={"error": "temporarily unavailable"})

        return httpx.Response(200, json={"status": "ok"})

    await client.start()
    assert client._client is not None
    await client._client.aclose()
    client._client = httpx.AsyncClient(
        base_url=client._config.base_url,
        transport=httpx.MockTransport(handler),
    )

    try:
        response = await client.get("/health")

        assert response == {"status": "ok"}
        assert request_count == 3
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_retry_exhaustion_raises_last_response_error() -> None:
    """Exhausted retries should surface the final HTTP failure."""
    client = AsyncAPIClient(build_config(max_retries=2))
    request_count = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(503, json={"error": "unavailable"})

    await client.start()
    assert client._client is not None
    await client._client.aclose()
    client._client = httpx.AsyncClient(
        base_url=client._config.base_url,
        transport=httpx.MockTransport(handler),
    )

    try:
        with pytest.raises(APIResponseError) as exc_info:
            await client.get("/health")

        assert exc_info.value.status_code == 503
        assert request_count == 3
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_timeout_is_retried_then_raises_client_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Network timeouts should be retried and eventually surfaced."""
    client = AsyncAPIClient(build_config(max_retries=2))
    request_count = 0

    async def failing_request(*args: object, **kwargs: object) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        raise httpx.ReadTimeout("request timed out")

    await client.start()
    assert client._client is not None
    monkeypatch.setattr(client._client, "request", failing_request)

    async def no_wait(_: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", no_wait)

    try:
        with pytest.raises(APIClientError, match="after 3 attempts"):
            await client.get("/slow")

        assert request_count == 3
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_context_manager_starts_and_closes_client() -> None:
    """The async context manager should manage client lifecycle."""
    client = AsyncAPIClient(build_config())

    async with client as active_client:
        assert active_client is client
        assert client._client is not None

    assert client._client is None