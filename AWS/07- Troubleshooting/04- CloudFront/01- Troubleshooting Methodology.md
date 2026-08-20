# 01- Troubleshooting Methodology

## Overview

CloudFront troubleshooting should be approached as a distributed-system investigation rather than as a single-service configuration problem. A request can pass through DNS, CloudFront, AWS WAF, the cache layer, an origin such as Amazon S3 or an Application Load Balancer, and finally backend components such as Nginx, Django, FastAPI, Redis, PostgreSQL, or downstream services.

The objective is not simply to find a configuration that looks suspicious. The objective is to identify **where the request stopped behaving as expected, why it behaved that way, and whether the failure is deterministic, intermittent, regional, or workload-dependent**.

A reliable troubleshooting process therefore follows the request path:

```text
Client
  │
  ▼
DNS
  │
  ▼
CloudFront Edge
  │
  ├── TLS
  ├── Viewer Request
  ├── AWS WAF
  ├── Cache Lookup
  │
  └── Origin Request
          │
          ▼
       Origin
          │
          ├── S3
          ├── ALB
          ├── Nginx
          └── Application
                  │
                  ├── Redis
                  ├── PostgreSQL
                  └── Downstream Services
```

The key operational principle is:

> **Troubleshoot from the outside inward, isolate the failing layer, then validate the hypothesis with evidence.**

## Why CloudFront Troubleshooting Is Different

CloudFront is distributed globally. A request may be served from an edge location without reaching the origin at all. This means an application engineer cannot assume that an origin log entry exists for every failed request.

For example, consider:

```text
Client
  │
  ▼
CloudFront
  │
  ├── Cache HIT ───────────────► Response
  │
  └── Cache MISS
          │
          ▼
        WAF
          │
          ▼
        Origin
```

If the response is a cache hit, the request may never reach Django or FastAPI. If AWS WAF blocks the request, the origin may never see it. If TLS negotiation fails, the application receives nothing.

This creates an important troubleshooting rule:

**Absence of an origin log does not prove that the application is healthy or that CloudFront is not receiving the request.**

## Troubleshooting Methodology

A production investigation should follow a consistent sequence:

```mermaid
flowchart TD
    A[User reports failure] --> B[Define exact symptom]
    B --> C[Reproduce request]
    C --> D[Identify affected URL and region]
    D --> E[Check DNS]
    E --> F[Check TLS]
    F --> G[Inspect CloudFront response]
    G --> H[Determine cache HIT/MISS]
    H --> I[Check WAF]
    I --> J[Check origin connectivity]
    J --> K[Inspect origin logs]
    K --> L[Inspect application dependencies]
    L --> M[Form hypothesis]
    M --> N[Make smallest safe change]
    N --> O[Verify behavior]
    O --> P[Monitor recovery]
```

Do not skip directly from a symptom to a configuration change.

## Define the Symptom Precisely

Start by converting a vague report such as:

> "CloudFront is down."

into an observable failure:

```text
URL:
https://api.example.com/v1/orders

HTTP method:
GET

Expected:
200 OK

Observed:
502 Bad Gateway

Affected users:
Unknown

Affected regions:
Possibly Europe

Started:
14:32 UTC

Frequency:
Intermittent

Origin:
Application Load Balancer

Recent changes:
CloudFront configuration deployed at 14:20 UTC
```

The distinction between these symptoms is critical:

| Symptom | Likely investigation areas |
|---|---|
| DNS resolution failure | Route 53, DNS records, resolver |
| TLS handshake failure | Certificate, hostname, TLS policy |
| `403` | WAF, CloudFront behavior, origin authorization |
| `404` | Cache behavior, origin path, application routing |
| `502` | Origin connectivity, TLS to origin, origin response |
| `503` | Origin availability, capacity, application health |
| `504` | Origin timeout, slow backend, network path |
| Stale content | Cache policy, TTL, invalidation |
| Works at origin but not CloudFront | CloudFront behavior, WAF, cache, headers, TLS |
| Works for one region but not another | Edge behavior, DNS, regional origin/network issue |

