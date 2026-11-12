# 05- Versioning and Lifecycle Templates

## Overview

Amazon S3 versioning and lifecycle management are complementary mechanisms for controlling object history, storage retention, and long-term storage costs.

When managed through AWS CloudFormation, these capabilities become part of the infrastructure definition. This provides repeatable configuration across environments, reviewable changes, and consistent deployment through CI/CD pipelines.

Versioning preserves multiple versions of an object under the same key. Lifecycle rules automate actions against current and noncurrent versions, including storage transitions, expiration, and incomplete multipart upload cleanup.

A production implementation should treat versioning and lifecycle configuration as a coordinated retention policy rather than independent bucket settings.

This document covers:

- Configuring S3 versioning through CloudFormation.
- Defining lifecycle rules and filters.
- Transitioning current and noncurrent object versions.
- Managing delete markers and expired objects.
- Cleaning up incomplete multipart uploads.
- Deploying and validating lifecycle configurations.
- Handling retention, cost, and operational considerations.

Detailed encryption, IAM, and replication configurations belong in their dedicated CloudFormation documents.

## S3 Versioning Fundamentals

### What Versioning Provides

S3 Versioning maintains multiple variants of an object in the same bucket. Each version is associated with a version ID.

When versioning is enabled, uploading an object using an existing key creates a new version instead of permanently replacing the previous version.

For example:

```text
Bucket: application-data

Object key: documents/report.pdf

Versions:
  Version A: report.pdf
  Version B: report.pdf
  Version C: report.pdf
```

Each version can be independently retrieved using its version ID.

Versioning is useful for:

- Recovering accidentally overwritten objects.
- Recovering from accidental deletion.
- Maintaining historical object states.
- Supporting application-level rollback.
- Preserving data for audit and recovery workflows.

Versioning does not replace backups or replication. It provides object history within the same bucket and Region.

### Versioning States

An S3 bucket supports three versioning states.

| State | Behavior |
|---|---|
| Never enabled | Objects are not versioned. |
| Enabled | New object writes receive unique version IDs. |
| Suspended | New writes use the null version ID; existing versions remain available. |

Versioning is configured through the bucket's `VersioningConfiguration`.

```yaml
VersioningConfiguration:
  Status: Enabled
```

Suspending versioning does not remove previously stored versions.

It also does not restore the bucket to an unversioned state. Existing historical versions remain until explicitly deleted or expired through lifecycle configuration.

### Delete Markers

Deleting an object without specifying a version ID in a versioning-enabled bucket normally creates a delete marker.

The delete marker becomes the current version, making the object appear deleted in ordinary key-based requests.

The previous object versions remain stored.

```text
Before deletion:

report.pdf
  Version C (current)
  Version B
  Version A

After deletion:

report.pdf
  Delete marker (current)
  Version C
  Version B
  Version A
```

To restore the object, remove the delete marker or copy an earlier version into a new current version.

A permanent version deletion requires specifying the version ID.

This distinction is important when implementing retention policies and calculating storage costs.

### Versioning and CloudFormation

CloudFormation manages versioning through `AWS::S3::Bucket`.

```yaml
Resources:
  ApplicationBucket:
    Type: AWS::S3::Bucket
    Properties:
      VersioningConfiguration:
        Status: Enabled
```

Versioning is a bucket-level configuration. It does not need to be configured separately for each object or prefix.

Production considerations:

- Enable versioning before storing data that requires recovery protection.
- Avoid suspending versioning without a documented operational reason.
- Monitor noncurrent-version storage growth.
- Define lifecycle expiration for historical versions where retention requirements permit.
- Protect buckets and historical data from accidental infrastructure deletion.
- Coordinate versioning changes with replication and lifecycle policies.

## Lifecycle Management Fundamentals

### What Lifecycle Management Does

S3 Lifecycle automatically applies actions to objects based on age, filters, and version state.

It helps manage storage costs and retention without requiring application code to periodically enumerate and modify objects.

Lifecycle rules can perform:

- Storage-class transitions.
- Current-version expiration.
- Noncurrent-version transitions.
- Noncurrent-version expiration.
- Expired delete-marker cleanup.
- Incomplete multipart upload abortion.

