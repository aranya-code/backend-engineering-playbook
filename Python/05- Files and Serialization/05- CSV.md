# 05- CSV

## Overview

CSV, or Comma-Separated Values, is a simple tabular data interchange format widely used for exports, imports, batch processing, reporting, and data pipelines.

Despite its apparent simplicity, CSV is not merely:

```python
line.split(",")
```

Real CSV data can contain:

- quoted fields
- embedded commas
- embedded newlines
- escaped quotes
- different delimiters
- headers
- missing values
- different encodings
- inconsistent row structures

Python's standard-library `csv` module exists to correctly handle these semantics.

CSV remains valuable because it is:

- human-readable
- easy to inspect
- supported by spreadsheets
- supported by databases
- language-independent
- suitable for batch interchange

However, CSV has weak schema and type semantics compared with formats such as JSON, Parquet, or database tables. Production systems should therefore treat CSV parsing and validation as a data-ingestion boundary.

---

## CSV Data Model

A CSV document conceptually consists of:

```text
CSV File
   │
   ├── Header
   │     ├── order_id
   │     ├── customer_id
   │     └── amount
   │
   ├── Record
   │     ├── 1001
   │     ├── C001
   │     └── 125.50
   │
   └── Record
         ├── 1002
         ├── C002
         └── 250.00
```

Example:

```csv
order_id,customer_id,amount
1001,C001,125.50
1002,C002,250.00
```

CSV itself generally does not encode strong application-level types.

For example:

```text
125.50
```

is typically read as a string:

```python
"125.50"
```

The application must decide whether that value represents:

- `Decimal`
- `float`
- text
- another domain type

This is why CSV parsing and validation are separate concerns.

---

## Why Use the `csv` Module

Do not parse CSV using:

```python
line.split(",")
```

This fails when a field contains a comma:

```csv
1001,"Kolkata, India",125.50
```

The correct parser understands quoting and delimiters:

```python
import csv

with open("orders.csv", encoding="utf-8", newline="") as file:
    reader = csv.reader(file)

    for row in reader:
        process(row)
```

The `csv` module implements CSV-specific parsing rules rather than treating the file as ordinary text.

---

## CSV Parsing Lifecycle

A production CSV pipeline typically looks like:

```mermaid
flowchart LR
    A[CSV File] --> B[Open Text Stream]
    B --> C[CSV Parser]
    C --> D[Structural Validation]
    D --> E[Type Conversion]
    E --> F[Domain Validation]
    F --> G[Persistence / Processing]
```

The important separation is:

```text
Parsing
  ≠
Validation
  ≠
Business Logic
```

A syntactically valid CSV row can still contain invalid business data.

---

## Opening CSV Files Correctly

The recommended pattern is:

```python
import csv
from pathlib import Path

path = Path("orders.csv")

with path.open(
    "r",
    encoding="utf-8",
    newline="",
) as file:
    reader = csv.DictReader(file)

    for row in reader:
        process(row)
```

The important settings are:

- text mode
- explicit encoding
- `newline=""`

The CSV documentation recommends `newline=""` so the CSV module can handle newline semantics itself.

---

## `csv.reader`

`csv.reader` returns each row as a list of strings.

```python
import csv

with open("orders.csv", encoding="utf-8", newline="") as file:
    reader = csv.reader(file)

    for row in reader:
        print(row)
```

Example result:

```python
["1001", "C001", "125.50"]
["1002", "C002", "250.00"]
```

Use `reader` when column positions are stable and positional access is appropriate.

---

## `csv.DictReader`

`DictReader` maps columns to dictionary keys.

```python
import csv

with open("orders.csv", encoding="utf-8", newline="") as file:
    reader = csv.DictReader(file)

    for row in reader:
        print(row["order_id"])
        print(row["amount"])
```

A row resembles:

```python
{
    "order_id": "1001",
    "customer_id": "C001",
    "amount": "125.50",
}
```

This is usually easier to maintain because code refers to column names rather than numeric positions.

---

## Headers

A CSV file may contain a header:

```csv
order_id,customer_id,amount
1001,C001,125.50
1002,C002,250.00
```

`DictReader` automatically uses the first row as field names unless explicitly configured otherwise.

You can provide field names manually:

```python
reader = csv.DictReader(
    file,
    fieldnames=["order_id", "customer_id", "amount"],
)
```

This is useful when the source format has no header.

---

## Header Validation

Do not assume an external CSV has the expected columns.

Validate:

```python
required_columns = {
    "order_id",
    "customer_id",
    "amount",
}

actual_columns = set(reader.fieldnames or [])

missing = required_columns - actual_columns

if missing:
    raise ValueError(
        f"missing required columns: {sorted(missing)}"
    )
```

Production ingestion should also consider:

- unexpected columns
- duplicate headers
- case sensitivity
- whitespace
- versioned schemas

---

## CSV as a Weakly Typed Format

The CSV parser returns strings.

```python
row["amount"]  # "125.50"
```

It does not automatically know that this should be:

```python
Decimal("125.50")
```

Perform explicit conversion:

```python
from decimal import Decimal

amount = Decimal(row["amount"])
```

For identifiers:

```python
order_id = int(row["order_id"])
```

Do not use `float` for financial amounts merely because the CSV contains decimal-looking text.

---

## Parsing Financial Values

For monetary values, `Decimal` is usually more appropriate than `float`.

```python
from decimal import Decimal

amount = Decimal(row["amount"])
```

This avoids many binary floating-point representation issues.

The final representation should match the database and domain model.

For example:

```text
CSV string
   │
   ▼
Decimal
   │
   ▼
PostgreSQL NUMERIC
```

---

## Boolean Conversion

CSV does not have a universal boolean type.

Values may appear as:

```text
true
false
TRUE
FALSE
yes
no
1
0
Y
N
```

Define an explicit contract:

```python
TRUE_VALUES = {"true", "1", "yes", "y"}
FALSE_VALUES = {"false", "0", "no", "n"}


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()

    if normalized in TRUE_VALUES:
        return True

    if normalized in FALSE_VALUES:
        return False

    raise ValueError(f"invalid boolean value: {value!r}")
```

Do not silently interpret arbitrary values as `False`.

---

## Date and Time Values

CSV stores dates as text.

For example:

```csv
order_id,created_at
1001,2026-09-06T10:30:00+00:00
```

Parse them explicitly:

```python
from datetime import datetime

created_at = datetime.fromisoformat(
    row["created_at"]
)
```

A production contract should specify:

- timezone behavior
- accepted formats
- whether timestamps must be UTC
- handling of invalid dates

Avoid ambiguous formats such as:

```text
09/06/26
```

when the producer and consumer may interpret them differently.

---

## Quoting

CSV fields may be quoted:

```csv
order_id,customer_name
1001,"Smith, John"
```

The CSV parser handles this correctly:

```python
with open("customers.csv", encoding="utf-8", newline="") as file:
    reader = csv.DictReader(file)

    for row in reader:
        print(row["customer_name"])
```

Result:

```text
Smith, John
```

Do not implement quoting manually.

---

## Embedded Quotes

CSV supports escaped quotes.

Example:

```csv
id,description
1001,"Customer said ""approved"""
```

The parser returns:

```text
Customer said "approved"
```

This is another reason `split(",")` is not a valid general-purpose CSV parser.

---

## Embedded Newlines

A quoted CSV field can contain a newline:

```csv
id,description
1001,"First line
Second line"
```

A line-oriented parser that assumes every newline terminates a record will break this file.

The `csv` module understands quoted multiline fields.

This is why CSV should be parsed as a structured format rather than processed with generic line splitting.

---

## Delimiters

CSV commonly uses commas, but other delimiters exist:

```text
,
;
\t
|
```

The reader can specify a delimiter:

```python
reader = csv.reader(
    file,
    delimiter=";",
)
```

Do not assume the extension alone defines the delimiter.

Some files use `.csv` while actually using semicolon-delimited records.

---

## Dialects

CSV dialects describe combinations of formatting rules.

