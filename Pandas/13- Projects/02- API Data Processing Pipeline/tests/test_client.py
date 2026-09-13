from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests

from src.client import (
    APIClient,
    APIClientError,
    APIHTTPError,
    APIPage,
)
from src.config import PipelineConfig


def make_config(
    tmp_path: Path,
    **overrides,
) -> PipelineConfig:
    """Create an isolated API pipeline configuration for tests."""
    values = {
        "raw_data_dir": tmp_path / "raw",
        "staging_data_dir": tmp_path / "staging",
        "processed_data_dir": tmp_path / "processed",
        "reports_dir": tmp_path / "reports",
        "api_base_url": "https://api.example.com",
        "api_timeout_seconds": 30.0,
        "api_connect_timeout_seconds": 10.0,
        "api_read_timeout_seconds": 30.0,
        "api_max_retries": 3,
        "api_backoff_factor": 0.0,
        "api_page_size": 2,
        "api_max_pages": 10,
        "api_response_timezone": "UTC",
        "log_level": "CRITICAL",
    }
    values.update(overrides)
    return PipelineConfig(**values)


def make_response(
    *,
    status_code: int = 200,
    payload: object | None = None,
    headers: Mapping[str, str] | None = None,
    reason: str = "OK",
) -> MagicMock:
    """Build a mock requests response."""
    response = MagicMock()
    response.status_code = status_code
    response.reason = reason
    response.headers = dict(headers or {})
    response.ok = status_code < 400
    response.json.return_value = payload

    return response


def make_client(
    tmp_path: Path,
    *,
    session: MagicMock | None = None,
    **overrides,
) -> APIClient:
    """Create an API client with deterministic test configuration."""
    pipeline_config = make_config(
        tmp_path,
        **overrides,
    )
    return APIClient(
        pipeline_config,
        session=session,
    )


def test_client_configures_session_headers(
    tmp_path: Path,
) -> None:
    session = MagicMock()

    client = make_client(
        tmp_path,
        session=session,
        api_token="secret-token",
    )

    headers = session.headers.update.call_args.args[0]

    assert headers["Accept"] == "application/json"
    assert headers["Authorization"] == "Bearer secret-token"
    assert headers["User-Agent"] == (
        "api-data-processing-pipeline/1.0"
    )

    client.close()


def test_client_configures_default_headers_without_token(
    tmp_path: Path,
) -> None:
    session = MagicMock()

    client = make_client(
        tmp_path,
        session=session,
        api_token=None,
    )

    headers = session.headers.update.call_args.args[0]

    assert headers["Accept"] == "application/json"
    assert "Authorization" not in headers
    assert headers["User-Agent"] == (
        "api-data-processing-pipeline/1.0"
    )

    client.close()


def test_base_url_is_normalized(
    tmp_path: Path,
) -> None:
    client = make_client(
        tmp_path,
        api_base_url="https://api.example.com///",
    )

    assert client.base_url == "https://api.example.com/"

    client.close()


def test_base_url_rejects_empty_value(
    tmp_path: Path,
) -> None:
    client = make_client(
        tmp_path,
        api_base_url="   ",
    )

    with pytest.raises(
        APIClientError,
        match="cannot be empty",
    ):
        _ = client.base_url

    client.close()


@pytest.mark.parametrize(
    "base_url",
    [
        "api.example.com",
        "ftp://api.example.com",
        "example",
    ],
)
def test_base_url_requires_http_or_https(
    tmp_path: Path,
    base_url: str,
) -> None:
    client = make_client(
        tmp_path,
        api_base_url=base_url,
    )

    with pytest.raises(
        APIClientError,
        match="HTTP or HTTPS",
    ):
        _ = client.base_url

    client.close()


def test_build_url_resolves_relative_endpoint(
    tmp_path: Path,
) -> None:
    client = make_client(
        tmp_path,
        api_base_url="https://api.example.com/v1/",
    )

    assert client.build_url("/orders") == (
        "https://api.example.com/v1/orders"
    )

    client.close()


def test_build_url_preserves_absolute_url(
    tmp_path: Path,
) -> None:
    client = make_client(
        tmp_path,
    )

    url = "https://other.example.com/data"

    assert client.build_url(url) == url

    client.close()


def test_build_url_rejects_empty_endpoint(
    tmp_path: Path,
) -> None:
    client = make_client(
        tmp_path,
    )

    with pytest.raises(
        APIClientError,
        match="endpoint cannot be empty",
    ):
        client.build_url("   ")

    client.close()


def test_request_json_returns_dictionary_payload(
    tmp_path: Path,
) -> None:
    session = MagicMock()
    response = make_response(
        payload={
            "data": [
                {"id": 1},
                {"id": 2},
            ]
        }
    )
    session.get.return_value = response

    client = make_client(
        tmp_path,
        session=session,
    )

    result = client.request_json(
        "/orders",
        params={"page": 1},
    )

    assert result == {
        "data": [
            {"id": 1},
            {"id": 2},
        ]
    }
    session.get.assert_called_once_with(
        "https://api.example.com/orders",
        params={"page": 1},
        timeout=(10.0, 30.0),
    )

    client.close()


def test_request_json_rejects_non_object_json_payload(
    tmp_path: Path,
) -> None:
    session = MagicMock()
    response = make_response(
        payload=[
            {"id": 1},
        ]
    )
    session.get.return_value = response

    client = make_client(
        tmp_path,
        session=session,
    )

    with pytest.raises(
        APIClientError,
        match="must be a JSON object",
    ):
        client.request_json(
            "/orders",
        )

    client.close()


