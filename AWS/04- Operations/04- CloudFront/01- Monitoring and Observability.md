# 01- Monitoring and Observability

## Overview

CloudFront monitoring and observability provide the visibility required to determine whether a distribution is serving traffic correctly, efficiently, and securely.

For production systems, monitoring should answer four questions:

- **Availability:** Are requests succeeding?
- **Performance:** How quickly are requests being served?
- **Efficiency:** Are requests being served from the edge cache or reaching the origin unnecessarily?
- **Security:** Are legitimate requests being allowed while abusive or unauthorized traffic is blocked?

CloudFront should not be monitored in isolation. A typical backend request path may look like:

```text
Client
  ↓
CloudFront
  ↓
AWS WAF
  ↓
Cache Behavior
  ↓
Origin
  ↓
ALB / Nginx / Kubernetes Ingress
  ↓
Django / FastAPI
  ↓
Redis / PostgreSQL / External APIs
```

A CloudFront dashboard that shows `2xx` responses does not necessarily mean the application is healthy. The edge may be healthy while the origin is overloaded, latency is increasing, or cached content is becoming stale.

The objective of observability is therefore to correlate **CloudFront metrics, logs, origin metrics, application telemetry, and deployment events** into a single operational view.

---

## Monitoring vs Observability

These terms are related but should not be treated as interchangeable.

| Concept | Purpose | Typical Question |
|---|---|---|
| Monitoring | Track known health signals | "Is the error rate above the threshold?" |
| Logging | Record individual events | "What happened to this request?" |
| Metrics | Measure aggregated behavior | "How many requests are failing?" |
| Tracing | Follow a request across services | "Where did this request spend its time?" |
| Observability | Understand system behavior from telemetry | "Why did latency increase?" |

For CloudFront, monitoring normally starts with metrics and alarms. Observability becomes important when diagnosing why a metric changed.

---

## CloudFront Monitoring Architecture

```mermaid
flowchart LR
    Client[Clients] --> CF[CloudFront Distribution]
    CF --> WAF[AWS WAF]
    WAF --> Origin[Origin]
    Origin --> ALB[ALB / Load Balancer]
    ALB --> App[Django / FastAPI]
    App --> Redis[Redis]
    App --> DB[(PostgreSQL)]

    CF --> Metrics[CloudFront Metrics]
    CF --> Logs[CloudFront Logs]

    WAF --> WAFLogs[WAF Logs]
    ALB --> ALBLogs[ALB Logs]
    App --> AppLogs[Application Logs]

    Metrics --> CW[CloudWatch]
    Logs --> S3[S3 / Log Analytics]
    WAFLogs --> CW
    ALBLogs --> CW
    AppLogs --> CW

    CW --> Dashboard[Operational Dashboard]
    CW --> Alarm[CloudWatch Alarms]
    Dashboard --> Engineer[Engineering / On-Call]
    Alarm --> Engineer
```

The important architectural principle is that **each layer produces different evidence**.

CloudFront can tell you that a request failed. Origin logs can tell you whether the request actually reached the backend. Application traces can tell you why the backend was slow.

---

## Core CloudFront Metrics

CloudFront exposes metrics that are useful for availability, traffic, caching, and performance analysis.

Common operational metrics include:

| Metric | What It Indicates | Operational Use |
|---|---|---|
| `Requests` | Number of viewer requests | Traffic analysis and capacity planning |
| `BytesDownloaded` | Data delivered to viewers | Bandwidth and traffic analysis |
| `BytesUploaded` | Data uploaded through CloudFront | Upload traffic analysis |
| `4xxErrorRate` | Percentage of 4xx responses | Client, access, routing, or authorization issues |
| `5xxErrorRate` | Percentage of 5xx responses | Origin or CloudFront-side failures |
| `ErrorRate` | Overall error behavior | High-level availability signal |
| Cache hit ratio | Percentage of requests served from cache | Cache efficiency and origin-load analysis |
| Origin latency | Time associated with origin responses | Backend performance analysis |

The exact set of available metrics and dimensions depends on the CloudFront monitoring capability being used. Always validate metric names and dimensions against the current AWS documentation before automating dashboards or alarms.

---

## Availability Monitoring

Availability monitoring should focus on **error ratios rather than raw error counts**.

