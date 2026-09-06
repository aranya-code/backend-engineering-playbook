# 03- Text Files

## Overview

Text files store character data as encoded bytes on disk. Python's text I/O layer handles the conversion between those bytes and Python `str` objects.

The important abstraction is:

```text
Filesystem
    │
    ▼
Bytes
    │
    │ decode
    ▼
Python str
    │
    │ application processing
    ▼
Python str
    │
    │ encode
    ▼
Bytes
    │
    ▼
Filesystem
```

This distinction matters because files do not inherently contain Python strings. They contain bytes, and an encoding determines how those bytes represent characters.

Text-file handling appears throughout backend systems:

- configuration files
- CSV and JSON documents
- application-generated reports
- SQL scripts
- templates
- logs
- ETL input
- data exports
- migration files
- test fixtures

Production-quality text I/O requires explicit decisions about encoding, newline handling, buffering, file size, atomicity, concurrency, permissions, and error recovery.

---

## Text I/O Model

Python separates binary I/O from text I/O.

```text
Binary stream
    │
    ▼
Buffered I/O
    │
    ▼
Text I/O
    │
    ├── encoding
    ├── decoding
    └── newline translation
```

When opening a file in text mode:

```python
from pathlib import Path

path = Path("data/orders.txt")

with path.open("r", encoding="utf-8") as file:
    text = file.read()
```

Python reads bytes from the operating system and decodes them into `str`.

When writing:

```python
with path.open("w", encoding="utf-8") as file:
    file.write("Order created")
```

Python encodes the `str` into bytes before writing them.

---

## Text vs Binary Mode

| Mode | Python data | Typical use |
|---|---|---|
| `r` | `str` | Read text |
| `w` | `str` | Write text |
| `a` | `str` | Append text |
| `x` | `str` | Create new text file |
| `rb` | `bytes` | Read binary data |
| `wb` | `bytes` | Write binary data |
| `ab` | `bytes` | Append binary data |

Text mode is appropriate when the file represents characters according to a known encoding.

Binary mode should be used when the content is inherently bytes, such as:

- images
- PDFs
- compressed data
- encrypted data
- arbitrary protocol payloads

---

## Opening Text Files

The preferred pattern is a context manager:

```python
from pathlib import Path

path = Path("data/orders.txt")

with path.open("r", encoding="utf-8") as file:
    content = file.read()
```

The context manager ensures the file is closed when execution leaves the block, including when an exception occurs.

Avoid:

```python
file = open("data/orders.txt", encoding="utf-8")
content = file.read()
file.close()
```

Manual cleanup is easier to break when exceptions or early returns are introduced.

---

## File Modes

The most important text modes are:

| Mode | Behavior |
|---|---|
| `r` | Read existing file |
| `w` | Create or truncate file |
| `a` | Append to file |
| `x` | Create exclusively; fail if present |
| `r+` | Read and write without truncating |
| `w+` | Read and write while truncating |
| `a+` | Read and append |

Be particularly careful with `w`:

```python
with path.open("w", encoding="utf-8") as file:
    file.write("new content")
```

Opening the file can truncate its existing contents before the write completes.

For important files, atomic replacement is often safer.

---

## Character Encoding

An encoding defines how characters map to bytes.

For example:

```text
Python string
"café"
    │
    ▼
UTF-8 encoding
    │
    ▼
Bytes
```

UTF-8 is the common default for modern interoperable systems.

Use it explicitly when the format requires UTF-8:

```python
with path.open("r", encoding="utf-8") as file:
    content = file.read()
```

This avoids relying on environment-specific defaults.

---

## Why Encoding Matters

The same bytes can be interpreted differently under different encodings.

For example:

```text
Bytes
  │
  ├── UTF-8      → correct text
  │
  └── wrong codec → decoding error / corrupted text
```

A production service can behave differently between:

- Windows
- Linux
- macOS
- local development
- Docker
- CI/CD
- Kubernetes

if it relies on implicit encoding selection.

---

## UTF-8

UTF-8 is a variable-width encoding.

A Unicode character can occupy one or more bytes.

This means:

```python
len("hello")
```

and:

```python
len("你好")
```

count Python characters, not necessarily the number of bytes written to disk.

For byte size:

```python
size = len("你好".encode("utf-8"))
```

This distinction matters for:

- file-size limits
- network payload limits
- storage calculations
- truncation
- database fields
- API request limits

---

## `str` vs `bytes`

Python keeps text and binary data conceptually separate:

```python
text = "hello"
data = b"hello"
```

Their types differ:

```python
type(text)  # str
type(data)  # bytes
```

Convert explicitly:

```python
encoded = text.encode("utf-8")
decoded = encoded.decode("utf-8")
```

Avoid accidental implicit conversions.

A useful rule is:

> Decode bytes at the system boundary and keep text as `str` internally when the application is processing textual data.

---

## Decoding Errors

If bytes cannot be decoded using the selected encoding:

```python
text = data.decode("utf-8")
```

Python can raise:

```text
UnicodeDecodeError
```

Do not blindly replace invalid characters unless data loss is acceptable.

For example:

```python
text = data.decode("utf-8", errors="replace")
```

can hide upstream corruption.

Possible strategies include:

- reject malformed input
- identify the actual encoding
- preserve raw bytes
- replace invalid characters when explicitly acceptable
- quarantine malformed files

The correct strategy depends on the data contract.

---

## Encoding Error Strategies

Python supports several error-handling strategies.

```python
data.decode("utf-8", errors="strict")
data.decode("utf-8", errors="replace")
data.decode("utf-8", errors="ignore")
```

| Strategy | Behavior | Production suitability |
|---|---|---|
| `strict` | Raise on invalid data | Preferred for validated data |
| `replace` | Substitute invalid sequences | Useful when loss is acceptable |
| `ignore` | Discard invalid data | Usually dangerous |

`ignore` can silently destroy information and should rarely be used for business data.

---

## Newline Handling

Text files can use different newline conventions:

| Platform | Common newline |
|---|---|
| Linux/macOS | `\n` |
| Windows | `\r\n` |
| Legacy systems | `\r` |

Python's text layer can translate newlines.

```python
with path.open("r", encoding="utf-8", newline=None) as file:
    ...
```

This is the normal text-mode behavior.

For formats such as CSV, explicit newline handling is important:

```python
with path.open("r", encoding="utf-8", newline="") as file:
    ...
```

This prevents Python's newline translation from interfering with the format's own handling.

---

## Writing Newlines

A portable application can write:

```python
file.write("line 1\n")
file.write("line 2\n")
```

The resulting physical representation depends on text I/O newline configuration.

When generating files consumed by external systems, follow that format's newline requirements rather than assuming the consumer will normalize everything correctly.

---

## Reading Entire Files

For small files:

```python
with path.open("r", encoding="utf-8") as file:
    content = file.read()
```

This is convenient for:

- small configuration files
- templates
- small JSON documents
- test fixtures
- SQL scripts

The entire decoded string is held in memory.

Therefore, it is not appropriate for arbitrarily large files.

---

## Reading Line by Line

For large text files:

```python
with path.open("r", encoding="utf-8") as file:
    for line in file:
        process(line)
```

Python file objects are iterable and yield lines incrementally.

Conceptually:

```text
Large File
   │
   ├── line 1 → process → discard
   ├── line 2 → process → discard
   ├── line 3 → process → discard
   └── ...
```

This keeps memory usage bounded by the active line and application processing state.

---

## `readline()`

For explicit control:

```python
with path.open("r", encoding="utf-8") as file:
    while line := file.readline():
        process(line)
```

Usually, direct iteration is cleaner:

```python
for line in file:
    process(line)
```

Use `readline()` when the control flow genuinely requires explicit reads.

---

## `readlines()`

`readlines()` loads all lines into a list:

```python
lines = file.readlines()
```

This is convenient for small files but can consume significant memory for large files.

Avoid:

```python
lines = file.readlines()

for line in lines:
    process(line)
```

when the file size is unbounded.

Prefer:

```python
for line in file:
    process(line)
```

---

## `read()` With a Size

Text streams can also read a bounded amount:

```python
with path.open("r", encoding="utf-8") as file:
    chunk = file.read(1024 * 1024)
```

This is useful for chunk-oriented processing.

Be aware that text-mode `read(size)` is expressed in characters rather than raw bytes, so byte-level processing should use binary mode.

---

## Writing Text

Use `write()` for a string:

```python
with path.open("w", encoding="utf-8") as file:
    file.write("order_id,status\n")
    file.write("1001,created\n")
```

For multiple strings:

```python
lines = [
    "order_id,status\n",
    "1001,created\n",
    "1002,paid\n",
]

with path.open("w", encoding="utf-8") as file:
    file.writelines(lines)
```

`writelines()` does not automatically add newline characters.

---

## Appending

Append mode writes at the end of the file:

```python
with path.open("a", encoding="utf-8") as file:
    file.write("new record\n")
```

Appending is useful for:

- append-only local logs
- simple exports
- incremental text output

