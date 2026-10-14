# 04- Bucket Naming

## Overview

Amazon S3 bucket naming is an infrastructure design decision that affects resource identification, deployment automation, application configuration, security, URL compatibility, and long-term operations.

A bucket name is part of the resource's externally visible identity. It can appear in S3 URLs, application configuration, infrastructure-as-code definitions, monitoring systems, logs, and operational scripts.

Unlike a database table name or a local directory name, a general purpose S3 bucket name in the shared global namespace must be unique across all AWS accounts and Regions within the applicable AWS partition. This makes predictable naming conventions insufficient on their own: a name can be syntactically valid but already owned by another account.

A production naming strategy should address four concerns:

- **Validity:** The name must satisfy the applicable S3 naming rules.
- **Uniqueness:** The name must be available in the selected namespace.
- **Consistency:** Names should follow a predictable application and environment convention.
- **Lifecycle safety:** Bucket names should not be casually changed or released when applications may still reference them.

For a backend engineering team, bucket naming should be treated as part of infrastructure provisioning and governance rather than an informal developer preference.

## General Purpose Bucket Naming Rules

General purpose buckets follow documented naming constraints.

| Rule | Requirement |
|---|---|
| Minimum length | 3 characters |
| Maximum length | 63 characters |
| Allowed characters | Lowercase letters, numbers, periods (`.`), and hyphens (`-`) |
| First character | Must be a letter or number |
| Last character | Must be a letter or number |
| Consecutive periods | Two adjacent periods are not allowed |
| IP address format | Names must not be formatted as an IP address |
| Reserved prefixes | Names must not begin with `xn--`, `sthree-`, or `amzn-s3-demo-` |
| Reserved suffixes | Names must not end with `-s3alias`, `--ol-s3`, `.mrap`, `--x-s3`, or `--table-s3` |
| Account regional namespace | Uses a prescribed suffix containing the AWS account ID and Region, ending in `-an` |
| Transfer Acceleration | Bucket names used with S3 Transfer Acceleration must not contain periods |

These are the general purpose bucket naming rules. Directory buckets, table buckets, vector buckets, and other specialized resource types have their own naming requirements.

Consult the official documentation before implementing a naming validator:

[General purpose bucket naming rules](https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html)

### Valid Naming Examples

The following names illustrate the conventional lowercase naming format:

```text
acme-document-api-dev
acme-document-api-staging
acme-document-api-prod
acme-finance-reports-prod
acme-data-platform-analytics
```

These names demonstrate syntactic conventions only. They are not guaranteed to be available in the shared global namespace.

### Invalid Naming Examples

| Bucket name | Reason |
|---|---|
| `Acme-Documents` | Contains uppercase letters |
| `acme_documents` | Contains an underscore |
| `ab` | Fewer than 3 characters |
| `-acme-documents` | Begins with a hyphen |
| `acme-documents-` | Ends with a hyphen |
| `acme..documents` | Contains adjacent periods |
| `192.168.1.10` | Formatted as an IP address |
| `xn--example` | Uses a reserved prefix |
| `acme-documents-s3alias` | Uses a reserved suffix |

Always distinguish between three separate checks:

1. Does the candidate satisfy the naming rules?
2. Does it belong to the intended namespace?
3. Can the intended AWS account create it in the selected Region?

A name passing the first check does not guarantee that the other two checks will succeed.

## Global Namespace vs Account Regional Namespace

Amazon S3 supports two naming namespaces for general purpose buckets: the shared global namespace and the account regional namespace.

The choice matters for automated provisioning, resource ownership, predictable naming, and protection against bucket-name reuse.

### Shared Global Namespace

By default, general purpose bucket names belong to a shared global namespace.

Within an AWS partition, a name in this namespace must be unique across AWS accounts and Regions. Another account cannot create a bucket with a name that is already in use in that partition.

AWS partitions include:

