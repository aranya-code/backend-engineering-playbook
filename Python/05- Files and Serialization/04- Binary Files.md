# 04- Binary Files

## Overview

Binary files contain raw bytes rather than text characters. Python represents binary data primarily with `bytes` and `bytearray`, while binary file objects expose byte-oriented I/O.

The fundamental distinction is:

```text
Text File
    │
    ▼
Bytes on disk
    │
    │ decode
    ▼
Python str

Binary File
    │
    ▼
Bytes on disk
    │
    ▼
Python bytes / bytearray
```

Binary handling is required whenever the data should not be interpreted as text, including:

- images
- PDFs
- ZIP archives
- compressed files
- audio and video
- encrypted payloads
- cryptographic keys
- database backups
- serialized binary formats
- uploaded documents
- network protocol payloads

In backend systems, binary data frequently moves between HTTP requests, application memory, temporary storage, object storage such as S3, background workers, and downstream services.

The main engineering concerns are **correct byte handling, bounded memory usage, streaming, integrity, security, concurrency, and durable storage**.

---

## `bytes` and `bytearray`

Python provides two primary mutable/immutable byte-oriented types.

```python
data = b"hello"
mutable_data = bytearray(b"hello")
```

| Type | Mutable | Typical use |
|---|---:|---|
| `bytes` | No | Immutable binary data |
| `bytearray` | Yes | Mutable binary buffers |
| `memoryview` | View | Zero-copy access to existing buffers |

For most application-level binary data, `bytes` is the default representation.

---

## Bytes Are Not Text

This is binary data:

```python
payload = b"\x89PNG\r\n\x1a\n"
```

It should not automatically be decoded as UTF-8.

Text requires an encoding:

```python
text = "hello"
data = text.encode("utf-8")
```

Binary data has no requirement to represent characters.

The correct mental model is:

```text
str
 │
 │ encode
 ▼
bytes
 │
 │ decode
 ▼
str
```

Only perform the conversion when the protocol or file format requires it.

---

## Opening Binary Files

Use binary modes:

```python
from pathlib import Path

path = Path("documents/report.pdf")

with path.open("rb") as file:
    data = file.read()
```

Writing:

```python
with path.open("wb") as file:
    file.write(data)
```

Common modes are:

| Mode | Meaning |
|---|---|
| `rb` | Read binary |
| `wb` | Write binary, truncating existing content |
| `ab` | Append binary |
| `xb` | Create binary file exclusively |
| `rb+` | Read/write existing binary file |
| `wb+` | Read/write and truncate |
| `ab+` | Read/append binary |

Use `with` so the underlying file descriptor is released reliably.

---

## Binary File Lifecycle

A typical binary operation follows:

```text
Path
 │
 ▼
Open binary stream
 │
 ▼
Read / write bytes
 │
 ▼
Flush buffered data
 │
 ▼
Close stream
```

The file object manages the stream, while `Path` identifies the filesystem location.

```python
from pathlib import Path

path = Path("uploads/document.pdf")

with path.open("rb") as file:
    process(file)
```

For large files, `process()` should generally consume the stream incrementally.

---

## Reading Entire Binary Files

For small files:

```python
with path.open("rb") as file:
    data = file.read()
```

This is reasonable for:

- small images
- small configuration artifacts
- cryptographic metadata
- test fixtures
- small generated documents

But memory usage is proportional to the file size.

A 500 MB file loaded into memory is fundamentally different from a 500 KB file.

Do not use whole-file reads for unbounded user uploads or large object transfers.

---

## Chunked Reads

For large binary files, process chunks:

```python
from pathlib import Path

CHUNK_SIZE = 1024 * 1024


def process_file(path: Path) -> None:
    with path.open("rb") as file:
        while chunk := file.read(CHUNK_SIZE):
            process_chunk(chunk)
```

The memory model becomes approximately:

```text
Memory
  │
  ├── current chunk
  ├── buffering
  └── application processing state
```

rather than:

```text
Memory ≈ entire file
```

This is one of the most important binary-I/O patterns for production systems.

---

## Why Chunk Size Matters

A chunk that is too small can increase overhead:

```text
many reads
   │
   └── many system calls
```

A chunk that is too large increases memory usage.

Common chunk sizes are often in the range of hundreds of KiB to a few MiB, but there is no universally optimal value.

