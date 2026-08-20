# 05- Signed URL and Cookie Questions

## Overview

CloudFront signed URLs and signed cookies provide controlled access to private content delivered through a CloudFront distribution.

They are primarily an **authorization mechanism for CloudFront resources**, not a replacement for application authentication.

A common production architecture is:

```text
                         Internet
                            │
                            ▼
                    ┌─────────────────┐
                    │ Django/FastAPI  │
                    │ Authentication  │
                    │ Authorization   │
                    └────────┬────────┘
                             │
                    Generate signed
                    URL or cookie
                             │
                             ▼
                         Client
                             │
                             │ Authorized request
                             ▼
                    ┌─────────────────┐
                    │   CloudFront    │
                    │                 │
                    │ Signature check │
                    │ Expiration      │
                    │ Policy          │
                    └────────┬────────┘
                             │
                             ▼
                       Private Origin
```

The application decides **whether the user should receive access**. CloudFront then enforces the cryptographic access policy when the client requests the protected resource.

Typical use cases include:

- Private documents.
- Paid downloads.
- Premium video.
- Software downloads.
- Temporary media access.
- Customer-specific assets.
- Training material.
- Subscription-based content.
- Large files that should not pass through the application server.

---

## What Problem Do Signed URLs and Cookies Solve?

Suppose an S3 object is publicly accessible:

```text
https://cdn.example.com/reports/report.pdf
```

Anyone who knows the URL can request it.

For private content, the desired behavior may be:

```text
Authorized user
      │
      ▼
Application
      │
      ├── Authenticate
      ├── Authorize
      └── Issue temporary access
              │
              ▼
          CloudFront
              │
              ▼
        Private content
```

The application does not need to proxy the entire file through Django or FastAPI.

Instead:

1. The application authenticates the user.
2. The application verifies authorization.
3. The application generates a signed URL or signed cookie.
4. The client requests CloudFront.
5. CloudFront validates the signature and policy.
6. CloudFront serves the content if the request is authorized.

This is particularly valuable for large files because the application does not become the data-transfer bottleneck.

---

## Signed URL vs Signed Cookie

Both mechanisms use CloudFront's trusted-key infrastructure to authorize access, but they solve different client-access patterns.

| Characteristic | Signed URL | Signed Cookie |
|---|---|---|
| Best for | Specific resource | Multiple resources |
| Authorization attached to | URL | Cookie |
| Works well for downloads | Yes | Sometimes |
| Multiple files | Less convenient | Excellent |
| User-visible URL | Yes | No authorization data in URL |
| Media collections | Less convenient | Excellent |
| Temporary access | Yes | Yes |
| Shareable URL | Possible, depending on policy | No |
| Browser-based applications | Excellent | Excellent |
| API-generated downloads | Excellent | Possible |

A useful rule is:

> Use a signed URL when access is centered around one resource; use signed cookies when a client needs access to many resources under a protected path or policy.

---

## How CloudFront Signed Access Works

CloudFront signed access is based on public-key cryptography.

Conceptually:

```text
                    Private key
                       │
                       ▼
Application ──sign──► Access policy
                       │
                       ▼
                    Client
                       │
                       │ Signed request
                       ▼
                  CloudFront
                       │
                Public key verifies
                       │
             ┌─────────┴─────────┐
             │                   │
          Valid               Invalid
             │                   │
             ▼                   ▼
          Allow                Reject
```

The application or trusted signing service possesses the private key.

CloudFront has access to the corresponding public key.

The private key is used to generate the signature. CloudFront uses the public key to verify it.

The private key must never be distributed to clients.

---

## CloudFront Key Groups

### What is a key group?

A CloudFront key group is a collection of public keys that CloudFront trusts when validating signed URLs or signed cookies.

The architecture is conceptually:

```text
Application
    │
    │ Private key
    ▼
Generate signature
    │
    ▼
Signed URL / Cookie
    │
    ▼
CloudFront
    │
    │ Key group
    ▼
Trusted public key
```

