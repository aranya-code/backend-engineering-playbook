# 05- Object Tagging

## Overview

Amazon S3 object tagging allows you to associate key-value pairs with individual objects. Tags provide a lightweight classification mechanism that can support lifecycle management, access-control policies, operational automation, and storage organization.

For example, a backend application might use tags to classify documents by environment, data classification, business purpose, or retention category.

```text
Key: environment
Value: production

Key: classification
Value: confidential

Key: purpose
Value: customer-report
```

Object tags are stored as part of an object's tagging configuration. They are distinct from object keys, user-defined metadata, bucket tags, and application database records.

Common use cases include:

- Classifying objects for lifecycle transitions and expiration.
- Restricting access based on existing object tags.
- Enforcing allowed tag values during uploads.
- Identifying objects for operational automation.
- Organizing storage assets by business purpose.
- Supporting cost analysis and data-governance workflows.

Tags are useful when an object needs a small number of mutable attributes that AWS services and policies can evaluate directly. They are not a replacement for a relational database or a general-purpose metadata store.

## Object Tagging Fundamentals

### Tag structure

An S3 object tag consists of a key and a value.

| Property | Constraint or behavior |
|---|---|
| Maximum tags | 10 tags per object version |
| Tag key length | Up to 128 Unicode characters |
| Tag value length | Up to 256 Unicode characters |
| Key uniqueness | Each tag key must be unique within the object's tag set |
| Case sensitivity | Keys and values are case-sensitive |
| Mutation | Tags can be added, replaced, or removed |
| Object association | Tags belong to an object version |
| Hierarchy | Tags do not create a directory structure |
| Supported bucket types | The tagging APIs discussed here apply to general-purpose buckets, not directory buckets |

Tag length restrictions use Unicode rules, with S3 internally representing tags in UTF-16. Characters that occupy two UTF-16 positions need additional consideration when validating boundary lengths.

The 10-tag limit makes object tagging suitable for a compact set of classifications rather than storing arbitrary application metadata.

### Example tag set

Consider a document stored at:

```text
s3://example-private-bucket/documents/tenant-123/report.pdf
```

Its tags might be:

| Key | Value | Purpose |
|---|---|---|
| `environment` | `production` | Environment classification |
| `classification` | `confidential` | Data classification |
| `department` | `finance` | Business ownership |
| `retention` | `standard` | Lifecycle or governance category |
| `application` | `report-service` | Producing application |

An application can change these tags without changing the object's key. However, changing a tag can affect lifecycle eligibility and access-control decisions, so tag mutation must be controlled.

## Object Tags vs. Metadata and Bucket Tags

These mechanisms solve different problems.

| Feature | Object tags | User-defined object metadata | Bucket tags |
|---|---|---|---|
| Scope | Individual object version | Individual object | Bucket |
| Structure | Up to 10 key-value pairs | Key-value metadata fields, subject to metadata limits | Key-value pairs |
| Mutable independently of object content | Yes | Generally requires a copy or object rewrite to change | Yes |
| Lifecycle filtering | Supported | Not directly supported as a lifecycle filter | Does not directly classify individual objects |
| Tag-based object authorization | Supported through applicable policy conditions | Not equivalent to object-tag condition keys | May be used in policies for supported bucket-level conditions |
| Typical purpose | Classification and AWS policy integration | Object-associated technical attributes | Bucket-level classification and administration |

For example, `Content-Type: application/pdf` is system-defined object metadata. A tag such as `classification=confidential` is an object tag.

Use metadata for attributes such as content type and cache behavior. Use tags for small classifications that need to participate in AWS lifecycle rules or tag-aware policies. Keep frequently queried business records, ownership relationships, and detailed workflow state in the application database.

## Setting Tags During Upload

Tags can be assigned while creating an object. Doing so avoids an additional tagging request after the upload completes.

### Upload with the AWS CLI

```bash
aws s3api put-object \
  --bucket example-private-bucket \
  --key documents/report.pdf \
  --body ./report.pdf \
  --content-type application/pdf \
  --tagging "environment=production&classification=confidential" \
  --region ap-south-1
```

This example uploads the object and associates the specified tags in the same operation.

The tag query string must be URL-encoded correctly when keys or values contain characters requiring encoding. For general automation, use a JSON-based SDK structure when available rather than manually assembling a query string.

### Upload with Boto3

