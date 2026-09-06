# README

## Overview

The `05- Files and Serialization` section covers how Python applications work with filesystem resources and transform data between in-memory objects and persistent or transport-oriented representations.

File and serialization handling appears throughout backend systems:

```text
HTTP / API
    │
    ▼
Python Objects
    │
    ├── JSON
    ├── YAML
    ├── CSV
    ├── Binary
    └── Database / Object Storage
          │
          ▼
      Files / S3 / Streams
```

The section progresses from basic file I/O to production concerns such as:

- safe path handling
- text and binary data
- structured formats
- serialization boundaries
- validation
- large-file streaming
- memory efficiency
- security
- atomic writes
- cloud object storage
- API integration
- data pipelines

The goal is not merely to learn how to open a file. It is to understand how file and serialization decisions affect **correctness, performance, memory usage, security, reliability, and scalability**.

---

## Section Structure

```text
05- Files and Serialization
│
├── File Handling
│     │
│     ├── Pathlib
│     ├── Text Files
│     └── Binary Files
│
├── Structured Data
│     │
│     ├── CSV
│     ├── JSON
│     └── YAML
│
├── Serialization
│     │
│     ├── Pickle
│     ├── Serialization
│     └── Deserialization and Validation
│
└── Large Data
      │
      └── Streaming Large Files
```

| File | Focus |
|---|---|
| `01- File Handling.md` | Opening, reading, writing, appending, closing, buffering, encodings, and safe file operations |
| `02- Pathlib.md` | Object-oriented filesystem paths, path composition, inspection, and cross-platform handling |
| `03- Text Files.md` | Text encoding, decoding, newline behavior, line-oriented processing, and text I/O |
| `04- Binary Files.md` | Bytes, binary streams, buffering, binary formats, and non-text data |
| `05- CSV.md` | CSV parsing and writing, dialects, quoting, streaming, and data pipelines |
| `06- JSON.md` | JSON encoding/decoding, Python mappings, API payloads, and JSON limitations |
| `07- YAML.md` | YAML parsing, configuration files, safety considerations, and structured configuration |
| `08- Pickle.md` | Python-specific serialization, compatibility, security risks, and appropriate use cases |
| `09- Serialization.md` | Serialization concepts, formats, contracts, compatibility, and system boundaries |
| `10- Deserialization and Validation.md` | Safely converting external data into validated application objects |
| `11- Streaming Large Files.md` | Iterative processing, bounded memory usage, chunking, backpressure, and large-file workflows |

---

## Core Mental Model

File handling and serialization involve multiple transformations:

```text
External Representation
        │
        ▼
Bytes
        │
        ├── decode ──► Text
        │
        ▼
Structured Format
        │
        ├── parse ──► Python Objects
        │
        ▼
Validation
        │
        ▼
Application / Domain Model
```

The reverse operation is serialization:

```text
Application Object
        │
        ▼
Serialization
        │
        ▼
JSON / CSV / YAML / Binary
        │
        ▼
Bytes / Text
        │
        ▼
File / HTTP / Object Storage / Queue
```

Keeping these boundaries explicit makes systems easier to reason about.

---

## File Handling Fundamentals

Python provides built-in file I/O through `open()`.

A typical production-oriented pattern is:

```python
from pathlib import Path

path = Path("data/orders.json")

with path.open("r", encoding="utf-8") as file:
    content = file.read()
```

The context manager ensures that the file is closed even when an exception occurs.

The lifecycle is:

```text
open
  │
  ▼
read / write
  │
  ▼
flush / close
```

Prefer context managers rather than manually managing file descriptors.

---

## Why File Resources Require Care

An open file consumes an operating-system resource.

A process has limits on:

- file descriptors
- memory
- filesystem connections
- concurrent handles

For long-running backend processes, leaked file handles can eventually prevent new files or sockets from being opened.

Use:

```python
with open(...):
    ...
```

or another context-managed abstraction.

---

## File Modes

Common modes include:

| Mode | Purpose |
|---|---|
| `r` | Read text |
| `w` | Write text, replacing existing content |
| `a` | Append text |
| `x` | Create new file, fail if it exists |
| `rb` | Read binary |
| `wb` | Write binary |
| `ab` | Append binary |
| `r+` | Read/write existing file |

Be particularly careful with:

```python
open(path, "w")
```

because it truncates an existing file.

For important data, atomic replacement is often safer than directly overwriting the target.

---

## `pathlib`

`pathlib.Path` should generally be preferred over manually concatenating filesystem paths.

