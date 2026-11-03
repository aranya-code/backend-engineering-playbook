# 19- Common Interview Traps and Misconceptions

## Overview

Amazon S3 interview questions often test whether a candidate understands the difference between a service guarantee and an application-level assumption. Knowing the APIs is not enough; senior engineers must understand consistency, authorization, data recovery, event delivery, object identity, performance, and operational cost.

This document covers common misconceptions, why they are incorrect, how S3 behaves, and what a production-ready design should do instead.

## Object Storage and Object Identity Traps

### Misconception: S3 uses a traditional folder hierarchy

**Incorrect:** S3 objects are stored inside physical directories, just like files on a Linux filesystem.

**Correct:** General purpose S3 buckets use a flat object namespace. A key such as `customers/42/invoice.pdf` is an object key containing slash characters. The S3 console interprets common prefixes as folders for convenient navigation.

```text
Bucket: company-documents

Object keys:
    customers/42/invoice.pdf
    customers/42/profile.png
    customers/73/invoice.pdf
```

These are independent objects. Renaming a logical folder is not a normal directory operation; an application generally copies objects to new keys and deletes the old ones.

Directory buckets have a different hierarchical directory model, so avoid making universal claims about every S3 bucket type.

**Interview follow-up:** Can you rename a folder without copying objects?

Not as a conventional filesystem rename in a general purpose bucket. Applications typically implement the operation by copying objects and deleting their previous keys.

Reference: [Organizing objects using folders](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-folders.html).

### Misconception: An S3 object is identified only by its filename

**Incorrect:** `invoice.pdf` uniquely identifies an object in S3.

**Correct:** An object is identified by its bucket and key. When versioning is enabled, the version ID identifies a particular version of that object.

For example:

```text
Bucket: company-documents
Key:    customers/42/invoice.pdf
Version ID: 3HL4kqtJlcpXroDTDmjVBH40Nrjfkd
```

Two objects can have the same key in different buckets. Multiple versions can also exist for the same key in a versioned bucket.

**Production implication:** Store stable object references in application metadata. If a workflow must process a precise version of an object, preserve its version ID rather than assuming that the key will always refer to the same bytes.

### Misconception: Prefixes provide automatic tenant isolation

**Incorrect:** Storing each tenant under `tenant-123/` automatically prevents other tenants from accessing its data.

**Correct:** A prefix is a naming convention, not an authorization boundary by itself.

For example:

```text
s3://company-documents/tenant-123/reports/report.pdf
```

The application must enforce the correct access permissions through IAM, bucket policies, access points, or application authorization, as appropriate.

**Production recommendation:** Derive tenant identifiers from authenticated identity and validated application state. Never trust a client-supplied object key as proof of ownership.

### Misconception: Bucket names are always globally unique across every AWS environment

**Incorrect:** Every S3 bucket type follows the same naming and namespace rules.

**Correct:** General purpose buckets traditionally use a shared global namespace within an AWS partition. AWS also supports an account regional namespace for eligible general purpose bucket creation. Directory buckets use different naming rules, including a zone-specific suffix.

The bucket type and namespace selected during creation therefore matter. A bucket's name and Region cannot be changed after creation.

**Production implication:** Generate environment-specific names carefully, and do not assume a bucket name can be reused by another account after deletion. Validate the namespace and ownership model before implementing automated bucket creation.

Reference: [Amazon S3 bucket types and namespaces](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html).

### Misconception: S3 object metadata is the same as a database record

**Incorrect:** Custom metadata can replace a relational database for all application queries.

**Correct:** Object metadata describes an object, while database records support application-level query and transaction patterns.

Use S3 metadata and tags for object-associated attributes. Use PostgreSQL or DynamoDB for searchable business data, tenant ownership, processing state, relationships, and transactional workflows.

Do not make large-scale metadata searches through repeated object listings a substitute for a properly designed query store.

## Consistency, Durability, and Availability Traps

### Misconception: S3 is eventually consistent

**Incorrect:** After a successful upload, a read or listing may routinely return an older view because S3 is eventually consistent.

**Correct:** S3 provides strong read-after-write consistency for object PUTs and DELETEs, including relevant object metadata operations and listings.

For example, after a successful PUT completes, a subsequent GET for that object reflects the completed write.

However, strong consistency does not mean:

