from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Any

import pandas as pd

from .aggregation import (
    aggregate_overall_metrics,
)
from .chunk_processor import (
    ProcessingMetrics,
    iter_processed_chunks,
)
from .config import PipelineConfig, config
from .ingestion import IngestionError, iter_validated_chunks
from .storage import (
    StorageError,
    cleanup_checkpoints,
    write_checkpoint,
    write_parquet,
    write_partition,
    write_processing_report,
)
from .transformation import (
    TransformationError,
    transform_chunk,
)
from .validation import (
    ValidationError,
    ValidationResult,
    assert_valid,
    validate_chunk,
    validate_global_dataset,
)


class PipelineError(RuntimeError):
    """Raised when the large-dataset pipeline cannot complete successfully."""


@dataclass(frozen=True, slots=True)
class PipelineMetrics:
    """Represent operational metrics produced by a pipeline run."""

    rows_read: int
    rows_written: int
    chunks_processed: int
    chunks_failed: int
    rows_rejected: int
    input_memory_bytes: int
    output_memory_bytes: int
    elapsed_seconds: float

    @property
    def throughput_rows_per_second(self) -> float:
        """Return processed-row throughput for the completed run."""
        if self.elapsed_seconds <= 0:
            return 0.0

        return self.rows_read / self.elapsed_seconds


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """Represent the result of a large-dataset pipeline execution."""

    output_path: Path
    report_path: Path
    metrics: PipelineMetrics
    validation: ValidationResult
    checkpoint_paths: tuple[Path, ...] = field(
        default_factory=tuple
    )

    @property
    def rows_processed(self) -> int:
        """Return the number of successfully written rows."""
        return self.metrics.rows_written

    @property
    def throughput_rows_per_second(self) -> float:
        """Return processed-row throughput."""
        return self.metrics.throughput_rows_per_second


@dataclass(slots=True)
class _PipelineState:
    """Maintain internal counters while processing chunks."""

    rows_read: int = 0
    rows_written: int = 0
    chunks_processed: int = 0
    chunks_failed: int = 0
    rows_rejected: int = 0
    input_memory_bytes: int = 0
    output_memory_bytes: int = 0
    checkpoint_paths: list[Path] = field(
        default_factory=list
    )


def _memory_bytes(
    frame: pd.DataFrame,
) -> int:
    """Return the deep memory footprint of a DataFrame."""
    return int(
        frame.memory_usage(
            index=True,
            deep=True,
        ).sum()
    )


def _validate_configuration(
    pipeline_config: PipelineConfig,
) -> None:
    """Validate runtime configuration before processing starts."""
    try:
        pipeline_config.validate()
    except (
        ValueError,
        TypeError,
        OSError,
    ) as exc:
        raise PipelineError(
            "Invalid pipeline configuration."
        ) from exc

    if not pipeline_config.input_path:
        raise PipelineError(
            "An input_path must be configured."
        )

    input_path = Path(
        pipeline_config.input_path
    ).expanduser()

    if not input_path.exists():
        raise PipelineError(
            f"Configured input file does not exist: {input_path}"
        )

    if not input_path.is_file():
        raise PipelineError(
            f"Configured input path is not a file: {input_path}"
        )


def _validate_chunk(
    frame: pd.DataFrame,
    pipeline_config: PipelineConfig,
) -> ValidationResult:
    """Run configured validation checks against one processed chunk."""
    result = validate_chunk(
        frame,
        required_columns=pipeline_config.required_columns,
        required_value_columns=pipeline_config.required_columns,
        unique_key_columns=pipeline_config.identifier_columns,
        numeric_columns=pipeline_config.numeric_columns,
        non_negative_columns=pipeline_config.numeric_columns,
        datetime_columns=pipeline_config.timestamp_columns,
        require_non_empty=False,
        maximum_memory_bytes=(
            pipeline_config.target_memory_mb * 1024 * 1024
            if pipeline_config.target_memory_mb > 0
            else None
        ),
    )

    if (
        not result.is_valid
        and pipeline_config.fail_on_validation
    ):
        assert_valid(result)

    return result


