# Managing Object Metadata

## Overview

Amazon S3 object metadata describes an object without requiring an application to download its contents. Metadata includes properties such as content type, content length, cache behavior, content disposition, encryption information, and application-defined attributes.

Metadata affects how backend applications deliver files, how browsers interpret responses, how content-delivery networks cache objects, and how services identify stored artifacts.

Common use cases include:

- Setting `Content-Type` for documents, images, and generated reports.
- Controlling browser and CDN caching through `Cache-Control`.
- Specifying download filenames through `Content-Disposition`.
- Recording small application-specific attributes.
- Inspecting object properties without downloading the object body.
- Updating metadata during object-copy operations.
- Verifying object identity, storage properties, and encryption configuration.

S3 metadata is associated with an object representation. Unlike object tags, most object metadata cannot be modified independently in place. Updating existing metadata generally requires copying the object to itself or to a different key with replacement metadata.

Production metadata management must account for metadata preservation, object size, versioning, concurrent writes, permissions, application consistency, and the cost of rewriting large objects.

## Types of Object Metadata

S3 object metadata can be broadly divided into system-defined metadata and user-defined metadata.

### System-defined metadata

System-defined metadata describes an object or controls aspects of how it is stored and delivered. Some properties are maintained by S3, while others can be supplied or changed through supported upload and copy operations.

| Metadata | Purpose | Management |
|---|---|---|
| `Content-Type` | Declares the media type | Set through upload or copy operations |
| `Content-Length` | Reports object size in bytes | Maintained by S3 |
| `Content-Disposition` | Controls intended presentation or download behavior | Set through supported upload or copy parameters |
| `Content-Encoding` | Describes an encoding applied to the representation | Set when appropriate |
| `Cache-Control` | Provides caching directives | Set through supported upload or copy parameters |
| `Expires` | Provides an expiration time for applicable caching behavior | Set through supported operations |
| `Last-Modified` | Indicates the object's last modification time | Maintained by S3 |
| `ETag` | Identifies an object representation according to S3's ETag semantics | Returned by S3 |
| `VersionId` | Identifies an object version when versioning is enabled | Assigned by S3 |
| Server-side encryption properties | Describe the encryption configuration used for the object | Controlled by supported S3 operations and bucket configuration |

Not every system-defined property is writable. For example, an application cannot arbitrarily assign an object size, version ID, or last-modified timestamp through ordinary metadata updates.

Copying an object to replace metadata can create a new object representation and change fields such as modification time and ETag. Do not assume that every property remains unchanged after a copy.

### User-defined metadata

User-defined metadata lets applications attach small custom attributes to objects.

Example:

```text
x-amz-meta-source-service: report-service
x-amz-meta-document-category: financial-report
x-amz-meta-schema-version: v2
```

With Boto3, specify metadata keys without the `x-amz-meta-` prefix:

```python
Metadata={
    "source-service": "report-service",
    "document-category": "financial-report",
    "schema-version": "v2",
}
```

User-defined metadata is useful for small, relatively stable attributes that should accompany the object. It is not appropriate for large payloads, confidential data, frequently changing workflow status, or complex business relationships.

User-defined metadata is subject to S3 metadata-size constraints and HTTP header limitations. Keep metadata compact and verify the applicable limits before designing a large-scale ingestion workflow.

Reference: [Working with object metadata](https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingMetadata.html).

## Object Metadata vs. Object Tags

Metadata and tags are related but serve different purposes.

| Feature | Object metadata | Object tags |
|---|---|---|
| Association | Object representation | Object version |
| Typical purpose | Describe content and response behavior | Classify objects for lifecycle and policy workflows |
| Independent update | Generally requires a copy or rewrite | Updated using tagging APIs |
| Capacity | Subject to metadata and request-header limits | Maximum of 10 tags per object version |
| Lifecycle filtering | Not directly supported as a lifecycle filter | Supported through tag filters |
| Tag-aware authorization | Not equivalent to tag condition keys | Supported for applicable policy operations |
| Examples | Content type, cache control, source service | Environment, retention category, classification |

Use metadata for technical properties and small attributes that should be associated with the stored representation. Use tags when classifications need to participate in supported lifecycle or tag-aware access-control policies.

For frequently changing application state, use a database. For example, a `processing_status` field that changes from `pending` to `completed` belongs in the application's database rather than in object metadata.

## Inspecting Object Metadata