Benchmark the actual workload when throughput matters.

---

## Streaming

Streaming means processing binary data incrementally rather than materializing the complete payload.

```text
Source
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

This is useful for:

- file uploads
- downloads
- media processing
- checksums
- compression
- encryption
- object-storage transfers
- ETL pipelines

Streaming is especially important in containerized services with strict memory limits.

---

## Binary Writing

Write bytes directly:

```python
from pathlib import Path

path = Path("output.bin")

with path.open("wb") as file:
    file.write(b"\x00\x01\x02\x03")
```

For multiple chunks:

```python
with path.open("wb") as file:
    for chunk in generate_chunks():
        file.write(chunk)
```

The generator can produce data incrementally without constructing the complete output in memory.

---

## Copying Binary Files

For straightforward file copying, prefer `shutil` rather than manually implementing the copy loop.

```python
from pathlib import Path
import shutil

source = Path("input.pdf")
target = Path("archive/input.pdf")

target.parent.mkdir(parents=True, exist_ok=True)

shutil.copyfile(source, target)
```

For metadata-preserving copies, `shutil.copy2()` may be more appropriate.

Use lower-level chunk processing when the application needs to transform or inspect the data while copying.

---

## Binary File Position

File objects maintain a current position.

```python
with path.open("rb") as file:
    header = file.read(8)
    body = file.read()
```

The second read begins after the first eight bytes.

You can inspect the current position:

```python
position = file.tell()
```

and move it:

```python
file.seek(0)
```

This is useful for formats where metadata and payload are located at known offsets.

---

## Random Access

Binary files can support random access:

```python
with path.open("rb") as file:
    file.seek(1024)
    data = file.read(4096)
```

This can be useful for:

- fixed-size records
- indexed binary formats
- media files
- database-like local formats
- partial downloads

Random access performance depends heavily on the underlying storage.

A local SSD and a remote network filesystem can have very different latency characteristics.

---

## `read()` and `readinto()`

Normal reads allocate a new `bytes` object:

```python
data = file.read(4096)
```

For specialized high-performance workflows, `readinto()` can write directly into a preallocated mutable buffer:

```python
buffer = bytearray(4096)

with path.open("rb") as file:
    count = file.readinto(buffer)
```

This can reduce allocations in tight loops.

It is an optimization for specialized workloads, not a default requirement for ordinary backend code.

---

## `memoryview`

`memoryview` provides a view over an existing buffer without necessarily copying the underlying data.

```python
data = bytearray(b"abcdef")
view = memoryview(data)

print(view[1:4])
```

It is useful when working with:

- high-throughput binary processing
- protocol buffers
- image processing
- network buffers
- low-copy transformations

Avoid introducing `memoryview` merely for theoretical optimization. Use profiling to justify it.

---

## Buffer Protocol

Python objects such as:

- `bytes`
- `bytearray`
- `memoryview`

participate in the buffer protocol.

This allows compatible libraries to operate on binary memory without requiring unnecessary conversions.

Conceptually:

```text
Underlying Buffer
      │
      ├── bytes
      ├── bytearray
      └── memoryview
```

This becomes important in performance-sensitive applications where copying large buffers is expensive.

---

## Binary Data and HTTP

HTTP payloads are fundamentally bytes.

A backend may receive:

```text
HTTP Request
     │
     ▼
Raw bytes
     │
     ├── image
     ├── PDF
     ├── ZIP
     └── JSON / text
```

Textual payloads can then be decoded according to their content type and encoding.

Binary uploads should remain binary until a format-specific parser needs to interpret them.

---

## File Upload Architecture

A scalable upload design can look like:

```mermaid
flowchart LR
    A[Client] --> B[Nginx / API Gateway]
    B --> C[FastAPI / Django]
    C --> D[Validation]
    D --> E[Temporary Stream]
    E --> F[Object Storage]
    F --> G[PostgreSQL Metadata]
```

For large files, the application may avoid buffering the entire payload.

An even more scalable design can upload directly from the client to S3 using a presigned URL:

```text
Client
   │
   ├── request upload authorization ──► API
   │
   ◄── presigned URL ──────────────────┤
   │
   └────────────── file ───────────────► S3
