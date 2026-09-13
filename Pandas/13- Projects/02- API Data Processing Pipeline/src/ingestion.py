from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any

from .client import APIClient
from .config import PipelineConfig, config


class IngestionError(RuntimeError):
    """Raised when API ingestion cannot complete safely."""


@dataclass(frozen=True, slots=True)
class IngestionResult:
    """Represent records ingested from the source API."""

    records: list[dict[str, Any]]
    pages_fetched: int
    records_fetched: int


def iter_api_records(
    endpoint: str,
    *,
    pipeline_config: PipelineConfig = config,
    client: APIClient | None = None,
    extra_params: Mapping[str, Any] | None = None,
) -> Iterator[dict[str, Any]]:
    """Yield API records incrementally through the configured client."""
    owns_client = client is None
    api_client = client or APIClient(pipeline_config)

    try:
        try:
            yield from api_client.iter_records(
                endpoint,
                page_size=pipeline_config.api_page_size,
                extra_params=extra_params,
            )
        except Exception as exc:
            if isinstance(exc, IngestionError):
                raise
            raise IngestionError(
                f"Failed to ingest API records from endpoint: {endpoint}"
            ) from exc
    finally:
        if owns_client:
            api_client.close()


def ingest_api_data(
    endpoint: str,
    *,
    pipeline_config: PipelineConfig = config,
    client: APIClient | None = None,
    extra_params: Mapping[str, Any] | None = None,
) -> IngestionResult:
    """Fetch all API records into memory with ingestion statistics."""
    records: list[dict[str, Any]] = []
    pages_fetched = 0

    owns_client = client is None
    api_client = client or APIClient(pipeline_config)

    try:
        try:
            for page in api_client.iter_pages(
                endpoint,
                page_size=pipeline_config.api_page_size,
                extra_params=extra_params,
            ):
                pages_fetched += 1
                records.extend(page.items)
        except Exception as exc:
            if isinstance(exc, IngestionError):
                raise
            raise IngestionError(
                f"Failed to ingest API data from endpoint: {endpoint}"
            ) from exc
    finally:
        if owns_client:
            api_client.close()

    return IngestionResult(
        records=records,
        pages_fetched=pages_fetched,
        records_fetched=len(records),
    )


def ingest_pages(
    endpoint: str,
    *,
    pipeline_config: PipelineConfig = config,
    client: APIClient | None = None,
    extra_params: Mapping[str, Any] | None = None,
) -> Iterator[list[dict[str, Any]]]:
    """Yield records page-by-page without accumulating the complete dataset."""
    owns_client = client is None
    api_client = client or APIClient(pipeline_config)

    try:
        try:
            for page in api_client.iter_pages(
                endpoint,
                page_size=pipeline_config.api_page_size,
                extra_params=extra_params,
            ):
                yield page.items
        except Exception as exc:
            if isinstance(exc, IngestionError):
                raise
            raise IngestionError(
                f"Failed to ingest API pages from endpoint: {endpoint}"
            ) from exc
    finally:
        if owns_client:
            api_client.close()


def validate_ingestion_result(
    result: IngestionResult,
) -> None:
    """Validate internal consistency of ingestion statistics."""
    if result.pages_fetched < 0:
        raise IngestionError(
            "pages_fetched cannot be negative."
        )

    if result.records_fetched < 0:
        raise IngestionError(
            "records_fetched cannot be negative."
        )

    if result.records_fetched != len(result.records):
        raise IngestionError(
            "records_fetched does not match the number of records."
        )

    for index, record in enumerate(result.records):
        if not isinstance(record, dict):
            raise IngestionError(
                f"Ingested record at index {index} is not a dictionary."
            )


def ingest_and_validate(
    endpoint: str,
    *,
    pipeline_config: PipelineConfig = config,
    client: APIClient | None = None,
    extra_params: Mapping[str, Any] | None = None,
) -> IngestionResult:
    """Ingest API records and validate the resulting dataset contract."""
    result = ingest_api_data(
        endpoint,
        pipeline_config=pipeline_config,
        client=client,
        extra_params=extra_params,
    )
    validate_ingestion_result(result)
    return result


__all__ = [
    "IngestionError",
    "IngestionResult",
    "ingest_and_validate",
    "ingest_api_data",
    "ingest_pages",
    "iter_api_records",
    "validate_ingestion_result",
]

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any

