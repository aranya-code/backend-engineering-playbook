"""Pipeline orchestration for vectorized numerical data transformation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .aggregation import finite_statistics
from .config import (
    BATCH_SIZE,
    DEFAULT_OFFSET,
    DEFAULT_SCALE,
    MAX_ELEMENTS,
    MAX_ALLOWED_VALUE,
    MIN_ALLOWED_VALUE,
    NORMALIZE_OUTPUT,
)
from .exporter import export_array
from .loader import load_array
from .masking import finite_mask, range_mask
from .transformations import transform


@dataclass(frozen=True, slots=True)
class PipelineConfig:
    """Configuration for a single transformation pipeline execution."""

    factor: float = DEFAULT_SCALE
    offset: float = DEFAULT_OFFSET
    minimum: float = MIN_ALLOWED_VALUE
    maximum: float = MAX_ALLOWED_VALUE
    normalize_output: bool = NORMALIZE_OUTPUT
    max_elements: int = MAX_ELEMENTS
    batch_size: int = BATCH_SIZE

    def validate(self) -> None:
        """Validate pipeline configuration before processing starts."""
        if not np.isfinite(self.factor):
            raise ValueError("factor must be finite.")

        if not np.isfinite(self.offset):
            raise ValueError("offset must be finite.")

        if not np.isfinite(self.minimum):
            raise ValueError("minimum must be finite.")

        if not np.isfinite(self.maximum):
            raise ValueError("maximum must be finite.")

        if self.minimum > self.maximum:
            raise ValueError(
                "minimum must not exceed maximum."
            )

        if self.max_elements <= 0:
            raise ValueError(
                "max_elements must be positive."
            )

        if self.batch_size <= 0:
            raise ValueError(
                "batch_size must be positive."
            )


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """Operational result produced by a pipeline execution."""

    output_path: Path
    input_elements: int
    output_elements: int
    input_nbytes: int
    output_nbytes: int
    statistics: dict[str, float | int]


def validate_input(
    values: np.ndarray,
    *,
    max_elements: int,
) -> np.ndarray:
    """Validate input shape, size, dtype, and finite numerical values."""
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    if values.ndim == 0:
        raise ValueError(
            "Expected an array with at least one dimension."
        )

    if values.size > max_elements:
        raise ValueError(
            f"Input contains {values.size:,} elements; "
            f"maximum allowed is {max_elements:,}."
        )

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected numeric input, got {values.dtype}."
        )

    if not finite_mask(values).all():
        raise ValueError(
            "Input contains NaN or infinite values."
        )

    return values


def transform_batch(
    values: np.ndarray,
    *,
    config: PipelineConfig,
) -> np.ndarray:
    """Transform and retain values within the configured output range."""
    transformed = transform(
        values,
        factor=config.factor,
        amount=config.offset,
        minimum=config.minimum,
        maximum=config.maximum,
        normalize_output=config.normalize_output,
    )

    valid = range_mask(
        transformed,
        minimum=config.minimum,
        maximum=config.maximum,
    )

    return transformed[valid]


def run_pipeline(
    input_path: str | Path,
    output_path: str | Path,
    *,
    config: PipelineConfig | None = None,
) -> PipelineResult:
    """Load, validate, transform, aggregate, and export numerical data."""
    pipeline_config = config or PipelineConfig()
    pipeline_config.validate()

    values = load_array(
        input_path,
        max_elements=pipeline_config.max_elements,
    )

    values = validate_input(
        values,
        max_elements=pipeline_config.max_elements,
    )

    if values.ndim != 1:
        values = values.reshape(-1)

    transformed_batches: list[np.ndarray] = []

    for start in range(
        0,
        values.size,
        pipeline_config.batch_size,
    ):
        batch = values[
            start:start + pipeline_config.batch_size
        ]

        transformed_batch = transform_batch(
            batch,
            config=pipeline_config,
        )

        transformed_batches.append(
            transformed_batch
        )

    if transformed_batches:
        transformed = np.concatenate(
            transformed_batches
        )
    else:
        transformed = np.empty(
            0,
            dtype=np.float64,
        )

    destination = export_array(
        transformed,
        output_path,
        allow_overwrite=True,
    )

    statistics = finite_statistics(
        transformed
    ) if transformed.size else {
        "count": 0,
        "sum": 0.0,
        "mean": 0.0,
        "minimum": 0.0,
        "maximum": 0.0,
        "median": 0.0,
        "standard_deviation": 0.0,
    }

    return PipelineResult(
        output_path=destination,
        input_elements=int(values.size),
        output_elements=int(transformed.size),
        input_nbytes=int(values.nbytes),
        output_nbytes=int(transformed.nbytes),
        statistics=statistics,
    )

"""Pipeline orchestration for vectorized numerical data transformation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .aggregation import finite_statistics
from .config import (
    BATCH_SIZE,
    DEFAULT_OFFSET,
    DEFAULT_SCALE,
    MAX_ELEMENTS,
    MAX_ALLOWED_VALUE,
    MIN_ALLOWED_VALUE,
    NORMALIZE_OUTPUT,
)
from .exporter import export_array
from .loader import load_array
from .masking import finite_mask, range_mask
from .transformations import transform


