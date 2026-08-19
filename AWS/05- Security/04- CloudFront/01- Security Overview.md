# 01- Security Overview

## Overview

CloudFront security is best understood as a layered security model spanning the viewer, edge, cache, origin, and application. CloudFront can terminate TLS, enforce viewer access behavior, integrate with AWS WAF, restrict access to private content, and protect origins from unnecessary direct exposure. It does not, however, replace application authentication, authorization, IAM, or secure backend design.

A production CloudFront deployment should establish clear security responsibilities for every layer:

```text
                              Internet
                                  │
                                  │ HTTPS
                                  ▼
                         ┌─────────────────┐
                         │   CloudFront    │
                         │                 │
                         │ TLS termination │
                         │ Cache controls  │
                         │ Access controls │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │    AWS WAF      │
                         │                 │
                         │ Managed rules   │
                         │ Rate limiting   │
                         │ IP / geo rules  │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ Protected       │
                         │ Origin          │
                         └────────┬────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
                   S3            ALB       API Gateway
                                  │
                                  ▼
                         Django / FastAPI
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
                  Redis       PostgreSQL       Kafka
```

The key security principle is **defense in depth**. CloudFront should reduce the attack surface and absorb malicious or unnecessary traffic at the edge, while the origin and application continue enforcing their own security boundaries.

## Security Responsibilities by Layer

| Layer | Primary Responsibility | Typical Controls |
|---|---|---|
| Viewer | Secure client communication | HTTPS, TLS policy |
| CloudFront | Edge request and delivery controls | Behaviors, policies, restrictions |
| AWS WAF | HTTP request inspection | Managed rules, custom rules, rate-based rules |
| Cache | Prevent unintended data sharing | Cache policies, cache keys, TTLs |
| Origin | Protect backend infrastructure | Origin access controls, HTTPS, network controls |
| Application | User identity and permissions | Authentication, authorization, RBAC, ABAC |
| AWS Resources | Infrastructure authorization | IAM, bucket policies, resource policies |
| Operations | Detection and response | Logs, metrics, alarms, CloudTrail |

Security failures frequently occur when responsibility is incorrectly assigned to the wrong layer.

For example, CloudFront can block requests from an IP address, but it should not be responsible for determining whether a user is allowed to delete another user's database record.

## Viewer-to-CloudFront Security

### HTTPS

The viewer connection should normally use HTTPS:

```text
Client
  │
  │ HTTPS
  ▼
CloudFront
```

TLS protects:

- Credentials
- Authorization headers
- Cookies
- Query parameters
- Request bodies
- Response content

For production workloads, HTTP should generally redirect to HTTPS rather than serving application content over plaintext HTTP.

### Viewer Protocol Policy

A typical configuration is conceptually:

```text
HTTP request
     │
     ▼
CloudFront
     │
     └──► HTTPS redirect
              │
              ▼
         HTTPS request
```

This establishes a single secure entry point for the application.

### TLS Policy

The distribution should use an appropriate modern TLS security policy.

The correct policy is a balance between:

- Client compatibility
- Security requirements
- Organizational standards
- Supported protocol versions
- Certificate configuration

Avoid choosing an obsolete TLS configuration simply to support legacy clients unless that compatibility requirement is explicitly justified.

## CloudFront-to-Origin Security

Viewer-side TLS does not automatically imply that the origin connection uses the same security properties.

There are two distinct connections:

```text
Client ───── HTTPS ─────► CloudFront
                              │
                              │ HTTPS
                              ▼
                           Origin
```

The origin connection should use HTTPS where the origin architecture supports it and the workload requires transport encryption.

This is particularly important when the origin handles:

- Authentication
- Personal information
- Payment-related operations
- API credentials
- Internal application data

### Security Principle

Treat the viewer-to-edge and edge-to-origin connections as independent security boundaries.

## Origin Protection

CloudFront does not automatically make an origin inaccessible to the public internet.

Consider:

```text
                    ┌──────────► CloudFront ─────► Origin
Internet ───────────┤
                    └──────────► Direct Origin
```

The second path may bypass:

- CloudFront
- WAF inspection
- Edge rate controls
- CloudFront access policies
- Intended centralized traffic controls

