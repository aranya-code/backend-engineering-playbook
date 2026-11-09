# 06- S3 Glacier Instant Retrieval

## Overview

Amazon S3 Glacier Instant Retrieval is a storage class designed for long-lived data that is accessed infrequently but must remain available with millisecond retrieval latency.

It is suitable for data that must remain online without the asynchronous restoration process required by S3 Glacier Flexible Retrieval and S3 Glacier Deep Archive.

Typical use cases include historical medical images, older customer documents, archival media, and records that are rarely accessed but must be retrieved immediately when requested.

Glacier Instant Retrieval can reduce storage costs compared with S3 Standard and other frequently accessed storage classes. However, the lower storage rate comes with retrieval charges, a 90-day minimum storage duration, and a minimum billable object size of 128 KB.

The key engineering decision is whether the expected storage savings outweigh retrieval, request, lifecycle transition, and early-deletion costs.

## Understand S3 Glacier Instant Retrieval

### Key characteristics

| Characteristic | Behavior |
|---|---|
| AWS CLI storage class identifier | `GLACIER_IR` |
| Access pattern | Rarely accessed, typically quarterly |
| Retrieval latency | Milliseconds |
| Restoration required | No |
| Minimum storage duration | 90 days |
| Minimum billable object size | 128 KB |
| Retrieval charges | Apply |
| Availability design | Designed for 99.9% availability |
| Availability Zone resilience | Data is stored across multiple Availability Zones |
| Object encryption | Supports applicable S3 server-side encryption configurations |
| Lifecycle transitions | Supported from eligible source storage classes |

These properties distinguish Glacier Instant Retrieval from the other S3 Glacier storage classes. Confirm current pricing, regional availability, and applicable feature constraints in the [official S3 storage class documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/glacier-storage-classes.html).

### Understand immediate access versus archival restoration

The word *Glacier* does not mean every Glacier storage class requires restoration.

| Storage class | Access behavior | Restore required? | Appropriate workload |
|---|---|---|---|
| S3 Glacier Instant Retrieval | Millisecond access | No | Rarely accessed data requiring immediate retrieval |
| S3 Glacier Flexible Retrieval | Asynchronous retrieval, generally minutes to hours | Yes | Archives that tolerate restoration delays |
| S3 Glacier Deep Archive | Asynchronous retrieval, generally hours | Yes | Long-term archives with infrequent recovery requirements |

With Glacier Instant Retrieval, authorized clients can issue ordinary S3 `GetObject` requests. Applications do not need to initiate an archive restore and track its completion before reading the object.

This makes the class suitable for online applications that must support occasional immediate access to historical data.

## Choose Appropriate Workloads

### Use cases

Consider Glacier Instant Retrieval for:

- **Historical medical records:** Images that are rarely opened but must be available during an appointment.
- **Document repositories:** Older invoices, contracts, or customer documents with infrequent retrieval.
- **Media archives:** Original images and media assets that must remain immediately downloadable.
- **Regulated records:** Retained records that require online retrieval, subject to their retention and compliance requirements.
- **Historical application artifacts:** Long-lived files that must remain accessible without a restoration workflow.

These workloads should have sufficiently low retrieval volumes to justify the storage-class economics.

### Workloads that are poor candidates

Avoid Glacier Instant Retrieval when:

- Users frequently download the objects.
- The application repeatedly reads the same data.
- Objects are commonly deleted or replaced before 90 days.
- The workload creates millions of very small objects with limited per-object storage savings.
- The application's expected access pattern is unknown and changing, making S3 Intelligent-Tiering more appropriate.
- Retrieval latency is not required to be immediate and a lower-cost asynchronous archive is acceptable.

For unpredictable access patterns, evaluate S3 Intelligent-Tiering. For long-term archival workloads that can tolerate restoration delays, compare Glacier Flexible Retrieval and Glacier Deep Archive.

## Understand Cost and Billing

### Account for all cost components

Storage-class selection must consider the full cost of retaining and retrieving data.

| Cost component | Consideration |
|---|---|
| Storage | Monthly storage is billed at the applicable Glacier Instant Retrieval rate |
| Retrieval | Data retrieval incurs applicable per-GB charges |
| Requests | PUT, GET, COPY, LIST, and other applicable requests incur request charges |
| Lifecycle transitions | Each object transition can incur a transition request charge |
| Minimum storage duration | Deletion, overwrite, or transition before 90 days can incur a prorated early-deletion charge |
| Minimum object size | Objects smaller than 128 KB are billed for 128 KB of storage |
| Data transfer | Applicable data-transfer charges can apply |
| Monitoring and operations | Reporting, application processing, and operational tooling may add costs |

