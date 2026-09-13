from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import pandas as pd

from .config import PipelineConfig, config
from .ingestion import IngestionError, IngestionResult, ingest_and_validate
from .logging_config import configure_logging
from .normalization import NormalizationError, NormalizationResult, normalize_api_records
from .storage import StorageError, write_csv, write_json, write_parquet
from .transformation import TransformationError, TransformationResult, transform_records
from .validation import ValidationError, assert_valid, validate_transformed_data


logger = logging.getLogger("api_data_pipeline.pipeline")


class PipelineError(RuntimeError):
    """Raised when the API data processing pipeline cannot complete safely."""


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """Represent the outputs and metrics produced by a pipeline run."""

    ingestion: IngestionResult
    normalization: NormalizationResult
    transformation: TransformationResult


def _write_pipeline_outputs(
    normalized: NormalizationResult,
    transformed: TransformationResult,
    *,
    pipeline_config: PipelineConfig,
) -> None:
    """Persist raw, normalized, rejected, and reporting outputs."""
    try:
        write_json(
            normalized.normalized.to_dict(
                orient="records"
            ),
            pipeline_config.raw_response_path,
            atomic=pipeline_config.atomic_writes,
        )

        write_parquet(
            transformed.data,
            pipeline_config.normalized_data_path,
            atomic=pipeline_config.atomic_writes,
        )

        write_csv(
            normalized.rejected,
            pipeline_config.rejected_records_path,
            atomic=pipeline_config.atomic_writes,
        )

        processing_report = pd.DataFrame(
            [
                {
                    "input_rows": transformed.metrics.get(
                        "input_rows",
                        0,
                    ),
                    "output_rows": transformed.metrics.get(
                        "output_rows",
                        0,
                    ),
                    "rows_removed": transformed.metrics.get(
                        "rows_removed",
                        0,
                    ),
                    "numeric_total": transformed.metrics.get(
                        "numeric_total",
                        0.0,
                    ),
                    "records_fetched": (
                        transformed.metrics.get(
                            "input_rows",
                            0,
                        )
                    ),
                }
            ]
        )

        write_parquet(
            processing_report,
            pipeline_config.processing_report_path,
            atomic=pipeline_config.atomic_writes,
        )
    except StorageError:
        raise
    except (OSError, TypeError, ValueError) as exc:
        raise PipelineError(
            "Failed to persist pipeline outputs."
        ) from exc


def _normalize_ingestion(
    ingestion: IngestionResult,
    *,
    pipeline_config: PipelineConfig,
) -> NormalizationResult:
    """Normalize records returned by the API."""
    try:
        return normalize_api_records(
            ingestion.records,
            required_columns=(),
            timestamp_columns=(
                "created_at",
                "updated_at",
                "timestamp",
            ),
            numeric_columns=(
                "amount",
                "quantity",
            ),
            timezone=pipeline_config.api_response_timezone,
        )
    except NormalizationError:
        raise
    except (TypeError, ValueError, KeyError) as exc:
        raise PipelineError(
            "API response normalization failed."
        ) from exc


def _transform_normalized_data(
    normalized: NormalizationResult,
) -> TransformationResult:
    """Apply reusable business transformations to normalized records."""
    if normalized.normalized.empty:
        return TransformationResult(
            data=normalized.normalized.copy(),
            metrics={
                "input_rows": 0,
                "output_rows": 0,
                "rows_removed": 0,
            },
        )

    frame = normalized.normalized

    timestamp_column = (
        "created_at"
        if "created_at" in frame.columns
        else (
            "updated_at"
            if "updated_at" in frame.columns
            else None
        )
    )

    status_column = (
        "status"
        if "status" in frame.columns
        else None
    )

    numeric_column = None
    for candidate in ("amount", "total", "value", "price"):
        if candidate in frame.columns:
            numeric_column = candidate
            break

    id_columns: tuple[str, ...] = tuple(
        column
        for column in (
            "id",
            "order_id",
            "event_id",
            "transaction_id",
        )
        if column in frame.columns
    )

    try:
        return transform_records(
            frame,
            id_columns=id_columns[:1],
            timestamp_column=timestamp_column,
            status_column=status_column,
            numeric_column=numeric_column,
        )
    except TransformationError:
        raise
    except (TypeError, ValueError, KeyError) as exc:
        raise PipelineError(
            "API response transformation failed."
        ) from exc


