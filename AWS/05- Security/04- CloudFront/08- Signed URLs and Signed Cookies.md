# 08- Signed URLs and Signed Cookies

## Overview

CloudFront signed URLs and signed cookies provide **application-controlled access to private content distributed through CloudFront**.

They allow an application to authenticate or authorize a viewer and then issue a time-limited cryptographic credential that CloudFront validates before serving protected content.

The basic architecture is:

```text
User
  │
  │ Authenticate
  ▼
Backend Application
  │
  │ Generate signed URL
  │ or signed cookies
  ▼
User
  │
  │ Request protected content
  ▼
CloudFront
  │
  │ Verify signature + policy
  │
  ├── Valid ──────► Serve content
  │
  └── Invalid ────► Reject request
```

This is particularly useful for:

- Private downloads
- Paid media
- Subscriber-only content
- Software installers
- Temporary file access
- Private images and documents
- HLS/video segments
- Protected static assets

CloudFront supports both mechanisms because the access pattern differs:

| Mechanism | Primary use case |
|---|---|
| Signed URL | Access to an individual file or resource |
| Signed cookie | Access to multiple protected resources without changing URLs |

AWS currently recommends **CloudFront trusted key groups** over legacy trusted AWS accounts for managing signers. Trusted key groups allow public keys and key groups to be managed through the CloudFront API and IAM rather than requiring CloudFront key-pair management through the AWS account root user. :contentReference[oaicite:0]{index=0}

## Why Signed URLs and Cookies Exist

An S3 object behind CloudFront might normally be reachable through a URL such as:

```text
https://cdn.example.com/reports/annual-report.pdf
```

If the object is public, anyone who knows the URL can request it.

For private content, the desired behavior is:

```text
Public URL
    │
    ▼
CloudFront
    │
    ├── Valid authorization credential ──► Content
    │
    └── Missing/invalid credential ─────► 403
```

The backend decides whether the user should receive access.

CloudFront then enforces that decision at the edge.

This creates a useful separation:

```text
Backend
  │
  │ "User is authorized"
  ▼
Signed credential
  │
  ▼
CloudFront
  │
  │ "Credential is valid"
  ▼
Private content
```

The backend does not need to proxy every byte of the protected file.

## Authentication vs Authorization

Signed URLs and signed cookies are primarily **authorization mechanisms**, not replacements for user authentication.

A common architecture is:

```text
Client
  │
  ▼
Django / FastAPI
  │
  ├── Authenticate user
  │
  ├── Check subscription
  │
  ├── Check resource ownership
  │
  └── Generate signed credential
           │
           ▼
       CloudFront
           │
           ▼
       Private content
```

The backend determines:

> "This user is allowed to access this resource."

CloudFront then enforces the resulting credential.

CloudFront does not inherently understand your application's:

- Django session
- JWT claims
- PostgreSQL permissions
- Redis session
- Subscription status
- Business rules

Those remain application responsibilities.

## How Signed URLs Work

A signed URL contains the normal CloudFront resource URL plus additional signature information.

Conceptually:

```text
https://cdn.example.com/video/movie.mp4
    ?Expires=...
    &Signature=...
    &Key-Pair-Id=...
```

The signature is generated using the private key corresponding to a public key trusted by CloudFront.

The high-level flow is:

```text
Private Key
     │
     ▼
Sign policy/resource
     │
     ▼
Signed URL
     │
     ▼
Client
     │
     ▼
CloudFront
     │
     ├── Locate public key
     ├── Verify signature
     ├── Validate policy
     └── Serve/reject
```

CloudFront verifies the signature and the restrictions encoded in the signed URL or its policy before granting access. :contentReference[oaicite:1]{index=1}

## How Signed Cookies Work

Signed cookies use the same fundamental authorization model but put the authorization information in HTTP cookies instead of modifying the content URL.

A typical signed-cookie flow is:

```text
Client
  │
  ▼
Backend
  │
  │ Authenticate + authorize
  ▼
Set-Cookie
  │
  ├── CloudFront-Policy
  ├── CloudFront-Signature
  └── CloudFront-Key-Pair-Id
  │
  ▼
Browser
  │
  │ Request many resources
  ▼
CloudFront
  │
  │ Validate cookies
  ▼
Private content
```

CloudFront's documentation describes signed cookies as particularly useful when users need access to multiple restricted files or when you want to keep existing URLs unchanged. :contentReference[oaicite:2]{index=2}

## Signed URL vs Signed Cookie

Both mechanisms provide the same basic security model, but their delivery model differs.

