from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd


class StorageError(RuntimeError):
    """Raised when a storage operation cannot be completed safely."""


def _temporary_path(path: Path) -> Path:
    """Return a process-specific temporary path beside the target."""
    return path.with_name(
        f".{path.name}.tmp-{os.getpid()}",
    )


def _ensure_parent_directory(path: Path) -> None:
    """Create the target parent directory when necessary."""
    try:
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
    except OSError as exc:
        raise StorageError(
            f"Failed to create output directory: {path.parent}"
        ) from exc


def _atomic_replace(
    temporary_path: Path,
    target_path: Path,
) -> None:
    """Atomically replace a target file with a completed temporary file."""
    try:
        os.replace(
            temporary_path,
            target_path,
        )
    except OSError as exc:
        raise StorageError(
            f"Failed to publish output file: {target_path}"
        ) from exc


def write_json(
    payload: Any,
    path: Path,
    *,
    atomic: bool = True,
) -> None:
    """Write a JSON-compatible payload to disk."""
    if not isinstance(path, Path):
        raise StorageError(
            "path must be a pathlib.Path instance."
        )

    _ensure_parent_directory(path)

    target_path = path
    temporary_path = _temporary_path(target_path)

    output_path = temporary_path if atomic else target_path

    try:
        if isinstance(payload, pd.DataFrame):
            payload.to_json(
                output_path,
                orient="records",
                date_format="iso",
                force_ascii=False,
            )
        elif isinstance(payload, (dict, list, tuple)):
            import json

            with output_path.open(
                "w",
                encoding="utf-8",
            ) as handle:
                json.dump(
                    payload,
                    handle,
                    ensure_ascii=False,
                    indent=2,
                )
        else:
            raise StorageError(
                "payload must be a pandas DataFrame or JSON-compatible "
                "mapping/sequence."
            )

        if atomic:
            _atomic_replace(
                temporary_path,
                target_path,
            )
    except (OSError, TypeError, ValueError, OverflowError) as exc:
        temporary_path.unlink(
            missing_ok=True,
        )
        if isinstance(exc, StorageError):
            raise
        raise StorageError(
            f"Failed to write JSON output: {target_path}"
        ) from exc


def read_json(
    path: Path,
) -> Any:
    """Read JSON data from disk."""
    if not isinstance(path, Path):
        raise StorageError(
            "path must be a pathlib.Path instance."
        )

    if not path.exists():
        raise StorageError(
            f"Input file does not exist: {path}"
        )

    if not path.is_file():
        raise StorageError(
            f"Input path is not a file: {path}"
        )

    try:
        import json

        with path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            return json.load(handle)
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        raise StorageError(
            f"Failed to read JSON input: {path}"
        ) from exc


def write_parquet(
    frame: pd.DataFrame,
    path: Path,
    *,
    atomic: bool = True,
) -> None:
    """Write a DataFrame to Parquet with optional atomic publication."""
    if not isinstance(frame, pd.DataFrame):
        raise StorageError(
            "frame must be a pandas DataFrame."
        )

    if not isinstance(path, Path):
        raise StorageError(
            "path must be a pathlib.Path instance."
        )

    _ensure_parent_directory(path)

    target_path = path
    temporary_path = _temporary_path(target_path)
    output_path = temporary_path if atomic else target_path

    try:
        frame.to_parquet(
            output_path,
            index=False,
        )

        if atomic:
            _atomic_replace(
                temporary_path,
                target_path,
            )
    except (OSError, ImportError, ValueError) as exc:
        temporary_path.unlink(
            missing_ok=True,
        )
        if isinstance(exc, StorageError):
            raise
        raise StorageError(
            f"Failed to write Parquet output: {target_path}"
        ) from exc


def read_parquet(
    path: Path,
) -> pd.DataFrame:
    """Read a Parquet dataset into a DataFrame."""
    if not isinstance(path, Path):
        raise StorageError(
            "path must be a pathlib.Path instance."
        )

    if not path.exists():
        raise StorageError(
            f"Input file does not exist: {path}"
        )

    if not path.is_file():
        raise StorageError(
            f"Input path is not a file: {path}"
        )

    try:
        return pd.read_parquet(
            path,
        )
    except (OSError, ImportError, ValueError) as exc:
        raise StorageError(
            f"Failed to read Parquet input: {path}"
        ) from exc


