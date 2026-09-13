# E-Commerce Data Pipeline

A production-oriented Pandas pipeline that ingests order, customer, and product CSV data, applies validation and enrichment, and publishes Parquet sales reports.

---

## Overview

This project demonstrates a realistic backend data pipeline built entirely with Pandas. It covers chunked ingestion, schema validation, referential integrity checks, data cleaning, business-rule transformation, multi-level aggregation, and atomic report publication — the same concerns that appear in production analytics and ETL systems.

The pipeline reads three raw CSV datasets:

```text
data/raw/
├── orders.csv
├── customers.csv
└── products.csv
```

It produces four outputs:

```text
reports/
├── daily_sales_report.parquet
├── customer_sales_report.parquet
├── product_sales_report.parquet
└── rejected_orders.csv
```

---

## Architecture

```text
orders.csv (chunked)     customers.csv     products.csv
       │                      │                 │
       ▼                      ▼                 ▼
   Ingestion ──────── Reference Data Load ──────┘
       │
       ▼
   Validation
   (schema · status · amount · timestamps · referential integrity)
       │
       ├──── rejected_orders.csv
       │
       ▼
   Cleaning
   (nulls · types · normalization)
       │
       ▼
   Transformation / Enrichment
   (joins · derived columns · order value)
       │
       ▼
   Aggregation
   (daily · by customer · by product)
       │
       ▼
   Reporting
   (Parquet reports · reconciliation)
       │
       ▼
   Atomic Publication
```

### Source Modules

| Module | Responsibility |
|---|---|
| `src/ingestion.py` | Chunked CSV loading and reference dataset ingestion |
| `src/validation.py` | Schema, domain, timestamp, and referential-integrity checks |
| `src/cleaning.py` | Null handling, dtype coercion, string normalization |
| `src/transformation.py` | Order enrichment with customer and product attributes |
| `src/aggregation.py` | Daily, customer, and product-level metric aggregation |
| `src/reporting.py` | Report building, reconciliation, and file publication |
| `src/pipeline.py` | Orchestration — runs the complete pipeline end to end |
| `src/config.py` | Runtime configuration object with environment-variable overrides |

---

## Project Structure

```text
01- E-Commerce Data Pipeline/
├── config/
│   ├── settings.yaml       # Baseline operational configuration
│   ├── pyproject.toml      # Project metadata and tooling
│   ├── .gitignore
│   └── README.md           # Configuration reference
├── scripts/
│   └── run_pipeline.py     # CLI entry point
├── src/
│   ├── __init__.py
│   ├── aggregation.py
│   ├── cleaning.py
│   ├── config.py
│   ├── ingestion.py
│   ├── pipeline.py
│   ├── reporting.py
│   ├── transformation.py
│   └── validation.py
└── tests/
    ├── __init__.py
    ├── test_aggregation.py
    ├── test_cleaning.py
    ├── test_ingestion.py
    ├── test_pipeline.py
    ├── test_transformation.py
    └── test_validation.py
```

---

## Key Concepts Demonstrated

### Chunked CSV Ingestion

Orders are read in configurable chunks rather than loaded entirely into memory. This makes the pipeline suitable for datasets that exceed available RAM:

```python
pd.read_csv("data/raw/orders.csv", chunksize=100_000)
```

Reference datasets (customers, products) are small enough to load once and used as in-memory lookup tables during chunk processing.

### Schema Validation

Before any transformation runs, every chunk is checked for:

- Required columns (`order_id`, `customer_id`, `product_id`, `status`, `amount`, `created_at`, `updated_at`)
- Valid order statuses (`pending`, `completed`, `cancelled`)
- Non-negative amounts
- `updated_at >= created_at` timestamp ordering

Invalid records are quarantined into `rejected_orders.csv` and optionally fail the pipeline, depending on the `fail_on_invalid_records` setting.

### Referential Integrity

Every `customer_id` in the orders dataset must exist in `customers.csv`. Orphaned records are rejected rather than silently dropped or processed with missing attributes.

### Enrichment and Transformation

Valid, cleaned orders are joined with customer and product reference data to produce an enriched DataFrame with derived columns that support multi-dimensional reporting.

### Aggregation and Reporting

Three report types are produced:

| Report | Grain | Key Metrics |
|---|---|---|
| Daily Sales | Order date | Revenue, order count, average order value |
| Customer Sales | Customer | Lifetime revenue, order count |
| Product Sales | Product | Units sold, product revenue |

All Parquet outputs are written atomically — written to a temporary file first and then replaced into the final destination to protect downstream consumers from partially written files.

