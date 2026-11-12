# README

## Overview

This example provisions a versioned Amazon S3 source bucket and a destination bucket in a separate AWS Region, then configures Cross-Region Replication (CRR) using Terraform.

It demonstrates the infrastructure required for asynchronous replication between Regions:

- Source and destination S3 buckets.
- Versioning enabled on both buckets.
- Server-side encryption using SSE-S3 or optional SSE-KMS.
- S3 Block Public Access and Bucket Owner Enforced ownership.
- An IAM role assumed by the S3 replication service.
- Least-privilege replication permissions.
- A replication rule with configurable prefix filtering and destination storage class.
- Optional replication metrics and S3 Replication Time Control (RTC).

The example is intended for learning and validating a multi-Region replication configuration. Replication is not synchronous storage, automatic application failover, or a substitute for a tested disaster recovery strategy.

## Project Structure

```text
replicated-bucket/
└── main.tf
```

All Terraform declarations are contained in `main.tf`, including variables, providers, resources, data sources, locals, and outputs.

## Architecture

```mermaid
flowchart TB
    APP[Application or Backend Service]

    subgraph SOURCE["Source AWS Region"]
        SB[Source S3 Bucket]
        SV[Source Bucket Versioning]
        IAM[IAM Replication Role]
        POLICY[Replication IAM Policy]
    end

    subgraph DESTINATION["Destination AWS Region"]
        DB[Destination S3 Bucket]
        DV[Destination Bucket Versioning]
    end

    APP -->|Upload object| SB
    SB --> SV
    SV -->|Eligible object versions| IAM
    IAM --> POLICY
    IAM -->|Replicate object versions| DB
    DB --> DV

    SB -.->|Replication metrics and status| OBS[Monitoring]
```

### Component Responsibilities

| Component | Responsibility |
|---|---|
| Source bucket | Stores original objects and versions |
| Destination bucket | Stores replicated object versions in another Region |
| Bucket versioning | Enables S3 replication of object versions |
| IAM replication role | Provides permissions assumed by the S3 replication service |
| IAM replication policy | Grants source read and destination replication permissions |
| Replication configuration | Defines the destination, filters, storage class, and optional monitoring |
| KMS keys | Optionally encrypt source and replicated objects using customer-managed keys |

### Replication Flow

1. An application uploads an object to the source bucket.
2. S3 stores the object and creates a version because versioning is enabled.
3. S3 evaluates the configured replication rule.
4. The S3 replication service assumes the configured IAM role.
5. The role reads the eligible source object version.
6. S3 replicates the object to the destination bucket.
7. The destination bucket stores the replicated object version.
8. Replication status and metrics can be inspected when monitoring is enabled.

Replication is asynchronous. A successful source upload does not guarantee that the destination object is immediately available.

## Prerequisites

### Required Tools

| Tool | Requirement |
|---|---|
| Terraform | 1.5.0 or later |
| AWS CLI | Configured with valid credentials |
| AWS provider | HashiCorp AWS provider `~> 6.0` |
| AWS account | Permissions to create S3 buckets and IAM resources |
| AWS Regions | Two different Regions |

The example uses `use` of the default AWS credential chain through the provider. Do not place access keys or secret keys in Terraform source files.

### AWS Permissions

The deployment identity needs permissions to manage:

- S3 buckets and bucket configurations.
- Bucket versioning and encryption.
- Bucket ownership controls and public access blocks.
- S3 replication configurations.
- IAM roles, trust policies, and inline policies.
- Relevant KMS permissions when customer-managed keys are configured.

The deployment identity's permissions are separate from the permissions granted to the S3 replication role.

### Configure AWS Credentials

Using an AWS CLI profile:

```bash
aws configure --profile s3-replication
```

Verify the identity:

```bash
aws sts get-caller-identity --profile s3-replication
```

Use the profile for Terraform:

```powershell
$env:AWS_PROFILE = "s3-replication"
```

On Linux or macOS:

```bash
export AWS_PROFILE=s3-replication
```

## Configuration

The example declares all inputs in `main.tf`.

### Region Configuration