Modern CloudFront deployments should generally use **trusted key groups** and public keys rather than relying on legacy CloudFront key-pair mechanisms.

---

### Why use key groups?

Key groups provide a manageable trust boundary.

Instead of treating one key as permanently embedded into the entire distribution configuration, a key group can contain the public keys trusted for signed-content verification.

This also makes key rotation easier.

For example:

```text
CloudFront Key Group
│
├── Public Key A
└── Public Key B
```

During rotation:

```text
Old private key ──► Old public key
New private key ──► New public key

Key Group
│
├── Old public key
└── New public key
```

After existing signatures have expired and clients have transitioned:

```text
Key Group
│
└── New public key
```

---

## Why Does CloudFront Use Asymmetric Cryptography?

Asymmetric cryptography allows the signing authority to keep the private key secret while CloudFront only needs the public key.

This is preferable to distributing a shared secret to CloudFront and application clients.

The basic model is:

```text
Private key
    │
    └── Sign

Public key
    │
    └── Verify
```

If the private key is compromised, an attacker may be able to generate valid signatures.

Therefore:

> The private signing key is a high-value secret and must be protected like an application credential.

---

## What Is a Canned Policy?

A canned policy is the simpler CloudFront signed-access policy format.

It provides a relatively straightforward access model centered around:

- The resource.
- An expiration time.

For example:

```text
Resource:
https://cdn.example.com/private/report.pdf

Expires:
2026-08-20 23:00:00

Signature:
<cryptographic signature>
```

Canned policies are useful when the authorization requirement is simple.

Typical use case:

```text
Generate a download link
        │
        ▼
Valid for 15 minutes
        │
        ▼
One CloudFront resource
```

---

## What Is a Custom Policy?

A custom policy provides more control over the access conditions.

It can express conditions such as:

- Resource restrictions.
- Expiration.
- Start time.
- IP-address restrictions.

A conceptual policy might look like:

```json
{
  "Statement": [
    {
      "Resource": "https://cdn.example.com/private/*",
      "Condition": {
        "DateLessThan": {
          "AWS:EpochTime": 1787266800
        },
        "DateGreaterThan": {
          "AWS:EpochTime": 1787265000
        }
      }
    }
  ]
}
```

The exact policy format and signing requirements should be generated according to CloudFront's current signing specification and SDK implementation.

Custom policies are useful when the authorization model requires more than a simple expiration timestamp.

---

## Canned Policy vs Custom Policy

| Capability | Canned Policy | Custom Policy |
|---|---:|---:|
| Expiration | Yes | Yes |
| Resource restriction | Yes | Yes |
| Start time | No | Yes |
| IP restriction | No | Yes |
| Simplicity | High | Lower |
| Flexibility | Lower | Higher |
| Operational complexity | Lower | Higher |

Use the simplest policy that satisfies the actual security requirement.

---

## What Is a Signed URL?

A signed URL is a CloudFront URL containing the information CloudFront needs to validate temporary access.

Conceptually:

```text
https://cdn.example.com/private/report.pdf
    ?Expires=...
    &Signature=...
    &Key-Pair-Id=...
```

The exact parameters depend on the signing mechanism and policy type.

The important concept is that the URL contains cryptographic authorization material that CloudFront can validate.

---

## Signed URL Request Lifecycle

```mermaid
sequenceDiagram
    participant U as User
    participant A as Django/FastAPI
    participant C as CloudFront
    participant O as Private Origin

    U->>A: Request protected resource
    A->>A: Authenticate user
    A->>A: Authorize resource access
    A->>A: Generate signed URL
    A-->>U: Signed CloudFront URL

    U->>C: GET signed URL
    C->>C: Validate signature
    C->>C: Validate policy/time constraints

    alt Valid
        C->>O: Fetch resource if cache miss
        O-->>C: Resource
        C-->>U: Protected resource
    else Invalid or expired
        C-->>U: Access denied
    end
```

