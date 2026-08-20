# 10- Signed URL Issues

## Overview

CloudFront signed URLs provide controlled access to private content by requiring a request to contain a cryptographically signed policy or URL parameters that CloudFront can validate.

A signed URL failure usually appears as an HTTP `403 Forbidden`, but the underlying cause can be very different:

- Invalid signature
- Expired URL
- URL modified after signing
- Incorrect key group or public key configuration
- Incorrect trusted key configuration
- Policy mismatch
- Incorrect resource path
- Incorrect query parameters
- Clock or timestamp problems
- Wrong CloudFront distribution
- Incorrect signer configuration
- Application-generated URLs using the wrong signing algorithm or key

The troubleshooting goal is to determine whether the request reached CloudFront with a valid authorization mechanism and whether the CloudFront distribution is configured to trust the signer.

A typical architecture is:

```text
Client
   │
   │ Signed URL
   ▼
CloudFront
   │
   ├── Signature valid ──► Cache / Origin
   │
   └── Signature invalid
            │
            ▼
        HTTP 403
```

Signed URL problems should be investigated at the CloudFront authorization layer before investigating the origin application.

## What a CloudFront Signed URL Is

A signed URL is a URL containing authorization information that CloudFront validates before allowing access to a protected resource.

A typical URL contains parameters similar to:

```text
https://cdn.example.com/private/report.pdf
    ?Expires=1787200000
    &Signature=<signature>
    &Key-Pair-Id=<identifier>
```

The exact parameters depend on the signing approach and policy type.

The important concept is that CloudFront does not simply check whether a query parameter exists. It validates the cryptographic signature against a trusted public key and verifies the associated access policy.

## Why Signed URLs Exist

Signed URLs allow applications to keep content private while still delivering it through CloudFront.

Without signed URLs:

```text
Client
   │
   ▼
CloudFront
   │
   ▼
Public object
```

Anyone who knows the URL may be able to retrieve the content.

With signed URLs:

```text
Client
   │
   │ authenticated application request
   ▼
Backend
   │
   │ generates signed URL
   ▼
Client
   │
   │ signed request
   ▼
CloudFront
   │
   ├── Valid → Content
   └── Invalid → 403
```

This is useful for:

- Private downloads
- Paid media
- Temporary documents
- Customer-specific files
- Protected software packages
- Private images or videos
- Time-limited access

## Signed URL Request Lifecycle

A production request typically follows this sequence:

```mermaid
sequenceDiagram
    participant C as Client
    participant A as Backend
    participant CF as CloudFront
    participant O as Origin

    C->>A: Request protected resource
    A->>A: Authorize user
    A->>A: Generate signed URL
    A-->>C: Signed CloudFront URL
    C->>CF: GET signed URL
    CF->>CF: Validate signature and policy
    alt Valid
        CF->>O: Fetch object on cache miss
        O-->>CF: Object
        CF-->>C: Protected content
    else Invalid
        CF-->>C: 403 Forbidden
    end
```

The backend should generally authorize the user **before** generating a signed URL.

For example:

```text
User
  ↓
Django / FastAPI
  ↓
Verify identity
  ↓
Verify object ownership
  ↓
Generate short-lived CloudFront URL
  ↓
Return URL
```

CloudFront signed URLs are not a replacement for application authorization.

## Signed URL Components

A signed URL commonly contains:

| Component | Purpose |
|---|---|
| Resource URL | Identifies the protected object |
| Expiration | Limits how long the URL remains valid |
| Signature | Cryptographically proves authorization |
| Key identifier | Identifies the trusted public key |
| Policy parameters | Optional restrictions depending on policy type |

The exact parameters and signing mechanism depend on whether a canned policy or custom policy is being used.

## Canned Policy vs Custom Policy

CloudFront supports two policy styles for signed URLs.

| Policy | Characteristics |
|---|---|
| Canned policy | Simpler; primarily controls resource and expiration |
| Custom policy | Supports additional restrictions such as IP address and broader policy conditions |

### Canned Policy

A canned policy is appropriate when access requirements are straightforward.

Typical requirement:

```text
Allow access to this exact resource
until this timestamp.
```

It is easier to generate and easier to troubleshoot.

### Custom Policy

Custom policies are useful when access must be constrained beyond simple expiration.

For example:

```text
Resource:
https://cdn.example.com/private/*

Expiration:
10 minutes

Not-before:
current time

IP restriction:
specific client network
```

