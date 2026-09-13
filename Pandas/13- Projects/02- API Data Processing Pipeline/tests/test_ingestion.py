from __future__ import annotations

from collections.abc import Iterator, Mapping
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.client import APIClient, APIPage
from src.config import PipelineConfig
from src.ingestion import (
    IngestionError,
    IngestionResult,
    ingest_and_validate,
    ingest_api_data,
    ingest_pages,
    iter_api_records,
    validate_ingestion_result,
)


def make_config(
    tmp_path: Path,
    **overrides,
) -> PipelineConfig:
    """Create an isolated pipeline configuration for tests."""
    values = {
        "raw_data_dir": tmp_path / "raw",
        "staging_data_dir": tmp_path / "staging",
        "processed_data_dir": tmp_path / "processed",
        "reports_dir": tmp_path / "reports",
        "api_base_url": "https://api.example.com",
        "api_page_size": 2,
        "api_max_pages": 10,
        "api_timeout_seconds": 30.0,
        "api_connect_timeout_seconds": 10.0,
        "api_read_timeout_seconds": 30.0,
        "api_max_retries": 0,
        "api_backoff_factor": 0.0,
        "api_response_timezone": "UTC",
        "log_level": "CRITICAL",
    }
    values.update(overrides)
    return PipelineConfig(**values)


def make_client(
    pages: list[APIPage] | None = None,
    *,
    records: list[dict] | None = None,
) -> MagicMock:
    """Create a mocked API client with configurable page and record streams."""
    client = MagicMock(spec=APIClient)

    if pages is not None:
        client.iter_pages.return_value = iter(pages)

    if records is not None:
        client.iter_records.return_value = iter(records)

    return client


def make_page(
    items: list[dict],
    *,
    page: int = 1,
    next_page: int | None = None,
    raw: Mapping | None = None,
) -> APIPage:
    """Build an API page fixture."""
    return APIPage(
        items=items,
        page=page,
        next_page=next_page,
        raw=dict(raw or {"data": items}),
    )


def test_iter_api_records_yields_records_incrementally(
    tmp_path: Path,
) -> None:
    records = [
        {"id": "1", "status": "completed"},
        {"id": "2", "status": "pending"},
    ]
    client = make_client(records=records)

    result = list(
        iter_api_records(
            "/orders",
            pipeline_config=make_config(tmp_path),
            client=client,
        )
    )

    assert result == records
    client.iter_records.assert_called_once_with(
        "/orders",
        page_size=2,
        extra_params=None,
    )
    client.close.assert_not_called()


def test_iter_api_records_passes_extra_parameters(
    tmp_path: Path,
) -> None:
    client = make_client(
        records=[
            {"id": "1"},
        ]
    )
    extra_params = {
        "status": "completed",
        "region": "apac",
    }

    result = list(
        iter_api_records(
            "/orders",
            pipeline_config=make_config(tmp_path),
            client=client,
            extra_params=extra_params,
        )
    )

    assert result == [{"id": "1"}]
    client.iter_records.assert_called_once_with(
        "/orders",
        page_size=2,
        extra_params=extra_params,
    )


def test_iter_api_records_closes_owned_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = make_client(
        records=[
            {"id": "1"},
        ]
    )
    client_factory = MagicMock(return_value=client)

    monkeypatch.setattr(
        "src.ingestion.APIClient",
        client_factory,
    )

    result = list(
        iter_api_records(
            "/orders",
            pipeline_config=make_config(tmp_path),
        )
    )

    assert result == [{"id": "1"}]
    client_factory.assert_called_once()
    client.close.assert_called_once()


def test_iter_api_records_closes_owned_client_when_ingestion_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = MagicMock(spec=APIClient)
    client.iter_records.side_effect = RuntimeError(
        "connection failed"
    )

    client_factory = MagicMock(return_value=client)

    monkeypatch.setattr(
        "src.ingestion.APIClient",
        client_factory,
    )

    with pytest.raises(
        IngestionError,
        match="Failed to ingest API records",
    ):
        list(
            iter_api_records(
                "/orders",
                pipeline_config=make_config(tmp_path),
            )
        )

    client.close.assert_called_once()