Metadata inspection helps verify upload behavior, investigate content-delivery issues, and confirm object properties without transferring the object body.

### Inspect metadata with the AWS CLI

```bash
aws s3api head-object \
  --bucket example-private-bucket \
  --key documents/report.pdf \
  --region ap-south-1
```

An illustrative response might contain:

```json
{
  "ContentLength": 245760,
  "ContentType": "application/pdf",
  "CacheControl": "private, max-age=300",
  "ETag": "\"EXAMPLE_ETAG\"",
  "Metadata": {
    "source-service": "report-service",
    "schema-version": "v2"
  }
}
```

The actual fields depend on the object's configuration.

`HeadObject` retrieves metadata without downloading the object body. The caller still needs the appropriate permissions, and optional fields may be absent when they are not configured.

Do not treat an ETag as a universal full-object MD5 checksum. Multipart uploads and other upload conditions can produce different ETag semantics.

### Inspect a specific object version

For versioned buckets, specify a version ID when examining a historical object representation:

```bash
aws s3api head-object \
  --bucket example-private-bucket \
  --key documents/report.pdf \
  --version-id "VERSION_ID" \
  --region ap-south-1
```

Replace `VERSION_ID` with the actual version identifier.

Version-specific inspection is useful when investigating unexpected metadata changes or verifying an immutable asset. Retrieving a specific version commonly requires `s3:GetObjectVersion`.

### Inspect metadata using Boto3

```python
from app.storage import s3_client


def get_object_metadata(
    *,
    bucket_name: str,
    object_key: str,
    version_id: str | None = None,
) -> dict:
    params = {
        "Bucket": bucket_name,
        "Key": object_key,
    }

    if version_id:
        params["VersionId"] = version_id

    response = s3_client.head_object(**params)

    return {
        "content_length": response.get("ContentLength"),
        "content_type": response.get("ContentType"),
        "content_disposition": response.get("ContentDisposition"),
        "content_encoding": response.get("ContentEncoding"),
        "cache_control": response.get("CacheControl"),
        "etag": response.get("ETag"),
        "version_id": response.get("VersionId"),
        "last_modified": response.get("LastModified"),
        "metadata": response.get("Metadata", {}),
        "server_side_encryption": response.get("ServerSideEncryption"),
        "sse_kms_key_id": response.get("SSEKMSKeyId"),
    }
```

Configure the S3 client with the correct credentials and Region. Keep object lookup and application authorization in the service layer, and return only metadata the caller is permitted to see.

Avoid exposing internal KMS key identifiers or sensitive application metadata through public API responses.

## Setting Metadata During Upload

The preferred time to define object metadata is during upload, when the intended content type and response behavior are known.

### Set metadata using the AWS CLI

```bash
aws s3api put-object \
  --bucket example-private-bucket \
  --key documents/report.pdf \
  --body ./report.pdf \
  --content-type application/pdf \
  --content-disposition 'attachment; filename="report.pdf"' \
  --cache-control 'private, max-age=300' \
  --metadata source-service=report-service,schema-version=v2 \
  --region ap-south-1
```

This creates the object with the specified metadata.

The `Content-Type` value is metadata supplied with the request. It does not validate the file's actual format. Applications must inspect content independently whenever file validity or security matters.

### Set metadata using Boto3

```python
from pathlib import Path

from app.storage import s3_client


def upload_document(
    *,
    file_path: Path,
    bucket_name: str,
    object_key: str,
) -> dict:
    with file_path.open("rb") as fileobj:
        return s3_client.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=fileobj,
            ContentType="application/pdf",
            ContentDisposition='attachment; filename="report.pdf"',
            CacheControl="private, max-age=300",
            Metadata={
                "source-service": "report-service",
                "schema-version": "v2",
            },
        )
```

This example assumes the file is genuinely a PDF and the object key has already been generated and authorized by the application.

For large files, use a managed transfer interface with suitable transfer settings. Ensure the intended metadata is passed through supported parameters, including when the SDK uses multipart upload.

### Metadata in presigned uploads

A client uploading directly to S3 through a presigned URL can supply metadata when the signed operation supports the relevant parameters. Headers included in the signature must match the headers sent by the client.

The backend should define which metadata values clients may provide. A client should not be allowed to assign trusted attributes such as security classification or retention category unless that behavior is explicitly authorized.

After the upload, verify the expected metadata before marking the asset as accepted. Do not rely exclusively on the client's confirmation response.

