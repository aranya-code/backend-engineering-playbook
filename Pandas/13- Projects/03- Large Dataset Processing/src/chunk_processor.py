from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .config import PipelineConfig, config
from .ingestion import ChunkMetadata, IngestionError, iter_validated_chunks


class ChunkProcessingError(RuntimeError):
    """Raised when a dataset chunk cannot be processed safely."""


@dataclass(frozen=True, slots=True)
class ChunkResult:
    """Represent the result produced by processing one data chunk."""

    chunk_number: int
    input_rows: int
    output_rows: int
    input_memory_bytes: int
    output_memory_bytes: int
    data: pd.DataFrame


@dataclass(frozen=True, slots=True)
class ProcessingMetrics:
    """Represent aggregate metrics for a chunk-processing run."""

    chunks_processed: int
    input_rows: int
    output_rows: int
    input_memory_bytes: int
    output_memory_bytes: int
    rows_removed: int


@dataclass(frozen=True, slots=True)
class ProcessingResult:
    """Represent the complete output of a chunk-processing operation."""

    chunks: tuple[ChunkResult, ...]
    metrics: ProcessingMetrics


ChunkTransformer = Callable[
    [pd.DataFrame, ChunkMetadata],
    pd.DataFrame,
]


def _validate_chunk_result(
    result: pd.DataFrame,
) -> None:
    """Validate that a transformer returned a DataFrame."""
    if not isinstance(result, pd.DataFrame):
        raise ChunkProcessingError(
            "Chunk transformer must return a pandas DataFrame."
        )


def _calculate_memory_bytes(
    frame: pd.DataFrame,
) -> int:
    """Return the deep memory footprint of a DataFrame."""
    return int(
        frame.memory_usage(
            index=True,
            deep=True,
        ).sum()
    )


