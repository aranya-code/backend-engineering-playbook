# 05- Origin Access Control

## Overview

Origin Access Control (OAC) is the recommended CloudFront mechanism for securing access from a CloudFront distribution to supported AWS origins, particularly Amazon S3.

The core security objective is to make the architecture behave like:

```text
Internet
   │
   ▼
CloudFront
   │
   │ authenticated origin request
   ▼
S3 / Origin
```

rather than:

```text
Internet
   │
   ├──────────────► CloudFront ─────► Origin
   │
   └───────────────────────────────► Origin
```

The second architecture creates a bypass path. If the origin is directly reachable, an attacker may avoid CloudFront controls such as:

- AWS WAF
- CloudFront caching
- CloudFront rate controls
- CloudFront geographic controls
- CloudFront TLS configuration
- Other edge-level policies

OAC addresses this problem by allowing CloudFront to authenticate requests to the origin using AWS Signature Version 4 (SigV4).

For S3 origins, the preferred production architecture is generally:

```text
Client
  │
  │ HTTPS
  ▼
CloudFront
  │
  │ OAC + SigV4
  ▼
Private S3 bucket
```

OAC is primarily an **origin authentication and authorization mechanism**. It does not replace:

- AWS WAF
- AWS Shield
- CloudFront TLS
- S3 encryption
- Application authentication
- Application authorization

## Why Origin Access Control Exists

A CloudFront distribution can serve content from an S3 bucket, but simply configuring S3 as an origin does not automatically mean the bucket is securely restricted to CloudFront.

Consider a public S3 bucket:

```text
Internet
   │
   ├────────► CloudFront
   │
   └────────► S3
```

An attacker can potentially bypass CloudFront entirely.

This creates several problems:

| Problem | Impact |
|---|---|
| Origin bypass | Requests avoid CloudFront security controls |
| Cache bypass | Every request can reach S3 |
| Cost leakage | Direct origin requests can increase costs |
| Inconsistent security | CloudFront and direct-origin policies differ |
| Exposure | Objects may become directly accessible |

The preferred model is:

```text
Internet
   │
   ▼
CloudFront
   │
   ▼
OAC
   │
   ▼
S3
```

S3 should trust CloudFront rather than the public internet.

## OAC vs Origin Access Identity

OAC replaced the older Origin Access Identity (OAI) model for S3 origins.

| Capability | OAI | OAC |
|---|---|---|
| S3 origin access | Yes | Yes |
| SigV4 signing | Limited/older model | Yes |
| AWS KMS integration | More limited | Better support |
| Dynamic HTTP methods | More limited | Supports broader methods |
| Recommended for new designs | No | Yes |
| Fine-grained modern authorization | Limited | Better |

For new CloudFront/S3 architectures, prefer OAC unless a specific legacy constraint requires OAI.

## How OAC Works

The simplified request flow is:

```text
Client
  │
  │ HTTPS
  ▼
CloudFront
  │
  │ Determine origin
  │
  ▼
Origin Access Control
  │
  │ Sign origin request with SigV4
  ▼
S3
  │
  │ Evaluate bucket policy
  ▼
Object
```

CloudFront creates an origin request and signs it using AWS SigV4.

S3 evaluates the resulting request against the bucket policy.

Conceptually:

```text
CloudFront
    │
    │ Authorization: AWS4-HMAC-SHA256 ...
    │ X-Amz-Date: ...
    │ X-Amz-Content-SHA256: ...
    ▼
S3
    │
    ▼
Bucket policy evaluation
```

If the bucket policy allows the CloudFront service principal to access the requested resource, S3 serves the object.

Otherwise:

```text
S3
 │
 └──► AccessDenied
```

## Origin Access Control Configuration

An OAC defines how CloudFront signs requests sent to the origin.

The important configuration concept is the signing behavior.

For modern S3 architectures, the normal configuration is to have CloudFront sign origin requests.

Conceptually:

```text
Signing behavior
       │
       ▼
Always sign requests
       │
       ▼
CloudFront → S3
```

This ensures origin requests have authenticated AWS credentials/signatures rather than relying on anonymous access.

## S3 Bucket Policy

The OAC itself does not grant CloudFront access by magically overriding S3 permissions.

The S3 bucket policy must authorize the CloudFront service principal.

