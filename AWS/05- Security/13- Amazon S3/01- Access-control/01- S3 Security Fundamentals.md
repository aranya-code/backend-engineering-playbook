# 01- S3 Security Fundamentals

## Overview

Amazon S3 security protects object data against unauthorized access, accidental exposure, unauthorized modification, data loss, and misuse of application identities.

In production systems, S3 security is not a single bucket policy or encryption setting. It is a combination of identity management, resource policies, public-access controls, encryption, network restrictions, application authorization, auditing, and recovery mechanisms.

A secure implementation must answer the following questions:

- Who can access the bucket and its objects?
- Which operations can each identity perform?
- Can data become publicly accessible?
- How is data protected at rest and in transit?
- How are access decisions and sensitive operations audited?
- What prevents one application or tenant from accessing another tenant's data?
- How can unauthorized access, accidental deletion, or configuration drift be detected?

This document establishes the foundational security model for Amazon S3. Detailed IAM policy evaluation, encryption and KMS configuration, advanced access patterns, and security troubleshooting should be covered in their respective dedicated documents.

## Amazon S3 Security Model

S3 security is implemented across multiple layers. No single control should be treated as a complete security boundary.

| Security layer | Primary purpose | Typical controls |
|---|---|---|
| Identity | Establish who or what is making a request | IAM roles, temporary credentials, workload identities |
| Authorization | Determine which operations are permitted | IAM policies, bucket policies, access point policies |
| Public-access prevention | Prevent unintended public exposure | S3 Block Public Access |
| Ownership | Establish ownership and simplify access management | S3 Object Ownership |
| Data protection | Protect stored and transmitted data | Server-side encryption, TLS |
| Network | Restrict supported access paths | VPC endpoints, endpoint policies, access point network controls |
| Application | Enforce business and tenant-level authorization | Authentication, object ownership checks, safe key generation |
| Audit and detection | Identify suspicious access and configuration changes | CloudTrail, CloudWatch, access logging, security findings |
| Recovery | Limit the impact of data loss or destructive operations | Versioning, backups, retention controls, S3 Object Lock where appropriate |

These controls complement one another. For example, encryption at rest protects stored data but does not prevent an authorized principal from downloading the object. A private bucket prevents anonymous public access but does not automatically isolate individual tenants using the same application role.

## Shared Responsibility for S3 Security

AWS operates the underlying S3 infrastructure, including the physical facilities and managed service components. Customers remain responsible for how their data is classified, accessed, configured, and used.

### AWS responsibilities

AWS is responsible for the security of the underlying cloud infrastructure and managed S3 service, including the infrastructure that supports service availability and data durability.

### Customer responsibilities

Customers are responsible for controls such as:

- Configuring IAM permissions and resource policies.
- Preventing unintended public access.
- Protecting application credentials.
- Enforcing tenant-level authorization.
- Selecting suitable encryption and key-management settings.
- Configuring logging and security monitoring.
- Applying appropriate retention, backup, and recovery policies.
- Reviewing configuration changes and responding to security findings.

The exact allocation of responsibilities also depends on the other AWS services used in the architecture.

## Identity and Access Fundamentals

Every S3 API request must be authorized according to the applicable authentication and access-control mechanisms.

For ordinary application access, use an IAM role or another supported temporary-credential mechanism rather than embedding long-lived AWS access keys in application code.

### Common identities

| Identity | Typical use | Security consideration |
|---|---|---|
| IAM role assumed by an EC2 workload | Application access from an EC2 instance | Limit the role to the required S3 operations and resources |
| IAM role used by Lambda | Reading input objects and writing processed results | Separate function permissions according to processing responsibilities |
| ECS task role | Access from a containerized application | Use the task role rather than credentials baked into the container |
| EKS workload identity | Access from Kubernetes workloads | Associate AWS permissions with the intended workload identity |
| CI/CD deployment role | Provision or update S3 infrastructure | Separate deployment permissions from runtime application permissions |
| Cross-account role | Controlled access between AWS accounts | Define trusted principals and narrowly scoped permissions |
| Presigned URL recipient | Temporary access to a specific S3 operation | Treat the URL as a bearer capability and protect it accordingly |