| Variable | Default | Description |
|---|---|---|
| `source_aws_region` | `ap-south-1` | Region containing the source bucket |
| `destination_aws_region` | `ap-southeast-1` | Region containing the replica bucket |

The destination Region must differ from the source Region for this CRR example.

### Bucket Configuration

| Variable | Required | Default | Description |
|---|---:|---|---|
| `source_bucket_name` | Yes | None | Globally unique source bucket name |
| `destination_bucket_name` | Yes | None | Globally unique destination bucket name |
| `force_destroy` | No | `false` | Whether Terraform may delete non-empty buckets |

Both bucket names must be globally unique across the applicable S3 namespace.

Keep `force_destroy = false` for production and protected data. A versioned bucket may contain historical versions and delete markers even when its current object listing appears empty.

### Encryption Configuration

| Variable | Default | Description |
|---|---|---|
| `source_kms_key_arn` | `null` | Optional source customer-managed KMS key |
| `destination_kms_key_arn` | `null` | Optional destination customer-managed KMS key |
| `bucket_key_enabled` | `true` | Enables S3 Bucket Keys for SSE-KMS |

When both KMS key variables are null, the example configures SSE-S3 using AES-256.

When SSE-KMS is configured:

- The source key must allow the replication role to decrypt source objects.
- The destination key must allow the replication role to encrypt replicated objects.
- KMS key policies must authorize the relevant principal.
- The destination replication configuration identifies the destination KMS key.
- The source selection criteria enables replication of SSE-KMS-encrypted objects.

The example requires a destination KMS key whenever a source KMS key is configured.

KMS key ARNs must refer to keys in the appropriate Regions. A source Region KMS key cannot be used as the destination Region's encryption key.

### Replication Configuration

| Variable | Default | Description |
|---|---|---|
| `replication_role_name` | `s3-cross-region-replication-role` | IAM role assumed by S3 |
| `replication_rule_id` | `cross-region-replication-rule` | Replication rule identifier |
| `replication_filter_prefix` | `""` | Prefix filter for eligible objects |
| `replication_enabled` | `true` | Enables or disables the rule |
| `delete_marker_replication_enabled` | `false` | Controls delete-marker replication |
| `destination_storage_class` | `STANDARD` | Storage class for replicated objects |

An empty prefix applies the rule to all eligible objects.

For example, setting:

```hcl
replication_filter_prefix = "documents/"
```

limits the rule to objects whose keys begin with `documents/`.

Delete-marker replication is disabled by default. It should be enabled only when the application's deletion semantics require it and the configured replication filter and S3 feature constraints support the intended behavior.

### Replication Monitoring

| Variable | Default | Description |
|---|---|---|
| `replication_metrics_enabled` | `true` | Enables replication metrics |
| `replication_time_control_enabled` | `false` | Enables S3 Replication Time Control |

Replication metrics expose replication progress and failure-related indicators for monitoring.

S3 Replication Time Control provides a 15-minute replication SLA for eligible objects. It is an additional-cost feature and should be enabled only when the workload requires the corresponding replication commitment.

RTC requires replication metrics. The Terraform configuration enforces this dependency.

### Tags

The `tags` map applies common tags to the buckets and supported IAM resources.

Update the default values to match your organization's tagging and cost-allocation standards.

## Deployment

### Initialize Terraform

Run from the `replicated-bucket` directory:

```bash
terraform init
```

This downloads the AWS provider and initializes the working directory.

### Format and Validate

```bash
terraform fmt -recursive
terraform validate
```

### Provide Input Variables

Create a `terraform.tfvars` file:

```hcl
source_aws_region      = "ap-south-1"
destination_aws_region = "ap-southeast-1"

source_bucket_name      = "your-org-s3-source-replication-example"
destination_bucket_name = "your-org-s3-destination-replication-example"

source_account_id = "123456789012"

force_destroy = false

source_kms_key_arn      = null
destination_kms_key_arn = null

replication_role_name = "s3-cross-region-replication-role"
replication_rule_id   = "cross-region-replication-rule"

replication_filter_prefix = ""
replication_enabled       = true

delete_marker_replication_enabled = false
destination_storage_class         = "STANDARD"

replication_metrics_enabled      = true
replication_time_control_enabled = false
```

