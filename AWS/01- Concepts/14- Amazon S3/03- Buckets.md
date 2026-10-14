# 03- Buckets

## Overview

An Amazon S3 bucket is a top-level container used to store and manage objects. Every object in S3 belongs to a bucket, and the bucket provides a boundary for configuration, access management, data organization, and operational controls.

For backend engineers, a bucket is more than a container for uploaded files. Its configuration affects data residency, security, encryption, versioning, lifecycle management, replication, monitoring, and cost allocation.

For example, a document management platform might use separate buckets for customer uploads, generated reports, application backups, and long-term archives. Each bucket can have different retention requirements, access policies, and operational settings.

```text
AWS Account
    |
    +-- S3 Bucket: application-uploads
    |       |
    |       +-- tenants/tenant-17/document-a.pdf
    |       +-- tenants/tenant-28/document-b.pdf
    |
    +-- S3 Bucket: application-reports
    |       |
    |       +-- reports/monthly/report-2026-10.csv
    |
    +-- S3 Bucket: application-backups
            |
            +-- database/backup-2026-10-13.sql.gz
```

This organization is illustrative. A production system should choose bucket boundaries according to security, compliance, lifecycle, application ownership, and operational requirements rather than creating a bucket for every object or customer automatically.

This document focuses on general purpose buckets, which are appropriate for most conventional S3 workloads. Specialized bucket types have different capabilities and are covered separately where relevant.

## What Is an S3 Bucket?

A bucket is a named S3 resource that contains objects and supports bucket-level configuration.

A bucket has several important characteristics:

- **Name:** The identifier used to address the bucket.
- **Region:** The AWS Region where the bucket is created.
- **Ownership:** The AWS account that owns the bucket.
- **Access configuration:** IAM permissions, bucket policies, public access controls, and Object Ownership.
- **Storage configuration:** Default encryption, versioning, lifecycle rules, and other supported settings.
- **Operational configuration:** Logging, event notifications, replication, monitoring, and resource tags.

A bucket is not a filesystem directory or a conventional database schema. It is a storage resource with its own configuration and resource identity.

### Bucket and Object Relationship

Every object belongs to one bucket. The object key identifies the object within that bucket.

For example:

```text
Bucket:
    company-app-documents

Objects:
    invoices/2026/invoice-001.pdf
    invoices/2026/invoice-002.pdf
    contracts/contract-001.pdf
```

The bucket name and object key are used together to address an object.

A bucket can contain an effectively unbounded number of objects for ordinary application planning purposes. S3 does not impose a fixed maximum total bucket size or object count for general purpose buckets, although individual object limits, request constraints, account quotas, and service-specific restrictions still apply.

You cannot create a bucket inside another bucket. Use object keys and prefixes to logically organize related objects.

## Types of Amazon S3 Buckets

Amazon S3 supports multiple bucket types designed for different data models and access patterns.

| Bucket type | Primary purpose | Typical use case |
|---|---|---|
| General purpose bucket | General-purpose object storage | Documents, images, backups, application files, and datasets |
| Directory bucket | Low-latency workloads using S3 Express One Zone, or supported data-residency workloads | Performance-sensitive data access |
| Table bucket | Managed storage for tabular data using S3 Tables | Apache Iceberg tables and analytics |
| Vector bucket | Storage and similarity search for vector data | Machine learning embeddings and retrieval workflows |

These bucket types are not interchangeable. Their naming rules, APIs, authorization models, supported features, and limitations can differ.

### General Purpose Buckets

General purpose buckets are the default choice for most backend applications.

They support conventional S3 object operations and a broad range of storage classes, management features, and integrations. Depending on the selected storage class and feature, objects can be stored redundantly across multiple Availability Zones.

Use a general purpose bucket for workloads such as:

- User-uploaded documents and media.
- Static application assets.
- Backend-generated reports.
- Data ingestion and data lakes.
- Backups and long-term archives.
- Event-driven application processing.

The examples in this document primarily use general purpose buckets.

### Directory Buckets

Directory buckets support specialized S3 Express One Zone workloads that require low-latency object access. They have different namespace and API characteristics from general purpose buckets.

Directory buckets should be selected only when the workload benefits from their specific performance or supported data-residency characteristics.

Do not assume that every general purpose bucket feature is available for a directory bucket.

### Table and Vector Buckets

S3 table buckets are designed for managed tabular datasets, including Apache Iceberg tables. S3 vector buckets are designed for storing and querying vector embeddings.

