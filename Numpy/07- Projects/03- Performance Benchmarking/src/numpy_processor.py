"""NumPy-based numerical processing implementations for performance benchmarks."""

from __future__ import annotations

import numpy as np


def scale_and_offset(
    values: np.ndarray,
    *,
    factor: float = 1.0,
    offset: float = 0.0,
) -> np.ndarray:
    """Apply scaling and offset using vectorized NumPy operations."""
    values = np.asarray(values)

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected a numeric array, got {values.dtype}."
        )

    if not np.isfinite(factor):
        raise ValueError("factor must be finite.")

    if not np.isfinite(offset):
        raise ValueError("offset must be finite.")

    return values * factor + offset


def clip(
    values: np.ndarray,
    *,
    minimum: float,
    maximum: float,
) -> np.ndarray:
    """Clip values to an inclusive range using NumPy."""
    if not np.isfinite(minimum):
        raise ValueError("minimum must be finite.")

    if not np.isfinite(maximum):
        raise ValueError("maximum must be finite.")

    if minimum > maximum:
        raise ValueError(
            "minimum must not exceed maximum."
        )

    values = np.asarray(values)

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected a numeric array, got {values.dtype}."
        )

    return np.clip(
        values,
        minimum,
        maximum,
    )


def scale_offset_and_clip(
    values: np.ndarray,
    *,
    factor: float = 1.0,
    offset: float = 0.0,
    minimum: float = 0.0,
    maximum: float = 1_000_000.0,
) -> np.ndarray:
    """Apply scaling, offset, and clipping with vectorized operations."""
    if not np.isfinite(factor):
        raise ValueError("factor must be finite.")

    if not np.isfinite(offset):
        raise ValueError("offset must be finite.")

    if not np.isfinite(minimum):
        raise ValueError("minimum must be finite.")

    if not np.isfinite(maximum):
        raise ValueError("maximum must be finite.")

    if minimum > maximum:
        raise ValueError(
            "minimum must not exceed maximum."
        )

    values = np.asarray(values)

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected a numeric array, got {values.dtype}."
        )

    transformed = values * factor + offset

    return np.clip(
        transformed,
        minimum,
        maximum,
    )


def sum_values(
    values: np.ndarray,
    *,
    axis: int | tuple[int, ...] | None = None,
) -> np.ndarray | np.generic:
    """Calculate an array sum with NumPy's vectorized reduction."""
    values = np.asarray(values)

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected a numeric array, got {values.dtype}."
        )

    return np.sum(
        values,
        axis=axis,
    )


def mean_values(
    values: np.ndarray,
    *,
    axis: int | tuple[int, ...] | None = None,
) -> np.ndarray | np.generic:
    """Calculate an arithmetic mean using NumPy."""
    values = np.asarray(values)

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected a numeric array, got {values.dtype}."
        )

    if values.size == 0:
        raise ValueError(
            "Cannot calculate the mean of an empty array."
        )

    return np.mean(
        values,
        axis=axis,
    )


def filter_range(
    values: np.ndarray,
    *,
    minimum: float,
    maximum: float,
) -> np.ndarray:
    """Filter values inside an inclusive range using Boolean masking."""
    if not np.isfinite(minimum):
        raise ValueError("minimum must be finite.")

    if not np.isfinite(maximum):
        raise ValueError("maximum must be finite.")

    if minimum > maximum:
        raise ValueError(
            "minimum must not exceed maximum."
        )

    values = np.asarray(values)

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected a numeric array, got {values.dtype}."
        )

    mask = (
        (values >= minimum)
        & (values <= maximum)
    )

    return values[mask]


def normalize(
    values: np.ndarray,
    *,
    output_min: float = 0.0,
    output_max: float = 1.0,
) -> np.ndarray:
    """Apply min-max normalization using vectorized operations."""
    if not np.isfinite(output_min):
        raise ValueError("output_min must be finite.")

    if not np.isfinite(output_max):
        raise ValueError("output_max must be finite.")

    if output_min >= output_max:
        raise ValueError(
            "output_min must be less than output_max."
        )

    values = np.asarray(
        values,
        dtype=np.float64,
    )

    if values.size == 0:
        return values.copy()

    if not np.isfinite(values).all():
        raise ValueError(
            "Input contains NaN or infinite values."
        )

    source_min = np.min(values)
    source_max = np.max(values)
    source_range = source_max - source_min

    if source_range == 0.0:
        return np.full_like(
            values,
            output_min,
        )

    normalized = (
        (values - source_min)
        / source_range
    )

    return (
        normalized * (output_max - output_min)
        + output_min
    )


def transform(
    values: np.ndarray,
    *,
    factor: float = 1.0,
    offset: float = 0.0,
    minimum: float = 0.0,
    maximum: float = 1_000_000.0,
) -> np.ndarray:
    """Run the standard vectorized benchmark transformation."""
    return scale_offset_and_clip(
        values,
        factor=factor,
        offset=offset,
        minimum=minimum,
        maximum=maximum,
    )


def to_float64(
    values: np.ndarray,
) -> np.ndarray:
    """Convert numerical input to a float64 NumPy array for benchmarking."""
    return np.asarray(
        values,
        dtype=np.float64,
    )

