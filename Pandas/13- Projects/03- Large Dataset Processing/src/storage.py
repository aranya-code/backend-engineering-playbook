from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import pandas as pd

from .config import PipelineConfig, config


class StorageError(RuntimeError):
    """Raised when dataset storage operations cannot complete safely."""


def _temporary_path(
    destination: Path,
) -> Path:
    """Create a temporary file path in the destination directory."""
    destination = Path(destination).expanduser().resolve()
    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    handle = NamedTemporaryFile(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
        delete=False,
    )
    temporary = Path(handle.name)
    handle.close()

    return temporary


def _atomic_replace(
    temporary: Path,
    destination: Path,
) -> None:
    """Atomically replace a destination file with a completed temporary file."""
    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    os.replace(
        temporary,
        destination,
    )


def _cleanup_temporary(
    path: Path,
) -> None:
    """Best-effort cleanup of a temporary output file."""
    try:
        path.unlink(
            missing_ok=True
        )
    except OSError:
        pass


def _prepare_destination(
    destination: Path,
) -> Path:
    """Normalize an output destination."""
    return Path(
        destination
    ).expanduser().resolve()


def write_parquet(
    frame: pd.DataFrame,
    destination: Path,
    *,
    pipeline_config: PipelineConfig = config,
    atomic: bool | None = None,
) -> Path:
    """Write a DataFrame to Parquet using an atomic replacement when enabled."""
    if not isinstance(
        frame,
        pd.DataFrame,
    ):
        raise StorageError(
            "frame must be a pandas DataFrame."
        )

    destination = _prepare_destination(
        destination
    )
    use_atomic = (
        pipeline_config.atomic_writes
        if atomic is None
        else atomic
    )

    temporary: Path | None = None

    try:
        if use_atomic:
            temporary = _temporary_path(
                destination
            )
            output = temporary
        else:
            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            output = destination

        frame.to_parquet(
            output,
            compression=pipeline_config.parquet_compression,
            index=False,
        )

        if use_atomic:
            assert temporary is not None
            _atomic_replace(
                temporary,
                destination,
            )

        return destination

    except (
        OSError,
        ValueError,
        TypeError,
        ImportError,
    ) as exc:
        if temporary is not None:
            _cleanup_temporary(
                temporary
            )

        raise StorageError(
            f"Failed to write Parquet file: {destination}"
        ) from exc


def read_parquet(
    source: Path,
    *,
    columns: list[str] | None = None,
) -> pd.DataFrame:
    """Read a Parquet file into a DataFrame."""
    source = Path(
        source
    ).expanduser().resolve()

    if not source.exists():
        raise StorageError(
            f"Parquet file does not exist: {source}"
        )

    try:
        return pd.read_parquet(
            source,
            columns=columns,
        )
    except (
        OSError,
        ValueError,
        TypeError,
        ImportError,
    ) as exc:
        raise StorageError(
            f"Failed to read Parquet file: {source}"
        ) from exc


def write_csv(
    frame: pd.DataFrame,
    destination: Path,
    *,
    pipeline_config: PipelineConfig = config,
    atomic: bool | None = None,
) -> Path:
    """Write a DataFrame to CSV with configured encoding and delimiter."""
    if not isinstance(
        frame,
        pd.DataFrame,
    ):
        raise StorageError(
            "frame must be a pandas DataFrame."
        )

    destination = _prepare_destination(
        destination
    )
    use_atomic = (
        pipeline_config.atomic_writes
        if atomic is None
        else atomic
    )

    temporary: Path | None = None

    try:
        if use_atomic:
            temporary = _temporary_path(
                destination
            )
            output = temporary
        else:
            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            output = destination

        frame.to_csv(
            output,
            index=False,
            encoding=pipeline_config.csv_encoding,
            sep=pipeline_config.csv_separator,
        )

        if use_atomic:
            assert temporary is not None
            _atomic_replace(
                temporary,
                destination,
            )

        return destination

    except (
        OSError,
        ValueError,
        TypeError,
    ) as exc:
        if temporary is not None:
            _cleanup_temporary(
                temporary
            )

        raise StorageError(
            f"Failed to write CSV file: {destination}"
        ) from exc


