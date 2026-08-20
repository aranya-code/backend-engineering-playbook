# 04- Security Questions

## Overview

CloudFront security questions typically test whether you understand the CDN as part of the complete application security boundary rather than as a simple caching layer.

A production CloudFront architecture commonly combines:

- TLS termination and HTTPS enforcement.
- AWS WAF for HTTP-layer filtering.
- Origin Access Control (OAC) for private Amazon S3 origins.
- Security controls around custom origins such as Application Load Balancers.
- Cache-policy design to prevent sensitive data leakage.
- Signed URLs or signed cookies for controlled content access.
- Geographic restrictions where required.
- Security headers and response-header policies.
- Logging and monitoring for detection and investigation.
- Least-privilege IAM policies.
- Origin protection so users cannot bypass CloudFront unintentionally.

A useful security model is:

```text
                         Internet
                            │
                            ▼
                    ┌────────────────┐
                    │    Route 53    │
                    └───────┬────────┘
                            │
                            ▼
                    ┌────────────────┐
                    │   CloudFront   │
                    │                │
                    │ TLS / HTTPS    │
                    │ AWS WAF        │
                    │ Cache Policies │
                    │ Access Control │
                    └───────┬────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
        ┌──────────────┐        ┌──────────────┐
        │ Private S3   │        │ ALB / API    │
        │ Origin + OAC │        │ Origin       │
        └──────────────┘        └──────┬───────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │ Django/FastAPI  │
                              │ Microservices   │
                              └─────────────────┘
```

The most important principle is:

> CloudFront security must protect both the viewer-to-CloudFront path and the CloudFront-to-origin path.

---

## HTTPS and TLS

### Why should CloudFront use HTTPS?

HTTPS protects data while it travels between the client and CloudFront.

It provides:

- Encryption.
- Server authentication.
- Integrity protection.
- Protection against network-level interception.

A production application should normally redirect HTTP requests to HTTPS.

```text
HTTP request
    │
    ▼
CloudFront
    │
    └── Redirect to HTTPS
             │
             ▼
        HTTPS request
```

---

### Where does TLS terminate?

CloudFront can terminate the viewer's TLS connection at the CloudFront edge.

The connection can then be established separately from CloudFront to the origin.

Conceptually:

```text
Client
  │
  │ HTTPS
  ▼
CloudFront
  │
  │ HTTPS
  ▼
Origin
```

These are separate connections.

HTTPS between the viewer and CloudFront does not automatically mean the CloudFront-to-origin connection is protected by HTTPS.

---

### Should CloudFront connect to the origin using HTTPS?

**Answer:**

For production systems, HTTPS should generally be used between CloudFront and the origin whenever the origin supports it.

This protects data on the origin-facing network path.

For example:

```text
Browser
   │
   │ HTTPS
   ▼
CloudFront
   │
   │ HTTPS
   ▼
ALB
   │
   ▼
Application
```

For custom origins, verify that the origin's TLS configuration and certificate hostname are correct.

---

### What is the difference between viewer protocol policy and origin protocol policy?

**Answer:**

They control different connections.

| Setting | Controls |
|---|---|
| Viewer protocol policy | Client → CloudFront |
| Origin protocol policy | CloudFront → Origin |

A common production configuration is:

```text
Viewer:
HTTP → HTTPS redirect

Origin:
HTTPS only
```

This protects both sides of the CDN boundary.

---

## AWS WAF

### What is AWS WAF?

**Answer:**

AWS WAF is a web application firewall that can inspect HTTP(S) requests and allow, block, count, or otherwise control requests based on configured rules.

It can be associated with CloudFront distributions.

Typical controls include:

- IP-based rules.
- Rate-based rules.
- Managed rule groups.
- Geographic conditions.
- Header matching.
- URI matching.
- Query-string inspection.
- HTTP method restrictions.
- Custom application-specific rules.

---

### Why put WAF in front of CloudFront?

CloudFront is the public edge entry point, so inspecting malicious traffic before it reaches the origin reduces unnecessary load and attack exposure.

```text
Internet
   │
   ▼
CloudFront
   │
   ▼
AWS WAF
   │
   ├── Block ──► Request rejected
   │
   └── Allow
        │
        ▼
      Origin
```

Depending on the architecture, WAF evaluates requests associated with the protected resource before they reach the application.

