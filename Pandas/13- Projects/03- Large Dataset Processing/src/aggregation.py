from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

import pandas as pd


class AggregationError(ValueError):
    """Raised when a large-dataset aggregation cannot be completed safely."""


@dataclass(frozen=True, slots=True)
class AggregationMetrics:
    """Represent metrics produced by a chunk aggregation."""

    input_rows: int
    output_rows: int
    groups: int
    numeric_total: float
    memory_bytes: int


@dataclass(frozen=True, slots=True)
class AggregationResult:
    """Represent an aggregated DataFrame and its metrics."""

    data: pd.DataFrame
    metrics: AggregationMetrics


def _validate_frame(
    frame: pd.DataFrame,
) -> None:
    """Validate the aggregation input."""
    if not isinstance(frame, pd.DataFrame):
        raise AggregationError(
            "frame must be a pandas DataFrame."
        )


def _validate_columns(
    frame: pd.DataFrame,
    columns: Iterable[str],
) -> None:
    """Validate that all requested columns exist."""
    missing = [
        column
        for column in columns
        if column not in frame.columns
    ]

    if missing:
        raise AggregationError(
            "Missing required columns: "
            + ", ".join(missing)
        )


def _validate_aggregation(
    aggregation: str,
) -> None:
    """Validate a supported aggregation function."""
    allowed = {
        "sum",
        "mean",
        "min",
        "max",
        "count",
        "median",
        "std",
        "var",
    }

    if aggregation not in allowed:
        raise AggregationError(
            "Unsupported aggregation. Expected one of: "
            + ", ".join(sorted(allowed))
        )


def _memory_bytes(
    frame: pd.DataFrame,
) -> int:
    """Return the deep memory footprint of a DataFrame."""
    return int(
        frame.memory_usage(
            index=True,
            deep=True,
        ).sum()
    )


def aggregate_chunk(
    frame: pd.DataFrame,
    *,
    dimensions: Sequence[str],
    value_column: str,
    aggregation: str = "sum",
    dropna: bool = False,
) -> pd.DataFrame:
    """Aggregate one chunk using vectorized Pandas groupby operations."""
    _validate_frame(frame)

    dimensions = tuple(dimensions)

    _validate_columns(
        frame,
        (
            *dimensions,
            value_column,
        ),
    )
    _validate_aggregation(
        aggregation
    )

    if not dimensions:
        raise AggregationError(
            "At least one dimension is required for grouped aggregation."
        )

    values = pd.to_numeric(
        frame[value_column],
        errors="coerce",
    )

    working = frame.loc[
        :,
        [*dimensions],
    ].copy()
    working[value_column] = values

    result = (
        working.groupby(
            list(dimensions),
            dropna=dropna,
            observed=True,
        )[value_column]
        .agg(aggregation)
        .reset_index()
    )

    return result


def aggregate_multiple_metrics(
    frame: pd.DataFrame,
    *,
    dimensions: Sequence[str],
    aggregations: Mapping[str, Sequence[str]],
    dropna: bool = False,
) -> pd.DataFrame:
    """Aggregate multiple columns and metrics in one groupby operation."""
    _validate_frame(frame)

    dimensions = tuple(dimensions)

    if not dimensions:
        raise AggregationError(
            "At least one dimension is required for grouped aggregation."
        )

    if not aggregations:
        raise AggregationError(
            "At least one aggregation specification is required."
        )

    value_columns = tuple(
        aggregations.keys()
    )

    _validate_columns(
        frame,
        (
            *dimensions,
            *value_columns,
        ),
    )

    for methods in aggregations.values():
        for method in methods:
            _validate_aggregation(
                method
            )

    working = frame.copy()

    for column in value_columns:
        working[column] = pd.to_numeric(
            working[column],
            errors="coerce",
        )

    result = (
        working.groupby(
            list(dimensions),
            dropna=dropna,
            observed=True,
        )
        .agg(
            {
                column: list(methods)
                for column, methods in aggregations.items()
            }
        )
    )

    result.columns = [
        "_".join(
            str(part)
            for part in column
            if str(part)
        )
        for column in result.columns.to_flat_index()
    ]

    return result.reset_index()