For example, an increase from 100 errors to 500 errors sounds severe. It has a different meaning if traffic increased from 10,000 requests to 100 million requests.

A useful high-level signal is:

```text
Error Rate = Failed Requests / Total Requests
```

Monitor:

- 4xx error rate.
- 5xx error rate.
- Total request volume.
- Origin error rate.
- WAF blocked requests.
- Sudden changes in traffic.

### Why Error Rate Matters

Suppose an API normally receives:

```text
1,000 requests/minute
10 errors/minute
```

The error rate is:

```text
1%
```

If traffic increases to:

```text
100,000 requests/minute
500 errors/minute
```

the raw error count increased significantly, but the error rate is only:

```text
0.5%
```

An alert based solely on error count could generate unnecessary noise.

Conversely, a low-volume service could experience a serious outage with only a few hundred errors.

Production alerting should therefore combine:

- Percentage-based thresholds.
- Minimum traffic thresholds.
- Absolute error counts where appropriate.
- Duration-based conditions.

---

## Monitoring 4xx Errors

4xx responses generally indicate that the request could not be fulfilled because of the request, access policy, routing, or authorization state.

Common causes include:

- Incorrect URLs.
- Missing objects.
- Incorrect cache behaviors.
- AWS WAF rules.
- Signed URL failures.
- Signed cookie failures.
- Geographic restrictions.
- Authorization problems.
- Incorrect application routing.

A 4xx increase should not automatically be treated as an application outage.

For example:

```text
CloudFront 403
    ↓
AWS WAF
    ↓
Rule matched
    ↓
Request blocked
```

In this case, the CloudFront distribution may be operating correctly.

The important diagnostic question is:

> **Who generated the 4xx response?**

---

## Monitoring 5xx Errors

5xx responses are more likely to indicate a server-side problem.

Typical investigation areas include:

```text
CloudFront
   ↓
Origin connectivity
   ↓
ALB
   ↓
Target health
   ↓
Nginx / Ingress
   ↓
Application
   ↓
Database / Redis / External API
```

A spike in `5xxErrorRate` should be correlated with:

- Origin latency.
- ALB target response time.
- ALB target health.
- Application error rate.
- Database CPU and connections.
- Redis latency.
- Container CPU and memory.
- Kubernetes pod restarts.
- Deployment events.

---

## Cache Hit Ratio

Cache hit ratio is one of the most important CloudFront performance indicators.

Conceptually:

```text
Cache Hit Ratio =
Cache Hits / Total Cacheable Requests
```

A higher cache hit ratio generally means fewer requests reach the origin.

```mermaid
flowchart TD
    Request[Viewer Request] --> Cache{Cached Object?}

    Cache -->|Hit| Edge[Serve from Edge]
    Cache -->|Miss| Origin[Request Origin]

    Edge --> Client[Viewer]
    Origin --> Store[Store Response in Cache]
    Store --> Client
```

### Why Cache Hit Ratio Matters

Consider an API or web application receiving:

```text
1,000,000 requests/hour
```

If only 20% are served from cache:

```text
800,000 requests/hour → Origin
```

If cache efficiency improves to 80%:

```text
200,000 requests/hour → Origin
```

That reduction can materially affect:

- ALB traffic.
- Application CPU.
- Database queries.
- Redis traffic.
- Network transfer.
- Infrastructure cost.

However, maximizing cache hit ratio is not the objective by itself.

A highly cacheable but incorrectly cached response can be a security or correctness problem.

---

## Cache Hit Ratio Investigation

When cache hit ratio decreases, inspect:

| Area | Possible Problem |
|---|---|
| Cache policy | Excessive cache-key components |
| Query strings | Unique parameters producing unique cache keys |
| Cookies | User-specific cookies fragmenting the cache |
| Headers | Unnecessary headers included in cache behavior |
| TTL | Objects expiring too quickly |
| Cache invalidations | Frequent invalidation activity |
| URL design | Highly dynamic URLs |
| Deployment | Large-scale cache invalidation |
| Content type | Content is inherently dynamic |

A common mistake is adding every request header, cookie, or query parameter to the cache key "just in case."

That can turn a potentially highly cacheable resource into an effectively uncacheable resource.

---

## Origin Monitoring

CloudFront metrics should be correlated with origin metrics.

