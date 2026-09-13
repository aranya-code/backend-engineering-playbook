from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.config import PipelineConfig
from src.normalization import (
    NormalizationError,
    NormalizationResult,
    normalize_api_records,
)


def make_config(
    tmp_path: Path,
    **overrides,
) -> PipelineConfig:
    """Create an isolated pipeline configuration for normalization tests."""
    values = {
        "raw_data_dir": tmp_path / "raw",
        "staging_data_dir": tmp_path / "staging",
        "processed_data_dir": tmp_path / "processed",
        "reports_dir": tmp_path / "reports",
        "api_base_url": "https://api.example.com",
        "api_page_size": 100,
        "api_max_pages": 10,
        "api_timeout_seconds": 30.0,
        "api_connect_timeout_seconds": 10.0,
        "api_read_timeout_seconds": 30.0,
        "api_max_retries": 0,
        "api_backoff_factor": 0.0,
        "api_response_timezone": "UTC",
        "log_level": "CRITICAL",
    }
    values.update(overrides)
    return PipelineConfig(**values)


def test_normalize_api_records_returns_normalization_result(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": "order-1",
                "status": "completed",
                "amount": "125.50",
            }
        ],
        required_columns=("id",),
        numeric_columns=("amount",),
        timezone="UTC",
    )

    assert isinstance(result, NormalizationResult)
    assert isinstance(result.normalized, pd.DataFrame)
    assert isinstance(result.rejected, pd.DataFrame)


def test_normalize_api_records_normalizes_column_names(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "Order ID": "order-1",
                "Customer-ID": "customer-1",
                "Created At": "2026-01-01T10:00:00Z",
            }
        ],
        required_columns=(),
        timestamp_columns=("created_at",),
        timezone="UTC",
    )

    assert list(result.normalized.columns) == [
        "order_id",
        "customer_id",
        "created_at",
    ]


def test_normalize_api_records_strips_string_values(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": "  order-1  ",
                "status": " completed ",
                "customer_id": " customer-42 ",
            }
        ],
        required_columns=("id",),
        timezone="UTC",
    )

    normalized = result.normalized.iloc[0]

    assert normalized["id"] == "order-1"
    assert normalized["status"] == "completed"
    assert normalized["customer_id"] == "customer-42"


def test_normalize_api_records_normalizes_identifier_columns(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": 12345,
                "customer_id": 67890,
                "product_id": 1001,
            }
        ],
        required_columns=(),
        timezone="UTC",
    )

    normalized = result.normalized.iloc[0]

    assert normalized["id"] == "12345"
    assert normalized["customer_id"] == "67890"
    assert normalized["product_id"] == "1001"


def test_normalize_api_records_converts_numeric_columns(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": "order-1",
                "amount": "125.50",
                "quantity": "3",
            },
            {
                "id": "order-2",
                "amount": 50,
                "quantity": 2,
            },
        ],
        required_columns=("id",),
        numeric_columns=("amount", "quantity"),
        timezone="UTC",
    )

    assert pd.api.types.is_numeric_dtype(
        result.normalized["amount"]
    )
    assert pd.api.types.is_numeric_dtype(
        result.normalized["quantity"]
    )
    assert result.normalized["amount"].tolist() == [
        125.5,
        50.0,
    ]
    assert result.normalized["quantity"].tolist() == [
        3.0,
        2.0,
    ]


def test_normalize_api_records_coerces_invalid_numeric_values_to_nan(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": "order-1",
                "amount": "invalid",
            },
            {
                "id": "order-2",
                "amount": "100.25",
            },
        ],
        required_columns=("id",),
        numeric_columns=("amount",),
        timezone="UTC",
    )

    assert pd.isna(
        result.normalized.loc[
            result.normalized["id"] == "order-1",
            "amount",
        ].iloc[0]
    )
    assert (
        result.normalized.loc[
            result.normalized["id"] == "order-2",
            "amount",
        ].iloc[0]
        == 100.25
    )


def test_normalize_api_records_normalizes_utc_timestamps(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": "order-1",
                "created_at": "2026-01-15T10:30:00Z",
            }
        ],
        required_columns=("id",),
        timestamp_columns=("created_at",),
        timezone="UTC",
    )

    timestamp = result.normalized.loc[
        0,
        "created_at",
    ]

    assert timestamp == pd.Timestamp(
        "2026-01-15 10:30:00+00:00"
    )