These specialized services have their own data models and API operations. A conventional application file repository should not use them merely because it stores structured data or AI-related files.

For most REST API file-upload systems, start with a general purpose bucket unless a specific specialized requirement justifies another bucket type.

Reference: [What is Amazon S3?](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html)

## Bucket Naming Rules

A general purpose bucket requires a name that satisfies S3 naming constraints and the namespace selected during creation.

Bucket names are visible in resource URLs and may appear in application configuration, logs, deployment definitions, and monitoring systems. Never use a bucket name to store secrets or sensitive customer information.

### General Purpose Bucket Naming Requirements

General purpose bucket names generally must:

- Be between 3 and 63 characters long.
- Contain only lowercase letters, numbers, periods (`.`), and hyphens (`-`).
- Begin and end with a letter or number.
- Not contain two adjacent periods.
- Not be formatted as an IP address.
- Avoid reserved prefixes and suffixes specified by AWS.

Names must also satisfy the uniqueness rules of the selected namespace.

For buckets in the shared global namespace, a name must be unique across the applicable AWS partition. AWS also supports an account regional namespace for general purpose buckets, which provides account-specific naming isolation.

Consult the current AWS naming rules before implementing automated bucket creation.

Reference: [General purpose bucket naming rules](https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html)

### Designing Production Bucket Names

A useful convention communicates the application's purpose and environment without exposing sensitive information.

For example:

```text
acme-document-service-dev
acme-document-service-staging
acme-document-service-prod
```

These names are illustrative and may need an additional identifier to satisfy uniqueness requirements.

For automated infrastructure deployment, a naming convention can incorporate an account-specific or environment-specific identifier when required.

A naming convention should be stable across:

- Terraform and CloudFormation resources.
- Application configuration.
- CI/CD deployment workflows.
- Monitoring and incident-response documentation.
- Operational scripts and resource inventories.

Avoid building application logic around the assumption that an arbitrary desired bucket name is available.

### Bucket Names Cannot Be Changed in Place

When a general purpose bucket is created, its name and Region cannot be changed.

Changing either generally requires creating another bucket and migrating the required configuration and data.

A migration can involve:

1. Creating the destination bucket.
2. Applying security and storage configuration.
3. Copying existing objects and associated metadata or tags as required.
4. Recreating applicable lifecycle, replication, and notification settings.
5. Updating application and infrastructure configuration.
6. Validating permissions and object integrity.
7. Switching application traffic to the destination.
8. Retiring the old bucket according to the migration and retention plan.

Not every bucket setting transfers automatically with object copying. Validate the specific configuration and behaviors required by the application.

### Bucket Deletion and Name Reuse

Deleting a bucket in the shared global namespace can introduce a security risk if another AWS account subsequently creates a bucket with the same name.

An application might continue issuing requests to the old bucket name, particularly if the name is embedded in configuration or external integrations.

Before deleting a globally named bucket:

- Identify every system that references the bucket.
- Remove or update obsolete application references.
- Confirm retention and recovery requirements.
- Empty the bucket and remove relevant configurations as required.
- Verify that no deployment, backup, or event-processing workflow depends on it.

For retired buckets whose names must remain associated with the original workload, retaining the bucket while removing its objects and disabling unwanted access can be safer than deleting it.

## Bucket Region and Resource Location

A general purpose bucket is created in a specific AWS Region.

Region selection is an architectural decision because it affects data location, regulatory requirements, latency, service integrations, and potentially data-transfer costs.

### Why Region Selection Matters

Consider an API deployed primarily in AWS Region `ap-south-1`.

If the API frequently reads and writes objects in a bucket in another Region, the design can introduce additional network latency and cross-Region transfer costs.

A sensible starting point is to place the bucket in the Region that best satisfies:

- Application latency requirements.
- Data residency and compliance obligations.
- Availability of required AWS services.
- Disaster recovery requirements.
- Expected data movement and integration costs.

The nearest Region is not automatically the best choice if the application must meet specific residency, recovery, or service-availability requirements.

### Region Is Immutable After Creation

You cannot change the Region of an existing general purpose bucket.

If a workload must move to another Region, create a destination bucket in the target Region and implement a controlled migration or replication strategy.

The migration should validate not only the objects but also the relevant bucket settings, policies, encryption keys, lifecycle rules, event notifications, logging, and integrations.

### Bucket Regions and Client Configuration

Configure application clients and deployment tooling deliberately.

