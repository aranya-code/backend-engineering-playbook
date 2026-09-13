"""End-to-end pipeline orchestration for the Numerical Data Processor."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .config import (
    DEFAULT_OUTPUT_FILENAME,
    OUTPUT_DIR,
)
from .exporter import export_array, export_statistics
from .loader import load_array
from .processor import normalize
from .statistics import describe
from .validator import validate_array


def run_pipeline(
    input_path: str | Path,
    *,
    output_array_path: str | Path | None = None,
    output_statistics_path: str | Path | None = None,
) -> tuple[Path, Path]:
    """Load, validate, process, analyze, and export a numerical dataset."""
    values = load_array(input_path)
    values = validate_array(values)

    normalized = normalize(values)
    statistics = describe(values)

    array_path = export_array(
        normalized,
        output_array_path
        if output_array_path is not None
        else OUTPUT_DIR / DEFAULT_OUTPUT_FILENAME,
    )

    statistics_path = export_statistics(
        statistics,
        output_statistics_path
        if output_statistics_path is not None
        else OUTPUT_DIR / "statistics.json",
    )

    return array_path, statistics_path


def process_values(
    values: np.ndarray,
) -> tuple[np.ndarray, dict[str, float]]:
    """Process an in-memory array without performing file I/O."""
    validated = validate_array(values)

    normalized = normalize(validated)
    statistics = describe(validated)

    return normalized, statistics

"""End-to-end pipeline orchestration for the Numerical Data Processor."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .config import (
    DEFAULT_OUTPUT_FILENAME,
    OUTPUT_DIR,
)
from .exporter import export_array, export_statistics
from .loader import load_array
from .processor import normalize
from .statistics import describe
from .validator import validate_array


def run_pipeline(
    input_path: str | Path,
    *,
    output_array_path: str | Path | None = None,
    output_statistics_path: str | Path | None = None,
) -> tuple[Path, Path]:
    """Load, validate, process, analyze, and export a numerical dataset."""
    values = load_array(input_path)
    values = validate_array(values)

    normalized = normalize(values)
    statistics = describe(values)

    array_path = export_array(
        normalized,
        output_array_path
        if output_array_path is not None
        else OUTPUT_DIR / DEFAULT_OUTPUT_FILENAME,
    )

    statistics_path = export_statistics(
        statistics,
        output_statistics_path
        if output_statistics_path is not None
        else OUTPUT_DIR / "statistics.json",
    )

    return array_path, statistics_path


def process_values(
    values: np.ndarray,
) -> tuple[np.ndarray, dict[str, float]]:
    """Process an in-memory array without performing file I/O."""
    validated = validate_array(values)

    normalized = normalize(validated)
    statistics = describe(validated)

    return normalized, statistics