If CloudFront is supposed to be the mandatory public entry point, direct origin access should be explicitly addressed.

A preferred architecture is:

```text
Internet
   │
   ▼
CloudFront
   │
   ▼
Protected Origin
```

The exact protection mechanism depends on whether the origin is S3, an ALB, API Gateway, or another supported origin type.

## S3 Origin Security

Private S3 content should not normally be exposed by making the entire bucket publicly readable.

A stronger model is:

```text
Viewer
   │
   ▼
CloudFront
   │
   │ Authorized origin access
   ▼
Private S3 Bucket
```

CloudFront can retrieve objects using the appropriate origin access mechanism while the bucket remains private to ordinary public clients.

### Production Rules

- Keep sensitive S3 buckets private.
- Grant only the required origin access.
- Avoid public bucket policies merely because CloudFront needs access.
- Verify that direct S3 object access is not unintentionally available.
- Review bucket policies whenever the CloudFront architecture changes.

## Application Origin Security

A common backend architecture is:

```text
Internet
    │
    ▼
CloudFront
    │
    ▼
AWS WAF
    │
    ▼
ALB
    │
    ▼
Django / FastAPI
```

The application still needs its own security controls.

For example:

```python
def authorize_request(user, resource):
    if not user.is_authenticated:
        raise PermissionError("Authentication required")

    if resource.owner_id != user.id and not user.is_staff:
        raise PermissionError("Insufficient permissions")
```

The important architectural distinction is:

- CloudFront controls edge traffic.
- WAF filters HTTP requests.
- The application determines user identity and business authorization.

## AWS WAF

AWS WAF can be associated with CloudFront to inspect HTTP requests before they reach the origin.

