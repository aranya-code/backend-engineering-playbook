from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.chunk_processor import (
    ChunkMetadata,
    ChunkProcessingError,
    ProcessingMetrics,
    ProcessingResult,
    cleanup_checkpoints,
    iter_processed_chunks,
    load_checkpoints,
    process_chunk,
    process_dataset,
    process_dataset_to_dataframe,
)
from src.ingestion import IngestionError


def _metadata(
    chunk_number: int = 1,
    row_count: int = 2,
    columns: tuple[str, ...] = ("id", "amount"),
) -> ChunkMetadata:
    """Build deterministic metadata for unit tests."""
    return ChunkMetadata(
        chunk_number=chunk_number,
        row_count=row_count,
        memory_bytes=0,
        columns=columns,
    )


def _frame(
    ids: tuple[int, ...] = (1, 2),
    amounts: tuple[float, ...] = (10.0, 20.0),
) -> pd.DataFrame:
    """Build a representative input DataFrame."""
    return pd.DataFrame(
        {
            "id": ids,
            "amount": amounts,
        }
    )


def test_process_chunk_returns_transformed_dataframe_and_metrics() -> None:
    frame = _frame()
    metadata = _metadata()

    def transformer(
        chunk: pd.DataFrame,
        chunk_metadata: ChunkMetadata,
    ) -> pd.DataFrame:
        assert chunk_metadata.chunk_number == 1

        result = chunk.copy()
        result["amount_with_tax"] = result["amount"] * 1.18
        return result

    result = process_chunk(
        frame,
        metadata,
        transformer,
    )

    assert isinstance(
        result,
        ProcessingResult,
    )
    assert result.metadata == metadata
    assert result.metrics.rows_input == 2
    assert result.metrics.rows_processed == 2
    assert result.metrics.rows_removed == 0
    assert result.data["amount_with_tax"].tolist() == [
        pytest.approx(11.8),
        pytest.approx(23.6),
    ]


def test_process_chunk_preserves_input_dataframe() -> None:
    frame = _frame()
    original = frame.copy(deep=True)

    def transformer(
        chunk: pd.DataFrame,
        chunk_metadata: ChunkMetadata,
    ) -> pd.DataFrame:
        return chunk.copy()

    process_chunk(
        frame,
        _metadata(),
        transformer,
    )

    pd.testing.assert_frame_equal(
        frame,
        original,
    )


def test_process_chunk_rejects_non_dataframe_input() -> None:
    with pytest.raises(
        ChunkProcessingError,
        match="DataFrame",
    ):
        process_chunk(
            "invalid",
            _metadata(),  # type: ignore[arg-type]
            lambda frame, metadata: frame,
        )


def test_process_chunk_rejects_invalid_metadata() -> None:
    with pytest.raises(
        ChunkProcessingError,
        match="metadata",
    ):
        process_chunk(
            _frame(),
            None,  # type: ignore[arg-type]
            lambda frame, metadata: frame,
        )


def test_process_chunk_wraps_transformer_exceptions() -> None:
    def transformer(
        chunk: pd.DataFrame,
        chunk_metadata: ChunkMetadata,
    ) -> pd.DataFrame:
        raise ValueError("invalid business transformation")

    with pytest.raises(
        ChunkProcessingError,
        match="processing chunk",
    ) as exc_info:
        process_chunk(
            _frame(),
            _metadata(),
            transformer,
        )

    assert isinstance(
        exc_info.value.__cause__,
        ValueError,
    )


def test_process_chunk_rejects_transformer_result_with_wrong_type() -> None:
    def transformer(
        chunk: pd.DataFrame,
        chunk_metadata: ChunkMetadata,
    ) -> str:
        return "invalid"  # type: ignore[return-value]

    with pytest.raises(
        ChunkProcessingError,
        match="DataFrame",
    ):
        process_chunk(
            _frame(),
            _metadata(),
            transformer,
        )


def test_process_chunk_rejects_transformer_result_with_duplicate_columns() -> None:
    frame = pd.DataFrame(
        [
            [1, 10.0, 20.0],
            [2, 15.0, 25.0],
        ],
        columns=["id", "amount", "amount"],
    )

    def transformer(
        chunk: pd.DataFrame,
        chunk_metadata: ChunkMetadata,
    ) -> pd.DataFrame:
        return chunk

    with pytest.raises(
        ChunkProcessingError,
        match="duplicate",
    ):
        process_chunk(
            frame,
            ChunkMetadata(
                chunk_number=1,
                row_count=2,
                memory_bytes=0,
                columns=("id", "amount"),
            ),
            transformer,
        )