```python
from urllib.parse import urlencode

from app.storage import s3_client


def upload_tagged_object(
    *,
    file_path: str,
    bucket_name: str,
    object_key: str,
    environment: str,
    classification: str,
) -> dict:
    tags = [
        {"Key": "environment", "Value": environment},
        {"Key": "classification", "Value": classification},
    ]

    tagging = urlencode([
        (tag["Key"], tag["Value"])
        for tag in tags
    ])

    with open(file_path, "rb") as fileobj:
        return s3_client.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=fileobj,
            ContentType="application/pdf",
            Tagging=tagging,
        )
```

The example assumes the file path, bucket, key, environment, and classification have already passed application-level validation. In production, allow only approved tag keys and values rather than accepting arbitrary tag sets from clients.

For larger uploads, use an appropriate multipart transfer workflow and ensure tags are set through supported upload parameters or subsequent tagging operations.

### Operational considerations

Setting tags during upload can be preferable when the initial classification is known and must be present from creation. If an upload workflow is asynchronous, verify that the completed object retains the intended tags before marking it available for downstream processing.

If a caller is not allowed to supply a particular tag, set that value in trusted backend code or enforce it through IAM and bucket policy controls.

## Managing Tags on Existing Objects

S3 provides APIs to retrieve, replace, and remove an object's tag set.

| API operation | Purpose |
|---|---|
| `GetObjectTagging` | Retrieve tags for the current or specified object version |
| `PutObjectTagging` | Set the complete tag set for the current or specified version |
| `DeleteObjectTagging` | Remove all tags from the current or specified version |

A critical behavior is that `PutObjectTagging` replaces the existing tag set. It does not automatically append the supplied tags to the existing set.

### Retrieve tags with the AWS CLI

```bash
aws s3api get-object-tagging \
  --bucket example-private-bucket \
  --key documents/report.pdf \
  --region ap-south-1
```

Example response:

```json
{
  "VersionId": "EXAMPLE_VERSION_ID",
  "TagSet": [
    {
      "Key": "environment",
      "Value": "production"
    },
    {
      "Key": "classification",
      "Value": "confidential"
    }
  ]
}
```

For a versioned bucket, this operation returns tags for the current version unless a version ID is specified.

### Replace the tag set

Create `tags.json`:

```json
{
  "TagSet": [
    {
      "Key": "environment",
      "Value": "production"
    },
    {
      "Key": "classification",
      "Value": "internal"
    },
    {
      "Key": "department",
      "Value": "engineering"
    }
  ]
}
```

Apply the tags:

```bash
aws s3api put-object-tagging \
  --bucket example-private-bucket \
  --key documents/report.pdf \
  --tagging file://tags.json \
  --region ap-south-1
```

This replaces the previous tag set with the three tags supplied in `tags.json`. Any old tag not included in the new set is removed.

For an existing object with tags that must be preserved, retrieve the current tag set, merge the intended changes in application code, validate the resulting set, and write back the complete tag set.

### Remove all tags

```bash
aws s3api delete-object-tagging \
  --bucket example-private-bucket \
  --key documents/report.pdf \
  --region ap-south-1
```

This removes the object's tags, not the object itself.

Use this operation when an object's classifications should be cleared. Before doing so, determine whether any lifecycle rule or access-control policy depends on the tags.

