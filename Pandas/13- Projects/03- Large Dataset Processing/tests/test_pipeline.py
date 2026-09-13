from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

import src.pipeline as pipeline_module
from src.aggregation import AggregationResult
from src.config import PipelineConfig
from src.pipeline import (
    PipelineError,
    PipelineMetrics,
    PipelineResult,
    _build_pipeline_metrics,
    _build_processing_report,
    _cleanup_previous_run,
    _memory_bytes,
    _validate_chunk,
    _validate_configuration,
    run,
    run_pipeline,
)


def _pipeline_config(
    tmp_path: Path,
    **overrides: object,
) -> PipelineConfig:
    """Create a deterministic pipeline configuration for tests."""
    values: dict[str, object] = {
        "input_path": tmp_path / "input.csv",
        "output_path": tmp_path / "processed" / "output.parquet",
        "report_path": tmp_path / "reports" / "processing_report.parquet",
        "processed_data_dir": tmp_path / "processed",
        "checkpoint_dir": tmp_path / "checkpoints",
        "input_format": "csv",
        "output_format": "parquet",
        "create_directories": True,
        "atomic_writes": True,
        "checkpointing_enabled": False,
        "resume_enabled": False,
        "fail_on_validation": True,
        "required_columns": ("order_id",),
        "identifier_columns": ("order_id",),
        "numeric_columns": ("amount",),
        "timestamp_columns": (),
        "categorical_columns": ("status",),
    }
    values.update(overrides)

    configuration = PipelineConfig(
        **values
    )
    configuration.input_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    configuration.input_path.write_text(
        "order_id,amount\n1001,100\n1002,200\n",
        encoding="utf-8",
    )

    return configuration


def _simple_pipeline_config(
    tmp_path: Path,
    **overrides: object,
) -> SimpleNamespace:
    """Build a lightweight configuration object for focused unit tests."""
    values = {
        "input_path": tmp_path / "input.csv",
        "output_path": tmp_path / "processed" / "output.parquet",
        "report_path": tmp_path / "reports" / "report.parquet",
        "processed_data_dir": tmp_path / "processed",
        "checkpoint_dir": tmp_path / "checkpoints",
        "input_format": "csv",
        "output_format": "parquet",
        "create_directories": True,
        "atomic_writes": True,
        "checkpointing_enabled": False,
        "resume_enabled": False,
        "fail_on_validation": True,
        "required_columns": ("order_id",),
        "identifier_columns": ("order_id",),
        "numeric_columns": ("amount",),
        "timestamp_columns": (),
        "categorical_columns": ("status",),
        "pipeline_name": "large-dataset-processing",
        "parquet_compression": "snappy",
        "csv_encoding": "utf-8",
        "csv_separator": ",",
        "low_memory": True,
        "memory_map": False,
        "target_memory_mb": 256,
    }
    values.update(overrides)

    configuration = SimpleNamespace(
        **values
    )

    configuration.validate = lambda: None
    configuration.ensure_directories = lambda: (
        Path(configuration.processed_data_dir).mkdir(
            parents=True,
            exist_ok=True,
        ),
        Path(configuration.checkpoint_dir).mkdir(
            parents=True,
            exist_ok=True,
        ),
        Path(configuration.report_path).parent.mkdir(
            parents=True,
            exist_ok=True,
        ),
    )

    return configuration


def test_memory_bytes_returns_deep_dataframe_size() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001", "1002"],
            "amount": [100.0, 200.0],
        }
    )

    result = _memory_bytes(
        frame
    )

    expected = int(
        frame.memory_usage(
            index=True,
            deep=True,
        ).sum()
    )

    assert result == expected
    assert result > 0


def test_validate_configuration_accepts_valid_configuration(
    tmp_path: Path,
) -> None:
    configuration = _pipeline_config(
        tmp_path
    )

    _validate_configuration(
        configuration
    )


def test_validate_configuration_rejects_missing_input_path(
    tmp_path: Path,
) -> None:
    configuration = _pipeline_config(
        tmp_path
    )
    configuration.input_path.unlink()

    with pytest.raises(
        PipelineError,
        match="does not exist",
    ):
        _validate_configuration(
            configuration
        )


def test_validate_configuration_rejects_input_directory(
    tmp_path: Path,
) -> None:
    configuration = _pipeline_config(
        tmp_path
    )
    configuration.input_path.unlink()
    configuration.input_path.mkdir()

    with pytest.raises(
        PipelineError,
        match="not a file",
    ):
        _validate_configuration(
            configuration
        )


def test_validate_configuration_wraps_configuration_errors(
    tmp_path: Path,
) -> None:
    configuration = _pipeline_config(
        tmp_path
    )

    def fail_validation() -> None:
        raise ValueError(
            "invalid configuration"
        )

    configuration.validate = fail_validation

    with pytest.raises(
        PipelineError,
        match="Invalid pipeline configuration",
    ):
        _validate_configuration(
            configuration
        )


def test_validate_chunk_returns_valid_result_for_clean_data(
    tmp_path: Path,
) -> None:
    configuration = _pipeline_config(
        tmp_path
    )

    frame = pd.DataFrame(
        {
            "order_id": [
                "1001",
                "1002",
            ],
            "amount": [
                100.0,
                200.0,
            ],
        }
    )

    result = _validate_chunk(
        frame,
        configuration,
    )

    assert result.is_valid