def test_iter_api_records_wraps_client_errors(
    tmp_path: Path,
) -> None:
    client = make_client()

    client.iter_records.side_effect = RuntimeError(
        "unexpected client failure"
    )

    with pytest.raises(
        IngestionError,
        match="Failed to ingest API records from endpoint: /orders",
    ):
        list(
            iter_api_records(
                "/orders",
                pipeline_config=make_config(tmp_path),
                client=client,
            )
        )


def test_iter_api_records_preserves_ingestion_errors(
    tmp_path: Path,
) -> None:
    client = make_client()
    expected = IngestionError("already normalized")

    client.iter_records.side_effect = expected

    with pytest.raises(IngestionError) as exc_info:
        list(
            iter_api_records(
                "/orders",
                pipeline_config=make_config(tmp_path),
                client=client,
            )
        )

    assert exc_info.value is expected


def test_ingest_api_data_accumulates_all_pages(
    tmp_path: Path,
) -> None:
    pages = [
        make_page(
            [
                {"id": "1"},
                {"id": "2"},
            ],
            page=1,
            next_page=2,
        ),
        make_page(
            [
                {"id": "3"},
            ],
            page=2,
            next_page=None,
        ),
    ]
    client = make_client(pages=pages)

    result = ingest_api_data(
        "/orders",
        pipeline_config=make_config(tmp_path),
        client=client,
    )

    assert isinstance(result, IngestionResult)
    assert result.records == [
        {"id": "1"},
        {"id": "2"},
        {"id": "3"},
    ]
    assert result.pages_fetched == 2
    assert result.records_fetched == 3

    client.iter_pages.assert_called_once_with(
        "/orders",
        page_size=2,
        extra_params=None,
    )


def test_ingest_api_data_passes_extra_parameters(
    tmp_path: Path,
) -> None:
    pages = [
        make_page(
            [{"id": "1"}],
        )
    ]
    client = make_client(pages=pages)
    extra_params = {
        "status": "completed",
    }

    result = ingest_api_data(
        "/orders",
        pipeline_config=make_config(tmp_path),
        client=client,
        extra_params=extra_params,
    )

    assert result.records == [{"id": "1"}]
    client.iter_pages.assert_called_once_with(
        "/orders",
        page_size=2,
        extra_params=extra_params,
    )


def test_ingest_api_data_returns_empty_result_for_empty_api(
    tmp_path: Path,
) -> None:
    client = make_client(
        pages=[
            make_page([]),
        ]
    )

    result = ingest_api_data(
        "/orders",
        pipeline_config=make_config(tmp_path),
        client=client,
    )

    assert result.records == []
    assert result.pages_fetched == 1
    assert result.records_fetched == 0


def test_ingest_api_data_closes_owned_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = make_client(
        pages=[
            make_page(
                [{"id": "1"}],
            )
        ]
    )
    client_factory = MagicMock(return_value=client)

    monkeypatch.setattr(
        "src.ingestion.APIClient",
        client_factory,
    )

    result = ingest_api_data(
        "/orders",
        pipeline_config=make_config(tmp_path),
    )

    assert result.records == [{"id": "1"}]
    client_factory.assert_called_once()
    client.close.assert_called_once()


def test_ingest_api_data_closes_owned_client_when_client_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = MagicMock(spec=APIClient)
    client.iter_pages.side_effect = RuntimeError(
        "api unavailable"
    )

    client_factory = MagicMock(return_value=client)

    monkeypatch.setattr(
        "src.ingestion.APIClient",
        client_factory,
    )

    with pytest.raises(
        IngestionError,
        match="Failed to ingest API data",
    ):
        ingest_api_data(
            "/orders",
            pipeline_config=make_config(tmp_path),
        )

    client.close.assert_called_once()


