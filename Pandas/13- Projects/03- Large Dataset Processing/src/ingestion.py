from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .config import PipelineConfig, config


class IngestionError(RuntimeError):
    """Raised when source data cannot be ingested safely."""


@dataclass(frozen=True, slots=True)
class ChunkMetadata:
    """Describe one ingested DataFrame chunk."""

    chunk_number: int
    row_count: int
    memory_bytes: int
    columns: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class IngestionResult:
    """Represent ingestion metrics and metadata for a pipeline run."""

    chunks_processed: int
    rows_processed: int
    columns: tuple[str, ...]
    source_path: Path


def _validate_source(
    source_path: Path,
    pipeline_config: PipelineConfig,
) -> None:
    """Validate that the configured source can be read."""
    if not source_path.exists():
        raise IngestionError(
            f"Input file does not exist: {source_path}"
        )

    if not source_path.is_file():
        raise IngestionError(
            f"Input path is not a file: {source_path}"
        )

    if not source_path.stat().st_size:
        raise IngestionError(
            f"Input file is empty: {source_path}"
        )

    supported_suffixes = {
        "csv": {".csv"},
        "parquet": {".parquet", ".pq"},
        "json": {".json", ".jsonl", ".ndjson"},
    }

    expected_suffixes = supported_suffixes.get(
        pipeline_config.file_format,
        set(),
    )

    if expected_suffixes and source_path.suffix.lower() not in expected_suffixes:
        raise IngestionError(
            "Input file extension does not match the configured "
            f"file format '{pipeline_config.file_format}': {source_path}"
        )


def _read_csv_chunks(
    source_path: Path,
    pipeline_config: PipelineConfig,
) -> Iterator[pd.DataFrame]:
    """Read a CSV source incrementally using configured chunking."""
    read_kwargs: dict[str, Any] = {
        "chunksize": pipeline_config.effective_chunk_size,
        "sep": pipeline_config.csv_separator,
        "encoding": pipeline_config.csv_encoding,
        "low_memory": pipeline_config.low_memory,
    }

    if pipeline_config.usecols:
        read_kwargs["usecols"] = list(
            pipeline_config.usecols
        )

    if pipeline_config.null_value:
        read_kwargs["na_values"] = [
            pipeline_config.null_value
        ]

    if pipeline_config.memory_map:
        read_kwargs["memory_map"] = True

    try:
        reader = pd.read_csv(
            source_path,
            **read_kwargs,
        )

        for chunk in reader:
            yield chunk

    except (
        OSError,
        UnicodeDecodeError,
        pd.errors.ParserError,
        pd.errors.EmptyDataError,
        ValueError,
        TypeError,
    ) as exc:
        raise IngestionError(
            f"Failed to read CSV input: {source_path}"
        ) from exc


def _read_parquet(
    source_path: Path,
    pipeline_config: PipelineConfig,
) -> Iterator[pd.DataFrame]:
    """Read a Parquet source."""
    try:
        read_kwargs: dict[str, Any] = {}

        if pipeline_config.usecols:
            read_kwargs["columns"] = list(
                pipeline_config.usecols
            )

        frame = pd.read_parquet(
            source_path,
            **read_kwargs,
        )

    except (
        OSError,
        ImportError,
        ValueError,
        TypeError,
    ) as exc:
        raise IngestionError(
            f"Failed to read Parquet input: {source_path}"
        ) from exc

    if frame.empty:
        yield frame
        return

    chunk_size = pipeline_config.effective_chunk_size

    for start in range(
        0,
        len(frame),
        chunk_size,
    ):
        yield frame.iloc[
            start : start + chunk_size
        ].copy()


def _read_json(
    source_path: Path,
    pipeline_config: PipelineConfig,
) -> Iterator[pd.DataFrame]:
    """Read JSON, JSON Lines, or NDJSON input."""
    try:
        frame = pd.read_json(
            source_path,
            lines=source_path.suffix.lower()
            in {".jsonl", ".ndjson"},
        )
    except (
        OSError,
        ValueError,
        TypeError,
    ) as exc:
        raise IngestionError(
            f"Failed to read JSON input: {source_path}"
        ) from exc

    if pipeline_config.usecols:
        missing = [
            column
            for column in pipeline_config.usecols
            if column not in frame.columns
        ]

        if missing:
            raise IngestionError(
                "Configured columns are missing from JSON input: "
                + ", ".join(missing)
            )

        frame = frame.loc[
            :,
            list(pipeline_config.usecols),
        ]

    if frame.empty:
        yield frame
        return

    chunk_size = pipeline_config.effective_chunk_size

    for start in range(
        0,
        len(frame),
        chunk_size,
    ):
        yield frame.iloc[
            start : start + chunk_size
        ].copy()


