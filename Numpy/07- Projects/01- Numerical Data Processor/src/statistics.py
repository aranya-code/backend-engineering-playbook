"""Statistical calculations for the Numerical Data Processor."""

from __future__ import annotations

import numpy as np


def _prepare(values: np.ndarray) -> np.ndarray:
    """Validate and normalize numerical input for statistical operations."""
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    if values.ndim != 1:
        raise ValueError(
            f"Expected a one-dimensional array, got {values.shape}."
        )

    if values.size == 0:
        raise ValueError(
            "Cannot calculate statistics for an empty array."
        )

    if not np.isfinite(values).all():
        raise ValueError(
            "Statistics require finite numerical values."
        )

    return values


def mean(values: np.ndarray) -> float:
    """Return the arithmetic mean."""
    return float(_prepare(values).mean())


def median(values: np.ndarray) -> float:
    """Return the median."""
    return float(np.median(_prepare(values)))


def minimum(values: np.ndarray) -> float:
    """Return the minimum value."""
    return float(_prepare(values).min())


def maximum(values: np.ndarray) -> float:
    """Return the maximum value."""
    return float(_prepare(values).max())


def standard_deviation(values: np.ndarray) -> float:
    """Return the population standard deviation."""
    return float(_prepare(values).std())


def variance(values: np.ndarray) -> float:
    """Return the population variance."""
    return float(_prepare(values).var())


def percentiles(
    values: np.ndarray,
    percentages: tuple[float, ...] = (25.0, 50.0, 75.0),
) -> dict[float, float]:
    """Return selected percentiles as a percentage-to-value mapping."""
    values = _prepare(values)

    if not percentages:
        return {}

    if any(
        percentage < 0.0 or percentage > 100.0
        for percentage in percentages
    ):
        raise ValueError(
            "Percentages must be between 0 and 100."
        )

    result = np.percentile(
        values,
        percentages,
    )

    return {
        percentage: float(value)
        for percentage, value in zip(
            percentages,
            np.atleast_1d(result),
        )
    }


def describe(values: np.ndarray) -> dict[str, float]:
    """Return the core descriptive statistics for a numerical dataset."""
    values = _prepare(values)

    return {
        "count": float(values.size),
        "mean": float(values.mean()),
        "median": float(np.median(values)),
        "minimum": float(values.min()),
        "maximum": float(values.max()),
        "standard_deviation": float(values.std()),
        "variance": float(values.var()),
        "p25": float(np.percentile(values, 25)),
        "p75": float(np.percentile(values, 75)),
    }

"""Statistical calculations for the Numerical Data Processor."""

from __future__ import annotations

import numpy as np


def _prepare(values: np.ndarray) -> np.ndarray:
    """Validate and normalize numerical input for statistical operations."""
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    if values.ndim != 1:
        raise ValueError(
            f"Expected a one-dimensional array, got {values.shape}."
        )

    if values.size == 0:
        raise ValueError(
            "Cannot calculate statistics for an empty array."
        )

    if not np.isfinite(values).all():
        raise ValueError(
            "Statistics require finite numerical values."
        )

    return values


def mean(values: np.ndarray) -> float:
    """Return the arithmetic mean."""
    return float(_prepare(values).mean())


def median(values: np.ndarray) -> float:
    """Return the median."""
    return float(np.median(_prepare(values)))


def minimum(values: np.ndarray) -> float:
    """Return the minimum value."""
    return float(_prepare(values).min())


def maximum(values: np.ndarray) -> float:
    """Return the maximum value."""
    return float(_prepare(values).max())


def standard_deviation(values: np.ndarray) -> float:
    """Return the population standard deviation."""
    return float(_prepare(values).std())


def variance(values: np.ndarray) -> float:
    """Return the population variance."""
    return float(_prepare(values).var())


def percentiles(
    values: np.ndarray,
    percentages: tuple[float, ...] = (25.0, 50.0, 75.0),
) -> dict[float, float]:
    """Return selected percentiles as a percentage-to-value mapping."""
    values = _prepare(values)

    if not percentages:
        return {}

    if any(
        percentage < 0.0 or percentage > 100.0
        for percentage in percentages
    ):
        raise ValueError(
            "Percentages must be between 0 and 100."
        )

    result = np.percentile(
        values,
        percentages,
    )

    return {
        percentage: float(value)
        for percentage, value in zip(
            percentages,
            np.atleast_1d(result),
        )
    }


def describe(values: np.ndarray) -> dict[str, float]:
    """Return the core descriptive statistics for a numerical dataset."""
    values = _prepare(values)

    return {
        "count": float(values.size),
        "mean": float(values.mean()),
        "median": float(np.median(values)),
        "minimum": float(values.min()),
        "maximum": float(values.max()),
        "standard_deviation": float(values.std()),
        "variance": float(values.var()),
        "p25": float(np.percentile(values, 25)),
        "p75": float(np.percentile(values, 75)),
    }