The key architectural advantage is that the application participates in **authorization**, but does not need to handle the actual content transfer.

---

## What Happens When a Signed URL Expires?

Once the signed URL's authorization conditions are no longer valid, CloudFront should reject requests using that authorization.

For example:

```text
Signed URL
    │
    ├── 20:00 → Valid
    ├── 20:10 → Valid
    └── 20:15 → Expired
                    │
                    ▼
                 Reject
```

Expiration does not mean the underlying object has been deleted.

It means the particular CloudFront authorization has expired.

---

## Does Expiration Remove the Object From CloudFront Cache?

No.

This is an important interview distinction.

The authorization policy controls whether the viewer is allowed to access the resource.

Caching determines whether CloudFront already has the object available at the edge.

Conceptually:

```text
Authorization
     │
     └── Can this request access the resource?

Caching
     │
     └── Where can CloudFront retrieve the resource from?
```

A cached object may continue to exist internally according to its caching behavior even after a particular signed authorization expires.

The viewer still needs valid authorization to receive it through the protected distribution.

---

## What Is a Signed Cookie?

A signed cookie allows CloudFront to authorize requests using cookies rather than placing authorization information directly in every URL.

This is useful when a user needs access to many resources.

For example:

```text
User receives signed cookies
        │
        ├── GET /video/lesson-1.mp4
        ├── GET /video/lesson-2.mp4
        ├── GET /video/lesson-3.mp4
        └── GET /video/lesson-4.mp4
```

The client does not need a separate signed URL for every object.

---

## Why Are Signed Cookies Useful for Video?

Consider a video system where one course contains hundreds of segments:

```text
/course-1/
    segment-001.ts
    segment-002.ts
    segment-003.ts
    ...
    segment-500.ts
```

Generating and managing a separate signed URL for every segment is inconvenient.

A signed cookie can authorize access to the required protected content according to the configured policy.

This makes signed cookies particularly useful for:

- Streaming media.
- Video libraries.
- Course platforms.
- Protected asset collections.
- Multi-file downloads.

---

## Signed URL Example With Python

A backend can generate CloudFront signed URLs after performing its own authorization checks.

A common Python approach is to use the AWS SDK's CloudFront signing support with an RSA private key.

```python
from datetime import datetime, timedelta, timezone

import boto3


def create_signed_url(
    cloudfront_url: str,
    key_id: str,
    private_key_path: str,
    expires_in_seconds: int = 900,
) -> str:
    with open(private_key_path, "rb") as key_file:
        private_key = key_file.read()

    signer = boto3.cloudfront.CloudFrontSigner(
        key_id,
        lambda message: _rsa_sign(message, private_key),
    )

    expire_at = datetime.now(timezone.utc) + timedelta(
        seconds=expires_in_seconds
    )

    return signer.generate_presigned_url(
        cloudfront_url,
        date_less_than=expire_at,
    )
```

The signing implementation should use a proper RSA signing implementation and should never expose the private key to the browser.

A production system should generally retrieve the private key from a secure secret-management mechanism rather than storing it directly in the application repository or container image.

---

## Why Should the Application Generate Signed URLs?

The application usually has the business context required to determine whether the user should receive access.

For example:

```text
GET /api/documents/123/download
```

Django/FastAPI can perform:

```text
Authentication
      │
      ▼
User exists?
      │
      ▼
User owns document?
      │
      ▼
Subscription active?
      │
      ▼
Generate signed URL
```

CloudFront should not need to understand the entire business relationship between:

- User.
- Subscription.
- Organization.
- Document.
- Order.
- Entitlement.

The application already has that context.

---

## Example Django Architecture

A Django API might expose:

```text
GET /api/documents/{document_id}/download/
```

The endpoint can:

1. Authenticate the user.
2. Retrieve the document.
3. Verify ownership or entitlement.
4. Generate a short-lived CloudFront signed URL.
5. Return the URL.

Conceptually:

```python
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required


@login_required
def download_document(request, document_id):
    document = get_object_or_404(
        Document,
        id=document_id,
    )

    if not document.user_can_download(request.user):
        return JsonResponse(
            {"detail": "Forbidden"},
            status=403,
        )

    signed_url = create_signed_url_for_document(document)

    return JsonResponse(
        {
            "url": signed_url,
            "expires_in": 900,
        }
    )
```

The important security property is that the signed URL is issued only after application-level authorization succeeds.

---

## Why Should Signed URLs Usually Be Short-Lived?

Long-lived signed URLs increase the impact of URL leakage.

URLs can accidentally appear in:

- Browser history.
- Access logs.
- Monitoring systems.
- Screenshots.
- Chat messages.
- Referrer data.
- Support tickets.
- Client-side debugging tools.

If a URL is valid for 15 minutes, accidental exposure has a smaller security window than a URL valid for 30 days.

A practical pattern is:

```text
High-value private document
        │
        └── 5–15 minute authorization

Long-running media session
        │
        └── Session-appropriate signed cookie lifetime
```

The correct duration depends on the application's threat model and user experience.

---

## Can a Signed URL Be Revoked?

A signed URL is primarily time/policy based.

Once a valid signed URL has been issued, revoking that individual URL immediately is not as straightforward as revoking a database session.

This is an important architectural limitation.

Suppose:

```text
10:00 → Application issues URL
10:01 → User account disabled
10:02 → URL still valid
```

If the URL's policy remains valid, CloudFront may continue honoring it.

Therefore, for sensitive systems:

- Keep expiration periods short.
- Avoid excessively long authorization windows.
- Design explicit revocation mechanisms where required.
- Consider invalidating or replacing content when appropriate.
- Do not treat a signed URL as a fully stateful authorization session.

---

## Signed URL and Application Authorization

A common mistake is:

```text
User has a valid signed URL
        │
        ▼
Therefore user is currently authorized
```

That assumption is not always correct.

A signed URL proves that the request satisfies the CloudFront signing policy.

It does not necessarily prove that the user's current business authorization remains valid.

The application should therefore choose an appropriate expiration period.

---

## Signed Cookies and Browser Security

Signed cookies are credentials.

They should be treated as sensitive authentication-like material.

Consider:

- HTTPS-only delivery.
- Appropriate cookie attributes where applicable.
- Short expiration periods.
- Avoiding unnecessary exposure to client-side JavaScript.
- Preventing cross-site misuse where the application's architecture allows it.

For browser-based applications, cookie behavior should be designed alongside the application's normal authentication and CSRF model.

---

## Can Signed Cookies Be Used With Any CloudFront Resource?

They can be used for resources served through the relevant CloudFront distribution when the distribution behavior is configured to require signed access and the request satisfies the associated policy.

The practical requirement is that the request must reach the CloudFront behavior configured for the protected content.

For example:

```text
cdn.example.com
│
├── /public/*
│      └── Public behavior
│
└── /private/*
       └── Trusted-signature behavior
```

This allows a distribution to serve public and private content using different behaviors.

---

## Public vs Private Behaviors

A single distribution can contain different path-based behaviors.

Example:

| Path | Access model |
|---|---|
| `/assets/*` | Public |
| `/images/public/*` | Public |
| `/documents/private/*` | Signed access |
| `/videos/premium/*` | Signed access |

This avoids unnecessarily requiring signatures for every resource.

The configuration should be explicit so that sensitive paths cannot accidentally inherit a public behavior.

---

## How Does Cache Policy Interact With Signed URLs?

Signed URL parameters are authorization metadata.

They should not automatically be treated as business data that must create a completely separate cache object for every signature.

A good architecture separates:

```text
Authorization
      │
      └── Is this viewer allowed?

Cache identity
      │
      └── Which representation is being requested?
```

Otherwise, every unique signed URL could unnecessarily fragment the cache.

The exact CloudFront behavior depends on the distribution's cache policy and configuration.

The important engineering principle is:

> Do not confuse authorization parameters with representation-varying cache-key inputs.

---

## Can Multiple Users Share the Same Signed URL?

Potentially, yes.

If a signed URL is not bound to a specific user identity, anyone who obtains a still-valid URL may be able to use it.

For example:

```text
User A receives signed URL
       │
       ▼
URL copied to User B
       │
       ▼
User B requests URL
       │
       ▼
CloudFront validates signature
       │
       ▼
Access may succeed
```

Therefore:

> A signed URL should be treated as a bearer credential unless the policy provides additional restrictions.

This is one of the most important security concepts for interviews.

---

## IP Restrictions

Custom policies can support additional request conditions such as IP restrictions.

For example:

```text
Signed policy
│
├── Resource = private/report.pdf
├── Expiration = 15 minutes
└── Allowed IP = expected client address
```

This can reduce the usefulness of a leaked URL in some environments.

However, IP-based restrictions can create usability and reliability problems because client IP addresses can change due to:

- Mobile networks.
- NAT.
- Corporate proxies.
- VPNs.
- Carrier networks.

Use IP restrictions only when the application's environment makes them appropriate.

---

## Should You Bind Every Signed URL to an IP?

Usually not.

For general consumer internet applications, IP binding can cause legitimate requests to fail when the client's apparent IP changes.

A better default is:

```text
Short expiration
+
Strong signature
+
Application authorization
```

Add IP restrictions only when there is a concrete security requirement.

---

## Private S3 + CloudFront Signed URL

A common production architecture is:

```text
                         ┌─────────────────┐
                         │ Django/FastAPI  │
                         │                 │
                         │ Auth + Authz    │
                         └────────┬────────┘
                                  │
                           Signed URL
                                  │
                                  ▼
                              Browser
                                  │
                                  ▼
                         ┌─────────────────┐
                         │   CloudFront    │
                         │ Signed Access   │
                         └────────┬────────┘
                                  │
                           Origin Access
                              Control
                                  │
                                  ▼
                         ┌─────────────────┐
                         │   Private S3    │
                         │     Bucket      │
                         └─────────────────┘
```

This architecture provides separation of responsibilities:

| Component | Responsibility |
|---|---|
| Django/FastAPI | User authentication and business authorization |
| CloudFront | Signed-content enforcement and content delivery |
| OAC | CloudFront-to-S3 authorization |
| S3 | Object storage |
| Browser | Uses temporary authorization |

---

## Signed URL vs Direct S3 Presigned URL

CloudFront signed URLs and S3 presigned URLs solve related but different problems.

| Characteristic | CloudFront Signed URL | S3 Presigned URL |
|---|---|---|
| Delivery layer | CloudFront | S3 |
| CDN caching | Yes | No CloudFront caching by default |
| Edge delivery | Yes | No |
| Private S3 origin | Yes | Direct S3 access |
| Large global audience | Excellent | Less optimized |
| Temporary object access | Yes | Yes |
| Application can bypass CDN | Not necessarily | Yes, by design |
| Typical use | Protected CDN content | Direct temporary S3 access |

For a globally distributed application where content should be delivered through CloudFront, CloudFront signed access is often the better architectural fit.

---

## Signed URL vs Application Proxy

There are two common approaches to protected downloads.

### Application Proxy

```text
User
  │
  ▼
Django/FastAPI
  │
  ▼
S3
  │
  ▼
Django/FastAPI
  │
  ▼
User
```

The application handles the data transfer.

### Signed CloudFront URL

```text
User
  │
  ▼
Django/FastAPI
  │
  └── Authorization only
          │
          ▼
       CloudFront
          │
          ▼
       S3 / Origin
```