```python
from pathlib import Path

base_dir = Path("/var/app/data")
file_path = base_dir / "orders" / "2026" / "orders.json"
```

This provides:

- platform-aware path operations
- path inspection
- directory creation
- file existence checks
- globbing
- convenient file operations

Avoid:

```python
path = "/var/app/data/" + filename
```

Use:

```python
path = Path("/var/app/data") / filename
```

---

## Text and Encoding

Text files contain encoded bytes.

```text
Bytes
  │
  ▼
UTF-8 decoding
  │
  ▼
Python str
```

When reading external files, specifying the encoding explicitly is generally safer:

```python
with path.open("r", encoding="utf-8") as file:
    text = file.read()
```

Encoding mistakes can produce:

- `UnicodeDecodeError`
- corrupted text
- inconsistent behavior across environments

Production systems should not depend on the host operating system's default encoding when the file format has a known encoding.

---

## Binary Data

Binary files should be handled as `bytes`.

```python
with path.open("rb") as file:
    data = file.read()
```

Common binary data includes:

- images
- PDFs
- compressed files
- archives
- cryptographic material
- protocol payloads

Do not decode arbitrary binary data as UTF-8.

---

## Buffered I/O

Python file objects typically use buffering.

For large sequential operations, buffering reduces the number of operating-system calls.

However, reading an entire large file into memory can still be problematic:

```python
data = file.read()
```

For large files, prefer iteration or chunked reads.

```python
with path.open("rb") as file:
    while chunk := file.read(1024 * 1024):
        process(chunk)
```

This keeps memory bounded.

---

## Streaming

Large-file processing should generally avoid:

```python
content = file.read()
```

when the file may be gigabytes in size.

Prefer:

```python
with path.open("r", encoding="utf-8") as file:
    for line in file:
        process(line)
```

or chunked binary processing.

Conceptually:

```text
Large File
    │
    ▼
Chunk
    │
    ▼
Process
    │
    ▼
Discard
    │
    ▼
Next Chunk
```

Memory usage remains approximately bounded by the chunk size and processing state.

---

## CSV

CSV is common in:

- data exports
- ETL pipelines
- batch jobs
- reporting systems
- data imports

Python provides the `csv` module.

```python
import csv
from pathlib import Path

path = Path("orders.csv")

with path.open("r", encoding="utf-8", newline="") as file:
    reader = csv.DictReader(file)

    for row in reader:
        process_order(row)
```

Using `DictReader` provides named columns rather than positional indexing.

---

## CSV Production Considerations

CSV is deceptively complex.

Consider:

- delimiters
- quoting
- embedded commas
- embedded newlines
- headers
- encoding
- missing values
- inconsistent columns
- newline handling

Do not implement CSV parsing with:

```python
line.split(",")
```

because quoted fields can contain commas.

Use the standard library's CSV parser or a specialized data-processing library when appropriate.

---

## JSON

JSON is widely used for:

- REST APIs
- configuration
- event payloads
- object storage
- service-to-service communication

Python provides the `json` module.

```python
import json

payload = {
    "order_id": 123,
    "status": "created",
}

encoded = json.dumps(payload)
decoded = json.loads(encoded)
```

JSON naturally maps to common Python types:

| JSON | Python |
|---|---|
| object | `dict` |
| array | `list` |
| string | `str` |
| number | `int` / `float` |
| boolean | `bool` |
| null | `None` |

---

## JSON Limitations

JSON does not natively represent all Python objects.

For example:

```python
from datetime import datetime

payload = {
    "created_at": datetime.now(),
}
```

cannot be serialized by the default JSON encoder.

A serialization boundary must define how such values are represented, commonly as:

```text
ISO 8601 string
```

or another explicit wire format.

Do not rely on arbitrary object stringification as a data contract.

---

## YAML

YAML is frequently used for:

- application configuration
- deployment configuration
- CI/CD configuration
- human-maintained structured data

YAML is expressive but should be handled carefully.

A critical security rule is:

> Never deserialize untrusted YAML using unsafe object-construction mechanisms.

For configuration files, use a safe loader and validate the resulting structure before using it.

---

## Pickle

Python's `pickle` module serializes Python objects into a Python-specific binary representation.

```python
import pickle

with open("model.pkl", "wb") as file:
    pickle.dump(data, file)
```

However:

> **Never unpickle untrusted data.**

Unpickling can execute arbitrary code because the format supports object reconstruction with executable behavior.

Pickle is therefore appropriate only for trusted Python-controlled environments where its compatibility and security characteristics are understood.