Python provides predefined dialects such as:

```python
csv.excel
csv.excel_tab
```

A reader can specify:

```python
reader = csv.reader(
    file,
    dialect="excel",
)
```

For external systems, explicit configuration is often clearer than relying on implicit dialect assumptions.

---

## `csv.Sniffer`

Python provides `csv.Sniffer` to infer certain CSV characteristics.

```python
import csv

sample = file.read(4096)
dialect = csv.Sniffer().sniff(sample)
file.seek(0)

reader = csv.reader(file, dialect)
```

This can be useful for exploratory ingestion, but automatic inference is not a reliable substitute for an explicit data contract.

Inference can fail when:

- samples are ambiguous
- values contain unusual delimiters
- files are small
- formatting is inconsistent

For production pipelines, prefer explicit source configuration whenever possible.

---

## Writing CSV

Use `csv.writer`:

```python
import csv

with open(
    "orders.csv",
    "w",
    encoding="utf-8",
    newline="",
) as file:
    writer = csv.writer(file)

    writer.writerow(
        ["order_id", "customer_id", "amount"]
    )

    writer.writerow(
        ["1001", "C001", "125.50"]
    )
```

The writer handles quoting and escaping according to the configured dialect.

---

## `DictWriter`

For named fields:

```python
import csv

fieldnames = [
    "order_id",
    "customer_id",
    "amount",
]

with open(
    "orders.csv",
    "w",
    encoding="utf-8",
    newline="",
) as file:
    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames,
    )

    writer.writeheader()

    writer.writerow(
        {
            "order_id": "1001",
            "customer_id": "C001",
            "amount": "125.50",
        }
    )
```

This makes export code less dependent on column position.

---

## Extra and Missing Fields

`DictReader` can encounter rows that do not match the header.

For example:

```csv
id,name
1,Alice,unexpected
```

Depending on configuration, extra values may be stored under a special key.

You can explicitly configure:

```python
reader = csv.DictReader(
    file,
    restkey="__extra__",
)
```

Similarly, missing values can be represented with:

```python
restval=""
```

Production ingestion should explicitly decide whether malformed row structures should:

- fail the entire file
- reject individual rows
- quarantine malformed records

---

## Strict Parsing

The CSV parser can use strict mode:

```python
reader = csv.reader(
    file,
    strict=True,
)
```

This can make malformed CSV structures fail instead of being tolerated.

Strictness is useful when the source is contractually expected to be valid.

For uncontrolled external data, a quarantine strategy may be more appropriate than terminating a large batch for one malformed record.

---

## CSV and Schema Validation

A production CSV ingestion system should distinguish:

### Structural validation

Examples:

- expected columns exist
- row has correct shape
- CSV syntax is valid

### Type validation

Examples:

- `order_id` is an integer
- `amount` is a valid decimal
- timestamp is parseable

### Domain validation

Examples:

- amount is non-negative
- order status is allowed
- customer ID exists
- currency is supported

The pipeline becomes:

```text
CSV
 │
 ▼
Structural Validation
 │
 ▼
Type Conversion
 │
 ▼
Domain Validation
 │
 ▼
Business Processing
```

---

## CSV and PostgreSQL

CSV is frequently used to import or export PostgreSQL data.

A typical architecture is:

```text
CSV
 │
 ▼
Validation
 │
 ▼
Staging Table
 │
 ▼
SQL Validation / Transformation
 │
 ▼
Production Tables
```

For large imports, PostgreSQL's `COPY` mechanism is generally more efficient than inserting rows individually through an ORM.

The Python application can still perform validation before or around the database import depending on requirements.

---

## CSV and Django

Django applications may generate CSV exports:

```python
import csv

from django.http import StreamingHttpResponse


def export_orders(request):
    response = StreamingHttpResponse(
        (
            ",".join(["order_id", "status"]) + "\n",
        ),
        content_type="text/csv",
    )

    response["Content-Disposition"] = (
        'attachment; filename="orders.csv"'
    )

    return response
```

For complex CSV generation, use Python's `csv` module rather than manually concatenating values.

