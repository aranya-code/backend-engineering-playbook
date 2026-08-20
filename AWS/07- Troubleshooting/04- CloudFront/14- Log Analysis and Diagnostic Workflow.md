# 14- Log Analysis and Diagnostic Workflow

## Overview

CloudFront troubleshooting is fundamentally an observability problem. A production incident rarely provides enough information through the browser response or a single HTTP status code. Effective diagnosis requires correlating request behavior across CloudFront, AWS WAF, the origin, and the application.

A useful diagnostic model is:

```text
Client
  │
  ▼
DNS
  │
  ▼
CloudFront
  │
  ├── WAF
  ├── Cache behavior
  ├── Viewer protocol
  ├── Access controls
  └── Cache
  │
  ▼
Origin
  │
  ├── S3
  ├── ALB
  ├── Nginx
  ├── Kubernetes
  └── Django / FastAPI
```

The goal is not simply to find an error message. The goal is to establish:

1. What request was made?
2. Which CloudFront distribution and behavior handled it?
3. Was the request served from cache or forwarded to the origin?
4. Did AWS WAF allow or block it?
5. Did CloudFront successfully communicate with the origin?
6. What did the origin return?
7. Where did latency or failure begin?
8. What configuration or deployment change correlates with the incident?

This workflow becomes especially important for:

- `403` access-control failures
- `404` missing-resource failures
- `502` origin failures
- `503` service-unavailable conditions
- `504` origin timeouts
- High latency
- Low cache-hit ratios
- Unexpected origin traffic
- WAF false positives
- Signed URL and signed-cookie failures

## Diagnostic Philosophy

The most reliable approach is **request-path reconstruction**.

Do not begin with:

> "CloudFront is returning 5xx, so the CloudFront configuration must be broken."

Instead ask:

> "At which layer did the request first diverge from the expected request path?"

For example:

```text
Expected:

Client
  ↓
CloudFront
  ↓
WAF → Allow
  ↓
Cache Hit
  ↓
Response


Observed:

Client
  ↓
CloudFront
  ↓
WAF → Allow
  ↓
Cache Miss
  ↓
ALB
  ↓
Nginx
  ↓
Django
  ↓
PostgreSQL timeout
  ↓
504
```

The final HTTP response is only the visible symptom.

## Request Correlation

A diagnostic workflow becomes much easier when every investigation begins with a precise request.

Capture at minimum:

| Field | Why it matters |
|---|---|
| Timestamp | Correlates events across services |
| Hostname | Identifies distribution/application |
| URI | Identifies resource and behavior |
| HTTP method | Determines request handling |
| Query string | May affect cache and authorization |
| Client IP | Useful for WAF and rate-limit analysis |
| User-Agent | Helps distinguish clients |
| HTTP status | Identifies broad failure class |
| Response headers | May reveal CloudFront behavior |
| Request ID | Helps correlate logs where available |

For incident response, avoid investigating with only:

```text
"It returns 503."
```

Use:

```text
2026-08-20T14:32:15Z
GET
https://cdn.example.com/api/orders?page=2
client=203.0.113.10
status=503
```

That gives the investigation a concrete event to follow.

## Diagnostic Workflow

A production CloudFront investigation should generally follow this sequence:

```mermaid
flowchart TD
    A[Capture Exact Request] --> B[Reproduce]
    B --> C[Inspect Response Headers]
    C --> D[Identify CloudFront Distribution]
    D --> E[Check WAF]
    E --> F[Determine Cache Hit or Miss]
    F --> G[Check Origin Request]
    G --> H[Inspect Origin Logs]
    H --> I[Correlate Application Metrics]
    I --> J[Check Recent Configuration Changes]
    J --> K[Form Root Cause]
    K --> L[Validate Fix]
```

The exact order may vary by incident, but each stage should produce evidence for the next.

## Start With the Client Request

Use `curl` to remove browser-specific behavior from the initial investigation.

```bash
curl -v \
  --connect-timeout 10 \
  --max-time 30 \
  "https://cdn.example.com/api/orders"
```

For headers only:

```bash
curl -I \
  "https://cdn.example.com/api/orders"
```

For timing information:

```bash
curl -sS -o /dev/null \
  -w 'status=%{http_code} total=%{time_total}s connect=%{time_connect}s starttransfer=%{time_starttransfer}s\n' \
  "https://cdn.example.com/api/orders"
```

This provides a fast way to distinguish:

- Connection problems
- TLS problems
- Slow origin responses
- Fast failures
- Different response statuses

