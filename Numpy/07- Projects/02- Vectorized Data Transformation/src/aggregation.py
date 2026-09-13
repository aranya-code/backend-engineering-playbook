"""Aggregation utilities for vectorized numerical processing."""

from __future__ import annotations

import numpy as np


def sum_values(
    values: np.ndarray,
    *,
    axis: int | tuple[int, ...] | None = None,
    dtype: np.dtype | type | None = None,
) -> np.ndarray | np.generic:
    """Return the sum of array elements along the requested axis."""
    values = np.asarray(values)

    if values.size == 0:
        return np.sum(
            values,
            axis=axis,
            dtype=dtype,
        )

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected a numeric array, got {values.dtype}."
        )

    return np.sum(
        values,
        axis=axis,
        dtype=dtype,
    )


def mean_values(
    values: np.ndarray,
    *,
    axis: int | tuple[int, ...] | None = None,
) -> np.ndarray | np.generic:
    """Return the arithmetic mean of array elements."""
    values = np.asarray(values)

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected a numeric array, got {values.dtype}."
        )

    if values.size == 0:
        raise ValueError("Cannot calculate the mean of an empty array.")

    return np.mean(
        values,
        axis=axis,
    )


def min_value(
    values: np.ndarray,
    *,
    axis: int | tuple[int, ...] | None = None,
) -> np.ndarray | np.generic:
    """Return the minimum value along the requested axis."""
    values = np.asarray(values)

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected a numeric array, got {values.dtype}."
        )

    if values.size == 0:
        raise ValueError("Cannot calculate the minimum of an empty array.")

    return np.min(
        values,
        axis=axis,
    )


def max_value(
    values: np.ndarray,
    *,
    axis: int | tuple[int, ...] | None = None,
) -> np.ndarray | np.generic:
    """Return the maximum value along the requested axis."""
    values = np.asarray(values)

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected a numeric array, got {values.dtype}."
        )

    if values.size == 0:
        raise ValueError("Cannot calculate the maximum of an empty array.")

    return np.max(
        values,
        axis=axis,
    )


def median_value(
    values: np.ndarray,
    *,
    axis: int | tuple[int, ...] | None = None,
) -> np.ndarray | np.generic:
    """Return the median value along the requested axis."""
    values = np.asarray(values)

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected a numeric array, got {values.dtype}."
        )

    if values.size == 0:
        raise ValueError("Cannot calculate the median of an empty array.")

    return np.median(
        values,
        axis=axis,
    )


def percentile_value(
    values: np.ndarray,
    percentile: float,
    *,
    axis: int | tuple[int, ...] | None = None,
) -> np.ndarray | np.generic:
    """Return a requested percentile along the requested axis."""
    if not np.isfinite(percentile):
        raise ValueError("percentile must be finite.")

    if not 0.0 <= percentile <= 100.0:
        raise ValueError(
            "percentile must be between 0 and 100."
        )

    values = np.asarray(values)

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected a numeric array, got {values.dtype}."
        )

    if values.size == 0:
        raise ValueError(
            "Cannot calculate a percentile of an empty array."
        )

    return np.percentile(
        values,
        percentile,
        axis=axis,
    )


def nanmean_values(
    values: np.ndarray,
    *,
    axis: int | tuple[int, ...] | None = None,
) -> np.ndarray | np.generic:
    """Return the mean while ignoring NaN values."""
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    if values.size == 0:
        raise ValueError(
            "Cannot calculate the mean of an empty array."
        )

    return np.nanmean(
        values,
        axis=axis,
    )


def finite_statistics(
    values: np.ndarray,
) -> dict[str, float | int]:
    """Return common aggregate statistics over finite values only."""
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    finite = values[np.isfinite(values)]

    if finite.size == 0:
        raise ValueError(
            "Input does not contain finite numerical values."
        )

    return {
        "count": int(finite.size),
        "sum": float(np.sum(finite)),
        "mean": float(np.mean(finite)),
        "minimum": float(np.min(finite)),
        "maximum": float(np.max(finite)),
        "median": float(np.median(finite)),
        "standard_deviation": float(np.std(finite)),
    }