Lifecycle policies are particularly useful for:

- Application logs.
- Archived documents.
- Historical reports.
- Uploaded media.
- Data lake datasets.
- Backup objects.
- Temporary processing artifacts.

Lifecycle execution is asynchronous. A rule becoming eligible does not mean the corresponding object is transitioned or deleted immediately.

Applications must not depend on lifecycle execution at an exact timestamp.

### Lifecycle Rule Structure

A lifecycle rule contains a status, optional filter, and one or more lifecycle actions.

```yaml
LifecycleConfiguration:
  Rules:
    - Id: ArchiveApplicationLogs
      Status: Enabled
      Filter:
        Prefix: logs/
      Transitions:
        - StorageClass: STANDARD_IA
          TransitionInDays: 30
```

| Property | Purpose |
|---|---|
| `Id` | Identifies the lifecycle rule. |
| `Status` | Enables or disables the rule. |
| `Filter` | Selects objects affected by the rule. |
| `Transitions` | Changes the storage class of current objects. |
| `Expiration` | Expires current objects. |
| `NoncurrentVersionTransitions` | Transitions historical versions. |
| `NoncurrentVersionExpiration` | Expires historical versions. |
| `AbortIncompleteMultipartUpload` | Removes incomplete multipart uploads. |
| `ExpiredObjectDeleteMarker` | Removes eligible expired delete markers. |

A bucket can contain multiple lifecycle rules. Give each rule a descriptive ID and avoid overlapping rules with conflicting retention intentions.

## Storage-Class Transitions

### Current-Version Transitions

A lifecycle transition changes the storage class of an eligible current object version.

For example, application logs can move from S3 Standard to S3 Standard-IA after 30 days.

```yaml
Transitions:
  - StorageClass: STANDARD_IA
    TransitionInDays: 30
```

Common lifecycle storage-class values include:

| Storage class | CloudFormation value | Typical use |
|---|---|---|
| S3 Standard-IA | `STANDARD_IA` | Infrequently accessed data requiring millisecond retrieval. |
| S3 One Zone-IA | `ONEZONE_IA` | Re-creatable data where single-AZ storage is acceptable. |
| S3 Intelligent-Tiering | `INTELLIGENT_TIERING` | Data with unpredictable access patterns. |
| S3 Glacier Instant Retrieval | `GLACIER_IR` | Archive data requiring millisecond retrieval. |
| S3 Glacier Flexible Retrieval | `GLACIER` | Archive data where retrieval delay is acceptable. |
| S3 Glacier Deep Archive | `DEEP_ARCHIVE` | Long-term archival with infrequent retrieval. |

Storage-class selection should account for:

- Retrieval frequency.
- Retrieval latency requirements.
- Minimum storage duration.
- Minimum billable object size.
- Retrieval and request charges.
- Availability requirements.
- Regional and service-specific constraints.

A transition is not automatically a cost optimization. Frequently accessed objects may become more expensive after moving to an archival class because of retrieval charges.

### Transition Eligibility

S3 lifecycle transitions are subject to service restrictions.

For example:

- Standard-IA and One Zone-IA have minimum storage-duration and object-size considerations.
- Glacier classes introduce retrieval latency and retrieval charges.
- Objects smaller than 128 KB are generally not transitioned by default to most storage classes through lifecycle policies.
- Some transition paths and timing combinations are restricted.

Validate the applicable S3 lifecycle constraints before deploying a policy. Do not assume that every object becomes eligible exactly on its configured transition day.

## Current Object Expiration

### Expiration in Versioned Buckets

In an unversioned bucket, lifecycle expiration permanently removes an eligible object.

In a versioning-enabled bucket, expiration of a current object normally creates a delete marker.

The previous object version becomes noncurrent and remains stored until another lifecycle action removes it.

Example:

```yaml
Expiration:
  Days: 365
```

This rule does not guarantee permanent removal of all versions after 365 days.

For permanent historical-version cleanup, configure `NoncurrentVersionExpiration` separately.

### Retention Design

A production retention policy should distinguish between:

- Current object retention.
- Historical version retention.
- Delete-marker cleanup.
- Compliance or legal retention requirements.

For example:

```text
Current object:
  Retain for 365 days.

Noncurrent versions:
  Retain for 90 additional days.

Expired delete markers:
  Remove when no object versions remain.
```

This approach separates application-visible expiration from historical-version cleanup.

Do not use lifecycle expiration as a substitute for S3 Object Lock or a compliance retention mechanism.

## Noncurrent Version Management

### Noncurrent Version Transitions

When a new object version replaces an existing version, the previous version becomes noncurrent.

Lifecycle policies can transition these historical versions to cheaper storage classes.

```yaml
NoncurrentVersionTransitions:
  - StorageClass: GLACIER
    TransitionInDays: 30
```

This is useful for documents and records where historical versions must remain available but are rarely retrieved.

### Noncurrent Version Expiration

Historical versions can be permanently deleted after a configured retention period.

```yaml
NoncurrentVersionExpiration:
  NoncurrentDays: 90
```

This permanently removes eligible noncurrent versions.

Use this action carefully because deleting a historical version removes that recovery point.

### NewerNoncurrentVersions

The `NewerNoncurrentVersions` property provides an additional version-count condition.

```yaml
NoncurrentVersionExpiration:
  NoncurrentDays: 90
  NewerNoncurrentVersions: 5
```

The object must satisfy both the age and newer-version conditions before expiration.

When using `NewerNoncurrentVersions`, include a lifecycle `Filter`. AWS also applies limits to the supported count value.

A retention policy using this property should be tested against realistic object-update patterns.

### Version Retention Example

```yaml
LifecycleConfiguration:
  Rules:
    - Id: RetainHistoricalVersions
      Status: Enabled
      Filter:
        Prefix: documents/
      NoncurrentVersionTransitions:
        - StorageClass: GLACIER
          TransitionInDays: 30
      NoncurrentVersionExpiration:
        NoncurrentDays: 180
```

This configuration:

1. Selects objects under `documents/`.
2. Transitions eligible historical versions to Glacier Flexible Retrieval.
3. Expires eligible historical versions after 180 days.

The transition and expiration rules should be evaluated together. A version should not be scheduled for deletion before the intended archival retention period has elapsed.

## Expired Delete Marker Cleanup

An expired delete marker is a delete marker with no remaining object versions.

Lifecycle can remove these markers automatically.

```yaml
Expiration:
  ExpiredObjectDeleteMarker: true
```

Use a separate lifecycle rule for this action.

`ExpiredObjectDeleteMarker` cannot be combined with `Expiration` or `Tags` in the same rule. A separate rule makes the configuration easier to validate and maintain.

Example:

```yaml
LifecycleConfiguration:
  Rules:
    - Id: RemoveExpiredDeleteMarkers
      Status: Enabled
      Filter:
        Prefix: documents/
      Expiration:
        ExpiredObjectDeleteMarker: true
```

This action does not delete active object versions. It only removes eligible expired delete markers.

## Incomplete Multipart Upload Cleanup

Multipart uploads allow large objects to be uploaded in independent parts.

If an upload is interrupted before completion, uploaded parts can remain stored and incur charges.

Lifecycle can automatically abort incomplete multipart uploads.

```yaml
AbortIncompleteMultipartUpload:
  DaysAfterInitiation: 7
```

A typical rule is:

```yaml
LifecycleConfiguration:
  Rules:
    - Id: CleanupIncompleteUploads
      Status: Enabled
      Filter:
        Prefix: uploads/
      AbortIncompleteMultipartUpload:
        DaysAfterInitiation: 7
```

The cleanup action:

- Aborts eligible incomplete multipart uploads.
- Releases storage occupied by their uploaded parts.
- Does not delete successfully completed objects.

Choose the cleanup interval based on expected upload duration and retry behavior. A short interval may interfere with legitimate long-running upload workflows.

## Lifecycle Filters

Lifecycle filters determine which objects a rule affects.

### Prefix Filter

A prefix filter targets objects under a logical key prefix.

```yaml
Filter:
  Prefix: logs/
```

Example object keys:

```text
logs/api/2026/10/01/app.log
logs/worker/2026/10/01/worker.log
documents/report.pdf
```

Only objects under `logs/` match this filter.

Prefixes are key-name conventions, not physical directories.

### Tag Filter

Lifecycle policies can select objects using tags.

```yaml
Filter:
  Tag:
    Key: retention
    Value: archive
```

Tags are useful when lifecycle requirements depend on business classification rather than object location.

For example:

```text
retention=archive
data-classification=internal
department=finance
```

Object tags can be changed independently of object keys, which makes them useful for flexible retention workflows.

### Object Size Filters

Lifecycle rules can filter objects by size.

```yaml
Filter:
  ObjectSizeGreaterThan: 1048576
```

This selects objects larger than 1 MiB.

A maximum-size filter can also be used:

```yaml
Filter:
  ObjectSizeLessThan: 104857600
```

For combined size constraints:

```yaml
Filter:
  And:
    ObjectSizeGreaterThan: 1048576
    ObjectSizeLessThan: 104857600
    Prefix: uploads/
```

The example selects objects under `uploads/` whose sizes are between the specified boundaries.

### Combining Filters

An `And` filter supports multiple conditions.

```yaml
Filter:
  And:
    Prefix: reports/
    Tags:
      - Key: environment
        Value: production
      - Key: retention
        Value: archive
```

This rule applies only when all specified conditions match.

Use combined filters when lifecycle behavior depends on both object location and business metadata.

## Complete CloudFormation Versioning and Lifecycle Template

The following template creates a versioned S3 bucket with:

- S3-managed encryption.
- Public access blocking.
- Object ownership enforcement.
- Current-object transitions.
- Noncurrent-version transitions and expiration.
- Expired delete-marker cleanup.
- Incomplete multipart upload cleanup.
- Configurable retention parameters.

The template focuses on versioning and lifecycle configuration. Production access policies and SSE-KMS configuration should be managed through the dedicated security template.

### `s3-versioning-lifecycle.yaml`

```yaml
AWSTemplateFormatVersion: "2010-09-09"

Description: >
  Versioned S3 bucket with lifecycle transitions,
  historical version retention, and multipart cleanup.

Parameters:
  BucketName:
    Type: String
    Description: Globally unique S3 bucket name.
    AllowedPattern: "^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$"

  Environment:
    Type: String
    Default: dev
    AllowedValues:
      - dev
      - staging
      - production

  CurrentTransitionDays:
    Type: Number
    Default: 90
    MinValue: 30

  NoncurrentTransitionDays:
    Type: Number
    Default: 30
    MinValue: 1

  NoncurrentExpirationDays:
    Type: Number
    Default: 180
    MinValue: 1

  MultipartCleanupDays:
    Type: Number
    Default: 7
    MinValue: 1

Resources:
  ApplicationBucket:
    Type: AWS::S3::Bucket
    DeletionPolicy: Retain
    UpdateReplacePolicy: Retain

    Properties:
      BucketName: !Ref BucketName

      Tags:
        - Key: Environment
          Value: !Ref Environment
        - Key: ManagedBy
          Value: CloudFormation

      OwnershipControls:
        Rules:
          - ObjectOwnership: BucketOwnerEnforced

      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true

      VersioningConfiguration:
        Status: Enabled

      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256

      LifecycleConfiguration:
        Rules:
          - Id: ArchiveCurrentObjects
            Status: Enabled
            Filter:
              Prefix: logs/
            Transitions:
              - StorageClass: STANDARD_IA
                TransitionInDays: !Ref CurrentTransitionDays
              - StorageClass: GLACIER
                TransitionInDays: 180

          - Id: ManageHistoricalVersions
            Status: Enabled
            Filter:
              Prefix: documents/
            NoncurrentVersionTransitions:
              - StorageClass: GLACIER
                TransitionInDays: !Ref NoncurrentTransitionDays
            NoncurrentVersionExpiration:
              NoncurrentDays: !Ref NoncurrentExpirationDays

          - Id: RemoveExpiredDeleteMarkers
            Status: Enabled
            Filter:
              Prefix: documents/
            Expiration:
              ExpiredObjectDeleteMarker: true

          - Id: CleanupIncompleteMultipartUploads
            Status: Enabled
            Filter:
              Prefix: uploads/
            AbortIncompleteMultipartUpload:
              DaysAfterInitiation: !Ref MultipartCleanupDays

Outputs:
  BucketName:
    Description: Created S3 bucket name.
    Value: !Ref ApplicationBucket

  BucketArn:
    Description: Created S3 bucket ARN.
    Value: !GetAtt ApplicationBucket.Arn
```