def test_normalize_api_records_converts_timestamp_to_requested_timezone(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": "order-1",
                "created_at": "2026-01-15T10:30:00Z",
            }
        ],
        required_columns=("id",),
        timestamp_columns=("created_at",),
        timezone="Asia/Kolkata",
    )

    timestamp = result.normalized.loc[
        0,
        "created_at",
    ]

    assert timestamp == pd.Timestamp(
        "2026-01-15 16:00:00+05:30"
    )


def test_normalize_api_records_coerces_invalid_timestamp_to_nat(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": "order-1",
                "created_at": "not-a-timestamp",
            },
            {
                "id": "order-2",
                "created_at": "2026-01-15T10:30:00Z",
            },
        ],
        required_columns=("id",),
        timestamp_columns=("created_at",),
        timezone="UTC",
    )

    timestamps = result.normalized["created_at"]

    assert pd.isna(timestamps.iloc[0])
    assert timestamps.iloc[1] == pd.Timestamp(
        "2026-01-15 10:30:00+00:00"
    )


def test_normalize_api_records_drops_completely_empty_rows(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": "order-1",
                "status": "completed",
            },
            {
                "id": None,
                "status": None,
            },
            {},
        ],
        required_columns=(),
        timezone="UTC",
    )

    assert len(result.normalized) == 1
    assert result.normalized.iloc[0]["id"] == "order-1"


def test_normalize_api_records_rejects_rows_missing_required_columns(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": "order-1",
                "customer_id": "customer-1",
            },
            {
                "id": None,
                "customer_id": "customer-2",
            },
        ],
        required_columns=("id",),
        timezone="UTC",
    )

    assert len(result.normalized) == 1
    assert result.normalized.iloc[0]["id"] == "order-1"

    assert len(result.rejected) == 1
    assert result.rejected.iloc[0]["customer_id"] == "customer-2"


def test_normalize_api_records_preserves_rejected_row_data(
    tmp_path: Path,
) -> None:
    records = [
        {
            "id": "order-1",
            "customer_id": "customer-1",
            "amount": "100",
        },
        {
            "id": None,
            "customer_id": "customer-2",
            "amount": "250",
        },
    ]

    result = normalize_api_records(
        records,
        required_columns=("id",),
        numeric_columns=("amount",),
        timezone="UTC",
    )

    assert len(result.rejected) == 1
    rejected = result.rejected.iloc[0]

    assert pd.isna(rejected["id"])
    assert rejected["customer_id"] == "customer-2"
    assert rejected["amount"] == 250.0


def test_normalize_api_records_handles_empty_input(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [],
        required_columns=("id",),
        timestamp_columns=("created_at",),
        numeric_columns=("amount",),
        timezone="UTC",
    )

    assert isinstance(result.normalized, pd.DataFrame)
    assert isinstance(result.rejected, pd.DataFrame)
    assert result.normalized.empty
    assert result.rejected.empty


def test_normalize_api_records_handles_mapping_records(
    tmp_path: Path,
) -> None:
    records = (
        {
            "id": "order-1",
            "amount": "100.00",
        },
        {
            "id": "order-2",
            "amount": "200.00",
        },
    )

    result = normalize_api_records(
        records,
        required_columns=("id",),
        numeric_columns=("amount",),
        timezone="UTC",
    )

    assert result.normalized["id"].tolist() == [
        "order-1",
        "order-2",
    ]
    assert result.normalized["amount"].tolist() == [
        100.0,
        200.0,
    ]


def test_normalize_api_records_preserves_input_order(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {"id": "order-3"},
            {"id": "order-1"},
            {"id": "order-2"},
        ],
        required_columns=("id",),
        timezone="UTC",
    )

    assert result.normalized["id"].tolist() == [
        "order-3",
        "order-1",
        "order-2",
    ]


def test_normalize_api_records_does_not_mutate_input_records(
    tmp_path: Path,
) -> None:
    records = [
        {
            "id": " order-1 ",
            "amount": "100.00",
        }
    ]

    original = [
        {
            "id": " order-1 ",
            "amount": "100.00",
        }
    ]

    normalize_api_records(
        records,
        required_columns=("id",),
        numeric_columns=("amount",),
        timezone="UTC",
    )

    assert records == original


def test_normalize_api_records_normalizes_common_identifier_columns(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "ID": 101,
                "Order ID": 202,
                "Customer ID": 303,
                "Product ID": 404,
            }
        ],
        required_columns=(),
        timezone="UTC",
    )

    normalized = result.normalized.iloc[0]

    assert normalized["id"] == "101"
    assert normalized["order_id"] == "202"
    assert normalized["customer_id"] == "303"
    assert normalized["product_id"] == "404"