## Establish a Baseline

Before changing anything, establish what currently works.

Test the public CloudFront endpoint:

```bash
curl -I https://d123example.cloudfront.net/
```

Test the production hostname:

```bash
curl -I https://api.example.com/
```

Capture the complete response when headers are relevant:

```bash
curl -sv https://api.example.com/health
```

For APIs, test a representative endpoint:

```bash
curl -sv \
  -H 'Accept: application/json' \
  https://api.example.com/v1/health
```

The purpose is to collect evidence such as:

- HTTP status
- Response headers
- TLS behavior
- Redirects
- Cache status
- Request identifiers
- Response latency
- Whether the origin appears to have been contacted

## Check DNS First

DNS determines whether clients are reaching the intended CloudFront distribution.

Inspect the hostname:

```bash
dig api.example.com
```

For a concise answer:

```bash
dig +short api.example.com
```

Inspect the authoritative chain:

```bash
dig api.example.com +trace
```

Check the CNAME:

```bash
dig api.example.com CNAME
```

For CloudFront custom domains, verify that the hostname resolves toward the expected CloudFront distribution.

A DNS problem can produce a failure that looks like an application outage even though CloudFront itself is healthy.

### DNS Troubleshooting Questions

Ask:

- Does the hostname resolve?
- Is the expected CNAME present?
- Was the DNS record recently changed?
- Are multiple DNS records involved?
- Is DNS weighted or latency-based?
- Does the failure occur from multiple networks?
- Is the resolver returning stale or unexpected data?

Do not modify CloudFront configuration when the actual failure is DNS routing.

## Check TLS

TLS failures occur before HTTP processing.

Inspect the certificate presented by the endpoint:

```bash
openssl s_client \
  -connect api.example.com:443 \
  -servername api.example.com
```

Look for:

- Certificate subject
- Subject Alternative Names
- Certificate chain
- Expiration
- TLS version
- Negotiated cipher
- Certificate verification errors

Test the HTTPS endpoint directly:

```bash
curl -Iv https://api.example.com/
```

Common CloudFront TLS issues include:

- Custom hostname not associated with the distribution
- Certificate does not cover the requested hostname
- Incorrect ACM certificate
- Certificate deployed in an unsupported region for CloudFront
- Incompatible TLS settings
- Incorrect DNS-to-distribution mapping

## Determine Whether CloudFront Is Reaching the Origin

This is one of the most important troubleshooting distinctions.

A request can fail:

```text
Before origin
```

or:

```text
At origin
```

or:

```text
After origin response
```

Conceptually:

```mermaid
sequenceDiagram
    participant C as Client
    participant CF as CloudFront
    participant W as AWS WAF
    participant O as Origin

    C->>CF: HTTPS request
    CF->>W: Evaluate request
    W-->>CF: Allow / Block

    alt Blocked
        CF-->>C: 403
    else Allowed
        CF->>CF: Cache lookup
        alt Cache HIT
            CF-->>C: Cached response
        else Cache MISS
            CF->>O: Origin request
            O-->>CF: Origin response
            CF-->>C: Response
        end
    end
```

If there is no origin request, investigate:

- DNS
- TLS
- CloudFront behavior
- WAF
- Cache behavior
- Viewer request processing
- Origin selection

If the origin receives the request, investigate:

- Origin connectivity
- Origin TLS
- ALB
- Nginx
- Application
- Database
- Redis
- Downstream dependencies

## Inspect the CloudFront Distribution

Start with:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID"
```

For the configuration:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID"
```

Useful fields include:

| Configuration | Why it matters |
|---|---|
| `Enabled` | Determines whether distribution is active |
| `Status` | Shows deployment state |
| `DomainName` | Confirms CloudFront endpoint |
| `Origins` | Determines where requests are sent |
| `DefaultCacheBehavior` | Controls default request processing |
| `CacheBehaviors` | Controls path-specific behavior |
| `ViewerCertificate` | Controls viewer TLS |
| `WebACLId` | Shows WAF association |
| `DefaultRootObject` | Affects root-path behavior |
| `PriceClass` | Affects edge-location coverage and cost |
| `HttpVersion` | Controls supported HTTP protocol behavior |