Custom policies introduce more signing and policy complexity, so they should be used only when the additional controls are actually required.

## Key Groups and Trusted Public Keys

Modern CloudFront deployments commonly use CloudFront key groups to control which public keys CloudFront trusts for signed URLs and signed cookies.

The trust relationship is conceptually:

```text
Application
   │
   │ private key
   ▼
Generate signature
   │
   ▼
Signed URL
   │
   ▼
CloudFront
   │
   │ trusted public key
   ▼
Validate signature
```

The private key must remain under application-side control.

CloudFront should receive the corresponding public key.

Never distribute the private signing key to clients.

## Key Pair Identifier Problems

A signed URL can fail if the key identifier does not correspond to a trusted key.

Common causes include:

- Wrong key identifier
- Deleted key
- Disabled or incorrectly configured key
- Key belongs to another distribution
- Public key is not associated with the expected key group
- Application uses an old key after rotation

A useful troubleshooting question is:

> Does the key identifier embedded in the signed URL correspond to a currently trusted CloudFront public key?

## Inspect CloudFront Distribution Configuration

Retrieve the distribution:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID"
```

Retrieve the configuration:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID"
```

Review the cache behavior associated with the requested path.

The relevant behavior must be configured to require signed URLs or signed cookies when private content protection is intended.

## Identify the Matching Cache Behavior

CloudFront can have multiple cache behaviors:

```text
/private/*      → Private behavior
/videos/*       → Media behavior
/static/*       → Public behavior
*               → Default behavior
```

A common mistake is troubleshooting the default behavior when the request actually matches a more specific path behavior.

Determine the exact requested URL:

```text
https://cdn.example.com/private/report.pdf
```

Then determine which cache behavior matches:

```text
/private/*
```

The configuration of that behavior determines the relevant authorization settings.

## 403 Does Not Always Mean Signature Failure

A `403 Forbidden` response can have several causes.

| Cause | Typical layer |
|---|---|
| Invalid signature | CloudFront authorization |
| Expired URL | CloudFront authorization |
| Wrong key | CloudFront authorization |
| Missing required signature | CloudFront authorization |
| Incorrect policy | CloudFront authorization |
| AWS WAF rule | WAF |
| Origin access restriction | Origin |
| Application authorization | Origin application |
| Object permissions | S3/origin |

Do not immediately regenerate a signature repeatedly without identifying which layer returned the `403`.

## Check the URL for Modification

A signed URL is sensitive to changes in the signed request.

For example:

```text
Original:
https://cdn.example.com/private/report.pdf?Expires=...&Signature=...&Key-Pair-Id=...
```

If an intermediary or application changes the URL, the signature may no longer correspond to the request being validated.

Potential problems include:

- URL encoding changes
- Resource path changes
- Query-string changes
- Parameter corruption
- Truncation
- Incorrect escaping
- Case changes in paths where relevant

Treat a signed URL as an opaque security credential.

Do not reconstruct or normalize it unnecessarily.

## URL Encoding Problems

Signed URLs can contain characters that require correct URL encoding.

Incorrect handling can happen when:

- A backend framework re-encodes the URL
- A frontend constructs the URL manually
- A proxy modifies query parameters
- A URL is passed through multiple serialization layers

A safer pattern is:

```text
Backend generates complete signed URL
        ↓
Return URL as a string
        ↓
Client uses URL exactly as provided
```

Avoid manually rebuilding the signed URL in frontend code.

## Expired Signed URLs

Expiration is one of the simplest causes of failure.

If:

```text
Expires = 1787200000
```

and the current CloudFront evaluation time is beyond that timestamp, access is rejected.

Inspect the URL and compare the expiration timestamp with the current time.

On Linux:

```bash
date -u
```

Convert a Unix timestamp:

```bash
date -u -d '@1787200000'
```

On systems where GNU `date` is unavailable, use an equivalent timestamp conversion utility.

## Clock and Timestamp Problems

Timestamp-based authorization requires correct time handling.

Potential problems include:

- Incorrect server clock
- Incorrect timezone conversion
- Milliseconds used instead of seconds
- Expiration generated in the wrong time basis
- Application code calculating expiration incorrectly

Unix timestamps should normally represent seconds since the Unix epoch.

For example:

```python
from datetime import datetime, timedelta, timezone

expires_at = int(
    (datetime.now(timezone.utc) + timedelta(minutes=10)).timestamp()
)
```

The important property is that the timestamp is generated from a reliable UTC-aware clock.

## Private Key Problems