References:
- [GetObjectTagging API](https://docs.aws.amazon.com/AmazonS3/latest/API/API_GetObjectTagging.html)
- [PutObjectTagging API](https://docs.aws.amazon.com/AmazonS3/latest/API/API_PutObjectTagging.html)
- [Managing object tags](https://docs.aws.amazon.com/AmazonS3/latest/userguide/tagging-managing.html)

## Managing Tags with Boto3

A storage service should own tag operations so that framework views and API routes do not duplicate AWS-specific logic.

### Read the current tag set

```python
from app.storage import s3_client


def get_object_tags(
    *,
    bucket_name: str,
    object_key: str,
    version_id: str | None = None,
) -> list[dict[str, str]]:
    params = {
        "Bucket": bucket_name,
        "Key": object_key,
    }

    if version_id:
        params["VersionId"] = version_id

    response = s3_client.get_object_tagging(**params)
    return response.get("TagSet", [])
```

The function returns the tags associated with the requested version or the current version when no version ID is supplied.

### Replace tags safely

```python
ALLOWED_TAG_KEYS = {
    "environment",
    "classification",
    "department",
    "application",
}


def validate_tags(tags: list[dict[str, str]]) -> None:
    if len(tags) > 10:
        raise ValueError("An object can have at most 10 tags")

    keys = [tag["Key"] for tag in tags]

    if len(keys) != len(set(keys)):
        raise ValueError("Tag keys must be unique")

    if not set(keys).issubset(ALLOWED_TAG_KEYS):
        raise ValueError("Unsupported tag key")

    for tag in tags:
        key = tag["Key"]
        value = tag["Value"]

        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("Tag keys and values must be strings")

        if not key or len(key) > 128 or len(value) > 256:
            raise ValueError("Tag key or value length is invalid")


def replace_object_tags(
    *,
    bucket_name: str,
    object_key: str,
    tags: list[dict[str, str]],
    version_id: str | None = None,
) -> dict:
    validate_tags(tags)

    params = {
        "Bucket": bucket_name,
        "Key": object_key,
        "Tagging": {
            "TagSet": tags,
        },
    }

    if version_id:
        params["VersionId"] = version_id

    return s3_client.put_object_tagging(**params)
```

This example enforces a small application-specific vocabulary. A production validator should also account for Unicode length semantics, allowed values for each key, tenant boundaries, and any additional tag restrictions imposed by S3.

Do not allow clients to overwrite system-controlled classifications such as `classification` or `retention` without appropriate authorization.

### Add or update one tag without losing others

Because `PutObjectTagging` replaces the whole tag set, updating a single key requires a read-merge-write operation.

```python
def upsert_object_tag(
    *,
    bucket_name: str,
    object_key: str,
    tag_key: str,
    tag_value: str,
) -> None:
    current_tags = get_object_tags(
        bucket_name=bucket_name,
        object_key=object_key,
    )

    updated = {
        tag["Key"]: tag["Value"]
        for tag in current_tags
    }

    updated[tag_key] = tag_value

    tags = [
        {"Key": key, "Value": value}
        for key, value in updated.items()
    ]

    replace_object_tags(
        bucket_name=bucket_name,
        object_key=object_key,
        tags=tags,
    )
```

This is a read-modify-write workflow and can lose concurrent updates. Two callers might read the same tags and then overwrite each other's changes.

If concurrent tag updates matter, serialize changes through a controlled workflow or implement an application-level concurrency mechanism. Do not assume that the read-merge-write sequence is an atomic tag update.

## Versioning and Object Tags

Object tags are associated with object versions. In a versioning-enabled bucket, changing the tags on the current version does not automatically change the tags on every historical version.

Retrieve the tags for a specific version:

```bash
aws s3api get-object-tagging \
  --bucket example-private-bucket \
  --key documents/report.pdf \
  --version-id "VERSION_ID" \
  --region ap-south-1
```

Replace tags on a specific version:

```bash
aws s3api put-object-tagging \
  --bucket example-private-bucket \
  --key documents/report.pdf \
  --version-id "VERSION_ID" \
  --tagging file://tags.json \
  --region ap-south-1
```

The relevant version-tagging operations commonly require `s3:GetObjectVersionTagging` and `s3:PutObjectVersionTagging`, respectively.

If lifecycle or access-control decisions depend on tags, verify whether the intended object version has the expected tags. Do not assume that a tag update on the current version retroactively changes all previous versions.

## Using Tags in Lifecycle Rules

Object tags can be used as filters in S3 Lifecycle rules to select objects for transitions and expiration.

For example, an organization might use a tag such as:

```text
retention = temporary
```

to identify objects eligible for expiration under an approved policy.

### Example lifecycle rule

The following JSON shows a lifecycle rule that expires objects carrying `retention=temporary` after 30 days.

```json
{
  "Rules": [
    {
      "ID": "ExpireTemporaryTaggedObjects",
      "Status": "Enabled",
      "Filter": {
        "Tag": {
          "Key": "retention",
          "Value": "temporary"
        }
      },
      "Expiration": {
        "Days": 30
      }
    }
  ]
}
```

Save the full lifecycle configuration as `lifecycle.json` and apply it:

```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket example-private-bucket \
  --lifecycle-configuration file://lifecycle.json \
  --region ap-south-1
```

**Important:** `put-bucket-lifecycle-configuration` replaces the bucket's lifecycle configuration. Retrieve and merge existing rules before applying a new configuration so that unrelated retention policies are not accidentally removed.

### Combining tags and prefixes

Lifecycle filters can combine a prefix with one or more tags. When multiple filter conditions are combined within an `And` filter, all specified conditions must match.

For example, a rule could target objects under `exports/` that also have `retention=temporary`. This is useful when several applications share a bucket but need different retention behavior.

### Lifecycle timing and versioning

Lifecycle actions are asynchronous. A tag matching an expiration rule does not imply that the object will be removed immediately.

In versioning-enabled buckets, expiration of a current object normally creates a delete marker; historical versions require their own lifecycle handling. If expiration or transition must be prevented, do not assume a tag change will cancel an action that has already been queued for processing.

Use tag-driven deletion only when the tagging process is governed and tested. An incorrect tag can result in unexpected data retention or deletion.

References:
- [Adding filters to lifecycle rules](https://docs.aws.amazon.com/AmazonS3/latest/userguide/intro-lifecycle-filters.html)
- [Lifecycle configuration elements](https://docs.aws.amazon.com/AmazonS3/latest/userguide/intro-lifecycle-rules.html)

## Using Tags in IAM and Bucket Policies

Object tagging can support fine-grained authorization. S3 provides condition keys that can evaluate existing object tags or the tags included in a write request.

Two important condition-key families are:

| Condition key | Purpose |
|---|---|
| `s3:ExistingObjectTag/<tag-key>` | Evaluates a tag already associated with an object for supported operations |
| `s3:RequestObjectTag/<tag-key>` | Evaluates a tag supplied in an applicable write request |
| `s3:RequestObjectTagKeys` | Restricts the tag keys supplied by a request |

These condition keys apply only to supported actions. Check the AWS service authorization documentation before relying on a tag condition for a particular S3 API operation.

### Restrict reads using existing tags

An identity policy can allow reads of objects classified as internal:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadInternalObjects",
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::example-private-bucket/documents/*",
      "Condition": {
        "StringEquals": {
          "s3:ExistingObjectTag/classification": "internal"
        }
      }
    }
  ]
}
```

This example shows an allow statement for supported tag-conditioned reads. It does not grant access to other objects, and the effective permissions still depend on all applicable IAM, bucket, organization, and other authorization controls.

### Restrict tags supplied during writes

For applicable write requests, a policy can require an approved environment tag:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowProductionTaggedWrites",
      "Effect": "Allow",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::example-private-bucket/documents/*",
      "Condition": {
        "StringEquals": {
          "s3:RequestObjectTag/environment": "production"
        }
      }
    }
  ]
}
```

This illustrative statement allows writes only when the request supplies the specified environment tag, for operations where that request condition is supported. Ensure that the upload workflow actually includes the tag.

A production policy may also restrict allowed tag keys and other request properties. Avoid assuming that a policy condition on one tag automatically restricts every other tag that can be supplied.

### Security considerations

- Treat classification and retention tags as security-relevant inputs.
- Restrict who can create, replace, and remove tags.
- Prevent untrusted clients from self-assigning privileged classifications.
- Ensure tag-conditioned access policies behave as expected when tags are missing.
- Test access with both matching and non-matching tags.
- Account for historical versions when version-specific tagging matters.

A tag-based allow statement is not a substitute for bucket privacy, least-privilege IAM, or explicit-deny safeguards. Review the complete authorization model before deploying tag-conditioned policies.

Reference: [Tagging and access-control policies](https://docs.aws.amazon.com/AmazonS3/latest/userguide/tagging-and-policies.html).

## Permissions Required for Tagging

Object tagging uses permissions distinct from ordinary object reads and writes.

| Operation | Common permission |
|---|---|
| Retrieve current object tags | `s3:GetObjectTagging` |
| Replace current object tags | `s3:PutObjectTagging` |
| Remove current object tags | `s3:DeleteObjectTagging` |
| Retrieve tags for a specific version | `s3:GetObjectVersionTagging` |
| Replace tags on a specific version | `s3:PutObjectVersionTagging` |
| Remove tags from a specific version | `s3:DeleteObjectVersionTagging` |
| Upload an object with tags | Appropriate object-write permission plus applicable request-tag policy conditions |

The exact permissions depend on the API operation, versioning configuration, and policy conditions. For example, a caller that can upload objects may still be unable to change the tags on an existing object.

For cross-account workflows, evaluate identity-based permissions and resource-based policies together. A successful object read also does not guarantee that the caller can retrieve, replace, or delete its tags.

## Tagging and Large-Scale Operations

Object-by-object tagging is appropriate for interactive applications and small operational tasks. Large datasets may require a manifest-driven workflow.

### Bulk tagging approaches

| Approach | Suitable use |
|---|---|
| Boto3 script | Controlled batches of known object keys |
| AWS CLI commands | Manual operations and small automation jobs |
| S3 Inventory | Producing object inventories for large-scale analysis |
| S3 Batch Operations | Applying supported operations to large object populations using a manifest |
| Event-driven tagging | Assigning classifications after uploads or processing events |

Large-scale tagging operations should be designed to tolerate partial failures. Record which objects were updated and which failed so that the workflow can resume safely.

When using S3 Inventory or Batch Operations, consider the inventory's reporting interval and whether the manifest reflects the intended object versions. A manifest is not necessarily a real-time view of current bucket state.

Before running a bulk tagging job:

1. Define the intended bucket, prefixes, tags, and object versions.
2. Validate that every tag key and value conforms to the approved vocabulary.
3. Confirm that the resulting tag set will not exceed the per-object limit.
4. Test on a small, representative subset.
5. Record execution results and retry failures.
6. Verify the final tags and evaluate any affected lifecycle or access-control behavior.

Do not generate empty placeholder manifests or report successful bulk updates without checking the actual operation results.

## Operational Monitoring and Troubleshooting

### Common failures

| Symptom | Likely cause | Diagnostic approach |
|---|---|---|
| `AccessDenied` while reading tags | Missing tagging permission or a policy restriction | Check the caller identity, tagging action, bucket policy, and relevant version |
| `AccessDenied` while updating tags | Missing `s3:PutObjectTagging` or version-tagging permission | Determine whether the request targets the current or a specific object version |
| Tag set loses existing values | The write replaced the entire tag set | Retrieve the tag set before applying a merged update |
| Lifecycle rule does not match | Tag key or value differs, prefix is wrong, or the rule filter is incorrect | Compare exact tag values, prefixes, and lifecycle configuration |
| Objects are unexpectedly expired | An incorrect or overly broad tag caused the rule to match | Inspect current tags, lifecycle filters, and versioning behavior |
| Tag-conditioned access fails | Missing tags, incorrect case, unsupported action condition, or another authorization restriction | Test with matching and non-matching tags and inspect the complete policy |
| Tag update affects only one version | The operation targeted the current or specified version only | Inspect version IDs and retrieve tags for the intended version |
| Invalid tag request | Too many tags, duplicate keys, invalid lengths, or incorrect encoding | Validate the tag set and request encoding before retrying |

### Operational verification

Retrieve tags through the AWS CLI:

```bash
aws s3api get-object-tagging \
  --bucket example-private-bucket \
  --key documents/report.pdf \
  --region ap-south-1
```

Inspect the current bucket lifecycle configuration:

```bash
aws s3api get-bucket-lifecycle-configuration \
  --bucket example-private-bucket \
  --region ap-south-1
```

Record application-level tag mutations where they influence security, retention, or business processing. Useful fields include the asset ID, actor, operation, tag keys changed, timestamp, and outcome. Avoid logging sensitive tag values unnecessarily.

Monitor repeated tagging failures, unexpected classification changes, and changes that alter lifecycle eligibility. For regulated data, tag mutations may need to follow a controlled approval and audit process.

## Best Practices

- Define a small, documented tag vocabulary with stable key names and approved values.
- Use tags only for compact classifications and policy integration; keep rich metadata and business relationships in the application database.
- Apply required tags during upload when the classification is known and enforced.
- Treat `PutObjectTagging` as full tag-set replacement and preserve existing tags deliberately.
- Restrict tagging permissions and validate both supplied and existing tags where relevant.
- Test lifecycle and IAM behavior with matching, missing, and incorrect tags.
- Use version-specific tagging when historical versions require independent classifications.
- Use manifest-driven operations and reconciliation for large-scale tagging.
- Avoid using tags to store secrets or to grant privileges without controlled policy design.
- Monitor tag changes that can affect data access, retention, deletion, or cost analysis.

## Official References

- [Tagging your objects](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-tagging.html)
- [Managing object tags](https://docs.aws.amazon.com/AmazonS3/latest/userguide/tagging-managing.html)
- [PutObjectTagging API](https://docs.aws.amazon.com/AmazonS3/latest/API/API_PutObjectTagging.html)
- [GetObjectTagging API](https://docs.aws.amazon.com/AmazonS3/latest/API/API_GetObjectTagging.html)
- [Tagging and access-control policies](https://docs.aws.amazon.com/AmazonS3/latest/userguide/tagging-and-policies.html)
- [Lifecycle configuration elements](https://docs.aws.amazon.com/AmazonS3/latest/userguide/intro-lifecycle-rules.html)
- [S3 Batch Operations](https://docs.aws.amazon.com/AmazonS3/latest/userguide/batch-ops.html)
- [Object tags and annotations](https://docs.aws.amazon.com/AmazonS3/latest/userguide/annotations-overview.html)

## Key Takeaways

- S3 object tags are compact, mutable key-value classifications with a limit of 10 unique-key tags per object version.
- `PutObjectTagging` replaces the complete tag set, so read-merge-write operations must account for concurrent updates.
- Tags can drive lifecycle rules and supported tag-aware access policies, making incorrect classifications a potential security or data-retention risk.
- Use least-privilege tagging permissions, validate tag vocabulary and values, and handle version-specific tags explicitly.
- For bulk tagging, use validated manifests, record per-object outcomes, and verify final state before relying on tags for access control or retention.