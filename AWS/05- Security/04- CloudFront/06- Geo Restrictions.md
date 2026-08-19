# 06- Geo Restrictions

## Overview

Amazon CloudFront geo restrictions control whether CloudFront serves content to viewers based on the geographic location associated with their IP address.

They provide an edge-level control for requirements such as:

- Restricting content to specific countries
- Blocking traffic from specific countries
- Enforcing regional distribution requirements
- Reducing exposure in markets where a service is not offered
- Supporting licensing or contractual geographic restrictions

The request flow is:

```text
Viewer
  │
  │ HTTPS request
  ▼
CloudFront Edge Location
  │
  │ Determine viewer country
  ▼
Geo Restriction
  │
  ├── Allowed ─────► Cache / Origin
  │
  └── Blocked ─────► HTTP 403
```

Geo restrictions operate at the CloudFront distribution level and are independent of application-level authorization.

They should therefore be treated as one layer in a broader security architecture:

```text
Internet
   │
   ▼
CloudFront
   │
   ├── TLS
   ├── Geo Restriction
   ├── AWS WAF
   ├── Cache Policies
   └── Origin Access Control
          │
          ▼
       Origin
```

Geo restrictions are useful when the requirement is fundamentally geographic. They are not a replacement for user authentication, authorization, or precise location verification.

## Why Geo Restrictions Exist

A backend application may have users distributed globally while its business or legal requirements apply only to selected countries.

Without edge-level geographic filtering:

```text
Viewer ──► CloudFront ──► Application
  │
  ├── India
  ├── Germany
  ├── United States
  ├── Brazil
  └── Other countries
```

Every request reaches the application or origin path before the application determines whether the request should be served.

With CloudFront geo restriction:

```text
Viewer
  │
  ▼
CloudFront
  │
  ├── Allowed country ──► Application / Origin
  │
  └── Blocked country ──► 403
```

This can prevent unnecessary origin traffic and enforce geographic boundaries closer to the user.

## What Geo Restrictions Control

CloudFront supports two primary modes:

| Mode | Behavior | Typical use |
|---|---|---|
| Allowlist | Only specified countries can access content | Regional service availability |
| Blocklist | Specified countries are denied | Blocking selected markets |

### Allowlist

An allowlist explicitly defines the countries that may access the distribution.

```text
Allowed:
├── IN
├── US
├── GB
└── DE

Everything else:
└── Blocked
```

This is appropriate when the valid geographic set is small and known.

For example:

> A service is currently licensed only in India, the United Kingdom, and Germany.

The distribution can allow only those countries.

### Blocklist

A blocklist defines countries that should not receive the content.

```text
Blocked:
├── Country A
├── Country B
└── Country C

Everything else:
└── Allowed
```

This is appropriate when the application is globally available but a small number of regions must be excluded.

## How CloudFront Determines the Country

CloudFront determines the viewer's country primarily from the viewer IP address using its geographic IP-location data.

Conceptually:

```text
Viewer IP
   │
   ▼
CloudFront
   │
   ▼
Geolocation lookup
   │
   ▼
Country
   │
   ▼
Geo restriction evaluation
```

The application does not need to perform the initial geographic decision itself.

However, IP geolocation is not equivalent to precise physical location.

An IP address can be associated with:

- VPN infrastructure
- Corporate proxies
- Mobile carrier networks
- NAT gateways
- Cloud providers
- ISP address pools
- Privacy services

Therefore:

```text
IP location ≠ guaranteed physical location
```

This distinction is critical for security and regulatory designs.

## Request Lifecycle

A simplified CloudFront request lifecycle is:

```mermaid
sequenceDiagram
    participant U as Viewer
    participant CF as CloudFront
    participant G as Geo Restriction
    participant O as Origin

    U->>CF: HTTPS request
    CF->>G: Determine viewer country
    alt Country allowed
        G-->>CF: Allow
        CF->>CF: Check cache
        alt Cache hit
            CF-->>U: Cached response
        else Cache miss
            CF->>O: Origin request
            O-->>CF: Response
            CF-->>U: Response
        end
    else Country blocked
        G-->>CF: Deny
        CF-->>U: HTTP 403
    end
```

