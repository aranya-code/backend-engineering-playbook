from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import pandas as pd


class CleaningError(ValueError):
    """Raised when an order dataset cannot be cleaned safely."""


ORDER_COLUMNS = (
    "order_id",
    "customer_id",
    "product_id",
    "status",
    "amount",
    "created_at",
    "updated_at",
)

VALID_ORDER_STATUSES = frozenset(
    {
        "pending",
        "completed",
        "cancelled",
    }
)


@dataclass(frozen=True, slots=True)
class CleaningResult:
    """Result of cleaning an order dataset."""

    cleaned: pd.DataFrame
    rejected: pd.DataFrame


def _validate_columns(
    frame: pd.DataFrame,
    required_columns: Iterable[str],
) -> None:
    """Validate that all required columns are present."""
    missing = [
        column
        for column in required_columns
        if column not in frame.columns
    ]

    if missing:
        raise CleaningError(
            "Missing required columns: "
            + ", ".join(missing)
        )


def _empty_cleaned_frame() -> pd.DataFrame:
    """Return an empty DataFrame with the normalized order schema."""
    return pd.DataFrame(
        {
            "order_id": pd.Series(dtype="string"),
            "customer_id": pd.Series(dtype="string"),
            "product_id": pd.Series(dtype="string"),
            "status": pd.Series(dtype="string"),
            "amount": pd.Series(dtype="float64"),
            "created_at": pd.Series(
                dtype="datetime64[ns, UTC]"
            ),
            "updated_at": pd.Series(
                dtype="datetime64[ns, UTC]"
            ),
        }
    )


def _empty_rejected_frame(
    columns: Iterable[str],
) -> pd.DataFrame:
    """Return an empty DataFrame for rejected records."""
    return pd.DataFrame(
        columns=list(columns),
    )