def aggregate_row_counts(
    frame: pd.DataFrame,
    *,
    dimensions: Sequence[str],
    output_column: str = "row_count",
    dropna: bool = False,
) -> pd.DataFrame:
    """Calculate record counts per dimension."""
    _validate_frame(frame)

    dimensions = tuple(dimensions)

    _validate_columns(
        frame,
        dimensions,
    )

    if not dimensions:
        raise AggregationError(
            "At least one dimension is required for row counts."
        )

    result = (
        frame.groupby(
            list(dimensions),
            dropna=dropna,
            observed=True,
        )
        .size()
        .rename(output_column)
        .reset_index()
    )

    return result


def aggregate_distinct_counts(
    frame: pd.DataFrame,
    *,
    dimensions: Sequence[str],
    value_column: str,
    output_column: str = "unique_count",
    dropna: bool = False,
) -> pd.DataFrame:
    """Calculate distinct value counts per dimension."""
    _validate_frame(frame)

    dimensions = tuple(dimensions)

    _validate_columns(
        frame,
        (
            *dimensions,
            value_column,
        ),
    )

    if not dimensions:
        raise AggregationError(
            "At least one dimension is required for distinct counts."
        )

    result = (
        frame.groupby(
            list(dimensions),
            dropna=dropna,
            observed=True,
        )[value_column]
        .nunique(dropna=True)
        .rename(output_column)
        .reset_index()
    )

    return result


def aggregate_weighted_average(
    frame: pd.DataFrame,
    *,
    dimensions: Sequence[str],
    value_column: str,
    weight_column: str,
    output_column: str = "weighted_average",
    dropna: bool = False,
) -> pd.DataFrame:
    """Calculate weighted averages without Python row iteration."""
    _validate_frame(frame)

    dimensions = tuple(dimensions)

    _validate_columns(
        frame,
        (
            *dimensions,
            value_column,
            weight_column,
        ),
    )

    if not dimensions:
        raise AggregationError(
            "At least one dimension is required for weighted averages."
        )

    working = frame.loc[
        :,
        [*dimensions, value_column, weight_column],
    ].copy()

    working[value_column] = pd.to_numeric(
        working[value_column],
        errors="coerce",
    )
    working[weight_column] = pd.to_numeric(
        working[weight_column],
        errors="coerce",
    )

    working["_weighted_value"] = (
        working[value_column]
        * working[weight_column]
    )

    grouped = (
        working.groupby(
            list(dimensions),
            dropna=dropna,
            observed=True,
        )
        .agg(
            weighted_value_sum=(
                "_weighted_value",
                "sum",
            ),
            weight_sum=(
                weight_column,
                "sum",
            ),
        )
        .reset_index()
    )

    denominator = grouped["weight_sum"].mask(
        grouped["weight_sum"].eq(0)
    )

    grouped[output_column] = (
        grouped["weighted_value_sum"]
        .div(denominator)
    )

    return grouped.loc[
        :,
        [
            *dimensions,
            output_column,
        ],
    ]


def merge_chunk_aggregates(
    aggregates: Iterable[pd.DataFrame],
    *,
    dimensions: Sequence[str],
    value_columns: Sequence[str],
) -> pd.DataFrame:
    """Merge independent chunk-level aggregates into a final aggregate."""
    frames = list(aggregates)

    dimensions = tuple(dimensions)
    value_columns = tuple(value_columns)

    if not frames:
        return pd.DataFrame(
            columns=[
                *dimensions,
                *value_columns,
            ]
        )

    for frame in frames:
        _validate_frame(frame)
        _validate_columns(
            frame,
            (
                *dimensions,
                *value_columns,
            ),
        )

    combined = pd.concat(
        frames,
        axis=0,
        ignore_index=True,
    )

    if not value_columns:
        return (
            combined.loc[
                :,
                list(dimensions),
            ]
            .drop_duplicates()
            .reset_index(drop=True)
        )

    return (
        combined.groupby(
            list(dimensions),
            dropna=False,
            observed=True,
        )[list(value_columns)]
        .sum()
        .reset_index()
    )