- A transaction spans S3 and PostgreSQL.
- Multiple independent API calls form one atomic operation.
- An event notification arrives immediately or exactly once.
- A downstream cache automatically invalidates itself.
- A replicated destination object is instantly available in another Region.

**Interview trap:** A candidate may correctly explain strong consistency but incorrectly infer that an S3 upload and database update form a transaction.

Consider this failure:

1. The backend uploads a file to S3.
2. The PostgreSQL transaction fails.
3. The object remains in S3 without its expected application record.

The application needs a recovery strategy, such as idempotent upload initiation, processing states, reconciliation jobs, or cleanup of abandoned objects.

Reference: [Amazon S3 data consistency model](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html).

### Misconception: Eleven nines of durability means the application will always be available

**Incorrect:** Extremely high durability guarantees that every S3 request will succeed.

**Correct:** Durability concerns the probability of losing stored data. Availability concerns whether the service can successfully serve requests.

Requests can still fail because of network problems, incorrect authorization, throttling, application errors, misconfiguration, or service disruptions.

**Production recommendation:** Combine appropriate timeouts, retry policies with backoff and jitter, error handling, monitoring, and recovery procedures. Do not interpret durability figures as an application-level availability guarantee.

### Misconception: Strong consistency means S3 supports multi-object transactions

**Incorrect:** Updating multiple objects is atomic because S3 provides strong consistency.

**Correct:** Strong consistency applies to individual supported operations; it does not provide a general transaction spanning multiple objects.

Suppose a data pipeline publishes a manifest and ten data files. A reader could observe some successfully uploaded files before the complete dataset is published.

One solution is a publication protocol:

1. Upload data files under an immutable run-specific prefix.
2. Validate the files and their checksums.
3. Publish a manifest or completion record only after validation succeeds.
4. Require readers to consume only published datasets.

This makes publication state explicit without assuming multi-object atomicity.

## Versioning, Replication, and Recovery Traps

### Misconception: Deleting an object always permanently deletes its data

**Incorrect:** A DELETE request always removes every stored version of an object.

**Correct:** In a versioning-enabled general purpose bucket, deleting an object without specifying a version ID normally creates a delete marker. Older versions can remain stored and incur storage charges.

A version-specific delete removes the specified version, subject to applicable permissions and retention controls.

Inspect versions when diagnosing an unexpected deletion:

```bash
aws s3api list-object-versions \
  --bucket company-documents \
  --prefix customers/42/invoice.pdf
```

**Production implication:** Recovery procedures must understand version IDs and delete markers. A normal GET may report the object as deleted even though older versions remain recoverable.

### Misconception: Versioning is a complete backup strategy

**Incorrect:** Enabling S3 Versioning guarantees recovery from every accidental deletion, compromise, or data-loss scenario.

**Correct:** Versioning helps recover from overwrites and certain deletions, but it does not independently protect against every privileged action, retention mistake, or broader account compromise.

A production recovery strategy may combine versioning with independently protected backups, retention controls, replication, and tested restoration procedures.

The design should answer:

- Which identities can permanently delete versions?
- How long must data remain recoverable?
- Can an attacker modify the recovery configuration?
- How is the destination or backup copy protected?
- Has an actual restoration been tested?

### Misconception: Cross-Region Replication is synchronous

**Incorrect:** A successful source write means the destination Region immediately contains the replicated object.

**Correct:** S3 Replication is asynchronous. Replication can lag or fail, and a source PUT does not imply that the destination copy is already available.

A recovery procedure must verify the destination object's existence, version, and readiness rather than assuming immediate replication.

Also, a replication rule ordinarily applies to eligible objects written after the rule is configured. Existing objects may require S3 Batch Replication or another migration procedure.

Reference: [S3 Replication](https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication.html).

### Misconception: Replication automatically provides complete disaster recovery

**Incorrect:** Two replicated buckets in different Regions automatically provide a functioning regional failover architecture.

**Correct:** Replication copies eligible objects; it does not automatically migrate every dependency of an application.

A complete disaster recovery plan may need:
- Application deployment in the recovery Region.
- Independent IAM and KMS configuration.
- Database recovery and replication.
- DNS, routing, and endpoint changes.
- Verification that the destination data is complete.
- A tested procedure for restoring service and controlling writes.

Replication also does not automatically turn the destination into a fully independent backup. Deletion and replication behavior depends on the configured rules.

**Interview follow-up:** How would you prove the recovery design works?

