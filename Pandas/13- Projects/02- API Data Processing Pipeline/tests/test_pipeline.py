from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

from src.config import PipelineConfig
from src.ingestion import IngestionError, IngestionResult
from src.normalization import NormalizationError, NormalizationResult
from src.pipeline import (
    PipelineError,
    PipelineResult,
    _transform_normalized_data,
    _validate_transformation,
    _write_pipeline_outputs,
    main,
    run_pipeline,
)
from src.storage import StorageError
from src.transformation import TransformationError, TransformationResult
from src.validation import ValidationError, ValidationResult


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
        "api_base_url": "https://api.example.com/orders",
        "api_page_size": 2,
        "api_max_pages": 10,
        "api_timeout_seconds": 30.0,
        "api_connect_timeout_seconds": 10.0,
        "api_read_timeout_seconds": 30.0,
        "api_max_retries": 0,
        "api_backoff_factor": 0.0,
        "api_response_timezone": "UTC",
        "drop_invalid_records": False,
        "fail_on_http_error": True,
        "fail_on_schema_error": True,
        "create_directories": True,
        "atomic_writes": True,
        "log_level": "CRITICAL",
    }
    values.update(overrides)
    return PipelineConfig(**values)


def make_ingestion_result(
    records: list[dict] | None = None,
    *,
    pages_fetched: int | None = None,
) -> IngestionResult:
    """Create a deterministic ingestion result fixture."""
    records = records or [
        {
            "id": "order-1",
            "status": "completed",
            "amount": "100.00",
            "created_at": "2026-01-01T10:00:00Z",
        },
        {
            "id": "order-2",
            "status": "pending",
            "amount": "200.00",
            "created_at": "2026-01-02T10:00:00Z",
        },
    ]

    return IngestionResult(
        records=records,
        pages_fetched=(
            pages_fetched
            if pages_fetched is not None
            else len(records)
        ),
        records_fetched=len(records),
    )


def make_normalization_result(
    *,
    normalized: pd.DataFrame | None = None,
    rejected: pd.DataFrame | None = None,
    input_rows: int = 2,
    normalized_rows: int = 2,
    rejected_rows: int = 0,
) -> NormalizationResult:
    """Create a deterministic normalization result fixture."""
    normalized = (
        normalized
        if normalized is not None
        else pd.DataFrame(
            [
                {
                    "id": "order-1",
                    "status": "completed",
                    "amount": 100.0,
                    "created_at": pd.Timestamp(
                        "2026-01-01T10:00:00Z"
                    ),
                },
                {
                    "id": "order-2",
                    "status": "pending",
                    "amount": 200.0,
                    "created_at": pd.Timestamp(
                        "2026-01-02T10:00:00Z"
                    ),
                },
            ]
        )
    )

    rejected = (
        rejected
        if rejected is not None
        else pd.DataFrame()
    )

    return NormalizationResult(
        normalized=normalized,
        rejected=rejected,
        input_rows=input_rows,
        normalized_rows=normalized_rows,
        rejected_rows=rejected_rows,
    )


def make_transformation_result(
    *,
    data: pd.DataFrame | None = None,
    metrics: dict[str, int | float] | None = None,
) -> TransformationResult:
    """Create a deterministic transformation result fixture."""
    data = (
        data
        if data is not None
        else pd.DataFrame(
            [
                {
                    "id": "order-1",
                    "amount": 100.0,
                },
                {
                    "id": "order-2",
                    "amount": 200.0,
                },
            ]
        )
    )

    metrics = (
        metrics
        if metrics is not None
        else {
            "input_rows": 2,
            "output_rows": 2,
            "rows_removed": 0,
            "numeric_total": 300.0,
            "aggregation_rows": 2,
        }
    )

    return TransformationResult(
        data=data,
        metrics=metrics,
    )


def test_run_pipeline_returns_pipeline_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ingestion = make_ingestion_result()
    normalization = make_normalization_result()
    transformation = make_transformation_result()

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(return_value=ingestion),
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        MagicMock(return_value=normalization),
    )
    monkeypatch.setattr(
        "src.pipeline.transform_records",
        MagicMock(return_value=transformation),
    )
    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        MagicMock(return_value=ValidationResult()),
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline._write_pipeline_outputs",
        MagicMock(),
    )

    pipeline_config = make_config(tmp_path)

    result = run_pipeline(
        "/orders",
        pipeline_config=pipeline_config,
    )

    assert isinstance(result, PipelineResult)
    assert result.ingestion is ingestion
    assert result.normalization is normalization
    assert result.transformation is transformation


