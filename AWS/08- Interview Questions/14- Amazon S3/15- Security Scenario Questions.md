# 15- Security Scenario Questions

## Overview

Amazon S3 security interviews evaluate how engineers protect object data against unauthorized access, accidental exposure, credential compromise, malicious uploads, destructive operations, and configuration errors.

A production-ready security design combines identity-based permissions, resource policies, encryption, data validation, audit logging, retention controls, and incident response. No single control replaces the others.

For S3-backed applications, security must be enforced across multiple boundaries: the authenticated application user, the backend workload identity, the S3 bucket, the encryption key, and any downstream processing or content-delivery service.

This document focuses on scenario-driven questions, diagnostic workflows, practical policies, and security trade-offs relevant to senior backend engineers.

## Scenario: A Private S3 Bucket Becomes Public

### Interview question

A security scanner reports that a bucket containing customer documents is publicly accessible. How would you investigate and contain the incident without destroying legitimate application access?

### What could have caused the exposure?

Potential causes include:

- A bucket policy grants access to anonymous principals.
- An access point policy grants unintended public access.
- An ACL grants public access on a bucket or object where ACLs are enabled.
- Block Public Access settings were weakened.
- An application or deployment pipeline introduced an unsafe policy.
- A related delivery configuration exposes content through another access path.

A public-access finding should be investigated against the effective configuration. Do not assume that the presence of a bucket policy alone proves that public access succeeds.

### How would you investigate?

Start by identifying the affected account, bucket, Region, data classification, and public-access finding.

Inspect the bucket's public-access settings and policy:

```bash
aws s3api get-public-access-block \
  --bucket company-prod-documents

aws s3api get-bucket-policy-status \
  --bucket company-prod-documents

aws s3api get-bucket-policy \
  --bucket company-prod-documents
```

Also inspect account-level Block Public Access, access points, relevant ACLs where enabled, and the delivery architecture.

Review CloudTrail management events to establish who changed the configuration and when. Determine whether the exposure was possible from the internet or whether the finding represents a narrower cross-account access path.

### How should the incident be contained?

If public access is not required, restore the approved Block Public Access configuration and remove the unintended policy grant.

For example, an approved emergency action may reapply all four bucket-level Block Public Access controls:

```bash
aws s3api put-public-access-block \
  --bucket company-prod-documents \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
```

Before making the change, understand the application's intended access path. A private S3 origin behind CloudFront may need a narrowly scoped resource policy, but it does not require unrestricted public access to the bucket.

After containment:

1. Determine which objects and time periods were exposed.
2. Inspect available CloudTrail, server access, and delivery logs.
3. Preserve relevant evidence and identify affected data.
4. Correct the infrastructure definition to prevent configuration drift.
5. Validate application functionality and public-access restrictions.
6. Review whether incident notification or regulatory procedures apply.

**Interview expectation:** Explain both immediate containment and the permanent correction. A console-only fix that is later overwritten by Terraform is not a durable remediation.

References: [S3 security best practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html), [Blocking public access](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html).

## Scenario: A Backend Workload Receives AccessDenied

### Interview question

A FastAPI application can upload files in development but receives `AccessDenied` in ECS after deployment. How would you identify the root cause?

### Which authorization layers must be checked?

Inspect the identity used by the running container before changing permissions.

| Layer | What to verify |
|---|---|
| Workload identity | Is the application using the expected ECS task role rather than unrelated credentials? |
| IAM identity policy | Does the task role allow the requested S3 action on the correct resource ARN? |
| Bucket policy | Is the principal allowed, or explicitly denied, by the bucket policy? |
| Permission boundary | Does a permissions boundary limit the role's effective permissions? |
| AWS Organizations | Could a service control policy (SCP) restrict the action? |
| VPC endpoint policy | If traffic uses an S3 VPC endpoint, does its policy permit the request? |
| Session policies | Are temporary credentials constrained by session policies? |
| KMS authorization | If SSE-KMS is involved, can the principal use the relevant key? |