The application must sign the URL with the correct private key corresponding to the public key trusted by CloudFront.

Common mistakes include:

- Wrong private key
- Corrupted PEM file
- Wrong environment variable
- Incorrect secret mounted in Docker
- Incorrect Kubernetes Secret
- Old key after rotation
- File permission problems
- Accidental newline corruption

For production workloads, keep signing keys in a dedicated secret-management system rather than committing them to Git.

Examples include:

- AWS Secrets Manager
- AWS Systems Manager Parameter Store
- Kubernetes Secrets backed by appropriate secret-management controls

## Python Signed URL Example

A backend service may generate signed URLs using the AWS SDK.

The exact implementation should match the CloudFront signing model and key configuration used by the distribution.

A conceptual backend flow is:

```python
from datetime import datetime, timedelta, timezone

def create_expiration(minutes: int = 10) -> int:
    return int(
        (datetime.now(timezone.utc) + timedelta(minutes=minutes)).timestamp()
    )

expires_at = create_expiration()

# Use the AWS-supported CloudFront signing implementation
# configured with the appropriate private key and key identifier.
```

In a real Django or FastAPI service, the signing operation should be isolated behind a small service component rather than duplicated throughout route handlers.

For example:

```text
API View
   ↓
Authorization Service
   ↓
CloudFront URL Signer
   ↓
Signed URL
```

This makes key rotation and signing behavior easier to manage.

## Django Integration Pattern

A Django endpoint might follow this design:

```python
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


@login_required
def download_document(request, document_id):
    document = get_document_for_user(request.user, document_id)

    signed_url = cloudfront_signer.create_signed_url(
        path=document.private_path,
        expires_in=600,
    )

    return JsonResponse({"url": signed_url})
```

The important architectural separation is:

```text
Django
├── Authenticate user
├── Authorize document
└── Generate signed URL

CloudFront
└── Validate signed URL
```

CloudFront should not be expected to understand your application's ownership rules.

## FastAPI Integration Pattern

The same architecture applies to FastAPI:

```text
GET /documents/{id}/download
        │
        ▼
Authenticate request
        │
        ▼
Authorize document
        │
        ▼
Generate signed CloudFront URL
        │
        ▼
Return URL
```

The signer should be injected as a service dependency rather than implemented directly in every route.

## Docker Secret Problems

When signing inside Docker, verify that the container actually has the expected private key.

Inspect environment configuration without exposing the secret:

```bash
docker exec "$CONTAINER_ID" \
  sh -c 'test -n "$CLOUDFRONT_KEY_ID" && echo "key id configured"'
```

Avoid commands such as:

```bash
docker exec "$CONTAINER_ID" env
```

during production troubleshooting if they would expose secrets to terminal history, logs, or incident tooling.

## Kubernetes Secret Problems

For Kubernetes deployments, verify configuration without printing secret values.

For example:

```bash
kubectl get deployment backend -o yaml
```

Review references to:

- Secret names
- Secret keys
- Mounted paths
- Environment variable names

Do not dump Secret objects into shared incident channels.

## Signature Algorithm and Library Compatibility

Signing failures can occur when application code uses an implementation that does not match the CloudFront signing mechanism.

Common causes include:

- Incorrect cryptographic algorithm
- Incorrect key format
- Incorrect policy serialization
- Incorrect signature encoding
- Unsupported or outdated library implementation

Use AWS-supported signing mechanisms and current SDK/library documentation rather than implementing CloudFront signing manually unless there is a strong engineering reason.

Manual cryptographic implementations increase the risk of subtle compatibility and security bugs.

## Policy Mismatch

With custom policies, the signed policy must correspond to the requested resource and constraints.

Potential mismatches include:

```text
Signed resource:
https://cdn.example.com/private/*

Requested:
https://cdn.example.com/public/file.pdf
```

or:

```text
Policy:
expires at 12:00

Request:
12:01
```

or:

```text
Policy:
IP restricted

Client:
different IP
```

When a custom policy is used, inspect every policy condition rather than only checking the signature parameter.

## Wildcard Resource Policies

Custom policies can cover a resource pattern.

For example:

```text
https://cdn.example.com/private/*
```

This can reduce the need to generate a separate policy for every object.

However, broad policies increase the impact of a leaked URL or signing credential.

Use the narrowest resource scope that satisfies the application requirement.

## Signed URL Lifetime

Signed URL duration is a security and operational tradeoff.