For large exports, streaming responses prevent the application from constructing the complete CSV in memory.

---

## CSV and FastAPI

FastAPI can process uploaded CSV files using an upload abstraction and stream or incrementally process the content.

Conceptually:

```text
Client
  │
  │ CSV upload
  ▼
FastAPI
  │
  ▼
Size / type validation
  │
  ▼
Temporary storage or stream
  │
  ▼
CSV parser
  │
  ▼
Validation
  │
  ▼
Database / queue
```

For large files, avoid:

```python
contents = await upload.read()
```

when that would materialize the entire upload in memory.

Use incremental reads or direct-to-object-storage workflows.

---

## CSV and Celery

Large CSV imports are often better processed asynchronously:

```text
API
 │
 ├── validate request
 ├── persist upload
 └── enqueue job
          │
          ▼
       Celery
          │
          ▼
    Stream CSV rows
          │
          ▼
       Validate
          │
          ▼
    Batch database writes
```

This avoids keeping an HTTP request open for a potentially long import.

Track job state such as:

```text
PENDING
RUNNING
COMPLETED
FAILED
PARTIAL
```

when the business workflow requires it.

---

## Batch Database Writes

Writing every CSV row individually can be inefficient:

```python
for row in reader:
    repository.insert(row)
```

For large files, batch operations are usually more efficient.

Conceptually:

```python
batch = []

for row in reader:
    batch.append(transform(row))

    if len(batch) >= 1000:
        repository.bulk_insert(batch)
        batch.clear()

if batch:
    repository.bulk_insert(batch)
```

The optimal batch size depends on:

- database
- row size
- transaction behavior
- network latency
- memory
- lock duration

Measure rather than assuming a universal value.

---

## Transactions and CSV Imports

For critical imports, define transaction boundaries deliberately.

A single transaction for millions of rows may cause:

- large transaction logs
- long locks
- high memory/resource usage
- difficult recovery

Per-row commits are also inefficient.

A common compromise is batch-level transactions:

```text
Rows 1–1000
   │
   ▼
Transaction
   │
   ▼
Commit

Rows 1001–2000
   │
   ▼
Transaction
   │
   ▼
Commit
```

For financial or strongly consistent imports, the correct strategy depends on domain requirements.

---

## Idempotent CSV Processing

A batch job may be retried after failure.

If the same file is processed twice, duplicate records can result.

Use an explicit processing identity such as:

```text
file_id
checksum
source_system
row_number
business_key
```

Possible strategies include:

- unique database constraints
- staging tables
- import manifests
- idempotency keys
- processed-file records

Do not rely solely on filenames because the same filename may be reused.

---

## CSV Checksums

A file checksum can identify content:

```python
import hashlib
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            digest.update(chunk)

    return digest.hexdigest()
```

A checksum can support:

- duplicate detection
- integrity validation
- import identity
- auditability

For large files, calculate the checksum incrementally.

---

## Large CSV Files

Never assume a CSV file is small.

For large files:

```python
with path.open(
    "r",
    encoding="utf-8",
    newline="",
) as file:
    reader = csv.DictReader(file)

    for row in reader:
        process(row)
```

The parser processes records incrementally.

Memory usage is primarily influenced by:

- current row
- parser state
- application state
- batch size

rather than the entire file size.

---

## Streaming CSV Export

Large exports should also be streamed.

Avoid:

```python
rows = list(queryset)
csv_content = generate_csv(rows)
return csv_content
```

This can consume significant memory.

Prefer a streaming architecture:

```text
Database Cursor
      │
      ▼
Batch of Rows
      │
      ▼
CSV Writer
      │
      ▼
HTTP Response Stream
      │
      ▼
Client
```

For very large exports, database cursors and chunked query strategies can prevent excessive memory use.

---

## CSV Injection

CSV files can be opened in spreadsheet applications.

Some spreadsheet applications interpret cells beginning with characters such as:

```text
=
+
-
@
```

as formulas.

If untrusted user input is exported directly into CSV, an attacker may attempt formula injection.

For example:

```csv
name
=HYPERLINK(...)
```

A security-sensitive export pipeline should consider neutralizing dangerous spreadsheet formulas according to the consumer's behavior and requirements.

Do not assume that "CSV is just data" means spreadsheet consumers will treat every field as inert text.

---

## Encoding and BOM

Some CSV files generated by spreadsheet software may contain a UTF-8 BOM.

Python supports:

```python
encoding="utf-8-sig"
```

when BOM-compatible input handling is required.

Example:

```python
with open(
    "export.csv",
    encoding="utf-8-sig",
    newline="",
) as file:
    reader = csv.DictReader(file)
```

Use this only when the source format requires it. Do not blindly add encoding workarounds without understanding the producer.

---

## Excel Compatibility

Spreadsheet applications can have compatibility quirks around:

- encodings
- delimiters
- quoting
- newlines
- dates
- formulas
- large integer identifiers

For exports intended for spreadsheet users, define the expected consumer behavior.

A CSV that is technically valid may still be inconvenient or unsafe when opened by a particular spreadsheet application.

---

## CSV and Leading Zeros

CSV does not preserve semantic numeric types.

For example:

```csv
account_number
001234
```

If a consumer interprets this as an integer, it may become:

```text
1234
```

For identifiers, preserve them as strings:

```python
account_number = row["account_number"]
```

Do not automatically convert every numeric-looking field to `int`.

Identifiers are often not numbers semantically.

---

## CSV and Large Integers

Identifiers may exceed the safe numeric range of downstream systems.

For example:

```text
12345678901234567890
```

Treat identifiers according to their domain semantics.

If an ID is an identifier rather than a quantity, keeping it as a string can prevent accidental numeric conversion and precision loss in downstream tools.

---

## CSV and Missing Values

CSV has no universal null representation.

Common representations include:

```text
empty string
NULL
null
N/A
NA
-
```

Define the source contract.

For example:

```python
def parse_optional(value: str) -> str | None:
    value = value.strip()

    return value if value else None
```

Do not assume that every string such as `"N/A"` should become `None`.

---

## Data Quality Monitoring

Production CSV ingestion should measure:

- files received
- files processed
- files rejected
- rows processed
- rows rejected
- missing columns
- invalid values
- duplicate records
- processing duration
- throughput
- database failures

Example:

```text
Import Job
 │
 ├── 1,000,000 rows received
 ├── 998,450 rows accepted
 ├── 1,550 rows rejected
 └── 12 rows structurally invalid
```

These metrics make data-quality problems operationally visible.

---

## Error Handling

A robust import pipeline should distinguish:

```text
File-level failure
    │
    ├── unreadable file
    ├── invalid encoding
    └── invalid CSV structure

Row-level failure
    │
    ├── invalid type
    ├── missing value
    └── domain violation
```

The recovery policy should be explicit.

For example:

```text
Invalid file → reject entire import

Invalid row → quarantine row and continue
```

This is appropriate only when the business process permits partial success.

---

## Quarantine Files

Invalid records can be written to a separate output:

```text
imports/
    incoming/
        orders.csv
    processed/
        orders.csv
    rejected/
        orders-errors.csv
```

Rejected records should ideally include:

```text
row number
error code
error message
original values
import ID
```

Avoid exposing sensitive source data unnecessarily.

---

## CSV and Object Storage

Large CSV files are commonly stored in S3:

```text
S3
 │
 ├── incoming/
 │      └── orders-2026-09-06.csv
 │
 ├── processed/
 │      └── orders-2026-09-06.csv
 │
 └── rejected/
        └── orders-2026-09-06-errors.csv
```

An event can trigger processing:

```text
S3 Upload
    │
    ▼
Event
    │
    ▼
Queue / Kafka
    │
    ▼
Celery Worker
    │
    ▼
CSV Processing
```

This architecture decouples file arrival from processing.

---

## CSV vs JSON vs Parquet

