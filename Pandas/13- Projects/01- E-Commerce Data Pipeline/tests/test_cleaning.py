from __future__ import annotations

import pandas as pd
import pytest

from src.cleaning import (
    CleaningError,
    clean_order_chunks,
    clean_orders,
)


def make_orders() -> pd.DataFrame:
    """Build representative order records for cleaning tests."""
    return pd.DataFrame(
        {
            "order_id": [
                " O-1 ",
                "O-2",
                "O-3",
                "O-4",
            ],
            "customer_id": [
                " C-1 ",
                "C-2",
                "C-3",
                "C-4",
            ],
            "product_id": [
                " P-1 ",
                "P-2",
                "P-3",
                "P-4",
            ],
            "status": [
                "COMPLETED",
                " pending ",
                "cancelled",
                "completed",
            ],
            "amount": [
                "100.00",
                "200",
                "50.25",
                "300",
            ],
            "created_at": [
                "2026-01-01T10:00:00Z",
                "2026-01-02T10:00:00Z",
                "2026-01-03T10:00:00Z",
                "2026-01-04T10:00:00Z",
            ],
            "updated_at": [
                "2026-01-01T10:05:00Z",
                "2026-01-02T10:05:00Z",
                "2026-01-03T10:05:00Z",
                "2026-01-04T10:05:00Z",
            ],
        }
    )


def test_clean_orders_normalizes_strings_and_types() -> None:
    result = clean_orders(
        make_orders(),
    )

    cleaned = result.cleaned

    assert cleaned["order_id"].tolist() == [
        "O-1",
        "O-2",
        "O-3",
        "O-4",
    ]
    assert cleaned["customer_id"].tolist() == [
        "C-1",
        "C-2",
        "C-3",
        "C-4",
    ]
    assert cleaned["product_id"].tolist() == [
        "P-1",
        "P-2",
        "P-3",
        "P-4",
    ]
    assert cleaned["status"].tolist() == [
        "completed",
        "pending",
        "cancelled",
        "completed",
    ]
    assert pd.api.types.is_float_dtype(
        cleaned["amount"]
    )
    assert pd.api.types.is_datetime64tz_dtype(
        cleaned["created_at"]
    )
    assert pd.api.types.is_datetime64tz_dtype(
        cleaned["updated_at"]
    )


def test_clean_orders_rejects_missing_required_values() -> None:
    orders = make_orders()
    orders.loc[1, "customer_id"] = None

    result = clean_orders(
        orders,
    )

    assert len(result.cleaned) == 3
    assert len(result.rejected) == 1
    assert result.rejected.loc[0, "order_id"] == "O-2"


@pytest.mark.parametrize(
    "status",
    [
        "shipped",
        "returned",
        "unknown",
        "",
        None,
    ],
)
def test_clean_orders_rejects_invalid_status(
    status: str | None,
) -> None:
    orders = make_orders()
    orders.loc[0, "status"] = status

    result = clean_orders(
        orders,
    )

    assert len(result.cleaned) == 3
    assert len(result.rejected) == 1
    assert result.rejected.loc[0, "order_id"] == "O-1"


def test_clean_orders_rejects_negative_amount() -> None:
    orders = make_orders()
    orders.loc[0, "amount"] = -10

    result = clean_orders(
        orders,
    )

    assert len(result.cleaned) == 3
    assert len(result.rejected) == 1
    assert result.rejected.loc[0, "order_id"] == "O-1"


def test_clean_orders_rejects_non_numeric_amount() -> None:
    orders = make_orders()
    orders.loc[0, "amount"] = "not-a-number"

    result = clean_orders(
        orders,
    )

    assert len(result.cleaned) == 3
    assert len(result.rejected) == 1
    assert result.rejected.loc[0, "order_id"] == "O-1"


def test_clean_orders_rejects_invalid_timestamp_order() -> None:
    orders = make_orders()
    orders.loc[0, "updated_at"] = "2025-12-31T10:05:00Z"

    result = clean_orders(
        orders,
    )

    assert len(result.cleaned) == 3
    assert len(result.rejected) == 1
    assert result.rejected.loc[0, "order_id"] == "O-1"


def test_clean_orders_keeps_latest_duplicate_version() -> None:
    orders = pd.DataFrame(
        {
            "order_id": [
                "O-1",
                "O-1",
            ],
            "customer_id": [
                "C-1",
                "C-1",
            ],
            "product_id": [
                "P-1",
                "P-1",
            ],
            "status": [
                "pending",
                "completed",
            ],
            "amount": [
                "100",
                "150",
            ],
            "created_at": [
                "2026-01-01T10:00:00Z",
                "2026-01-01T10:00:00Z",
            ],
            "updated_at": [
                "2026-01-01T10:05:00Z",
                "2026-01-01T10:10:00Z",
            ],
        }
    )

    result = clean_orders(
        orders,
    )

    assert len(result.cleaned) == 1
    assert result.cleaned.loc[0, "status"] == "completed"
    assert result.cleaned.loc[0, "amount"] == 150.0