The important property is that blocked requests can be rejected at CloudFront before the origin is contacted.

## Geo Restrictions and Cache

Geo restriction is evaluated before CloudFront serves content to the viewer.

Conceptually:

```text
Request
  │
  ▼
Geo restriction
  │
  ├── Denied ──► 403
  │
  └── Allowed
        │
        ▼
     Cache lookup
        │
        ├── Hit ──► Response
        │
        └── Miss ──► Origin
```

This means a blocked viewer should not receive an object simply because that object is already cached at the edge.

Geo restriction is therefore not simply an origin routing mechanism.

## Geo Restrictions vs Application Authorization

These controls operate at different layers.

| Control | Primary decision |
|---|---|
| CloudFront Geo Restriction | Is this viewer's geographic location allowed? |
| AWS WAF | Does this HTTP request satisfy security rules? |
| Application authentication | Who is the user? |
| Application authorization | Is this user allowed to perform this operation? |
| Signed URL/cookie | Does the request have valid delegated access? |
| S3 OAC | Is CloudFront authorized to access the origin? |

A production application may use several simultaneously:

```text
Viewer
  │
  ▼
CloudFront
  │
  ├── Geo restriction
  ├── AWS WAF
  ├── TLS
  └── Signed URL/cookie
          │
          ▼
       Origin
```

Do not attempt to solve identity-based authorization using country restrictions.

## Geo Restrictions vs AWS WAF Geo Match

CloudFront geo restrictions and AWS WAF geographic matching overlap but are not interchangeable.

| Capability | CloudFront Geo Restriction | AWS WAF Geo Match |
|---|---|---|
| Primary purpose | Distribution-level country access | Request filtering |
| Allow/block countries | Yes | Yes |
| Rule combinations | Limited | Extensive |
| Combine with IP rules | Limited | Yes |
| Rate-based rules | No | Yes |
| Header inspection | No | Yes |
| URI/path inspection | No | Yes |
| User-agent filtering | No | Yes |
| Custom responses | More limited | More flexible |
| Per-path policies | Not the primary model | Better suited |
| Typical use | Broad geographic access control | Application security policy |

Use CloudFront geo restriction when the requirement is:

> This distribution should only be accessible from these countries.

Use AWS WAF when the requirement is closer to:

> Requests from this country should be blocked only for `/admin`, or combined with IP reputation, rate limits, headers, or other conditions.

## Choosing Between CloudFront Geo Restriction and WAF

A useful decision rule is:

```text
Entire distribution?
       │
       ├── Yes ──► CloudFront Geo Restriction
       │
       └── No
            │
            ▼
       Request-specific rule?
            │
            └──► AWS WAF
```

For example:

### Requirement

> Block all traffic from Country X.

CloudFront geo restriction is a natural fit.

### Requirement

> Block Country X only from `/admin`.

AWS WAF is more appropriate.

### Requirement

> Allow Country X but only for authenticated users.

Neither geographic control nor WAF replaces application authorization.

Use:

```text
Geo check
   +
Authentication
   +
Authorization
```

## Country Code Configuration

CloudFront country selections correspond to standard country identifiers.

A practical representation is:

| Country | Code |
|---|---|
| India | `IN` |
| United States | `US` |
| United Kingdom | `GB` |
| Germany | `DE` |
| France | `FR` |
| Japan | `JP` |
| Singapore | `SG` |
| Australia | `AU` |

Use the country selection supported by CloudFront rather than manually maintaining application-level IP ranges.

## Allowlist Strategy

An allowlist is usually safer when the business requirement is:

> Only explicitly approved countries should receive this service.

Example:

```text
CloudFront Distribution
       │
       ▼
Allow:
├── IN
├── US
└── GB

All other countries
       │
       ▼
HTTP 403
```

Advantages:

- Explicit security boundary
- Smaller geographic attack surface
- New countries do not become available accidentally
- Easy to reason about during audits

Limitations:

- Requires maintenance when expanding into new markets
- Can unintentionally block legitimate users
- VPN/proxy users may appear to originate from unexpected countries

## Blocklist Strategy

A blocklist is useful when the application is globally available except for known restricted regions.

Example:

```text
CloudFront Distribution
       │
       ▼
Block:
├── Country A
└── Country B

Everything else
       │
       ▼
Allowed
```

Advantages:

- Simple for globally available services
- Lower operational maintenance when only a few regions are restricted

Limitations:

- Newly restricted countries must be added
- It is easy to overlook emerging geographic requirements
- It may not satisfy strict allow-only compliance requirements

## Geo Restrictions and Signed URLs

Signed URLs and signed cookies provide a separate access mechanism.

For example:

```text
User
  │
  ▼
Application
  │
  │ Authenticate user
  │ Authorize object
  ▼
Signed CloudFront URL
  │
  ▼
CloudFront
  │
  ├── Geo restriction
  └── Signature validation
          │
          ▼
        Origin
```

A valid signed URL does not fundamentally change the viewer's geographic location.

Therefore, if the distribution blocks a country, a valid signed URL should not be treated as a universal bypass for the distribution's geographic restriction.

This is an important architectural distinction:

```text
Geographic policy
        +
Access credential
```

Both can be required.

## Geo Restrictions and APIs

CloudFront can sit in front of REST APIs and other HTTP workloads.

Example:

```text
Client
  │
  ▼
CloudFront
  │
  ├── Geo restriction
  ├── WAF
  └── TLS
        │
        ▼
       ALB
        │
        ▼
   Django / FastAPI
        │
        ├── PostgreSQL
        ├── Redis
        └── Kafka
```

However, geographic restriction should be applied only if the API's business requirements justify it.

For an API used by a globally distributed mobile application, an aggressive country allowlist can accidentally break:

- Roaming users
- Corporate users
- VPN users
- Travelers
- International support teams
- CI/CD systems
- External integrations

API geographic restrictions therefore require more careful operational validation than simple static-content restrictions.

## Geo Restrictions for Static Frontends

A static frontend is a straightforward use case.

Example:

```text
Browser
  │
  ▼
CloudFront
  │
  ├── Geo restriction
  ├── WAF
  └── Cache
       │
       ▼
    Private S3
```

If the frontend is available only in selected markets, blocking unauthorized countries at CloudFront can prevent unnecessary S3 access and simplify the public delivery boundary.

## Geo Restrictions for Media

Streaming and media distribution frequently have geographic licensing requirements.

A simplified architecture is:

```text
Viewer
  │
  ▼
CloudFront
  │
  ├── Geo restriction
  ├── Signed URL / Cookie
  └── Cache
        │
        ▼
    Private S3
```

This combines:

- Geographic entitlement
- Content entitlement
- Origin protection
- Edge caching

These are separate controls and should remain separate in the architecture.

## Geo Restrictions Are Not DRM

A geographic restriction does not provide digital rights management.

It does not prevent a user from:

- Recording content
- Sharing credentials
- Using a VPN
- Re-hosting content
- Copying content after legitimate access

The control is primarily:

```text
Viewer IP
    │
    ▼
Country determination
    │
    ▼
Allow / deny
```

Do not treat geo restriction as a complete content-protection mechanism.

## VPN and Proxy Considerations

VPNs and proxies are a major limitation of IP-based geographic controls.

Example:

```text
User in India
      │
      ▼
VPN endpoint in United States
      │
      ▼
CloudFront
      │
      ▼
Detected country = United States
```

CloudFront sees the source network path presented to it, not necessarily the user's physical location.

This means:

```text
Geo restriction
       ≠
Physical presence verification
```

If a requirement demands stronger geographic assurance, additional application-level or identity-based controls may be necessary.

## Mobile Networks and NAT

Mobile users can also create unexpected geographic results.

Many users may share public IP addresses through carrier NAT infrastructure:

```text
Phone A ─┐
Phone B ─┼──► Mobile Carrier NAT ──► Public IP
Phone C ─┘
```

The public IP may be associated with a location different from the user's actual physical location.

This can result in false positives or false negatives.