### Reconciliation

After report generation, pipeline metrics are reconciled: the sum of completed-order revenue across all reports must match the source data within a configurable tolerance (`0.01` by default). This verifies that no revenue was silently lost during aggregation.

---

## Configuration

The pipeline is configured through `config/settings.yaml` and supports environment-variable overrides at runtime.

Key configuration options:

| Setting | Default | Purpose |
|---|---|---|
| `csv_chunksize` | `100000` | Rows per ingestion chunk |
| `report_timezone` | `UTC` | Timestamp normalization |
| `fail_on_invalid_records` | `false` | Quarantine vs. abort on bad records |
| `reconciliation.enabled` | `true` | Validate report totals against source |
| `reconciliation.tolerance` | `0.01` | Allowed revenue rounding difference |
| `atomic_writes` | `true` | Protect consumers from partial outputs |

Environment variable overrides:

```bash
PANDAS_CSV_CHUNKSIZE=50000
FAIL_ON_INVALID_RECORDS=true
REPORT_TIMEZONE=UTC
LOG_LEVEL=DEBUG
```

See [`config/README.md`](config/README.md) for the full configuration reference.

---

## Requirements

- Python ≥ 3.11
- pandas ≥ 2.2, < 3.0
- pyarrow ≥ 16, < 22
- PyYAML ≥ 6.0, < 7.0

---

## Installation

```bash
# From the project root
pip install -e ".[dev]"
```

---

## Running the Pipeline

```bash
# Using the script
python scripts/run_pipeline.py

# Using the installed CLI entry point
run-pipeline

# Override chunk size
PANDAS_CSV_CHUNKSIZE=25000 python scripts/run_pipeline.py

# Fail on any invalid record
FAIL_ON_INVALID_RECORDS=true python scripts/run_pipeline.py
```

Place the input files in `data/raw/` before running. The pipeline creates all required directories automatically.

---

## Running Tests

```bash
# Full test suite
pytest

# With coverage report
pytest --cov=src --cov-report=term-missing

# Integration tests only
pytest -m integration

# Single module
pytest tests/test_validation.py
```

---

## Data Quality Design

The pipeline is designed to surface data-quality problems rather than hide them:

- **Schema failures** are caught before expensive transformations
- **Rejected records** are preserved in `rejected_orders.csv` for inspection and reprocessing
- **Reconciliation** verifies that derived report totals are consistent with source data
- **Atomic writes** ensure consumers never see a half-written report

Silently producing an incorrect report is treated as a worse failure than failing the pipeline loudly.

---

## Production Considerations

| Concern | Approach |
|---|---|
| Memory | Chunked CSV ingestion with configurable chunk size |
| Reliability | Atomic writes, reconciliation, quarantine for bad records |
| Observability | Structured logging, pipeline metrics, reconciliation results |
| Configuration | YAML defaults + environment-variable overrides, no secrets in files |
| Scalability | For very large datasets, replace Pandas chunking with Parquet + column pushdown or a distributed framework |

---

## Navigation

| # | Section |
|---|---|
| [01](../01-%20Fundamentals/README.md) | Fundamentals |
| [02](../02-%20Reading%20and%20Writing%20Data/README.md) | Reading and Writing Data |
| [03](../03-%20Selecting%20and%20Filtering/README.md) | Selecting and Filtering |
| [04](../04-%20Data%20Cleaning/README.md) | Data Cleaning |
| [05](../05-%20Data%20Transformation/README.md) | Data Transformation |
| [06](../06-%20Grouping%20and%20Aggregation/README.md) | Grouping and Aggregation |
| [07](../07-%20Combining%20Data/README.md) | Combining Data |
| [08](../08-%20Sorting%20Ranking%20and%20Statistics/README.md) | Sorting Ranking and Statistics |
| [09](../09-%20Strings%20and%20Datetime/README.md) | Strings and Datetime |
| [10](../10-%20Performance%20and%20Memory/README.md) | Performance and Memory |
| [11](../11-%20Backend%20and%20Data%20Engineering/README.md) | Backend and Data Engineering |
| [12](../12-%20Interview%20Preparation/README.md) | Interview Preparation |
| **13** | **Projects** |
| ↳ [01](README.md) | E-Commerce Data Pipeline |
| ↳ [02](../02-%20API%20Data%20Processing%20Pipeline/README.md) | API Data Processing Pipeline |
| ↳ [03](../03-%20Large%20Dataset%20Processing/README.md) | Large Dataset Processing |