def test_run_pipeline_configures_logging(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_logging = MagicMock()

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        configure_logging,
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(
            return_value=make_ingestion_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        MagicMock(
            return_value=make_normalization_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.transform_records",
        MagicMock(
            return_value=make_transformation_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        MagicMock(
            return_value=ValidationResult(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline._write_pipeline_outputs",
        MagicMock(),
    )

    pipeline_config = make_config(tmp_path)

    run_pipeline(
        "/orders",
        pipeline_config=pipeline_config,
    )

    configure_logging.assert_called_once_with(
        pipeline_config,
    )


def test_run_pipeline_ensures_directories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ensure_directories = MagicMock()

    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        ensure_directories,
    )
    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(
            return_value=make_ingestion_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        MagicMock(
            return_value=make_normalization_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.transform_records",
        MagicMock(
            return_value=make_transformation_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        MagicMock(
            return_value=ValidationResult(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline._write_pipeline_outputs",
        MagicMock(),
    )

    pipeline_config = make_config(tmp_path)

    run_pipeline(
        "/orders",
        pipeline_config=pipeline_config,
    )

    ensure_directories.assert_called_once()


@pytest.mark.parametrize(
    "endpoint",
    [
        "",
        " ",
        "\t",
    ],
)
def test_run_pipeline_rejects_empty_endpoint(
    tmp_path: Path,
    endpoint: str,
) -> None:
    pipeline_config = make_config(tmp_path)

    with pytest.raises(
        PipelineError,
        match="endpoint",
    ):
        run_pipeline(
            endpoint,
            pipeline_config=pipeline_config,
        )


def test_run_pipeline_passes_endpoint_and_params_to_ingestion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ingestion_mock = MagicMock(
        return_value=make_ingestion_result(),
    )

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        ingestion_mock,
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        MagicMock(
            return_value=make_normalization_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.transform_records",
        MagicMock(
            return_value=make_transformation_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        MagicMock(
            return_value=ValidationResult(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline._write_pipeline_outputs",
        MagicMock(),
    )

    pipeline_config = make_config(tmp_path)
    extra_params = {
        "status": "completed",
        "region": "apac",
    }

    run_pipeline(
        "/orders",
        pipeline_config=pipeline_config,
        extra_params=extra_params,
    )

    ingestion_mock.assert_called_once_with(
        "/orders",
        pipeline_config=pipeline_config,
        extra_params=extra_params,
    )


def test_run_pipeline_normalizes_expected_api_fields(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    normalize_mock = MagicMock(
        return_value=make_normalization_result(),
    )

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(
            return_value=make_ingestion_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        normalize_mock,
    )
    monkeypatch.setattr(
        "src.pipeline.transform_records",
        MagicMock(
            return_value=make_transformation_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        MagicMock(
            return_value=ValidationResult(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline._write_pipeline_outputs",
        MagicMock(),
    )

    pipeline_config = make_config(tmp_path)
    ingestion = make_ingestion_result()

    run_pipeline(
        "/orders",
        pipeline_config=pipeline_config,
    )

    normalize_mock.assert_called_once_with(
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


def test_run_pipeline_uses_transformation_result_for_validation_and_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transformation = make_transformation_result()

    transform_mock = MagicMock(
        return_value=transformation,
    )
    validate_mock = MagicMock(
        return_value=ValidationResult(),
    )
    write_mock = MagicMock()

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(
            return_value=make_ingestion_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        MagicMock(
            return_value=make_normalization_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.transform_records",
        transform_mock,
    )
    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        validate_mock,
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline._write_pipeline_outputs",
        write_mock,
    )

    result = run_pipeline(
        "/orders",
        pipeline_config=make_config(tmp_path),
    )

    assert result.transformation is transformation
    validate_mock.assert_called_once()
    assert validate_mock.call_args.args[0] is transformation.data
    write_mock.assert_called_once()


def test_run_pipeline_calls_assert_valid_on_validation_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    validation_result = ValidationResult()
    assert_valid_mock = MagicMock()

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(
            return_value=make_ingestion_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        MagicMock(
            return_value=make_normalization_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.transform_records",
        MagicMock(
            return_value=make_transformation_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        MagicMock(
            return_value=validation_result,
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        assert_valid_mock,
    )
    monkeypatch.setattr(
        "src.pipeline._write_pipeline_outputs",
        MagicMock(),
    )

    run_pipeline(
        "/orders",
        pipeline_config=make_config(tmp_path),
    )

    assert_valid_mock.assert_called_once_with(
        validation_result,
    )


def test_run_pipeline_rejects_invalid_rows_when_schema_validation_is_strict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    normalization = make_normalization_result(
        normalized=pd.DataFrame(
            [
                {
                    "id": "order-1",
                    "amount": 100.0,
                }
            ]
        ),
        rejected=pd.DataFrame(
            [
                {
                    "id": None,
                    "amount": 200.0,
                }
            ]
        ),
        input_rows=2,
        normalized_rows=1,
        rejected_rows=1,
    )

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(
            return_value=make_ingestion_result(
                [
                    {"id": "order-1"},
                    {"id": None},
                ]
            ),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        MagicMock(return_value=normalization),
    )

    pipeline_config = make_config(
        tmp_path,
        fail_on_schema_error=True,
        drop_invalid_records=False,
    )

    with pytest.raises(
        PipelineError,
        match="schema",
    ):
        run_pipeline(
            "/orders",
            pipeline_config=pipeline_config,
        )


def test_run_pipeline_allows_rejected_rows_when_configured_to_drop_invalid_records(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    normalization = make_normalization_result(
        normalized=pd.DataFrame(
            [
                {
                    "id": "order-1",
                    "amount": 100.0,
                }
            ]
        ),
        rejected=pd.DataFrame(
            [
                {
                    "id": None,
                    "amount": 200.0,
                }
            ]
        ),
        input_rows=2,
        normalized_rows=1,
        rejected_rows=1,
    )

    transformation = make_transformation_result(
        data=pd.DataFrame(
            [
                {
                    "id": "order-1",
                    "amount": 100.0,
                }
            ]
        ),
        metrics={
            "input_rows": 1,
            "output_rows": 1,
            "rows_removed": 0,
            "numeric_total": 100.0,
        },
    )

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(
            return_value=make_ingestion_result(
                [
                    {"id": "order-1"},
                    {"id": None},
                ]
            ),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        MagicMock(
            return_value=normalization,
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.transform_records",
        MagicMock(
            return_value=transformation,
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        MagicMock(
            return_value=ValidationResult(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        MagicMock(),
    )
    write_mock = MagicMock()
    monkeypatch.setattr(
        "src.pipeline._write_pipeline_outputs",
        write_mock,
    )

    result = run_pipeline(
        "/orders",
        pipeline_config=make_config(
            tmp_path,
            fail_on_schema_error=True,
            drop_invalid_records=True,
        ),
    )

    assert result.normalization is normalization
    assert result.transformation is transformation
    write_mock.assert_called_once()


def test_run_pipeline_wraps_ingestion_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = IngestionError(
        "API unavailable",
    )

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(side_effect=expected),
    )

    with pytest.raises(
        PipelineError,
        match="ingestion",
    ) as exc_info:
        run_pipeline(
            "/orders",
            pipeline_config=make_config(tmp_path),
        )

    assert exc_info.value.__cause__ is expected


def test_run_pipeline_wraps_normalization_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = NormalizationError(
        "invalid payload",
    )

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(
            return_value=make_ingestion_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        MagicMock(side_effect=expected),
    )

    with pytest.raises(
        PipelineError,
        match="normalization",
    ) as exc_info:
        run_pipeline(
            "/orders",
            pipeline_config=make_config(tmp_path),
        )

    assert exc_info.value.__cause__ is expected


def test_run_pipeline_wraps_transformation_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = TransformationError(
        "invalid transformation",
    )

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(
            return_value=make_ingestion_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        MagicMock(
            return_value=make_normalization_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.transform_records",
        MagicMock(side_effect=expected),
    )

    with pytest.raises(
        PipelineError,
        match="transformation",
    ) as exc_info:
        run_pipeline(
            "/orders",
            pipeline_config=make_config(tmp_path),
        )

    assert exc_info.value.__cause__ is expected


def test_run_pipeline_wraps_validation_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = ValidationError(
        "transformed data is invalid",
    )

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(
            return_value=make_ingestion_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        MagicMock(
            return_value=make_normalization_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.transform_records",
        MagicMock(
            return_value=make_transformation_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        MagicMock(
            return_value=ValidationResult(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        MagicMock(side_effect=expected),
    )

    with pytest.raises(
        PipelineError,
        match="validation",
    ) as exc_info:
        run_pipeline(
            "/orders",
            pipeline_config=make_config(tmp_path),
        )

    assert exc_info.value.__cause__ is expected


def test_run_pipeline_wraps_storage_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = StorageError(
        "failed to write output",
    )

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(
            return_value=make_ingestion_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        MagicMock(
            return_value=make_normalization_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.transform_records",
        MagicMock(
            return_value=make_transformation_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        MagicMock(
            return_value=ValidationResult(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline._write_pipeline_outputs",
        MagicMock(side_effect=expected),
    )

    with pytest.raises(
        PipelineError,
        match="storage",
    ) as exc_info:
        run_pipeline(
            "/orders",
            pipeline_config=make_config(tmp_path),
        )

    assert exc_info.value.__cause__ is expected


def test_transform_normalized_data_returns_empty_result_for_empty_frame() -> None:
    normalized = make_normalization_result(
        normalized=pd.DataFrame(
            columns=[
                "id",
                "amount",
            ]
        ),
        rejected=pd.DataFrame(),
        input_rows=0,
        normalized_rows=0,
        rejected_rows=0,
    )

    result = _transform_normalized_data(
        normalized,
    )

    assert isinstance(
        result,
        TransformationResult,
    )
    assert result.data.empty
    assert result.metrics["input_rows"] == 0
    assert result.metrics["output_rows"] == 0


def test_transform_normalized_data_selects_created_at_when_available() -> None:
    normalized = make_normalization_result(
        normalized=pd.DataFrame(
            [
                {
                    "id": "order-1",
                    "amount": 100.0,
                    "created_at": pd.Timestamp(
                        "2026-01-01T10:00:00Z"
                    ),
                }
            ]
        )
    )

    result = _transform_normalized_data(
        normalized,
    )

    assert "event_year" in result.data.columns
    assert result.data.loc[0, "event_year"] == 2026


def test_transform_normalized_data_falls_back_to_updated_at() -> None:
    normalized = make_normalization_result(
        normalized=pd.DataFrame(
            [
                {
                    "id": "order-1",
                    "amount": 100.0,
                    "updated_at": pd.Timestamp(
                        "2026-02-01T10:00:00Z"
                    ),
                }
            ]
        )
    )

    result = _transform_normalized_data(
        normalized,
    )

    assert "event_month" in result.data.columns
    assert result.data.loc[0, "event_month"] == 2


def test_transform_normalized_data_detects_status_column() -> None:
    normalized = make_normalization_result(
        normalized=pd.DataFrame(
            [
                {
                    "id": "order-1",
                    "status": "completed",
                    "amount": 100.0,
                }
            ]
        )
    )

    result = _transform_normalized_data(
        normalized,
    )

    assert result.data.loc[0, "is_completed"] is True


def test_transform_normalized_data_detects_numeric_value_column() -> None:
    normalized = make_normalization_result(
        normalized=pd.DataFrame(
            [
                {
                    "id": "order-1",
                    "value": "100.00",
                }
            ]
        )
    )

    result = _transform_normalized_data(
        normalized,
    )

    assert result.data.loc[0, "value"] == 100.0


def test_transform_normalized_data_detects_transaction_id_identifier() -> None:
    normalized = make_normalization_result(
        normalized=pd.DataFrame(
            [
                {
                    "transaction_id": "txn-1",
                    "amount": 100.0,
                },
                {
                    "transaction_id": "txn-2",
                    "amount": 200.0,
                },
            ]
        )
    )

    result = _transform_normalized_data(
        normalized,
    )

    assert result.data["transaction_id"].tolist() == [
        "txn-1",
        "txn-2",
    ]


def test_validate_transformation_returns_validation_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    validation_result = ValidationResult()

    validate_mock = MagicMock(
        return_value=validation_result,
    )
    assert_mock = MagicMock()

    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        validate_mock,
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        assert_mock,
    )

    frame = pd.DataFrame(
        [
            {
                "id": "order-1",
                "amount": 100.0,
            }
        ]
    )

    _validate_transformation(
        frame,
    )

    assert_mock.assert_called_once_with(
        validation_result,
    )


def test_validate_transformation_detects_present_identifier_columns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    validate_mock = MagicMock(
        return_value=ValidationResult(),
    )
    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        validate_mock,
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        MagicMock(),
    )

    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "amount": 100.0,
            }
        ]
    )

    _validate_transformation(
        frame,
    )

    kwargs = validate_mock.call_args.kwargs

    assert kwargs["id_columns"] == ("order_id",)
    assert kwargs["numeric_columns"] == ("amount",)


def test_validate_transformation_detects_datetime_columns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    validate_mock = MagicMock(
        return_value=ValidationResult(),
    )
    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        validate_mock,
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        MagicMock(),
    )

    frame = pd.DataFrame(
        [
            {
                "id": "order-1",
                "created_at": pd.Timestamp(
                    "2026-01-01T10:00:00Z"
                ),
            }
        ]
    )

    _validate_transformation(
        frame,
    )

    kwargs = validate_mock.call_args.kwargs

    assert kwargs["datetime_columns"] == (
        "created_at",
    )


def test_write_pipeline_outputs_persists_expected_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    normalized = make_normalization_result()
    transformed = make_transformation_result()
    pipeline_config = make_config(tmp_path)

    write_json = MagicMock()
    write_parquet = MagicMock()
    write_csv = MagicMock()

    monkeypatch.setattr(
        "src.pipeline.write_json",
        write_json,
    )
    monkeypatch.setattr(
        "src.pipeline.write_parquet",
        write_parquet,
    )
    monkeypatch.setattr(
        "src.pipeline.write_csv",
        write_csv,
    )

    _write_pipeline_outputs(
        normalized,
        transformed,
        pipeline_config=pipeline_config,
    )

    assert write_json.call_count == 1
    assert write_csv.call_count == 1
    assert write_parquet.call_count == 2

    write_json.assert_called_once_with(
        normalized.normalized.to_dict(
            orient="records"
        ),
        pipeline_config.raw_response_path,
        atomic=True,
    )

    write_csv.assert_called_once_with(
        normalized.rejected,
        pipeline_config.rejected_records_path,
        atomic=True,
    )


def test_write_pipeline_outputs_writes_transformed_data_to_expected_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    normalized = make_normalization_result()
    transformed = make_transformation_result()
    pipeline_config = make_config(tmp_path)

    write_parquet = MagicMock()

    monkeypatch.setattr(
        "src.pipeline.write_json",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.write_csv",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.write_parquet",
        write_parquet,
    )

    _write_pipeline_outputs(
        normalized,
        transformed,
        pipeline_config=pipeline_config,
    )

    calls = write_parquet.call_args_list

    assert calls[0].args[0].equals(
        transformed.data
    )
    assert calls[0].args[1] == (
        pipeline_config.normalized_data_path
    )
    assert calls[0].kwargs == {
        "atomic": pipeline_config.atomic_writes,
    }


def test_write_pipeline_outputs_creates_processing_report_from_metrics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    normalized = make_normalization_result()
    transformed = make_transformation_result(
        metrics={
            "input_rows": 10,
            "output_rows": 8,
            "rows_removed": 2,
            "numeric_total": 1234.5,
        }
    )
    pipeline_config = make_config(tmp_path)

    write_parquet = MagicMock()

    monkeypatch.setattr(
        "src.pipeline.write_json",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.write_csv",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.write_parquet",
        write_parquet,
    )

    _write_pipeline_outputs(
        normalized,
        transformed,
        pipeline_config=pipeline_config,
    )

    report_call = write_parquet.call_args_list[-1]

    report = report_call.args[0]

    assert report.loc[0, "input_rows"] == 10
    assert report.loc[0, "output_rows"] == 8
    assert report.loc[0, "rows_removed"] == 2
    assert report.loc[0, "numeric_total"] == 1234.5
    assert report.loc[0, "records_fetched"] == 10


def test_write_pipeline_outputs_honors_atomic_write_configuration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    normalized = make_normalization_result()
    transformed = make_transformation_result()
    pipeline_config = make_config(
        tmp_path,
        atomic_writes=False,
    )

    write_json = MagicMock()
    write_parquet = MagicMock()
    write_csv = MagicMock()

    monkeypatch.setattr(
        "src.pipeline.write_json",
        write_json,
    )
    monkeypatch.setattr(
        "src.pipeline.write_parquet",
        write_parquet,
    )
    monkeypatch.setattr(
        "src.pipeline.write_csv",
        write_csv,
    )

    _write_pipeline_outputs(
        normalized,
        transformed,
        pipeline_config=pipeline_config,
    )

    for call in write_json.call_args_list:
        assert call.kwargs["atomic"] is False

    for call in write_parquet.call_args_list:
        assert call.kwargs["atomic"] is False

    for call in write_csv.call_args_list:
        assert call.kwargs["atomic"] is False


def test_write_pipeline_outputs_wraps_unexpected_storage_exceptions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_json = MagicMock(
        side_effect=OSError("disk full"),
    )

    monkeypatch.setattr(
        "src.pipeline.write_json",
        write_json,
    )
    monkeypatch.setattr(
        "src.pipeline.write_parquet",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.write_csv",
        MagicMock(),
    )

    with pytest.raises(
        PipelineError,
        match="persist pipeline outputs",
    ) as exc_info:
        _write_pipeline_outputs(
            make_normalization_result(),
            make_transformation_result(),
            pipeline_config=make_config(tmp_path),
        )

    assert isinstance(
        exc_info.value.__cause__,
        OSError,
    )


def test_write_pipeline_outputs_preserves_storage_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = StorageError(
        "parquet write failed",
    )

    monkeypatch.setattr(
        "src.pipeline.write_json",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.write_parquet",
        MagicMock(side_effect=expected),
    )
    monkeypatch.setattr(
        "src.pipeline.write_csv",
        MagicMock(),
    )

    with pytest.raises(StorageError) as exc_info:
        _write_pipeline_outputs(
            make_normalization_result(),
            make_transformation_result(),
            pipeline_config=make_config(tmp_path),
        )

    assert exc_info.value is expected


def test_main_returns_zero_when_pipeline_succeeds(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_mock = MagicMock(
        return_value=PipelineResult(
            ingestion=make_ingestion_result(),
            normalization=make_normalization_result(),
            transformation=make_transformation_result(),
        )
    )

    monkeypatch.setattr(
        "src.pipeline.run_pipeline",
        run_mock,
    )

    pipeline_config = make_config(tmp_path)

    exit_code = main(
        "/orders",
        pipeline_config=pipeline_config,
    )

    assert exit_code == 0

    run_mock.assert_called_once_with(
        "/orders",
        pipeline_config=pipeline_config,
    )


def test_main_returns_one_when_pipeline_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_mock = MagicMock(
        side_effect=PipelineError(
            "pipeline failed",
        )
    )

    monkeypatch.setattr(
        "src.pipeline.run_pipeline",
        run_mock,
    )

    exit_code = main(
        "/orders",
        pipeline_config=make_config(tmp_path),
    )

    assert exit_code == 1


def test_main_handles_pipeline_error_without_raising(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "src.pipeline.run_pipeline",
        MagicMock(
            side_effect=PipelineError(
                "controlled failure",
            )
        ),
    )

    assert (
        main(
            "/orders",
            pipeline_config=make_config(tmp_path),
        )
        == 1
    )


def test_pipeline_result_preserves_stage_results() -> None:
    ingestion = make_ingestion_result()
    normalization = make_normalization_result()
    transformation = make_transformation_result()

    result = PipelineResult(
        ingestion=ingestion,
        normalization=normalization,
        transformation=transformation,
    )

    assert result.ingestion is ingestion
    assert result.normalization is normalization
    assert result.transformation is transformation


def test_run_pipeline_does_not_write_outputs_when_validation_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_mock = MagicMock()

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(
            return_value=make_ingestion_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        MagicMock(
            return_value=make_normalization_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.transform_records",
        MagicMock(
            return_value=make_transformation_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        MagicMock(
            return_value=ValidationResult(
                issues=[],
            ),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        MagicMock(
            side_effect=ValidationError(
                "invalid transformed data",
            ),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline._write_pipeline_outputs",
        write_mock,
    )

    with pytest.raises(
        PipelineError,
    ):
        run_pipeline(
            "/orders",
            pipeline_config=make_config(tmp_path),
        )

    write_mock.assert_not_called()


def test_run_pipeline_handles_empty_normalized_dataset(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    normalization = make_normalization_result(
        normalized=pd.DataFrame(),
        rejected=pd.DataFrame(),
        input_rows=0,
        normalized_rows=0,
        rejected_rows=0,
    )
    transformation = TransformationResult(
        data=pd.DataFrame(),
        metrics={
            "input_rows": 0,
            "output_rows": 0,
            "rows_removed": 0,
            "numeric_total": 0.0,
        },
    )

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(
            return_value=make_ingestion_result(
                records=[],
                pages_fetched=0,
            ),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        MagicMock(
            return_value=normalization,
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.transform_records",
        MagicMock(
            return_value=transformation,
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        MagicMock(
            return_value=ValidationResult(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline._write_pipeline_outputs",
        MagicMock(),
    )

    result = run_pipeline(
        "/orders",
        pipeline_config=make_config(
            tmp_path,
            fail_on_schema_error=False,
        ),
    )

    assert result.normalization.normalized.empty
    assert result.transformation.data.empty


def test_run_pipeline_passes_config_timezone_to_normalization(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    normalize_mock = MagicMock(
        return_value=make_normalization_result(),
    )

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(
            return_value=make_ingestion_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        normalize_mock,
    )
    monkeypatch.setattr(
        "src.pipeline.transform_records",
        MagicMock(
            return_value=make_transformation_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        MagicMock(
            return_value=ValidationResult(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline._write_pipeline_outputs",
        MagicMock(),
    )

    pipeline_config = make_config(
        tmp_path,
        api_response_timezone="Asia/Kolkata",
    )

    run_pipeline(
        "/orders",
        pipeline_config=pipeline_config,
    )

    assert (
        normalize_mock.call_args.kwargs["timezone"]
        == "Asia/Kolkata"
    )

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

from src.config import PipelineConfig
from src.ingestion import IngestionError, IngestionResult
from src.normalization import NormalizationError, NormalizationResult
from src.pipeline import (
    PipelineError,
    PipelineResult,
    _transform_normalized_data,
    _validate_transformation,
    _write_pipeline_outputs,
    main,
    run_pipeline,
)
from src.storage import StorageError
from src.transformation import TransformationError, TransformationResult
from src.validation import ValidationError, ValidationResult


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
        "api_base_url": "https://api.example.com/orders",
        "api_page_size": 2,
        "api_max_pages": 10,
        "api_timeout_seconds": 30.0,
        "api_connect_timeout_seconds": 10.0,
        "api_read_timeout_seconds": 30.0,
        "api_max_retries": 0,
        "api_backoff_factor": 0.0,
        "api_response_timezone": "UTC",
        "drop_invalid_records": False,
        "fail_on_http_error": True,
        "fail_on_schema_error": True,
        "create_directories": True,
        "atomic_writes": True,
        "log_level": "CRITICAL",
    }
    values.update(overrides)
    return PipelineConfig(**values)


def make_ingestion_result(
    records: list[dict] | None = None,
    *,
    pages_fetched: int | None = None,
) -> IngestionResult:
    """Create a deterministic ingestion result fixture."""
    records = records or [
        {
            "id": "order-1",
            "status": "completed",
            "amount": "100.00",
            "created_at": "2026-01-01T10:00:00Z",
        },
        {
            "id": "order-2",
            "status": "pending",
            "amount": "200.00",
            "created_at": "2026-01-02T10:00:00Z",
        },
    ]

    return IngestionResult(
        records=records,
        pages_fetched=(
            pages_fetched
            if pages_fetched is not None
            else len(records)
        ),
        records_fetched=len(records),
    )


def make_normalization_result(
    *,
    normalized: pd.DataFrame | None = None,
    rejected: pd.DataFrame | None = None,
    input_rows: int = 2,
    normalized_rows: int = 2,
    rejected_rows: int = 0,
) -> NormalizationResult:
    """Create a deterministic normalization result fixture."""
    normalized = (
        normalized
        if normalized is not None
        else pd.DataFrame(
            [
                {
                    "id": "order-1",
                    "status": "completed",
                    "amount": 100.0,
                    "created_at": pd.Timestamp(
                        "2026-01-01T10:00:00Z"
                    ),
                },
                {
                    "id": "order-2",
                    "status": "pending",
                    "amount": 200.0,
                    "created_at": pd.Timestamp(
                        "2026-01-02T10:00:00Z"
                    ),
                },
            ]
        )
    )

    rejected = (
        rejected
        if rejected is not None
        else pd.DataFrame()
    )

    return NormalizationResult(
        normalized=normalized,
        rejected=rejected,
        input_rows=input_rows,
        normalized_rows=normalized_rows,
        rejected_rows=rejected_rows,
    )


def make_transformation_result(
    *,
    data: pd.DataFrame | None = None,
    metrics: dict[str, int | float] | None = None,
) -> TransformationResult:
    """Create a deterministic transformation result fixture."""
    data = (
        data
        if data is not None
        else pd.DataFrame(
            [
                {
                    "id": "order-1",
                    "amount": 100.0,
                },
                {
                    "id": "order-2",
                    "amount": 200.0,
                },
            ]
        )
    )

    metrics = (
        metrics
        if metrics is not None
        else {
            "input_rows": 2,
            "output_rows": 2,
            "rows_removed": 0,
            "numeric_total": 300.0,
            "aggregation_rows": 2,
        }
    )

    return TransformationResult(
        data=data,
        metrics=metrics,
    )


def test_run_pipeline_returns_pipeline_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ingestion = make_ingestion_result()
    normalization = make_normalization_result()
    transformation = make_transformation_result()

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(return_value=ingestion),
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        MagicMock(return_value=normalization),
    )
    monkeypatch.setattr(
        "src.pipeline.transform_records",
        MagicMock(return_value=transformation),
    )
    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        MagicMock(return_value=ValidationResult()),
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline._write_pipeline_outputs",
        MagicMock(),
    )

    pipeline_config = make_config(tmp_path)

    result = run_pipeline(
        "/orders",
        pipeline_config=pipeline_config,
    )

    assert isinstance(result, PipelineResult)
    assert result.ingestion is ingestion
    assert result.normalization is normalization
    assert result.transformation is transformation


def test_run_pipeline_configures_logging(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_logging = MagicMock()

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        configure_logging,
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(
            return_value=make_ingestion_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        MagicMock(
            return_value=make_normalization_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.transform_records",
        MagicMock(
            return_value=make_transformation_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        MagicMock(
            return_value=ValidationResult(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline._write_pipeline_outputs",
        MagicMock(),
    )

    pipeline_config = make_config(tmp_path)

    run_pipeline(
        "/orders",
        pipeline_config=pipeline_config,
    )

    configure_logging.assert_called_once_with(
        pipeline_config,
    )


def test_run_pipeline_ensures_directories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ensure_directories = MagicMock()

    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        ensure_directories,
    )
    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(
            return_value=make_ingestion_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        MagicMock(
            return_value=make_normalization_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.transform_records",
        MagicMock(
            return_value=make_transformation_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        MagicMock(
            return_value=ValidationResult(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline._write_pipeline_outputs",
        MagicMock(),
    )

    pipeline_config = make_config(tmp_path)

    run_pipeline(
        "/orders",
        pipeline_config=pipeline_config,
    )

    ensure_directories.assert_called_once()


@pytest.mark.parametrize(
    "endpoint",
    [
        "",
        " ",
        "\t",
    ],
)
def test_run_pipeline_rejects_empty_endpoint(
    tmp_path: Path,
    endpoint: str,
) -> None:
    pipeline_config = make_config(tmp_path)

    with pytest.raises(
        PipelineError,
        match="endpoint",
    ):
        run_pipeline(
            endpoint,
            pipeline_config=pipeline_config,
        )


def test_run_pipeline_passes_endpoint_and_params_to_ingestion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ingestion_mock = MagicMock(
        return_value=make_ingestion_result(),
    )

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        ingestion_mock,
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        MagicMock(
            return_value=make_normalization_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.transform_records",
        MagicMock(
            return_value=make_transformation_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        MagicMock(
            return_value=ValidationResult(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline._write_pipeline_outputs",
        MagicMock(),
    )

    pipeline_config = make_config(tmp_path)
    extra_params = {
        "status": "completed",
        "region": "apac",
    }

    run_pipeline(
        "/orders",
        pipeline_config=pipeline_config,
        extra_params=extra_params,
    )

    ingestion_mock.assert_called_once_with(
        "/orders",
        pipeline_config=pipeline_config,
        extra_params=extra_params,
    )


def test_run_pipeline_normalizes_expected_api_fields(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    normalize_mock = MagicMock(
        return_value=make_normalization_result(),
    )

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(
            return_value=make_ingestion_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        normalize_mock,
    )
    monkeypatch.setattr(
        "src.pipeline.transform_records",
        MagicMock(
            return_value=make_transformation_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        MagicMock(
            return_value=ValidationResult(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline._write_pipeline_outputs",
        MagicMock(),
    )

    pipeline_config = make_config(tmp_path)
    ingestion = make_ingestion_result()

    run_pipeline(
        "/orders",
        pipeline_config=pipeline_config,
    )

    normalize_mock.assert_called_once_with(
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


def test_run_pipeline_uses_transformation_result_for_validation_and_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transformation = make_transformation_result()

    transform_mock = MagicMock(
        return_value=transformation,
    )
    validate_mock = MagicMock(
        return_value=ValidationResult(),
    )
    write_mock = MagicMock()

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(
            return_value=make_ingestion_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        MagicMock(
            return_value=make_normalization_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.transform_records",
        transform_mock,
    )
    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        validate_mock,
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline._write_pipeline_outputs",
        write_mock,
    )

    result = run_pipeline(
        "/orders",
        pipeline_config=make_config(tmp_path),
    )

    assert result.transformation is transformation
    validate_mock.assert_called_once()
    assert validate_mock.call_args.args[0] is transformation.data
    write_mock.assert_called_once()


def test_run_pipeline_calls_assert_valid_on_validation_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    validation_result = ValidationResult()
    assert_valid_mock = MagicMock()

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(
            return_value=make_ingestion_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        MagicMock(
            return_value=make_normalization_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.transform_records",
        MagicMock(
            return_value=make_transformation_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        MagicMock(
            return_value=validation_result,
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        assert_valid_mock,
    )
    monkeypatch.setattr(
        "src.pipeline._write_pipeline_outputs",
        MagicMock(),
    )

    run_pipeline(
        "/orders",
        pipeline_config=make_config(tmp_path),
    )

    assert_valid_mock.assert_called_once_with(
        validation_result,
    )


def test_run_pipeline_rejects_invalid_rows_when_schema_validation_is_strict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    normalization = make_normalization_result(
        normalized=pd.DataFrame(
            [
                {
                    "id": "order-1",
                    "amount": 100.0,
                }
            ]
        ),
        rejected=pd.DataFrame(
            [
                {
                    "id": None,
                    "amount": 200.0,
                }
            ]
        ),
        input_rows=2,
        normalized_rows=1,
        rejected_rows=1,
    )

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(
            return_value=make_ingestion_result(
                [
                    {"id": "order-1"},
                    {"id": None},
                ]
            ),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        MagicMock(return_value=normalization),
    )

    pipeline_config = make_config(
        tmp_path,
        fail_on_schema_error=True,
        drop_invalid_records=False,
    )

    with pytest.raises(
        PipelineError,
        match="schema",
    ):
        run_pipeline(
            "/orders",
            pipeline_config=pipeline_config,
        )


def test_run_pipeline_allows_rejected_rows_when_configured_to_drop_invalid_records(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    normalization = make_normalization_result(
        normalized=pd.DataFrame(
            [
                {
                    "id": "order-1",
                    "amount": 100.0,
                }
            ]
        ),
        rejected=pd.DataFrame(
            [
                {
                    "id": None,
                    "amount": 200.0,
                }
            ]
        ),
        input_rows=2,
        normalized_rows=1,
        rejected_rows=1,
    )

    transformation = make_transformation_result(
        data=pd.DataFrame(
            [
                {
                    "id": "order-1",
                    "amount": 100.0,
                }
            ]
        ),
        metrics={
            "input_rows": 1,
            "output_rows": 1,
            "rows_removed": 0,
            "numeric_total": 100.0,
        },
    )

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(
            return_value=make_ingestion_result(
                [
                    {"id": "order-1"},
                    {"id": None},
                ]
            ),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        MagicMock(
            return_value=normalization,
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.transform_records",
        MagicMock(
            return_value=transformation,
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        MagicMock(
            return_value=ValidationResult(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        MagicMock(),
    )
    write_mock = MagicMock()
    monkeypatch.setattr(
        "src.pipeline._write_pipeline_outputs",
        write_mock,
    )

    result = run_pipeline(
        "/orders",
        pipeline_config=make_config(
            tmp_path,
            fail_on_schema_error=True,
            drop_invalid_records=True,
        ),
    )

    assert result.normalization is normalization
    assert result.transformation is transformation
    write_mock.assert_called_once()


def test_run_pipeline_wraps_ingestion_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = IngestionError(
        "API unavailable",
    )

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(side_effect=expected),
    )

    with pytest.raises(
        PipelineError,
        match="ingestion",
    ) as exc_info:
        run_pipeline(
            "/orders",
            pipeline_config=make_config(tmp_path),
        )

    assert exc_info.value.__cause__ is expected


def test_run_pipeline_wraps_normalization_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = NormalizationError(
        "invalid payload",
    )

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(
            return_value=make_ingestion_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        MagicMock(side_effect=expected),
    )

    with pytest.raises(
        PipelineError,
        match="normalization",
    ) as exc_info:
        run_pipeline(
            "/orders",
            pipeline_config=make_config(tmp_path),
        )

    assert exc_info.value.__cause__ is expected


def test_run_pipeline_wraps_transformation_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = TransformationError(
        "invalid transformation",
    )

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(
            return_value=make_ingestion_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        MagicMock(
            return_value=make_normalization_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.transform_records",
        MagicMock(side_effect=expected),
    )

    with pytest.raises(
        PipelineError,
        match="transformation",
    ) as exc_info:
        run_pipeline(
            "/orders",
            pipeline_config=make_config(tmp_path),
        )

    assert exc_info.value.__cause__ is expected


def test_run_pipeline_wraps_validation_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = ValidationError(
        "transformed data is invalid",
    )

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(
            return_value=make_ingestion_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        MagicMock(
            return_value=make_normalization_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.transform_records",
        MagicMock(
            return_value=make_transformation_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        MagicMock(
            return_value=ValidationResult(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        MagicMock(side_effect=expected),
    )

    with pytest.raises(
        PipelineError,
        match="validation",
    ) as exc_info:
        run_pipeline(
            "/orders",
            pipeline_config=make_config(tmp_path),
        )

    assert exc_info.value.__cause__ is expected


def test_run_pipeline_wraps_storage_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = StorageError(
        "failed to write output",
    )

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(
            return_value=make_ingestion_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        MagicMock(
            return_value=make_normalization_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.transform_records",
        MagicMock(
            return_value=make_transformation_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        MagicMock(
            return_value=ValidationResult(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline._write_pipeline_outputs",
        MagicMock(side_effect=expected),
    )

    with pytest.raises(
        PipelineError,
        match="storage",
    ) as exc_info:
        run_pipeline(
            "/orders",
            pipeline_config=make_config(tmp_path),
        )

    assert exc_info.value.__cause__ is expected


def test_transform_normalized_data_returns_empty_result_for_empty_frame() -> None:
    normalized = make_normalization_result(
        normalized=pd.DataFrame(
            columns=[
                "id",
                "amount",
            ]
        ),
        rejected=pd.DataFrame(),
        input_rows=0,
        normalized_rows=0,
        rejected_rows=0,
    )

    result = _transform_normalized_data(
        normalized,
    )

    assert isinstance(
        result,
        TransformationResult,
    )
    assert result.data.empty
    assert result.metrics["input_rows"] == 0
    assert result.metrics["output_rows"] == 0


def test_transform_normalized_data_selects_created_at_when_available() -> None:
    normalized = make_normalization_result(
        normalized=pd.DataFrame(
            [
                {
                    "id": "order-1",
                    "amount": 100.0,
                    "created_at": pd.Timestamp(
                        "2026-01-01T10:00:00Z"
                    ),
                }
            ]
        )
    )

    result = _transform_normalized_data(
        normalized,
    )

    assert "event_year" in result.data.columns
    assert result.data.loc[0, "event_year"] == 2026


def test_transform_normalized_data_falls_back_to_updated_at() -> None:
    normalized = make_normalization_result(
        normalized=pd.DataFrame(
            [
                {
                    "id": "order-1",
                    "amount": 100.0,
                    "updated_at": pd.Timestamp(
                        "2026-02-01T10:00:00Z"
                    ),
                }
            ]
        )
    )

    result = _transform_normalized_data(
        normalized,
    )

    assert "event_month" in result.data.columns
    assert result.data.loc[0, "event_month"] == 2


def test_transform_normalized_data_detects_status_column() -> None:
    normalized = make_normalization_result(
        normalized=pd.DataFrame(
            [
                {
                    "id": "order-1",
                    "status": "completed",
                    "amount": 100.0,
                }
            ]
        )
    )

    result = _transform_normalized_data(
        normalized,
    )

    assert result.data.loc[0, "is_completed"] is True


def test_transform_normalized_data_detects_numeric_value_column() -> None:
    normalized = make_normalization_result(
        normalized=pd.DataFrame(
            [
                {
                    "id": "order-1",
                    "value": "100.00",
                }
            ]
        )
    )

    result = _transform_normalized_data(
        normalized,
    )

    assert result.data.loc[0, "value"] == 100.0


def test_transform_normalized_data_detects_transaction_id_identifier() -> None:
    normalized = make_normalization_result(
        normalized=pd.DataFrame(
            [
                {
                    "transaction_id": "txn-1",
                    "amount": 100.0,
                },
                {
                    "transaction_id": "txn-2",
                    "amount": 200.0,
                },
            ]
        )
    )

    result = _transform_normalized_data(
        normalized,
    )

    assert result.data["transaction_id"].tolist() == [
        "txn-1",
        "txn-2",
    ]


def test_validate_transformation_returns_validation_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    validation_result = ValidationResult()

    validate_mock = MagicMock(
        return_value=validation_result,
    )
    assert_mock = MagicMock()

    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        validate_mock,
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        assert_mock,
    )

    frame = pd.DataFrame(
        [
            {
                "id": "order-1",
                "amount": 100.0,
            }
        ]
    )

    _validate_transformation(
        frame,
    )

    assert_mock.assert_called_once_with(
        validation_result,
    )


def test_validate_transformation_detects_present_identifier_columns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    validate_mock = MagicMock(
        return_value=ValidationResult(),
    )
    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        validate_mock,
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        MagicMock(),
    )

    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "amount": 100.0,
            }
        ]
    )

    _validate_transformation(
        frame,
    )

    kwargs = validate_mock.call_args.kwargs

    assert kwargs["id_columns"] == ("order_id",)
    assert kwargs["numeric_columns"] == ("amount",)


def test_validate_transformation_detects_datetime_columns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    validate_mock = MagicMock(
        return_value=ValidationResult(),
    )
    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        validate_mock,
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        MagicMock(),
    )

    frame = pd.DataFrame(
        [
            {
                "id": "order-1",
                "created_at": pd.Timestamp(
                    "2026-01-01T10:00:00Z"
                ),
            }
        ]
    )

    _validate_transformation(
        frame,
    )

    kwargs = validate_mock.call_args.kwargs

    assert kwargs["datetime_columns"] == (
        "created_at",
    )


def test_write_pipeline_outputs_persists_expected_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    normalized = make_normalization_result()
    transformed = make_transformation_result()
    pipeline_config = make_config(tmp_path)

    write_json = MagicMock()
    write_parquet = MagicMock()
    write_csv = MagicMock()

    monkeypatch.setattr(
        "src.pipeline.write_json",
        write_json,
    )
    monkeypatch.setattr(
        "src.pipeline.write_parquet",
        write_parquet,
    )
    monkeypatch.setattr(
        "src.pipeline.write_csv",
        write_csv,
    )

    _write_pipeline_outputs(
        normalized,
        transformed,
        pipeline_config=pipeline_config,
    )

    assert write_json.call_count == 1
    assert write_csv.call_count == 1
    assert write_parquet.call_count == 2

    write_json.assert_called_once_with(
        normalized.normalized.to_dict(
            orient="records"
        ),
        pipeline_config.raw_response_path,
        atomic=True,
    )

    write_csv.assert_called_once_with(
        normalized.rejected,
        pipeline_config.rejected_records_path,
        atomic=True,
    )


def test_write_pipeline_outputs_writes_transformed_data_to_expected_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    normalized = make_normalization_result()
    transformed = make_transformation_result()
    pipeline_config = make_config(tmp_path)

    write_parquet = MagicMock()

    monkeypatch.setattr(
        "src.pipeline.write_json",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.write_csv",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.write_parquet",
        write_parquet,
    )

    _write_pipeline_outputs(
        normalized,
        transformed,
        pipeline_config=pipeline_config,
    )

    calls = write_parquet.call_args_list

    assert calls[0].args[0].equals(
        transformed.data
    )
    assert calls[0].args[1] == (
        pipeline_config.normalized_data_path
    )
    assert calls[0].kwargs == {
        "atomic": pipeline_config.atomic_writes,
    }


def test_write_pipeline_outputs_creates_processing_report_from_metrics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    normalized = make_normalization_result()
    transformed = make_transformation_result(
        metrics={
            "input_rows": 10,
            "output_rows": 8,
            "rows_removed": 2,
            "numeric_total": 1234.5,
        }
    )
    pipeline_config = make_config(tmp_path)

    write_parquet = MagicMock()

    monkeypatch.setattr(
        "src.pipeline.write_json",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.write_csv",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.write_parquet",
        write_parquet,
    )

    _write_pipeline_outputs(
        normalized,
        transformed,
        pipeline_config=pipeline_config,
    )

    report_call = write_parquet.call_args_list[-1]

    report = report_call.args[0]

    assert report.loc[0, "input_rows"] == 10
    assert report.loc[0, "output_rows"] == 8
    assert report.loc[0, "rows_removed"] == 2
    assert report.loc[0, "numeric_total"] == 1234.5
    assert report.loc[0, "records_fetched"] == 10


def test_write_pipeline_outputs_honors_atomic_write_configuration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    normalized = make_normalization_result()
    transformed = make_transformation_result()
    pipeline_config = make_config(
        tmp_path,
        atomic_writes=False,
    )

    write_json = MagicMock()
    write_parquet = MagicMock()
    write_csv = MagicMock()

    monkeypatch.setattr(
        "src.pipeline.write_json",
        write_json,
    )
    monkeypatch.setattr(
        "src.pipeline.write_parquet",
        write_parquet,
    )
    monkeypatch.setattr(
        "src.pipeline.write_csv",
        write_csv,
    )

    _write_pipeline_outputs(
        normalized,
        transformed,
        pipeline_config=pipeline_config,
    )

    for call in write_json.call_args_list:
        assert call.kwargs["atomic"] is False

    for call in write_parquet.call_args_list:
        assert call.kwargs["atomic"] is False

    for call in write_csv.call_args_list:
        assert call.kwargs["atomic"] is False


def test_write_pipeline_outputs_wraps_unexpected_storage_exceptions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_json = MagicMock(
        side_effect=OSError("disk full"),
    )

    monkeypatch.setattr(
        "src.pipeline.write_json",
        write_json,
    )
    monkeypatch.setattr(
        "src.pipeline.write_parquet",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.write_csv",
        MagicMock(),
    )

    with pytest.raises(
        PipelineError,
        match="persist pipeline outputs",
    ) as exc_info:
        _write_pipeline_outputs(
            make_normalization_result(),
            make_transformation_result(),
            pipeline_config=make_config(tmp_path),
        )

    assert isinstance(
        exc_info.value.__cause__,
        OSError,
    )


def test_write_pipeline_outputs_preserves_storage_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = StorageError(
        "parquet write failed",
    )

    monkeypatch.setattr(
        "src.pipeline.write_json",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.write_parquet",
        MagicMock(side_effect=expected),
    )
    monkeypatch.setattr(
        "src.pipeline.write_csv",
        MagicMock(),
    )

    with pytest.raises(StorageError) as exc_info:
        _write_pipeline_outputs(
            make_normalization_result(),
            make_transformation_result(),
            pipeline_config=make_config(tmp_path),
        )

    assert exc_info.value is expected


def test_main_returns_zero_when_pipeline_succeeds(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_mock = MagicMock(
        return_value=PipelineResult(
            ingestion=make_ingestion_result(),
            normalization=make_normalization_result(),
            transformation=make_transformation_result(),
        )
    )

    monkeypatch.setattr(
        "src.pipeline.run_pipeline",
        run_mock,
    )

    pipeline_config = make_config(tmp_path)

    exit_code = main(
        "/orders",
        pipeline_config=pipeline_config,
    )

    assert exit_code == 0

    run_mock.assert_called_once_with(
        "/orders",
        pipeline_config=pipeline_config,
    )


def test_main_returns_one_when_pipeline_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_mock = MagicMock(
        side_effect=PipelineError(
            "pipeline failed",
        )
    )

    monkeypatch.setattr(
        "src.pipeline.run_pipeline",
        run_mock,
    )

    exit_code = main(
        "/orders",
        pipeline_config=make_config(tmp_path),
    )

    assert exit_code == 1


def test_main_handles_pipeline_error_without_raising(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "src.pipeline.run_pipeline",
        MagicMock(
            side_effect=PipelineError(
                "controlled failure",
            )
        ),
    )

    assert (
        main(
            "/orders",
            pipeline_config=make_config(tmp_path),
        )
        == 1
    )


def test_pipeline_result_preserves_stage_results() -> None:
    ingestion = make_ingestion_result()
    normalization = make_normalization_result()
    transformation = make_transformation_result()

    result = PipelineResult(
        ingestion=ingestion,
        normalization=normalization,
        transformation=transformation,
    )

    assert result.ingestion is ingestion
    assert result.normalization is normalization
    assert result.transformation is transformation


def test_run_pipeline_does_not_write_outputs_when_validation_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_mock = MagicMock()

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(
            return_value=make_ingestion_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        MagicMock(
            return_value=make_normalization_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.transform_records",
        MagicMock(
            return_value=make_transformation_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        MagicMock(
            return_value=ValidationResult(
                issues=[],
            ),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        MagicMock(
            side_effect=ValidationError(
                "invalid transformed data",
            ),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline._write_pipeline_outputs",
        write_mock,
    )

    with pytest.raises(
        PipelineError,
    ):
        run_pipeline(
            "/orders",
            pipeline_config=make_config(tmp_path),
        )

    write_mock.assert_not_called()


def test_run_pipeline_handles_empty_normalized_dataset(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    normalization = make_normalization_result(
        normalized=pd.DataFrame(),
        rejected=pd.DataFrame(),
        input_rows=0,
        normalized_rows=0,
        rejected_rows=0,
    )
    transformation = TransformationResult(
        data=pd.DataFrame(),
        metrics={
            "input_rows": 0,
            "output_rows": 0,
            "rows_removed": 0,
            "numeric_total": 0.0,
        },
    )

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(
            return_value=make_ingestion_result(
                records=[],
                pages_fetched=0,
            ),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        MagicMock(
            return_value=normalization,
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.transform_records",
        MagicMock(
            return_value=transformation,
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        MagicMock(
            return_value=ValidationResult(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline._write_pipeline_outputs",
        MagicMock(),
    )

    result = run_pipeline(
        "/orders",
        pipeline_config=make_config(
            tmp_path,
            fail_on_schema_error=False,
        ),
    )

    assert result.normalization.normalized.empty
    assert result.transformation.data.empty


def test_run_pipeline_passes_config_timezone_to_normalization(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    normalize_mock = MagicMock(
        return_value=make_normalization_result(),
    )

    monkeypatch.setattr(
        "src.pipeline.configure_logging",
        MagicMock(),
    )
    monkeypatch.setattr(
        PipelineConfig,
        "ensure_directories",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline.ingest_and_validate",
        MagicMock(
            return_value=make_ingestion_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.normalize_api_records",
        normalize_mock,
    )
    monkeypatch.setattr(
        "src.pipeline.transform_records",
        MagicMock(
            return_value=make_transformation_result(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.validate_transformed_data",
        MagicMock(
            return_value=ValidationResult(),
        ),
    )
    monkeypatch.setattr(
        "src.pipeline.assert_valid",
        MagicMock(),
    )
    monkeypatch.setattr(
        "src.pipeline._write_pipeline_outputs",
        MagicMock(),
    )

    pipeline_config = make_config(
        tmp_path,
        api_response_timezone="Asia/Kolkata",
    )

    run_pipeline(
        "/orders",
        pipeline_config=pipeline_config,
    )

    assert (
        normalize_mock.call_args.kwargs["timezone"]
        == "Asia/Kolkata"
    )