"""Synthetic dataset generation utilities for performance benchmarks."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np


DEFAULT_SEED = 42


def generate_uniform(
    size: int,
    *,
    low: float = 0.0,
    high: float = 1.0,
    dtype: np.dtype | type = np.float64,
    seed: int = DEFAULT_SEED,
) -> np.ndarray:
    """Generate reproducible uniformly distributed numerical data."""
    _validate_size(size)

    if not np.isfinite(low) or not np.isfinite(high):
        raise ValueError("low and high must be finite.")

    if low >= high:
        raise ValueError("low must be less than high.")

    rng = np.random.default_rng(seed)

    return rng.uniform(
        low,
        high,
        size=size,
    ).astype(
        dtype,
        copy=False,
    )


def generate_normal(
    size: int,
    *,
    mean: float = 0.0,
    standard_deviation: float = 1.0,
    dtype: np.dtype | type = np.float64,
    seed: int = DEFAULT_SEED,
) -> np.ndarray:
    """Generate reproducible normally distributed numerical data."""
    _validate_size(size)

    if not np.isfinite(mean):
        raise ValueError("mean must be finite.")

    if not np.isfinite(standard_deviation):
        raise ValueError(
            "standard_deviation must be finite."
        )

    if standard_deviation <= 0.0:
        raise ValueError(
            "standard_deviation must be positive."
        )

    rng = np.random.default_rng(seed)

    return rng.normal(
        loc=mean,
        scale=standard_deviation,
        size=size,
    ).astype(
        dtype,
        copy=False,
    )


def generate_integers(
    size: int,
    *,
    low: int = 0,
    high: int = 1_000,
    dtype: np.dtype | type = np.int64,
    seed: int = DEFAULT_SEED,
) -> np.ndarray:
    """Generate reproducible bounded integer benchmark data."""
    _validate_size(size)

    if low >= high:
        raise ValueError(
            "low must be less than high."
        )

    rng = np.random.default_rng(seed)

    return rng.integers(
        low,
        high,
        size=size,
        dtype=dtype,
    )


def generate_benchmark_sizes(
    sizes: Sequence[int],
) -> list[int]:
    """Validate and normalize a collection of benchmark dataset sizes."""
    if not sizes:
        raise ValueError("sizes must not be empty.")

    normalized = [
        int(size)
        for size in sizes
    ]

    for size in normalized:
        _validate_size(size)

    if normalized != sorted(set(normalized)):
        raise ValueError(
            "sizes must contain unique values in ascending order."
        )

    return normalized


def generate_matrix(
    rows: int,
    columns: int,
    *,
    low: float = 0.0,
    high: float = 1.0,
    dtype: np.dtype | type = np.float64,
    seed: int = DEFAULT_SEED,
) -> np.ndarray:
    """Generate a reproducible two-dimensional benchmark matrix."""
    _validate_size(rows)
    _validate_size(columns)

    if not np.isfinite(low) or not np.isfinite(high):
        raise ValueError("low and high must be finite.")

    if low >= high:
        raise ValueError(
            "low must be less than high."
        )

    rng = np.random.default_rng(seed)

    return rng.uniform(
        low,
        high,
        size=(rows, columns),
    ).astype(
        dtype,
        copy=False,
    )


def dataset_metadata(values: np.ndarray) -> dict[str, object]:
    """Return metadata required to describe a benchmark dataset."""
    values = np.asarray(values)

    return {
        "shape": values.shape,
        "dtype": str(values.dtype),
        "size": int(values.size),
        "itemsize": int(values.itemsize),
        "nbytes": int(values.nbytes),
        "c_contiguous": bool(values.flags.c_contiguous),
        "f_contiguous": bool(values.flags.f_contiguous),
    }


def _validate_size(size: int) -> None:
    """Validate that a dataset dimension is a positive integer."""
    if not isinstance(size, (int, np.integer)):
        raise TypeError("size must be an integer.")

    if size <= 0:
        raise ValueError("size must be positive.")

"""Synthetic dataset generation utilities for performance benchmarks."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np


