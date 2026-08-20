# 11- Signed Cookie Issues

## Overview

CloudFront signed cookies provide controlled access to multiple private resources without requiring a separate signed URL for every object.

They are particularly useful when a client needs to access a collection of protected resources, such as:

- Private video segments
- Multiple images belonging to a protected page
- Private downloadable assets
- Subscription-based media
- Customer-specific static content
- Applications serving many related protected objects

A signed-cookie request typically works like this:

```text
Client
   │
   │ Request protected application page
   ▼
Backend
   │
   │ Authenticate + authorize
   │ Generate CloudFront signed-cookie values
   ▼
Client
   │
   │ Cookies automatically attached
   ▼
CloudFront
   │
   ├── Cookie valid → Cache / Origin
   │
   └── Cookie invalid → 403
```

The key operational difference from signed URLs is that authorization information is carried in HTTP cookies rather than embedded in each resource URL.

When troubleshooting signed-cookie failures, focus on four areas:

1. Cookie generation
2. Cookie delivery and browser behavior
3. CloudFront trust and policy configuration
4. Resource, domain, path, and expiration compatibility

A `403 Forbidden` from CloudFront does not necessarily mean the signing algorithm is wrong. The cookie may have been generated correctly but never sent to CloudFront, sent for the wrong domain, expired, modified, or signed with a key that CloudFront does not trust.

## Signed Cookies vs Signed URLs

Both mechanisms provide CloudFront-level authorization, but they solve different delivery patterns.

| Characteristic | Signed URL | Signed Cookie |
|---|---|---|
| Authorization location | URL query parameters | HTTP cookies |
| Best for | Individual resources | Multiple related resources |
| URL remains clean | No | Yes |
| Requires changing resource URLs | No for cookie-based access | No |
| Browser automatically sends credentials | No | Yes |
| Useful for media segments | Less convenient | Often more convenient |
| Multiple objects | Requires multiple signed URLs | One cookie set can authorize many resources |
| Troubleshooting | URL/signature focused | Cookie/domain/browser focused |

A useful rule is:

> Use signed URLs when authorization is naturally attached to one resource. Use signed cookies when a client needs access to multiple protected resources under a common authorization policy.

## Why Signed Cookies Exist

Consider a protected video:

```text
/video/movie/manifest.m3u8
/video/movie/segment-001.ts
/video/movie/segment-002.ts
/video/movie/segment-003.ts
...
```

Generating and distributing a separate signed URL for every segment is inefficient.

With signed cookies:

```text
Client
  │
  ├── CloudFront-Policy
  ├── CloudFront-Signature
  └── CloudFront-Key-Pair-Id
          │
          ▼
     CloudFront
          │
          ├── manifest
          ├── segment-001
          ├── segment-002
          └── segment-003
```

The cookie policy can authorize access to a resource pattern rather than requiring authorization data in every URL.

## Signed Cookie Components

CloudFront signed cookies use three related cookie values:

| Cookie | Purpose |
|---|---|
| `CloudFront-Policy` | Custom policy containing access conditions |
| `CloudFront-Signature` | Cryptographic signature for the policy |
| `CloudFront-Key-Pair-Id` | Identifies the trusted public key |

For a canned policy, CloudFront uses:

| Cookie | Purpose |
|---|---|
| `CloudFront-Expires` | Expiration timestamp |
| `CloudFront-Signature` | Cryptographic signature |
| `CloudFront-Key-Pair-Id` | Identifies the trusted public key |

The browser must send the appropriate cookie values when requesting the protected CloudFront resource.

## Custom Policy vs Canned Policy

CloudFront supports both canned and custom policies for signed cookies.

| Policy type | Main characteristics |
|---|---|
| Canned policy | Simpler; expiration-based access to a specific resource |
| Custom policy | Supports resource patterns and additional conditions |

Custom policies are particularly useful when multiple related resources need to be protected.

For example:

```text
https://cdn.example.com/video/course-123/*
```

can potentially authorize access to:

```text
/video/course-123/manifest.m3u8
/video/course-123/segment-001.ts
/video/course-123/segment-002.ts
```