def test_clean_orders_keeps_the_latest_record_across_multiple_versions() -> None:
    orders = pd.DataFrame(
        {
            "order_id": [
                "O-1",
                "O-1",
                "O-1",
            ],
            "customer_id": [
                "C-1",
                "C-1",
                "C-1",
            ],
            "product_id": [
                "P-1",
                "P-1",
                "P-1",
            ],
            "status": [
                "pending",
                "completed",
                "cancelled",
            ],
            "amount": [
                "100",
                "200",
                "50",
            ],
            "created_at": [
                "2026-01-01T10:00:00Z",
                "2026-01-01T10:00:00Z",
                "2026-01-01T10:00:00Z",
            ],
            "updated_at": [
                "2026-01-01T10:05:00Z",
                "2026-01-01T10:10:00Z",
                "2026-01-01T10:15:00Z",
            ],
        }
    )

    result = clean_orders(
        orders,
    )

    assert len(result.cleaned) == 1
    assert result.cleaned.loc[0, "status"] == "cancelled"
    assert result.cleaned.loc[0, "amount"] == 50.0


def test_clean_order_chunks_deduplicates_across_chunk_boundaries() -> None:
    first_chunk = pd.DataFrame(
        {
            "order_id": ["O-1", "O-2"],
            "customer_id": ["C-1", "C-2"],
            "product_id": ["P-1", "P-2"],
            "status": ["pending", "completed"],
            "amount": ["100", "200"],
            "created_at": [
                "2026-01-01T10:00:00Z",
                "2026-01-02T10:00:00Z",
            ],
            "updated_at": [
                "2026-01-01T10:05:00Z",
                "2026-01-02T10:05:00Z",
            ],
        }
    )

    second_chunk = pd.DataFrame(
        {
            "order_id": ["O-1", "O-3"],
            "customer_id": ["C-1", "C-3"],
            "product_id": ["P-1", "P-3"],
            "status": ["completed", "completed"],
            "amount": ["150", "300"],
            "created_at": [
                "2026-01-01T10:00:00Z",
                "2026-01-03T10:00:00Z",
            ],
            "updated_at": [
                "2026-01-01T10:15:00Z",
                "2026-01-03T10:05:00Z",
            ],
        }
    )

    result = clean_order_chunks(
        [
            first_chunk,
            second_chunk,
        ]
    )

    assert result.cleaned["order_id"].tolist() == [
        "O-1",
        "O-2",
        "O-3",
    ]
    assert result.cleaned.loc[
        result.cleaned["order_id"].eq("O-1"),
        "status",
    ].item() == "completed"
    assert result.cleaned.loc[
        result.cleaned["order_id"].eq("O-1"),
        "amount",
    ].item() == 150.0


def test_clean_order_chunks_preserves_rejected_records() -> None:
    valid_chunk = make_orders().iloc[:2].copy()

    invalid_chunk = make_orders().iloc[2:3].copy()
    invalid_chunk.loc[invalid_chunk.index[0], "amount"] = -25

    result = clean_order_chunks(
        [
            valid_chunk,
            invalid_chunk,
        ]
    )

    assert len(result.cleaned) == 2
    assert len(result.rejected) == 1
    assert result.rejected.loc[0, "order_id"] == "O-3"


def test_clean_orders_handles_mixed_valid_and_invalid_records() -> None:
    orders = make_orders()

    orders.loc[1, "amount"] = -1
    orders.loc[2, "status"] = "invalid"

    result = clean_orders(
        orders,
    )

    assert result.cleaned["order_id"].tolist() == [
        "O-1",
        "O-4",
    ]
    assert result.rejected["order_id"].tolist() == [
        "O-2",
        "O-3",
    ]


def test_clean_orders_handles_empty_input() -> None:
    orders = pd.DataFrame(
        columns=[
            "order_id",
            "customer_id",
            "product_id",
            "status",
            "amount",
            "created_at",
            "updated_at",
        ]
    )

    result = clean_orders(
        orders,
    )

    assert result.cleaned.empty
    assert result.rejected.empty
    assert list(result.cleaned.columns) == [
        "order_id",
        "customer_id",
        "product_id",
        "status",
        "amount",
        "created_at",
        "updated_at",
    ]