### Follow least privilege

An application that downloads and uploads objects should not automatically receive permission to delete objects, change bucket policies, or administer account-level S3 settings.

Separate runtime access from administrative access.

Prefer narrowly scoped permissions for known buckets and object prefixes. Avoid unrestricted permissions such as `s3:*` on every bucket unless an explicitly justified administrative role requires them.

Use temporary credentials, credential rotation where applicable, and appropriate identity controls. Never store production AWS credentials in source code, container images, notebooks, logs, or version control.

Reference: [How Amazon S3 works with IAM](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security_iam_service-with-iam.html).

## Understand the Main Access-Control Mechanisms

S3 supports identity-based and resource-based policies, access point policies, and access control lists (ACLs) in configurations where ACLs are enabled.

### Identity-based policies

An identity-based policy is attached to an IAM user, group, or role. It grants or denies that identity permission to perform specified actions on resources.

For example, an application role may be allowed to upload and download objects from a particular application prefix.

### Resource-based policies

A bucket policy is attached to a bucket and defines access for applicable principals. It can grant access to another AWS account or restrict requests according to supported conditions.

An access point policy controls access through its associated access point and is evaluated alongside the underlying bucket policy.

### Access control lists

ACLs provide an older object- and bucket-level permission model. For new general-purpose buckets, S3 Object Ownership defaults to **Bucket owner enforced**, which disables ACLs and makes the bucket owner own uploaded objects.

Prefer policy-based access control for new designs unless a specific compatibility requirement justifies another approach.

### Policy evaluation

An allowed request must satisfy the applicable authorization requirements. An explicit deny overrides an allow.

A permission granted by an IAM policy does not override an applicable explicit deny in a bucket policy, organization-level control, service control policy, permissions boundary, or other relevant policy mechanism.

Not every S3 operation uses the same resource type or permission. Some operations target the bucket, while others target objects. A policy must reference the appropriate resource ARN and required action.

For example:

- Bucket ARN: `arn:aws:s3:::example-prod-documents`
- Object ARN: `arn:aws:s3:::example-prod-documents/*`

Do not use an object ARN where an operation requires a bucket resource, or vice versa.

Detailed policy evaluation and policy design should be covered in the dedicated IAM and S3 policy documents.

Reference: [Policies and permissions in Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-policy-language-overview.html).

## Prevent Unintended Public Access

Public exposure is one of the most important S3 security risks.

An incorrectly configured bucket policy, ACL, or access point policy can expose sensitive documents, media, backups, logs, or other data.

### S3 Block Public Access

S3 Block Public Access provides controls at the organization, account, bucket, and supported access point levels. The most restrictive applicable settings govern public-access behavior.

The four settings are:

| Setting | Purpose |
|---|---|
| `BlockPublicAcls` | Blocks attempts to apply public ACLs and relevant public ACL-based changes |
| `IgnorePublicAcls` | Causes public ACL grants to be ignored when evaluating access |
| `BlockPublicPolicy` | Blocks attempts to apply bucket or access point policies that grant public access |
| `RestrictPublicBuckets` | Restricts access to buckets with public policies according to the feature's documented behavior |

For most private application buckets, enable all four settings.

New S3 buckets have Block Public Access enabled by default, but existing resources and organizational configurations should be verified rather than assumed to be secure.

### Inspect public-access settings

```bash
aws s3api get-public-access-block \
  --bucket example-prod-documents \
  --region ap-south-1
```

Inspect the account-level configuration:

```bash
aws s3control get-public-access-block \
  --account-id YOUR_ACCOUNT_ID \
  --region ap-south-1
```

Account-level controls apply across the account's applicable S3 resources, subject to the documented service behavior. Organizational controls can impose additional restrictions.

### Keep private buckets private

For a website delivered through CloudFront, prefer a private S3 origin with Origin Access Control rather than opening the bucket to the public internet.

If a workload genuinely requires public content, define the intended public-access boundary explicitly and verify that sensitive objects cannot be accessed through it.

Do not disable Block Public Access globally merely to solve a problem with one bucket.

Reference: [Blocking public access to Amazon S3 storage](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html).