---

### What attacks can WAF help mitigate?

WAF can help mitigate or detect application-layer attacks such as:

- SQL injection attempts.
- Cross-site scripting patterns.
- Malicious request patterns.
- Excessive request rates.
- Known bad IP addresses.
- Unexpected request structures.

WAF is not a replacement for secure application code.

For example:

```text
WAF
 ↓
Filters known malicious HTTP traffic

Application
 ↓
Still must validate input
 ↓
Still must enforce authorization
 ↓
Still must use parameterized SQL
```

---

### Does WAF replace authentication?

**Answer:**

No.

WAF controls whether HTTP requests should be allowed through the firewall rules.

Authentication determines who the caller is.

Authorization determines what that caller is allowed to do.

These are different responsibilities.

```text
WAF
 └── Is this request acceptable?

Authentication
 └── Who is the caller?

Authorization
 └── What can the caller access?
```

---

## Origin Access Control

### What is Origin Access Control?

**Answer:**

Origin Access Control (OAC) allows CloudFront to securely access supported origins such as Amazon S3 using AWS authorization mechanisms.

The key architectural goal is:

> Prevent clients from bypassing CloudFront and directly accessing private S3 content.

A typical architecture is:

```text
Internet
   │
   ▼
CloudFront
   │
   │ Signed AWS request
   ▼
Private S3 Bucket
```

The S3 bucket policy can restrict access to requests originating through the intended CloudFront distribution.

---

### Why is OAC important?

Without appropriate origin protection, a public S3 bucket may allow users to access objects directly:

```text
Client ───────────────► S3
   │
   └──────────────► CloudFront
```

This creates two access paths.

With a private bucket and OAC:

```text
Client ──► CloudFront ──► S3
                    ▲
                    │
             Controlled access
```

The CDN becomes the intended public access layer.

---

### What is the recommended approach for private S3 origins?

**Answer:**

Use a private S3 bucket with CloudFront Origin Access Control and an appropriate bucket policy.

Avoid making the bucket public simply because CloudFront needs to retrieve its objects.

The security model should be:

```text
S3
 │
 └── Public access blocked

CloudFront
 │
 └── Authorized to read required objects

Internet
 │
 └── Access through CloudFront
```

---

## OAC vs OAI

### What is Origin Access Identity?

**Answer:**

Origin Access Identity (OAI) is the older mechanism historically used to restrict CloudFront access to private S3 content.

For new architectures, OAC is generally preferred.

| Feature | OAI | OAC |
|---|---|---|
| Older mechanism | Yes | No |
| Designed for S3 origin protection | Yes | Yes |
| Modern recommendation | Generally no | Yes |
| AWS SigV4-based authorization | Limited compared with OAC | Yes |
| New deployments | Prefer OAC | Prefer OAC |

When maintaining an existing system, understand whether it uses OAI before changing the bucket policy.

---

## Preventing Origin Bypass

### Why is direct origin access a security concern?

Suppose:

```text
https://cdn.example.com
```

is protected by CloudFront and WAF.

But the origin is also publicly reachable:

```text
https://api-origin.example.com
```

An attacker can bypass:

- CloudFront caching.
- WAF controls attached to CloudFront.
- Edge-level rate controls.
- CDN-level routing and security policies.

The architecture then has two security paths.

---

### How do you protect a custom origin?

For an ALB-backed application, common strategies include:

- Keep the ALB private when architecture permits.
- Restrict access to trusted network paths.
- Use security groups appropriately.
- Ensure application-level authentication remains enabled.
- Use CloudFront-specific controls where appropriate.
- Avoid relying on an obscure origin hostname as a security mechanism.

For public custom origins, an additional origin-verification mechanism can be used so the application can distinguish legitimate CloudFront-originated traffic from arbitrary direct requests.

---

### Can an attacker simply discover the origin?

Potentially, yes.

Origin hostnames can leak through:

- DNS records.
- Infrastructure configuration.
- Error messages.
- Certificates.
- Application responses.
- Historical configuration.
- Public documentation.

Therefore:

> Hiding the origin hostname is not an access-control mechanism.

The origin must enforce security independently.

---

## Signed URLs

### What is a CloudFront signed URL?

**Answer:**

A signed URL provides temporary authorization to access a protected CloudFront resource.

