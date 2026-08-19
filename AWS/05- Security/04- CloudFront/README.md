# README

## Overview

This directory contains the security architecture and operational guidance for Amazon CloudFront.

The documents progress from foundational security controls to production-level authorization, origin protection, traffic filtering, and operational hardening. The emphasis is on understanding CloudFront as a security boundary rather than treating it only as a content-delivery layer.

The material covers:

- TLS and HTTPS
- DDoS protection with AWS Shield
- Request filtering with AWS WAF
- Origin Access Control
- Geographic restrictions
- Field-level encryption
- Signed URLs and signed cookies
- Cache and origin security
- Security hardening and operational best practices

## Documentation Structure

```text
05- Security/
└── 04- CloudFront/
    ├── 01- Security Overview.md
    ├── 02- HTTPS and TLS.md
    ├── 03- AWS Shield and DDoS Protection.md
    ├── 04- AWS WAF and Request Filtering.md
    ├── 05- Origin Access Control.md
    ├── 06- Geo Restrictions.md
    ├── 07- Field-Level Encryption.md
    ├── 08- Signed URLs and Signed Cookies.md
    ├── 09- Security Best Practices.md
    └── README.md
```

## Quick Navigation

| Document | Focus |
|---|---|
| [01- Security Overview](./01-%20Security%20Overview.md) | CloudFront security model, security boundaries, defense in depth, and the major security controls |
| [02- HTTPS and TLS](./02-%20HTTPS%20and%20TLS.md) | Viewer HTTPS, TLS policies, certificates, and CloudFront-to-origin encryption |
| [03- AWS Shield and DDoS Protection](./03-%20AWS%20Shield%20and%20DDoS%20Protection.md) | DDoS protection, Shield, traffic absorption, and resilient edge architecture |
| [04- AWS WAF and Request Filtering](./04-%20AWS%20WAF%20and%20Request%20Filtering.md) | Web ACLs, managed rules, rate limiting, request inspection, and blocking strategies |
| [05- Origin Access Control](./05-%20Origin%20Access%20Control.md) | Protecting S3 origins and preventing direct origin access through OAC |
| [06- Geo Restrictions](./06-%20Geo%20Restrictions.md) | Country-level content restrictions and geographic access control |
| [07- Field-Level Encryption](./07-%20Field-Level%20Encryption.md) | Protecting sensitive request fields as traffic passes through CloudFront |
| [08- Signed URLs and Signed Cookies](./08-%20Signed%20URLs%20and%20Signed%20Cookies.md) | Private content authorization, temporary access, and signing workflows |
| [09- Security Best Practices](./09-%20Security%20Best%20Practices.md) | Production hardening, cache security, IAM, monitoring, origin protection, and security review |

## Recommended Reading Order

The recommended sequence follows the security lifecycle of a CloudFront request:

```mermaid
flowchart LR
    A[Security Overview]
    B[HTTPS and TLS]
    C[Shield and DDoS]
    D[WAF and Request Filtering]
    E[Origin Access Control]
    F[Geo Restrictions]
    G[Field-Level Encryption]
    H[Signed URLs and Cookies]
    I[Security Best Practices]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
```

### Recommended progression

1. **Security Overview** — Establish the CloudFront security model and understand the role of each control.
2. **HTTPS and TLS** — Secure viewer and origin communication.
3. **AWS Shield and DDoS Protection** — Understand edge-level availability and DDoS protection.
4. **AWS WAF and Request Filtering** — Control malicious and abusive HTTP traffic.
5. **Origin Access Control** — Prevent direct access to protected S3 origins.
6. **Geo Restrictions** — Apply coarse geographic access policies.
7. **Field-Level Encryption** — Protect sensitive request fields beyond transport encryption.
8. **Signed URLs and Signed Cookies** — Implement controlled access to private content.
9. **Security Best Practices** — Consolidate the controls into production architecture and operational practices.

## Security Architecture

A typical secure CloudFront deployment can be modeled as multiple security layers:

```text
                         Internet
                            │
                            ▼
                    ┌───────────────┐
                    │   CloudFront  │
                    │               │
                    │ HTTPS / TLS   │
                    │ AWS Shield    │
                    │ AWS WAF       │
                    │ Geo Controls  │
                    │ Signed Access │
                    └───────┬───────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
        ┌───────────────┐       ┌───────────────┐
        │ Private S3    │       │ Application    │
        │ Origin        │       │ Origin         │
        │               │       │               │
        │ OAC           │       │ ALB / Nginx   │
        └───────────────┘       │ Django/FastAPI│
                                └───────┬───────┘
                                        │
                                        ▼
                                  ┌────────────┐
                                  │ PostgreSQL │
                                  └────────────┘
```

The layers have different responsibilities:

| Security layer | Responsibility |
|---|---|
| HTTPS/TLS | Encrypt traffic in transit |
| AWS Shield | DDoS protection |
| AWS WAF | HTTP request inspection and filtering |
| Geo restrictions | Country-level access restrictions |
| Signed URLs/cookies | Private content authorization |
| Field-level encryption | Protect selected sensitive request fields |
| OAC | Protect S3 origins from direct access |
| Application authorization | Enforce business permissions |
| IAM | Control AWS resource access |
| Logging and monitoring | Detect and investigate security events |

No individual control replaces the others.

For example:

```text
HTTPS
  ≠ Authentication

WAF
  ≠ Business Authorization

OAC
  ≠ Viewer Authorization

Shield
  ≠ Application Security
```

## Core Security Principles

### Defense in Depth

Use multiple independent controls so that failure or misconfiguration of one layer does not expose the entire system.

```text
TLS
 +
Shield
 +
WAF
 +
Private Origin
 +
Application Authorization
 +
Least-Privilege IAM
 +
Monitoring
```

### Least Privilege

AWS identities, CI/CD roles, applications, and origin integrations should receive only the permissions they require.

Avoid broad permissions such as:

```json
{
  "Effect": "Allow",
  "Action": "*",
  "Resource": "*"
}
```

### Minimize the Attack Surface

Only expose functionality that is required.

Examples:

- Restrict HTTP methods.
- Keep S3 buckets private.
- Forward only required headers and cookies.
- Avoid unnecessary origin exposure.
- Use separate cache behaviors for materially different security requirements.
- Do not expose private signing keys.

### Protect the Origin

CloudFront security controls are ineffective if an attacker can simply bypass CloudFront and reach the origin directly.

A production review should always ask:

> Can the origin be accessed independently of CloudFront?

If the answer is yes, determine whether that access is intentional and whether it bypasses important security controls.

## CloudFront Security Decision Matrix

| Requirement | Primary CloudFront/AWS control |
|---|---|
| Encrypt viewer traffic | HTTPS / TLS |
| Encrypt origin traffic | HTTPS to origin |
| Mitigate DDoS attacks | AWS Shield |
| Filter malicious HTTP requests | AWS WAF |
| Restrict country access | Geo restrictions |
| Protect S3 origin | Origin Access Control |
| Restrict private content | Signed URLs / signed cookies |
| Protect sensitive request fields | Field-level encryption |
| Prevent cache-related data exposure | Correct cache policy and cache key |
| Detect attacks | CloudFront/WAF logging and monitoring |
| Restrict AWS administration | IAM least privilege |

## Backend Engineering Considerations

CloudFront should be integrated into the backend architecture deliberately.

For a Django or FastAPI application:

```text
Client
  │
  │ HTTPS
  ▼
CloudFront
  │
  ├── AWS WAF
  ├── AWS Shield
  └── Cache / Edge Processing
          │
          ▼
         ALB
          │
          ▼
   Django / FastAPI
          │
          ├── Redis
          ├── Celery
          └── PostgreSQL
```

CloudFront should handle edge-level concerns while the application remains responsible for business-level concerns.

For example:

```text
CloudFront/WAF:
"Is this request malicious or structurally invalid?"

Application:
"Is this authenticated user allowed to update order 123?"
```

These responsibilities should not be mixed.

## Cache Security