@pytest.mark.parametrize(
    "timestamp_column",
    [
        "created_at",
        "updated_at",
        "timestamp",
    ],
)
def test_normalize_api_records_supports_common_timestamp_columns(
    tmp_path: Path,
    timestamp_column: str,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": "event-1",
                timestamp_column: "2026-02-01T12:00:00Z",
            }
        ],
        required_columns=("id",),
        timestamp_columns=(timestamp_column,),
        timezone="UTC",
    )

    assert result.normalized.loc[
        0,
        timestamp_column,
    ] == pd.Timestamp(
        "2026-02-01 12:00:00+00:00"
    )


def test_normalize_api_records_rejects_missing_required_column_definition(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        NormalizationError,
        match="required",
    ):
        normalize_api_records(
            [
                {
                    "customer_id": "customer-1",
                }
            ],
            required_columns=("id",),
            timezone="UTC",
        )


def test_normalize_api_records_raises_for_non_mapping_records(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        NormalizationError,
    ):
        normalize_api_records(
            [
                {
                    "id": "order-1",
                },
                "not-a-record",
            ],
            required_columns=("id",),
            timezone="UTC",
        )


@pytest.mark.parametrize(
    "records",
    [
        None,
        "invalid-records",
        123,
    ],
)
def test_normalize_api_records_rejects_invalid_input_type(
    records: object,
) -> None:
    with pytest.raises(
        (NormalizationError, TypeError, ValueError),
    ):
        normalize_api_records(
            records,  # type: ignore[arg-type]
            required_columns=("id",),
            timezone="UTC",
        )


def test_normalize_api_records_reports_row_counts(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": "order-1",
                "amount": "100",
            },
            {
                "id": None,
                "amount": "200",
            },
        ],
        required_columns=("id",),
        numeric_columns=("amount",),
        timezone="UTC",
    )

    assert result.input_rows == 2
    assert result.normalized_rows == 1
    assert result.rejected_rows == 1


def test_normalize_api_records_preserves_expected_columns(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": "order-1",
                "status": "completed",
                "amount": "100.00",
                "created_at": "2026-01-01T12:00:00Z",
            }
        ],
        required_columns=("id",),
        timestamp_columns=("created_at",),
        numeric_columns=("amount",),
        timezone="UTC",
    )

    assert set(result.normalized.columns) == {
        "id",
        "status",
        "amount",
        "created_at",
    }


def test_normalize_api_records_handles_null_numeric_values(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": "order-1",
                "amount": None,
            },
            {
                "id": "order-2",
                "amount": "125.25",
            },
        ],
        required_columns=("id",),
        numeric_columns=("amount",),
        timezone="UTC",
    )

    assert pd.isna(result.normalized.loc[0, "amount"])
    assert result.normalized.loc[1, "amount"] == 125.25


def test_normalize_api_records_preserves_nan_as_missing(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": "order-1",
                "amount": float("nan"),
            }
        ],
        required_columns=("id",),
        numeric_columns=("amount",),
        timezone="UTC",
    )

    assert pd.isna(result.normalized.loc[0, "amount"])


def test_normalize_api_records_strips_column_names(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "  Order ID  ": "order-1",
                " Customer Name ": "Alice",
            }
        ],
        required_columns=(),
        timezone="UTC",
    )

    assert "order_id" in result.normalized.columns
    assert "customer_name" in result.normalized.columns


def test_normalize_api_records_handles_boolean_values_in_string_columns(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": True,
                "active": False,
            }
        ],
        required_columns=("id",),
        timezone="UTC",
    )

    assert result.normalized.loc[0, "id"] == "True"
    assert result.normalized.loc[0, "active"] in {
        False,
        "False",
    }


def test_normalize_api_records_result_indexes_are_reset(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": "order-1",
            },
            {
                "id": None,
            },
            {
                "id": "order-2",
            },
        ],
        required_columns=("id",),
        timezone="UTC",
    )

    assert result.normalized.index.tolist() == [0, 1]
    assert result.rejected.index.tolist() == [0]


def test_normalization_result_contains_separate_frames(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {"id": "order-1"},
            {"id": None},
        ],
        required_columns=("id",),
        timezone="UTC",
    )

    assert result.normalized is not result.rejected
    assert len(result.normalized) == 1
    assert len(result.rejected) == 1

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.config import PipelineConfig
from src.normalization import (
    NormalizationError,
    NormalizationResult,
    normalize_api_records,
)