def write_csv(
    frame: pd.DataFrame,
    path: Path,
    *,
    atomic: bool = True,
) -> None:
    """Write a DataFrame to CSV with optional atomic publication."""
    if not isinstance(frame, pd.DataFrame):
        raise StorageError(
            "frame must be a pandas DataFrame."
        )

    if not isinstance(path, Path):
        raise StorageError(
            "path must be a pathlib.Path instance."
        )

    _ensure_parent_directory(path)

    target_path = path
    temporary_path = _temporary_path(target_path)
    output_path = temporary_path if atomic else target_path

    try:
        frame.to_csv(
            output_path,
            index=False,
        )

        if atomic:
            _atomic_replace(
                temporary_path,
                target_path,
            )
    except (OSError, ValueError) as exc:
        temporary_path.unlink(
            missing_ok=True,
        )
        if isinstance(exc, StorageError):
            raise
        raise StorageError(
            f"Failed to write CSV output: {target_path}"
        ) from exc


def read_csv(
    path: Path,
    *,
    **read_options: Any,
) -> pd.DataFrame:
    """Read a CSV dataset into a DataFrame."""
    if not isinstance(path, Path):
        raise StorageError(
            "path must be a pathlib.Path instance."
        )

    if not path.exists():
        raise StorageError(
            f"Input file does not exist: {path}"
        )

    if not path.is_file():
        raise StorageError(
            f"Input path is not a file: {path}"
        )

    try:
        return pd.read_csv(
            path,
            **read_options,
        )
    except (
        OSError,
        UnicodeDecodeError,
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        ValueError,
    ) as exc:
        raise StorageError(
            f"Failed to read CSV input: {path}"
        ) from exc


def file_exists(path: Path) -> bool:
    """Return whether the configured path exists as a regular file."""
    if not isinstance(path, Path):
        raise StorageError(
            "path must be a pathlib.Path instance."
        )

    return path.is_file()


def remove_file(path: Path) -> None:
    """Remove a file when it exists."""
    if not isinstance(path, Path):
        raise StorageError(
            "path must be a pathlib.Path instance."
        )

    try:
        path.unlink(
            missing_ok=True,
        )
    except OSError as exc:
        raise StorageError(
            f"Failed to remove file: {path}"
        ) from exc


__all__ = [
    "StorageError",
    "file_exists",
    "read_csv",
    "read_json",
    "read_parquet",
    "remove_file",
    "write_csv",
    "write_json",
    "write_parquet",
]

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd


class StorageError(RuntimeError):
    """Raised when a storage operation cannot be completed safely."""


def _temporary_path(path: Path) -> Path:
    """Return a process-specific temporary path beside the target."""
    return path.with_name(
        f".{path.name}.tmp-{os.getpid()}",
    )


def _ensure_parent_directory(path: Path) -> None:
    """Create the target parent directory when necessary."""
    try:
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
    except OSError as exc:
        raise StorageError(
            f"Failed to create output directory: {path.parent}"
        ) from exc


def _atomic_replace(
    temporary_path: Path,
    target_path: Path,
) -> None:
    """Atomically replace a target file with a completed temporary file."""
    try:
        os.replace(
            temporary_path,
            target_path,
        )
    except OSError as exc:
        raise StorageError(
            f"Failed to publish output file: {target_path}"
        ) from exc


def write_json(
    payload: Any,
    path: Path,
    *,
    atomic: bool = True,
) -> None:
    """Write a JSON-compatible payload to disk."""
    if not isinstance(path, Path):
        raise StorageError(
            "path must be a pathlib.Path instance."
        )

    _ensure_parent_directory(path)

    target_path = path
    temporary_path = _temporary_path(target_path)

    output_path = temporary_path if atomic else target_path

    try:
        if isinstance(payload, pd.DataFrame):
            payload.to_json(
                output_path,
                orient="records",
                date_format="iso",
                force_ascii=False,
            )
        elif isinstance(payload, (dict, list, tuple)):
            import json

            with output_path.open(
                "w",
                encoding="utf-8",
            ) as handle:
                json.dump(
                    payload,
                    handle,
                    ensure_ascii=False,
                    indent=2,
                )
        else:
            raise StorageError(
                "payload must be a pandas DataFrame or JSON-compatible "
                "mapping/sequence."
            )

        if atomic:
            _atomic_replace(
                temporary_path,
                target_path,
            )
    except (OSError, TypeError, ValueError, OverflowError) as exc:
        temporary_path.unlink(
            missing_ok=True,
        )
        if isinstance(exc, StorageError):
            raise
        raise StorageError(
            f"Failed to write JSON output: {target_path}"
        ) from exc