It is generally inappropriate as an external API format.

---

## Serialization

Serialization converts an in-memory representation into a transferable or persistent representation.

```text
Python Object
      │
      ▼
Serialization
      │
      ▼
JSON / CSV / YAML / Binary
      │
      ▼
File / Network / Queue / Storage
```

Deserialization reverses the process:

```text
External Data
      │
      ▼
Parse
      │
      ▼
Python Representation
      │
      ▼
Validation
      │
      ▼
Application Model
```

Serialization format selection should be driven by system requirements rather than convenience alone.

---

## Format Comparison

| Format | Strengths | Limitations | Typical use |
|---|---|---|---|
| JSON | Portable, API-friendly, human-readable | Verbose, limited type system | REST APIs, events |
| CSV | Simple, widely supported | Weak schema, ambiguous types | Data exchange |
| YAML | Human-friendly configuration | Complex semantics, security concerns | Config |
| Pickle | Preserves Python objects | Python-specific, unsafe for untrusted data | Trusted internal workflows |
| Binary formats | Compact, efficient, typed | More tooling required | High-volume systems |

For large data pipelines, additional formats such as Parquet may be appropriate.

---

## Deserialization and Validation

Parsing data does not mean the data is trustworthy.

These are separate stages:

```text
Raw Input
   │
   ▼
Parse
   │
   ▼
Structural Validation
   │
   ▼
Semantic Validation
   │
   ▼
Domain Model
```

For example:

```python
payload = json.loads(raw_body)

if not isinstance(payload, dict):
    raise ValueError("expected JSON object")

if not isinstance(payload.get("quantity"), int):
    raise ValueError("quantity must be an integer")
```

Production systems should generally use structured validation libraries or domain validation rather than scattering ad hoc checks throughout business logic.

---

## Serialization Boundaries

Serialization is a system boundary.

Examples:

```text
HTTP JSON
    ↔
API DTO
    ↔
Domain Model
```

or:

```text
Database Row
    ↔
Repository Model
    ↔
Domain Object
```

or:

```text
Kafka Event
    ↔
Event Schema
    ↔
Consumer Model
```

Do not assume an external representation should be identical to an internal domain model.

---

## Files and Backend APIs

A common backend flow is:

```text
HTTP Upload
    │
    ▼
Request Validation
    │
    ▼
Temporary Storage
    │
    ▼
Streaming Processing
    │
    ▼
Object Storage
    │
    ▼
Database Metadata
```

For large uploads, streaming avoids loading the entire file into Python memory.

This is important for FastAPI, Django, Nginx, Kubernetes workloads, and containerized services where memory is limited.

---

## Files and Object Storage

Production systems often store large files in object storage such as Amazon S3 rather than local application disks.

A common architecture is:

```text
Client
  │
  ▼
API
  │
  ├── metadata → PostgreSQL
  │
  └── file → S3
```

The database stores metadata:

```text
file_id
object_key
content_type
size
checksum
created_at
```

while the object store holds the actual file.

This separates application state from large binary payloads.

---

## Local Files vs Object Storage

| Concern | Local filesystem | Object storage |
|---|---|---|
| Persistence | Host-dependent | Durable |
| Horizontal scaling | Difficult | Natural |
| Pod restart | Data may disappear | Data persists |
| Large objects | Possible | Well suited |
| Access control | OS permissions | IAM / bucket policies |
| Replication | Application responsibility | Service-managed |
| Backend deployment | More operational complexity | Usually simpler |

Containers should generally not be treated as permanent storage.

---

## Temporary Files

Temporary files are useful for intermediate processing.

Python provides `tempfile`:

```python
from tempfile import NamedTemporaryFile

with NamedTemporaryFile() as file:
    file.write(b"temporary data")
    file.flush()
    process(file.name)
```

Temporary storage should be:

- bounded
- cleaned up
- isolated
- protected from unauthorized access

Do not assume `/tmp` has unlimited capacity.

---

## Atomic File Writes

Directly overwriting an important file can leave partially written content if the process crashes.

A safer approach is:

```text
Write temporary file
       │
       ▼
Flush / close
       │
       ▼
Atomic rename
       │
       ▼
Target file
```

Conceptually:

```python
from pathlib import Path
import os
import tempfile


def atomic_write(path: Path, content: bytes) -> None:
    with tempfile.NamedTemporaryFile(
        dir=path.parent,
        delete=False,
    ) as temp:
        temp.write(content)
        temp.flush()
        os.fsync(temp.fileno())
        temp_path = Path(temp.name)

    os.replace(temp_path, path)
```