def iter_chunks(
    source_path: Path | None = None,
    *,
    pipeline_config: PipelineConfig = config,
) -> Iterator[pd.DataFrame]:
    """Yield source data incrementally as Pandas DataFrames."""
    source = Path(
        source_path or pipeline_config.input_file
    ).expanduser().resolve()

    _validate_source(
        source,
        pipeline_config,
    )

    if pipeline_config.file_format == "csv":
        yield from _read_csv_chunks(
            source,
            pipeline_config,
        )
        return

    if pipeline_config.file_format == "parquet":
        yield from _read_parquet(
            source,
            pipeline_config,
        )
        return

    if pipeline_config.file_format == "json":
        yield from _read_json(
            source,
            pipeline_config,
        )
        return

    raise IngestionError(
        "Unsupported input file format: "
        f"{pipeline_config.file_format}"
    )


def _validate_columns(
    frame: pd.DataFrame,
    *,
    required_columns: tuple[str, ...],
) -> None:
    """Validate required columns before processing a chunk."""
    missing = [
        column
        for column in required_columns
        if column not in frame.columns
    ]

    if missing:
        raise IngestionError(
            "Input data is missing required columns: "
            + ", ".join(missing)
        )


def _apply_row_limit(
    frame: pd.DataFrame,
    *,
    rows_remaining: int | None,
) -> pd.DataFrame:
    """Limit a chunk when a maximum row count is configured."""
    if rows_remaining is None:
        return frame

    if rows_remaining <= 0:
        return frame.iloc[0:0].copy()

    if len(frame) <= rows_remaining:
        return frame

    return frame.iloc[:rows_remaining].copy()


def iter_validated_chunks(
    source_path: Path | None = None,
    *,
    pipeline_config: PipelineConfig = config,
) -> Iterator[tuple[ChunkMetadata, pd.DataFrame]]:
    """Yield validated chunks together with ingestion metadata."""
    total_rows = 0
    required_columns = pipeline_config.required_columns

    for chunk_number, frame in enumerate(
        iter_chunks(
            source_path,
            pipeline_config=pipeline_config,
        ),
        start=1,
    ):
        if pipeline_config.max_rows is not None:
            rows_remaining = (
                pipeline_config.max_rows - total_rows
            )

            frame = _apply_row_limit(
                frame,
                rows_remaining=rows_remaining,
            )

        _validate_columns(
            frame,
            required_columns=required_columns,
        )

        frame = frame.reset_index(
            drop=True
        )

        metadata = ChunkMetadata(
            chunk_number=chunk_number,
            row_count=len(frame),
            memory_bytes=int(
                frame.memory_usage(
                    index=True,
                    deep=True,
                ).sum()
            ),
            columns=tuple(
                str(column)
                for column in frame.columns
            ),
        )

        yield metadata, frame

        total_rows += len(frame)

        if (
            pipeline_config.max_rows is not None
            and total_rows >= pipeline_config.max_rows
        ):
            break


def ingest(
    source_path: Path | None = None,
    *,
    pipeline_config: PipelineConfig = config,
) -> IngestionResult:
    """Ingest a large dataset without loading it through the public API at once."""
    total_rows = 0
    chunks_processed = 0
    columns: tuple[str, ...] = ()

    try:
        for metadata, frame in iter_validated_chunks(
            source_path,
            pipeline_config=pipeline_config,
        ):
            chunks_processed += 1
            total_rows += len(frame)

            if not columns:
                columns = metadata.columns

            if columns != metadata.columns:
                raise IngestionError(
                    "Input schema changed between chunks. "
                    "Large dataset processing requires a stable schema."
                )

            if frame.empty and chunks_processed == 1:
                continue

    except IngestionError:
        raise
    except (
        OSError,
        ValueError,
        TypeError,
    ) as exc:
        source = Path(
            source_path or pipeline_config.input_file
        )
        raise IngestionError(
            f"Failed during dataset ingestion: {source}"
        ) from exc

    if chunks_processed == 0:
        raise IngestionError(
            "No chunks were produced from the input dataset."
        )

    return IngestionResult(
        chunks_processed=chunks_processed,
        rows_processed=total_rows,
        columns=columns,
        source_path=Path(
            source_path or pipeline_config.input_file
        ).expanduser().resolve(),
    )


__all__ = [
    "ChunkMetadata",
    "IngestionError",
    "IngestionResult",
    "ingest",
    "iter_chunks",
    "iter_validated_chunks",
]

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .config import PipelineConfig, config