def make_config(
    tmp_path: Path,
    **overrides,
) -> PipelineConfig:
    """Create an isolated pipeline configuration for normalization tests."""
    values = {
        "raw_data_dir": tmp_path / "raw",
        "staging_data_dir": tmp_path / "staging",
        "processed_data_dir": tmp_path / "processed",
        "reports_dir": tmp_path / "reports",
        "api_base_url": "https://api.example.com",
        "api_page_size": 100,
        "api_max_pages": 10,
        "api_timeout_seconds": 30.0,
        "api_connect_timeout_seconds": 10.0,
        "api_read_timeout_seconds": 30.0,
        "api_max_retries": 0,
        "api_backoff_factor": 0.0,
        "api_response_timezone": "UTC",
        "log_level": "CRITICAL",
    }
    values.update(overrides)
    return PipelineConfig(**values)


def test_normalize_api_records_returns_normalization_result(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": "order-1",
                "status": "completed",
                "amount": "125.50",
            }
        ],
        required_columns=("id",),
        numeric_columns=("amount",),
        timezone="UTC",
    )

    assert isinstance(result, NormalizationResult)
    assert isinstance(result.normalized, pd.DataFrame)
    assert isinstance(result.rejected, pd.DataFrame)


def test_normalize_api_records_normalizes_column_names(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "Order ID": "order-1",
                "Customer-ID": "customer-1",
                "Created At": "2026-01-01T10:00:00Z",
            }
        ],
        required_columns=(),
        timestamp_columns=("created_at",),
        timezone="UTC",
    )

    assert list(result.normalized.columns) == [
        "order_id",
        "customer_id",
        "created_at",
    ]


def test_normalize_api_records_strips_string_values(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": "  order-1  ",
                "status": " completed ",
                "customer_id": " customer-42 ",
            }
        ],
        required_columns=("id",),
        timezone="UTC",
    )

    normalized = result.normalized.iloc[0]

    assert normalized["id"] == "order-1"
    assert normalized["status"] == "completed"
    assert normalized["customer_id"] == "customer-42"


def test_normalize_api_records_normalizes_identifier_columns(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": 12345,
                "customer_id": 67890,
                "product_id": 1001,
            }
        ],
        required_columns=(),
        timezone="UTC",
    )

    normalized = result.normalized.iloc[0]

    assert normalized["id"] == "12345"
    assert normalized["customer_id"] == "67890"
    assert normalized["product_id"] == "1001"


def test_normalize_api_records_converts_numeric_columns(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": "order-1",
                "amount": "125.50",
                "quantity": "3",
            },
            {
                "id": "order-2",
                "amount": 50,
                "quantity": 2,
            },
        ],
        required_columns=("id",),
        numeric_columns=("amount", "quantity"),
        timezone="UTC",
    )

    assert pd.api.types.is_numeric_dtype(
        result.normalized["amount"]
    )
    assert pd.api.types.is_numeric_dtype(
        result.normalized["quantity"]
    )
    assert result.normalized["amount"].tolist() == [
        125.5,
        50.0,
    ]
    assert result.normalized["quantity"].tolist() == [
        3.0,
        2.0,
    ]


def test_normalize_api_records_coerces_invalid_numeric_values_to_nan(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": "order-1",
                "amount": "invalid",
            },
            {
                "id": "order-2",
                "amount": "100.25",
            },
        ],
        required_columns=("id",),
        numeric_columns=("amount",),
        timezone="UTC",
    )

    assert pd.isna(
        result.normalized.loc[
            result.normalized["id"] == "order-1",
            "amount",
        ].iloc[0]
    )
    assert (
        result.normalized.loc[
            result.normalized["id"] == "order-2",
            "amount",
        ].iloc[0]
        == 100.25
    )


def test_normalize_api_records_normalizes_utc_timestamps(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": "order-1",
                "created_at": "2026-01-15T10:30:00Z",
            }
        ],
        required_columns=("id",),
        timestamp_columns=("created_at",),
        timezone="UTC",
    )

    timestamp = result.normalized.loc[
        0,
        "created_at",
    ]

    assert timestamp == pd.Timestamp(
        "2026-01-15 10:30:00+00:00"
    )


