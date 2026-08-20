# 08- Operational Best Practices

## Overview

CloudFront should be operated as a production edge layer rather than treated as a simple CDN configuration.

Operational quality depends on maintaining correct behavior across the entire request path:

```text
Viewer
  ↓
DNS
  ↓
CloudFront
  ├── Cache
  ├── WAF
  ├── TLS
  └── Request policies
        ↓
      Origin
        ↓
  ALB / Nginx / API Gateway
        ↓
  Django / FastAPI / Microservices
        ↓
 Redis / PostgreSQL / Kafka / External Services
```

A technically valid CloudFront distribution can still be operationally unsafe because of:

- Poor cache-key design.
- Excessive origin traffic.
- Incorrect TLS configuration.
- Overly permissive origin access.
- Missing observability.
- Manual configuration drift.
- Unsafe invalidations.
- Poor deployment practices.
- Incorrect WAF rules.
- Unbounded origin failures.
- Insufficient rollback procedures.

Production CloudFront operations should therefore focus on **correctness, security, observability, performance, reliability, cost control, and controlled change management**.

---

## Operational Principles

A reliable CloudFront environment should follow these principles:

| Principle | Operational goal |
|---|---|
| Configuration as code | Make infrastructure reproducible |
| Least privilege | Minimize security exposure |
| Explicit caching | Avoid accidental cache behavior |
| Observable behavior | Detect failures quickly |
| Controlled changes | Reduce deployment risk |
| Automated validation | Catch configuration errors early |
| Safe rollback | Restore known-good state quickly |
| Origin protection | Prevent unnecessary backend load |
| Immutable assets | Reduce invalidation dependency |
| Continuous optimization | Improve cost and performance over time |

The most important operational rule is:

> Do not optimize CloudFront configuration based only on cache-hit percentage or latency. Optimize for correct application behavior under normal and failure conditions.

---

## Configuration as Code

CloudFront configuration should be managed through infrastructure as code whenever possible.

Common choices include:

- Terraform.
- AWS CloudFormation.
- AWS CDK.
- CI/CD-managed infrastructure workflows.

A conceptual Terraform configuration might look like:

```hcl
resource "aws_cloudfront_distribution" "application" {
  enabled = true

  origin {
    domain_name = aws_lb.application.dns_name
    origin_id   = "application-origin"
  }

  default_cache_behavior {
    target_origin_id       = "application-origin"
    viewer_protocol_policy = "redirect-to-https"

    allowed_methods = [
      "GET",
      "HEAD",
      "OPTIONS",
      "PUT",
      "POST",
      "PATCH",
      "DELETE"
    ]

    cached_methods = [
      "GET",
      "HEAD"
    ]
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }

  }

  viewer_certificate {
    acm_certificate_arn = aws_acm_certificate.application.arn
    ssl_support_method  = "sni-only"
  }
}
```

The exact configuration should be adapted to the application's traffic and security model rather than copied unchanged.

### Why Configuration as Code Matters

Manual console changes create configuration drift:

```text
Git repository
      │
      │ expected state
      ▼
Terraform / CloudFormation
      │
      ▼
CloudFront

        ≠

AWS Console
      │
      │ manual changes
      ▼
Production state
```

Drift becomes especially dangerous during incidents because engineers may not know which configuration is authoritative.

### Production Practices

- Store CloudFront configuration in version control.
- Review changes through pull requests.
- Run infrastructure validation in CI.
- Keep production and non-production configurations comparable.
- Record emergency console changes and reconcile them into code.
- Avoid configuration changes that cannot be reproduced.

---

## Separate Distribution Configuration by Environment

Production and non-production environments should not casually share the same CloudFront distribution.

A typical architecture is:

```text
Development
    ↓
dev.example.com
    ↓
CloudFront Distribution A

Staging
    ↓
staging.example.com
    ↓
CloudFront Distribution B

Production
    ↓
example.com
    ↓
CloudFront Distribution C
```

This prevents testing from directly modifying production behavior.

Environment-specific configuration may include:

- Origins.
- WAF rules.
- Certificates.
- Cache policies.
- Logging destinations.
- Allowed domains.
- Security controls.

Avoid making staging behave so differently from production that operational testing becomes meaningless.

---

## Change Management

CloudFront changes can have a broad blast radius because one configuration change can affect globally distributed traffic.

Treat changes such as the following as production-impacting:

- Cache policy modifications.
- Origin changes.
- Viewer protocol changes.
- TLS policy changes.
- WAF association changes.
- Response header policy changes.
- Origin request policy changes.
- Allowed methods changes.
- Signed URL/cookie changes.
- Custom error response changes.

A safe change process is:

```mermaid
flowchart LR
    Change[Configuration Change]
    Change --> Review[Peer Review]
    Review --> Validate[Automated Validation]
    Validate --> Stage[Staging]
    Stage --> Test[Functional Tests]
    Test --> Deploy[Production Deployment]
    Deploy --> Observe[Monitor]
    Observe --> Rollback{Healthy?}
    Rollback -->|Yes| Done[Complete]
    Rollback -->|No| Revert[Rollback]
```

Do not treat CloudFront as a configuration layer that can be changed casually during application deployment.

---

## Cache Policy Discipline

Caching is one of the highest-impact CloudFront configuration areas.

A cache policy determines which request characteristics participate in the cache key and how cached responses are reused.

Potential cache-key dimensions include:

- Path.
- Query strings.
- Cookies.
- Headers.

A cache key that is too broad can return incorrect content.

A cache key that is too narrow can destroy the cache hit ratio.

### Too Broad

```text
Cache key:
  /products/123
```

If the response differs based on:

```text
Accept-Language
Authorization
Cookie
```

the same cached object may be incorrectly reused.

### Too Fragmented

```text
/products/123?tracking_id=abc
/products/123?tracking_id=def
/products/123?tracking_id=ghi
```

If irrelevant query parameters participate in the cache key, every request may generate a different cache entry.

### Production Rule

Only include request attributes in the cache key when they materially affect the representation being cached.

---

## Do Not Cache Personalized Responses Accidentally

Authenticated or personalized responses require particular care.

For example:

```http
GET /api/profile
Authorization: Bearer user-token
```

If the response is incorrectly cached as a shared object, one user's response could potentially be served to another user.

This is both:

- A security vulnerability.
- A correctness failure.

For personalized APIs, carefully evaluate:

- Whether CloudFront should cache the response at all.
- Whether authorization information participates in the required behavior.
- Whether the request should bypass caching.
- Whether the response contains user-specific data.

A common production strategy is to cache public content aggressively while leaving sensitive dynamic APIs uncached unless the caching model is explicitly designed and verified.

---

## Origin Request Policy vs Cache Policy

These policies solve different problems.

| Policy | Purpose |
|---|---|
| Cache policy | Determines cache-key behavior and caching settings |
| Origin request policy | Determines what additional request information is forwarded to the origin |

Do not assume that forwarding a header to the origin automatically means it should participate in the cache key.

This distinction is important.

For example:

```text
Viewer request
    │
    ├── Header A affects cache identity
    │       ↓
    │   Cache key
    │
    └── Header B only needed by origin
            ↓
        Origin request
```

Forwarding unnecessary data to the origin can reduce efficiency, while incorrectly adding it to the cache key can fragment the cache.

---

## Minimize Origin Dependencies

CloudFront provides the greatest operational benefit when the origin does not need to process every request.

For cacheable content:

```text
Viewer
  ↓
CloudFront
  ↓
Cache HIT
  ↓
Response
```

is preferable to:

```text
Viewer
  ↓
CloudFront
  ↓
ALB
  ↓
Django
  ↓
Redis
  ↓
PostgreSQL
```

The shorter dependency chain improves:

- Latency.
- Origin capacity.
- Failure isolation.
- Cost.
- Scalability.

However, do not cache content merely to increase the cache-hit ratio. Response correctness remains the primary requirement.

---

## Protect the Origin

The origin should not unnecessarily behave as a publicly exposed backend.

Where appropriate, configure the architecture so that traffic is expected to arrive through the intended edge path and use appropriate AWS security controls.

For S3 origins, use modern origin access controls rather than relying on a publicly readable bucket when private access is required.

For custom origins, evaluate:

- Security groups.
- Load balancer configuration.
- Origin authentication.
- WAF placement.
- Network exposure.
- Application-level authentication.

The exact control depends on the origin architecture.

---

## WAF Operational Practices

AWS WAF rules can protect CloudFront distributions against malicious traffic, but incorrect rules can also block legitimate users.

Use a controlled rollout strategy:

```text
New WAF Rule
    ↓
Observe / Count
    ↓
Review matches
    ↓
Tune exclusions
    ↓
Block
```

Avoid immediately deploying complex blocking rules without observing their effect.