Replace the bucket names and account ID with values for your AWS environment.

`source_account_id` must identify the account that owns the source bucket and replication role. The destination bucket in this example is also created in the same account, but in a different Region.

Do not commit a `terraform.tfvars` file containing sensitive values.

### Review the Execution Plan

```bash
terraform plan -out=tfplan
```

Inspect the plan before applying it. Confirm:

- The source and destination Regions are correct.
- Bucket names are unique and correctly assigned.
- Both buckets will have versioning enabled.
- Encryption settings match the intended design.
- The IAM trust policy and replication permissions are scoped to the source and destination buckets.
- The replication filter and destination storage class are correct.
- RTC is enabled only when required.

### Apply

```bash
terraform apply tfplan
```

Terraform provisions the buckets, their configurations, the IAM role and policy, and the replication configuration.

### Inspect Outputs

```bash
terraform output
```

Individual outputs can be inspected:

```bash
terraform output source_bucket_id
terraform output destination_bucket_id
terraform output replication_role_arn
terraform output replication_configuration_id
terraform output replication_rule_status
```

## Verification

### Verify Bucket Versioning

Source bucket:

```bash
aws s3api get-bucket-versioning \
  --bucket your-org-s3-source-replication-example \
  --region ap-south-1
```

Destination bucket:

```bash
aws s3api get-bucket-versioning \
  --bucket your-org-s3-destination-replication-example \
  --region ap-southeast-1
```

Both should report:

```json
{
  "Status": "Enabled"
}
```

### Verify Replication Configuration

```bash
aws s3api get-bucket-replication \
  --bucket your-org-s3-source-replication-example \
  --region ap-south-1
```

Inspect the returned configuration for:

- IAM role ARN.
- Rule identifier and status.
- Prefix filter.
- Destination bucket ARN.
- Destination storage class.
- Optional encryption configuration.
- Replication metrics and RTC settings.

### Verify Bucket Encryption

Source:

```bash
aws s3api get-bucket-encryption \
  --bucket your-org-s3-source-replication-example \
  --region ap-south-1
```

Destination:

```bash
aws s3api get-bucket-encryption \
  --bucket your-org-s3-destination-replication-example \
  --region ap-southeast-1
```

Confirm that the configured encryption algorithm and KMS key ARN match the intended configuration.

### Verify Public Access Block

```bash
aws s3api get-public-access-block \
  --bucket your-org-s3-source-replication-example \
  --region ap-south-1
```

Repeat for the destination bucket using its Region and name.

All four public-access block settings should be enabled.

### Verify Replication Role

```bash
aws iam get-role \
  --role-name s3-cross-region-replication-role
```

Inspect the trust relationship and confirm that the S3 service principal can assume the role under the configured source account and source bucket conditions.

Inspect the attached inline policy:

```bash
aws iam get-role-policy \
  --role-name s3-cross-region-replication-role \
  --policy-name s3-cross-region-replication-role-policy
```

### Test Object Replication

Upload a test object to the source bucket:

```bash
printf "S3 cross-region replication test\n" > replication-test.txt

aws s3api put-object \
  --bucket your-org-s3-source-replication-example \
  --key replication-tests/replication-test.txt \
  --body replication-test.txt \
  --region ap-south-1
```

Retrieve the source object's version ID:

```bash
aws s3api head-object \
  --bucket your-org-s3-source-replication-example \
  --key replication-tests/replication-test.txt \
  --region ap-south-1
```

Inspect the `ReplicationStatus` field when available. For a source object, `PENDING`, `COMPLETED`, or `FAILED` can indicate replication progress or outcome.

Replication is asynchronous. Allow time for the replication service to process the object.

Check the destination bucket:

```bash
aws s3api head-object \
  --bucket your-org-s3-destination-replication-example \
  --key replication-tests/replication-test.txt \
  --region ap-southeast-1
```

A successful destination lookup confirms that the object is available there. Compare object metadata and checksums where appropriate rather than assuming that a successful source upload proves replication completion.

### Verify Replicated Object Versions

List destination object versions:

```bash
aws s3api list-object-versions \
  --bucket your-org-s3-destination-replication-example \
  --prefix replication-tests/ \
  --region ap-southeast-1
```

