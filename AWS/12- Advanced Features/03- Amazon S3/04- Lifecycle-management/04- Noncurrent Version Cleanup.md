# 04- Noncurrent Version Cleanup

## Overview

Amazon S3 Versioning preserves multiple versions of an object under the same object key. This protects against accidental overwrites and enables recovery from certain application errors, but it also increases storage consumption when older versions accumulate.

A noncurrent version is an object version that has been superseded by a newer version. It remains stored until it is permanently deleted, subject to applicable lifecycle rules, retention controls, and permissions.

For example, repeatedly updating a document can retain many historical versions:

```text
documents/
    report.pdf
        Version A: Noncurrent
        Version B: Noncurrent
        Version C: Noncurrent
        Version D: Current
```

Even if the application exposes only the current version, all retained versions can contribute to storage costs.

S3 Lifecycle provides the `NoncurrentVersionExpiration` action to permanently delete eligible noncurrent versions after a configured period. It can also limit the number of newer noncurrent versions that must be retained.

A production cleanup strategy should balance storage savings, recovery requirements, compliance obligations, and operational safety.

## Understand Noncurrent Version Cleanup

### How versions become noncurrent

When versioning is enabled, uploading an object with an existing key creates a new version. The previous current version becomes noncurrent.

Deleting an object without specifying its version ID normally creates a delete marker instead of permanently deleting the existing versions.

These operations have different effects:

| Operation | Result |
|---|---|
| Upload an object using an existing key | Creates a new current version and makes the former current version noncurrent |
| Delete an object without a version ID | Creates a delete marker that becomes current |
| Delete a specific object version using its version ID | Permanently deletes that version, subject to applicable restrictions |
| Expire a noncurrent version through Lifecycle | Permanently deletes the eligible noncurrent version |
| Remove an expired delete marker | Removes a delete marker when no other object versions remain |

**Important:** Noncurrent version cleanup does not delete the current object version. Current-version expiration and expired-delete-marker cleanup are separate lifecycle actions.