from .client import APIClient
from .config import PipelineConfig, config


class IngestionError(RuntimeError):
    """Raised when API ingestion cannot complete safely."""


@dataclass(frozen=True, slots=True)
class IngestionResult:
    """Represent records ingested from the source API."""

    records: list[dict[str, Any]]
    pages_fetched: int
    records_fetched: int


def iter_api_records(
    endpoint: str,
    *,
    pipeline_config: PipelineConfig = config,
    client: APIClient | None = None,
    extra_params: Mapping[str, Any] | None = None,
) -> Iterator[dict[str, Any]]:
    """Yield API records incrementally through the configured client."""
    owns_client = client is None
    api_client = client or APIClient(pipeline_config)

    try:
        try:
            yield from api_client.iter_records(
                endpoint,
                page_size=pipeline_config.api_page_size,
                extra_params=extra_params,
            )
        except Exception as exc:
            if isinstance(exc, IngestionError):
                raise
            raise IngestionError(
                f"Failed to ingest API records from endpoint: {endpoint}"
            ) from exc
    finally:
        if owns_client:
            api_client.close()


def ingest_api_data(
    endpoint: str,
    *,
    pipeline_config: PipelineConfig = config,
    client: APIClient | None = None,
    extra_params: Mapping[str, Any] | None = None,
) -> IngestionResult:
    """Fetch all API records into memory with ingestion statistics."""
    records: list[dict[str, Any]] = []
    pages_fetched = 0

    owns_client = client is None
    api_client = client or APIClient(pipeline_config)

    try:
        try:
            for page in api_client.iter_pages(
                endpoint,
                page_size=pipeline_config.api_page_size,
                extra_params=extra_params,
            ):
                pages_fetched += 1
                records.extend(page.items)
        except Exception as exc:
            if isinstance(exc, IngestionError):
                raise
            raise IngestionError(
                f"Failed to ingest API data from endpoint: {endpoint}"
            ) from exc
    finally:
        if owns_client:
            api_client.close()

    return IngestionResult(
        records=records,
        pages_fetched=pages_fetched,
        records_fetched=len(records),
    )


def ingest_pages(
    endpoint: str,
    *,
    pipeline_config: PipelineConfig = config,
    client: APIClient | None = None,
    extra_params: Mapping[str, Any] | None = None,
) -> Iterator[list[dict[str, Any]]]:
    """Yield records page-by-page without accumulating the complete dataset."""
    owns_client = client is None
    api_client = client or APIClient(pipeline_config)

    try:
        try:
            for page in api_client.iter_pages(
                endpoint,
                page_size=pipeline_config.api_page_size,
                extra_params=extra_params,
            ):
                yield page.items
        except Exception as exc:
            if isinstance(exc, IngestionError):
                raise
            raise IngestionError(
                f"Failed to ingest API pages from endpoint: {endpoint}"
            ) from exc
    finally:
        if owns_client:
            api_client.close()


def validate_ingestion_result(
    result: IngestionResult,
) -> None:
    """Validate internal consistency of ingestion statistics."""
    if result.pages_fetched < 0:
        raise IngestionError(
            "pages_fetched cannot be negative."
        )

    if result.records_fetched < 0:
        raise IngestionError(
            "records_fetched cannot be negative."
        )

    if result.records_fetched != len(result.records):
        raise IngestionError(
            "records_fetched does not match the number of records."
        )

    for index, record in enumerate(result.records):
        if not isinstance(record, dict):
            raise IngestionError(
                f"Ingested record at index {index} is not a dictionary."
            )


def ingest_and_validate(
    endpoint: str,
    *,
    pipeline_config: PipelineConfig = config,
    client: APIClient | None = None,
    extra_params: Mapping[str, Any] | None = None,
) -> IngestionResult:
    """Ingest API records and validate the resulting dataset contract."""
    result = ingest_api_data(
        endpoint,
        pipeline_config=pipeline_config,
        client=client,
        extra_params=extra_params,
    )
    validate_ingestion_result(result)
    return result


__all__ = [
    "IngestionError",
    "IngestionResult",
    "ingest_and_validate",
    "ingest_api_data",
    "ingest_pages",
    "iter_api_records",
    "validate_ingestion_result",
]