```

The API then records metadata rather than carrying the complete file through the application tier.

---

## Binary Files and S3

Object storage is generally more appropriate than local disk for durable large files in distributed systems.

Example metadata:

```text
file_id
bucket
object_key
content_type
size
checksum
created_at
```

The application stores metadata in PostgreSQL while S3 stores the binary object.

This architecture avoids tying durable file storage to a particular application instance.

---

## Content Type

Binary files often have a MIME type:

```text
application/pdf
image/png
image/jpeg
application/zip
```

However, a declared MIME type is metadata, not proof of content.

Do not trust:

```http
Content-Type: image/png
```

as the only validation mechanism for security-sensitive uploads.

---

## File Signatures

Many binary formats begin with characteristic bytes.

Examples include:

```text
PNG  → 89 50 4E 47 ...
PDF  → 25 50 44 46 ...
ZIP  → 50 4B 03 04 ...
```

These signatures can help identify actual content.

However, robust validation should use a format-aware parser when security or correctness matters.

Do not treat a magic-byte check as complete malware or content validation.

---

## Binary File Validation

A production upload pipeline can validate:

```text
Request
  │
  ▼
Size limit
  │
  ▼
Declared type
  │
  ▼
Magic bytes / signature
  │
  ▼
Format parser
  │
  ▼
Security scanning
  │
  ▼
Durable storage
```

Validation requirements depend on the file type and threat model.

For example, uploaded PDFs may require different validation than raw application-generated binary data.

---

## Security Considerations

Binary files can carry security risks even when they are not executable by the application.

Potential threats include:

- malware
- parser vulnerabilities
- decompression bombs
- oversized files
- malicious metadata
- path traversal
- polyglot files
- resource exhaustion

Defenses may include:

- strict size limits
- content validation
- antivirus scanning
- sandboxed processing
- isolated workers
- generated storage keys
- least-privilege permissions
- encryption
- content-disposition controls

Never process untrusted binary content with unnecessary privileges.

---

## Decompression Bombs

Compressed data can expand dramatically:

```text
Small compressed input
        │
        ▼
Huge decompressed output
        │
        ▼
Memory / CPU / storage exhaustion
```

For archive processing, enforce limits on:

- compressed input size
- number of entries
- total uncompressed size
- individual file size
- directory depth
- processing time

Do not assume that a small uploaded archive is cheap to process.

---

## Encryption

Encrypted binary payloads are still bytes:

```python
ciphertext: bytes
```

Do not decode encrypted data as text simply because it needs to be transported.

For transport:

```text
Binary ciphertext
      │
      ├── raw bytes
      └── Base64 if a text-only transport requires it
```

Base64 increases payload size, so use it only when required by the protocol.

---

## Base64

Base64 converts binary data into ASCII characters.

```python
import base64

encoded = base64.b64encode(b"binary data")
decoded = base64.b64decode(encoded)
```

It is useful when a system requires text-only transport.

However, Base64 introduces approximately 33% encoding overhead before other framing or compression effects.

Do not Base64-encode large binary files unnecessarily.

Prefer native binary upload mechanisms when available.

---

## Binary Data in JSON

This is common:

```json
{
  "file": "base64-encoded-content"
}
```

but inefficient for large files because:

- Base64 increases size
- JSON adds additional structure
- the application may materialize the entire payload
- API memory usage increases

For large files, use multipart uploads or direct object-storage uploads instead.

---

## Checksums

Checksums can verify binary integrity.

For example:

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

The implementation is streaming and does not require the entire file in memory.

Checksums can support:

- integrity verification
- deduplication
- upload validation
- content-addressed storage
- corruption detection

---

## Hashing vs Encryption

These solve different problems.

| Mechanism | Purpose |
|---|---|
| Hash | Integrity / fingerprint |
| Encryption | Confidentiality |
| Digital signature | Integrity + authenticity |
| MAC | Integrity + authenticity with shared secret |

Do not use a cryptographic hash as a substitute for encryption.

---

## Binary Files and Concurrency

Concurrent processing creates several concerns:

```text
Worker A ──► read file
Worker B ──► modify file
Worker C ──► delete file
```

Possible outcomes include:

- stale reads
- partial writes
- missing files
- corrupted output
- conflicting updates

Prefer immutable object naming for generated artifacts:

```text
reports/
    report-8a1f....pdf
```

rather than having many workers mutate one shared file.

---

## Atomic Binary Writes

For important local files, write to a temporary file and replace the target.

```python
import os
import tempfile
from pathlib import Path