| Concern | Signed URL | Signed Cookie |
|---|---|---|
| Credential location | URL query parameters | HTTP cookies |
| Best for | Individual resources | Groups of resources |
| URL changes | Yes | No |
| Multiple files | Less convenient | Convenient |
| Browser cookie dependency | No | Yes |
| Custom HTTP clients | Convenient | Client must support cookies |
| Download link | Excellent | Less convenient |
| HLS/video segments | Possible | Often more convenient |
| Existing URLs preserved | No | Yes |
| Credential visible in URL | Yes | No |
| Typical example | Temporary PDF download | Subscriber video area |

AWS recommends signed URLs when access should be restricted to individual files or when clients do not support cookies. Signed cookies are better suited to multiple restricted files or situations where existing URLs should remain unchanged. :contentReference[oaicite:3]{index=3}

## Request Lifecycle

```mermaid
sequenceDiagram
    participant U as User
    participant A as Backend
    participant CF as CloudFront
    participant O as Origin

    U->>A: Authenticate / request access
    A->>A: Authorize resource
    A->>A: Sign URL or cookie
    A-->>U: Authorization credential

    U->>CF: Request private content
    CF->>CF: Identify cache behavior
    CF->>CF: Verify signature
    CF->>CF: Validate policy and expiration

    alt Valid credential
        CF->>O: Retrieve object if needed
        O-->>CF: Content
        CF-->>U: Protected content
    else Invalid or expired credential
        CF-->>U: 403 Forbidden
    end
```

An important architectural property is that the backend does not have to participate in every content request.

For a large video:

```text
Backend
  │
  │ Issue authorization
  ▼
Client
  │
  ├── Segment 1 ──► CloudFront
  ├── Segment 2 ──► CloudFront
  ├── Segment 3 ──► CloudFront
  └── Segment N ──► CloudFront
```

The application handles authorization while CloudFront handles content delivery.

## Trusted Key Groups

A trusted key group is the recommended modern signer-management model.

Conceptually:

```text
Private Key
    │
    │ kept by signing service
    ▼
Backend
    │
    │ signs URL/cookie
    ▼
Client

Public Key
    │
    ▼
CloudFront Public Key
    │
    ▼
Trusted Key Group
    │
    ▼
Cache Behavior
```

CloudFront uses the public key in the trusted key group to validate signatures created with the corresponding private key. :contentReference[oaicite:4]{index=4}

A key group can be associated with one or more cache behaviors.

When a cache behavior contains trusted key groups, CloudFront requires signed URLs or signed cookies for requests matching that behavior. :contentReference[oaicite:5]{index=5}

## Why Trusted Key Groups Are Preferred

Legacy CloudFront trusted signers are associated with AWS accounts and CloudFront key pairs.

Trusted key groups provide a cleaner operational model:

```text
Public Key
    │
    ▼
Key Group
    │
    ▼
CloudFront Distribution
```

Advantages include:

- API-based management
- IAM-controlled permissions
- Easier automation
- Cleaner key rotation
- Separation between signing infrastructure and AWS account root credentials

AWS explicitly recommends trusted key groups instead of legacy trusted signers. :contentReference[oaicite:6]{index=6}

## Cryptographic Model

The signing model uses asymmetric cryptography.

```text
                 Private Key
                     │
                     ▼
                  Signing
                     │
                     ▼
              Signed URL/Cookie
                     │
                     ▼
                  Internet
                     │
                     ▼
                CloudFront
                     │
                     ▼
                 Public Key
                     │
                     ▼
                 Verification
```

The private key should remain exclusively within the trusted signing system.

The public key is distributed to CloudFront.

This means CloudFront can verify signatures without possessing the private signing key.

## Key Pair Requirements

AWS currently documents supported signer key pairs as:

- RSA 2048
- ECDSA 256

The key pair must be provided in the required PEM/base64 representation for the CloudFront signing workflow. :contentReference[oaicite:7]{index=7}

For production systems, the private key should be treated as a highly sensitive credential.

Never:

```text
Git repository
Docker image
Application logs
Client JavaScript
Frontend bundle
Public S3 object
```

Store it in an appropriate secrets or key-management system and restrict access to the service that generates signatures.

## Canned Policy vs Custom Policy

CloudFront supports two policy models for signed URLs and signed cookies:

- Canned policy
- Custom policy

The choice affects what restrictions can be expressed.

| Capability | Canned Policy | Custom Policy |
|---|---:|---:|
| Expiration | Yes | Yes |
| Start time | No | Yes |
| IP restriction | No | Yes |
| Policy embedded in credential | No | Yes |
| Simpler credential | Yes | No |
| Fine-grained restrictions | Limited | Yes |

