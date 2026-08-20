# 02- 403 Forbidden Errors

## Overview

A `403 Forbidden` response from a CloudFront distribution means that the request was rejected rather than successfully authorized to access the requested resource. The critical troubleshooting point is that **CloudFront returning `403` does not identify which layer generated the denial**.

A `403` can originate from several places in the request path:

```text
Client
  │
  ▼
DNS
  │
  ▼
CloudFront
  │
  ├── Viewer request processing
  ├── AWS WAF
  ├── Geo restriction
  ├── Signed URL / Signed Cookie
  ├── Cache behavior
  │
  ▼
Origin
  │
  ├── S3
  ├── ALB
  ├── Nginx
  └── Application
       │
       └── Django / FastAPI
```

Therefore, the correct question is not:

> "Why is CloudFront returning 403?"

It is:

> **"Which component rejected the request, and what authorization or request condition caused the rejection?"**

This distinction is essential in production because changing the wrong layer can make the incident harder to diagnose and can weaken security controls.

## Request Flow for a 403

A simplified CloudFront request lifecycle is:

```mermaid
sequenceDiagram
    participant C as Client
    participant CF as CloudFront
    participant W as AWS WAF
    participant O as Origin
    participant A as Application

    C->>CF: HTTPS request
    CF->>W: Evaluate request

    alt WAF blocks
        W-->>CF: Block
        CF-->>C: 403 Forbidden
    else WAF allows
        CF->>CF: Evaluate restrictions and cache behavior

        alt Edge-level rejection
            CF-->>C: 403 Forbidden
        else Request forwarded
            CF->>O: Origin request
            O->>A: Application request

            alt Origin rejects
                A-->>O: 403
                O-->>CF: 403
                CF-->>C: 403
            else Origin allows
                O-->>CF: Success
                CF-->>C: Response
            end
        end
    end
```

The same HTTP status code can therefore represent very different failures.

## Identify the Source of the 403

Before changing configuration, classify the possible source.

| Potential source | Typical reason |
|---|---|
| CloudFront | Distribution or behavior restriction |
| AWS WAF | Rule matched and request blocked |
| Geo restriction | Client country is denied |
| Signed URL | Signature invalid or expired |
| Signed cookie | Cookie missing, invalid, or expired |
| S3 | Bucket/object access denied |
| ALB/origin | Origin authorization policy |
| Nginx | Access-control rule |
| Django/FastAPI | Application authorization |
| Custom origin | Application-specific security policy |

The first investigation goal is to determine which category applies.

## Reproduce the Failure

Start with the exact failing URL:

```bash
curl -sv https://api.example.com/resource
```

Inspect only response headers:

```bash
curl -sS -D - -o /dev/null \
  https://api.example.com/resource
```

For a CloudFront distribution hostname:

```bash
curl -sv https://d123example.cloudfront.net/resource
```

Record:

- HTTP status
- Response headers
- Response body
- Request timestamp
- Hostname
- HTTP method
- Query string
- Cookies
- Authorization headers
- Client location
- Whether the request works through another network

A production investigation should reproduce the original request as closely as possible.

## Compare the CloudFront Hostname and Custom Domain

If both endpoints are available, compare:

```bash
curl -sv https://d123example.cloudfront.net/resource
```

and:

```bash
curl -sv https://api.example.com/resource
```

If one succeeds and the other fails, investigate:

- DNS
- Alternate domain names
- Viewer certificate
- Host-based behavior
- CloudFront configuration
- Application handling of the `Host` header

The comparison is useful because it isolates hostname-specific behavior.

## Inspect the Distribution

Retrieve the distribution:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID"
```

Inspect the configuration:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID"
```

For a concise overview:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.{Id:Id,Status:Status,Domain:DomainName,Enabled:DistributionConfig.Enabled,WebACL:DistributionConfig.WebACLId}' \
  --output table
```

Pay particular attention to:

- `Enabled`
- `Status`
- `Origins`
- `DefaultCacheBehavior`
- `CacheBehaviors`
- `WebACLId`
- `ViewerCertificate`
- `Aliases`
- Geo restriction configuration

## Check AWS WAF

AWS WAF is one of the first components to investigate when a CloudFront request returns `403`.

Inspect the associated Web ACL:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.DistributionConfig.WebACLId'
```

If a Web ACL is associated, determine whether the request is being blocked by:

- Managed rules
- Custom rules
- IP-based rules
- Rate-based rules
- Geographic rules
- Header matching
- URI matching
- Bot controls
- Reputation rules

A common production mistake is assuming:

```text
HTTP 403
    ↓
Django authorization failure
```

when the actual flow is:

```text
HTTP request
    ↓
CloudFront
    ↓
AWS WAF
    ↓
403
    ↓
Origin never receives request
```

### WAF Investigation

When WAF is suspected, correlate:

- Request timestamp
- Client IP
- Requested URI
- Rule evaluation
- Web ACL
- WAF metrics
- WAF logs

The goal is to identify the exact rule responsible rather than disabling the entire Web ACL.

## Check Geo Restrictions

CloudFront can restrict access based on geographic location.

Inspect the distribution configuration:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  --query 'DistributionConfig.Restrictions'
```

A geographic restriction can produce:

```text
Client
  │
  ▼
CloudFront
  │
  ├── Country allowed → Continue
  │
  └── Country blocked → 403
```

If users in one country receive `403` while users elsewhere receive `200`, geographic restriction becomes a strong hypothesis.

However, do not immediately assume that geography is the cause. WAF geographic rules and application-level geographic restrictions can produce similar symptoms.

## Check Signed URLs

Private CloudFront content can use signed URLs.

A signed URL typically contains authorization information such as:

```text
Expires
Signature
Key-Pair-Id
```

A request may receive `403` when:

- The signature is invalid.
- The URL has expired.
- The wrong key pair is used.
- The policy does not match the requested resource.
- The resource path differs from the signed path.
- The signing configuration is inconsistent.

Conceptually:

```text
Client
  │
  │ Signed URL
  ▼
CloudFront
  │
  ├── Signature valid?
  │       │
  │       ├── No → 403
  │       └── Yes
  │
  ▼
Origin
```

Do not troubleshoot a signed URL problem by changing origin permissions unless there is evidence that the request reaches the origin.

## Check Signed Cookies

Signed cookies are useful when a client needs access to multiple private objects without generating a separate signed URL for each object.

A `403` can occur when:

- Required cookies are missing.
- Cookie signatures are invalid.
- Cookies have expired.
- The policy does not cover the requested resource.
- The client is not preserving cookies correctly.

Inspect the request:

```bash
curl -sv \
  -H 'Cookie: CloudFront-Key-Pair-Id=...; CloudFront-Policy=...; CloudFront-Signature=...' \
  https://cdn.example.com/private/file.pdf
```

Do not expose real signing values in shell history, CI logs, or incident tickets.

## S3 Origin Access Problems

S3-backed CloudFront distributions commonly use private S3 buckets with CloudFront authorization.

A typical architecture is:

```text
Client
  │
  ▼
CloudFront
  │
  │ Origin Access Control
  ▼
S3 Bucket
  │
  ▼
Object
```

If the CloudFront distribution is not authorized to retrieve an object, S3 can return an access-denied response that surfaces as a `403`.

Investigate:

- Origin Access Control configuration
- S3 bucket policy
- Bucket/object ownership
- Object existence
- CloudFront origin configuration
- Incorrect bucket ARN
- Incorrect distribution authorization
- Encryption and KMS permissions where applicable

Inspect origins:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  --query 'DistributionConfig.Origins.Items[*].{Id:Id,DomainName:DomainName,OriginAccessControlId:OriginAccessControlId}'
```

A common production mistake is making the S3 bucket public simply to eliminate a CloudFront `403`.

That may remove the symptom while creating an unnecessary security exposure.

## S3 Object Does Not Exist

An object lookup can also produce an access-related response depending on bucket permissions and configuration.

Verify the object directly when appropriate:

```bash
aws s3api head-object \
  --bucket "$BUCKET_NAME" \
  --key "path/to/object"
```

Check whether the expected object exists:

```bash
aws s3api head-object \
  --bucket "$BUCKET_NAME" \
  --key "assets/app.js"
```

Then compare:

```text
Requested CloudFront path:
    /assets/app.js

Origin path:
    assets/app.js
```

A mismatch caused by origin path configuration or path rewriting can result in an unexpected origin access failure.

## Origin Access Control

For private S3 origins, verify that CloudFront is configured with the expected Origin Access Control.

The security model should normally look like:

```text
Public Internet
      │
      ▼
  CloudFront
      │
      │ authenticated origin request
      ▼
     S3
      │
      └── Bucket remains private
```

The objective is to prevent users from bypassing CloudFront and directly accessing the bucket.

Avoid this anti-pattern:

```text
CloudFront 403
     ↓
Make S3 public
     ↓
Problem appears fixed
```

The correct approach is to identify and repair the CloudFront-to-S3 authorization relationship.

## Check CloudFront Cache Behaviors

A path can be routed through a different cache behavior than expected.

For example:

```text
/                  → Static behavior
/assets/*          → S3
/api/*             → ALB
/private/*         → Private origin
```

A request to:

```text
/api/users
```