def test_clean_order_chunks_handles_empty_chunk_collection() -> None:
    result = clean_order_chunks(
        [],
    )

    assert result.cleaned.empty
    assert result.rejected.empty
    assert list(result.cleaned.columns) == [
        "order_id",
        "customer_id",
        "product_id",
        "status",
        "amount",
        "created_at",
        "updated_at",
    ]


def test_clean_order_chunks_handles_empty_chunks() -> None:
    empty_orders = pd.DataFrame(
        columns=[
            "order_id",
            "customer_id",
            "product_id",
            "status",
            "amount",
            "created_at",
            "updated_at",
        ]
    )

    result = clean_order_chunks(
        [
            empty_orders,
            empty_orders.copy(),
        ]
    )

    assert result.cleaned.empty
    assert result.rejected.empty


def test_clean_orders_does_not_mutate_input() -> None:
    orders = make_orders()
    original = orders.copy(deep=True)

    clean_orders(
        orders,
    )

    pd.testing.assert_frame_equal(
        orders,
        original,
    )


def test_clean_orders_raises_for_missing_required_columns() -> None:
    orders = make_orders().drop(
        columns=["updated_at"],
    )

    with pytest.raises(
        CleaningError,
        match="Missing required columns",
    ):
        clean_orders(
            orders,
        )


@pytest.mark.parametrize(
    "invalid_column",
    [
        "order_id",
        "customer_id",
        "product_id",
        "status",
        "amount",
        "created_at",
        "updated_at",
    ],
)
def test_clean_orders_rejects_missing_required_column(
    invalid_column: str,
) -> None:
    orders = make_orders().drop(
        columns=[invalid_column],
    )

    with pytest.raises(
        CleaningError,
        match="Missing required columns",
    ):
        clean_orders(
            orders,
        )


def test_clean_orders_rejects_non_dataframe_input() -> None:
    with pytest.raises(
        CleaningError,
        match="must be a pandas DataFrame",
    ):
        clean_orders(  # type: ignore[arg-type]
            [],
        )


def test_clean_order_chunks_rejects_invalid_chunk() -> None:
    with pytest.raises(
        CleaningError,
        match="must be a pandas DataFrame",
    ):
        clean_order_chunks(  # type: ignore[list-item]
            [
                [],
            ]
        )

from __future__ import annotations

import pandas as pd
import pytest

from src.cleaning import (
    CleaningError,
    clean_order_chunks,
    clean_orders,
)


def make_orders() -> pd.DataFrame:
    """Build representative order records for cleaning tests."""
    return pd.DataFrame(
        {
            "order_id": [
                " O-1 ",
                "O-2",
                "O-3",
                "O-4",
            ],
            "customer_id": [
                " C-1 ",
                "C-2",
                "C-3",
                "C-4",
            ],
            "product_id": [
                " P-1 ",
                "P-2",
                "P-3",
                "P-4",
            ],
            "status": [
                "COMPLETED",
                " pending ",
                "cancelled",
                "completed",
            ],
            "amount": [
                "100.00",
                "200",
                "50.25",
                "300",
            ],
            "created_at": [
                "2026-01-01T10:00:00Z",
                "2026-01-02T10:00:00Z",
                "2026-01-03T10:00:00Z",
                "2026-01-04T10:00:00Z",
            ],
            "updated_at": [
                "2026-01-01T10:05:00Z",
                "2026-01-02T10:05:00Z",
                "2026-01-03T10:05:00Z",
                "2026-01-04T10:05:00Z",
            ],
        }
    )


def test_clean_orders_normalizes_strings_and_types() -> None:
    result = clean_orders(
        make_orders(),
    )

    cleaned = result.cleaned

    assert cleaned["order_id"].tolist() == [
        "O-1",
        "O-2",
        "O-3",
        "O-4",
    ]
    assert cleaned["customer_id"].tolist() == [
        "C-1",
        "C-2",
        "C-3",
        "C-4",
    ]
    assert cleaned["product_id"].tolist() == [
        "P-1",
        "P-2",
        "P-3",
        "P-4",
    ]
    assert cleaned["status"].tolist() == [
        "completed",
        "pending",
        "cancelled",
        "completed",
    ]
    assert pd.api.types.is_float_dtype(
        cleaned["amount"]
    )
    assert pd.api.types.is_datetime64tz_dtype(
        cleaned["created_at"]
    )
    assert pd.api.types.is_datetime64tz_dtype(
        cleaned["updated_at"]
    )