def test_normalize_api_records_converts_timestamp_to_requested_timezone(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": "order-1",
                "created_at": "2026-01-15T10:30:00Z",
            }
        ],
        required_columns=("id",),
        timestamp_columns=("created_at",),
        timezone="Asia/Kolkata",
    )

    timestamp = result.normalized.loc[
        0,
        "created_at",
    ]

    assert timestamp == pd.Timestamp(
        "2026-01-15 16:00:00+05:30"
    )


def test_normalize_api_records_coerces_invalid_timestamp_to_nat(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": "order-1",
                "created_at": "not-a-timestamp",
            },
            {
                "id": "order-2",
                "created_at": "2026-01-15T10:30:00Z",
            },
        ],
        required_columns=("id",),
        timestamp_columns=("created_at",),
        timezone="UTC",
    )

    timestamps = result.normalized["created_at"]

    assert pd.isna(timestamps.iloc[0])
    assert timestamps.iloc[1] == pd.Timestamp(
        "2026-01-15 10:30:00+00:00"
    )


def test_normalize_api_records_drops_completely_empty_rows(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": "order-1",
                "status": "completed",
            },
            {
                "id": None,
                "status": None,
            },
            {},
        ],
        required_columns=(),
        timezone="UTC",
    )

    assert len(result.normalized) == 1
    assert result.normalized.iloc[0]["id"] == "order-1"


def test_normalize_api_records_rejects_rows_missing_required_columns(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": "order-1",
                "customer_id": "customer-1",
            },
            {
                "id": None,
                "customer_id": "customer-2",
            },
        ],
        required_columns=("id",),
        timezone="UTC",
    )

    assert len(result.normalized) == 1
    assert result.normalized.iloc[0]["id"] == "order-1"

    assert len(result.rejected) == 1
    assert result.rejected.iloc[0]["customer_id"] == "customer-2"


def test_normalize_api_records_preserves_rejected_row_data(
    tmp_path: Path,
) -> None:
    records = [
        {
            "id": "order-1",
            "customer_id": "customer-1",
            "amount": "100",
        },
        {
            "id": None,
            "customer_id": "customer-2",
            "amount": "250",
        },
    ]

    result = normalize_api_records(
        records,
        required_columns=("id",),
        numeric_columns=("amount",),
        timezone="UTC",
    )

    assert len(result.rejected) == 1
    rejected = result.rejected.iloc[0]

    assert pd.isna(rejected["id"])
    assert rejected["customer_id"] == "customer-2"
    assert rejected["amount"] == 250.0


def test_normalize_api_records_handles_empty_input(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [],
        required_columns=("id",),
        timestamp_columns=("created_at",),
        numeric_columns=("amount",),
        timezone="UTC",
    )

    assert isinstance(result.normalized, pd.DataFrame)
    assert isinstance(result.rejected, pd.DataFrame)
    assert result.normalized.empty
    assert result.rejected.empty


def test_normalize_api_records_handles_mapping_records(
    tmp_path: Path,
) -> None:
    records = (
        {
            "id": "order-1",
            "amount": "100.00",
        },
        {
            "id": "order-2",
            "amount": "200.00",
        },
    )

    result = normalize_api_records(
        records,
        required_columns=("id",),
        numeric_columns=("amount",),
        timezone="UTC",
    )

    assert result.normalized["id"].tolist() == [
        "order-1",
        "order-2",
    ]
    assert result.normalized["amount"].tolist() == [
        100.0,
        200.0,
    ]


def test_normalize_api_records_preserves_input_order(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {"id": "order-3"},
            {"id": "order-1"},
            {"id": "order-2"},
        ],
        required_columns=("id",),
        timezone="UTC",
    )

    assert result.normalized["id"].tolist() == [
        "order-3",
        "order-1",
        "order-2",
    ]


def test_normalize_api_records_does_not_mutate_input_records(
    tmp_path: Path,
) -> None:
    records = [
        {
            "id": " order-1 ",
            "amount": "100.00",
        }
    ]

    original = [
        {
            "id": " order-1 ",
            "amount": "100.00",
        }
    ]

    normalize_api_records(
        records,
        required_columns=("id",),
        numeric_columns=("amount",),
        timezone="UTC",
    )

    assert records == original


def test_normalize_api_records_normalizes_common_identifier_columns(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "ID": 101,
                "Order ID": 202,
                "Customer ID": 303,
                "Product ID": 404,
            }
        ],
        required_columns=(),
        timezone="UTC",
    )

    normalized = result.normalized.iloc[0]

    assert normalized["id"] == "101"
    assert normalized["order_id"] == "202"
    assert normalized["customer_id"] == "303"
    assert normalized["product_id"] == "404"