## Updating Existing Object Metadata

S3 does not provide a general-purpose API for directly patching arbitrary object metadata in place. The standard approach is to copy the object and apply replacement metadata.

This can be accomplished by copying an object to itself or to another key. For a same-key copy, the operation rewrites the current representation rather than modifying a field in an independent transaction.

### Metadata directives

Copy operations support two primary metadata directives.

| Directive | Behavior |
|---|---|
| `COPY` | Preserves source metadata under normal copy semantics |
| `REPLACE` | Uses supplied metadata to replace the applicable source metadata |

When using `REPLACE`, provide every metadata field that must remain present. Omitting an existing `Content-Type`, `Cache-Control`, or user-defined metadata attribute can remove or change that attribute.

Some fields are controlled by S3 and cannot be set to arbitrary values through a replacement request.

### Update metadata with `copy-object`

For an object within the single-request copy size limit:

```bash
aws s3api copy-object \
  --bucket example-private-bucket \
  --key documents/report.pdf \
  --copy-source example-private-bucket/documents/report.pdf \
  --metadata-directive REPLACE \
  --content-type application/pdf \
  --content-disposition 'attachment; filename="report.pdf"' \
  --cache-control 'private, max-age=600' \
  --metadata source-service=report-service,schema-version=v3 \
  --region ap-south-1
```

This copies the object onto the same key with replacement metadata.

Before execution, inspect and preserve all metadata that must remain. This example deliberately changes the `schema-version` value and cache lifetime.

A same-key copy can create a new version when versioning is enabled or replace the current representation when versioning is disabled. It can also change other object properties. Treat the operation as an object rewrite rather than a trivial field update.

### Update metadata with Boto3

```python
from app.storage import s3_client


def replace_object_metadata(
    *,
    bucket_name: str,
    object_key: str,
    content_type: str,
    cache_control: str,
    metadata: dict[str, str],
    version_id: str | None = None,
) -> dict:
    copy_source = {
        "Bucket": bucket_name,
        "Key": object_key,
    }

    if version_id:
        copy_source["VersionId"] = version_id

    return s3_client.copy_object(
        Bucket=bucket_name,
        Key=object_key,
        CopySource=copy_source,
        MetadataDirective="REPLACE",
        ContentType=content_type,
        CacheControl=cache_control,
        Metadata=metadata,
    )
```

This example uses the single-request `CopyObject` API and is appropriate only when the source object is within that API's copy limit. It demonstrates replacement, not preservation of all source metadata.

A production implementation may also need to preserve or set additional fields, including content disposition, content encoding, expiration behavior, website redirect location, tags, storage class, and encryption configuration.

### Objects larger than 5 GB

A single `CopyObject` request supports copying objects up to 5 GB. Larger objects require multipart copy.

Boto3's managed `copy()` operation can use multipart copy when required:

```python
from boto3.s3.transfer import TransferConfig

from app.storage import s3_client


TRANSFER_CONFIG = TransferConfig(
    multipart_threshold=64 * 1024 * 1024,
    multipart_chunksize=16 * 1024 * 1024,
    max_concurrency=4,
    use_threads=True,
)


def rewrite_large_object_metadata(
    *,
    bucket_name: str,
    object_key: str,
    content_type: str,
    metadata: dict[str, str],
) -> None:
    s3_client.copy(
        CopySource={
            "Bucket": bucket_name,
            "Key": object_key,
        },
        Bucket=bucket_name,
        Key=object_key,
        ExtraArgs={
            "MetadataDirective": "REPLACE",
            "ContentType": content_type,
            "Metadata": metadata,
        },
        Config=TRANSFER_CONFIG,
    )
```

The managed transfer interface can use multipart copy as needed. Verify the behavior with the deployed Boto3 version and include all metadata that the destination must retain.

For both small and large objects, verify the resulting metadata and any required checksum before declaring the operation complete.

## Preserving Metadata During Copy

Copying an object can preserve or replace metadata depending on the chosen directive and copy parameters.

### Preserve existing metadata

```python
from app.storage import s3_client


def copy_preserving_metadata(
    *,
    source_bucket: str,
    source_key: str,
    destination_bucket: str,
    destination_key: str,
) -> dict:
    return s3_client.copy_object(
        Bucket=destination_bucket,
        Key=destination_key,
        CopySource={
            "Bucket": source_bucket,
            "Key": source_key,
        },
        MetadataDirective="COPY",
    )
```

