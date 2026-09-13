from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import pandas as pd


class TransformationError(ValueError):
    """Raised when normalized API data cannot be transformed safely."""


@dataclass(frozen=True, slots=True)
class TransformationResult:
    """Represent transformed data and transformation metrics."""

    data: pd.DataFrame
    metrics: dict[str, int | float]


def _validate_frame(
    frame: pd.DataFrame,
    required_columns: Iterable[str],
) -> None:
    """Validate the input DataFrame and required columns."""
    if not isinstance(frame, pd.DataFrame):
        raise TransformationError(
            "frame must be a pandas DataFrame."
        )

    missing = [
        column
        for column in required_columns
        if column not in frame.columns
    ]

    if missing:
        raise TransformationError(
            "Input DataFrame is missing required columns: "
            + ", ".join(missing)
        )


def filter_valid_records(
    frame: pd.DataFrame,
    *,
    required_columns: Iterable[str] = (),
) -> pd.DataFrame:
    """Remove rows with missing values in business-critical columns."""
    _validate_frame(
        frame,
        required_columns,
    )

    result = frame.copy()

    if not required_columns:
        return result.reset_index(drop=True)

    mask = result[list(required_columns)].notna().all(axis=1)

    return result.loc[mask].reset_index(drop=True)


def add_numeric_metrics(
    frame: pd.DataFrame,
    *,
    value_column: str,
    quantity_column: str | None = None,
    output_column: str = "value",
) -> pd.DataFrame:
    """Add a derived numeric metric using vectorized arithmetic."""
    required_columns = [value_column]

    if quantity_column is not None:
        required_columns.append(quantity_column)

    _validate_frame(
        frame,
        required_columns,
    )

    result = frame.copy()

    values = pd.to_numeric(
        result[value_column],
        errors="coerce",
    )

    if quantity_column is None:
        result[output_column] = values
        return result

    quantities = pd.to_numeric(
        result[quantity_column],
        errors="coerce",
    )

    result[output_column] = values * quantities
    return result


def add_datetime_features(
    frame: pd.DataFrame,
    *,
    timestamp_column: str,
    prefix: str = "event",
) -> pd.DataFrame:
    """Derive calendar attributes from a timestamp column."""
    _validate_frame(
        frame,
        [timestamp_column],
    )

    result = frame.copy()

    timestamps = pd.to_datetime(
        result[timestamp_column],
        errors="coerce",
        utc=True,
    )

    if timestamps.isna().all() and not result.empty:
        raise TransformationError(
            f"Column '{timestamp_column}' contains no valid timestamps."
        )

    result[f"{prefix}_date"] = timestamps.dt.date
    result[f"{prefix}_year"] = timestamps.dt.year.astype("Int64")
    result[f"{prefix}_month"] = timestamps.dt.month.astype("Int64")
    result[f"{prefix}_quarter"] = timestamps.dt.quarter.astype("Int64")
    result[f"{prefix}_day_of_week"] = (
        timestamps.dt.dayofweek.astype("Int64")
    )

    return result