def test_ingest_api_data_does_not_close_injected_client(
    tmp_path: Path,
) -> None:
    client = make_client(
        pages=[
            make_page(
                [{"id": "1"}],
            )
        ]
    )

    ingest_api_data(
        "/orders",
        pipeline_config=make_config(tmp_path),
        client=client,
    )

    client.close.assert_not_called()


def test_ingest_pages_yields_each_page_without_accumulating(
    tmp_path: Path,
) -> None:
    pages = [
        make_page(
            [
                {"id": "1"},
                {"id": "2"},
            ],
            page=1,
            next_page=2,
        ),
        make_page(
            [
                {"id": "3"},
            ],
            page=2,
        ),
    ]
    client = make_client(pages=pages)

    result = list(
        ingest_pages(
            "/orders",
            pipeline_config=make_config(tmp_path),
            client=client,
        )
    )

    assert result == [
        [
            {"id": "1"},
            {"id": "2"},
        ],
        [
            {"id": "3"},
        ],
    ]
    client.iter_pages.assert_called_once_with(
        "/orders",
        page_size=2,
        extra_params=None,
    )


def test_ingest_pages_preserves_page_boundaries(
    tmp_path: Path,
) -> None:
    pages = [
        make_page([{"id": "1"}]),
        make_page([{"id": "2"}]),
        make_page([]),
    ]
    client = make_client(pages=pages)

    result = list(
        ingest_pages(
            "/orders",
            pipeline_config=make_config(tmp_path),
            client=client,
        )
    )

    assert result == [
        [{"id": "1"}],
        [{"id": "2"}],
        [],
    ]


def test_ingest_pages_passes_extra_parameters(
    tmp_path: Path,
) -> None:
    client = make_client(
        pages=[
            make_page([{"id": "1"}]),
        ]
    )
    extra_params = {
        "updated_since": "2026-01-01T00:00:00Z",
    }

    result = list(
        ingest_pages(
            "/events",
            pipeline_config=make_config(tmp_path),
            client=client,
            extra_params=extra_params,
        )
    )

    assert result == [[{"id": "1"}]]
    client.iter_pages.assert_called_once_with(
        "/events",
        page_size=2,
        extra_params=extra_params,
    )


def test_ingest_pages_wraps_client_errors(
    tmp_path: Path,
) -> None:
    client = make_client()
    client.iter_pages.side_effect = RuntimeError(
        "request failed"
    )

    with pytest.raises(
        IngestionError,
        match="Failed to ingest API pages from endpoint: /orders",
    ):
        list(
            ingest_pages(
                "/orders",
                pipeline_config=make_config(tmp_path),
                client=client,
            )
        )


def test_ingest_pages_closes_owned_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = make_client(
        pages=[
            make_page(
                [{"id": "1"}],
            )
        ]
    )
    client_factory = MagicMock(return_value=client)

    monkeypatch.setattr(
        "src.ingestion.APIClient",
        client_factory,
    )

    result = list(
        ingest_pages(
            "/orders",
            pipeline_config=make_config(tmp_path),
        )
    )

    assert result == [[{"id": "1"}]]
    client_factory.assert_called_once()
    client.close.assert_called_once()


@pytest.mark.parametrize(
    "result",
    [
        IngestionResult(
            records=[],
            pages_fetched=0,
            records_fetched=0,
        ),
        IngestionResult(
            records=[
                {"id": "1"},
                {"id": "2"},
            ],
            pages_fetched=1,
            records_fetched=2,
        ),
        IngestionResult(
            records=[
                {"id": "1"},
            ],
            pages_fetched=3,
            records_fetched=1,
        ),
    ],
)
def test_validate_ingestion_result_accepts_consistent_results(
    result: IngestionResult,
) -> None:
    validate_ingestion_result(result)