def _transform(
    frame: pd.DataFrame,
    metadata: Any,
    pipeline_config: PipelineConfig,
) -> pd.DataFrame:
    """Transform one validated chunk using the project's transformation layer."""
    try:
        transformed = transform_chunk(
            frame,
            pipeline_config=pipeline_config,
        )
    except TransformationError:
        raise
    except Exception as exc:
        raise TransformationError(
            "Unexpected error while transforming a dataset chunk."
        ) from exc

    validation = _validate_chunk(
        transformed,
        pipeline_config,
    )

    if (
        not validation.is_valid
        and pipeline_config.fail_on_validation
    ):
        assert_valid(validation)

    return transformed


def _write_output_partition(
    frame: pd.DataFrame,
    *,
    chunk_number: int,
    pipeline_config: PipelineConfig,
) -> Path:
    """Write one processed chunk as a durable partition."""
    destination_dir = Path(
        pipeline_config.processed_data_dir
    )

    return write_partition(
        frame,
        destination_dir,
        partition_number=chunk_number,
        pipeline_config=pipeline_config,
    )


def _write_final_output(
    pipeline_config: PipelineConfig,
) -> Path:
    """Build the final output from processed Parquet partitions."""
    processed_dir = Path(
        pipeline_config.processed_data_dir
    )

    partitions = sorted(
        processed_dir.glob(
            "part-*.parquet"
        )
    )

    output_path = Path(
        pipeline_config.output_path
    )

    if not partitions:
        empty = pd.DataFrame()
        return write_parquet(
            empty,
            output_path,
            pipeline_config=pipeline_config,
        )

    frames = [
        pd.read_parquet(path)
        for path in partitions
    ]

    combined = pd.concat(
        frames,
        ignore_index=True,
    )

    return write_parquet(
        combined,
        output_path,
        pipeline_config=pipeline_config,
    )


def _build_processing_report(
    state: _PipelineState,
    *,
    pipeline_config: PipelineConfig,
    elapsed_seconds: float,
) -> pd.DataFrame:
    """Build an operational metrics report for the completed run."""
    throughput = (
        state.rows_read / elapsed_seconds
        if elapsed_seconds > 0
        else 0.0
    )

    return pd.DataFrame(
        [
            {
                "pipeline": pipeline_config.pipeline_name,
                "input_path": str(
                    pipeline_config.input_path
                ),
                "output_path": str(
                    pipeline_config.output_path
                ),
                "rows_read": state.rows_read,
                "rows_written": state.rows_written,
                "rows_rejected": state.rows_rejected,
                "chunks_processed": state.chunks_processed,
                "chunks_failed": state.chunks_failed,
                "input_memory_bytes": (
                    state.input_memory_bytes
                ),
                "output_memory_bytes": (
                    state.output_memory_bytes
                ),
                "elapsed_seconds": elapsed_seconds,
                "throughput_rows_per_second": throughput,
            }
        ]
    )


def _build_pipeline_metrics(
    state: _PipelineState,
    *,
    elapsed_seconds: float,
) -> PipelineMetrics:
    """Convert mutable execution state into immutable run metrics."""
    return PipelineMetrics(
        rows_read=state.rows_read,
        rows_written=state.rows_written,
        chunks_processed=state.chunks_processed,
        chunks_failed=state.chunks_failed,
        rows_rejected=state.rows_rejected,
        input_memory_bytes=state.input_memory_bytes,
        output_memory_bytes=state.output_memory_bytes,
        elapsed_seconds=elapsed_seconds,
    )