| Partition | Scope |
|---|---|
| `aws` | Standard AWS Regions |
| `aws-cn` | AWS China Regions |
| `aws-us-gov` | AWS GovCloud (US) Regions |
| `aws-eusc` | AWS European Sovereign Cloud |

A bucket name does not become globally unique across every AWS partition merely because it is unique in one partition.

Consider this candidate:

```text
acme-document-api-prod
```

It may be syntactically valid, but another account could already own that name. Infrastructure code must not assume that a desired global name is available until the bucket has been successfully created or its ownership has otherwise been established.

### Account Regional Namespace

AWS also supports an account regional namespace for general purpose buckets. Within this namespace, only the owning AWS account can create bucket names in its reserved namespace.

This is useful when designing consistent naming schemes across environments and Regions.

The naming convention is:

```text
<customer-prefix>-<12-digit-account-id>-<region>-an
```

For example:

```text
acme-documents-123456789012-ap-south-1-an
```

The account ID and Region in this example are illustrative.

The suffix identifies the account regional namespace. It also counts toward the maximum 63-character bucket-name length.

To use this namespace, the creation request must explicitly select `account-regional`. Naming a bucket with a string that resembles the convention does not, by itself, place the bucket in that namespace.

Account regional namespace buckets are supported in AWS Regions except Middle East (Bahrain) and Middle East (UAE), according to the current AWS documentation. Check the latest Region and feature availability before relying on this capability in automated deployments.

