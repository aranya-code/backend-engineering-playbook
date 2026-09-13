"""Vectorized numerical transformation utilities."""

from __future__ import annotations

import numpy as np

from .config import (
    DEFAULT_OFFSET,
    DEFAULT_SCALE,
    MAX_ALLOWED_VALUE,
    MIN_ALLOWED_VALUE,
    NORMALIZATION_MAX,
    NORMALIZATION_MIN,
)


def scale(
    values: np.ndarray,
    factor: float = DEFAULT_SCALE,
) -> np.ndarray:
    """Apply a scalar factor using vectorized multiplication."""
    values = np.asarray(values, dtype=np.float64)

    if not np.isfinite(factor):
        raise ValueError("factor must be finite.")

    return values * factor


def offset(
    values: np.ndarray,
    amount: float = DEFAULT_OFFSET,
) -> np.ndarray:
    """Apply a scalar offset using vectorized addition."""
    values = np.asarray(values, dtype=np.float64)

    if not np.isfinite(amount):
        raise ValueError("amount must be finite.")

    return values + amount


def scale_and_offset(
    values: np.ndarray,
    *,
    factor: float = DEFAULT_SCALE,
    amount: float = DEFAULT_OFFSET,
) -> np.ndarray:
    """Apply scaling followed by an additive offset."""
    values = np.asarray(values, dtype=np.float64)

    if not np.isfinite(factor):
        raise ValueError("factor must be finite.")

    if not np.isfinite(amount):
        raise ValueError("amount must be finite.")

    return values * factor + amount


def clip(
    values: np.ndarray,
    *,
    minimum: float = MIN_ALLOWED_VALUE,
    maximum: float = MAX_ALLOWED_VALUE,
) -> np.ndarray:
    """Restrict values to an inclusive numerical range."""
    if minimum > maximum:
        raise ValueError(
            "minimum must not exceed maximum."
        )

    values = np.asarray(values, dtype=np.float64)

    return np.clip(
        values,
        minimum,
        maximum,
    )


def normalize(
    values: np.ndarray,
    *,
    minimum: float = NORMALIZATION_MIN,
    maximum: float = NORMALIZATION_MAX,
) -> np.ndarray:
    """Normalize an array into the configured output range."""
    if minimum >= maximum:
        raise ValueError(
            "normalization minimum must be less than maximum."
        )

    values = np.asarray(values, dtype=np.float64)

    if values.size == 0:
        return values.copy()

    source_minimum = values.min()
    source_maximum = values.max()
    source_range = source_maximum - source_minimum

    if source_range == 0.0:
        return np.full_like(
            values,
            minimum,
        )

    normalized = (
        (values - source_minimum)
        / source_range
    )

    return (
        normalized * (maximum - minimum)
        + minimum
    )


def threshold(
    values: np.ndarray,
    *,
    minimum: float = MIN_ALLOWED_VALUE,
    maximum: float = MAX_ALLOWED_VALUE,
) -> np.ndarray:
    """Return a Boolean mask for values inside an inclusive range."""
    if minimum > maximum:
        raise ValueError(
            "minimum must not exceed maximum."
        )

    values = np.asarray(values, dtype=np.float64)

    return (
        (values >= minimum)
        & (values <= maximum)
    )


def transform(
    values: np.ndarray,
    *,
    factor: float = DEFAULT_SCALE,
    amount: float = DEFAULT_OFFSET,
    minimum: float = MIN_ALLOWED_VALUE,
    maximum: float = MAX_ALLOWED_VALUE,
    normalize_output: bool = False,
) -> np.ndarray:
    """Apply the project's standard vectorized transformation pipeline."""
    transformed = scale_and_offset(
        values,
        factor=factor,
        amount=amount,
    )

    transformed = clip(
        transformed,
        minimum=minimum,
        maximum=maximum,
    )

    if normalize_output:
        transformed = normalize(transformed)

    return transformed

"""Vectorized numerical transformation utilities."""

from __future__ import annotations

import numpy as np

from .config import (
    DEFAULT_OFFSET,
    DEFAULT_SCALE,
    MAX_ALLOWED_VALUE,
    MIN_ALLOWED_VALUE,
    NORMALIZATION_MAX,
    NORMALIZATION_MIN,
)


def scale(
    values: np.ndarray,
    factor: float = DEFAULT_SCALE,
) -> np.ndarray:
    """Apply a scalar factor using vectorized multiplication."""
    values = np.asarray(values, dtype=np.float64)

    if not np.isfinite(factor):
        raise ValueError("factor must be finite.")

    return values * factor


def offset(
    values: np.ndarray,
    amount: float = DEFAULT_OFFSET,
) -> np.ndarray:
    """Apply a scalar offset using vectorized addition."""
    values = np.asarray(values, dtype=np.float64)

    if not np.isfinite(amount):
        raise ValueError("amount must be finite.")

    return values + amount


def scale_and_offset(
    values: np.ndarray,
    *,
    factor: float = DEFAULT_SCALE,
    amount: float = DEFAULT_OFFSET,
) -> np.ndarray:
    """Apply scaling followed by an additive offset."""
    values = np.asarray(values, dtype=np.float64)

    if not np.isfinite(factor):
        raise ValueError("factor must be finite.")

    if not np.isfinite(amount):
        raise ValueError("amount must be finite.")

    return values * factor + amount


def clip(
    values: np.ndarray,
    *,
    minimum: float = MIN_ALLOWED_VALUE,
    maximum: float = MAX_ALLOWED_VALUE,
) -> np.ndarray:
    """Restrict values to an inclusive numerical range."""
    if minimum > maximum:
        raise ValueError(
            "minimum must not exceed maximum."
        )

    values = np.asarray(values, dtype=np.float64)

    return np.clip(
        values,
        minimum,
        maximum,
    )


def normalize(
    values: np.ndarray,
    *,
    minimum: float = NORMALIZATION_MIN,
    maximum: float = NORMALIZATION_MAX,
) -> np.ndarray:
    """Normalize an array into the configured output range."""
    if minimum >= maximum:
        raise ValueError(
            "normalization minimum must be less than maximum."
        )

    values = np.asarray(values, dtype=np.float64)

    if values.size == 0:
        return values.copy()

    source_minimum = values.min()
    source_maximum = values.max()
    source_range = source_maximum - source_minimum

    if source_range == 0.0:
        return np.full_like(
            values,
            minimum,
        )

    normalized = (
        (values - source_minimum)
        / source_range
    )

    return (
        normalized * (maximum - minimum)
        + minimum
    )


def threshold(
    values: np.ndarray,
    *,
    minimum: float = MIN_ALLOWED_VALUE,
    maximum: float = MAX_ALLOWED_VALUE,
) -> np.ndarray:
    """Return a Boolean mask for values inside an inclusive range."""
    if minimum > maximum:
        raise ValueError(
            "minimum must not exceed maximum."
        )

    values = np.asarray(values, dtype=np.float64)

    return (
        (values >= minimum)
        & (values <= maximum)
    )


def transform(
    values: np.ndarray,
    *,
    factor: float = DEFAULT_SCALE,
    amount: float = DEFAULT_OFFSET,
    minimum: float = MIN_ALLOWED_VALUE,
    maximum: float = MAX_ALLOWED_VALUE,
    normalize_output: bool = False,
) -> np.ndarray:
    """Apply the project's standard vectorized transformation pipeline."""
    transformed = scale_and_offset(
        values,
        factor=factor,
        amount=amount,
    )

    transformed = clip(
        transformed,
        minimum=minimum,
        maximum=maximum,
    )

    if normalize_output:
        transformed = normalize(transformed)

    return transformed