DEFAULT_SEED = 42


def generate_uniform(
    size: int,
    *,
    low: float = 0.0,
    high: float = 1.0,
    dtype: np.dtype | type = np.float64,
    seed: int = DEFAULT_SEED,
) -> np.ndarray:
    """Generate reproducible uniformly distributed numerical data."""
    _validate_size(size)

    if not np.isfinite(low) or not np.isfinite(high):
        raise ValueError("low and high must be finite.")

    if low >= high:
        raise ValueError("low must be less than high.")

    rng = np.random.default_rng(seed)

    return rng.uniform(
        low,
        high,
        size=size,
    ).astype(
        dtype,
        copy=False,
    )


def generate_normal(
    size: int,
    *,
    mean: float = 0.0,
    standard_deviation: float = 1.0,
    dtype: np.dtype | type = np.float64,
    seed: int = DEFAULT_SEED,
) -> np.ndarray:
    """Generate reproducible normally distributed numerical data."""
    _validate_size(size)

    if not np.isfinite(mean):
        raise ValueError("mean must be finite.")

    if not np.isfinite(standard_deviation):
        raise ValueError(
            "standard_deviation must be finite."
        )

    if standard_deviation <= 0.0:
        raise ValueError(
            "standard_deviation must be positive."
        )

    rng = np.random.default_rng(seed)

    return rng.normal(
        loc=mean,
        scale=standard_deviation,
        size=size,
    ).astype(
        dtype,
        copy=False,
    )


def generate_integers(
    size: int,
    *,
    low: int = 0,
    high: int = 1_000,
    dtype: np.dtype | type = np.int64,
    seed: int = DEFAULT_SEED,
) -> np.ndarray:
    """Generate reproducible bounded integer benchmark data."""
    _validate_size(size)

    if low >= high:
        raise ValueError(
            "low must be less than high."
        )

    rng = np.random.default_rng(seed)

    return rng.integers(
        low,
        high,
        size=size,
        dtype=dtype,
    )


def generate_benchmark_sizes(
    sizes: Sequence[int],
) -> list[int]:
    """Validate and normalize a collection of benchmark dataset sizes."""
    if not sizes:
        raise ValueError("sizes must not be empty.")

    normalized = [
        int(size)
        for size in sizes
    ]

    for size in normalized:
        _validate_size(size)

    if normalized != sorted(set(normalized)):
        raise ValueError(
            "sizes must contain unique values in ascending order."
        )

    return normalized


def generate_matrix(
    rows: int,
    columns: int,
    *,
    low: float = 0.0,
    high: float = 1.0,
    dtype: np.dtype | type = np.float64,
    seed: int = DEFAULT_SEED,
) -> np.ndarray:
    """Generate a reproducible two-dimensional benchmark matrix."""
    _validate_size(rows)
    _validate_size(columns)

    if not np.isfinite(low) or not np.isfinite(high):
        raise ValueError("low and high must be finite.")

    if low >= high:
        raise ValueError(
            "low must be less than high."
        )

    rng = np.random.default_rng(seed)

    return rng.uniform(
        low,
        high,
        size=(rows, columns),
    ).astype(
        dtype,
        copy=False,
    )


def dataset_metadata(values: np.ndarray) -> dict[str, object]:
    """Return metadata required to describe a benchmark dataset."""
    values = np.asarray(values)

    return {
        "shape": values.shape,
        "dtype": str(values.dtype),
        "size": int(values.size),
        "itemsize": int(values.itemsize),
        "nbytes": int(values.nbytes),
        "c_contiguous": bool(values.flags.c_contiguous),
        "f_contiguous": bool(values.flags.f_contiguous),
    }


def _validate_size(size: int) -> None:
    """Validate that a dataset dimension is a positive integer."""
    if not isinstance(size, (int, np.integer)):
        raise TypeError("size must be an integer.")

    if size <= 0:
        raise ValueError("size must be positive.")