Reference: [Namespaces for general purpose buckets](https://docs.aws.amazon.com/AmazonS3/latest/userguide/gpbucketnamespaces.html)

### Comparing the Two Namespaces

| Consideration | Shared global namespace | Account regional namespace |
|---|---|---|
| Name uniqueness | Across accounts within a partition | Reserved for the owning account |
| Naming convention | Customer-defined valid name | Customer-defined prefix plus account ID, Region, and `-an` |
| Predictable cross-Region names | Possible, but collision-prone | Easier to template within the account |
| Availability | Depends on whether the name is already taken | Depends on namespace, Region, and account requirements |
| Name reuse risk after deletion | Another account may acquire the name | Another account cannot recreate a name reserved to the original account |
| Creation requirements | Standard bucket creation | Must select the account regional namespace |
| Application compatibility | Standard S3 behavior for supported features | Same general purpose bucket feature model, with documented namespace-specific considerations |

**Recommendation:** For newly designed infrastructure that supports it, prefer the account regional namespace when the objective is to ensure that another account cannot claim the application's bucket name. Otherwise, use a carefully designed global name and treat name ownership as an infrastructure dependency.

The namespace is selected at bucket creation and cannot be changed afterward.

## Designing a Bucket Naming Convention

A naming convention should describe the resource's role without becoming an uncontrolled collection of implementation details.

A useful convention for shared global namespace buckets is:

```text
<organization>-<application>-<environment>-<purpose>-<unique-id>
```

For example:

```text
acme-billing-prod-documents-a82f71
acme-billing-dev-exports-c104b2
acme-platform-prod-audit-logs-f29a31
```

The unique suffix helps reduce collision risk. These example suffixes are illustrative identifiers, not proof of uniqueness.

For an account regional namespace bucket, the account ID and Region are incorporated through the prescribed suffix instead.

### Naming Components

| Component | Example | Purpose |
|---|---|---|
| Organization | `acme` | Identifies the organization or platform |
| Application | `billing` | Identifies the workload |
| Environment | `prod` | Distinguishes production from development |
| Purpose | `documents` | Communicates the storage responsibility |
| Unique identifier | `a82f71` | Reduces collision risk in the shared namespace |
| Account ID | `123456789012` | Identifies the owning account in an account regional name |
| Region | `ap-south-1` | Identifies the intended Region when following an account regional naming convention |

Do not include every component in every name mechanically. The shared global namespace has a strict 63-character limit, and account regional names must reserve space for the account ID, Region, and `-an` suffix.

### Separate Environments Explicitly

Development, staging, and production should not depend on different conventions implemented manually by individual developers.

Use consistent names or account regional prefixes to distinguish environments, and combine this convention with actual access boundaries.

For example:

```text
acme-payments-dev-...
acme-payments-staging-...
acme-payments-prod-...
```

The naming convention improves discoverability, but it does not enforce isolation.

For sensitive production workloads, separate AWS accounts, appropriate IAM roles, resource policies, and deployment permissions may provide stronger isolation than different bucket names alone.

### Prefer Stable Purpose-Based Names

Prefer names that remain meaningful as implementation details change.

Good examples:

```text
acme-documents-prod-...
acme-backups-prod-...
acme-audit-logs-prod-...
```

Avoid names that encode temporary implementation details:

```text
acme-documents-new-final-v2-...
acme-documents-test-copy-...
acme-temp-bucket-use-this-...
```

A bucket may outlive an application version, deployment pipeline, or individual service instance. Naming should reflect the resource's durable responsibility.

## DNS Compatibility and URL Considerations

S3 bucket names can appear in request URLs, so naming choices affect endpoint compatibility.

A virtual-hosted-style S3 endpoint commonly has the following structure:

```text
https://<bucket-name>.s3.<region>.amazonaws.com/<object-key>
```

For example:

```text
https://acme-documents-prod.s3.ap-south-1.amazonaws.com/invoices/invoice-001.pdf
```

### Avoid Periods for General Application Buckets

Although periods are permitted by the general purpose bucket naming rules, hyphens are generally a safer default for application buckets.

A bucket name containing periods can cause problems with HTTPS virtual-hosted-style requests because of wildcard TLS certificate matching.

For example:

```text
acme.documents.prod
```

When inserted into a virtual-hosted-style hostname, the bucket name introduces additional hostname labels. This can conflict with the wildcard certificate used by the standard S3 endpoint.

Bucket names containing periods also cannot be used with S3 Transfer Acceleration.

Prefer:

```text
acme-documents-prod
```

over:

```text
acme.documents.prod
```

Use periods only when the workload and endpoint configuration have been evaluated carefully, such as certain static website use cases.

Reference: [Virtual hosting of general purpose buckets](https://docs.aws.amazon.com/AmazonS3/latest/userguide/VirtualHosting.html)

## Naming Buckets for Multi-Tenant Applications

A multi-tenant application must distinguish between the resource naming strategy and the authorization model.

There are two common choices.

### Shared Bucket with Tenant Prefixes

A shared bucket can organize objects by tenant:

```text
acme-document-platform-prod/
    tenants/tenant-17/documents/...
    tenants/tenant-28/documents/...
```

Advantages include fewer bucket resources, centralized configuration, and simpler infrastructure management.

However, the application must enforce tenant authorization, and any prefix-based IAM policy must be scoped carefully.

A user must not be able to substitute another tenant's identifier and access another tenant's objects.

### Bucket per Tenant

A separate bucket per tenant may be appropriate when tenants require distinct retention, access configuration, operational ownership, or other resource-level controls.

It introduces more infrastructure to provision, monitor, secure, and retire.

It also makes naming and quota management more complicated if tenant creation is a frequent application operation.

Do not create a bucket per customer merely to simulate application authorization. The decision should follow actual isolation requirements, not the desire to make object paths appear separate.

Reference: [Common general purpose bucket patterns for building applications on Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/common-bucket-patterns.html)

## Name Validation in Python

A local validator can catch common naming errors before an infrastructure deployment is attempted.

However, a regular expression cannot establish namespace ownership, global availability, account regional namespace selection, or every bucket-type-specific restriction.

The following example validates the ordinary general purpose bucket naming format and reserved prefixes and suffixes. It intentionally does not claim that a valid name is available.

```python
import ipaddress
import re

BUCKET_NAME_PATTERN = re.compile(
    r"^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$"
)

RESERVED_PREFIXES = (
    "xn--",
    "sthree-",
    "amzn-s3-demo-",
)

RESERVED_SUFFIXES = (
    "-s3alias",
    "--ol-s3",
    ".mrap",
    "--x-s3",
    "--table-s3",
)


def validate_general_purpose_bucket_name(name: str) -> None:
    """Raise ValueError if a candidate violates common global-namespace rules."""
    if not isinstance(name, str):
        raise ValueError("Bucket name must be a string.")

    if not 3 <= len(name) <= 63:
        raise ValueError("Bucket name must be 3–63 characters long.")

    if not BUCKET_NAME_PATTERN.fullmatch(name):
        raise ValueError(
            "Bucket name must use lowercase letters, numbers, "
            "periods, and hyphens, and start and end with "
            "a letter or number."
        )

    if ".." in name:
        raise ValueError("Bucket name cannot contain adjacent periods.")

    try:
        ipaddress.ip_address(name)
    except ValueError:
        pass
    else:
        raise ValueError("Bucket name cannot be formatted as an IP address.")

    if name.startswith(RESERVED_PREFIXES):
        raise ValueError("Bucket name uses a reserved prefix.")

    if name.endswith(RESERVED_SUFFIXES):
        raise ValueError("Bucket name uses a reserved suffix.")

    if name.endswith("-an"):
        raise ValueError(
            "The -an suffix is reserved for the account regional "
            "namespace; validate its naming convention separately."
        )


if __name__ == "__main__":
    candidates = [
        "acme-documents-prod-a82f71",
        "Acme-Documents",
        "acme_documents_prod",
        "acme..documents",
    ]

    for candidate in candidates:
        try:
            validate_general_purpose_bucket_name(candidate)
        except ValueError as exc:
            print(f"INVALID: {candidate}: {exc}")
        else:
            print(f"FORMAT OK: {candidate}")
```

This is an initial validation layer, not a replacement for AWS-side validation. Production tooling should explicitly distinguish shared global names from account regional names and validate the relevant rules separately.

The example also checks a reserved suffix at a basic string level. It does not attempt to validate directory, table, vector, access-point, or other specialized resource naming rules.

## Generating Stable Names for Infrastructure as Code

For shared global namespace buckets, automated provisioning should include a collision-resistant suffix when globally unique naming is required.

For example, Terraform can generate a resource-specific identifier:

```hcl
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "documents" {
  bucket = "acme-documents-prod-${random_id.bucket_suffix.hex}"
}
```

This example illustrates a naming pattern. A production deployment must also configure the appropriate provider, dependencies, security settings, variables, and outputs.

Important considerations:

- Retain the generated name in Terraform state so normal changes do not produce an unnecessary replacement.
- Do not regenerate the suffix on every deployment.
- Store the resulting bucket name in the infrastructure outputs and application configuration.
- Treat a bucket replacement as a data migration, not a simple rename.
- Use the account regional namespace where appropriate instead of depending solely on random suffixes for ownership isolation.

For account regional buckets, use the supported namespace configuration in the relevant IaC provider and include the prescribed account and Region suffix. Do not merely append those values to a name and assume that the bucket has been created in the account regional namespace.

## Creating an Account Regional Bucket with the AWS CLI

An account regional namespace bucket uses the required naming convention and an explicit namespace selection.

Example for an illustrative AWS account in the `ap-south-1` Region:

```bash
aws s3api create-bucket \
    --bucket acme-documents-123456789012-ap-south-1-an \
    --bucket-namespace account-regional \
    --region ap-south-1 \
    --create-bucket-configuration LocationConstraint=ap-south-1
```

Replace the example account ID and name with values appropriate to your environment.

Before deploying this pattern:

1. Confirm the target AWS account and Region.
2. Verify that the selected Region supports the namespace.
3. Ensure that the full name satisfies the length and naming requirements.
4. Confirm that the CLI and infrastructure tooling support the relevant namespace option.
5. Record the created bucket name in the deployment outputs or configuration.

Reference: [Creating a bucket in your account regional namespace](https://docs.aws.amazon.com/AmazonS3/latest/userguide/gpbucketnamespaces.html)

## Bucket Naming and Security

Bucket names are not secrets. They can appear in URLs, application configuration, request logs, deployment artifacts, and infrastructure inventories.

Avoid putting the following information into bucket names:

- Access keys, passwords, tokens, or other credentials.
- Customer names or personal identifiers.
- Confidential project names.
- Sensitive information about data classification.
- Internal details that should not be externally visible.

A descriptive bucket name can reveal the purpose of the workload, even when its objects remain private.

Use naming conventions to support operations, but rely on IAM, bucket policies, Block Public Access, appropriate account boundaries, and application authorization to protect data.

### Safe Decommissioning

Deleting a bucket in the shared global namespace can allow another AWS account in the same partition to create a bucket with the same name.

If a system continues to reference the old name, requests intended for the original bucket may be directed to the newly created resource. This can create a security risk if the application sends data to that endpoint without verifying the expected resource ownership.

For example, a retired service may still have the old bucket name configured in an environment variable, backup job, or delayed processing workflow.

Before deleting the bucket:

- Search application configuration and infrastructure code for references.
- Disable or update workflows that may still access the resource.
- Confirm that required data has been migrated or retained.
- Review lifecycle, retention, and recovery requirements.
- Ensure that stale applications cannot continue writing to an unintended resource.

AWS recommends retaining an unused shared-global-namespace bucket when continuing to own its name is important. Emptying the bucket and restricting requests can be safer than deleting it purely to reduce storage costs.

Reference: [General purpose bucket naming rules and naming best practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html)

## Common Naming Mistakes

| Mistake | Consequence | Better approach |
|---|---|---|
| Assuming a valid name is available | Infrastructure creation fails because another account already owns the name | Use a collision-resistant convention or the account regional namespace |
| Ignoring the 63-character limit | Provisioning fails when adding account IDs, Regions, or suffixes | Calculate the full name before deployment |
| Using periods by default | HTTPS hostname compatibility issues and Transfer Acceleration restrictions | Prefer lowercase names separated by hyphens |
| Treating an account ID in the name as namespace selection | The bucket may still be in the shared global namespace | Explicitly select `account-regional` when creating the resource |
| Putting tenant identifiers into a shared bucket without authorization checks | Cross-tenant access vulnerabilities | Enforce application authorization and scope AWS permissions |
| Encoding personal data in bucket names | Unnecessary disclosure through URLs and logs | Use non-sensitive workload identifiers |
| Regenerating bucket names during deployment | Unnecessary bucket replacement and migration risk | Keep names stable in configuration and state |
| Deleting a bucket to reuse its global name | Another account may acquire the name | Retain the bucket when ownership must be preserved |
| Using a bucket naming convention as a substitute for access control | Naming does not prevent unauthorized requests | Enforce IAM, bucket policy, and application-level controls |

## Further Reading

- [General purpose bucket naming rules](https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html)
- [Namespaces for general purpose buckets](https://docs.aws.amazon.com/AmazonS3/latest/userguide/gpbucketnamespaces.html)
- [Creating a general purpose bucket](https://docs.aws.amazon.com/AmazonS3/latest/userguide/create-bucket-overview.html)
- [Common general purpose bucket patterns for building applications](https://docs.aws.amazon.com/AmazonS3/latest/userguide/common-bucket-patterns.html)
- [Virtual hosting of general purpose buckets](https://docs.aws.amazon.com/AmazonS3/latest/userguide/VirtualHosting.html)

## Key Takeaways

- General purpose S3 bucket names must satisfy strict naming constraints, but syntactic validity does not guarantee global availability.
- Choose between the shared global namespace and account regional namespace deliberately; namespace selection is made at creation time.
- Prefer stable, non-sensitive, hyphen-separated names that identify the workload and environment without exceeding the 63-character limit.
- Bucket naming improves discoverability and deployment consistency, but it does not provide authorization or tenant isolation.
- Treat bucket deletion and replacement as lifecycle and security decisions because a released global name may later belong to another AWS account.