"""Memory measurement utilities for numerical performance benchmarks."""

from __future__ import annotations

import gc
import resource
import tracemalloc
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np


@dataclass(frozen=True, slots=True)
class ArrayMemoryStats:
    """Memory characteristics of a NumPy array."""

    shape: tuple[int, ...]
    dtype: str
    size: int
    itemsize: int
    nbytes: int
    c_contiguous: bool
    f_contiguous: bool


@dataclass(frozen=True, slots=True)
class MemoryMeasurement:
    """Python allocation statistics captured around an operation."""

    current_bytes: int
    peak_bytes: int
    rss_before_bytes: int
    rss_after_bytes: int

    @property
    def traced_peak_bytes(self) -> int:
        """Return peak Python allocation observed during measurement."""
        return self.peak_bytes

    @property
    def rss_delta_bytes(self) -> int:
        """Return the change in process resident memory."""
        return self.rss_after_bytes - self.rss_before_bytes


def array_memory_stats(
    values: np.ndarray,
) -> ArrayMemoryStats:
    """Return storage and layout metadata for a NumPy array."""
    values = np.asarray(values)

    return ArrayMemoryStats(
        shape=values.shape,
        dtype=str(values.dtype),
        size=int(values.size),
        itemsize=int(values.itemsize),
        nbytes=int(values.nbytes),
        c_contiguous=bool(values.flags.c_contiguous),
        f_contiguous=bool(values.flags.f_contiguous),
    )


def array_memory_bytes(
    values: np.ndarray,
) -> int:
    """Return the size of a NumPy array's data buffer in bytes."""
    values = np.asarray(values)
    return int(values.nbytes)


def arrays_memory_bytes(
    *values: np.ndarray,
) -> int:
    """Return the combined data-buffer size of multiple arrays."""
    return sum(
        array_memory_bytes(value)
        for value in values
    )


def dtype_memory_bytes(
    size: int,
    dtype: np.dtype | type,
) -> int:
    """Estimate raw data-buffer memory for a homogeneous NumPy array."""
    if size < 0:
        raise ValueError("size must be non-negative.")

    resolved_dtype = np.dtype(dtype)

    return int(
        size * resolved_dtype.itemsize
    )


def measure_operation(
    function: Callable[..., Any],
    *args: Any,
    collect_garbage: bool = True,
    **kwargs: Any,
) -> MemoryMeasurement:
    """Measure Python allocations and process RSS around one operation."""
    if collect_garbage:
        gc.collect()

    rss_before = _resident_set_size_bytes()

    tracemalloc.start()

    try:
        function(
            *args,
            **kwargs,
        )
        current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    rss_after = _resident_set_size_bytes()

    return MemoryMeasurement(
        current_bytes=int(current),
        peak_bytes=int(peak),
        rss_before_bytes=rss_before,
        rss_after_bytes=rss_after,
    )


def compare_memory(
    baseline_function: Callable[..., Any],
    candidate_function: Callable[..., Any],
    *args: Any,
    collect_garbage: bool = True,
    **kwargs: Any,
) -> dict[str, MemoryMeasurement]:
    """Measure memory behavior of two implementations using the same input."""
    return {
        "baseline": measure_operation(
            baseline_function,
            *args,
            collect_garbage=collect_garbage,
            **kwargs,
        ),
        "candidate": measure_operation(
            candidate_function,
            *args,
            collect_garbage=collect_garbage,
            **kwargs,
        ),
    }


def format_bytes(
    value: int,
) -> str:
    """Format a byte count for human-readable benchmark output."""
    if value < 0:
        raise ValueError("value must be non-negative.")

    units = (
        "B",
        "KiB",
        "MiB",
        "GiB",
        "TiB",
    )

    amount = float(value)

    for unit in units:
        if amount < 1024.0 or unit == units[-1]:
            return f"{amount:.2f} {unit}"

        amount /= 1024.0

    return f"{amount:.2f} TiB"


def memory_metadata(
    measurement: MemoryMeasurement,
) -> dict[str, int | str]:
    """Convert a memory measurement into a serializable metadata mapping."""
    return {
        "current_bytes": measurement.current_bytes,
        "current": format_bytes(
            measurement.current_bytes
        ),
        "peak_bytes": measurement.peak_bytes,
        "peak": format_bytes(
            measurement.peak_bytes
        ),
        "rss_before_bytes": measurement.rss_before_bytes,
        "rss_before": format_bytes(
            measurement.rss_before_bytes
        ),
        "rss_after_bytes": measurement.rss_after_bytes,
        "rss_after": format_bytes(
            measurement.rss_after_bytes
        ),
        "rss_delta_bytes": measurement.rss_delta_bytes,
        "rss_delta": format_bytes(
            abs(measurement.rss_delta_bytes)
        ),
    }


def _resident_set_size_bytes() -> int:
    """Return current process RSS using the platform resource interface."""
    usage = resource.getrusage(
        resource.RUSAGE_SELF
    )

    rss = int(usage.ru_maxrss)

    if rss <= 0:
        return 0

    return _normalize_maxrss_units(rss)


def _normalize_maxrss_units(
    value: int,
) -> int:
    """Normalize platform-specific ru_maxrss units to bytes."""
    if value < 0:
        raise ValueError("RSS value must be non-negative.")

    # Linux reports KiB; macOS reports bytes.
    if value < 1024 * 1024:
        return value * 1024

    return value