Monitor:

- Blocked requests.
- Allowed requests.
- Rule match counts.
- False positives.
- Geographic patterns.
- URI patterns.
- Client behavior.

A WAF rule that blocks a large percentage of legitimate traffic is an availability incident, not simply a security success.

---

## TLS Best Practices

Production distributions should use:

- HTTPS.
- An appropriate ACM certificate.
- SNI-based certificate delivery where appropriate.
- A modern TLS security policy.
- HTTP-to-HTTPS redirection when HTTP is not intentionally supported.

The viewer path should generally be:

```text
HTTP
 ↓
CloudFront
 ↓
HTTPS redirect
 ↓
HTTPS
```

Do not treat TLS as merely a certificate installation task.

Operationally monitor:

- Certificate expiration.
- Certificate validation.
- Alternate domain names.
- TLS negotiation failures.
- Deployment changes affecting certificates.

Automated certificate management should be preferred where appropriate.

---

## Certificate Management

CloudFront has specific ACM certificate requirements that differ from certificates used by regional AWS resources.

Production certificate operations should include:

- Automated renewal where possible.
- Expiration monitoring.
- DNS validation.
- Correct alternate domain names.
- Controlled certificate replacement.

A certificate problem can produce a complete edge-level outage even when the application origin is perfectly healthy.

---

## DNS Operational Practices

CloudFront reliability depends on DNS configuration.

Typical production flow:

```text
example.com
    ↓
Route 53
    ↓
CloudFront Distribution
    ↓
Origin
```

Maintain:

- Correct aliases.
- Correct hosted zone configuration.
- Appropriate DNS TTLs.
- Controlled domain migrations.
- Certificate/domain alignment.

During migrations, lower DNS TTLs ahead of the planned cutover when appropriate, then restore them after stabilization.

Do not repeatedly change DNS during an incident without understanding resolver caching and propagation behavior.

---

## Logging Strategy

Use the logging mechanism appropriate to the operational question.

A practical model is:

```text
CloudFront Metrics
    ↓
Operational health

Standard Access Logs
    ↓
Historical request analysis

Real-Time Logs
    ↓
Low-latency request investigation

CloudWatch
    ↓
Dashboards + alarms

Application Logs
    ↓
Origin-level diagnosis
```

CloudFront logs and application logs answer different questions.

For example:

```text
CloudFront:
"Did the viewer receive a 503?"

Application:
"Why did the Django service return 503?"
```

Correlating both layers is essential during incidents.

---

## Monitoring and Alerting

Monitor user-facing outcomes rather than only infrastructure metrics.

Useful CloudFront signals include:

| Signal | Operational meaning |
|---|---|
| 4xx rate | Client or access failures |
| 5xx rate | Server-side failures |
| Requests | Traffic volume |
| Bytes downloaded | Delivery volume |
| Cache hit ratio | Cache effectiveness |
| Origin latency | Backend responsiveness |
| Origin request volume | Origin exposure |

Alerts should be based on meaningful thresholds and SLOs rather than every small metric fluctuation.

Avoid creating dozens of alarms that nobody responds to.

---

## Alert Quality

A production alert should answer:

1. What is broken?
2. How severe is it?
3. Who owns it?
4. What should be checked first?
5. Is immediate action required?

Weak alert:

```text
CloudFront metric exceeded threshold.
```

Better alert:

```text
Production CloudFront 5xx rate exceeded the availability threshold
for 5 consecutive minutes.

Check:
- CloudFront 5xx metrics
- Origin latency
- ALB target health
- Application logs
- Recent deployments
```

Operational alerts should reduce investigation time rather than simply report numbers.

---

## Dashboards

A CloudFront dashboard should provide enough information to understand the request path.

A practical dashboard can contain:

```text
Traffic
├── Request count
├── Bytes downloaded
└── Geographic distribution

Reliability
├── 4xx rate
├── 5xx rate
└── Origin errors

Performance
├── Cache hit ratio
├── Origin latency
└── Origin request count

Security
├── WAF blocked requests
└── WAF rule matches
```

Correlate CloudFront metrics with:

- ALB.
- ECS/EKS/EC2.
- Django/FastAPI.
- Redis.
- PostgreSQL.
- WAF.

This allows engineers to distinguish edge failures from origin failures.

---

## Performance Operations

CloudFront performance optimization should focus on reducing unnecessary origin work.

Key areas include:

- Cacheability.
- Cache-key cardinality.
- TTLs.
- Compression.
- Object size.
- Origin latency.
- Geographic placement.
- Connection behavior.

For static assets, use immutable versioned filenames:

```text
main.4f93b7.js
styles.8a21d4.css
logo.72a19c.svg
```

Then use long-lived caching.

This is generally safer than repeatedly invalidating the same object name.

---

## Cache Invalidation Discipline

Invalidations are useful, but they should not become the primary deployment strategy for every asset.

Poor deployment:

```text
Deploy
 ↓
Invalidate /*
 ↓
Every request becomes a cache miss
 ↓
Origin load spike
```

Better deployment:

```text
Build immutable assets
 ↓
Deploy new asset versions
 ↓
Reference new versions
 ↓
Allow old versions to expire naturally
```

Use targeted invalidations when necessary.

Avoid unnecessary wildcard invalidations because they can increase origin traffic and operational risk.

---

## Origin Capacity Planning

A high cache-hit ratio does not eliminate the need for origin capacity planning.

The origin must handle:

- Cache misses.
- Cache expiration.
- Cache invalidations.
- Traffic spikes.
- New content.
- Dynamic requests.

A simplified model is:

```text
Origin Requests
≈
Total Requests × (1 - Cache Hit Ratio)
+
Non-cacheable Requests
```

For example:

```text
10,000 requests/sec
Cache hit ratio = 90%

Approximate cache misses:
10,000 × 10%
= 1,000 requests/sec
```

The origin still needs to handle those requests safely.

---

## Traffic Spikes

Operational planning should account for sudden increases in:

- Requests.
- Object downloads.
- Cache misses.
- API traffic.
- WAF evaluations.

A common failure pattern is:

```text
Traffic spike
    ↓
Cache misses increase
    ↓
Origin traffic increases
    ↓
Application CPU increases
    ↓
Database connections increase
    ↓
Latency increases
    ↓
Timeouts
```

Use caching, autoscaling, rate limiting, queueing, and appropriate backend capacity to prevent this cascade.

---

## Deployment Best Practices

CloudFront changes should be compatible with application deployments.

For APIs, prefer backward-compatible changes.

For example:

```text
Old application:
GET /api/users
→ {"name": "Aranya"}

New application:
GET /api/users
→ {"name": "Aranya", "avatar_url": "..."}
```

Adding a response field is typically safer than immediately removing fields that existing clients depend on.

For static assets, immutable filenames reduce cache consistency problems.

---

## Rollback Strategy

Every production CloudFront change should have a known rollback path.

Examples:

```text
Cache policy change
→ Restore previous policy

Origin change
→ Restore previous origin

WAF rule
→ Disable/revert rule

TLS configuration
→ Restore previous certificate/policy

Application deployment
→ Roll back application version
```

Rollback procedures should be documented before a production incident occurs.

---

## Safe Rollouts

For high-risk changes:

1. Validate configuration.
2. Deploy to a non-production distribution.
3. Run automated tests.
4. Validate cache behavior.
5. Validate WAF behavior.
6. Validate TLS.
7. Deploy to production.
8. Monitor key metrics.
9. Roll back if predefined thresholds are breached.

Avoid relying solely on manual browser testing.

Test representative:

- URLs.
- HTTP methods.
- Headers.
- Query parameters.
- Cookies.
- Authentication states.
- Error responses.

---

## Testing Cache Behavior

A cache test should verify both cache correctness and cache efficiency.

Example:

```bash
curl -I https://example.com/assets/app.js
```

Inspect headers relevant to the deployment and caching configuration.

Run repeated requests:

```bash
curl -sSI https://example.com/assets/app.js
curl -sSI https://example.com/assets/app.js
```

For APIs, test different request contexts:

```text
GET /api/products
GET /api/products?category=books
GET /api/products?category=games
```

If query parameters affect the representation, verify that the cache policy handles them correctly.

---

## Incident Response Workflow

When CloudFront traffic behaves unexpectedly, use a layered diagnostic workflow.

```mermaid
flowchart TD
    Start[Incident detected] --> Metrics[Check CloudFront metrics]
    Metrics --> Errors{Errors elevated?}

    Errors -->|No| Latency[Check latency and cache behavior]
    Errors -->|Yes| WAF[Check WAF]
    
    WAF --> Origin[Check origin metrics]
    Origin --> Deploy[Check recent deployments]
    Deploy --> Config[Check CloudFront configuration]

    Latency --> Cache[Check cache hit ratio]
    Cache --> OriginTraffic[Check origin request volume]

    Config --> Recover[Apply controlled remediation]
    OriginTraffic --> Recover
    Recover --> Verify[Verify user-facing behavior]
```