The policy should be as restrictive as practical.

## Signed Cookie Request Lifecycle

```mermaid
sequenceDiagram
    participant B as Browser
    participant A as Backend
    participant CF as CloudFront
    participant O as Origin

    B->>A: Authenticate and request protected content
    A->>A: Authorize user
    A->>A: Generate CloudFront cookie values
    A-->>B: Set-Cookie headers
    B->>CF: Request protected resource + cookies
    CF->>CF: Validate policy, signature and key
    alt Valid
        CF->>O: Origin request on cache miss
        O-->>CF: Protected resource
        CF-->>B: Resource
    else Invalid
        CF-->>B: 403 Forbidden
    end
```

The backend's responsibility is to establish authorization and issue the cookies.

CloudFront's responsibility is to validate the signed-cookie credentials on subsequent requests.

## Browser Cookie Mechanics Matter

Signed cookies introduce an additional troubleshooting layer that signed URLs do not have.

The backend can generate a perfectly valid signature while the browser never sends it to CloudFront.

The request must satisfy normal cookie rules involving:

- Domain
- Path
- Secure
- SameSite
- Expiration
- Browser cookie policies
- Cross-site behavior
- HTTPS
- Request destination

This creates an important diagnostic distinction:

```text
Cookie generation
       │
       ▼
Cookie response
       │
       ▼
Browser stores cookie?
       │
       ▼
Browser sends cookie to CloudFront?
       │
       ▼
CloudFront validates cookie
```

A failure at any stage can result in access denial.

## Domain Configuration

Cookie domain configuration is one of the most common causes of signed-cookie problems.

Suppose the CloudFront distribution uses:

```text
cdn.example.com
```

but the backend responds from:

```text
api.example.com
```

The cookie must be scoped so that the browser sends it to the CloudFront hostname.

For example:

```http
Set-Cookie: CloudFront-Key-Pair-Id=...; Domain=.example.com; Path=/; Secure
```

A domain that is too narrow can prevent the cookie from being sent to CloudFront.

A domain that is broader than necessary can increase the scope of the credential.

Prefer the narrowest domain scope that satisfies the architecture.

## Cookie Path

The `Path` attribute controls which request paths receive the cookie.

For example:

```http
Path=/private-video/
```

means the cookie will be sent for paths under:

```text
/private-video/
```

but may not be sent for:

```text
/public/
```

If CloudFront requests are outside the configured cookie path, the browser may omit the cookie entirely.

For broad protected applications, this may be appropriate:

```http
Path=/
```

For tightly scoped authorization, a narrower path can reduce exposure.

## Secure Attribute

Signed cookies should normally use:

```http
Secure
```

This ensures that browsers send the cookie only over HTTPS.

Production CloudFront distributions should use HTTPS for protected content.

A missing `Secure` attribute is not always the direct cause of a 403, but failing to enforce HTTPS weakens the security model and can create inconsistent browser behavior.

## SameSite Considerations

The `SameSite` cookie attribute can affect whether browsers send cookies in cross-site request scenarios.

This becomes important when:

```text
Application:
https://app.example.com

CDN:
https://cdn.example.com
```

and especially when the frontend is embedded or accessed through a different site context.

The appropriate `SameSite` value depends on the application architecture.

Do not blindly change `SameSite` to `None`.

If cross-site cookie delivery is genuinely required, browsers generally require:

```http
SameSite=None; Secure
```

Test the behavior in the actual browser environment used by customers.

## Inspect Browser Cookies

Browser developer tools are often more useful than backend logs for signed-cookie failures.

Inspect the storage/cookies section and verify that all expected values exist:

```text
CloudFront-Policy
CloudFront-Signature
CloudFront-Key-Pair-Id
```

or, for a canned policy:

```text
CloudFront-Expires
CloudFront-Signature
CloudFront-Key-Pair-Id
```

Then inspect the failing CloudFront request and verify that the cookies were actually attached.

The distinction is critical:

```text
Cookie exists in browser
        ≠
Cookie was sent with request
```