Unlike Glacier Flexible Retrieval and Deep Archive, Glacier Instant Retrieval does not have the same additional 40 KB per-object archival metadata storage overhead described for those archive classes.

Always use current regional pricing rather than assuming that a low storage rate guarantees lower total costs.

Reference: [Amazon S3 pricing](https://aws.amazon.com/s3/pricing/).

### Evaluate the 90-day minimum storage duration

Objects stored in Glacier Instant Retrieval have a minimum storage duration of 90 days.

If an object is deleted, overwritten, or transitioned to another storage class before the minimum duration ends, a prorated charge can apply for the remaining period.

For example, moving an object into Glacier Instant Retrieval and deleting it after 20 days does not necessarily eliminate the remaining 70 days of minimum-duration storage charges.

For workloads with frequent updates, assess whether the expected retention period is sufficiently long before applying the class.

### Evaluate small-object economics

The class has a minimum billable object size of 128 KB. An object smaller than this threshold is billed as though it occupies 128 KB.

This matters for applications that store:
- Small JSON documents.
- Individual log records.
- Tiny thumbnails.
- Metadata fragments.
- Numerous small generated artifacts.

Consider retaining these objects in another suitable storage class or aggregating them into larger objects when the application can preserve the required access and retention boundaries.

Do not aggregate objects when independent deletion, authorization, retrieval, or legal retention is required.

### Estimate the total cost

Use the following model to compare Glacier Instant Retrieval with alternative storage classes:

\[
\begin{aligned}
C_{\text{total}} ={}&
C_{\text{storage}} + C_{\text{requests}} \\
&+ C_{\text{retrieval}} + C_{\text{transitions}} \\
&+ C_{\text{early deletion}} + C_{\text{transfer}}
\end{aligned}
\]

Estimate each component using actual storage volume, object count, retrieval frequency, average object size, retention period, and current regional prices.

The correct comparison is total workload cost, not storage cost per GB alone.

## Upload Objects Directly to Glacier Instant Retrieval

### Use the AWS CLI

Specify `GLACIER_IR` when uploading objects that are already known to meet the intended access requirements.

```bash
aws s3 cp ./historical-report.pdf \
  "s3://${BUCKET}/historical/reports/report-2025.pdf" \
  --storage-class GLACIER_IR
```

The command uploads the object directly into Glacier Instant Retrieval.

The AWS identity must have the permissions required for the upload, and the bucket must be configured according to the organization's security and encryption requirements.

### Verify the resulting storage class

Use `head-object` to inspect an object:

```bash
aws s3api head-object \
  --bucket "$BUCKET" \
  --key "historical/reports/report-2025.pdf"
```

Inspect the returned `StorageClass` field where present. For objects stored in S3 Standard, the field can be omitted because Standard is the default storage class.

For programmatic verification, use an AWS SDK to inspect the response metadata rather than assuming that a successful upload proves every required configuration property.

## Configure Lifecycle Transitions

### Automate transitions for older objects

S3 Lifecycle can transition eligible objects to Glacier Instant Retrieval after a specified number of days.

This is appropriate when objects start in a more frequently accessed class and become rarely accessed according to a predictable retention policy.

Example lifecycle configuration:

```json
{
  "Rules": [
    {
      "ID": "TransitionHistoricalReportsToGlacierInstantRetrieval",
      "Status": "Enabled",
      "Filter": {
        "And": {
          "Prefix": "historical/reports/",
          "ObjectSizeGreaterThan": 131071
        }
      },
      "Transitions": [
        {
          "Days": 90,
          "StorageClass": "GLACIER_IR"
        }
      ]
    }
  ]
}
```

This rule targets objects under `historical/reports/` that are at least 128 KB and transitions eligible objects after 90 days.

The age threshold is illustrative. Select it according to the application's actual access pattern and retention requirements.

Objects smaller than 128 KB are excluded because their transition costs may outweigh the savings. Lifecycle configurations also have object-size filtering behavior that should be reviewed before deployment.

### Apply and inspect the configuration

First, inspect the bucket's existing lifecycle configuration:

```bash
aws s3api get-bucket-lifecycle-configuration \
  --bucket "$BUCKET"
```

After combining the intended rule with any existing rules that must be preserved, apply the complete configuration:

```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket "$BUCKET" \
  --lifecycle-configuration file://lifecycle.json
```

Verify the resulting configuration:

```bash
aws s3api get-bucket-lifecycle-configuration \
  --bucket "$BUCKET"
```

**Important:** `put-bucket-lifecycle-configuration` replaces the existing lifecycle configuration. Do not deploy a partial JSON document without preserving other required rules.

Lifecycle actions are asynchronous. The object may not transition at the exact moment its age threshold is reached.

Reference: [S3 Lifecycle transition considerations](https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-transition-general-considerations.html).

## Access Objects from Backend Applications

### Use normal S3 object operations

Glacier Instant Retrieval does not require the application to initiate an archive restoration before reading an eligible object.

A Python backend using Boto3 can read an object through the normal S3 client:

```python
import os

import boto3
from botocore.config import Config


s3_client = boto3.client(
    "s3",
    region_name=os.environ["AWS_REGION"],
    config=Config(
        retries={
            "mode": "standard",
            "total_max_attempts": 4,
        }
    ),
)


def download_object(bucket: str, key: str, destination: str) -> None:
    s3_client.download_file(
        Bucket=bucket,
        Key=key,
        Filename=destination,
    )
```

The runtime should obtain AWS credentials through an appropriate IAM role or the standard AWS credential provider chain. Avoid embedding access keys in application source code.

Production implementations should additionally handle authorization, object-not-found errors, temporary local storage, cleanup, logging, and application-specific retry policies.

### Keep S3 operations in a service layer

Django, Django REST Framework, FastAPI, Flask, and Celery applications should use a reusable storage service rather than duplicating S3 logic in every request handler.

The service layer should:
- Validate the caller's authorization before exposing an object.
- Generate object keys from trusted application identifiers.
- Use the appropriate bucket and Region.
- Handle `NoSuchKey`, `AccessDenied`, and transient failures distinctly.
- Avoid loading large objects entirely into memory.
- Apply timeouts and bounded retry policies.
- Track operational failures without logging sensitive document contents or credentials.

For large downloads, stream data or use a presigned URL when the architecture permits direct client-to-S3 access.

## Design Secure Download Workflows

### Generate presigned URLs for authorized clients

A backend can generate a time-limited presigned download URL for an object stored in Glacier Instant Retrieval.

The flow is:

1. Authenticate the caller.
2. Verify that the caller is authorized to access the requested document.
3. Generate a URL for the exact object key.
4. Return the URL with an appropriate expiration.
5. Allow the client to download the object directly from S3.

Presigned URLs do not bypass the underlying access controls. The signing principal must have the permissions required for the operation, and the URL remains subject to relevant credential, policy, and expiration constraints.

Treat the URL as a temporary bearer capability. Do not expose it through logs, analytics, or error messages.

### Handle application and S3 failures separately

A successful API response does not guarantee that a subsequent download will succeed. A URL can expire, credentials can become invalid, permissions can change, or the object can be deleted.

Distinguish between:
- Application authentication or authorization failures.
- S3 object-not-found responses.
- S3 access-denied responses.
- Network timeouts and transient service errors.
- Presigned URL expiration or signature problems.

Apply bounded retries to transient failures. Repeated retries do not fix invalid permissions, missing objects, or expired URLs.

Reference: [Using S3 presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html).

## Migrate Existing Objects Safely

Changing a bucket's default encryption or storage configuration does not automatically change the storage class of existing objects.

To transition a large dataset:
1. Identify the intended object population through S3 Inventory or another reliable inventory process.
2. Review object sizes, retention requirements, and access patterns.
3. Calculate transition, retrieval, and early-deletion costs.
4. Test the lifecycle rule or copy operation on representative objects.
5. Apply the change using S3 Lifecycle or S3 Batch Operations where appropriate.
6. Verify the resulting storage classes and application access behavior.
7. Monitor costs and transition failures.

For an individual object, a copy operation can be used to change storage class:

```bash
aws s3api copy-object \
  --bucket "$BUCKET" \
  --key "$OBJECT_KEY" \
  --copy-source "${BUCKET}/${OBJECT_KEY}" \
  --storage-class GLACIER_IR \
  --metadata-directive COPY
```

Treat this as an illustrative self-copy operation. Ensure that the `--copy-source` value is correctly URL-encoded when necessary, and verify permissions, metadata, tags, versioning behavior, and encryption requirements before running it.

A self-copy can create a new object version in a versioned bucket. Use a controlled migration procedure rather than executing broad recursive copy commands against production data.

## Monitor and Operate the Storage Class

### Establish measurable indicators

Track the following metrics and operational signals:

| Indicator | Purpose |
|---|---|
| Stored bytes and object counts | Understand the size and shape of the archived dataset |
| GET requests and retrieved bytes | Determine whether the access pattern still justifies the class |
| Storage-class distribution | Verify that lifecycle transitions are taking effect |
| Transition request activity | Understand migration costs and workload changes |
| Early deletion or overwrite activity | Identify avoidable minimum-duration charges |
| S3 request failures | Detect access and application integration problems |
| Total S3 cost by workload | Validate expected savings |

Use S3 Inventory, Storage Lens, CloudWatch metrics where applicable, CloudTrail data events where configured, and AWS Cost and Usage Reports according to the required level of detail.

No single reporting source provides every metric needed for a complete cost and security investigation.

### Review the policy periodically

Reassess the class when:
- The business starts retrieving historical objects more frequently.
- Object retention periods change.
- A large volume of small objects is added.
- Application download latency requirements change.
- Lifecycle rules are modified.
- Storage costs diverge from estimates.

A workload that becomes frequently accessed may be better suited to S3 Standard. A workload with unpredictable access may benefit from Intelligent-Tiering. A workload that no longer requires immediate retrieval may qualify for a different archive class.

## Common Mistakes

| Mistake | Consequence | Prevention |
|---|---|---|
| Assuming Glacier Instant Retrieval requires restoration | Unnecessary workflow complexity and delayed access | Use normal S3 GET operations for eligible objects |
| Ignoring retrieval charges | Unexpected costs when historical data is downloaded | Estimate retrieved GB per month |
| Ignoring the 90-day minimum | Early-deletion or early-transition charges | Align retention and lifecycle policies with the minimum duration |
| Transitioning tiny objects without analysis | Storage and request costs can outweigh savings | Filter small objects or evaluate aggregation |
| Treating Glacier Instant Retrieval as Deep Archive | Incorrect assumptions about access latency and restoration | Distinguish storage classes by their access behavior |
| Assuming bucket defaults migrate existing objects | Historical objects remain in their previous classes | Use Lifecycle, Batch Operations, or a controlled migration |
| Replacing lifecycle configuration with a partial file | Unrelated lifecycle policies can be lost | Inspect, merge, apply, and verify the complete configuration |
| Assuming a successful API request guarantees download availability | Later requests may still fail because of changed permissions or expired URLs | Handle download-time errors explicitly |
| Measuring only storage costs | Request and retrieval charges undermine savings | Measure total cost per workload |

## Production Readiness Checklist

- [ ] The workload requires millisecond object retrieval despite infrequent access.
- [ ] Expected storage savings exceed retrieval and request costs.
- [ ] The 90-day minimum storage duration is compatible with retention requirements.
- [ ] Objects smaller than 128 KB have been evaluated for cost efficiency.
- [ ] Lifecycle transition rules use suitable prefixes, filters, and retention thresholds.
- [ ] Existing lifecycle rules are preserved when configurations are updated.
- [ ] Direct uploads and lifecycle transitions have been tested.
- [ ] Backend access uses IAM-based credentials and least-privilege permissions.
- [ ] Presigned download URLs are generated only after authorization.
- [ ] Existing objects are inventoried before a large-scale migration.
- [ ] S3 costs and retrieval behavior are monitored after deployment.
- [ ] Application error handling distinguishes authorization failures, missing objects, and transient errors.

## Authoritative References

- [S3 Glacier Instant Retrieval](https://docs.aws.amazon.com/AmazonS3/latest/userguide/glacier-storage-classes.html)
- [Understanding and managing S3 storage classes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html)
- [S3 Lifecycle management](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html)
- [Lifecycle transition considerations](https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-transition-general-considerations.html)
- [Using S3 presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html)
- [Amazon S3 pricing](https://aws.amazon.com/s3/pricing/)

## Key Takeaways

- S3 Glacier Instant Retrieval provides millisecond access without an archive restoration workflow, making it suitable for rarely accessed online data.
- Include retrieval fees, request charges, the 128 KB minimum billable object size, and the 90-day minimum storage duration in cost estimates.
- Use S3 Lifecycle for predictable transitions and verify existing rules before replacing bucket lifecycle configuration.
- Keep backend access secure through IAM roles, caller authorization, bounded retries, and carefully managed presigned URLs.
- Validate storage-class decisions using object inventories, application access patterns, operational metrics, and total workload cost.