For an AWS architecture such as:

```text
CloudFront
    ↓
Application Load Balancer
    ↓
ECS / EKS / EC2
    ↓
Django / FastAPI
```

monitor at least:

- ALB request count.
- ALB target response time.
- ALB HTTP 4xx.
- ALB HTTP 5xx.
- Target health.
- ECS/EKS/EC2 CPU.
- ECS/EKS/EC2 memory.
- Container restarts.
- Application request latency.
- Application error rate.

For Kubernetes, also monitor:

- Pod restarts.
- Readiness failures.
- Liveness failures.
- Deployment rollout status.
- CPU throttling.
- Memory pressure.
- Node capacity.
- Horizontal Pod Autoscaler behavior.

---

## Application-Level Observability

CloudFront cannot explain why a Django or FastAPI request takes five seconds.

Application-level instrumentation is required.

For example:

```text
CloudFront latency
        ↓
ALB latency
        ↓
Application latency
        ↓
Database latency
        ↓
External API latency
```

Suppose:

```text
CloudFront request: 4.8 seconds
ALB target response: 4.7 seconds
Application request: 4.6 seconds
PostgreSQL query: 4.2 seconds
```

The evidence strongly suggests that CloudFront is not the root cause.

The application is waiting on PostgreSQL.

---

## Structured Application Logging

Backend services should produce structured logs rather than unstructured text.

A useful application log might contain:

```json
{
  "timestamp": "2026-08-20T14:32:11Z",
  "level": "ERROR",
  "service": "orders-api",
  "request_id": "7f5f7c1d",
  "method": "GET",
  "path": "/api/orders/123",
  "status_code": 500,
  "duration_ms": 1842,
  "user_id": "redacted",
  "exception": "DatabaseTimeout"
}
```

Avoid logging:

- Passwords.
- Authorization tokens.
- Session cookies.
- Private keys.
- Sensitive personal data.
- Complete request headers without filtering.

---

## Request Correlation

A production troubleshooting workflow benefits from a correlation identifier.

Conceptually:

```text
Viewer
  │
  │ Request ID
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
Django / FastAPI
  │
  ├── Redis
  │
  └── PostgreSQL
```

The identifier allows engineers to correlate events across systems.

Do not assume that a CloudFront request identifier automatically becomes the application's correlation ID. If end-to-end correlation is required, explicitly design and propagate an appropriate request identifier while preserving security and privacy constraints.

---

## CloudFront Logs

CloudFront access logs provide request-level information useful for troubleshooting traffic and behavior.

Logs can help answer questions such as:

- Which URLs are receiving traffic?
- Which status codes are being returned?
- Which HTTP methods are being used?
- Which edge locations are involved?
- Which requests are cache hits or misses?
- Which requests are producing errors?
- Are specific paths disproportionately failing?

Depending on the logging mechanism, delivery can differ in latency and format. Choose the logging approach based on the required investigation and analysis workflow.

---

## Real-Time Monitoring vs Historical Logs

Use different telemetry for different operational questions.

| Tool / Signal | Best Use |
|---|---|
| CloudWatch metrics | Dashboards, alarms, trends |
| CloudFront standard logs | Historical request analysis |
| CloudFront real-time logs | Low-latency request diagnostics |
| AWS WAF logs | Security and access-control analysis |
| ALB access logs | Origin request investigation |
| Application logs | Application failures |
| Distributed traces | Cross-service latency analysis |
| Deployment events | Change correlation |

Metrics are excellent for detecting an incident.

Logs and traces are usually better for explaining it.

---

## CloudWatch Dashboards

A production CloudFront dashboard should present related signals together rather than displaying dozens of unrelated graphs.

A practical dashboard can include:

```text
CloudFront
├── Requests
├── 4xx Error Rate
├── 5xx Error Rate
├── Cache Hit Ratio
├── Bytes Downloaded
└── Origin Latency
        │
        ├── ALB Request Count
        ├── ALB Target Response Time
        ├── ALB 4xx
        └── ALB 5xx
                │
                ├── Application Error Rate
                ├── Application Latency
                ├── Database Latency
                └── Redis Latency
```

The dashboard should make causal relationships visible.

---

## Alerting Strategy

Avoid alerting on every metric.

An alert should represent a condition requiring human or automated action.