## Inspect the Actual Request

Use browser developer tools or an HTTP client to inspect request headers.

The request should contain a cookie header similar to:

```http
Cookie: CloudFront-Key-Pair-Id=...;
        CloudFront-Signature=...;
        CloudFront-Policy=...
```

Do not expose complete production signatures in tickets, logs, or screenshots.

Redact sensitive values:

```http
Cookie: CloudFront-Key-Pair-Id=[REDACTED];
CloudFront-Signature=[REDACTED];
CloudFront-Policy=[REDACTED]
```

## 403 Caused by Missing Cookies

A common flow is:

```text
Backend generates cookies
        │
        ▼
Browser receives Set-Cookie
        │
        ├── Domain mismatch
        │
        ├── Path mismatch
        │
        ├── SameSite restriction
        │
        ├── Secure/HTTPS mismatch
        │
        └── Browser blocks cookie
                │
                ▼
CloudFront request has no cookies
                │
                ▼
403 Forbidden
```

If CloudFront is configured to require signed cookies, missing credentials normally result in authorization failure.

Before debugging cryptography, verify that the browser actually sent the cookies.

## Set-Cookie Response Example

A backend might return:

```http
Set-Cookie: CloudFront-Key-Pair-Id=K123456789; Domain=cdn.example.com; Path=/; Secure; HttpOnly
Set-Cookie: CloudFront-Signature=<signature>; Domain=cdn.example.com; Path=/; Secure; HttpOnly
Set-Cookie: CloudFront-Policy=<policy>; Domain=cdn.example.com; Path=/; Secure; HttpOnly
```

The exact attributes should match the application architecture.

Do not add `HttpOnly` blindly if browser JavaScript genuinely needs access to the cookie. However, signed CloudFront cookies generally should not need to be read or manipulated by frontend JavaScript, so `HttpOnly` is often desirable where compatible with the application.

## Backend Cookie Generation

A backend service should centralize signed-cookie creation.

For example:

```python
class CloudFrontCookieSigner:
    def __init__(self, key_id: str, private_key: bytes):
        self.key_id = key_id
        self.private_key = private_key

    def create_cookies(self, resource: str, expires_at: int) -> dict[str, str]:
        # Use the AWS-supported CloudFront signing implementation.
        # Return only the cookie values required by the chosen policy.
        raise NotImplementedError
```

The signing implementation should use the AWS-supported SDK/library mechanism appropriate to the CloudFront configuration.

Do not implement the cryptographic protocol manually unless there is a compelling reason and the implementation is independently reviewed.

## Django Integration

A Django endpoint may authenticate the user and issue CloudFront cookies:

```python
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required


@login_required
def authorize_video(request, video_id):
    video = get_video_for_user(request.user, video_id)

    cookies = cloudfront_signer.create_cookies(
        resource=f"https://cdn.example.com/video/{video.id}/*",
        expires_at=calculate_expiration(),
    )

    response = HttpResponse(status=204)

    for name, value in cookies.items():
        response.set_cookie(
            key=name,
            value=value,
            secure=True,
            httponly=True,
            samesite="Lax",
            path="/",
        )

    return response
```

The exact `Domain` and `SameSite` configuration depends on how the application and CloudFront domains are deployed.

For cross-site scenarios, the cookie attributes may need to be different.

## FastAPI Integration

The same pattern can be implemented with FastAPI:

```python
from fastapi import APIRouter, Response

router = APIRouter()


@router.get("/videos/{video_id}/authorize")
def authorize_video(video_id: str, response: Response):
    cookies = cloudfront_signer.create_cookies(
        resource=f"https://cdn.example.com/video/{video_id}/*",
        expires_at=calculate_expiration(),
    )

    for name, value in cookies.items():
        response.set_cookie(
            key=name,
            value=value,
            secure=True,
            httponly=True,
            samesite="lax",
            path="/",
        )

    return {"authorized": True}
```

In production, the endpoint must perform application-level authorization before issuing the cookies.

## CORS Is Not the Same as Cookie Delivery