| Characteristic | CSV | JSON | Parquet |
|---|---|---|---|
| Human-readable | Excellent | Excellent | No |
| Schema | Weak | Moderate | Strong |
| Nested data | Poor | Excellent | Good |
| Type preservation | Poor | Moderate | Strong |
| Streaming rows | Excellent | Possible | Supported by tooling |
| Compression | External | External | Excellent |
| Analytics | Basic | Moderate | Excellent |
| Spreadsheet compatibility | Excellent | Moderate | Poor |
| Cross-language support | Excellent | Excellent | Excellent |

CSV is excellent for simple tabular interchange but is not necessarily the best format for large analytical workloads.

---

## Performance Considerations

CSV parsing has unavoidable costs because:

- every field starts as text
- delimiters must be parsed
- quoting must be interpreted
- values may require type conversion

For high-volume workloads, consider:

- streaming
- batch processing
- parallel file-level processing
- efficient database bulk loading
- columnar formats
- compression
- avoiding unnecessary conversions

Do not assume Python-level micro-optimizations will matter more than database or storage throughput.

---

## Parallel Processing

CSV files can sometimes be processed in parallel, but naïvely splitting a CSV file by byte offsets is unsafe because quoted fields may contain newlines.

For example:

```csv
id,description
1,"line one
line two"
```

A byte-level split can occur in the middle of a logical record.

Safer approaches include:

- splitting by known record boundaries
- using a format-aware parallel parser
- processing multiple independent files
- converting to a partitioned format such as Parquet

File-level parallelism is often simpler and safer than arbitrary byte-level partitioning.

---

## Memory and Backpressure

For pipelines such as:

```text
S3 → Worker → PostgreSQL
```

the producer may read data faster than the database can consume it.

Without bounded buffering:

```text
Fast producer
     │
     ▼
Growing queue
     │
     ▼
Memory exhaustion
```

Use bounded batches and controlled concurrency.

The system should apply backpressure rather than continuously accumulating rows in memory.

---

## Reliability

A production CSV pipeline should be able to answer:

- Which file was processed?
- When was it processed?
- How many rows succeeded?
- How many failed?
- Which rows failed?
- Was the file processed before?
- What checksum identifies the file?
- Can the job be safely retried?

This turns file processing from an ad hoc script into an observable data-ingestion workflow.

---

## Disaster Recovery

For important CSV imports and exports, consider:

- durable object storage
- versioning
- lifecycle policies
- retention periods
- checksums
- import manifests
- metadata backups

Do not rely on a worker's local filesystem as the authoritative copy of a production dataset.

---

## Testing

Test CSV behavior using realistic cases.

```python
import csv
from io import StringIO


def test_csv_with_quoted_comma():
    content = (
        "id,name\n"
        '1,"Smith, John"\n'
    )

    reader = csv.DictReader(
        StringIO(content)
    )

    row = next(reader)

    assert row["name"] == "Smith, John"
```

Test cases should include:

- quoted commas
- quoted quotes
- embedded newlines
- empty fields
- missing fields
- extra fields
- Unicode
- BOM
- malformed CSV
- large files
- duplicate records
- invalid types
- invalid domain values

---

## Round-Trip Testing

For generated CSV:

```text
Python records
      │
      ▼
CSV writer
      │
      ▼
CSV parser
      │
      ▼
Equivalent records
```

Round-trip tests verify that quoting, delimiters, newlines, and data conversion behave as expected.

Do not test only the happy path with simple ASCII strings.

---

## Common Mistakes and Pitfalls

### Using `split(",")`

This fails on quoted fields and embedded commas.

Use `csv.reader` or `csv.DictReader`.

### Forgetting `newline=""`

This can produce newline-handling problems, particularly when writing CSV.

### Assuming Every Field Is a Number

Identifiers, ZIP codes, account numbers, and phone numbers can contain leading zeros.

### Using `float` for Money

Use `Decimal` where decimal-exact monetary semantics are required.

### Assuming CSV Has a Schema

CSV provides limited structural information. Application-level validation is still required.

### Trusting Headers

External files can contain missing, duplicate, renamed, or unexpected columns.

Validate them.

### Loading the Entire File

Large CSV files should normally be streamed.