def test_process_chunk_supports_empty_result() -> None:
    def transformer(
        chunk: pd.DataFrame,
        chunk_metadata: ChunkMetadata,
    ) -> pd.DataFrame:
        return chunk.iloc[0:0].copy()

    result = process_chunk(
        _frame(),
        _metadata(),
        transformer,
    )

    assert result.data.empty
    assert result.metrics.rows_input == 2
    assert result.metrics.rows_processed == 0
    assert result.metrics.rows_removed == 2


def test_process_chunk_calculates_memory_metrics() -> None:
    result = process_chunk(
        _frame(),
        _metadata(),
        lambda frame, metadata: frame.copy(),
    )

    assert isinstance(
        result.metrics,
        ProcessingMetrics,
    )
    assert result.metrics.input_memory_bytes > 0
    assert result.metrics.output_memory_bytes > 0


def test_process_chunk_does_not_treat_same_row_count_as_no_copy() -> None:
    frame = _frame()

    result = process_chunk(
        frame,
        _metadata(),
        lambda chunk, metadata: chunk.copy(),
    )

    assert result.data is not frame


def test_iter_processed_chunks_processes_chunks_in_order() -> None:
    chunks = [
        (
            _frame((1, 2)),
            _metadata(chunk_number=1),
        ),
        (
            _frame((3, 4)),
            _metadata(chunk_number=2),
        ),
        (
            _frame((5, 6)),
            _metadata(chunk_number=3),
        ),
    ]

    transformed = list(
        iter_processed_chunks(
            iter(chunks),
            transformer=lambda frame, metadata: frame.assign(
                processed=True
            ),
        )
    )

    assert [
        result.metadata.chunk_number
        for result in transformed
    ] == [1, 2, 3]

    assert all(
        result.data["processed"].eq(True).all()
        for result in transformed
    )


def test_iter_processed_chunks_yields_no_results_for_empty_input() -> None:
    results = list(
        iter_processed_chunks(
            iter(()),
            transformer=lambda frame, metadata: frame,
        )
    )

    assert results == []


def test_iter_processed_chunks_wraps_ingestion_errors() -> None:
    def source():
        yield (
            _frame(),
            _metadata(),
        )
        raise IngestionError(
            "source failed"
        )

    with pytest.raises(
        ChunkProcessingError,
        match="ingestion",
    ):
        list(
            iter_processed_chunks(
                source(),
                transformer=lambda frame, metadata: frame,
            )
        )


def test_process_dataset_returns_processing_results() -> None:
    chunks = [
        (
            _frame((1, 2)),
            _metadata(chunk_number=1),
        ),
        (
            _frame((3, 4)),
            _metadata(chunk_number=2),
        ),
    ]

    result = process_dataset(
        chunks,
        transformer=lambda frame, metadata: frame.assign(
            processed=True
        ),
    )

    assert isinstance(
        result,
        list,
    )
    assert len(result) == 2
    assert [
        item.metadata.chunk_number
        for item in result
    ] == [1, 2]


def test_process_dataset_preserves_chunk_order() -> None:
    chunks = [
        (
            _frame((1,)),
            _metadata(
                chunk_number=1,
                row_count=1,
            ),
        ),
        (
            _frame((2,)),
            _metadata(
                chunk_number=2,
                row_count=1,
            ),
        ),
    ]

    results = process_dataset(
        chunks,
        transformer=lambda frame, metadata: frame,
    )

    combined_ids = [
        int(item.data["id"].iloc[0])
        for item in results
    ]

    assert combined_ids == [1, 2]


def test_process_dataset_writes_checkpoints_when_enabled(
    tmp_path: Path,
) -> None:
    chunks = [
        (
            _frame((1, 2)),
            _metadata(chunk_number=1),
        ),
        (
            _frame((3, 4)),
            _metadata(chunk_number=2),
        ),
    ]

    checkpoint_dir = tmp_path / "checkpoints"

    results = process_dataset(
        chunks,
        transformer=lambda frame, metadata: frame,
        checkpoint_dir=checkpoint_dir,
        checkpoint_interval=1,
    )

    assert len(results) == 2

    checkpoints = sorted(
        checkpoint_dir.glob(
            "chunk-*.parquet"
        )
    )

    assert [path.name for path in checkpoints] == [
        "chunk-00000001.parquet",
        "chunk-00000002.parquet",
    ]