A common troubleshooting mistake is assuming that CORS configuration alone determines whether signed cookies work.

These are separate concerns:

```text
CORS
└── Controls browser cross-origin request permissions

Cookies
└── Controls credential storage and transmission
```

For cross-origin browser requests, frontend code may also need:

```javascript
fetch("https://cdn.example.com/private/file.mp4", {
    credentials: "include",
});
```

The server-side response and browser cookie policy must also permit the intended credential flow.

Do not diagnose a signed-cookie problem as "just CORS" without checking whether the cookie is actually being sent.

## Credentialed Fetch Requests

If JavaScript is explicitly making cross-origin requests using cookies, the request may need credentials enabled:

```javascript
const response = await fetch(
    "https://cdn.example.com/private/file.mp4",
    {
        credentials: "include",
    },
);
```

However, not every browser request requires explicit JavaScript credential configuration. For example, browser-managed resource requests can behave differently from `fetch()` or XHR.

The actual request type must therefore be considered during troubleshooting.

## CloudFront Key Trust

CloudFront must trust the public key corresponding to the private key used by the application.

The trust chain is:

```text
Backend
  │
  │ private key
  ▼
Signature
  │
  ▼
Signed cookie
  │
  ▼
CloudFront
  │
  │ trusted public key
  ▼
Signature validation
```

If the application signs with a private key that does not correspond to the configured trusted public key, CloudFront rejects the request.

## Key Group Configuration

Modern CloudFront deployments commonly use key groups to manage trusted public keys.

Inspect the distribution configuration:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID"
```

Then verify that the relevant cache behavior has the intended trusted key configuration.

Do not assume that because a public key exists in AWS, CloudFront automatically trusts it for every distribution and behavior.

The key must be correctly associated with the relevant trust configuration.

## Key Identifier Problems

The `CloudFront-Key-Pair-Id` cookie identifies the public key CloudFront should use for validation.

Common problems include:

- Typographical error
- Old key identifier
- Key removed during rotation
- Wrong environment
- Wrong distribution
- Application using the wrong secret
- Deployment partially completed

A useful diagnostic comparison is:

```text
Application configuration
        │
        ▼
Key identifier
        │
        ▼
CloudFront trusted public key
        │
        ▼
Key group / cache behavior
```

All three layers must align.

## Expired Cookies

CloudFront signed cookies are time-bound.

For a canned policy:

```text
CloudFront-Expires
```

defines the expiration.

For a custom policy, the expiration is contained in the policy.

An expired cookie can produce a 403 even when:

- The key is correct
- The cookie exists
- The browser sends it
- The signature is correctly generated

Check expiration before changing the signing implementation.

## Clock Problems

Expiration and policy evaluation depend on timestamps.

Common mistakes include:

- Milliseconds instead of seconds
- Incorrect epoch conversion
- Application clock problems
- Incorrect timezone handling
- Expiration calculated too far in the past
- Expiration generated from stale cached configuration

Use UTC-aware application code:

```python
from datetime import datetime, timedelta, timezone


def expires_in(minutes: int = 10) -> int:
    return int(
        (datetime.now(timezone.utc) + timedelta(minutes=minutes)).timestamp()
    )
```

The important property is a correct Unix timestamp, not the local timezone displayed by the operating system.

## Custom Policy Problems

Custom policies can introduce failures beyond simple expiration.

A policy may include:

- Resource
- Expiration
- Not-before timestamp
- IP restrictions

For example:

```json
{
  "Statement": [
    {
      "Resource": "https://cdn.example.com/video/course-123/*",
      "Condition": {
        "DateLessThan": {
          "AWS:EpochTime": 1787200000
        }
      }
    }
  ]
}
```

The exact policy representation and signing format must follow the CloudFront signing requirements.

Troubleshoot every condition independently.

## Resource Mismatch

Suppose the policy authorizes:

```text
https://cdn.example.com/video/course-123/*
```

but the client requests:

```text
https://cdn.example.com/video/course-456/segment.ts
```

The cookie can be cryptographically valid while still failing authorization because the resource does not match the policy.

Always compare:

```text
Requested URL
vs.
Policy Resource
```

## IP Restrictions

Custom policies can restrict access by source IP.

This can cause unexpected failures when clients operate behind:

- Mobile networks
- Corporate proxies
- NAT gateways
- VPNs
- Changing residential IPs

For example:

```text
Policy expects:
203.0.113.10