def _validate_transformation(
    transformed: TransformationResult,
) -> None:
    """Validate the transformed dataset before publication."""
    required_columns = tuple(
        column
        for column in (
            "id",
            "order_id",
            "event_id",
            "transaction_id",
        )
        if column in transformed.data.columns
    )

    numeric_columns = tuple(
        column
        for column in (
            "amount",
            "quantity",
            "value",
            "price",
        )
        if column in transformed.data.columns
    )

    datetime_columns = tuple(
        column
        for column in (
            "created_at",
            "updated_at",
            "timestamp",
        )
        if column in transformed.data.columns
    )

    try:
        result = validate_transformed_data(
            transformed.data,
            required_columns=required_columns,
            numeric_columns=numeric_columns,
            datetime_columns=datetime_columns,
        )
        assert_valid(result)
    except ValidationError:
        raise
    except (TypeError, ValueError, KeyError) as exc:
        raise PipelineError(
            "Transformed data validation failed."
        ) from exc


def run_pipeline(
    endpoint: str,
    *,
    pipeline_config: PipelineConfig = config,
    extra_params: dict[str, Any] | None = None,
) -> PipelineResult:
    """Execute API ingestion, normalization, transformation, validation, and storage."""
    configure_logging(
        pipeline_config,
    )

    logger.info(
        "Starting API data processing pipeline for endpoint=%s",
        endpoint,
    )

    if not endpoint.strip():
        raise PipelineError(
            "API endpoint cannot be empty."
        )

    try:
        pipeline_config.ensure_directories()

        logger.info("Fetching records from the API.")

        ingestion = ingest_and_validate(
            endpoint,
            pipeline_config=pipeline_config,
            extra_params=extra_params,
        )

        logger.info(
            "Fetched %d record(s) across %d page(s).",
            ingestion.records_fetched,
            ingestion.pages_fetched,
        )

        logger.info("Normalizing API records.")

        normalized = _normalize_ingestion(
            ingestion,
            pipeline_config=pipeline_config,
        )

        logger.info(
            "Normalization produced %d record(s) and rejected %d.",
            len(normalized.normalized),
            len(normalized.rejected),
        )

        if (
            pipeline_config.fail_on_schema_error
            and normalized.rejected.empty is False
            and pipeline_config.drop_invalid_records is False
        ):
            raise PipelineError(
                "Normalization produced rejected records while strict "
                "schema validation is enabled."
            )

        logger.info("Transforming normalized data.")

        transformation = _transform_normalized_data(
            normalized,
        )

        logger.info(
            "Transformation produced %d output record(s).",
            len(transformation.data),
        )

        _validate_transformation(
            transformation,
        )

        logger.info("Persisting pipeline outputs.")

        _write_pipeline_outputs(
            normalized,
            transformation,
            pipeline_config=pipeline_config,
        )

        logger.info(
            "API data processing pipeline completed successfully.",
        )

        return PipelineResult(
            ingestion=ingestion,
            normalization=normalized,
            transformation=transformation,
        )

    except (
        IngestionError,
        NormalizationError,
        TransformationError,
        ValidationError,
        StorageError,
    ) as exc:
        logger.exception(
            "API data processing pipeline failed.",
        )
        raise PipelineError(
            str(exc)
        ) from exc
    except (
        OSError,
        TypeError,
        ValueError,
        KeyError,
        ImportError,
        pd.errors.PandasError,
    ) as exc:
        logger.exception(
            "Unexpected API data processing pipeline failure.",
        )
        raise PipelineError(
            "API data processing pipeline failed."
        ) from exc


def main(
    endpoint: str,
    *,
    pipeline_config: PipelineConfig = config,
) -> int:
    """Run the pipeline as a programmatic command entry point."""
    try:
        run_pipeline(
            endpoint,
            pipeline_config=pipeline_config,
        )
    except PipelineError as exc:
        logger.error(
            "%s",
            exc,
        )
        return 1

    return 0


__all__ = [
    "PipelineError",
    "PipelineResult",
    "main",
    "run_pipeline",
]


if __name__ == "__main__":
    raise SystemExit(
        main(
            config.api_base_url,
        )
    )

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import pandas as pd

