# 09- Security Best Practices

## Overview

CloudFront security should be designed as a layered system rather than as a single configuration setting. A production distribution commonly combines:

- HTTPS and TLS enforcement
- Private origins
- Origin Access Control (OAC)
- AWS WAF
- AWS Shield
- Signed URLs or signed cookies
- Geo restrictions where required
- Least-privilege IAM policies
- Security headers
- Controlled cache behavior
- Logging and monitoring
- Key and credential rotation

The central security principle is:

> **Do not trust the CDN merely because it is in front of the application. Explicitly control who can access the distribution, what they can access, how the origin can be reached, and how requests are inspected.**

A typical production architecture looks like:

```mermaid
flowchart LR
    Client[Client]
    DNS[Route 53 / DNS]
    CF[CloudFront]
    WAF[AWS WAF]
    Shield[AWS Shield]
    ALB[Application Load Balancer]
    OAC[Origin Access Control]
    S3[Private S3 Origin]
    App[Django / FastAPI]
    DB[(PostgreSQL)]

    Client --> DNS
    DNS --> CF
    Shield -. DDoS protection .-> CF
    CF --> WAF
    WAF --> CF
    CF --> OAC
    OAC --> S3
    CF --> ALB
    ALB --> App
    App --> DB
```

The exact components depend on the workload. A static private-content distribution may use CloudFront + WAF + OAC + S3, while a backend API may use CloudFront + WAF + ALB + Django/FastAPI.

## Security Model

CloudFront sits between the client and the origin, so security controls exist at multiple boundaries.

```text
Internet
   │
   ▼
CloudFront
   │
   ├── TLS
   ├── AWS Shield
   ├── AWS WAF
   ├── Signed URLs/Cookies
   ├── Geo Restrictions
   ├── Cache Behavior Controls
   │
   ▼
Origin
   │
   ├── OAC for S3
   ├── ALB security controls
   ├── Application authentication
   └── Application authorization
```

Each layer addresses a different problem.

| Layer | Primary responsibility |
|---|---|
| TLS | Encrypt traffic in transit |
| Shield | DDoS protection |
| WAF | HTTP request inspection and filtering |
| Signed URLs/Cookies | Private content authorization |
| Geo restrictions | Country-level delivery restrictions |
| OAC | Protect S3 origins from direct access |
| ALB | Application traffic entry point |
| Application | Business authentication and authorization |
| IAM | AWS resource permissions |
| Logging | Detection and investigation |

A common mistake is assuming that one layer makes the others unnecessary.

For example:

```text
HTTPS ≠ authentication
WAF ≠ authorization
Signed URL ≠ application session
OAC ≠ viewer authorization
Shield ≠ application security
```

## Security Boundaries

A useful way to reason about CloudFront security is to identify each trust boundary.

### Viewer → CloudFront

Controls include:

- HTTPS
- WAF
- Signed URLs
- Signed cookies
- Geo restrictions
- Rate-based rules

### CloudFront → Origin

Controls include:

- OAC for S3
- HTTPS to custom origins
- Origin authentication
- Security groups and network controls
- Origin request policies

### Application → Data Layer

Controls include:

- IAM
- Database authentication
- Application authorization
- Secrets management
- Network segmentation

This separation prevents security responsibilities from becoming concentrated in a single component.

## HTTPS and TLS

All production CloudFront distributions should normally enforce HTTPS for viewer traffic.

A secure request path is:

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

There are two independent encryption decisions:

1. Viewer-to-CloudFront encryption
2. CloudFront-to-origin encryption

Using HTTPS only on the viewer side does not automatically guarantee encrypted communication between CloudFront and a custom origin.

For sensitive workloads, use HTTPS throughout the request path.

### Viewer Protocol Policy

For public web applications, a common configuration is:

```text
HTTP request
    │
    ▼
CloudFront
    │
    └──► Redirect to HTTPS

HTTPS request
    │
    ▼
CloudFront
    │
    ▼
Origin
```

Avoid allowing plaintext HTTP for sensitive applications.

### TLS Version

Use modern TLS policies appropriate for the client population and application requirements.