## Use S3 Object Ownership Correctly

S3 Object Ownership determines who owns objects and how ACLs are handled.

For general-purpose buckets, **Bucket owner enforced** disables ACLs and makes the bucket owner own all objects in the bucket. This simplifies access management by centralizing permissions in policies.

This setting is appropriate for most modern application architectures.

It also avoids a class of cross-account upload problems in which an uploading account might otherwise own an object and create unexpected permission behavior.

Before applying this configuration to an existing integration, verify that clients and external uploaders do not depend on setting object ACLs. Requests that attempt to use unsupported ACL behavior can fail.

Inspect the ownership configuration:

```bash
aws s3api get-bucket-ownership-controls \
  --bucket example-prod-documents \
  --region ap-south-1
```

Reference: [Controlling object ownership and disabling ACLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/about-object-ownership.html).

## Protect Data at Rest

S3 encrypts new object uploads at rest by default using server-side encryption with Amazon S3 managed keys (SSE-S3).

This provides baseline encryption without requiring the application to implement its own encryption algorithm.

### Server-side encryption options

| Encryption option | Key management | Typical consideration |
|---|---|---|
| SSE-S3 | AWS manages the encryption keys | Suitable when standard server-side encryption meets the security requirements |
| SSE-KMS | AWS KMS manages the key material and access controls | Useful when key-policy control, auditing, or other KMS capabilities are required |
| DSSE-KMS | Dual-layer server-side encryption using AWS KMS | Consider where dual-layer encryption requirements justify its additional complexity and cost |
| SSE-C | Customer supplies encryption keys with requests | Requires secure key distribution, handling, and retention by the customer |
| Client-side encryption | Application encrypts data before uploading | Useful when the design requires protection beyond server-side encryption boundaries, but substantially increases key-management responsibility |

Choose the encryption method according to data sensitivity, regulatory requirements, access patterns, key-management requirements, and cost.

### Important security distinction

Encryption at rest does not replace access control.

If a principal is authorized to retrieve an object and the necessary encryption permissions are satisfied, S3 can return the plaintext object over the authorized connection.

For SSE-KMS, access may require both the relevant S3 permissions and appropriate KMS permissions. A request denied by KMS is not the same as an S3 bucket-policy denial.

Do not assume that enabling SSE-KMS automatically prevents authorized applications from reading data.

### Verify default encryption

```bash
aws s3api get-bucket-encryption \
  --bucket example-prod-documents \
  --region ap-south-1
```

Use this check to inspect the configured default encryption behavior. Default encryption settings do not establish that every existing object uses the required key or encryption mode; verify object-level requirements separately where necessary.

Reference: [Protecting data with server-side encryption](https://docs.aws.amazon.com/AmazonS3/latest/userguide/serv-side-encryption.html).

## Protect Data in Transit

S3 supports HTTPS for encrypted transport using TLS.

Use HTTPS for application access, presigned URLs, AWS SDK operations, and other client interactions. Avoid sending sensitive object data over unencrypted HTTP.

S3 supports TLS 1.2 and TLS 1.3 across its API endpoints. Current AWS SDKs and the AWS CLI normally negotiate an appropriate TLS version automatically.

### Enforce HTTPS using a bucket policy

The following policy denies requests that do not use secure transport, while excluding AWS service principals from this particular deny statement.

Replace the bucket name before applying it.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyInsecureTransport",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::example-prod-documents",
        "arn:aws:s3:::example-prod-documents/*"
      ],
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false",
          "aws:PrincipalIsAWSService": "false"
        }
      }
    }
  ]
}
```

The condition requires both the insecure-transport condition and the non-service-principal condition to match.

This statement does not grant access; it denies matching insecure requests. Existing required permissions must remain in place.

Test the policy with the actual application, AWS service integrations, replication configuration, and administrative workflows before enforcing it in production.

Reference: [Protecting data in transit with encryption](https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingEncryptionInTransit.html).

## Apply Least-Privilege Bucket and Object Permissions

A common mistake is to grant a backend role full access to every object in a bucket when it only needs a particular prefix.

The following identity-based policy allows listing a specific bucket prefix and reading or writing objects under that prefix.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListApplicationPrefix",
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::example-prod-documents",
      "Condition": {
        "StringLike": {
          "s3:prefix": [
            "reports",
            "reports/*"
          ]
        }
      }
    },
    {
      "Sid": "ReadWriteApplicationObjects",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::example-prod-documents/reports/*"
    }
  ]
}
```