Perform a controlled recovery exercise that verifies data availability, application access, dependency readiness, and measured recovery time. Document what was tested instead of claiming that replication alone proves failover.

### Misconception: Versioning can simply be disabled after being enabled

**Incorrect:** S3 Versioning can always be returned to its original never-versioned state.

**Correct:** Once versioning has been enabled on a general purpose bucket, it can be suspended, but not returned to the original never-enabled state. Previously created versions remain subject to their applicable lifecycle and deletion rules.

Suspending versioning also does not mean that all existing noncurrent versions disappear.

**Production recommendation:** Treat enabling versioning as a long-term storage design decision. Define lifecycle policies for noncurrent versions and incomplete multipart uploads where appropriate, and estimate their ongoing costs.

### Misconception: Object Lock is equivalent to versioning

**Incorrect:** Versioning alone guarantees that a retained object cannot be permanently deleted.

**Correct:** Versioning preserves object versions, while S3 Object Lock provides retention and legal-hold capabilities for supported bucket configurations.

Object Lock retention depends on its mode and configuration. Governance and compliance modes have different protection guarantees, and governance-mode bypass requires specific authorization.

Use Object Lock when regulatory or business requirements call for protection against deletion or alteration during a defined retention period. Verify the retention configuration and operational consequences before applying it to production data.

## Security and Authorization Traps

### Misconception: A successful IAM permission check guarantees S3 access

**Incorrect:** If the caller has `s3:GetObject`, the request must succeed.

**Correct:** Authorization depends on the complete applicable policy configuration, including explicit denies, resource policies, identity policies, permission boundaries, session policies, organization-level controls, and other applicable restrictions.

For SSE-KMS encrypted objects, KMS authorization must also permit the relevant cryptographic operation.

A useful diagnostic separation is:

| Observed failure | What to investigate |
|---|---|
| S3 `AccessDenied` | IAM policies, bucket policy, access point policy, organization controls, request context, and object permissions |
| Failure accessing an SSE-KMS object | S3 authorization plus KMS key policy, IAM permissions, grants where applicable, and the relevant KMS operation |
| Presigned URL returns `403` | Signing identity, operation permissions, expiration, required headers, policy restrictions, and KMS permissions |
| Cross-account access fails | Both account-side configuration and resource-side authorization, including KMS where applicable |

Do not treat every `403` as a missing `s3:GetObject` permission.

### Misconception: Encryption means an object is private

**Incorrect:** If an object is encrypted, unauthorized principals cannot retrieve it.

**Correct:** Encryption protects the confidentiality of stored data, while authorization determines who can perform operations.

An SSE-S3 or SSE-KMS encrypted object still requires appropriate access permissions. A public-access configuration or overly permissive policy must not be treated as safe merely because encryption is enabled.

Use private buckets by default, review public-access settings, and grant only required actions and resources.

### Misconception: CORS is an authorization mechanism

**Incorrect:** Disabling cross-origin access prevents unauthorized clients from accessing an S3 object.

**Correct:** CORS controls whether browsers permit frontend JavaScript to make certain cross-origin requests and access their responses. It does not replace IAM, bucket policies, or application authorization.

A non-browser client is not constrained by browser CORS enforcement.

**Production recommendation:** Configure both appropriate browser CORS rules and actual access controls. Never use CORS as the security boundary for private document storage.

### Misconception: A presigned URL is an ordinary permanent download URL

**Incorrect:** A presigned URL simply points to a file and remains usable as long as its configured expiration has not passed.

**Correct:** A presigned URL is a bearer capability granting time-limited access to a specific signed operation. Anyone holding a usable URL may exercise that capability within its restrictions.

Its effective lifetime can be shorter than the requested expiration if the signing credentials expire or are revoked. A presigned PUT to an existing key can replace the current object at that key.

**Production recommendation:**
- Use a short, appropriate expiration.
- Generate URLs only after application authorization.
- Use server-generated object keys.
- Validate expected content, size, and upload completion.
- Avoid logging or exposing signed query strings.
- Treat URLs as secrets while they remain valid.

Reference: [Using S3 presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html).

### Misconception: A private bucket can be made safe just by hiding its URL

**Incorrect:** S3 endpoints are difficult to guess, so obscure object keys are sufficient protection.

**Correct:** Security must come from enforced authorization, not secrecy of object names or endpoints.