class IngestionError(RuntimeError):
    """Raised when source data cannot be ingested safely."""


@dataclass(frozen=True, slots=True)
class ChunkMetadata:
    """Describe one ingested DataFrame chunk."""

    chunk_number: int
    row_count: int
    memory_bytes: int
    columns: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class IngestionResult:
    """Represent ingestion metrics and metadata for a pipeline run."""

    chunks_processed: int
    rows_processed: int
    columns: tuple[str, ...]
    source_path: Path


def _validate_source(
    source_path: Path,
    pipeline_config: PipelineConfig,
) -> None:
    """Validate that the configured source can be read."""
    if not source_path.exists():
        raise IngestionError(
            f"Input file does not exist: {source_path}"
        )

    if not source_path.is_file():
        raise IngestionError(
            f"Input path is not a file: {source_path}"
        )

    if not source_path.stat().st_size:
        raise IngestionError(
            f"Input file is empty: {source_path}"
        )

    supported_suffixes = {
        "csv": {".csv"},
        "parquet": {".parquet", ".pq"},
        "json": {".json", ".jsonl", ".ndjson"},
    }

    expected_suffixes = supported_suffixes.get(
        pipeline_config.file_format,
        set(),
    )

    if expected_suffixes and source_path.suffix.lower() not in expected_suffixes:
        raise IngestionError(
            "Input file extension does not match the configured "
            f"file format '{pipeline_config.file_format}': {source_path}"
        )


def _read_csv_chunks(
    source_path: Path,
    pipeline_config: PipelineConfig,
) -> Iterator[pd.DataFrame]:
    """Read a CSV source incrementally using configured chunking."""
    read_kwargs: dict[str, Any] = {
        "chunksize": pipeline_config.effective_chunk_size,
        "sep": pipeline_config.csv_separator,
        "encoding": pipeline_config.csv_encoding,
        "low_memory": pipeline_config.low_memory,
    }

    if pipeline_config.usecols:
        read_kwargs["usecols"] = list(
            pipeline_config.usecols
        )

    if pipeline_config.null_value:
        read_kwargs["na_values"] = [
            pipeline_config.null_value
        ]

    if pipeline_config.memory_map:
        read_kwargs["memory_map"] = True

    try:
        reader = pd.read_csv(
            source_path,
            **read_kwargs,
        )

        for chunk in reader:
            yield chunk

    except (
        OSError,
        UnicodeDecodeError,
        pd.errors.ParserError,
        pd.errors.EmptyDataError,
        ValueError,
        TypeError,
    ) as exc:
        raise IngestionError(
            f"Failed to read CSV input: {source_path}"
        ) from exc


def _read_parquet(
    source_path: Path,
    pipeline_config: PipelineConfig,
) -> Iterator[pd.DataFrame]:
    """Read a Parquet source."""
    try:
        read_kwargs: dict[str, Any] = {}

        if pipeline_config.usecols:
            read_kwargs["columns"] = list(
                pipeline_config.usecols
            )

        frame = pd.read_parquet(
            source_path,
            **read_kwargs,
        )

    except (
        OSError,
        ImportError,
        ValueError,
        TypeError,
    ) as exc:
        raise IngestionError(
            f"Failed to read Parquet input: {source_path}"
        ) from exc

    if frame.empty:
        yield frame
        return

    chunk_size = pipeline_config.effective_chunk_size

    for start in range(
        0,
        len(frame),
        chunk_size,
    ):
        yield frame.iloc[
            start : start + chunk_size
        ].copy()


def _read_json(
    source_path: Path,
    pipeline_config: PipelineConfig,
) -> Iterator[pd.DataFrame]:
    """Read JSON, JSON Lines, or NDJSON input."""
    try:
        frame = pd.read_json(
            source_path,
            lines=source_path.suffix.lower()
            in {".jsonl", ".ndjson"},
        )
    except (
        OSError,
        ValueError,
        TypeError,
    ) as exc:
        raise IngestionError(
            f"Failed to read JSON input: {source_path}"
        ) from exc

    if pipeline_config.usecols:
        missing = [
            column
            for column in pipeline_config.usecols
            if column not in frame.columns
        ]

        if missing:
            raise IngestionError(
                "Configured columns are missing from JSON input: "
                + ", ".join(missing)
            )

        frame = frame.loc[
            :,
            list(pipeline_config.usecols),
        ]

    if frame.empty:
        yield frame
        return

    chunk_size = pipeline_config.effective_chunk_size

    for start in range(
        0,
        len(frame),
        chunk_size,
    ):
        yield frame.iloc[
            start : start + chunk_size
        ].copy()