def atomic_write_bytes(path: Path, data: bytes) -> None:
    with tempfile.NamedTemporaryFile(
        mode="wb",
        dir=path.parent,
        delete=False,
    ) as file:
        file.write(data)
        file.flush()
        os.fsync(file.fileno())
        temporary_path = Path(file.name)

    os.replace(temporary_path, path)
```

For very large files, avoid first constructing `data` as a complete `bytes` object. Stream the producer into the temporary file instead.

---

## Streaming Atomic Writes

For large generated files:

```python
import os
import tempfile
from pathlib import Path
from collections.abc import Iterable


def atomic_write_chunks(
    path: Path,
    chunks: Iterable[bytes],
) -> None:
    with tempfile.NamedTemporaryFile(
        mode="wb",
        dir=path.parent,
        delete=False,
    ) as file:
        for chunk in chunks:
            file.write(chunk)

        file.flush()
        os.fsync(file.fileno())
        temporary_path = Path(file.name)

    os.replace(temporary_path, path)
```

This combines:

- bounded memory
- temporary isolation
- atomic replacement

The exact durability guarantees depend on the filesystem.

---

## Temporary Binary Files

Use `tempfile` rather than manually generating temporary filenames.

```python
from tempfile import NamedTemporaryFile

with NamedTemporaryFile(mode="wb") as file:
    file.write(binary_data)
    file.flush()
    process(file.name)
```

This avoids common filename-collision and insecure temporary-file creation patterns.

For large files, monitor temporary storage capacity.

---

## Binary Processing in Celery

Large binary workloads are often better handled asynchronously:

```text
API
 │
 ├── validate upload
 ├── persist object
 └── enqueue job
          │
          ▼
       Celery
          │
          ▼
   Binary processing
          │
          ▼
   Result in S3
```

Examples include:

- PDF conversion
- image resizing
- video transcoding
- archive processing
- malware scanning

Workers should have explicit:

- memory limits
- CPU limits
- execution timeouts
- temporary-storage limits
- retry policies

---

## Binary Processing and Kafka

Kafka messages are byte-oriented, but large binary objects generally should not be embedded directly into messages.

A common architecture is:

```text
Binary Object
     │
     ▼
S3
     │
     └── object key ──► Kafka Event
```

Example event:

```json
{
  "event_type": "document_uploaded",
  "file_id": "8f7c...",
  "object_key": "documents/8f7c....pdf"
}
```

This keeps event payloads small while allowing consumers to retrieve the actual object.

---

## Database Storage

Binary data can be stored in databases using binary columns such as PostgreSQL `bytea`.

This can be appropriate for:

- small objects
- transactional data tightly coupled to the row
- cryptographic material where appropriate
- specialized application requirements

It is often less suitable for very large objects.

For large files, object storage commonly provides better scalability and operational characteristics.

---

## Database vs Object Storage

| Requirement | Database binary column | Object storage |
|---|---|---|
| Small binary payloads | Good | Good |
| Very large files | Usually less suitable | Excellent |
| Transactional coupling | Strong | Requires coordination |
| Horizontal scaling | Database-dependent | Strong |
| CDN integration | Limited | Strong |
| Object lifecycle policies | Limited | Strong |
| Metadata querying | Excellent | Usually external metadata |
| Large file throughput | Workload-dependent | Designed for it |

Choose based on access patterns rather than a universal rule.

---

## Binary Data and Memory Management

A common hidden cost is repeated copying:

```text
network buffer
    │
    ▼
bytes object
    │
    ▼
temporary bytes
    │
    ▼
processed bytes
    │
    ▼
output bytes
```

Large payloads can therefore consume significantly more memory than the raw file size.

Production systems should minimize unnecessary copies.

Useful techniques include:

- streaming
- chunk processing
- `memoryview`
- direct object-storage transfer
- streaming request/response APIs
- incremental hashing

---

## Network Streaming

For a large download, the ideal architecture is often:

```text
S3
 │
 │ stream
 ▼
Application / proxy
 │
 │ stream
 ▼
Client
```

rather than:

```text
S3
 │
 ▼
Application memory
 │
 ▼