Client request arrives from:
203.0.113.25
```

The policy may fail even though the user has not changed accounts.

IP-bound policies should therefore be used only when the operational characteristics of the client network are well understood.

## Cookie and CDN Domain Architecture

A common production architecture is:

```text
Application
https://app.example.com
        │
        │ Set-Cookie
        ▼
Browser
        │
        │ Cookie sent to CDN
        ▼
CloudFront
https://cdn.example.com
        │
        ▼
Private origin
```

The cookie domain must be compatible with the hostname receiving the protected request.

A cookie issued for:

```text
app.example.com
```

does not automatically become a cookie for:

```text
cdn.example.com
```

This distinction causes many real-world failures.

## Subdomain Considerations

If the application needs to authorize:

```text
app.example.com
```

and then access:

```text
cdn.example.com
```

the cookie may need an appropriate parent-domain scope such as:

```text
Domain=.example.com
```

But broad domain cookies increase the set of hosts that receive the credential.

Use the narrowest practical scope.

If the architecture allows the backend to set cookies specifically for the CloudFront hostname, that can reduce credential exposure.

## Browser Storage vs Network Transmission

When troubleshooting, check both:

```text
Application response
       ↓
Set-Cookie present?
       ↓
Browser storage
       ↓
Cookie attributes accepted?
       ↓
Matching CloudFront request
       ↓
Cookie header present?
```

This is more reliable than checking only application logs.

A backend log showing:

```text
CloudFront cookies generated successfully
```

does not prove the browser accepted or transmitted them.

## Inspect Set-Cookie Headers

Use browser developer tools or an HTTP client to inspect the authorization response.

For example:

```bash
curl -i \
  "https://api.example.com/videos/123/authorize"
```

Look for:

```http
Set-Cookie: CloudFront-Key-Pair-Id=...
Set-Cookie: CloudFront-Signature=...
Set-Cookie: CloudFront-Policy=...
```

When testing authenticated endpoints, use an appropriate authentication mechanism and avoid exposing credentials in shell history.

## Inspect the CloudFront Request

After authorization, inspect the actual protected request.

You want to establish:

```text
GET https://cdn.example.com/video/123/segment.ts
Cookie: CloudFront-...
```

If the cookie header is missing:

```text
Do not debug the signature yet.
```

The problem is upstream of CloudFront signature validation.

## Common Cookie Attribute Failures

| Problem | Effect |
|---|---|
| Wrong `Domain` | Browser does not send cookie to CloudFront |
| Wrong `Path` | Cookie omitted for protected resource |
| Missing `Secure` | Weak or inconsistent HTTPS behavior |
| Incorrect `SameSite` | Cross-site requests may omit cookie |
| Expired cookie | Browser may remove or stop sending it |
| Browser blocking cookie | CloudFront receives no authorization |
| Incorrect credentials mode | Cross-origin fetch may omit credentials |

## CORS Configuration

If the frontend is hosted separately from the API or CDN, verify CORS behavior where relevant.

A common architecture is:

```text
Browser
 ├── app.example.com
 ├── api.example.com
 └── cdn.example.com
```

CORS and cookie handling should be designed together for browser-based applications.

Avoid:

```http
Access-Control-Allow-Origin: *
```

when credentials are required.

Credentialed cross-origin access requires a more restrictive origin configuration.

## Do Not Put Signed Cookie Values in URLs

Signed cookies exist partly to keep authorization information out of URLs.

Avoid converting:

```text
CloudFront-Policy
CloudFront-Signature
CloudFront-Key-Pair-Id
```

into query parameters merely because troubleshooting is difficult.

This changes the authorization mechanism and can expose sensitive authorization material through:

- Browser history
- Access logs
- Proxy logs
- Referrer headers
- Monitoring systems

Keep the credentials in cookies when using the signed-cookie model.

## Cookie Lifetime Strategy

Use the shortest lifetime that fits the user experience.

For example:

```text
Authenticate
    ↓