def test_request_json_rejects_invalid_json(
    tmp_path: Path,
) -> None:
    session = MagicMock()
    response = make_response()

    response.json.side_effect = ValueError("invalid json")
    session.get.return_value = response

    client = make_client(
        tmp_path,
        session=session,
    )

    with pytest.raises(
        APIClientError,
        match="invalid JSON",
    ):
        client.request_json(
            "/orders",
        )

    client.close()


@pytest.mark.parametrize(
    ("status_code", "message"),
    [
        (400, "HTTP 400"),
        (401, "authentication failed"),
        (403, "authorization failed"),
        (404, "endpoint was not found"),
    ],
)
def test_request_json_raises_api_http_error_for_non_retryable_status(
    tmp_path: Path,
    status_code: int,
    message: str,
) -> None:
    session = MagicMock()
    response = make_response(
        status_code=status_code,
        payload={"error": "failure"},
        reason="Error",
    )
    session.get.return_value = response

    client = make_client(
        tmp_path,
        session=session,
        api_max_retries=2,
    )

    with pytest.raises(
        APIHTTPError,
        match=message,
    ) as exc_info:
        client.request_json(
            "/orders",
        )

    assert exc_info.value.status_code == status_code
    assert exc_info.value.response is response
    session.get.assert_called_once()

    client.close()


