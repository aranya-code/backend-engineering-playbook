# 02- Object Key Prefix Design

## Overview

Amazon S3 stores objects in a flat namespace. Each object is identified by its key within a bucket; apparent folders are logical groupings created by key prefixes and delimiters such as `/`.

Object key and prefix design affects more than readability. It influences how applications locate objects, how efficiently they list and process data, how IAM policies scope access, how lifecycle rules target datasets, and how high-throughput workloads distribute requests.

A production-ready design should support predictable object lookup, scalable upload and download traffic, efficient data processing, maintainable retention policies, and safe multi-tenant isolation.

The goal is not to create as many prefixes as possible. It is to select a key structure that matches application access patterns and operational requirements, introducing additional prefix distribution when sustained request rates justify it.

## Understand Object Keys and Prefixes

### Object keys

An object key is the complete identifier of an object within a bucket.

Consider this key:

```text
documents/tenant-42/2026/10/invoice-8912.pdf
```

Its logical components are:

| Component | Example | Purpose |
|---|---|---|
| Dataset prefix | `documents/` | Identifies a broad object category |
| Tenant prefix | `tenant-42/` | Groups objects by tenant |
| Time prefix | `2026/10/` | Supports time-based organization |
| Object identifier | `invoice-8912.pdf` | Identifies the individual object |

The entire string is one object key. S3 does not create a physical directory structure corresponding to these components.

Object keys can contain UTF-8 characters and have a maximum length of 1,024 bytes. The limit includes all prefixes, separators, and the filename. Object keys are case-sensitive.

Reference: [Naming Amazon S3 objects](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-keys.html).

### Prefixes

A prefix is a string at the beginning of an object key.

For example, the following keys share the prefix `documents/tenant-42/`:

```text
documents/tenant-42/2026/10/invoice-8912.pdf
documents/tenant-42/2026/10/invoice-8913.pdf
documents/tenant-42/2026/09/invoice-8821.pdf
```

The prefix can be used to narrow an object listing:

```bash
aws s3api list-objects-v2 \
  --bucket "$BUCKET" \
  --prefix "documents/tenant-42/" \
  --max-keys 100
```

This lists objects whose keys begin with the specified prefix. It does not perform an arbitrary substring search.

### Prefixes and delimiters

A delimiter groups keys into logical levels during listing. The common delimiter is `/`.

```bash
aws s3api list-objects-v2 \
  --bucket "$BUCKET" \
  --prefix "documents/" \
  --delimiter "/" \
  --max-keys 100
```

With a delimiter, S3 returns immediate logical groupings through `CommonPrefixes`, alongside any directly matching objects.

Use delimiters when an application needs to browse a hierarchy. Use a prefix-only listing when a worker must process every matching object, including objects nested under additional logical levels.

A listing response can be truncated. Always implement pagination when processing the complete population.

## Design a Consistent Key Hierarchy

### Start with access patterns

Design keys around the operations your systems perform most frequently.

Typical access patterns include:
- Retrieve one object using a known identifier.
- List all objects belonging to a tenant.
- Process objects created during a particular period.
- Apply retention policies to a dataset.
- Scan data efficiently using Athena or another analytics engine.
- Distribute high request rates across multiple prefixes.

A key structure that is convenient for one operation can be inefficient for another. For example, a layout optimized for date-based analytics may not provide a direct listing path for every individual customer.

Prefer a primary access hierarchy that satisfies the most important operational requirements. Store additional searchable attributes in application metadata or a database when necessary.

### Use stable, meaningful prefixes

A document-management application might use:

```text
documents/
    tenant-42/
        2026/
            10/
                01J9M8F2K7....pdf
                01J9M8G4P1....pdf
```

The same keys could be generated without physical folders:

```python
object_key = (
    f"documents/{tenant_id}/{year}/{month}/{document_id}.pdf"
)
```

A key structure should be:
- Consistent across application instances.
- Predictable for authorized lookup operations.
- Compatible with lifecycle, access-control, and reporting requirements.
- Independent of the original filename when filenames are untrusted.
- Stable enough for downstream systems and retained records.