from .config import PipelineConfig, config
from .ingestion import IngestionError, IngestionResult, ingest_and_validate
from .logging_config import configure_logging
from .normalization import NormalizationError, NormalizationResult, normalize_api_records
from .storage import StorageError, write_csv, write_json, write_parquet
from .transformation import TransformationError, TransformationResult, transform_records
from .validation import ValidationError, assert_valid, validate_transformed_data


logger = logging.getLogger("api_data_pipeline.pipeline")


class PipelineError(RuntimeError):
    """Raised when the API data processing pipeline cannot complete safely."""


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """Represent the outputs and metrics produced by a pipeline run."""

    ingestion: IngestionResult
    normalization: NormalizationResult
    transformation: TransformationResult


def _write_pipeline_outputs(
    normalized: NormalizationResult,
    transformed: TransformationResult,
    *,
    pipeline_config: PipelineConfig,
) -> None:
    """Persist raw, normalized, rejected, and reporting outputs."""
    try:
        write_json(
            normalized.normalized.to_dict(
                orient="records"
            ),
            pipeline_config.raw_response_path,
            atomic=pipeline_config.atomic_writes,
        )

        write_parquet(
            transformed.data,
            pipeline_config.normalized_data_path,
            atomic=pipeline_config.atomic_writes,
        )

        write_csv(
            normalized.rejected,
            pipeline_config.rejected_records_path,
            atomic=pipeline_config.atomic_writes,
        )

        processing_report = pd.DataFrame(
            [
                {
                    "input_rows": transformed.metrics.get(
                        "input_rows",
                        0,
                    ),
                    "output_rows": transformed.metrics.get(
                        "output_rows",
                        0,
                    ),
                    "rows_removed": transformed.metrics.get(
                        "rows_removed",
                        0,
                    ),
                    "numeric_total": transformed.metrics.get(
                        "numeric_total",
                        0.0,
                    ),
                    "records_fetched": (
                        transformed.metrics.get(
                            "input_rows",
                            0,
                        )
                    ),
                }
            ]
        )

        write_parquet(
            processing_report,
            pipeline_config.processing_report_path,
            atomic=pipeline_config.atomic_writes,
        )
    except StorageError:
        raise
    except (OSError, TypeError, ValueError) as exc:
        raise PipelineError(
            "Failed to persist pipeline outputs."
        ) from exc


def _normalize_ingestion(
    ingestion: IngestionResult,
    *,
    pipeline_config: PipelineConfig,
) -> NormalizationResult:
    """Normalize records returned by the API."""
    try:
        return normalize_api_records(
            ingestion.records,
            required_columns=(),
            timestamp_columns=(
                "created_at",
                "updated_at",
                "timestamp",
            ),
            numeric_columns=(
                "amount",
                "quantity",
            ),
            timezone=pipeline_config.api_response_timezone,
        )
    except NormalizationError:
        raise
    except (TypeError, ValueError, KeyError) as exc:
        raise PipelineError(
            "API response normalization failed."
        ) from exc


def _transform_normalized_data(
    normalized: NormalizationResult,
) -> TransformationResult:
    """Apply reusable business transformations to normalized records."""
    if normalized.normalized.empty:
        return TransformationResult(
            data=normalized.normalized.copy(),
            metrics={
                "input_rows": 0,
                "output_rows": 0,
                "rows_removed": 0,
            },
        )

    frame = normalized.normalized

    timestamp_column = (
        "created_at"
        if "created_at" in frame.columns
        else (
            "updated_at"
            if "updated_at" in frame.columns
            else None
        )
    )

    status_column = (
        "status"
        if "status" in frame.columns
        else None
    )

    numeric_column = None
    for candidate in ("amount", "total", "value", "price"):
        if candidate in frame.columns:
            numeric_column = candidate
            break

    id_columns: tuple[str, ...] = tuple(
        column
        for column in (
            "id",
            "order_id",
            "event_id",
            "transaction_id",
        )
        if column in frame.columns
    )

    try:
        return transform_records(
            frame,
            id_columns=id_columns[:1],
            timestamp_column=timestamp_column,
            status_column=status_column,
            numeric_column=numeric_column,
        )
    except TransformationError:
        raise
    except (TypeError, ValueError, KeyError) as exc:
        raise PipelineError(
            "API response transformation failed."
        ) from exc


