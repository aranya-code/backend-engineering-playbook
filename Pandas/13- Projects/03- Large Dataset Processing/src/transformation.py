from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd

from .config import PipelineConfig, config


class TransformationError(ValueError):
    """Raised when a dataset transformation cannot be completed safely."""


def _validate_frame(
    frame: pd.DataFrame,
) -> None:
    """Validate the transformation input."""
    if not isinstance(frame, pd.DataFrame):
        raise TransformationError(
            "frame must be a pandas DataFrame."
        )


def _normalize_column_names(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Normalize column names without modifying the input frame."""
    result = frame.copy()

    result.columns = [
        str(column)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        for column in result.columns
    ]

    return result


def _strip_string_columns(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Strip surrounding whitespace from object/string columns."""
    result = frame.copy()

    for column in result.select_dtypes(
        include=["object", "string"]
    ).columns:
        result[column] = result[column].astype("string").str.strip()

    return result


def _normalize_identifiers(
    frame: pd.DataFrame,
    *,
    identifier_columns: Iterable[str],
) -> pd.DataFrame:
    """Normalize identifiers into stable string representations."""
    result = frame.copy()

    for column in identifier_columns:
        if column not in result.columns:
            continue

        result[column] = (
            result[column]
            .astype("string")
            .str.strip()
        )

    return result


def _normalize_numeric_columns(
    frame: pd.DataFrame,
    *,
    numeric_columns: Iterable[str],
) -> pd.DataFrame:
    """Convert configured numeric columns using safe coercion."""
    result = frame.copy()

    for column in numeric_columns:
        if column not in result.columns:
            continue

        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        )

    return result


def _normalize_datetime_columns(
    frame: pd.DataFrame,
    *,
    timestamp_columns: Iterable[str],
    timezone: str,
) -> pd.DataFrame:
    """Normalize configured timestamp columns to one timezone."""
    result = frame.copy()

    for column in timestamp_columns:
        if column not in result.columns:
            continue

        values = pd.to_datetime(
            result[column],
            errors="coerce",
            utc=True,
        )

        if timezone.upper() != "UTC":
            try:
                values = values.dt.tz_convert(
                    timezone
                )
            except (
                TypeError,
                ValueError,
            ) as exc:
                raise TransformationError(
                    f"Invalid timestamp timezone '{timezone}'."
                ) from exc

        result[column] = values

    return result