must use the intended behavior.

Inspect cache behaviors:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  --query 'DistributionConfig.{Default:DefaultCacheBehavior,Behaviors:CacheBehaviors}'
```

Investigate:

- Path pattern
- Target origin
- Allowed methods
- Viewer protocol policy
- Cache policy
- Origin request policy
- Trusted key groups
- Function/Lambda associations

A `403` may occur because the request is being routed to an origin that does not authorize it.

## Path and Origin Configuration

Consider:

```text
CloudFront URL:
https://cdn.example.com/api/users

Origin path:
/production

Origin receives:
/production/api/users
```

An unexpected origin path can cause the backend or object store to reject the request.

When troubleshooting, explicitly map:

```text
Viewer path
    ↓
CloudFront behavior
    ↓
Origin
    ↓
Origin path
    ↓
Final origin request
```

Do not assume that the viewer URL is identical to the origin URL.

## Application-Level 403

If CloudFront successfully forwards the request, the origin application may generate the `403`.

For Django or FastAPI, investigate:

- Authentication
- Authorization
- CSRF protection
- Host validation
- IP restrictions
- Application middleware
- Route-specific permissions
- API gateway or reverse-proxy policies

For Django, check application logs around the exact request timestamp.

For FastAPI, inspect middleware and dependency-based authorization.

The important distinction is:

```text
CloudFront-generated 403
```

versus:

```text
Origin-generated 403
```

The remediation is completely different.

## Nginx-Level 403

Nginx can also reject requests before they reach Django or FastAPI.

Potential causes include:

- `deny` directives
- IP allowlists
- Location-specific access rules
- Incorrect filesystem permissions
- Security modules
- Host-based restrictions

Request path:

```text
CloudFront
   │
   ▼
ALB
   │
   ▼
Nginx
   │
   ├── 403 → Application never receives request
   │
   └── Allow
          │
          ▼
      Django/FastAPI
```

Check Nginx access and error logs before modifying application authorization.

## Check the Origin Directly

When the architecture allows it, compare CloudFront behavior with direct origin behavior.

CloudFront:

```bash
curl -sv https://api.example.com/resource
```

Origin:

```bash
curl -sv https://origin.example.internal/resource
```

Interpretation:

| CloudFront | Origin | Investigation |
|---|---|---|
| `403` | `200` | CloudFront, WAF, signing, geo, or edge behavior |
| `403` | `403` | Origin authorization or shared request condition |
| `200` | `403` | Different request path or headers may be involved |
| `403` | Inaccessible | Continue investigating CloudFront and origin connectivity |

Direct-origin testing is not always equivalent because CloudFront may alter or add request information and may use different authentication or routing.

## Inspect Request Headers

Some authorization systems depend on headers.

Capture the request:

```bash
curl -sv \
  -H 'Authorization: Bearer <token>' \
  https://api.example.com/private
```

Check whether the CloudFront behavior forwards the required headers to the origin.

For authenticated APIs, carefully evaluate:

- `Authorization`
- `Host`
- `Origin`
- `Referer`
- Custom application headers
- Cookies

Do not blindly forward every viewer header. Excessive header forwarding can reduce cache efficiency and create unnecessary security or cache-key complexity.

## Common 403 Patterns

| Pattern | Strong initial hypothesis |
|---|---|
| All requests return `403` | WAF, distribution restriction, origin authorization |
| Only one country returns `403` | Geo restriction or geographic WAF rule |
| Only private files return `403` | Signed access or origin authorization |
| S3 objects return `403` | OAC/bucket policy/object access |
| API requests return `403` | WAF, forwarded auth headers, application authorization |
| Only one path returns `403` | Cache behavior or path-specific origin |
| Requests work directly against origin but not CloudFront | Edge/WAF/signing/cache behavior |
| Requests fail after a WAF deployment | WAF rule change |
| Requests fail after changing S3 permissions | OAC/bucket policy |
| Requests fail after changing authentication | Signed URL/cookie or forwarded headers |

## Production Investigation Workflow

### Capture the Exact Failure

```bash
curl -sv https://api.example.com/resource
```

Record:

- URL
- Method
- Timestamp
- Client location
- Status code
- Response headers
- Response body
- Authentication state

### Verify Distribution Identity

```bash
aws sts get-caller-identity
```

Then:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.{Id:Id,Domain:DomainName,Status:Status,WebACL:DistributionConfig.WebACLId}' \
  --output table
```

### Inspect Security Controls

Check:

- WAF
- Geo restrictions
- Signed URLs
- Signed cookies
- Origin Access Control

### Inspect Routing

Check:

- Path pattern
- Target origin
- Origin path
- Cache policy
- Origin request policy
- Allowed methods