def _process_stream(
    pipeline_config: PipelineConfig,
    state: _PipelineState,
) -> ValidationResult:
    """Stream input chunks through transformation and persistence."""
    aggregate_validation = ValidationResult()

    try:
        input_chunks = iter_validated_chunks(
            pipeline_config
        )
    except IngestionError as exc:
        raise PipelineError(
            "Unable to initialize dataset ingestion."
        ) from exc

    def transformer(
        frame: pd.DataFrame,
        metadata: Any,
    ) -> pd.DataFrame:
        nonlocal aggregate_validation

        state.rows_read += len(frame)
        state.input_memory_bytes += _memory_bytes(
            frame
        )

        validation = _validate_chunk(
            frame,
            pipeline_config,
        )
        aggregate_validation = aggregate_validation.extend(
            validation
        )

        if (
            not validation.is_valid
            and pipeline_config.fail_on_validation
        ):
            assert_valid(validation)

        transformed = _transform(
            frame,
            metadata,
            pipeline_config,
        )

        state.output_memory_bytes += _memory_bytes(
            transformed
        )
        state.rows_written += len(
            transformed
        )

        return transformed

    try:
        processed_chunks = iter_processed_chunks(
            input_chunks,
            transformer=transformer,
        )

        for result in processed_chunks:
            state.chunks_processed += 1

            output_path = _write_output_partition(
                result.data,
                chunk_number=result.metadata.chunk_number,
                pipeline_config=pipeline_config,
            )

            if pipeline_config.checkpointing_enabled:
                checkpoint_path = write_checkpoint(
                    result.data,
                    pipeline_config.checkpoint_dir,
                    chunk_number=result.metadata.chunk_number,
                    pipeline_config=pipeline_config,
                )
                state.checkpoint_paths.append(
                    checkpoint_path
                )

            if result.metrics.rows_processed == 0:
                state.rows_rejected += (
                    result.metadata.row_count
                )

            _ = output_path

    except (
        IngestionError,
        TransformationError,
        ValidationError,
        StorageError,
    ) as exc:
        state.chunks_failed += 1
        raise PipelineError(
            "Dataset processing failed while handling a chunk."
        ) from exc
    except Exception as exc:
        state.chunks_failed += 1
        raise PipelineError(
            "Unexpected error during dataset processing."
        ) from exc

    return aggregate_validation


def _validate_final_output(
    output: pd.DataFrame,
    pipeline_config: PipelineConfig,
) -> ValidationResult:
    """Run dataset-wide validation after all partitions are combined."""
    result = validate_global_dataset(
        output,
        required_columns=pipeline_config.required_columns,
        unique_key_columns=pipeline_config.identifier_columns,
        numeric_columns=pipeline_config.numeric_columns,
        non_negative_columns=pipeline_config.numeric_columns,
        datetime_columns=pipeline_config.timestamp_columns,
    )

    if (
        not result.is_valid
        and pipeline_config.fail_on_validation
    ):
        assert_valid(result)

    return result


def _cleanup_previous_run(
    pipeline_config: PipelineConfig,
) -> None:
    """Remove output partitions left by a previous non-resumable run."""
    if pipeline_config.resume_enabled:
        return

    processed_dir = Path(
        pipeline_config.processed_data_dir
    )

    if not processed_dir.exists():
        return

    for path in processed_dir.glob(
        "part-*.parquet"
    ):
        try:
            path.unlink()
        except OSError as exc:
            raise PipelineError(
                f"Failed to clean previous output partition: {path}"
            ) from exc

    if pipeline_config.checkpointing_enabled:
        try:
            cleanup_checkpoints(
                pipeline_config.checkpoint_dir
            )
        except StorageError as exc:
            raise PipelineError(
                "Failed to clean previous checkpoints."
            ) from exc