AWS documents custom policies as supporting additional conditions such as start time and optional IP restrictions, while canned policies provide a simpler structure. :contentReference[oaicite:8]{index=8}

## Canned Policy

A canned policy is appropriate when the authorization requirement is straightforward.

Typical requirement:

> Allow access to this exact object until a specific expiration time.

Conceptually:

```text
Resource
   +
Expiration
   +
Key identifier
   +
Signature
```

Example:

```text
https://cdn.example.com/private/report.pdf
    ?Expires=1780000000
    &Signature=...
    &Key-Pair-Id=K123456
```

The exact values and signature encoding are generated programmatically.

## Custom Policy

Custom policies allow more precise restrictions.

Conceptually:

```json
{
  "Statement": [
    {
      "Resource": "https://cdn.example.com/private/*",
      "Condition": {
        "DateLessThan": {
          "AWS:EpochTime": 1780000000
        },
        "DateGreaterThan": {
          "AWS:EpochTime": 1779990000
        }
      }
    }
  ]
}
```

A custom policy can express restrictions such as:

- Resource pattern
- Start time
- Expiration time
- IP address/range

AWS notes that custom-policy credentials are larger because the policy is included in encoded form. :contentReference[oaicite:9]{index=9}

## Choosing the Policy Type

Use a canned policy when:

```text
One resource
+
Expiration
+
Simple access requirement
```

Use a custom policy when:

```text
Multiple resources
+
Time window
+
Additional restrictions
```

Do not choose custom policies simply because they are more flexible.

More policy complexity means more:

- Testing
- Debugging
- Operational complexity
- Potential configuration mistakes

## Expiration Design

Expiration is one of the most important parts of the authorization model.

For example:

```text
Signed at: 10:00
Expires:    10:15
```

The credential should only remain useful for the required period.

A good rule is:

> Make credentials valid for the minimum practical duration required by the business workflow.

Examples:

| Use case | Typical design |
|---|---|
| Temporary document download | Short lifetime |
| One-time installer | Short lifetime |
| Paid video session | Session-oriented lifetime |
| Subscriber content | Cookie lifetime aligned with entitlement |
| Internal asset access | Short-lived authorization |

Do not use a multi-day or multi-month signed URL for a resource that only needs five minutes of access.

## Clock Synchronization

Signed credentials depend on timestamps.

A system with incorrect time can produce credentials that are:

- Already expired
- Not yet valid
- Valid for the wrong duration

Production signing infrastructure should therefore use reliable time synchronization.

The backend should also avoid manually manipulating timestamps in inconsistent ways.

Prefer a centralized time-handling strategy.

## Signed URL Architecture for Django

A common Django architecture is:

```text
Browser
  │
  ▼
Django / DRF
  │
  ├── Authenticate
  ├── Authorize
  └── Generate signed URL
          │
          ▼
      Browser
          │
          ▼
      CloudFront
          │
          ▼
      Private S3
```

The Django service should not stream large files through the application unless there is a specific requirement.

Instead:

```text
Django
  │
  │ authorize
  ▼
Signed CloudFront URL
  │
  ▼
Browser
  │
  ▼
CloudFront
  │
  ▼
S3
```

This allows CloudFront to perform the high-bandwidth delivery work.

## Django Example

The signing service should encapsulate signing logic rather than placing cryptographic code directly inside views.

Conceptually:

```python
from datetime import datetime, timedelta, timezone


class CloudFrontAccessService:
    def __init__(self, signer):
        self.signer = signer

    def create_download_url(self, resource_url: str) -> str:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        return self.signer.generate_presigned_url(
            resource_url,
            date_less_than=expires_at,
        )
```

The exact signer implementation should use the AWS-supported CloudFront signing libraries or a well-tested cryptographic implementation.

The important application architecture is:

```text
View
  │
  ▼
Authorization Service
  │
  ▼
CloudFront Signing Service
  │
  ▼
Signed URL
```

Avoid implementing signing logic independently in multiple Django views.

## FastAPI Architecture

A FastAPI implementation follows the same pattern:

```text
GET /documents/{document_id}/download
        │
        ▼
Authentication
        │
        ▼
Authorization
        │
        ▼
CloudFrontSigner
        │
        ▼
Signed URL
```

Example response:

```json
{
  "download_url": "https://cdn.example.com/private/report.pdf?...",
  "expires_at": "2026-08-19T18:30:00Z"
}
```

The API should not return a signed URL until the authorization check succeeds.

## Authorization Should Happen Before Signing

This is critical.

Bad architecture:

```text
Request
  │
  ▼
Generate signed URL
  │
  ▼
Check authorization
```

Correct architecture:

```text
Request
  │
  ▼
Authenticate
  │
  ▼
Authorize
  │
  ▼
Generate signed URL
  │
  ▼
Return credential
```

Once a valid signed URL is issued, CloudFront can serve the resource without consulting your application's authorization database.

Therefore the signing service is effectively an **authorization boundary**.

## Database Integration

A Django or FastAPI backend may determine access from PostgreSQL:

```text
User
  │
  ▼
Subscription
  │
  ▼
Resource entitlement
  │
  ▼
Generate signed credential
```

For example:

```sql
SELECT 1
FROM subscriptions s
JOIN resources r
  ON r.subscription_plan_id = s.plan_id
WHERE s.user_id = $1
  AND r.id = $2
  AND s.status = 'active';
```

The signed URL should only be generated if the authorization query succeeds.

## Redis Integration

Redis can be useful for short-lived entitlement or session data:

```text
User
  │
  ▼
Django / FastAPI
  │
  ▼
Redis entitlement cache
  │
  ├── Authorized
  │
  ▼
Generate signed URL
```

However, Redis should not become the only source of truth for long-lived authorization unless the architecture explicitly supports that model.

A good pattern is:

```text
PostgreSQL
    │
    ▼
Authorization state
    │
    ▼
Redis
    │
    ▼
Short-lived decision cache
```

## Signed Cookies for Subscriber Content

Signed cookies are especially useful for a content area containing many objects.

Consider:

```text
https://cdn.example.com/video/course-1/manifest.m3u8
https://cdn.example.com/video/course-1/segment-001.ts
https://cdn.example.com/video/course-1/segment-002.ts
https://cdn.example.com/video/course-1/segment-003.ts
...
```

Generating a separate signed URL for every segment is inconvenient.

A signed-cookie model can instead authorize the browser for the protected content set:

```text
Backend
  │
  │ authorize subscriber
  ▼
Set signed cookies
  │
  ▼
Browser
  │
  ├── manifest.m3u8 ──► CloudFront
  ├── segment-001 ────► CloudFront
  ├── segment-002 ────► CloudFront
  └── segment-N ──────► CloudFront
```

This is one of the strongest use cases for signed cookies. :contentReference[oaicite:10]{index=10}

## Signed Cookies and HTTP Headers

A signed-cookie authorization flow normally involves three CloudFront cookies:

```text
CloudFront-Policy
CloudFront-Signature
CloudFront-Key-Pair-Id
```

For a canned policy, CloudFront uses the appropriate expiration-based cookie structure instead of a full custom policy.

The browser automatically sends the cookies on subsequent requests to the relevant CloudFront domain.

## Cookie Security

Signed cookies should be configured with appropriate browser security attributes.

Conceptually:

```http
Set-Cookie: CloudFront-...;
  Secure;
  HttpOnly;
  SameSite=Lax;
  Path=/private/
```

The exact cookie attributes should match the application's domain and browser requirements.

Important considerations include:

- `Secure`
- `HttpOnly` where JavaScript does not need access
- Appropriate `SameSite`
- Narrow cookie scope where practical
- Appropriate expiration

Do not make cookies broader than necessary.

## Signed URL Leakage

Signed URLs contain authorization material.

For example:

```text
https://cdn.example.com/private/report.pdf?Expires=...&Signature=...
```

A user may copy the URL.

It may also appear in:

- Browser history
- Access logs
- Analytics systems
- Referrer headers in some scenarios
- Support tickets
- Screenshots
- Monitoring systems

Therefore signed URLs should be treated as **bearer credentials** during their validity period.

Anyone possessing a valid signed URL may be able to use it until it expires, subject to the policy restrictions.

## Signed Cookie Leakage

Signed cookies also represent authorization credentials.

If an attacker obtains valid signed cookies, they may be able to access the protected content until the credentials expire or otherwise become invalid.

Protect them like session credentials.

## Preventing Credential Abuse

A common mistake is to assume:

> "The URL is signed, so it cannot be abused."

The signature prevents unauthorized modification, but it does not inherently prevent a valid credential from being copied.

For example:

```text
Authorized User
      │
      │ valid signed URL
      ▼
Attacker copies URL
      │
      ▼
CloudFront
      │
      ▼
Valid signature
      │
      ▼
Content
```

This is why expiration and policy design matter.

For higher-security use cases, consider:

- Short expiration
- Custom policy restrictions where appropriate
- Application-level authorization before issuance
- Content-specific controls
- Tokenization
- DRM for premium video use cases where applicable