def aggregate_sum_and_count(
    frame: pd.DataFrame,
    *,
    dimensions: Sequence[str],
    value_column: str,
    value_sum_column: str = "value_sum",
    row_count_column: str = "row_count",
    dropna: bool = False,
) -> pd.DataFrame:
    """Produce sum and count metrics for a value column."""
    _validate_frame(frame)

    dimensions = tuple(dimensions)

    _validate_columns(
        frame,
        (
            *dimensions,
            value_column,
        ),
    )

    if not dimensions:
        raise AggregationError(
            "At least one dimension is required."
        )

    working = frame.loc[
        :,
        [*dimensions, value_column],
    ].copy()

    working[value_column] = pd.to_numeric(
        working[value_column],
        errors="coerce",
    )

    result = (
        working.groupby(
            list(dimensions),
            dropna=dropna,
            observed=True,
        )
        .agg(
            **{
                value_sum_column: (
                    value_column,
                    "sum",
                ),
                row_count_column: (
                    value_column,
                    "count",
                ),
            }
        )
        .reset_index()
    )

    return result


def calculate_derived_metrics(
    aggregate: pd.DataFrame,
    *,
    revenue_sum_column: str = "revenue_sum",
    order_count_column: str = "order_count",
    average_order_value_column: str = "average_order_value",
) -> pd.DataFrame:
    """Add derived reporting metrics such as average order value."""
    _validate_frame(aggregate)

    _validate_columns(
        aggregate,
        (
            revenue_sum_column,
            order_count_column,
        ),
    )

    result = aggregate.copy()

    revenue = pd.to_numeric(
        result[revenue_sum_column],
        errors="coerce",
    )
    order_count = pd.to_numeric(
        result[order_count_column],
        errors="coerce",
    )

    denominator = order_count.mask(
        order_count.eq(0)
    )

    result[average_order_value_column] = (
        revenue.div(denominator)
    )

    return result


def aggregate_overall_metrics(
    frame: pd.DataFrame,
    *,
    value_column: str,
) -> dict[str, int | float]:
    """Calculate dataset-level metrics without creating grouped output."""
    _validate_frame(frame)
    _validate_columns(
        frame,
        (value_column,),
    )

    values = pd.to_numeric(
        frame[value_column],
        errors="coerce",
    )

    return {
        "row_count": int(len(frame)),
        "non_null_count": int(
            values.notna().sum()
        ),
        "numeric_sum": float(
            values.sum(
                skipna=True
            )
        ),
        "numeric_mean": float(
            values.mean()
        )
        if values.notna().any()
        else 0.0,
        "numeric_min": float(
            values.min()
        )
        if values.notna().any()
        else 0.0,
        "numeric_max": float(
            values.max()
        )
        if values.notna().any()
        else 0.0,
    }


def aggregate_with_metrics(
    frame: pd.DataFrame,
    *,
    dimensions: Sequence[str],
    value_column: str,
    aggregation: str = "sum",
) -> AggregationResult:
    """Aggregate a DataFrame and return operational metrics."""
    _validate_frame(frame)

    result = aggregate_chunk(
        frame,
        dimensions=dimensions,
        value_column=value_column,
        aggregation=aggregation,
    )

    values = pd.to_numeric(
        frame[value_column],
        errors="coerce",
    )

    numeric_total = float(
        values.sum(
            skipna=True
        )
    )

    metrics = AggregationMetrics(
        input_rows=len(frame),
        output_rows=len(result),
        groups=len(result),
        numeric_total=numeric_total,
        memory_bytes=_memory_bytes(
            result
        ),
    )

    return AggregationResult(
        data=result,
        metrics=metrics,
    )


__all__ = [
    "AggregationError",
    "AggregationMetrics",
    "AggregationResult",
    "aggregate_chunk",
    "aggregate_distinct_counts",
    "aggregate_multiple_metrics",
    "aggregate_overall_metrics",
    "aggregate_row_counts",
    "aggregate_sum_and_count",
    "aggregate_weighted_average",
    "aggregate_with_metrics",
    "calculate_derived_metrics",
    "merge_chunk_aggregates",
]

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