However, a local text file should not automatically be treated as a reliable distributed event log.

For durable multi-worker event processing, use systems designed for that purpose, such as Kafka or a database.

---

## Flush and Close

Python buffers writes.

```python
with path.open("w", encoding="utf-8") as file:
    file.write("data")
```

When the context exits, the file is closed and buffered data is flushed.

Explicit flushing is possible:

```python
file.flush()
```

But `flush()` generally means pushing Python's buffered data to the underlying I/O layer. It does not necessarily mean the data is durably committed to physical storage.

For stronger durability requirements, filesystem-specific synchronization such as `os.fsync()` may be necessary.

---

## Buffering

Python's I/O stack can buffer data:

```text
Application
    │
    ▼
TextIOWrapper
    │
    ▼
Buffered I/O
    │
    ▼
Operating System
    │
    ▼
Storage
```

Buffering reduces the overhead of many small system calls.

For most application code, default buffering is appropriate.

Do not optimize buffering before measuring the actual workload.

---

## Large-File Processing

For large text files, prefer streaming:

```python
from pathlib import Path


def process_log(path: Path) -> int:
    count = 0

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if "ERROR" in line:
                count += 1

    return count
```

Memory usage is independent of total file size in the common case.

The important exception is when individual lines themselves are extremely large.

A "line-oriented" design does not guarantee bounded memory if one line can contain hundreds of megabytes.

---

## Very Large Records

Some formats contain records that may be much larger than normal lines.

Examples:

- minified JSON
- generated SQL
- malformed CSV rows
- attacker-controlled input

Production systems should enforce:

- maximum file size
- maximum record size
- maximum processing time
- maximum memory consumption

Do not assume newline-based streaming alone prevents memory exhaustion.

---

## Text Files in ETL

A typical batch pipeline may look like:

```text
Raw Text File
      │
      ▼
Streaming Reader
      │
      ▼
Decode
      │
      ▼
Parse
      │
      ▼
Validate
      │
      ▼
Transform
      │
      ▼
Database / Kafka / Object Storage
```

For example:

```python
from pathlib import Path


def process_file(path: Path) -> None:
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            record = parse_record(line)
            validate_record(record)
            persist(record, line_number)
```

Production pipelines should also define what happens when one record is invalid.

---

## Error Isolation in Batch Processing

A large file may contain millions of records.

Failing the entire job because of one malformed line may be undesirable.

A batch system can isolate failures:

```text
Record
  │
  ├── valid ──► process
  │
  └── invalid ──► quarantine / dead-letter output
```

For example:

```python
with path.open("r", encoding="utf-8") as file:
    for line_number, line in enumerate(file, start=1):
        try:
            record = parse_record(line)
            process(record)
        except ValueError as exc:
            record_error(line_number, line, exc)
```

The correct policy depends on whether the file represents:

- best-effort ingestion
- financial data
- configuration
- migration state
- contractual batch input

Critical data often should fail fast rather than silently skip records.

---

## Text Files and REST APIs

Text files may originate from HTTP uploads.

A typical flow is:

```text
Client
  │
  │ multipart upload
  ▼
Nginx / API Gateway
  │
  ▼
FastAPI / Django
  │
  ▼
Upload Validation
  │
  ▼
Temporary Storage
  │
  ▼
Streaming Processor
  │
  ▼
Persistent Storage
```

Do not assume that because an HTTP request is textual, the application should load the entire request into memory.

Large uploads should be streamed or delegated to object storage where appropriate.

---

## File Upload Security

Text files can still be malicious.

Examples include:

- path traversal
- enormous files
- malformed encodings
- malicious content hidden behind a `.txt` extension
- log injection payloads
- parser abuse

Validate:

- size
- encoding
- expected format
- structure
- content constraints
- storage location

Do not trust:

```text
filename
Content-Type
file extension
```

as complete validation.

---

## Log Files

Writing application logs directly to text files can be useful in simple environments:

```python
with log_path.open("a", encoding="utf-8") as file:
    file.write("request completed\n")
```

Production services commonly delegate log management to:

- stdout/stderr
- container logging
- centralized log collectors
- CloudWatch
- Elasticsearch/OpenSearch
- other observability platforms

This avoids treating a local file as the authoritative logging system.

---

## Log Injection

Never blindly place user-controlled data into structured or multiline logs.

For example:

```python
file.write(f"user={user_input}\n")
```

An attacker could inject additional lines.

Structured logging is generally safer:

```python
logger.info(
    "user request received",
    extra={"user_id": user_id},
)
```