"""Memory measurement utilities for numerical performance benchmarks."""

from __future__ import annotations

import gc
import resource
import tracemalloc
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np


@dataclass(frozen=True, slots=True)
class ArrayMemoryStats:
    """Memory characteristics of a NumPy array."""

    shape: tuple[int, ...]
    dtype: str
    size: int
    itemsize: int
    nbytes: int
    c_contiguous: bool
    f_contiguous: bool


@dataclass(frozen=True, slots=True)
class MemoryMeasurement:
    """Python allocation statistics captured around an operation."""

    current_bytes: int
    peak_bytes: int
    rss_before_bytes: int
    rss_after_bytes: int

    @property
    def traced_peak_bytes(self) -> int:
        """Return peak Python allocation observed during measurement."""
        return self.peak_bytes

    @property
    def rss_delta_bytes(self) -> int:
        """Return the change in process resident memory."""
        return self.rss_after_bytes - self.rss_before_bytes


def array_memory_stats(
    values: np.ndarray,
) -> ArrayMemoryStats:
    """Return storage and layout metadata for a NumPy array."""
    values = np.asarray(values)

    return ArrayMemoryStats(
        shape=values.shape,
        dtype=str(values.dtype),
        size=int(values.size),
        itemsize=int(values.itemsize),
        nbytes=int(values.nbytes),
        c_contiguous=bool(values.flags.c_contiguous),
        f_contiguous=bool(values.flags.f_contiguous),
    )


def array_memory_bytes(
    values: np.ndarray,
) -> int:
    """Return the size of a NumPy array's data buffer in bytes."""
    values = np.asarray(values)
    return int(values.nbytes)


def arrays_memory_bytes(
    *values: np.ndarray,
) -> int:
    """Return the combined data-buffer size of multiple arrays."""
    return sum(
        array_memory_bytes(value)
        for value in values
    )


def dtype_memory_bytes(
    size: int,
    dtype: np.dtype | type,
) -> int:
    """Estimate raw data-buffer memory for a homogeneous NumPy array."""
    if size < 0:
        raise ValueError("size must be non-negative.")

    resolved_dtype = np.dtype(dtype)

    return int(
        size * resolved_dtype.itemsize
    )


def measure_operation(
    function: Callable[..., Any],
    *args: Any,
    collect_garbage: bool = True,
    **kwargs: Any,
) -> MemoryMeasurement:
    """Measure Python allocations and process RSS around one operation."""
    if collect_garbage:
        gc.collect()

    rss_before = _resident_set_size_bytes()

    tracemalloc.start()

    try:
        function(
            *args,
            **kwargs,
        )
        current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    rss_after = _resident_set_size_bytes()

    return MemoryMeasurement(
        current_bytes=int(current),
        peak_bytes=int(peak),
        rss_before_bytes=rss_before,
        rss_after_bytes=rss_after,
    )


def compare_memory(
    baseline_function: Callable[..., Any],
    candidate_function: Callable[..., Any],
    *args: Any,
    collect_garbage: bool = True,
    **kwargs: Any,
) -> dict[str, MemoryMeasurement]:
    """Measure memory behavior of two implementations using the same input."""
    return {
        "baseline": measure_operation(
            baseline_function,
            *args,
            collect_garbage=collect_garbage,
            **kwargs,
        ),
        "candidate": measure_operation(
            candidate_function,
            *args,
            collect_garbage=collect_garbage,
            **kwargs,
        ),
    }


def format_bytes(
    value: int,
) -> str:
    """Format a byte count for human-readable benchmark output."""
    if value < 0:
        raise ValueError("value must be non-negative.")

    units = (
        "B",
        "KiB",
        "MiB",
        "GiB",
        "TiB",
    )

    amount = float(value)

    for unit in units:
        if amount < 1024.0 or unit == units[-1]:
            return f"{amount:.2f} {unit}"

        amount /= 1024.0

    return f"{amount:.2f} TiB"


def memory_metadata(
    measurement: MemoryMeasurement,
) -> dict[str, int | str]:
    """Convert a memory measurement into a serializable metadata mapping."""
    return {
        "current_bytes": measurement.current_bytes,
        "current": format_bytes(
            measurement.current_bytes
        ),
        "peak_bytes": measurement.peak_bytes,
        "peak": format_bytes(
            measurement.peak_bytes
        ),
        "rss_before_bytes": measurement.rss_before_bytes,
        "rss_before": format_bytes(
            measurement.rss_before_bytes
        ),
        "rss_after_bytes": measurement.rss_after_bytes,
        "rss_after": format_bytes(
            measurement.rss_after_bytes
        ),
        "rss_delta_bytes": measurement.rss_delta_bytes,
        "rss_delta": format_bytes(
            abs(measurement.rss_delta_bytes)
        ),
    }


def _resident_set_size_bytes() -> int:
    """Return current process RSS using the platform resource interface."""
    usage = resource.getrusage(
        resource.RUSAGE_SELF
    )

    rss = int(usage.ru_maxrss)

    if rss <= 0:
        return 0

    return _normalize_maxrss_units(rss)


def _normalize_maxrss_units(
    value: int,
) -> int:
    """Normalize platform-specific ru_maxrss units to bytes."""
    if value < 0:
        raise ValueError("RSS value must be non-negative.")

    # Linux reports KiB; macOS reports bytes.
    if value < 1024 * 1024:
        return value * 1024

    return value