### Check the Origin

Determine whether the origin received the request.

If it did:

```text
CloudFront
    ↓
Origin
    ↓
Nginx / Application
```

If it did not:

```text
Client
    ↓
CloudFront / WAF / edge control
    ↓
403
```

### Verify the Fix

After changing the configuration:

1. Wait for CloudFront deployment where required.
2. Reproduce the original request.
3. Test from the affected environment.
4. Test a control request that previously worked.
5. Check relevant WAF and CloudFront metrics.
6. Verify that the fix did not weaken another security boundary.

## Production Pitfalls

### Disabling WAF to "Test"

Do not disable the entire Web ACL merely to determine whether WAF is responsible.

Instead:

- Identify the suspected rule.
- Inspect WAF logs and metrics.
- Reproduce the request.
- Use a controlled rule change when necessary.
- Restore the intended security posture immediately after testing.

### Making S3 Public

A CloudFront-to-S3 `403` should not automatically result in a public bucket.

Maintain:

```text
S3 private
     │
     ▼
CloudFront OAC
     │
     ▼
Public CloudFront endpoint
```

rather than:

```text
S3 public
     │
     ├── Direct access
     └── CloudFront access
```

### Removing Authentication

Do not remove signed URL, signed cookie, or application authentication simply because a request fails with `403`.

First identify which authorization mechanism is rejecting the request.

### Assuming Every 403 Is a Security Rule

A `403` can be produced by a backend application or Nginx.

Always establish the generating layer.

### Changing Multiple Layers Simultaneously

Avoid changing:

- WAF
- CloudFront behavior
- S3 policy
- Application authorization

at the same time.

Otherwise, a successful response does not prove which change fixed the problem.

## Monitoring and Evidence

A strong investigation combines multiple evidence sources.

| Evidence | What it helps establish |
|---|---|
| `curl` | Actual client-visible behavior |
| CloudFront configuration | Intended distribution behavior |
| WAF logs | Security rule decisions |
| CloudFront metrics | Aggregate request behavior |
| S3 logs/metrics | Origin-side access behavior |
| ALB logs | Origin request arrival |
| Nginx logs | Reverse-proxy authorization |
| Application logs | Application authorization |
| CloudWatch | Time-series correlation |

Use timestamps consistently in UTC when correlating distributed logs.

## Prevention

Most recurring CloudFront `403` incidents can be reduced through disciplined configuration and deployment practices.

### Infrastructure as Code

Manage CloudFront, WAF, S3, and origin authorization through infrastructure as code where practical.

This makes security-sensitive configuration reviewable and reproducible.

### Configuration Review

Before deployment, review:

- WAF changes
- Geo restrictions
- Origin authorization
- Cache behaviors
- Signed access configuration
- Header forwarding
- Alternate domain names
- TLS configuration

### Automated Smoke Tests

After deployment, test representative paths:

```bash
curl -fsS https://api.example.com/health
curl -fsS https://cdn.example.com/assets/app.js
```

For private content, test the appropriate signed access mechanism.

### Monitor Authorization Failures

Track unexpected increases in:

- CloudFront `403`
- WAF blocks
- Origin `403`
- Application authorization failures

A sudden increase after a deployment is a strong signal for configuration regression.

## Interview Perspective

A strong answer to:

> "CloudFront is returning 403. How would you troubleshoot it?"

should not immediately assume WAF.

A production-oriented sequence is:

1. Reproduce the exact request.
2. Determine whether the `403` originates at the edge or origin.
3. Check AWS WAF.
4. Check geo restrictions.
5. Check signed URLs or signed cookies.
6. Check CloudFront cache behavior and origin selection.
7. If S3 is the origin, inspect OAC and bucket policy.
8. If the request reaches the application, inspect Nginx and application authorization.
9. Compare CloudFront behavior with direct-origin behavior where possible.
10. Make the smallest change that tests the identified hypothesis.

The interviewer is typically testing whether you understand that **HTTP status codes identify a response, not necessarily the component that generated it**.

## Key Takeaways

- **A CloudFront `403` is a symptom, not a root cause:** identify whether CloudFront, WAF, signing, geo restrictions, the origin, Nginx, or the application generated the denial.
- **Security controls should be investigated before being weakened:** do not make S3 public or disable WAF simply to eliminate a `403`.
- **Compare edge and origin behavior:** direct-origin testing can isolate CloudFront/WAF/signing problems from backend authorization failures.
- **Trace the complete request path:** cache behavior, headers, path patterns, OAC, authentication, and origin routing can all affect authorization.
- **Use evidence and controlled changes:** correlate request data, WAF logs, CloudFront configuration, origin logs, and metrics before modifying production.