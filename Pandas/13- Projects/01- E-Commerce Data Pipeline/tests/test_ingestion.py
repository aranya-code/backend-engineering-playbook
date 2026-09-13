from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.config import PipelineConfig
from src.ingestion import (
    IngestionError,
    ingest_all,
    ingest_customers,
    ingest_orders,
    ingest_products,
)


def write_csv(
    path: Path,
    frame: pd.DataFrame,
) -> None:
    """Write a test DataFrame to CSV."""
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    frame.to_csv(
        path,
        index=False,
    )


def make_config(
    tmp_path: Path,
    *,
    csv_chunksize: int = 2,
) -> PipelineConfig:
    """Create an isolated pipeline configuration for tests."""
    return PipelineConfig(
        raw_data_dir=tmp_path / "raw",
        staging_data_dir=tmp_path / "staging",
        processed_data_dir=tmp_path / "processed",
        reports_dir=tmp_path / "reports",
        orders_file="orders.csv",
        customers_file="customers.csv",
        products_file="products.csv",
        csv_chunksize=csv_chunksize,
        create_directories=True,
    )


def make_orders() -> pd.DataFrame:
    """Build representative order source data."""
    return pd.DataFrame(
        {
            "order_id": ["O-1", "O-2", "O-3"],
            "customer_id": ["C-1", "C-2", "C-3"],
            "product_id": ["P-1", "P-2", "P-3"],
            "status": [
                "completed",
                "completed",
                "cancelled",
            ],
            "amount": [100.0, 200.0, 50.0],
            "created_at": [
                "2026-01-01T10:00:00Z",
                "2026-01-02T11:00:00Z",
                "2026-01-03T12:00:00Z",
            ],
            "updated_at": [
                "2026-01-01T10:05:00Z",
                "2026-01-02T11:05:00Z",
                "2026-01-03T12:05:00Z",
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


def write_pipeline_inputs(
    pipeline_config: PipelineConfig,
    *,
    orders: pd.DataFrame | None = None,
    customers: pd.DataFrame | None = None,
    products: pd.DataFrame | None = None,
) -> None:
    """Write configured source datasets."""
    write_csv(
        pipeline_config.orders_path,
        orders if orders is not None else make_orders(),
    )
    write_csv(
        pipeline_config.customers_path,
        customers
        if customers is not None
        else make_customers(),
    )
    write_csv(
        pipeline_config.products_path,
        products
        if products is not None
        else make_products(),
    )


def test_ingest_orders_reads_csv_in_chunks(
    tmp_path: Path,
) -> None:
    pipeline_config = make_config(
        tmp_path,
        csv_chunksize=2,
    )
    orders = make_orders()

    write_csv(
        pipeline_config.orders_path,
        orders,
    )

    chunks = ingest_orders(
        pipeline_config,
    )

    assert isinstance(chunks, object)

    collected = list(chunks)

    assert len(collected) == 2
    assert [len(chunk) for chunk in collected] == [2, 1]
    pd.testing.assert_frame_equal(
        pd.concat(
            collected,
            ignore_index=True,
        ),
        orders,
    )


def test_ingest_orders_uses_configured_chunk_size(
    tmp_path: Path,
) -> None:
    pipeline_config = make_config(
        tmp_path,
        csv_chunksize=1,
    )

    write_csv(
        pipeline_config.orders_path,
        make_orders(),
    )

    chunks = list(
        ingest_orders(
            pipeline_config,
        )
    )

    assert len(chunks) == 3
    assert all(len(chunk) == 1 for chunk in chunks)


def test_ingest_customers_reads_reference_data(
    tmp_path: Path,
) -> None:
    pipeline_config = make_config(
        tmp_path,
    )
    customers = make_customers()

    write_csv(
        pipeline_config.customers_path,
        customers,
    )

    result = ingest_customers(
        pipeline_config,
    )

    pd.testing.assert_frame_equal(
        result,
        customers,
    )


def test_ingest_products_reads_reference_data(
    tmp_path: Path,
) -> None:
    pipeline_config = make_config(
        tmp_path,
    )
    products = make_products()

    write_csv(
        pipeline_config.products_path,
        products,
    )

    result = ingest_products(
        pipeline_config,
    )

    pd.testing.assert_frame_equal(
        result,
        products,
    )


@pytest.mark.parametrize(
    "ingest_function, filename",
    [
        (ingest_orders, "orders.csv"),
        (ingest_customers, "customers.csv"),
        (ingest_products, "products.csv"),
    ],
)
def test_missing_input_file_raises_ingestion_error(
    tmp_path: Path,
    ingest_function,
    filename: str,
) -> None:
    pipeline_config = make_config(
        tmp_path,
    )

    with pytest.raises(
        IngestionError,
        match="does not exist",
    ):
        if ingest_function is ingest_orders:
            list(
                ingest_function(
                    pipeline_config,
                )
            )
        else:
            ingest_function(
                pipeline_config,
            )


@pytest.mark.parametrize(
    "ingest_function, path_attribute",
    [
        (ingest_orders, "raw_data_dir"),
        (ingest_customers, "customers_path"),
        (ingest_products, "products_path"),
    ],
)
def test_input_directory_is_rejected(
    tmp_path: Path,
    ingest_function,
    path_attribute: str,
) -> None:
    pipeline_config = make_config(
        tmp_path,
    )

    path = getattr(
        pipeline_config,
        path_attribute,
    )

    if path.suffix:
        path.unlink(
            missing_ok=True,
        )
        path.mkdir(
            parents=True,
            exist_ok=True,
        )
    else:
        path.mkdir(
            parents=True,
            exist_ok=True,
        )

    with pytest.raises(
        IngestionError,
        match="not a file",
    ):
        if ingest_function is ingest_orders:
            list(
                ingest_function(
                    pipeline_config,
                )
            )
        else:
            ingest_function(
                pipeline_config,
            )


@pytest.mark.parametrize(
    "ingest_function, path",
    [
        (
            ingest_customers,
            "customers_path",
        ),
        (
            ingest_products,
            "products_path",
        ),
    ],
)
def test_malformed_csv_raises_ingestion_error(
    tmp_path: Path,
    ingest_function,
    path: str,
) -> None:
    pipeline_config = make_config(
        tmp_path,
    )

    csv_path = getattr(
        pipeline_config,
        path,
    )
    csv_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    csv_path.write_text(
        'customer_id,segment\n"C-1,"premium\n',
        encoding="utf-8",
    )

    with pytest.raises(
        IngestionError,
        match="Failed to read CSV input",
    ):
        ingest_function(
            pipeline_config,
        )


def test_ingest_orders_handles_empty_csv(
    tmp_path: Path,
) -> None:
    pipeline_config = make_config(
        tmp_path,
    )

    pipeline_config.orders_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    pipeline_config.orders_path.write_text(
        "",
        encoding="utf-8",
    )

    with pytest.raises(
        IngestionError,
        match="Failed to read CSV input",
    ):
        list(
            ingest_orders(
                pipeline_config,
            )
        )


def test_ingest_all_loads_all_sources(
    tmp_path: Path,
) -> None:
    pipeline_config = make_config(
        tmp_path,
    )
    orders = make_orders()
    customers = make_customers()
    products = make_products()

    write_pipeline_inputs(
        pipeline_config,
        orders=orders,
        customers=customers,
        products=products,
    )

    order_chunks, customer_result, product_result = ingest_all(
        pipeline_config,
    )

    pd.testing.assert_frame_equal(
        pd.concat(
            list(order_chunks),
            ignore_index=True,
        ),
        orders,
    )
    pd.testing.assert_frame_equal(
        customer_result,
        customers,
    )
    pd.testing.assert_frame_equal(
        product_result,
        products,
    )


def test_ingest_all_creates_pipeline_directories(
    tmp_path: Path,
) -> None:
    pipeline_config = make_config(
        tmp_path,
    )

    write_pipeline_inputs(
        pipeline_config,
    )

    pipeline_config.raw_data_dir.rmdir()
    pipeline_config.staging_data_dir.rmdir()
    pipeline_config.processed_data_dir.rmdir()
    pipeline_config.reports_dir.rmdir()

    ingest_all(
        pipeline_config,
    )

    assert pipeline_config.raw_data_dir.exists()
    assert pipeline_config.staging_data_dir.exists()
    assert pipeline_config.processed_data_dir.exists()
    assert pipeline_config.reports_dir.exists()


def test_ingestion_does_not_modify_source_files(
    tmp_path: Path,
) -> None:
    pipeline_config = make_config(
        tmp_path,
    )
    orders = make_orders()
    customers = make_customers()
    products = make_products()

    write_pipeline_inputs(
        pipeline_config,
        orders=orders,
        customers=customers,
        products=products,
    )

    original_orders_bytes = (
        pipeline_config.orders_path.read_bytes()
    )
    original_customers_bytes = (
        pipeline_config.customers_path.read_bytes()
    )
    original_products_bytes = (
        pipeline_config.products_path.read_bytes()
    )

    list(
        ingest_orders(
            pipeline_config,
        )
    )
    ingest_customers(
        pipeline_config,
    )
    ingest_products(
        pipeline_config,
    )

    assert (
        pipeline_config.orders_path.read_bytes()
        == original_orders_bytes
    )
    assert (
        pipeline_config.customers_path.read_bytes()
        == original_customers_bytes
    )
    assert (
        pipeline_config.products_path.read_bytes()
        == original_products_bytes
    )

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.config import PipelineConfig
from src.ingestion import (
    IngestionError,
    ingest_all,
    ingest_customers,
    ingest_orders,
    ingest_products,
)


def write_csv(
    path: Path,
    frame: pd.DataFrame,
) -> None:
    """Write a test DataFrame to CSV."""
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    frame.to_csv(
        path,
        index=False,
    )


def make_config(
    tmp_path: Path,
    *,
    csv_chunksize: int = 2,
) -> PipelineConfig:
    """Create an isolated pipeline configuration for tests."""
    return PipelineConfig(
        raw_data_dir=tmp_path / "raw",
        staging_data_dir=tmp_path / "staging",
        processed_data_dir=tmp_path / "processed",
        reports_dir=tmp_path / "reports",
        orders_file="orders.csv",
        customers_file="customers.csv",
        products_file="products.csv",
        csv_chunksize=csv_chunksize,
        create_directories=True,
    )


def make_orders() -> pd.DataFrame:
    """Build representative order source data."""
    return pd.DataFrame(
        {
            "order_id": ["O-1", "O-2", "O-3"],
            "customer_id": ["C-1", "C-2", "C-3"],
            "product_id": ["P-1", "P-2", "P-3"],
            "status": [
                "completed",
                "completed",
                "cancelled",
            ],
            "amount": [100.0, 200.0, 50.0],
            "created_at": [
                "2026-01-01T10:00:00Z",
                "2026-01-02T11:00:00Z",
                "2026-01-03T12:00:00Z",
            ],
            "updated_at": [
                "2026-01-01T10:05:00Z",
                "2026-01-02T11:05:00Z",
                "2026-01-03T12:05:00Z",
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


def write_pipeline_inputs(
    pipeline_config: PipelineConfig,
    *,
    orders: pd.DataFrame | None = None,
    customers: pd.DataFrame | None = None,
    products: pd.DataFrame | None = None,
) -> None:
    """Write configured source datasets."""
    write_csv(
        pipeline_config.orders_path,
        orders if orders is not None else make_orders(),
    )
    write_csv(
        pipeline_config.customers_path,
        customers
        if customers is not None
        else make_customers(),
    )
    write_csv(
        pipeline_config.products_path,
        products
        if products is not None
        else make_products(),
    )


def test_ingest_orders_reads_csv_in_chunks(
    tmp_path: Path,
) -> None:
    pipeline_config = make_config(
        tmp_path,
        csv_chunksize=2,
    )
    orders = make_orders()

    write_csv(
        pipeline_config.orders_path,
        orders,
    )

    chunks = ingest_orders(
        pipeline_config,
    )

    assert isinstance(chunks, object)

    collected = list(chunks)

    assert len(collected) == 2
    assert [len(chunk) for chunk in collected] == [2, 1]
    pd.testing.assert_frame_equal(
        pd.concat(
            collected,
            ignore_index=True,
        ),
        orders,
    )


def test_ingest_orders_uses_configured_chunk_size(
    tmp_path: Path,
) -> None:
    pipeline_config = make_config(
        tmp_path,
        csv_chunksize=1,
    )

    write_csv(
        pipeline_config.orders_path,
        make_orders(),
    )

    chunks = list(
        ingest_orders(
            pipeline_config,
        )
    )

    assert len(chunks) == 3
    assert all(len(chunk) == 1 for chunk in chunks)


def test_ingest_customers_reads_reference_data(
    tmp_path: Path,
) -> None:
    pipeline_config = make_config(
        tmp_path,
    )
    customers = make_customers()

    write_csv(
        pipeline_config.customers_path,
        customers,
    )

    result = ingest_customers(
        pipeline_config,
    )

    pd.testing.assert_frame_equal(
        result,
        customers,
    )


def test_ingest_products_reads_reference_data(
    tmp_path: Path,
) -> None:
    pipeline_config = make_config(
        tmp_path,
    )
    products = make_products()

    write_csv(
        pipeline_config.products_path,
        products,
    )

    result = ingest_products(
        pipeline_config,
    )

    pd.testing.assert_frame_equal(
        result,
        products,
    )


@pytest.mark.parametrize(
    "ingest_function, filename",
    [
        (ingest_orders, "orders.csv"),
        (ingest_customers, "customers.csv"),
        (ingest_products, "products.csv"),
    ],
)
def test_missing_input_file_raises_ingestion_error(
    tmp_path: Path,
    ingest_function,
    filename: str,
) -> None:
    pipeline_config = make_config(
        tmp_path,
    )

    with pytest.raises(
        IngestionError,
        match="does not exist",
    ):
        if ingest_function is ingest_orders:
            list(
                ingest_function(
                    pipeline_config,
                )
            )
        else:
            ingest_function(
                pipeline_config,
            )


@pytest.mark.parametrize(
    "ingest_function, path_attribute",
    [
        (ingest_orders, "raw_data_dir"),
        (ingest_customers, "customers_path"),
        (ingest_products, "products_path"),
    ],
)
def test_input_directory_is_rejected(
    tmp_path: Path,
    ingest_function,
    path_attribute: str,
) -> None:
    pipeline_config = make_config(
        tmp_path,
    )

    path = getattr(
        pipeline_config,
        path_attribute,
    )

    if path.suffix:
        path.unlink(
            missing_ok=True,
        )
        path.mkdir(
            parents=True,
            exist_ok=True,
        )
    else:
        path.mkdir(
            parents=True,
            exist_ok=True,
        )

    with pytest.raises(
        IngestionError,
        match="not a file",
    ):
        if ingest_function is ingest_orders:
            list(
                ingest_function(
                    pipeline_config,
                )
            )
        else:
            ingest_function(
                pipeline_config,
            )


@pytest.mark.parametrize(
    "ingest_function, path",
    [
        (
            ingest_customers,
            "customers_path",
        ),
        (
            ingest_products,
            "products_path",
        ),
    ],
)
def test_malformed_csv_raises_ingestion_error(
    tmp_path: Path,
    ingest_function,
    path: str,
) -> None:
    pipeline_config = make_config(
        tmp_path,
    )

    csv_path = getattr(
        pipeline_config,
        path,
    )
    csv_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    csv_path.write_text(
        'customer_id,segment\n"C-1,"premium\n',
        encoding="utf-8",
    )

    with pytest.raises(
        IngestionError,
        match="Failed to read CSV input",
    ):
        ingest_function(
            pipeline_config,
        )


def test_ingest_orders_handles_empty_csv(
    tmp_path: Path,
) -> None:
    pipeline_config = make_config(
        tmp_path,
    )

    pipeline_config.orders_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    pipeline_config.orders_path.write_text(
        "",
        encoding="utf-8",
    )

    with pytest.raises(
        IngestionError,
        match="Failed to read CSV input",
    ):
        list(
            ingest_orders(
                pipeline_config,
            )
        )


def test_ingest_all_loads_all_sources(
    tmp_path: Path,
) -> None:
    pipeline_config = make_config(
        tmp_path,
    )
    orders = make_orders()
    customers = make_customers()
    products = make_products()

    write_pipeline_inputs(
        pipeline_config,
        orders=orders,
        customers=customers,
        products=products,
    )

    order_chunks, customer_result, product_result = ingest_all(
        pipeline_config,
    )

    pd.testing.assert_frame_equal(
        pd.concat(
            list(order_chunks),
            ignore_index=True,
        ),
        orders,
    )
    pd.testing.assert_frame_equal(
        customer_result,
        customers,
    )
    pd.testing.assert_frame_equal(
        product_result,
        products,
    )


def test_ingest_all_creates_pipeline_directories(
    tmp_path: Path,
) -> None:
    pipeline_config = make_config(
        tmp_path,
    )

    write_pipeline_inputs(
        pipeline_config,
    )

    pipeline_config.raw_data_dir.rmdir()
    pipeline_config.staging_data_dir.rmdir()
    pipeline_config.processed_data_dir.rmdir()
    pipeline_config.reports_dir.rmdir()

    ingest_all(
        pipeline_config,
    )

    assert pipeline_config.raw_data_dir.exists()
    assert pipeline_config.staging_data_dir.exists()
    assert pipeline_config.processed_data_dir.exists()
    assert pipeline_config.reports_dir.exists()


def test_ingestion_does_not_modify_source_files(
    tmp_path: Path,
) -> None:
    pipeline_config = make_config(
        tmp_path,
    )
    orders = make_orders()
    customers = make_customers()
    products = make_products()

    write_pipeline_inputs(
        pipeline_config,
        orders=orders,
        customers=customers,
        products=products,
    )

    original_orders_bytes = (
        pipeline_config.orders_path.read_bytes()
    )
    original_customers_bytes = (
        pipeline_config.customers_path.read_bytes()
    )
    original_products_bytes = (
        pipeline_config.products_path.read_bytes()
    )

    list(
        ingest_orders(
            pipeline_config,
        )
    )
    ingest_customers(
        pipeline_config,
    )
    ingest_products(
        pipeline_config,
    )

    assert (
        pipeline_config.orders_path.read_bytes()
        == original_orders_bytes
    )
    assert (
        pipeline_config.customers_path.read_bytes()
        == original_customers_bytes
    )
    assert (
        pipeline_config.products_path.read_bytes()
        == original_products_bytes
    )