An allow statement in an IAM policy is not sufficient when another applicable policy imposes an explicit deny or a permissions boundary prevents the requested access.

### How would you verify the running identity?

Run the following command using the same credential environment as the workload:

```bash
aws sts get-caller-identity
```

In ECS, execute an equivalent diagnostic within the intended task or use a controlled diagnostic task with the same task role.

Then inspect the requested bucket, key, Region, and operation. `PutObject`, `GetObject`, `ListBucket`, and `DeleteObject` require different permissions and resource scopes.

For example, a workload may have `s3:GetObject` on object ARNs but still be unable to list the bucket because `s3:ListBucket` applies to the bucket ARN.

### How would you fix the problem?

Correct the specific authorization boundary that blocks the operation. Do not grant `s3:*` on every bucket as the first diagnostic step.

A role dedicated to document uploads might need narrowly scoped permissions for the intended bucket and prefix. Its download and delete permissions should be granted separately when the workflow requires them.

Test both allowed and denied operations after the change. A successful upload does not prove that the role can read, delete, list, or decrypt every object.

Reference: [S3 access control](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-overview.html).

## Scenario: S3 Access Is Allowed but SSE-KMS Requests Fail

### Interview question

An application can access an S3 bucket, but uploads or downloads of SSE-KMS-encrypted objects fail with authorization errors. How would you distinguish an S3 permission problem from a KMS permission problem?

### Why are S3 and KMS authorization separate?

S3 authorization determines whether the principal can perform the object operation. KMS authorization determines whether the principal can use the encryption key where required.

Typical permissions include:

| Operation | Relevant permissions to investigate |
|---|---|
| Upload an SSE-KMS-encrypted object | S3 `s3:PutObject` and KMS `kms:GenerateDataKey` |
| Download an SSE-KMS-encrypted object | S3 `s3:GetObject` and KMS `kms:Decrypt` |
| Multipart SSE-KMS upload | Relevant S3 multipart permissions and required KMS permissions, which can include `kms:GenerateDataKey` and `kms:Decrypt` |
| Copy an encrypted object | Permissions for the source read/decryption and destination write/encryption paths, according to the keys involved |

The actual requirements depend on the operation, key configuration, and request parameters.

### What should be inspected?

Determine the object's encryption mode, the key ARN, the caller identity, and the exact failed API operation.

Inspect the bucket's default encryption configuration:

```bash
aws s3api get-bucket-encryption \
  --bucket company-prod-documents
```

Then review the IAM policy, KMS key policy, grants where applicable, and any cross-account key permissions. Use CloudTrail to correlate relevant S3 and KMS API events.

An S3 allow does not override a KMS key policy or a KMS authorization failure.

### How should it be corrected?

Grant only the key-use permissions required by the intended workload. Verify that the key policy permits the relevant principal or enables authorization through the appropriate IAM permissions.

For cross-account access, confirm that both the resource-owning account and the caller's account permit the required operation. KMS keys are Region-specific, so verify that the key and request use the intended Region.

Do not disable encryption to bypass the failure. Also verify that the key is enabled and usable; an inaccessible key can make encrypted data unavailable even when the S3 object still exists.