It can contain policy information and cryptographic authorization allowing CloudFront to determine whether access is permitted.

Typical use cases include:

- Paid downloads.
- Private media.
- Temporary document access.
- Time-limited file downloads.

Conceptually:

```text
Application
   │
   │ Generates signed URL
   ▼
Client
   │
   │ Signed request
   ▼
CloudFront
   │
   ├── Valid signature → Allow
   │
   └── Invalid/expired → Reject
```

---

### Why use signed URLs instead of public URLs?

A public URL provides unrestricted access while the object remains publicly reachable.

A signed URL can restrict access based on conditions such as:

- Expiration time.
- Resource.
- Policy constraints.

This is useful when access should be temporary rather than permanently public.

---

### Are signed URLs authentication?

**Answer:**

Not in the complete application sense.

A signed URL authorizes access to a specific protected CloudFront resource according to its policy.

Your application may still need to authenticate the user before issuing the URL.

For example:

```text
User
  │
  ▼
Django API
  │
  ├── Authenticate user
  ├── Check authorization
  └── Generate signed URL
          │
          ▼
       CloudFront
```

The application decides whether the user should receive the URL.

CloudFront then enforces the signed access policy.

---

## Signed Cookies

### When should signed cookies be used?

**Answer:**

Signed cookies are useful when a client needs access to multiple protected resources rather than one specific URL.

For example:

```text
/video/course-1/segment-001.ts
/video/course-1/segment-002.ts
/video/course-1/segment-003.ts
...
```

A signed URL for every object can become cumbersome.

Signed cookies allow access authorization to be applied across multiple requests.

---

### Signed URL vs signed cookie

| Requirement | Signed URL | Signed Cookie |
|---|---:|---:|
| Single protected object | Excellent | Possible |
| Multiple protected objects | Less convenient | Excellent |
| Shareable direct URL | Yes | No |
| Temporary access | Yes | Yes |
| Typical use | Downloads | Media/content collections |

---

## Security Headers

### What are CloudFront response headers policies?

**Answer:**

A response headers policy allows CloudFront to add or manage HTTP response headers sent to viewers.

Security-related headers can include:

```http
Strict-Transport-Security
Content-Security-Policy
X-Content-Type-Options
Referrer-Policy
```

The exact policy should match the application and frontend architecture.

---

### Why use CloudFront for security headers?

It provides a centralized edge-level mechanism for responses served through the distribution.

This can be useful when:

- Multiple origins need consistent headers.
- Static content comes from S3.
- APIs and frontend assets need standardized browser controls.

However, application-specific security headers may still need to be generated by the application.

---

### What is HSTS?

**Answer:**

HTTP Strict Transport Security (HSTS) tells compatible browsers to use HTTPS for future requests to the protected domain.

A typical header is:

```http
Strict-Transport-Security: max-age=31536000
```

HSTS should be deployed carefully because browsers can enforce HTTPS for the configured duration.

Do not blindly enable aggressive HSTS settings on domains where HTTPS is not consistently supported.

---

## CORS and CloudFront

### Does CloudFront enforce CORS?

**Answer:**

CloudFront can forward relevant request information and return appropriate response headers, but CORS remains fundamentally a browser security policy implemented through HTTP response headers.

For example:

```http
Access-Control-Allow-Origin: https://app.example.com
```

A backend API behind CloudFront still needs correct CORS semantics.

---

### What is a common CORS caching problem?

Suppose the origin returns:

```http
Access-Control-Allow-Origin: https://app-a.example.com
```

for one request and:

```http
Access-Control-Allow-Origin: https://app-b.example.com
```

for another.

If CloudFront caches the response without correctly accounting for the request's `Origin` header, the cached response may contain the wrong CORS header for another viewer.

Therefore, if response headers vary based on a request header, the caching design must account for that variation.

---

## Cache Security

### Why can caching become a security problem?

Caching changes the normal request-to-response relationship.

Normally:

```text
User A → Application → User A response
User B → Application → User B response
```

With shared caching:

```text
User A ──┐
         ├──► Shared Cache
User B ──┘
```

If the cached representation is personalized but the cache key does not isolate the personalization dimension, User B can potentially receive User A's response.

Therefore:

> Cache correctness is part of security correctness.

---

### What responses should generally be treated cautiously?

Examples include:

- Account information.
- Payment information.
- Order history.
- Private documents.
- User dashboards.
- Authentication responses.
- Authorization-sensitive API responses.

Do not make these cacheable simply because the HTTP method is `GET`.

---

## Cache Poisoning

### What is cache poisoning?

**Answer:**

Cache poisoning occurs when an attacker causes CloudFront to cache an unintended representation that is subsequently served to other requests.

A simplified example:

```text
Attacker Request
      │
      ▼
Origin interprets malicious input
      │
      ▼
Malicious response
      │
      ▼
CloudFront caches response
      │
      ▼
Other viewers receive cached response
```

Potential causes include incorrect handling of:

- Host headers.
- Query strings.
- Headers.
- Cookies.
- Redirect behavior.
- Untrusted request input.

The defense is to ensure that every response-affecting request attribute is correctly represented in the caching model.

---

## AWS WAF Rate-Based Protection

### How can WAF help protect an API behind CloudFront from abusive traffic?

**Answer:**

A WAF rate-based rule can limit excessive request rates from clients according to the rule configuration.

Architecture:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
WAF Rate Rule
  │
  ├── Within threshold → Origin
  │
  └── Excessive rate → Block
```

This can reduce:

- Accidental traffic spikes.
- Simple HTTP floods.
- Certain abusive clients.
- Some automated attack patterns.

It is not a complete DDoS strategy.

---

## CloudFront and DDoS Protection

### Does CloudFront protect against DDoS attacks?

**Answer:**

CloudFront is part of AWS's edge infrastructure and can absorb and distribute large volumes of traffic, while AWS Shield provides DDoS protection capabilities.

The exact protection model depends on the architecture and AWS services used.

For application-layer attacks, WAF can provide additional filtering.

A layered architecture is:

```text
Internet
   │
   ▼
AWS edge infrastructure / Shield
   │
   ▼
CloudFront
   │
   ▼
AWS WAF
   │
   ▼
Origin
```

The key interview point is:

> DDoS resilience is a layered architecture, not a single CloudFront configuration switch.

---

## Geo Restrictions

### What are CloudFront geographic restrictions?

**Answer:**

CloudFront can restrict delivery of content based on viewer geographic location.

This can be useful for:

- Licensing restrictions.
- Regulatory requirements.
- Regional content distribution.
- Business availability rules.

However, geographic restriction should not be treated as strong identity or authorization.

IP-based geolocation can be imperfect.

---

### Can geo restriction replace application authorization?

**Answer:**

No.

For example:

```text
Country = India
```

does not establish:

```text
User = Authorized customer
```

Geo restrictions are a coarse access-control layer.

Application authorization remains responsible for user-level permissions.

---

## IAM and CloudFront

### Why does least-privilege IAM matter?

CloudFront deployments often interact with:

- S3.
- ACM.
- WAF.
- CloudWatch.
- Route 53.
- IAM.
- Infrastructure-as-code systems.

Deployment roles should receive only the permissions required to manage the intended resources.

Avoid giving broad administrator permissions to CI/CD pipelines simply because they make deployment easier.

---

### Should an application instance have permission to modify CloudFront?

**Answer:**

Usually no.

The runtime application should generally not need administrative permissions to change CDN configuration.

A better separation is:

```text
CI/CD / Infrastructure Role
        │
        └── Manage CloudFront

Application Runtime Role
        │
        └── Run application
```

This reduces blast radius if the application is compromised.

---

## Secrets and CloudFront

### Should API keys or secrets be embedded in CloudFront configuration?

**Answer:**

Sensitive secrets should not be hard-coded into URLs, frontend assets, or publicly accessible CloudFront configuration.

For backend systems:

- Store secrets in appropriate secret-management systems.
- Keep private credentials server-side.
- Avoid exposing origin credentials to browsers.
- Rotate credentials.
- Use IAM-based authentication where appropriate.

CloudFront is a public delivery layer, so anything delivered to a viewer should be treated as potentially observable by that viewer.

---

## Origin Security for S3

### How should an S3 bucket behind CloudFront be configured?

A strong baseline is:

```text
S3 Bucket
 ├── Block Public Access
 ├── Private bucket
 ├── Bucket policy allows intended CloudFront access
 └── CloudFront OAC
