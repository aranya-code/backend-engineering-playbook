"""Numerical processing operations for the Numerical Data Processor."""

from __future__ import annotations

import numpy as np


def clean_values(
    values: np.ndarray,
    *,
    minimum: float = 0.0,
    maximum: float | None = None,
) -> np.ndarray:
    """Return a validated floating-point copy with optional value bounds."""
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    if values.ndim != 1:
        raise ValueError(
            f"Expected a one-dimensional array, got {values.shape}."
        )

    if not np.isfinite(values).all():
        raise ValueError(
            "Input contains NaN or infinite values."
        )

    if minimum > 0:
        values = np.maximum(values, minimum)

    if maximum is not None:
        if minimum > maximum:
            raise ValueError(
                "minimum must not exceed maximum."
            )

        values = np.minimum(values, maximum)

    return values


def normalize(
    values: np.ndarray,
) -> np.ndarray:
    """Normalize values to the range [0, 1]."""
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    if values.size == 0:
        return values.copy()

    minimum = values.min()
    maximum = values.max()
    span = maximum - minimum

    if span == 0.0:
        return np.zeros_like(values)

    return (values - minimum) / span


def aggregate(
    values: np.ndarray,
) -> dict[str, float]:
    """Calculate core numerical statistics for a one-dimensional array."""
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    if values.ndim != 1:
        raise ValueError(
            f"Expected a one-dimensional array, got {values.shape}."
        )

    if values.size == 0:
        raise ValueError("Cannot aggregate an empty array.")

    if not np.isfinite(values).all():
        raise ValueError(
            "Cannot aggregate non-finite values."
        )

    return {
        "count": float(values.size),
        "sum": float(values.sum()),
        "mean": float(values.mean()),
        "median": float(np.median(values)),
        "minimum": float(values.min()),
        "maximum": float(values.max()),
        "standard_deviation": float(values.std()),
    }


def process(
    values: np.ndarray,
    *,
    minimum: float = 0.0,
    maximum: float | None = None,
) -> tuple[np.ndarray, dict[str, float]]:
    """Clean, normalize, and aggregate a numerical dataset."""
    cleaned = clean_values(
        values,
        minimum=minimum,
        maximum=maximum,
    )

    normalized = normalize(cleaned)
    statistics = aggregate(cleaned)

    return normalized, statistics

"""Numerical processing operations for the Numerical Data Processor."""

from __future__ import annotations

import numpy as np


def clean_values(
    values: np.ndarray,
    *,
    minimum: float = 0.0,
    maximum: float | None = None,
) -> np.ndarray:
    """Return a validated floating-point copy with optional value bounds."""
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    if values.ndim != 1:
        raise ValueError(
            f"Expected a one-dimensional array, got {values.shape}."
        )

    if not np.isfinite(values).all():
        raise ValueError(
            "Input contains NaN or infinite values."
        )

    if minimum > 0:
        values = np.maximum(values, minimum)

    if maximum is not None:
        if minimum > maximum:
            raise ValueError(
                "minimum must not exceed maximum."
            )

        values = np.minimum(values, maximum)

    return values


def normalize(
    values: np.ndarray,
) -> np.ndarray:
    """Normalize values to the range [0, 1]."""
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    if values.size == 0:
        return values.copy()

    minimum = values.min()
    maximum = values.max()
    span = maximum - minimum

    if span == 0.0:
        return np.zeros_like(values)

    return (values - minimum) / span


def aggregate(
    values: np.ndarray,
) -> dict[str, float]:
    """Calculate core numerical statistics for a one-dimensional array."""
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    if values.ndim != 1:
        raise ValueError(
            f"Expected a one-dimensional array, got {values.shape}."
        )

    if values.size == 0:
        raise ValueError("Cannot aggregate an empty array.")

    if not np.isfinite(values).all():
        raise ValueError(
            "Cannot aggregate non-finite values."
        )

    return {
        "count": float(values.size),
        "sum": float(values.sum()),
        "mean": float(values.mean()),
        "median": float(np.median(values)),
        "minimum": float(values.min()),
        "maximum": float(values.max()),
        "standard_deviation": float(values.std()),
    }


def process(
    values: np.ndarray,
    *,
    minimum: float = 0.0,
    maximum: float | None = None,
) -> tuple[np.ndarray, dict[str, float]]:
    """Clean, normalize, and aggregate a numerical dataset."""
    cleaned = clean_values(
        values,
        minimum=minimum,
        maximum=maximum,
    )

    normalized = normalize(cleaned)
    statistics = aggregate(cleaned)

    return normalized, statistics