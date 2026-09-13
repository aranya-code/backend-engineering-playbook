"""Validation utilities for the Numerical Data Processor."""

from __future__ import annotations

import numpy as np

from .config import (
    MAX_ALLOWED_VALUE,
    MAX_ELEMENTS,
    MIN_ALLOWED_VALUE,
    REJECT_NON_FINITE_VALUES,
)


def validate_array(
    values: np.ndarray,
    *,
    max_elements: int = MAX_ELEMENTS,
    minimum: float = MIN_ALLOWED_VALUE,
    maximum: float = MAX_ALLOWED_VALUE,
    reject_non_finite: bool = REJECT_NON_FINITE_VALUES,
) -> np.ndarray:
    """Validate numerical input against the processor's data constraints."""
    values = np.asarray(values)

    if values.ndim != 1:
        raise ValueError(
            f"Expected a one-dimensional array, got shape {values.shape}."
        )

    if values.size == 0:
        raise ValueError("Input array must not be empty.")

    if values.size > max_elements:
        raise ValueError(
            f"Input contains {values.size:,} elements; "
            f"maximum allowed is {max_elements:,}."
        )

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected numeric dtype, got {values.dtype}."
        )

    if reject_non_finite and not np.isfinite(values).all():
        raise ValueError(
            "Input contains NaN or infinite values."
        )

    if np.any(values < minimum):
        raise ValueError(
            f"Input contains values below the minimum of {minimum}."
        )

    if np.any(values > maximum):
        raise ValueError(
            f"Input contains values above the maximum of {maximum}."
        )

    return values

"""Validation utilities for the Numerical Data Processor."""

from __future__ import annotations

import numpy as np

from .config import (
    MAX_ALLOWED_VALUE,
    MAX_ELEMENTS,
    MIN_ALLOWED_VALUE,
    REJECT_NON_FINITE_VALUES,
)


def validate_array(
    values: np.ndarray,
    *,
    max_elements: int = MAX_ELEMENTS,
    minimum: float = MIN_ALLOWED_VALUE,
    maximum: float = MAX_ALLOWED_VALUE,
    reject_non_finite: bool = REJECT_NON_FINITE_VALUES,
) -> np.ndarray:
    """Validate numerical input against the processor's data constraints."""
    values = np.asarray(values)

    if values.ndim != 1:
        raise ValueError(
            f"Expected a one-dimensional array, got shape {values.shape}."
        )

    if values.size == 0:
        raise ValueError("Input array must not be empty.")

    if values.size > max_elements:
        raise ValueError(
            f"Input contains {values.size:,} elements; "
            f"maximum allowed is {max_elements:,}."
        )

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected numeric dtype, got {values.dtype}."
        )

    if reject_non_finite and not np.isfinite(values).all():
        raise ValueError(
            "Input contains NaN or infinite values."
        )

    if np.any(values < minimum):
        raise ValueError(
            f"Input contains values below the minimum of {minimum}."
        )

    if np.any(values > maximum):
        raise ValueError(
            f"Input contains values above the maximum of {maximum}."
        )

    return values