### Template Design Considerations

The template uses `DeletionPolicy: Retain` and `UpdateReplacePolicy: Retain` to reduce the risk of accidental data loss during stack deletion or resource replacement.

These policies do not prevent lifecycle expiration or explicit object deletion.

The bucket uses SSE-S3 for the example. Replace this with the appropriate SSE-KMS configuration when customer-managed encryption keys, key policies, or cross-account encryption requirements apply.

The lifecycle configuration is intentionally prefix-based. For more complex retention policies, use object tags or combined filters.

The template uses a 30-day default for Standard-IA transition eligibility. Validate object-size, minimum-duration, and transition constraints against the intended workload before deployment.

The `CurrentTransitionDays` parameter controls the Standard-IA transition. The Glacier transition is fixed at 180 days in this example and should be reviewed if the retention policy changes.

## Environment-Specific Configuration

Different environments often require different retention periods.

For example:

| Environment | Current object retention | Historical version retention | Multipart cleanup |
|---|---:|---:|---:|
| Development | 30 days | 30 days | 3 days |
| Staging | 60 days | 60 days | 5 days |
| Production | 365 days | 180 days | 7 days |

These values are examples, not universal retention recommendations.

Use parameter files to keep environment-specific configuration outside the template.

### Development Parameters

`dev-parameters.json`

```json
[
  {
    "ParameterKey": "BucketName",
    "ParameterValue": "company-app-data-dev"
  },
  {
    "ParameterKey": "Environment",
    "ParameterValue": "dev"
  },
  {
    "ParameterKey": "CurrentTransitionDays",
    "ParameterValue": "30"
  },
  {
    "ParameterKey": "NoncurrentTransitionDays",
    "ParameterValue": "30"
  },
  {
    "ParameterKey": "NoncurrentExpirationDays",
    "ParameterValue": "30"
  },
  {
    "ParameterKey": "MultipartCleanupDays",
    "ParameterValue": "3"
  }
]
```

### Production Parameters

`production-parameters.json`

```json
[
  {
    "ParameterKey": "BucketName",
    "ParameterValue": "company-app-data-production"
  },
  {
    "ParameterKey": "Environment",
    "ParameterValue": "production"
  },
  {
    "ParameterKey": "CurrentTransitionDays",
    "ParameterValue": "90"
  },
  {
    "ParameterKey": "NoncurrentTransitionDays",
    "ParameterValue": "30"
  },
  {
    "ParameterKey": "NoncurrentExpirationDays",
    "ParameterValue": "180"
  },
  {
    "ParameterKey": "MultipartCleanupDays",
    "ParameterValue": "7"
  }
]
```

Keep parameter files under version control when they contain non-sensitive configuration. Never place credentials or secrets in CloudFormation parameters or source-controlled files.

## Lifecycle Rule Design for Different Workloads

### Application Logs

Logs are frequently written and become less valuable for immediate access as they age.

A typical policy might be:

```text
logs/
  Current objects:
    Standard initially
    Standard-IA after 30 days
    Glacier Flexible Retrieval after 180 days
    Expire after the approved retention period
```

The retention period must align with incident investigation, audit, and compliance requirements.

### User Documents

Documents may require historical recovery.

```text
documents/
  Current objects:
    Remain in Standard or Intelligent-Tiering

  Historical versions:
    Transition to Glacier Flexible Retrieval
    Expire after the approved recovery window
```

Do not transition documents to archival storage if the application requires immediate retrieval without considering restoration latency.

### Temporary Uploads

Temporary uploads should have a defined cleanup policy.