The second model is generally more scalable for large files because the application is not in the data path.

---

## Performance Considerations

Signed access does not eliminate CloudFront caching.

A typical flow is:

```text
Authorized request
       │
       ▼
CloudFront signature validation
       │
       ▼
Cache lookup
       │
       ├── Hit ──► Serve edge cache
       │
       └── Miss ─► Origin
```

This allows protected content to benefit from CDN distribution.

For large files and media, this can substantially reduce origin bandwidth and application-server load.

---

## Security Considerations

### Protect the Private Key

Never:

- Commit it to Git.
- Put it in frontend JavaScript.
- Put it in a public Docker image.
- Send it to the browser.
- Store it in source code.
- Log it.

Prefer a secure secret-management strategy.

### Use Short Expiration

Avoid unnecessarily long authorization windows.

### Authorize Before Signing

The application should verify the user's entitlement before generating access credentials.

### Treat URLs as Secrets

A signed URL can be replayed while it remains valid if an unauthorized party obtains it.

### Protect the Origin

For private S3 origins:

- Keep the bucket private.
- Use OAC.
- Block public access.

### Monitor Access

Use CloudFront logs and application-level audit events to understand who is requesting protected resources.

---

## Key Rotation

Private signing keys should have an operational rotation strategy.

A safe conceptual rotation process is:

```text
Current key
    │
    ▼
Create new key pair
    │
    ▼
Add new public key to trusted key group
    │
    ▼
Deploy application using new private key
    │
    ▼
Wait for old signatures to expire
    │
    ▼
Remove old public key
```

The overlap period is important.

If the old public key is removed before all old signatures have expired, valid clients can suddenly receive authorization failures.

---

## What Happens If the Private Key Is Compromised?

Assume an attacker obtains the private signing key.

The attacker may be able to generate valid CloudFront signed URLs or cookies.

The response should include:

1. Stop using the compromised private key.
2. Generate a new key pair.
3. Add the new public key to the trusted key group.
4. Update the signing service to use the new private key.
5. Remove the compromised public key when appropriate.
6. Reduce authorization lifetimes if necessary.
7. Investigate how the private key was exposed.
8. Audit access associated with the compromised credentials.

This is why key rotation and secret management should be designed before production deployment.

---

## Operational Monitoring

Useful signals include:

| Signal | Possible interpretation |
|---|---|
| Increased 403 responses | Invalid or expired signatures |
| Sudden increase in signed URL generation | Application or abuse issue |
| Unexpected geographic access | Credential sharing or abuse |
| Repeated requests to protected paths | Automated probing |
| Sudden origin traffic | Cache miss or authorization/content behavior change |
| Key validation failures | Client expiration, configuration error, or attack |

A 403 spike should not automatically be treated as an attack.

It can also indicate:

- Clock skew.
- Expired URLs.
- Incorrect key IDs.
- Wrong distribution configuration.
- Invalid signatures.
- Application bugs.

---

## Clock Synchronization

Time-based policies depend on accurate time.

If the signing server's clock is significantly incorrect, signatures can appear prematurely expired or not yet valid.

Production systems should synchronize system clocks using standard time synchronization mechanisms.

For example:

```text
Application server
       │
       ▼
Accurate system clock
       │
       ▼
Generate policy expiration
       │
       ▼
CloudFront validates policy
```

Time synchronization becomes particularly important when using custom policies with both start and expiration times.

---

## Common Mistakes