def read_csv(
    source: Path,
    *,
    pipeline_config: PipelineConfig = config,
    usecols: list[str] | None = None,
    nrows: int | None = None,
) -> pd.DataFrame:
    """Read a CSV file into memory for operations that require a full DataFrame."""
    source = Path(
        source
    ).expanduser().resolve()

    if not source.exists():
        raise StorageError(
            f"CSV file does not exist: {source}"
        )

    try:
        return pd.read_csv(
            source,
            sep=pipeline_config.csv_separator,
            encoding=pipeline_config.csv_encoding,
            usecols=usecols,
            nrows=nrows,
            low_memory=pipeline_config.low_memory,
            memory_map=pipeline_config.memory_map,
        )
    except (
        OSError,
        UnicodeDecodeError,
        pd.errors.ParserError,
        pd.errors.EmptyDataError,
        ValueError,
        TypeError,
    ) as exc:
        raise StorageError(
            f"Failed to read CSV file: {source}"
        ) from exc


def append_parquet(
    frame: pd.DataFrame,
    destination: Path,
    *,
    pipeline_config: PipelineConfig = config,
) -> Path:
    """Append a DataFrame by writing it as a partition-style Parquet file."""
    if not isinstance(
        frame,
        pd.DataFrame,
    ):
        raise StorageError(
            "frame must be a pandas DataFrame."
        )

    destination = _prepare_destination(
        destination
    )
    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if destination.suffix.lower() != ".parquet":
        raise StorageError(
            "append_parquet requires a .parquet destination."
        )

    if destination.exists():
        try:
            existing = pd.read_parquet(
                destination
            )
            combined = pd.concat(
                [
                    existing,
                    frame,
                ],
                ignore_index=True,
            )
        except (
            OSError,
            ValueError,
            TypeError,
            ImportError,
        ) as exc:
            raise StorageError(
                f"Failed to read existing Parquet file: {destination}"
            ) from exc

        return write_parquet(
            combined,
            destination,
            pipeline_config=pipeline_config,
        )

    return write_parquet(
        frame,
        destination,
        pipeline_config=pipeline_config,
    )


def write_partition(
    frame: pd.DataFrame,
    destination_dir: Path,
    *,
    partition_number: int,
    pipeline_config: PipelineConfig = config,
) -> Path:
    """Write one processed chunk as an independently readable Parquet partition."""
    if partition_number < 1:
        raise StorageError(
            "partition_number must be greater than or equal to 1."
        )

    destination_dir = (
        Path(destination_dir)
        .expanduser()
        .resolve()
    )
    destination_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination = (
        destination_dir
        / f"part-{partition_number:08d}.parquet"
    )

    return write_parquet(
        frame,
        destination,
        pipeline_config=pipeline_config,
    )


def iter_partition_files(
    directory: Path,
) -> Iterable[Path]:
    """Yield partition files in deterministic lexical order."""
    directory = (
        Path(directory)
        .expanduser()
        .resolve()
    )

    if not directory.exists():
        return iter(())

    return iter(
        sorted(
            directory.glob(
                "part-*.parquet"
            )
        )
    )


def read_partitions(
    directory: Path,
) -> pd.DataFrame:
    """Read and combine all Parquet partitions from a directory."""
    files = list(
        iter_partition_files(
            directory
        )
    )

    if not files:
        return pd.DataFrame()

    frames: list[pd.DataFrame] = []

    for path in files:
        frames.append(
            read_parquet(
                path
            )
        )

    return pd.concat(
        frames,
        ignore_index=True,
    )


def write_processing_report(
    report: pd.DataFrame,
    destination: Path,
    *,
    pipeline_config: PipelineConfig = config,
) -> Path:
    """Persist a processing metrics report as Parquet."""
    if not isinstance(
        report,
        pd.DataFrame,
    ):
        raise StorageError(
            "report must be a pandas DataFrame."
        )

    return write_parquet(
        report,
        destination,
        pipeline_config=pipeline_config,
    )


def write_checkpoint(
    frame: pd.DataFrame,
    checkpoint_dir: Path,
    *,
    chunk_number: int,
    pipeline_config: PipelineConfig = config,
) -> Path:
    """Persist a processed chunk as a resumable checkpoint."""
    if chunk_number < 1:
        raise StorageError(
            "chunk_number must be greater than or equal to 1."
        )

    checkpoint_dir = (
        Path(checkpoint_dir)
        .expanduser()
        .resolve()
    )

    destination = (
        checkpoint_dir
        / f"chunk-{chunk_number:08d}.parquet"
    )

    return write_parquet(
        frame,
        destination,
        pipeline_config=pipeline_config,
    )