This is an illustrative policy, not a complete permission set for every application. Multipart uploads, tagging, deletion, KMS-encrypted objects, or additional operations may require other permissions.

The policy also does not prevent every possible indirect access path. Effective access depends on all applicable IAM and resource-based controls.

### Policy design principles

- Separate bucket operations from object operations.
- Scope resources to the intended bucket and prefix.
- Add permissions only when a workflow requires them.
- Prefer separate roles for unrelated applications and workers.
- Review cross-account trust and access paths.
- Avoid broad wildcards when narrower permissions are practical.
- Test both allowed and denied operations.

Reference: [Required permissions for Amazon S3 API operations](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-with-s3-policy-actions.html).

## Network Access Controls

S3 access can be restricted through supported network controls in addition to identity and resource policies.

### VPC endpoints

An S3 gateway VPC endpoint allows supported S3 traffic from a VPC to reach S3 without requiring the traffic to traverse an internet gateway or NAT gateway.

Endpoint policies can further restrict which S3 resources or operations are accessible through that endpoint.

However, a VPC endpoint does not automatically grant permission to access a bucket. The applicable IAM and resource policies must still permit the operation.

### Access points

S3 Access Points provide named endpoints with independent access policies and supported network controls. They are useful when multiple applications access a shared dataset under different permissions.

An access point policy works alongside the underlying bucket policy; it does not eliminate the need to reason about bucket-level authorization.

### Use network restrictions with care

Before restricting a bucket to a particular VPC or endpoint, verify every legitimate access path, including:

- Application workloads.
- Backup and recovery processes.
- Replication workflows.
- Administrative operations.
- CI/CD deployment and validation jobs.
- Analytics and data-processing services.
- Cross-account consumers.

A network restriction that excludes an essential service can break a workflow even when its IAM permissions are otherwise correct.

References:

- [Amazon S3 VPC endpoints](https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints-s3.html)
- [Managing access to shared datasets with S3 Access Points](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-access-points.html)

## Secure Application and Tenant Access

S3 security depends on correct authorization in the application layer as well as AWS policies.

For example, a multi-tenant Django or FastAPI application might store documents under separate tenant prefixes:

```text
documents/
    tenant-123/
        invoice-001.pdf
    tenant-456/
        invoice-002.pdf
```

The prefix is an organizational convention, not an authorization boundary by itself.

If one application role can read every object in the bucket, the application must correctly authorize each request before retrieving an object for a user.

### Recommended application design

1. Authenticate the user.
2. Validate the user's authorization to access the requested document.
3. Retrieve the object key from trusted application metadata where possible.
4. Use a narrowly scoped S3 service layer to retrieve the object or generate a presigned URL.
5. Record relevant security events without logging credentials or signed URLs.
6. Return only the data the user is authorized to access.

Do not allow a client to supply an arbitrary S3 key and assume that authentication alone makes the requested object safe to return.

### Secure object key generation

Generate object keys using trusted identifiers and controlled path conventions.

Avoid constructing a key directly from an untrusted filename or URL path. Validate filename input and prevent application-level path or tenant-boundary confusion.

Object keys are not filesystem paths, but unsafe key handling can still cause authorization mistakes, overwrites, or exposure of another tenant's objects.

### Presigned URLs

A presigned URL provides temporary access to a specific S3 operation. Anyone possessing a valid URL can generally exercise the capability encoded in it until it expires or becomes invalid.

Use short expiration periods appropriate to the task and protect URLs from:

- Application logs and tracing systems.
- Analytics events.
- Browser history or referrer leakage.
- Public issue trackers and chat messages.
- Unauthorized reuse or sharing.

Authorize the user before creating the URL. A presigned URL does not replace application-level tenant authorization.