def _drop_empty_rows(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Remove rows where every column is missing."""
    if frame.empty:
        return frame.copy()

    return frame.dropna(
        how="all"
    ).reset_index(
        drop=True
    )


def _drop_invalid_required_values(
    frame: pd.DataFrame,
    *,
    required_columns: Iterable[str],
) -> pd.DataFrame:
    """Remove rows missing configured business-critical values."""
    required = tuple(
        column
        for column in required_columns
        if column in frame.columns
    )

    if not required:
        return frame.reset_index(
            drop=True
        )

    mask = frame[list(required)].notna().all(
        axis=1
    )

    for column in required:
        if pd.api.types.is_string_dtype(
            frame[column]
        ):
            mask &= frame[column].fillna("").str.strip().ne("")

    return frame.loc[
        mask
    ].reset_index(
        drop=True
    )


def _coerce_categorical_columns(
    frame: pd.DataFrame,
    *,
    categorical_columns: Iterable[str],
) -> pd.DataFrame:
    """Convert configured low-cardinality columns to categorical dtype."""
    result = frame.copy()

    for column in categorical_columns:
        if column not in result.columns:
            continue

        if result[column].nunique(
            dropna=False
        ) == 0:
            continue

        result[column] = result[column].astype(
            "category"
        )

    return result


def _optimize_numeric_dtypes(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Downcast numeric columns when doing so is safe."""
    result = frame.copy()

    for column in result.select_dtypes(
        include=["integer"]
    ).columns:
        result[column] = pd.to_numeric(
            result[column],
            downcast="integer",
        )

    for column in result.select_dtypes(
        include=["floating"]
    ).columns:
        result[column] = pd.to_numeric(
            result[column],
            downcast="float",
        )

    return result


def _add_datetime_features(
    frame: pd.DataFrame,
    *,
    timestamp_column: str | None,
) -> pd.DataFrame:
    """Add common calendar features when a timestamp is available."""
    if timestamp_column is None:
        return frame.copy()

    if timestamp_column not in frame.columns:
        return frame.copy()

    result = frame.copy()
    timestamps = pd.to_datetime(
        result[timestamp_column],
        errors="coerce",
        utc=True,
    )

    result["event_date"] = timestamps.dt.date
    result["event_year"] = timestamps.dt.year.astype(
        "Int64"
    )
    result["event_month"] = timestamps.dt.month.astype(
        "Int64"
    )
    result["event_quarter"] = timestamps.dt.quarter.astype(
        "Int64"
    )
    result["event_day_of_week"] = timestamps.dt.dayofweek.astype(
        "Int64"
    )

    return result


def _add_value_metrics(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Add a generic row-level value metric from common financial columns."""
    result = frame.copy()

    amount_column = next(
        (
            column
            for column in (
                "amount",
                "total_amount",
                "total",
                "value",
                "revenue",
            )
            if column in result.columns
        ),
        None,
    )

    quantity_column = next(
        (
            column
            for column in (
                "quantity",
                "units",
            )
            if column in result.columns
        ),
        None,
    )

    if amount_column is not None:
        result["numeric_value"] = pd.to_numeric(
            result[amount_column],
            errors="coerce",
        )

        if (
            quantity_column is not None
            and amount_column
            in {
                "price",
                "unit_price",
            }
        ):
            quantity = pd.to_numeric(
                result[quantity_column],
                errors="coerce",
            )
            result["numeric_value"] = (
                result["numeric_value"]
                * quantity
            )

    elif (
        "price" in result.columns
        and quantity_column is not None
    ):
        price = pd.to_numeric(
            result["price"],
            errors="coerce",
        )
        quantity = pd.to_numeric(
            result[quantity_column],
            errors="coerce",
        )
        result["numeric_value"] = (
            price * quantity
        )

    return result


def _deduplicate(
    frame: pd.DataFrame,
    *,
    identifier_columns: Iterable[str],
) -> pd.DataFrame:
    """Drop duplicates using the first available business identifier."""
    result = frame.copy()

    key_column = next(
        (
            column
            for column in identifier_columns
            if column in result.columns
        ),
        None,
    )

    if key_column is None or result.empty:
        return result.reset_index(
            drop=True
        )

    if (
        "updated_at" in result.columns
        and result["updated_at"].notna().any()
    ):
        result = result.sort_values(
            "updated_at",
            kind="stable",
        )

    result = result.drop_duplicates(
        subset=[key_column],
        keep="last",
    )

    return result.reset_index(
        drop=True
    )


def transform_chunk(
    frame: pd.DataFrame,
    *,
    pipeline_config: PipelineConfig = config,
) -> pd.DataFrame:
    """Transform one chunk using vectorized Pandas operations."""
    _validate_frame(frame)

    result = _normalize_column_names(
        frame
    )
    result = _strip_string_columns(
        result
    )
    result = _normalize_identifiers(
        result,
        identifier_columns=(
            column
            for column in pipeline_config.identifier_columns
            if column in result.columns
        ),
    )
    result = _normalize_numeric_columns(
        result,
        numeric_columns=(
            column
            for column in pipeline_config.numeric_columns
            if column in result.columns
        ),
    )
    result = _normalize_datetime_columns(
        result,
        timestamp_columns=(
            column
            for column in pipeline_config.timestamp_columns
            if column in result.columns
        ),
        timezone=pipeline_config.timestamp_timezone,
    )
    result = _drop_empty_rows(
        result
    )
    result = _drop_invalid_required_values(
        result,
        required_columns=pipeline_config.required_columns,
    )

    if pipeline_config.drop_duplicate_records:
        result = _deduplicate(
            result,
            identifier_columns=(
                column
                for column in pipeline_config.identifier_columns
                if column in result.columns
            ),
        )

    result = _add_datetime_features(
        result,
        timestamp_column=(
            pipeline_config.timestamp_columns[0]
            if (
                pipeline_config.timestamp_columns
                and pipeline_config.timestamp_columns[0]
                in result.columns
            )
            else next(
                (
                    column
                    for column in pipeline_config.timestamp_columns
                    if column in result.columns
                ),
                None,
            )
        ),
    )

    result = _add_value_metrics(
        result
    )

    result = _coerce_categorical_columns(
        result,
        categorical_columns=(
            column
            for column in pipeline_config.categorical_columns
            if column in result.columns
        ),
    )

    result = _optimize_numeric_dtypes(
        result
    )

    return result.reset_index(
        drop=True
    )


def filter_rows(
    frame: pd.DataFrame,
    predicate: pd.Series,
) -> pd.DataFrame:
    """Filter rows using a boolean Pandas mask."""
    _validate_frame(frame)

    if not isinstance(
        predicate,
        pd.Series,
    ):
        raise TransformationError(
            "predicate must be a pandas Series."
        )

    if len(predicate) != len(frame):
        raise TransformationError(
            "predicate length must match frame length."
        )

    if not pd.api.types.is_bool_dtype(
        predicate
    ):
        raise TransformationError(
            "predicate must contain boolean values."
        )

    return frame.loc[
        predicate.fillna(False)
    ].reset_index(
        drop=True
    )


def add_ratio_column(
    frame: pd.DataFrame,
    *,
    numerator: str,
    denominator: str,
    output: str,
) -> pd.DataFrame:
    """Add a safely calculated ratio percentage column."""
    _validate_frame(frame)

    missing = [
        column
        for column in (
            numerator,
            denominator,
        )
        if column not in frame.columns
    ]

    if missing:
        raise TransformationError(
            "Missing required columns: "
            + ", ".join(missing)
        )

    result = frame.copy()

    numerator_values = pd.to_numeric(
        result[numerator],
        errors="coerce",
    )
    denominator_values = pd.to_numeric(
        result[denominator],
        errors="coerce",
    )

    denominator_values = denominator_values.mask(
        denominator_values.eq(0)
    )

    result[output] = (
        numerator_values
        .div(denominator_values)
        .mul(100.0)
    )

    return result


def aggregate_chunk(
    frame: pd.DataFrame,
    *,
    dimensions: Iterable[str],
    value_column: str,
    aggregation: str = "sum",
) -> pd.DataFrame:
    """Aggregate a chunk without constructing Python row-level loops."""
    _validate_frame(frame)

    dimensions = tuple(dimensions)

    missing = [
        column
        for column in (
            *dimensions,
            value_column,
        )
        if column not in frame.columns
    ]

    if missing:
        raise TransformationError(
            "Missing required columns: "
            + ", ".join(missing)
        )

    allowed_aggregations = {
        "sum",
        "mean",
        "min",
        "max",
        "count",
    }

    if aggregation not in allowed_aggregations:
        raise TransformationError(
            "Unsupported aggregation. "
            "Expected one of: "
            + ", ".join(
                sorted(allowed_aggregations)
            )
        )

    grouped = (
        frame.groupby(
            list(dimensions),
            dropna=False,
            observed=True,
        )[value_column]
        .agg(aggregation)
        .reset_index()
    )

    return grouped


def summarize_chunk(
    frame: pd.DataFrame,
) -> dict[str, int | float]:
    """Calculate lightweight metrics without retaining an extra DataFrame."""
    _validate_frame(frame)

    numeric_memory = frame.memory_usage(
        index=True,
        deep=True,
    ).sum()

    result: dict[str, int | float] = {
        "rows": int(len(frame)),
        "columns": int(len(frame.columns)),
        "memory_bytes": int(numeric_memory),
    }

    if "numeric_value" in frame.columns:
        values = pd.to_numeric(
            frame["numeric_value"],
            errors="coerce",
        )
        result["numeric_total"] = float(
            values.sum(
                skipna=True
            )
        )

    if "id" in frame.columns:
        result["unique_ids"] = int(
            frame["id"].nunique(
                dropna=True
            )
        )

    return result


def make_transformer(
    pipeline_config: PipelineConfig = config,
) -> Any:
    """Return a transformer compatible with the chunk processor."""
    def transformer(
        frame: pd.DataFrame,
        metadata: Any,
    ) -> pd.DataFrame:
        return transform_chunk(
            frame,
            pipeline_config=pipeline_config,
        )

    return transformer


__all__ = [
    "TransformationError",
    "add_ratio_column",
    "aggregate_chunk",
    "filter_rows",
    "make_transformer",
    "summarize_chunk",
    "transform_chunk",
]

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd

from .config import PipelineConfig, config


class TransformationError(ValueError):
    """Raised when a dataset transformation cannot be completed safely."""


def _validate_frame(
    frame: pd.DataFrame,
) -> None:
    """Validate the transformation input."""
    if not isinstance(frame, pd.DataFrame):
        raise TransformationError(
            "frame must be a pandas DataFrame."
        )


def _normalize_column_names(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Normalize column names without modifying the input frame."""
    result = frame.copy()

    result.columns = [
        str(column)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        for column in result.columns
    ]

    return result


def _strip_string_columns(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Strip surrounding whitespace from object/string columns."""
    result = frame.copy()

    for column in result.select_dtypes(
        include=["object", "string"]
    ).columns:
        result[column] = result[column].astype("string").str.strip()

    return result


def _normalize_identifiers(
    frame: pd.DataFrame,
    *,
    identifier_columns: Iterable[str],
) -> pd.DataFrame:
    """Normalize identifiers into stable string representations."""
    result = frame.copy()

    for column in identifier_columns:
        if column not in result.columns:
            continue

        result[column] = (
            result[column]
            .astype("string")
            .str.strip()
        )

    return result


def _normalize_numeric_columns(
    frame: pd.DataFrame,
    *,
    numeric_columns: Iterable[str],
) -> pd.DataFrame:
    """Convert configured numeric columns using safe coercion."""
    result = frame.copy()

    for column in numeric_columns:
        if column not in result.columns:
            continue

        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        )

    return result


def _normalize_datetime_columns(
    frame: pd.DataFrame,
    *,
    timestamp_columns: Iterable[str],
    timezone: str,
) -> pd.DataFrame:
    """Normalize configured timestamp columns to one timezone."""
    result = frame.copy()

    for column in timestamp_columns:
        if column not in result.columns:
            continue

        values = pd.to_datetime(
            result[column],
            errors="coerce",
            utc=True,
        )

        if timezone.upper() != "UTC":
            try:
                values = values.dt.tz_convert(
                    timezone
                )
            except (
                TypeError,
                ValueError,
            ) as exc:
                raise TransformationError(
                    f"Invalid timestamp timezone '{timezone}'."
                ) from exc

        result[column] = values

    return result


def _drop_empty_rows(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Remove rows where every column is missing."""
    if frame.empty:
        return frame.copy()

    return frame.dropna(
        how="all"
    ).reset_index(
        drop=True
    )


def _drop_invalid_required_values(
    frame: pd.DataFrame,
    *,
    required_columns: Iterable[str],
) -> pd.DataFrame:
    """Remove rows missing configured business-critical values."""
    required = tuple(
        column
        for column in required_columns
        if column in frame.columns
    )

    if not required:
        return frame.reset_index(
            drop=True
        )

    mask = frame[list(required)].notna().all(
        axis=1
    )

    for column in required:
        if pd.api.types.is_string_dtype(
            frame[column]
        ):
            mask &= frame[column].fillna("").str.strip().ne("")

    return frame.loc[
        mask
    ].reset_index(
        drop=True
    )


def _coerce_categorical_columns(
    frame: pd.DataFrame,
    *,
    categorical_columns: Iterable[str],
) -> pd.DataFrame:
    """Convert configured low-cardinality columns to categorical dtype."""
    result = frame.copy()

    for column in categorical_columns:
        if column not in result.columns:
            continue

        if result[column].nunique(
            dropna=False
        ) == 0:
            continue

        result[column] = result[column].astype(
            "category"
        )

    return result


def _optimize_numeric_dtypes(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Downcast numeric columns when doing so is safe."""
    result = frame.copy()

    for column in result.select_dtypes(
        include=["integer"]
    ).columns:
        result[column] = pd.to_numeric(
            result[column],
            downcast="integer",
        )

    for column in result.select_dtypes(
        include=["floating"]
    ).columns:
        result[column] = pd.to_numeric(
            result[column],
            downcast="float",
        )

    return result


def _add_datetime_features(
    frame: pd.DataFrame,
    *,
    timestamp_column: str | None,
) -> pd.DataFrame:
    """Add common calendar features when a timestamp is available."""
    if timestamp_column is None:
        return frame.copy()

    if timestamp_column not in frame.columns:
        return frame.copy()

    result = frame.copy()
    timestamps = pd.to_datetime(
        result[timestamp_column],
        errors="coerce",
        utc=True,
    )

    result["event_date"] = timestamps.dt.date
    result["event_year"] = timestamps.dt.year.astype(
        "Int64"
    )
    result["event_month"] = timestamps.dt.month.astype(
        "Int64"
    )
    result["event_quarter"] = timestamps.dt.quarter.astype(
        "Int64"
    )
    result["event_day_of_week"] = timestamps.dt.dayofweek.astype(
        "Int64"
    )

    return result


def _add_value_metrics(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Add a generic row-level value metric from common financial columns."""
    result = frame.copy()

    amount_column = next(
        (
            column
            for column in (
                "amount",
                "total_amount",
                "total",
                "value",
                "revenue",
            )
            if column in result.columns
        ),
        None,
    )

    quantity_column = next(
        (
            column
            for column in (
                "quantity",
                "units",
            )
            if column in result.columns
        ),
        None,
    )

    if amount_column is not None:
        result["numeric_value"] = pd.to_numeric(
            result[amount_column],
            errors="coerce",
        )

        if (
            quantity_column is not None
            and amount_column
            in {
                "price",
                "unit_price",
            }
        ):
            quantity = pd.to_numeric(
                result[quantity_column],
                errors="coerce",
            )
            result["numeric_value"] = (
                result["numeric_value"]
                * quantity
            )

    elif (
        "price" in result.columns
        and quantity_column is not None
    ):
        price = pd.to_numeric(
            result["price"],
            errors="coerce",
        )
        quantity = pd.to_numeric(
            result[quantity_column],
            errors="coerce",
        )
        result["numeric_value"] = (
            price * quantity
        )

    return result


def _deduplicate(
    frame: pd.DataFrame,
    *,
    identifier_columns: Iterable[str],
) -> pd.DataFrame:
    """Drop duplicates using the first available business identifier."""
    result = frame.copy()

    key_column = next(
        (
            column
            for column in identifier_columns
            if column in result.columns
        ),
        None,
    )

    if key_column is None or result.empty:
        return result.reset_index(
            drop=True
        )

    if (
        "updated_at" in result.columns
        and result["updated_at"].notna().any()
    ):
        result = result.sort_values(
            "updated_at",
            kind="stable",
        )

    result = result.drop_duplicates(
        subset=[key_column],
        keep="last",
    )

    return result.reset_index(
        drop=True
    )


def transform_chunk(
    frame: pd.DataFrame,
    *,
    pipeline_config: PipelineConfig = config,
) -> pd.DataFrame:
    """Transform one chunk using vectorized Pandas operations."""
    _validate_frame(frame)

    result = _normalize_column_names(
        frame
    )
    result = _strip_string_columns(
        result
    )
    result = _normalize_identifiers(
        result,
        identifier_columns=(
            column
            for column in pipeline_config.identifier_columns
            if column in result.columns
        ),
    )
    result = _normalize_numeric_columns(
        result,
        numeric_columns=(
            column
            for column in pipeline_config.numeric_columns
            if column in result.columns
        ),
    )
    result = _normalize_datetime_columns(
        result,
        timestamp_columns=(
            column
            for column in pipeline_config.timestamp_columns
            if column in result.columns
        ),
        timezone=pipeline_config.timestamp_timezone,
    )
    result = _drop_empty_rows(
        result
    )
    result = _drop_invalid_required_values(
        result,
        required_columns=pipeline_config.required_columns,
    )

    if pipeline_config.drop_duplicate_records:
        result = _deduplicate(
            result,
            identifier_columns=(
                column
                for column in pipeline_config.identifier_columns
                if column in result.columns
            ),
        )

    result = _add_datetime_features(
        result,
        timestamp_column=(
            pipeline_config.timestamp_columns[0]
            if (
                pipeline_config.timestamp_columns
                and pipeline_config.timestamp_columns[0]
                in result.columns
            )
            else next(
                (
                    column
                    for column in pipeline_config.timestamp_columns
                    if column in result.columns
                ),
                None,
            )
        ),
    )

    result = _add_value_metrics(
        result
    )

    result = _coerce_categorical_columns(
        result,
        categorical_columns=(
            column
            for column in pipeline_config.categorical_columns
            if column in result.columns
        ),
    )

    result = _optimize_numeric_dtypes(
        result
    )

    return result.reset_index(
        drop=True
    )


def filter_rows(
    frame: pd.DataFrame,
    predicate: pd.Series,
) -> pd.DataFrame:
    """Filter rows using a boolean Pandas mask."""
    _validate_frame(frame)

    if not isinstance(
        predicate,
        pd.Series,
    ):
        raise TransformationError(
            "predicate must be a pandas Series."
        )

    if len(predicate) != len(frame):
        raise TransformationError(
            "predicate length must match frame length."
        )

    if not pd.api.types.is_bool_dtype(
        predicate
    ):
        raise TransformationError(
            "predicate must contain boolean values."
        )

    return frame.loc[
        predicate.fillna(False)
    ].reset_index(
        drop=True
    )


def add_ratio_column(
    frame: pd.DataFrame,
    *,
    numerator: str,
    denominator: str,
    output: str,
) -> pd.DataFrame:
    """Add a safely calculated ratio percentage column."""
    _validate_frame(frame)

    missing = [
        column
        for column in (
            numerator,
            denominator,
        )
        if column not in frame.columns
    ]

    if missing:
        raise TransformationError(
            "Missing required columns: "
            + ", ".join(missing)
        )

    result = frame.copy()

    numerator_values = pd.to_numeric(
        result[numerator],
        errors="coerce",
    )
    denominator_values = pd.to_numeric(
        result[denominator],
        errors="coerce",
    )

    denominator_values = denominator_values.mask(
        denominator_values.eq(0)
    )

    result[output] = (
        numerator_values
        .div(denominator_values)
        .mul(100.0)
    )

    return result


def aggregate_chunk(
    frame: pd.DataFrame,
    *,
    dimensions: Iterable[str],
    value_column: str,
    aggregation: str = "sum",
) -> pd.DataFrame:
    """Aggregate a chunk without constructing Python row-level loops."""
    _validate_frame(frame)

    dimensions = tuple(dimensions)

    missing = [
        column
        for column in (
            *dimensions,
            value_column,
        )
        if column not in frame.columns
    ]

    if missing:
        raise TransformationError(
            "Missing required columns: "
            + ", ".join(missing)
        )

    allowed_aggregations = {
        "sum",
        "mean",
        "min",
        "max",
        "count",
    }

    if aggregation not in allowed_aggregations:
        raise TransformationError(
            "Unsupported aggregation. "
            "Expected one of: "
            + ", ".join(
                sorted(allowed_aggregations)
            )
        )

    grouped = (
        frame.groupby(
            list(dimensions),
            dropna=False,
            observed=True,
        )[value_column]
        .agg(aggregation)
        .reset_index()
    )

    return grouped


def summarize_chunk(
    frame: pd.DataFrame,
) -> dict[str, int | float]:
    """Calculate lightweight metrics without retaining an extra DataFrame."""
    _validate_frame(frame)

    numeric_memory = frame.memory_usage(
        index=True,
        deep=True,
    ).sum()

    result: dict[str, int | float] = {
        "rows": int(len(frame)),
        "columns": int(len(frame.columns)),
        "memory_bytes": int(numeric_memory),
    }

    if "numeric_value" in frame.columns:
        values = pd.to_numeric(
            frame["numeric_value"],
            errors="coerce",
        )
        result["numeric_total"] = float(
            values.sum(
                skipna=True
            )
        )

    if "id" in frame.columns:
        result["unique_ids"] = int(
            frame["id"].nunique(
                dropna=True
            )
        )

    return result


def make_transformer(
    pipeline_config: PipelineConfig = config,
) -> Any:
    """Return a transformer compatible with the chunk processor."""
    def transformer(
        frame: pd.DataFrame,
        metadata: Any,
    ) -> pd.DataFrame:
        return transform_chunk(
            frame,
            pipeline_config=pipeline_config,
        )

    return transformer


__all__ = [
    "TransformationError",
    "add_ratio_column",
    "aggregate_chunk",
    "filter_rows",
    "make_transformer",
    "summarize_chunk",
    "transform_chunk",
]