def read_checkpoint(
    checkpoint_path: Path,
) -> pd.DataFrame:
    """Read a single persisted checkpoint."""
    return read_parquet(
        checkpoint_path
    )


def list_checkpoints(
    checkpoint_dir: Path,
) -> list[Path]:
    """Return checkpoint files in deterministic processing order."""
    checkpoint_dir = (
        Path(checkpoint_dir)
        .expanduser()
        .resolve()
    )

    if not checkpoint_dir.exists():
        return []

    return sorted(
        checkpoint_dir.glob(
            "chunk-*.parquet"
        )
    )


def cleanup_checkpoints(
    checkpoint_dir: Path,
) -> int:
    """Remove persisted checkpoints and return the number deleted."""
    paths = list_checkpoints(
        checkpoint_dir
    )
    removed = 0

    for path in paths:
        try:
            path.unlink()
            removed += 1
        except OSError as exc:
            raise StorageError(
                f"Failed to remove checkpoint: {path}"
            ) from exc

    return removed


def file_exists(
    path: Path,
) -> bool:
    """Return whether a path exists and is a regular file."""
    return (
        Path(path)
        .expanduser()
        .resolve()
        .is_file()
    )


def remove_file(
    path: Path,
) -> bool:
    """Remove a file if it exists and report whether it was removed."""
    path = (
        Path(path)
        .expanduser()
        .resolve()
    )

    if not path.exists():
        return False

    if not path.is_file():
        raise StorageError(
            f"Path is not a regular file: {path}"
        )

    try:
        path.unlink()
    except OSError as exc:
        raise StorageError(
            f"Failed to remove file: {path}"
        ) from exc

    return True


def ensure_storage_directories(
    pipeline_config: PipelineConfig = config,
) -> None:
    """Create configured storage directories."""
    try:
        pipeline_config.ensure_directories()
    except OSError as exc:
        raise StorageError(
            "Failed to create configured storage directories."
        ) from exc


__all__ = [
    "StorageError",
    "append_parquet",
    "cleanup_checkpoints",
    "ensure_storage_directories",
    "file_exists",
    "iter_partition_files",
    "list_checkpoints",
    "read_checkpoint",
    "read_csv",
    "read_parquet",
    "read_partitions",
    "remove_file",
    "write_checkpoint",
    "write_csv",
    "write_parquet",
    "write_partition",
    "write_processing_report",
]

from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import pandas as pd

from .config import PipelineConfig, config


class StorageError(RuntimeError):
    """Raised when dataset storage operations cannot complete safely."""


def _temporary_path(
    destination: Path,
) -> Path:
    """Create a temporary file path in the destination directory."""
    destination = Path(destination).expanduser().resolve()
    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    handle = NamedTemporaryFile(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
        delete=False,
    )
    temporary = Path(handle.name)
    handle.close()

    return temporary


def _atomic_replace(
    temporary: Path,
    destination: Path,
) -> None:
    """Atomically replace a destination file with a completed temporary file."""
    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    os.replace(
        temporary,
        destination,
    )


def _cleanup_temporary(
    path: Path,
) -> None:
    """Best-effort cleanup of a temporary output file."""
    try:
        path.unlink(
            missing_ok=True
        )
    except OSError:
        pass


def _prepare_destination(
    destination: Path,
) -> Path:
    """Normalize an output destination."""
    return Path(
        destination
    ).expanduser().resolve()


def write_parquet(
    frame: pd.DataFrame,
    destination: Path,
    *,
    pipeline_config: PipelineConfig = config,
    atomic: bool | None = None,
) -> Path:
    """Write a DataFrame to Parquet using an atomic replacement when enabled."""
    if not isinstance(
        frame,
        pd.DataFrame,
    ):
        raise StorageError(
            "frame must be a pandas DataFrame."
        )

    destination = _prepare_destination(
        destination
    )
    use_atomic = (
        pipeline_config.atomic_writes
        if atomic is None
        else atomic
    )

    temporary: Path | None = None

    try:
        if use_atomic:
            temporary = _temporary_path(
                destination
            )
            output = temporary
        else:
            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            output = destination

        frame.to_parquet(
            output,
            compression=pipeline_config.parquet_compression,
            index=False,
        )

        if use_atomic:
            assert temporary is not None
            _atomic_replace(
                temporary,
                destination,
            )

        return destination

    except (
        OSError,
        ValueError,
        TypeError,
        ImportError,
    ) as exc:
        if temporary is not None:
            _cleanup_temporary(
                temporary
            )

        raise StorageError(
            f"Failed to write Parquet file: {destination}"
        ) from exc