Avoid frequently changing established conventions. Renaming an S3 object requires a copy followed by deletion of the original object, rather than an in-place rename.

### Avoid uncontrolled naming variations

These keys represent different objects:

```text
documents/tenant-42/invoice.pdf
Documents/tenant-42/invoice.pdf
documents/Tenant-42/invoice.pdf
documents/tenant-42/invoice.PDF
```

Inconsistent capitalization and separators create unnecessary complexity in access policies, application lookups, bulk operations, and analytics.

Define a canonical naming convention and enforce it in the storage service layer.

## Choose Prefix Components Deliberately

### Organize by workload and data type

For a backend platform storing different object categories, use a clear namespace:

```text
uploads/{tenant_id}/{object_id}
documents/{tenant_id}/{year}/{month}/{object_id}.pdf
media/original/{tenant_id}/{object_id}
media/processed/{tenant_id}/{object_id}/thumbnail.webp
exports/{tenant_id}/{job_id}/result.parquet
audit-events/{year}/{month}/{day}/{partition_id}.jsonl
```

Separate logical categories when their access patterns, retention periods, or processing workflows differ.

For example, original images and derived thumbnails may need separate lifecycle rules. Keeping them in distinct prefixes simplifies configuration and reduces the risk of applying the wrong retention policy.

Do not create a separate bucket for every object category automatically. Prefixes are sufficient for many organizational requirements; separate buckets may be appropriate when isolation, ownership, encryption configuration, policy boundaries, or operational responsibilities differ materially.

### Decide where tenant identifiers belong

Multi-tenant applications often need to list objects by tenant and restrict access to tenant-specific data.

A tenant-first layout supports these operations:

```text
documents/tenant-42/{object_id}.pdf
documents/tenant-84/{object_id}.pdf
```

It can also support prefix-scoped permissions where applicable. However, a prefix is not an authorization mechanism on its own. The application must enforce ownership checks, and AWS IAM and bucket policies must establish the intended access boundary.

Choose stable, canonical tenant identifiers rather than user-provided display names. Never trust a client to select an arbitrary tenant prefix without verifying that the caller is authorized for that tenant.

### Avoid embedding sensitive information

Object keys can appear in application logs, access logs, error messages, monitoring systems, and presigned URLs.

Do not put the following directly into object keys unless there is a documented requirement and an appropriate data-handling assessment:
- Passwords, access tokens, or credentials.
- Personal information that does not need to be exposed in identifiers.
- Financial or medical details.
- Long-lived authorization secrets.

Prefer opaque identifiers for sensitive objects, with descriptive metadata stored in an appropriately protected database.

## Design Prefixes for High Request Rates

### Understand S3 request scaling

Amazon S3 automatically scales to accommodate increasing request rates. AWS documents baseline performance guidelines of at least 3,500 PUT/COPY/POST/DELETE requests per second and 5,500 GET/HEAD requests per second per partitioned prefix.

These figures are planning guidelines, not guaranteed application throughput or hard per-prefix limits. Actual performance depends on workload characteristics, object sizes, request distribution, client connections, and other configuration factors.

S3 scales gradually as request rates increase. During scaling, applications can temporarily receive HTTP 503 `Slow Down` responses.

