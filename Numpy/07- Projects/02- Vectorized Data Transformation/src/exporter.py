"""Array export utilities for the vectorized data transformation pipeline."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .config import DEFAULT_OUTPUT_FILENAME, OUTPUT_DIR


def save_array(
    values: np.ndarray,
    path: str | Path | None = None,
    *,
    allow_overwrite: bool = False,
) -> Path:
    """Persist a NumPy array as a .npy file."""
    values = np.asarray(values)

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected a numeric array, got {values.dtype}."
        )

    output_path = (
        Path(path)
        if path is not None
        else OUTPUT_DIR / DEFAULT_OUTPUT_FILENAME
    )

    if output_path.suffix.lower() != ".npy":
        raise ValueError(
            f"Unsupported output format: {output_path.suffix}"
        )

    if output_path.exists() and not allow_overwrite:
        raise FileExistsError(
            f"Output file already exists: {output_path}"
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    np.save(
        output_path,
        values,
        allow_pickle=False,
    )

    return output_path


def save_csv(
    values: np.ndarray,
    path: str | Path,
    *,
    delimiter: str = ",",
    header: str | None = None,
    fmt: str = "%.18g",
    allow_overwrite: bool = False,
) -> Path:
    """Persist a one- or two-dimensional numerical array as CSV."""
    values = np.asarray(values)

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected a numeric array, got {values.dtype}."
        )

    if values.ndim not in (1, 2):
        raise ValueError(
            "CSV export supports only one- or two-dimensional arrays."
        )

    if not delimiter:
        raise ValueError("delimiter must not be empty.")

    output_path = Path(path)

    if output_path.suffix.lower() != ".csv":
        raise ValueError(
            f"Unsupported output format: {output_path.suffix}"
        )

    if output_path.exists() and not allow_overwrite:
        raise FileExistsError(
            f"Output file already exists: {output_path}"
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    np.savetxt(
        output_path,
        values,
        delimiter=delimiter,
        header=header or "",
        comments="",
        fmt=fmt,
    )

    return output_path


def save_text(
    values: np.ndarray,
    path: str | Path,
    *,
    delimiter: str = " ",
    fmt: str = "%.18g",
    allow_overwrite: bool = False,
) -> Path:
    """Persist a one- or two-dimensional numerical array as text."""
    values = np.asarray(values)

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected a numeric array, got {values.dtype}."
        )

    if values.ndim not in (1, 2):
        raise ValueError(
            "Text export supports only one- or two-dimensional arrays."
        )

    if not delimiter:
        raise ValueError("delimiter must not be empty.")

    output_path = Path(path)

    if output_path.exists() and not allow_overwrite:
        raise FileExistsError(
            f"Output file already exists: {output_path}"
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    np.savetxt(
        output_path,
        values,
        delimiter=delimiter,
        fmt=fmt,
    )

    return output_path


def export_array(
    values: np.ndarray,
    path: str | Path,
    *,
    allow_overwrite: bool = False,
) -> Path:
    """Export an array using the format implied by the file extension."""
    output_path = Path(path)
    suffix = output_path.suffix.lower()

    if suffix == ".npy":
        return save_array(
            values,
            output_path,
            allow_overwrite=allow_overwrite,
        )

    if suffix == ".csv":
        return save_csv(
            values,
            output_path,
            allow_overwrite=allow_overwrite,
        )

    if suffix in {".txt", ".dat"}:
        return save_text(
            values,
            output_path,
            allow_overwrite=allow_overwrite,
        )

    raise ValueError(
        f"Unsupported output format: {output_path.suffix}"
    )


def array_metadata(values: np.ndarray) -> dict[str, object]:
    """Return operational metadata useful for export validation and logging."""
    values = np.asarray(values)

    return {
        "shape": values.shape,
        "dtype": str(values.dtype),
        "ndim": values.ndim,
        "size": int(values.size),
        "itemsize": values.itemsize,
        "nbytes": int(values.nbytes),
        "c_contiguous": bool(values.flags.c_contiguous),
        "f_contiguous": bool(values.flags.f_contiguous),
    }

"""Array export utilities for the vectorized data transformation pipeline."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .config import DEFAULT_OUTPUT_FILENAME, OUTPUT_DIR