## IP Restrictions

Custom policies can optionally restrict access based on IP address or range. :contentReference[oaicite:11]{index=11}

Conceptually:

```text
Signed credential
      │
      ├── Signature valid
      ├── Time valid
      └── IP valid
              │
              ▼
           Allow
```

However, IP restrictions can create operational problems.

Examples:

- Mobile networks changing IP addresses
- Corporate proxies
- VPNs
- IPv4/IPv6 changes
- NAT behavior
- Large enterprise networks

Use IP restrictions only when the network behavior is sufficiently stable for the application's requirements.

## Cache Behavior Integration

Signed URLs and cookies are enforced through CloudFront cache behaviors.

For example:

```text
/*                 → Public content
/private/*         → Signed access required
/downloads/*       → Signed access required
/video/*            → Signed access required
```

Conceptually:

```text
Request
  │
  ▼
Path matching
  │
  ├── /public/* ────────► Public cache behavior
  │
  └── /private/* ───────► Signed access required
```

CloudFront associates trusted key groups with cache behaviors, which means the path-pattern design is part of the security boundary. :contentReference[oaicite:12]{index=12}

## Cache Behavior Ordering

Cache behavior ordering is a common production pitfall.

Suppose the intended configuration is:

```text
/private/* → Require signed access
```

but an earlier, broader behavior matches the same request:

```text
/* → Public
```

The request may be handled by the earlier matching behavior.

AWS specifically warns that cache behavior path patterns and their order must be configured carefully when introducing signed URL or cookie protection. :contentReference[oaicite:13]{index=13}

A safe mental model is:

```text
Specific protected behavior
        │
        ▼
Broader public behavior
```

Review behavior ordering as part of every security change.

## Protecting S3

Signed URLs and signed cookies protect viewer access through CloudFront.

They should generally be combined with origin protection so users cannot bypass CloudFront and access the S3 object directly.

A stronger architecture is:

```text
User
  │
  ▼
CloudFront
  │
  │ signed access
  ▼
S3
  │
  │ private bucket
  ▼
Object
```

Do not rely solely on:

```text
CloudFront signed URL
```

while leaving the underlying S3 objects publicly readable.

If the S3 object is public, an attacker can bypass CloudFront authorization by accessing S3 directly.

## Origin Access Control

For S3 origins, use an appropriate CloudFront origin access control architecture so the bucket can remain private.

The combined model is:

```text
                    ┌──────────────┐
                    │    Client    │
                    └──────┬───────┘
                           │
                     Signed request
                           │
                           ▼
                    ┌──────────────┐
                    │  CloudFront  │
                    └──────┬───────┘
                           │
                  Origin authentication
                           │
                           ▼
                    ┌──────────────┐
                    │      S3      │
                    │    Private   │
                    └──────────────┘
```

This creates two distinct controls:

```text
Viewer → CloudFront
         └── Signed URL/Cookie

CloudFront → S3
             └── Origin access control
```

## Signed URLs and S3 Presigned URLs

These are often confused.

### CloudFront Signed URL

```text
Client
  │
  ▼
CloudFront
  │
  ▼
S3
```

CloudFront controls viewer access.

### S3 Presigned URL

```text
Client
  │
  ▼
S3
```

The client accesses S3 directly using an S3 presigned URL.

| Concern | CloudFront Signed URL | S3 Presigned URL |
|---|---|---|
| CDN delivery | Yes | No |
| Edge caching | Yes | No |
| Viewer authorization at CloudFront | Yes | No |
| Direct S3 access | No | Yes |
| Best for large-scale content delivery | Yes | Sometimes |
| CDN-level controls | Yes | No |

For content that should be delivered through CloudFront, CloudFront signed URLs/cookies are usually the more appropriate authorization mechanism.

## Signed URLs and JWTs

JWTs and CloudFront signed URLs also solve different problems.

A JWT might look conceptually like:

```text
Authorization: Bearer <JWT>
```

The application validates it:

```text
Client
  │
  ▼
API
  │
  ▼
JWT verification
  │
  ▼
Application authorization
```

A CloudFront signed URL is validated by CloudFront:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
Signature verification
  │
  ▼
Content
```

For static/private content delivery, CloudFront signed credentials avoid forcing every file request through the application API.

## Signed URLs and JWT-Based APIs

A common production architecture is:

```text
Client
  │
  ├── API request + JWT ──────► Django/FastAPI
  │
  │                           Authenticate
  │                           Authorize
  │
  └── Signed URL ◄────────────┘
          │
          ▼
      CloudFront
          │
          ▼
      Private content