Use JMESPath queries to avoid scanning large JSON responses:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.{Id:Id,Domain:DomainName,Status:Status,Enabled:DistributionConfig.Enabled}' \
  --output table
```

## Check Distribution Deployment State

CloudFront configuration changes are asynchronous.

Inspect status:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.Status'
```

A distribution can be:

```text
InProgress
```

after a configuration update and later transition to:

```text
Deployed
```

Do not assume that the API returning successfully means every edge location has already adopted the configuration.

For scripted operations, wait for the relevant deployment state rather than immediately running production verification.

## Cache Troubleshooting

Cache behavior is a frequent source of confusion.

A request can produce:

```text
Cache HIT
Cache MISS
Cache ERROR
```

and the application may behave differently depending on which path occurs.

Inspect response headers:

```bash
curl -sS -D - -o /dev/null https://api.example.com/resource
```

Useful headers can include:

- `Age`
- `Cache-Control`
- `ETag`
- `Last-Modified`
- CloudFront-specific cache/status headers
- Request identifiers

The exact headers exposed depend on the CloudFront configuration and response behavior.

### Typical Cache Problems

#### Unexpected stale content

Possible causes:

- TTL is longer than expected
- Cache-Control headers are incorrect
- Cache policy allows caching
- Content was changed without cache invalidation
- Cache key does not vary on an input that changes the response

#### Dynamic API response is cached

Possible causes:

- Incorrect cache policy
- Incorrect path behavior
- HTTP methods or query strings are not handled as intended
- Authorization-related request data is not included in the cache key or forwarding policy

For authenticated APIs, carefully evaluate whether a response is cacheable at all.

## Cache Key Investigation

A senior-level CloudFront investigation should ask:

> **What makes two requests equivalent from the cache's perspective?**

Depending on the behavior, this can involve:

- Path
- Query strings
- Headers
- Cookies

For example:

```text
GET /products?id=10
GET /products?id=20
```

must not accidentally share a cache entry if the query parameter determines the response and the cache policy does not distinguish the requests appropriately.

Similarly:

```text
Authorization: Bearer token-A
Authorization: Bearer token-B
```

must not cause user-specific responses to be shared through an incorrectly configured cache.

## AWS WAF Troubleshooting

A CloudFront request can be rejected by AWS WAF before it reaches the origin.

Check the distribution's WAF association:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.DistributionConfig.WebACLId'
```

If WAF is involved, inspect its configuration and logging/metrics.

A `403` therefore does not automatically mean:

```text
Application returned 403
```

It may instead mean:

```text
CloudFront or WAF rejected the request
```

Useful investigation questions:

- Is a Web ACL attached?
- Which rule matched?
- Is rate limiting triggered?
- Is a managed rule blocking the request?
- Is a geographic restriction involved?
- Is the request missing a required header?
- Is a bot-control or reputation rule involved?

## Origin Troubleshooting

When CloudFront reaches the origin, test the origin independently where the architecture allows it.

For an ALB-backed application, for example:

```bash
curl -sv https://origin.example.internal/health
```

Use an origin-specific hostname or endpoint only when it is appropriate and accessible from the troubleshooting environment.

The goal is to separate:

```text
CloudFront → Origin
```

from:

```text
Origin → Application
```

If the origin fails independently, changing CloudFront configuration is unlikely to solve the underlying issue.

## Application-Level Troubleshooting

For Django or FastAPI applications, inspect application logs and correlate them with the request.

A useful request path is:

```text
CloudFront request
      │
      ▼
ALB
      │
      ▼
Nginx / Ingress
      │
      ▼
Django / FastAPI
      │
      ├── Redis
      ├── PostgreSQL
      └── External service