def run_pipeline(
    *,
    pipeline_config: PipelineConfig = config,
) -> PipelineResult:
    """Execute the complete large-dataset processing workflow."""
    started_at = perf_counter()

    _validate_configuration(
        pipeline_config
    )

    try:
        if pipeline_config.create_directories:
            pipeline_config.ensure_directories()

        _cleanup_previous_run(
            pipeline_config
        )

        state = _PipelineState()

        validation = _process_stream(
            pipeline_config,
            state,
        )

        output_path = _write_final_output(
            pipeline_config
        )

        final_output = pd.read_parquet(
            output_path
        )

        final_validation = _validate_final_output(
            final_output,
            pipeline_config,
        )
        validation = validation.extend(
            final_validation
        )

        elapsed_seconds = (
            perf_counter()
            - started_at
        )

        report = _build_processing_report(
            state,
            pipeline_config=pipeline_config,
            elapsed_seconds=elapsed_seconds,
        )

        report_path = write_processing_report(
            report,
            pipeline_config.report_path,
            pipeline_config=pipeline_config,
        )

        metrics = _build_pipeline_metrics(
            state,
            elapsed_seconds=elapsed_seconds,
        )

        return PipelineResult(
            output_path=output_path,
            report_path=report_path,
            metrics=metrics,
            validation=validation,
            checkpoint_paths=tuple(
                state.checkpoint_paths
            ),
        )

    except PipelineError:
        raise
    except (
        StorageError,
        ValidationError,
        IngestionError,
        TransformationError,
        OSError,
        ValueError,
    ) as exc:
        raise PipelineError(
            "Large-dataset pipeline execution failed."
        ) from exc
    except Exception as exc:
        raise PipelineError(
            "Unexpected failure during large-dataset pipeline execution."
        ) from exc


def run(
    *,
    pipeline_config: PipelineConfig = config,
) -> int:
    """Run the pipeline and return a process-compatible exit code."""
    try:
        result = run_pipeline(
            pipeline_config=pipeline_config
        )

    except PipelineError:
        return 1

    if (
        pipeline_config.fail_on_validation
        and not result.validation.is_valid
    ):
        return 1

    return 0


def main() -> int:
    """Execute the pipeline using the global project configuration."""
    return run(
        pipeline_config=config
    )


__all__ = [
    "PipelineError",
    "PipelineMetrics",
    "PipelineResult",
    "main",
    "run",
    "run_pipeline",
]

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Any

import pandas as pd

from .aggregation import (
    aggregate_overall_metrics,
)
from .chunk_processor import (
    ProcessingMetrics,
    iter_processed_chunks,
)
from .config import PipelineConfig, config
from .ingestion import IngestionError, iter_validated_chunks
from .storage import (
    StorageError,
    cleanup_checkpoints,
    write_checkpoint,
    write_parquet,
    write_partition,
    write_processing_report,
)
from .transformation import (
    TransformationError,
    transform_chunk,
)
from .validation import (
    ValidationError,
    ValidationResult,
    assert_valid,
    validate_chunk,
    validate_global_dataset,
)


class PipelineError(RuntimeError):
    """Raised when the large-dataset pipeline cannot complete successfully."""


@dataclass(frozen=True, slots=True)
class PipelineMetrics:
    """Represent operational metrics produced by a pipeline run."""

    rows_read: int
    rows_written: int
    chunks_processed: int
    chunks_failed: int
    rows_rejected: int
    input_memory_bytes: int
    output_memory_bytes: int
    elapsed_seconds: float

    @property
    def throughput_rows_per_second(self) -> float:
        """Return processed-row throughput for the completed run."""
        if self.elapsed_seconds <= 0:
            return 0.0

        return self.rows_read / self.elapsed_seconds


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """Represent the result of a large-dataset pipeline execution."""

    output_path: Path
    report_path: Path
    metrics: PipelineMetrics
    validation: ValidationResult
    checkpoint_paths: tuple[Path, ...] = field(
        default_factory=tuple
    )

    @property
    def rows_processed(self) -> int:
        """Return the number of successfully written rows."""
        return self.metrics.rows_written

    @property
    def throughput_rows_per_second(self) -> float:
        """Return processed-row throughput."""
        return self.metrics.throughput_rows_per_second