"""NumPy-based numerical processing implementations for performance benchmarks."""

from __future__ import annotations

import numpy as np


def scale_and_offset(
    values: np.ndarray,
    *,
    factor: float = 1.0,
    offset: float = 0.0,
) -> np.ndarray:
    """Apply scaling and offset using vectorized NumPy operations."""
    values = np.asarray(values)

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected a numeric array, got {values.dtype}."
        )

    if not np.isfinite(factor):
        raise ValueError("factor must be finite.")

    if not np.isfinite(offset):
        raise ValueError("offset must be finite.")

    return values * factor + offset


def clip(
    values: np.ndarray,
    *,
    minimum: float,
    maximum: float,
) -> np.ndarray:
    """Clip values to an inclusive range using NumPy."""
    if not np.isfinite(minimum):
        raise ValueError("minimum must be finite.")

    if not np.isfinite(maximum):
        raise ValueError("maximum must be finite.")

    if minimum > maximum:
        raise ValueError(
            "minimum must not exceed maximum."
        )

    values = np.asarray(values)

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected a numeric array, got {values.dtype}."
        )

    return np.clip(
        values,
        minimum,
        maximum,
    )


def scale_offset_and_clip(
    values: np.ndarray,
    *,
    factor: float = 1.0,
    offset: float = 0.0,
    minimum: float = 0.0,
    maximum: float = 1_000_000.0,
) -> np.ndarray:
    """Apply scaling, offset, and clipping with vectorized operations."""
    if not np.isfinite(factor):
        raise ValueError("factor must be finite.")

    if not np.isfinite(offset):
        raise ValueError("offset must be finite.")

    if not np.isfinite(minimum):
        raise ValueError("minimum must be finite.")

    if not np.isfinite(maximum):
        raise ValueError("maximum must be finite.")

    if minimum > maximum:
        raise ValueError(
            "minimum must not exceed maximum."
        )

    values = np.asarray(values)

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected a numeric array, got {values.dtype}."
        )

    transformed = values * factor + offset

    return np.clip(
        transformed,
        minimum,
        maximum,
    )


def sum_values(
    values: np.ndarray,
    *,
    axis: int | tuple[int, ...] | None = None,
) -> np.ndarray | np.generic:
    """Calculate an array sum with NumPy's vectorized reduction."""
    values = np.asarray(values)

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected a numeric array, got {values.dtype}."
        )

    return np.sum(
        values,
        axis=axis,
    )


def mean_values(
    values: np.ndarray,
    *,
    axis: int | tuple[int, ...] | None = None,
) -> np.ndarray | np.generic:
    """Calculate an arithmetic mean using NumPy."""
    values = np.asarray(values)

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected a numeric array, got {values.dtype}."
        )

    if values.size == 0:
        raise ValueError(
            "Cannot calculate the mean of an empty array."
        )

    return np.mean(
        values,
        axis=axis,
    )


def filter_range(
    values: np.ndarray,
    *,
    minimum: float,
    maximum: float,
) -> np.ndarray:
    """Filter values inside an inclusive range using Boolean masking."""
    if not np.isfinite(minimum):
        raise ValueError("minimum must be finite.")

    if not np.isfinite(maximum):
        raise ValueError("maximum must be finite.")

    if minimum > maximum:
        raise ValueError(
            "minimum must not exceed maximum."
        )

    values = np.asarray(values)

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected a numeric array, got {values.dtype}."
        )

    mask = (
        (values >= minimum)
        & (values <= maximum)
    )

    return values[mask]


def normalize(
    values: np.ndarray,
    *,
    output_min: float = 0.0,
    output_max: float = 1.0,
) -> np.ndarray:
    """Apply min-max normalization using vectorized operations."""
    if not np.isfinite(output_min):
        raise ValueError("output_min must be finite.")

    if not np.isfinite(output_max):
        raise ValueError("output_max must be finite.")

    if output_min >= output_max:
        raise ValueError(
            "output_min must be less than output_max."
        )

    values = np.asarray(
        values,
        dtype=np.float64,
    )

    if values.size == 0:
        return values.copy()

    if not np.isfinite(values).all():
        raise ValueError(
            "Input contains NaN or infinite values."
        )

    source_min = np.min(values)
    source_max = np.max(values)
    source_range = source_max - source_min

    if source_range == 0.0:
        return np.full_like(
            values,
            output_min,
        )

    normalized = (
        (values - source_min)
        / source_range
    )

    return (
        normalized * (output_max - output_min)
        + output_min
    )


def transform(
    values: np.ndarray,
    *,
    factor: float = 1.0,
    offset: float = 0.0,
    minimum: float = 0.0,
    maximum: float = 1_000_000.0,
) -> np.ndarray:
    """Run the standard vectorized benchmark transformation."""
    return scale_offset_and_clip(
        values,
        factor=factor,
        offset=offset,
        minimum=minimum,
        maximum=maximum,
    )


def to_float64(
    values: np.ndarray,
) -> np.ndarray:
    """Convert numerical input to a float64 NumPy array for benchmarking."""
    return np.asarray(
        values,
        dtype=np.float64,
    )