@pytest.mark.parametrize(
    "result",
    [
        IngestionResult(
            records=[],
            pages_fetched=-1,
            records_fetched=0,
        ),
        IngestionResult(
            records=[
                {"id": "1"},
            ],
            pages_fetched=1,
            records_fetched=-1,
        ),
        IngestionResult(
            records=[
                {"id": "1"},
            ],
            pages_fetched=1,
            records_fetched=0,
        ),
    ],
)
def test_validate_ingestion_result_rejects_inconsistent_statistics(
    result: IngestionResult,
) -> None:
    with pytest.raises(
        IngestionError,
    ):
        validate_ingestion_result(result)


@pytest.mark.parametrize(
    "records",
    [
        [None],
        ["invalid"],
        [1],
        [object()],
    ],
)
def test_validate_ingestion_result_rejects_non_dictionary_records(
    records: list,
) -> None:
    result = IngestionResult(
        records=records,
        pages_fetched=1,
        records_fetched=len(records),
    )

    with pytest.raises(
        IngestionError,
        match="not a dictionary",
    ):
        validate_ingestion_result(result)


def test_ingest_and_validate_returns_valid_result(
    tmp_path: Path,
) -> None:
    client = make_client(
        pages=[
            make_page(
                [
                    {"id": "1"},
                    {"id": "2"},
                ]
            )
        ]
    )

    result = ingest_and_validate(
        "/orders",
        pipeline_config=make_config(tmp_path),
        client=client,
    )

    assert result == IngestionResult(
        records=[
            {"id": "1"},
            {"id": "2"},
        ],
        pages_fetched=1,
        records_fetched=2,
    )


def test_ingest_and_validate_rejects_invalid_client_output(
    tmp_path: Path,
) -> None:
    client = make_client(
        pages=[
            make_page(
                [
                    {"id": "1"},
                ]
            )
        ]
    )

    with pytest.raises(
        IngestionError,
        match="records_fetched",
    ):
        result = IngestionResult(
            records=[{"id": "1"}],
            pages_fetched=1,
            records_fetched=2,
        )
        validate_ingestion_result(result)

    client.close.assert_not_called()


def test_ingest_and_validate_delegates_to_ingestion_and_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = IngestionResult(
        records=[
            {"id": "1"},
        ],
        pages_fetched=1,
        records_fetched=1,
    )

    ingest_mock = MagicMock(
        return_value=expected,
    )
    validate_mock = MagicMock()

    monkeypatch.setattr(
        "src.ingestion.ingest_api_data",
        ingest_mock,
    )
    monkeypatch.setattr(
        "src.ingestion.validate_ingestion_result",
        validate_mock,
    )

    result = ingest_and_validate(
        "/orders",
        pipeline_config=make_config(tmp_path),
        extra_params={"status": "completed"},
    )

    assert result is expected

    ingest_mock.assert_called_once_with(
        "/orders",
        pipeline_config=make_config(tmp_path),
        client=None,
        extra_params={"status": "completed"},
    )
    validate_mock.assert_called_once_with(expected)


def test_ingestion_functions_use_configured_page_size(
    tmp_path: Path,
) -> None:
    client = make_client(
        pages=[
            make_page(
                [{"id": "1"}],
            )
        ]
    )
    pipeline_config = make_config(
        tmp_path,
        api_page_size=100,
    )

    ingest_api_data(
        "/orders",
        pipeline_config=pipeline_config,
        client=client,
    )

    client.iter_pages.assert_called_once_with(
        "/orders",
        page_size=100,
        extra_params=None,
    )


def test_iter_api_records_returns_iterator(
    tmp_path: Path,
) -> None:
    client = make_client(
        records=[
            {"id": "1"},
        ]
    )

    result = iter_api_records(
        "/orders",
        pipeline_config=make_config(tmp_path),
        client=client,
    )

    assert isinstance(
        result,
        Iterator,
    )

    assert list(result) == [{"id": "1"}]


def test_ingest_pages_returns_iterator(
    tmp_path: Path,
) -> None:
    client = make_client(
        pages=[
            make_page(
                [{"id": "1"}],
            )
        ]
    )

    result = ingest_pages(
        "/orders",
        pipeline_config=make_config(tmp_path),
        client=client,
    )

    assert isinstance(
        result,
        Iterator,
    )

    assert list(result) == [[{"id": "1"}]]