def _normalize_transformer_result(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Reset the processed chunk index without changing its rows."""
    return frame.reset_index(
        drop=True
    )


def process_chunk(
    frame: pd.DataFrame,
    metadata: ChunkMetadata,
    transformer: ChunkTransformer,
) -> ChunkResult:
    """Transform a single dataset chunk and collect processing metrics."""
    if not isinstance(frame, pd.DataFrame):
        raise ChunkProcessingError(
            "Input chunk must be a pandas DataFrame."
        )

    input_rows = len(frame)
    input_memory_bytes = _calculate_memory_bytes(
        frame
    )

    try:
        transformed = transformer(
            frame,
            metadata,
        )
    except Exception as exc:
        raise ChunkProcessingError(
            f"Failed to process chunk {metadata.chunk_number}."
        ) from exc

    _validate_chunk_result(
        transformed
    )

    transformed = _normalize_transformer_result(
        transformed
    )

    return ChunkResult(
        chunk_number=metadata.chunk_number,
        input_rows=input_rows,
        output_rows=len(transformed),
        input_memory_bytes=input_memory_bytes,
        output_memory_bytes=_calculate_memory_bytes(
            transformed
        ),
        data=transformed,
    )


def iter_processed_chunks(
    transformer: ChunkTransformer,
    source_path: Path | None = None,
    *,
    pipeline_config: PipelineConfig = config,
) -> Iterator[ChunkResult]:
    """Read, validate, and transform a dataset incrementally."""
    if not callable(transformer):
        raise ChunkProcessingError(
            "transformer must be callable."
        )

    try:
        for metadata, frame in iter_validated_chunks(
            source_path,
            pipeline_config=pipeline_config,
        ):
            yield process_chunk(
                frame,
                metadata,
                transformer,
            )
    except IngestionError as exc:
        raise ChunkProcessingError(
            "Failed while reading dataset chunks."
        ) from exc
    except ChunkProcessingError:
        raise


def _write_checkpoint(
    frame: pd.DataFrame,
    *,
    chunk_number: int,
    pipeline_config: PipelineConfig,
) -> Path:
    """Persist one processed chunk as a resumable checkpoint."""
    checkpoint_dir = pipeline_config.checkpoint_dir
    checkpoint_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    checkpoint_path = (
        checkpoint_dir
        / f"chunk-{chunk_number:08d}.parquet"
    )
    temporary_path = checkpoint_path.with_suffix(
        ".parquet.tmp"
    )

    try:
        frame.to_parquet(
            temporary_path,
            **pipeline_config.parquet_write_kwargs,
        )
        temporary_path.replace(
            checkpoint_path
        )
    except (
        OSError,
        ValueError,
        ImportError,
        TypeError,
    ) as exc:
        try:
            temporary_path.unlink(
                missing_ok=True
            )
        except OSError:
            pass

        raise ChunkProcessingError(
            "Failed to write checkpoint "
            f"for chunk {chunk_number}: {checkpoint_path}"
        ) from exc

    return checkpoint_path


def load_checkpoints(
    *,
    pipeline_config: PipelineConfig = config,
) -> Iterator[pd.DataFrame]:
    """Yield previously persisted checkpoint DataFrames in chunk order."""
    checkpoint_dir = pipeline_config.checkpoint_dir

    if not checkpoint_dir.exists():
        return

    checkpoint_files = sorted(
        checkpoint_dir.glob(
            "chunk-*.parquet"
        )
    )

    for checkpoint_path in checkpoint_files:
        try:
            yield pd.read_parquet(
                checkpoint_path
            )
        except (
            OSError,
            ValueError,
            ImportError,
            TypeError,
        ) as exc:
            raise ChunkProcessingError(
                f"Failed to load checkpoint: {checkpoint_path}"
            ) from exc


def _combine_chunks(
    chunks: Iterable[pd.DataFrame],
) -> pd.DataFrame:
    """Combine processed chunks while preserving row order."""
    frames = list(chunks)

    if not frames:
        return pd.DataFrame()

    return pd.concat(
        frames,
        axis=0,
        ignore_index=True,
    )


def process_dataset(
    transformer: ChunkTransformer,
    source_path: Path | None = None,
    *,
    pipeline_config: PipelineConfig = config,
) -> ProcessingResult:
    """Process an entire dataset incrementally and return all chunk results."""
    chunk_results: list[ChunkResult] = []

    for chunk_result in iter_processed_chunks(
        transformer,
        source_path,
        pipeline_config=pipeline_config,
    ):
        chunk_results.append(
            chunk_result
        )

        if (
            pipeline_config.checkpointing_enabled
            and (
                chunk_result.chunk_number
                % pipeline_config.checkpoint_interval_chunks
                == 0
            )
        ):
            _write_checkpoint(
                chunk_result.data,
                chunk_number=chunk_result.chunk_number,
                pipeline_config=pipeline_config,
            )

    input_rows = sum(
        result.input_rows
        for result in chunk_results
    )
    output_rows = sum(
        result.output_rows
        for result in chunk_results
    )
    input_memory_bytes = sum(
        result.input_memory_bytes
        for result in chunk_results
    )
    output_memory_bytes = sum(
        result.output_memory_bytes
        for result in chunk_results
    )

    return ProcessingResult(
        chunks=tuple(
            chunk_results
        ),
        metrics=ProcessingMetrics(
            chunks_processed=len(
                chunk_results
            ),
            input_rows=input_rows,
            output_rows=output_rows,
            input_memory_bytes=input_memory_bytes,
            output_memory_bytes=output_memory_bytes,
            rows_removed=max(
                input_rows - output_rows,
                0,
            ),
        ),
    )


def process_dataset_to_dataframe(
    transformer: ChunkTransformer,
    source_path: Path | None = None,
    *,
    pipeline_config: PipelineConfig = config,
) -> tuple[pd.DataFrame, ProcessingMetrics]:
    """Process chunks incrementally and combine the results into one DataFrame."""
    result = process_dataset(
        transformer,
        source_path,
        pipeline_config=pipeline_config,
    )

    frame = _combine_chunks(
        chunk.data
        for chunk in result.chunks
    )

    return frame, result.metrics


def cleanup_checkpoints(
    *,
    pipeline_config: PipelineConfig = config,
) -> int:
    """Remove persisted chunk checkpoints and return the number removed."""
    checkpoint_dir = pipeline_config.checkpoint_dir

    if not checkpoint_dir.exists():
        return 0

    removed = 0

    for checkpoint_path in checkpoint_dir.glob(
        "chunk-*.parquet"
    ):
        try:
            checkpoint_path.unlink()
            removed += 1
        except OSError as exc:
            raise ChunkProcessingError(
                f"Failed to remove checkpoint: {checkpoint_path}"
            ) from exc

    return removed


__all__ = [
    "ChunkProcessingError",
    "ChunkResult",
    "ChunkTransformer",
    "ProcessingMetrics",
    "ProcessingResult",
    "cleanup_checkpoints",
    "iter_processed_chunks",
    "load_checkpoints",
    "process_chunk",
    "process_dataset",
    "process_dataset_to_dataframe",
]

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .config import PipelineConfig, config
from .ingestion import ChunkMetadata, IngestionError, iter_validated_chunks


class ChunkProcessingError(RuntimeError):
    """Raised when a dataset chunk cannot be processed safely."""


@dataclass(frozen=True, slots=True)
class ChunkResult:
    """Represent the result produced by processing one data chunk."""

    chunk_number: int
    input_rows: int
    output_rows: int
    input_memory_bytes: int
    output_memory_bytes: int
    data: pd.DataFrame


@dataclass(frozen=True, slots=True)
class ProcessingMetrics:
    """Represent aggregate metrics for a chunk-processing run."""

    chunks_processed: int
    input_rows: int
    output_rows: int
    input_memory_bytes: int
    output_memory_bytes: int
    rows_removed: int


@dataclass(frozen=True, slots=True)
class ProcessingResult:
    """Represent the complete output of a chunk-processing operation."""

    chunks: tuple[ChunkResult, ...]
    metrics: ProcessingMetrics


ChunkTransformer = Callable[
    [pd.DataFrame, ChunkMetadata],
    pd.DataFrame,
]


def _validate_chunk_result(
    result: pd.DataFrame,
) -> None:
    """Validate that a transformer returned a DataFrame."""
    if not isinstance(result, pd.DataFrame):
        raise ChunkProcessingError(
            "Chunk transformer must return a pandas DataFrame."
        )


def _calculate_memory_bytes(
    frame: pd.DataFrame,
) -> int:
    """Return the deep memory footprint of a DataFrame."""
    return int(
        frame.memory_usage(
            index=True,
            deep=True,
        ).sum()
    )


def _normalize_transformer_result(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Reset the processed chunk index without changing its rows."""
    return frame.reset_index(
        drop=True
    )


def process_chunk(
    frame: pd.DataFrame,
    metadata: ChunkMetadata,
    transformer: ChunkTransformer,
) -> ChunkResult:
    """Transform a single dataset chunk and collect processing metrics."""
    if not isinstance(frame, pd.DataFrame):
        raise ChunkProcessingError(
            "Input chunk must be a pandas DataFrame."
        )

    input_rows = len(frame)
    input_memory_bytes = _calculate_memory_bytes(
        frame
    )

    try:
        transformed = transformer(
            frame,
            metadata,
        )
    except Exception as exc:
        raise ChunkProcessingError(
            f"Failed to process chunk {metadata.chunk_number}."
        ) from exc

    _validate_chunk_result(
        transformed
    )

    transformed = _normalize_transformer_result(
        transformed
    )

    return ChunkResult(
        chunk_number=metadata.chunk_number,
        input_rows=input_rows,
        output_rows=len(transformed),
        input_memory_bytes=input_memory_bytes,
        output_memory_bytes=_calculate_memory_bytes(
            transformed
        ),
        data=transformed,
    )


def iter_processed_chunks(
    transformer: ChunkTransformer,
    source_path: Path | None = None,
    *,
    pipeline_config: PipelineConfig = config,
) -> Iterator[ChunkResult]:
    """Read, validate, and transform a dataset incrementally."""
    if not callable(transformer):
        raise ChunkProcessingError(
            "transformer must be callable."
        )

    try:
        for metadata, frame in iter_validated_chunks(
            source_path,
            pipeline_config=pipeline_config,
        ):
            yield process_chunk(
                frame,
                metadata,
                transformer,
            )
    except IngestionError as exc:
        raise ChunkProcessingError(
            "Failed while reading dataset chunks."
        ) from exc
    except ChunkProcessingError:
        raise


def _write_checkpoint(
    frame: pd.DataFrame,
    *,
    chunk_number: int,
    pipeline_config: PipelineConfig,
) -> Path:
    """Persist one processed chunk as a resumable checkpoint."""
    checkpoint_dir = pipeline_config.checkpoint_dir
    checkpoint_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    checkpoint_path = (
        checkpoint_dir
        / f"chunk-{chunk_number:08d}.parquet"
    )
    temporary_path = checkpoint_path.with_suffix(
        ".parquet.tmp"
    )

    try:
        frame.to_parquet(
            temporary_path,
            **pipeline_config.parquet_write_kwargs,
        )
        temporary_path.replace(
            checkpoint_path
        )
    except (
        OSError,
        ValueError,
        ImportError,
        TypeError,
    ) as exc:
        try:
            temporary_path.unlink(
                missing_ok=True
            )
        except OSError:
            pass

        raise ChunkProcessingError(
            "Failed to write checkpoint "
            f"for chunk {chunk_number}: {checkpoint_path}"
        ) from exc

    return checkpoint_path


def load_checkpoints(
    *,
    pipeline_config: PipelineConfig = config,
) -> Iterator[pd.DataFrame]:
    """Yield previously persisted checkpoint DataFrames in chunk order."""
    checkpoint_dir = pipeline_config.checkpoint_dir

    if not checkpoint_dir.exists():
        return

    checkpoint_files = sorted(
        checkpoint_dir.glob(
            "chunk-*.parquet"
        )
    )

    for checkpoint_path in checkpoint_files:
        try:
            yield pd.read_parquet(
                checkpoint_path
            )
        except (
            OSError,
            ValueError,
            ImportError,
            TypeError,
        ) as exc:
            raise ChunkProcessingError(
                f"Failed to load checkpoint: {checkpoint_path}"
            ) from exc


def _combine_chunks(
    chunks: Iterable[pd.DataFrame],
) -> pd.DataFrame:
    """Combine processed chunks while preserving row order."""
    frames = list(chunks)

    if not frames:
        return pd.DataFrame()

    return pd.concat(
        frames,
        axis=0,
        ignore_index=True,
    )


def process_dataset(
    transformer: ChunkTransformer,
    source_path: Path | None = None,
    *,
    pipeline_config: PipelineConfig = config,
) -> ProcessingResult:
    """Process an entire dataset incrementally and return all chunk results."""
    chunk_results: list[ChunkResult] = []

    for chunk_result in iter_processed_chunks(
        transformer,
        source_path,
        pipeline_config=pipeline_config,
    ):
        chunk_results.append(
            chunk_result
        )

        if (
            pipeline_config.checkpointing_enabled
            and (
                chunk_result.chunk_number
                % pipeline_config.checkpoint_interval_chunks
                == 0
            )
        ):
            _write_checkpoint(
                chunk_result.data,
                chunk_number=chunk_result.chunk_number,
                pipeline_config=pipeline_config,
            )

    input_rows = sum(
        result.input_rows
        for result in chunk_results
    )
    output_rows = sum(
        result.output_rows
        for result in chunk_results
    )
    input_memory_bytes = sum(
        result.input_memory_bytes
        for result in chunk_results
    )
    output_memory_bytes = sum(
        result.output_memory_bytes
        for result in chunk_results
    )

    return ProcessingResult(
        chunks=tuple(
            chunk_results
        ),
        metrics=ProcessingMetrics(
            chunks_processed=len(
                chunk_results
            ),
            input_rows=input_rows,
            output_rows=output_rows,
            input_memory_bytes=input_memory_bytes,
            output_memory_bytes=output_memory_bytes,
            rows_removed=max(
                input_rows - output_rows,
                0,
            ),
        ),
    )


def process_dataset_to_dataframe(
    transformer: ChunkTransformer,
    source_path: Path | None = None,
    *,
    pipeline_config: PipelineConfig = config,
) -> tuple[pd.DataFrame, ProcessingMetrics]:
    """Process chunks incrementally and combine the results into one DataFrame."""
    result = process_dataset(
        transformer,
        source_path,
        pipeline_config=pipeline_config,
    )

    frame = _combine_chunks(
        chunk.data
        for chunk in result.chunks
    )

    return frame, result.metrics


def cleanup_checkpoints(
    *,
    pipeline_config: PipelineConfig = config,
) -> int:
    """Remove persisted chunk checkpoints and return the number removed."""
    checkpoint_dir = pipeline_config.checkpoint_dir

    if not checkpoint_dir.exists():
        return 0

    removed = 0

    for checkpoint_path in checkpoint_dir.glob(
        "chunk-*.parquet"
    ):
        try:
            checkpoint_path.unlink()
            removed += 1
        except OSError as exc:
            raise ChunkProcessingError(
                f"Failed to remove checkpoint: {checkpoint_path}"
            ) from exc

    return removed


__all__ = [
    "ChunkProcessingError",
    "ChunkResult",
    "ChunkTransformer",
    "ProcessingMetrics",
    "ProcessingResult",
    "cleanup_checkpoints",
    "iter_processed_chunks",
    "load_checkpoints",
    "process_chunk",
    "process_dataset",
    "process_dataset_to_dataframe",
]