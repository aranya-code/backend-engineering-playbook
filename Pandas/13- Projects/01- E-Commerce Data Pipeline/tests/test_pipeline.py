from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.config import PipelineConfig
from src.pipeline import (
    PipelineError,
    PipelineResult,
    _write_csv_atomically,
    _write_parquet_atomically,
    main,
    run_pipeline,
)


def make_orders() -> pd.DataFrame:
    """Build representative source orders."""
    return pd.DataFrame(
        {
            "order_id": ["O-1", "O-2", "O-3", "O-4"],
            "customer_id": ["C-1", "C-1", "C-2", "C-3"],
            "product_id": ["P-1", "P-2", "P-1", "P-3"],
            "status": [
                "completed",
                "completed",
                "cancelled",
                "completed",
            ],
            "amount": [100.0, 200.0, 50.0, 300.0],
            "created_at": [
                "2026-01-01T10:00:00Z",
                "2026-01-01T11:00:00Z",
                "2026-01-02T10:00:00Z",
                "2026-01-02T12:00:00Z",
            ],
            "updated_at": [
                "2026-01-01T10:05:00Z",
                "2026-01-01T11:05:00Z",
                "2026-01-02T10:05:00Z",
                "2026-01-02T12:05:00Z",
            ],
        }
    )


def make_customers() -> pd.DataFrame:
    """Build representative customer reference data."""
    return pd.DataFrame(
        {
            "customer_id": ["C-1", "C-2", "C-3"],
            "segment": [
                "premium",
                "standard",
                "enterprise",
            ],
        }
    )


def make_products() -> pd.DataFrame:
    """Build representative product reference data."""
    return pd.DataFrame(
        {
            "product_id": ["P-1", "P-2", "P-3"],
            "name": [
                "Laptop",
                "Keyboard",
                "Monitor",
            ],
        }
    )


def make_config(tmp_path: Path, **overrides) -> PipelineConfig:
    """Create an isolated configuration for pipeline tests."""
    values = {
        "raw_data_dir": tmp_path / "raw",
        "staging_data_dir": tmp_path / "staging",
        "processed_data_dir": tmp_path / "processed",
        "reports_dir": tmp_path / "reports",
        "orders_file": "orders.csv",
        "customers_file": "customers.csv",
        "products_file": "products.csv",
        "csv_chunksize": 2,
        "fail_on_invalid_records": False,
        "create_directories": True,
        "atomic_writes": True,
        "reconciliation_enabled": True,
        "reconciliation_tolerance": 0.01,
        "log_level": "CRITICAL",
    }
    values.update(overrides)
    return PipelineConfig(**values)


def write_inputs(
    pipeline_config: PipelineConfig,
    *,
    orders: pd.DataFrame | None = None,
    customers: pd.DataFrame | None = None,
    products: pd.DataFrame | None = None,
) -> None:
    """Write test input datasets to configured paths."""
    pipeline_config.ensure_directories()

    (
        orders if orders is not None else make_orders()
    ).to_csv(
        pipeline_config.orders_path,
        index=False,
    )
    (
        customers if customers is not None else make_customers()
    ).to_csv(
        pipeline_config.customers_path,
        index=False,
    )
    (
        products if products is not None else make_products()
    ).to_csv(
        pipeline_config.products_path,
        index=False,
    )


def test_run_pipeline_returns_expected_pipeline_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(tmp_path)
    write_inputs(pipeline_config)

    writes: dict[str, object] = {}

    def fake_write_outputs(
        reports,
        rejected_orders,
        *,
        pipeline_config,
    ) -> None:
        writes["reports"] = reports
        writes["rejected_orders"] = rejected_orders
        writes["config"] = pipeline_config

    monkeypatch.setattr(
        "src.pipeline._write_outputs",
        fake_write_outputs,
    )

    result = run_pipeline(
        pipeline_config,
    )

    assert isinstance(result, PipelineResult)
    assert len(result.enriched_orders) == 4
    assert list(result.enriched_orders["order_id"]) == [
        "O-1",
        "O-2",
        "O-3",
        "O-4",
    ]
    assert "segment" in result.enriched_orders.columns

    assert result.metrics == {
        "input_rows": 4,
        "completed_rows": 3,
        "unique_orders": 4,
        "unique_customers": 3,
        "total_revenue": 600.0,
        "average_order_value": 200.0,
    }

    assert result.reports.daily_sales["revenue"].sum() == 600.0
    assert result.reports.daily_sales["order_count"].sum() == 3
    assert result.rejected_orders.empty

    assert writes["reports"] is result.reports
    assert writes["rejected_orders"] is result.rejected_orders
    assert writes["config"] is pipeline_config