def test_validate_chunk_raises_when_validation_fails_and_strict_mode_enabled(
    tmp_path: Path,
) -> None:
    configuration = _pipeline_config(
        tmp_path,
        fail_on_validation=True,
    )

    frame = pd.DataFrame(
        {
            "order_id": [
                "1001",
                "1001",
            ],
            "amount": [
                100.0,
                -25.0,
            ],
        }
    )

    with pytest.raises(
        ValueError,
    ):
        _validate_chunk(
            frame,
            configuration,
        )


def test_validate_chunk_returns_invalid_result_when_validation_is_non_strict(
    tmp_path: Path,
) -> None:
    configuration = _pipeline_config(
        tmp_path,
        fail_on_validation=False,
    )

    frame = pd.DataFrame(
        {
            "order_id": [
                "1001",
                "1001",
            ],
            "amount": [
                100.0,
                -25.0,
            ],
        }
    )

    result = _validate_chunk(
        frame,
        configuration,
    )

    assert not result.is_valid
    assert result.issue_count > 0


def test_build_processing_report_contains_operational_metrics(
    tmp_path: Path,
) -> None:
    configuration = _simple_pipeline_config(
        tmp_path
    )

    state = pipeline_module._PipelineState(
        rows_read=1000,
        rows_written=950,
        chunks_processed=10,
        chunks_failed=1,
        rows_rejected=50,
        input_memory_bytes=10_000,
        output_memory_bytes=8_000,
    )

    result = _build_processing_report(
        state,
        pipeline_config=configuration,
        elapsed_seconds=5.0,
    )

    assert isinstance(
        result,
        pd.DataFrame,
    )
    assert len(result) == 1

    row = result.iloc[0]

    assert row["pipeline"] == configuration.pipeline_name
    assert row["rows_read"] == 1000
    assert row["rows_written"] == 950
    assert row["rows_rejected"] == 50
    assert row["chunks_processed"] == 10
    assert row["chunks_failed"] == 1
    assert row["elapsed_seconds"] == 5.0
    assert row["throughput_rows_per_second"] == 200.0


def test_build_processing_report_handles_zero_elapsed_time(
    tmp_path: Path,
) -> None:
    configuration = _simple_pipeline_config(
        tmp_path
    )

    state = pipeline_module._PipelineState(
        rows_read=100,
        rows_written=100,
    )

    result = _build_processing_report(
        state,
        pipeline_config=configuration,
        elapsed_seconds=0.0,
    )

    assert result["throughput_rows_per_second"].iloc[0] == 0.0


def test_build_pipeline_metrics_returns_immutable_run_metrics(
    tmp_path: Path,
) -> None:
    state = pipeline_module._PipelineState(
        rows_read=1000,
        rows_written=950,
        chunks_processed=10,
        chunks_failed=1,
        rows_rejected=50,
        input_memory_bytes=10_000,
        output_memory_bytes=8_000,
    )

    metrics = _build_pipeline_metrics(
        state,
        elapsed_seconds=5.0,
    )

    assert isinstance(
        metrics,
        PipelineMetrics,
    )
    assert metrics.rows_read == 1000
    assert metrics.rows_written == 950
    assert metrics.chunks_processed == 10
    assert metrics.chunks_failed == 1
    assert metrics.rows_rejected == 50
    assert metrics.input_memory_bytes == 10_000
    assert metrics.output_memory_bytes == 8_000
    assert metrics.elapsed_seconds == 5.0
    assert metrics.throughput_rows_per_second == 200.0


def test_pipeline_metrics_returns_zero_throughput_for_non_positive_elapsed_time() -> None:
    metrics = PipelineMetrics(
        rows_read=100,
        rows_written=100,
        chunks_processed=1,
        chunks_failed=0,
        rows_rejected=0,
        input_memory_bytes=1000,
        output_memory_bytes=1000,
        elapsed_seconds=0.0,
    )

    assert metrics.throughput_rows_per_second == 0.0


def test_pipeline_result_exposes_processed_row_count(
    tmp_path: Path,
) -> None:
    metrics = PipelineMetrics(
        rows_read=100,
        rows_written=95,
        chunks_processed=5,
        chunks_failed=0,
        rows_rejected=5,
        input_memory_bytes=1000,
        output_memory_bytes=900,
        elapsed_seconds=2.0,
    )

    result = PipelineResult(
        output_path=tmp_path / "output.parquet",
        report_path=tmp_path / "report.parquet",
        metrics=metrics,
        validation=pipeline_module.ValidationResult(),
    )

    assert result.rows_processed == 95
    assert result.throughput_rows_per_second == 50.0


def test_pipeline_result_defaults_to_no_checkpoint_paths(
    tmp_path: Path,
) -> None:
    metrics = PipelineMetrics(
        rows_read=1,
        rows_written=1,
        chunks_processed=1,
        chunks_failed=0,
        rows_rejected=0,
        input_memory_bytes=100,
        output_memory_bytes=100,
        elapsed_seconds=1.0,
    )

    result = PipelineResult(
        output_path=tmp_path / "output.parquet",
        report_path=tmp_path / "report.parquet",
        metrics=metrics,
        validation=pipeline_module.ValidationResult(),
    )

    assert result.checkpoint_paths == ()