A representative policy looks like:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCloudFrontServicePrincipalReadOnly",
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudfront.amazonaws.com"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::example-private-assets/*",
      "Condition": {
        "StringEquals": {
          "AWS:SourceArn": "arn:aws:cloudfront::<ACCOUNT_ID>:distribution/<DISTRIBUTION_ID>"
        }
      }
    }
  ]
}
```

The important security properties are:

- `Principal` is the CloudFront service.
- `Action` is restricted to the required S3 operation.
- `Resource` identifies the objects that CloudFront may access.
- `AWS:SourceArn` restricts access to a specific CloudFront distribution.

This is substantially stronger than:

```json
{
  "Principal": "*",
  "Action": "s3:GetObject"
}
```

which effectively makes the objects publicly readable.

## Restricting the Bucket to CloudFront

The desired security state is:

```text
Public Internet
      │
      │
      X
      │
      ▼
   S3 Bucket
      ▲
      │
      │ Authorized
      │
CloudFront Distribution
```

The S3 bucket should not need to accept arbitrary anonymous `GetObject` requests.

Instead:

```text
Client
  │
  ▼
CloudFront
  │
  │ authenticated
  ▼
S3
```

This creates CloudFront as the intended public access boundary.

## S3 Block Public Access

For private CloudFront-backed S3 buckets, S3 Block Public Access should normally remain enabled.

A typical security posture is:

```text
S3 Bucket
├── Block Public ACLs
├── Ignore Public ACLs
├── Block Public Bucket Policies
└── Restrict Public Bucket Policies
```

The exact account and bucket configuration should be reviewed against the application's requirements.

OAC does not require making the bucket public.

In fact, the security objective is usually the opposite: keep the bucket private and grant CloudFront the minimum required access.

## OAC and KMS Encryption

OAC is particularly useful when objects are encrypted using AWS Key Management Service (KMS).

The access path becomes:

```text
CloudFront
   │
   │ OAC / SigV4
   ▼
S3
   │
   │ KMS-encrypted object
   ▼
AWS KMS
```

For SSE-KMS protected objects, permissions must be configured correctly across both S3 and KMS.

The relevant security layers become:

```text
CloudFront
    │
    ▼
S3 bucket policy
    │
    ▼
S3 object
    │
    ▼
KMS key policy / IAM permissions
```

A common production mistake is configuring the S3 bucket policy correctly but forgetting that KMS authorization is a separate control plane.

## OAC and SSE-KMS

For a KMS-encrypted S3 origin, verify:

- CloudFront can access the S3 object.
- The KMS key policy allows the required CloudFront service access.
- The key is in an appropriate AWS Region for the S3 data.
- The CloudFront distribution is correctly associated with the OAC.
- The bucket policy is correctly scoped.

The exact KMS policy should be generated according to the current AWS service integration and least-privilege requirements rather than copied blindly between environments.

## OAC Request Lifecycle

A more detailed request lifecycle is:

```mermaid
sequenceDiagram
    participant C as Client
    participant CF as CloudFront
    participant W as AWS WAF
    participant S3 as Private S3
    participant KMS as AWS KMS

    C->>CF: HTTPS request
    CF->>W: Evaluate request
    W-->>CF: Allow
    CF->>CF: Check cache
    alt Cache hit
        CF-->>C: Cached response
    else Cache miss
        CF->>CF: Create origin request
        CF->>CF: Sign request using OAC / SigV4
        CF->>S3: Authenticated request
        S3->>S3: Evaluate bucket policy
        opt SSE-KMS object
            S3->>KMS: Authorize/decrypt data key
            KMS-->>S3: Authorization
        end
        S3-->>CF: Object response
        CF-->>C: Response
    end
```

This separation is important because each layer has a different responsibility.

## OAC and CloudFront Caching

OAC is involved when CloudFront needs to communicate with the origin.

A cache hit may not require an origin request at all:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
Cache hit
  │
  ▼
Response
```

For a cache miss:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
Cache miss
  │
  ▼
OAC
  │
  ▼
S3
```

This means OAC does not add a SigV4 request to every cache hit going back to S3 because cache hits do not require an origin fetch.

## Origin Request Signing

CloudFront signs the request it sends to the origin.

At a conceptual level:

```text
Origin request
      │
      ├── HTTP method
      ├── URI
      ├── Headers
      └── Timestamp
             │
             ▼
       Canonical request
             │
             ▼
          SigV4
             │
             ▼
      Signed HTTP request