```text
Client
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

Typical WAF controls include:

- AWS Managed Rules
- IP address rules
- IP reputation controls
- Rate-based rules
- Geographic restrictions
- URI matching
- Header matching
- Query-string matching
- Custom application-specific rules

### When to Use WAF

WAF is particularly valuable for:

- Public APIs
- Authentication endpoints
- Internet-facing applications
- High-volume applications
- Applications exposed to untrusted clients
- Endpoints vulnerable to automated abuse

### WAF Does Not Replace Application Security

A WAF rule such as:

```text
Block /admin/*
```

does not replace:

```text
Authentication
      │
      ▼
Authorization
      │
      ▼
Business operation
```

A Django or FastAPI application must still validate:

- Authentication credentials
- Access tokens
- Session state
- User identity
- Resource ownership
- Roles
- Permissions
- Business rules

## Rate Limiting

Rate-based WAF rules can reduce abusive traffic before it reaches backend infrastructure.

```text
Client
  │
  ▼
CloudFront
  │
  ▼
WAF Rate-Based Rule
  │
  ├── Excessive traffic ──► Block
  │
  └── Normal traffic ─────► Origin
```

This is useful for:

- Login endpoints
- Password-reset endpoints
- Expensive search operations
- Public APIs
- Resource-intensive operations

However, edge rate limiting is not equivalent to application-level quotas.

A backend may still need:

```text
User quota
Tenant quota
API-key quota
Business-operation quota
```

Redis is commonly useful for application-level counters when distributed rate limiting is required across multiple application instances.

## Cache Security

Caching introduces a major security consideration: **can the response safely be shared?**

A public asset such as:

```text
GET /static/app.91ab42.js
```

can normally be shared among users.

A personalized endpoint such as:

```text
GET /api/profile
Authorization: Bearer <token>
```

is fundamentally different.

If a user-specific response is incorrectly stored in a shared cache, another user could potentially receive it.

### Cache Classification

| Content | Typical Strategy |
|---|---|
| Versioned JavaScript | Aggressive caching |
| Versioned CSS | Aggressive caching |
| Public images | Aggressive caching |
| Public documentation | Aggressive caching |
| Public API response | Controlled caching |
| Authenticated API response | Usually bypass shared cache |
| User profile | Generally not shared-cacheable |
| Administrative API | Generally not shared-cacheable |
| Payment operations | Do not use shared caching |

The correct strategy depends on the response semantics, not merely the URL.

## Cache Key Security

A cache key determines which requests can reuse the same cached response.

Suppose:

```text
GET /products?currency=USD
GET /products?currency=EUR
```

If the response changes based on `currency`, the cache must distinguish those requests.

Similarly, if an API varies by:

```text
X-Tenant-ID
Accept-Language
Cookie
Authorization
```

the cache architecture must account for that variation.

### Critical Rule

> Every request attribute that changes a shared response must either be represented appropriately in the cache key or the response must not be shared through the cache.

This is both a correctness and security requirement.

## Cache Poisoning

Cache poisoning can occur when attacker-controlled request information influences a response that is subsequently stored and served to other clients.

Potential causes include:

- Incorrect cache keys
- Untrusted headers affecting responses
- Unvalidated query parameters
- Host-dependent application behavior
- Incorrect origin request configuration
- Inconsistent cache and application behavior

A production cache design should explicitly answer:

1. What determines the response?
2. Which request attributes affect it?
3. Which attributes belong in the cache key?
4. Which attributes should be forwarded to the origin?
5. Should the response be shared at all?

If those questions cannot be answered clearly, the endpoint probably should not use shared caching until its behavior is understood.

## Query String Security

Query strings can influence both application behavior and cache behavior.

Consider:

```text
/search?q=python
/search?q=django
```

If `q` changes the response, it must be handled as part of the cache design.

Conversely, tracking parameters such as:

```text
?utm_source=google
?utm_campaign=summer
```

may not change the response.

Including every query parameter indiscriminately can create unnecessary cache variants:

```text
More query-string variants
          │
          ▼
Lower cache hit ratio
          │
          ▼
More origin requests
          │
          ▼
Higher origin load
```

Security and performance therefore intersect in cache-key design.

## Headers and Cookies

Headers and cookies require the same analysis.

Potential response-varying inputs include:

```text
Authorization
Cookie
Accept-Language
X-Tenant-ID
X-Feature-Flag
```

A multi-tenant application requires particular caution.

For example:

```text
GET /api/dashboard
X-Tenant-ID: tenant-a
```

must not accidentally reuse a response generated for:

```text
GET /api/dashboard
X-Tenant-ID: tenant-b
```

For highly personalized or tenant-sensitive APIs, bypassing shared caching is often safer than building a complicated cache-key model.

## Cache Policy and Origin Request Policy

These policies serve different purposes.

| Policy | Purpose |
|---|---|
| Cache policy | Defines caching behavior and cache-key inputs |
| Origin request policy | Defines which request values are forwarded to the origin |

A request attribute may need to reach the origin without necessarily being part of the cache key.

This distinction is important when integrating CloudFront with Django or FastAPI APIs.

Do not assume:

> "If CloudFront forwards a value to the origin, that value automatically becomes part of the cache key."

Caching and origin forwarding should be designed independently.

## Signed URLs and Signed Cookies

Signed URLs and signed cookies can restrict access to CloudFront content.

They are useful for controlled distribution of:

- Paid media
- Private downloads
- Subscription content
- Temporary documents
- Restricted assets

Conceptually:

```text
Client
  │
  │ Signed URL / Cookie
  ▼
CloudFront
  │
  ├── Valid ───► Cache / Origin
  │
  └── Invalid ─► Deny
```

### Advantages

- Access can expire automatically.
- Authorization can happen at the edge.
- Private content can remain behind CloudFront.
- Application traffic can be reduced for suitable content.

### Limitations

Signed access does not replace complex application authorization.

For example:

```text
User → Tenant → Resource → Permission
```

may require application-level authorization rather than simply checking whether a signed URL is valid.

## Security Headers

CloudFront can participate in delivering security-related response headers.

Common browser security headers include:

| Header | Purpose |
|---|---|
| `Strict-Transport-Security` | Enforces HTTPS behavior in compatible browsers |
| `Content-Security-Policy` | Restricts permitted resource and script sources |
| `X-Content-Type-Options` | Prevents MIME-type sniffing |
| `Referrer-Policy` | Controls referrer information |
| `Permissions-Policy` | Restricts browser capabilities |

Do not copy a generic security-header configuration without understanding the application.

For example, an API-only service may have different requirements from a browser-rendered frontend.

## CORS Security

CORS controls browser access between origins. It should be treated as a browser security policy, not as backend authorization.

For example:

```text
Frontend
https://app.example.com

API
https://api.example.com
```

The API may intentionally allow requests from the frontend origin.

Avoid unnecessarily broad policies such as:

```http
Access-Control-Allow-Origin: *
```

for sensitive applications, particularly when credentials are involved.

CORS behavior should be consistent across:

- CloudFront
- Origin
- Application
- Browser client

## Authentication and Authorization

CloudFront may carry authentication information to the origin, but application authorization remains a backend responsibility.

A typical request path is:

```mermaid
sequenceDiagram
    participant C as Client
    participant CF as CloudFront
    participant W as AWS WAF
    participant O as Origin
    participant A as Django/FastAPI

    C->>CF: HTTPS request
    CF->>W: Inspect request
    W-->>CF: Allow
    CF->>O: Forward request
    O->>A: Process request
    A->>A: Authenticate user
    A->>A: Authorize operation
    A-->>O: Response
    O-->>CF: Response
    CF-->>C: HTTPS response
```

The application should remain the authoritative component for decisions such as:

```text
Can this user modify this resource?
Can this tenant access this object?
Can this role perform this operation?
```

## Origin Authentication

Viewer authentication and origin authentication are different concerns.

### Viewer Authentication

```text
Who is the user?
```

Typical mechanisms:

- JWT
- Session cookies
- OAuth/OIDC
- API keys
- Application authentication systems

### Origin Access

```text
Is this request allowed to access the origin through the intended infrastructure path?
```

Typical mechanisms vary by origin:

- S3 origin access controls
- Origin authentication patterns
- Network-level controls
- Resource policies
- Application-level validation

Keeping these concepts separate prevents CloudFront configuration from becoming a substitute for application security.

## Django and FastAPI Architecture

A secure backend architecture may look like:

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
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
                 Django                      FastAPI
                    │                           │
                    └─────────────┬─────────────┘
                                  │
                       ┌──────────┼──────────┐
                       ▼          ▼          ▼
                     Redis    PostgreSQL    Kafka
```

Responsibilities should remain explicit:

| Component | Responsibility |
|---|---|
| CloudFront | Edge delivery and edge request handling |
| WAF | HTTP threat filtering and rate controls |
| ALB | Load distribution |
| Django/FastAPI | Authentication, authorization, business logic |
| Redis | Application cache and ephemeral distributed state |
| PostgreSQL | Persistent data |
| Kafka | Event distribution |

Avoid placing business rules into CloudFront configuration merely because edge request processing is available.

## Network Security

CloudFront should be considered part of the public edge, while backend resources should be protected according to their role.

A common architecture is:

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
Public ALB
   │
   ▼
Private Application Subnets
   │
   ├── Django / FastAPI
   ├── Redis
   └── PostgreSQL
```

The database should not become publicly reachable merely because the API is internet-facing.

A strong network design separates:

- Public edge resources
- Load-balancing layer
- Application layer
- Data layer

## Kubernetes and Containerized Backends

CloudFront can sit in front of applications deployed on Kubernetes or container infrastructure:

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
Load Balancer
   │
   ▼
Kubernetes Ingress
   │
   ▼
Services
   │
   ├── Django
   └── FastAPI
```

Security responsibility remains distributed.

Kubernetes network policies, pod security, service identity, secrets management, and application authorization remain relevant even when CloudFront provides the public edge.

CloudFront should not be treated as a replacement for Kubernetes security controls.

## Security Logging and Monitoring

A secure architecture must be observable.

Monitor:

- CloudFront request metrics
- CloudFront error rates
- Origin error rates
- WAF blocked requests
- WAF allowed requests
- Request volume
- Geographic traffic anomalies
- Cache behavior
- Origin traffic spikes
- Authentication failures
- Authorization failures

Useful operational questions include:

- Did WAF blocks suddenly increase?
- Did origin traffic spike unexpectedly?
- Did cache hit ratio suddenly fall?
- Did a deployment change cache behavior?
- Did a WAF rule start blocking legitimate clients?
- Are unexpected countries or IP ranges generating traffic?
- Did origin errors increase after a CloudFront configuration change?

Security monitoring should correlate edge and application signals.

## Security Testing

CloudFront security should be tested as an integrated system rather than as isolated configuration items.

### Origin Bypass Testing

Verify whether users can access the origin directly when they should not.

### Cache Isolation Testing

Test that:

```text
User A → Response A
User B → Response B
```

cannot become:

```text
User A → Response A
User B → Response A
```

### Authentication Testing

Test:

- Missing credentials
- Invalid credentials
- Expired credentials
- Valid credentials
- Insufficient permissions
- Revoked credentials

### WAF Testing

Verify:

- Malicious requests are blocked.
- Legitimate requests are allowed.
- Rate-based controls behave as intended.
- Managed rules do not introduce unacceptable false positives.

### TLS Testing

Verify:

- HTTP behavior is intentional.
- HTTPS is enforced where required.
- Origin connections use the intended protocol.
- Certificates are valid and correctly associated.

## Production Security Checklist

### Transport

- [ ] HTTPS is enabled for production viewer traffic.
- [ ] HTTP behavior is explicitly configured.
- [ ] CloudFront uses an appropriate TLS security policy.
- [ ] Origin communication uses HTTPS where required.
- [ ] Certificates are managed and monitored.

### Origin

- [ ] Direct origin exposure has been evaluated.
- [ ] Private S3 content is not publicly readable without justification.
- [ ] Origin access mechanisms are correctly configured.
- [ ] Origin access is tested independently of CloudFront.

### WAF

- [ ] AWS WAF is associated where required.
- [ ] Managed rules have been evaluated.
- [ ] Rate-based rules protect abuse-prone endpoints.
- [ ] Custom rules are tested.
- [ ] False positives are monitored.

### Cache

- [ ] Public and private content are explicitly classified.
- [ ] Authenticated responses are not accidentally shared.
- [ ] Cache keys account for response-varying inputs.
- [ ] Sensitive cookies are handled deliberately.
- [ ] Sensitive headers are handled deliberately.
- [ ] Query-string behavior is intentional.
- [ ] Cache poisoning risks have been reviewed.

### Application

- [ ] Authentication remains an application responsibility.
- [ ] Authorization remains an application responsibility.
- [ ] Resource ownership is enforced.
- [ ] Tenant isolation is enforced.
- [ ] Business-level rate limits exist where required.
- [ ] CORS is intentionally configured.

### Monitoring

- [ ] CloudFront metrics are monitored.
- [ ] WAF metrics are monitored.
- [ ] Origin errors are monitored.
- [ ] Security-relevant logs are retained appropriately.
- [ ] Alerts exist for abnormal traffic patterns.
- [ ] Incident investigation can correlate edge and application activity.

## Common Mistakes and Pitfalls

### Treating CloudFront as the Entire Security Layer

**Problem:** The backend trusts CloudFront to enforce all security decisions.

**Why it happens:** CloudFront sits at the public edge and appears to control all incoming traffic.

**Correction:** Keep application authentication and authorization in the application.

### Making the Origin Public Without a Reason

**Problem:** Attackers can bypass CloudFront and WAF.

**Why it happens:** The origin is configured for convenience rather than as a deliberate security boundary.

**Correction:** Explicitly define how origin access is protected and test direct-origin access.

### Caching Personalized Responses

**Problem:** User-specific content can be served to another user.

**Why it happens:** Caching is configured primarily for performance.

**Correction:** Analyze response variation and disable shared caching where isolation cannot be guaranteed.

### Forwarding Every Header and Cookie

**Problem:** Cache efficiency decreases and the behavior becomes difficult to reason about.

**Why it happens:** Forwarding everything appears safer than determining what is required.

**Correction:** Forward only required values and design cache behavior explicitly.

### Assuming WAF Provides Authorization

**Problem:** Edge rules are used to make business-level permission decisions.

**Why it happens:** WAF can inspect request attributes and block requests.

**Correction:** Use WAF for traffic filtering and application code for authorization.

### Using Wildcard CORS

**Problem:** Browser access may become broader than intended.

**Why it happens:** `*` is convenient during development and is copied into production.

**Correction:** Define explicit allowed origins where the application handles sensitive data.

### Ignoring Cache Poisoning

**Problem:** Attacker-controlled input can influence shared cached responses.

**Why it happens:** Cache behavior is treated solely as a performance concern.

**Correction:** Identify every request attribute that influences the response and model cache behavior accordingly.

### Ignoring Observability

**Problem:** Security incidents become difficult to investigate.

**Why it happens:** Logging is deferred until after deployment.

**Correction:** Design logs, metrics, alarms, and retention requirements as part of the initial architecture.

## Security and Performance Trade-Offs

Security controls have operational and performance consequences.

| Design Choice | Security Impact | Performance Impact | Operational Impact |
|---|---|---|---|
| WAF | Stronger edge filtering | Small processing overhead | Rule management required |
| Aggressive caching | Reduces origin exposure | Lower latency | Requires careful invalidation |
| No caching for private APIs | Reduces sharing risk | More origin traffic | Higher backend load |
| Signed URLs | Restricts content access | Low edge overhead | Requires signing lifecycle |
| HTTPS to origin | Encrypts backend traffic | TLS processing | Certificate management |
| Detailed logging | Better investigation | Additional processing/storage | Retention and cost |
| Multi-region origin | Improves resilience | Potential latency improvement | Higher complexity |

The correct design depends on the threat model, data sensitivity, traffic profile, and availability requirements.

## Security Decision Matrix

| Requirement | Recommended CloudFront Control | Backend Control |
|---|---|---|
| Encrypt client traffic | HTTPS/TLS | Application HTTPS awareness |
| Block known malicious traffic | AWS WAF | Application validation |
| Prevent origin bypass | Origin access/network controls | Application validation where appropriate |
| Protect private S3 objects | CloudFront origin access | S3 bucket policy |
| Restrict private downloads | Signed URLs/cookies | Authorization and issuance |
| Protect login endpoint | WAF rate controls | Authentication throttling |
| Protect user data | Avoid unsafe shared caching | Authorization and tenant isolation |
| Prevent tenant data leakage | Correct cache strategy | Tenant authorization |
| Browser access control | CORS | Application CORS policy |
| Browser hardening | Security headers | Application security configuration |
| Detect attacks | CloudFront/WAF logs and metrics | Application logs and alerts |

## Interview Traps

### Does CloudFront Make an API Secure?

No. CloudFront improves the edge security posture, but authentication, authorization, secure coding, IAM, origin protection, and application security remain necessary.

### Does HTTPS Encrypt the Entire Request Path?

Only the individual HTTPS connection being used. Viewer-to-CloudFront and CloudFront-to-origin are separate connections and should be configured independently.

### Can Authenticated APIs Be Cached?

They can be cached only when the caching model safely guarantees response isolation. For many personalized APIs, bypassing shared caching is safer and easier to reason about.

### Does WAF Replace Application Rate Limiting?

No. WAF provides edge-level protection, while applications may need user-, tenant-, API-key-, or business-specific quotas.

### Does CloudFront Automatically Hide the Origin?

No. Origin exposure depends on how the origin and its access controls are configured.

### Does a Private S3 Bucket Automatically Mean CloudFront Is Secure?

No. The CloudFront-to-S3 authorization path must also be configured correctly, and direct access paths should be tested.

## Key Takeaways

- **CloudFront should be treated as one layer in a defense-in-depth security architecture, not as a replacement for application or AWS security controls.**
- **Origin protection and secure cache design are critical because direct-origin access and incorrect cache sharing can bypass intended security boundaries.**
- **AWS WAF is effective for edge-level traffic filtering and rate controls, while authentication, authorization, tenant isolation, and business rules remain backend responsibilities.**
- **HTTPS, origin access controls, cache policies, CORS, signed access, and security headers should be designed according to the workload rather than applied as generic configuration.**
- **Production CloudFront security requires continuous observability and testing across the viewer, edge, WAF, cache, origin, and application layers.**