def test_run_pipeline_creates_required_directories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(tmp_path)

    write_inputs(pipeline_config)

    pipeline_config.staging_data_dir.rmdir()
    pipeline_config.processed_data_dir.rmdir()
    pipeline_config.reports_dir.rmdir()

    monkeypatch.setattr(
        "src.pipeline._write_outputs",
        lambda *args, **kwargs: None,
    )

    run_pipeline(
        pipeline_config,
    )

    assert pipeline_config.staging_data_dir.exists()
    assert pipeline_config.processed_data_dir.exists()
    assert pipeline_config.reports_dir.exists()


def test_run_pipeline_rejects_invalid_orders_without_failing_by_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(tmp_path)
    orders = make_orders()
    orders.loc[0, "amount"] = -10.0

    write_inputs(
        pipeline_config,
        orders=orders,
    )

    monkeypatch.setattr(
        "src.pipeline._write_outputs",
        lambda *args, **kwargs: None,
    )

    result = run_pipeline(
        pipeline_config,
    )

    assert len(result.enriched_orders) == 3
    assert len(result.rejected_orders) == 1
    assert result.rejected_orders.loc[0, "order_id"] == "O-1"


def test_run_pipeline_fails_when_invalid_records_are_configured_as_fatal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(
        tmp_path,
        fail_on_invalid_records=True,
    )
    orders = make_orders()
    orders.loc[0, "amount"] = -10.0

    write_inputs(
        pipeline_config,
        orders=orders,
    )

    write_called = False

    def fake_write_outputs(*args, **kwargs) -> None:
        nonlocal write_called
        write_called = True

    monkeypatch.setattr(
        "src.pipeline._write_outputs",
        fake_write_outputs,
    )

    with pytest.raises(
        PipelineError,
        match="cleaning rejected",
    ):
        run_pipeline(
            pipeline_config,
        )

    assert write_called is False


def test_run_pipeline_reports_rejected_records_without_dropping_valid_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(tmp_path)
    orders = make_orders()
    orders.loc[1, "status"] = "invalid"
    orders.loc[2, "amount"] = -1.0

    write_inputs(
        pipeline_config,
        orders=orders,
    )

    monkeypatch.setattr(
        "src.pipeline._write_outputs",
        lambda *args, **kwargs: None,
    )

    result = run_pipeline(
        pipeline_config,
    )

    assert result.enriched_orders["order_id"].tolist() == [
        "O-1",
        "O-4",
    ]
    assert result.rejected_orders["order_id"].tolist() == [
        "O-2",
        "O-3",
    ]


def test_run_pipeline_fails_when_customer_reference_is_invalid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(tmp_path)
    customers = make_customers()
    customers.loc[0, "customer_id"] = "C-1"
    customers.loc[1, "customer_id"] = "C-1"

    write_inputs(
        pipeline_config,
        customers=customers,
    )

    monkeypatch.setattr(
        "src.pipeline._write_outputs",
        lambda *args, **kwargs: None,
    )

    with pytest.raises(
        PipelineError,
        match="Customer reference data validation failed",
    ):
        run_pipeline(
            pipeline_config,
        )


def test_run_pipeline_fails_when_order_references_unknown_customer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(tmp_path)
    orders = make_orders()
    orders.loc[0, "customer_id"] = "C-999"

    write_inputs(
        pipeline_config,
        orders=orders,
    )

    monkeypatch.setattr(
        "src.pipeline._write_outputs",
        lambda *args, **kwargs: None,
    )

    with pytest.raises(
        PipelineError,
        match="relationship validation failed",
    ):
        run_pipeline(
            pipeline_config,
        )


def test_run_pipeline_fails_when_required_input_is_missing(
    tmp_path: Path,
) -> None:
    pipeline_config = make_config(tmp_path)
    pipeline_config.ensure_directories()

    with pytest.raises(
        PipelineError,
    ):
        run_pipeline(
            pipeline_config,
        )