```

The viewer should interact with:

```text
https://cdn.example.com/object
```

rather than:

```text
https://bucket.s3.amazonaws.com/object
```

The latter should not be an unintended public bypass path.

---

## Origin Security for ALB

### How should an ALB-backed CloudFront application be protected?

A common production architecture is:

```text
Internet
   │
   ▼
CloudFront
   │
   ▼
WAF
   │
   ▼
ALB
   │
   ▼
Django / FastAPI
```

Security considerations include:

- HTTPS between CloudFront and ALB.
- Proper security groups.
- Application authentication.
- Application authorization.
- Origin protection.
- Rate limiting.
- WAF rules.
- Logging and alerting.

If the ALB must be internet-facing, do not assume CloudFront alone prevents direct ALB access.

---

## Authentication and Authorization

### Where should authentication happen?

It depends on the architecture.

CloudFront can participate in access-control designs, but application authentication is typically handled by the application or an identity-aware service.

For a Django/FastAPI API:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
WAF
  │
  ▼
ALB
  │
  ▼
Django/FastAPI
  │
  ├── Authenticate
  └── Authorize
```

CloudFront should not be treated as a replacement for application authorization.

---

### Can CloudFront cache authenticated API responses?

**Answer:**

It can be technically possible, but it requires careful design.

The critical questions are:

- Does the response vary by user?
- What identifies the cache variant?
- Is that identity safely represented in the cache key?
- Can a response be shared?
- What happens when authorization changes?
- How are revocations handled?
- What data is sensitive?

For most user-specific APIs, bypassing shared caching is the simpler and safer default.

---

## Security Logging

### Why are CloudFront logs important for security?

Logs can help investigate:

- Suspicious request patterns.
- Unexpected geographic traffic.
- HTTP floods.
- Repeated 4xx/5xx responses.
- Unexpected paths.
- User-agent anomalies.
- Cache behavior.
- WAF activity.

For security investigations, combine CloudFront data with:

- AWS WAF logs.
- Application logs.
- ALB logs.
- S3 access logs where applicable.
- CloudTrail.
- CloudWatch metrics and alarms.

No single log source gives complete visibility.

---

## Security Monitoring

### What should you monitor?

Useful security-related signals include:

| Signal | Why it matters |
|---|---|
| 4xx increase | Possible abuse or client failure |
| 5xx increase | Origin/application failure |
| WAF blocked requests | Attack or abusive traffic |
| Rate-limit events | Traffic spikes or automation |
| Origin request increase | Cache bypass or traffic change |
| Geographic anomalies | Potential abuse |
| Sudden URI changes | Scanning or probing |
| Cache behavior changes | Configuration/security issue |

A production alert should be based on meaningful deviation rather than every isolated blocked request.

---

## Secure CloudFront Request Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant CF as CloudFront
    participant W as AWS WAF
    participant O as Origin

    C->>CF: HTTPS request
    CF->>W: Inspect request
    W-->>CF: Allow / Block

    alt Blocked
        CF-->>C: 403
    else Allowed
        CF->>CF: Cache lookup
        alt Cache hit
            CF-->>C: Cached response
        else Cache miss
            CF->>O: HTTPS origin request
            O-->>CF: Origin response
            CF->>CF: Cache if eligible
            CF-->>C: Response
        end
    end