| Lifetime | Security | Operational behavior |
|---|---|---|
| 1–5 minutes | Strong | Requires frequent regeneration |
| 10–30 minutes | Strong | Common for temporary downloads |
| Several hours | Weaker | More convenient |
| Days | Significantly weaker | Harder to revoke effectively |

For sensitive content, short-lived URLs are generally preferable.

A signed URL should normally be treated as a bearer credential.

Anyone possessing a valid URL may be able to use it until it expires or another control invalidates access.

## Revocation Limitations

Signed URLs are not equivalent to a database-backed authorization check on every request.

Once a valid signed URL has been issued, revoking a user's application account does not necessarily invalidate an already-issued URL.

This is why short expiration periods are important.

For stronger revocation requirements, combine signed URLs with:

- Short TTLs
- Application authorization
- Object-level access controls
- Session/token revocation
- Controlled URL issuance

## S3 Origin Considerations

When CloudFront uses S3 as an origin, private content should not simply be made publicly readable to compensate for CloudFront access issues.

A common architecture is:

```text
Client
  │
  ▼
CloudFront
  │
  │ Signed URL
  ▼
Private S3
```

CloudFront should be authorized to retrieve the private objects through the configured origin access mechanism.

Do not solve:

```text
CloudFront 403
```

by changing the bucket to:

```text
Public Read
```

That removes an important security boundary.

## Origin vs CloudFront Authorization

There are two distinct authorization decisions:

```text
Client
  │
  ▼
CloudFront
  │
  │ signed URL valid?
  ├── No → 403
  │
  ▼
Origin
  │
  │ origin authorization valid?
  ├── No → origin error
  │
  ▼
Object
```

A valid signed URL does not automatically mean the origin request will succeed.

For example:

```text
Signed URL valid
+
CloudFront authorized
+
S3 origin access misconfigured
=
Origin failure
```

Always determine which layer rejected the request.

## Use Response Headers for Diagnosis

Inspect the response headers:

```bash
curl -sS -D - \
  -o /dev/null \
  "https://cdn.example.com/private/report.pdf?..."
```

Useful headers may include:

```text
HTTP/2 403
Content-Type
Date
Via
X-Cache
X-Amz-Cf-Id
X-Amz-Cf-Pop
```

Do not assume that every header will always be present or identical across configurations.

`X-Amz-Cf-Id` can be useful when correlating a CloudFront request with AWS operational diagnostics.

## Test Without Modifying the URL

When troubleshooting a signed URL, first use the exact URL generated by the backend:

```bash
SIGNED_URL='https://cdn.example.com/private/report.pdf?...'

curl -v "$SIGNED_URL"
```

Avoid manually copying only some query parameters.

For example, this is a poor diagnostic approach:

```text
Copy path
+
copy Signature
+
manually recreate Expires
+
manually add Key-Pair-Id
```

Use the original generated URL so the test represents the actual client request.

## Compare Working and Failing URLs

A highly effective troubleshooting technique is to compare:

```text
Known-good signed URL
vs.
Failing signed URL
```

Compare:

- Hostname
- Path
- Expiration
- Key identifier
- Signature
- Policy
- Query parameters
- Encoding
- Generation timestamp

Do not expose private signing keys while collecting diagnostic data.

## CloudFront Distribution Mismatch

A signed URL generated for one CloudFront distribution should not be assumed to work against another.

For example:

```text
Signing configuration
      │
      ▼
cdn-prod.example.com
```

but the application returns:

```text
cdn-staging.example.com
```

The URL may be structurally valid while still failing because the distribution is not configured to trust the relevant key.

Environment-specific signing configuration should therefore be explicit.

## Multi-Environment Configuration

Avoid accidental reuse of production signing configuration in development or staging.

A clean configuration model is:

```text
Development
├── Distribution ID
├── CloudFront domain
├── Key identifier
└── Private signing key

Staging
├── Distribution ID
├── CloudFront domain
├── Key identifier
└── Private signing key

Production
├── Distribution ID
├── CloudFront domain
├── Key identifier
└── Private signing key
```

Separate environments reduce accidental cross-environment authorization failures.

## Key Rotation

Signing keys should be rotated without causing an availability outage.

A safe high-level process is:

```text
Create new key
      ↓
Add public key
      ↓
Associate with trusted key group
      ↓
Deploy application with new private key
      ↓
Generate new URLs
      ↓
Observe
      ↓
Retire old key after existing URLs expire
```

Do not immediately remove the old trusted key if existing signed URLs still need to remain valid.

