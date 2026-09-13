# Projects

Applied Pandas projects that put the skills from earlier sections to work in realistic, production-style scenarios. Each project is a self-contained Python package with a full source tree, tests, configuration, and a CLI entry point.

---

## Projects

### [01 — E-Commerce Data Pipeline](01-%20E-Commerce%20Data%20Pipeline/README.md)

Ingests orders, customers, and product CSVs using chunked reading, validates schema and referential integrity, enriches orders through joins, aggregates revenue across three reporting dimensions (daily, customer, product), and publishes Parquet reports with reconciliation.

**Key skills:** chunked ingestion · validation · enrichment joins · multi-level aggregation · atomic writes · reconciliation

---

### [02 — API Data Processing Pipeline](02-%20API%20Data%20Processing%20Pipeline/README.md)

Collects paginated REST API data with an authenticated HTTP client, applies exponential-backoff retry logic, normalizes JSON payloads into typed DataFrames, validates and transforms records, and writes Parquet outputs atomically.

**Key skills:** HTTP client with retries and backoff · pagination · JSON normalization · schema validation · rejected-record quarantine · atomic writes

---

### [03 — Large Dataset Processing](03-%20Large%20Dataset%20Processing/README.md)

Processes large CSV datasets without loading them entirely into memory. Uses chunked reads, column projection, categorical dtype optimization, per-chunk validation, deterministic partition writes, checkpoint-based crash recovery, and a benchmark suite for measuring throughput and memory usage.

**Key skills:** chunked processing · column projection · categorical dtypes · checkpointing and resume · partition writes · memory benchmarking

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
| ↳ [01](01-%20E-Commerce%20Data%20Pipeline/README.md) | E-Commerce Data Pipeline |
| ↳ [02](02-%20API%20Data%20Processing%20Pipeline/README.md) | API Data Processing Pipeline |
| ↳ [03](03-%20Large%20Dataset%20Processing/README.md) | Large Dataset Processing |