def test_clean_orders_rejects_missing_required_values() -> None:
    orders = make_orders()
    orders.loc[1, "customer_id"] = None

    result = clean_orders(
        orders,
    )

    assert len(result.cleaned) == 3
    assert len(result.rejected) == 1
    assert result.rejected.loc[0, "order_id"] == "O-2"


@pytest.mark.parametrize(
    "status",
    [
        "shipped",
        "returned",
        "unknown",
        "",
        None,
    ],
)
def test_clean_orders_rejects_invalid_status(
    status: str | None,
) -> None:
    orders = make_orders()
    orders.loc[0, "status"] = status

    result = clean_orders(
        orders,
    )

    assert len(result.cleaned) == 3
    assert len(result.rejected) == 1
    assert result.rejected.loc[0, "order_id"] == "O-1"


def test_clean_orders_rejects_negative_amount() -> None:
    orders = make_orders()
    orders.loc[0, "amount"] = -10

    result = clean_orders(
        orders,
    )

    assert len(result.cleaned) == 3
    assert len(result.rejected) == 1
    assert result.rejected.loc[0, "order_id"] == "O-1"


def test_clean_orders_rejects_non_numeric_amount() -> None:
    orders = make_orders()
    orders.loc[0, "amount"] = "not-a-number"

    result = clean_orders(
        orders,
    )

    assert len(result.cleaned) == 3
    assert len(result.rejected) == 1
    assert result.rejected.loc[0, "order_id"] == "O-1"


def test_clean_orders_rejects_invalid_timestamp_order() -> None:
    orders = make_orders()
    orders.loc[0, "updated_at"] = "2025-12-31T10:05:00Z"

    result = clean_orders(
        orders,
    )

    assert len(result.cleaned) == 3
    assert len(result.rejected) == 1
    assert result.rejected.loc[0, "order_id"] == "O-1"


def test_clean_orders_keeps_latest_duplicate_version() -> None:
    orders = pd.DataFrame(
        {
            "order_id": [
                "O-1",
                "O-1",
            ],
            "customer_id": [
                "C-1",
                "C-1",
            ],
            "product_id": [
                "P-1",
                "P-1",
            ],
            "status": [
                "pending",
                "completed",
            ],
            "amount": [
                "100",
                "150",
            ],
            "created_at": [
                "2026-01-01T10:00:00Z",
                "2026-01-01T10:00:00Z",
            ],
            "updated_at": [
                "2026-01-01T10:05:00Z",
                "2026-01-01T10:10:00Z",
            ],
        }
    )

    result = clean_orders(
        orders,
    )

    assert len(result.cleaned) == 1
    assert result.cleaned.loc[0, "status"] == "completed"
    assert result.cleaned.loc[0, "amount"] == 150.0


def test_clean_orders_keeps_the_latest_record_across_multiple_versions() -> None:
    orders = pd.DataFrame(
        {
            "order_id": [
                "O-1",
                "O-1",
                "O-1",
            ],
            "customer_id": [
                "C-1",
                "C-1",
                "C-1",
            ],
            "product_id": [
                "P-1",
                "P-1",
                "P-1",
            ],
            "status": [
                "pending",
                "completed",
                "cancelled",
            ],
            "amount": [
                "100",
                "200",
                "50",
            ],
            "created_at": [
                "2026-01-01T10:00:00Z",
                "2026-01-01T10:00:00Z",
                "2026-01-01T10:00:00Z",
            ],
            "updated_at": [
                "2026-01-01T10:05:00Z",
                "2026-01-01T10:10:00Z",
                "2026-01-01T10:15:00Z",
            ],
        }
    )

    result = clean_orders(
        orders,
    )

    assert len(result.cleaned) == 1
    assert result.cleaned.loc[0, "status"] == "cancelled"
    assert result.cleaned.loc[0, "amount"] == 50.0


def test_clean_order_chunks_deduplicates_across_chunk_boundaries() -> None:
    first_chunk = pd.DataFrame(
        {
            "order_id": ["O-1", "O-2"],
            "customer_id": ["C-1", "C-2"],
            "product_id": ["P-1", "P-2"],
            "status": ["pending", "completed"],
            "amount": ["100", "200"],
            "created_at": [
                "2026-01-01T10:00:00Z",
                "2026-01-02T10:00:00Z",
            ],
            "updated_at": [
                "2026-01-01T10:05:00Z",
                "2026-01-02T10:05:00Z",
            ],
        }
    )

    second_chunk = pd.DataFrame(
        {
            "order_id": ["O-1", "O-3"],
            "customer_id": ["C-1", "C-3"],
            "product_id": ["P-1", "P-3"],
            "status": ["completed", "completed"],
            "amount": ["150", "300"],
            "created_at": [
                "2026-01-01T10:00:00Z",
                "2026-01-03T10:00:00Z",
            ],
            "updated_at": [
                "2026-01-01T10:15:00Z",
                "2026-01-03T10:05:00Z",
            ],
        }
    )

    result = clean_order_chunks(
        [
            first_chunk,
            second_chunk,
        ]
    )

    assert result.cleaned["order_id"].tolist() == [
        "O-1",
        "O-2",
        "O-3",
    ]
    assert result.cleaned.loc[
        result.cleaned["order_id"].eq("O-1"),
        "status",
    ].item() == "completed"
    assert result.cleaned.loc[
        result.cleaned["order_id"].eq("O-1"),
        "amount",
    ].item() == 150.0