Client
```

The second approach unnecessarily makes application memory part of the transfer path.

When possible, direct client-to-S3 or S3-to-client flows reduce backend resource usage.

---

## Range Requests

Some HTTP clients request only portions of large files.

```http
Range: bytes=1048576-2097151
```

This can support:

- resumable downloads
- media seeking
- partial retrieval
- large-file acceleration

Implementing range semantics correctly requires attention to:

- byte offsets
- content length
- `206 Partial Content`
- `Content-Range`
- caching
- storage backend capabilities

Do not implement custom range handling casually.

---

## File Integrity During Transfer

A robust transfer pipeline can track:

```text
Expected size
     +
Expected checksum
     │
     ▼
Transferred bytes
     │
     ▼
Calculated checksum
     │
     ▼
Verification
```

If verification fails:

- do not mark the file complete
- retry if appropriate
- quarantine the object
- emit an operational signal

This is especially useful for large data transfers.

---

## Binary File Formats

Binary files may have internal structure.

For example:

```text
Header
  │
  ├── version
  ├── metadata
  ├── flags
  └── payload length
          │
          ▼
       Payload
```

Do not treat a structured binary format as an arbitrary byte sequence.

Use a format-specific parser or library when available.

Examples include:

- image libraries
- PDF libraries
- archive libraries
- protocol implementations
- serialization libraries

Parsing untrusted binary formats should be considered a security-sensitive operation.

---

## Serialization Formats

Binary serialization formats may provide:

- compact representation
- faster parsing
- schema support
- efficient network transfer

Examples include:

- Protocol Buffers
- MessagePack
- Avro
- Parquet
- application-specific binary formats

Selection should consider:

- schema evolution
- language interoperability
- size
- performance
- tooling
- compatibility
- security

Python-specific `pickle` has different characteristics and should not be treated as a general-purpose interchange format.

---

## Compression and Binary Data

Binary data may already be compressed.

Examples:

```text
JPEG
PNG
ZIP
GZIP
```

Compressing already-compressed content often produces little benefit while consuming CPU.

For data pipelines, measure:

```text
CPU cost
+
compression ratio
+
network savings
+
storage savings
```

before introducing additional compression.

---

## Observability

Binary-processing systems should expose metrics such as:

- files processed
- bytes processed
- upload throughput
- download throughput
- processing latency
- checksum failures
- validation failures
- parser failures
- storage errors
- temporary-storage usage
- worker memory usage

Do not log entire binary payloads.

Instead log identifiers:

```text
file_id
object_key
size
content_type
checksum
job_id
processing_status
```

Sensitive metadata should also be handled according to the application's privacy requirements.

---

## Reliability and Recovery

Binary workflows often cross multiple systems:

```text
Client
  │
  ▼
API
  │
  ▼
Temporary Storage
  │
  ▼
S3
  │
  ▼
PostgreSQL
  │
  ▼
Celery / Kafka
```

Each boundary can fail independently.

A reliable design should define:

- idempotency
- retry behavior
- cleanup
- reconciliation
- orphan detection
- processing status
- retention
- failure quarantine

For example, if S3 upload succeeds but database metadata creation fails, a reconciliation process may need to detect and clean up the orphaned object.

---

## Disaster Recovery

Durable binary data should have an explicit recovery strategy.

Depending on requirements, this may include:

- S3 versioning
- replication
- backups
- lifecycle policies
- cross-region copies
- database metadata backups

The recovery design should align with:

- RPO
- RTO
- retention requirements
- compliance
- cost

Local binary files inside application containers should not be considered a disaster-recovery mechanism.

---

## Common Mistakes and Pitfalls

### Opening Binary Data in Text Mode

```python
open("file.pdf", "r")
```

can attempt to decode arbitrary bytes as text.

Use:

```python
open("file.pdf", "rb")
```

### Loading Huge Files Into Memory

```python
data = file.read()
```

can cause memory exhaustion.

Stream or chunk large files.

### Base64-Encoding Everything

Base64 adds size overhead and unnecessary processing.

Use native binary transport when possible.

### Trusting MIME Types

A declared content type is not proof of the actual file format.

### Trusting File Extensions

`report.pdf` does not prove the content is a valid PDF.

### Using User Filenames as Storage Keys

This can enable traversal, collisions, and awkward storage semantics.

Generate server-side storage identifiers.

### Treating S3 Keys as Filesystem Paths

Object keys resemble paths but do not have filesystem semantics.

### Concurrently Mutating Shared Files

Multiple workers can create races and inconsistent state.

Prefer immutable files or transactional storage.

### Compressing Already-Compressed Data

This can waste CPU while providing little storage benefit.

### Logging Binary Payloads

This can cause huge logs, performance problems, and data leakage.

### Ignoring Decompression Limits

A small archive can expand into enormous resource consumption.

### Assuming `flush()` Guarantees Durability

Buffer flushing does not by itself establish physical persistence guarantees.

### Storing Every Large File in PostgreSQL

Database binary storage can increase database size, backup duration, replication traffic, and operational cost.

---

## Testing

Binary processing should use realistic byte-level test cases.

```python
def test_binary_round_trip(tmp_path):
    path = tmp_path / "payload.bin"
    payload = bytes(range(256))

    path.write_bytes(payload)

    assert path.read_bytes() == payload