def test_run_pipeline_requires_products_input(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(tmp_path)
    pipeline_config.ensure_directories()

    make_orders().to_csv(
        pipeline_config.orders_path,
        index=False,
    )
    make_customers().to_csv(
        pipeline_config.customers_path,
        index=False,
    )

    monkeypatch.setattr(
        "src.pipeline._write_outputs",
        lambda *args, **kwargs: None,
    )

    with pytest.raises(
        PipelineError,
    ):
        run_pipeline(
            pipeline_config,
        )


def test_run_pipeline_does_not_write_outputs_before_successful_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(tmp_path)
    orders = make_orders()
    orders.loc[0, "customer_id"] = "C-999"

    write_inputs(
        pipeline_config,
        orders=orders,
    )

    write_called = False

    def fake_write_outputs(*args, **kwargs) -> None:
        nonlocal write_called
        write_called = True

    monkeypatch.setattr(
        "src.pipeline._write_outputs",
        fake_write_outputs,
    )

    with pytest.raises(
        PipelineError,
        match="relationship validation failed",
    ):
        run_pipeline(
            pipeline_config,
        )

    assert write_called is False


def test_run_pipeline_skips_reconciliation_when_disabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(
        tmp_path,
        reconciliation_enabled=False,
    )
    write_inputs(pipeline_config)

    def fail_reconciliation(*args, **kwargs):
        raise AssertionError(
            "Reconciliation should not run when disabled."
        )

    monkeypatch.setattr(
        "src.pipeline._validate_pipeline_results",
        fail_reconciliation,
    )
    monkeypatch.setattr(
        "src.pipeline._write_outputs",
        lambda *args, **kwargs: None,
    )

    result = run_pipeline(
        pipeline_config,
    )

    assert result.metrics["total_revenue"] == 600.0


def test_run_pipeline_uses_configured_reconciliation_tolerance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(
        tmp_path,
        reconciliation_tolerance=0.50,
    )
    write_inputs(pipeline_config)

    captured: dict[str, float] = {}

    def fake_validate_pipeline_results(
        orders,
        customers,
        reports,
        *,
        tolerance: float,
    ) -> None:
        captured["tolerance"] = tolerance

    monkeypatch.setattr(
        "src.pipeline._validate_pipeline_results",
        fake_validate_pipeline_results,
    )
    monkeypatch.setattr(
        "src.pipeline._write_outputs",
        lambda *args, **kwargs: None,
    )

    run_pipeline(
        pipeline_config,
    )

    assert captured["tolerance"] == 0.50


def test_run_pipeline_propagates_pipeline_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(tmp_path)
    write_inputs(pipeline_config)

    expected = PipelineError("intentional failure")

    def fail_cleaning(*args, **kwargs):
        raise expected

    monkeypatch.setattr(
        "src.pipeline._clean_orders",
        fail_cleaning,
    )

    with pytest.raises(
        PipelineError,
        match="intentional failure",
    ) as exc_info:
        run_pipeline(
            pipeline_config,
        )

    assert exc_info.value is expected


def test_run_pipeline_wraps_unexpected_value_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(tmp_path)
    write_inputs(pipeline_config)

    monkeypatch.setattr(
        "src.pipeline.enrich_orders",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            ValueError("unexpected transformation failure")
        ),
    )

    with pytest.raises(
        PipelineError,
        match="E-commerce data pipeline failed",
    ) as exc_info:
        run_pipeline(
            pipeline_config,
        )

    assert isinstance(
        exc_info.value.__cause__,
        ValueError,
    )


def test_run_pipeline_is_reproducible_for_identical_inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(tmp_path)
    write_inputs(pipeline_config)

    monkeypatch.setattr(
        "src.pipeline._write_outputs",
        lambda *args, **kwargs: None,
    )

    first = run_pipeline(
        pipeline_config,
    )
    second = run_pipeline(
        pipeline_config,
    )

    pd.testing.assert_frame_equal(
        first.enriched_orders,
        second.enriched_orders,
    )
    pd.testing.assert_frame_equal(
        first.reports.daily_sales,
        second.reports.daily_sales,
    )
    pd.testing.assert_frame_equal(
        first.reports.customer_sales,
        second.reports.customer_sales,
    )
    pd.testing.assert_frame_equal(
        first.reports.product_sales,
        second.reports.product_sales,
    )
    pd.testing.assert_frame_equal(
        first.rejected_orders,
        second.rejected_orders,
    )
    assert first.metrics == second.metrics