import pandas as pd


class AggregationError(ValueError):
    """Raised when a large-dataset aggregation cannot be completed safely."""


@dataclass(frozen=True, slots=True)
class AggregationMetrics:
    """Represent metrics produced by a chunk aggregation."""

    input_rows: int
    output_rows: int
    groups: int
    numeric_total: float
    memory_bytes: int


@dataclass(frozen=True, slots=True)
class AggregationResult:
    """Represent an aggregated DataFrame and its metrics."""

    data: pd.DataFrame
    metrics: AggregationMetrics


def _validate_frame(
    frame: pd.DataFrame,
) -> None:
    """Validate the aggregation input."""
    if not isinstance(frame, pd.DataFrame):
        raise AggregationError(
            "frame must be a pandas DataFrame."
        )


def _validate_columns(
    frame: pd.DataFrame,
    columns: Iterable[str],
) -> None:
    """Validate that all requested columns exist."""
    missing = [
        column
        for column in columns
        if column not in frame.columns
    ]

    if missing:
        raise AggregationError(
            "Missing required columns: "
            + ", ".join(missing)
        )


def _validate_aggregation(
    aggregation: str,
) -> None:
    """Validate a supported aggregation function."""
    allowed = {
        "sum",
        "mean",
        "min",
        "max",
        "count",
        "median",
        "std",
        "var",
    }

    if aggregation not in allowed:
        raise AggregationError(
            "Unsupported aggregation. Expected one of: "
            + ", ".join(sorted(allowed))
        )


def _memory_bytes(
    frame: pd.DataFrame,
) -> int:
    """Return the deep memory footprint of a DataFrame."""
    return int(
        frame.memory_usage(
            index=True,
            deep=True,
        ).sum()
    )


def aggregate_chunk(
    frame: pd.DataFrame,
    *,
    dimensions: Sequence[str],
    value_column: str,
    aggregation: str = "sum",
    dropna: bool = False,
) -> pd.DataFrame:
    """Aggregate one chunk using vectorized Pandas groupby operations."""
    _validate_frame(frame)

    dimensions = tuple(dimensions)

    _validate_columns(
        frame,
        (
            *dimensions,
            value_column,
        ),
    )
    _validate_aggregation(
        aggregation
    )

    if not dimensions:
        raise AggregationError(
            "At least one dimension is required for grouped aggregation."
        )

    values = pd.to_numeric(
        frame[value_column],
        errors="coerce",
    )

    working = frame.loc[
        :,
        [*dimensions],
    ].copy()
    working[value_column] = values

    result = (
        working.groupby(
            list(dimensions),
            dropna=dropna,
            observed=True,
        )[value_column]
        .agg(aggregation)
        .reset_index()
    )

    return result


def aggregate_multiple_metrics(
    frame: pd.DataFrame,
    *,
    dimensions: Sequence[str],
    aggregations: Mapping[str, Sequence[str]],
    dropna: bool = False,
) -> pd.DataFrame:
    """Aggregate multiple columns and metrics in one groupby operation."""
    _validate_frame(frame)

    dimensions = tuple(dimensions)

    if not dimensions:
        raise AggregationError(
            "At least one dimension is required for grouped aggregation."
        )

    if not aggregations:
        raise AggregationError(
            "At least one aggregation specification is required."
        )

    value_columns = tuple(
        aggregations.keys()
    )

    _validate_columns(
        frame,
        (
            *dimensions,
            *value_columns,
        ),
    )

    for methods in aggregations.values():
        for method in methods:
            _validate_aggregation(
                method
            )

    working = frame.copy()

    for column in value_columns:
        working[column] = pd.to_numeric(
            working[column],
            errors="coerce",
        )

    result = (
        working.groupby(
            list(dimensions),
            dropna=dropna,
            observed=True,
        )
        .agg(
            {
                column: list(methods)
                for column, methods in aggregations.items()
            }
        )
    )

    result.columns = [
        "_".join(
            str(part)
            for part in column
            if str(part)
        )
        for column in result.columns.to_flat_index()
    ]

    return result.reset_index()