def test_cleanup_previous_run_removes_old_output_partitions(
    tmp_path: Path,
) -> None:
    configuration = _simple_pipeline_config(
        tmp_path
    )

    processed_dir = Path(
        configuration.processed_data_dir
    )
    processed_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    first = processed_dir / "part-00000001.parquet"
    second = processed_dir / "part-00000002.parquet"

    pd.DataFrame(
        {"id": [1]}
    ).to_parquet(
        first,
        index=False,
    )
    pd.DataFrame(
        {"id": [2]}
    ).to_parquet(
        second,
        index=False,
    )

    _cleanup_previous_run(
        configuration
    )

    assert not first.exists()
    assert not second.exists()


def test_cleanup_previous_run_preserves_outputs_when_resume_is_enabled(
    tmp_path: Path,
) -> None:
    configuration = _simple_pipeline_config(
        tmp_path,
        resume_enabled=True,
    )

    processed_dir = Path(
        configuration.processed_data_dir
    )
    processed_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    partition = (
        processed_dir
        / "part-00000001.parquet"
    )
    pd.DataFrame(
        {"id": [1]}
    ).to_parquet(
        partition,
        index=False,
    )

    _cleanup_previous_run(
        configuration
    )

    assert partition.exists()


def test_cleanup_previous_run_cleans_checkpoints_for_non_resumable_runs(
    tmp_path: Path,
) -> None:
    configuration = _simple_pipeline_config(
        tmp_path,
        checkpointing_enabled=True,
    )

    checkpoint_dir = Path(
        configuration.checkpoint_dir
    )
    checkpoint_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    checkpoint = (
        checkpoint_dir
        / "chunk-00000001.parquet"
    )
    pd.DataFrame(
        {"id": [1]}
    ).to_parquet(
        checkpoint,
        index=False,
    )

    _cleanup_previous_run(
        configuration
    )

    assert not checkpoint.exists()


def test_run_pipeline_writes_final_output_and_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuration = _simple_pipeline_config(
        tmp_path
    )

    output_dir = Path(
        configuration.processed_data_dir
    )
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    partition = (
        output_dir
        / "part-00000001.parquet"
    )

    expected_output = pd.DataFrame(
        {
            "order_id": [
                "1001",
                "1002",
            ],
            "amount": [
                100.0,
                200.0,
            ],
        }
    )

    expected_output.to_parquet(
        partition,
        index=False,
    )

    def fake_process_stream(
        pipeline_config: PipelineConfig,
        state: object,
    ) -> pipeline_module.ValidationResult:
        state.rows_read = 2
        state.rows_written = 2
        state.chunks_processed = 1
        state.input_memory_bytes = _memory_bytes(
            expected_output
        )
        state.output_memory_bytes = _memory_bytes(
            expected_output
        )
        return pipeline_module.ValidationResult()

    monkeypatch.setattr(
        pipeline_module,
        "_process_stream",
        fake_process_stream,
    )

    result = run_pipeline(
        pipeline_config=configuration,
    )

    assert result.output_path.exists()
    assert result.report_path.exists()

    output = pd.read_parquet(
        result.output_path
    )

    pd.testing.assert_frame_equal(
        output,
        expected_output,
    )

    report = pd.read_parquet(
        result.report_path
    )

    assert report["rows_read"].iloc[0] == 2
    assert report["rows_written"].iloc[0] == 2
    assert report["chunks_processed"].iloc[0] == 1


def test_run_pipeline_returns_validation_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuration = _simple_pipeline_config(
        tmp_path
    )

    output_dir = Path(
        configuration.processed_data_dir
    )
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    pd.DataFrame(
        {
            "order_id": ["1001"],
        }
    ).to_parquet(
        output_dir / "part-00000001.parquet",
        index=False,
    )

    monkeypatch.setattr(
        pipeline_module,
        "_process_stream",
        lambda pipeline_config, state: (
            setattr(state, "rows_read", 1),
            setattr(state, "rows_written", 1),
            setattr(state, "chunks_processed", 1),
            pipeline_module.ValidationResult(),
        )[-1],
    )

    result = run_pipeline(
        pipeline_config=configuration,
    )

    assert isinstance(
        result.validation,
        pipeline_module.ValidationResult,
    )
    assert result.validation.is_valid


def test_run_pipeline_wraps_storage_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuration = _simple_pipeline_config(
        tmp_path
    )

    monkeypatch.setattr(
        pipeline_module,
        "_process_stream",
        lambda pipeline_config, state: pipeline_module.ValidationResult(),
    )

    def fail_output(
        pipeline_config: PipelineConfig,
    ) -> Path:
        raise pipeline_module.StorageError(
            "cannot write output"
        )

    monkeypatch.setattr(
        pipeline_module,
        "_write_final_output",
        fail_output,
    )

    with pytest.raises(
        PipelineError,
        match="output",
    ):
        run_pipeline(
            pipeline_config=configuration,
        )


def test_run_pipeline_wraps_unexpected_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuration = _simple_pipeline_config(
        tmp_path
    )

    def fail_stream(
        pipeline_config: PipelineConfig,
        state: object,
    ) -> pipeline_module.ValidationResult:
        raise RuntimeError(
            "unexpected failure"
        )

    monkeypatch.setattr(
        pipeline_module,
        "_process_stream",
        fail_stream,
    )

    with pytest.raises(
        PipelineError,
        match="pipeline execution failed",
    ):
        run_pipeline(
            pipeline_config=configuration,
        )


