"""Pure-Python numerical processing implementations for performance benchmarks."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def scale_and_offset(
    values: Sequence[float],
    *,
    factor: float = 1.0,
    offset: float = 0.0,
) -> list[float]:
    """Apply scaling and offset using an explicit Python loop."""
    if not np.isfinite(factor):
        raise ValueError("factor must be finite.")

    if not np.isfinite(offset):
        raise ValueError("offset must be finite.")

    return [
        value * factor + offset
        for value in values
    ]


def clip(
    values: Sequence[float],
    *,
    minimum: float,
    maximum: float,
) -> list[float]:
    """Clip values to an inclusive range using a Python loop."""
    if not np.isfinite(minimum):
        raise ValueError("minimum must be finite.")

    if not np.isfinite(maximum):
        raise ValueError("maximum must be finite.")

    if minimum > maximum:
        raise ValueError(
            "minimum must not exceed maximum."
        )

    result: list[float] = []

    for value in values:
        if value < minimum:
            result.append(minimum)
        elif value > maximum:
            result.append(maximum)
        else:
            result.append(value)

    return result


def scale_offset_and_clip(
    values: Sequence[float],
    *,
    factor: float = 1.0,
    offset: float = 0.0,
    minimum: float = 0.0,
    maximum: float = 1_000_000.0,
) -> list[float]:
    """Apply scaling, offset, and clipping in a single Python loop."""
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

    result: list[float] = []

    for value in values:
        transformed = value * factor + offset

        if transformed < minimum:
            transformed = minimum
        elif transformed > maximum:
            transformed = maximum

        result.append(transformed)

    return result


def sum_values(
    values: Sequence[float],
) -> float:
    """Calculate a sum using Python's built-in iteration."""
    total = 0.0

    for value in values:
        total += value

    return total


def mean_values(
    values: Sequence[float],
) -> float:
    """Calculate an arithmetic mean using explicit Python iteration."""
    count = 0
    total = 0.0

    for value in values:
        total += value
        count += 1

    if count == 0:
        raise ValueError(
            "Cannot calculate the mean of an empty sequence."
        )

    return total / count


def filter_range(
    values: Sequence[float],
    *,
    minimum: float,
    maximum: float,
) -> list[float]:
    """Filter values inside an inclusive range using a Python loop."""
    if minimum > maximum:
        raise ValueError(
            "minimum must not exceed maximum."
        )

    result: list[float] = []

    for value in values:
        if minimum <= value <= maximum:
            result.append(value)

    return result


def normalize(
    values: Sequence[float],
    *,
    output_min: float = 0.0,
    output_max: float = 1.0,
) -> list[float]:
    """Min-max normalize values using Python iteration."""
    if output_min >= output_max:
        raise ValueError(
            "output_min must be less than output_max."
        )

    values = list(values)

    if not values:
        return []

    source_min = min(values)
    source_max = max(values)
    source_range = source_max - source_min

    if source_range == 0.0:
        return [
            output_min
            for _ in values
        ]

    output_range = output_max - output_min

    return [
        (
            (value - source_min)
            / source_range
            * output_range
            + output_min
        )
        for value in values
    ]


def transform(
    values: Sequence[float],
    *,
    factor: float = 1.0,
    offset: float = 0.0,
    minimum: float = 0.0,
    maximum: float = 1_000_000.0,
) -> list[float]:
    """Run the benchmark transformation as a Python loop."""
    return scale_offset_and_clip(
        values,
        factor=factor,
        offset=offset,
        minimum=minimum,
        maximum=maximum,
    )


def to_numpy(
    values: Sequence[float],
    *,
    dtype: np.dtype | type = np.float64,
) -> np.ndarray:
    """Convert benchmark input to a NumPy array with the requested dtype."""
    return np.asarray(
        values,
        dtype=dtype,
    )

"""Pure-Python numerical processing implementations for performance benchmarks."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def scale_and_offset(
    values: Sequence[float],
    *,
    factor: float = 1.0,
    offset: float = 0.0,
) -> list[float]:
    """Apply scaling and offset using an explicit Python loop."""
    if not np.isfinite(factor):
        raise ValueError("factor must be finite.")

    if not np.isfinite(offset):
        raise ValueError("offset must be finite.")

    return [
        value * factor + offset
        for value in values
    ]


def clip(
    values: Sequence[float],
    *,
    minimum: float,
    maximum: float,
) -> list[float]:
    """Clip values to an inclusive range using a Python loop."""
    if not np.isfinite(minimum):
        raise ValueError("minimum must be finite.")

    if not np.isfinite(maximum):
        raise ValueError("maximum must be finite.")

    if minimum > maximum:
        raise ValueError(
            "minimum must not exceed maximum."
        )

    result: list[float] = []

    for value in values:
        if value < minimum:
            result.append(minimum)
        elif value > maximum:
            result.append(maximum)
        else:
            result.append(value)

    return result


def scale_offset_and_clip(
    values: Sequence[float],
    *,
    factor: float = 1.0,
    offset: float = 0.0,
    minimum: float = 0.0,
    maximum: float = 1_000_000.0,
) -> list[float]:
    """Apply scaling, offset, and clipping in a single Python loop."""
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

    result: list[float] = []

    for value in values:
        transformed = value * factor + offset

        if transformed < minimum:
            transformed = minimum
        elif transformed > maximum:
            transformed = maximum

        result.append(transformed)

    return result


def sum_values(
    values: Sequence[float],
) -> float:
    """Calculate a sum using Python's built-in iteration."""
    total = 0.0

    for value in values:
        total += value

    return total


def mean_values(
    values: Sequence[float],
) -> float:
    """Calculate an arithmetic mean using explicit Python iteration."""
    count = 0
    total = 0.0

    for value in values:
        total += value
        count += 1

    if count == 0:
        raise ValueError(
            "Cannot calculate the mean of an empty sequence."
        )

    return total / count


def filter_range(
    values: Sequence[float],
    *,
    minimum: float,
    maximum: float,
) -> list[float]:
    """Filter values inside an inclusive range using a Python loop."""
    if minimum > maximum:
        raise ValueError(
            "minimum must not exceed maximum."
        )

    result: list[float] = []

    for value in values:
        if minimum <= value <= maximum:
            result.append(value)

    return result


def normalize(
    values: Sequence[float],
    *,
    output_min: float = 0.0,
    output_max: float = 1.0,
) -> list[float]:
    """Min-max normalize values using Python iteration."""
    if output_min >= output_max:
        raise ValueError(
            "output_min must be less than output_max."
        )

    values = list(values)

    if not values:
        return []

    source_min = min(values)
    source_max = max(values)
    source_range = source_max - source_min

    if source_range == 0.0:
        return [
            output_min
            for _ in values
        ]

    output_range = output_max - output_min

    return [
        (
            (value - source_min)
            / source_range
            * output_range
            + output_min
        )
        for value in values
    ]


def transform(
    values: Sequence[float],
    *,
    factor: float = 1.0,
    offset: float = 0.0,
    minimum: float = 0.0,
    maximum: float = 1_000_000.0,
) -> list[float]:
    """Run the benchmark transformation as a Python loop."""
    return scale_offset_and_clip(
        values,
        factor=factor,
        offset=offset,
        minimum=minimum,
        maximum=maximum,
    )


def to_numpy(
    values: Sequence[float],
    *,
    dtype: np.dtype | type = np.float64,
) -> np.ndarray:
    """Convert benchmark input to a NumPy array with the requested dtype."""
    return np.asarray(
        values,
        dtype=dtype,
    )