@pytest.mark.parametrize(
    "status_code",
    [429, 500, 502, 503, 504],
)
def test_request_json_retries_retryable_http_status(
    tmp_path: Path,
    status_code: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = MagicMock()
    session.get.side_effect = [
        make_response(
            status_code=status_code,
            headers={"Retry-After": "0"},
        ),
        make_response(
            payload={
                "data": [
                    {"id": 1},
                ]
            }
        ),
    ]

    sleep = MagicMock()
    monkeypatch.setattr(
        "src.client.time.sleep",
        sleep,
    )

    client = make_client(
        tmp_path,
        session=session,
        api_max_retries=1,
    )

    result = client.request_json(
        "/orders",
    )

    assert result == {
        "data": [
            {"id": 1},
        ]
    }
    assert session.get.call_count == 2
    sleep.assert_called_once_with(0.0)

    client.close()


def test_request_json_stops_after_max_retries_for_retryable_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = MagicMock()
    session.get.return_value = make_response(
        status_code=503,
        headers={"Retry-After": "0"},
    )

    sleep = MagicMock()
    monkeypatch.setattr(
        "src.client.time.sleep",
        sleep,
    )

    client = make_client(
        tmp_path,
        session=session,
        api_max_retries=2,
    )

    with pytest.raises(
        APIHTTPError,
        match="503",
    ):
        client.request_json(
            "/orders",
        )

    assert session.get.call_count == 3
    assert sleep.call_count == 2

    client.close()


def test_request_json_uses_retry_after_header(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = MagicMock()
    session.get.side_effect = [
        make_response(
            status_code=429,
            headers={"Retry-After": "2"},
        ),
        make_response(
            payload={
                "data": [],
            }
        ),
    ]

    sleep = MagicMock()
    monkeypatch.setattr(
        "src.client.time.sleep",
        sleep,
    )

    client = make_client(
        tmp_path,
        session=session,
        api_max_retries=1,
    )

    client.request_json(
        "/orders",
    )

    sleep.assert_called_once_with(2.0)

    client.close()


def test_request_json_retries_timeout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = MagicMock()
    session.get.side_effect = [
        requests.Timeout("timed out"),
        make_response(
            payload={
                "data": [
                    {"id": 1},
                ]
            }
        ),
    ]

    sleep = MagicMock()
    monkeypatch.setattr(
        "src.client.time.sleep",
        sleep,
    )

    client = make_client(
        tmp_path,
        session=session,
        api_max_retries=1,
        api_backoff_factor=0.0,
    )

    result = client.request_json(
        "/orders",
    )

    assert result == {
        "data": [
            {"id": 1},
        ]
    }
    assert session.get.call_count == 2
    sleep.assert_called_once()

    client.close()


def test_request_json_raises_after_timeout_retries_exhausted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = MagicMock()
    session.get.side_effect = requests.Timeout(
        "timed out",
    )

    sleep = MagicMock()
    monkeypatch.setattr(
        "src.client.time.sleep",
        sleep,
    )

    client = make_client(
        tmp_path,
        session=session,
        api_max_retries=2,
    )

    with pytest.raises(
        APIClientError,
        match="timed out",
    ):
        client.request_json(
            "/orders",
        )

    assert session.get.call_count == 3
    assert sleep.call_count == 2

    client.close()


def test_request_json_retries_request_exception(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = MagicMock()
    session.get.side_effect = [
        requests.ConnectionError("connection reset"),
        make_response(
            payload={
                "data": [
                    {"id": 1},
                ]
            }
        ),
    ]

    sleep = MagicMock()
    monkeypatch.setattr(
        "src.client.time.sleep",
        sleep,
    )

    client = make_client(
        tmp_path,
        session=session,
        api_max_retries=1,
    )

    result = client.request_json(
        "/orders",
    )

    assert result["data"] == [{"id": 1}]
    assert session.get.call_count == 2
    assert sleep.call_count == 1

    client.close()


def test_request_json_raises_after_request_exceptions_exhausted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = MagicMock()
    session.get.side_effect = requests.ConnectionError(
        "connection reset",
    )

    monkeypatch.setattr(
        "src.client.time.sleep",
        MagicMock(),
    )

    client = make_client(
        tmp_path,
        session=session,
        api_max_retries=1,
    )

    with pytest.raises(
        APIClientError,
        match="request failed",
    ):
        client.request_json(
            "/orders",
        )

    assert session.get.call_count == 2

    client.close()


def test_extract_items_accepts_data_key(
    tmp_path: Path,
) -> None:
    client = make_client(tmp_path)

    payload = {
        "data": [
            {"id": 1},
            {"id": 2},
        ]
    }

    assert client._extract_items(payload) == [
        {"id": 1},
        {"id": 2},
    ]

    client.close()


def test_extract_items_accepts_items_key(
    tmp_path: Path,
) -> None:
    client = make_client(tmp_path)

    payload = {
        "items": [
            {"id": 1},
        ]
    }

    assert client._extract_items(payload) == [
        {"id": 1},
    ]

    client.close()


def test_extract_items_rejects_missing_items(
    tmp_path: Path,
) -> None:
    client = make_client(tmp_path)

    with pytest.raises(
        APIClientError,
        match="does not contain",
    ):
        client._extract_items({})

    client.close()


def test_extract_items_rejects_non_list_items(
    tmp_path: Path,
) -> None:
    client = make_client(tmp_path)

    with pytest.raises(
        APIClientError,
        match="must be a list",
    ):
        client._extract_items(
            {
                "data": {
                    "id": 1,
                }
            }
        )

    client.close()


def test_extract_items_rejects_non_dictionary_record(
    tmp_path: Path,
) -> None:
    client = make_client(tmp_path)

    with pytest.raises(
        APIClientError,
        match="index 1",
    ):
        client._extract_items(
            {
                "data": [
                    {"id": 1},
                    "invalid",
                ]
            }
        )

    client.close()


def test_extract_next_page_reads_nested_pagination(
    tmp_path: Path,
) -> None:
    client = make_client(tmp_path)

    result = client._extract_next_page(
        {
            "pagination": {
                "next_page": 3,
            }
        },
        2,
    )

    assert result == 3

    client.close()


def test_extract_next_page_reads_top_level_value(
    tmp_path: Path,
) -> None:
    client = make_client(tmp_path)

    result = client._extract_next_page(
        {
            "next_page": 3,
        },
        2,
    )

    assert result == 3

    client.close()


def test_extract_next_page_returns_none_when_absent(
    tmp_path: Path,
) -> None:
    client = make_client(tmp_path)

    assert (
        client._extract_next_page(
            {},
            1,
        )
        is None
    )

    client.close()


def test_extract_next_page_rejects_non_forward_page(
    tmp_path: Path,
) -> None:
    client = make_client(tmp_path)

    with pytest.raises(
        APIClientError,
        match="non-forward",
    ):
        client._extract_next_page(
            {"next_page": 1},
            1,
        )

    client.close()


def test_fetch_page_returns_api_page(
    tmp_path: Path,
) -> None:
    session = MagicMock()
    session.get.return_value = make_response(
        payload={
            "data": [
                {"id": 1},
                {"id": 2},
            ],
            "pagination": {
                "next_page": 2,
            },
        }
    )

    client = make_client(
        tmp_path,
        session=session,
        api_page_size=50,
    )

    result = client.fetch_page(
        "/orders",
        page=1,
        extra_params={
            "status": "completed",
        },
    )

    assert isinstance(result, APIPage)
    assert result.items == [
        {"id": 1},
        {"id": 2},
    ]
    assert result.next_page == 2
    assert result.raw["data"] == [
        {"id": 1},
        {"id": 2},
    ]

    session.get.assert_called_once_with(
        "https://api.example.com/orders",
        params={
            "page": 1,
            "page_size": 50,
            "status": "completed",
        },
        timeout=(10.0, 30.0),
    )

    client.close()


@pytest.mark.parametrize(
    "page",
    [0, -1],
)
def test_fetch_page_rejects_invalid_page(
    tmp_path: Path,
    page: int,
) -> None:
    client = make_client(tmp_path)

    with pytest.raises(
        ValueError,
        match="greater than or equal to 1",
    ):
        client.fetch_page(
            "/orders",
            page=page,
        )

    client.close()


def test_fetch_page_rejects_invalid_page_size(
    tmp_path: Path,
) -> None:
    client = make_client(tmp_path)

    with pytest.raises(
        ValueError,
        match="page_size",
    ):
        client.fetch_page(
            "/orders",
            page_size=0,
        )

    client.close()


def test_iter_pages_follows_pagination(
    tmp_path: Path,
) -> None:
    session = MagicMock()
    session.get.side_effect = [
        make_response(
            payload={
                "data": [
                    {"id": 1},
                ],
                "pagination": {
                    "next_page": 2,
                },
            }
        ),
        make_response(
            payload={
                "data": [
                    {"id": 2},
                ],
                "pagination": {
                    "next_page": 3,
                },
            }
        ),
        make_response(
            payload={
                "data": [
                    {"id": 3},
                ],
            }
        ),
    ]

    client = make_client(
        tmp_path,
        session=session,
    )

    pages = list(
        client.iter_pages(
            "/orders",
        )
    )

    assert [page.items for page in pages] == [
        [{"id": 1}],
        [{"id": 2}],
        [{"id": 3}],
    ]

    assert [page.next_page for page in pages] == [
        2,
        3,
        None,
    ]

    assert session.get.call_count == 3

    client.close()


def test_iter_pages_stops_at_configured_page_limit(
    tmp_path: Path,
) -> None:
    session = MagicMock()
    session.get.return_value = make_response(
        payload={
            "data": [
                {"id": 1},
            ],
            "pagination": {
                "next_page": 2,
            },
        }
    )

    client = make_client(
        tmp_path,
        session=session,
        api_max_pages=2,
    )

    with pytest.raises(
        APIClientError,
        match="maximum page count",
    ):
        list(
            client.iter_pages(
                "/orders",
            )
        )

    assert session.get.call_count == 2

    client.close()


def test_iter_records_flattens_pages(
    tmp_path: Path,
) -> None:
    session = MagicMock()
    session.get.side_effect = [
        make_response(
            payload={
                "data": [
                    {"id": 1},
                    {"id": 2},
                ],
                "next_page": 2,
            }
        ),
        make_response(
            payload={
                "data": [
                    {"id": 3},
                ],
            }
        ),
    ]

    client = make_client(
        tmp_path,
        session=session,
    )

    records = list(
        client.iter_records(
            "/orders",
        )
    )

    assert records == [
        {"id": 1},
        {"id": 2},
        {"id": 3},
    ]

    client.close()


def test_retry_delay_prefers_retry_after_header(
    tmp_path: Path,
) -> None:
    client = make_client(tmp_path)

    response = make_response(
        status_code=429,
        headers={
            "Retry-After": "5",
        },
    )

    assert client._retry_delay(
        1,
        response,
    ) == 5.0

    client.close()


def test_retry_delay_uses_exponential_backoff_when_retry_after_is_invalid(
    tmp_path: Path,
) -> None:
    client = make_client(
        tmp_path,
        api_backoff_factor=2.0,
    )

    response = make_response(
        status_code=503,
        headers={
            "Retry-After": "not-a-delay",
        },
    )

    delay = client._retry_delay(
        3,
        response,
    )

    assert 8.0 <= delay <= 8.25

    client.close()


def test_context_manager_closes_session(
    tmp_path: Path,
) -> None:
    session = MagicMock()

    with APIClient(
        make_config(tmp_path),
        session=session,
    ) as client:
        assert client is not None

    session.close.assert_called_once()


def test_close_closes_underlying_session(
    tmp_path: Path,
) -> None:
    session = MagicMock()

    client = make_client(
        tmp_path,
        session=session,
    )

    client.close()

    session.close.assert_called_once()


def test_request_timeout_uses_connect_and_read_configuration(
    tmp_path: Path,
) -> None:
    session = MagicMock()
    session.get.return_value = make_response(
        payload={
            "data": [],
        }
    )

    client = make_client(
        tmp_path,
        session=session,
        api_connect_timeout_seconds=3.5,
        api_read_timeout_seconds=17.5,
    )

    client.request_json(
        "/orders",
    )

    session.get.assert_called_once_with(
        "https://api.example.com/orders",
        params={},
        timeout=(3.5, 17.5),
    )

    client.close()


def test_request_json_retries_are_bounded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = MagicMock()
    session.get.return_value = make_response(
        status_code=500,
        headers={"Retry-After": "0"},
    )

    sleep = MagicMock()
    monkeypatch.setattr(
        "src.client.time.sleep",
        sleep,
    )

    client = make_client(
        tmp_path,
        session=session,
        api_max_retries=3,
    )

    with pytest.raises(
        APIHTTPError,
        match="500",
    ):
        client.request_json(
            "/orders",
        )

    assert session.get.call_count == 4
    assert sleep.call_count == 3

    client.close()


def test_retry_delay_is_capped(
    tmp_path: Path,
) -> None:
    client = make_client(
        tmp_path,
        api_backoff_factor=10_000.0,
    )

    delay = client._retry_delay(
        10,
        None,
    )

    assert delay <= 300.0

    client.close()


def test_fetch_page_defaults_to_configured_page_size(
    tmp_path: Path,
) -> None:
    session = MagicMock()
    session.get.return_value = make_response(
        payload={
            "data": [],
        }
    )

    client = make_client(
        tmp_path,
        session=session,
        api_page_size=25,
    )

    client.fetch_page(
        "/orders",
    )

    session.get.assert_called_once_with(
        "https://api.example.com/orders",
        params={
            "page": 1,
            "page_size": 25,
        },
        timeout=(10.0, 30.0),
    )

    client.close()


def test_iter_pages_passes_extra_parameters_to_each_page(
    tmp_path: Path,
) -> None:
    session = MagicMock()
    session.get.side_effect = [
        make_response(
            payload={
                "data": [
                    {"id": 1},
                ],
                "next_page": 2,
            }
        ),
        make_response(
            payload={
                "data": [
                    {"id": 2},
                ],
            }
        ),
    ]

    client = make_client(
        tmp_path,
        session=session,
    )

    list(
        client.iter_pages(
            "/orders",
            extra_params={
                "status": "completed",
                "region": "apac",
            },
        )
    )

    expected_calls = [
        (
            "https://api.example.com/orders",
            {
                "params": {
                    "page": 1,
                    "page_size": 2,
                    "status": "completed",
                    "region": "apac",
                },
                "timeout": (10.0, 30.0),
            },
        ),
        (
            "https://api.example.com/orders",
            {
                "params": {
                    "page": 2,
                    "page_size": 2,
                    "status": "completed",
                    "region": "apac",
                },
                "timeout": (10.0, 30.0),
            },
        ),
    ]

    assert session.get.call_count == 2
    for call, expected in zip(
        session.get.call_args_list,
        expected_calls,
    ):
        assert call.args == (expected[0],)
        assert call.kwargs == expected[1]

    client.close()

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests

from src.client import (
    APIClient,
    APIClientError,
    APIHTTPError,
    APIPage,
)
from src.config import PipelineConfig


def make_config(
    tmp_path: Path,
    **overrides,
) -> PipelineConfig:
    """Create an isolated API pipeline configuration for tests."""
    values = {
        "raw_data_dir": tmp_path / "raw",
        "staging_data_dir": tmp_path / "staging",
        "processed_data_dir": tmp_path / "processed",
        "reports_dir": tmp_path / "reports",
        "api_base_url": "https://api.example.com",
        "api_timeout_seconds": 30.0,
        "api_connect_timeout_seconds": 10.0,
        "api_read_timeout_seconds": 30.0,
        "api_max_retries": 3,
        "api_backoff_factor": 0.0,
        "api_page_size": 2,
        "api_max_pages": 10,
        "api_response_timezone": "UTC",
        "log_level": "CRITICAL",
    }
    values.update(overrides)
    return PipelineConfig(**values)


def make_response(
    *,
    status_code: int = 200,
    payload: object | None = None,
    headers: Mapping[str, str] | None = None,
    reason: str = "OK",
) -> MagicMock:
    """Build a mock requests response."""
    response = MagicMock()
    response.status_code = status_code
    response.reason = reason
    response.headers = dict(headers or {})
    response.ok = status_code < 400
    response.json.return_value = payload

    return response


def make_client(
    tmp_path: Path,
    *,
    session: MagicMock | None = None,
    **overrides,
) -> APIClient:
    """Create an API client with deterministic test configuration."""
    pipeline_config = make_config(
        tmp_path,
        **overrides,
    )
    return APIClient(
        pipeline_config,
        session=session,
    )


def test_client_configures_session_headers(
    tmp_path: Path,
) -> None:
    session = MagicMock()

    client = make_client(
        tmp_path,
        session=session,
        api_token="secret-token",
    )

    headers = session.headers.update.call_args.args[0]

    assert headers["Accept"] == "application/json"
    assert headers["Authorization"] == "Bearer secret-token"
    assert headers["User-Agent"] == (
        "api-data-processing-pipeline/1.0"
    )

    client.close()


def test_client_configures_default_headers_without_token(
    tmp_path: Path,
) -> None:
    session = MagicMock()

    client = make_client(
        tmp_path,
        session=session,
        api_token=None,
    )

    headers = session.headers.update.call_args.args[0]

    assert headers["Accept"] == "application/json"
    assert "Authorization" not in headers
    assert headers["User-Agent"] == (
        "api-data-processing-pipeline/1.0"
    )

    client.close()


def test_base_url_is_normalized(
    tmp_path: Path,
) -> None:
    client = make_client(
        tmp_path,
        api_base_url="https://api.example.com///",
    )

    assert client.base_url == "https://api.example.com/"

    client.close()


def test_base_url_rejects_empty_value(
    tmp_path: Path,
) -> None:
    client = make_client(
        tmp_path,
        api_base_url="   ",
    )

    with pytest.raises(
        APIClientError,
        match="cannot be empty",
    ):
        _ = client.base_url

    client.close()


@pytest.mark.parametrize(
    "base_url",
    [
        "api.example.com",
        "ftp://api.example.com",
        "example",
    ],
)
def test_base_url_requires_http_or_https(
    tmp_path: Path,
    base_url: str,
) -> None:
    client = make_client(
        tmp_path,
        api_base_url=base_url,
    )

    with pytest.raises(
        APIClientError,
        match="HTTP or HTTPS",
    ):
        _ = client.base_url

    client.close()


def test_build_url_resolves_relative_endpoint(
    tmp_path: Path,
) -> None:
    client = make_client(
        tmp_path,
        api_base_url="https://api.example.com/v1/",
    )

    assert client.build_url("/orders") == (
        "https://api.example.com/v1/orders"
    )

    client.close()


def test_build_url_preserves_absolute_url(
    tmp_path: Path,
) -> None:
    client = make_client(
        tmp_path,
    )

    url = "https://other.example.com/data"

    assert client.build_url(url) == url

    client.close()


def test_build_url_rejects_empty_endpoint(
    tmp_path: Path,
) -> None:
    client = make_client(
        tmp_path,
    )

    with pytest.raises(
        APIClientError,
        match="endpoint cannot be empty",
    ):
        client.build_url("   ")

    client.close()


def test_request_json_returns_dictionary_payload(
    tmp_path: Path,
) -> None:
    session = MagicMock()
    response = make_response(
        payload={
            "data": [
                {"id": 1},
                {"id": 2},
            ]
        }
    )
    session.get.return_value = response

    client = make_client(
        tmp_path,
        session=session,
    )

    result = client.request_json(
        "/orders",
        params={"page": 1},
    )

    assert result == {
        "data": [
            {"id": 1},
            {"id": 2},
        ]
    }
    session.get.assert_called_once_with(
        "https://api.example.com/orders",
        params={"page": 1},
        timeout=(10.0, 30.0),
    )

    client.close()


def test_request_json_rejects_non_object_json_payload(
    tmp_path: Path,
) -> None:
    session = MagicMock()
    response = make_response(
        payload=[
            {"id": 1},
        ]
    )
    session.get.return_value = response

    client = make_client(
        tmp_path,
        session=session,
    )

    with pytest.raises(
        APIClientError,
        match="must be a JSON object",
    ):
        client.request_json(
            "/orders",
        )

    client.close()


def test_request_json_rejects_invalid_json(
    tmp_path: Path,
) -> None:
    session = MagicMock()
    response = make_response()

    response.json.side_effect = ValueError("invalid json")
    session.get.return_value = response

    client = make_client(
        tmp_path,
        session=session,
    )

    with pytest.raises(
        APIClientError,
        match="invalid JSON",
    ):
        client.request_json(
            "/orders",
        )

    client.close()


@pytest.mark.parametrize(
    ("status_code", "message"),
    [
        (400, "HTTP 400"),
        (401, "authentication failed"),
        (403, "authorization failed"),
        (404, "endpoint was not found"),
    ],
)
def test_request_json_raises_api_http_error_for_non_retryable_status(
    tmp_path: Path,
    status_code: int,
    message: str,
) -> None:
    session = MagicMock()
    response = make_response(
        status_code=status_code,
        payload={"error": "failure"},
        reason="Error",
    )
    session.get.return_value = response

    client = make_client(
        tmp_path,
        session=session,
        api_max_retries=2,
    )

    with pytest.raises(
        APIHTTPError,
        match=message,
    ) as exc_info:
        client.request_json(
            "/orders",
        )

    assert exc_info.value.status_code == status_code
    assert exc_info.value.response is response
    session.get.assert_called_once()

    client.close()


@pytest.mark.parametrize(
    "status_code",
    [429, 500, 502, 503, 504],
)
def test_request_json_retries_retryable_http_status(
    tmp_path: Path,
    status_code: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = MagicMock()
    session.get.side_effect = [
        make_response(
            status_code=status_code,
            headers={"Retry-After": "0"},
        ),
        make_response(
            payload={
                "data": [
                    {"id": 1},
                ]
            }
        ),
    ]

    sleep = MagicMock()
    monkeypatch.setattr(
        "src.client.time.sleep",
        sleep,
    )

    client = make_client(
        tmp_path,
        session=session,
        api_max_retries=1,
    )

    result = client.request_json(
        "/orders",
    )

    assert result == {
        "data": [
            {"id": 1},
        ]
    }
    assert session.get.call_count == 2
    sleep.assert_called_once_with(0.0)

    client.close()


def test_request_json_stops_after_max_retries_for_retryable_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = MagicMock()
    session.get.return_value = make_response(
        status_code=503,
        headers={"Retry-After": "0"},
    )

    sleep = MagicMock()
    monkeypatch.setattr(
        "src.client.time.sleep",
        sleep,
    )

    client = make_client(
        tmp_path,
        session=session,
        api_max_retries=2,
    )

    with pytest.raises(
        APIHTTPError,
        match="503",
    ):
        client.request_json(
            "/orders",
        )

    assert session.get.call_count == 3
    assert sleep.call_count == 2

    client.close()


def test_request_json_uses_retry_after_header(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = MagicMock()
    session.get.side_effect = [
        make_response(
            status_code=429,
            headers={"Retry-After": "2"},
        ),
        make_response(
            payload={
                "data": [],
            }
        ),
    ]

    sleep = MagicMock()
    monkeypatch.setattr(
        "src.client.time.sleep",
        sleep,
    )

    client = make_client(
        tmp_path,
        session=session,
        api_max_retries=1,
    )

    client.request_json(
        "/orders",
    )

    sleep.assert_called_once_with(2.0)

    client.close()


def test_request_json_retries_timeout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = MagicMock()
    session.get.side_effect = [
        requests.Timeout("timed out"),
        make_response(
            payload={
                "data": [
                    {"id": 1},
                ]
            }
        ),
    ]

    sleep = MagicMock()
    monkeypatch.setattr(
        "src.client.time.sleep",
        sleep,
    )

    client = make_client(
        tmp_path,
        session=session,
        api_max_retries=1,
        api_backoff_factor=0.0,
    )

    result = client.request_json(
        "/orders",
    )

    assert result == {
        "data": [
            {"id": 1},
        ]
    }
    assert session.get.call_count == 2
    sleep.assert_called_once()

    client.close()


def test_request_json_raises_after_timeout_retries_exhausted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = MagicMock()
    session.get.side_effect = requests.Timeout(
        "timed out",
    )

    sleep = MagicMock()
    monkeypatch.setattr(
        "src.client.time.sleep",
        sleep,
    )

    client = make_client(
        tmp_path,
        session=session,
        api_max_retries=2,
    )

    with pytest.raises(
        APIClientError,
        match="timed out",
    ):
        client.request_json(
            "/orders",
        )

    assert session.get.call_count == 3
    assert sleep.call_count == 2

    client.close()


def test_request_json_retries_request_exception(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = MagicMock()
    session.get.side_effect = [
        requests.ConnectionError("connection reset"),
        make_response(
            payload={
                "data": [
                    {"id": 1},
                ]
            }
        ),
    ]

    sleep = MagicMock()
    monkeypatch.setattr(
        "src.client.time.sleep",
        sleep,
    )

    client = make_client(
        tmp_path,
        session=session,
        api_max_retries=1,
    )

    result = client.request_json(
        "/orders",
    )

    assert result["data"] == [{"id": 1}]
    assert session.get.call_count == 2
    assert sleep.call_count == 1

    client.close()


def test_request_json_raises_after_request_exceptions_exhausted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = MagicMock()
    session.get.side_effect = requests.ConnectionError(
        "connection reset",
    )

    monkeypatch.setattr(
        "src.client.time.sleep",
        MagicMock(),
    )

    client = make_client(
        tmp_path,
        session=session,
        api_max_retries=1,
    )

    with pytest.raises(
        APIClientError,
        match="request failed",
    ):
        client.request_json(
            "/orders",
        )

    assert session.get.call_count == 2

    client.close()


def test_extract_items_accepts_data_key(
    tmp_path: Path,
) -> None:
    client = make_client(tmp_path)

    payload = {
        "data": [
            {"id": 1},
            {"id": 2},
        ]
    }

    assert client._extract_items(payload) == [
        {"id": 1},
        {"id": 2},
    ]

    client.close()


def test_extract_items_accepts_items_key(
    tmp_path: Path,
) -> None:
    client = make_client(tmp_path)

    payload = {
        "items": [
            {"id": 1},
        ]
    }

    assert client._extract_items(payload) == [
        {"id": 1},
    ]

    client.close()


def test_extract_items_rejects_missing_items(
    tmp_path: Path,
) -> None:
    client = make_client(tmp_path)

    with pytest.raises(
        APIClientError,
        match="does not contain",
    ):
        client._extract_items({})

    client.close()


def test_extract_items_rejects_non_list_items(
    tmp_path: Path,
) -> None:
    client = make_client(tmp_path)

    with pytest.raises(
        APIClientError,
        match="must be a list",
    ):
        client._extract_items(
            {
                "data": {
                    "id": 1,
                }
            }
        )

    client.close()


def test_extract_items_rejects_non_dictionary_record(
    tmp_path: Path,
) -> None:
    client = make_client(tmp_path)

    with pytest.raises(
        APIClientError,
        match="index 1",
    ):
        client._extract_items(
            {
                "data": [
                    {"id": 1},
                    "invalid",
                ]
            }
        )

    client.close()


def test_extract_next_page_reads_nested_pagination(
    tmp_path: Path,
) -> None:
    client = make_client(tmp_path)

    result = client._extract_next_page(
        {
            "pagination": {
                "next_page": 3,
            }
        },
        2,
    )

    assert result == 3

    client.close()


def test_extract_next_page_reads_top_level_value(
    tmp_path: Path,
) -> None:
    client = make_client(tmp_path)

    result = client._extract_next_page(
        {
            "next_page": 3,
        },
        2,
    )

    assert result == 3

    client.close()


def test_extract_next_page_returns_none_when_absent(
    tmp_path: Path,
) -> None:
    client = make_client(tmp_path)

    assert (
        client._extract_next_page(
            {},
            1,
        )
        is None
    )

    client.close()


def test_extract_next_page_rejects_non_forward_page(
    tmp_path: Path,
) -> None:
    client = make_client(tmp_path)

    with pytest.raises(
        APIClientError,
        match="non-forward",
    ):
        client._extract_next_page(
            {"next_page": 1},
            1,
        )

    client.close()


def test_fetch_page_returns_api_page(
    tmp_path: Path,
) -> None:
    session = MagicMock()
    session.get.return_value = make_response(
        payload={
            "data": [
                {"id": 1},
                {"id": 2},
            ],
            "pagination": {
                "next_page": 2,
            },
        }
    )

    client = make_client(
        tmp_path,
        session=session,
        api_page_size=50,
    )

    result = client.fetch_page(
        "/orders",
        page=1,
        extra_params={
            "status": "completed",
        },
    )

    assert isinstance(result, APIPage)
    assert result.items == [
        {"id": 1},
        {"id": 2},
    ]
    assert result.next_page == 2
    assert result.raw["data"] == [
        {"id": 1},
        {"id": 2},
    ]

    session.get.assert_called_once_with(
        "https://api.example.com/orders",
        params={
            "page": 1,
            "page_size": 50,
            "status": "completed",
        },
        timeout=(10.0, 30.0),
    )

    client.close()


@pytest.mark.parametrize(
    "page",
    [0, -1],
)
def test_fetch_page_rejects_invalid_page(
    tmp_path: Path,
    page: int,
) -> None:
    client = make_client(tmp_path)

    with pytest.raises(
        ValueError,
        match="greater than or equal to 1",
    ):
        client.fetch_page(
            "/orders",
            page=page,
        )

    client.close()


def test_fetch_page_rejects_invalid_page_size(
    tmp_path: Path,
) -> None:
    client = make_client(tmp_path)

    with pytest.raises(
        ValueError,
        match="page_size",
    ):
        client.fetch_page(
            "/orders",
            page_size=0,
        )

    client.close()


def test_iter_pages_follows_pagination(
    tmp_path: Path,
) -> None:
    session = MagicMock()
    session.get.side_effect = [
        make_response(
            payload={
                "data": [
                    {"id": 1},
                ],
                "pagination": {
                    "next_page": 2,
                },
            }
        ),
        make_response(
            payload={
                "data": [
                    {"id": 2},
                ],
                "pagination": {
                    "next_page": 3,
                },
            }
        ),
        make_response(
            payload={
                "data": [
                    {"id": 3},
                ],
            }
        ),
    ]

    client = make_client(
        tmp_path,
        session=session,
    )

    pages = list(
        client.iter_pages(
            "/orders",
        )
    )

    assert [page.items for page in pages] == [
        [{"id": 1}],
        [{"id": 2}],
        [{"id": 3}],
    ]

    assert [page.next_page for page in pages] == [
        2,
        3,
        None,
    ]

    assert session.get.call_count == 3

    client.close()


def test_iter_pages_stops_at_configured_page_limit(
    tmp_path: Path,
) -> None:
    session = MagicMock()
    session.get.return_value = make_response(
        payload={
            "data": [
                {"id": 1},
            ],
            "pagination": {
                "next_page": 2,
            },
        }
    )

    client = make_client(
        tmp_path,
        session=session,
        api_max_pages=2,
    )

    with pytest.raises(
        APIClientError,
        match="maximum page count",
    ):
        list(
            client.iter_pages(
                "/orders",
            )
        )

    assert session.get.call_count == 2

    client.close()


def test_iter_records_flattens_pages(
    tmp_path: Path,
) -> None:
    session = MagicMock()
    session.get.side_effect = [
        make_response(
            payload={
                "data": [
                    {"id": 1},
                    {"id": 2},
                ],
                "next_page": 2,
            }
        ),
        make_response(
            payload={
                "data": [
                    {"id": 3},
                ],
            }
        ),
    ]

    client = make_client(
        tmp_path,
        session=session,
    )

    records = list(
        client.iter_records(
            "/orders",
        )
    )

    assert records == [
        {"id": 1},
        {"id": 2},
        {"id": 3},
    ]

    client.close()


def test_retry_delay_prefers_retry_after_header(
    tmp_path: Path,
) -> None:
    client = make_client(tmp_path)

    response = make_response(
        status_code=429,
        headers={
            "Retry-After": "5",
        },
    )

    assert client._retry_delay(
        1,
        response,
    ) == 5.0

    client.close()


def test_retry_delay_uses_exponential_backoff_when_retry_after_is_invalid(
    tmp_path: Path,
) -> None:
    client = make_client(
        tmp_path,
        api_backoff_factor=2.0,
    )

    response = make_response(
        status_code=503,
        headers={
            "Retry-After": "not-a-delay",
        },
    )

    delay = client._retry_delay(
        3,
        response,
    )

    assert 8.0 <= delay <= 8.25

    client.close()


def test_context_manager_closes_session(
    tmp_path: Path,
) -> None:
    session = MagicMock()

    with APIClient(
        make_config(tmp_path),
        session=session,
    ) as client:
        assert client is not None

    session.close.assert_called_once()


def test_close_closes_underlying_session(
    tmp_path: Path,
) -> None:
    session = MagicMock()

    client = make_client(
        tmp_path,
        session=session,
    )

    client.close()

    session.close.assert_called_once()


def test_request_timeout_uses_connect_and_read_configuration(
    tmp_path: Path,
) -> None:
    session = MagicMock()
    session.get.return_value = make_response(
        payload={
            "data": [],
        }
    )

    client = make_client(
        tmp_path,
        session=session,
        api_connect_timeout_seconds=3.5,
        api_read_timeout_seconds=17.5,
    )

    client.request_json(
        "/orders",
    )

    session.get.assert_called_once_with(
        "https://api.example.com/orders",
        params={},
        timeout=(3.5, 17.5),
    )

    client.close()


def test_request_json_retries_are_bounded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = MagicMock()
    session.get.return_value = make_response(
        status_code=500,
        headers={"Retry-After": "0"},
    )

    sleep = MagicMock()
    monkeypatch.setattr(
        "src.client.time.sleep",
        sleep,
    )

    client = make_client(
        tmp_path,
        session=session,
        api_max_retries=3,
    )

    with pytest.raises(
        APIHTTPError,
        match="500",
    ):
        client.request_json(
            "/orders",
        )

    assert session.get.call_count == 4
    assert sleep.call_count == 3

    client.close()


def test_retry_delay_is_capped(
    tmp_path: Path,
) -> None:
    client = make_client(
        tmp_path,
        api_backoff_factor=10_000.0,
    )

    delay = client._retry_delay(
        10,
        None,
    )

    assert delay <= 300.0

    client.close()


def test_fetch_page_defaults_to_configured_page_size(
    tmp_path: Path,
) -> None:
    session = MagicMock()
    session.get.return_value = make_response(
        payload={
            "data": [],
        }
    )

    client = make_client(
        tmp_path,
        session=session,
        api_page_size=25,
    )

    client.fetch_page(
        "/orders",
    )

    session.get.assert_called_once_with(
        "https://api.example.com/orders",
        params={
            "page": 1,
            "page_size": 25,
        },
        timeout=(10.0, 30.0),
    )

    client.close()


def test_iter_pages_passes_extra_parameters_to_each_page(
    tmp_path: Path,
) -> None:
    session = MagicMock()
    session.get.side_effect = [
        make_response(
            payload={
                "data": [
                    {"id": 1},
                ],
                "next_page": 2,
            }
        ),
        make_response(
            payload={
                "data": [
                    {"id": 2},
                ],
            }
        ),
    ]

    client = make_client(
        tmp_path,
        session=session,
    )

    list(
        client.iter_pages(
            "/orders",
            extra_params={
                "status": "completed",
                "region": "apac",
            },
        )
    )

    expected_calls = [
        (
            "https://api.example.com/orders",
            {
                "params": {
                    "page": 1,
                    "page_size": 2,
                    "status": "completed",
                    "region": "apac",
                },
                "timeout": (10.0, 30.0),
            },
        ),
        (
            "https://api.example.com/orders",
            {
                "params": {
                    "page": 2,
                    "page_size": 2,
                    "status": "completed",
                    "region": "apac",
                },
                "timeout": (10.0, 30.0),
            },
        ),
    ]

    assert session.get.call_count == 2
    for call, expected in zip(
        session.get.call_args_list,
        expected_calls,
    ):
        assert call.args == (expected[0],)
        assert call.kwargs == expected[1]

    client.close()