def test_process_dataset_skips_checkpoint_until_interval(
    tmp_path: Path,
) -> None:
    chunks = [
        (
            _frame((1, 2)),
            _metadata(chunk_number=1),
        ),
        (
            _frame((3, 4)),
            _metadata(chunk_number=2),
        ),
        (
            _frame((5, 6)),
            _metadata(chunk_number=3),
        ),
    ]

    checkpoint_dir = tmp_path / "checkpoints"

    process_dataset(
        chunks,
        transformer=lambda frame, metadata: frame,
        checkpoint_dir=checkpoint_dir,
        checkpoint_interval=2,
    )

    checkpoints = sorted(
        checkpoint_dir.glob(
            "chunk-*.parquet"
        )
    )

    assert [path.name for path in checkpoints] == [
        "chunk-00000002.parquet",
    ]


def test_process_dataset_to_dataframe_combines_processed_chunks() -> None:
    chunks = [
        (
            _frame((1, 2)),
            _metadata(chunk_number=1),
        ),
        (
            _frame((3, 4)),
            _metadata(chunk_number=2),
        ),
    ]

    result = process_dataset_to_dataframe(
        chunks,
        transformer=lambda frame, metadata: frame.assign(
            processed=True
        ),
    )

    expected = pd.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "amount": [
                10.0,
                20.0,
                10.0,
                20.0,
            ],
            "processed": [
                True,
                True,
                True,
                True,
            ],
        }
    )

    pd.testing.assert_frame_equal(
        result.reset_index(drop=True),
        expected,
    )


def test_process_dataset_to_dataframe_returns_empty_dataframe() -> None:
    result = process_dataset_to_dataframe(
        iter(()),
        transformer=lambda frame, metadata: frame,
    )

    assert isinstance(
        result,
        pd.DataFrame,
    )
    assert result.empty


def test_process_dataset_to_dataframe_resets_index() -> None:
    chunks = [
        (
            pd.DataFrame(
                {
                    "id": [10, 20],
                    "amount": [100.0, 200.0],
                },
                index=[10, 20],
            ),
            _metadata(),
        )
    ]

    result = process_dataset_to_dataframe(
        chunks,
        transformer=lambda frame, metadata: frame,
    )

    assert result.index.tolist() == [0, 1]


def test_load_checkpoints_returns_checkpoints_in_order(
    tmp_path: Path,
) -> None:
    checkpoint_dir = tmp_path / "checkpoints"
    checkpoint_dir.mkdir()

    first = checkpoint_dir / "chunk-00000001.parquet"
    second = checkpoint_dir / "chunk-00000002.parquet"

    _frame((1, 2)).to_parquet(
        first,
        index=False,
    )
    _frame((3, 4)).to_parquet(
        second,
        index=False,
    )

    loaded = load_checkpoints(
        checkpoint_dir
    )

    assert len(loaded) == 2
    assert [
        path.name
        for path in loaded
    ] == [
        "chunk-00000001.parquet",
        "chunk-00000002.parquet",
    ]


def test_load_checkpoints_returns_empty_list_for_missing_directory(
    tmp_path: Path,
) -> None:
    loaded = load_checkpoints(
        tmp_path / "missing"
    )

    assert loaded == []


def test_load_checkpoints_ignores_non_checkpoint_files(
    tmp_path: Path,
) -> None:
    checkpoint_dir = tmp_path / "checkpoints"
    checkpoint_dir.mkdir()

    _frame().to_parquet(
        checkpoint_dir / "chunk-00000001.parquet",
        index=False,
    )
    (checkpoint_dir / "notes.txt").write_text(
        "ignore me",
        encoding="utf-8",
    )

    loaded = load_checkpoints(
        checkpoint_dir
    )

    assert len(loaded) == 1
    assert loaded[0].name == (
        "chunk-00000001.parquet"
    )


def test_cleanup_checkpoints_removes_checkpoint_files(
    tmp_path: Path,
) -> None:
    checkpoint_dir = tmp_path / "checkpoints"
    checkpoint_dir.mkdir()

    for number in (1, 2, 3):
        _frame().to_parquet(
            checkpoint_dir
            / f"chunk-{number:08d}.parquet",
            index=False,
        )

    removed = cleanup_checkpoints(
        checkpoint_dir
    )

    assert removed == 3
    assert list(
        checkpoint_dir.glob("chunk-*.parquet")
    ) == []