Random identifiers can reduce accidental disclosure, but an object reference is not an authorization check. Always authorize the requester before returning metadata, issuing a download URL, or permitting deletion.

### Misconception: Block Public Access replaces all access-control design

**Incorrect:** Once S3 Block Public Access is enabled, no other permissions need review.

**Correct:** Block Public Access prevents specified forms of public exposure, but applications must still control private access through identity-based policies, bucket policies, access points, and other applicable authorization mechanisms.

Review both public exposure protections and the permissions granted to trusted identities.

## Upload, API, and Performance Traps

### Misconception: Every S3 object can be uploaded in one PUT request

**Incorrect:** Any object size can be sent through a single `PutObject` operation.

**Correct:** A single PUT supports objects up to 5 GB. The maximum size of an S3 object is 5 TB. Larger uploads require multipart upload, which is also useful for many objects that are smaller than the maximum.

A multipart workflow divides the object into parts that are uploaded separately and assembled by S3 at completion.

**Production recommendation:** Use an appropriate transfer manager or multipart-upload implementation for large objects. Handle retries per part, preserve upload state when needed, and configure cleanup for abandoned multipart uploads.

Reference: [Uploading and copying objects](https://docs.aws.amazon.com/AmazonS3/latest/userguide/upload-objects.html).

### Misconception: A successful HTTP response proves that the entire business workflow completed

**Incorrect:** Once S3 returns success, the file is necessarily validated, indexed, virus-scanned, and available to every downstream service.

**Correct:** S3 success confirms the corresponding storage operation succeeded. Business processing is a separate workflow.

A backend should distinguish states such as:

```text
PENDING_UPLOAD
    -> UPLOADED
    -> VALIDATING
    -> PROCESSING
    -> COMPLETED

Failure transitions:
    VALIDATING -> FAILED
    PROCESSING -> FAILED
```

The exact state machine depends on the application. Ensure that retries, duplicate events, and worker crashes cannot incorrectly mark an incomplete job as complete.

### Misconception: S3 event notifications are delivered exactly once and in order

**Incorrect:** An S3 event-triggered Lambda runs exactly once for each object change, in the original event order.

**Correct:** S3 Event Notifications are designed for at-least-once delivery. Notifications can be duplicated and are not guaranteed to arrive in the same order as the corresponding operations.

A consumer should therefore be idempotent and should not rely on event arrival order as the source of truth.

Common safeguards include:
- Deduplication based on durable application state and an appropriate event identity.
- Recording processing outcomes in a database.
- Using object version IDs where version-specific processing is required.
- Separating input and output prefixes to avoid recursive triggers.
- Configuring retries, monitoring, and failure recovery.

Reference: [S3 event notification behavior](https://docs.aws.amazon.com/AmazonS3/latest/userguide/notification-how-to-event-types-and-destinations.html).

### Misconception: The S3 ETag is always the MD5 checksum of the object

**Incorrect:** Comparing ETags always verifies that two object contents are identical using MD5.

**Correct:** ETag behavior depends on the upload and encryption circumstances. Multipart-upload ETags are not generally the MD5 checksum of the complete object, and other upload configurations can also produce ETags that should not be interpreted as a universal content checksum.

When content integrity matters, use supported S3 checksum functionality or an application-controlled checksum with a clearly defined algorithm and verification procedure.

Do not build data-integrity guarantees around an unconditional assumption that ETag equals MD5.

### Misconception: More upload concurrency always improves performance

**Incorrect:** Increasing the number of simultaneous uploads necessarily increases throughput.

**Correct:** Throughput depends on object sizes, available network bandwidth, client-side CPU, connection reuse, concurrency, retry behavior, and the workload's request pattern.

Excessive concurrency can exhaust connections, memory, sockets, or worker capacity and can amplify transient failures.

**Production recommendation:** Benchmark with representative object sizes and traffic. Tune concurrency and multipart part sizes, reuse SDK clients, apply bounded retries, and measure throughput and error rates.

### Misconception: S3 is a mounted filesystem with atomic rename

**Incorrect:** Copying or renaming a file behaves exactly like a local filesystem operation.

**Correct:** General purpose S3 object operations do not provide conventional filesystem rename semantics. A move is normally implemented as a copy followed by a delete, creating a failure window in which both keys may exist or the operation may be incomplete.

For large datasets, migration workflows should support retries, destination verification, and recovery from partial completion.

## Storage Class and Cost Traps

### Misconception: The cheapest storage class is always the most economical

**Incorrect:** Choose the storage class with the lowest price per stored gigabyte.

**Correct:** Total cost can include storage, retrieval, requests, lifecycle transitions, minimum storage duration, restoration, and data transfer.

A frequently accessed workload can become more expensive when placed in a class with retrieval charges. An archive with strict immediate-access requirements may also be unsuitable for a class requiring restoration.

Evaluate actual access patterns and business latency requirements before changing classes.

### Misconception: Lifecycle policies immediately move or delete objects

**Incorrect:** An object is transitioned or expired at the exact moment its configured lifecycle age is reached.

**Correct:** Lifecycle rules define eligibility for actions, and execution is asynchronous. Object age, eligibility criteria, versioning, retention protections, and supported transition paths affect the result.

Use lifecycle rules for automated management, but do not design time-critical business operations around the assumption that an action executes at an exact instant.

### Misconception: Deleting visible files removes all associated storage costs

**Incorrect:** An empty-looking prefix means every associated object and stored version has been removed.

**Correct:** Stored noncurrent versions, delete markers, and incomplete multipart uploads may remain and incur charges. Console folder views do not always reveal the entire recovery or storage state.

Inspect object versions and multipart uploads when investigating unexpected storage usage. Before destructive cleanup, validate the scope and understand retention requirements.

### Misconception: Replication is free and has no operational cost

**Incorrect:** Enabling replication only adds an automatic copy with no extra cost or monitoring needs.

**Correct:** Replication can incur destination storage charges, request charges, and applicable data-transfer or encryption costs. Replication delay and failures also create operational risk.

Monitor replication status and define what should happen when objects remain pending or fail replication. Account for the storage and recovery behavior of both source and destination.

## Request Signing and Endpoint Traps

### Misconception: Any valid AWS credentials can be used with any Region or endpoint

**Incorrect:** Authentication succeeds as long as the access key and secret key are valid.

**Correct:** S3 requests are signed using AWS Signature Version 4 under the applicable signing context. The Region, endpoint, canonical request, headers, credentials, and signing details must match the actual request.

A Region mismatch, altered request headers, or a modified presigned URL can cause request-signing failures even when the credentials themselves are valid.

When diagnosing `SignatureDoesNotMatch` or redirect errors, verify:
- The bucket's actual Region.
- The endpoint and signing Region.
- System clock accuracy where relevant.
- Required signed headers and query parameters.
- Whether a proxy, client, or browser altered the request.

Do not respond to every signing failure by rotating valid credentials.

### Misconception: A bucket's Region can be changed after creation

**Incorrect:** Moving a bucket to another Region is a configuration-only update.

**Correct:** A bucket's Region is selected at creation and cannot simply be changed. A cross-Region migration requires creating a destination bucket and moving or replicating the data using an appropriate procedure.

The migration must also account for application references, policies, encryption keys, logging, replication, lifecycle settings, and cutover behavior.

### Misconception: CloudTrail records every S3 object operation automatically in every configuration

**Incorrect:** Any S3 GET, PUT, or DELETE will necessarily appear in the default CloudTrail event history.

**Correct:** CloudTrail management events and S3 object-level data events have different coverage. Object-level data events must be configured appropriately for the intended resources and operations.

For investigation and audit readiness, verify which event categories are enabled, the selected resources, delivery configuration, retention, and applicable cost.

S3 server access logging is another option for request-level visibility, with its own delivery and operational considerations.

## Architecture and Deployment Traps

### Misconception: Static website hosting on S3 automatically provides HTTPS

**Incorrect:** Enabling S3 static website hosting provides a complete public HTTPS website architecture.

**Correct:** S3 website endpoints support website hosting behavior but do not themselves provide HTTPS. A common production design uses CloudFront for HTTPS delivery and a private S3 REST origin protected with Origin Access Control.

The correct architecture depends on whether the application needs website-endpoint behavior, private origin access, custom domains, caching, and controlled deployment workflows.

### Misconception: S3 and PostgreSQL updates can be committed together

**Incorrect:** A successful upload and database commit are one atomic operation because both services are reliable.

**Correct:** There is no general transaction spanning the two services. The application must handle partial success.

For example, an upload may complete while a database transaction fails. Conversely, a database record may be created before an upload fails.

Use durable upload states, idempotency, reconciliation, and explicit cleanup or compensation logic. Avoid assuming that a single try/except block makes cross-service operations atomic.

### Misconception: Terraform can safely delete an S3 bucket just because the resource is removed from configuration

**Incorrect:** Removing an S3 resource from Terraform is an ordinary, harmless configuration change.

**Correct:** Destruction may be blocked by stored objects, object versions, Object Lock retention, or other service constraints. Successfully deleting a bucket can also irreversibly remove required data if safeguards are inadequate.

Before destructive changes:
- Inspect the Terraform plan.
- Verify environment and account identity.
- Confirm backup and retention requirements.
- Understand the treatment of all object versions and delete markers.
- Use lifecycle and resource-protection controls where appropriate.
- Test teardown in non-production environments.

Infrastructure-as-code tools manage resource configuration; they do not eliminate the need for data-retention and recovery design.

## Interview Practice: Explain the Correct Behavior

Use the following questions to test whether you can reason beyond definitions.

| Interview question | Strong answer should mention |
|---|---|
| Can a GET immediately after a successful PUT return stale object data? | Strong read-after-write consistency, scoped to completed operations |
| Does S3 provide a transaction across several object writes? | No general multi-object transaction; use a publication or workflow protocol |
| Does deleting a key permanently erase all its versions? | Delete markers, version-specific deletion, and retention controls |
| Does replication guarantee destination readiness immediately after a source write? | Asynchronous replication, status verification, and recovery planning |
| Are S3 event notifications exactly once and ordered? | At-least-once delivery, possible duplicates, and idempotent consumers |
| Does a `403` necessarily mean `s3:GetObject` is missing? | Complete S3 authorization evaluation, request context, and possible KMS authorization failures |
| Is an ETag always the MD5 checksum of an object? | Multipart and other cases where that assumption is invalid |
| Does a presigned URL become unusable only at its configured expiration? | Signing credentials may expire or be revoked earlier; bearer-token risk |
| Does S3 Versioning replace independent backups? | Version retention limits, privileged deletion risks, and restore testing |
| Does encrypting an object make it private? | Encryption and authorization are separate controls |
| Are S3 folders equivalent to physical directories? | General purpose buckets use object keys and prefixes; directory buckets differ |
| Does selecting the lowest storage price guarantee the lowest total cost? | Retrieval, requests, transitions, minimum duration, and restore costs |
| Does an S3 website endpoint directly provide HTTPS? | Website endpoint limitations and CloudFront-based alternatives |
| Does a valid AWS access key guarantee a valid signed request? | SigV4 context, endpoint, Region, headers, and credentials |

## Practical Verification Commands

The following commands help confirm service behavior rather than relying on assumptions. Run them only against an authorized test bucket.

Inspect bucket versioning:

```bash
aws s3api get-bucket-versioning \
  --bucket "$BUCKET"
```

Inspect bucket encryption:

```bash
aws s3api get-bucket-encryption \
  --bucket "$BUCKET"
```

Inspect an object's current metadata:

```bash
aws s3api head-object \
  --bucket "$BUCKET" \
  --key "test/sample.txt"
```

List object versions and delete markers:

```bash
aws s3api list-object-versions \
  --bucket "$BUCKET" \
  --prefix "test/sample.txt"
```

Inspect replication configuration:

```bash
aws s3api get-bucket-replication \
  --bucket "$BUCKET"
```

Inspect incomplete multipart uploads:

```bash
aws s3api list-multipart-uploads \
  --bucket "$BUCKET"
```

A successful configuration inspection does not prove that end-to-end recovery, authorization, replication, or application processing works. Validate the corresponding behavior with controlled tests.

## Key Takeaways

- Distinguish S3 guarantees from application guarantees: strong consistency does not provide multi-object transactions, exactly-once events, or synchronous replication.
- Treat versioning, replication, encryption, and presigned URLs as separate mechanisms with specific limitations rather than complete solutions to recovery or security.
- Design event-driven consumers and cross-service workflows for duplicate delivery, retries, partial failure, and reconciliation.
- Base performance, storage-class, and architecture decisions on access patterns, failure requirements, and total operational cost rather than a single headline metric.
- In interviews, explain not only what S3 supports, but also the assumptions that fail, the evidence needed to diagnose a problem, and how the production design prevents recurrence.