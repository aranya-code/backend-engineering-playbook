"""Boolean masking and conditional selection utilities."""

from __future__ import annotations

import numpy as np


def finite_mask(values: np.ndarray) -> np.ndarray:
    """Return a mask selecting only finite numerical values."""
    values = np.asarray(values)

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected numeric dtype, got {values.dtype}."
        )

    return np.isfinite(values)


def range_mask(
    values: np.ndarray,
    *,
    minimum: float,
    maximum: float,
) -> np.ndarray:
    """Return a mask for values inside an inclusive numerical range."""
    if minimum > maximum:
        raise ValueError(
            "minimum must not exceed maximum."
        )

    values = np.asarray(
        values,
        dtype=np.float64,
    )

    return (
        (values >= minimum)
        & (values <= maximum)
    )


def positive_mask(values: np.ndarray) -> np.ndarray:
    """Return a mask selecting strictly positive values."""
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    return values > 0.0


def select(
    values: np.ndarray,
    mask: np.ndarray,
) -> np.ndarray:
    """Select elements using a Boolean mask."""
    values = np.asarray(values)
    mask = np.asarray(mask)

    if mask.dtype != np.bool_:
        raise TypeError(
            f"Expected Boolean mask, got {mask.dtype}."
        )

    if mask.shape != values.shape:
        raise ValueError(
            f"Mask shape {mask.shape} does not match "
            f"value shape {values.shape}."
        )

    return values[mask]


def filter_finite(
    values: np.ndarray,
) -> np.ndarray:
    """Return only finite values from a numerical array."""
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    return values[np.isfinite(values)]


def filter_range(
    values: np.ndarray,
    *,
    minimum: float,
    maximum: float,
) -> np.ndarray:
    """Return values inside an inclusive numerical range."""
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    mask = range_mask(
        values,
        minimum=minimum,
        maximum=maximum,
    )

    return values[mask]


def replace_where(
    values: np.ndarray,
    replacement: float,
    *,
    predicate: np.ndarray,
) -> np.ndarray:
    """Replace elements selected by a Boolean predicate."""
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    predicate = np.asarray(predicate)

    if predicate.dtype != np.bool_:
        raise TypeError(
            f"Expected Boolean predicate, got {predicate.dtype}."
        )

    if predicate.shape != values.shape:
        raise ValueError(
            f"Predicate shape {predicate.shape} does not match "
            f"value shape {values.shape}."
        )

    if not np.isfinite(replacement):
        raise ValueError(
            "replacement must be finite."
        )

    result = values.copy()
    result[predicate] = replacement

    return result

"""Boolean masking and conditional selection utilities."""

from __future__ import annotations

import numpy as np


def finite_mask(values: np.ndarray) -> np.ndarray:
    """Return a mask selecting only finite numerical values."""
    values = np.asarray(values)

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected numeric dtype, got {values.dtype}."
        )

    return np.isfinite(values)


def range_mask(
    values: np.ndarray,
    *,
    minimum: float,
    maximum: float,
) -> np.ndarray:
    """Return a mask for values inside an inclusive numerical range."""
    if minimum > maximum:
        raise ValueError(
            "minimum must not exceed maximum."
        )

    values = np.asarray(
        values,
        dtype=np.float64,
    )

    return (
        (values >= minimum)
        & (values <= maximum)
    )


def positive_mask(values: np.ndarray) -> np.ndarray:
    """Return a mask selecting strictly positive values."""
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    return values > 0.0


def select(
    values: np.ndarray,
    mask: np.ndarray,
) -> np.ndarray:
    """Select elements using a Boolean mask."""
    values = np.asarray(values)
    mask = np.asarray(mask)

    if mask.dtype != np.bool_:
        raise TypeError(
            f"Expected Boolean mask, got {mask.dtype}."
        )

    if mask.shape != values.shape:
        raise ValueError(
            f"Mask shape {mask.shape} does not match "
            f"value shape {values.shape}."
        )

    return values[mask]


def filter_finite(
    values: np.ndarray,
) -> np.ndarray:
    """Return only finite values from a numerical array."""
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    return values[np.isfinite(values)]


def filter_range(
    values: np.ndarray,
    *,
    minimum: float,
    maximum: float,
) -> np.ndarray:
    """Return values inside an inclusive numerical range."""
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    mask = range_mask(
        values,
        minimum=minimum,
        maximum=maximum,
    )

    return values[mask]


def replace_where(
    values: np.ndarray,
    replacement: float,
    *,
    predicate: np.ndarray,
) -> np.ndarray:
    """Replace elements selected by a Boolean predicate."""
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    predicate = np.asarray(predicate)

    if predicate.dtype != np.bool_:
        raise TypeError(
            f"Expected Boolean predicate, got {predicate.dtype}."
        )

    if predicate.shape != values.shape:
        raise ValueError(
            f"Predicate shape {predicate.shape} does not match "
            f"value shape {values.shape}."
        )

    if not np.isfinite(replacement):
        raise ValueError(
            "replacement must be finite."
        )

    result = values.copy()
    result[predicate] = replacement

    return result