def test_run_returns_zero_for_successful_pipeline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuration = _simple_pipeline_config(
        tmp_path
    )

    metrics = PipelineMetrics(
        rows_read=1,
        rows_written=1,
        chunks_processed=1,
        chunks_failed=0,
        rows_rejected=0,
        input_memory_bytes=100,
        output_memory_bytes=100,
        elapsed_seconds=1.0,
    )

    result = PipelineResult(
        output_path=tmp_path / "output.parquet",
        report_path=tmp_path / "report.parquet",
        metrics=metrics,
        validation=pipeline_module.ValidationResult(),
    )

    monkeypatch.setattr(
        pipeline_module,
        "run_pipeline",
        lambda pipeline_config: result,
    )

    assert run(
        pipeline_config=configuration,
    ) == 0


def test_run_returns_one_when_pipeline_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuration = _simple_pipeline_config(
        tmp_path
    )

    def fail(
        pipeline_config: PipelineConfig,
    ) -> PipelineResult:
        raise PipelineError(
            "pipeline failed"
        )

    monkeypatch.setattr(
        pipeline_module,
        "run_pipeline",
        fail,
    )

    assert run(
        pipeline_config=configuration,
    ) == 1


def test_run_returns_one_when_strict_validation_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuration = _simple_pipeline_config(
        tmp_path,
        fail_on_validation=True,
    )

    invalid = pipeline_module.ValidationResult(
        issues=(
            pipeline_module.ValidationIssue(
                check="numeric",
                message="Invalid numeric data.",
                column="amount",
                row_count=1,
            ),
        )
    )

    metrics = PipelineMetrics(
        rows_read=1,
        rows_written=1,
        chunks_processed=1,
        chunks_failed=0,
        rows_rejected=0,
        input_memory_bytes=100,
        output_memory_bytes=100,
        elapsed_seconds=1.0,
    )

    result = PipelineResult(
        output_path=tmp_path / "output.parquet",
        report_path=tmp_path / "report.parquet",
        metrics=metrics,
        validation=invalid,
    )

    monkeypatch.setattr(
        pipeline_module,
        "run_pipeline",
        lambda pipeline_config: result,
    )

    assert run(
        pipeline_config=configuration,
    ) == 1


def test_run_allows_invalid_validation_when_strict_mode_is_disabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuration = _simple_pipeline_config(
        tmp_path,
        fail_on_validation=False,
    )

    invalid = pipeline_module.ValidationResult(
        issues=(
            pipeline_module.ValidationIssue(
                check="numeric",
                message="Invalid numeric data.",
                column="amount",
                row_count=1,
            ),
        )
    )

    metrics = PipelineMetrics(
        rows_read=1,
        rows_written=1,
        chunks_processed=1,
        chunks_failed=0,
        rows_rejected=0,
        input_memory_bytes=100,
        output_memory_bytes=100,
        elapsed_seconds=1.0,
    )

    result = PipelineResult(
        output_path=tmp_path / "output.parquet",
        report_path=tmp_path / "report.parquet",
        metrics=metrics,
        validation=invalid,
    )

    monkeypatch.setattr(
        pipeline_module,
        "run_pipeline",
        lambda pipeline_config: result,
    )

    assert run(
        pipeline_config=configuration,
    ) == 0


def test_run_pipeline_creates_required_directories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuration = _simple_pipeline_config(
        tmp_path,
        create_directories=True,
    )

    processed_dir = Path(
        configuration.processed_data_dir
    )
    reports_dir = Path(
        configuration.report_path
    ).parent

    assert not processed_dir.exists()
    assert not reports_dir.exists()

    monkeypatch.setattr(
        pipeline_module,
        "_process_stream",
        lambda pipeline_config, state: pipeline_module.ValidationResult(),
    )

    with pytest.raises(
        PipelineError,
    ):
        run_pipeline(
            pipeline_config=configuration,
        )

    assert processed_dir.exists()
    assert reports_dir.exists()


def test_pipeline_result_preserves_checkpoint_paths(
    tmp_path: Path,
) -> None:
    checkpoints = (
        tmp_path / "chunk-00000001.parquet",
        tmp_path / "chunk-00000002.parquet",
    )

    metrics = PipelineMetrics(
        rows_read=10,
        rows_written=10,
        chunks_processed=2,
        chunks_failed=0,
        rows_rejected=0,
        input_memory_bytes=1000,
        output_memory_bytes=1000,
        elapsed_seconds=1.0,
    )

    result = PipelineResult(
        output_path=tmp_path / "output.parquet",
        report_path=tmp_path / "report.parquet",
        metrics=metrics,
        validation=pipeline_module.ValidationResult(),
        checkpoint_paths=checkpoints,
    )

    assert result.checkpoint_paths == checkpoints


def test_build_processing_report_uses_pipeline_input_and_output_paths(
    tmp_path: Path,
) -> None:
    configuration = _simple_pipeline_config(
        tmp_path
    )

    state = pipeline_module._PipelineState(
        rows_read=10
    )

    report = _build_processing_report(
        state,
        pipeline_config=configuration,
        elapsed_seconds=2.0,
    )

    row = report.iloc[0]

    assert row["input_path"] == str(
        configuration.input_path
    )
    assert row["output_path"] == str(
        configuration.output_path
    )


def test_pipeline_metrics_throughput_uses_rows_read(
) -> None:
    metrics = PipelineMetrics(
        rows_read=500,
        rows_written=450,
        chunks_processed=5,
        chunks_failed=0,
        rows_rejected=50,
        input_memory_bytes=5000,
        output_memory_bytes=4500,
        elapsed_seconds=2.5,
    )

    assert metrics.throughput_rows_per_second == pytest.approx(
        200.0
    )

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

