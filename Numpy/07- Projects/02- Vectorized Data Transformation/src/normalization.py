"""Normalization utilities for vectorized numerical transformations."""

from __future__ import annotations

import numpy as np

from .config import NORMALIZATION_MAX, NORMALIZATION_MIN


def min_max_normalize(
    values: np.ndarray,
    *,
    output_min: float = NORMALIZATION_MIN,
    output_max: float = NORMALIZATION_MAX,
) -> np.ndarray:
    """Scale values linearly into an inclusive output range."""
    if not np.isfinite(output_min) or not np.isfinite(output_max):
        raise ValueError("Normalization bounds must be finite.")

    if output_min >= output_max:
        raise ValueError(
            "output_min must be less than output_max."
        )

    values = np.asarray(
        values,
        dtype=np.float64,
    )

    if values.ndim == 0:
        raise ValueError("Expected an array with at least one dimension.")

    if values.size == 0:
        return values.copy()

    if not np.isfinite(values).all():
        raise ValueError(
            "Input contains NaN or infinite values."
        )

    source_min = values.min()
    source_max = values.max()
    source_range = source_max - source_min

    if source_range == 0.0:
        return np.full_like(
            values,
            output_min,
        )

    scaled = (
        (values - source_min)
        / source_range
    )

    return (
        scaled * (output_max - output_min)
        + output_min
    )


def standardize(
    values: np.ndarray,
    *,
    ddof: int = 0,
) -> np.ndarray:
    """Standardize values to zero mean and unit standard deviation."""
    if ddof < 0:
        raise ValueError("ddof must be non-negative.")

    values = np.asarray(
        values,
        dtype=np.float64,
    )

    if values.ndim == 0:
        raise ValueError("Expected an array with at least one dimension.")

    if values.size == 0:
        return values.copy()

    if not np.isfinite(values).all():
        raise ValueError(
            "Input contains NaN or infinite values."
        )

    mean = values.mean()
    standard_deviation = values.std(ddof=ddof)

    if standard_deviation == 0.0:
        return np.zeros_like(values)

    return (
        values - mean
    ) / standard_deviation


def normalize_by_max_abs(
    values: np.ndarray,
) -> np.ndarray:
    """Scale values by the largest absolute magnitude."""
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    if values.ndim == 0:
        raise ValueError("Expected an array with at least one dimension.")

    if values.size == 0:
        return values.copy()

    if not np.isfinite(values).all():
        raise ValueError(
            "Input contains NaN or infinite values."
        )

    scale = np.max(np.abs(values))

    if scale == 0.0:
        return np.zeros_like(values)

    return values / scale


def normalize_columns(
    values: np.ndarray,
    *,
    axis: int = 0,
) -> np.ndarray:
    """Apply min-max normalization independently along an array axis."""
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    if values.ndim < 2:
        raise ValueError(
            "normalize_columns requires a two-dimensional array."
        )

    if axis not in (0, 1):
        raise ValueError(
            "axis must be 0 or 1."
        )

    if values.shape[axis] == 0:
        return values.copy()

    if not np.isfinite(values).all():
        raise ValueError(
            "Input contains NaN or infinite values."
        )

    source_min = np.min(
        values,
        axis=axis,
        keepdims=True,
    )
    source_max = np.max(
        values,
        axis=axis,
        keepdims=True,
    )
    source_range = source_max - source_min

    safe_range = np.where(
        source_range == 0.0,
        1.0,
        source_range,
    )

    normalized = (
        values - source_min
    ) / safe_range

    return np.where(
        source_range == 0.0,
        0.0,
        normalized,
    )

"""Normalization utilities for vectorized numerical transformations."""

from __future__ import annotations

import numpy as np

from .config import NORMALIZATION_MAX, NORMALIZATION_MIN


def min_max_normalize(
    values: np.ndarray,
    *,
    output_min: float = NORMALIZATION_MIN,
    output_max: float = NORMALIZATION_MAX,
) -> np.ndarray:
    """Scale values linearly into an inclusive output range."""
    if not np.isfinite(output_min) or not np.isfinite(output_max):
        raise ValueError("Normalization bounds must be finite.")

    if output_min >= output_max:
        raise ValueError(
            "output_min must be less than output_max."
        )

    values = np.asarray(
        values,
        dtype=np.float64,
    )

    if values.ndim == 0:
        raise ValueError("Expected an array with at least one dimension.")

    if values.size == 0:
        return values.copy()

    if not np.isfinite(values).all():
        raise ValueError(
            "Input contains NaN or infinite values."
        )

    source_min = values.min()
    source_max = values.max()
    source_range = source_max - source_min

    if source_range == 0.0:
        return np.full_like(
            values,
            output_min,
        )

    scaled = (
        (values - source_min)
        / source_range
    )

    return (
        scaled * (output_max - output_min)
        + output_min
    )


def standardize(
    values: np.ndarray,
    *,
    ddof: int = 0,
) -> np.ndarray:
    """Standardize values to zero mean and unit standard deviation."""
    if ddof < 0:
        raise ValueError("ddof must be non-negative.")

    values = np.asarray(
        values,
        dtype=np.float64,
    )

    if values.ndim == 0:
        raise ValueError("Expected an array with at least one dimension.")

    if values.size == 0:
        return values.copy()

    if not np.isfinite(values).all():
        raise ValueError(
            "Input contains NaN or infinite values."
        )

    mean = values.mean()
    standard_deviation = values.std(ddof=ddof)

    if standard_deviation == 0.0:
        return np.zeros_like(values)

    return (
        values - mean
    ) / standard_deviation


def normalize_by_max_abs(
    values: np.ndarray,
) -> np.ndarray:
    """Scale values by the largest absolute magnitude."""
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    if values.ndim == 0:
        raise ValueError("Expected an array with at least one dimension.")

    if values.size == 0:
        return values.copy()

    if not np.isfinite(values).all():
        raise ValueError(
            "Input contains NaN or infinite values."
        )

    scale = np.max(np.abs(values))

    if scale == 0.0:
        return np.zeros_like(values)

    return values / scale


def normalize_columns(
    values: np.ndarray,
    *,
    axis: int = 0,
) -> np.ndarray:
    """Apply min-max normalization independently along an array axis."""
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    if values.ndim < 2:
        raise ValueError(
            "normalize_columns requires a two-dimensional array."
        )

    if axis not in (0, 1):
        raise ValueError(
            "axis must be 0 or 1."
        )

    if values.shape[axis] == 0:
        return values.copy()

    if not np.isfinite(values).all():
        raise ValueError(
            "Input contains NaN or infinite values."
        )

    source_min = np.min(
        values,
        axis=axis,
        keepdims=True,
    )
    source_max = np.max(
        values,
        axis=axis,
        keepdims=True,
    )
    source_range = source_max - source_min

    safe_range = np.where(
        source_range == 0.0,
        1.0,
        source_range,
    )

    normalized = (
        values - source_min
    ) / safe_range

    return np.where(
        source_range == 0.0,
        0.0,
        normalized,
    )