def iter_chunks(
    source_path: Path | None = None,
    *,
    pipeline_config: PipelineConfig = config,
) -> Iterator[pd.DataFrame]:
    """Yield source data incrementally as Pandas DataFrames."""
    source = Path(
        source_path or pipeline_config.input_file
    ).expanduser().resolve()

    _validate_source(
        source,
        pipeline_config,
    )

    if pipeline_config.file_format == "csv":
        yield from _read_csv_chunks(
            source,
            pipeline_config,
        )
        return

    if pipeline_config.file_format == "parquet":
        yield from _read_parquet(
            source,
            pipeline_config,
        )
        return

    if pipeline_config.file_format == "json":
        yield from _read_json(
            source,
            pipeline_config,
        )
        return

    raise IngestionError(
        "Unsupported input file format: "
        f"{pipeline_config.file_format}"
    )


def _validate_columns(
    frame: pd.DataFrame,
    *,
    required_columns: tuple[str, ...],
) -> None:
    """Validate required columns before processing a chunk."""
    missing = [
        column
        for column in required_columns
        if column not in frame.columns
    ]

    if missing:
        raise IngestionError(
            "Input data is missing required columns: "
            + ", ".join(missing)
        )


def _apply_row_limit(
    frame: pd.DataFrame,
    *,
    rows_remaining: int | None,
) -> pd.DataFrame:
    """Limit a chunk when a maximum row count is configured."""
    if rows_remaining is None:
        return frame

    if rows_remaining <= 0:
        return frame.iloc[0:0].copy()

    if len(frame) <= rows_remaining:
        return frame

    return frame.iloc[:rows_remaining].copy()


def iter_validated_chunks(
    source_path: Path | None = None,
    *,
    pipeline_config: PipelineConfig = config,
) -> Iterator[tuple[ChunkMetadata, pd.DataFrame]]:
    """Yield validated chunks together with ingestion metadata."""
    total_rows = 0
    required_columns = pipeline_config.required_columns

    for chunk_number, frame in enumerate(
        iter_chunks(
            source_path,
            pipeline_config=pipeline_config,
        ),
        start=1,
    ):
        if pipeline_config.max_rows is not None:
            rows_remaining = (
                pipeline_config.max_rows - total_rows
            )

            frame = _apply_row_limit(
                frame,
                rows_remaining=rows_remaining,
            )

        _validate_columns(
            frame,
            required_columns=required_columns,
        )

        frame = frame.reset_index(
            drop=True
        )

        metadata = ChunkMetadata(
            chunk_number=chunk_number,
            row_count=len(frame),
            memory_bytes=int(
                frame.memory_usage(
                    index=True,
                    deep=True,
                ).sum()
            ),
            columns=tuple(
                str(column)
                for column in frame.columns
            ),
        )

        yield metadata, frame

        total_rows += len(frame)

        if (
            pipeline_config.max_rows is not None
            and total_rows >= pipeline_config.max_rows
        ):
            break


def ingest(
    source_path: Path | None = None,
    *,
    pipeline_config: PipelineConfig = config,
) -> IngestionResult:
    """Ingest a large dataset without loading it through the public API at once."""
    total_rows = 0
    chunks_processed = 0
    columns: tuple[str, ...] = ()

    try:
        for metadata, frame in iter_validated_chunks(
            source_path,
            pipeline_config=pipeline_config,
        ):
            chunks_processed += 1
            total_rows += len(frame)

            if not columns:
                columns = metadata.columns

            if columns != metadata.columns:
                raise IngestionError(
                    "Input schema changed between chunks. "
                    "Large dataset processing requires a stable schema."
                )

            if frame.empty and chunks_processed == 1:
                continue

    except IngestionError:
        raise
    except (
        OSError,
        ValueError,
        TypeError,
    ) as exc:
        source = Path(
            source_path or pipeline_config.input_file
        )
        raise IngestionError(
            f"Failed during dataset ingestion: {source}"
        ) from exc

    if chunks_processed == 0:
        raise IngestionError(
            "No chunks were produced from the input dataset."
        )

    return IngestionResult(
        chunks_processed=chunks_processed,
        rows_processed=total_rows,
        columns=columns,
        source_path=Path(
            source_path or pipeline_config.input_file
        ).expanduser().resolve(),
    )


__all__ = [
    "ChunkMetadata",
    "IngestionError",
    "IngestionResult",
    "ingest",
    "iter_chunks",
    "iter_validated_chunks",
]