import src.pipeline as pipeline_module
from src.aggregation import AggregationResult
from src.config import PipelineConfig
from src.pipeline import (
    PipelineError,
    PipelineMetrics,
    PipelineResult,
    _build_pipeline_metrics,
    _build_processing_report,
    _cleanup_previous_run,
    _memory_bytes,
    _validate_chunk,
    _validate_configuration,
    run,
    run_pipeline,
)


def _pipeline_config(
    tmp_path: Path,
    **overrides: object,
) -> PipelineConfig:
    """Create a deterministic pipeline configuration for tests."""
    values: dict[str, object] = {
        "input_path": tmp_path / "input.csv",
        "output_path": tmp_path / "processed" / "output.parquet",
        "report_path": tmp_path / "reports" / "processing_report.parquet",
        "processed_data_dir": tmp_path / "processed",
        "checkpoint_dir": tmp_path / "checkpoints",
        "input_format": "csv",
        "output_format": "parquet",
        "create_directories": True,
        "atomic_writes": True,
        "checkpointing_enabled": False,
        "resume_enabled": False,
        "fail_on_validation": True,
        "required_columns": ("order_id",),
        "identifier_columns": ("order_id",),
        "numeric_columns": ("amount",),
        "timestamp_columns": (),
        "categorical_columns": ("status",),
    }
    values.update(overrides)

    configuration = PipelineConfig(
        **values
    )
    configuration.input_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    configuration.input_path.write_text(
        "order_id,amount\n1001,100\n1002,200\n",
        encoding="utf-8",
    )

    return configuration


def _simple_pipeline_config(
    tmp_path: Path,
    **overrides: object,
) -> SimpleNamespace:
    """Build a lightweight configuration object for focused unit tests."""
    values = {
        "input_path": tmp_path / "input.csv",
        "output_path": tmp_path / "processed" / "output.parquet",
        "report_path": tmp_path / "reports" / "report.parquet",
        "processed_data_dir": tmp_path / "processed",
        "checkpoint_dir": tmp_path / "checkpoints",
        "input_format": "csv",
        "output_format": "parquet",
        "create_directories": True,
        "atomic_writes": True,
        "checkpointing_enabled": False,
        "resume_enabled": False,
        "fail_on_validation": True,
        "required_columns": ("order_id",),
        "identifier_columns": ("order_id",),
        "numeric_columns": ("amount",),
        "timestamp_columns": (),
        "categorical_columns": ("status",),
        "pipeline_name": "large-dataset-processing",
        "parquet_compression": "snappy",
        "csv_encoding": "utf-8",
        "csv_separator": ",",
        "low_memory": True,
        "memory_map": False,
        "target_memory_mb": 256,
    }
    values.update(overrides)

    configuration = SimpleNamespace(
        **values
    )

    configuration.validate = lambda: None
    configuration.ensure_directories = lambda: (
        Path(configuration.processed_data_dir).mkdir(
            parents=True,
            exist_ok=True,
        ),
        Path(configuration.checkpoint_dir).mkdir(
            parents=True,
            exist_ok=True,
        ),
        Path(configuration.report_path).parent.mkdir(
            parents=True,
            exist_ok=True,
        ),
    )

    return configuration


def test_memory_bytes_returns_deep_dataframe_size() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001", "1002"],
            "amount": [100.0, 200.0],
        }
    )

    result = _memory_bytes(
        frame
    )

    expected = int(
        frame.memory_usage(
            index=True,
            deep=True,
        ).sum()
    )

    assert result == expected
    assert result > 0


def test_validate_configuration_accepts_valid_configuration(
    tmp_path: Path,
) -> None:
    configuration = _pipeline_config(
        tmp_path
    )

    _validate_configuration(
        configuration
    )


def test_validate_configuration_rejects_missing_input_path(
    tmp_path: Path,
) -> None:
    configuration = _pipeline_config(
        tmp_path
    )
    configuration.input_path.unlink()

    with pytest.raises(
        PipelineError,
        match="does not exist",
    ):
        _validate_configuration(
            configuration
        )


def test_validate_configuration_rejects_input_directory(
    tmp_path: Path,
) -> None:
    configuration = _pipeline_config(
        tmp_path
    )
    configuration.input_path.unlink()
    configuration.input_path.mkdir()

    with pytest.raises(
        PipelineError,
        match="not a file",
    ):
        _validate_configuration(
            configuration
        )


def test_validate_configuration_wraps_configuration_errors(
    tmp_path: Path,
) -> None:
    configuration = _pipeline_config(
        tmp_path
    )

    def fail_validation() -> None:
        raise ValueError(
            "invalid configuration"
        )

    configuration.validate = fail_validation

    with pytest.raises(
        PipelineError,
        match="Invalid pipeline configuration",
    ):
        _validate_configuration(
            configuration
        )


def test_validate_chunk_returns_valid_result_for_clean_data(
    tmp_path: Path,
) -> None:
    configuration = _pipeline_config(
        tmp_path
    )

    frame = pd.DataFrame(
        {
            "order_id": [
                "1001",
                "1002",
            ],
            "amount": [
                100.0,
                200.0,
            ],
        }
    )

    result = _validate_chunk(
        frame,
        configuration,
    )

    assert result.is_valid