```

S3 can then verify the request and determine whether the request is authorized.

The exact cryptographic implementation should be treated as AWS-managed behavior; application developers do not manually implement SigV4 for OAC.

## OAC Does Not Sign Client Requests

A common misunderstanding is:

```text
Client
   │
   │ SigV4
   ▼
CloudFront
```

That is not what OAC means.

The client generally sends a normal HTTPS request:

```text
Client
   │
   │ HTTPS
   ▼
CloudFront
```

CloudFront then signs the request that it sends to the origin:

```text
Client
   │
   ▼
CloudFront
   │
   │ OAC / SigV4
   ▼
S3
```

This distinction is fundamental.

## OAC for Private Static Websites

A common architecture is hosting a frontend application in S3 while keeping the bucket private.

For example:

```text
Browser
   │
   ▼
CloudFront
   │
   ├── AWS WAF
   ├── TLS
   └── Cache
          │
          ▼
       OAC
          │
          ▼
      Private S3
          │
          ├── index.html
          ├── assets/
          ├── JavaScript
          └── CSS
```

The browser never needs direct S3 access.

CloudFront becomes the public delivery endpoint.

## OAC for Media Assets

The same pattern works for protected media assets:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
OAC
  │
  ▼
Private S3
  │
  ├── images/
  ├── videos/
  └── documents/
```

This is useful when objects should be distributed globally but should not be publicly accessible through their S3 URLs.

## OAC for Downloadable Files

Consider a Django or FastAPI application storing generated files in S3:

```text
Application
    │
    ▼
Private S3
    │
    ├── invoices/
    ├── reports/
    └── exports/
```

CloudFront can distribute the files without making the S3 bucket public.

The application can expose:

```text
https://cdn.example.com/reports/report-123.pdf
```

while the underlying S3 object remains private.

## OAC vs Presigned URLs

OAC and presigned URLs solve different problems.

| Requirement | OAC | Presigned URL |
|---|---|---|
| Keep S3 private | Yes | Yes |
| CloudFront-to-S3 authentication | Yes | Not the primary purpose |
| User-specific temporary access | No | Yes |
| Time-limited object access | Not by itself | Yes |
| Edge distribution | Yes | Can be combined |
| Per-user authorization | Usually application-controlled | Yes, through URL issuance |
| Primary use | Origin authorization | Temporary delegated access |

A common architecture for private downloads is:

```text
User
  │
  ▼
Django / FastAPI
  │
  │ Authenticate + authorize
  ▼
CloudFront URL
  │
  │ Signed URL / cookie where appropriate
  ▼
CloudFront
  │
  │ OAC
  ▼
Private S3
```

This creates two separate authorization decisions:

```text
Application
    │
    └── Can this user access the object?

CloudFront
    │
    └── Can CloudFront access the S3 origin?
```

These should not be confused.

## OAC vs S3 Bucket Policies

OAC and the S3 bucket policy work together.

Think of the relationship as:

```text
OAC
 │
 │ Causes CloudFront to sign requests
 ▼
Signed origin request
 │
 ▼
S3 bucket policy
 │
 │ Decides whether request is authorized
 ▼
Object
```

OAC provides the mechanism for CloudFront to authenticate to the origin.

The bucket policy defines what that authenticated CloudFront principal is allowed to do.

## Least Privilege

A production OAC configuration should follow least privilege.

Prefer:

```text
CloudFront
  │
  └── s3:GetObject
          │
          └── specific bucket/object resources
```

over:

```text
CloudFront
  │
  └── s3:*
```

Similarly, avoid granting access to unrelated buckets.

A useful policy design asks:

- Which distribution?
- Which bucket?
- Which objects?
- Which actions?
- Which AWS account?
- Which encryption key?
- Which environments?

## Environment Isolation

Development, staging, and production should generally use separate resources.

For example:

```text
Development
CloudFront Dev
      │
      ▼
S3 Dev

Staging
CloudFront Staging
      │
      ▼
S3 Staging

Production
CloudFront Production
      │
      ▼
S3 Production
```

Avoid a production distribution using a broad policy that grants access to every bucket in the account.

Environment-specific policies reduce blast radius.

## Cross-Account Architecture

OAC can be used in architectures where CloudFront and the S3 bucket have different ownership or account boundaries, provided the relevant AWS resource policies and permissions are configured correctly.