from __future__ import annotations

from collections.abc import Iterator, Mapping
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.client import APIClient, APIPage
from src.config import PipelineConfig
from src.ingestion import (
    IngestionError,
    IngestionResult,
    ingest_and_validate,
    ingest_api_data,
    ingest_pages,
    iter_api_records,
    validate_ingestion_result,
)


def make_config(
    tmp_path: Path,
    **overrides,
) -> PipelineConfig:
    """Create an isolated pipeline configuration for tests."""
    values = {
        "raw_data_dir": tmp_path / "raw",
        "staging_data_dir": tmp_path / "staging",
        "processed_data_dir": tmp_path / "processed",
        "reports_dir": tmp_path / "reports",
        "api_base_url": "https://api.example.com",
        "api_page_size": 2,
        "api_max_pages": 10,
        "api_timeout_seconds": 30.0,
        "api_connect_timeout_seconds": 10.0,
        "api_read_timeout_seconds": 30.0,
        "api_max_retries": 0,
        "api_backoff_factor": 0.0,
        "api_response_timezone": "UTC",
        "log_level": "CRITICAL",
    }
    values.update(overrides)
    return PipelineConfig(**values)


def make_client(
    pages: list[APIPage] | None = None,
    *,
    records: list[dict] | None = None,
) -> MagicMock:
    """Create a mocked API client with configurable page and record streams."""
    client = MagicMock(spec=APIClient)

    if pages is not None:
        client.iter_pages.return_value = iter(pages)

    if records is not None:
        client.iter_records.return_value = iter(records)

    return client


def make_page(
    items: list[dict],
    *,
    page: int = 1,
    next_page: int | None = None,
    raw: Mapping | None = None,
) -> APIPage:
    """Build an API page fixture."""
    return APIPage(
        items=items,
        page=page,
        next_page=next_page,
        raw=dict(raw or {"data": items}),
    )


def test_iter_api_records_yields_records_incrementally(
    tmp_path: Path,
) -> None:
    records = [
        {"id": "1", "status": "completed"},
        {"id": "2", "status": "pending"},
    ]
    client = make_client(records=records)

    result = list(
        iter_api_records(
            "/orders",
            pipeline_config=make_config(tmp_path),
            client=client,
        )
    )

    assert result == records
    client.iter_records.assert_called_once_with(
        "/orders",
        page_size=2,
        extra_params=None,
    )
    client.close.assert_not_called()


def test_iter_api_records_passes_extra_parameters(
    tmp_path: Path,
) -> None:
    client = make_client(
        records=[
            {"id": "1"},
        ]
    )
    extra_params = {
        "status": "completed",
        "region": "apac",
    }

    result = list(
        iter_api_records(
            "/orders",
            pipeline_config=make_config(tmp_path),
            client=client,
            extra_params=extra_params,
        )
    )

    assert result == [{"id": "1"}]
    client.iter_records.assert_called_once_with(
        "/orders",
        page_size=2,
        extra_params=extra_params,
    )


def test_iter_api_records_closes_owned_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = make_client(
        records=[
            {"id": "1"},
        ]
    )
    client_factory = MagicMock(return_value=client)

    monkeypatch.setattr(
        "src.ingestion.APIClient",
        client_factory,
    )

    result = list(
        iter_api_records(
            "/orders",
            pipeline_config=make_config(tmp_path),
        )
    )

    assert result == [{"id": "1"}]
    client_factory.assert_called_once()
    client.close.assert_called_once()


def test_iter_api_records_closes_owned_client_when_ingestion_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = MagicMock(spec=APIClient)
    client.iter_records.side_effect = RuntimeError(
        "connection failed"
    )

    client_factory = MagicMock(return_value=client)

    monkeypatch.setattr(
        "src.ingestion.APIClient",
        client_factory,
    )

    with pytest.raises(
        IngestionError,
        match="Failed to ingest API records",
    ):
        list(
            iter_api_records(
                "/orders",
                pipeline_config=make_config(tmp_path),
            )
        )

    client.close.assert_called_once()