def test_validate_chunk_raises_when_validation_fails_and_strict_mode_enabled(
    tmp_path: Path,
) -> None:
    configuration = _pipeline_config(
        tmp_path,
        fail_on_validation=True,
    )

    frame = pd.DataFrame(
        {
            "order_id": [
                "1001",
                "1001",
            ],
            "amount": [
                100.0,
                -25.0,
            ],
        }
    )

    with pytest.raises(
        ValueError,
    ):
        _validate_chunk(
            frame,
            configuration,
        )


def test_validate_chunk_returns_invalid_result_when_validation_is_non_strict(
    tmp_path: Path,
) -> None:
    configuration = _pipeline_config(
        tmp_path,
        fail_on_validation=False,
    )

    frame = pd.DataFrame(
        {
            "order_id": [
                "1001",
                "1001",
            ],
            "amount": [
                100.0,
                -25.0,
            ],
        }
    )

    result = _validate_chunk(
        frame,
        configuration,
    )

    assert not result.is_valid
    assert result.issue_count > 0


def test_build_processing_report_contains_operational_metrics(
    tmp_path: Path,
) -> None:
    configuration = _simple_pipeline_config(
        tmp_path
    )

    state = pipeline_module._PipelineState(
        rows_read=1000,
        rows_written=950,
        chunks_processed=10,
        chunks_failed=1,
        rows_rejected=50,
        input_memory_bytes=10_000,
        output_memory_bytes=8_000,
    )

    result = _build_processing_report(
        state,
        pipeline_config=configuration,
        elapsed_seconds=5.0,
    )

    assert isinstance(
        result,
        pd.DataFrame,
    )
    assert len(result) == 1

    row = result.iloc[0]

    assert row["pipeline"] == configuration.pipeline_name
    assert row["rows_read"] == 1000
    assert row["rows_written"] == 950
    assert row["rows_rejected"] == 50
    assert row["chunks_processed"] == 10
    assert row["chunks_failed"] == 1
    assert row["elapsed_seconds"] == 5.0
    assert row["throughput_rows_per_second"] == 200.0


def test_build_processing_report_handles_zero_elapsed_time(
    tmp_path: Path,
) -> None:
    configuration = _simple_pipeline_config(
        tmp_path
    )

    state = pipeline_module._PipelineState(
        rows_read=100,
        rows_written=100,
    )

    result = _build_processing_report(
        state,
        pipeline_config=configuration,
        elapsed_seconds=0.0,
    )

    assert result["throughput_rows_per_second"].iloc[0] == 0.0


def test_build_pipeline_metrics_returns_immutable_run_metrics(
    tmp_path: Path,
) -> None:
    state = pipeline_module._PipelineState(
        rows_read=1000,
        rows_written=950,
        chunks_processed=10,
        chunks_failed=1,
        rows_rejected=50,
        input_memory_bytes=10_000,
        output_memory_bytes=8_000,
    )

    metrics = _build_pipeline_metrics(
        state,
        elapsed_seconds=5.0,
    )

    assert isinstance(
        metrics,
        PipelineMetrics,
    )
    assert metrics.rows_read == 1000
    assert metrics.rows_written == 950
    assert metrics.chunks_processed == 10
    assert metrics.chunks_failed == 1
    assert metrics.rows_rejected == 50
    assert metrics.input_memory_bytes == 10_000
    assert metrics.output_memory_bytes == 8_000
    assert metrics.elapsed_seconds == 5.0
    assert metrics.throughput_rows_per_second == 200.0


def test_pipeline_metrics_returns_zero_throughput_for_non_positive_elapsed_time() -> None:
    metrics = PipelineMetrics(
        rows_read=100,
        rows_written=100,
        chunks_processed=1,
        chunks_failed=0,
        rows_rejected=0,
        input_memory_bytes=1000,
        output_memory_bytes=1000,
        elapsed_seconds=0.0,
    )

    assert metrics.throughput_rows_per_second == 0.0


def test_pipeline_result_exposes_processed_row_count(
    tmp_path: Path,
) -> None:
    metrics = PipelineMetrics(
        rows_read=100,
        rows_written=95,
        chunks_processed=5,
        chunks_failed=0,
        rows_rejected=5,
        input_memory_bytes=1000,
        output_memory_bytes=900,
        elapsed_seconds=2.0,
    )

    result = PipelineResult(
        output_path=tmp_path / "output.parquet",
        report_path=tmp_path / "report.parquet",
        metrics=metrics,
        validation=pipeline_module.ValidationResult(),
    )

    assert result.rows_processed == 95
    assert result.throughput_rows_per_second == 50.0


def test_pipeline_result_defaults_to_no_checkpoint_paths(
    tmp_path: Path,
) -> None:
    metrics = PipelineMetrics(
        rows_read=1,
        rows_written=1,
        chunks_processed=1,
        chunks_failed=0,
        rows_rejected=0,
        input_memory_bytes=100,
        output_memory_bytes=100,
        elapsed_seconds=1.0,
    )

    result = PipelineResult(
        output_path=tmp_path / "output.parquet",
        report_path=tmp_path / "report.parquet",
        metrics=metrics,
        validation=pipeline_module.ValidationResult(),
    )

    assert result.checkpoint_paths == ()