```text
uploads/
  Incomplete multipart uploads:
    Abort after 7 days

  Completed temporary objects:
    Expire according to application retention requirements
```

Multipart cleanup and completed-object expiration solve different problems. Configure both when the workload requires them.

### Data Lake Objects

Data lake lifecycle policies should account for downstream analytics and reprocessing requirements.

For example:

```text
raw/
  Retain source data according to governance requirements.

processed/
  Retain derived outputs according to rebuildability.

temporary/
  Expire intermediate data after a short retention period.
```

Do not delete raw source data merely because processed outputs exist. Confirm that the source data can be reconstructed or is no longer required.

## Lifecycle Evaluation and Rule Conflicts

Lifecycle rules are evaluated by S3 asynchronously.

An object can match more than one lifecycle rule. When actions overlap, S3 applies documented lifecycle precedence and eligibility behavior.

Avoid designing policies that depend on ambiguous interactions between multiple rules.

A practical design approach is:

1. Define retention requirements by object category.
2. Assign each category a prefix or tag.
3. Keep lifecycle rules narrowly scoped.
4. Separate current-version and noncurrent-version retention.
5. Validate transitions against minimum storage-duration and object-size constraints.
6. Test the policy against representative object histories.
7. Monitor actual storage-class distribution and expiration behavior.

Do not assume that a lifecycle action runs at midnight on the configured day.

Lifecycle rules are asynchronous management operations, not real-time schedulers.

## CloudFormation Deployment Workflow

### Validate the Template

Use the AWS CLI to validate the template syntax.

```bash
aws cloudformation validate-template \
  --template-body file://s3-versioning-lifecycle.yaml
```

For stronger static validation, use tools such as `cfn-lint`.

```bash
cfn-lint s3-versioning-lifecycle.yaml
```

Validation does not guarantee that every lifecycle combination is valid or that the deployment will succeed in the target account and Region.

### Create the Stack

```bash
aws cloudformation create-stack \
  --stack-name application-s3-lifecycle \
  --template-body file://s3-versioning-lifecycle.yaml \
  --parameters file://dev-parameters.json \
  --capabilities CAPABILITY_IAM
```

The example does not define IAM resources, so `CAPABILITY_IAM` is unnecessary for this specific template. Omit it unless the deployed template actually creates IAM resources.

### Monitor Deployment

```bash
aws cloudformation describe-stacks \
  --stack-name application-s3-lifecycle
```

Inspect resource events:

```bash
aws cloudformation describe-stack-events \
  --stack-name application-s3-lifecycle
```

### Update the Stack

```bash
aws cloudformation update-stack \
  --stack-name application-s3-lifecycle \
  --template-body file://s3-versioning-lifecycle.yaml \
  --parameters file://production-parameters.json
```

For production, create and review a change set before applying lifecycle or retention changes.

```bash
aws cloudformation create-change-set \
  --stack-name application-s3-lifecycle \
  --change-set-name update-lifecycle-retention \
  --change-set-type UPDATE \
  --template-body file://s3-versioning-lifecycle.yaml \
  --parameters file://production-parameters.json
```

Review the change set:

```bash
aws cloudformation describe-change-set \
  --stack-name application-s3-lifecycle \
  --change-set-name update-lifecycle-retention
```

Execute only after reviewing the resource changes and their data-retention implications.

```bash
aws cloudformation execute-change-set \
  --stack-name application-s3-lifecycle \
  --change-set-name update-lifecycle-retention
```

## Verifying Versioning and Lifecycle Configuration

### Check Versioning

```bash
aws s3api get-bucket-versioning \
  --bucket company-app-data-production
```

Expected configuration:

```json
{
  "Status": "Enabled"
}
```

### Check Lifecycle Rules

```bash
aws s3api get-bucket-lifecycle-configuration \
  --bucket company-app-data-production
```

Inspect the returned rules for:

- Correct rule IDs.
- Enabled status.
- Correct filters.
- Transition dates.
- Noncurrent version retention.
- Expired delete-marker cleanup.
- Multipart upload cleanup.

### Inspect Object Versions

```bash
aws s3api list-object-versions \
  --bucket company-app-data-production \
  --prefix documents/
```