A Python application using Boto3 can specify a Region explicitly:

```python
import boto3

s3_client = boto3.client(
    "s3",
    region_name="ap-south-1",
)
```

For production, use environment-specific configuration rather than assuming the machine's default Region matches the bucket's Region.

The target Region of the S3 client, the bucket's Region, and any KMS key Region requirements must be consistent with the intended operation.

Reference: [Creating a general purpose bucket](https://docs.aws.amazon.com/AmazonS3/latest/userguide/create-bucket-overview.html)

## Choosing the Number of Buckets

A recurring design question is whether to use one bucket for an entire application, multiple buckets for different data categories, or a separate bucket for every tenant.

There is no universal answer. Bucket boundaries should follow operational and security requirements.

### One Bucket for Multiple Data Categories

A shared bucket can support multiple logical data categories using key prefixes.

For example:

```text
company-app-storage/
    uploads/
    reports/
    exports/
    generated-images/
```

This approach can simplify infrastructure management when the categories share the same security posture, retention expectations, and operational requirements.

However, if different categories require significantly different controls, a single bucket may complicate policy management and incident isolation.

### Separate Buckets by Environment

Separate development, staging, and production buckets are generally a useful baseline.

```text
application-files-dev
application-files-staging
application-files-prod
```

For stronger isolation, production and non-production workloads may also use separate AWS accounts.

Separate buckets are easier to manage when environments require different access permissions, lifecycle rules, retention settings, encryption configuration, and deployment controls.

Naming alone does not create security isolation. The corresponding IAM permissions, bucket policies, accounts, and deployment controls must enforce the intended boundaries.

### Separate Buckets by Data Classification

Different buckets can be justified when data categories have different requirements.

| Data category | Possible reason for separation |
|---|---|
| Customer uploads | Customer data isolation and application access controls |
| Public website assets | Different content-delivery requirements |
| Database backups | Retention, recovery, and restricted access |
| Security logs | Audit retention and controlled write access |
| Long-term archives | Different lifecycle policies and retrieval characteristics |
| Temporary processing files | Short retention and automated cleanup |

The decision should be based on meaningful operational or security differences, not merely on the number of categories.

### One Bucket per Tenant

Creating a bucket per tenant may be appropriate when tenants require independent policies, resource ownership, retention configuration, or operational isolation.

However, it introduces additional resource-management complexity, including bucket creation, naming, quotas, monitoring, policy provisioning, migration, and cleanup.

For many multi-tenant applications, a shared bucket with controlled tenant-specific prefixes and application-level authorization is more manageable.

```text
tenant-documents/
    tenant-17/
        document-a.pdf
    tenant-28/
        document-b.pdf
```

A prefix is an organizational mechanism, not an authorization mechanism. Do not rely on users being unable to guess another tenant's prefix.

Use separate buckets or AWS accounts when stronger resource boundaries are necessary, and enforce access through appropriate IAM and resource policies.

## Bucket ARN and Object ARN

AWS uses Amazon Resource Names (ARNs) to identify resources in IAM policies and other AWS configurations.

A general purpose bucket ARN follows this structure:

```text
arn:aws:s3:::bucket-name
```

An object ARN uses the bucket name and an object key or key pattern:

```text
arn:aws:s3:::bucket-name/object-key
```

For example:

```text
Bucket ARN:
    arn:aws:s3:::company-app-documents

Object ARN:
    arn:aws:s3:::company-app-documents/invoices/2026/invoice-001.pdf

All objects in the bucket:
    arn:aws:s3:::company-app-documents/*
```

For standard S3 bucket ARNs, the Region and account ID fields are empty. Do not construct these ARNs using the same format as EC2 instance or KMS key ARNs.

Bucket-level actions and object-level actions commonly require different resource ARNs. For example, listing a bucket and reading an object are different permissions.

A policy that grants `s3:ListBucket` normally references the bucket ARN, while `s3:GetObject` normally references object ARNs.

Reference: [Amazon S3 actions, resources, and condition keys](https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazons3.html)

## Bucket Configuration and Important Settings

A bucket is configurable throughout its lifecycle. Some settings apply to the entire bucket, while others apply to particular objects or operations.

| Setting | Purpose | Recommended starting point |
|---|---|---|
| AWS Region | Determines the bucket's Region | Choose based on residency, latency, services, and recovery requirements |
| Block Public Access | Prevents unintended public exposure | Keep all applicable settings enabled unless a reviewed requirement dictates otherwise |
| Object Ownership | Controls object ownership and ACL behavior | Prefer Bucket owner enforced, which disables ACLs |
| Default encryption | Encrypts new object uploads at rest | Keep default encryption enabled; configure KMS where additional key control is needed |
| Versioning | Preserves multiple object versions | Enable when recovery from overwrites or deletions is important |
| Lifecycle rules | Transitions or expires eligible objects | Configure according to retention and access requirements |
| Bucket policy | Defines resource-based access permissions | Apply least privilege and review resource scope |
| Logging and monitoring | Provides visibility into usage and activity | Configure according to operational, security, and audit requirements |
| Replication | Copies eligible objects to destination buckets | Use when recovery, geographic separation, or another replication requirement justifies it |
| Object Lock | Protects supported object versions from deletion or overwrite | Use when retention or WORM requirements justify it |

The exact configuration depends on the bucket type and workload. Not every feature is supported by every S3 bucket type.

### Public Access Block

S3 enables Block Public Access settings by default for new general purpose buckets.

These controls help prevent public exposure through applicable bucket policies, access control lists, and related configuration.

A public access setting can exist at the account level and the bucket level. Effective protection depends on the applicable settings and how the requested access is granted.

For private application storage, keep Block Public Access enabled unless there is a specific, reviewed reason to allow public access.

If a website requires public content delivery, consider a private S3 origin behind CloudFront with Origin Access Control rather than exposing the bucket directly.

### Object Ownership

For new general purpose buckets, S3 Object Ownership defaults to **Bucket owner enforced**, which disables ACLs.

This makes the bucket owner responsible for object ownership and allows access to be managed through policies instead of relying on per-object ACLs.

Keep ACLs disabled for modern applications unless an identified integration or legacy requirement needs them.

Enabling ACLs without a clear reason adds another layer of access configuration that must be understood during security reviews and troubleshooting.

### Default Encryption

S3 automatically encrypts new object uploads using SSE-S3 by default.

For workloads requiring control over key policies, permissions, rotation, or other key-management requirements, SSE-KMS or another supported encryption option may be appropriate.

Default encryption primarily governs new writes; changing a bucket's default encryption configuration does not automatically rewrite every previously stored object to the new configuration.

Encryption configuration and KMS permissions should be reviewed independently from ordinary S3 access permissions.

Reference: [Configuring default encryption](https://docs.aws.amazon.com/AmazonS3/latest/userguide/default-bucket-encryption.html)

### Versioning

Versioning preserves multiple versions of an object under the same key.

It can help recover from accidental overwrites and deletions, but increases storage consumption when multiple versions are retained.

Versioning is disabled by default for a new general purpose bucket.

Enable it when the workload requires recovery from accidental changes, and define lifecycle or retention behavior for noncurrent versions.

Versioning is not a substitute for a tested disaster recovery strategy, access control, or backup planning.

### Lifecycle Management

Lifecycle policies can transition eligible objects between storage classes or expire eligible objects according to defined rules.

A bucket holding customer documents may require long retention, while a bucket holding temporary exports may support a shorter lifecycle.

Lifecycle rules must be aligned with business retention requirements. An overly broad expiration rule can remove data that an application or compliance process still needs.

### Object Lock

S3 Object Lock provides retention and legal-hold controls that can protect supported object versions from deletion or overwrite.

It is relevant for workloads with WORM (write once, read many) requirements or stronger protection against unauthorized or accidental modification.

Object Lock has important retention semantics and configuration requirements. Plan retention periods and governance requirements before enabling it.

Enabling Object Lock for a bucket automatically enables versioning. Validate the resulting configuration and understand the operational implications before deployment.

## Bucket Access and Permission Boundaries

Buckets provide a resource boundary, but the existence of a bucket does not automatically grant an application permission to use it.

Access is determined by the combination of applicable AWS identity permissions, resource policies, organization controls, public access settings, and other relevant authorization mechanisms.

### Bucket-Level and Object-Level Operations

| Operation | Typical IAM action | Resource type |
|---|---|---|
| List objects | `s3:ListBucket` | Bucket ARN |
| Read object data | `s3:GetObject` | Object ARN |
| Upload object | `s3:PutObject` | Object ARN |
| Delete object | `s3:DeleteObject` | Object ARN |
| Read bucket configuration | Depends on the configuration API | Bucket ARN |
| Configure bucket policy | `s3:PutBucketPolicy` | Bucket ARN |

The required permissions depend on the exact API operation and configuration. Use the AWS Service Authorization Reference when designing production policies.

An application role that needs to read objects from one bucket should not receive unrestricted access to every S3 bucket in the account.

### Example: Restricting Application Access

A service that lists objects under a particular bucket and reads objects might need separate permissions for listing and retrieving content.

A simplified identity policy could look like this:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListDocumentBucket",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::company-app-documents"
    },
    {
      "Sid": "ReadDocumentObjects",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::company-app-documents/*"
    }
  ]
}
```

This example grants read access to all objects in the specified bucket. It is not a complete production policy for every application, and it should be narrowed to the required object scope when possible.

For example, a service that only reads reports might use a narrower resource pattern or another suitable access design.

Do not confuse granting an AWS role access to a bucket with granting every end user permission to access every object. Backend authorization remains responsible for application-level user and tenant boundaries.

Detailed access-control, encryption, and policy-evaluation guidance belongs in the dedicated S3 Security section.

## Creating a General Purpose Bucket

A bucket can be created through the AWS Management Console, AWS CLI, SDKs, CloudFormation, Terraform, or AWS CDK.

For repeatable infrastructure, use infrastructure as code rather than relying exclusively on manual console operations.

### Create a Bucket in US East (N. Virginia)

First, confirm the AWS identity and default Region:

```bash
aws sts get-caller-identity
aws configure list
```

Create a general purpose bucket:

```bash
aws s3api create-bucket \
    --bucket acme-app-documents-example \
    --region us-east-1
```

Replace the example name with one that satisfies the selected namespace's requirements.

### Create a Bucket in Another Region

For a conventional general purpose bucket in another Region, specify the Region and its location constraint:

```bash
aws s3api create-bucket \
    --bucket acme-app-documents-example \
    --region ap-south-1 \
    --create-bucket-configuration \
        LocationConstraint=ap-south-1
```

The `LocationConstraint` value must match the intended Region.

These commands demonstrate the conventional shared-namespace creation pattern. If you use account regional bucket namespaces or a specialized bucket type, follow the relevant API and AWS documentation for that creation mode.

A globally named bucket must have a unique name in the applicable partition. An example name may already exist, so do not assume that a demonstration name is available.

### Configure Versioning

For a bucket that requires object-version recovery:

```bash
aws s3api put-bucket-versioning \
    --bucket acme-app-documents-example \
    --versioning-configuration Status=Enabled
```

Versioning should be enabled only after considering the desired data-protection and retention behavior.

### Verify Bucket Properties

Check the bucket's location:

```bash
aws s3api get-bucket-location \
    --bucket acme-app-documents-example
```

Inspect versioning:

```bash
aws s3api get-bucket-versioning \
    --bucket acme-app-documents-example
```

Inspect public access controls:

```bash
aws s3api get-public-access-block \
    --bucket acme-app-documents-example
```

Inspect Object Ownership:

```bash
aws s3api get-bucket-ownership-controls \
    --bucket acme-app-documents-example
```

Inspect default encryption:

```bash
aws s3api get-bucket-encryption \
    --bucket acme-app-documents-example
```

These inspection operations require the appropriate permissions. A missing or inaccessible configuration response must be interpreted in context rather than automatically treated as proof that the bucket is insecure.

## Accessing a Bucket Through Endpoints

S3 requests use service endpoints. For general purpose buckets, a common virtual-hosted-style URL has this form:

```text
https://<bucket-name>.s3.<region>.amazonaws.com/<object-key>
```

For example:

```text
https://company-app-documents.s3.ap-south-1.amazonaws.com/invoices/2026/invoice-001.pdf
```

This format is useful for understanding how bucket names, Regions, and object keys participate in object addressing.

However, a valid URL does not guarantee that an object is publicly accessible. Access still depends on the configured permissions and request authentication.

Applications should generally use an AWS SDK or another supported S3 client rather than constructing and signing low-level API requests manually.

### Website Endpoints

S3 static website hosting uses a website endpoint that differs from the normal S3 REST API endpoint.

This distinction matters when configuring CloudFront, HTTPS, website routing, and bucket access.

For a production static website that should keep its content private, prefer a suitable CloudFront configuration with Origin Access Control and a private S3 REST origin.

For further details, see [S3 website endpoints](https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteEndpoints.html).

## Monitoring, Costs, and Bucket Operations

A bucket is also an important operational boundary for inventory and usage analysis.

S3 usage and related charges may include stored data, API requests, retrieval operations, data transfer, replication, and other enabled capabilities.

Consider the following operational practices.

### Monitoring

Use appropriate tools to understand resource usage and investigate behavior:

- CloudWatch metrics for supported request and storage indicators.
- CloudTrail for relevant API activity and audit investigation.
- S3 Storage Lens for storage usage and activity insights.
- S3 Inventory for object-level inventory and selected metadata or configuration reporting.
- S3 server access logging where detailed request records are appropriate.

Select the tools based on operational requirements and account configuration. Not every monitoring feature is enabled automatically, and some capabilities have associated costs.

### Cost Allocation

Bucket-level resource tags can help categorize costs for reporting where supported.

A naming convention such as environment and workload identifiers can assist with resource discovery, but naming alone is not a cost-allocation mechanism.

Use tagging, cost-allocation reporting, and appropriate organizational controls to understand consumption.

### Bucket Quotas

AWS documents a default quota of 10,000 general purpose buckets per AWS account, with quota increases available through Service Quotas.

The appropriate quota and limits vary by bucket type. Confirm current restrictions before designing systems that create many buckets dynamically.

For a multi-tenant service, evaluate the long-term bucket count, policy-management overhead, and lifecycle implications before choosing a bucket-per-tenant design.

Reference: [General purpose bucket quotas, limitations, and restrictions](https://docs.aws.amazon.com/AmazonS3/latest/userguide/BucketRestrictions.html)

## Common Bucket Design Mistakes

### Choosing a Bucket Region Without Considering the Application

A bucket in the wrong Region may increase latency and transfer costs or conflict with data residency requirements.

Choose the Region as part of the architecture and deployment design, and remember that the Region cannot be changed in place.

### Creating Too Many Buckets

Creating a bucket for every customer or individual file can lead to unnecessary configuration and operational overhead.

Choose separate buckets where isolation and independently managed settings justify them. Use controlled prefixes and application-level authorization when a shared bucket is appropriate.

### Treating Bucket Names as Secrets

Bucket names can appear in URLs, logs, deployment files, and client configuration. Avoid putting credentials, personal information, or sensitive business details into names.

### Assuming a Private Bucket Eliminates Application Security Risks

A private bucket still requires correctly configured permissions. An overly permissive application role, incorrect bucket policy, or authorization flaw in the backend can expose stored objects.

Review AWS access permissions and application-level authorization separately.

### Disabling Public Access Controls to Fix an Access Error

When an application receives `AccessDenied`, changing Block Public Access settings is usually not the correct first response.

Inspect the caller's identity, bucket and object resource scope, policies, and request configuration. Resolve the actual authorization problem without making private data public.

### Forgetting Versioning and Lifecycle Consequences

Versioning can retain older object versions, and lifecycle rules can transition or expire objects. These features affect recovery, storage costs, and data retention.

Define versioning, lifecycle, and deletion behavior together rather than enabling features without an operational plan.

### Deleting a Bucket Without Checking Dependencies

A bucket may be referenced by applications, backup workflows, event notifications, replication rules, logging systems, and external integrations.

Before deletion, confirm ownership, retention requirements, dependent systems, and data migration or cleanup needs.

## Further Reading

- [What is Amazon S3?](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html)
- [Creating a general purpose bucket](https://docs.aws.amazon.com/AmazonS3/latest/userguide/create-bucket-overview.html)
- [General purpose bucket naming rules](https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html)
- [General purpose bucket quotas, limitations, and restrictions](https://docs.aws.amazon.com/AmazonS3/latest/userguide/BucketRestrictions.html)
- [S3 Object Ownership](https://docs.aws.amazon.com/AmazonS3/latest/userguide/about-object-ownership.html)
- [Blocking public access to Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html)
- [Amazon S3 actions, resources, and condition keys](https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazons3.html)

## Key Takeaways

- A general purpose S3 bucket is a top-level storage resource that defines important boundaries for configuration, access control, data location, and operations.
- Bucket names and Regions cannot be changed in place, so both must be chosen carefully during architecture and deployment planning.
- Separate buckets when security, retention, lifecycle, environment, or operational requirements justify the boundary; use prefixes for logical organization where appropriate.
- Keep public access blocked and ACLs disabled by default, and manage permissions through carefully scoped IAM and resource policies.
- Plan versioning, lifecycle, replication, monitoring, and deletion behavior as part of the bucket's production lifecycle rather than treating bucket creation as the complete storage design.