```

The JWT protects API access.

The CloudFront signed credential protects content delivery.

This separation is generally cleaner than sending JWTs directly to a static-content origin.

## Revocation Limitations

Signed URLs are intentionally self-contained credentials.

This creates an important limitation:

> Issuing a signed URL does not automatically provide an easy per-user revocation mechanism.

Suppose:

```text
Signed URL
Expires in 60 minutes
```

The user is suspended after 5 minutes.

Unless the architecture has an additional control, the signed URL may remain usable until expiration.

This is why expiration should be chosen carefully.

For highly sensitive content:

```text
Short-lived signed credential
+
Application authorization
+
Origin protection
+
Additional security controls
```

may be preferable.

## Key Rotation

Signing keys should be rotated periodically.

A safe rotation strategy is:

```text
Old Key
  │
  │ still valid
  ▼
Add New Public Key
  │
  ▼
Deploy New Private Key
  │
  ▼
Start signing with New Key
  │
  ▼
Wait for old credentials to expire
  │
  ▼
Remove Old Public Key
```

AWS specifically recommends adding the new public key before removing the old one and waiting until credentials signed with the previous key have expired. :contentReference[oaicite:14]{index=14}

Do not perform:

```text
Delete old key
      │
      ▼
Deploy new key
```

without accounting for credentials that are still valid.

## Key Rotation Architecture

```text
                 Key Group
                /         \
               /           \
        Public Key A    Public Key B
             │               │
             │               │
        Old credentials   New credentials
             │               │
             ▼               ▼
         Expire          Start immediately
             │
             ▼
        Remove A
```

During rotation, both keys can temporarily be trusted.

This provides a controlled transition.

## Private Key Storage

The signing private key should never be shipped to the frontend.

Bad:

```text
React / JavaScript
      │
      ▼
Private signing key
```

This completely destroys the security model because anyone who can execute the client code can extract the key and generate credentials.

Correct:

```text
Browser
   │
   ▼
Backend
   │
   │ private key
   ▼
Signing operation
   │
   ▼
Signed URL
```

Only the trusted backend or dedicated signing service should have access to the private key.

## Dedicated Signing Service

At scale, signing can be isolated into a dedicated internal service:

```text
Django / FastAPI
      │
      │ authorization request
      ▼
Signing Service
      │
      │ private key
      ▼
Signed URL
      │
      ▼
Client
```

Advantages include:

- Smaller private-key trust boundary
- Centralized key rotation
- Centralized auditing
- Consistent signing policy
- Reduced cryptographic code duplication

A signing service should not become an authorization bypass.

The application still needs to determine whether the user is allowed to access the resource.

## API Gateway / Nginx Considerations

CloudFront signed URLs should generally be validated by CloudFront rather than implementing equivalent signing validation in Nginx.

For example:

```text
Client
  │
  ▼
CloudFront
  │
  │ signature validation
  ▼
ALB
  │
  ▼
Nginx
  │
  ▼
Origin
```

Nginx can continue handling:

- Routing
- Headers
- Compression where appropriate
- Connection management
- Reverse proxying

without needing the CloudFront private signing key.

## Kubernetes Considerations

If a Kubernetes workload generates signed URLs:

```text
Ingress / ALB
       │
       ▼
Django / FastAPI
       │
       ▼
Signing component
       │
       ▼
CloudFront
```

Do not put the signing private key into every pod.

Prefer a narrow secret-access boundary:

```text
Application
    │
    ▼
Signing service
    │
    ▼
Private key
```

This limits blast radius if an unrelated workload is compromised.

## Celery Considerations

If signed URLs are generated asynchronously, avoid putting private keys into Celery task payloads.

Bad:

```text
Celery Task
  │
  └── private_key=...
```

Better:

```text
Celery Worker
  │
  ▼
Secure key access
  │
  ▼
Signing operation
```

For short-lived downloads, synchronous signing is often simpler because generating a signed URL is lightweight compared with transferring the actual content.

## Kafka Considerations

Do not publish signing private keys or signed credentials unnecessarily through Kafka.

Avoid:

```json
{
  "event": "download.created",
  "private_key": "..."
}
```

Even signed URLs should be treated as authorization credentials.

If an event must reference a download, prefer:

```json
{
  "event": "download.created",
  "resource_id": "report_123"
}
```

and generate the signed URL only when the authorized client needs it.

## Monitoring

CloudFront access-control failures should be observable.

Useful operational signals include:

- 403 response rates
- Expired credential failures
- Invalid signature failures
- Unexpected access spikes
- Access patterns by protected path
- Key rotation failures
- Signing-service failures
- Authorization-service failures

Monitor:

```text
Signing service
      │
      ├── latency
      ├── error rate
      └── key-access failures