@dataclass(slots=True)
class _PipelineState:
    """Maintain internal counters while processing chunks."""

    rows_read: int = 0
    rows_written: int = 0
    chunks_processed: int = 0
    chunks_failed: int = 0
    rows_rejected: int = 0
    input_memory_bytes: int = 0
    output_memory_bytes: int = 0
    checkpoint_paths: list[Path] = field(
        default_factory=list
    )


def _memory_bytes(
    frame: pd.DataFrame,
) -> int:
    """Return the deep memory footprint of a DataFrame."""
    return int(
        frame.memory_usage(
            index=True,
            deep=True,
        ).sum()
    )


def _validate_configuration(
    pipeline_config: PipelineConfig,
) -> None:
    """Validate runtime configuration before processing starts."""
    try:
        pipeline_config.validate()
    except (
        ValueError,
        TypeError,
        OSError,
    ) as exc:
        raise PipelineError(
            "Invalid pipeline configuration."
        ) from exc

    if not pipeline_config.input_path:
        raise PipelineError(
            "An input_path must be configured."
        )

    input_path = Path(
        pipeline_config.input_path
    ).expanduser()

    if not input_path.exists():
        raise PipelineError(
            f"Configured input file does not exist: {input_path}"
        )

    if not input_path.is_file():
        raise PipelineError(
            f"Configured input path is not a file: {input_path}"
        )


def _validate_chunk(
    frame: pd.DataFrame,
    pipeline_config: PipelineConfig,
) -> ValidationResult:
    """Run configured validation checks against one processed chunk."""
    result = validate_chunk(
        frame,
        required_columns=pipeline_config.required_columns,
        required_value_columns=pipeline_config.required_columns,
        unique_key_columns=pipeline_config.identifier_columns,
        numeric_columns=pipeline_config.numeric_columns,
        non_negative_columns=pipeline_config.numeric_columns,
        datetime_columns=pipeline_config.timestamp_columns,
        require_non_empty=False,
        maximum_memory_bytes=(
            pipeline_config.target_memory_mb * 1024 * 1024
            if pipeline_config.target_memory_mb > 0
            else None
        ),
    )

    if (
        not result.is_valid
        and pipeline_config.fail_on_validation
    ):
        assert_valid(result)

    return result


def _transform(
    frame: pd.DataFrame,
    metadata: Any,
    pipeline_config: PipelineConfig,
) -> pd.DataFrame:
    """Transform one validated chunk using the project's transformation layer."""
    try:
        transformed = transform_chunk(
            frame,
            pipeline_config=pipeline_config,
        )
    except TransformationError:
        raise
    except Exception as exc:
        raise TransformationError(
            "Unexpected error while transforming a dataset chunk."
        ) from exc

    validation = _validate_chunk(
        transformed,
        pipeline_config,
    )

    if (
        not validation.is_valid
        and pipeline_config.fail_on_validation
    ):
        assert_valid(validation)

    return transformed


def _write_output_partition(
    frame: pd.DataFrame,
    *,
    chunk_number: int,
    pipeline_config: PipelineConfig,
) -> Path:
    """Write one processed chunk as a durable partition."""
    destination_dir = Path(
        pipeline_config.processed_data_dir
    )

    return write_partition(
        frame,
        destination_dir,
        partition_number=chunk_number,
        pipeline_config=pipeline_config,
    )


def _write_final_output(
    pipeline_config: PipelineConfig,
) -> Path:
    """Build the final output from processed Parquet partitions."""
    processed_dir = Path(
        pipeline_config.processed_data_dir
    )

    partitions = sorted(
        processed_dir.glob(
            "part-*.parquet"
        )
    )

    output_path = Path(
        pipeline_config.output_path
    )

    if not partitions:
        empty = pd.DataFrame()
        return write_parquet(
            empty,
            output_path,
            pipeline_config=pipeline_config,
        )

    frames = [
        pd.read_parquet(path)
        for path in partitions
    ]

    combined = pd.concat(
        frames,
        ignore_index=True,
    )

    return write_parquet(
        combined,
        output_path,
        pipeline_config=pipeline_config,
    )