Confirm that the expected object version is present.

### Important Limitation: Existing Objects

The replication configuration does not automatically replicate objects that existed in the source bucket before the rule was created.

Use S3 Batch Replication to replicate eligible existing objects. Plan this separately, including job permissions, manifests, completion reporting, and cost.

## Security Considerations

### Least-Privilege Replication Role

The IAM role is trusted by the S3 service and constrained using:

- `aws:SourceAccount`
- `aws:SourceArn`

Its inline policy grants the source read permissions and destination replication permissions required by the configured rule.

Do not reuse this role for unrelated application workloads.

### Bucket Security

Both buckets enforce:

- S3 Block Public Access.
- Bucket Owner Enforced object ownership.
- Server-side encryption.
- Versioning.

Application identities should receive only the S3 permissions required for their operations. The replication role should remain separate from application upload and download identities.

### KMS Permissions

S3 authorization and KMS authorization are separate permission layers.

For SSE-KMS replication, validate:

- Source key policy authorization for decryption.
- Destination key policy authorization for encryption.
- IAM permissions for the replication role.
- Key state and Region compatibility.
- Any applicable organizational controls, grants, or explicit denies.

An IAM policy allowing S3 replication does not by itself guarantee that KMS operations will succeed.

### Cross-Account Replication

This example creates both buckets in the same AWS account. For cross-account replication, additional configuration is required:

- A destination bucket policy granting the source replication role the required destination permissions.
- Appropriate KMS key policies and grants when SSE-KMS is used.
- Correct destination account ownership and replication ownership settings where required.

Do not assume that changing only the destination bucket ARN makes this example cross-account ready.

## Production Considerations

### Replication Is Not Automatic Failover

CRR asynchronously copies eligible object versions to another Region. It does not automatically redirect application traffic or guarantee that all writes are present in the destination Region during a failure.

A production disaster recovery design must separately address:

- Application deployment and service availability in the recovery Region.
- Database replication and consistency.
- DNS or traffic-routing changes.
- Credential and KMS key availability.
- Recovery point objective (RPO).
- Recovery time objective (RTO).
- Verification of replicated object availability.
- Controlled failback procedures.

### Replication Monitoring

Monitor replication metrics and object replication status.

Useful operational checks include:

- Objects with `PENDING` replication status.
- Objects with `FAILED` replication status.
- Replication latency.
- Bytes pending replication.
- Replication failures caused by IAM or KMS authorization.
- Destination bucket availability.

For RTC workloads, monitor the relevant replication metrics and alarms against the expected service commitment.

### Versioning and Deletion

Versioning is required on both buckets and must remain enabled for replication.

Replication does not make the destination a fully independent backup by itself. Delete-marker behavior, object retention, lifecycle expiration, and administrative deletion policies must be designed deliberately.

A deletion or lifecycle action in one Region should not be assumed to provide the recovery behavior required by the application.

### Cost Management

CRR can incur charges for:

- Replication requests.
- Data transfer between Regions.
- Destination storage.
- Destination storage-class minimum storage duration or retrieval charges where applicable.
- Replication metrics.
- Replication Time Control.
- KMS API requests.
- Monitoring and inventory services used by the broader solution.

Choose destination storage classes based on access patterns and recovery requirements, not storage price alone.

### Terraform State and Resource Ownership

This example manages the complete replication configuration for the source bucket through one `aws_s3_bucket_replication_configuration` resource.

Do not manage the same bucket's replication configuration independently through another Terraform resource or module. Conflicting ownership can cause configuration drift or overwrite behavior.

For production environments, use remote Terraform state with encryption, restricted access, and state locking. Keep state storage independently managed from the resources deployed by this example.

### Existing Object Recovery

If historical source objects must be available in the destination Region, create and monitor an S3 Batch Replication job. Validate the job's completion report and verify representative object versions before treating the destination as a recovery source.

## Common Mistakes