Caching is an important security boundary.

A public asset can usually be aggressively cached:

```text
/static/app.8f42a1.js
```

A personalized API response requires substantially more care:

```text
/api/me
/api/orders
/api/profile
```

If sharing a cached response between users would expose private information, the response should not use an unsafe shared-cache design.

Review:

- Cache policy
- Cache key
- Query strings
- Cookies
- Authorization headers
- Origin request policy
- Response `Cache-Control`
- Personalized content

A useful design principle is:

> Cache only what can safely be shared.

## Private Content

For protected downloads or media, a common architecture is:

```text
User
  │
  ▼
Backend
  │
  ├── Authenticate
  ├── Authorize
  └── Generate temporary access
          │
          ▼
      CloudFront
          │
          ▼
      Private Origin
```

Signed URLs and signed cookies should be treated as temporary bearer credentials.

Avoid:

- Excessively long expiration periods
- Logging complete signed URLs
- Exposing private signing keys
- Generating access before authorization
- Reusing credentials unnecessarily

## Origin Security

For S3:

```text
CloudFront
    │
    │ OAC
    ▼
Private S3
```

For custom application origins:

```text
CloudFront
    │
    ▼
ALB
    │
    ▼
Django / FastAPI
```

The origin should not become an uncontrolled bypass around CloudFront's security controls.

## Monitoring and Operations

A production CloudFront security setup should be observable.

Useful signals include:

- Request volume
- 4xx responses
- 5xx responses
- WAF blocked requests
- WAF rule matches
- Origin latency
- Cache hit ratio
- Geographic traffic distribution
- Unexpected origin traffic
- Authentication failures
- Rate-limit events

A useful operational view correlates:

```text
CloudFront
    │
    ▼
WAF
    │
    ▼
ALB
    │
    ▼
Application
```

This makes incident investigation considerably easier.

## Infrastructure as Code

CloudFront security configuration should be managed through repeatable deployment processes where practical.

Common approaches include:

- Terraform
- AWS CloudFormation
- AWS CDK

Security-sensitive configuration should not exist only as undocumented console changes.

Track changes to:

- Distribution configuration
- Cache behaviors
- Origin configuration
- OAC
- WAF Web ACLs
- TLS configuration
- Key groups
- Geo restrictions
- Logging configuration

## Production Security Checklist

### Viewer Security

- [ ] HTTPS is enforced.
- [ ] TLS configuration is appropriate for the supported clients.
- [ ] HTTP methods are restricted.
- [ ] Security headers are reviewed.
- [ ] CORS is explicitly configured where required.

### Edge Security

- [ ] AWS WAF is associated where required.
- [ ] AWS Shield protections are understood.
- [ ] Rate-based controls are configured where appropriate.
- [ ] Geo restrictions are applied where required.
- [ ] Private-content authorization is implemented where required.

### Origin Security

- [ ] S3 origins are private.
- [ ] OAC is configured for S3 where applicable.
- [ ] Custom origins have appropriate protection.
- [ ] Direct origin access has been evaluated.
- [ ] Origin traffic uses HTTPS where appropriate.

### Cache Security

- [ ] Public and private behaviors are separated where appropriate.
- [ ] Cache keys are intentionally designed.
- [ ] Cookies are forwarded only when required.
- [ ] Query strings are intentionally handled.
- [ ] Personalized responses cannot leak through shared caching.
- [ ] Sensitive responses use appropriate cache-control directives.

### Credential Security

- [ ] Private signing keys are protected.
- [ ] Secrets are not committed to source control.
- [ ] Signed credentials have appropriate expiration.
- [ ] Key rotation is documented.
- [ ] Sensitive credentials are not written to logs.

### Operations

- [ ] CloudFront logging is configured where required.
- [ ] WAF events are observable.
- [ ] Security alerts are defined.
- [ ] Configuration is managed as code.
- [ ] Configuration drift is reviewed.
- [ ] Disaster recovery includes security configuration.

## Interview Reference

Common CloudFront security questions include:

| Question | Key point |
|---|---|
| Why use OAC? | To allow CloudFront to access a private S3 origin without making the bucket public |
| Is WAF an authentication mechanism? | No; WAF filters requests, while authentication and authorization remain application concerns |
| Why use signed URLs? | To provide controlled, temporary access to private CloudFront content |
| Does HTTPS prevent DDoS? | No; HTTPS encrypts traffic, while DDoS protection is handled through services such as AWS Shield and architectural controls |
| Why can caching create security issues? | Incorrect cache-key or behavior configuration can cause personalized responses to be reused incorrectly |
| Why protect the origin if CloudFront already has WAF? | A directly reachable origin can bypass CloudFront, WAF, and other edge controls |
| What is the difference between Shield and WAF? | Shield focuses on DDoS protection; WAF evaluates and filters application-layer requests |
| Should CloudFront replace application authorization? | No; business authorization belongs in the application |
| Why restrict forwarded headers and cookies? | To reduce attack surface, origin complexity, and cache fragmentation |
| Why rotate signing keys? | To limit the impact of key compromise and support controlled credential lifecycle management |

## Reference Architecture

A strong baseline for a production web application is:

```mermaid
flowchart TD
    User[User / Client]
    DNS[DNS]
    CF[CloudFront]
    Shield[AWS Shield]
    WAF[AWS WAF]
    ALB[Application Load Balancer]
    App[Django / FastAPI]
    Redis[(Redis)]
    DB[(PostgreSQL)]
    S3[Private S3]
    OAC[Origin Access Control]

    User --> DNS
    DNS --> CF
    Shield -. DDoS protection .-> CF
    CF --> WAF

    WAF --> ALB
    ALB --> App
    App --> Redis
    App --> DB

    CF --> OAC
    OAC --> S3
```

This architecture separates responsibilities:

```text
CloudFront
    → Global delivery and edge termination

Shield
    → DDoS protection

WAF
    → Request filtering

OAC
    → S3 origin protection

ALB
    → Application traffic entry

Django / FastAPI
    → Authentication and business authorization

Redis
    → Application caching

PostgreSQL
    → Persistent application data
```

## Navigation

### Architecture

For the broader CloudFront architecture material, see:

- [Origin Architecture](../../02-%20Architecture/04-%20CloudFront/02-%20Origin%20Architecture.md)

### Security

| File | Focus |
|---|---|
| [01- Security Overview](./01-%20Security%20Overview.md) | Security model and defense-in-depth architecture |
| [02- HTTPS and TLS](./02-%20HTTPS%20and%20TLS.md) | TLS termination and encrypted communication |
| [03- AWS Shield and DDoS Protection](./03-%20AWS%20Shield%20and%20DDoS%20Protection.md) | DDoS resilience |
| [04- AWS WAF and Request Filtering](./04-%20AWS%20WAF%20and%20Request%20Filtering.md) | HTTP request filtering |
| [05- Origin Access Control](./05-%20Origin%20Access%20Control.md) | Private S3 origin access |
| [06- Geo Restrictions](./06-%20Geo%20Restrictions.md) | Geographic access restrictions |
| [07- Field-Level Encryption](./07-%20Field-Level%20Encryption.md) | Sensitive request-field protection |
| [08- Signed URLs and Signed Cookies](./08-%20Signed%20URLs%20and%20Signed%20Cookies.md) | Private content authorization |
| [09- Security Best Practices](./09-%20Security%20Best%20Practices.md) | Production security hardening |

## Key Takeaways

- **CloudFront security is layered:** combine TLS, Shield, WAF, origin protection, authorization, IAM, and monitoring according to the workload.
- **The origin must be protected independently:** otherwise users may bypass CloudFront and its security controls.
- **Caching is a security boundary:** cache policies, cache keys, cookies, query strings, and personalized responses must be designed together.
- **Private content requires explicit authorization:** use mechanisms such as OAC and signed URLs/cookies rather than relying on obscurity or public origins.
- **Production security is operational:** manage configuration as code, monitor security signals, rotate credentials, review drift, and maintain a recoverable architecture.