def test_cleanup_checkpoints_is_idempotent(
    tmp_path: Path,
) -> None:
    checkpoint_dir = tmp_path / "checkpoints"

    assert cleanup_checkpoints(
        checkpoint_dir
    ) == 0

    assert cleanup_checkpoints(
        checkpoint_dir
    ) == 0


def test_process_dataset_accepts_named_transformer() -> None:
    calls: list[int] = []

    def transformer(
        frame: pd.DataFrame,
        metadata: ChunkMetadata,
    ) -> pd.DataFrame:
        calls.append(
            metadata.chunk_number
        )
        return frame.copy()

    chunks = [
        (
            _frame(),
            _metadata(chunk_number=1),
        ),
        (
            _frame(),
            _metadata(chunk_number=2),
        ),
    ]

    results = process_dataset(
        chunks,
        transformer=transformer,
    )

    assert len(results) == 2
    assert calls == [1, 2]


def test_process_chunk_supports_transformer_returning_same_dataframe() -> None:
    frame = _frame()

    result = process_chunk(
        frame,
        _metadata(),
        lambda chunk, metadata: chunk,
    )

    pd.testing.assert_frame_equal(
        result.data,
        frame,
    )


def test_processing_metrics_report_removed_rows() -> None:
    def transformer(
        frame: pd.DataFrame,
        metadata: ChunkMetadata,
    ) -> pd.DataFrame:
        return frame.iloc[:1].copy()

    result = process_chunk(
        _frame(),
        _metadata(),
        transformer,
    )

    assert result.metrics.rows_input == 2
    assert result.metrics.rows_processed == 1
    assert result.metrics.rows_removed == 1


def test_processing_metrics_are_non_negative() -> None:
    result = process_chunk(
        _frame(),
        _metadata(),
        lambda frame, metadata: frame.copy(),
    )

    assert result.metrics.rows_input >= 0
    assert result.metrics.rows_processed >= 0
    assert result.metrics.rows_removed >= 0
    assert result.metrics.input_memory_bytes >= 0
    assert result.metrics.output_memory_bytes >= 0

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.chunk_processor import (
    ChunkMetadata,
    ChunkProcessingError,
    ProcessingMetrics,
    ProcessingResult,
    cleanup_checkpoints,
    iter_processed_chunks,
    load_checkpoints,
    process_chunk,
    process_dataset,
    process_dataset_to_dataframe,
)
from src.ingestion import IngestionError


def _metadata(
    chunk_number: int = 1,
    row_count: int = 2,
    columns: tuple[str, ...] = ("id", "amount"),
) -> ChunkMetadata:
    """Build deterministic metadata for unit tests."""
    return ChunkMetadata(
        chunk_number=chunk_number,
        row_count=row_count,
        memory_bytes=0,
        columns=columns,
    )


def _frame(
    ids: tuple[int, ...] = (1, 2),
    amounts: tuple[float, ...] = (10.0, 20.0),
) -> pd.DataFrame:
    """Build a representative input DataFrame."""
    return pd.DataFrame(
        {
            "id": ids,
            "amount": amounts,
        }
    )


def test_process_chunk_returns_transformed_dataframe_and_metrics() -> None:
    frame = _frame()
    metadata = _metadata()

    def transformer(
        chunk: pd.DataFrame,
        chunk_metadata: ChunkMetadata,
    ) -> pd.DataFrame:
        assert chunk_metadata.chunk_number == 1

        result = chunk.copy()
        result["amount_with_tax"] = result["amount"] * 1.18
        return result

    result = process_chunk(
        frame,
        metadata,
        transformer,
    )

    assert isinstance(
        result,
        ProcessingResult,
    )
    assert result.metadata == metadata
    assert result.metrics.rows_input == 2
    assert result.metrics.rows_processed == 2
    assert result.metrics.rows_removed == 0
    assert result.data["amount_with_tax"].tolist() == [
        pytest.approx(11.8),
        pytest.approx(23.6),
    ]


def test_process_chunk_preserves_input_dataframe() -> None:
    frame = _frame()
    original = frame.copy(deep=True)

    def transformer(
        chunk: pd.DataFrame,
        chunk_metadata: ChunkMetadata,
    ) -> pd.DataFrame:
        return chunk.copy()

    process_chunk(
        frame,
        _metadata(),
        transformer,
    )

    pd.testing.assert_frame_equal(
        frame,
        original,
    )