```

If the request reaches Django or FastAPI but fails there, CloudFront may simply be exposing an application failure.

Investigate:

- Application exceptions
- Database connection exhaustion
- Slow PostgreSQL queries
- Redis failures
- Connection pool exhaustion
- External API latency
- Worker saturation
- CPU or memory pressure

## HTTP Status Code Investigation

Use status codes as clues, not conclusions.

| Status | Typical CloudFront investigation |
|---|---|
| `200` | Verify whether content is correct and fresh |
| `301` / `302` | Redirect configuration, origin behavior, HTTPS enforcement |
| `400` | Request validation, malformed request, application behavior |
| `401` | Authentication behavior |
| `403` | WAF, CloudFront restrictions, origin authorization, application |
| `404` | Path mapping, cache behavior, origin routing |
| `405` | Allowed methods and origin/application routing |
| `429` | Rate limiting at WAF, API gateway, application, or origin |
| `500` | Origin/application failure |
| `502` | Origin connectivity or invalid origin response |
| `503` | Origin availability or capacity |
| `504` | Origin timeout or slow backend |

The same status code can have different causes depending on where it was generated.

## Regional Troubleshooting

CloudFront is globally distributed, so a regional symptom deserves separate investigation.

Ask:

- Is the problem global?
- Is it limited to one geography?
- Does it occur from one ISP?
- Does it occur from one corporate network?
- Is DNS behavior different?
- Does the same URL work through another network?
- Does the origin itself work independently?

A useful test matrix is:

| Test | Region / Network | Result |
|---|---|---|
| CloudFront hostname | India | `200` |
| CloudFront hostname | Europe | `502` |
| Origin endpoint | India | `200` |
| Origin endpoint | Europe | `200` |

This suggests the problem may be between the European client path and CloudFront rather than inside the application.

Do not infer a regional CloudFront problem solely from a single user's report.

## Compare CloudFront With the Origin

One of the most useful troubleshooting techniques is to compare:

```text
Public CloudFront endpoint
vs.
Origin endpoint
```

For example:

```bash
curl -sv https://api.example.com/health
```

and, where safe:

```bash
curl -sv https://origin.example.internal/health
```

Interpretation:

| CloudFront | Origin | Likely direction |
|---|---|---|
| Fails | Works | CloudFront/WAF/TLS/cache/origin connection |
| Works | Fails | Origin/application problem |
| Fails | Fails | Origin or broader infrastructure problem |
| Works | Works | Investigate request-specific behavior |

This is not absolute proof because CloudFront and direct-origin requests can differ in headers, TLS, routing, authentication, and caching.

## Correlation and Request IDs

Distributed systems require correlation.

Preserve relevant identifiers from:

- Client
- CloudFront
- ALB
- Nginx
- Application
- Downstream services

For example:

```text
Client request
    │
    ├── Request ID
    ▼
CloudFront
    │
    ├── Request ID
    ▼
ALB
    │
    ├── Trace ID
    ▼
Django/FastAPI
    │
    ├── Trace ID
    ▼
PostgreSQL / Redis / downstream service
```

If request identifiers are not preserved across layers, incident investigation becomes substantially harder.

## CloudWatch Investigation

CloudWatch should be used to correlate CloudFront symptoms with infrastructure behavior.

Relevant signals can include:

- Request count
- Error rates
- Cache hit ratio
- Origin latency
- HTTP status distributions
- WAF metrics
- ALB target health
- Application CPU and memory
- Database metrics
- Redis metrics

The important principle is correlation.

For example:

```text
14:20  CloudFront deployment
14:25  Origin latency increases
14:27  5xx rate increases
14:28  ALB target failures increase
14:30  Application database connections exhausted
```

This is much stronger evidence than observing a single `502` response.

## Log and Metric Limitations

Do not expect every CloudFront troubleshooting question to be answered by one data source.

| Source | Strength | Limitation |
|---|---|---|
| `curl` | Real client behavior | Single request perspective |
| CloudFront configuration | Desired configuration | Does not prove runtime behavior |
| CloudFront metrics | Aggregate behavior | Limited request-level detail |
| WAF metrics/logs | Security decisions | Only covers WAF processing |
| Origin logs | Application-side evidence | Misses requests stopped before origin |
| ALB logs | Load-balancer traffic | Does not explain CloudFront-side failures |
| Application logs | Application behavior | Only sees requests that reach application |
| CloudWatch | Correlation and trends | Requires correct metrics/logging |

Senior troubleshooting combines these sources rather than trusting one source.

## Configuration Diffing

When an incident follows a configuration change, compare the current state with the previous known-good state.

Retrieve the current configuration:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  > current-cloudfront.json
```