CloudFront
      │
      ├── 2xx
      ├── 3xx
      ├── 4xx
      └── 5xx
```

A sudden increase in `403` responses can indicate:

- Expired credentials
- Clock problems
- Incorrect policy
- Incorrect key configuration
- Cache behavior changes
- Broken frontend logic
- Attack attempts

## Logging

Do not log complete signed URLs indiscriminately.

A signed URL contains authorization material.

Bad:

```text
download_url=https://cdn.example.com/private/report.pdf?Expires=...&Signature=...
```

Better:

```text
request_id=req_123
resource_id=report_123
signing_status=success
expires_at=2026-08-19T18:30:00Z
```

If debugging requires identifying the credential, log only a safe identifier or fingerprint rather than the entire credential.

## Cost Considerations

One of the major architectural benefits is that the application does not need to stream every protected byte.

Without CloudFront:

```text
Client
  │
  ▼
Django
  │
  ▼
S3
```

The application may become a bandwidth bottleneck.

With CloudFront:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
S3
```

The application primarily handles authorization and signing.

This improves scalability for:

- Large downloads
- Video
- Static documents
- Images
- Software packages

CloudFront still incurs its normal data-transfer and request costs, so caching strategy and traffic patterns should be considered during capacity and cost planning.

## Reliability Considerations

The signing service should be designed separately from the content-delivery path.

A typical dependency chain is:

```text
User
  │
  ▼
Application
  │
  ▼
Authorization
  │
  ▼
Signing
  │
  ▼
CloudFront
  │
  ▼
Origin
```

Once a signed credential is issued, content requests do not need to call the application for every object.

This reduces runtime coupling:

```text
Signed once
    │
    ▼
Many content requests
    │
    ├── CloudFront
    ├── CloudFront
    ├── CloudFront
    └── CloudFront
```

This is particularly valuable for high-volume media workloads.

## Security Checklist

### CloudFront

- [ ] Protected content uses dedicated cache behaviors.
- [ ] Trusted key groups are used.
- [ ] Path patterns are reviewed.
- [ ] Cache behavior ordering is reviewed.
- [ ] Viewer protocol policy requires HTTPS where appropriate.
- [ ] Public and private content are separated clearly.

### Signing Service

- [ ] Private key never reaches the client.
- [ ] Private key is not stored in Git.
- [ ] Private key is not embedded in Docker images.
- [ ] Signing operations require prior authorization.
- [ ] Signing logic is centralized.
- [ ] Signing failures are monitored.

### Credentials

- [ ] URLs/cookies use short practical lifetimes.
- [ ] Credentials are treated as bearer credentials.
- [ ] Signed URLs are not unnecessarily logged.
- [ ] Signed cookies use appropriate security attributes.
- [ ] Key rotation is tested.

### Origin

- [ ] S3 objects are not publicly readable.
- [ ] CloudFront origin access is protected.
- [ ] Direct origin bypass is prevented.
- [ ] Origin access controls are independently reviewed.

## Common Mistakes and Pitfalls

### Treating a Signed URL as a User Session

A signed URL is not equivalent to a full application session.

It is a scoped content-access credential.

Do not put broad user authorization semantics into a long-lived URL.

### Using Long Expiration Times

A credential valid for 30 days creates a much larger abuse window than one valid for 10 minutes.

Use the shortest practical lifetime.

### Generating URLs Before Authorization

Never generate the URL first and check permissions afterward.

Correct:

```text
Authenticate
    ↓
Authorize
    ↓
Sign
    ↓
Return
```

### Exposing the Private Key

If the private key reaches:

- Browser
- Mobile app
- Frontend JavaScript
- Public repository

the signing trust model is compromised.

### Public S3 Objects

If S3 is public, an attacker can bypass CloudFront entirely.

CloudFront authorization should be combined with origin protection.

### Incorrect Cache Behavior Ordering

A broad public cache behavior can accidentally match a protected resource.

Always inspect path patterns and order.

### Logging Signed URLs

A signed URL can function as a bearer credential.

Logging it may expose content access to anyone who can read the logs.

### No Key Rotation

Static signing keys increase the impact of compromise.

Use controlled rotation with an overlap period.

### Rotating Keys Too Aggressively

Removing the old public key before old credentials expire can invalidate legitimate users.

Maintain an overlap period.

### Using Signed Cookies for One File

Signed cookies can work, but a signed URL is usually simpler when access is limited to one resource.

### Using Signed URLs for Large Content Trees

