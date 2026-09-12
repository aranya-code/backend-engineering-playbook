# Reading and Writing Data

## Overview

The **Reading and Writing Data** section covers how Pandas interfaces with external data sources and produces serialized datasets for downstream systems.

A production Pandas workflow rarely begins with an already-clean DataFrame. Data typically crosses multiple boundaries:

```text
External Source
      ↓
Reading / Ingestion
      ↓
Parsing
      ↓
Dtype Control
      ↓
Normalization
      ↓
DataFrame
      ↓
Transformation
      ↓
Writing / Serialization
      ↓
Storage / Database / API / File
```

This section focuses on the engineering practices required to make those boundaries reliable, explicit, and predictable.

The topics progress from common file formats to the lower-level controls that determine how data is interpreted:

```text
CSV / JSON / Excel / Parquet / SQL / HTML / Text
                         ↓
                  Read Functions
                         ↓
                  Write Functions
                         ↓
                   Dtype Control
                         ↓
             Parsing and Converters
                         ↓
                  Chunked Reading
                         ↓
                    Compression
                         ↓
                     Encoding
```

The goal is not simply to know which Pandas function reads or writes a particular format. The goal is to understand **how external representations become typed Pandas data and how Pandas data is safely published back to external systems**.

---

## Navigation

| # | File | Description |
|---|---|---|
| 01 | [01- CSV](./01-%20CSV.md) | Reading and writing CSV files with dtype control |
| 02 | [02- JSON](./02-%20JSON.md) | Reading and writing JSON data at service and API boundaries |
| 03 | [03- Excel](./03-%20Excel.md) | Reading and writing Excel workbooks in business workflows |
| 04 | [04- Parquet](./04-%20Parquet.md) | Typed columnar format suited to analytical storage |
| 05 | [05- SQL](./05-%20SQL.md) | Integrating Pandas with relational databases |
| 06 | [06- HTML](./06-%20HTML.md) | HTML tabular information when no structured source is available |
| 07 | [07- Text Files](./07-%20Text%20Files.md) | Delimited and fixed-width text files in legacy workflows |
| 08 | [08- Read Functions](./08-%20Read%20Functions.md) | Pandas read_*() APIs for external data sources |
| 09 | [09- Write Functions](./09-%20Write%20Functions.md) | Pandas to_*() APIs for publishing internal data |
| 10 | [10- Dtype Control](./10-%20Dtype%20Control.md) | Explicit dtype choices for important columns |
| 11 | [11- Parsing And Converters](./11-%20Parsing%20And%20Converters.md) | Parser configuration for deterministic local parsing |
| 12 | [12- Chunked Reading](./12-%20Chunked%20Reading.md) | Bounded chunk processing for large files |
| 13 | [13- Compression](./13-%20Compression.md) | Reducing serialized storage and transfer size |
| 14 | [14- Encoding](./14-%20Encoding.md) | Text encoding and UTF-8 handling |




## Reading vs Writing

Pandas provides two complementary families of I/O operations.

### Reading

Reading converts external data into Pandas structures:

```text
CSV
JSON
Excel
Parquet
SQL
HTML
Text
 ↓
Pandas
 ↓
DataFrame / Series
```

Typical APIs include:

```python
pd.read_csv()
pd.read_json()
pd.read_excel()
pd.read_parquet()
pd.read_sql()
pd.read_html()
```

### Writing

Writing converts Pandas structures into external representations:

```text
DataFrame / Series
       ↓
Serialization
       ↓
CSV / JSON / Excel / Parquet / SQL / Text
```

Typical APIs include:

```python
DataFrame.to_csv()
DataFrame.to_json()
DataFrame.to_excel()
DataFrame.to_parquet()
DataFrame.to_sql()
```

Reading and writing are related, but they are not necessarily perfect inverses.

For example:

```text
DataFrame
   ↓
CSV
   ↓
DataFrame
```

may lose information about:

* Original dtypes
* Index semantics
* Timezone information
* Missing-value representation
* Categorical metadata
* Exact numeric representation

Therefore, serialization should be treated as a **data contract**, not merely a file-format operation.

---

## External Data Boundaries

A useful production mental model is:

```text
                 External Boundary
                        │
        ┌───────────────┼────────────────┐
        ↓               ↓                ↓
      Files          Databases         Services
        │               │                │
        ↓               ↓                ↓
     Parsing         Querying          Parsing
        │               │                │
        └───────────────┼────────────────┘
                        ↓
                 Typed DataFrame
                        │
                        ↓
                  Transformation
                        │
                        ↓
                 Validation
                        │
                        ↓
                 Serialization
                        │
        ┌───────────────┼────────────────┐
        ↓               ↓                ↓
      Files          Databases         Services
```

The I/O layer therefore establishes an important boundary between:

```text
Uncontrolled external representation
```

and:

```text
Controlled internal representation
```

---

## File Formats

Different formats provide different guarantees and trade-offs.