Production teams should test:

- Mobile networks
- Residential ISPs
- Corporate networks
- VPNs
- IPv4
- IPv6

before enforcing strict geographic policies.

## IPv4 and IPv6 Considerations

Modern applications should account for both IPv4 and IPv6 traffic.

The architectural concern is:

```text
IPv4 ──► GeoIP ──► Country
IPv6 ──► GeoIP ──► Country
```

Do not assume that testing only IPv4 represents the complete production behavior.

Where geographic access is business-critical, validate IPv6 behavior as part of release testing.

## Error Behavior

A blocked viewer is generally denied by CloudFront rather than being sent to the origin.

Conceptually:

```text
Blocked country
      │
      ▼
CloudFront
      │
      ▼
403 Forbidden
```

This is useful because the origin does not need to spend resources processing a request that should never have been served.

## Custom Error Handling

If the user experience requires a custom response, error handling can be designed around the CloudFront response path.

For example:

```text
Blocked viewer
     │
     ▼
CloudFront
     │
     ▼
403
     │
     ▼
Custom error response
```

Be careful when customizing errors.

Do not accidentally create a response path that exposes information about the geographic policy or allows a blocked request to retrieve protected content.

## Security Considerations

Geo restrictions should be considered a coarse-grained security control.

They are useful for reducing exposure, but they should not be the only security mechanism.

A layered architecture is stronger:

```text
                    Internet
                       │
                       ▼
                 CloudFront
                       │
        ┌──────────────┼──────────────┐
        │              │              │
       TLS       Geo Restriction     WAF
        │              │              │
        └──────────────┼──────────────┘
                       │
                       ▼
                  Application
                       │
             ┌─────────┴─────────┐
             │                   │
      Authentication       Authorization
```

For S3-backed distributions, add origin protection:

```text
CloudFront
    │
    ▼
OAC
    │
    ▼
Private S3
```

## Security Best Practices

### Use the Narrowest Appropriate Boundary

If the entire distribution is geographically restricted, CloudFront geo restriction is appropriate.

If only specific paths require geographic controls, consider AWS WAF.

### Do Not Use Geo Restrictions as Authentication

Country restrictions do not answer:

> Who is this user?

Use proper identity and authorization controls for that requirement.

### Combine with WAF

For public applications:

```text
CloudFront
├── Geo Restriction
├── AWS WAF
├── TLS
└── Origin Protection
```

Each layer addresses a different threat or policy.

### Protect the Origin

A geo restriction does not protect an origin if attackers can bypass CloudFront.

For S3:

```text
CloudFront ──OAC──► Private S3
```

For application origins:

```text
CloudFront ──► ALB ──► Application
```

Use appropriate network and application controls to prevent unintended direct-origin access.

## Scalability Considerations

Geo restrictions are particularly efficient because the decision occurs at the CloudFront edge.

Without edge filtering:

```text
Blocked request
    │
    ▼
CloudFront
    │
    ▼
ALB
    │
    ▼
Django
    │
    ▼
Application logic
```

With edge filtering:

```text
Blocked request
    │
    ▼
CloudFront
    │
    ▼
403
```

This can reduce:

- Origin request volume
- Application CPU consumption
- Load balancer traffic
- Database pressure caused by downstream request processing

The largest benefit comes when blocked traffic would otherwise generate significant origin workload.

## Performance Considerations

A geo restriction is evaluated close to the viewer.

A blocked request can therefore terminate before:

- Cache lookup proceeds to content delivery
- Origin connection establishment
- Application execution
- Database queries

For allowed traffic, the geographic decision is only one part of the CloudFront request lifecycle.

Do not expect geo restrictions themselves to make allowed requests significantly faster. Their primary value is access control and origin-load reduction.

## Cost Considerations

Blocking traffic at CloudFront can reduce downstream infrastructure consumption because denied requests do not need to reach the origin.

Potential savings can include:

- Application compute
- Load balancer processing
- Database workload
- Origin bandwidth

However, CloudFront request processing still has associated costs.

The correct architecture should therefore be evaluated based on:

```text
CloudFront cost
        +
Origin cost
        +
Security requirements
        +
Operational requirements
```

Do not implement geographic filtering solely as a cost optimization unless the traffic pattern justifies it.

## Monitoring

A production geo-restricted distribution should be observable.

Useful signals include:

- CloudFront request counts
- HTTP status codes
- 403 response volume
- Requests by geographic location
- WAF blocked requests
- Origin request volume
- Cache hit ratio
- Application error rates

A useful operational view is:

```text
CloudFront
├── Requests
├── 2xx
├── 4xx
├── 5xx
├── Cache hit ratio
└── Geographic distribution
```

When a geographic policy changes, monitor the 403 rate closely.

An unexpected increase may indicate that legitimate users are being blocked.

## Logging

CloudFront logs can help investigate geographic access behavior.

When troubleshooting, correlate:

```text
Request
  │
  ├── Timestamp
  ├── Client IP
  ├── Country
  ├── URI
  ├── Status
  └── User-Agent
```

with:

```text
WAF logs
Application logs
ALB logs
Origin logs
```

This makes it easier to determine whether a request was denied by CloudFront, WAF, or the application.

## Operational Change Management

Geo restrictions can have immediate user impact.

A configuration change such as:

```text
Allow:
IN, US, GB
```

versus:

```text
Allow:
IN, US, GB, DE
```

changes production availability.

Treat geographic configuration as application policy, not merely infrastructure configuration.

Recommended practices:

- Version-control the configuration.
- Review country changes.
- Test before production deployment.
- Record the business reason for restrictions.
- Define an owner for geographic policy.
- Monitor 403 rates after changes.
- Have a rollback procedure.

## Infrastructure as Code

A CloudFront distribution can represent geo restrictions in infrastructure code.

A representative Terraform configuration is:

```hcl
resource "aws_cloudfront_distribution" "cdn" {
  enabled = true

  # Origins and cache behaviors omitted for clarity.

  restrictions {
    geo_restriction {
      restriction_type = "whitelist"

      locations = [
        "IN",
        "GB",
        "DE"
      ]
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}
```

A blocklist configuration can use:

```hcl
restrictions {
  geo_restriction {
    restriction_type = "blacklist"

    locations = [
      "XX",
      "YY"
    ]
  }
}
```

Use the actual country identifiers supported by CloudFront rather than arbitrary application-defined values.

For production infrastructure, keep the country list configurable:

```hcl
variable "allowed_countries" {
  type        = list(string)
  description = "Countries allowed to access the CloudFront distribution."
  default     = ["IN", "GB", "DE"]
}
```

Then:

```hcl
restrictions {
  geo_restriction {
    restriction_type = "whitelist"
    locations        = var.allowed_countries
  }
}
```

This makes policy changes explicit in CI/CD.

## AWS CLI Inspection

Inspect a CloudFront distribution:

```bash
aws cloudfront get-distribution \
  --id <DISTRIBUTION_ID>
```

The distribution configuration contains the geographic restriction configuration.

For configuration workflows, retrieve the distribution configuration and ETag before updating it:

```bash
aws cloudfront get-distribution-config \
  --id <DISTRIBUTION_ID>
```

When making CLI-based updates, preserve the required configuration and supply the returned ETag for optimistic concurrency control.

For production environments, infrastructure as code is generally preferable to ad hoc CLI modifications because the desired state remains version-controlled.

## Deployment Workflow

A controlled geographic-policy deployment can follow:

```mermaid
flowchart TD
    A[Business Requirement] --> B[Define Countries]
    B --> C[Update IaC]
    C --> D[Code Review]
    D --> E[CI Validation]
    E --> F[Deploy Staging]
    F --> G[Test Geographic Behavior]
    G --> H[Production Deployment]
    H --> I[Monitor 403 Rate]
    I --> J{Unexpected Impact?}
    J -->|No| K[Keep Policy]
    J -->|Yes| L[Rollback]
```

Testing should include representative networks rather than assuming a single test machine is sufficient.

## Testing Strategy

A useful test matrix is:

| Test case | Expected behavior |
|---|---|
| Allowed country | Request succeeds |
| Blocked country | Request receives 403 |
| Cache hit from allowed country | Content succeeds |
| Cache hit from blocked country | Request remains blocked |
| Direct origin access | Must follow origin security policy |
| VPN endpoint | Behavior based on detected endpoint country |
| Mobile network | Validate expected geographic result |
| IPv4 | Country detected correctly |
| IPv6 | Country detected correctly |
| WAF block | WAF policy still applies |
| Authenticated request | Geo policy still applies |

Do not validate geographic controls only by changing an application header such as:

```http
X-Country: IN
```

Client-controlled headers are not equivalent to CloudFront's geographic determination.

## Common Mistakes and Pitfalls

### Treating IP Geolocation as Exact Location

**Problem:** The architecture assumes that the detected country proves where the user physically is.

**Why it happens:** Country detection looks deterministic from an application perspective.

**Correction:** Treat IP geolocation as an approximate network-location signal.

### Using Geo Restriction for User Authorization

**Problem:** The team assumes users in an allowed country are automatically authorized.

**Correction:** Combine geographic policy with authentication and authorization.

### Using an Allowlist Without an Expansion Process

**Problem:** A new market launches but remains inaccessible because the country was never added.

**Correction:** Make geographic policy changes part of the product release process.

### Blocking a Country Without Testing Mobile Networks

**Problem:** Legitimate mobile users are unexpectedly denied.

**Correction:** Test representative mobile and carrier networks before enforcing strict policies.

### Forgetting VPNs

**Problem:** Users appear to come from the wrong country.

**Correction:** Document VPN behavior as an expected limitation of IP-based geolocation.

### Using Geo Restriction Instead of WAF

**Problem:** The requirement is actually path-specific or request-specific.

**Correction:** Use AWS WAF when geographic logic needs to be combined with paths, headers, IPs, rate limits, or other request attributes.

### Assuming Geo Restriction Protects the Origin

**Problem:** Attackers bypass CloudFront and access the origin directly.

**Correction:** Protect the origin independently.

For S3:

```text
CloudFront ──OAC──► Private S3
```

### Making Country Lists Manually in Production

**Problem:** Configuration changes become difficult to audit.

**Correction:** Manage geographic policies through IaC and CI/CD.

### Ignoring 403 Monitoring

**Problem:** A configuration change blocks legitimate users without immediate detection.

**Correction:** Monitor CloudFront 4xx responses and geographic request patterns after policy changes.

## Production Architecture

A production architecture combining geographic filtering with application security can look like:

```mermaid
flowchart LR
    USER[Global Users]
    CF[CloudFront]
    GEO[Geo Restriction]
    WAF[AWS WAF]
    CACHE[CloudFront Cache]
    OAC[Origin Access Control]
    S3[(Private S3)]
    APP[Application Origin]

    USER -->|HTTPS| CF
    CF --> GEO
    GEO -->|Allowed| WAF
    GEO -->|Blocked| DENY[403]
    WAF -->|Allowed| CACHE
    CACHE -->|Cache hit| USER
    CACHE -->|Cache miss| OAC
    OAC --> S3
    WAF --> APP
```

For an S3-backed static application:

```text
                         Internet
                            │
                            ▼
                       CloudFront
                            │
             ┌──────────────┼──────────────┐
             │              │              │
            TLS       Geo Restriction     WAF
             │              │              │
             └──────────────┼──────────────┘
                            │
                            ▼
                     CloudFront Cache
                            │
                       Cache Miss
                            │
                            ▼
                           OAC
                            │
                            ▼
                       Private S3
```

For a backend API:

```text
                         Internet
                            │
                            ▼
                       CloudFront
                            │
             ┌──────────────┼──────────────┐
             │              │              │
            TLS       Geo Restriction     WAF
             │              │              │
             └──────────────┼──────────────┘
                            │
                            ▼
                           ALB
                            │
                            ▼
                    Django / FastAPI
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
         PostgreSQL       Redis         Kafka
```

## When Not to Use CloudFront Geo Restrictions

