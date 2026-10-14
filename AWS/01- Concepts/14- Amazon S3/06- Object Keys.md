# 06- Object Keys

## Overview

An Amazon S3 object key is the name used to identify an object within a bucket. Together, the bucket name and object key identify the object. When versioning is enabled, a version ID can additionally identify a specific version of that object.

Object keys are fundamental to how backend applications store, retrieve, organize, and process data in Amazon S3.

For example, a document management service might use the following object key:

```text
tenants/tenant-1042/documents/2026/10/invoice-7f42a91c.pdf
```

This key communicates a logical hierarchy through its prefixes, but S3 does not treat those segments as conventional filesystem directories. The entire string is one object key.

Object key design affects more than readability. It influences listing efficiency, lifecycle policy targeting, event notification filtering, application authorization, data migration, concurrent updates, and integration with services such as Lambda, SQS, and analytics platforms.

A production-ready key scheme should be predictable, safe to construct, compatible with relevant APIs, and stable enough that database records and asynchronous workflows can reference objects reliably.

## Object Key Fundamentals

### What Is an Object Key?

An object key is a sequence of Unicode characters encoded as UTF-8. It uniquely identifies an object's name within a bucket.

For example:

```text
Bucket:
    acme-documents-prod

Object key:
    tenants/tenant-1042/documents/invoice-001.pdf
```

The following elements have distinct meanings:

| Element | Example | Meaning |
|---|---|---|
| Bucket | `acme-documents-prod` | Storage resource containing the object |
| Prefix | `tenants/tenant-1042/` | Beginning portion of the object key |
| Logical category | `documents/` | Convention used by the application |
| Filename component | `invoice-001.pdf` | Descriptive portion of the key |
| Complete object key | `tenants/tenant-1042/documents/invoice-001.pdf` | Actual key passed to S3 APIs |

Only the bucket and complete key are needed to identify the current object. Prefixes and filename components are conventions chosen by the application.

### Key Length

An S3 object key can be up to **1,024 bytes** long. The limit includes every character in the key, including prefixes, delimiters, and the filename.

The limit is measured in UTF-8 bytes, not necessarily in Unicode characters.

For example, ASCII characters generally require one byte each, while certain non-ASCII characters require multiple bytes.

```python
key = "documents/café/invoice.pdf"

print(len(key))                      # Number of Python characters
print(len(key.encode("utf-8")))      # Number of UTF-8 bytes
```

These values are not guaranteed to be identical.

Applications that allow Unicode filenames should validate the encoded byte length rather than relying only on `len(key)`.

### Case Sensitivity

S3 object keys are case-sensitive.

The following are different keys:

```text
reports/October.csv
reports/october.csv
Reports/October.csv
```

This matters when applications generate keys, build cache keys, process events, or migrate objects between storage systems that may have different case-sensitivity behavior.

Choose a consistent convention and avoid normalizing the case of existing keys unless the migration is intentional.

### Flat Namespace

S3 uses a flat object namespace within a bucket. Slashes and other characters are part of the object key; they do not create actual directories.

Consider these keys:

```text
documents/invoices/invoice-001.pdf
documents/invoices/invoice-002.pdf
documents/contracts/contract-001.pdf
```

The S3 console presents them in a directory-like hierarchy, but each complete path-like string is an individual key.

An application can upload an object using a key such as:

```text
documents/invoices/invoice-001.pdf
```

without creating the `documents/` or `invoices/` directories first.

An empty folder displayed in the console may be represented by a zero-byte object whose key ends with `/`. Such a folder marker is itself an object, not a native filesystem directory.

## Object Keys and Prefixes

### What Is a Prefix?

A prefix is any beginning portion of an object key.

Given the key:

```text
tenants/tenant-1042/documents/2026/invoice-001.pdf
```

Examples of prefixes include:

```text
tenants/
tenants/tenant-1042/
tenants/tenant-1042/documents/
tenants/tenant-1042/documents/2026/
```

A prefix allows an application to restrict listing operations to objects whose keys begin with a particular string.

For example, a listing request with the prefix:

```text
tenants/tenant-1042/documents/
```

can return the matching keys for that tenant's document namespace.

Prefixes are useful for logical grouping, filtering, operational organization, and applying selected S3 management rules.

### Prefix and Delimiter

The S3 `ListObjectsV2` API supports both `Prefix` and `Delimiter`.

- `Prefix` restricts the results to keys beginning with the supplied string.
- `Delimiter` groups matching keys into common prefixes in the response.

For example, consider:

```text
reports/2026/january.csv
reports/2026/february.csv
reports/2025/december.csv
```

