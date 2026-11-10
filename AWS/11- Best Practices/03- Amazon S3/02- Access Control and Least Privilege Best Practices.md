# Access Control and Least Privilege Best Practices

## Overview

Amazon S3 access control determines which identities can discover buckets, read objects, upload data, modify configuration, delete content, and share resources with other AWS accounts or external applications.

A production security design must establish more than a permissive bucket policy. It must define the intended identity, required actions, resource scope, applicable conditions, encryption permissions, and mechanisms for detecting unintended access.

The primary objective is to grant each identity only the permissions required to perform its responsibilities, while preserving operational recovery, auditability, and controlled delegation.

This document covers practical S3 access-control standards for Python backends, asynchronous workers, CI/CD pipelines, analytics workloads, and multi-tenant systems.

## Establish a Least-Privilege Access Model

### Define access by workload and responsibility

Avoid giving every application component the same broad S3 permissions. Separate identities according to their responsibilities and the operations they need to perform.

| Identity or workload | Typical access | Permissions to avoid unless required |
|---|---|---|
| Upload API | Create authorized objects and initiate uploads | Bucket administration, unrestricted listing, version deletion |
| Download API | Read authorized objects and generate download URLs | Object writes, bucket configuration changes |
| Processing worker | Read source objects and write designated outputs | Access to unrelated prefixes or buckets |
| Analytics workload | Read approved datasets and write designated query results | General application-document access |
| Replication role | Perform the configured replication operations | Unrelated application access |
| CI/CD deployment role | Manage explicitly designated infrastructure resources | Unrestricted production data access |
| Audit role | Inspect required configuration and security evidence | Data modification and permanent deletion |
| Human administrator | Perform approved administrative operations | Unrestricted use of permanent access keys |

The exact actions depend on the workload. For example, an upload service may need to abort incomplete multipart uploads, while a download-only service generally does not.

**Best practice:** Create separate IAM roles for applications, workers, deployment automation, and human administration. Give each role the narrowest permissions compatible with its responsibilities.

### Prefer temporary credentials

Use IAM roles and temporary credentials for applications running on EC2, ECS, EKS, Lambda, and other supported AWS compute environments.

For external CI/CD platforms such as GitHub Actions, evaluate OIDC federation to obtain short-lived AWS credentials without storing long-lived access keys in repository secrets.

For human access, prefer federated identities and AWS IAM Identity Center where appropriate.

Avoid embedding credentials in:

- Source code or configuration files.
- Docker images and container environment defaults.
- GitHub Actions or other CI/CD workflow definitions.
- Application logs and exception messages.
- Shared configuration files.
- Static frontend code.

Boto3 can obtain credentials through its standard credential provider chain. Prefer the appropriate runtime identity rather than explicitly supplying access keys to every S3 client.

```python
import boto3
from botocore.config import Config


def create_s3_client(region_name: str):
    return boto3.client(
        "s3",
        region_name=region_name,
        config=Config(
            connect_timeout=5,
            read_timeout=30,
            retries={
                "mode": "standard",
                "max_attempts": 4,
            },
        ),
    )
```

The client uses the configured AWS credential provider chain. In production, the runtime environment should provide an appropriately scoped role or federated identity.

Retry settings do not replace authorization or application-level error handling.

Reference: [AWS IAM best practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html).

## Scope IAM Permissions Correctly

### Distinguish bucket-level and object-level permissions

S3 IAM actions refer to different resource types. A policy that scopes an action to the wrong ARN may not work as intended or may accidentally grant a broader permission than necessary.

| Operation | IAM action | Resource scope |
|---|---|---|
| List objects | `s3:ListBucket` | Bucket ARN |
| Read object content | `s3:GetObject` | Object ARN |
| Upload an object | `s3:PutObject` | Object ARN |
| Delete an object | `s3:DeleteObject` | Object ARN |
| Read object tags | `s3:GetObjectTagging` | Object ARN |
| Update object tags | `s3:PutObjectTagging` | Object ARN |
| Delete a specific object version | `s3:DeleteObjectVersion` | Object ARN |
| Abort an incomplete multipart upload | `s3:AbortMultipartUpload` | Object ARN |

For a general purpose bucket named `acme-prod-documents`, the resource ARNs are:

```text
Bucket:
arn:aws:s3:::acme-prod-documents

Objects:
arn:aws:s3:::acme-prod-documents/*
```