def read_json(
    path: Path,
) -> Any:
    """Read JSON data from disk."""
    if not isinstance(path, Path):
        raise StorageError(
            "path must be a pathlib.Path instance."
        )

    if not path.exists():
        raise StorageError(
            f"Input file does not exist: {path}"
        )

    if not path.is_file():
        raise StorageError(
            f"Input path is not a file: {path}"
        )

    try:
        import json

        with path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            return json.load(handle)
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        raise StorageError(
            f"Failed to read JSON input: {path}"
        ) from exc


def write_parquet(
    frame: pd.DataFrame,
    path: Path,
    *,
    atomic: bool = True,
) -> None:
    """Write a DataFrame to Parquet with optional atomic publication."""
    if not isinstance(frame, pd.DataFrame):
        raise StorageError(
            "frame must be a pandas DataFrame."
        )

    if not isinstance(path, Path):
        raise StorageError(
            "path must be a pathlib.Path instance."
        )

    _ensure_parent_directory(path)

    target_path = path
    temporary_path = _temporary_path(target_path)
    output_path = temporary_path if atomic else target_path

    try:
        frame.to_parquet(
            output_path,
            index=False,
        )

        if atomic:
            _atomic_replace(
                temporary_path,
                target_path,
            )
    except (OSError, ImportError, ValueError) as exc:
        temporary_path.unlink(
            missing_ok=True,
        )
        if isinstance(exc, StorageError):
            raise
        raise StorageError(
            f"Failed to write Parquet output: {target_path}"
        ) from exc


def read_parquet(
    path: Path,
) -> pd.DataFrame:
    """Read a Parquet dataset into a DataFrame."""
    if not isinstance(path, Path):
        raise StorageError(
            "path must be a pathlib.Path instance."
        )

    if not path.exists():
        raise StorageError(
            f"Input file does not exist: {path}"
        )

    if not path.is_file():
        raise StorageError(
            f"Input path is not a file: {path}"
        )

    try:
        return pd.read_parquet(
            path,
        )
    except (OSError, ImportError, ValueError) as exc:
        raise StorageError(
            f"Failed to read Parquet input: {path}"
        ) from exc


def write_csv(
    frame: pd.DataFrame,
    path: Path,
    *,
    atomic: bool = True,
) -> None:
    """Write a DataFrame to CSV with optional atomic publication."""
    if not isinstance(frame, pd.DataFrame):
        raise StorageError(
            "frame must be a pandas DataFrame."
        )

    if not isinstance(path, Path):
        raise StorageError(
            "path must be a pathlib.Path instance."
        )

    _ensure_parent_directory(path)

    target_path = path
    temporary_path = _temporary_path(target_path)
    output_path = temporary_path if atomic else target_path

    try:
        frame.to_csv(
            output_path,
            index=False,
        )

        if atomic:
            _atomic_replace(
                temporary_path,
                target_path,
            )
    except (OSError, ValueError) as exc:
        temporary_path.unlink(
            missing_ok=True,
        )
        if isinstance(exc, StorageError):
            raise
        raise StorageError(
            f"Failed to write CSV output: {target_path}"
        ) from exc


def read_csv(
    path: Path,
    *,
    **read_options: Any,
) -> pd.DataFrame:
    """Read a CSV dataset into a DataFrame."""
    if not isinstance(path, Path):
        raise StorageError(
            "path must be a pathlib.Path instance."
        )

    if not path.exists():
        raise StorageError(
            f"Input file does not exist: {path}"
        )

    if not path.is_file():
        raise StorageError(
            f"Input path is not a file: {path}"
        )

    try:
        return pd.read_csv(
            path,
            **read_options,
        )
    except (
        OSError,
        UnicodeDecodeError,
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        ValueError,
    ) as exc:
        raise StorageError(
            f"Failed to read CSV input: {path}"
        ) from exc


def file_exists(path: Path) -> bool:
    """Return whether the configured path exists as a regular file."""
    if not isinstance(path, Path):
        raise StorageError(
            "path must be a pathlib.Path instance."
        )

    return path.is_file()


def remove_file(path: Path) -> None:
    """Remove a file when it exists."""
    if not isinstance(path, Path):
        raise StorageError(
            "path must be a pathlib.Path instance."
        )

    try:
        path.unlink(
            missing_ok=True,
        )
    except OSError as exc:
        raise StorageError(
            f"Failed to remove file: {path}"
        ) from exc


__all__ = [
    "StorageError",
    "file_exists",
    "read_csv",
    "read_json",
    "read_parquet",
    "remove_file",
    "write_csv",
    "write_json",
    "write_parquet",
]