def read_parquet(
    source: Path,
    *,
    columns: list[str] | None = None,
) -> pd.DataFrame:
    """Read a Parquet file into a DataFrame."""
    source = Path(
        source
    ).expanduser().resolve()

    if not source.exists():
        raise StorageError(
            f"Parquet file does not exist: {source}"
        )

    try:
        return pd.read_parquet(
            source,
            columns=columns,
        )
    except (
        OSError,
        ValueError,
        TypeError,
        ImportError,
    ) as exc:
        raise StorageError(
            f"Failed to read Parquet file: {source}"
        ) from exc


def write_csv(
    frame: pd.DataFrame,
    destination: Path,
    *,
    pipeline_config: PipelineConfig = config,
    atomic: bool | None = None,
) -> Path:
    """Write a DataFrame to CSV with configured encoding and delimiter."""
    if not isinstance(
        frame,
        pd.DataFrame,
    ):
        raise StorageError(
            "frame must be a pandas DataFrame."
        )

    destination = _prepare_destination(
        destination
    )
    use_atomic = (
        pipeline_config.atomic_writes
        if atomic is None
        else atomic
    )

    temporary: Path | None = None

    try:
        if use_atomic:
            temporary = _temporary_path(
                destination
            )
            output = temporary
        else:
            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            output = destination

        frame.to_csv(
            output,
            index=False,
            encoding=pipeline_config.csv_encoding,
            sep=pipeline_config.csv_separator,
        )

        if use_atomic:
            assert temporary is not None
            _atomic_replace(
                temporary,
                destination,
            )

        return destination

    except (
        OSError,
        ValueError,
        TypeError,
    ) as exc:
        if temporary is not None:
            _cleanup_temporary(
                temporary
            )

        raise StorageError(
            f"Failed to write CSV file: {destination}"
        ) from exc


def read_csv(
    source: Path,
    *,
    pipeline_config: PipelineConfig = config,
    usecols: list[str] | None = None,
    nrows: int | None = None,
) -> pd.DataFrame:
    """Read a CSV file into memory for operations that require a full DataFrame."""
    source = Path(
        source
    ).expanduser().resolve()

    if not source.exists():
        raise StorageError(
            f"CSV file does not exist: {source}"
        )

    try:
        return pd.read_csv(
            source,
            sep=pipeline_config.csv_separator,
            encoding=pipeline_config.csv_encoding,
            usecols=usecols,
            nrows=nrows,
            low_memory=pipeline_config.low_memory,
            memory_map=pipeline_config.memory_map,
        )
    except (
        OSError,
        UnicodeDecodeError,
        pd.errors.ParserError,
        pd.errors.EmptyDataError,
        ValueError,
        TypeError,
    ) as exc:
        raise StorageError(
            f"Failed to read CSV file: {source}"
        ) from exc


def append_parquet(
    frame: pd.DataFrame,
    destination: Path,
    *,
    pipeline_config: PipelineConfig = config,
) -> Path:
    """Append a DataFrame by writing it as a partition-style Parquet file."""
    if not isinstance(
        frame,
        pd.DataFrame,
    ):
        raise StorageError(
            "frame must be a pandas DataFrame."
        )

    destination = _prepare_destination(
        destination
    )
    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if destination.suffix.lower() != ".parquet":
        raise StorageError(
            "append_parquet requires a .parquet destination."
        )

    if destination.exists():
        try:
            existing = pd.read_parquet(
                destination
            )
            combined = pd.concat(
                [
                    existing,
                    frame,
                ],
                ignore_index=True,
            )
        except (
            OSError,
            ValueError,
            TypeError,
            ImportError,
        ) as exc:
            raise StorageError(
                f"Failed to read existing Parquet file: {destination}"
            ) from exc

        return write_parquet(
            combined,
            destination,
            pipeline_config=pipeline_config,
        )

    return write_parquet(
        frame,
        destination,
        pipeline_config=pipeline_config,
    )


def write_partition(
    frame: pd.DataFrame,
    destination_dir: Path,
    *,
    partition_number: int,
    pipeline_config: PipelineConfig = config,
) -> Path:
    """Write one processed chunk as an independently readable Parquet partition."""
    if partition_number < 1:
        raise StorageError(
            "partition_number must be greater than or equal to 1."
        )

    destination_dir = (
        Path(destination_dir)
        .expanduser()
        .resolve()
    )
    destination_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination = (
        destination_dir
        / f"part-{partition_number:08d}.parquet"
    )

    return write_parquet(
        frame,
        destination,
        pipeline_config=pipeline_config,
    )


