"""Input loading utilities for the Numerical Data Processor."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .config import DEFAULT_DTYPE, MAX_ELEMENTS


def load_array(
    path: str | Path,
    *,
    dtype: str = DEFAULT_DTYPE,
    max_elements: int = MAX_ELEMENTS,
) -> np.ndarray:
    """Load a NumPy-compatible array from a .npy file with basic validation."""
    input_path = Path(path)

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

"""Input loading utilities for the Numerical Data Processor."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .config import DEFAULT_DTYPE, MAX_ELEMENTS


def load_array(
    path: str | Path,
    *,
    dtype: str = DEFAULT_DTYPE,
    max_elements: int = MAX_ELEMENTS,
) -> np.ndarray:
    """Load a NumPy-compatible array from a .npy file with basic validation."""
    input_path = Path(path)

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