Issue 10-minute CloudFront authorization
    ↓
Client downloads content
    ↓
Refresh authorization if necessary
```

For long-running media sessions, design renewal explicitly rather than issuing days-long credentials.

Short lifetimes reduce the impact of leaked cookies.

## Cookie Rotation and Refresh

Applications with long-lived sessions may need to issue new signed cookies before the old ones expire.

A practical architecture is:

```text
Application session
       │
       ▼
CloudFront authorization cookie
       │
       ├── Valid → Continue
       │
       └── Near expiration
               │
               ▼
        Refresh authorization
```

Do not refresh credentials on every CDN request.

The application should refresh authorization at a controlled interval.

## Key Rotation

Signing key rotation requires coordination between the backend and CloudFront.

A safe process is:

```text
Create new CloudFront public key
        ↓
Associate with trusted key group
        ↓
Deploy new private key to backend
        ↓
Generate cookies using new key
        ↓
Observe production traffic
        ↓
Wait for old cookies to expire
        ↓
Remove old key
```

Do not delete the old trusted key before all relevant old cookies have expired.

Otherwise, users with otherwise-valid cookies may suddenly receive `403` responses.

## Environment Mismatch

Production incidents can occur when:

```text
Production backend
      │
      ▼
Staging CloudFront key
```

or:

```text
Production application
      │
      ▼
Staging CDN hostname
```

Environment-specific configuration should include:

- CloudFront hostname
- Distribution identifier
- Key identifier
- Private signing key
- Cookie domain
- Resource paths

These values should be validated during deployment.

## Docker Configuration

If the signing service runs in Docker, verify that the expected key identifier and private key are available without exposing the secret.

For example:

```bash
docker exec "$CONTAINER_ID" \
  sh -c 'test -n "$CLOUDFRONT_KEY_ID" && echo "CloudFront key configured"'
```

Avoid dumping the entire environment:

```bash
docker exec "$CONTAINER_ID" env
```

because production environment variables may contain sensitive credentials.

## Kubernetes Configuration

For Kubernetes deployments, verify references to Secrets rather than printing secret values.

Inspect the deployment:

```bash
kubectl get deployment backend -o yaml
```

Look for:

- Secret references
- Environment variable names
- Mounted secret paths
- Container configuration

Also verify that the running pod received the expected configuration after a rotation.

## CloudFront Distribution Configuration

Retrieve the distribution configuration:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID"
```

Review the cache behavior responsible for the protected resource.

Confirm that:

- Signed-cookie enforcement is configured where intended
- The trusted key configuration is correct
- The requested path matches the expected behavior
- The distribution is the expected environment

## Response Header Inspection

Inspect the CloudFront response:

```bash
curl -sS -D - \
  -o /dev/null \
  "https://cdn.example.com/private/file.mp4"
```

Useful diagnostic headers can include:

```text
X-Cache
X-Amz-Cf-Id
X-Amz-Cf-Pop
Via
```

These headers do not by themselves explain every signed-cookie failure, but they can help establish that the request reached CloudFront and identify useful request metadata for further investigation.

## CloudFront vs Origin Failure

A signed-cookie problem should first be separated from an origin problem.

```text
Browser
   │
   │ Cookies
   ▼
CloudFront
   │
   ├── Cookie invalid → 403
   │
   └── Cookie valid
          │
          ▼
       Origin
          │
          ├── Success
          └── Origin error
```

If CloudFront accepts the signed cookie but the origin returns an error, debugging the cookie further is unlikely to solve the problem.

## Troubleshooting Decision Tree