The response includes object versions and delete markers.

For large buckets, paginate the response rather than assuming a single request returns all versions.

### Upload Multiple Versions

```bash
echo "First version" > report.txt

aws s3api put-object \
  --bucket company-app-data-production \
  --key documents/report.txt \
  --body report.txt
```

Modify and upload the same key:

```bash
echo "Second version" > report.txt

aws s3api put-object \
  --bucket company-app-data-production \
  --key documents/report.txt \
  --body report.txt
```

List the versions:

```bash
aws s3api list-object-versions \
  --bucket company-app-data-production \
  --prefix documents/report.txt
```

### Test Delete-Marker Behavior

```bash
aws s3api delete-object \
  --bucket company-app-data-production \
  --key documents/report.txt
```

Inspect the version history:

```bash
aws s3api list-object-versions \
  --bucket company-app-data-production \
  --prefix documents/report.txt
```

The delete operation normally creates a delete marker when versioning is enabled.

### Retrieve a Specific Version

```bash
aws s3api get-object \
  --bucket company-app-data-production \
  --key documents/report.txt \
  --version-id VERSION_ID \
  restored-report.txt
```

Replace `VERSION_ID` with an actual version ID returned by S3.

This is a useful recovery verification step for versioned application data.

## Lifecycle Testing Strategy

Lifecycle actions are asynchronous and should not be tested by assuming that an object will transition or expire immediately after deployment.

A reliable test strategy separates configuration validation from actual lifecycle execution.

| Test area | Verification method |
|---|---|
| Versioning | Upload the same key multiple times and inspect version IDs. |
| Delete markers | Delete an object and inspect `DeleteMarkers`. |
| Current transitions | Inspect lifecycle configuration and later verify object storage class. |
| Noncurrent transitions | Create multiple versions and inspect historical versions over time. |
| Noncurrent expiration | Verify eligible historical versions are removed after lifecycle processing. |
| Multipart cleanup | Initiate an incomplete upload and inspect multipart upload state. |
| Delete-marker cleanup | Create a delete marker with no remaining object versions and verify eventual cleanup. |

Use a dedicated test bucket with short retention periods where supported.

Do not shorten production retention policies simply to make lifecycle tests complete faster.

### Inspect Multipart Uploads

```bash
aws s3api list-multipart-uploads \
  --bucket company-app-data-production
```

Inspect the parts of a specific upload:

```bash
aws s3api list-parts \
  --bucket company-app-data-production \
  --key uploads/example.bin \
  --upload-id UPLOAD_ID
```

Use a controlled test upload to verify cleanup behavior.

## Updating Lifecycle Configuration Safely

Lifecycle configuration is managed as a bucket-level configuration.

When CloudFormation updates `LifecycleConfiguration`, the resulting configuration should be reviewed as a complete policy.

Important considerations:

- Preserve existing lifecycle rules that remain required.
- Avoid replacing unrelated rules accidentally.
- Review changes to expiration and noncurrent-version retention.
- Check whether existing objects become eligible for new actions.
- Confirm that the policy does not conflict with legal retention or Object Lock.
- Verify the final deployed configuration using the S3 API.

A lifecycle policy change can affect objects that were uploaded before the deployment.

Do not assume that new rules apply only to objects created after the change.

## Security and Retention Considerations

Lifecycle and versioning are data-management controls, but they are not complete security controls.

Consider the following:

- Use least-privilege permissions for CloudFormation deployment roles.
- Restrict permissions that can suspend versioning or change lifecycle rules.
- Protect production buckets from accidental stack deletion.
- Use Object Lock where immutable retention is required.
- Coordinate lifecycle expiration with legal and regulatory requirements.
- Use SSE-KMS where customer-managed encryption keys are required.
- Ensure that KMS key retention is compatible with the retention period of encrypted objects.
- Audit infrastructure changes and object deletion activity.

A retained bucket whose KMS key is deleted can become inaccessible even though the objects remain in S3.

Similarly, a retained bucket does not protect objects from lifecycle expiration or explicit deletion.

## Monitoring and Cost Considerations