Use `jq` to inspect selected sections:

```bash
jq '.DistributionConfig.Origins' current-cloudfront.json
```

Inspect cache behaviors:

```bash
jq '.DistributionConfig.DefaultCacheBehavior' current-cloudfront.json
```

The objective is to answer:

> What changed between the last known-good state and the failing state?

Do not assume the most recent change is the cause, but prioritize it as a hypothesis.

## Safe Change Strategy

During an incident, make the smallest change that tests the hypothesis.

Bad approach:

```text
Multiple CloudFront behaviors changed
+ WAF rules modified
+ origin changed
+ cache invalidated
```

If the issue disappears, the root cause remains unclear.

Better approach:

```text
Hypothesis:
A newly introduced cache policy is caching authenticated responses.

Test:
Modify only the affected behavior.

Verify:
Repeat the same request.

Observe:
Check response behavior and origin traffic.

Decision:
Keep, revert, or continue investigation.
```

Small changes preserve causality.

## Troubleshooting Decision Tree

```mermaid
flowchart TD
    A[Request fails] --> B{DNS resolves?}
    B -->|No| C[Investigate DNS]
    B -->|Yes| D{TLS succeeds?}
    D -->|No| E[Investigate certificate/TLS]
    D -->|Yes| F{CloudFront returns response?}
    F -->|No| G[Inspect edge/network behavior]
    F -->|Yes| H{HTTP status expected?}
    H -->|403| I[Inspect WAF/restrictions/origin authorization]
    H -->|4xx| J[Inspect cache behavior/request/origin]
    H -->|5xx| K{Origin received request?}
    H -->|Yes| L[Inspect content/cache semantics]
    K -->|No| M[Inspect CloudFront/WAF/origin connectivity]
    K -->|Yes| N[Inspect ALB/Nginx/application]
    N --> O{Application dependency healthy?}
    O -->|No| P[Investigate Redis/PostgreSQL/downstream]
    O -->|Yes| Q[Compare request-specific behavior]
```

## Common CloudFront Failure Patterns

### `403` Immediately After Deployment

Possible causes:

- WAF rule blocks the new request pattern
- Origin access policy is incorrect
- S3 origin permissions changed
- CloudFront behavior changed
- Geo restriction blocks the client
- Signed URL or cookie validation fails

Investigation:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.DistributionConfig.{WebACL:WebACLId,Origins:Origins.Items[*].{Id:Id,Domain:DomainName}}'
```

Then inspect WAF and origin authorization separately.

### `502` From CloudFront

Investigate:

1. Origin hostname.
2. Origin protocol policy.
3. Origin TLS.
4. DNS resolution from the origin perspective.
5. ALB or origin health.
6. Origin security groups and network controls.
7. Application availability.
8. Origin response validity.

A `502` is not sufficient evidence that Django or FastAPI returned a `502`.

### `504` During Traffic Spikes

Investigate:

- Origin latency
- ALB target response time
- Application worker saturation
- Database connection pools
- PostgreSQL latency
- Redis latency
- External API calls
- Application timeouts

A CloudFront timeout may be the final symptom of latency introduced several layers deeper.

### Stale API Data

Investigate:

- Cache policy
- TTL
- `Cache-Control`
- Query-string handling
- Header handling
- Cookie handling
- Cache key
- Invalidation behavior

Do not solve every stale-content problem with a global invalidation. First determine why the content became stale.

## Common Mistakes

### Treating CloudFront as the Origin

CloudFront is an edge distribution layer. It does not replace the application.

Avoid assuming:

```text
CloudFront error = CloudFront configuration error
```

Instead investigate the complete request path.

### Changing Configuration Without Capturing State

A production incident becomes harder to recover from when the previous configuration is unknown.

Capture the current state before changing it:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  > before-change.json
```