Do not retain obsolete protocol versions simply because they improve compatibility with clients that are no longer supported.

The security decision should balance:

- Supported client population
- Compliance requirements
- Security requirements
- Operational compatibility

## Origin Encryption

For custom origins such as an ALB or application server, configure HTTPS where appropriate.

```text
Client
  │ HTTPS
  ▼
CloudFront
  │ HTTPS
  ▼
ALB
  │
  ▼
Django / FastAPI
```

This prevents the CloudFront-to-origin segment from becoming an unencrypted portion of an otherwise secure architecture.

## Origin Access Control

For S3 origins, use Origin Access Control to prevent users from bypassing CloudFront and accessing S3 directly.

The desired architecture is:

```text
Client
  │
  ▼
CloudFront
  │
  │ OAC-authenticated request
  ▼
Private S3
```

Not:

```text
Client
  │
  ├──► CloudFront
  │
  └──► Public S3
```

The second architecture creates a bypass around CloudFront security controls.

### OAC Security Principle

The S3 bucket should remain private.

CloudFront should be the intended path to the objects.

This allows you to combine:

```text
Viewer security
+
CDN security
+
Origin security
```

rather than relying on public S3 permissions.

## AWS WAF

AWS WAF provides application-layer request inspection.

Typical controls include:

- IP-based blocking
- Rate-based rules
- Managed rule groups
- URI restrictions
- Header inspection
- Query-string inspection
- Geographic conditions
- Allow/block rules

A typical request path is:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
AWS WAF
  │
  ├── Block
  │
  └── Allow
       │
       ▼
    Origin
```

WAF should be treated as a request-filtering layer, not as a replacement for application authorization.

## AWS Managed Rules

Managed rule groups can provide protection against common classes of malicious requests.

They are useful because maintaining a comprehensive HTTP attack-detection ruleset manually is difficult.

However, managed rules can produce false positives.

Production deployment should therefore include:

- Monitoring
- Testing
- Rule tuning
- Scope-down statements where appropriate
- Careful rollout

Do not blindly enable every rule and assume the application will continue to function correctly.

## WAF Rule Ordering

Rule evaluation order matters.

A simplified model is:

```text
Request
  │
  ▼
Rule 1
  │
  ├── Block
  │
  └── Continue
       │
       ▼
     Rule 2
       │
       ├── Allow
       │
       └── Continue
```

Security rules should be designed intentionally.

For example:

```text
Known malicious traffic
        ↓
Block

Trusted internal integration
        ↓
Allow

Managed security rules
        ↓
Inspect

Default
        ↓
Continue to application
```

The actual WAF evaluation behavior depends on rule actions and Web ACL configuration, so production changes should be validated against AWS WAF semantics rather than relying on a simplified mental model.

## Rate-Based Protection

Rate-based rules are useful for limiting abusive request patterns.

Example:

```text
Single client/IP
       │
       ├── 100 requests
       ├── 200 requests
       ├── 500 requests
       ▼
Rate threshold
       │
       ▼
Temporary mitigation
```

They are particularly useful for:

- Login endpoints
- Search endpoints
- Expensive API endpoints
- Download endpoints
- Scraping protection
- Abuse mitigation

However, IP-based rate limiting can be inaccurate when many legitimate users share an IP through NAT, proxies, or corporate networks.

Rate limiting should therefore be designed around the application's traffic model.

## WAF and API Security

For a Django or FastAPI API:

```text
Client
  │
  │ HTTPS
  ▼
CloudFront
  │
  ▼
WAF
  │
  ├── Malicious request → Block
  │
  └── Valid request
          │
          ▼
         ALB
          │
          ▼
    Django / FastAPI
          │
          ▼
       PostgreSQL
```

WAF can reduce malicious traffic reaching the application, but application-level authorization remains necessary.

For example:

```text
WAF:
"Is this request structurally suspicious?"

Application:
"Is this authenticated user allowed to access this order?"
```

Those are different questions.

## Signed URLs and Signed Cookies

For private content, use signed URLs or signed cookies when appropriate.

```text
Backend
  │
  ├── Authenticate
  ├── Authorize
  └── Generate credential
            │
            ▼
        CloudFront
            │
            ├── Valid → Content
            └── Invalid → 403