` s3:ListBucket ` must use the bucket ARN, without `/*`. Object operations such as `s3:GetObject` use an object ARN.

Do not add `s3:*` merely to resolve an authorization error. Identify the failing API operation and grant the necessary action on the correct resource.

### Grant access to a specific application prefix

Suppose a document-processing worker must read source documents and write generated reports under a designated prefix.

A policy can grant only those operations:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadSourceDocuments",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::acme-prod-documents/processing/input/*"
    },
    {
      "Sid": "WriteGeneratedReports",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::acme-prod-documents/processing/output/*"
    }
  ]
}
```

This policy does not grant bucket listing, access to unrelated prefixes, object deletion, or bucket administration.

If the worker requires multipart-upload cleanup, object tagging, or version-specific operations, add only the relevant permissions to the appropriate resources.

### Restrict object listing separately

A worker that can read known object keys may not need unrestricted bucket listing.

When listing is required, consider restricting `s3:ListBucket` through the `s3:prefix` condition.

Example:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListProcessingInput",
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::acme-prod-documents",
      "Condition": {
        "StringLike": {
          "s3:prefix": [
            "processing/input",
            "processing/input/*"
          ]
        }
      }
    }
  ]
}
```

This limits the prefixes that can be listed through this permission. It does not automatically grant access to the objects returned; object-level authorization must also allow the requested operation.

For APIs that already know their object keys through database records, avoid unnecessary bucket-wide listing permissions.

## Secure Multi-Tenant Access

### Never trust a client-supplied tenant prefix

Consider an API request containing:

```json
{
  "tenant_id": "tenant-42",
  "document_id": "document-123"
}
```

The API must not assume the caller is authorized to access `tenant-42` merely because the request contains that identifier.

Resolve the tenant from authenticated identity and authorized application state. Retrieve the relevant document record, verify ownership or access rights, and then operate on its trusted object key.

A typical key could be:

```text
tenants/<tenant-id>/documents/<document-id>
```

The key structure improves organization, but application authorization still decides who can access the document.

### Use policy-based tenant isolation when the identity model supports it

Attribute-based access control (ABAC) can reduce policy duplication by using trusted principal tags and resource naming conventions.

The following identity policy illustrates tenant-prefix scoping using a trusted `tenant-id` principal tag:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListOwnTenantObjects",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::acme-prod-documents",
      "Condition": {
        "StringLike": {
          "s3:prefix": [
            "tenants/${aws:PrincipalTag/tenant-id}",
            "tenants/${aws:PrincipalTag/tenant-id}/*"
          ]
        }
      }
    },
    {
      "Sid": "AccessOwnTenantObjects",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::acme-prod-documents/tenants/${aws:PrincipalTag/tenant-id}/*"
    }
  ]
}
```

This policy assumes that the principal tag is set through a trusted identity-management process. It is not safe to let untrusted users choose their own tenant tags or freely pass arbitrary session tags.

Production requirements include:

- Restricting who can assign and modify tenant attributes.
- Preventing access to objects outside the intended tenant scope.
- Validating application ownership independently where applicable.
- Avoiding unnecessary wildcard permissions.
- Testing both allowed and denied cross-tenant requests.

For large-scale data sharing or more complex access patterns, evaluate S3 Access Points or S3 Access Grants when their capabilities fit the design. Neither removes the need to establish the correct identity and authorization boundary.

## Configure Bucket-Level Access Controls

### Keep S3 Block Public Access enabled

S3 Block Public Access provides protection against public exposure through applicable bucket policies and ACLs.

For private application storage, keep all four Block Public Access settings enabled unless a documented use case explicitly requires otherwise.

| Setting | Purpose |
|---|---|
| `BlockPublicAcls` | Blocks new public ACL grants and certain requests that attempt to apply them |
| `IgnorePublicAcls` | Ignores existing public ACL grants |
| `BlockPublicPolicy` | Blocks attempts to apply bucket policies that grant public access |
| `RestrictPublicBuckets` | Restricts access when a bucket has a public policy, subject to the service's documented behavior |

Enable these protections at the account and bucket levels as appropriate. Where organizational controls are available, consider preventing unauthorized identities from disabling the required settings.

Verify the configuration:

```bash
aws s3api get-public-access-block \
  --bucket "$BUCKET"
```

Account-level configuration can be inspected separately:

```bash
aws s3control get-public-access-block \
  --account-id "$AWS_ACCOUNT_ID"
```

Use an account ID belonging to the intended account and ensure the calling identity has the necessary permissions.

A successful public-access-block configuration does not eliminate the need to review private cross-account policies, identity policies, access points, or application authorization.

Reference: [Blocking public access to Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html).

### Disable ACLs using Bucket owner enforced

For most new applications, configure S3 Object Ownership as `BucketOwnerEnforced`.

This disables ACLs and makes the bucket owner the owner of uploaded objects. Access is managed through policies rather than per-object ACLs.

Advantages include:

- More predictable ownership of objects uploaded by other accounts.
- Reduced complexity from overlapping ACL and policy permissions.
- Simpler centralized administration.
- Fewer accidental public access paths.

Legacy integrations may depend on ACLs or specific canned ACLs. Verify those dependencies before disabling ACLs on an existing bucket.

For modern application workloads, do not enable ACLs merely because an old example includes an ACL parameter.

Reference: [Controlling ownership of objects and disabling ACLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/about-object-ownership.html).

### Require encrypted transport

Applications should use HTTPS for S3 API requests. A bucket policy can explicitly deny non-TLS requests.

Example policy statement:

```json
{
  "Sid": "DenyInsecureTransport",
  "Effect": "Deny",
  "Principal": "*",
  "Action": "s3:*",
  "Resource": [
    "arn:aws:s3:::acme-prod-documents",
    "arn:aws:s3:::acme-prod-documents/*"
  ],
  "Condition": {
    "Bool": {
      "aws:SecureTransport": "false",
      "aws:PrincipalIsAWSService": "false"
    }
  }
}
```

This statement is designed to deny insecure requests while excluding direct AWS service principals from this particular deny condition. Service integrations must still be configured securely and reviewed against their documented authorization requirements.

For cross-account resources, CloudFront origins, and service-to-service access, test the complete request path before enforcing a new explicit deny.

Do not copy security policy snippets blindly into production. An explicit deny can override otherwise applicable allows and break legitimate workloads if its scope is incorrect.

## Separate Application Permissions from Administrative Permissions

### Keep bucket administration out of runtime roles

An application that needs to upload files should not normally have permissions to:

- Delete the bucket.
- Change public-access settings.
- Modify bucket policies.
- Disable encryption or versioning.
- Configure replication.
- Change lifecycle rules.
- Modify logging or audit configuration.
- Permanently delete all object versions.

Keep infrastructure changes in controlled deployment roles and configuration workflows.

For example, a runtime role may need only `s3:PutObject` on an upload prefix, while a deployment role manages bucket policies, versioning, encryption, and lifecycle configuration.

Use permissions boundaries, AWS Organizations service control policies, and other governance controls as guardrails where appropriate. Remember that a permission boundary or service control policy restricts what can be authorized; it does not independently grant permissions.

### Treat deletion as a separate capability

Object deletion is often more destructive than reading or uploading data.

Grant `s3:DeleteObject` only when the application genuinely needs to delete objects. Grant `s3:DeleteObjectVersion` separately when permanent deletion of a particular object version is required.

For regulated or business-critical data, evaluate versioning, Object Lock, retention rules, backup, and recovery requirements before granting deletion capabilities.

Do not assume that removing a current object key permanently deletes every stored version.

## Apply Resource Policies Carefully

### Understand identity-based and resource-based policies

S3 access decisions can involve both identity-based policies and resource-based policies.

| Policy type | Attached to | Main purpose |
|---|---|---|
| Identity-based policy | IAM user, group, or role | Defines permissions granted to an identity |
| Bucket policy | S3 bucket | Defines access to a bucket and its objects |
| Access point policy | S3 access point | Defines access through a particular access point |
| VPC endpoint policy | VPC endpoint | Restricts applicable requests that pass through the endpoint |
| KMS key policy | KMS key | Controls access to cryptographic operations involving that key |

Effective permissions also depend on the applicable policy evaluation rules, explicit denies, session policies, permissions boundaries, organization-level controls, and other relevant mechanisms.

For same-account access, identity-based or resource-based policies may provide an applicable allow, depending on the principal and request. Cross-account access generally requires the appropriate authorization from both the caller's side and the resource owner's side.

Do not assume that adding an allow to a bucket policy automatically grants access when another applicable policy denies the request.

### Use explicit denies with care

Explicit denies are useful for enforcing security invariants, such as prohibiting insecure transport or blocking certain destructive operations.

However, they are powerful because they override conflicting allows within the applicable policy evaluation.

Before deploying a deny statement:

1. Identify all identities and services that will be affected.
2. Verify the requested actions, resources, and condition keys.
3. Test legitimate application and service requests.
4. Review cross-account and service-to-service access.
5. Deploy through a reviewed infrastructure change.
6. Monitor denied requests after rollout.

Do not use broad deny statements as a substitute for understanding the required trust model.

## Secure Cross-Account Access

### Define both the caller and resource authorization

When an external AWS account requires S3 access, define the exact principal, actions, resources, and conditions.

A typical design uses a role in the external account, with a trust policy controlling who can assume it, and a resource policy in the bucket-owning account when required.

For a controlled integration, prefer:

- A dedicated role or trusted external principal.
- Narrow access to designated buckets and prefixes.
- Explicit separation between read, write, and administrative capabilities.
- Temporary role credentials.
- Auditing and revocation procedures.
- Restricted KMS access when SSE-KMS encryption is used.

Do not grant an external account broad access to all objects simply because it needs to upload a single dataset.

### Use S3 Access Points for distinct access patterns

S3 Access Points can provide separate endpoints and policies for different consumers of a shared bucket.

For example, an analytics workload and a document-processing workload may require different read scopes. Access Points can help express those access boundaries without continuously expanding a single bucket policy.

The underlying bucket policy, the access point policy, and any applicable identity or network restrictions must all be considered. Creating an access point does not automatically override other policy requirements.

## Separate S3 Authorization from KMS Authorization

### Treat encryption permissions as an independent layer

With SSE-KMS, a successful S3 authorization check does not guarantee that the operation will succeed. The relevant KMS permissions and key policy must also permit the required cryptographic operation.

| Operation | S3 permission | Typical KMS consideration |
|---|---|---|
| Upload an SSE-KMS object | `s3:PutObject` | `kms:GenerateDataKey` and applicable key-policy authorization |
| Download an SSE-KMS object | `s3:GetObject` | `kms:Decrypt` and applicable key-policy authorization |
| Multipart upload with SSE-KMS | Relevant object-upload permissions | Required KMS operations and applicable key-policy authorization |
| Copy an encrypted object | Relevant source-read and destination-write permissions | Permissions depend on the source and destination encryption configuration |

Exact requirements vary with the operation, encryption configuration, and caller.

For SSE-S3, there is no customer-managed KMS key permission requirement. Do not troubleshoot every encrypted-object error as a KMS problem.

For SSE-KMS workloads:

- Restrict the role to the intended KMS key and operations.
- Review the key policy as well as IAM permissions.
- Confirm the key is available in the required Region.
- Ensure replication and cross-account workflows have the necessary key access.
- Monitor encryption-related authorization failures.

References:
- [S3 server-side encryption](https://docs.aws.amazon.com/AmazonS3/latest/userguide/serv-side-encryption.html)
- [AWS KMS key policies](https://docs.aws.amazon.com/kms/latest/developerguide/key-policies.html)

## Secure Presigned URL Access

### Treat presigned URLs as bearer capabilities

A presigned URL grants temporary access to a specific signed operation. Anyone possessing a usable URL may perform that operation within its effective restrictions.

Best practices include:

- Authenticate and authorize the requester before generating a URL.
- Use a server-generated object key.
- Limit the URL to the required operation and resource.
- Set a short, appropriate expiration.
- Avoid logging or sharing full signed URLs.
- Sign required request headers where applicable.
- Validate the uploaded object's content and size after upload.
- Define how object overwrite and repeated upload attempts are handled.
- Remember that the signing credentials may expire or be revoked before the configured URL expiry.

A presigned PUT URL does not automatically enforce every application-level file validation rule. The application must validate the completed object and prevent untrusted clients from selecting unauthorized object keys.

For private download URLs, perform the application's authorization check before issuing the URL. The URL should not be treated as permanent public access.

Reference: [Using presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html).

## Protect Network and Service Integration Boundaries

### Use VPC endpoint policies where appropriate

For private workloads that access S3 through a VPC endpoint, an endpoint policy can further restrict which resources and actions can be requested through that endpoint.

An endpoint policy is an additional restriction, not a replacement for IAM and resource-based policies.

If a workload requires access through multiple paths, evaluate how the endpoint policy interacts with the rest of the architecture. A broad `aws:SourceVpce` condition in a bucket policy can inadvertently block valid service integrations or requests that do not travel through the expected endpoint.

Test all intended access paths before imposing network-based conditions.

### Scope AWS service access to the intended resource

When granting access to AWS services, use the service's documented trust and resource-policy requirements.

Where supported, evaluate conditions such as `aws:SourceAccount` and `aws:SourceArn` to restrict which source resources can invoke or write to the destination.

This is particularly relevant to integrations such as CloudFront, CloudTrail, and event-driven processing.

Avoid broad service-principal permissions without conditions when the service supports narrower resource-level authorization.

## Monitor and Audit Access

### Enable appropriate audit controls

Access policies prevent unauthorized operations; monitoring and auditing help detect misconfiguration and investigate activity.

Consider the following controls:

| Control | Purpose |
|---|---|
| CloudTrail management events | Audit applicable configuration and management operations |
| CloudTrail S3 data events | Record configured object-level API activity |
| S3 server access logging | Provide request-level access log records with its own delivery considerations |
| IAM Access Analyzer for S3 | Identify buckets and access policies that allow public or shared access |
| AWS Config and security findings | Detect applicable configuration drift and compliance issues |
| CloudWatch alarms | Alert on selected operational or security indicators |
| Centralized log storage | Preserve investigation evidence under controlled access |

Object-level CloudTrail data events require appropriate configuration and may incur additional charges. Confirm resource scope, event selectors, retention, and log delivery before relying on them.

At minimum, establish an operational review process for unexpected public access, changes to bucket policies, disabled Block Public Access settings, suspicious object deletions, unusual access patterns, and encryption failures.

### Test effective access, not just policy syntax

Valid JSON does not prove that a policy grants the intended access or denies the unintended access.

A verification plan should test:

- The intended role can perform required operations.
- The same role is denied access to unrelated prefixes.
- A separate workload cannot access the protected data.
- Cross-account access works only for explicitly authorized principals.
- The application cannot change bucket security configuration.
- Encrypted object operations work with the intended KMS configuration.
- Presigned URLs expire and cannot be used for unintended operations.

Use IAM policy analysis tools and the IAM policy simulator where applicable, but supplement them with controlled integration tests because not every service-specific or request-context behavior is captured by every simulation.

## Production Readiness Checklist

- [ ] Applications use workload-specific roles and temporary credentials.
- [ ] S3 actions are scoped to the required bucket and object resources.
- [ ] Bucket-level and object-level permissions use the correct ARN forms.
- [ ] Bucket listing is restricted to required prefixes where possible.
- [ ] Block Public Access is enabled at appropriate account and bucket levels.
- [ ] Object Ownership uses Bucket owner enforced unless a documented requirement needs ACLs.
- [ ] Bucket policies and explicit denies have been reviewed against actual application and service traffic.
- [ ] Tenant identity is established by trusted authentication and authorization logic.
- [ ] Runtime identities cannot modify bucket security or infrastructure without a justified requirement.
- [ ] Cross-account access is scoped to the intended principals, actions, and resources.
- [ ] SSE-KMS permissions are reviewed separately from S3 permissions.
- [ ] Presigned URLs have appropriate scope, expiration, and handling protections.
- [ ] CloudTrail data events and other audit controls cover the required resources and operations.
- [ ] IAM Access Analyzer and relevant configuration checks are reviewed.
- [ ] Automated tests verify both allowed and denied access paths.
- [ ] Policy changes are deployed through reviewed, auditable infrastructure workflows.

## Authoritative References

- [Amazon S3 security best practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)
- [S3 access management](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-access-management.html)
- [Blocking public access to Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html)
- [S3 Object Ownership and ACLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/about-object-ownership.html)
- [AWS IAM best practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [S3 bucket policies](https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-policies.html)
- [S3 presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html)
- [IAM Access Analyzer](https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html)
- [S3 server-side encryption](https://docs.aws.amazon.com/AmazonS3/latest/userguide/serv-side-encryption.html)

## Key Takeaways

- Design access around workload-specific IAM roles, temporary credentials, narrowly scoped resources, and only the actions each component requires.
- Keep Block Public Access enabled and ACLs disabled for typical private application buckets unless a documented requirement dictates otherwise.
- Treat tenant prefixes, presigned URLs, S3 policies, and KMS permissions as distinct parts of the security model.
- Verify effective access with both positive and negative tests, including cross-account, encryption, and service-integration paths.
- Combine preventive controls with audit events, configuration monitoring, and reviewed infrastructure changes to reduce the likelihood and impact of security failures.