The retirement window should account for the maximum lifetime of previously issued URLs.

## Production Key Management

Never store private CloudFront signing keys in:

- Git repositories
- Docker images
- Frontend JavaScript
- Client applications
- Public configuration files
- Source code

Prefer a secret-management system and restrict access to the backend components that actually generate URLs.

The frontend should receive only the resulting signed URL.

## Monitoring Signed URL Failures

Track signed URL failures separately from generic CloudFront `403` responses when possible.

Useful signals include:

- CloudFront 403 rate
- Requests to private paths
- URL generation success rate
- URL generation latency
- Download success rate
- Key rotation events
- Application authorization failures
- WAF blocks
- Origin authorization failures

A useful operational metric is:

```text
Signed URL generation success
vs.
CloudFront signed URL request success
```

If generation succeeds but CloudFront requests fail, investigate signing and distribution configuration.

If generation itself fails, investigate the backend.

## Troubleshooting Decision Tree

```mermaid
flowchart TD
    A[Signed URL returns 403] --> B{Is URL expired?}
    B -->|Yes| C[Regenerate URL]
    B -->|No| D{Was URL modified?}
    D -->|Yes| E[Use original generated URL]
    D -->|No| F{Correct distribution/domain?}
    F -->|No| G[Fix environment/configuration]
    F -->|Yes| H{Key trusted by CloudFront?}
    H -->|No| I[Fix public key/key group]
    H -->|Yes| J{Policy valid?}
    J -->|No| K[Fix policy/resource/conditions]
    J -->|Yes| L{WAF or origin returning 403?}
    L -->|WAF| M[Inspect WAF rules]
    L -->|Origin| N[Inspect origin authorization]
    L -->|CloudFront| O[Inspect signing implementation]
```

## Operational Troubleshooting Workflow

### Capture the Exact Failing URL

Use the URL returned by the backend without modifying it.

Do not log the full URL indiscriminately in production because it may function as a bearer credential.

### Verify Expiration

Determine whether the URL is still within its allowed lifetime.

### Verify the Distribution

Confirm:

- Hostname
- Environment
- Distribution
- Requested path

### Identify the Matching Cache Behavior

Confirm that the requested path uses the intended private-content behavior.

### Verify Trusted Keys

Confirm that:

- The key identifier is correct
- The corresponding public key exists
- The public key is trusted
- The key group is associated correctly
- The application is using the corresponding private key

### Verify Policy

For custom policies, inspect:

- Resource
- Expiration
- Not-before condition
- IP restrictions
- Other policy conditions

### Verify URL Integrity

Check whether:

- Query parameters changed
- URL encoding changed
- Path changed
- Signature was truncated
- Frontend code rebuilt the URL

### Determine Which Layer Returned 403

Use:

```bash
curl -v "$SIGNED_URL"
```

and correlate the response with:

- CloudFront logs
- WAF logs
- Origin logs
- Application logs

### Test a Newly Generated URL

Generate a fresh URL with a short lifetime and immediately test it.

If a newly generated URL works while an older URL fails, investigate:

- Expiration
- Key rotation
- Policy lifetime
- URL modification

If newly generated URLs consistently fail, investigate configuration or signing implementation.

## Common Mistakes

### Logging Full Signed URLs

Signed URLs may grant access to private resources.

**Why it is dangerous:** logs, tracing systems, browser history, proxies, and monitoring systems may retain the URL.

**Better approach:** redact sensitive query parameters.

For example:

```text
https://cdn.example.com/private/report.pdf?Signature=[REDACTED]&Expires=[REDACTED]
```

### Putting the Private Key in Frontend Code

The browser must never receive the private signing key.

**Why it is dangerous:** users can extract the key and generate arbitrary signed URLs.

**Better approach:** sign only on trusted backend infrastructure.

### Using Very Long Expiration Periods

Long-lived signed URLs increase the impact of credential leakage.

**Better approach:** use short expiration periods appropriate for the business workflow.

### Rebuilding Signed URLs

Manual URL manipulation can invalidate signatures.

**Better approach:** treat generated signed URLs as immutable strings.

### Making S3 Public to Fix CloudFront 403

This bypasses the intended security architecture.

**Better approach:** distinguish CloudFront signed URL authorization from origin access authorization.

### Rotating Keys Without a Transition Window

Removing an old key immediately can invalidate existing URLs.

**Better approach:** maintain the old trusted key until previously issued URLs expire.

### Ignoring WAF