def iter_partition_files(
    directory: Path,
) -> Iterable[Path]:
    """Yield partition files in deterministic lexical order."""
    directory = (
        Path(directory)
        .expanduser()
        .resolve()
    )

    if not directory.exists():
        return iter(())

    return iter(
        sorted(
            directory.glob(
                "part-*.parquet"
            )
        )
    )


def read_partitions(
    directory: Path,
) -> pd.DataFrame:
    """Read and combine all Parquet partitions from a directory."""
    files = list(
        iter_partition_files(
            directory
        )
    )

    if not files:
        return pd.DataFrame()

    frames: list[pd.DataFrame] = []

    for path in files:
        frames.append(
            read_parquet(
                path
            )
        )

    return pd.concat(
        frames,
        ignore_index=True,
    )


def write_processing_report(
    report: pd.DataFrame,
    destination: Path,
    *,
    pipeline_config: PipelineConfig = config,
) -> Path:
    """Persist a processing metrics report as Parquet."""
    if not isinstance(
        report,
        pd.DataFrame,
    ):
        raise StorageError(
            "report must be a pandas DataFrame."
        )

    return write_parquet(
        report,
        destination,
        pipeline_config=pipeline_config,
    )


def write_checkpoint(
    frame: pd.DataFrame,
    checkpoint_dir: Path,
    *,
    chunk_number: int,
    pipeline_config: PipelineConfig = config,
) -> Path:
    """Persist a processed chunk as a resumable checkpoint."""
    if chunk_number < 1:
        raise StorageError(
            "chunk_number must be greater than or equal to 1."
        )

    checkpoint_dir = (
        Path(checkpoint_dir)
        .expanduser()
        .resolve()
    )

    destination = (
        checkpoint_dir
        / f"chunk-{chunk_number:08d}.parquet"
    )

    return write_parquet(
        frame,
        destination,
        pipeline_config=pipeline_config,
    )


def read_checkpoint(
    checkpoint_path: Path,
) -> pd.DataFrame:
    """Read a single persisted checkpoint."""
    return read_parquet(
        checkpoint_path
    )


def list_checkpoints(
    checkpoint_dir: Path,
) -> list[Path]:
    """Return checkpoint files in deterministic processing order."""
    checkpoint_dir = (
        Path(checkpoint_dir)
        .expanduser()
        .resolve()
    )

    if not checkpoint_dir.exists():
        return []

    return sorted(
        checkpoint_dir.glob(
            "chunk-*.parquet"
        )
    )


def cleanup_checkpoints(
    checkpoint_dir: Path,
) -> int:
    """Remove persisted checkpoints and return the number deleted."""
    paths = list_checkpoints(
        checkpoint_dir
    )
    removed = 0

    for path in paths:
        try:
            path.unlink()
            removed += 1
        except OSError as exc:
            raise StorageError(
                f"Failed to remove checkpoint: {path}"
            ) from exc

    return removed


def file_exists(
    path: Path,
) -> bool:
    """Return whether a path exists and is a regular file."""
    return (
        Path(path)
        .expanduser()
        .resolve()
        .is_file()
    )


def remove_file(
    path: Path,
) -> bool:
    """Remove a file if it exists and report whether it was removed."""
    path = (
        Path(path)
        .expanduser()
        .resolve()
    )

    if not path.exists():
        return False

    if not path.is_file():
        raise StorageError(
            f"Path is not a regular file: {path}"
        )

    try:
        path.unlink()
    except OSError as exc:
        raise StorageError(
            f"Failed to remove file: {path}"
        ) from exc

    return True


def ensure_storage_directories(
    pipeline_config: PipelineConfig = config,
) -> None:
    """Create configured storage directories."""
    try:
        pipeline_config.ensure_directories()
    except OSError as exc:
        raise StorageError(
            "Failed to create configured storage directories."
        ) from exc


__all__ = [
    "StorageError",
    "append_parquet",
    "cleanup_checkpoints",
    "ensure_storage_directories",
    "file_exists",
    "iter_partition_files",
    "list_checkpoints",
    "read_checkpoint",
    "read_csv",
    "read_parquet",
    "read_partitions",
    "remove_file",
    "write_checkpoint",
    "write_csv",
    "write_parquet",
    "write_partition",
    "write_processing_report",
]