```

Signed credentials should be:

- Short-lived
- Generated only after authorization
- Protected from logging
- Signed with securely stored private keys
- Rotated appropriately

Treat signed URLs and cookies as bearer credentials during their validity period.

## Credential Leakage

A signed URL may appear in:

- Browser history
- Application logs
- Proxy logs
- Monitoring systems
- Analytics
- Referrer information
- Screenshots
- Support tickets

Therefore avoid logging complete signed URLs.

Bad:

```text
download_url=https://cdn.example.com/private/file.pdf?Expires=...&Signature=...
```

Better:

```text
resource_id=file_123
authorization=issued
expires_at=2026-08-19T18:30:00Z
request_id=req_123
```

## Key Management

Private signing keys are high-value secrets.

They should not be stored in:

- Git
- Frontend code
- Docker images
- Public S3
- Configuration committed to source control
- Application logs

Use an appropriate secret-management mechanism and restrict access to the service that actually performs signing.

A mature architecture is:

```text
Django / FastAPI
       │
       ▼
Signing Service
       │
       ▼
Secret / Key Storage
       │
       ▼
Private Signing Key
```

## Key Rotation

CloudFront signing keys should be rotated through a controlled process.

A safe pattern is:

```text
Old public key trusted
        │
        ▼
Add new public key
        │
        ▼
Deploy new private key
        │
        ▼
Issue new credentials
        │
        ▼
Wait for old credentials to expire
        │
        ▼
Remove old public key
```

Do not remove the old public key before existing credentials have had an opportunity to expire.

## Geo Restrictions

CloudFront geographic restrictions can prevent distribution to users in selected countries.

They are useful for requirements such as:

- Licensing restrictions
- Regional content availability
- Contractual distribution limitations
- Regulatory requirements

However, country-level restriction is not equivalent to precise user geolocation.

Treat geo restrictions as a coarse distribution control.

For business rules requiring finer authorization, application-level controls may still be required.

## Security Headers

Applications should send appropriate security-related HTTP headers.

Common examples include:

```http
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
Content-Security-Policy: default-src 'self'
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

The exact policy depends on the application.

Do not blindly copy a Content Security Policy into production without validating all application dependencies.

For example, a Django frontend may legitimately depend on:

- API endpoints
- Static asset hosts
- Image CDNs
- Analytics providers
- Authentication providers

The CSP must reflect the actual dependency graph.

## Cache Security

Caching is a security concern because cached content can be served to subsequent requests.

A dangerous design is:

```text
Authenticated response
        │
        ▼
Shared CloudFront cache
        │
        ▼
Another user
```

The cache policy and cache key must be designed so that personalized or authorization-sensitive responses are not unintentionally shared.

### Public vs Private Content

Separate cache behaviors when possible:

```text
/public/*
    │
    └── Public caching

/private/*
    │
    └── Authorization-aware behavior

/api/*
    │
    └── Application/API behavior
```

Do not mix public and user-specific responses in the same caching model without carefully controlling the cache key and response behavior.

## Authorization Headers and Caching

For APIs, authorization headers can be part of request processing, but simply forwarding an authorization header does not automatically mean responses are safely isolated in every caching configuration.

Before caching authenticated API responses, verify:

- Cache key configuration
- Origin request policy
- Cache policy
- Authorization semantics
- Response headers
- Application behavior

A safe default for highly personalized APIs is often to avoid caching responses unless the caching model is explicitly designed.

## Cache-Control

Use response caching directives intentionally.

For private or user-specific responses:

```http
Cache-Control: private, no-store
```

For immutable public assets:

```http
Cache-Control: public, max-age=31536000, immutable
```

The correct value depends on whether the resource can safely be shared.

For example:

```text
/static/app.8f42a1.js
```

can often use aggressive caching because the filename is content-versioned.

A personalized endpoint such as:

```text
/api/me
```

should be treated very differently.

## Query Strings

Query strings can influence caching behavior.

Security-sensitive query parameters should not accidentally create unintended cache sharing.

Example:

```text
/download?id=123&token=abc
```

If the token affects authorization, caching must be designed carefully.

Do not assume that adding a security-sensitive query parameter automatically makes a response safe.

For private-content authorization, prefer CloudFront's supported signed URL/cookie mechanisms rather than inventing custom cache-key authorization schemes.

## Cookies and Caching

Cookies can contain:

- Sessions
- Authorization state
- Preferences
- Personalization information

Forwarding all cookies to the origin can:

- Reduce cache efficiency
- Increase origin requests
- Increase complexity
- Create accidental cache-sharing risks

Only forward cookies that the origin actually requires.

Avoid the blanket configuration:

```text
Forward every cookie
```

unless there is a clear architectural reason.

## Origin Request Policies

Origin request policies determine what information CloudFront forwards to the origin.

Potential request components include:

- Headers
- Cookies
- Query strings

The security principle is:

> Forward only what the origin needs.

This reduces:

- Information exposure
- Origin complexity
- Cache fragmentation
- Accidental dependency on client-controlled headers

## Host Header Security

Do not blindly trust arbitrary client-controlled host-related information at the application layer.

CloudFront, ALB, and the application should have clearly defined hostname expectations.

For multi-domain deployments, explicitly model:

```text
Host
  │
  ▼
CloudFront behavior
  │
  ▼
Origin
  │
  ▼
Application routing
```

Application-level host validation may also be important for Django configurations such as `ALLOWED_HOSTS`.

## HTTP Method Restrictions

If a CloudFront behavior only needs:

```text
GET
HEAD
```

do not unnecessarily allow:

```text
POST
PUT
PATCH
DELETE
OPTIONS
```

Restricting methods reduces attack surface and prevents unintended operations.

For APIs, configure supported methods according to the API contract.

For static content:

```text
GET + HEAD
```

is often sufficient.

## Origin Protection for Custom Origins

S3 has OAC, but custom origins require different protection strategies.

For an ALB-backed application:

```text
Internet
   │
   ▼
CloudFront
   │
   ▼
ALB
   │
   ▼
Application
```

The goal should be to make the origin difficult to bypass or to ensure that direct origin access does not provide a privileged path around CloudFront controls.

Possible controls include:

- Origin authentication
- Secret headers where appropriate
- ALB security controls
- Network architecture
- Application-level validation
- Separate origin hostnames
- AWS-supported private connectivity patterns where applicable

Do not treat a custom origin's public DNS name as a secret.

## Avoiding Origin Bypass

A common failure mode is:

```text
User
  │
  ├──► CloudFront ──► Protected application
  │
  └──► origin.example.com ──► Same application
```

If the second path bypasses:

- WAF
- CloudFront authentication
- Geo restrictions
- Rate controls
- Edge security

the architecture has a security gap.

Review the origin as an independently reachable attack surface.

## DDoS Protection

CloudFront benefits from AWS Shield protections at the AWS edge.

The security architecture should still consider:

```text
DDoS
 │
 ▼
Shield
 │
 ▼
CloudFront
 │
 ▼
WAF
 │
 ▼
Application
```

Shield and WAF have different responsibilities.

| Service | Primary role |
|---|---|
| AWS Shield | DDoS protection |
| AWS WAF | Application-layer request filtering |
| CloudFront | Global content delivery and edge termination |
| Application | Business-level authorization |

Do not use WAF rules as a replacement for DDoS architecture.

## Rate Limiting vs DDoS Protection

Application rate limiting and DDoS protection are related but different.

Application rate limiting answers:

> "Should this client be allowed to make more requests?"

DDoS protection answers:

> "How do we absorb or mitigate large-scale malicious traffic?"

Use both where appropriate.

## Logging and Detection

Enable appropriate CloudFront logging and monitoring for the workload.

Useful signals include:

- 4xx rate
- 5xx rate
- WAF blocked requests
- Request volume
- Origin latency
- Cache hit ratio
- Geographic request distribution
- Unexpected traffic patterns
- Authentication failures
- Security-rule matches

A useful operational dashboard might contain:

```text
CloudFront
├── Requests
├── 4xx
├── 5xx
├── Cache Hit Ratio
└── Origin Latency

WAF
├── Allowed
├── Blocked
├── Counted
└── Top Rules

Application
├── 401
├── 403
├── 429
├── 500
└── Latency
```

## Security Monitoring

A mature security setup should correlate events across layers.

Example:

```text
CloudFront request
      │
      ▼
WAF decision
      │
      ▼
ALB request
      │
      ▼
Application log
      │
      ▼
Security investigation
```

Use consistent identifiers such as request IDs where possible.

This makes it easier to answer:

> "Why did this request receive a 403?"

instead of looking at each system independently.

## Alerting

Not every security event should generate an immediate incident.

Useful alert candidates include:

- Sudden increase in blocked requests
- Large unexpected traffic spike
- Abnormal 4xx increase
- Abnormal 5xx increase
- WAF rule suddenly blocking legitimate traffic
- Signing-service failures
- Unexpected origin traffic
- Key-management failures
- Large traffic from unexpected regions

Alerts should be based on baselines where possible rather than arbitrary thresholds.

## Least Privilege

CloudFront-related IAM permissions should follow least privilege.

Avoid broad permissions such as:

```json
{
  "Effect": "Allow",
  "Action": "*",
  "Resource": "*"
}
```

Instead, CI/CD and operations roles should receive only the permissions required to:

- Deploy distributions
- Update WAF associations
- Manage key groups
- Update origins
- Inspect distributions
- Read required configuration

Separate deployment privileges from application runtime privileges.

## CI/CD Security

CloudFront configuration should be managed as code where practical.

Examples include:

- Terraform
- AWS CloudFormation
- AWS CDK

A deployment pipeline can follow:

```text
Git Push
   │
   ▼
CI
   │
   ├── Validate configuration
   ├── Security checks
   ├── Policy checks
   └── Tests
        │
        ▼
     Deploy
        │
        ▼
   CloudFront
```

Do not make undocumented production security changes manually unless there is a justified operational emergency.

## Configuration Drift

Manual changes can create differences between:

```text
Infrastructure as Code
        │
        ≠
AWS Console
```

This becomes dangerous for security settings.

Examples:

- WAF rule changed manually
- OAC removed
- HTTPS policy changed
- Cache behavior changed
- Public access accidentally enabled
- Origin changed

Use drift detection and regular configuration review where supported by your infrastructure tooling.

## Secrets Management

CloudFront configuration itself may contain identifiers and public keys that are not necessarily secrets.

However, private signing keys and application credentials are sensitive.

Use:

- AWS Secrets Manager
- AWS Systems Manager Parameter Store
- Appropriate external secret managers

Do not confuse:

```text
Public key
```

with:

```text
Private signing key
```

The public key can be distributed to CloudFront for verification; the private key must remain protected.

## Backend Application Security

CloudFront cannot compensate for insecure backend authorization.

For Django:

```text
Authentication
      │
      ▼
Permission checks
      │
      ▼
Object-level authorization
      │
      ▼
Response
```

For FastAPI:

```text
Authentication dependency
      │
      ▼
Authorization dependency
      │
      ▼
Endpoint
```

CloudFront protects the delivery edge.

The application still owns business authorization.

## CORS

CORS is a browser security mechanism, not an authentication mechanism.

For APIs behind CloudFront, configure CORS deliberately.

Do not use:

```http
Access-Control-Allow-Origin: *
```

for sensitive credentialed browser applications unless the security model explicitly supports it.

If cookies or credentials are required, origin-specific CORS configuration is usually more appropriate.

## Security Headers and CORS

These controls solve different problems:

| Control | Purpose |
|---|---|
| CORS | Controls browser cross-origin access |
| CSP | Controls browser resource execution/loading |
| HSTS | Encourages HTTPS-only browser communication |
| X-Content-Type-Options | Prevents MIME sniffing |
| Referrer-Policy | Controls referrer information |
| Permissions-Policy | Restricts browser capabilities |

Do not treat one as a replacement for another.

## Content Security Policy

CSP is particularly important for web applications delivered through CloudFront.

A restrictive starting point might look like:

```http
Content-Security-Policy:
  default-src 'self';
  object-src 'none';
  base-uri 'self';
  frame-ancestors 'none';
```

Production applications often require additional directives.

Validate CSP in a non-production environment before enforcing it aggressively.

## Clickjacking Protection

For applications that should never be embedded in frames, use:

```http
Content-Security-Policy: frame-ancestors 'none';
```

This helps prevent clickjacking attacks.

If the application legitimately needs embedding, explicitly define trusted ancestors instead of disabling the protection globally.

## Compression and Security

Compression improves performance but can interact with security-sensitive content in certain attack scenarios.

Be cautious when compressing responses that combine:

- Secret information
- User-controlled content
- Predictable response structures

For most ordinary static assets, compression is straightforward. For highly sensitive dynamic responses, evaluate the complete response model rather than enabling every optimization indiscriminately.

## Cache Poisoning Considerations

Cache poisoning occurs when an attacker causes CloudFront to cache a response that should not be reused by other requests.

Risk factors include:

- Uncontrolled headers
- Unnecessary query parameters
- Host-based behavior
- Untrusted origin response variation
- Incorrect cache-key design

A secure cache design should explicitly identify:

```text
What changes the response?
        │
        ▼
What belongs in the cache key?
        │
        ▼
What must be forwarded to the origin?
```

Do not blindly include every request attribute.

## Web Application Firewall and Cache Poisoning

WAF can reduce some malicious request patterns, but correct cache architecture remains the primary control.

Do not expect:

```text
WAF enabled
```

to make an unsafe cache policy safe.

The application and CloudFront cache configuration must correctly model response variation.

## Sensitive Data

Do not cache sensitive personalized responses merely because CloudFront can cache them.

Examples include:

- Account information
- Payment details
- Private messages
- User-specific dashboards
- Authorization responses
- Security tokens

A useful rule is:

> If sharing the cached response with another user would be a security incident, do not use a shared-cache design without explicit isolation.

## PCI, HIPAA, and Compliance

CloudFront security configuration may form part of a compliance architecture, but enabling CloudFront security features does not automatically make an application compliant.

Compliance requirements depend on:

- Data classification
- Logging
- Encryption
- Access control
- Retention
- Key management
- Application architecture
- Organizational processes

Treat CloudFront as one component of the control framework.

## Disaster Recovery

CloudFront is globally distributed, but application disaster recovery still matters.

Consider:

```text
CloudFront
    │
    ├── Primary origin
    │
    └── Failover origin
```

For critical workloads, evaluate:

- Origin failover
- Multi-region origins
- S3 replication
- Database recovery
- DNS strategy
- Secret recovery
- Signing-key recovery
- Infrastructure recreation

Security configuration must be recoverable as well.

## Security Deployment Checklist

Before production deployment, verify:

### Viewer Security

- [ ] HTTPS is enforced.
- [ ] Modern TLS policy is configured.
- [ ] HTTP methods are restricted.
- [ ] Security headers are configured where appropriate.
- [ ] CORS is explicitly configured.

### CloudFront

- [ ] Public and private cache behaviors are separated.
- [ ] Cache keys are reviewed.
- [ ] Query strings are intentionally handled.
- [ ] Cookies are intentionally handled.
- [ ] Origin request policies are minimized.
- [ ] Signed URLs/cookies are configured where required.

### WAF

- [ ] Web ACL is associated with the distribution.
- [ ] Managed rules are evaluated.
- [ ] Rate-based protection is configured where required.
- [ ] False positives are monitored.
- [ ] Rules are tested before enforcement.

### Origin

- [ ] S3 origins are private.
- [ ] OAC is configured for S3 where applicable.
- [ ] Custom origins use appropriate authentication and network controls.
- [ ] Direct origin bypass has been evaluated.
- [ ] HTTPS to the origin is enabled where appropriate.

### Credentials

- [ ] Private signing keys are protected.
- [ ] Secrets are not stored in source control.
- [ ] Signing credentials have appropriate expiration.
- [ ] Key rotation is documented and tested.

### Operations