def test_process_chunk_rejects_non_dataframe_input() -> None:
    with pytest.raises(
        ChunkProcessingError,
        match="DataFrame",
    ):
        process_chunk(
            "invalid",
            _metadata(),  # type: ignore[arg-type]
            lambda frame, metadata: frame,
        )


def test_process_chunk_rejects_invalid_metadata() -> None:
    with pytest.raises(
        ChunkProcessingError,
        match="metadata",
    ):
        process_chunk(
            _frame(),
            None,  # type: ignore[arg-type]
            lambda frame, metadata: frame,
        )


def test_process_chunk_wraps_transformer_exceptions() -> None:
    def transformer(
        chunk: pd.DataFrame,
        chunk_metadata: ChunkMetadata,
    ) -> pd.DataFrame:
        raise ValueError("invalid business transformation")

    with pytest.raises(
        ChunkProcessingError,
        match="processing chunk",
    ) as exc_info:
        process_chunk(
            _frame(),
            _metadata(),
            transformer,
        )

    assert isinstance(
        exc_info.value.__cause__,
        ValueError,
    )


def test_process_chunk_rejects_transformer_result_with_wrong_type() -> None:
    def transformer(
        chunk: pd.DataFrame,
        chunk_metadata: ChunkMetadata,
    ) -> str:
        return "invalid"  # type: ignore[return-value]

    with pytest.raises(
        ChunkProcessingError,
        match="DataFrame",
    ):
        process_chunk(
            _frame(),
            _metadata(),
            transformer,
        )


def test_process_chunk_rejects_transformer_result_with_duplicate_columns() -> None:
    frame = pd.DataFrame(
        [
            [1, 10.0, 20.0],
            [2, 15.0, 25.0],
        ],
        columns=["id", "amount", "amount"],
    )

    def transformer(
        chunk: pd.DataFrame,
        chunk_metadata: ChunkMetadata,
    ) -> pd.DataFrame:
        return chunk

    with pytest.raises(
        ChunkProcessingError,
        match="duplicate",
    ):
        process_chunk(
            frame,
            ChunkMetadata(
                chunk_number=1,
                row_count=2,
                memory_bytes=0,
                columns=("id", "amount"),
            ),
            transformer,
        )


def test_process_chunk_supports_empty_result() -> None:
    def transformer(
        chunk: pd.DataFrame,
        chunk_metadata: ChunkMetadata,
    ) -> pd.DataFrame:
        return chunk.iloc[0:0].copy()

    result = process_chunk(
        _frame(),
        _metadata(),
        transformer,
    )

    assert result.data.empty
    assert result.metrics.rows_input == 2
    assert result.metrics.rows_processed == 0
    assert result.metrics.rows_removed == 2


def test_process_chunk_calculates_memory_metrics() -> None:
    result = process_chunk(
        _frame(),
        _metadata(),
        lambda frame, metadata: frame.copy(),
    )

    assert isinstance(
        result.metrics,
        ProcessingMetrics,
    )
    assert result.metrics.input_memory_bytes > 0
    assert result.metrics.output_memory_bytes > 0


def test_process_chunk_does_not_treat_same_row_count_as_no_copy() -> None:
    frame = _frame()

    result = process_chunk(
        frame,
        _metadata(),
        lambda chunk, metadata: chunk.copy(),
    )

    assert result.data is not frame


def test_iter_processed_chunks_processes_chunks_in_order() -> None:
    chunks = [
        (
            _frame((1, 2)),
            _metadata(chunk_number=1),
        ),
        (
            _frame((3, 4)),
            _metadata(chunk_number=2),
        ),
        (
            _frame((5, 6)),
            _metadata(chunk_number=3),
        ),
    ]

    transformed = list(
        iter_processed_chunks(
            iter(chunks),
            transformer=lambda frame, metadata: frame.assign(
                processed=True
            ),
        )
    )

    assert [
        result.metadata.chunk_number
        for result in transformed
    ] == [1, 2, 3]

    assert all(
        result.data["processed"].eq(True).all()
        for result in transformed
    )


def test_iter_processed_chunks_yields_no_results_for_empty_input() -> None:
    results = list(
        iter_processed_chunks(
            iter(()),
            transformer=lambda frame, metadata: frame,
        )
    )

    assert results == []