def test_cleanup_previous_run_removes_old_output_partitions(
    tmp_path: Path,
) -> None:
    configuration = _simple_pipeline_config(
        tmp_path
    )

    processed_dir = Path(
        configuration.processed_data_dir
    )
    processed_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    first = processed_dir / "part-00000001.parquet"
    second = processed_dir / "part-00000002.parquet"

    pd.DataFrame(
        {"id": [1]}
    ).to_parquet(
        first,
        index=False,
    )
    pd.DataFrame(
        {"id": [2]}
    ).to_parquet(
        second,
        index=False,
    )

    _cleanup_previous_run(
        configuration
    )

    assert not first.exists()
    assert not second.exists()


def test_cleanup_previous_run_preserves_outputs_when_resume_is_enabled(
    tmp_path: Path,
) -> None:
    configuration = _simple_pipeline_config(
        tmp_path,
        resume_enabled=True,
    )

    processed_dir = Path(
        configuration.processed_data_dir
    )
    processed_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    partition = (
        processed_dir
        / "part-00000001.parquet"
    )
    pd.DataFrame(
        {"id": [1]}
    ).to_parquet(
        partition,
        index=False,
    )

    _cleanup_previous_run(
        configuration
    )

    assert partition.exists()


def test_cleanup_previous_run_cleans_checkpoints_for_non_resumable_runs(
    tmp_path: Path,
) -> None:
    configuration = _simple_pipeline_config(
        tmp_path,
        checkpointing_enabled=True,
    )

    checkpoint_dir = Path(
        configuration.checkpoint_dir
    )
    checkpoint_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    checkpoint = (
        checkpoint_dir
        / "chunk-00000001.parquet"
    )
    pd.DataFrame(
        {"id": [1]}
    ).to_parquet(
        checkpoint,
        index=False,
    )

    _cleanup_previous_run(
        configuration
    )

    assert not checkpoint.exists()


def test_run_pipeline_writes_final_output_and_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuration = _simple_pipeline_config(
        tmp_path
    )

    output_dir = Path(
        configuration.processed_data_dir
    )
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    partition = (
        output_dir
        / "part-00000001.parquet"
    )

    expected_output = pd.DataFrame(
        {
            "order_id": [
                "1001",
                "1002",
            ],
            "amount": [
                100.0,
                200.0,
            ],
        }
    )

    expected_output.to_parquet(
        partition,
        index=False,
    )

    def fake_process_stream(
        pipeline_config: PipelineConfig,
        state: object,
    ) -> pipeline_module.ValidationResult:
        state.rows_read = 2
        state.rows_written = 2
        state.chunks_processed = 1
        state.input_memory_bytes = _memory_bytes(
            expected_output
        )
        state.output_memory_bytes = _memory_bytes(
            expected_output
        )
        return pipeline_module.ValidationResult()

    monkeypatch.setattr(
        pipeline_module,
        "_process_stream",
        fake_process_stream,
    )

    result = run_pipeline(
        pipeline_config=configuration,
    )

    assert result.output_path.exists()
    assert result.report_path.exists()

    output = pd.read_parquet(
        result.output_path
    )

    pd.testing.assert_frame_equal(
        output,
        expected_output,
    )

    report = pd.read_parquet(
        result.report_path
    )

    assert report["rows_read"].iloc[0] == 2
    assert report["rows_written"].iloc[0] == 2
    assert report["chunks_processed"].iloc[0] == 1


def test_run_pipeline_returns_validation_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuration = _simple_pipeline_config(
        tmp_path
    )

    output_dir = Path(
        configuration.processed_data_dir
    )
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    pd.DataFrame(
        {
            "order_id": ["1001"],
        }
    ).to_parquet(
        output_dir / "part-00000001.parquet",
        index=False,
    )

    monkeypatch.setattr(
        pipeline_module,
        "_process_stream",
        lambda pipeline_config, state: (
            setattr(state, "rows_read", 1),
            setattr(state, "rows_written", 1),
            setattr(state, "chunks_processed", 1),
            pipeline_module.ValidationResult(),
        )[-1],
    )

    result = run_pipeline(
        pipeline_config=configuration,
    )

    assert isinstance(
        result.validation,
        pipeline_module.ValidationResult,
    )
    assert result.validation.is_valid


def test_run_pipeline_wraps_storage_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuration = _simple_pipeline_config(
        tmp_path
    )

    monkeypatch.setattr(
        pipeline_module,
        "_process_stream",
        lambda pipeline_config, state: pipeline_module.ValidationResult(),
    )

    def fail_output(
        pipeline_config: PipelineConfig,
    ) -> Path:
        raise pipeline_module.StorageError(
            "cannot write output"
        )

    monkeypatch.setattr(
        pipeline_module,
        "_write_final_output",
        fail_output,
    )

    with pytest.raises(
        PipelineError,
        match="output",
    ):
        run_pipeline(
            pipeline_config=configuration,
        )


def test_run_pipeline_wraps_unexpected_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuration = _simple_pipeline_config(
        tmp_path
    )

    def fail_stream(
        pipeline_config: PipelineConfig,
        state: object,
    ) -> pipeline_module.ValidationResult:
        raise RuntimeError(
            "unexpected failure"
        )

    monkeypatch.setattr(
        pipeline_module,
        "_process_stream",
        fail_stream,
    )

    with pytest.raises(
        PipelineError,
        match="pipeline execution failed",
    ):
        run_pipeline(
            pipeline_config=configuration,
        )