A request using `Prefix="reports/"` and `Delimiter="/"` can group the results into prefixes such as `reports/2025/` and `reports/2026/`.

A request using `Prefix="reports/2026/"` narrows the results to the specified year.

The delimiter does not change the stored object keys. It changes how the listing response groups matching keys.

### Listing Objects with Boto3

```python
import boto3


def list_document_keys(
    bucket: str,
    tenant_id: str,
) -> list[str]:
    """List document keys under a trusted tenant prefix."""
    s3 = boto3.client("s3")

    prefix = f"tenants/{tenant_id}/documents/"
    paginator = s3.get_paginator("list_objects_v2")

    keys: list[str] = []

    for page in paginator.paginate(
        Bucket=bucket,
        Prefix=prefix,
    ):
        for item in page.get("Contents", []):
            keys.append(item["Key"])

    return keys
```

This example uses an SDK paginator because a single listing response may not contain every matching object.

In a production application, `tenant_id` must come from a trusted, authorization-checked source. Do not allow a user to enumerate another tenant's documents simply by supplying another tenant identifier.

For a large namespace, return pages to the caller or process objects incrementally rather than collecting every matching key in application memory.

Reference: [Organizing objects using prefixes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-prefixes.html).

## Designing a Production Object Key Scheme

A useful key scheme should reflect the application's access patterns without encoding unnecessary business logic into the storage layer.

Consider a multi-tenant document management platform. Different services may need to retrieve individual documents, list documents for a tenant, process new uploads, or identify data belonging to a particular lifecycle category.

A suitable key design might be:

```text
tenants/<tenant-id>/documents/<document-id>/<object-id>.<extension>
```

For example:

```text
tenants/tenant-1042/documents/doc-8f14e45f/7f42c19e.pdf
```

This scheme separates several concepts:

- Tenant scope.
- Application-level document identity.
- Physical stored-object identity.
- File extension, where useful.

The application can maintain a database record that associates the logical document with its actual S3 object key.

This separation is valuable when a document is reprocessed, replaced, or retained in multiple versions.

### Recommended Key Design Principles

**Use stable identifiers.** Generate keys from controlled identifiers such as UUIDs or other unique application IDs rather than relying exclusively on original filenames.

**Keep keys predictable.** Consistent conventions simplify listing, migrations, event processing, monitoring, and operational inspection.

**Avoid exposing sensitive values.** Keys can appear in logs, events, request traces, and presigned URLs. Do not embed secrets or unnecessary personal information.

**Design around read and listing patterns.** If a service frequently lists all objects for a tenant, a tenant prefix may be useful. If analytics jobs process data by date, a date-oriented prefix can make batch discovery easier.

**Keep business rules outside the key where possible.** Do not make a key the only source of truth for ownership, workflow status, or retention decisions.

**Avoid unnecessary complexity.** Hashing, encoding, or partitioning every key is not automatically beneficial. Add complexity only when the workload requires it.

### UUID-Based Keys

UUID-based keys reduce collisions and make it less likely that two uploads accidentally target the same key.

For example:

```text
tenants/tenant-1042/documents/7f42c19e-0b24-4c10-bc92-5e81b826ad3f.pdf
```

A UUID does not guarantee authorization or secrecy. It is an identifier, not an access-control mechanism.

For public-facing systems, do not assume that an unguessable object key makes an object safe to expose. Enforce access permissions independently.

## Generating Safe Object Keys in Python

Never use a client-supplied filename as the complete object key without validation and an explicit overwrite strategy.

A safer approach is to retain the original filename in the database and generate the S3 key using trusted application identifiers.

```python
from uuid import uuid4


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".csv",
}


def build_document_key(
    tenant_id: str,
    document_id: str,
    original_extension: str,
) -> str:
    """Build an object key using trusted identifiers."""
    extension = original_extension.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file extension.")

    if not tenant_id or not document_id:
        raise ValueError("Tenant and document IDs are required.")

    object_id = uuid4().hex

    key = (
        f"tenants/{tenant_id}/documents/"
        f"{document_id}/{object_id}{extension}"
    )

    if len(key.encode("utf-8")) > 1024:
        raise ValueError("Object key exceeds the S3 byte-length limit.")

    return key
```

The example assumes that `tenant_id`, `document_id`, and `original_extension` have already been derived from trusted application state or validated using appropriate rules.

Additional production controls should include:

- Verify that the caller can upload to the specified tenant and document.
- Validate file content instead of trusting the extension or declared content type.
- Apply upload size limits.
- Store the generated key and original filename in the database.
- Use an appropriate S3 credential or role with narrowly scoped permissions.
- Define behavior for retries and duplicate upload attempts.