| Mistake | Why it is dangerous | Better approach |
|---|---|---|
| Putting private key in frontend | Anyone can generate signatures | Keep key server-side |
| Making URLs valid for months | Large replay window | Use short-lived access |
| Assuming signed URL identifies user | URL can be shared | Treat as bearer authorization |
| Skipping application authorization | Unauthorized users can obtain URLs | Authorize before signing |
| Using IP restriction everywhere | Mobile/proxy clients may change IP | Use only when justified |
| Proxying every large download through Django | Application becomes bandwidth bottleneck | Offload delivery to CloudFront |
| Public S3 bucket behind CloudFront | Direct origin bypass | Private S3 + OAC |
| Removing old key immediately | Existing clients fail | Rotate with overlap |
| Logging complete signed URLs | Logs may contain credentials | Redact sensitive query parameters |
| Confusing cache with authorization | Incorrect security assumptions | Model cache and access independently |
| Ignoring clock skew | Valid requests can fail | Maintain accurate server time |
| Using custom policies unnecessarily | More complexity | Use simplest sufficient policy |

---

## Interview Questions and Answers

### What is a CloudFront signed URL?

A signed URL is a CloudFront URL containing cryptographic authorization information that allows CloudFront to verify whether access to a protected resource is permitted.

It is commonly used for temporary access to private content.

---

### What is the difference between signed URLs and signed cookies?

Signed URLs attach authorization information to individual URLs and are well suited to individual downloads or resources.

Signed cookies provide authorization separately from the URL and are useful when a client needs access to many protected resources.

---

### When would you choose a signed cookie instead of a signed URL?

Use a signed cookie when a user needs access to multiple protected resources under a common policy, such as a video library containing many segments.

Use a signed URL when access is primarily centered around a specific object.

---

### Are signed URLs authentication?

No.

They provide CloudFront resource authorization.

The application may authenticate the user and determine whether the user is entitled to access the resource before issuing the signed URL.

---

### Can a signed URL be shared?

Yes.

Unless additional restrictions prevent it, anyone who obtains a valid signed URL may be able to use it until it expires.

Treat signed URLs as bearer credentials.

---

### Can CloudFront signed URLs prevent URL sharing?

Not completely.

A signed URL can be made short-lived and, in some custom-policy designs, additional restrictions can be applied.

But if the URL is fundamentally bearer-based, someone who obtains it may be able to replay it during its validity period.

---

### What happens when a signed URL expires?

CloudFront rejects subsequent requests that do not satisfy the required signed-access policy.

The underlying object is not automatically deleted.

---

### Can you revoke one signed URL immediately?

Not in the same way that a stateful application session can be revoked.

Signed access is primarily policy and time based.

If immediate revocation is a requirement, the system needs an additional design for revocation or content-access control.

---

### What is a CloudFront key group?

A key group contains public keys that CloudFront trusts when validating signed URLs or signed cookies.

The application keeps the corresponding private signing key.

---

### Why is asymmetric cryptography useful here?

The private key can remain exclusively with the trusted signing system while CloudFront verifies signatures using the corresponding public key.

This avoids distributing the signing secret to clients.

---

### What is a canned policy?

A canned policy is a simpler signed-access policy primarily intended for straightforward authorization requirements such as resource and expiration.

---

### What is a custom policy?

A custom policy provides more control over authorization conditions, including conditions such as start time and IP restrictions.

---

### What is the main security risk of a compromised private signing key?

An attacker who obtains the private key may be able to create valid CloudFront signed authorization.

The key should therefore be treated as a high-value secret and rotated immediately if compromised.

---

### Should signed URLs be generated by the frontend?

No.

The frontend should receive the signed URL after the trusted backend has performed authorization.

The private signing key must remain on a trusted backend or signing service.

---

### Can Django or FastAPI generate signed URLs?

Yes.

A Django or FastAPI backend can authenticate and authorize the user and then use a CloudFront signing implementation to generate a temporary signed URL or signed-cookie values.

---

### Why use CloudFront signed URLs instead of S3 presigned URLs?

CloudFront signed URLs authorize access through the CDN and allow the content to benefit from CloudFront's global edge delivery and caching model.

S3 presigned URLs authorize direct S3 access.