def test_iter_processed_chunks_wraps_ingestion_errors() -> None:
    def source():
        yield (
            _frame(),
            _metadata(),
        )
        raise IngestionError(
            "source failed"
        )

    with pytest.raises(
        ChunkProcessingError,
        match="ingestion",
    ):
        list(
            iter_processed_chunks(
                source(),
                transformer=lambda frame, metadata: frame,
            )
        )


def test_process_dataset_returns_processing_results() -> None:
    chunks = [
        (
            _frame((1, 2)),
            _metadata(chunk_number=1),
        ),
        (
            _frame((3, 4)),
            _metadata(chunk_number=2),
        ),
    ]

    result = process_dataset(
        chunks,
        transformer=lambda frame, metadata: frame.assign(
            processed=True
        ),
    )

    assert isinstance(
        result,
        list,
    )
    assert len(result) == 2
    assert [
        item.metadata.chunk_number
        for item in result
    ] == [1, 2]


def test_process_dataset_preserves_chunk_order() -> None:
    chunks = [
        (
            _frame((1,)),
            _metadata(
                chunk_number=1,
                row_count=1,
            ),
        ),
        (
            _frame((2,)),
            _metadata(
                chunk_number=2,
                row_count=1,
            ),
        ),
    ]

    results = process_dataset(
        chunks,
        transformer=lambda frame, metadata: frame,
    )

    combined_ids = [
        int(item.data["id"].iloc[0])
        for item in results
    ]

    assert combined_ids == [1, 2]


def test_process_dataset_writes_checkpoints_when_enabled(
    tmp_path: Path,
) -> None:
    chunks = [
        (
            _frame((1, 2)),
            _metadata(chunk_number=1),
        ),
        (
            _frame((3, 4)),
            _metadata(chunk_number=2),
        ),
    ]

    checkpoint_dir = tmp_path / "checkpoints"

    results = process_dataset(
        chunks,
        transformer=lambda frame, metadata: frame,
        checkpoint_dir=checkpoint_dir,
        checkpoint_interval=1,
    )

    assert len(results) == 2

    checkpoints = sorted(
        checkpoint_dir.glob(
            "chunk-*.parquet"
        )
    )

    assert [path.name for path in checkpoints] == [
        "chunk-00000001.parquet",
        "chunk-00000002.parquet",
    ]


def test_process_dataset_skips_checkpoint_until_interval(
    tmp_path: Path,
) -> None:
    chunks = [
        (
            _frame((1, 2)),
            _metadata(chunk_number=1),
        ),
        (
            _frame((3, 4)),
            _metadata(chunk_number=2),
        ),
        (
            _frame((5, 6)),
            _metadata(chunk_number=3),
        ),
    ]

    checkpoint_dir = tmp_path / "checkpoints"

    process_dataset(
        chunks,
        transformer=lambda frame, metadata: frame,
        checkpoint_dir=checkpoint_dir,
        checkpoint_interval=2,
    )

    checkpoints = sorted(
        checkpoint_dir.glob(
            "chunk-*.parquet"
        )
    )

    assert [path.name for path in checkpoints] == [
        "chunk-00000002.parquet",
    ]


def test_process_dataset_to_dataframe_combines_processed_chunks() -> None:
    chunks = [
        (
            _frame((1, 2)),
            _metadata(chunk_number=1),
        ),
        (
            _frame((3, 4)),
            _metadata(chunk_number=2),
        ),
    ]

    result = process_dataset_to_dataframe(
        chunks,
        transformer=lambda frame, metadata: frame.assign(
            processed=True
        ),
    )

    expected = pd.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "amount": [
                10.0,
                20.0,
                10.0,
                20.0,
            ],
            "processed": [
                True,
                True,
                True,
                True,
            ],
        }
    )

    pd.testing.assert_frame_equal(
        result.reset_index(drop=True),
        expected,
    )


def test_process_dataset_to_dataframe_returns_empty_dataframe() -> None:
    result = process_dataset_to_dataframe(
        iter(()),
        transformer=lambda frame, metadata: frame,
    )

    assert isinstance(
        result,
        pd.DataFrame,
    )
    assert result.empty


def test_process_dataset_to_dataframe_resets_index() -> None:
    chunks = [
        (
            pd.DataFrame(
                {
                    "id": [10, 20],
                    "amount": [100.0, 200.0],
                },
                index=[10, 20],
            ),
            _metadata(),
        )
    ]

    result = process_dataset_to_dataframe(
        chunks,
        transformer=lambda frame, metadata: frame,
    )

    assert result.index.tolist() == [0, 1]