Reference: [Amazon S3 performance design patterns](https://docs.aws.amazon.com/AmazonS3/latest/userguide/optimizing-performance-design-patterns.html).

### Distribute traffic when necessary

Suppose an application stores every upload beneath one concentrated prefix:

```text
uploads/2026/10/{object_id}
```

This layout may be perfectly adequate for an ordinary workload. If a sustained, very high request rate concentrates on a narrow prefix, however, distributing requests across multiple prefixes can help S3 scale the workload.

An alternative layout could be:

```text
uploads/00/{object_id}
uploads/01/{object_id}
uploads/02/{object_id}
...
uploads/0f/{object_id}
```

The application assigns objects to a shard using a deterministic function.

```python
import hashlib


def get_shard(object_id: str, shard_count: int = 16) -> str:
    if not object_id:
        raise ValueError("object_id must not be empty")

    if shard_count <= 0:
        raise ValueError("shard_count must be positive")

    digest = hashlib.sha256(object_id.encode("utf-8")).digest()
    shard = int.from_bytes(digest[:4], byteorder="big") % shard_count

    return f"{shard:02x}"
```

Example:

```python
object_id = "01J9M8F2K7XQ"
shard = get_shard(object_id)

object_key = f"uploads/{shard}/{object_id}"
```

This creates 16 possible shard prefixes. The application must retain the ability to calculate the correct prefix whenever it needs to locate an object.

Use a sufficiently stable shard function. Changing the shard count changes the mapping for many identifiers and can make existing objects difficult to locate unless the migration and lookup strategy accounts for it.

### Do not randomize every key by default

Random prefixes are not a universal performance requirement for modern S3 workloads.

Start with a logical, predictable key structure and measure actual request rates and errors. Introduce a shard or distribution component when workload evidence shows that request distribution would improve performance.

Additional prefixes introduce trade-offs:
- More complex object-key generation and lookup.
- Potentially more complex listing and migration operations.
- More complicated prefix-specific policies and monitoring.
- Increased risk of inconsistent implementations across services.

The objective is to distribute genuinely high-volume traffic, not to make every object's path harder to understand.

### Handle temporary scaling responses

Use current AWS SDKs and configure retry behavior appropriate to the application's latency requirements.

For HTTP 503 responses:
- Use bounded retries with exponential backoff and jitter.
- Enforce an overall operation deadline.
- Monitor retry counts and request latency.
- Avoid synchronized retry storms across worker fleets.
- Ramp new traffic gradually when introducing a substantially higher request rate.

Retries should distinguish transient service conditions from permanent authorization, validation, and missing-object failures.

Reference: [Optimizing S3 performance](https://docs.aws.amazon.com/AmazonS3/latest/userguide/optimizing-performance.html).

## Design Keys for Data Lakes and Analytics

### Align prefixes with common query filters

Data lake layouts often include partition columns in object paths.

For example:

```text
events/
    year=2026/
        month=10/
            day=16/
                part-00001.parquet
                part-00002.parquet
```

This can align with query predicates such as:

```sql
SELECT tenant_id, event_type, event_timestamp
FROM analytics.events
WHERE year = 2026
  AND month = 10
  AND day = 16;
```

When the table is configured with the corresponding partition scheme, query engines such as Amazon Athena can use partition pruning to avoid scanning unrelated data.

Key naming alone does not guarantee efficient queries. The table definition, partition metadata, file format, compression, file sizes, and query predicates all influence the amount of data scanned.

### Avoid excessive small files

A layout that creates one tiny file for every event can generate large numbers of objects and increase listing, metadata-management, and query-planning overhead.

For high-volume analytics workloads:
- Buffer and batch events before writing.
- Prefer columnar formats such as Parquet when suitable.
- Use reasonable file sizes based on query patterns and engine requirements.
- Partition only by attributes that materially reduce query scans.
- Compact small files when justified.
- Avoid extremely high-cardinality partitions unless the workload needs them.

Do not partition on every available column. Excessive partition cardinality can produce many tiny directories in the logical layout and make metadata management less efficient.

## Build Keys Safely in Backend Applications

### Generate identifiers on the server

A client filename should not determine an unrestricted S3 key.

A safer Python example creates an opaque document identifier, verifies the tenant identifier, and constructs the key from trusted values.

```python
from uuid import uuid4


def build_document_key(
    tenant_id: str,
    original_filename: str,
    extension: str,
) -> str:
    if not tenant_id or "/" in tenant_id or "\\" in tenant_id:
        raise ValueError("Invalid tenant identifier")

    allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg"}

    normalized_extension = extension.lower()
    if normalized_extension not in allowed_extensions:
        raise ValueError("Unsupported file extension")

    document_id = uuid4().hex

    return (
        f"documents/{tenant_id}/"
        f"{document_id}{normalized_extension}"
    )
```

In production, `tenant_id` must come from authenticated and authorized application context. The extension must be derived from validated content and application policy, not blindly accepted from the client.

The function generates a storage key; it does not replace authentication, content validation, malware scanning, or S3 authorization.

### Keep object identity separate from presentation

Store the following information in an application database when required:

| Database field | Purpose |
|---|---|
| `document_id` | Stable application-level identifier |
| `tenant_id` | Ownership and authorization |
| `bucket_name` | Bucket containing the object |
| `object_key` | Exact S3 object key |
| `original_filename` | Display name shown to the user |
| `content_type` | Validated media type |
| `size_bytes` | Object size |
| `created_at` | Creation timestamp |
| `status` | Upload, scan, or processing state |

This separation allows filenames and user-facing metadata to change without changing object identity.

Do not expose bucket names and raw keys unnecessarily in public APIs. Return application-level identifiers and issue authorized download access through the appropriate service layer.

## Use Prefixes to Simplify Lifecycle and Access Management

A stable prefix hierarchy can make infrastructure policies easier to maintain.

For example:

```text
temporary-uploads/{tenant_id}/{object_id}
documents/{tenant_id}/{document_id}.pdf
audit-events/{year}/{month}/{day}/{event_id}.jsonl
```

These categories can have different lifecycle, access, and reporting requirements.

| Prefix | Potential operational purpose |
|---|---|
| `temporary-uploads/` | Cleanup of abandoned or short-lived objects |
| `documents/` | Long-term business document storage |
| `audit-events/` | Retention and reporting for audit records |
| `media/original/` | Preservation of source media |
| `media/processed/` | Independent retention for derived assets |

### Lifecycle policies

Lifecycle rules can filter objects by prefix and other supported criteria. A good naming convention allows those rules to target the intended population without accidentally affecting unrelated data.

Before changing lifecycle configuration, verify that the filter matches the intended keys, that object versions are handled appropriately, and that business or legal retention requirements permit expiration.

### IAM policies

IAM policies can also restrict operations to selected resource prefixes. Keep the key hierarchy consistent with the intended access boundary.

Do not treat path components as a substitute for authorization checks. In particular, never allow an untrusted caller to select another tenant's identifier and thereby obtain access to that tenant's objects.

Detailed access-control design belongs in the S3 security documentation.

## List Objects Efficiently

### Use narrow prefixes

Prefer:

```bash
aws s3api list-objects-v2 \
  --bucket "$BUCKET" \
  --prefix "documents/tenant-42/2026/10/" \
  --max-keys 100
```

over listing the entire bucket when the application only needs documents for one tenant and month.

Narrow prefixes reduce the result set that the application must process. They do not make S3 execute an arbitrary database-style query over object metadata.

### Implement pagination

For automation, process every page rather than assuming that one response includes every matching key.

A Boto3 example:

```python
import boto3


def iter_object_keys(bucket: str, prefix: str):
    s3 = boto3.client("s3")

    paginator = s3.get_paginator("list_objects_v2")

    for page in paginator.paginate(
        Bucket=bucket,
        Prefix=prefix,
        PaginationConfig={"PageSize": 1000},
    ):
        for item in page.get("Contents", []):
            yield item["Key"]
```

For very large object populations, repeated interactive listing may be inefficient. Evaluate S3 Inventory, S3 Batch Operations, or a dedicated data catalog for bulk reporting and processing.

Do not run unbounded listing and processing loops inside synchronous API requests. Use background workers and bounded batches for large jobs.

## Plan Key-Convention Changes Carefully

Changing an established object-key convention is a data migration, not a simple rename.

For example, moving from:

```text
documents/{document_id}.pdf
```

to:

```text
documents/{tenant_id}/{year}/{month}/{document_id}.pdf
```

requires a migration plan.

A safe process should:
1. Define the new canonical key schema.
2. Inventory existing objects and their application references.
3. Establish an authoritative mapping from application IDs to source and destination keys.
4. Copy objects in bounded, retryable batches.
5. Verify destination objects, metadata, encryption, and required tags.
6. Update database references only after successful verification.
7. Preserve rollback and recovery options during the transition.
8. Retire old objects only after dependent systems no longer need them.

S3 does not offer an in-place object rename. A copy followed by deletion is not atomic across the two keys. Concurrent writers and partial migration failures must be accounted for explicitly.

For versioned buckets, consider object versions and delete markers during migration and cleanup. Never assume a successful copy means that every version or required metadata attribute has been migrated.

## Common Object Key and Prefix Design Mistakes

| Mistake | Consequence | Better practice |
|---|---|---|
| Treating prefixes as real directories | Incorrect assumptions about filesystem operations | Design around object keys and prefix-based listing |
| Randomizing keys without a measurable need | More complex lookup and operational logic | Start with logical keys; add distribution when justified |
| Concentrating very high request volume on a narrow prefix without monitoring | Temporary scaling errors may affect latency | Measure traffic, distribute requests when necessary, and implement retries |
| Putting every object under one generic prefix | Difficult lifecycle management and inefficient targeted listing | Separate categories and workloads with stable prefixes |
| Using client-controlled filenames as object keys | Collisions, unsafe paths, and inconsistent naming | Generate opaque server-side identifiers |
| Putting sensitive data in keys | Data exposure through logs and URLs | Use non-sensitive identifiers and protected metadata |
| Changing shard-count logic without a migration plan | Existing objects become difficult to locate | Version the key schema or maintain a mapping |
| Using a date partition for every API lookup | Object retrieval may require unnecessary listing | Store direct object references in a database |
| Creating too many analytics partitions | Small files and expensive metadata operations | Partition only on useful query dimensions |
| Assuming key changes are atomic renames | Partial migrations can leave duplicate or missing references | Use verified copy-and-cutover workflows |
| Ignoring pagination | Bulk jobs silently omit objects | Use paginators and track batch completion |
| Allowing arbitrary prefixes to determine tenant access | Cross-tenant data exposure | Enforce authorization independently of the key layout |

## Production Readiness Checklist

- [ ] The key schema supports the application's primary lookup and listing operations.
- [ ] Prefix names, case conventions, separators, and identifiers are standardized.
- [ ] Object keys stay within the 1,024-byte maximum.
- [ ] Client filenames and tenant identifiers are validated or generated from trusted application context.
- [ ] Keys do not contain credentials or unnecessary sensitive information.
- [ ] Access boundaries and lifecycle requirements align with the prefix hierarchy.
- [ ] High request rates are measured before introducing shard prefixes.
- [ ] Sharding logic is deterministic and backward-compatible.
- [ ] S3 503 responses are handled using bounded retries and backoff.
- [ ] Bulk listing uses pagination, and large jobs run asynchronously.
- [ ] Analytics prefixes support useful partition pruning without excessive small files.
- [ ] Key-schema changes have inventory, migration, verification, and rollback procedures.
- [ ] Versioning, encryption, metadata, and retention requirements are preserved during object migration.
- [ ] Monitoring covers request rates, latency, errors, and the performance of bulk-processing jobs.

## Authoritative References

- [Naming Amazon S3 objects](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-keys.html)
- [Organizing objects using prefixes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-prefixes.html)
- [Performance design patterns for Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/optimizing-performance-design-patterns.html)
- [Performance guidelines for Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/optimizing-performance-guidelines.html)
- [Amazon S3 Inventory](https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-inventory.html)
- [Using Amazon S3 with Amazon Athena](https://docs.aws.amazon.com/athena/latest/ug/what-is.html)

## Key Takeaways

- Design object keys around lookup patterns, tenant boundaries, lifecycle requirements, and analytics needs rather than arbitrary folder-like structures.
- S3 prefixes are logical key groupings, not physical directories; use narrow prefixes and pagination for efficient listing.
- Introduce deterministic prefix sharding only when measured high request rates justify the additional lookup and migration complexity.
- Generate safe, opaque object identifiers in trusted backend code and keep authorization independent of client-supplied paths.
- Treat key-schema changes as controlled data migrations with verification, rollback, and explicit handling of object versions and metadata.