| Mistake | Impact | Prevention |
|---|---|---|
| Enabling replication without source versioning | Replication configuration cannot be used as intended | Enable versioning on both buckets |
| Forgetting destination versioning | Replication requirements are not satisfied | Enable destination versioning before configuring replication |
| Using the wrong Region for a KMS key | Replication encryption can fail | Use a destination-Region KMS key |
| Granting S3 permissions but not KMS permissions | SSE-KMS replication fails | Validate both IAM permissions and key policies |
| Assuming existing objects are replicated | Historical data is missing in the destination | Use S3 Batch Replication |
| Treating replication as synchronous | Applications may read stale or missing destination objects | Design around asynchronous replication |
| Treating CRR as automatic failover | Recovery procedures remain incomplete | Implement and test a separate DR runbook |
| Enabling RTC without metrics | Invalid configuration | Enable replication metrics with RTC |
| Setting `force_destroy = true` indiscriminately | Data may be permanently deleted during teardown | Keep it false for protected data |
| Sharing the replication role with applications | Expands the security boundary | Use dedicated workload identities |

## Troubleshooting

### Replication Configuration Errors

Inspect the source bucket configuration:

```bash
aws s3api get-bucket-replication \
  --bucket your-org-s3-source-replication-example \
  --region ap-south-1
```

Check:

- Source bucket versioning.
- Destination bucket versioning.
- Replication role ARN.
- Rule status and filter.
- Destination bucket ARN.
- Encryption configuration.

### Replication Status Is `FAILED`

Inspect the source object's replication status:

```bash
aws s3api head-object \
  --bucket your-org-s3-source-replication-example \
  --key replication-tests/replication-test.txt \
  --region ap-south-1
```

Investigate:

- IAM trust policy and role permissions.
- Destination bucket policy, if cross-account.
- Source and destination KMS key policies.
- Explicit denies from bucket policies, SCPs, or permission boundaries.
- Destination bucket configuration and availability.

Use CloudTrail and relevant S3 replication metrics to identify authorization or service-side failures.

### Destination Object Is Missing

First confirm that the source object is eligible for the replication rule.

Check:

- The object key matches the configured prefix.
- The rule is enabled.
- The object was created after replication was configured, or is included in a Batch Replication job.
- The source object's replication status.
- The destination bucket and Region.
- The role and KMS permissions.

Do not repeatedly upload duplicate objects as a substitute for identifying the original replication failure.

### Terraform Reports Conflicting Configuration

If another deployment system or Terraform resource manages the source bucket replication configuration, reconcile ownership before applying changes.

Use Terraform state inspection and AWS configuration inspection to identify the authoritative owner. Import or migrate existing resources deliberately rather than creating competing configuration resources.

## Cleanup

Destroying the infrastructure can delete bucket data when `force_destroy` is enabled. This example defaults to `false` to reduce accidental data loss.

### Inspect the Destroy Plan

```bash
terraform plan -destroy
```

Review all resources that will be removed.

### Remove Test Objects

Delete the test object from the source bucket:

```bash
aws s3api delete-object \
  --bucket your-org-s3-source-replication-example \
  --key replication-tests/replication-test.txt \
  --region ap-south-1
```

The destination object is managed separately and may need explicit cleanup.

For versioned buckets, deleting an object without a version ID generally creates a delete marker. To empty a versioned bucket, remove object versions and delete markers, not only current object keys.

Inspect versions:

```bash
aws s3api list-object-versions \
  --bucket your-org-s3-source-replication-example \
  --region ap-south-1
```

Repeat for the destination bucket. Remove all required versions and delete markers using carefully reviewed version-specific deletion commands.

### Destroy Terraform Resources

Once both buckets are empty:

```bash
terraform destroy
```

Confirm the plan before approving the operation.

Do not remove KMS keys or other shared infrastructure as part of this example's cleanup unless their ownership and dependencies have been independently verified.

## Key Takeaways

- CRR asynchronously replicates eligible object versions between Regions; it is not synchronous replication or automatic application failover.
- Both source and destination buckets must have versioning enabled, and the replication service requires a dedicated IAM role with appropriate permissions.
- SSE-KMS replication requires compatible keys and authorization at both the S3 IAM and KMS policy layers.
- Existing objects require S3 Batch Replication, while ongoing replication should be monitored through object status and replication metrics.
- A production DR strategy must independently define recovery objectives, application failover, data consistency, verification, and safe cleanup.