### Assuming a `403` Came From the Application

A `403` can be generated by:

- CloudFront
- AWS WAF
- Origin
- Application

Identify the layer before changing application authentication.

### Ignoring Caching

Developers often test an application directly and conclude that CloudFront should behave identically.

It may not.

CloudFront can return a cached response without contacting the application.

### Ignoring Asynchronous Deployment

CloudFront configuration changes propagate asynchronously. Immediately testing one edge location does not necessarily prove global deployment.

### Invalidating Everything

This:

```text
/*
```

can be operationally expensive and often hides the actual caching design problem.

Prefer targeted invalidation or, for frequently deployed assets, versioned filenames.

### Testing Only From One Network

A global CDN should be investigated globally when the symptom suggests geographic or ISP-specific behavior.

### Making Too Many Changes at Once

Multiple simultaneous changes destroy causal evidence and make rollback harder.

## Production Troubleshooting Checklist

### Initial Assessment

- [ ] Record exact URL
- [ ] Record HTTP method
- [ ] Record expected and actual status
- [ ] Record timestamp in UTC
- [ ] Determine whether issue is intermittent
- [ ] Determine affected regions/networks
- [ ] Check recent deployments and configuration changes

### Network and Edge

- [ ] Verify DNS
- [ ] Verify TLS
- [ ] Test CloudFront hostname
- [ ] Test production hostname
- [ ] Inspect response headers
- [ ] Determine cache behavior
- [ ] Check WAF
- [ ] Check geo restrictions where applicable

### CloudFront

- [ ] Confirm distribution ID
- [ ] Check distribution status
- [ ] Inspect origin configuration
- [ ] Inspect cache behaviors
- [ ] Inspect viewer certificate
- [ ] Inspect Web ACL association
- [ ] Check recent configuration changes

### Origin

- [ ] Test origin independently where possible
- [ ] Check ALB health
- [ ] Check Nginx/Ingress
- [ ] Check application logs
- [ ] Check application resource usage
- [ ] Check Redis
- [ ] Check PostgreSQL
- [ ] Check downstream dependencies

### Recovery

- [ ] Form a specific hypothesis
- [ ] Make the smallest safe change
- [ ] Wait for propagation where applicable
- [ ] Reproduce the original request
- [ ] Verify from multiple locations when necessary
- [ ] Monitor metrics after recovery
- [ ] Record the root cause and corrective action

## Interview Perspective

CloudFront troubleshooting questions often test whether an engineer understands distributed request paths rather than whether they memorized AWS commands.

A strong explanation should distinguish:

```text
DNS
  ↓
TLS
  ↓
CloudFront
  ↓
WAF
  ↓
Cache
  ↓
Origin
  ↓
Application
  ↓
Dependencies
```

For example, if asked:

> "CloudFront returns 502. What do you check?"

A production-oriented answer should include:

1. Confirm the exact request and reproduce it.
2. Check whether the distribution is deployed.
3. Inspect the origin configuration.
4. Determine whether the origin receives the request.
5. Validate origin DNS and TLS behavior.
6. Check ALB/origin health.
7. Inspect Nginx and application logs.
8. Check application dependencies and latency.
9. Compare direct-origin behavior with CloudFront behavior.
10. Form and test a specific hypothesis before changing production configuration.

The important distinction is between **symptom**, **location of failure**, and **root cause**.

## Key Takeaways

- **Troubleshoot the request path layer by layer:** DNS, TLS, CloudFront, WAF, cache, origin, application, and dependencies.
- **Use evidence to identify the failing layer:** a CloudFront status code alone does not identify where the error originated.
- **Separate edge behavior from origin behavior:** determine whether the request was served from cache, blocked at the edge, or forwarded to the origin.
- **Make small, hypothesis-driven changes:** preserve configuration state and avoid multiple simultaneous production changes.
- **Correlate metrics, logs, and request behavior:** reliable CloudFront troubleshooting requires evidence across the entire distributed system.