```mermaid
flowchart TD
    A[Protected CloudFront request returns 403] --> B{Cookies stored?}

    B -->|No| C[Inspect Set-Cookie response]
    B -->|Yes| D{Cookies sent to CloudFront?}

    C --> E{Domain / Path / Secure / SameSite correct?}
    E -->|No| F[Fix cookie attributes]
    E -->|Yes| G[Inspect browser cookie policy]

    D -->|No| H[Inspect cookie scope and browser request]
    D -->|Yes| I{Cookie expired?}

    I -->|Yes| J[Generate fresh cookies]
    I -->|No| K{Correct key identifier?}

    K -->|No| L[Fix signing configuration]
    K -->|Yes| M{Trusted public key configured?}

    M -->|No| N[Fix key group / trust configuration]
    M -->|Yes| O{Policy matches resource?}

    O -->|No| P[Fix policy]
    O -->|Yes| Q{WAF or origin failure?}

    Q -->|WAF| R[Inspect WAF logs]
    Q -->|Origin| S[Inspect origin authorization]
    Q -->|CloudFront| T[Inspect signing implementation]
```

## Production Troubleshooting Workflow

### Capture the Failing Request

Record:

- CloudFront hostname
- Resource path
- HTTP status
- Request timestamp
- CloudFront request ID when available
- Browser/client type
- Environment

Do not record complete signed-cookie values.

### Verify Cookie Generation

Confirm the backend generated all required values.

For a custom policy:

```text
CloudFront-Policy
CloudFront-Signature
CloudFront-Key-Pair-Id
```

For a canned policy:

```text
CloudFront-Expires
CloudFront-Signature
CloudFront-Key-Pair-Id
```

### Verify Browser Storage

Confirm the browser accepted the cookies.

Check:

- Domain
- Path
- Secure
- SameSite
- Expiration

### Verify Cookie Transmission

Inspect the actual CloudFront request.

Confirm that the required cookies are present.

### Verify Expiration

Check whether the policy or expiration timestamp is still valid.

### Verify Key Configuration

Confirm:

```text
Private key
     ↕
Public key
     ↕
Key identifier
     ↕
Trusted key group
     ↕
CloudFront behavior
```

### Verify Resource Policy

Compare the requested resource with the policy resource.

### Verify Client IP Conditions

If the policy uses an IP restriction, verify that the request source satisfies the policy.

### Check WAF and Origin

Only after cookie validation is established should you investigate downstream authorization.

## Logging Strategy

Do not log signed-cookie values.

Instead log metadata such as:

```json
{
  "event": "cloudfront_cookie_issued",
  "user_id": "internal-user-reference",
  "resource": "/video/course-123/*",
  "key_id": "K123456789",
  "expires_at": 1787200000
}
```

Avoid:

```json
{
  "CloudFront-Signature": "<actual-secret-value>"
}
```

The signature is authorization material and should be treated as sensitive.

## Observability

Useful metrics include:

| Metric | Purpose |
|---|---|
| Cookie generation failures | Detect backend signing issues |
| CloudFront 403 rate | Detect authorization failures |
| Protected request success rate | Measure actual delivery |
| Cookie refresh failures | Detect session authorization problems |
| Key rotation failures | Detect deployment/configuration issues |
| WAF block rate | Separate security filtering from signing failures |
| Origin error rate | Separate downstream failures |

A useful dashboard separates:

```text
Authorization generation
        ↓
Cookie delivery
        ↓
CloudFront authorization
        ↓
Origin delivery
```

This prevents teams from treating all `403` responses as the same problem.

## Security Considerations

Signed cookies should be treated as bearer credentials.

Important controls include:

- Keep private keys server-side.
- Use HTTPS.
- Use `Secure`.
- Prefer `HttpOnly` when JavaScript does not need cookie access.
- Use an appropriate `SameSite` policy.
- Restrict cookie domain and path.
- Use short expiration periods.
- Avoid logging cookie values.
- Avoid exposing cookies through unnecessary subdomains.
- Rotate signing keys.
- Authorize users before issuing cookies.
- Restrict policy resources as much as practical.

The frontend should receive authorization cookies, not the private signing key.

## Common Mistakes

### Generating Valid Cookies but Using the Wrong Domain

The backend may correctly generate the signature, but the browser does not send the cookie to CloudFront.