def test_load_checkpoints_returns_checkpoints_in_order(
    tmp_path: Path,
) -> None:
    checkpoint_dir = tmp_path / "checkpoints"
    checkpoint_dir.mkdir()

    first = checkpoint_dir / "chunk-00000001.parquet"
    second = checkpoint_dir / "chunk-00000002.parquet"

    _frame((1, 2)).to_parquet(
        first,
        index=False,
    )
    _frame((3, 4)).to_parquet(
        second,
        index=False,
    )

    loaded = load_checkpoints(
        checkpoint_dir
    )

    assert len(loaded) == 2
    assert [
        path.name
        for path in loaded
    ] == [
        "chunk-00000001.parquet",
        "chunk-00000002.parquet",
    ]


def test_load_checkpoints_returns_empty_list_for_missing_directory(
    tmp_path: Path,
) -> None:
    loaded = load_checkpoints(
        tmp_path / "missing"
    )

    assert loaded == []


def test_load_checkpoints_ignores_non_checkpoint_files(
    tmp_path: Path,
) -> None:
    checkpoint_dir = tmp_path / "checkpoints"
    checkpoint_dir.mkdir()

    _frame().to_parquet(
        checkpoint_dir / "chunk-00000001.parquet",
        index=False,
    )
    (checkpoint_dir / "notes.txt").write_text(
        "ignore me",
        encoding="utf-8",
    )

    loaded = load_checkpoints(
        checkpoint_dir
    )

    assert len(loaded) == 1
    assert loaded[0].name == (
        "chunk-00000001.parquet"
    )


def test_cleanup_checkpoints_removes_checkpoint_files(
    tmp_path: Path,
) -> None:
    checkpoint_dir = tmp_path / "checkpoints"
    checkpoint_dir.mkdir()

    for number in (1, 2, 3):
        _frame().to_parquet(
            checkpoint_dir
            / f"chunk-{number:08d}.parquet",
            index=False,
        )

    removed = cleanup_checkpoints(
        checkpoint_dir
    )

    assert removed == 3
    assert list(
        checkpoint_dir.glob("chunk-*.parquet")
    ) == []


def test_cleanup_checkpoints_is_idempotent(
    tmp_path: Path,
) -> None:
    checkpoint_dir = tmp_path / "checkpoints"

    assert cleanup_checkpoints(
        checkpoint_dir
    ) == 0

    assert cleanup_checkpoints(
        checkpoint_dir
    ) == 0


def test_process_dataset_accepts_named_transformer() -> None:
    calls: list[int] = []

    def transformer(
        frame: pd.DataFrame,
        metadata: ChunkMetadata,
    ) -> pd.DataFrame:
        calls.append(
            metadata.chunk_number
        )
        return frame.copy()

    chunks = [
        (
            _frame(),
            _metadata(chunk_number=1),
        ),
        (
            _frame(),
            _metadata(chunk_number=2),
        ),
    ]

    results = process_dataset(
        chunks,
        transformer=transformer,
    )

    assert len(results) == 2
    assert calls == [1, 2]


def test_process_chunk_supports_transformer_returning_same_dataframe() -> None:
    frame = _frame()

    result = process_chunk(
        frame,
        _metadata(),
        lambda chunk, metadata: chunk,
    )

    pd.testing.assert_frame_equal(
        result.data,
        frame,
    )


def test_processing_metrics_report_removed_rows() -> None:
    def transformer(
        frame: pd.DataFrame,
        metadata: ChunkMetadata,
    ) -> pd.DataFrame:
        return frame.iloc[:1].copy()

    result = process_chunk(
        _frame(),
        _metadata(),
        transformer,
    )

    assert result.metrics.rows_input == 2
    assert result.metrics.rows_processed == 1
    assert result.metrics.rows_removed == 1


def test_processing_metrics_are_non_negative() -> None:
    result = process_chunk(
        _frame(),
        _metadata(),
        lambda frame, metadata: frame.copy(),
    )

    assert result.metrics.rows_input >= 0
    assert result.metrics.rows_processed >= 0
    assert result.metrics.rows_removed >= 0
    assert result.metrics.input_memory_bytes >= 0
    assert result.metrics.output_memory_bytes >= 0