This example uses `CopyObject`, so the source object must be within the single-request copy limit. Use a managed copy operation for larger objects.

Tags are separate from metadata. If tag preservation matters, configure and verify the appropriate tagging behavior and permissions separately.

### Replace metadata selectively

A replacement request should specify the complete desired metadata state, not just the field being changed.

For example, to change the cache policy while retaining the original content type and application metadata:

1. Read the existing metadata.
2. Validate the object's identity and version.
3. Construct the complete target metadata set.
4. Copy the source using `MetadataDirective="REPLACE"`.
5. Verify the destination metadata.
6. Persist the resulting version or workflow state.

The read-copy-verify sequence is not atomic. If the source is mutable, a concurrent write can change the key between inspection and copying. Use version-aware copying or an appropriate concurrency-control strategy when stable object identity matters.

## User-Defined Metadata in Boto3

User-defined metadata keys are supplied without the `x-amz-meta-` prefix.

```python
s3_client.put_object(
    Bucket="example-private-bucket",
    Key="documents/report.pdf",
    Body=b"example content",
    ContentType="application/pdf",
    Metadata={
        "source-service": "report-service",
        "schema-version": "v2",
        "document-category": "financial-report",
    },
)
```

When retrieving metadata, Boto3 generally exposes user-defined metadata keys in lowercase. Avoid application logic that assumes the original capitalization will be preserved.

Metadata keys and values must conform to S3 and HTTP constraints. Use consistent naming conventions and avoid storing information whose correctness depends on frequent updates.

### Avoid metadata as a database substitute

Metadata is not a general-purpose query engine. S3 does not support arbitrary server-side object listing based on user-defined metadata fields.

If an application needs to locate every document associated with a customer, status, or workflow, use a database or suitable index rather than expecting object metadata to support database-style queries.

| Information | Recommended location |
|---|---|
| Content type and cache behavior | Object metadata |
| Small, stable source-system identifier | Object metadata, when useful for storage-level inspection |
| Lifecycle classification | Object tags where appropriate |
| Tenant ownership and authorization relationships | Application database and access-control model |
| Processing status and retry count | Application database |
| Searchable business attributes | Database or search index |
| Detailed audit history | Durable audit store |
| Credentials and secrets | Secret-management system, not object metadata |

## Metadata and Versioning

Metadata belongs to an object representation. In a versioned bucket, metadata associated with a previous version does not automatically change when a newer version is created.

A metadata rewrite can create a new object version even when the object body remains logically identical.

For applications requiring immutable document references:

- Record the version ID associated with the asset.
- Inspect metadata using that version ID when necessary.
- Define whether metadata corrections should create a new version or update only the current representation.
- Apply retention and recovery rules to historical versions.
- Ensure downstream services process the intended object version.

A key-only metadata copy targets the current source representation. If the key changes between inspection and copying, the resulting metadata rewrite might apply to unexpected content.

Use a version-specific `CopySource` when a particular historical version must be copied. The calling identity must have the appropriate permission to read that version.

## Metadata, Caching, and Content Delivery

Metadata can affect how files are served by S3 and other delivery components.

### Content-Type

`Content-Type` identifies the media type associated with the response.

Examples:

```text
application/pdf
image/png
image/jpeg
application/json
application/octet-stream
```

An incorrect content type can cause browsers to interpret responses incorrectly. Derive it from validated application rules rather than trusting arbitrary client input.

### Content-Disposition

`Content-Disposition` controls how a consumer should present a response. For private document downloads, `attachment` is often appropriate:

```text
attachment; filename="report.pdf"
```

For filenames containing non-ASCII characters, use an appropriately encoded extended filename parameter where supported.

Sanitize user-controlled filenames to prevent carriage-return and line-feed injection. Do not use the original filename as the S3 object key merely because it is used as the download filename.

### Cache-Control

`Cache-Control` influences caching behavior in browsers and intermediary caches:

```text
private, max-age=300
```

This permits private caching for a limited period. For sensitive data that must not be stored by caches, an appropriate policy may include `no-store`, depending on the delivery architecture.

For public, content-addressed assets that do not change, a longer cache lifetime may improve performance. When an object is overwritten at the same URL, existing CDN or browser caches may continue serving the earlier content until expiration or invalidation.