def add_status_flags(
    frame: pd.DataFrame,
    *,
    status_column: str = "status",
    completed_status: str = "completed",
    cancelled_status: str = "cancelled",
) -> pd.DataFrame:
    """Add boolean lifecycle flags from a status column."""
    _validate_frame(
        frame,
        [status_column],
    )

    result = frame.copy()

    statuses = (
        result[status_column]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    result["is_completed"] = statuses.eq(
        completed_status.strip().lower()
    )
    result["is_cancelled"] = statuses.eq(
        cancelled_status.strip().lower()
    )
    result["is_active"] = ~result["is_cancelled"]

    return result


def calculate_percentage(
    numerator: pd.Series,
    denominator: pd.Series,
) -> pd.Series:
    """Calculate percentages while safely handling zero denominators."""
    if not isinstance(numerator, pd.Series):
        raise TransformationError(
            "numerator must be a pandas Series."
        )

    if not isinstance(denominator, pd.Series):
        raise TransformationError(
            "denominator must be a pandas Series."
        )

    if len(numerator) != len(denominator):
        raise TransformationError(
            "numerator and denominator must have the same length."
        )

    denominator_numeric = pd.to_numeric(
        denominator,
        errors="coerce",
    )
    numerator_numeric = pd.to_numeric(
        numerator,
        errors="coerce",
    )

    result = numerator_numeric.div(
        denominator_numeric.where(
            denominator_numeric.ne(0)
        )
    )

    return result.mul(100.0)


def aggregate_by_dimension(
    frame: pd.DataFrame,
    *,
    dimension_columns: Iterable[str],
    value_column: str,
    aggregation: str = "sum",
) -> pd.DataFrame:
    """Aggregate numeric data by one or more dimensions."""
    dimensions = tuple(dimension_columns)

    _validate_frame(
        frame,
        [*dimensions, value_column],
    )

    if not dimensions:
        raise TransformationError(
            "At least one dimension column is required."
        )

    supported_aggregations = {
        "sum",
        "mean",
        "min",
        "max",
        "count",
        "median",
    }

    if aggregation not in supported_aggregations:
        raise TransformationError(
            "Unsupported aggregation. Expected one of: "
            + ", ".join(sorted(supported_aggregations))
        )

    result = frame.copy()
    result[value_column] = pd.to_numeric(
        result[value_column],
        errors="coerce",
    )

    grouped = (
        result.groupby(
            list(dimensions),
            as_index=False,
            dropna=False,
        )[value_column]
        .agg(aggregation)
        .rename(
            columns={
                value_column: f"{value_column}_{aggregation}",
            }
        )
    )

    return grouped.reset_index(drop=True)


def deduplicate_records(
    frame: pd.DataFrame,
    *,
    key_columns: Iterable[str],
    sort_by: str | None = None,
    keep: str = "last",
) -> pd.DataFrame:
    """Deduplicate records using explicit business keys."""
    keys = tuple(key_columns)

    _validate_frame(
        frame,
        keys,
    )

    if not keys:
        raise TransformationError(
            "At least one key column is required."
        )

    if keep not in {"first", "last", False}:
        raise TransformationError(
            "keep must be 'first', 'last', or False."
        )

    result = frame.copy()

    if sort_by is not None:
        _validate_frame(
            result,
            [sort_by],
        )
        result = result.sort_values(
            by=sort_by,
            kind="mergesort",
        )

    return (
        result.drop_duplicates(
            subset=list(keys),
            keep=keep,
        )
        .reset_index(drop=True)
    )


def transform_records(
    frame: pd.DataFrame,
    *,
    id_columns: Iterable[str] = (),
    timestamp_column: str | None = None,
    status_column: str | None = None,
    numeric_column: str | None = None,
    dimension_columns: Iterable[str] = (),
    aggregation: str = "sum",
) -> TransformationResult:
    """Run the standard API-to-analytics transformation workflow."""
    if not isinstance(frame, pd.DataFrame):
        raise TransformationError(
            "frame must be a pandas DataFrame."
        )

    result = frame.copy()

    result = filter_valid_records(
        result,
        required_columns=id_columns,
    )

    if id_columns:
        result = deduplicate_records(
            result,
            key_columns=id_columns,
        )

    if timestamp_column is not None:
        result = add_datetime_features(
            result,
            timestamp_column=timestamp_column,
        )

    if status_column is not None:
        result = add_status_flags(
            result,
            status_column=status_column,
        )

    if numeric_column is not None:
        numeric_values = pd.to_numeric(
            result[numeric_column],
            errors="coerce",
        )

        if numeric_values.isna().all() and not result.empty:
            raise TransformationError(
                f"Column '{numeric_column}' does not contain valid numeric values."
            )

        result[numeric_column] = numeric_values

    metrics: dict[str, int | float] = {
        "input_rows": len(frame),
        "output_rows": len(result),
        "rows_removed": len(frame) - len(result),
    }

    if numeric_column is not None:
        metrics["numeric_total"] = float(
            result[numeric_column].sum()
        )

    if dimension_columns and numeric_column is not None:
        aggregated = aggregate_by_dimension(
            result,
            dimension_columns=dimension_columns,
            value_column=numeric_column,
            aggregation=aggregation,
        )
        metrics["aggregation_rows"] = len(aggregated)

    return TransformationResult(
        data=result,
        metrics=metrics,
    )


__all__ = [
    "TransformationError",
    "TransformationResult",
    "add_datetime_features",
    "add_numeric_metrics",
    "add_status_flags",
    "aggregate_by_dimension",
    "calculate_percentage",
    "deduplicate_records",
    "filter_valid_records",
    "transform_records",
]

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import pandas as pd


class TransformationError(ValueError):
    """Raised when normalized API data cannot be transformed safely."""


@dataclass(frozen=True, slots=True)
class TransformationResult:
    """Represent transformed data and transformation metrics."""

    data: pd.DataFrame
    metrics: dict[str, int | float]


def _validate_frame(
    frame: pd.DataFrame,
    required_columns: Iterable[str],
) -> None:
    """Validate the input DataFrame and required columns."""
    if not isinstance(frame, pd.DataFrame):
        raise TransformationError(
            "frame must be a pandas DataFrame."
        )

    missing = [
        column
        for column in required_columns
        if column not in frame.columns
    ]

    if missing:
        raise TransformationError(
            "Input DataFrame is missing required columns: "
            + ", ".join(missing)
        )


def filter_valid_records(
    frame: pd.DataFrame,
    *,
    required_columns: Iterable[str] = (),
) -> pd.DataFrame:
    """Remove rows with missing values in business-critical columns."""
    _validate_frame(
        frame,
        required_columns,
    )

    result = frame.copy()

    if not required_columns:
        return result.reset_index(drop=True)

    mask = result[list(required_columns)].notna().all(axis=1)

    return result.loc[mask].reset_index(drop=True)


def add_numeric_metrics(
    frame: pd.DataFrame,
    *,
    value_column: str,
    quantity_column: str | None = None,
    output_column: str = "value",
) -> pd.DataFrame:
    """Add a derived numeric metric using vectorized arithmetic."""
    required_columns = [value_column]

    if quantity_column is not None:
        required_columns.append(quantity_column)

    _validate_frame(
        frame,
        required_columns,
    )

    result = frame.copy()

    values = pd.to_numeric(
        result[value_column],
        errors="coerce",
    )

    if quantity_column is None:
        result[output_column] = values
        return result

    quantities = pd.to_numeric(
        result[quantity_column],
        errors="coerce",
    )

    result[output_column] = values * quantities
    return result


def add_datetime_features(
    frame: pd.DataFrame,
    *,
    timestamp_column: str,
    prefix: str = "event",
) -> pd.DataFrame:
    """Derive calendar attributes from a timestamp column."""
    _validate_frame(
        frame,
        [timestamp_column],
    )

    result = frame.copy()

    timestamps = pd.to_datetime(
        result[timestamp_column],
        errors="coerce",
        utc=True,
    )

    if timestamps.isna().all() and not result.empty:
        raise TransformationError(
            f"Column '{timestamp_column}' contains no valid timestamps."
        )

    result[f"{prefix}_date"] = timestamps.dt.date
    result[f"{prefix}_year"] = timestamps.dt.year.astype("Int64")
    result[f"{prefix}_month"] = timestamps.dt.month.astype("Int64")
    result[f"{prefix}_quarter"] = timestamps.dt.quarter.astype("Int64")
    result[f"{prefix}_day_of_week"] = (
        timestamps.dt.dayofweek.astype("Int64")
    )

    return result


def add_status_flags(
    frame: pd.DataFrame,
    *,
    status_column: str = "status",
    completed_status: str = "completed",
    cancelled_status: str = "cancelled",
) -> pd.DataFrame:
    """Add boolean lifecycle flags from a status column."""
    _validate_frame(
        frame,
        [status_column],
    )

    result = frame.copy()

    statuses = (
        result[status_column]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    result["is_completed"] = statuses.eq(
        completed_status.strip().lower()
    )
    result["is_cancelled"] = statuses.eq(
        cancelled_status.strip().lower()
    )
    result["is_active"] = ~result["is_cancelled"]

    return result


def calculate_percentage(
    numerator: pd.Series,
    denominator: pd.Series,
) -> pd.Series:
    """Calculate percentages while safely handling zero denominators."""
    if not isinstance(numerator, pd.Series):
        raise TransformationError(
            "numerator must be a pandas Series."
        )

    if not isinstance(denominator, pd.Series):
        raise TransformationError(
            "denominator must be a pandas Series."
        )

    if len(numerator) != len(denominator):
        raise TransformationError(
            "numerator and denominator must have the same length."
        )

    denominator_numeric = pd.to_numeric(
        denominator,
        errors="coerce",
    )
    numerator_numeric = pd.to_numeric(
        numerator,
        errors="coerce",
    )

    result = numerator_numeric.div(
        denominator_numeric.where(
            denominator_numeric.ne(0)
        )
    )

    return result.mul(100.0)


def aggregate_by_dimension(
    frame: pd.DataFrame,
    *,
    dimension_columns: Iterable[str],
    value_column: str,
    aggregation: str = "sum",
) -> pd.DataFrame:
    """Aggregate numeric data by one or more dimensions."""
    dimensions = tuple(dimension_columns)

    _validate_frame(
        frame,
        [*dimensions, value_column],
    )

    if not dimensions:
        raise TransformationError(
            "At least one dimension column is required."
        )

    supported_aggregations = {
        "sum",
        "mean",
        "min",
        "max",
        "count",
        "median",
    }

    if aggregation not in supported_aggregations:
        raise TransformationError(
            "Unsupported aggregation. Expected one of: "
            + ", ".join(sorted(supported_aggregations))
        )

    result = frame.copy()
    result[value_column] = pd.to_numeric(
        result[value_column],
        errors="coerce",
    )

    grouped = (
        result.groupby(
            list(dimensions),
            as_index=False,
            dropna=False,
        )[value_column]
        .agg(aggregation)
        .rename(
            columns={
                value_column: f"{value_column}_{aggregation}",
            }
        )
    )

    return grouped.reset_index(drop=True)


def deduplicate_records(
    frame: pd.DataFrame,
    *,
    key_columns: Iterable[str],
    sort_by: str | None = None,
    keep: str = "last",
) -> pd.DataFrame:
    """Deduplicate records using explicit business keys."""
    keys = tuple(key_columns)

    _validate_frame(
        frame,
        keys,
    )

    if not keys:
        raise TransformationError(
            "At least one key column is required."
        )

    if keep not in {"first", "last", False}:
        raise TransformationError(
            "keep must be 'first', 'last', or False."
        )

    result = frame.copy()

    if sort_by is not None:
        _validate_frame(
            result,
            [sort_by],
        )
        result = result.sort_values(
            by=sort_by,
            kind="mergesort",
        )

    return (
        result.drop_duplicates(
            subset=list(keys),
            keep=keep,
        )
        .reset_index(drop=True)
    )


def transform_records(
    frame: pd.DataFrame,
    *,
    id_columns: Iterable[str] = (),
    timestamp_column: str | None = None,
    status_column: str | None = None,
    numeric_column: str | None = None,
    dimension_columns: Iterable[str] = (),
    aggregation: str = "sum",
) -> TransformationResult:
    """Run the standard API-to-analytics transformation workflow."""
    if not isinstance(frame, pd.DataFrame):
        raise TransformationError(
            "frame must be a pandas DataFrame."
        )

    result = frame.copy()

    result = filter_valid_records(
        result,
        required_columns=id_columns,
    )

    if id_columns:
        result = deduplicate_records(
            result,
            key_columns=id_columns,
        )

    if timestamp_column is not None:
        result = add_datetime_features(
            result,
            timestamp_column=timestamp_column,
        )

    if status_column is not None:
        result = add_status_flags(
            result,
            status_column=status_column,
        )

    if numeric_column is not None:
        numeric_values = pd.to_numeric(
            result[numeric_column],
            errors="coerce",
        )

        if numeric_values.isna().all() and not result.empty:
            raise TransformationError(
                f"Column '{numeric_column}' does not contain valid numeric values."
            )

        result[numeric_column] = numeric_values

    metrics: dict[str, int | float] = {
        "input_rows": len(frame),
        "output_rows": len(result),
        "rows_removed": len(frame) - len(result),
    }

    if numeric_column is not None:
        metrics["numeric_total"] = float(
            result[numeric_column].sum()
        )

    if dimension_columns and numeric_column is not None:
        aggregated = aggregate_by_dimension(
            result,
            dimension_columns=dimension_columns,
            value_column=numeric_column,
            aggregation=aggregation,
        )
        metrics["aggregation_rows"] = len(aggregated)

    return TransformationResult(
        data=result,
        metrics=metrics,
    )


__all__ = [
    "TransformationError",
    "TransformationResult",
    "add_datetime_features",
    "add_numeric_metrics",
    "add_status_flags",
    "aggregate_by_dimension",
    "calculate_percentage",
    "deduplicate_records",
    "filter_valid_records",
    "transform_records",
]