Detailed presigned URL design should be covered in the dedicated security and integration documents.

## Audit and Monitor Security-Relevant Activity

Security controls need observability so that unauthorized access attempts, configuration changes, and unexpected data operations can be investigated.

### AWS CloudTrail

CloudTrail records supported AWS API activity and can help investigate bucket configuration changes, identity activity, and S3 data access when the relevant data events are configured.

Management events and S3 object-level data events have different coverage and cost implications. Do not assume every object read or write appears in the default management-event history.

For sensitive buckets, evaluate whether S3 data events are required to audit object-level operations.

### S3 server access logging

S3 server access logging provides request-level records for a bucket. It is useful for selected operational and security investigations but has delivery and completeness considerations.

Choose logging controls based on the investigation requirements and the operational cost of retaining and analyzing records.

### CloudWatch and security findings

Use CloudWatch metrics and alarms where appropriate to detect request patterns or errors. Use AWS security services and configuration checks, where enabled, to identify public exposure, policy changes, or other security findings.

### Logging safeguards

- Restrict access to logs containing resource identifiers and request metadata.
- Define retention and deletion policies.
- Avoid logging AWS credentials, authorization headers, or presigned URLs.
- Monitor changes to bucket policies, Block Public Access, ownership controls, encryption, and logging settings.
- Establish an incident-response workflow for public exposure or unauthorized access.

References:

- [Logging Amazon S3 API calls with CloudTrail](https://docs.aws.amazon.com/AmazonS3/latest/userguide/cloudtrail-logging.html)
- [Amazon S3 server access logging](https://docs.aws.amazon.com/AmazonS3/latest/userguide/ServerLogs.html)

## Protect Against Accidental Deletion and Data Loss

Security also includes protecting data from destructive operations, compromised credentials, and application bugs.

Versioning allows recovery from certain overwrites and deletions, while an appropriate backup strategy can provide additional recovery options.

S3 Object Lock can help protect eligible object versions from deletion or overwrite for a defined retention period. It should be configured according to documented compliance and governance requirements.

### Select controls according to recovery needs

| Requirement | Relevant control |
|---|---|
| Recover from accidental overwrites | S3 Versioning |
| Recover from certain accidental deletions | Versioning and appropriate recovery procedures |
| Retain protected records for a defined period | S3 Object Lock where appropriate |
| Recover from account or application failures | Separate backup and recovery procedures |
| Restore after a regional incident | An appropriately tested regional recovery architecture |
| Reduce the impact of compromised application credentials | Least privilege, separation of roles, and restrictive policies |

Versioning is not a complete backup strategy, and replication is not automatically an independent backup. A compromised identity or destructive operation can affect data according to the permissions and configuration in place.

Test restoration procedures rather than assuming that enabling a feature guarantees recovery.

## Security Verification Commands

Use these commands to inspect foundational bucket security settings. They are read-only checks.

### Verify Block Public Access

```bash
aws s3api get-public-access-block \
  --bucket example-prod-documents \
  --region ap-south-1
```

### Inspect bucket policy

```bash
aws s3api get-bucket-policy \
  --bucket example-prod-documents \
  --region ap-south-1
```

If no bucket policy exists, the command may return an error indicating that no policy is configured. That does not by itself establish whether access is secure; identity-based and other applicable policies must also be assessed.

### Verify default encryption

```bash
aws s3api get-bucket-encryption \
  --bucket example-prod-documents \
  --region ap-south-1
```

### Verify ownership controls

```bash
aws s3api get-bucket-ownership-controls \
  --bucket example-prod-documents \
  --region ap-south-1
```

### Inspect versioning

```bash
aws s3api get-bucket-versioning \
  --bucket example-prod-documents \
  --region ap-south-1
```

Versioning is a recovery and data-protection control, not an access-control mechanism.

### Verify effective security

These commands inspect individual settings but do not calculate every applicable permission. A complete review should also consider:

- IAM identity policies.
- Bucket and access point policies.
- Organization-level controls and applicable service control policies.
- Permissions boundaries and session policies.
- VPC endpoint policies and network conditions.
- KMS key policies and permissions when applicable.
- Application-level authorization.
- Public-access settings at the relevant organizational, account, bucket, and access point levels.

## Common Security Mistakes

### Treating encryption as access control

Encryption at rest does not prevent an authorized principal from retrieving plaintext data.

**Prevention:** Enforce least privilege, secure transport, and suitable data-access monitoring alongside encryption.

### Relying only on Block Public Access

Block Public Access prevents public access paths covered by its settings. It does not eliminate the need to review identities, resource policies, application authorization, and cross-account access.

**Prevention:** Review effective access across all relevant policy layers.

### Granting broad permissions to application roles

A compromised application role with unrestricted S3 access can expose or destroy more data than a narrowly scoped role.

**Prevention:** Scope permissions to required actions and resources, and separate roles by responsibility.

### Assuming object prefixes enforce tenant isolation

A prefix is a naming convention, not an independent security boundary.

**Prevention:** Enforce tenant authorization in the application and use IAM or resource policies where the architecture supports stronger isolation.

### Disabling public-access controls to fix an integration

Broadly disabling Block Public Access may solve an immediate configuration problem while exposing unrelated data.

**Prevention:** Identify the required access path and configure the narrowest suitable exception, if one is justified.

### Treating versioning as sufficient backup

Versioning may not protect against all destructive scenarios, including authorized permanent deletion of versions or other compromise.

**Prevention:** Define recovery objectives and test independent recovery procedures.

### Ignoring the cost and coverage of audit logging

Enabling only management events may leave object-level activity unaudited, while enabling extensive data events can add cost.

**Prevention:** Define audit requirements explicitly and select logging coverage accordingly.

## Production Security Checklist

- [ ] Application workloads use appropriate IAM roles or temporary credentials.
- [ ] IAM permissions follow least-privilege principles.
- [ ] Bucket and object policies reference the correct resource types.
- [ ] S3 Block Public Access is enabled at suitable levels.
- [ ] Public exposure is reviewed across relevant policies and ACL configurations.
- [ ] Bucket owner enforced Object Ownership is used where compatible.
- [ ] Encryption requirements are documented and verified.
- [ ] HTTPS/TLS is used for data in transit.
- [ ] SSE-KMS permissions are evaluated separately from S3 permissions where applicable.
- [ ] VPC endpoints and access point restrictions are tested against all legitimate access paths.
- [ ] Tenant access is enforced by trusted application authorization.
- [ ] Presigned URLs are short-lived and protected from disclosure.
- [ ] CloudTrail and other required logging sources provide the required audit coverage.
- [ ] Logs are protected and retained according to policy.
- [ ] Versioning, backups, retention controls, and recovery procedures match business requirements.
- [ ] Security settings are checked through automation and controlled infrastructure changes.
- [ ] Unauthorized access and configuration changes have an incident-response procedure.

## Official References

- [Security best practices for Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)
- [Access management for Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-access-management.html)
- [How Amazon S3 works with IAM](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security_iam_service-with-iam.html)
- [Blocking public access to Amazon S3 storage](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html)
- [Controlling object ownership and disabling ACLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/about-object-ownership.html)
- [Protecting data with server-side encryption](https://docs.aws.amazon.com/AmazonS3/latest/userguide/serv-side-encryption.html)
- [Protecting data in transit with encryption](https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingEncryptionInTransit.html)
- [Required permissions for Amazon S3 API operations](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-with-s3-policy-actions.html)
- [Logging Amazon S3 API calls with CloudTrail](https://docs.aws.amazon.com/AmazonS3/latest/userguide/cloudtrail-logging.html)
- [S3 Versioning](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html)
- [S3 Object Lock](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html)

## Key Takeaways

- Secure S3 deployments require layered identity, authorization, public-access, network, encryption, auditing, and recovery controls.
- Use temporary credentials, least-privilege policies, Block Public Access, and suitable Object Ownership settings as foundational protections.
- Encryption protects stored and transmitted data but does not replace authorization or tenant-level access checks.
- CloudTrail, CloudWatch, and appropriate logging provide evidence needed to investigate access and detect configuration changes.
- Validate security settings and recovery procedures continuously, preserving both data confidentiality and operational recoverability.