The appropriate choice depends on whether the application wants S3 to be the direct delivery endpoint or CloudFront to remain the content-delivery layer.

---

### Does a signed URL bypass CloudFront caching?

No.

Authorization and caching are separate concerns.

A valid signed request can still be served from a CloudFront cache according to the distribution's caching configuration.

---

### Can a signed URL be used with a private S3 bucket?

Yes.

A common architecture uses:

```text
Client
  │
  ▼
CloudFront
  │
  ├── Signed URL validation
  │
  ▼
OAC
  │
  ▼
Private S3
```

CloudFront handles viewer authorization while OAC controls CloudFront's access to the private S3 origin.

---

### Why shouldn't the application proxy every protected download?

For large files, proxying every download through Django or FastAPI consumes:

- Application bandwidth.
- Worker capacity.
- Network resources.
- CPU and memory resources.
- Infrastructure scaling capacity.

CloudFront allows the application to make the authorization decision while the CDN handles content delivery.

---

### What is the most important distinction when explaining signed URLs in an interview?

The strongest answer separates **authentication, authorization, and content delivery**:

```text
Application
    │
    ├── Authentication
    ├── Business authorization
    └── Issue temporary CloudFront authorization
                    │
                    ▼
                CloudFront
                    │
                    ├── Validate signature
                    └── Deliver content
```

The signed URL is not the user's complete identity or authorization system. It is a controlled credential for accessing CloudFront content.

---

## Production Decision Matrix

| Requirement | Recommended approach |
|---|---|
| Public static assets | Normal CloudFront access |
| Private single document | Signed URL |
| Temporary large-file download | Signed URL |
| Private video library | Signed cookies |
| HLS/DASH-style multi-object content | Signed cookies |
| Private S3 origin | OAC + private bucket |
| User entitlement | Application authorization |
| Very short download access | Short-lived signed URL |
| Multiple protected resources | Signed cookies |
| Long-lived public content | Public CloudFront behavior |
| High-security private content | Short-lived authorization + protected origin + monitoring |
| Direct S3 temporary access required | S3 presigned URL |

## Production Checklist

Before deploying signed CloudFront access, verify:

- [ ] Private signing key is stored securely.
- [ ] Private key is never shipped to clients.
- [ ] Private key is not committed to source control.
- [ ] Application authenticates users before issuing access.
- [ ] Application checks resource-level authorization.
- [ ] Signed URLs/cookies have appropriate expiration.
- [ ] Private content uses a protected CloudFront behavior.
- [ ] Public and private paths are explicitly separated.
- [ ] Private S3 origins use OAC where appropriate.
- [ ] S3 public access is blocked where CloudFront is the intended access path.
- [ ] CloudFront and origin use HTTPS where appropriate.
- [ ] Signed URLs are treated as bearer credentials.
- [ ] Logs do not unnecessarily expose complete signed URLs.
- [ ] Key rotation is documented and tested.
- [ ] Old and new signing keys have an intentional overlap period during rotation.
- [ ] Monitoring exists for unexpected 403 increases.
- [ ] Server clocks are synchronized.
- [ ] Revocation requirements are understood before selecting expiration periods.
- [ ] Cache behavior is reviewed independently from authorization behavior.

## Key Takeaways

- **Signed URLs and signed cookies provide temporary, cryptographically verifiable authorization for CloudFront content; they do not replace application authentication or business authorization.**
- **Use signed URLs for individual resources and signed cookies when a client needs access to multiple protected resources under a common policy.**
- **Keep CloudFront private signing keys exclusively on trusted backend infrastructure, use short authorization lifetimes, and maintain a deliberate key-rotation strategy.**
- **Treat signed URLs as bearer credentials because anyone who obtains a valid URL may be able to replay it until its policy expires.**
- **Separate viewer authorization, CloudFront caching, and origin protection; a secure design commonly combines signed access, appropriate cache policies, and protected origins such as private S3 with OAC.**