## Inspect Response Headers

CloudFront response headers can provide useful diagnostic signals.

For example:

```bash
curl -sSI "https://cdn.example.com/assets/app.js"
```

Inspect:

```text
HTTP status
Age
Via
X-Cache
X-Amz-Cf-Id
X-Amz-Cf-Pop
```

Header availability can vary by configuration and response path, so treat individual headers as diagnostic signals rather than guaranteed fields.

## `X-Cache`

`X-Cache` can indicate whether CloudFront served the request from cache or forwarded it to the origin.

Typical values include patterns such as:

```text
Hit from cloudfront
Miss from cloudfront
Error from cloudfront
```

Interpret the value together with the status code and other evidence.

For example:

```text
X-Cache: Hit from cloudfront
```

suggests that the response was served from CloudFront cache.

Whereas:

```text
X-Cache: Miss from cloudfront
```

indicates that CloudFront needed to obtain the response rather than satisfying it from an existing cached object.

Do not treat a cache miss as an error. Dynamic APIs commonly produce misses by design.

## CloudFront Request IDs

CloudFront may return identifiers such as:

```text
X-Amz-Cf-Id
```

Capture these values during investigations.

Example:

```bash
curl -sSI "https://cdn.example.com/api/orders"
```

Then inspect:

```text
X-Amz-Cf-Id: <request-id>
```

Use the request timestamp and available identifiers when correlating CloudFront, WAF, and origin telemetry.

## CloudFront Distribution Inspection

When diagnosing a distribution, inspect its configuration through the AWS CLI.

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID"
```

For configuration-focused output:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID"
```

Useful configuration areas include:

- Origins
- Default cache behavior
- Ordered cache behaviors
- Viewer certificate
- Allowed methods
- Compress configuration
- WAF association
- Restrictions
- Cache policies
- Origin request policies
- Response headers policies

## Inspect Origins

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" |
jq '.DistributionConfig.Origins'
```

Verify:

- Origin hostname
- Origin protocol
- Origin ID
- Origin access configuration
- Custom headers
- Connection settings

A common operational mistake is debugging the application while CloudFront is pointing at an unexpected origin.

## Inspect Cache Behaviors

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" |
jq '.DistributionConfig.DefaultCacheBehavior,
    .DistributionConfig.CacheBehaviors'
```

Check whether the requested path matches the intended behavior.

For example:

```text
/api/*
    → API origin

/static/*
    → S3 origin

/images/*
    → S3 origin
```

A path-pattern mistake can route requests to the wrong backend.

## Cache Hit Versus Origin Request

The cache state changes the entire troubleshooting path.

```mermaid
sequenceDiagram
    participant C as Client
    participant CF as CloudFront
    participant O as Origin

    C->>CF: GET /asset.js
    CF->>CF: Lookup cache key

    alt Cache Hit
        CF-->>C: Cached response
    else Cache Miss
        CF->>O: Origin request
        O-->>CF: Response
        CF->>CF: Cache eligible response
        CF-->>C: Response
    end
```

If a request is served from cache, the current origin may not be involved at all.

This matters during incidents.

A backend deployment can be healthy while CloudFront continues serving an older cached response.

Conversely, an invalidation or cache-policy change can suddenly increase origin traffic.

## Cache Key Investigation

When investigating unexpected cache behavior, inspect:

- Path
- Query strings
- Headers
- Cookies
- Cache policy
- Origin request policy
- Compression variants
- Authorization-related request behavior

A cache key that varies unnecessarily can reduce cache efficiency.

For example:

```text
/api/product?id=123
/api/product?id=123&utm_source=email
/api/product?id=123&utm_source=google
```

If irrelevant query parameters participate in the cache key, logically identical content may produce multiple cache entries.

## CloudFront Logs

CloudFront provides logging capabilities that can be used for detailed request analysis.

Depending on the configured logging mechanism, useful fields can include:

- Timestamp
- Edge location
- Client IP
- HTTP method
- Host
- URI
- Status
- Referer
- User-Agent
- Query string
- Result type
- Request ID
- Bytes sent
- Time taken

The exact fields depend on the logging configuration and log format.

## Standard Versus Real-Time Logs

CloudFront logging mechanisms serve different operational purposes.

| Capability | Standard logging | Real-time logging |
|---|---|---|
| Primary purpose | Historical analysis | Near-real-time diagnosis |
| Operational overhead | Lower | Higher |
| Latency | Not immediate | Near-real-time |
| Cost | Lower | Higher |
| Incident investigation | Useful | Very useful |
| High-volume analytics | Suitable | Selectively useful |