def test_run_returns_zero_for_successful_pipeline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuration = _simple_pipeline_config(
        tmp_path
    )

    metrics = PipelineMetrics(
        rows_read=1,
        rows_written=1,
        chunks_processed=1,
        chunks_failed=0,
        rows_rejected=0,
        input_memory_bytes=100,
        output_memory_bytes=100,
        elapsed_seconds=1.0,
    )

    result = PipelineResult(
        output_path=tmp_path / "output.parquet",
        report_path=tmp_path / "report.parquet",
        metrics=metrics,
        validation=pipeline_module.ValidationResult(),
    )

    monkeypatch.setattr(
        pipeline_module,
        "run_pipeline",
        lambda pipeline_config: result,
    )

    assert run(
        pipeline_config=configuration,
    ) == 0


def test_run_returns_one_when_pipeline_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuration = _simple_pipeline_config(
        tmp_path
    )

    def fail(
        pipeline_config: PipelineConfig,
    ) -> PipelineResult:
        raise PipelineError(
            "pipeline failed"
        )

    monkeypatch.setattr(
        pipeline_module,
        "run_pipeline",
        fail,
    )

    assert run(
        pipeline_config=configuration,
    ) == 1


def test_run_returns_one_when_strict_validation_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuration = _simple_pipeline_config(
        tmp_path,
        fail_on_validation=True,
    )

    invalid = pipeline_module.ValidationResult(
        issues=(
            pipeline_module.ValidationIssue(
                check="numeric",
                message="Invalid numeric data.",
                column="amount",
                row_count=1,
            ),
        )
    )

    metrics = PipelineMetrics(
        rows_read=1,
        rows_written=1,
        chunks_processed=1,
        chunks_failed=0,
        rows_rejected=0,
        input_memory_bytes=100,
        output_memory_bytes=100,
        elapsed_seconds=1.0,
    )

    result = PipelineResult(
        output_path=tmp_path / "output.parquet",
        report_path=tmp_path / "report.parquet",
        metrics=metrics,
        validation=invalid,
    )

    monkeypatch.setattr(
        pipeline_module,
        "run_pipeline",
        lambda pipeline_config: result,
    )

    assert run(
        pipeline_config=configuration,
    ) == 1


def test_run_allows_invalid_validation_when_strict_mode_is_disabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuration = _simple_pipeline_config(
        tmp_path,
        fail_on_validation=False,
    )

    invalid = pipeline_module.ValidationResult(
        issues=(
            pipeline_module.ValidationIssue(
                check="numeric",
                message="Invalid numeric data.",
                column="amount",
                row_count=1,
            ),
        )
    )

    metrics = PipelineMetrics(
        rows_read=1,
        rows_written=1,
        chunks_processed=1,
        chunks_failed=0,
        rows_rejected=0,
        input_memory_bytes=100,
        output_memory_bytes=100,
        elapsed_seconds=1.0,
    )

    result = PipelineResult(
        output_path=tmp_path / "output.parquet",
        report_path=tmp_path / "report.parquet",
        metrics=metrics,
        validation=invalid,
    )

    monkeypatch.setattr(
        pipeline_module,
        "run_pipeline",
        lambda pipeline_config: result,
    )

    assert run(
        pipeline_config=configuration,
    ) == 0


def test_run_pipeline_creates_required_directories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuration = _simple_pipeline_config(
        tmp_path,
        create_directories=True,
    )

    processed_dir = Path(
        configuration.processed_data_dir
    )
    reports_dir = Path(
        configuration.report_path
    ).parent

    assert not processed_dir.exists()
    assert not reports_dir.exists()

    monkeypatch.setattr(
        pipeline_module,
        "_process_stream",
        lambda pipeline_config, state: pipeline_module.ValidationResult(),
    )

    with pytest.raises(
        PipelineError,
    ):
        run_pipeline(
            pipeline_config=configuration,
        )

    assert processed_dir.exists()
    assert reports_dir.exists()


def test_pipeline_result_preserves_checkpoint_paths(
    tmp_path: Path,
) -> None:
    checkpoints = (
        tmp_path / "chunk-00000001.parquet",
        tmp_path / "chunk-00000002.parquet",
    )

    metrics = PipelineMetrics(
        rows_read=10,
        rows_written=10,
        chunks_processed=2,
        chunks_failed=0,
        rows_rejected=0,
        input_memory_bytes=1000,
        output_memory_bytes=1000,
        elapsed_seconds=1.0,
    )

    result = PipelineResult(
        output_path=tmp_path / "output.parquet",
        report_path=tmp_path / "report.parquet",
        metrics=metrics,
        validation=pipeline_module.ValidationResult(),
        checkpoint_paths=checkpoints,
    )

    assert result.checkpoint_paths == checkpoints


def test_build_processing_report_uses_pipeline_input_and_output_paths(
    tmp_path: Path,
) -> None:
    configuration = _simple_pipeline_config(
        tmp_path
    )

    state = pipeline_module._PipelineState(
        rows_read=10
    )

    report = _build_processing_report(
        state,
        pipeline_config=configuration,
        elapsed_seconds=2.0,
    )

    row = report.iloc[0]

    assert row["input_path"] == str(
        configuration.input_path
    )
    assert row["output_path"] == str(
        configuration.output_path
    )


def test_pipeline_metrics_throughput_uses_rows_read(
) -> None:
    metrics = PipelineMetrics(
        rows_read=500,
        rows_written=450,
        chunks_processed=5,
        chunks_failed=0,
        rows_rejected=50,
        input_memory_bytes=5000,
        output_memory_bytes=4500,
        elapsed_seconds=2.5,
    )

    assert metrics.throughput_rows_per_second == pytest.approx(
        200.0
    )