For private S3 objects delivered through CloudFront, design cache behavior and viewer authorization together. Ensure protected content cannot be served to an unauthorized viewer through an incorrectly configured cache policy.

## Security and Permissions

Metadata can be viewed by principals that have access to the relevant object metadata. It should not contain secrets, credentials, confidential implementation details, or unnecessary personal information.

### Common permissions

| Operation | Common permission |
|---|---|
| Read object metadata through `HeadObject` | Usually `s3:GetObject` |
| Read metadata for a specific version | Usually `s3:GetObjectVersion` |
| Copy a source object | Source read permission and destination write permission |
| Write a destination object during copy | Commonly `s3:PutObject` |
| Read object tags | `s3:GetObjectTagging` or the applicable version-specific permission |
| Set tags during a copy | Appropriate tagging permissions depending on the operation |

The actual permission requirements depend on the operation, bucket configuration, and access-control model. SSE-KMS operations may require additional KMS permissions and key-policy authorization.

A request can be denied by S3 authorization or KMS authorization. Diagnose these separately.

### Security practices

- Keep buckets private unless public access is explicitly required.
- Use least-privilege IAM roles and temporary credentials.
- Restrict who can modify metadata affecting content delivery or business processing.
- Validate metadata values before accepting uploads.
- Avoid putting sensitive identifiers or confidential information into metadata.
- Ensure signed upload requests match the intended metadata contract.
- Verify metadata after critical rewrites and migrations.
- Preserve audit records when changes affect retention, access behavior, or compliance.

Metadata alone is not an authorization mechanism. A value such as `classification=public` must not make content accessible unless a deliberately designed policy or application rule permits it.

## Reliability, Concurrency, and Failure Handling

Metadata changes involve a copy or rewrite operation that can create new object versions. Treat them as state-changing workflows rather than harmless field updates.

| Failure | Recommended response |
|---|---|
| `AccessDenied` | Check source-read and destination-write permissions, resource policies, and KMS authorization |
| Metadata unexpectedly missing | Inspect `MetadataDirective` and the fields supplied in the replacement request |
| Content type changed unexpectedly | Verify copy parameters and the resulting metadata |
| Wrong source version copied | Inspect the key and version ID used in `CopySource` |
| Copy fails for a large object | Use a multipart-capable transfer path and inspect operation failures |
| Concurrent write overwrites metadata | Introduce version-aware or application-level concurrency control |
| Tags no longer match metadata | Review metadata and tagging changes as separate operations |
| Database record diverges from the object | Reconcile the stored version, metadata, and application state |

### Concurrency control

A metadata update can race with a concurrent object upload. If a new object is written after metadata inspection but before copying, the rewrite may act on unexpected content.

For important workloads, consider:

- Using version IDs to bind the copy to the intended source representation.
- Generating immutable object keys for uploaded assets.
- Applying supported conditional-write or source-precondition mechanisms where appropriate.
- Serializing metadata rewrites through a durable application workflow.
- Verifying the destination after the operation.
- Recording the resulting version ID and metadata in the database.

Not every copy workflow supports every concurrency precondition. Validate the exact API capabilities and failure semantics before relying on conditional behavior.

### Database consistency

A metadata rewrite and a database update do not participate in one shared transaction.

If the S3 rewrite succeeds but the database update fails, the object and application record can diverge. Preserve enough information to reconcile object state, and record the intended operation durably when required.

Do not mark a workflow complete until the required verification and state updates have succeeded.

## Performance and Cost Considerations

Metadata inspection through `HeadObject` avoids downloading the object body, but it still generates an S3 API request.

Changing metadata on an existing object generally requires rewriting it through a copy operation. For large objects, this can require multipart copy and generate substantial request activity.

The cost and performance implications depend on:

- Object size and the number of objects affected.
- Same-Region versus cross-Region copying.
- Source and destination storage classes.
- Encryption configuration and KMS usage.
- Versioning and retention requirements.
- Copy concurrency and retries.
- CDN caching and invalidation behavior.

For thousands or millions of objects, avoid unbounded scripts. Use controlled concurrency, durable progress tracking, per-object error reporting, and staged execution.

S3 Batch Operations may be appropriate for supported large-scale operations. For metadata changes, verify that the selected operation and object sizes are supported; a custom workflow or managed multipart-copy process may be necessary for large objects.

## Operational Verification

### Inspect metadata before making changes