def test_clean_order_chunks_preserves_rejected_records() -> None:
    valid_chunk = make_orders().iloc[:2].copy()

    invalid_chunk = make_orders().iloc[2:3].copy()
    invalid_chunk.loc[invalid_chunk.index[0], "amount"] = -25

    result = clean_order_chunks(
        [
            valid_chunk,
            invalid_chunk,
        ]
    )

    assert len(result.cleaned) == 2
    assert len(result.rejected) == 1
    assert result.rejected.loc[0, "order_id"] == "O-3"


def test_clean_orders_handles_mixed_valid_and_invalid_records() -> None:
    orders = make_orders()

    orders.loc[1, "amount"] = -1
    orders.loc[2, "status"] = "invalid"

    result = clean_orders(
        orders,
    )

    assert result.cleaned["order_id"].tolist() == [
        "O-1",
        "O-4",
    ]
    assert result.rejected["order_id"].tolist() == [
        "O-2",
        "O-3",
    ]


def test_clean_orders_handles_empty_input() -> None:
    orders = pd.DataFrame(
        columns=[
            "order_id",
            "customer_id",
            "product_id",
            "status",
            "amount",
            "created_at",
            "updated_at",
        ]
    )

    result = clean_orders(
        orders,
    )

    assert result.cleaned.empty
    assert result.rejected.empty
    assert list(result.cleaned.columns) == [
        "order_id",
        "customer_id",
        "product_id",
        "status",
        "amount",
        "created_at",
        "updated_at",
    ]


def test_clean_order_chunks_handles_empty_chunk_collection() -> None:
    result = clean_order_chunks(
        [],
    )

    assert result.cleaned.empty
    assert result.rejected.empty
    assert list(result.cleaned.columns) == [
        "order_id",
        "customer_id",
        "product_id",
        "status",
        "amount",
        "created_at",
        "updated_at",
    ]


def test_clean_order_chunks_handles_empty_chunks() -> None:
    empty_orders = pd.DataFrame(
        columns=[
            "order_id",
            "customer_id",
            "product_id",
            "status",
            "amount",
            "created_at",
            "updated_at",
        ]
    )

    result = clean_order_chunks(
        [
            empty_orders,
            empty_orders.copy(),
        ]
    )

    assert result.cleaned.empty
    assert result.rejected.empty


def test_clean_orders_does_not_mutate_input() -> None:
    orders = make_orders()
    original = orders.copy(deep=True)

    clean_orders(
        orders,
    )

    pd.testing.assert_frame_equal(
        orders,
        original,
    )


def test_clean_orders_raises_for_missing_required_columns() -> None:
    orders = make_orders().drop(
        columns=["updated_at"],
    )

    with pytest.raises(
        CleaningError,
        match="Missing required columns",
    ):
        clean_orders(
            orders,
        )


@pytest.mark.parametrize(
    "invalid_column",
    [
        "order_id",
        "customer_id",
        "product_id",
        "status",
        "amount",
        "created_at",
        "updated_at",
    ],
)
def test_clean_orders_rejects_missing_required_column(
    invalid_column: str,
) -> None:
    orders = make_orders().drop(
        columns=[invalid_column],
    )

    with pytest.raises(
        CleaningError,
        match="Missing required columns",
    ):
        clean_orders(
            orders,
        )


def test_clean_orders_rejects_non_dataframe_input() -> None:
    with pytest.raises(
        CleaningError,
        match="must be a pandas DataFrame",
    ):
        clean_orders(  # type: ignore[arg-type]
            [],
        )


def test_clean_order_chunks_rejects_invalid_chunk() -> None:
    with pytest.raises(
        CleaningError,
        match="must be a pandas DataFrame",
    ):
        clean_order_chunks(  # type: ignore[list-item]
            [
                [],
            ]
        )