def aggregate_row_counts(
    frame: pd.DataFrame,
    *,
    dimensions: Sequence[str],
    output_column: str = "row_count",
    dropna: bool = False,
) -> pd.DataFrame:
    """Calculate record counts per dimension."""
    _validate_frame(frame)

    dimensions = tuple(dimensions)

    _validate_columns(
        frame,
        dimensions,
    )

    if not dimensions:
        raise AggregationError(
            "At least one dimension is required for row counts."
        )

    result = (
        frame.groupby(
            list(dimensions),
            dropna=dropna,
            observed=True,
        )
        .size()
        .rename(output_column)
        .reset_index()
    )

    return result


def aggregate_distinct_counts(
    frame: pd.DataFrame,
    *,
    dimensions: Sequence[str],
    value_column: str,
    output_column: str = "unique_count",
    dropna: bool = False,
) -> pd.DataFrame:
    """Calculate distinct value counts per dimension."""
    _validate_frame(frame)

    dimensions = tuple(dimensions)

    _validate_columns(
        frame,
        (
            *dimensions,
            value_column,
        ),
    )

    if not dimensions:
        raise AggregationError(
            "At least one dimension is required for distinct counts."
        )

    result = (
        frame.groupby(
            list(dimensions),
            dropna=dropna,
            observed=True,
        )[value_column]
        .nunique(dropna=True)
        .rename(output_column)
        .reset_index()
    )

    return result


def aggregate_weighted_average(
    frame: pd.DataFrame,
    *,
    dimensions: Sequence[str],
    value_column: str,
    weight_column: str,
    output_column: str = "weighted_average",
    dropna: bool = False,
) -> pd.DataFrame:
    """Calculate weighted averages without Python row iteration."""
    _validate_frame(frame)

    dimensions = tuple(dimensions)

    _validate_columns(
        frame,
        (
            *dimensions,
            value_column,
            weight_column,
        ),
    )

    if not dimensions:
        raise AggregationError(
            "At least one dimension is required for weighted averages."
        )

    working = frame.loc[
        :,
        [*dimensions, value_column, weight_column],
    ].copy()

    working[value_column] = pd.to_numeric(
        working[value_column],
        errors="coerce",
    )
    working[weight_column] = pd.to_numeric(
        working[weight_column],
        errors="coerce",
    )

    working["_weighted_value"] = (
        working[value_column]
        * working[weight_column]
    )

    grouped = (
        working.groupby(
            list(dimensions),
            dropna=dropna,
            observed=True,
        )
        .agg(
            weighted_value_sum=(
                "_weighted_value",
                "sum",
            ),
            weight_sum=(
                weight_column,
                "sum",
            ),
        )
        .reset_index()
    )

    denominator = grouped["weight_sum"].mask(
        grouped["weight_sum"].eq(0)
    )

    grouped[output_column] = (
        grouped["weighted_value_sum"]
        .div(denominator)
    )

    return grouped.loc[
        :,
        [
            *dimensions,
            output_column,
        ],
    ]


def merge_chunk_aggregates(
    aggregates: Iterable[pd.DataFrame],
    *,
    dimensions: Sequence[str],
    value_columns: Sequence[str],
) -> pd.DataFrame:
    """Merge independent chunk-level aggregates into a final aggregate."""
    frames = list(aggregates)

    dimensions = tuple(dimensions)
    value_columns = tuple(value_columns)

    if not frames:
        return pd.DataFrame(
            columns=[
                *dimensions,
                *value_columns,
            ]
        )

    for frame in frames:
        _validate_frame(frame)
        _validate_columns(
            frame,
            (
                *dimensions,
                *value_columns,
            ),
        )

    combined = pd.concat(
        frames,
        axis=0,
        ignore_index=True,
    )

    if not value_columns:
        return (
            combined.loc[
                :,
                list(dimensions),
            ]
            .drop_duplicates()
            .reset_index(drop=True)
        )

    return (
        combined.groupby(
            list(dimensions),
            dropna=False,
            observed=True,
        )[list(value_columns)]
        .sum()
        .reset_index()
    )