The logging framework can handle encoding and formatting consistently.

---

## Atomic Text-File Updates

For configuration or generated metadata, direct writes can leave partially written files if the process crashes.

A safer pattern is:

```text
Generate content
      │
      ▼
Temporary file
      │
      ▼
Flush / sync
      │
      ▼
Atomic replace
      │
      ▼
Target file
```

Example:

```python
import os
import tempfile
from pathlib import Path


def atomic_write_text(path: Path, content: str) -> None:
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
    ) as file:
        file.write(content)
        file.flush()
        os.fsync(file.fileno())
        temporary_path = Path(file.name)

    os.replace(temporary_path, path)
```

The exact durability guarantees depend on the filesystem and storage environment.

---

## File Locking and Concurrent Writers

Multiple processes writing the same text file can corrupt or interleave data depending on the operation and platform.

Do not assume:

```python
with path.open("a", encoding="utf-8") as file:
    file.write(...)
```

provides a complete distributed logging or coordination mechanism.

For multiple application instances:

```text
Worker A ──┐
Worker B ──┼──► Shared State
Worker C ──┘
```

prefer a system designed for concurrent shared state:

- PostgreSQL
- Redis
- Kafka
- centralized logging
- object storage

Filesystem locking is a specialized solution, not a general distributed coordination mechanism.

---

## Text Files in Docker

Containerized applications frequently encounter text files through:

- environment configuration
- mounted secrets
- generated reports
- migration scripts
- temporary processing
- mounted volumes

Use configured paths:

```python
from pathlib import Path

config_path = Path("/app/config/settings.yaml")
```

but avoid assuming that files written inside the container are durable.

---

## Kubernetes

Kubernetes workloads may be restarted or rescheduled.

Therefore:

```text
Pod-local text file
       │
       └── may disappear with pod
```

Use:

- ConfigMaps for non-secret configuration
- Secrets for sensitive configuration
- PersistentVolumes for appropriate durable filesystem workloads
- object storage for scalable file storage

The exact choice depends on size, lifecycle, security, and access requirements.

---

## Text Files and AWS

For durable large files, Amazon S3 is commonly preferable to local application storage.

A typical architecture is:

```text
Application
    │
    ├── metadata ──► PostgreSQL
    │
    └── text file ──► S3
```

The database can store:

```text
file_id
object_key
encoding
content_type
size
checksum
created_at
```

This avoids coupling file durability to application instances.

---

## Testing

Text-file tests should use isolated temporary directories.

With pytest:

```python
from pathlib import Path


def write_message(path: Path, message: str) -> None:
    path.write_text(message, encoding="utf-8")


def test_write_message(tmp_path):
    path = tmp_path / "message.txt"

    write_message(path, "hello")

    assert path.read_text(encoding="utf-8") == "hello"
```

Test important boundaries:

- empty files
- missing files
- invalid UTF-8
- non-ASCII characters
- very long lines
- large files
- newline variations
- permission failures
- concurrent access where relevant
- partial writes
- malformed input

---

## Testing Encoding Behavior

Encoding tests should include non-ASCII data:

```python
def test_utf8_round_trip(tmp_path):
    path = tmp_path / "message.txt"
    content = "café — 東京 — বাংলা"

    path.write_text(content, encoding="utf-8")

    assert path.read_text(encoding="utf-8") == content
```

This catches assumptions that ASCII-only test data would miss.

---

## Performance Considerations

For text processing, performance is usually influenced by:

- storage throughput
- decoding cost
- parser complexity
- Python-level processing
- memory allocation
- number of filesystem calls

A useful hierarchy is:

```text
Storage I/O
    │
    ▼
Buffered read
    │
    ▼
Decode
    │
    ▼
Parse
    │
    ▼
Application processing
```

Optimizing the wrong layer can have little effect.

For large workloads, measure:

- MB/s processed
- records/s
- CPU utilization
- memory usage
- I/O wait
- error rate

---

## Memory Considerations

These operations have very different memory characteristics:

| Operation | Typical memory behavior |
|---|---|
| `read()` | Entire file |
| `readlines()` | Entire file plus list overhead |
| Iterating lines | Incremental |
| `read(size)` | Bounded by requested amount plus buffering |
| `json.load()` | Entire parsed structure |
| Streaming parser | Incremental, depending on parser |

For production ingestion, streaming should be the default when file size is potentially unbounded.

---

## Reliability Considerations

A reliable text-file workflow should define:

```text
Input
  │
  ▼
Validation
  │
  ▼
Processing
  │
  ├── success ──► durable output
  │
  └── failure ──► retry / quarantine / alert
```