def test_iter_api_records_wraps_client_errors(
    tmp_path: Path,
) -> None:
    client = make_client()

    client.iter_records.side_effect = RuntimeError(
        "unexpected client failure"
    )

    with pytest.raises(
        IngestionError,
        match="Failed to ingest API records from endpoint: /orders",
    ):
        list(
            iter_api_records(
                "/orders",
                pipeline_config=make_config(tmp_path),
                client=client,
            )
        )


def test_iter_api_records_preserves_ingestion_errors(
    tmp_path: Path,
) -> None:
    client = make_client()
    expected = IngestionError("already normalized")

    client.iter_records.side_effect = expected

    with pytest.raises(IngestionError) as exc_info:
        list(
            iter_api_records(
                "/orders",
                pipeline_config=make_config(tmp_path),
                client=client,
            )
        )

    assert exc_info.value is expected


def test_ingest_api_data_accumulates_all_pages(
    tmp_path: Path,
) -> None:
    pages = [
        make_page(
            [
                {"id": "1"},
                {"id": "2"},
            ],
            page=1,
            next_page=2,
        ),
        make_page(
            [
                {"id": "3"},
            ],
            page=2,
            next_page=None,
        ),
    ]
    client = make_client(pages=pages)

    result = ingest_api_data(
        "/orders",
        pipeline_config=make_config(tmp_path),
        client=client,
    )

    assert isinstance(result, IngestionResult)
    assert result.records == [
        {"id": "1"},
        {"id": "2"},
        {"id": "3"},
    ]
    assert result.pages_fetched == 2
    assert result.records_fetched == 3

    client.iter_pages.assert_called_once_with(
        "/orders",
        page_size=2,
        extra_params=None,
    )


def test_ingest_api_data_passes_extra_parameters(
    tmp_path: Path,
) -> None:
    pages = [
        make_page(
            [{"id": "1"}],
        )
    ]
    client = make_client(pages=pages)
    extra_params = {
        "status": "completed",
    }

    result = ingest_api_data(
        "/orders",
        pipeline_config=make_config(tmp_path),
        client=client,
        extra_params=extra_params,
    )

    assert result.records == [{"id": "1"}]
    client.iter_pages.assert_called_once_with(
        "/orders",
        page_size=2,
        extra_params=extra_params,
    )


def test_ingest_api_data_returns_empty_result_for_empty_api(
    tmp_path: Path,
) -> None:
    client = make_client(
        pages=[
            make_page([]),
        ]
    )

    result = ingest_api_data(
        "/orders",
        pipeline_config=make_config(tmp_path),
        client=client,
    )

    assert result.records == []
    assert result.pages_fetched == 1
    assert result.records_fetched == 0


def test_ingest_api_data_closes_owned_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = make_client(
        pages=[
            make_page(
                [{"id": "1"}],
            )
        ]
    )
    client_factory = MagicMock(return_value=client)

    monkeypatch.setattr(
        "src.ingestion.APIClient",
        client_factory,
    )

    result = ingest_api_data(
        "/orders",
        pipeline_config=make_config(tmp_path),
    )

    assert result.records == [{"id": "1"}]
    client_factory.assert_called_once()
    client.close.assert_called_once()


def test_ingest_api_data_closes_owned_client_when_client_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = MagicMock(spec=APIClient)
    client.iter_pages.side_effect = RuntimeError(
        "api unavailable"
    )

    client_factory = MagicMock(return_value=client)

    monkeypatch.setattr(
        "src.ingestion.APIClient",
        client_factory,
    )

    with pytest.raises(
        IngestionError,
        match="Failed to ingest API data",
    ):
        ingest_api_data(
            "/orders",
            pipeline_config=make_config(tmp_path),
        )

    client.close.assert_called_once()