Do not enable the most expensive logging option for every request without an operational reason.

Use the level of telemetry appropriate to the workload and incident.

## Log Result Types

CloudFront logs can expose result-type information that helps distinguish cache and origin behavior.

Conceptually:

```text
Request
  │
  ├── Hit
  ├── Miss
  ├── RefreshHit
  └── Error
```

The exact values and meanings depend on the CloudFront logging format being used.

When analyzing logs, correlate:

```text
status
+
result type
+
origin behavior
+
latency
```

rather than interpreting one field in isolation.

## AWS WAF Logs

If WAF is attached to CloudFront, WAF logs are critical for diagnosing access-control problems.

Investigate:

- Action
- Rule ID
- Rule group
- Client IP
- URI
- HTTP method
- Headers
- Query parameters
- Labels
- Timestamp

A request blocked by WAF should generally not be investigated as an origin failure.

## WAF Query Example

If WAF logs are delivered to CloudWatch Logs, you can use CloudWatch Logs Insights to search for blocked traffic.

```sql
fields @timestamp, action, httpRequest.clientIp,
       httpRequest.httpMethod,
       httpRequest.uri,
       terminatingRuleId
| filter action = "BLOCK"
| sort @timestamp desc
| limit 100
```

Field names can differ depending on the exact WAF log structure and query environment. Validate them against the actual log schema before operational use.

## Searching for a Specific URI

A focused investigation is usually better than scanning an entire log stream.

```sql
fields @timestamp,
       httpRequest.clientIp,
       httpRequest.httpMethod,
       httpRequest.uri,
       action,
       terminatingRuleId
| filter httpRequest.uri like /api\/orders/
| sort @timestamp desc
| limit 100
```

When investigating a production incident, narrow the query by:

- Time range
- URI
- Client IP
- Action
- Rule
- Request characteristics

This reduces noise and query cost.

## CloudWatch Logs Insights Workflow

A practical workflow is:

```text
Incident timestamp
      │
      ▼
Choose narrow time window
      │
      ▼
Filter URI / status / client
      │
      ▼
Inspect representative requests
      │
      ▼
Identify common pattern
      │
      ▼
Correlate with WAF / origin
```

Start narrow and expand only when necessary.

## Origin Logs

Once evidence indicates that CloudFront forwarded the request, inspect the origin.

For an Nginx-based origin:

```bash
sudo tail -f /var/log/nginx/access.log
```

For errors:

```bash
sudo tail -f /var/log/nginx/error.log
```

For a containerized application:

```bash
docker logs --tail 200 <container>
```

For Kubernetes:

```bash
kubectl logs \
  deployment/backend \
  --tail=200 \
  -n production
```

The exact command depends on the deployment platform.

## Nginx Log Correlation

A useful Nginx access log should contain enough information to correlate requests.

For example:

```text
timestamp
remote_addr
request
status
request_time
upstream_status
upstream_response_time
request_id
```

A useful pattern is:

```text
CloudFront request
      │
      ▼
Nginx request
      │
      ▼
Application request
```

If CloudFront shows a request but Nginx has no corresponding entry, investigate whether the request was actually forwarded to the origin.

## Application Logs

For Django or FastAPI, application logs should provide enough context to distinguish:

- Authentication failures
- Authorization failures
- Validation failures
- Database latency
- External API latency
- Application exceptions

For example:

```text
request_id=abc123
route=/api/orders
status=500
duration_ms=1842
```

Do not log credentials, tokens, signed URLs, session cookies, or other sensitive information merely to improve troubleshooting.

## Request IDs Across Services

A mature backend architecture propagates a request correlation identifier:

```text
Client
  │
  │ request ID
  ▼
CloudFront
  │
  ▼
ALB
  │
  ▼
Nginx
  │
  ▼
Django/FastAPI
  │
  ▼
PostgreSQL / Redis / external service
```

The identifier should allow operators to connect events without exposing sensitive information.

Where CloudFront-generated identifiers cannot be directly propagated to the application, use an application-level correlation ID at a trusted downstream boundary.

## Latency Decomposition

Total request latency should be decomposed rather than treated as one number.

Conceptually:

```text
Total latency
=
DNS
+
TCP/TLS
+
CloudFront processing
+
cache lookup
+
origin connection
+
origin processing
+
response transfer
```

For cache hits:

```text
Client
  ↓
CloudFront
  ↓
Cache
  ↓
Client
```

For misses:

```text
Client
  ↓
CloudFront
  ↓
Origin
  ↓
Application
  ↓
Database
```

A high CloudFront latency metric does not automatically mean CloudFront itself is slow.

## Origin Latency

If CloudFront forwards the request, determine whether latency originates from:

- Network connection
- TLS negotiation
- Load balancer
- Nginx
- Application
- Database
- Redis
- External API
- Queue processing

For example:

```text
CloudFront → ALB          40 ms
ALB → Nginx               10 ms
Nginx → FastAPI           5 ms
FastAPI → PostgreSQL      900 ms
```

The correct optimization target is PostgreSQL or the application/database interaction, not CloudFront.

## Error Classification

Use status codes to select the initial investigation branch.

| Status | Initial focus |
|---|---|
| `403` | WAF/access control/authentication |
| `404` | Path, behavior, object, origin |
| `502` | Origin connectivity/application response |
| `503` | Origin availability/capacity |
| `504` | Origin timeout/slow backend |
| `5xx` spike | Origin health and recent infrastructure changes |

This is an initial routing mechanism, not a root-cause classification.

## 403 Diagnostic Path

```text
403
 │
 ├── WAF blocked?
 │      └── Inspect rule
 │
 ├── Signed access failed?
 │      └── Inspect URL/cookie/policy
 │
 ├── CloudFront restriction?
 │      └── Inspect behavior/geo/method
 │
 └── Origin returned 403?
        └── Inspect S3/Nginx/application
```

## 404 Diagnostic Path

```text
404
 │
 ├── Cache hit?
 │      └── Check cached response
 │
 ├── Correct cache behavior?
 │      └── Check path pattern
 │
 ├── Correct origin?
 │      └── Inspect origin configuration
 │
 └── Resource exists?
        └── Check S3/application
```

## 502 Diagnostic Path

```text
502
 │
 ├── Origin reachable?
 │
 ├── TLS valid?
 │
 ├── Origin protocol correct?
 │
 ├── ALB/Nginx healthy?
 │
 └── Application returning malformed/error response?
```

## 503 Diagnostic Path

```text
503
 │
 ├── Origin healthy?
 │
 ├── Backend capacity exhausted?
 │
 ├── Kubernetes pods healthy?
 │
 ├── ALB target health?
 │
 └── Deployment/scaling event?
```

## 504 Diagnostic Path

```text
504
 │
 ├── Origin response too slow?
 │
 ├── Database latency?
 │
 ├── External API timeout?
 │
 ├── Connection saturation?
 │
 └── Application deadlock/resource exhaustion?
```

## Comparing CloudFront and Origin Metrics

A powerful diagnostic technique is comparing metrics at the same time boundary.

Example:

| Metric | Before incident | During incident |
|---|---:|---:|
| CloudFront requests | 50k/min | 52k/min |
| Cache hit ratio | 92% | 61% |
| Origin requests | 4k/min | 20k/min |
| Origin latency | 180 ms | 1.8 s |
| 5xx | 0.1% | 8% |

This pattern strongly suggests an origin-load problem caused or amplified by a cache-efficiency change.

The numbers are illustrative, but the reasoning is operationally important.

## Detecting Origin Overload

Look for correlated signals:

```text
Cache hit ratio ↓
        │
        ▼
Origin request rate ↑
        │
        ▼
Application CPU ↑
        │
        ▼
Database connections ↑
        │
        ▼
Latency ↑
        │
        ▼
5xx ↑
```

This is more useful than looking at CloudFront error rate alone.

## Recent Change Analysis

Always ask:

> What changed immediately before the incident?

Potential changes include:

- CloudFront cache policy
- Origin request policy
- WAF rule
- Distribution behavior
- Origin endpoint
- TLS certificate
- DNS
- S3 policy
- ALB configuration
- Nginx configuration
- Django/FastAPI deployment
- Kubernetes deployment
- Database configuration

A simple incident timeline is often valuable:

```text
14:00  Deployment begins
14:03  Cache policy changed
14:05  Cache hit ratio falls
14:07  Origin CPU rises
14:09  5xx increases
14:12  Rollback starts
14:15  Error rate recovers
```

This establishes temporal correlation that can guide root-cause analysis.

## Configuration Inspection With AWS CLI

Check distribution status:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.Status'
```

Check distribution domain:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.DomainName'
```