@dataclass(frozen=True, slots=True)
class PipelineConfig:
    """Configuration for a single transformation pipeline execution."""

    factor: float = DEFAULT_SCALE
    offset: float = DEFAULT_OFFSET
    minimum: float = MIN_ALLOWED_VALUE
    maximum: float = MAX_ALLOWED_VALUE
    normalize_output: bool = NORMALIZE_OUTPUT
    max_elements: int = MAX_ELEMENTS
    batch_size: int = BATCH_SIZE

    def validate(self) -> None:
        """Validate pipeline configuration before processing starts."""
        if not np.isfinite(self.factor):
            raise ValueError("factor must be finite.")

        if not np.isfinite(self.offset):
            raise ValueError("offset must be finite.")

        if not np.isfinite(self.minimum):
            raise ValueError("minimum must be finite.")

        if not np.isfinite(self.maximum):
            raise ValueError("maximum must be finite.")

        if self.minimum > self.maximum:
            raise ValueError(
                "minimum must not exceed maximum."
            )

        if self.max_elements <= 0:
            raise ValueError(
                "max_elements must be positive."
            )

        if self.batch_size <= 0:
            raise ValueError(
                "batch_size must be positive."
            )


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """Operational result produced by a pipeline execution."""

    output_path: Path
    input_elements: int
    output_elements: int
    input_nbytes: int
    output_nbytes: int
    statistics: dict[str, float | int]


def validate_input(
    values: np.ndarray,
    *,
    max_elements: int,
) -> np.ndarray:
    """Validate input shape, size, dtype, and finite numerical values."""
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    if values.ndim == 0:
        raise ValueError(
            "Expected an array with at least one dimension."
        )

    if values.size > max_elements:
        raise ValueError(
            f"Input contains {values.size:,} elements; "
            f"maximum allowed is {max_elements:,}."
        )

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(
            f"Expected numeric input, got {values.dtype}."
        )

    if not finite_mask(values).all():
        raise ValueError(
            "Input contains NaN or infinite values."
        )

    return values


def transform_batch(
    values: np.ndarray,
    *,
    config: PipelineConfig,
) -> np.ndarray:
    """Transform and retain values within the configured output range."""
    transformed = transform(
        values,
        factor=config.factor,
        amount=config.offset,
        minimum=config.minimum,
        maximum=config.maximum,
        normalize_output=config.normalize_output,
    )

    valid = range_mask(
        transformed,
        minimum=config.minimum,
        maximum=config.maximum,
    )

    return transformed[valid]


def run_pipeline(
    input_path: str | Path,
    output_path: str | Path,
    *,
    config: PipelineConfig | None = None,
) -> PipelineResult:
    """Load, validate, transform, aggregate, and export numerical data."""
    pipeline_config = config or PipelineConfig()
    pipeline_config.validate()

    values = load_array(
        input_path,
        max_elements=pipeline_config.max_elements,
    )

    values = validate_input(
        values,
        max_elements=pipeline_config.max_elements,
    )

    if values.ndim != 1:
        values = values.reshape(-1)

    transformed_batches: list[np.ndarray] = []

    for start in range(
        0,
        values.size,
        pipeline_config.batch_size,
    ):
        batch = values[
            start:start + pipeline_config.batch_size
        ]

        transformed_batch = transform_batch(
            batch,
            config=pipeline_config,
        )

        transformed_batches.append(
            transformed_batch
        )

    if transformed_batches:
        transformed = np.concatenate(
            transformed_batches
        )
    else:
        transformed = np.empty(
            0,
            dtype=np.float64,
        )

    destination = export_array(
        transformed,
        output_path,
        allow_overwrite=True,
    )

    statistics = finite_statistics(
        transformed
    ) if transformed.size else {
        "count": 0,
        "sum": 0.0,
        "mean": 0.0,
        "minimum": 0.0,
        "maximum": 0.0,
        "median": 0.0,
        "standard_deviation": 0.0,
    }

    return PipelineResult(
        output_path=destination,
        input_elements=int(values.size),
        output_elements=int(transformed.size),
        input_nbytes=int(values.nbytes),
        output_nbytes=int(transformed.nbytes),
        statistics=statistics,
    )