def _build_processing_report(
    state: _PipelineState,
    *,
    pipeline_config: PipelineConfig,
    elapsed_seconds: float,
) -> pd.DataFrame:
    """Build an operational metrics report for the completed run."""
    throughput = (
        state.rows_read / elapsed_seconds
        if elapsed_seconds > 0
        else 0.0
    )

    return pd.DataFrame(
        [
            {
                "pipeline": pipeline_config.pipeline_name,
                "input_path": str(
                    pipeline_config.input_path
                ),
                "output_path": str(
                    pipeline_config.output_path
                ),
                "rows_read": state.rows_read,
                "rows_written": state.rows_written,
                "rows_rejected": state.rows_rejected,
                "chunks_processed": state.chunks_processed,
                "chunks_failed": state.chunks_failed,
                "input_memory_bytes": (
                    state.input_memory_bytes
                ),
                "output_memory_bytes": (
                    state.output_memory_bytes
                ),
                "elapsed_seconds": elapsed_seconds,
                "throughput_rows_per_second": throughput,
            }
        ]
    )


def _build_pipeline_metrics(
    state: _PipelineState,
    *,
    elapsed_seconds: float,
) -> PipelineMetrics:
    """Convert mutable execution state into immutable run metrics."""
    return PipelineMetrics(
        rows_read=state.rows_read,
        rows_written=state.rows_written,
        chunks_processed=state.chunks_processed,
        chunks_failed=state.chunks_failed,
        rows_rejected=state.rows_rejected,
        input_memory_bytes=state.input_memory_bytes,
        output_memory_bytes=state.output_memory_bytes,
        elapsed_seconds=elapsed_seconds,
    )


def _process_stream(
    pipeline_config: PipelineConfig,
    state: _PipelineState,
) -> ValidationResult:
    """Stream input chunks through transformation and persistence."""
    aggregate_validation = ValidationResult()

    try:
        input_chunks = iter_validated_chunks(
            pipeline_config
        )
    except IngestionError as exc:
        raise PipelineError(
            "Unable to initialize dataset ingestion."
        ) from exc

    def transformer(
        frame: pd.DataFrame,
        metadata: Any,
    ) -> pd.DataFrame:
        nonlocal aggregate_validation

        state.rows_read += len(frame)
        state.input_memory_bytes += _memory_bytes(
            frame
        )

        validation = _validate_chunk(
            frame,
            pipeline_config,
        )
        aggregate_validation = aggregate_validation.extend(
            validation
        )

        if (
            not validation.is_valid
            and pipeline_config.fail_on_validation
        ):
            assert_valid(validation)

        transformed = _transform(
            frame,
            metadata,
            pipeline_config,
        )

        state.output_memory_bytes += _memory_bytes(
            transformed
        )
        state.rows_written += len(
            transformed
        )

        return transformed

    try:
        processed_chunks = iter_processed_chunks(
            input_chunks,
            transformer=transformer,
        )

        for result in processed_chunks:
            state.chunks_processed += 1

            output_path = _write_output_partition(
                result.data,
                chunk_number=result.metadata.chunk_number,
                pipeline_config=pipeline_config,
            )

            if pipeline_config.checkpointing_enabled:
                checkpoint_path = write_checkpoint(
                    result.data,
                    pipeline_config.checkpoint_dir,
                    chunk_number=result.metadata.chunk_number,
                    pipeline_config=pipeline_config,
                )
                state.checkpoint_paths.append(
                    checkpoint_path
                )

            if result.metrics.rows_processed == 0:
                state.rows_rejected += (
                    result.metadata.row_count
                )

            _ = output_path

    except (
        IngestionError,
        TransformationError,
        ValidationError,
        StorageError,
    ) as exc:
        state.chunks_failed += 1
        raise PipelineError(
            "Dataset processing failed while handling a chunk."
        ) from exc
    except Exception as exc:
        state.chunks_failed += 1
        raise PipelineError(
            "Unexpected error during dataset processing."
        ) from exc

    return aggregate_validation