```

Test:

- empty files
- small files
- large files
- arbitrary byte values
- truncated files
- corrupted headers
- invalid formats
- checksum mismatches
- permission errors
- concurrent access where relevant
- interrupted processing
- storage failures

Avoid using only ASCII-compatible bytes because such tests can accidentally hide text/binary mistakes.

---

## Testing Large Files

Large-file tests should verify that processing does not accidentally materialize the entire file.

For example, test a chunk-processing function independently from storage:

```python
def process_chunks(chunks):
    total = 0

    for chunk in chunks:
        total += len(chunk)

    return total


def test_processes_chunks_incrementally():
    chunks = [b"a" * 1024, b"b" * 2048]

    assert process_chunks(chunks) == 3072
```

Integration tests can then verify actual filesystem or object-storage behavior.

---

## Performance Testing

For binary workloads, benchmark realistic file sizes.

Measure:

| Metric | Why it matters |
|---|---|
| Throughput | Overall processing capacity |
| Latency | User-visible performance |
| Memory | Container sizing |
| CPU | Processing cost |
| I/O wait | Storage bottlenecks |
| Network throughput | Transfer bottlenecks |
| Temporary storage | Capacity planning |

A benchmark using a 1 MB file may tell you very little about a service expected to process 5 GB objects.

---

## Production Checklist

Before deploying binary-file processing, verify:

- Binary files are opened with `rb`, `wb`, or another appropriate binary mode.
- `bytes` and `str` are not mixed accidentally.
- Large files are streamed or chunked.
- Maximum upload size is enforced.
- Maximum processing and decompression limits are enforced.
- User-controlled paths and filenames are not trusted.
- Storage keys are generated safely.
- File content is validated rather than relying only on extensions or MIME types.
- Untrusted binary formats are parsed in appropriately isolated environments when necessary.
- Temporary files use secure mechanisms such as `tempfile`.
- Critical local writes use atomic replacement where appropriate.
- Concurrent access is explicitly designed rather than assumed to be safe.
- Checksums are used where integrity verification is required.
- Binary payloads are not unnecessarily Base64-encoded.
- Large objects are preferably stored in appropriate object storage.
- Database binary storage is used intentionally rather than as a default for large files.
- S3 or equivalent object storage is used for durable distributed file storage where appropriate.
- Kafka events contain object references rather than unnecessarily embedding large binary payloads.
- Celery workers have appropriate CPU, memory, timeout, and temporary-storage limits.
- Retry behavior is idempotent.
- Partial failures and orphaned objects have a reconciliation strategy.
- Observability measures bytes, throughput, failures, and processing latency.
- Sensitive binary data is not written to logs.
- Backup, retention, replication, and disaster-recovery requirements are defined.
- Tests cover arbitrary bytes, corruption, truncation, large inputs, and storage failures.

## Key Takeaways

- Binary files are byte-oriented resources; use `bytes`, binary file modes, and explicit streaming rather than treating arbitrary binary content as text.
- For production workloads, stream or chunk large files to keep memory bounded and avoid turning file size directly into application memory consumption.
- Treat binary uploads as untrusted input: validate size, format, content, paths, and processing limits, and isolate risky parsers or decompression workloads when necessary.
- Prefer durable object storage such as S3 for large distributed files, while keeping metadata and transactional state in systems such as PostgreSQL.
- Reliable binary workflows require explicit handling of integrity, atomicity, concurrency, retries, partial failures, observability, retention, and disaster recovery.