Do not change multiple unrelated configuration components simultaneously during an incident.

That makes causal analysis much harder.

---

## Troubleshooting Priority

A practical order is:

| Priority | Check | Why |
|---|---|---|
| 1 | CloudFront 4xx/5xx | Establish impact |
| 2 | Recent changes | Identify likely cause |
| 3 | WAF | Detect accidental blocking |
| 4 | Cache behavior | Detect cache-related issues |
| 5 | Origin health | Identify backend failures |
| 6 | Origin latency | Identify degradation |
| 7 | DNS/TLS | Detect edge access problems |
| 8 | Application logs | Diagnose root cause |

This order is not absolute, but it prevents immediately diving into application logs when the failure may be at the edge.

---

## Operational Runbooks

Maintain runbooks for recurring incidents.

Recommended runbooks include:

- CloudFront 5xx spike.
- CloudFront 4xx spike.
- Low cache hit ratio.
- Origin overload.
- WAF false positives.
- TLS/certificate failure.
- Signed URL failure.
- Signed cookie failure.
- Origin failover.
- Unexpected cache behavior.
- High CloudFront cost.
- Deployment rollback.

Each runbook should contain:

```text
Symptoms
↓
Initial checks
↓
Relevant metrics
↓
Likely causes
↓
Safe remediation
↓
Validation
↓
Rollback
↓
Post-incident actions
```

---

## Operational Ownership

CloudFront often sits between several teams.

Typical ownership might be:

| Component | Primary owner |
|---|---|
| CloudFront | Platform / Infrastructure |
| WAF | Security / Platform |
| ALB | Platform |
| Django/FastAPI | Backend |
| PostgreSQL | Database / Platform |
| Redis | Platform / Backend |
| DNS | Platform |
| Application deployment | Backend / Platform |

Ownership boundaries should be explicit.

An incident should not stall because nobody knows who owns the CloudFront distribution or WAF rule.

---

## Security Best Practices

Production CloudFront environments should follow least-privilege principles.

Recommended practices include:

- Use HTTPS.
- Use appropriate TLS policies.
- Protect private S3 origins with origin access controls.
- Avoid exposing origins unnecessarily.
- Use AWS WAF where appropriate.
- Restrict administrative permissions.
- Protect signed URL/cookie private-key material.
- Avoid caching sensitive personalized responses.
- Review response headers.
- Log security-relevant activity.
- Monitor WAF false positives.

Never place private keys, signing secrets, or AWS credentials directly in frontend code.

---

## Secrets Management

CloudFront-related secrets should not be stored in:

```text
Source code
Frontend JavaScript
Git repository
Public configuration
```

Use appropriate secret-management mechanisms such as:

- AWS Secrets Manager.
- AWS Systems Manager Parameter Store.
- CI/CD secret stores.

For signed URLs or cookies, signing credentials must remain under controlled backend ownership.

A typical flow is:

```text
User
 ↓
Django / FastAPI
 ↓
Generate signed URL
 ↓
CloudFront
 ↓
Protected content
```

The viewer should receive only the authorization artifact required to access the content.

---

## Cost Management

Operational best practices should also consider cost.

CloudFront costs can be influenced by:

- Data transfer.
- Request volume.
- Cache effectiveness.
- Origin traffic.
- Logging.
- Real-time logging.
- Invalidations.
- WAF usage.
- Origin infrastructure.

Poor caching can therefore create a double cost:

```text
More CloudFront requests
+
More origin requests
+
More origin compute
+
More database load
```

Monitor both CloudFront cost and origin cost.

---

## Log Retention

Logs should be retained according to operational and compliance requirements.

Avoid indefinite retention without a business reason.

Consider:

- Incident investigation needs.
- Security requirements.
- Compliance requirements.
- Storage cost.
- Access controls.
- Data sensitivity.

Separate high-volume operational logs from long-term audit requirements when appropriate.

---

## Disaster Recovery

CloudFront configuration should be recoverable without manually reconstructing the distribution.

Maintain:

- Infrastructure as code.
- DNS configuration.
- ACM certificate configuration.
- WAF configuration.
- Cache policies.
- Origin configuration.
- Response header policies.
- Logging configuration.