Reference: [Specifying SSE-KMS encryption](https://docs.aws.amazon.com/AmazonS3/latest/userguide/specifying-kms-encryption.html).

## Scenario: A Presigned URL Leaks

### Interview question

A presigned URL for a confidential customer document appears in application logs and is shared outside the organization. What is the security impact, and how would you respond?

### Why is this a security incident?

A presigned URL is a bearer credential. Anyone possessing a valid URL may perform the signed operation, subject to the signing principal's permissions, applicable policies, and the URL's effective validity.

For a presigned GET URL, the holder may be able to read the specific object. For a presigned PUT URL, the holder may upload to the specified key; an upload to an existing key can replace its current contents when the signed request permits it.

The URL's configured expiration is not always its effective lifetime. Temporary signing credentials may expire earlier, and policy or credential changes may invalidate access.

### What should be done immediately?

1. Identify the operation, bucket, key, expiration, signing identity, and disclosure scope.
2. Remove or restrict the location where the URL was disclosed, preserving necessary incident evidence.
3. Determine whether unauthorized access or upload activity occurred.
4. Invalidate access through an appropriate policy or credential response where justified.
5. Assess the document's sensitivity and follow the organization's incident procedures.
6. Review logs and correct the URL-handling defect.

Changing an application database record does not automatically revoke an already issued URL. Do not claim that an individual URL has been revoked until the effective access path has been invalidated.

### How should presigned URLs be designed securely?

Generate URLs only after authenticating the caller and authorizing access to the particular document. Use short, business-appropriate expirations, least-privilege signing identities, and server-generated object keys.

Never log the complete URL. Redact query strings from reverse-proxy logs, application logs, tracing systems, analytics, and error reporting. Avoid placing URLs in long-lived database fields unless that behavior is explicitly required and protected.

For browser-based uploads, validate the resulting object after upload. Presigned URL generation is not proof that an upload occurred or that the uploaded content is safe.

Reference: [Download and upload objects with presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html).

## Scenario: A Presigned Upload Replaces Another Tenant's Object

### Interview question

A client can request a presigned PUT URL for a key that already exists. How would you prevent cross-tenant overwrite attacks and unauthorized uploads?

### What is the design flaw?

The application may allow the client to choose an arbitrary object key or reuse a document identifier belonging to another tenant.

A presigned URL is restricted by the permissions of the principal that generated it, but the application must still decide whether that principal should be allowed to sign the requested operation for that key.

### What is the safer workflow?

- Authenticate the user and resolve the tenant from trusted identity claims.
- Create or authorize an application document record.
- Generate a unique, server-controlled upload key.
- Issue a presigned URL limited to the intended operation and key.
- Store the pending upload relationship in the database.
- Verify the resulting object and its metadata before accepting it into the business workflow.

Where overwrites are not allowed, use unique immutable keys or an appropriate conditional-write design. Consider versioning as a recovery mechanism, not as a replacement for authorization.

A client-provided document ID, filename, path, or tenant ID must not be accepted as proof of ownership.

### How should malicious content be handled?

The declared content type and filename extension are untrusted input. Validate file size, inspect actual content, and perform malware scanning or format-specific validation when the risk justifies it.

Keep newly uploaded objects quarantined or in a pending state until required checks pass. Ensure that downstream parsers and image-processing workers have appropriate isolation and resource limits.

## Scenario: Cross-Account Access Is Failing

### Interview question

A workload in Account A must read objects from a bucket in Account B. The destination bucket policy appears to allow the role, but requests still fail.

### What must be allowed?

Direct cross-account access generally requires authorization on both sides.

- In Account A, the caller's identity policy must allow the requested operation.
- In Account B, the bucket policy must allow the external principal or an approved access path.
- Any applicable SCPs, resource controls, permission boundaries, session policies, and explicit denies must also be considered.
- For SSE-KMS objects, key-use authorization must be configured separately.

### How would you troubleshoot the failure?

Check the actual assumed-role identity and the exact requested object ARN. Confirm that the bucket policy identifies the intended principal, that the identity policy references the correct bucket and object resources, and that the request targets the correct Region.

For larger integrations, consider having the consuming workload assume a dedicated role in the data-owning account. This creates a clear trust relationship and lets the destination account control the permissions attached to that role.

A bucket policy granting access is not sufficient if another applicable authorization layer denies the request.

Reference: [Cross-account policy evaluation](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic-cross-account.html).

## Scenario: A Security Team Finds Excessive S3 Permissions

### Interview question

An audit finds that several application roles have `s3:*` permissions over all buckets. How would you reduce risk without breaking production systems?

### What is the danger?

Broad permissions increase the impact of credential theft, application compromise, deployment mistakes, and malicious or accidental code paths.

An upload-only service may not need list, read, or delete permissions. A processing worker may need access to one input prefix and one output prefix but not the entire storage account.

### How would you redesign permissions?

Separate roles by workload responsibility.

| Role | Example responsibility |
|---|---|
| Upload API role | Create objects in an approved upload prefix |
| Download service role | Read authorized stored objects |
| Processing worker role | Read input objects and write processed outputs |
| Cleanup role | Delete only eligible objects under a controlled workflow |
| Audit role | Read required audit logs and configuration evidence |
| Deployment role | Manage explicitly approved infrastructure resources |

Use identity policies, resource policies, permission boundaries, and organizational guardrails as complementary controls. Avoid giving the runtime application role permissions needed only by the deployment pipeline.

### How should least privilege be validated?

Use access logs, CloudTrail events, application tracing, IAM policy analysis, and tests to determine which actions are actually needed.

After narrowing permissions, test legitimate workflows and verify that prohibited operations fail. Do not conclude that a permission is unnecessary merely because the main success path did not exercise it; include retries, cleanup, recovery, and administrative tasks in the assessment.

## Scenario: The Application Must Meet Strict Network Access Requirements

### Interview question

A regulated workload must access S3 only through approved network paths. How would you restrict and verify access without assuming that private networking alone proves authorization?

### What controls may be relevant?

Depending on the architecture, controls may include:

- S3 VPC endpoints.
- VPC endpoint policies.
- Bucket policies using appropriate network context.
- Private workload subnets and controlled egress.
- IAM and resource-based permissions.
- TLS requirements.
- Explicit public-access restrictions.

Network paths and identity permissions are different concerns. A private subnet does not automatically mean a principal can access only approved objects, and a VPC endpoint does not automatically grant the required S3 permissions.

### How should the policy be designed?

First identify whether workloads access S3 through a gateway endpoint, an interface endpoint where appropriate, or another supported route. Verify the endpoint policy and request context before enforcing restrictive network conditions.

A policy condition tied to a particular VPC endpoint can deny requests that do not use that endpoint. However, such a restriction can also disrupt legitimate AWS service integrations or administrative workflows if applied without understanding their request path.

Test backend operations, replication, logging, deployment, and recovery from every supported execution environment before enforcing the restriction.

### What is the security trade-off?

Network restrictions can reduce the number of accepted access paths, but overly restrictive conditions can block legitimate operations and complicate incident response.

Use network controls as defense in depth, not as a substitute for least-privilege IAM and resource policies.

## Scenario: Objects Are Deleted by a Compromised Role

### Interview question

A compromised workload role deletes important S3 objects. How would you contain the incident, determine the impact, and restore the data?

### Immediate response

Identify the role, affected buckets and prefixes, approximate time window, and known deletion operations.

Contain the compromised identity by following the organization's credential and permission-response process. Preserve CloudTrail records, application logs, and other relevant evidence before changing configurations that may be important to the investigation.

Identify which objects and versions were affected. A deletion in a versioned bucket may create a delete marker rather than permanently removing earlier versions, but versioning is not a guarantee that data cannot be destroyed by every privileged operation.

### How would you recover the data?

Inspect object versions and delete markers to determine what remains available. Restore the intended version using a controlled recovery process and verify both the object content and the application's metadata.

If an independent backup or cross-account retained copy exists, evaluate it as an additional recovery source. Confirm that the compromised workload cannot also delete that copy.

Do not automatically replay every deleted-object event as a restoration command. Confirm the business intent, the applicable version, and the current application state first.

### How would you prevent recurrence?

Use least-privilege runtime roles, protect backup and recovery permissions, enable appropriate audit logging, and monitor destructive operations.

For important data, evaluate versioning, independent retained copies, and S3 Object Lock where the required retention model justifies it. Test restoration procedures rather than relying on configuration alone.

Reference: [S3 Versioning](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html).

## Scenario: A Bucket Uses the Wrong Object Ownership or ACL Configuration

### Interview question

Objects uploaded by a different AWS account cannot be managed by the bucket owner. What is happening, and how should the architecture be corrected?

### Why can this occur?

Historically, objects could be owned by the account that uploaded them. That ownership model could prevent the bucket-owning account from managing every object through its expected access policies.

S3 Object Ownership provides a bucket-level ownership model. The recommended modern default is commonly **Bucket owner enforced**, which disables ACLs and makes the bucket owner own the objects.

### How should the problem be addressed?

For new designs, prefer policy-based access control and disabled ACLs unless a specific integration requires ACLs.

Before changing an existing bucket, inspect the application's upload headers, external-account integrations, policies, and any ACL-dependent workflows. An incompatible ACL request may fail after ACLs are disabled.

Validate permissions on existing objects and test uploads from every authorized account.

Do not re-enable ACLs simply because an upload fails. Determine whether the caller should be using policies and the supported ownership configuration.

Reference: [Controlling object ownership and disabling ACLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/about-object-ownership.html).

## Scenario: An Application Must Reject Insecure Transport

### Interview question

A compliance requirement mandates HTTPS for every S3 request. How can the requirement be enforced beyond application coding conventions?

### Why is application configuration alone insufficient?

A particular SDK might use TLS by default, but other clients, scripts, or credentials could make requests through a different path.

A resource policy can provide a server-side enforcement boundary that denies non-TLS requests for the protected bucket.

An illustrative deny statement is:

```json
{
  "Sid": "DenyInsecureTransport",
  "Effect": "Deny",
  "Principal": "*",
  "Action": "s3:*",
  "Resource": [
    "arn:aws:s3:::company-prod-documents",
    "arn:aws:s3:::company-prod-documents/*"
  ],
  "Condition": {
    "Bool": {
      "aws:SecureTransport": "false"
    }
  }
}
```

Validate the policy alongside legitimate service integrations and any existing explicit-deny statements before deployment.

The statement protects against insecure transport; it does not authorize otherwise prohibited S3 operations or prove that the application uses least privilege.

## Scenario: Encryption Requirements Are Not Being Enforced

### Interview question

An organization requires approved encryption for all newly uploaded documents and needs to demonstrate compliance. How would you enforce and verify the requirement?

### What should be considered?

Identify the required encryption mode and key-management boundary.

S3 automatically applies server-side encryption to new object uploads, but an organization may require a specific SSE-KMS key or another approved configuration rather than relying solely on default SSE-S3 encryption.

Use bucket default encryption, appropriate bucket policies, and key policies according to the requirement. Ensure that the workload has the permissions required for the chosen encryption mode.

### How would you verify compliance?

Inspect the bucket encryption configuration and sample object metadata, then use suitable inventory or audit mechanisms for larger datasets.

For example:

```bash
aws s3api get-bucket-encryption \
  --bucket company-prod-documents

aws s3api head-object \
  --bucket company-prod-documents \
  --key tenants/tenant-123/documents/doc-001/original
```

For SSE-KMS, verify the key ARN as well as the encryption mode. An object being encrypted does not prove that it uses the required customer-managed key.

Do not treat encryption at rest as a replacement for access controls, TLS, data-retention policies, or secure handling of presigned URLs.

## Scenario: A Workload Must Share Access with CloudFront

### Interview question

A frontend requires global content delivery, but the S3 origin must remain private. How do you prevent a direct-origin bypass?

### Recommended design

Use CloudFront with Origin Access Control and an S3 bucket policy restricted to the intended distribution. Keep Block Public Access enabled where compatible with the complete design.

The application should still separate public static assets from private documents. A configuration appropriate for immutable public assets may be unsuitable for sensitive user content.

### How would you investigate a `403` response?

Determine whether the denial originates from CloudFront, the bucket policy, object permissions, the origin configuration, or KMS authorization.

Check the requested path, distribution origin, OAC signing configuration, bucket policy, and relevant logs. Verify that the exact object key exists and that the permitted access path matches the deployment.

Do not resolve the problem by making the origin bucket publicly readable. Correct the failed origin authorization while retaining the intended private-access architecture.

## Scenario: Security Auditing Does Not Show Object Downloads

### Interview question

An auditor asks who downloaded a particular document, but the CloudTrail event history contains no matching object-read event. What would you investigate?

### Why might the record be missing?

CloudTrail management-event history does not automatically provide a complete object-level audit history. S3 object-level data events must be configured for the required resources and operations.

Other possibilities include querying the wrong account or Region, using the wrong time window, selecting an incomplete destination, or searching for an incorrect object ARN.

### How would you investigate?

1. Confirm whether object-level CloudTrail data events were enabled during the relevant period.
2. Inspect the trail or event data store's selectors.
3. Check the centralized log destination and retention window.
4. Search the available records and correlate them with application and delivery logs.
5. Determine whether the request used a direct S3 path, a presigned URL, or CloudFront.
6. Document any gap in the available evidence.

Do not claim that a download did not occur simply because the required event is absent.

### How should monitoring be improved?

Enable the required data-event selectors, test the audit path with controlled object operations, and protect the resulting records in an appropriate destination.

For a sensitive bucket, capture only the required event scope where suitable, while preserving the coverage needed for incident investigation.

Reference: [Logging S3 API calls with CloudTrail](https://docs.aws.amazon.com/AmazonS3/latest/userguide/cloudtrail-logging.html).

## Scenario: A Public-Access Guardrail Breaks a Deployment

### Interview question

A deployment pipeline attempts to create a policy or ACL that allows public access, but the operation fails. How should the issue be resolved?

### What might be happening?

Block Public Access may be configured at the account or bucket level. Organization-level controls or deployment-role permissions may also prevent the change.

An `AccessDenied` response does not prove that Block Public Access caused the problem. Inspect the effective configuration, caller identity, and failure details.

### What is the correct response?

Determine whether public access is a legitimate requirement. For static web delivery, a private S3 origin and CloudFront OAC are usually preferable to a public bucket.

If the change is genuinely required, review it through the organization's security exception process rather than disabling broad protections to make the pipeline succeed.

Update infrastructure code, security checks, and deployment validation so the pipeline expresses the approved access model.

### How should it be prevented?

Validate bucket policies, Block Public Access, Object Ownership, and cross-account resource policies in CI/CD. Test infrastructure plans and policy changes before applying them to production.

Ensure that security exceptions are documented, narrowly scoped, and monitored.

## Scenario: A Security Incident Requires Object-Level and Identity-Level Evidence

### Interview question

A suspicious application role is suspected of reading and deleting customer data. How do you construct a reliable investigation timeline?

### Which evidence sources should be combined?

| Evidence source | Investigative value |
|---|---|
| CloudTrail data events | S3 object API activity and available caller context |
| CloudTrail management events | Bucket and policy changes |
| S3 server access logs | Detailed records of relevant requests |
| Application logs | Authenticated user, tenant, and business transaction context |
| CloudWatch metrics | Request and failure trends |
| Database audit records | Document ownership and business state |
| IAM configuration history | Role, policy, and trust changes |
| S3 Inventory and version information | Broad object-state assessment and recovery analysis |

Each source has different coverage and delivery characteristics. Correlate timestamps, principal identifiers, object keys, request identifiers where available, and business identifiers.

### How should the investigation proceed?

Establish the time window and identity, preserve evidence, identify affected objects, and determine which actions succeeded. Then assess whether data was read, overwritten, deleted, or merely made inaccessible through a policy change.

Use version information and retained backups to evaluate recovery options. Apply access containment without destroying evidence, and record where the available telemetry does not support a definitive conclusion.

## Common S3 Security Mistakes

| Mistake | Risk | Better practice |
|---|---|---|
| Making a bucket public to simplify delivery | Unintended data exposure and origin bypass | Prefer private buckets and controlled access paths |
| Using broad `s3:*` permissions | Larger compromise impact | Apply least privilege by workload and resource |
| Treating a presigned URL as a harmless link | Bearer-token disclosure can expose data or allow writes | Use short expirations and redact URLs from logs |
| Trusting client filenames or tenant IDs | Path manipulation, collisions, or cross-tenant access | Generate object keys server-side |
| Assuming SSE-KMS is covered by S3 permissions | Encryption operations may fail or be over-authorized | Configure and validate S3 and KMS authorization separately |
| Re-enabling ACLs without need | Ownership and access-management complexity | Prefer Bucket owner enforced Object Ownership |
| Assuming versioning is a complete backup | Privileged deletion or retention failures can still cause data loss | Use independent recovery controls and test restoration |
| Assuming absent audit records prove absent activity | Incorrect incident conclusions | Verify logging coverage and investigate evidence gaps |
| Applying policy changes directly in production | Configuration drift and regression | Use controlled infrastructure changes and post-deployment verification |
| Disabling security controls to fix deployments | Temporary workarounds become persistent exposures | Correct the policy or pipeline to match the approved design |

## Security Review Checklist

Before approving an S3-backed application, verify that:

- [ ] Buckets are private by default and Block Public Access remains enabled unless an approved exception exists.
- [ ] Object Ownership and ACL settings match the intended access model.
- [ ] Application roles use temporary credentials and least-privilege permissions.
- [ ] Cross-account authorization is configured and tested on both sides.
- [ ] S3 and KMS authorization are evaluated separately.
- [ ] Presigned URLs are issued only after application authorization and are protected from logging and disclosure.
- [ ] Uploads use server-controlled keys and appropriate size and content validation.
- [ ] Sensitive objects are not served through unintended public or cached access paths.
- [ ] TLS and required encryption controls are enforced.
- [ ] Versioning, retention, backup, and recovery requirements are explicitly defined.
- [ ] CloudTrail data-event coverage is enabled where object-level auditing is required.
- [ ] Security findings and configuration drift are monitored.
- [ ] Incident response includes containment, evidence preservation, recovery, and regression testing.

## Authoritative References

- [Amazon S3 security best practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)
- [S3 access control](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-overview.html)
- [Blocking public access to S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html)
- [Download and upload objects with presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html)
- [Cross-account policy evaluation](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic-cross-account.html)
- [Specifying SSE-KMS encryption](https://docs.aws.amazon.com/AmazonS3/latest/userguide/specifying-kms-encryption.html)
- [Logging S3 API calls with CloudTrail](https://docs.aws.amazon.com/AmazonS3/latest/userguide/cloudtrail-logging.html)
- [S3 Versioning](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html)
- [Controlling object ownership and disabling ACLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/about-object-ownership.html)
- [Restrict access to an S3 origin with CloudFront](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html)

## Key Takeaways

- Treat S3 security as a combination of identity permissions, resource policies, encryption authorization, network controls, and application-level access decisions.
- Keep buckets private by default, use least-privilege workload roles, and avoid relying on object-key secrecy or presigned URLs as authorization systems.
- Investigate S3 and KMS failures independently, and account for cross-account policies, explicit denies, and organizational guardrails.
- For security incidents, preserve evidence, contain access, establish the scope, and validate recovery rather than making unverified assumptions.
- Test security controls through both permitted and prohibited operations, and maintain durable audit coverage and infrastructure-as-code guardrails.