def _validate_final_output(
    output: pd.DataFrame,
    pipeline_config: PipelineConfig,
) -> ValidationResult:
    """Run dataset-wide validation after all partitions are combined."""
    result = validate_global_dataset(
        output,
        required_columns=pipeline_config.required_columns,
        unique_key_columns=pipeline_config.identifier_columns,
        numeric_columns=pipeline_config.numeric_columns,
        non_negative_columns=pipeline_config.numeric_columns,
        datetime_columns=pipeline_config.timestamp_columns,
    )

    if (
        not result.is_valid
        and pipeline_config.fail_on_validation
    ):
        assert_valid(result)

    return result


def _cleanup_previous_run(
    pipeline_config: PipelineConfig,
) -> None:
    """Remove output partitions left by a previous non-resumable run."""
    if pipeline_config.resume_enabled:
        return

    processed_dir = Path(
        pipeline_config.processed_data_dir
    )

    if not processed_dir.exists():
        return

    for path in processed_dir.glob(
        "part-*.parquet"
    ):
        try:
            path.unlink()
        except OSError as exc:
            raise PipelineError(
                f"Failed to clean previous output partition: {path}"
            ) from exc

    if pipeline_config.checkpointing_enabled:
        try:
            cleanup_checkpoints(
                pipeline_config.checkpoint_dir
            )
        except StorageError as exc:
            raise PipelineError(
                "Failed to clean previous checkpoints."
            ) from exc


def run_pipeline(
    *,
    pipeline_config: PipelineConfig = config,
) -> PipelineResult:
    """Execute the complete large-dataset processing workflow."""
    started_at = perf_counter()

    _validate_configuration(
        pipeline_config
    )

    try:
        if pipeline_config.create_directories:
            pipeline_config.ensure_directories()

        _cleanup_previous_run(
            pipeline_config
        )

        state = _PipelineState()

        validation = _process_stream(
            pipeline_config,
            state,
        )

        output_path = _write_final_output(
            pipeline_config
        )

        final_output = pd.read_parquet(
            output_path
        )

        final_validation = _validate_final_output(
            final_output,
            pipeline_config,
        )
        validation = validation.extend(
            final_validation
        )

        elapsed_seconds = (
            perf_counter()
            - started_at
        )

        report = _build_processing_report(
            state,
            pipeline_config=pipeline_config,
            elapsed_seconds=elapsed_seconds,
        )

        report_path = write_processing_report(
            report,
            pipeline_config.report_path,
            pipeline_config=pipeline_config,
        )

        metrics = _build_pipeline_metrics(
            state,
            elapsed_seconds=elapsed_seconds,
        )

        return PipelineResult(
            output_path=output_path,
            report_path=report_path,
            metrics=metrics,
            validation=validation,
            checkpoint_paths=tuple(
                state.checkpoint_paths
            ),
        )

    except PipelineError:
        raise
    except (
        StorageError,
        ValidationError,
        IngestionError,
        TransformationError,
        OSError,
        ValueError,
    ) as exc:
        raise PipelineError(
            "Large-dataset pipeline execution failed."
        ) from exc
    except Exception as exc:
        raise PipelineError(
            "Unexpected failure during large-dataset pipeline execution."
        ) from exc


def run(
    *,
    pipeline_config: PipelineConfig = config,
) -> int:
    """Run the pipeline and return a process-compatible exit code."""
    try:
        result = run_pipeline(
            pipeline_config=pipeline_config
        )

    except PipelineError:
        return 1

    if (
        pipeline_config.fail_on_validation
        and not result.validation.is_valid
    ):
        return 1

    return 0


def main() -> int:
    """Execute the pipeline using the global project configuration."""
    return run(
        pipeline_config=config
    )


__all__ = [
    "PipelineError",
    "PipelineMetrics",
    "PipelineResult",
    "main",
    "run",
    "run_pipeline",
]