def _validate_transformation(
    transformed: TransformationResult,
) -> None:
    """Validate the transformed dataset before publication."""
    required_columns = tuple(
        column
        for column in (
            "id",
            "order_id",
            "event_id",
            "transaction_id",
        )
        if column in transformed.data.columns
    )

    numeric_columns = tuple(
        column
        for column in (
            "amount",
            "quantity",
            "value",
            "price",
        )
        if column in transformed.data.columns
    )

    datetime_columns = tuple(
        column
        for column in (
            "created_at",
            "updated_at",
            "timestamp",
        )
        if column in transformed.data.columns
    )

    try:
        result = validate_transformed_data(
            transformed.data,
            required_columns=required_columns,
            numeric_columns=numeric_columns,
            datetime_columns=datetime_columns,
        )
        assert_valid(result)
    except ValidationError:
        raise
    except (TypeError, ValueError, KeyError) as exc:
        raise PipelineError(
            "Transformed data validation failed."
        ) from exc


def run_pipeline(
    endpoint: str,
    *,
    pipeline_config: PipelineConfig = config,
    extra_params: dict[str, Any] | None = None,
) -> PipelineResult:
    """Execute API ingestion, normalization, transformation, validation, and storage."""
    configure_logging(
        pipeline_config,
    )

    logger.info(
        "Starting API data processing pipeline for endpoint=%s",
        endpoint,
    )

    if not endpoint.strip():
        raise PipelineError(
            "API endpoint cannot be empty."
        )

    try:
        pipeline_config.ensure_directories()

        logger.info("Fetching records from the API.")

        ingestion = ingest_and_validate(
            endpoint,
            pipeline_config=pipeline_config,
            extra_params=extra_params,
        )

        logger.info(
            "Fetched %d record(s) across %d page(s).",
            ingestion.records_fetched,
            ingestion.pages_fetched,
        )

        logger.info("Normalizing API records.")

        normalized = _normalize_ingestion(
            ingestion,
            pipeline_config=pipeline_config,
        )

        logger.info(
            "Normalization produced %d record(s) and rejected %d.",
            len(normalized.normalized),
            len(normalized.rejected),
        )

        if (
            pipeline_config.fail_on_schema_error
            and normalized.rejected.empty is False
            and pipeline_config.drop_invalid_records is False
        ):
            raise PipelineError(
                "Normalization produced rejected records while strict "
                "schema validation is enabled."
            )

        logger.info("Transforming normalized data.")

        transformation = _transform_normalized_data(
            normalized,
        )

        logger.info(
            "Transformation produced %d output record(s).",
            len(transformation.data),
        )

        _validate_transformation(
            transformation,
        )

        logger.info("Persisting pipeline outputs.")

        _write_pipeline_outputs(
            normalized,
            transformation,
            pipeline_config=pipeline_config,
        )

        logger.info(
            "API data processing pipeline completed successfully.",
        )

        return PipelineResult(
            ingestion=ingestion,
            normalization=normalized,
            transformation=transformation,
        )

    except (
        IngestionError,
        NormalizationError,
        TransformationError,
        ValidationError,
        StorageError,
    ) as exc:
        logger.exception(
            "API data processing pipeline failed.",
        )
        raise PipelineError(
            str(exc)
        ) from exc
    except (
        OSError,
        TypeError,
        ValueError,
        KeyError,
        ImportError,
        pd.errors.PandasError,
    ) as exc:
        logger.exception(
            "Unexpected API data processing pipeline failure.",
        )
        raise PipelineError(
            "API data processing pipeline failed."
        ) from exc


def main(
    endpoint: str,
    *,
    pipeline_config: PipelineConfig = config,
) -> int:
    """Run the pipeline as a programmatic command entry point."""
    try:
        run_pipeline(
            endpoint,
            pipeline_config=pipeline_config,
        )
    except PipelineError as exc:
        logger.error(
            "%s",
            exc,
        )
        return 1

    return 0


__all__ = [
    "PipelineError",
    "PipelineResult",
    "main",
    "run_pipeline",
]


if __name__ == "__main__":
    raise SystemExit(
        main(
            config.api_base_url,
        )
    )