Test recovery procedures periodically.

A backup of the application alone is insufficient if the edge configuration cannot be reproduced.

---

## Common Operational Mistakes

### Manual Console Changes

They create configuration drift and make recovery harder.

### Wildcard Cache Invalidation After Every Deployment

This can cause unnecessary origin load.

### Excessive Cache-Key Dimensions

This fragments the cache and increases origin traffic.

### Ignoring Personalized Content

Shared caching can expose incorrect or sensitive responses.

### Overly Broad WAF Rules

Legitimate traffic can be blocked.

### No Rollback Procedure

Engineers may improvise during incidents, increasing recovery time.

### Monitoring Only CloudFront

A healthy edge does not prove that the origin is healthy.

### No Origin Capacity Planning

Cache misses and traffic spikes can overwhelm the backend.

### Treating Metrics as the Entire Observability Strategy

Metrics indicate that something is wrong; logs and traces help explain why.

### Testing Only Through a Browser

Browser testing rarely covers all cache-key, header, cookie, method, and error combinations.

### Ignoring Configuration Drift

The infrastructure repository may no longer represent production reality.

---

## Production Checklist

### Configuration

- [ ] CloudFront configuration is managed as code
- [ ] Production changes require review
- [ ] Configuration drift is detected
- [ ] Environment-specific distributions are separated
- [ ] Cache policies are explicitly designed
- [ ] Origin request policies are intentional

### Security

- [ ] HTTPS is enforced where appropriate
- [ ] TLS configuration is production-ready
- [ ] Origin access is restricted
- [ ] WAF rules are reviewed
- [ ] Signed URL/cookie secrets are protected
- [ ] Personalized responses are not accidentally shared

### Performance

- [ ] Cache keys are minimized
- [ ] Static assets use immutable filenames
- [ ] TTLs reflect content semantics
- [ ] Compression is configured appropriately
- [ ] Origin capacity handles cache misses
- [ ] Invalidations are targeted

### Observability

- [ ] CloudFront metrics are monitored
- [ ] Origin metrics are correlated
- [ ] Access logs are available
- [ ] Relevant alerts exist
- [ ] Dashboards show user-facing health
- [ ] Incident runbooks exist

### Reliability

- [ ] Origin redundancy matches requirements
- [ ] Health checks are configured
- [ ] Failover is tested where applicable
- [ ] Timeouts are bounded
- [ ] Deployment rollback is documented
- [ ] RTO and RPO are defined where applicable

### Operations

- [ ] Ownership is documented
- [ ] Production changes are auditable
- [ ] Emergency changes are reconciled to source control
- [ ] Cost is monitored
- [ ] Log retention is intentional
- [ ] Disaster recovery is periodically tested

---

## Interview Traps

### Is CloudFront configuration-as-code necessary?

For production environments, it is strongly recommended because CloudFront configuration can materially affect security, availability, and application behavior.

### Is a high cache hit ratio always good?

No. A high hit ratio is useful only when cached responses are correct. Incorrectly caching personalized or dynamic content can create severe security and correctness problems.

### Should every deployment invalidate the entire distribution?

No. Immutable versioned assets are generally preferable for static resources. Invalidations should be targeted when necessary.

### Why separate cache policy from origin request policy?

Because cache identity and origin forwarding are different concerns. Data required by the origin does not necessarily need to distinguish cached objects.

### Why can WAF configuration become an availability problem?

An incorrectly configured blocking rule can reject legitimate traffic. Security controls must therefore be monitored and safely rolled out.

### Why is CloudFront monitoring insufficient by itself?

CloudFront can report a healthy edge while the application, ALB, database, or another origin dependency is failing. Effective observability must span the request path.

## Key Takeaways

- **Manage CloudFront as production infrastructure:** use infrastructure as code, peer review, automated validation, controlled deployment, and explicit rollback procedures.
- **Treat cache configuration as application behavior:** design cache keys carefully, protect personalized responses, and separate cache identity from origin request forwarding.
- **Operate security controls as reliability controls:** WAF, TLS, origin access, and signed URL/cookie configuration can directly affect user availability.
- **Observe the complete request path:** correlate CloudFront metrics and logs with WAF, ALB, Django/FastAPI, Redis, PostgreSQL, and deployment activity.
- **Optimize for operational safety, not just performance:** use immutable assets, targeted invalidations, origin capacity planning, documented runbooks, and tested disaster recovery procedures.