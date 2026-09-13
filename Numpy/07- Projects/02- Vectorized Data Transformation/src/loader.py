"""Input loading utilities for the Vectorized Data Transformation pipeline."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .config import (
    DEFAULT_DTYPE,
    DEFAULT_INPUT_FILENAME,
    INPUT_DIR,
    MAX_ELEMENTS,
)


def load_array(
    path: str | Path | None = None,
    *,
    dtype: str = DEFAULT_DTYPE,
    max_elements: int = MAX_ELEMENTS,
) -> np.ndarray:
    """Load a NumPy array from a .npy file with resource validation."""
    input_path = (
        Path(path)
        if path is not None
        else INPUT_DIR / DEFAULT_INPUT_FILENAME
    )

    if not input_path.is_file():
        raise FileNotFoundError(
            f"Input file does not exist: {input_path}"
        )

    if input_path.suffix.lower() != ".npy":
        raise ValueError(
            f"Unsupported input format: {input_path.suffix}"
        )

    values = np.load(
        input_path,
        allow_pickle=False,
    )

    values = np.asarray(
        values,
        dtype=dtype,
    )

    if values.size > max_elements:
        raise ValueError(
            f"Input contains {values.size:,} elements; "
            f"maximum allowed is {max_elements:,}."
        )

    return values


def load_batches(
    path: str | Path | None = None,
    *,
    batch_size: int,
    dtype: str = DEFAULT_DTYPE,
    max_elements: int = MAX_ELEMENTS,
):
    """Yield bounded batches from a loaded one-dimensional NumPy array."""
    if batch_size <= 0:
        raise ValueError("batch_size must be positive.")

    values = load_array(
        path,
        dtype=dtype,
        max_elements=max_elements,
    )

    if values.ndim != 1:
        raise ValueError(
            f"Expected a one-dimensional array, got {values.shape}."
        )

    for start in range(0, values.size, batch_size):
        yield values[start:start + batch_size]

"""Input loading utilities for the Vectorized Data Transformation pipeline."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .config import (
    DEFAULT_DTYPE,
    DEFAULT_INPUT_FILENAME,
    INPUT_DIR,
    MAX_ELEMENTS,
)


def load_array(
    path: str | Path | None = None,
    *,
    dtype: str = DEFAULT_DTYPE,
    max_elements: int = MAX_ELEMENTS,
) -> np.ndarray:
    """Load a NumPy array from a .npy file with resource validation."""
    input_path = (
        Path(path)
        if path is not None
        else INPUT_DIR / DEFAULT_INPUT_FILENAME
    )

    if not input_path.is_file():
        raise FileNotFoundError(
            f"Input file does not exist: {input_path}"
        )

    if input_path.suffix.lower() != ".npy":
        raise ValueError(
            f"Unsupported input format: {input_path.suffix}"
        )

    values = np.load(
        input_path,
        allow_pickle=False,
    )

    values = np.asarray(
        values,
        dtype=dtype,
    )

    if values.size > max_elements:
        raise ValueError(
            f"Input contains {values.size:,} elements; "
            f"maximum allowed is {max_elements:,}."
        )

    return values


def load_batches(
    path: str | Path | None = None,
    *,
    batch_size: int,
    dtype: str = DEFAULT_DTYPE,
    max_elements: int = MAX_ELEMENTS,
):
    """Yield bounded batches from a loaded one-dimensional NumPy array."""
    if batch_size <= 0:
        raise ValueError("batch_size must be positive.")

    values = load_array(
        path,
        dtype=dtype,
        max_elements=max_elements,
    )

    if values.ndim != 1:
        raise ValueError(
            f"Expected a one-dimensional array, got {values.shape}."
        )

    for start in range(0, values.size, batch_size):
        yield values[start:start + batch_size]