The exact durability guarantees depend on the filesystem and deployment environment, but atomic replacement is generally safer than partially updating the target.

---

## File Permissions

Sensitive files require controlled permissions.

Examples include:

- private keys
- credentials
- configuration secrets
- user-uploaded private documents
- generated reports

Do not rely solely on application-level checks.

Use appropriate:

- filesystem permissions
- container user permissions
- IAM policies
- object storage policies
- encryption
- secret management

---

## Path Traversal

Never directly trust user-provided filenames.

Dangerous input:

```text
../../etc/passwd
```

or:

```text
..\..\secrets.txt
```

A secure design should not construct arbitrary filesystem paths from untrusted input.

Prefer generated identifiers:

```text
uploads/
    8f/
      8f7c...bin
```

and keep user-visible filenames as metadata rather than storage paths.

---

## File Type Validation

Do not trust:

```http
Content-Type: image/png
```

alone.

A malicious client can provide an incorrect MIME type or filename.

For sensitive uploads, consider validating:

- file signature / magic bytes
- actual format
- file size
- extension
- MIME type
- content structure

For example:

```text
Extension
   +
Declared MIME type
   +
Content inspection
```

should be evaluated according to the application's risk level.

---

## Resource Exhaustion

Files can be used for denial-of-service attacks.

Examples:

- extremely large uploads
- highly compressed archives
- huge CSV rows
- deeply nested JSON
- oversized multipart requests

Apply limits such as:

```text
Maximum request size
Maximum file size
Maximum decompressed size
Maximum processing time
Maximum memory usage
```

These limits should exist at appropriate layers such as Nginx, API gateway, application, and worker.

---

## Serialization Security

Deserialization is a trust boundary.

Never assume:

```text
parseable = trustworthy
```

An attacker may provide syntactically valid but malicious or pathological data.

Validate:

- type
- structure
- size
- allowed fields
- ranges
- encoding
- business constraints

Use allowlists rather than accepting arbitrary object construction.

---

## Large JSON

A large JSON document can consume substantial memory:

```python
data = json.load(file)
```

This constructs the entire structure in memory.

For very large datasets, consider:

- newline-delimited JSON
- streaming parsers
- chunked processing
- pagination
- object storage + batch processing

The right format can matter more than micro-optimizing Python code.

---

## JSON Lines

JSON Lines represents one JSON object per line:

```text
{"id": 1, "status": "created"}
{"id": 2, "status": "paid"}
{"id": 3, "status": "shipped"}
```

This works well for:

- logs
- event exports
- ETL
- batch processing
- streaming pipelines

Processing can remain incremental:

```python
import json

with open("events.jsonl", encoding="utf-8") as file:
    for line in file:
        event = json.loads(line)
        process(event)
```

---

## File Handling and Concurrency

Multiple workers may access the same file concurrently.

Potential problems include:

- lost updates
- partial reads
- race conditions
- inconsistent state
- file locking issues

For shared application state, a database or object store is often more appropriate than a local file.

If files must be shared between Kubernetes pods, local pod storage is usually insufficient.

---

## File Locks

File locks can coordinate access on a single host, but they introduce complexity.

They may not provide the desired semantics across:

- multiple containers
- network filesystems
- multiple hosts
- autoscaled workloads

For distributed coordination, use a system designed for it, such as PostgreSQL or Redis, rather than assuming filesystem locks provide cluster-wide synchronization.

---

## Performance Considerations

File operations are often I/O-bound.

Important variables include:

- file size
- access pattern
- buffering
- storage latency
- serialization cost
- compression
- network throughput
- number of concurrent workers

For large files:

```text
Memory usage
≈
chunk size
+
processing state
```

rather than:

```text
Memory usage
≈
entire file size
```

when streaming is implemented correctly.

---

## Compression

Compression can reduce storage and network costs.

Trade-offs include:

```text
Compression
   ├── lower storage
   ├── lower bandwidth
   └── higher CPU
```

For large backend pipelines, evaluate:

- CPU availability
- network bandwidth
- storage cost
- latency requirements
- compression ratio

Do not compress data merely because it is smaller; measure the actual workload.

---

## Checksums and Integrity

For important file transfers, checksums can detect corruption.

Metadata may include:

```text
file_id
size
sha256
content_type
storage_key
```

A checksum can support:

- integrity verification
- deduplication
- upload validation
- cache validation
- corruption detection