def _normalize_strings(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Normalize identifier and status string fields."""
    normalized = frame.copy()

    for column in (
        "order_id",
        "customer_id",
        "product_id",
    ):
        normalized[column] = (
            normalized[column]
            .astype("string")
            .str.strip()
        )

    normalized["status"] = (
        normalized["status"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    return normalized


def _normalize_types(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Normalize numeric and timestamp fields."""
    normalized = frame.copy()

    normalized["amount"] = pd.to_numeric(
        normalized["amount"],
        errors="coerce",
    )

    normalized["created_at"] = pd.to_datetime(
        normalized["created_at"],
        errors="coerce",
        utc=True,
    )

    normalized["updated_at"] = pd.to_datetime(
        normalized["updated_at"],
        errors="coerce",
        utc=True,
    )

    return normalized


def _build_rejection_mask(
    frame: pd.DataFrame,
) -> pd.Series:
    """Build a vectorized mask for invalid order records."""
    required_nulls = frame[
        [
            "order_id",
            "customer_id",
            "product_id",
            "status",
            "amount",
            "created_at",
            "updated_at",
        ]
    ].isna().any(axis=1)

    invalid_status = ~frame["status"].isin(
        VALID_ORDER_STATUSES,
    )

    negative_amount = frame["amount"].lt(0)

    invalid_timestamp_order = (
        frame["created_at"].notna()
        & frame["updated_at"].notna()
        & frame["updated_at"].lt(frame["created_at"])
    )

    return (
        required_nulls
        | invalid_status
        | negative_amount
        | invalid_timestamp_order
    )


def clean_orders(
    orders: pd.DataFrame,
) -> CleaningResult:
    """Clean, validate, and deduplicate order records.

    Invalid records are separated into ``rejected``. When an order ID
    occurs more than once, the record with the latest ``updated_at``
    timestamp is retained.
    """
    if not isinstance(orders, pd.DataFrame):
        raise CleaningError(
            "orders must be a pandas DataFrame"
        )

    _validate_columns(
        orders,
        ORDER_COLUMNS,
    )

    if orders.empty:
        return CleaningResult(
            cleaned=_empty_cleaned_frame(),
            rejected=_empty_rejected_frame(
                orders.columns,
            ),
        )

    normalized = _normalize_strings(orders)
    normalized = _normalize_types(normalized)

    rejection_mask = _build_rejection_mask(
        normalized,
    )

    rejected = normalized.loc[
        rejection_mask
    ].copy()

    cleaned = normalized.loc[
        ~rejection_mask
    ].copy()

    if cleaned.empty:
        return CleaningResult(
            cleaned=_empty_cleaned_frame(),
            rejected=rejected.reset_index(
                drop=True,
            ),
        )

    cleaned = (
        cleaned
        .sort_values(
            by=[
                "order_id",
                "updated_at",
            ],
            ascending=[
                True,
                True,
            ],
            kind="mergesort",
        )
        .drop_duplicates(
            subset=["order_id"],
            keep="last",
        )
        .sort_values(
            by="order_id",
            kind="mergesort",
        )
        .reset_index(drop=True)
    )

    return CleaningResult(
        cleaned=cleaned,
        rejected=rejected.reset_index(
            drop=True,
        ),
    )


def clean_order_chunks(
    chunks: Iterable[pd.DataFrame],
) -> CleaningResult:
    """Clean multiple order chunks and deduplicate across chunk boundaries."""
    cleaned_frames: list[pd.DataFrame] = []
    rejected_frames: list[pd.DataFrame] = []

    for chunk in chunks:
        result = clean_orders(chunk)

        if not result.cleaned.empty:
            cleaned_frames.append(result.cleaned)

        if not result.rejected.empty:
            rejected_frames.append(result.rejected)

    if cleaned_frames:
        cleaned = pd.concat(
            cleaned_frames,
            ignore_index=True,
        )

        cleaned = (
            cleaned
            .sort_values(
                by=[
                    "order_id",
                    "updated_at",
                ],
                ascending=[
                    True,
                    True,
                ],
                kind="mergesort",
            )
            .drop_duplicates(
                subset=["order_id"],
                keep="last",
            )
            .sort_values(
                by="order_id",
                kind="mergesort",
            )
            .reset_index(drop=True)
        )
    else:
        cleaned = _empty_cleaned_frame()

    if rejected_frames:
        rejected = pd.concat(
            rejected_frames,
            ignore_index=True,
        )
    else:
        rejected = _empty_rejected_frame(
            ORDER_COLUMNS,
        )

    return CleaningResult(
        cleaned=cleaned,
        rejected=rejected.reset_index(
            drop=True,
        ),
    )


__all__ = [
    "CleaningError",
    "CleaningResult",
    "ORDER_COLUMNS",
    "VALID_ORDER_STATUSES",
    "clean_order_chunks",
    "clean_orders",
]

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import pandas as pd


class CleaningError(ValueError):
    """Raised when an order dataset cannot be cleaned safely."""


ORDER_COLUMNS = (
    "order_id",
    "customer_id",
    "product_id",
    "status",
    "amount",
    "created_at",
    "updated_at",
)

VALID_ORDER_STATUSES = frozenset(
    {
        "pending",
        "completed",
        "cancelled",
    }
)


@dataclass(frozen=True, slots=True)
class CleaningResult:
    """Result of cleaning an order dataset."""

    cleaned: pd.DataFrame
    rejected: pd.DataFrame


def _validate_columns(
    frame: pd.DataFrame,
    required_columns: Iterable[str],
) -> None:
    """Validate that all required columns are present."""
    missing = [
        column
        for column in required_columns
        if column not in frame.columns
    ]

    if missing:
        raise CleaningError(
            "Missing required columns: "
            + ", ".join(missing)
        )


def _empty_cleaned_frame() -> pd.DataFrame:
    """Return an empty DataFrame with the normalized order schema."""
    return pd.DataFrame(
        {
            "order_id": pd.Series(dtype="string"),
            "customer_id": pd.Series(dtype="string"),
            "product_id": pd.Series(dtype="string"),
            "status": pd.Series(dtype="string"),
            "amount": pd.Series(dtype="float64"),
            "created_at": pd.Series(
                dtype="datetime64[ns, UTC]"
            ),
            "updated_at": pd.Series(
                dtype="datetime64[ns, UTC]"
            ),
        }
    )


def _empty_rejected_frame(
    columns: Iterable[str],
) -> pd.DataFrame:
    """Return an empty DataFrame for rejected records."""
    return pd.DataFrame(
        columns=list(columns),
    )


def _normalize_strings(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Normalize identifier and status string fields."""
    normalized = frame.copy()

    for column in (
        "order_id",
        "customer_id",
        "product_id",
    ):
        normalized[column] = (
            normalized[column]
            .astype("string")
            .str.strip()
        )

    normalized["status"] = (
        normalized["status"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    return normalized


def _normalize_types(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Normalize numeric and timestamp fields."""
    normalized = frame.copy()

    normalized["amount"] = pd.to_numeric(
        normalized["amount"],
        errors="coerce",
    )

    normalized["created_at"] = pd.to_datetime(
        normalized["created_at"],
        errors="coerce",
        utc=True,
    )

    normalized["updated_at"] = pd.to_datetime(
        normalized["updated_at"],
        errors="coerce",
        utc=True,
    )

    return normalized


def _build_rejection_mask(
    frame: pd.DataFrame,
) -> pd.Series:
    """Build a vectorized mask for invalid order records."""
    required_nulls = frame[
        [
            "order_id",
            "customer_id",
            "product_id",
            "status",
            "amount",
            "created_at",
            "updated_at",
        ]
    ].isna().any(axis=1)

    invalid_status = ~frame["status"].isin(
        VALID_ORDER_STATUSES,
    )

    negative_amount = frame["amount"].lt(0)

    invalid_timestamp_order = (
        frame["created_at"].notna()
        & frame["updated_at"].notna()
        & frame["updated_at"].lt(frame["created_at"])
    )

    return (
        required_nulls
        | invalid_status
        | negative_amount
        | invalid_timestamp_order
    )


def clean_orders(
    orders: pd.DataFrame,
) -> CleaningResult:
    """Clean, validate, and deduplicate order records.

    Invalid records are separated into ``rejected``. When an order ID
    occurs more than once, the record with the latest ``updated_at``
    timestamp is retained.
    """
    if not isinstance(orders, pd.DataFrame):
        raise CleaningError(
            "orders must be a pandas DataFrame"
        )

    _validate_columns(
        orders,
        ORDER_COLUMNS,
    )

    if orders.empty:
        return CleaningResult(
            cleaned=_empty_cleaned_frame(),
            rejected=_empty_rejected_frame(
                orders.columns,
            ),
        )

    normalized = _normalize_strings(orders)
    normalized = _normalize_types(normalized)

    rejection_mask = _build_rejection_mask(
        normalized,
    )

    rejected = normalized.loc[
        rejection_mask
    ].copy()

    cleaned = normalized.loc[
        ~rejection_mask
    ].copy()

    if cleaned.empty:
        return CleaningResult(
            cleaned=_empty_cleaned_frame(),
            rejected=rejected.reset_index(
                drop=True,
            ),
        )

    cleaned = (
        cleaned
        .sort_values(
            by=[
                "order_id",
                "updated_at",
            ],
            ascending=[
                True,
                True,
            ],
            kind="mergesort",
        )
        .drop_duplicates(
            subset=["order_id"],
            keep="last",
        )
        .sort_values(
            by="order_id",
            kind="mergesort",
        )
        .reset_index(drop=True)
    )

    return CleaningResult(
        cleaned=cleaned,
        rejected=rejected.reset_index(
            drop=True,
        ),
    )


def clean_order_chunks(
    chunks: Iterable[pd.DataFrame],
) -> CleaningResult:
    """Clean multiple order chunks and deduplicate across chunk boundaries."""
    cleaned_frames: list[pd.DataFrame] = []
    rejected_frames: list[pd.DataFrame] = []

    for chunk in chunks:
        result = clean_orders(chunk)

        if not result.cleaned.empty:
            cleaned_frames.append(result.cleaned)

        if not result.rejected.empty:
            rejected_frames.append(result.rejected)

    if cleaned_frames:
        cleaned = pd.concat(
            cleaned_frames,
            ignore_index=True,
        )

        cleaned = (
            cleaned
            .sort_values(
                by=[
                    "order_id",
                    "updated_at",
                ],
                ascending=[
                    True,
                    True,
                ],
                kind="mergesort",
            )
            .drop_duplicates(
                subset=["order_id"],
                keep="last",
            )
            .sort_values(
                by="order_id",
                kind="mergesort",
            )
            .reset_index(drop=True)
        )
    else:
        cleaned = _empty_cleaned_frame()

    if rejected_frames:
        rejected = pd.concat(
            rejected_frames,
            ignore_index=True,
        )
    else:
        rejected = _empty_rejected_frame(
            ORDER_COLUMNS,
        )

    return CleaningResult(
        cleaned=cleaned,
        rejected=rejected.reset_index(
            drop=True,
        ),
    )


__all__ = [
    "CleaningError",
    "CleaningResult",
    "ORDER_COLUMNS",
    "VALID_ORDER_STATUSES",
    "clean_order_chunks",
    "clean_orders",
]