def test_ingest_api_data_does_not_close_injected_client(
    tmp_path: Path,
) -> None:
    client = make_client(
        pages=[
            make_page(
                [{"id": "1"}],
            )
        ]
    )

    ingest_api_data(
        "/orders",
        pipeline_config=make_config(tmp_path),
        client=client,
    )

    client.close.assert_not_called()


def test_ingest_pages_yields_each_page_without_accumulating(
    tmp_path: Path,
) -> None:
    pages = [
        make_page(
            [
                {"id": "1"},
                {"id": "2"},
            ],
            page=1,
            next_page=2,
        ),
        make_page(
            [
                {"id": "3"},
            ],
            page=2,
        ),
    ]
    client = make_client(pages=pages)

    result = list(
        ingest_pages(
            "/orders",
            pipeline_config=make_config(tmp_path),
            client=client,
        )
    )

    assert result == [
        [
            {"id": "1"},
            {"id": "2"},
        ],
        [
            {"id": "3"},
        ],
    ]
    client.iter_pages.assert_called_once_with(
        "/orders",
        page_size=2,
        extra_params=None,
    )


def test_ingest_pages_preserves_page_boundaries(
    tmp_path: Path,
) -> None:
    pages = [
        make_page([{"id": "1"}]),
        make_page([{"id": "2"}]),
        make_page([]),
    ]
    client = make_client(pages=pages)

    result = list(
        ingest_pages(
            "/orders",
            pipeline_config=make_config(tmp_path),
            client=client,
        )
    )

    assert result == [
        [{"id": "1"}],
        [{"id": "2"}],
        [],
    ]


def test_ingest_pages_passes_extra_parameters(
    tmp_path: Path,
) -> None:
    client = make_client(
        pages=[
            make_page([{"id": "1"}]),
        ]
    )
    extra_params = {
        "updated_since": "2026-01-01T00:00:00Z",
    }

    result = list(
        ingest_pages(
            "/events",
            pipeline_config=make_config(tmp_path),
            client=client,
            extra_params=extra_params,
        )
    )

    assert result == [[{"id": "1"}]]
    client.iter_pages.assert_called_once_with(
        "/events",
        page_size=2,
        extra_params=extra_params,
    )


def test_ingest_pages_wraps_client_errors(
    tmp_path: Path,
) -> None:
    client = make_client()
    client.iter_pages.side_effect = RuntimeError(
        "request failed"
    )

    with pytest.raises(
        IngestionError,
        match="Failed to ingest API pages from endpoint: /orders",
    ):
        list(
            ingest_pages(
                "/orders",
                pipeline_config=make_config(tmp_path),
                client=client,
            )
        )


def test_ingest_pages_closes_owned_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = make_client(
        pages=[
            make_page(
                [{"id": "1"}],
            )
        ]
    )
    client_factory = MagicMock(return_value=client)

    monkeypatch.setattr(
        "src.ingestion.APIClient",
        client_factory,
    )

    result = list(
        ingest_pages(
            "/orders",
            pipeline_config=make_config(tmp_path),
        )
    )

    assert result == [[{"id": "1"}]]
    client_factory.assert_called_once()
    client.close.assert_called_once()


@pytest.mark.parametrize(
    "result",
    [
        IngestionResult(
            records=[],
            pages_fetched=0,
            records_fetched=0,
        ),
        IngestionResult(
            records=[
                {"id": "1"},
                {"id": "2"},
            ],
            pages_fetched=1,
            records_fetched=2,
        ),
        IngestionResult(
            records=[
                {"id": "1"},
            ],
            pages_fetched=3,
            records_fetched=1,
        ),
    ],
)
def test_validate_ingestion_result_accepts_consistent_results(
    result: IngestionResult,
) -> None:
    validate_ingestion_result(result)


@pytest.mark.parametrize(
    "result",
    [
        IngestionResult(
            records=[],
            pages_fetched=-1,
            records_fetched=0,
        ),
        IngestionResult(
            records=[
                {"id": "1"},
            ],
            pages_fetched=1,
            records_fetched=-1,
        ),
        IngestionResult(
            records=[
                {"id": "1"},
            ],
            pages_fetched=1,
            records_fetched=0,
        ),
    ],
)
def test_validate_ingestion_result_rejects_inconsistent_statistics(
    result: IngestionResult,
) -> None:
    with pytest.raises(
        IngestionError,
    ):
        validate_ingestion_result(result)