A valid signed URL can still be blocked by AWS WAF.

**Better approach:** inspect WAF rules when CloudFront authorization appears correct.

## Production Best Practices

- Generate signed URLs only after application-level authorization succeeds.
- Keep signing private keys exclusively on trusted backend infrastructure.
- Use short URL lifetimes for sensitive content.
- Use the narrowest resource scope practical.
- Prefer supported AWS signing implementations.
- Keep production, staging, and development signing configuration separate.
- Store private keys in a managed secret system.
- Rotate keys using an overlap period.
- Avoid logging complete signed URLs.
- Treat signed URLs as bearer credentials.
- Monitor private-content `403` rates.
- Correlate CloudFront, WAF, and origin diagnostics.
- Avoid making private S3 objects public to solve authorization failures.
- Test with the exact URL generated by the backend.
- Redact signatures and other sensitive query parameters from observability systems.

## Security Considerations

Signed URLs provide authorization at the CDN request layer, but they do not replace application identity and authorization.

A secure architecture is:

```text
User
 │
 ▼
Django / FastAPI
 │
 ├── Authenticate
 ├── Authorize resource
 └── Generate short-lived signed URL
          │
          ▼
       Client
          │
          ▼
      CloudFront
          │
          ├── Validate signature
          └── Retrieve private object
```

Security controls should be layered:

| Layer | Responsibility |
|---|---|
| Application | User identity and resource authorization |
| CloudFront | Signed URL validation |
| WAF | Traffic filtering and abuse protection |
| Origin | Origin-level authorization |
| S3 | Object-level access control |

This separation reduces the blast radius of a failure or credential leak.

## Performance Considerations

Signed URL validation occurs at CloudFront and does not require your application to authorize every download request.

This is one of the major advantages of the architecture:

```text
Backend
   │
   │ authorize once
   ▼
Signed URL
   │
   ▼
CloudFront
   │
   ├── Cache HIT → Content
   │
   └── Cache MISS → Origin
```

The backend does not need to process every subsequent byte of a large file download.

For large media or document workloads, this can substantially reduce application and database load.

## Reliability Considerations

Signed URL generation should not become a single point of failure for an otherwise healthy CDN.

The backend should:

- Keep signing configuration available
- Validate configuration during deployment
- Fail clearly when signing keys are unavailable
- Avoid generating excessively long-lived URLs as a workaround
- Monitor signing failures
- Support key rotation safely

CloudFront should continue serving already-authorized cached objects when appropriate, while the backend remains responsible for issuing new authorization credentials.

## Cost Considerations

Signed URLs can reduce origin workload when they allow private content to remain cacheable at CloudFront.

For example:

```text
Private object
      ↓
CloudFront cache
      ↓
Multiple authorized downloads
      ↓
Fewer origin fetches
```

However, authorization design should not unnecessarily fragment the cache.

The goal is to protect content without creating avoidable cache fragmentation or forcing every request back to the origin.

## Interview Perspective

A strong answer to:

> "A CloudFront signed URL is returning 403. How would you troubleshoot it?"

should include:

1. Capture the exact generated URL.
2. Check whether it has expired.
3. Verify that the URL was not modified.
4. Verify the CloudFront distribution and hostname.
5. Identify the matching cache behavior.
6. Verify the key identifier.
7. Verify that the corresponding public key is trusted through the configured key group.
8. Verify the application is using the correct private key.
9. Validate the signing algorithm and policy.
10. For custom policies, verify resource and policy conditions.
11. Check WAF and origin authorization separately.
12. Inspect CloudFront and origin diagnostics.
13. Generate a fresh short-lived URL and retest.
14. If keys were recently rotated, verify that old URLs still have a valid trusted key during the transition period.

The senior-level distinction is:

> **A signed URL problem is an authorization-path problem first. Do not start by debugging the origin until you have established that CloudFront accepted the request's authorization information.**

## Key Takeaways

- **Treat signed URLs as bearer credentials:** keep private keys server-side, use short expiration periods, and avoid logging complete signed URLs.
- **A CloudFront 403 is not automatically a signature failure:** distinguish CloudFront authorization, WAF, and origin authorization failures.
- **Verify the complete trust chain:** the URL's key identifier, trusted public key, key group, signing key, policy, and distribution must all align.
- **Never modify a generated signed URL:** path, query parameters, encoding, expiration, and signature must remain consistent with what was signed.
- **Rotate signing keys with an overlap window:** keep old trusted keys available until previously issued URLs have expired.