Do not automatically add geo restrictions to every application.

They may be inappropriate when:

- The application is globally available.
- Users frequently travel internationally.
- Users commonly access through corporate VPNs.
- Mobile carrier networks create unpredictable geographic mappings.
- Geographic location is not part of the business policy.
- Precise physical location is required.
- User-specific authorization is the actual requirement.

In these cases, application-level identity and authorization or more precise location controls may be more appropriate.

## Decision Matrix

| Requirement | Recommended control |
|---|---|
| Entire distribution restricted to countries | CloudFront Geo Restriction |
| Block selected countries globally | CloudFront Geo Restriction |
| Country-specific path restriction | AWS WAF |
| Country + IP restriction | AWS WAF |
| Country + rate limit | AWS WAF |
| User-specific access | Application authorization |
| Temporary content access | Signed URL/cookie |
| Private S3 origin | CloudFront OAC |
| Exact physical-location verification | Application/domain-specific location controls |
| DDoS protection | AWS Shield + CloudFront |
| Malicious HTTP request filtering | AWS WAF |

## Interview Traps

### Is CloudFront Geo Restriction Based on the User's GPS Location?

No. It is based on the geographic location associated with the viewer's IP address.

### Can a VPN Change the Result?

Yes. A VPN can cause CloudFront to associate the request with the VPN endpoint's geographic location.

### Does Geo Restriction Replace AWS WAF?

No. CloudFront geo restriction is a coarse distribution-level geographic control. AWS WAF provides more flexible request filtering.

### Does Geo Restriction Protect the Origin?

No. The origin must be protected independently.

### Can an Allowed Country Still Receive a WAF Block?

Yes. These are separate controls.

For example:

```text
Country allowed
      │
      ▼
CloudFront
      │
      ▼
AWS WAF
      │
      ▼
Blocked by WAF
```

### Does a Valid Signed URL Automatically Bypass Geo Restriction?

No. Geographic policy and signed access are separate controls.

### Is IP Geolocation Perfect?

No. VPNs, proxies, mobile networks, carrier NAT, corporate networks, and changing IP allocations can produce unexpected geographic results.

## Production Checklist

### Policy

- [ ] Geographic requirements are explicitly documented.
- [ ] Allowlist vs blocklist is intentional.
- [ ] Country identifiers are validated.
- [ ] A business owner exists for geographic policy.
- [ ] Policy changes have a review process.

### CloudFront

- [ ] HTTPS is enabled.
- [ ] Geo restriction is configured at the intended scope.
- [ ] AWS WAF is used where request-specific filtering is required.
- [ ] Cache behavior is understood.
- [ ] Origin protection is configured independently.

### Application

- [ ] Geographic restriction is not being used as authentication.
- [ ] Application authorization remains enforced.
- [ ] VPN and mobile-network behavior is documented.
- [ ] International users are tested where relevant.

### Operations

- [ ] CloudFront 4xx metrics are monitored.
- [ ] Geographic traffic patterns are observable.
- [ ] Configuration is managed through IaC.
- [ ] CI/CD validates policy changes.
- [ ] Rollback procedures exist.
- [ ] Production changes are monitored after deployment.

### Security

- [ ] Origin cannot be unintentionally bypassed.
- [ ] WAF protects request-level threats where required.
- [ ] TLS is configured correctly.
- [ ] Sensitive origins use appropriate authentication.
- [ ] Geo restrictions are treated as one layer of defense rather than the complete security model.

## Key Takeaways

- **CloudFront geo restrictions provide distribution-level country-based access control using the geographic location associated with the viewer's IP address.**
- **Use allowlists for explicitly approved markets and blocklists when the service is globally available except for selected regions.**
- **Geo restriction is not authentication, precise physical-location verification, or origin protection; combine it with WAF, application authorization, and appropriate origin security.**
- **AWS WAF is generally more appropriate when geographic rules must be combined with paths, IPs, headers, rate limits, or other request attributes.**
- **Treat geographic policy as production application policy: manage it through IaC, test VPN/mobile/IPv4/IPv6 scenarios, and monitor 4xx behavior after changes.**