### Good Alert

```text
5xx error rate > 2%
AND
request volume > minimum threshold
FOR
5 minutes
```

### Weak Alert

```text
5xx errors > 1
```

The second alert can trigger on a single malformed request and create unnecessary noise.

### Alert Categories

| Alert | Purpose |
|---|---|
| High 5xx rate | Availability |
| High 4xx rate | Routing/access regression |
| High origin latency | Backend performance |
| Low cache hit ratio | Cache efficiency |
| Sudden traffic increase | Capacity/security investigation |
| WAF block spike | Security investigation |
| Origin health degradation | Infrastructure availability |

Thresholds should be based on service-specific historical behavior rather than arbitrary universal numbers.

---

## SLO-Oriented Monitoring

Senior-level monitoring should connect CloudFront telemetry to service-level objectives.

Example:

```text
Availability SLO:
99.9% successful requests

Latency SLO:
99% of cacheable requests < 300 ms

Error Budget:
0.1% unsuccessful requests
```

CloudFront metrics can provide part of the evidence, but the SLO should reflect the **user-visible service**, not merely the health of the CDN.

For example, CloudFront could return `200` quickly for a cached page while the underlying API is completely unavailable.

That does not necessarily mean the entire product is healthy.

---

## High-Cardinality Analysis

Metrics systems are optimized for aggregated dimensions.

Avoid creating uncontrolled dimensions such as:

```text
/path=/api/users/123456
/path=/api/users/123457
/path=/api/users/123458
```

This can create extremely high-cardinality telemetry.

Prefer normalized dimensions where appropriate:

```text
route=/api/users/{id}
```

Detailed request-specific analysis belongs in logs or traces rather than unlimited metric dimensions.

---

## Performance Monitoring

Latency should be examined as a distribution rather than only an average.

For example:

```text
Average latency: 180 ms
p50:              120 ms
p95:              420 ms
p99:             1800 ms
```

An average of `180 ms` hides the fact that a significant tail of requests is taking much longer.

Monitor:

- p50.
- p95.
- p99.
- Origin latency.
- Cache-hit latency.
- Cache-miss latency.
- Backend latency.
- Dependency latency.

Tail latency is particularly important for APIs and dynamic applications.

---

## Cost Observability

Monitoring should also include cost-related signals.

CloudFront cost can be influenced by:

- Data transfer.
- Request volume.
- Logging.
- Real-time logging.
- Origin traffic caused by cache misses.
- Cache invalidations and related operational activity.

A cache-efficiency problem can therefore become both a **performance problem and a cost problem**.

A useful operational relationship is:

```text
Lower Cache Hit Ratio
        ↓
More Origin Requests
        ↓
More Compute
        ↓
More Database Work
        ↓
Higher Infrastructure Cost
```

---

## Security Monitoring

CloudFront observability should be integrated with security telemetry.

Monitor for:

- Sudden WAF block-rate increases.
- Abnormal request-rate changes.
- Unexpected geographic traffic.
- Repeated 403 responses.
- Signed URL failures.
- Signed cookie failures.
- Suspicious request patterns.
- Unexpected origin exposure.

A sudden traffic spike may indicate either:

- A successful product launch.
- A viral request.
- A bot.
- A DDoS event.
- A misconfigured client.
- A cache-key regression.

Metrics identify the anomaly; logs and security telemetry help determine the cause.

---

## Operational Troubleshooting Workflow

When an alert fires:

### Establish Scope

Determine:

- Start time.
- Affected distribution.
- Affected paths.
- Affected regions.
- Affected status codes.
- Percentage of traffic affected.

### Check CloudFront

Inspect:

- Request volume.
- 4xx rate.
- 5xx rate.
- Cache hit ratio.
- Origin latency.
- Recent configuration changes.

### Check WAF

Determine whether:

- Blocked requests increased.
- A rule was recently modified.
- Legitimate traffic matches a rule.
- Rate-based rules are triggering.

### Check Origin

Inspect:

- ALB health.
- Target response time.
- Target errors.
- Application availability.
- Container or instance capacity.

### Check Dependencies

Inspect:

- PostgreSQL connections and latency.
- Redis availability and latency.
- External API latency.
- Kafka or asynchronous processing if relevant.

### Correlate Changes

Look for:

- CloudFront configuration changes.
- WAF rule changes.
- Application deployments.
- Infrastructure deployments.
- Database migrations.
- DNS changes.
- Certificate changes.

### Validate

After remediation:

- Reproduce the original request.
- Confirm error rate returns to normal.
- Confirm latency improves.
- Confirm cache behavior is correct.
- Confirm WAF and security controls remain active.

---

## Example CloudWatch CLI Investigation

List available CloudFront distributions:

```bash
aws cloudfront list-distributions
```

Inspect a specific distribution:

```bash
aws cloudfront get-distribution \
  --id E1234567890ABC
```

List CloudFront monitoring subscriptions:

```bash
aws cloudfront get-monitoring-subscription \
  --distribution-id E1234567890ABC
```

The AWS CLI should be treated as an investigation tool, not a replacement for dashboards and centralized observability.

---

## Common Monitoring Mistakes

### Monitoring Only CloudFront

**Problem:** The edge looks healthy while the origin is failing.

**Fix:** Correlate CloudFront with ALB, application, database, and dependency telemetry.

### Alerting on Raw Error Counts

**Problem:** Alert thresholds do not account for traffic volume.

**Fix:** Prefer error percentages combined with minimum traffic and duration conditions.

### Using Only Average Latency

**Problem:** Tail latency remains invisible.

**Fix:** Monitor p50, p95, and p99.

### Ignoring Cache Hit Ratio

**Problem:** Origin load increases without an obvious application code change.

**Fix:** Correlate cache efficiency with origin request volume and backend capacity.

### Logging Sensitive Data

**Problem:** Troubleshooting telemetry becomes a security liability.

**Fix:** Redact credentials, tokens, cookies, and sensitive personal data.

### Creating Excessive Metric Dimensions

**Problem:** High-cardinality telemetry becomes expensive and difficult to operate.

**Fix:** Keep metrics aggregated and use logs/traces for detailed request-level analysis.

### Treating Every 4xx as an Outage

**Problem:** Legitimate client errors or security blocks create false alarms.

**Fix:** Separate client, security, routing, and application failure categories.

### No Baseline

**Problem:** Engineers cannot distinguish normal traffic variation from an incident.

**Fix:** Maintain historical baselines for traffic, latency, errors, and cache efficiency.

---

## Production Monitoring Checklist

### CloudFront

- [ ] Request volume monitored
- [ ] 4xx error rate monitored
- [ ] 5xx error rate monitored
- [ ] Cache hit ratio monitored
- [ ] Origin latency monitored
- [ ] Bandwidth monitored
- [ ] Appropriate dashboards configured
- [ ] Appropriate alarms configured

### Security

- [ ] AWS WAF telemetry available
- [ ] WAF block-rate anomalies monitored
- [ ] Signed URL failures diagnosable
- [ ] Signed cookie failures diagnosable
- [ ] Sensitive data excluded from logs

### Origin

- [ ] ALB metrics monitored
- [ ] Target health monitored
- [ ] Application latency monitored
- [ ] Application errors monitored
- [ ] Container/instance capacity monitored

### Dependencies

- [ ] PostgreSQL latency monitored
- [ ] PostgreSQL connection utilization monitored
- [ ] Redis health and latency monitored
- [ ] External dependency latency monitored

### Operations

- [ ] Deployment events correlated with incidents
- [ ] CloudFront configuration changes auditable
- [ ] WAF configuration changes auditable
- [ ] Request correlation available where appropriate
- [ ] Incident dashboards are documented
- [ ] Alert thresholds have defined owners and remediation paths

## Key Takeaways

- **Monitor the complete request path:** CloudFront metrics are only one layer of production observability; correlate them with WAF, ALB, application, database, and dependency telemetry.
- **Track both availability and efficiency:** Error rates, origin latency, request volume, and cache hit ratio together provide a much stronger operational picture than any single metric.
- **Use percentiles and meaningful alerts:** p95/p99 latency and traffic-aware error-rate alerts expose real user impact while reducing alert noise.
- **Separate detection from diagnosis:** Metrics and alarms detect anomalies; logs and traces provide the evidence needed to determine root cause.
- **Design observability as part of the architecture:** Secure structured logs, request correlation, dashboards, SLOs, and actionable alerts should exist before production incidents occur.