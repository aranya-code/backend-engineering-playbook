# API Data Processing Pipeline

A production-oriented Pandas pipeline that ingests paginated REST API data with retry logic, normalizes and validates the response payload, applies business transformations, and writes typed Parquet outputs.

---

## Overview

This project demonstrates how to build a reliable data pipeline that treats an external REST API as its source. It covers authenticated HTTP ingestion with exponential backoff, paginated data collection, JSON-to-DataFrame normalization, schema validation, business transformation, and atomic Parquet publication.

The same patterns appear in backend engineering jobs that connect internal data stores to external APIs, sync CRM systems, process webhook payloads, or build data products from SaaS platforms.

---

## Architecture

```text
REST API (paginated)
       │
       ▼
   HTTP Client
   (auth · timeouts · retries · backoff · pagination)
       │
       ▼
   Ingestion
   (collect pages · validate HTTP responses)
       │
       ▼
   Normalization
   (JSON → DataFrame · timestamps · numerics · identifiers)
       │
       ▼
   Validation
   (schema · domain rules · missing values · type enforcement)
       │
       ├──── rejected_records.csv
       │
       ▼
   Transformation
   (business rules · derived columns · deduplication)
       │
       ▼
   Storage
   (atomic Parquet + CSV writes · directory management)
       │
       ▼
   Reports
   (normalized_data.parquet · processing_report.parquet)
```

### Source Modules

| Module | Responsibility |
|---|---|
| `src/client.py` | HTTP client with authentication, timeouts, retries, and exponential backoff |
| `src/ingestion.py` | Paginated API traversal and raw response collection |
| `src/normalization.py` | JSON payload normalization into typed DataFrames |
| `src/validation.py` | Schema enforcement and data-quality checks |
| `src/transformation.py` | Business logic, derived columns, and deduplication |
| `src/storage.py` | Atomic Parquet/CSV writes and directory creation |
| `src/pipeline.py` | End-to-end orchestration |
| `src/config.py` | Typed runtime configuration with environment-variable overrides |
| `src/logging_config.py` | Structured logging setup |

---

## Project Structure

```text
02- API Data Processing Pipeline/
├── config/
│   ├── settings.yaml       # Baseline operational configuration
│   ├── pyproject.toml      # Project metadata and tooling
│   ├── .gitignore
│   └── README.md           # Configuration reference
├── scripts/
│   └── run_pipeline.py     # CLI entry point
├── src/
│   ├── __init__.py
│   ├── client.py
│   ├── config.py
│   ├── ingestion.py
│   ├── logging_config.py
│   ├── normalization.py
│   ├── pipeline.py
│   ├── storage.py
│   ├── transformation.py
│   └── validation.py
└── tests/
    ├── __init__.py
    ├── test_client.py
    ├── test_ingestion.py
    ├── test_normalization.py
    ├── test_pipeline.py
    ├── test_transformation.py
    └── test_validation.py
```

---

## Key Concepts Demonstrated

### Reliable HTTP Client

The HTTP client is built around the real-world requirements of calling external APIs under production conditions:

- **Authentication** — Bearer token supplied via `API_TOKEN` environment variable, never hardcoded
- **Timeouts** — Separate connect and read timeouts prevent indefinite hangs
- **Retries with exponential backoff** — Transient failures (`429`, `500`, `502`, `503`, `504`) are retried with configurable backoff; permanent failures (`401`, `403`, `404`) are not retried
- **Pagination** — Collects all pages up to a configurable `max_pages` safety limit

```text
Request
   ↓
Success?  ──── Yes ──→ Return response
   │
   No
   ↓
Retryable status?  ──── No ──→ Raise PermanentError
   │
   Yes
   ↓
Retries exhausted?  ──── Yes ──→ Raise RetryError
   │
   No
   ↓
Backoff sleep
   ↓
Retry
```

### JSON Normalization

API responses are JSON, not DataFrames. The normalization layer handles:

- Flattening nested JSON structures into columnar DataFrames
- Parsing timestamps from ISO-8601 strings to timezone-aware `datetime64`
- Coercing numeric fields to correct Pandas dtypes
- Preserving string identifiers (order IDs, customer IDs) without numeric conversion

This separation means the ingestion layer stays simple (collect raw data) while normalization handles the schema contract explicitly.

### Schema Validation and Rejected Records

All normalized data is validated before transformation:

- Required column presence
- Type conformance
- Null/missing value policy
- Domain rule enforcement (e.g., non-negative amounts)

Invalid records are written to `rejected_records.csv` so they can be inspected, re-ingested, or escalated without blocking the rest of the pipeline.

### Transformation

Validated records go through business-rule transformation:

- Derived columns (e.g., enriched status labels, revenue tiers)
- Deduplication by business key
- Cross-column consistency checks

### Atomic Outputs

All outputs are written atomically — to a temporary file first, then moved into place. Consumers (scheduled jobs, dashboards, downstream pipelines) always see either a complete previous version or a complete new version.

---

## Configuration

| Setting | Default | Purpose |
|---|---|---|
| `API_BASE_URL` | `https://api.example.com` | API endpoint |
| `API_TOKEN` | (unset) | Bearer authentication token |
| `API_CONNECT_TIMEOUT_SECONDS` | `10.0` | Connection timeout |
| `API_READ_TIMEOUT_SECONDS` | `30.0` | Read timeout |
| `API_MAX_RETRIES` | `3` | Maximum retry attempts |
| `API_BACKOFF_FACTOR` | `1.0` | Exponential backoff factor |
| `API_PAGE_SIZE` | `100` | Records per page |
| `API_MAX_PAGES` | `10000` | Maximum pages per run |
| `DROP_INVALID_RECORDS` | `false` | Quarantine vs. abort on bad records |
| `FAIL_ON_HTTP_ERROR` | `true` | Abort on unrecoverable HTTP failures |
| `FAIL_ON_SCHEMA_ERROR` | `true` | Abort on schema violations |
| `LOG_LEVEL` | `INFO` | Application log level |

> **Never commit `API_TOKEN` or any credentials to `settings.yaml` or source control.** Use environment variables or a managed secret provider.

See [`config/README.md`](config/README.md) for the full configuration reference.

---

## Requirements

- Python ≥ 3.11
- pandas ≥ 2.2, < 3.0
- pyarrow ≥ 16, < 22
- requests ≥ 2.32, < 3.0
- PyYAML ≥ 6.0, < 7.0

---

## Installation

```bash
pip install -e ".[dev]"
```

---

## Running the Pipeline

```bash
# Set credentials
export API_BASE_URL="https://api.example.com/orders"
export API_TOKEN="your-token"

# Run with script
python scripts/run_pipeline.py

# Pass the endpoint directly
python scripts/run_pipeline.py "https://api.example.com/orders"

# Use the installed entry point
run-pipeline "https://api.example.com/orders"
```

---

## Running Tests

Tests use mocked API responses and isolated temporary directories — no production credentials or network access required.

```bash
# Full test suite
pytest

# With coverage
pytest --cov=src --cov-report=term-missing

# Specific module
pytest tests/test_client.py
pytest tests/test_validation.py
```

---

## Production Considerations

| Concern | Approach |
|---|---|
| Reliability | Bounded retries, exponential backoff, separate connect/read timeouts |
| Security | Bearer token via env var; never in YAML or logs |
| Data quality | Schema validation, rejected-record quarantine, fail-fast on schema errors |
| Scalability | Paginated ingestion; for very large APIs, consider incremental extraction |
| Observability | Structured logging, per-stage metrics (records fetched, normalized, rejected, transformed) |
| Deployment | Container-friendly — all secrets and paths via environment variables |

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
| ↳ [01](../01-%20E-Commerce%20Data%20Pipeline/README.md) | E-Commerce Data Pipeline |
| ↳ [02](README.md) | API Data Processing Pipeline |
| ↳ [03](../03-%20Large%20Dataset%20Processing/README.md) | Large Dataset Processing |