### Committing Every Row

Per-row transactions can be extremely slow.

Use appropriate batch boundaries.

### Retrying Without Idempotency

A failed import can create duplicates when retried.

Use import identities and database constraints.

### Splitting Large CSVs by Arbitrary Byte Offsets

Quoted newlines can make byte boundaries invalid record boundaries.

### Trusting MIME Type or Extension

A file named `.csv` may not contain valid CSV data.

Validate content.

### Ignoring CSV Injection

Spreadsheet applications may interpret formulas embedded in fields.

Sanitize exports where required.

### Treating Invalid Rows and Invalid Files the Same

A malformed file structure may require complete rejection, while individual bad records may be safely quarantined.

Define the policy explicitly.

---

## Interview Traps

### Why is `split(",")` not a CSV parser?

Because CSV supports quoting, escaped quotes, embedded commas, and embedded newlines.

### Does `csv.reader` convert values to integers or floats?

No. CSV values are normally returned as strings. Type conversion is application responsibility.

### Why use `newline=""`?

It allows the CSV module to manage newline handling without interference from text I/O newline translation.

### Why can CSV be memory-efficient?

The standard reader can iterate through rows incrementally instead of loading the entire file.

### Does streaming guarantee low memory?

Not if the application accumulates rows, batches without limits, or encounters extremely large individual records.

### Why should IDs often remain strings?

Because identifiers may contain leading zeros or exceed numeric precision requirements and are not quantities mathematically.

### Why can arbitrary byte splitting break CSV parallelism?

A quoted field can contain a newline, so physical byte boundaries do not necessarily correspond to logical record boundaries.

### Why is CSV weakly typed?

The format primarily represents textual fields and separators; application-level type semantics are not strongly encoded.

---

## Production Checklist

Before deploying CSV ingestion or export, verify:

- The Python `csv` module is used instead of manual delimiter splitting.
- Files are opened with `newline=""`.
- The expected encoding is explicitly defined.
- Headers are validated.
- Required and unexpected columns are handled intentionally.
- CSV dialect and delimiter assumptions are explicit.
- Structural validation is separated from type and domain validation.
- Monetary values use appropriate decimal semantics.
- Identifiers are not unnecessarily converted to numeric types.
- Missing-value semantics are explicitly defined.
- Large files are streamed.
- Large exports use streaming responses or equivalent bounded-memory mechanisms.
- Batch sizes are bounded.
- Database writes use appropriate bulk or batch operations.
- Transaction boundaries are deliberate.
- Imports are idempotent and safe to retry.
- File checksums or import identities are tracked when needed.
- Invalid rows have an explicit quarantine or rejection policy.
- Invalid files have an explicit failure policy.
- User-controlled CSV exports are protected against spreadsheet formula injection where relevant.
- Uploaded CSV content is validated rather than trusting filename or MIME type.
- S3 or equivalent object storage is used for durable large files where appropriate.
- Celery or another background-processing mechanism is used for long-running imports when appropriate.
- Kafka or queues carry references to large files rather than unnecessarily embedding complete CSV payloads.
- Observability captures file counts, row counts, rejection rates, throughput, and processing duration.
- Sensitive CSV contents are not unnecessarily logged.
- Tests cover quoting, embedded newlines, Unicode, malformed input, large files, and type-validation failures.
- Retention, backup, and disaster-recovery requirements are defined for important imports and exports.

## Key Takeaways

- CSV is a text-based interchange format, not a strongly typed data model; use Python's `csv` module and perform explicit structural, type, and domain validation.
- Never parse real CSV with `split(",")`; quoting, embedded commas, escaped quotes, and embedded newlines make CSV parsing more complex than delimiter splitting.
- Stream large CSV files and use bounded batches for downstream processing to control memory usage and provide backpressure.
- Production imports should be idempotent, observable, and recoverable, with explicit policies for malformed files, invalid rows, retries, transactions, and duplicate detection.
- Treat CSV as an external data boundary with security concerns such as path validation, untrusted content, encoding issues, and spreadsheet formula injection.