@pytest.mark.parametrize(
    "records",
    [
        [None],
        ["invalid"],
        [1],
        [object()],
    ],
)
def test_validate_ingestion_result_rejects_non_dictionary_records(
    records: list,
) -> None:
    result = IngestionResult(
        records=records,
        pages_fetched=1,
        records_fetched=len(records),
    )

    with pytest.raises(
        IngestionError,
        match="not a dictionary",
    ):
        validate_ingestion_result(result)


def test_ingest_and_validate_returns_valid_result(
    tmp_path: Path,
) -> None:
    client = make_client(
        pages=[
            make_page(
                [
                    {"id": "1"},
                    {"id": "2"},
                ]
            )
        ]
    )

    result = ingest_and_validate(
        "/orders",
        pipeline_config=make_config(tmp_path),
        client=client,
    )

    assert result == IngestionResult(
        records=[
            {"id": "1"},
            {"id": "2"},
        ],
        pages_fetched=1,
        records_fetched=2,
    )


def test_ingest_and_validate_rejects_invalid_client_output(
    tmp_path: Path,
) -> None:
    client = make_client(
        pages=[
            make_page(
                [
                    {"id": "1"},
                ]
            )
        ]
    )

    with pytest.raises(
        IngestionError,
        match="records_fetched",
    ):
        result = IngestionResult(
            records=[{"id": "1"}],
            pages_fetched=1,
            records_fetched=2,
        )
        validate_ingestion_result(result)

    client.close.assert_not_called()


def test_ingest_and_validate_delegates_to_ingestion_and_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = IngestionResult(
        records=[
            {"id": "1"},
        ],
        pages_fetched=1,
        records_fetched=1,
    )

    ingest_mock = MagicMock(
        return_value=expected,
    )
    validate_mock = MagicMock()

    monkeypatch.setattr(
        "src.ingestion.ingest_api_data",
        ingest_mock,
    )
    monkeypatch.setattr(
        "src.ingestion.validate_ingestion_result",
        validate_mock,
    )

    result = ingest_and_validate(
        "/orders",
        pipeline_config=make_config(tmp_path),
        extra_params={"status": "completed"},
    )

    assert result is expected

    ingest_mock.assert_called_once_with(
        "/orders",
        pipeline_config=make_config(tmp_path),
        client=None,
        extra_params={"status": "completed"},
    )
    validate_mock.assert_called_once_with(expected)


def test_ingestion_functions_use_configured_page_size(
    tmp_path: Path,
) -> None:
    client = make_client(
        pages=[
            make_page(
                [{"id": "1"}],
            )
        ]
    )
    pipeline_config = make_config(
        tmp_path,
        api_page_size=100,
    )

    ingest_api_data(
        "/orders",
        pipeline_config=pipeline_config,
        client=client,
    )

    client.iter_pages.assert_called_once_with(
        "/orders",
        page_size=100,
        extra_params=None,
    )


def test_iter_api_records_returns_iterator(
    tmp_path: Path,
) -> None:
    client = make_client(
        records=[
            {"id": "1"},
        ]
    )

    result = iter_api_records(
        "/orders",
        pipeline_config=make_config(tmp_path),
        client=client,
    )

    assert isinstance(
        result,
        Iterator,
    )

    assert list(result) == [{"id": "1"}]


def test_ingest_pages_returns_iterator(
    tmp_path: Path,
) -> None:
    client = make_client(
        pages=[
            make_page(
                [{"id": "1"}],
            )
        ]
    )

    result = ingest_pages(
        "/orders",
        pipeline_config=make_config(tmp_path),
        client=client,
    )

    assert isinstance(
        result,
        Iterator,
    )

    assert list(result) == [[{"id": "1"}]]