Generating and distributing a separate signed URL for every protected asset can complicate the client.

Signed cookies may be better when a user needs access to many related resources.

## Decision Matrix

| Requirement | Recommended approach |
|---|---|
| Single private file download | Signed URL |
| Temporary installer download | Signed URL |
| Private PDF | Signed URL |
| Subscriber-only directory | Signed cookies |
| HLS/video with many segments | Signed cookies |
| Keep existing URLs unchanged | Signed cookies |
| Client does not support cookies | Signed URL |
| Multiple restricted files | Signed cookies |
| Short-lived individual access | Signed URL |
| Fine-grained time/IP policy | Custom policy |
| Simple expiration-only policy | Canned policy |
| Application authentication | Django/FastAPI authentication |
| API authorization | Application authorization |
| Private S3 origin | CloudFront Origin Access Control |
| Network encryption | HTTPS/TLS |

## Production Architecture

A mature architecture can combine all of these controls:

```text
                           ┌───────────────────┐
                           │      Client       │
                           └─────────┬─────────┘
                                     │
                                     │ JWT / Session
                                     ▼
                           ┌───────────────────┐
                           │ Django / FastAPI  │
                           └─────────┬─────────┘
                                     │
                            Authenticate +
                             Authorize
                                     │
                                     ▼
                           ┌───────────────────┐
                           │ Signing Service   │
                           │                   │
                           │ Private Key       │
                           └─────────┬─────────┘
                                     │
                         Signed URL / Cookie
                                     │
                                     ▼
                           ┌───────────────────┐
                           │    CloudFront     │
                           │                   │
                           │ Signature verify  │
                           └─────────┬─────────┘
                                     │
                              Origin Access
                                     │
                                     ▼
                           ┌───────────────────┐
                           │ Private S3 Origin │
                           └───────────────────┘
```

This separates responsibilities:

| Layer | Responsibility |
|---|---|
| Client | Present authorization credential |
| Django/FastAPI | Authentication and business authorization |
| Signing service | Generate CloudFront credentials |
| CloudFront | Validate credentials and distribute content |
| S3 | Store private content |
| Origin Access Control | Prevent unauthorized origin access |

## Interview Traps

### Are Signed URLs Authentication?

Not exactly.

They are primarily a mechanism for controlling access to CloudFront content. Your application should perform authentication and authorization before issuing them.

### What Is the Difference Between Signed URLs and Signed Cookies?

Signed URLs put the authorization information in the URL and are convenient for individual resources.

Signed cookies keep URLs unchanged and are useful when a viewer needs access to multiple protected resources. :contentReference[oaicite:15]{index=15}

### Can Anyone Generate a Signed URL?

Not without the appropriate private signing key.

CloudFront validates the signature using a corresponding trusted public key.

### Does CloudFront Need the Private Key?

No.

CloudFront uses the trusted public key to verify signatures. The signing system keeps the private key.

### Can a User Share a Signed URL?

Yes.

A signed URL is effectively a bearer credential while it remains valid. Short expiration times and appropriate policies reduce the risk.

### Can Signed URLs Prevent Direct S3 Access?

Not by themselves.

The S3 origin must also be protected so users cannot bypass CloudFront.

### Should You Use Trusted Signers or Trusted Key Groups?

Use **trusted key groups** for new architectures. AWS recommends them over legacy trusted AWS-account signers. :contentReference[oaicite:16]{index=16}

### Can Signed URLs Be Revoked Immediately?

Not in the same way as a centralized session lookup.

They are intentionally self-contained credentials. Short lifetimes and additional authorization controls should be used when rapid revocation is required.

### What Happens During Key Rotation?

Keep the old public key trusted while new credentials are being issued. After old credentials expire, remove the old public key. :contentReference[oaicite:17]{index=17}

### Which Is Better for HLS?

Signed cookies are often more convenient because a single authorization credential can cover many protected files or segments. :contentReference[oaicite:18]{index=18}

## Key Takeaways

- **Signed URLs are best suited to individual private resources, while signed cookies are generally better when a viewer needs access to many protected resources without changing their URLs.**
- **Use CloudFront trusted key groups for modern signer management and keep the private signing key exclusively inside a trusted backend or signing service.**
- **Authenticate and authorize the user before generating a signed credential; CloudFront should enforce the resulting access policy rather than replace application authorization.**
- **Treat signed URLs and cookies as bearer credentials: use short practical lifetimes, avoid logging them, and design key rotation with an overlap period.**
- **Combine viewer authorization with private origin protection such as CloudFront Origin Access Control so users cannot bypass CloudFront and access the underlying S3 objects directly.**