For critical workflows, consider:

- checksums
- idempotent processing
- file manifests
- processing status
- temporary files
- atomic replacement
- retry policies
- reconciliation jobs

A filename alone is usually not enough to uniquely identify processing state.

---

## Observability

For batch text processing, useful metrics include:

- files processed
- bytes processed
- records processed
- records rejected
- processing duration
- throughput
- decoding failures
- parser failures
- storage failures
- retry count

Logs should include identifiers such as:

```text
job_id
file_id
source
line_number
processing_status
```

Avoid logging complete sensitive file contents.

---

## Common Mistakes and Pitfalls

### Omitting the Encoding

```python
open("data.txt")
```

can behave differently across environments.

Prefer:

```python
open("data.txt", encoding="utf-8")
```

when UTF-8 is the contract.

### Reading Huge Files With `read()`

This can exhaust process memory.

Use streaming.

### Using `readlines()` for Large Files

It creates a list containing all lines.

Iterate directly instead.

### Treating `str` and `bytes` as Equivalent

Text and bytes have different semantics. Encode and decode explicitly at system boundaries.

### Using `errors="ignore"`

This can silently destroy data.

Prefer strict failure unless data loss is explicitly acceptable.

### Ignoring Newline Semantics

This can cause incorrect output, especially with CSV and cross-platform processing.

### Assuming `flush()` Means Durable Storage

Flushing Python buffers is not equivalent to durable persistence.

### Writing Directly Over Critical Files

A crash can leave partial content.

Use atomic replacement where appropriate.

### Trusting File Extensions

A `.txt` filename does not guarantee safe or valid textual content.

### Treating Local Files as Distributed Storage

Multiple Kubernetes replicas cannot safely coordinate shared state through arbitrary local files.

### Logging Untrusted Text Directly

User-controlled newlines can create log-injection problems.

---

## Interview Traps

### Are text files stored as strings?

No. Files contain bytes. Python's text layer decodes those bytes into `str`.

### What does `encoding="utf-8"` do?

It tells Python how to decode bytes when reading and encode characters when writing.

### Why use `newline=""` with CSV?

It prevents universal newline translation from interfering with the CSV module's own newline handling.

### Why is iterating over a file memory-efficient?

The file is processed incrementally rather than loading all content into memory.

### Is `flush()` equivalent to `fsync()`?

No. `flush()` moves buffered data through Python's I/O layer, while `fsync()` requests synchronization of file data to the underlying storage system.

### Why can `read()` be dangerous?

It creates a complete in-memory representation of the file. For unbounded input, this can cause memory exhaustion.

### Does line-by-line processing always guarantee bounded memory?

No. A single line or record can itself be extremely large.

---

## Production Checklist

Before deploying text-file processing, verify:

- File resources are managed with context managers.
- The expected encoding is explicit.
- `str` and `bytes` conversions occur at clear boundaries.
- Invalid encodings have a defined failure policy.
- Newline behavior is appropriate for the file format.
- Large files are streamed instead of fully loaded into memory.
- Maximum file and record sizes are enforced.
- Temporary files are cleaned up.
- Critical updates use atomic replacement where appropriate.
- Concurrent writers are handled deliberately.
- User-controlled filenames and paths are not trusted.
- Uploaded content is validated beyond filename and MIME type.
- Local container storage is not assumed to be durable.
- Durable files use appropriate persistent storage or object storage.
- Batch processing has explicit handling for malformed records.
- Failed records can be quarantined when business requirements permit.
- Checksums or other integrity mechanisms are used when required.
- Logs do not expose sensitive file contents.
- User-controlled text cannot inject misleading log entries.
- Processing metrics expose throughput, failures, and rejected records.
- Tests cover Unicode, malformed encoding, empty files, large inputs, and newline behavior.
- Recovery and retry behavior is defined for storage and processing failures.

## Key Takeaways

- Text files contain bytes; Python's text I/O layer decodes those bytes into `str` using an encoding and encodes `str` back into bytes when writing.
- Use explicit encodings, context managers, and appropriate newline handling to make text processing predictable across development, CI/CD, containers, and production environments.
- Stream large files rather than using `read()` or `readlines()` when input size is unbounded, while also considering pathological cases such as extremely large individual lines.
- Treat uploaded and externally sourced text as untrusted input: validate encoding, size, structure, paths, and content rather than trusting filenames or MIME types.
- Reliable production workflows require more than file I/O: design for atomic updates, concurrent access, durable storage, observability, integrity, failure isolation, and recovery.