```bash
aws s3api head-object \
  --bucket example-private-bucket \
  --key documents/report.pdf \
  --region ap-south-1
```

Record the existing metadata fields that must be preserved.

### Apply a metadata rewrite

Use a self-copy with replacement metadata for objects within the single-request copy limit, or a multipart-capable transfer for larger objects.

### Inspect metadata after the operation

```bash
aws s3api head-object \
  --bucket example-private-bucket \
  --key documents/report.pdf \
  --region ap-south-1
```

Compare the resulting values against the desired state. In a versioned bucket, capture the new version ID where applicable.

### Monitor changes

Useful operational signals include:

- Failed `HeadObject` and copy requests.
- Copy duration and retry counts.
- Number and size of objects rewritten.
- Unexpected metadata changes.
- New object versions created by metadata maintenance.
- Application records that reference outdated versions.
- KMS access failures during copy operations.
- Request and data-transfer costs.

For high-impact metadata changes, persist the intended and resulting metadata, object key, version ID, execution identity, and outcome.

## Testing Strategy

### Unit tests

Test the metadata service independently of real AWS resources. Cover:

- Metadata validation and approved field names.
- Missing and optional metadata values.
- Correct copy directives.
- Version-specific source selection.
- Preservation of required metadata.
- User-defined metadata normalization.
- Failure handling and retry classification.
- Handling of `ClientError` and permission failures.

### Integration tests

Use a dedicated test bucket to verify:

- Uploading objects with custom metadata.
- Reading metadata with `HeadObject`.
- Replacing metadata through copy operations.
- Preserving metadata during ordinary copies.
- Version-specific metadata inspection.
- Encryption and KMS access.
- Large-object copy behavior where relevant.
- Tag preservation and replacement as separate operations.

Mocks are useful for application logic but cannot reproduce every S3 policy, encryption, copy, versioning, and transfer behavior. Use real-AWS integration tests for service-specific semantics when necessary.

Do not report a copy or rewrite as verified unless the resulting object metadata was actually checked.

## Common Mistakes

### Treating metadata as independently mutable

Most object metadata cannot be patched in place. Use a supported copy or rewrite operation and account for its consequences.

### Replacing metadata without preserving existing fields

`MetadataDirective="REPLACE"` does not mean "update only this field." Supply the complete desired set of replacement metadata values.

### Assuming tags and metadata are the same

Metadata and tags have different APIs, limits, authorization conditions, and lifecycle uses. Update and verify them independently.

### Trusting client-supplied metadata

A client can claim that a file is a PDF or label an object as public. Validate actual content and assign security-sensitive classifications through trusted application logic.

### Forgetting versioning implications

A metadata rewrite can create a new object version. Historical versions may retain their original metadata and continue consuming storage.

### Using ETag as a universal checksum

ETag semantics depend on upload method and other conditions. Use an explicit checksum strategy for integrity verification.

### Rewriting large objects with the wrong API

`CopyObject` supports objects up to 5 GB per request. Use multipart-capable copying for larger objects.

### Updating the database before verifying S3

If a copy fails or metadata differs from the intended state, the application record can describe the object incorrectly. Verify the rewrite before committing the final application state.

## Official References

- [Working with object metadata](https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingMetadata.html)
- [Copying objects](https://docs.aws.amazon.com/AmazonS3/latest/userguide/copy-object.html)
- [CopyObject API reference](https://docs.aws.amazon.com/AmazonS3/latest/API/API_CopyObject.html)
- [HeadObject API reference](https://docs.aws.amazon.com/AmazonS3/latest/API/API_HeadObject.html)
- [Boto3 S3 client reference](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)
- [Managing object tags](https://docs.aws.amazon.com/AmazonS3/latest/userguide/tagging-managing.html)
- [Checking object integrity](https://docs.aws.amazon.com/AmazonS3/latest/userguide/checking-object-integrity.html)

## Key Takeaways

- S3 metadata describes an object representation; distinguish writable metadata fields from properties maintained by S3.
- Use `HeadObject` to inspect metadata without downloading content, and use version IDs when stable object identity is required.
- Updating existing metadata generally requires a copy or rewrite; `MetadataDirective="REPLACE"` requires explicitly preserving every desired metadata field.
- Treat metadata and tags as separate mechanisms with different APIs, policy behavior, and operational implications.
- Make metadata maintenance recoverable with least-privilege permissions, verification, version-aware concurrency control, and reconciliation of partial failures.