- [ ] CloudFront logging is configured as required.
- [ ] WAF logs are available.
- [ ] Security metrics are monitored.
- [ ] Alerts are configured.
- [ ] Infrastructure is managed as code.
- [ ] Configuration drift is reviewed.

## Common Security Mistakes

| Mistake | Why it is dangerous | Better approach |
|---|---|---|
| Public S3 bucket behind CloudFront | CloudFront can be bypassed | Keep S3 private and use OAC |
| HTTP allowed | Traffic can be intercepted or downgraded | Redirect or require HTTPS |
| WAF treated as authorization | WAF does not understand business permissions | Authorize in the application |
| Long-lived signed URLs | Large credential abuse window | Use short practical expiration |
| Private signing key in frontend | Anyone can create valid credentials | Keep it server-side |
| All cookies forwarded | Poor caching and possible data leakage | Forward only required cookies |
| All query strings cached | Cache fragmentation or unsafe sharing | Explicitly design cache keys |
| Origin publicly exposed | Security controls can be bypassed | Protect origin access |
| No key rotation | Long-lived compromise impact | Rotate keys with overlap |
| Complete signed URLs logged | Logs become credential stores | Log metadata, not credentials |
| Broad IAM permissions | Increased blast radius | Use least privilege |
| Blindly enabling WAF rules | Legitimate traffic can be blocked | Monitor and tune |
| Caching personalized data | Cross-user data leakage | Avoid shared caching or isolate responses |
| Assuming HTTPS means secure application | Encryption does not provide authorization | Layer TLS with authentication and authorization |

## Production Security Review

A senior-level CloudFront review should ask questions at every layer.

### Viewer

- Is all sensitive traffic encrypted?
- Are clients authorized before receiving private content?
- Are signed credentials short-lived?
- Are HTTP methods restricted?

### Edge

- Is AWS WAF enabled where required?
- Are rate-based rules appropriate?
- Are geo restrictions required?
- Are cache behaviors correctly ordered?

### Cache

- Can a response belonging to one user be served to another?
- Are query strings handled correctly?
- Are cookies handled correctly?
- Are authorization-sensitive responses cached?

### Origin

- Can the origin be reached directly?
- Is S3 private?
- Is OAC configured?
- Is CloudFront-to-origin traffic encrypted?

### Application

- Does the backend still perform authorization?
- Are Django/FastAPI permissions correct?
- Are JWT/session credentials protected?
- Are sensitive responses marked appropriately?

### Operations

- Are WAF and CloudFront logs available?
- Are security events monitored?
- Can signing keys be rotated?
- Can the entire security configuration be recreated from code?

## Security Architecture Checklist

A strong default architecture for private backend content is:

```mermaid
flowchart TD
    User[Internet User]
    CF[CloudFront]
    WAF[AWS WAF]
    Signed[Signed URL / Cookie]
    OAC[Origin Access Control]
    S3[Private S3]
    App[Django / FastAPI]
    ALB[ALB]
    DB[(PostgreSQL)]

    User -->|HTTPS| CF
    CF --> WAF
    WAF --> Signed
    Signed --> CF

    CF --> OAC
    OAC --> S3

    CF --> ALB
    ALB --> App
    App --> DB
```

The key security properties are:

```text
Encrypted viewer traffic
        +
Edge request filtering
        +
Content authorization
        +
Private origin
        +
Application authorization
        +
Least privilege
        +
Monitoring
```

No individual control should be expected to provide all of these properties.

## Key Takeaways

- **Treat CloudFront security as defense in depth: combine HTTPS, WAF, Shield, private origins, authorization, least-privilege IAM, and monitoring according to the workload.**
- **Protect the origin independently of viewer security; for S3, keep buckets private and use Origin Access Control so CloudFront cannot be bypassed.**
- **Design caching as a security boundary: never allow personalized or authorization-sensitive responses to become unintentionally shared cache entries.**
- **Treat signed URLs, signed cookies, private keys, sessions, and other authorization material as sensitive credentials with short lifetimes, controlled storage, safe logging, and planned rotation.**
- **Manage CloudFront security through repeatable infrastructure and operational controls, with WAF behavior, origin access, cache policies, logging, alerting, and configuration drift continuously reviewed.**