"""Aggregation utilities for vectorized numerical processing."""

from __future__ import annotations

import numpy as np


def sum_values(
    values: np.ndarray,
    *,
    axis: int | tuple[int, ...] | None = None,
    dtype: np.dtype | type | None = None,
) -> np.ndarray | np.generic:
    """Return the sum of array elements along the requested axis."""
    values = np.asarray(values)

    if values.size == 0:
        return np.sum(
            values,
            axis=axis,
            dtype=dtype,
        )

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected a numeric array, got {values.dtype}."
        )

    return np.sum(
        values,
        axis=axis,
        dtype=dtype,
    )


def mean_values(
    values: np.ndarray,
    *,
    axis: int | tuple[int, ...] | None = None,
) -> np.ndarray | np.generic:
    """Return the arithmetic mean of array elements."""
    values = np.asarray(values)

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected a numeric array, got {values.dtype}."
        )

    if values.size == 0:
        raise ValueError("Cannot calculate the mean of an empty array.")

    return np.mean(
        values,
        axis=axis,
    )


def min_value(
    values: np.ndarray,
    *,
    axis: int | tuple[int, ...] | None = None,
) -> np.ndarray | np.generic:
    """Return the minimum value along the requested axis."""
    values = np.asarray(values)

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected a numeric array, got {values.dtype}."
        )

    if values.size == 0:
        raise ValueError("Cannot calculate the minimum of an empty array.")

    return np.min(
        values,
        axis=axis,
    )


def max_value(
    values: np.ndarray,
    *,
    axis: int | tuple[int, ...] | None = None,
) -> np.ndarray | np.generic:
    """Return the maximum value along the requested axis."""
    values = np.asarray(values)

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected a numeric array, got {values.dtype}."
        )

    if values.size == 0:
        raise ValueError("Cannot calculate the maximum of an empty array.")

    return np.max(
        values,
        axis=axis,
    )


def median_value(
    values: np.ndarray,
    *,
    axis: int | tuple[int, ...] | None = None,
) -> np.ndarray | np.generic:
    """Return the median value along the requested axis."""
    values = np.asarray(values)

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected a numeric array, got {values.dtype}."
        )

    if values.size == 0:
        raise ValueError("Cannot calculate the median of an empty array.")

    return np.median(
        values,
        axis=axis,
    )


def percentile_value(
    values: np.ndarray,
    percentile: float,
    *,
    axis: int | tuple[int, ...] | None = None,
) -> np.ndarray | np.generic:
    """Return a requested percentile along the requested axis."""
    if not np.isfinite(percentile):
        raise ValueError("percentile must be finite.")

    if not 0.0 <= percentile <= 100.0:
        raise ValueError(
            "percentile must be between 0 and 100."
        )

    values = np.asarray(values)

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected a numeric array, got {values.dtype}."
        )

    if values.size == 0:
        raise ValueError(
            "Cannot calculate a percentile of an empty array."
        )

    return np.percentile(
        values,
        percentile,
        axis=axis,
    )


def nanmean_values(
    values: np.ndarray,
    *,
    axis: int | tuple[int, ...] | None = None,
) -> np.ndarray | np.generic:
    """Return the mean while ignoring NaN values."""
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    if values.size == 0:
        raise ValueError(
            "Cannot calculate the mean of an empty array."
        )

    return np.nanmean(
        values,
        axis=axis,
    )


def finite_statistics(
    values: np.ndarray,
) -> dict[str, float | int]:
    """Return common aggregate statistics over finite values only."""
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    finite = values[np.isfinite(values)]

    if finite.size == 0:
        raise ValueError(
            "Input does not contain finite numerical values."
        )

    return {
        "count": int(finite.size),
        "sum": float(np.sum(finite)),
        "mean": float(np.mean(finite)),
        "minimum": float(np.min(finite)),
        "maximum": float(np.max(finite)),
        "median": float(np.median(finite)),
        "standard_deviation": float(np.std(finite)),
    }