Check Web ACL association:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.DistributionConfig.WebACLId'
```

Check origins:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" |
jq '.DistributionConfig.Origins.Items'
```

Check cache behaviors:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" |
jq '.DistributionConfig.DefaultCacheBehavior,
    .DistributionConfig.CacheBehaviors'
```

## AWS CLI Queries for CloudFront Metrics

CloudFront metrics are available through Amazon CloudWatch.

For example, retrieve request counts:

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/CloudFront \
  --metric-name Requests \
  --dimensions Name=DistributionId,Value="$DISTRIBUTION_ID" \
               Name=Region,Value=Global \
  --statistics Sum \
  --period 300 \
  --start-time 2026-08-20T14:00:00Z \
  --end-time 2026-08-20T15:00:00Z
```

For production automation, prefer `get-metric-data` when retrieving multiple related metrics efficiently.

## Querying Multiple Metrics

A diagnostic script can retrieve several signals together:

```bash
aws cloudwatch get-metric-data \
  --metric-data-queries file://cloudfront-metrics.json \
  --start-time 2026-08-20T14:00:00Z \
  --end-time 2026-08-20T15:00:00Z
```

This is preferable to manually executing many independent commands during an incident.

## Example Metric Query Definition

```json
[
  {
    "Id": "requests",
    "MetricStat": {
      "Metric": {
        "Namespace": "AWS/CloudFront",
        "MetricName": "Requests",
        "Dimensions": [
          {
            "Name": "DistributionId",
            "Value": "EXAMPLE123"
          },
          {
            "Name": "Region",
            "Value": "Global"
          }
        ]
      },
      "Period": 300,
      "Stat": "Sum"
    },
    "ReturnData": true
  }
]
```

For additional metrics, add separate metric-data queries rather than repeatedly invoking the CLI.

## Operational Diagnostic Checklist

### Request

- [ ] Exact hostname captured
- [ ] Exact URI captured
- [ ] HTTP method captured
- [ ] Query string captured
- [ ] Timestamp captured
- [ ] Client characteristics captured
- [ ] Response headers captured

### CloudFront

- [ ] Correct distribution identified
- [ ] Distribution is deployed
- [ ] Correct behavior identified
- [ ] Correct origin identified
- [ ] Cache state understood
- [ ] Viewer protocol checked
- [ ] Allowed methods checked

### WAF

- [ ] Web ACL association checked
- [ ] WAF action identified
- [ ] Terminating rule identified
- [ ] Rate-based rules checked
- [ ] Managed rules checked
- [ ] Geographic rules checked

### Origin

- [ ] Origin reachable
- [ ] Origin health checked
- [ ] ALB target health checked
- [ ] Nginx logs checked
- [ ] Application logs checked
- [ ] Database latency checked
- [ ] External dependencies checked

### Changes

- [ ] Recent CloudFront changes reviewed
- [ ] WAF changes reviewed
- [ ] Origin changes reviewed
- [ ] Application deployments reviewed
- [ ] Infrastructure deployments reviewed
- [ ] DNS changes reviewed

## Production Logging Recommendations

A production backend should make CloudFront incidents diagnosable without requiring a full application-wide debug session.

Recommended telemetry includes:

- CloudFront access logging appropriate to the workload
- AWS WAF logging when WAF is security-critical
- CloudWatch metrics and alarms
- Origin access logs
- Application structured logs
- Request correlation IDs
- Distributed tracing where appropriate
- Deployment/change history
- Infrastructure-as-code state and version history

For structured application logs, prefer machine-readable output.

Example:

```json
{
  "timestamp": "2026-08-20T14:32:15Z",
  "level": "INFO",
  "service": "orders-api",
  "request_id": "abc123",
  "route": "/api/orders",
  "status": 200,
  "duration_ms": 142
}
```

Never include:

- Authorization headers
- Access tokens
- Session cookies
- Private signing keys
- Sensitive customer data

## Security Considerations

Logging improves observability but can create a data-exposure risk.

CloudFront and WAF investigations may involve:

- IP addresses
- Query parameters
- Cookies
- Authentication metadata
- User-Agent values
- Application identifiers

Before enabling or exporting detailed logs, define:

- Retention period
- Access permissions
- Encryption
- Data classification
- PII handling
- Operational access procedures

Diagnostic logs should provide enough information to identify a request without becoming an unrestricted copy of sensitive application traffic.

## Cost Considerations

Detailed logging and high-cardinality observability can increase operational costs.

Control cost by:

- Using standard logs for broad historical analysis
- Using real-time logs selectively
- Narrowing CloudWatch Logs Insights queries
- Applying appropriate log retention
- Avoiding unnecessary high-cardinality metrics
- Sampling detailed traces
- Centralizing reusable diagnostic queries

Do not reduce critical security logging solely to minimize cost. Balance observability requirements against workload and risk.

## Common Diagnostic Mistakes

| Mistake | Why it fails | Better approach |
|---|---|---|
| Look only at browser error | Loses request context | Reproduce with `curl` |
| Assume every 403 is WAF | Multiple access-control layers exist | Check WAF logs |
| Assume every 5xx is CloudFront | Origin often produces failure | Inspect origin telemetry |
| Ignore cache state | Origin may not be involved | Determine hit/miss |
| Search logs across days | Creates excessive noise | Narrow by timestamp |
| Debug application first | Request may never reach it | Trace edge to origin |
| Log sensitive credentials | Creates security exposure | Redact secrets |
| Ignore recent changes | Misses likely regression | Build incident timeline |
| Use only averages | Hides tail latency | Inspect p95/p99 |
| Query every log indiscriminately | Expensive and slow | Filter aggressively |

## Senior-Level Diagnostic Reasoning

At an intermediate level, troubleshooting often means finding the error.

At a senior level, the goal is to reconstruct the system behavior.

For example:

```text
Observed:
CloudFront 504 rate increased.

Evidence:
Cache hit ratio unchanged.
Origin request rate unchanged.
Origin latency increased from 200 ms to 5 s.
PostgreSQL connection pool is exhausted.

Inference:
CloudFront is exposing an origin-side saturation problem.

Action:
Investigate database connection usage rather than modifying CloudFront timeout behavior.
```

This distinction prevents infrastructure changes from being used to mask application bottlenecks.

## Incident Investigation Example

Consider:

```text
GET /api/catalog
```

with:

```text
HTTP 504
```

A disciplined investigation might produce:

```text
Client
  │
  ▼
CloudFront
  │
  │ 504
  ▼
Origin
  │
  ▼
ALB
  │
  ▼
FastAPI
  │
  ▼
PostgreSQL
  │
  └── Query latency increased
```

CloudFront is the component returning the observable response, but the root cause is downstream.

A useful incident statement would therefore be:

> CloudFront returned 504 because the origin failed to respond within the required time after PostgreSQL query latency increased.

That is significantly more actionable than:

> CloudFront is timing out.

## Building a Diagnostic Runbook

A production runbook should convert this methodology into repeatable operations.

A useful runbook structure is:

```text
Incident detected
      │
      ▼
Capture request
      │
      ▼
Identify distribution
      │
      ▼
Check CloudFront status
      │
      ▼
Check WAF
      │
      ▼
Determine cache state
      │
      ▼
Check origin
      │
      ▼
Check application dependencies
      │
      ▼
Correlate recent changes
      │
      ▼
Mitigate
      │
      ▼
Validate
      │
      ▼
Document root cause
```

The runbook should contain actual commands, dashboards, log queries, escalation contacts, rollback procedures, and ownership boundaries.

## Recommended Investigation Sequence

For most CloudFront incidents:

1. Capture an exact failing request.
2. Reproduce it with `curl`.
3. Record response headers and timing.
4. Identify the CloudFront distribution.
5. Determine whether the request was a cache hit or miss.
6. Check WAF decisions for access-control failures.
7. Inspect the applicable cache behavior.
8. Verify the configured origin.
9. Determine whether the request reached the origin.
10. Inspect origin and application logs.
11. Compare latency, request rate, cache-hit ratio, and error metrics.
12. Review recent infrastructure and application changes.
13. Form a root-cause hypothesis.
14. Apply the smallest safe mitigation.
15. Validate the result using the same request.
16. Record the evidence and root cause for future incidents.

## Key Takeaways

- **Start with an exact request:** timestamp, URI, method, headers, status, and available request identifiers provide the foundation for reliable correlation.
- **Trace the request path:** determine whether the failure occurred at WAF, CloudFront, cache processing, the origin, or the application.
- **Correlate logs with metrics:** cache-hit ratio, origin request volume, latency, and error rates often reveal the actual failure mechanism.
- **Use narrow diagnostic queries:** focused time windows, request attributes, and representative requests reduce investigation noise and observability cost.
- **Senior-level troubleshooting reconstructs system behavior:** identify the first layer that diverged from the expected request path rather than treating the final HTTP status as the root cause.