UUID generation reduces accidental naming collisions, but the upload workflow still needs an explicit policy for what happens if a key already exists.

## Original Filenames vs Object Keys

The original filename and the S3 object key serve different purposes.

| Concern | Original filename | Object key |
|---|---|---|
| Primary purpose | User-facing identification | Storage identification |
| Source | Usually supplied by the client | Preferably generated or controlled by the application |
| Uniqueness | Often not unique | Should follow the application's collision policy |
| Renaming | May be changed for display | Changing the key generally requires a copy-and-delete workflow |
| Business meaning | May be useful to the user | Should primarily support predictable storage behavior |
| Security concerns | May contain unsafe characters or misleading extensions | Must be controlled to prevent unexpected access or overwrite behavior |

For example, a customer may upload:

```text
October Invoice Final (Approved).pdf
```

The backend can store the display name in PostgreSQL and use a controlled key:

```text
tenants/tenant-1042/documents/doc-8f14e45f/7f42c19e.pdf
```

The application can still present the original filename when a user downloads the document.

When a download response needs to preserve the original name, use a correctly configured `Content-Disposition` header or another appropriate delivery mechanism. Avoid embedding an untrusted filename directly into response headers without proper encoding and validation.

## Special Characters and URL Encoding

S3 object keys may contain a wide range of UTF-8 characters. However, not every key is equally convenient for URLs, shell commands, XML-based APIs, log processing, or application frameworks.

Characters such as spaces, `+`, `%`, `#`, `?`, and some Unicode characters require particular care when passed through URL-based interfaces.

Consider these keys:

```text
documents/October Invoice.pdf
documents/100% complete.pdf
documents/report#final.csv
documents/a+b.csv
```

They may be valid object keys, but raw string interpolation into URLs can produce incorrect requests because these characters have special meanings in different protocols.

### URL Encoding Is Not Object Key Renaming

URL encoding changes how a key is represented in a request. It does not change the underlying S3 key.

For example, a space may be represented as `%20` in a URL path. Other characters require their corresponding percent-encoded representation.

Do not apply URL encoding repeatedly. Double-encoding can cause the request to target a different key.

Prefer an AWS SDK to construct and sign requests rather than manually building S3 REST URLs.

### S3 Event Notification Keys

Object keys included in S3 event notification records are URL-encoded. A space can appear as `+`, while a literal plus sign can appear as `%2B`.

When processing these events, decode the key using the appropriate URL-decoding behavior.

```python
from urllib.parse import unquote_plus


def decode_s3_event_key(encoded_key: str) -> str:
    """Decode an object key from an S3 event notification."""
    return unquote_plus(encoded_key)


assert decode_s3_event_key("reports/October+Invoice.pdf") == (
    "reports/October Invoice.pdf"
)

assert decode_s3_event_key("reports/a%2Bb.csv") == "reports/a+b.csv"
```

Without proper decoding, a Lambda function or event consumer may try to retrieve an object using the wrong key and receive `NoSuchKey`.