| Format  | Typical role                   | Key characteristic              |
| ------- | ------------------------------ | ------------------------------- |
| CSV     | Interchange and simple exports | Human-readable, weakly typed    |
| JSON    | APIs and service boundaries    | Nested and semi-structured      |
| Excel   | Business workflows             | Spreadsheet-oriented            |
| Parquet | Analytical storage             | Typed columnar format           |
| SQL     | Relational systems             | Database-backed structured data |
| HTML    | Web tables and legacy sources  | Presentation-oriented           |
| Text    | Legacy and specialized systems | Flexible but often weakly typed |

Format selection should consider:

```text
Schema requirements
Data volume
Read/write performance
Interoperability
Compression
Type preservation
Query requirements
Human accessibility
Operational environment
```

There is no universally best format.

---

## Schema and Dtype Control

External data frequently contains ambiguous representations.

For example:

```text
customer_id = "000123"
quantity    = "10"
active      = "Y"
created_at  = "2026-09-10 12:30:00"
```

A production DataFrame may require:

```text
customer_id → string
quantity    → nullable integer
active      → boolean
created_at  → timezone-aware datetime
```

This means ingestion should establish the intended schema deliberately.

A useful principle is:

```text
Source Representation
        ↓
Interpretation
        ↓
Target Schema
```

rather than:

```text
Source Representation
        ↓
Whatever Pandas infers
```

Explicit dtype control is particularly important for:

* Identifiers
* Nullable integers
* Boolean fields
* Dates and timestamps
* Monetary values
* Categorical columns
* High-cardinality text
* Columns used in joins

---

## Parsing and Conversion

Parsing determines how raw external values should be interpreted.

For example:

```text
"1,250.50"
       ↓
numeric value

"2026/09/10"
       ↓
datetime

"Y"
       ↓
boolean

"000123"
       ↓
string identifier
```

A robust ingestion pipeline separates:

```text
Parsing
   ↓
Normalization
   ↓
Conversion
   ↓
Validation
```

Successful parsing does not necessarily mean that the resulting value is valid business data.

---

## Large Dataset Processing

Reading an entire dataset into memory is not always appropriate.

For large files, chunked processing allows the pipeline to operate on bounded batches:

```text
Large Dataset
     ↓
┌─────────────┐
│   Chunk 1   │ → process → persist
├─────────────┤
│   Chunk 2   │ → process → persist
├─────────────┤
│   Chunk 3   │ → process → persist
└─────────────┘
```

The objective is to control:

```text
Peak memory
Processing batch size
Failure scope
Output buffering
Operational stability
```

Chunking is particularly useful for ETL jobs and large CSV/text inputs.

---

## Compression

Compression affects the serialized representation rather than the logical DataFrame.

The fundamental trade-off is:

```text
More compression
       ↓
Smaller files
       ↓
Less storage / network I/O
       ↓
Potentially more CPU
```

Compression therefore needs to be evaluated as part of the complete pipeline:

```text
Serialization
      ↓
Compression
      ↓
Storage / Network
      ↓
Decompression
      ↓
Parsing
```

The best compression choice depends on the workload, storage system, CPU capacity, and interoperability requirements.

---

## Encoding

Text-based formats introduce another important boundary:

```text
Bytes
  ↓
Decoding
  ↓
Text
  ↓
Pandas
```

UTF-8 is generally the preferred encoding for modern systems, but production pipelines must respect the actual encoding contract of the source or destination.

Incorrect encoding can cause:

```text
UnicodeDecodeError
Corrupted characters
Incorrect identifiers
Broken joins
Invalid reports
Data-quality failures
```

Encoding should therefore be treated as part of the ingestion contract.

---

## Production I/O Principles

A reliable Pandas I/O layer should make important assumptions explicit.

### Prefer explicit schemas

```python
pd.read_csv(
    "orders.csv",
    dtype={
        "order_id": "string",
        "customer_id": "string",
        "quantity": "Int64",
    },
)
```

### Avoid uncontrolled inference for critical fields

Especially for:

```text
Identifiers
Dates
Booleans
Financial values
Join keys
```

### Validate after ingestion

```text
Read
 ↓
Parse
 ↓
Normalize
 ↓
Convert
 ↓
Validate
 ↓
Process
```

### Treat serialization as a contract

Define:

```text
Format
Schema
Encoding
Compression
Null representation
Column ordering
Partitioning
Destination
```

rather than treating file output as an incidental operation.

### Consider operational constraints

Production I/O should account for:

```text
Memory
CPU
Disk
Network
File size
Failure recovery
Idempotency
Data quality
Schema evolution
```

---

## Key Takeaways

* Pandas I/O establishes the boundary between external data and internal DataFrame representations.
* CSV, JSON, Excel, Parquet, SQL, HTML, and text files have different strengths and limitations.
* Reading data is not simply file loading; it is the beginning of schema establishment and data interpretation.
* Writing data is not simply exporting a DataFrame; it defines how internal data is serialized for another system.
* Explicit dtype control prevents many subtle ingestion and downstream processing errors.
* Parsing, conversion, normalization, and validation should be treated as separate concerns.
* Chunked reading provides bounded-memory processing for large inputs.
* Compression trades CPU for reduced storage and network I/O.
* Encoding defines how external text bytes become usable characters.
* Production I/O should make schema, encoding, compression, and other external contracts explicit.
* Reliable data pipelines treat I/O as an engineering boundary rather than a collection of convenience functions.