@pytest.mark.parametrize(
    "timestamp_column",
    [
        "created_at",
        "updated_at",
        "timestamp",
    ],
)
def test_normalize_api_records_supports_common_timestamp_columns(
    tmp_path: Path,
    timestamp_column: str,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": "event-1",
                timestamp_column: "2026-02-01T12:00:00Z",
            }
        ],
        required_columns=("id",),
        timestamp_columns=(timestamp_column,),
        timezone="UTC",
    )

    assert result.normalized.loc[
        0,
        timestamp_column,
    ] == pd.Timestamp(
        "2026-02-01 12:00:00+00:00"
    )


def test_normalize_api_records_rejects_missing_required_column_definition(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        NormalizationError,
        match="required",
    ):
        normalize_api_records(
            [
                {
                    "customer_id": "customer-1",
                }
            ],
            required_columns=("id",),
            timezone="UTC",
        )


def test_normalize_api_records_raises_for_non_mapping_records(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        NormalizationError,
    ):
        normalize_api_records(
            [
                {
                    "id": "order-1",
                },
                "not-a-record",
            ],
            required_columns=("id",),
            timezone="UTC",
        )


@pytest.mark.parametrize(
    "records",
    [
        None,
        "invalid-records",
        123,
    ],
)
def test_normalize_api_records_rejects_invalid_input_type(
    records: object,
) -> None:
    with pytest.raises(
        (NormalizationError, TypeError, ValueError),
    ):
        normalize_api_records(
            records,  # type: ignore[arg-type]
            required_columns=("id",),
            timezone="UTC",
        )


def test_normalize_api_records_reports_row_counts(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": "order-1",
                "amount": "100",
            },
            {
                "id": None,
                "amount": "200",
            },
        ],
        required_columns=("id",),
        numeric_columns=("amount",),
        timezone="UTC",
    )

    assert result.input_rows == 2
    assert result.normalized_rows == 1
    assert result.rejected_rows == 1


def test_normalize_api_records_preserves_expected_columns(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": "order-1",
                "status": "completed",
                "amount": "100.00",
                "created_at": "2026-01-01T12:00:00Z",
            }
        ],
        required_columns=("id",),
        timestamp_columns=("created_at",),
        numeric_columns=("amount",),
        timezone="UTC",
    )

    assert set(result.normalized.columns) == {
        "id",
        "status",
        "amount",
        "created_at",
    }


def test_normalize_api_records_handles_null_numeric_values(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": "order-1",
                "amount": None,
            },
            {
                "id": "order-2",
                "amount": "125.25",
            },
        ],
        required_columns=("id",),
        numeric_columns=("amount",),
        timezone="UTC",
    )

    assert pd.isna(result.normalized.loc[0, "amount"])
    assert result.normalized.loc[1, "amount"] == 125.25


def test_normalize_api_records_preserves_nan_as_missing(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": "order-1",
                "amount": float("nan"),
            }
        ],
        required_columns=("id",),
        numeric_columns=("amount",),
        timezone="UTC",
    )

    assert pd.isna(result.normalized.loc[0, "amount"])


def test_normalize_api_records_strips_column_names(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "  Order ID  ": "order-1",
                " Customer Name ": "Alice",
            }
        ],
        required_columns=(),
        timezone="UTC",
    )

    assert "order_id" in result.normalized.columns
    assert "customer_name" in result.normalized.columns


def test_normalize_api_records_handles_boolean_values_in_string_columns(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": True,
                "active": False,
            }
        ],
        required_columns=("id",),
        timezone="UTC",
    )

    assert result.normalized.loc[0, "id"] == "True"
    assert result.normalized.loc[0, "active"] in {
        False,
        "False",
    }


def test_normalize_api_records_result_indexes_are_reset(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {
                "id": "order-1",
            },
            {
                "id": None,
            },
            {
                "id": "order-2",
            },
        ],
        required_columns=("id",),
        timezone="UTC",
    )

    assert result.normalized.index.tolist() == [0, 1]
    assert result.rejected.index.tolist() == [0]


def test_normalization_result_contains_separate_frames(
    tmp_path: Path,
) -> None:
    result = normalize_api_records(
        [
            {"id": "order-1"},
            {"id": None},
        ],
        required_columns=("id",),
        timezone="UTC",
    )

    assert result.normalized is not result.rejected
    assert len(result.normalized) == 1
    assert len(result.rejected) == 1