**Fix:** verify the cookie's `Domain` and the CloudFront hostname.

### Checking Browser Storage but Not the Request

A cookie can exist in browser storage while being excluded from a particular request.

**Fix:** inspect the actual request headers.

### Incorrect `Path`

The cookie may be scoped to:

```text
Path=/app/
```

while the protected resource is:

```text
/video/
```

**Fix:** use a path compatible with the protected resource.

### Incorrect `SameSite`

Cross-site browser requests can cause cookies to be omitted.

**Fix:** understand the application's site/origin relationship and configure `SameSite` accordingly.

### Forgetting `Secure`

Production protected resources should use HTTPS.

**Fix:** enforce HTTPS and use `Secure`.

### Logging Signed Cookies

This creates a credential leakage risk.

**Fix:** log metadata and redact cookie values.

### Sending the Private Key to the Browser

This completely compromises the signing model.

**Fix:** sign exclusively on trusted backend infrastructure.

### Using Long-Lived Cookies

Long-lived bearer credentials increase the impact of leakage.

**Fix:** use short-lived cookies and controlled renewal.

### Rotating Keys Immediately

Removing the old public key before old cookies expire can cause widespread 403 responses.

**Fix:** use an overlap period.

### Treating CORS as the Entire Problem

CORS, cookie policy, and CloudFront signature validation are different layers.

**Fix:** inspect browser cookie storage and the actual network request.

## Production Best Practices

- Authenticate and authorize users before issuing signed cookies.
- Keep private signing keys exclusively on backend infrastructure.
- Use managed secret storage for private keys.
- Scope cookies to the narrowest practical domain and path.
- Use HTTPS and `Secure`.
- Use `HttpOnly` unless browser JavaScript genuinely needs the cookie.
- Configure `SameSite` deliberately.
- Use short-lived authorization cookies.
- Refresh cookies in a controlled manner for long-running sessions.
- Keep staging and production signing configuration separate.
- Rotate keys with an overlap period.
- Never log complete cookie values.
- Monitor CloudFront 403 rates independently from origin errors.
- Verify browser transmission before debugging cryptographic signatures.
- Keep private S3 objects private and use CloudFront as the controlled delivery layer.

## Interview Perspective

A strong answer to:

> "CloudFront signed cookies are returning 403. How would you troubleshoot them?"

should start with the browser-to-CloudFront request path:

1. Confirm the backend generated all required cookie values.
2. Confirm the browser accepted the `Set-Cookie` headers.
3. Check cookie `Domain`, `Path`, `Secure`, `SameSite`, and expiration.
4. Inspect the actual CloudFront request and confirm the cookies were sent.
5. Check whether the policy or expiration has expired.
6. Verify the `CloudFront-Key-Pair-Id`.
7. Verify the corresponding public key and trusted key group.
8. Verify that the requested resource matches the signed policy.
9. Check any IP restrictions in custom policies.
10. Confirm the request is reaching the expected CloudFront distribution.
11. Check WAF independently.
12. Check origin authorization only after CloudFront authorization is established.
13. Generate a fresh short-lived cookie set and retest.
14. If a key rotation occurred, verify that old cookies still have a valid trusted key.

The senior-level distinction is:

> **For signed cookies, validate the entire credential delivery path—not just the signature. A correctly generated cookie that never reaches CloudFront is operationally equivalent to having no authorization credential at all.**

## Key Takeaways

- **Signed cookies authorize multiple CloudFront resources efficiently:** they are especially useful for protected media, downloads, and resource collections.
- **A valid generated cookie is not enough:** verify browser storage, cookie attributes, and the actual `Cookie` header sent to CloudFront.
- **The trust chain must align:** key identifier, private key, public key, trusted key group, policy, resource, and expiration must all be compatible.
- **Treat signed cookies as bearer credentials:** use HTTPS, short lifetimes, restricted scope, secure cookie attributes, and never log credential values.
- **Troubleshoot in layers:** cookie generation → browser delivery → CloudFront authorization → WAF → origin, rather than treating every `403` as a cryptographic failure.