Do not use weak hashes as security mechanisms where collision resistance matters.

---

## Reliability and Recovery

File workflows should account for partial failures.

Example:

```text
Upload
  │
  ▼
Temporary file
  │
  ▼
Validation
  │
  ▼
Object storage
  │
  ▼
Database metadata
```

If object storage succeeds but the database update fails, the system may contain an orphaned object.

Production designs may require:

- transactional metadata
- idempotent uploads
- cleanup jobs
- reconciliation
- object lifecycle policies

Distributed storage operations rarely provide a single atomic transaction across all systems.

---

## Disaster Recovery

Important file data should not rely on one local filesystem.

For durable data:

```text
Application
    │
    ▼
Object Storage
    │
    ├── versioning
    ├── replication
    ├── lifecycle policies
    └── backup strategy
```

The exact strategy depends on recovery objectives:

- RPO
- RTO
- retention
- compliance
- cost

The application should know which files are authoritative and which are merely temporary artifacts.

---

## Testing

File-related code should be tested without depending unnecessarily on developer machines.

Use temporary directories:

```python
from pathlib import Path


def write_report(path: Path) -> None:
    path.write_text(
        "report",
        encoding="utf-8",
    )
```

Tests can provide temporary paths through pytest fixtures.

Test:

- missing files
- permissions
- invalid encodings
- malformed data
- empty files
- large files
- duplicate files
- concurrent access where relevant
- cleanup behavior
- serialization compatibility

---

## Testing Serialization

Serialization tests should verify round-trip behavior:

```text
Python object
     │
     ▼
serialize
     │
     ▼
deserialize
     │
     ▼
Equivalent validated object
```

For APIs and events, also test schema compatibility rather than only Python object equality.

---

## Common Mistakes

### Reading Entire Large Files

```python
content = file.read()
```

This can exhaust memory.

Use streaming or chunking.

### Manually Building Paths

```python
path = base + "/" + filename
```

Use `pathlib`.

### Forgetting Encoding

Relying on environment defaults creates portability problems.

### Splitting CSV With `str.split`

CSV quoting makes this incorrect for real-world files.

### Unpickling Untrusted Data

This can result in arbitrary code execution.

### Trusting User Filenames

This creates path traversal and collision risks.

### Treating Local Disk as Durable Storage

Containers and autoscaled instances are not reliable permanent storage.

### Returning Raw Serialized Objects

Internal Python object representations should not automatically become external API contracts.

### Loading Huge JSON Documents

Entire-document parsing can create large memory spikes.

### Ignoring Partial Failure

Object storage and database updates can succeed or fail independently.

---

## Production Checklist

Before shipping file or serialization code, verify:

- Files are opened with context managers.
- Text encodings are explicit where appropriate.
- Binary data is handled as `bytes`.
- `pathlib` is used for filesystem paths.
- User-controlled paths cannot escape intended directories.
- File sizes and processing limits are enforced.
- Large files are streamed or chunked.
- Temporary files are cleaned up.
- Important writes use safe atomic-update patterns where appropriate.
- Sensitive files have appropriate permissions.
- Upload content is validated rather than trusting filenames or MIME types.
- Untrusted data is never deserialized using unsafe object-construction mechanisms.
- JSON, CSV, YAML, and other formats have explicit schemas or validation rules where required.
- Pickle is restricted to trusted environments.
- Serialization formats are treated as compatibility contracts.
- API and event payloads are not coupled directly to internal domain objects.
- Object storage is preferred over local disk for durable large-file storage where appropriate.
- File metadata and file contents have clearly defined consistency semantics.
- Checksums are used where integrity verification is required.
- Retry and recovery behavior is idempotent where applicable.
- Large-file processing has bounded memory usage.
- Observability captures processing failures and throughput.
- Tests cover malformed, missing, oversized, and boundary-case files.
- Disaster recovery and retention requirements are defined for important data.

## Key Takeaways

- File handling is a resource-management problem as much as an I/O problem; use context managers, explicit encodings, `pathlib`, bounded reads, and safe cleanup.
- Serialization is a system boundary: parsing external data is not validation, and internal Python models should not automatically become external data contracts.
- Large files should be streamed or processed in chunks to keep memory usage bounded and prevent a single request or worker from exhausting application resources.
- Treat file uploads, deserialization, paths, and temporary storage as security boundaries with strict size, type, path, permission, and trust controls.
- Production systems should distinguish temporary local files from durable object storage and design explicitly for atomicity, idempotency, integrity, recovery, observability, and disaster recovery.