def aggregate_sum_and_count(
    frame: pd.DataFrame,
    *,
    dimensions: Sequence[str],
    value_column: str,
    value_sum_column: str = "value_sum",
    row_count_column: str = "row_count",
    dropna: bool = False,
) -> pd.DataFrame:
    """Produce sum and count metrics for a value column."""
    _validate_frame(frame)

    dimensions = tuple(dimensions)

    _validate_columns(
        frame,
        (
            *dimensions,
            value_column,
        ),
    )

    if not dimensions:
        raise AggregationError(
            "At least one dimension is required."
        )

    working = frame.loc[
        :,
        [*dimensions, value_column],
    ].copy()

    working[value_column] = pd.to_numeric(
        working[value_column],
        errors="coerce",
    )

    result = (
        working.groupby(
            list(dimensions),
            dropna=dropna,
            observed=True,
        )
        .agg(
            **{
                value_sum_column: (
                    value_column,
                    "sum",
                ),
                row_count_column: (
                    value_column,
                    "count",
                ),
            }
        )
        .reset_index()
    )

    return result


def calculate_derived_metrics(
    aggregate: pd.DataFrame,
    *,
    revenue_sum_column: str = "revenue_sum",
    order_count_column: str = "order_count",
    average_order_value_column: str = "average_order_value",
) -> pd.DataFrame:
    """Add derived reporting metrics such as average order value."""
    _validate_frame(aggregate)

    _validate_columns(
        aggregate,
        (
            revenue_sum_column,
            order_count_column,
        ),
    )

    result = aggregate.copy()

    revenue = pd.to_numeric(
        result[revenue_sum_column],
        errors="coerce",
    )
    order_count = pd.to_numeric(
        result[order_count_column],
        errors="coerce",
    )

    denominator = order_count.mask(
        order_count.eq(0)
    )

    result[average_order_value_column] = (
        revenue.div(denominator)
    )

    return result


def aggregate_overall_metrics(
    frame: pd.DataFrame,
    *,
    value_column: str,
) -> dict[str, int | float]:
    """Calculate dataset-level metrics without creating grouped output."""
    _validate_frame(frame)
    _validate_columns(
        frame,
        (value_column,),
    )

    values = pd.to_numeric(
        frame[value_column],
        errors="coerce",
    )

    return {
        "row_count": int(len(frame)),
        "non_null_count": int(
            values.notna().sum()
        ),
        "numeric_sum": float(
            values.sum(
                skipna=True
            )
        ),
        "numeric_mean": float(
            values.mean()
        )
        if values.notna().any()
        else 0.0,
        "numeric_min": float(
            values.min()
        )
        if values.notna().any()
        else 0.0,
        "numeric_max": float(
            values.max()
        )
        if values.notna().any()
        else 0.0,
    }


def aggregate_with_metrics(
    frame: pd.DataFrame,
    *,
    dimensions: Sequence[str],
    value_column: str,
    aggregation: str = "sum",
) -> AggregationResult:
    """Aggregate a DataFrame and return operational metrics."""
    _validate_frame(frame)

    result = aggregate_chunk(
        frame,
        dimensions=dimensions,
        value_column=value_column,
        aggregation=aggregation,
    )

    values = pd.to_numeric(
        frame[value_column],
        errors="coerce",
    )

    numeric_total = float(
        values.sum(
            skipna=True
        )
    )

    metrics = AggregationMetrics(
        input_rows=len(frame),
        output_rows=len(result),
        groups=len(result),
        numeric_total=numeric_total,
        memory_bytes=_memory_bytes(
            result
        ),
    )

    return AggregationResult(
        data=result,
        metrics=metrics,
    )


__all__ = [
    "AggregationError",
    "AggregationMetrics",
    "AggregationResult",
    "aggregate_chunk",
    "aggregate_distinct_counts",
    "aggregate_multiple_metrics",
    "aggregate_overall_metrics",
    "aggregate_row_counts",
    "aggregate_sum_and_count",
    "aggregate_weighted_average",
    "aggregate_with_metrics",
    "calculate_derived_metrics",
    "merge_chunk_aggregates",
]