def save_array(
    values: np.ndarray,
    path: str | Path | None = None,
    *,
    allow_overwrite: bool = False,
) -> Path:
    """Persist a NumPy array as a .npy file."""
    values = np.asarray(values)

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected a numeric array, got {values.dtype}."
        )

    output_path = (
        Path(path)
        if path is not None
        else OUTPUT_DIR / DEFAULT_OUTPUT_FILENAME
    )

    if output_path.suffix.lower() != ".npy":
        raise ValueError(
            f"Unsupported output format: {output_path.suffix}"
        )

    if output_path.exists() and not allow_overwrite:
        raise FileExistsError(
            f"Output file already exists: {output_path}"
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    np.save(
        output_path,
        values,
        allow_pickle=False,
    )

    return output_path


def save_csv(
    values: np.ndarray,
    path: str | Path,
    *,
    delimiter: str = ",",
    header: str | None = None,
    fmt: str = "%.18g",
    allow_overwrite: bool = False,
) -> Path:
    """Persist a one- or two-dimensional numerical array as CSV."""
    values = np.asarray(values)

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected a numeric array, got {values.dtype}."
        )

    if values.ndim not in (1, 2):
        raise ValueError(
            "CSV export supports only one- or two-dimensional arrays."
        )

    if not delimiter:
        raise ValueError("delimiter must not be empty.")

    output_path = Path(path)

    if output_path.suffix.lower() != ".csv":
        raise ValueError(
            f"Unsupported output format: {output_path.suffix}"
        )

    if output_path.exists() and not allow_overwrite:
        raise FileExistsError(
            f"Output file already exists: {output_path}"
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    np.savetxt(
        output_path,
        values,
        delimiter=delimiter,
        header=header or "",
        comments="",
        fmt=fmt,
    )

    return output_path


def save_text(
    values: np.ndarray,
    path: str | Path,
    *,
    delimiter: str = " ",
    fmt: str = "%.18g",
    allow_overwrite: bool = False,
) -> Path:
    """Persist a one- or two-dimensional numerical array as text."""
    values = np.asarray(values)

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected a numeric array, got {values.dtype}."
        )

    if values.ndim not in (1, 2):
        raise ValueError(
            "Text export supports only one- or two-dimensional arrays."
        )

    if not delimiter:
        raise ValueError("delimiter must not be empty.")

    output_path = Path(path)

    if output_path.exists() and not allow_overwrite:
        raise FileExistsError(
            f"Output file already exists: {output_path}"
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    np.savetxt(
        output_path,
        values,
        delimiter=delimiter,
        fmt=fmt,
    )

    return output_path


def export_array(
    values: np.ndarray,
    path: str | Path,
    *,
    allow_overwrite: bool = False,
) -> Path:
    """Export an array using the format implied by the file extension."""
    output_path = Path(path)
    suffix = output_path.suffix.lower()

    if suffix == ".npy":
        return save_array(
            values,
            output_path,
            allow_overwrite=allow_overwrite,
        )

    if suffix == ".csv":
        return save_csv(
            values,
            output_path,
            allow_overwrite=allow_overwrite,
        )

    if suffix in {".txt", ".dat"}:
        return save_text(
            values,
            output_path,
            allow_overwrite=allow_overwrite,
        )

    raise ValueError(
        f"Unsupported output format: {output_path.suffix}"
    )


def array_metadata(values: np.ndarray) -> dict[str, object]:
    """Return operational metadata useful for export validation and logging."""
    values = np.asarray(values)

    return {
        "shape": values.shape,
        "dtype": str(values.dtype),
        "ndim": values.ndim,
        "size": int(values.size),
        "itemsize": values.itemsize,
        "nbytes": int(values.nbytes),
        "c_contiguous": bool(values.flags.c_contiguous),
        "f_contiguous": bool(values.flags.f_contiguous),
    }