def test_run_pipeline_writes_outputs_when_writer_is_called(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(tmp_path)
    write_inputs(pipeline_config)

    captured: dict[str, object] = {}

    def fake_write_outputs(
        reports,
        rejected_orders,
        *,
        pipeline_config,
    ) -> None:
        captured["reports"] = reports
        captured["rejected_orders"] = rejected_orders
        captured["config"] = pipeline_config

    monkeypatch.setattr(
        "src.pipeline._write_outputs",
        fake_write_outputs,
    )

    result = run_pipeline(
        pipeline_config,
    )

    assert captured["reports"] is result.reports
    assert captured["rejected_orders"] is result.rejected_orders
    assert captured["config"] is pipeline_config


def test_write_parquet_atomically_creates_parent_and_replaces_file(
    tmp_path: Path,
) -> None:
    path = tmp_path / "nested" / "result.parquet"
    frame = pd.DataFrame(
        {
            "order_id": ["O-1"],
            "revenue": [100.0],
        }
    )

    _write_parquet_atomically(
        frame,
        path,
    )

    assert path.exists()
    assert list(path.parent.iterdir()) == [path]

    restored = pd.read_parquet(path)
    pd.testing.assert_frame_equal(
        restored,
        frame,
    )


def test_write_parquet_atomically_replaces_existing_file(
    tmp_path: Path,
) -> None:
    path = tmp_path / "result.parquet"

    first = pd.DataFrame(
        {
            "order_id": ["O-1"],
            "revenue": [100.0],
        }
    )
    second = pd.DataFrame(
        {
            "order_id": ["O-2"],
            "revenue": [250.0],
        }
    )

    _write_parquet_atomically(
        first,
        path,
    )
    _write_parquet_atomically(
        second,
        path,
    )

    restored = pd.read_parquet(path)
    pd.testing.assert_frame_equal(
        restored,
        second,
    )


def test_write_csv_atomically_creates_parent_and_writes_data(
    tmp_path: Path,
) -> None:
    path = tmp_path / "nested" / "result.csv"
    frame = pd.DataFrame(
        {
            "order_id": ["O-1", "O-2"],
            "revenue": [100.0, 200.0],
        }
    )

    _write_csv_atomically(
        frame,
        path,
    )

    assert path.exists()
    restored = pd.read_csv(path)

    pd.testing.assert_frame_equal(
        restored,
        frame,
    )


def test_write_csv_atomically_replaces_existing_file(
    tmp_path: Path,
) -> None:
    path = tmp_path / "result.csv"

    first = pd.DataFrame(
        {
            "order_id": ["O-1"],
            "revenue": [100.0],
        }
    )
    second = pd.DataFrame(
        {
            "order_id": ["O-2"],
            "revenue": [250.0],
        }
    )

    _write_csv_atomically(
        first,
        path,
    )
    _write_csv_atomically(
        second,
        path,
    )

    restored = pd.read_csv(path)
    pd.testing.assert_frame_equal(
        restored,
        second,
    )


def test_write_parquet_atomically_wraps_writer_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "result.parquet"
    frame = pd.DataFrame(
        {
            "order_id": ["O-1"],
            "revenue": [100.0],
        }
    )

    def fail_to_write_parquet(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(
        pd.DataFrame,
        "to_parquet",
        fail_to_write_parquet,
    )

    with pytest.raises(
        PipelineError,
        match="Failed to write Parquet output",
    ):
        _write_parquet_atomically(
            frame,
            path,
        )

    assert not path.exists()
    assert not list(path.parent.glob(".result.parquet.tmp-*"))


def test_write_csv_atomically_wraps_writer_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "result.csv"
    frame = pd.DataFrame(
        {
            "order_id": ["O-1"],
            "revenue": [100.0],
        }
    )

    def fail_to_write_csv(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(
        pd.DataFrame,
        "to_csv",
        fail_to_write_csv,
    )

    with pytest.raises(
        PipelineError,
        match="Failed to write CSV output",
    ):
        _write_csv_atomically(
            frame,
            path,
        )

    assert not path.exists()
    assert not list(path.parent.glob(".result.csv.tmp-*"))


def test_main_returns_zero_on_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "src.pipeline.run_pipeline",
        lambda: None,
    )

    assert main() == 0


def test_main_returns_one_on_pipeline_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "src.pipeline.run_pipeline",
        lambda: (_ for _ in ()).throw(
            PipelineError("pipeline failed")
        ),
    )

    assert main() == 1


def test_run_pipeline_returns_rejected_records_separately(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(tmp_path)
    orders = make_orders()
    orders.loc[0, "amount"] = -25.0

    write_inputs(
        pipeline_config,
        orders=orders,
    )

    monkeypatch.setattr(
        "src.pipeline._write_outputs",
        lambda *args, **kwargs: None,
    )

    result = run_pipeline(
        pipeline_config,
    )

    assert len(result.rejected_orders) == 1
    assert result.rejected_orders.loc[0, "order_id"] == "O-1"
    assert "O-1" not in result.enriched_orders[
        "order_id"
    ].tolist()


def test_run_pipeline_preserves_report_grain_and_columns(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(tmp_path)
    write_inputs(pipeline_config)

    monkeypatch.setattr(
        "src.pipeline._write_outputs",
        lambda *args, **kwargs: None,
    )

    result = run_pipeline(
        pipeline_config,
    )

    assert list(result.reports.daily_sales.columns) == [
        "order_date",
        "order_count",
        "customer_count",
        "revenue",
        "average_order_value",
    ]
    assert list(result.reports.customer_sales.columns) == [
        "customer_id",
        "order_count",
        "revenue",
        "average_order_value",
    ]
    assert list(result.reports.product_sales.columns) == [
        "product_id",
        "order_count",
        "revenue",
        "average_order_value",
    ]

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.config import PipelineConfig
from src.pipeline import (
    PipelineError,
    PipelineResult,
    _write_csv_atomically,
    _write_parquet_atomically,
    main,
    run_pipeline,
)


def make_orders() -> pd.DataFrame:
    """Build representative source orders."""
    return pd.DataFrame(
        {
            "order_id": ["O-1", "O-2", "O-3", "O-4"],
            "customer_id": ["C-1", "C-1", "C-2", "C-3"],
            "product_id": ["P-1", "P-2", "P-1", "P-3"],
            "status": [
                "completed",
                "completed",
                "cancelled",
                "completed",
            ],
            "amount": [100.0, 200.0, 50.0, 300.0],
            "created_at": [
                "2026-01-01T10:00:00Z",
                "2026-01-01T11:00:00Z",
                "2026-01-02T10:00:00Z",
                "2026-01-02T12:00:00Z",
            ],
            "updated_at": [
                "2026-01-01T10:05:00Z",
                "2026-01-01T11:05:00Z",
                "2026-01-02T10:05:00Z",
                "2026-01-02T12:05:00Z",
            ],
        }
    )


def make_customers() -> pd.DataFrame:
    """Build representative customer reference data."""
    return pd.DataFrame(
        {
            "customer_id": ["C-1", "C-2", "C-3"],
            "segment": [
                "premium",
                "standard",
                "enterprise",
            ],
        }
    )


def make_products() -> pd.DataFrame:
    """Build representative product reference data."""
    return pd.DataFrame(
        {
            "product_id": ["P-1", "P-2", "P-3"],
            "name": [
                "Laptop",
                "Keyboard",
                "Monitor",
            ],
        }
    )


def make_config(tmp_path: Path, **overrides) -> PipelineConfig:
    """Create an isolated configuration for pipeline tests."""
    values = {
        "raw_data_dir": tmp_path / "raw",
        "staging_data_dir": tmp_path / "staging",
        "processed_data_dir": tmp_path / "processed",
        "reports_dir": tmp_path / "reports",
        "orders_file": "orders.csv",
        "customers_file": "customers.csv",
        "products_file": "products.csv",
        "csv_chunksize": 2,
        "fail_on_invalid_records": False,
        "create_directories": True,
        "atomic_writes": True,
        "reconciliation_enabled": True,
        "reconciliation_tolerance": 0.01,
        "log_level": "CRITICAL",
    }
    values.update(overrides)
    return PipelineConfig(**values)


def write_inputs(
    pipeline_config: PipelineConfig,
    *,
    orders: pd.DataFrame | None = None,
    customers: pd.DataFrame | None = None,
    products: pd.DataFrame | None = None,
) -> None:
    """Write test input datasets to configured paths."""
    pipeline_config.ensure_directories()

    (
        orders if orders is not None else make_orders()
    ).to_csv(
        pipeline_config.orders_path,
        index=False,
    )
    (
        customers if customers is not None else make_customers()
    ).to_csv(
        pipeline_config.customers_path,
        index=False,
    )
    (
        products if products is not None else make_products()
    ).to_csv(
        pipeline_config.products_path,
        index=False,
    )


def test_run_pipeline_returns_expected_pipeline_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(tmp_path)
    write_inputs(pipeline_config)

    writes: dict[str, object] = {}

    def fake_write_outputs(
        reports,
        rejected_orders,
        *,
        pipeline_config,
    ) -> None:
        writes["reports"] = reports
        writes["rejected_orders"] = rejected_orders
        writes["config"] = pipeline_config

    monkeypatch.setattr(
        "src.pipeline._write_outputs",
        fake_write_outputs,
    )

    result = run_pipeline(
        pipeline_config,
    )

    assert isinstance(result, PipelineResult)
    assert len(result.enriched_orders) == 4
    assert list(result.enriched_orders["order_id"]) == [
        "O-1",
        "O-2",
        "O-3",
        "O-4",
    ]
    assert "segment" in result.enriched_orders.columns

    assert result.metrics == {
        "input_rows": 4,
        "completed_rows": 3,
        "unique_orders": 4,
        "unique_customers": 3,
        "total_revenue": 600.0,
        "average_order_value": 200.0,
    }

    assert result.reports.daily_sales["revenue"].sum() == 600.0
    assert result.reports.daily_sales["order_count"].sum() == 3
    assert result.rejected_orders.empty

    assert writes["reports"] is result.reports
    assert writes["rejected_orders"] is result.rejected_orders
    assert writes["config"] is pipeline_config


def test_run_pipeline_creates_required_directories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(tmp_path)

    write_inputs(pipeline_config)

    pipeline_config.staging_data_dir.rmdir()
    pipeline_config.processed_data_dir.rmdir()
    pipeline_config.reports_dir.rmdir()

    monkeypatch.setattr(
        "src.pipeline._write_outputs",
        lambda *args, **kwargs: None,
    )

    run_pipeline(
        pipeline_config,
    )

    assert pipeline_config.staging_data_dir.exists()
    assert pipeline_config.processed_data_dir.exists()
    assert pipeline_config.reports_dir.exists()


def test_run_pipeline_rejects_invalid_orders_without_failing_by_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(tmp_path)
    orders = make_orders()
    orders.loc[0, "amount"] = -10.0

    write_inputs(
        pipeline_config,
        orders=orders,
    )

    monkeypatch.setattr(
        "src.pipeline._write_outputs",
        lambda *args, **kwargs: None,
    )

    result = run_pipeline(
        pipeline_config,
    )

    assert len(result.enriched_orders) == 3
    assert len(result.rejected_orders) == 1
    assert result.rejected_orders.loc[0, "order_id"] == "O-1"


def test_run_pipeline_fails_when_invalid_records_are_configured_as_fatal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(
        tmp_path,
        fail_on_invalid_records=True,
    )
    orders = make_orders()
    orders.loc[0, "amount"] = -10.0

    write_inputs(
        pipeline_config,
        orders=orders,
    )

    write_called = False

    def fake_write_outputs(*args, **kwargs) -> None:
        nonlocal write_called
        write_called = True

    monkeypatch.setattr(
        "src.pipeline._write_outputs",
        fake_write_outputs,
    )

    with pytest.raises(
        PipelineError,
        match="cleaning rejected",
    ):
        run_pipeline(
            pipeline_config,
        )

    assert write_called is False


def test_run_pipeline_reports_rejected_records_without_dropping_valid_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(tmp_path)
    orders = make_orders()
    orders.loc[1, "status"] = "invalid"
    orders.loc[2, "amount"] = -1.0

    write_inputs(
        pipeline_config,
        orders=orders,
    )

    monkeypatch.setattr(
        "src.pipeline._write_outputs",
        lambda *args, **kwargs: None,
    )

    result = run_pipeline(
        pipeline_config,
    )

    assert result.enriched_orders["order_id"].tolist() == [
        "O-1",
        "O-4",
    ]
    assert result.rejected_orders["order_id"].tolist() == [
        "O-2",
        "O-3",
    ]


def test_run_pipeline_fails_when_customer_reference_is_invalid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(tmp_path)
    customers = make_customers()
    customers.loc[0, "customer_id"] = "C-1"
    customers.loc[1, "customer_id"] = "C-1"

    write_inputs(
        pipeline_config,
        customers=customers,
    )

    monkeypatch.setattr(
        "src.pipeline._write_outputs",
        lambda *args, **kwargs: None,
    )

    with pytest.raises(
        PipelineError,
        match="Customer reference data validation failed",
    ):
        run_pipeline(
            pipeline_config,
        )


def test_run_pipeline_fails_when_order_references_unknown_customer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(tmp_path)
    orders = make_orders()
    orders.loc[0, "customer_id"] = "C-999"

    write_inputs(
        pipeline_config,
        orders=orders,
    )

    monkeypatch.setattr(
        "src.pipeline._write_outputs",
        lambda *args, **kwargs: None,
    )

    with pytest.raises(
        PipelineError,
        match="relationship validation failed",
    ):
        run_pipeline(
            pipeline_config,
        )


def test_run_pipeline_fails_when_required_input_is_missing(
    tmp_path: Path,
) -> None:
    pipeline_config = make_config(tmp_path)
    pipeline_config.ensure_directories()

    with pytest.raises(
        PipelineError,
    ):
        run_pipeline(
            pipeline_config,
        )


def test_run_pipeline_requires_products_input(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(tmp_path)
    pipeline_config.ensure_directories()

    make_orders().to_csv(
        pipeline_config.orders_path,
        index=False,
    )
    make_customers().to_csv(
        pipeline_config.customers_path,
        index=False,
    )

    monkeypatch.setattr(
        "src.pipeline._write_outputs",
        lambda *args, **kwargs: None,
    )

    with pytest.raises(
        PipelineError,
    ):
        run_pipeline(
            pipeline_config,
        )


def test_run_pipeline_does_not_write_outputs_before_successful_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(tmp_path)
    orders = make_orders()
    orders.loc[0, "customer_id"] = "C-999"

    write_inputs(
        pipeline_config,
        orders=orders,
    )

    write_called = False

    def fake_write_outputs(*args, **kwargs) -> None:
        nonlocal write_called
        write_called = True

    monkeypatch.setattr(
        "src.pipeline._write_outputs",
        fake_write_outputs,
    )

    with pytest.raises(
        PipelineError,
        match="relationship validation failed",
    ):
        run_pipeline(
            pipeline_config,
        )

    assert write_called is False


def test_run_pipeline_skips_reconciliation_when_disabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(
        tmp_path,
        reconciliation_enabled=False,
    )
    write_inputs(pipeline_config)

    def fail_reconciliation(*args, **kwargs):
        raise AssertionError(
            "Reconciliation should not run when disabled."
        )

    monkeypatch.setattr(
        "src.pipeline._validate_pipeline_results",
        fail_reconciliation,
    )
    monkeypatch.setattr(
        "src.pipeline._write_outputs",
        lambda *args, **kwargs: None,
    )

    result = run_pipeline(
        pipeline_config,
    )

    assert result.metrics["total_revenue"] == 600.0


def test_run_pipeline_uses_configured_reconciliation_tolerance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(
        tmp_path,
        reconciliation_tolerance=0.50,
    )
    write_inputs(pipeline_config)

    captured: dict[str, float] = {}

    def fake_validate_pipeline_results(
        orders,
        customers,
        reports,
        *,
        tolerance: float,
    ) -> None:
        captured["tolerance"] = tolerance

    monkeypatch.setattr(
        "src.pipeline._validate_pipeline_results",
        fake_validate_pipeline_results,
    )
    monkeypatch.setattr(
        "src.pipeline._write_outputs",
        lambda *args, **kwargs: None,
    )

    run_pipeline(
        pipeline_config,
    )

    assert captured["tolerance"] == 0.50


def test_run_pipeline_propagates_pipeline_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(tmp_path)
    write_inputs(pipeline_config)

    expected = PipelineError("intentional failure")

    def fail_cleaning(*args, **kwargs):
        raise expected

    monkeypatch.setattr(
        "src.pipeline._clean_orders",
        fail_cleaning,
    )

    with pytest.raises(
        PipelineError,
        match="intentional failure",
    ) as exc_info:
        run_pipeline(
            pipeline_config,
        )

    assert exc_info.value is expected


def test_run_pipeline_wraps_unexpected_value_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(tmp_path)
    write_inputs(pipeline_config)

    monkeypatch.setattr(
        "src.pipeline.enrich_orders",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            ValueError("unexpected transformation failure")
        ),
    )

    with pytest.raises(
        PipelineError,
        match="E-commerce data pipeline failed",
    ) as exc_info:
        run_pipeline(
            pipeline_config,
        )

    assert isinstance(
        exc_info.value.__cause__,
        ValueError,
    )


def test_run_pipeline_is_reproducible_for_identical_inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(tmp_path)
    write_inputs(pipeline_config)

    monkeypatch.setattr(
        "src.pipeline._write_outputs",
        lambda *args, **kwargs: None,
    )

    first = run_pipeline(
        pipeline_config,
    )
    second = run_pipeline(
        pipeline_config,
    )

    pd.testing.assert_frame_equal(
        first.enriched_orders,
        second.enriched_orders,
    )
    pd.testing.assert_frame_equal(
        first.reports.daily_sales,
        second.reports.daily_sales,
    )
    pd.testing.assert_frame_equal(
        first.reports.customer_sales,
        second.reports.customer_sales,
    )
    pd.testing.assert_frame_equal(
        first.reports.product_sales,
        second.reports.product_sales,
    )
    pd.testing.assert_frame_equal(
        first.rejected_orders,
        second.rejected_orders,
    )
    assert first.metrics == second.metrics


def test_run_pipeline_writes_outputs_when_writer_is_called(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(tmp_path)
    write_inputs(pipeline_config)

    captured: dict[str, object] = {}

    def fake_write_outputs(
        reports,
        rejected_orders,
        *,
        pipeline_config,
    ) -> None:
        captured["reports"] = reports
        captured["rejected_orders"] = rejected_orders
        captured["config"] = pipeline_config

    monkeypatch.setattr(
        "src.pipeline._write_outputs",
        fake_write_outputs,
    )

    result = run_pipeline(
        pipeline_config,
    )

    assert captured["reports"] is result.reports
    assert captured["rejected_orders"] is result.rejected_orders
    assert captured["config"] is pipeline_config


def test_write_parquet_atomically_creates_parent_and_replaces_file(
    tmp_path: Path,
) -> None:
    path = tmp_path / "nested" / "result.parquet"
    frame = pd.DataFrame(
        {
            "order_id": ["O-1"],
            "revenue": [100.0],
        }
    )

    _write_parquet_atomically(
        frame,
        path,
    )

    assert path.exists()
    assert list(path.parent.iterdir()) == [path]

    restored = pd.read_parquet(path)
    pd.testing.assert_frame_equal(
        restored,
        frame,
    )


def test_write_parquet_atomically_replaces_existing_file(
    tmp_path: Path,
) -> None:
    path = tmp_path / "result.parquet"

    first = pd.DataFrame(
        {
            "order_id": ["O-1"],
            "revenue": [100.0],
        }
    )
    second = pd.DataFrame(
        {
            "order_id": ["O-2"],
            "revenue": [250.0],
        }
    )

    _write_parquet_atomically(
        first,
        path,
    )
    _write_parquet_atomically(
        second,
        path,
    )

    restored = pd.read_parquet(path)
    pd.testing.assert_frame_equal(
        restored,
        second,
    )


def test_write_csv_atomically_creates_parent_and_writes_data(
    tmp_path: Path,
) -> None:
    path = tmp_path / "nested" / "result.csv"
    frame = pd.DataFrame(
        {
            "order_id": ["O-1", "O-2"],
            "revenue": [100.0, 200.0],
        }
    )

    _write_csv_atomically(
        frame,
        path,
    )

    assert path.exists()
    restored = pd.read_csv(path)

    pd.testing.assert_frame_equal(
        restored,
        frame,
    )


def test_write_csv_atomically_replaces_existing_file(
    tmp_path: Path,
) -> None:
    path = tmp_path / "result.csv"

    first = pd.DataFrame(
        {
            "order_id": ["O-1"],
            "revenue": [100.0],
        }
    )
    second = pd.DataFrame(
        {
            "order_id": ["O-2"],
            "revenue": [250.0],
        }
    )

    _write_csv_atomically(
        first,
        path,
    )
    _write_csv_atomically(
        second,
        path,
    )

    restored = pd.read_csv(path)
    pd.testing.assert_frame_equal(
        restored,
        second,
    )


def test_write_parquet_atomically_wraps_writer_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "result.parquet"
    frame = pd.DataFrame(
        {
            "order_id": ["O-1"],
            "revenue": [100.0],
        }
    )

    def fail_to_write_parquet(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(
        pd.DataFrame,
        "to_parquet",
        fail_to_write_parquet,
    )

    with pytest.raises(
        PipelineError,
        match="Failed to write Parquet output",
    ):
        _write_parquet_atomically(
            frame,
            path,
        )

    assert not path.exists()
    assert not list(path.parent.glob(".result.parquet.tmp-*"))


def test_write_csv_atomically_wraps_writer_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "result.csv"
    frame = pd.DataFrame(
        {
            "order_id": ["O-1"],
            "revenue": [100.0],
        }
    )

    def fail_to_write_csv(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(
        pd.DataFrame,
        "to_csv",
        fail_to_write_csv,
    )

    with pytest.raises(
        PipelineError,
        match="Failed to write CSV output",
    ):
        _write_csv_atomically(
            frame,
            path,
        )

    assert not path.exists()
    assert not list(path.parent.glob(".result.csv.tmp-*"))


def test_main_returns_zero_on_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "src.pipeline.run_pipeline",
        lambda: None,
    )

    assert main() == 0


def test_main_returns_one_on_pipeline_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "src.pipeline.run_pipeline",
        lambda: (_ for _ in ()).throw(
            PipelineError("pipeline failed")
        ),
    )

    assert main() == 1


def test_run_pipeline_returns_rejected_records_separately(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(tmp_path)
    orders = make_orders()
    orders.loc[0, "amount"] = -25.0

    write_inputs(
        pipeline_config,
        orders=orders,
    )

    monkeypatch.setattr(
        "src.pipeline._write_outputs",
        lambda *args, **kwargs: None,
    )

    result = run_pipeline(
        pipeline_config,
    )

    assert len(result.rejected_orders) == 1
    assert result.rejected_orders.loc[0, "order_id"] == "O-1"
    assert "O-1" not in result.enriched_orders[
        "order_id"
    ].tolist()


def test_run_pipeline_preserves_report_grain_and_columns(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline_config = make_config(tmp_path)
    write_inputs(pipeline_config)

    monkeypatch.setattr(
        "src.pipeline._write_outputs",
        lambda *args, **kwargs: None,
    )

    result = run_pipeline(
        pipeline_config,
    )

    assert list(result.reports.daily_sales.columns) == [
        "order_date",
        "order_count",
        "customer_count",
        "revenue",
        "average_order_value",
    ]
    assert list(result.reports.customer_sales.columns) == [
        "customer_id",
        "order_count",
        "revenue",
        "average_order_value",
    ]
    assert list(result.reports.product_sales.columns) == [
        "product_id",
        "order_count",
        "revenue",
        "average_order_value",
    ]