Conceptually:

```text
Account A
CloudFront
    │
    │ OAC
    ▼
Account B
Private S3
```

The important point is that cross-account authorization must be explicitly modeled.

Do not assume that:

```text
same organization
```

automatically means:

```text
authorized
```

Review:

- S3 bucket policy
- AWS account IDs
- CloudFront distribution ARN
- KMS policy where applicable
- Object ownership
- Organizational security controls

## Origin Shield and OAC

Origin Shield and OAC solve different problems.

| Feature | Responsibility |
|---|---|
| OAC | Authenticate CloudFront to origin |
| Origin Shield | Add an additional centralized CloudFront caching layer |

A high-scale architecture may use both:

```text
Clients
   │
   ▼
CloudFront Edge
   │
   ▼
Origin Shield
   │
   ▼
OAC
   │
   ▼
S3
```

OAC does not improve cache efficiency. Origin Shield and cache configuration address that concern.

## OAC with Custom Origins

OAC is primarily associated with CloudFront's authenticated access to supported AWS origins, especially S3. Custom origins such as ALB, EC2, or an external HTTP server have different origin authentication patterns.

For an application origin:

```text
CloudFront
   │
   ▼
ALB
   │
   ▼
Django / FastAPI
```

origin protection may instead involve:

- HTTPS
- Security groups
- Private networking
- Custom headers where appropriate
- Origin validation
- Application authentication
- Network controls

Do not assume that an S3 OAC configuration can simply be transferred to an arbitrary HTTP origin.

## OAC and ALB-Based Applications

A typical API architecture might be:

```text
Internet
   │
   ▼
CloudFront
   │
   ├── AWS WAF
   ├── TLS
   └── Caching / routing
          │
          ▼
         ALB
          │
          ▼
   Django / FastAPI
```

The security model differs from S3.

For example, the ALB can be protected using security groups and application-level mechanisms rather than an S3 bucket policy.

For sensitive applications, consider whether CloudFront should be the only public path to the ALB and design the network boundary accordingly.

## Direct Origin Access

The most important operational question is:

> Can a client bypass CloudFront and reach the origin directly?

For S3:

```text
https://bucket.s3.amazonaws.com/object
```

should not provide unrestricted access merely because CloudFront is configured.

The desired result is:

```text
CloudFront URL
     │
     ▼
Allowed

Direct S3 URL
     │
     ▼
Denied
```

Test both paths during security validation.

## Testing OAC

A useful validation procedure is:

1. Request the object through CloudFront.
2. Verify the CloudFront request succeeds.
3. Request the S3 object directly.
4. Verify the direct request is denied.
5. Inspect CloudFront and S3 logs where required.
6. Test object access after changing permissions.
7. Test encrypted objects if SSE-KMS is used.

Example:

```bash
curl -I https://cdn.example.com/assets/app.js
```

Then test the direct S3 endpoint:

```bash
curl -I https://example-private-assets.s3.amazonaws.com/assets/app.js
```

The expected security posture is:

```text
CloudFront URL  →  200 / expected response

Direct S3 URL   →  Access denied
```

The exact response may vary based on the endpoint and configuration.

## AWS CLI Inspection

List CloudFront distributions:

```bash
aws cloudfront list-distributions
```

Inspect a specific distribution:

```bash
aws cloudfront get-distribution \
  --id <DISTRIBUTION_ID>
```

List OACs:

```bash
aws cloudfront list-origin-access-controls
```

Inspect an OAC:

```bash
aws cloudfront get-origin-access-control \
  --id <OAC_ID>
```

Inspect the S3 bucket policy:

```bash
aws s3api get-bucket-policy \
  --bucket example-private-assets
```

Check public access configuration:

```bash
aws s3api get-public-access-block \
  --bucket example-private-assets
```

These commands are useful during troubleshooting and security reviews.

## Infrastructure as Code

OAC should be managed as infrastructure rather than manually configured and forgotten.

A simplified Terraform configuration can look like:

```hcl
resource "aws_cloudfront_origin_access_control" "s3" {
  name                              = "private-assets-oac"
  description                       = "CloudFront access to private S3 assets"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}
```

The CloudFront distribution then references the OAC:

```hcl
resource "aws_cloudfront_distribution" "cdn" {
  enabled = true

  origin {
    domain_name              = aws_s3_bucket.assets.bucket_regional_domain_name
    origin_id                = "s3-assets"
    origin_access_control_id = aws_cloudfront_origin_access_control.s3.id
  }

  default_cache_behavior {
    target_origin_id       = "s3-assets"
    viewer_protocol_policy = "redirect-to-https"

    allowed_methods = ["GET", "HEAD"]
    cached_methods  = ["GET", "HEAD"]

    forwarded_values {
      query_string = false

      cookies {
        forward = "none"
      }
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}
```

For new production infrastructure, prefer current CloudFront cache-policy and origin-request-policy constructs rather than relying on older legacy forwarding configuration.

## Terraform S3 Bucket Policy

A corresponding policy can be represented as:

```hcl
data "aws_iam_policy_document" "cloudfront_s3" {
  statement {
    sid    = "AllowCloudFrontServicePrincipalReadOnly"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.assets.arn}/*"]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"

      values = [
        aws_cloudfront_distribution.cdn.arn
      ]
    }
  }
}

resource "aws_s3_bucket_policy" "assets" {
  bucket = aws_s3_bucket.assets.id
  policy = data.aws_iam_policy_document.cloudfront_s3.json
}
```

The policy should be reviewed as part of infrastructure security review.

## Migration from OAI to OAC

Legacy CloudFront deployments may use Origin Access Identity.

A controlled migration is preferable to changing access policies abruptly.

A safe conceptual sequence is:

```text
Existing OAI
    │
    ▼
Create OAC
    │
    ▼
Update S3 policy
    │
    ▼
Configure CloudFront origin
    │
    ▼
Deploy distribution
    │
    ▼
Validate CloudFront access
    │
    ▼
Validate direct S3 denial
    │
    ▼
Remove obsolete OAI permissions
```

Do not remove the old S3 permission before the new CloudFront path has been validated.

## Common Mistakes and Pitfalls

### Making the S3 Bucket Public

**Problem:** The bucket policy allows anonymous `s3:GetObject`.

**Why it happens:** Developers verify that CloudFront works by making the bucket public.

**Correction:** Keep S3 private and explicitly authorize the CloudFront service principal through the bucket policy.

### Creating OAC but Forgetting the Bucket Policy

**Problem:** CloudFront returns origin authorization errors.

**Why it happens:** OAC controls signing, but S3 still needs an authorization policy.

**Correction:** Configure both the CloudFront OAC and the S3 bucket policy.

### Using the Wrong Distribution ARN

**Problem:** S3 rejects CloudFront requests.

**Why it happens:** The bucket policy's `AWS:SourceArn` does not match the actual distribution.

**Correction:** Use the exact CloudFront distribution ARN.

### Granting `s3:*`

**Problem:** CloudFront receives excessive permissions.

**Correction:** Grant only required actions such as `s3:GetObject`.

### Leaving Direct Origin Access Open

**Problem:** Attackers can access objects without CloudFront.

**Correction:** Test direct S3 access explicitly and keep public access blocked.

### Confusing OAC with Signed URLs

**Problem:** Teams expect OAC to provide per-user access control.

**Correction:** Use CloudFront signed URLs/cookies or application authorization when users require temporary or identity-specific access.

### Forgetting KMS Permissions

**Problem:** CloudFront can reach S3 but encrypted objects fail.

**Correction:** Review KMS key policy and authorization in addition to the S3 bucket policy.

### Assuming OAC Protects Every Origin

**Problem:** An S3-oriented OAC design is copied to an arbitrary HTTP origin.

**Correction:** Use the appropriate origin authentication and network controls for the origin type.

### Testing Only Through CloudFront

**Problem:** The team verifies that the normal URL works but never tests the origin directly.

**Correction:** Always test both the intended access path and the bypass path.

## Security Best Practices

### Keep S3 Private

Prefer:

```text
S3
├── Block Public Access
├── No anonymous object access
└── CloudFront-specific bucket policy
```

### Restrict CloudFront Access

Scope the bucket policy to:

- CloudFront service principal
- Specific distribution ARN
- Required S3 actions
- Required object resources

### Use SigV4

For modern S3 CloudFront architectures:

```text
OAC
  │
  ▼
SigV4
  │
  ▼
S3
```

### Encrypt Sensitive Data

Use appropriate S3 encryption, including SSE-KMS when stronger key-management controls are required.

### Protect the Distribution