Reference: [S3 event notification message structure](https://docs.aws.amazon.com/AmazonS3/latest/userguide/notification-content-structure.html).

## Avoiding Period-Only Path Segments

Keys containing standalone `.` or `..` segments can be interpreted as relative paths by libraries, tools, browsers, or intermediate systems.

For example:

```text
documents/./invoice.pdf
documents/../invoice.pdf
./invoice.pdf
../invoice.pdf
```

Although certain relative-path-containing object keys are valid under S3's documented rules, they can create unexpected behavior when another component normalizes the path.

A key such as:

```text
documents/../invoice.pdf
```

may be interpreted as:

```text
invoice.pdf
```

by a path-normalization function, even though the intended S3 key contains the `..` segment.

Prefer keys that do not contain standalone relative-path segments.

Do not confuse these with filenames such as:

```text
documents/.hidden/invoice.pdf
documents/..backup/invoice.pdf
```

Here, the period characters are part of ordinary segment names rather than standalone relative-path references.

### Preventing Path Normalization Bugs

Avoid using local filesystem path utilities to construct S3 keys without considering their semantics.

For example, `os.path.join()` follows the operating system's path conventions and may introduce backslashes on Windows.

For S3 keys, construct logical key components using the `/` delimiter deliberately.

```python
def make_key(*segments: str) -> str:
    """Join validated logical S3 key segments using forward slashes."""
    if not segments:
        raise ValueError("At least one segment is required.")

    for segment in segments:
        if (
            not segment
            or segment in {".", ".."}
            or "/" in segment
            or "\\" in segment
        ):
            raise ValueError(f"Invalid key segment: {segment!r}")

    return "/".join(segments)


key = make_key(
    "tenants",
    "tenant-1042",
    "documents",
    "invoice-7f42a91c.pdf",
)
```

This helper is intentionally restrictive. Applications that support arbitrary Unicode names or other characters should define and test their own validation policy.

Reference: [Object key naming guidelines](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-keys.html).

## Key Ordering and Date-Based Partitioning

S3 sorts object keys lexicographically according to their UTF-8 encoded byte values.

This behavior can be useful when designing keys for logs, analytics, or date-based ingestion.

For example:

```text
events/2026/10/12/event-0001.json
events/2026/10/12/event-0002.json
events/2026/10/13/event-0001.json
```

The year, month, and day components use fixed-width numeric representations, making the keys naturally sortable by date.

For timestamp-oriented workloads, another possible structure is:

```text
events/year=2026/month=10/day=13/hour=18/<event-id>.json
```

Such layouts can make prefix filtering and partition discovery easier for batch-processing and analytics workloads.

However, object-key ordering should not be treated as a substitute for a database index or a transactional ordering mechanism. Lexicographical order reflects key bytes, not necessarily business-event order or the time at which an upload completed.

### When to Use Date-Based Prefixes

Date-based prefixes can be useful for:

- Application log ingestion.
- Time-partitioned event data.
- Daily exports and reports.
- Analytics processing with date filters.
- Retention policies for time-bounded datasets.

Use UTC or another explicitly defined timezone convention consistently. If the same dataset mixes local timestamps and UTC timestamps without recording the difference, prefix-based analysis can become difficult.

For analytics systems, align the key layout with the downstream processing model rather than inventing a hierarchy solely to make the console appear organized.

## Performance Implications of Object Key Design

Object key layout can influence the ease of listing, filtering, and managing objects. It can also matter for very high request-rate workloads, but performance planning should reflect current S3 behavior rather than outdated assumptions.

### Prefer Useful Prefixes

A prefix should help the application identify the objects it needs.

For example:

```text
tenant-1042/documents/
tenant-1042/reports/
tenant-2098/documents/
```

A request that lists the `tenant-1042/documents/` prefix can return a narrower set of keys than listing the entire bucket.

Prefixes also support event-notification filtering and selected lifecycle configuration patterns.

### Do Not Randomize Every Key by Default

Older S3 performance guidance commonly recommended randomizing key prefixes to distribute requests.

Modern S3 automatically scales to high request rates, and ordinary workloads generally do not need random prefixes solely to obtain acceptable performance.

AWS documents baseline request-rate guidance of at least 3,500 PUT/COPY/POST/DELETE requests or 5,500 GET/HEAD requests per second per partitioned prefix. Actual performance depends on the workload, and scaling to sustained increases happens gradually.

For workloads that approach or exceed the relevant guidance, evaluate request distribution, parallelism, 503 responses, KMS limits, network throughput, and application retry behavior.

Do not add a hashed prefix to every object unless the workload demonstrates a genuine reason for doing so. It may complicate listing, analytics, lifecycle management, and operational investigations.

References:

- [Optimizing performance for Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/optimizing-performance.html)
- [Performance design patterns for Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/optimizing-performance-design-patterns.html)

## Object Keys, Versioning, and Immutable Data

An object key can point to different content over time if the application overwrites the object at that key.

For example:

```text
reports/monthly.csv
```

may initially contain October data and later be overwritten with revised data.

If versioning is enabled, S3 can retain prior versions, subject to the bucket's configuration and retention rules.

However, versioning does not make the key itself immutable. It preserves historical versions; it does not prevent every overwrite or guarantee that every historical version will remain indefinitely.

### Immutable Key Strategies

For generated artifacts, reports, audit evidence, or processed files, applications can use a unique key per output:

```text
reports/2026/10/report-7f42a91c.csv
reports/2026/10/report-c819aa23.csv
```

This reduces accidental overwrites and makes each output independently addressable.

An alternative is to maintain a stable logical identifier in the database and associate it with a unique physical object key.

For example:

```text
Database:
    report_id = monthly-finance-2026-10

Object key:
    generated-reports/7f42a91c/report.csv
```

The database can track which generated object is currently authoritative without forcing every consumer to rely on a mutable S3 key.

For workflows that require strict create-only behavior, consider supported conditional-write operations such as `If-None-Match: *`.

## Object Keys and Multi-Tenant Authorization

Object-key design and authorization should be considered together, but they are not the same concern.

A shared bucket can store data for multiple tenants:

```text
tenant-documents/
    tenant-1042/documents/...
    tenant-2098/documents/...
```

Prefix-based AWS permissions can restrict certain roles to specific portions of a bucket. However, an application-level authorization check may still be necessary when the backend's role has broader access than any individual user should possess.

A secure application should:

1. Authenticate the caller.
2. Resolve the requested document using a trusted identifier.
3. Verify tenant ownership or another applicable authorization rule.
4. Obtain the correct object key from trusted application state.
5. Perform the authorized S3 operation or issue a suitably restricted presigned URL.

Never authorize a request solely because the provided key begins with a tenant prefix supplied by the client.

Detailed policy design belongs in the Security section of the playbook.

## Object Key Design for Event-Driven Processing

S3 event-driven applications often organize keys to make downstream processing easier to manage.

For example:

```text
uploads/
    pending/
        <upload-id>.pdf

processed/
    documents/
        <upload-id>.json

failed/
    documents/
        <upload-id>.json
```

This example represents a logical layout rather than an automatic S3 workflow state machine.

An S3 event notification can trigger a Lambda function or deliver an event to another supported destination when an eligible object operation occurs.

The key structure can help identify the type of work to perform, but the consumer must still handle duplicate notifications, retries, and partial failures.

### Avoid Recursive Event Processing

If an S3 event triggers a Lambda function that writes a new object to the same bucket, and the same event configuration matches that output, the function may trigger itself repeatedly.

Use separate input and output prefixes or separate buckets, and configure event notification filters carefully.

For example:

```text
incoming/images/<image-id>.jpg
processed/thumbnails/<image-id>.jpg
```

Configure the relevant event notification to match only `incoming/images/` rather than the complete bucket.

The function should also be idempotent so that repeated delivery of the same logical operation does not corrupt the result or create uncontrolled duplicate work.

Reference: [Configuring S3 event notifications using object key name filtering](https://docs.aws.amazon.com/AmazonS3/latest/userguide/notification-how-to-filtering.html).

## Common Object Key Design Mistakes

| Mistake | Consequence | Recommended approach |
|---|---|---|
| Using client filenames as unique keys | Different uploads can overwrite one another | Use application-generated object identifiers |
| Treating prefixes as real directories | Code incorrectly assumes filesystem semantics | Work with full object keys and documented listing operations |
| Using raw keys in URLs | Special characters may be interpreted incorrectly | Use SDKs or correctly encode request paths |
| Ignoring event-key encoding | Event consumers retrieve the wrong key | Decode the event key according to S3 notification conventions |
| Using `.` or `..` path segments | Path normalization can target an unintended key | Avoid standalone relative-path segments |
| Assuming random prefixes are always necessary | Adds complexity without proven benefit | Design around listing patterns and measured workload requirements |
| Using the key as an authorization mechanism | Cross-tenant data exposure | Validate authorization independently |
| Embedding sensitive information in keys | Values may leak into logs, events, and URLs | Use opaque application identifiers |
| Ignoring UTF-8 byte length | Valid-looking Unicode names may exceed the limit | Check `len(key.encode("utf-8"))` |
| Assuming lexical order equals event order | Processing may be incorrectly sequenced | Maintain explicit timestamps, sequence values, or state where required |
| Changing an existing key as if renaming were atomic | Copy and delete can partially succeed | Implement a controlled migration with retry and reconciliation |
| Omitting retry and overwrite rules | Duplicate jobs may replace valid data | Design idempotency and conditional-write behavior explicitly |

## Further Reading

- [Naming Amazon S3 objects](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-keys.html)
- [Organizing objects using prefixes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-prefixes.html)
- [Amazon S3 performance optimization](https://docs.aws.amazon.com/AmazonS3/latest/userguide/optimizing-performance.html)
- [S3 event notification message structure](https://docs.aws.amazon.com/AmazonS3/latest/userguide/notification-content-structure.html)
- [Conditional writes in Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html)
- [Configuring S3 event notification filters](https://docs.aws.amazon.com/AmazonS3/latest/userguide/notification-how-to-filtering.html)

## Key Takeaways

- An S3 object key is a case-sensitive, UTF-8-encoded identifier limited to 1,024 bytes; prefixes and delimiters are part of that key.
- Design keys around trusted identifiers, predictable listing patterns, and application needs rather than relying exclusively on original filenames.
- Use AWS SDKs for request construction, decode event-notification keys correctly, and avoid path-like segments that can be normalized unexpectedly by other tools.
- Prefix design can improve organization and targeted listing, but randomized prefixes are not a universal performance requirement for modern S3 workloads.
- Object-key design must work together with authorization, idempotency, versioning, event processing, and data migration strategies to support reliable production systems.