```

This flow highlights an important security principle: **a cache hit can avoid an origin request entirely**, so origin-side controls do not necessarily inspect every viewer request.

Edge controls such as WAF therefore remain important for requests entering through CloudFront.

---

## Security Best Practices

### Viewer Layer

- Enforce HTTPS.
- Use an appropriate TLS security policy.
- Use a valid ACM certificate for the CloudFront distribution.
- Configure appropriate security headers.
- Avoid exposing sensitive data through frontend assets.

### Edge Layer

- Associate AWS WAF with the distribution where appropriate.
- Use rate-based rules for abuse-sensitive endpoints.
- Use managed rule groups where appropriate.
- Monitor blocked requests.
- Keep WAF rules versioned and reviewed.

### Cache Layer

- Never cache personalized responses accidentally.
- Keep cache keys minimal but complete.
- Account for every response-changing request attribute.
- Avoid unnecessary cookie/header/query-string variation.
- Review CORS-related cache behavior.

### Origin Layer

- Keep S3 buckets private when CloudFront is the intended public access layer.
- Use OAC for private S3 origins.
- Use HTTPS to custom origins.
- Restrict origin access where possible.
- Prevent unintended direct-origin bypass.

### Application Layer

- Continue enforcing authentication.
- Continue enforcing authorization.
- Validate input.
- Use parameterized database queries.
- Protect sensitive endpoints independently of CDN configuration.

### Operations Layer

- Enable appropriate logging.
- Monitor WAF and CloudFront metrics.
- Review CloudTrail changes.
- Use least-privilege deployment roles.
- Audit CloudFront policy changes through CI/CD.

---

## Common Security Mistakes

| Mistake | Risk | Better approach |
|---|---|---|
| Public S3 bucket behind CloudFront | Origin bypass | Private S3 + OAC |
| HTTP-only origin connection | Data exposure | HTTPS to origin |
| Cache authenticated responses blindly | Data leakage | Avoid shared caching or design isolation explicitly |
| Include too few cache-key dimensions | Incorrect response sharing | Include response-affecting attributes |
| Include every request attribute | Cache fragmentation | Use minimum sufficient variation |
| Assume WAF handles authorization | Broken access control | Keep application authorization |
| Expose origin as a security bypass | WAF/CDN bypass | Protect origin independently |
| Hard-code secrets | Credential exposure | Use IAM/secrets management |
| Give CI/CD administrator access | Large blast radius | Least-privilege deployment roles |
| Treat geo restriction as authorization | Weak access control | Use application-level authorization |
| Trust hidden origin hostname | Easily bypassed security | Enforce origin access controls |
| Ignore CORS variation | Incorrect cached responses | Account for response-varying origin headers |

---

## Interview Traps

### "CloudFront is a security boundary, so the origin does not need security."

**Incorrect.**

The origin must still enforce appropriate access controls.

### "OAC makes the S3 bucket public."

**Incorrect.**

OAC is used to authorize CloudFront access to a private S3 origin.

### "WAF authenticates users."

**Incorrect.**

WAF filters HTTP requests; authentication establishes identity.

### "HTTPS from the browser to CloudFront encrypts the entire path."

**Incomplete.**

The CloudFront-to-origin connection is separate and should also use HTTPS when appropriate.

### "A signed URL means the user is authenticated."

**Incorrect.**

A signed URL controls access to a protected CloudFront resource. The application may still need to authenticate and authorize the user before issuing it.

### "A hidden ALB hostname prevents direct-origin attacks."

**Incorrect.**

Security through obscurity is not sufficient. The origin must enforce appropriate access controls.

### "A high CloudFront cache hit ratio means the application is secure."

**Incorrect.**

An incorrectly designed cache key can produce a high hit ratio while leaking or incorrectly sharing data.

---

## Security Architecture Checklist

Before deploying a CloudFront distribution, verify:

| Area | Check |
|---|---|
| HTTPS | Viewer HTTPS enforced |
| TLS | Appropriate security policy configured |
| Certificate | Valid ACM certificate configured |
| WAF | Appropriate rules attached |
| Rate limiting | Sensitive/public APIs evaluated for rate controls |
| S3 | Public access blocked where appropriate |
| OAC | Configured for private S3 origins |
| Custom origin | HTTPS enabled |
| Origin bypass | Direct access reviewed and controlled |
| Cache | Personalized responses protected |
| Cache key | Response-affecting attributes included |
| Cookies | Sensitive cookies handled correctly |
| Headers | Security-sensitive headers reviewed |
| CORS | Origin-varying behavior correctly cached |
| Signed access | Signed URLs/cookies used where required |
| IAM | Least privilege enforced |
| Secrets | No credentials exposed through CDN content |
| Logging | Security-relevant logs enabled |
| Monitoring | WAF and CloudFront anomalies monitored |
| Change control | Configuration managed through reviewed deployment processes |

## Key Takeaways

- **Protect both sides of CloudFront: secure the viewer-to-edge path and the CloudFront-to-origin path.**
- **Use WAF for HTTP-layer filtering, but keep authentication and authorization in the appropriate application or identity layer.**
- **Use private S3 origins with Origin Access Control and prevent unintended direct-origin access.**
- **Treat cache-key design as a security concern because incorrect cache variation can expose personalized or sensitive responses.**
- **Use layered security: TLS, WAF, origin protection, least-privilege IAM, secure caching, application authorization, logging, and monitoring.**