Combine OAC with:

```text
CloudFront
├── HTTPS
├── AWS WAF
├── AWS Shield
├── Security headers
└── Appropriate cache policies
```

### Manage with IaC

Store:

- OAC configuration
- CloudFront distribution
- S3 bucket policy
- Public access configuration
- KMS policies
- WAF configuration

in version-controlled infrastructure code.

## Production Architecture

A production static-content architecture can look like:

```mermaid
flowchart LR
    USER[Browser / Client]
    CF[CloudFront]
    WAF[AWS WAF]
    OAC[Origin Access Control]
    S3[(Private S3 Bucket)]
    KMS[AWS KMS]

    USER -->|HTTPS| CF
    CF --> WAF
    WAF --> CF
    CF -->|Cache miss| OAC
    OAC -->|SigV4| S3
    S3 -->|Decrypt when required| KMS
    S3 --> OAC
    OAC --> CF
    CF --> USER
```

The security boundaries are intentionally layered:

```text
Client
  │
  ▼
CloudFront
  │
  ├── TLS
  ├── WAF
  ├── Cache
  └── OAC
         │
         ▼
       S3
         │
         └── KMS
```

## Production Checklist

### CloudFront

- [ ] CloudFront is the intended public access path.
- [ ] HTTPS is configured.
- [ ] Appropriate cache policies are configured.
- [ ] AWS WAF is associated where required.
- [ ] Origin access is explicitly configured.

### OAC

- [ ] OAC exists for the S3 origin.
- [ ] Signing protocol is SigV4.
- [ ] Signing behavior is appropriate.
- [ ] CloudFront origin references the correct OAC.
- [ ] Legacy OAI configuration has been removed where no longer required.

### S3

- [ ] S3 Block Public Access is enabled.
- [ ] Anonymous object access is disabled.
- [ ] Bucket policy grants only required CloudFront access.
- [ ] `AWS:SourceArn` is restricted to the intended distribution.
- [ ] S3 actions follow least privilege.

### Encryption

- [ ] S3 encryption is enabled.
- [ ] KMS permissions are configured when SSE-KMS is used.
- [ ] Key policies are reviewed separately from bucket policies.

### Validation

- [ ] CloudFront URL works.
- [ ] Direct S3 URL is denied.
- [ ] Existing cached content behaves as expected.
- [ ] New objects are accessible through CloudFront.
- [ ] Deleted/restricted objects are no longer accessible as intended.
- [ ] Logging and monitoring are available for troubleshooting.

## Interview Traps

### Does OAC Make the S3 Bucket Public?

No. The purpose is generally to keep the bucket private and allow CloudFront to access it through an authenticated origin request.

### Is OAC the Same as OAI?

No. OAI is the older CloudFront mechanism for S3 origin access. OAC is the recommended modern approach for new S3 integrations.

### Does OAC Authenticate the End User?

No. OAC authenticates CloudFront to the origin. End-user authentication remains the responsibility of the application or CloudFront's signed URL/cookie mechanisms where applicable.

### Does OAC Replace the S3 Bucket Policy?

No. OAC causes CloudFront to sign the origin request. S3 still evaluates its bucket policy and other authorization controls.

### Does OAC Encrypt S3 Objects?

No. OAC is about origin access authentication. Object encryption is a separate S3/KMS concern.

### Does OAC Prevent Direct S3 Access Automatically?

Not by itself. The S3 permissions must be configured so that unauthorized direct access is denied.

### Does OAC Replace WAF?

No. WAF filters HTTP requests. OAC controls CloudFront-to-origin authorization.

### Why Is the Distribution ARN Important?

Restricting the S3 policy to the intended CloudFront distribution reduces the possibility that another distribution can use the same authorization path.

## Key Takeaways

- **OAC allows CloudFront to authenticate to supported origins, especially private S3 buckets, using AWS SigV4.**
- **For S3, combine OAC with a tightly scoped bucket policy and S3 Block Public Access so CloudFront is the intended access path.**
- **OAC protects the CloudFront-to-origin relationship; it does not provide end-user authentication, replace WAF, or replace application authorization.**
- **Always test the intended CloudFront path and the direct-origin bypass path; a working CloudFront URL does not prove that the origin is private.**
- **For production systems, manage OAC, CloudFront, S3 policies, encryption, and related security controls through infrastructure as code and least-privilege policies.**