Reference: [Deleting object versions from a versioning-enabled bucket](https://docs.aws.amazon.com/AmazonS3/latest/userguide/DeletingObjectVersions.html).

### Understand the storage impact

Consider a document that is replaced 50 times, with each historical version averaging 20 MB.

The historical versions alone account for approximately:

\[
49 \times 20\text{ MB} = 980\text{ MB}
\]

The current version adds another 20 MB, resulting in approximately 1 GB of logical object data across all versions.

The actual billed amount depends on the applicable storage class, object sizes, retention duration, and other pricing factors.

Noncurrent version cleanup reduces ongoing storage consumption by removing historical data that no longer needs to be retained.

## Configure NoncurrentVersionExpiration

### Define the cleanup policy

The `NoncurrentVersionExpiration` lifecycle action permanently deletes eligible noncurrent object versions.

Two settings determine eligibility:

| Setting | Purpose |
|---|---|
| `NoncurrentDays` | Specifies how many days a version must have been noncurrent |
| `NewerNoncurrentVersions` | Optionally specifies how many newer noncurrent versions must be retained |

When both settings are configured, both conditions must be satisfied before the version becomes eligible for expiration. `NewerNoncurrentVersions` supports retaining between 1 and 100 newer noncurrent versions.

For example, a rule with `NoncurrentDays: 90` and `NewerNoncurrentVersions: 5` allows S3 to permanently delete a version only after it has been noncurrent for the required period and more than five newer noncurrent versions exist.

When the newer-version limit is omitted, eligible noncurrent versions can expire based on age alone.

### Example: Retain recent history and clean older versions

The following configuration targets objects under the `documents/` prefix. It removes eligible noncurrent versions after 90 days while retaining the five newest noncurrent versions where the version-count condition applies.

```json
{
  "Rules": [
    {
      "ID": "CleanupOldDocumentVersions",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "documents/"
      },
      "NoncurrentVersionExpiration": {
        "NoncurrentDays": 90,
        "NewerNoncurrentVersions": 5
      }
    }
  ]
}
```

The prefix limits the rule's scope. It does not affect other prefixes unless another matching lifecycle rule applies.

Test the retention settings against actual overwrite frequency. Objects overwritten frequently can accumulate substantial history even when the newest few noncurrent versions are retained.

### Apply the lifecycle configuration safely

Save the approved configuration as `lifecycle.json`.

First, inspect the existing configuration:

```bash
aws s3api get-bucket-lifecycle-configuration \
  --bucket "$BUCKET"
```

After merging the proposed rule with existing rules, apply the complete configuration:

```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket "$BUCKET" \
  --lifecycle-configuration file://lifecycle.json
```

Verify the deployed configuration:

```bash
aws s3api get-bucket-lifecycle-configuration \
  --bucket "$BUCKET"
```

**Production caution:** `put-bucket-lifecycle-configuration` replaces the bucket's entire existing lifecycle configuration. Deploying a file containing only the new cleanup rule can unintentionally remove existing transition, expiration, or incomplete-multipart-upload rules.

Use infrastructure as code to manage lifecycle configuration consistently across environments.

Reference: [Configuring lifecycle rules](https://docs.aws.amazon.com/AmazonS3/latest/userguide/intro-lifecycle-rules.html).

## Clean Up Expired Delete Markers Separately

### Why delete markers accumulate

In a versioning-enabled bucket, deleting an object without specifying a version ID normally creates a delete marker. Older object versions remain in storage.

When all object versions have been permanently removed but a delete marker remains as the only version, it becomes an expired object delete marker.

A separate lifecycle expiration setting can remove these markers automatically.

```json
{
  "Rules": [
    {
      "ID": "RemoveExpiredDocumentDeleteMarkers",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "documents/"
      },
      "Expiration": {
        "ExpiredObjectDeleteMarker": true
      }
    }
  ]
}
```

This rule is intended to remove expired delete markers, not to delete ordinary current objects or their retained historical versions.

`ExpiredObjectDeleteMarker` cannot be combined with an `Expiration` rule's `Days` or `Date` setting in the same expiration configuration. Keep age-based expiration and expired-delete-marker cleanup in separate rules when both are needed.

### Combine cleanup policies carefully

A bucket can use separate lifecycle rules for:

- Permanently deleting eligible noncurrent versions.
- Removing expired delete markers.
- Expiring current versions when the business retention policy permits it.
- Aborting incomplete multipart uploads.

These actions solve different problems. Do not assume that enabling noncurrent version expiration automatically removes every delete marker or empties the bucket.

Reference: [Managing delete markers](https://docs.aws.amazon.com/AmazonS3/latest/userguide/ManagingDelMarkers.html).

## Audit Versions Before Enabling Cleanup

### Inspect versioning status

Confirm the bucket's versioning configuration before changing its lifecycle policy.

```bash
aws s3api get-bucket-versioning \
  --bucket "$BUCKET"
```

A versioning-enabled bucket retains historical versions. A bucket with versioning suspended can have different behavior, including null-version semantics.

Do not suspend versioning as a substitute for deleting old versions. Suspending versioning does not automatically remove historical data already stored in the bucket.

### Inspect object versions and delete markers

For a targeted prefix, list versions and delete markers:

```bash
aws s3api list-object-versions \
  --bucket "$BUCKET" \
  --prefix "documents/" \
  --output json
```

Review:
- Object keys and version IDs.
- Current versus noncurrent status.
- Last-modified timestamps.
- Object sizes.
- Delete markers.
- Whether the retained history is required for business recovery.

For large buckets, use S3 Inventory with the appropriate version-related fields to analyze object populations at scale. Avoid repeatedly listing an entire bucket manually for routine audits.

### Establish a retention policy before deleting history

Determine which versions must survive and why.

Examples include:
- Financial reports required for regulatory retention.
- Documents needed for audit investigations.
- Uploaded source files needed to reproduce derived output.
- Application-generated artifacts that can be regenerated.
- Temporary files whose historical versions have no continuing business value.

Version cleanup should implement an approved retention decision, not replace one.

## Protect Compliance and Recovery Requirements

### Account for S3 Object Lock

S3 Object Lock can protect object versions through retention periods and legal holds. Lifecycle cleanup must not be treated as a mechanism for bypassing those protections.

Before deploying cleanup:
- Identify buckets using Object Lock.
- Review retention mode and retention deadlines.
- Check applicable legal holds.
- Confirm that the lifecycle policy complies with record-retention requirements.

Objects protected by Object Lock may remain stored even when a lifecycle rule would otherwise attempt to remove them.

### Verify recovery requirements

Historical versions are useful only when the organization understands how to retrieve them and how long they must remain available.

For critical data, define:
- The number of historical versions to retain.
- The minimum retention period.
- The required recovery point and recovery time objectives.
- The recovery procedure for accidental overwrites or deletions.
- The relationship between version retention and backups or replication.

Versioning is not a complete backup or disaster recovery strategy. It does not independently protect against every form of account compromise, malicious deletion, or regional disaster.

Test the ability to restore an older version before relying on it as a recovery mechanism.

## Monitor Cleanup and Storage Savings

### Track operational indicators

Measure the following before and after enabling cleanup:

| Indicator | Why it matters |
|---|---|
| Noncurrent version count | Reveals whether historical versions are accumulating |
| Noncurrent storage volume | Indicates the potential impact on storage charges |
| Storage volume by storage class | Helps determine the actual cost of retained versions |
| Delete marker count | Identifies metadata and cleanup patterns that require investigation |
| Lifecycle expiration activity | Helps verify that configured cleanup actions are occurring |
| Recovery test results | Confirms that retained history meets business requirements |

Use S3 Inventory and storage reporting to estimate the number and volume of eligible versions. CloudTrail and applicable S3 lifecycle event notifications can provide additional audit evidence for deletion activity.

Lifecycle processing is asynchronous. Do not expect every eligible version to disappear exactly when a configured day threshold is reached.

### Investigate unexpected retention

If versions remain after the expected cleanup period, inspect:

1. Whether the lifecycle rule is enabled.
2. Whether the rule's prefix, tag, or size filter matches the object.
3. Whether the object version has been noncurrent long enough.
4. Whether `NewerNoncurrentVersions` prevents expiration.
5. Whether Object Lock or a legal hold protects the version.
6. Whether the bucket's current lifecycle configuration matches the approved deployment.

Use the evidence to distinguish configuration errors from retention restrictions or normal lifecycle processing delays.

Reference: [Troubleshooting S3 Lifecycle issues](https://docs.aws.amazon.com/AmazonS3/latest/userguide/troubleshoot-lifecycle.html).

## Common Cleanup Mistakes

| Mistake | Impact | Recommended practice |
|---|---|---|
| Treating versioning as unlimited, free history | Storage costs can grow with repeated overwrites | Establish retention and cleanup policies |
| Confusing current-version expiration with noncurrent-version expiration | Current data may be hidden or deleted contrary to expectations | Use the appropriate lifecycle action for each requirement |
| Omitting the lifecycle rule's intended filter | Cleanup can affect a broader object population than intended | Target approved prefixes, tags, or other supported filters |
| Using a newer-version count without evaluating age | Older history may remain longer than expected | Understand both expiration conditions |
| Assuming suspended versioning removes older versions | Existing historical data remains | Use lifecycle expiration or a controlled version-deletion process |
| Ignoring expired delete markers | Delete markers can accumulate after historical versions disappear | Configure separate expired-delete-marker cleanup where appropriate |
| Replacing the entire lifecycle configuration accidentally | Existing lifecycle behavior may be lost | Preserve and review all existing rules before deployment |
| Ignoring Object Lock retention | Protected versions remain despite cleanup expectations | Verify retention settings and legal holds |
| Treating version cleanup as a backup strategy | Required history or disaster recovery protection may be inadequate | Test recovery and maintain suitable independent protections |

## Production Readiness Checklist

- [ ] Bucket versioning status has been verified.
- [ ] The target object population and lifecycle filter have been reviewed.
- [ ] Required retention periods and the number of newer versions to preserve are documented.
- [ ] Noncurrent version expiration has been tested against representative objects.
- [ ] Existing lifecycle rules are preserved and reviewed before deployment.
- [ ] Expired delete markers are managed separately when appropriate.
- [ ] Object Lock retention and legal holds have been considered.
- [ ] Historical-version recovery has been tested for critical data.
- [ ] Storage consumption and lifecycle processing are monitored.
- [ ] Configuration is managed through a reviewed deployment process.
- [ ] Rollback and incident-response procedures are documented.

## Authoritative References

- [Lifecycle configuration elements](https://docs.aws.amazon.com/AmazonS3/latest/userguide/intro-lifecycle-rules.html)
- [Lifecycle configuration examples](https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-configuration-examples.html)
- [Deleting object versions](https://docs.aws.amazon.com/AmazonS3/latest/userguide/DeletingObjectVersions.html)
- [Managing delete markers](https://docs.aws.amazon.com/AmazonS3/latest/userguide/ManagingDelMarkers.html)
- [S3 Versioning troubleshooting](https://docs.aws.amazon.com/AmazonS3/latest/userguide/troubleshooting-versioning.html)
- [Troubleshooting S3 Lifecycle](https://docs.aws.amazon.com/AmazonS3/latest/userguide/troubleshoot-lifecycle.html)

## Key Takeaways

- Noncurrent version cleanup reduces storage costs by permanently deleting historical versions that are no longer required.
- `NoncurrentVersionExpiration` supports age-based cleanup and optional retention of newer noncurrent versions.
- Expired delete markers require separate lifecycle handling, and current-version expiration is a different operation.
- Object Lock, legal holds, lifecycle filters, and existing rules must be reviewed before deploying cleanup.
- Monitor lifecycle behavior and verify historical-version recovery so that cost optimization does not undermine retention or disaster recovery requirements.