Versioning and lifecycle can materially affect storage costs.

A bucket may appear to contain a small number of current objects while retaining many historical versions.

Monitor:

- Current object storage.
- Noncurrent version storage.
- Storage-class distribution.
- Number of delete markers.
- Incomplete multipart upload storage.
- Lifecycle transition and expiration behavior.
- Replication status where replication is configured.

Useful operational mechanisms include:

- S3 Storage Lens for storage usage and trends.
- S3 Inventory for object-level reporting.
- CloudWatch metrics for bucket activity and request monitoring.
- Cost Explorer and cost allocation tags for expenditure analysis.

Lifecycle optimization should be based on measured access patterns and retention requirements.

For example, moving a frequently retrieved object to Glacier Flexible Retrieval may increase retrieval costs and introduce unacceptable latency.

## Common Mistakes and Production Pitfalls

### Assuming Versioning Prevents Deletion

Versioning preserves historical versions, but users and applications can still permanently delete specific versions.

**Avoidance:** Restrict `s3:DeleteObjectVersion` and audit privileged deletion operations.

### Assuming Expiration Permanently Deletes Versioned Objects

Current-version expiration generally creates a delete marker. Historical versions remain.

**Avoidance:** Configure noncurrent-version expiration separately.

### Ignoring Noncurrent Version Costs

Frequent object updates can produce large numbers of historical versions.

**Avoidance:** Monitor noncurrent storage and define an appropriate retention window.

### Using Lifecycle as a Real-Time Scheduler

Lifecycle processing is asynchronous and does not guarantee execution at an exact time.

**Avoidance:** Use application-level scheduling when an exact execution time is required.

### Applying Aggressive Expiration Rules

A lifecycle rule can affect existing objects, not only newly uploaded objects.

**Avoidance:** Review change sets and test the policy against representative object histories.

### Ignoring Storage-Class Constraints

Not all objects are suitable for every storage class.

**Avoidance:** Validate minimum duration, minimum object size, retrieval cost, and latency requirements.

### Deleting Historical Versions Without a Recovery Plan

Noncurrent-version expiration permanently removes eligible historical versions.

**Avoidance:** Align expiration with recovery objectives, backup requirements, and governance policies.

### Treating Bucket Retention as Object Retention

CloudFormation retention policies protect the bucket resource from automatic stack deletion. They do not prevent lifecycle expiration.

**Avoidance:** Manage infrastructure retention and object retention as separate controls.

### Forgetting Incomplete Multipart Uploads

Interrupted uploads can leave billable parts behind.

**Avoidance:** Configure `AbortIncompleteMultipartUpload` and monitor incomplete uploads.

### Replacing Existing Lifecycle Rules Accidentally

A new lifecycle configuration can unintentionally remove previously managed rules.

**Avoidance:** Treat lifecycle configuration as a complete bucket-level policy and review the entire resulting rule set.

## Production Best Practices

- Enable versioning for buckets that require object recovery or historical retention.
- Define current and noncurrent retention independently.
- Use descriptive lifecycle rule IDs and narrowly scoped filters.
- Use prefixes or tags to separate retention categories.
- Keep lifecycle expiration aligned with business and compliance requirements.
- Validate storage-class eligibility before deploying transitions.
- Configure incomplete multipart upload cleanup.
- Use Object Lock for immutable retention requirements.
- Protect production bucket resources from accidental deletion.
- Review CloudFormation change sets before changing expiration behavior.
- Monitor noncurrent version storage and lifecycle outcomes.
- Test recovery by retrieving an actual historical version.
- Maintain a documented rollback and data-recovery procedure.

## Key Takeaways

- S3 Versioning preserves object history, while lifecycle policies automate storage transitions and retention actions.
- Expiration in a versioned bucket generally creates a delete marker; noncurrent-version expiration is required to remove historical versions permanently.
- Lifecycle execution is asynchronous, so applications must not depend on exact transition or deletion timestamps.
- CloudFormation lifecycle changes can affect existing objects and should be reviewed through change sets and verified after deployment.
- Production retention policies must balance recovery requirements, compliance, storage-class constraints, and long-term storage costs.