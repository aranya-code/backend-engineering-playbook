# 02- CloudFront Metrics

## Overview

Amazon CloudFront publishes operational metrics to Amazon CloudWatch for monitoring traffic, errors, cache effectiveness, and origin performance. These metrics are the first layer of observability for a CloudFront distribution and are useful for detecting incidents, establishing service-level indicators, capacity planning, and correlating CDN behavior with origin infrastructure.

CloudFront provides a set of default distribution metrics at no additional CloudFront metric charge:

- `Requests`
- `BytesDownloaded`
- `BytesUploaded`
- `4xxErrorRate`
- `5xxErrorRate`
- `TotalErrorRate`

Additional distribution metrics can be enabled per distribution:

- `CacheHitRate`
- `OriginLatency`
- `401ErrorRate`
- `403ErrorRate`
- `404ErrorRate`
- `502ErrorRate`
- `503ErrorRate`
- `504ErrorRate`

The additional metrics provide substantially better troubleshooting visibility, particularly for production APIs and high-traffic applications. They incur an additional fixed CloudWatch metric charge per distribution, with up to eight additional metrics sent to CloudWatch. :contentReference[oaicite:0]{index=0}

CloudFront is a global service. Its CloudWatch metrics use the `AWS/CloudFront` namespace, and CloudWatch operations for these metrics must be performed in `us-east-1` because CloudFront metrics are sent to US East (N. Virginia). :contentReference[oaicite:1]{index=1}

A production observability model should therefore look beyond CloudFront itself:

```text
                         ┌──────────────────┐
                         │      Client      │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │    CloudFront    │
                         │                  │
                         │ Requests         │
                         │ Error Rates      │
                         │ Cache Hit Rate   │
                         │ Origin Latency   │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │       ALB        │
                         │                  │
                         │ Request Count    │
                         │ Target Errors    │
                         │ Target Latency   │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Django / FastAPI │
                         │                  │
                         │ App Latency      │
                         │ Exceptions       │
                         │ Dependency Calls │
                         └────────┬─────────┘
                                  │
                     ┌────────────┴────────────┐
                     ▼                         ▼
              ┌─────────────┐           ┌─────────────┐
              │ PostgreSQL  │           │    Redis    │
              └─────────────┘           └─────────────┘
```

A CloudFront metric generally tells you **what changed**, not necessarily **why it changed**. For example, an increase in `5xxErrorRate` could originate from CloudFront, the origin, an ALB, Nginx, Django, FastAPI, PostgreSQL, Redis, or another dependency.

---

## CloudFront Metrics Model

CloudFront distribution metrics can be divided into three practical categories:

| Category | Examples | Primary Purpose |
|---|---|---|
| Traffic | `Requests`, `BytesDownloaded`, `BytesUploaded` | Understand workload |
| Reliability | `4xxErrorRate`, `5xxErrorRate`, `TotalErrorRate` | Detect failures |
| Performance | `CacheHitRate`, `OriginLatency` | Understand caching and origin behavior |
| Diagnostic | `401`, `403`, `404`, `502`, `503`, `504` rates | Isolate failure types |

CloudFront also provides metrics for CloudFront Functions and Lambda@Edge. Those are separate from the distribution metrics discussed here.

---

## CloudFront Metric Namespace and Dimensions

CloudFront distribution metrics are published under:

```text
Namespace:
AWS/CloudFront
```

The primary dimensions are:

```text
DistributionId
Region
```

For CloudFront distribution metrics, the `Region` dimension is `Global`. CloudWatch API and CLI operations use `us-east-1`. :contentReference[oaicite:2]{index=2}

This distinction is important:

```text
CloudFront service:
Global

CloudFront metric dimension:
Region = Global

CloudWatch API/CLI region:
us-east-1
```

For example:

```bash
aws cloudwatch list-metrics \
  --namespace AWS/CloudFront \
  --region us-east-1
```

A common operational mistake is opening CloudWatch in the application's AWS Region and assuming the CloudFront metrics are missing.

---

## Default Distribution Metrics

The following metrics are available for every CloudFront distribution without enabling additional distribution metrics. :contentReference[oaicite:3]{index=3}

| Metric | Meaning | Statistic |
|---|---|---|
| `Requests` | Total viewer requests | `Sum` |
| `BytesDownloaded` | Bytes downloaded for `GET` and `HEAD` requests | `Sum` |
| `BytesUploaded` | Bytes uploaded using `OPTIONS`, `POST`, and `PUT` | `Sum` |
| `4xxErrorRate` | Percentage of viewer requests returning 4xx | `Average` |
| `5xxErrorRate` | Percentage of viewer requests returning 5xx | `Average` |
| `TotalErrorRate` | Percentage of viewer requests returning 4xx or 5xx | `Average` |

The statistic matters when querying metrics programmatically. CloudFront defines the supported statistic for each metric. :contentReference[oaicite:4]{index=4}

---

## Requests

### What It Is

`Requests` represents the total number of viewer requests received by CloudFront for all HTTP methods and both HTTP and HTTPS requests. The valid CloudWatch statistic is `Sum`. :contentReference[oaicite:5]{index=5}

```text
Requests
    =
GET
+ HEAD
+ POST
+ PUT
+ OPTIONS
+ other viewer requests
```

### Why It Matters

Request volume is the baseline traffic signal for a distribution.

It is useful for:

- Capacity planning.
- Detecting traffic spikes.
- Detecting unexpected traffic drops.
- Correlating traffic with errors.
- Identifying abnormal usage.
- Understanding application demand.

For example:

```text
Normal:
100,000 requests / minute

Incident:
1,500,000 requests / minute
```

If the same period shows increased origin latency and 5xx responses, the traffic increase may be contributing directly to the incident.

### Production Consideration

Do not alert simply because request volume increased.

A spike may be:

- Expected business traffic.
- A deployment-related event.
- A marketing campaign.
- A crawler.
- A bot.
- A traffic attack.

Correlate `Requests` with error rates, cache efficiency, WAF telemetry, and origin capacity.

---

## BytesDownloaded

### What It Is

`BytesDownloaded` represents the total number of bytes downloaded by viewers for `GET` and `HEAD` requests. Its valid CloudWatch statistic is `Sum`. :contentReference[oaicite:6]{index=6}

### Why It Matters

It helps identify:

- Bandwidth consumption.
- Large-object delivery.
- Media traffic.
- Asset deployment effects.
- Traffic growth.
- Potential cost drivers.

Consider:

```text
Scenario A

Requests:
1,000,000

BytesDownloaded:
50 GB
```

versus:

```text
Scenario B

Requests:
1,000,000

BytesDownloaded:
5 TB
```

Both workloads have the same request count but dramatically different bandwidth characteristics.

### Production Investigation

If `BytesDownloaded` increases sharply without a proportional request increase, investigate:

- Larger response payloads.
- New media assets.
- Incorrect compression.
- Unexpected downloads.
- Large API responses.
- Cache behavior changes.

---

## BytesUploaded

### What It Is

`BytesUploaded` represents bytes uploaded by viewers to CloudFront through `OPTIONS`, `POST`, and `PUT` requests. Its valid statistic is `Sum`. :contentReference[oaicite:7]{index=7}

This metric is particularly relevant when CloudFront handles upload or API traffic.

```text
Client
  │
  │ POST /upload
  ▼
CloudFront
  │
  ▼
Origin
```

### When It Matters

Monitor it when your architecture supports:

- File uploads.
- API write operations.
- Large request payloads.
- Upload-heavy workloads.

For a static website serving only cached assets, this metric is usually much less important.

---

## 4xxErrorRate

### What It Is

`4xxErrorRate` is the percentage of all viewer requests for which the response status code is in the `4xx` range. Its valid statistic is `Average`. :contentReference[oaicite:8]{index=8}

Examples include:

```text
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
```

### Why It Matters

A 4xx increase does not automatically mean that CloudFront infrastructure is unhealthy.

Potential causes include:

| Cause | Example |
|---|---|
| Invalid request | Malformed API request |
| Missing resource | `/assets/app.js` does not exist |
| Authentication failure | Missing credentials |
| Authorization failure | Invalid signed URL |
| WAF block | Security rule rejects request |
| Routing problem | Incorrect behavior/path pattern |
| Application response | Django/FastAPI returns 404 |

The important question is:

> Which component generated the 4xx response?

---

## 5xxErrorRate

### What It Is

`5xxErrorRate` is the percentage of viewer requests for which the response status code is in the `5xx` range. Its valid statistic is `Average`. :contentReference[oaicite:9]{index=9}

Typical responses include:

```text
500 Internal Server Error
502 Bad Gateway
503 Service Unavailable
504 Gateway Timeout
```

### Diagnostic Model

A 5xx increase should be correlated across the complete request path:

```mermaid
flowchart LR
    Client --> CF[CloudFront]
    CF --> Origin[Origin]
    Origin --> ALB[ALB]
    ALB --> App[Django / FastAPI]
    App --> DB[(PostgreSQL)]
    App --> Redis[(Redis)]

    CF -.-> CF5xx[CloudFront 5xx]
    CF -.-> OL[Origin Latency]
    ALB -.-> ALB5xx[ALB 5xx]
    App -.-> App5xx[Application 5xx]
```

For example:

```text
CloudFront 5xx ↑
      │
      ├── ALB 5xx ↑
      │      └── Investigate application/origin
      │
      ├── OriginLatency ↑
      │      └── Investigate slow dependencies
      │
      └── CloudFront only
             └── Investigate CDN/origin connectivity
```

---

## TotalErrorRate

### What It Is

`TotalErrorRate` is the percentage of viewer requests resulting in either a `4xx` or `5xx` response. Its valid statistic is `Average`. :contentReference[oaicite:10]{index=10}

Conceptually:

```text
TotalErrorRate
    =
4xxErrorRate + 5xxErrorRate
```

The relationship is useful, but the metrics should not be treated as interchangeable.

For example:

```text
TotalErrorRate = 8%

4xx = 7.5%
5xx = 0.5%
```

This is fundamentally different from:

```text
TotalErrorRate = 8%

4xx = 0.5%
5xx = 7.5%
```

The first case points toward client, routing, authentication, authorization, or WAF behavior. The second suggests a much more serious server-side failure.

---

## Additional Distribution Metrics

Additional metrics must be enabled for each distribution separately and incur additional cost. They include cache efficiency, origin latency, and status-specific error rates. :contentReference[oaicite:11]{index=11}

| Metric | What It Helps Diagnose | Statistic |
|---|---|---|
| `CacheHitRate` | Cache efficiency | `Average` |
| `OriginLatency` | Origin first-byte latency | `Percentile` |
| `401ErrorRate` | Authentication failures | `Average` |
| `403ErrorRate` | Authorization/WAF/access failures | `Average` |
| `404ErrorRate` | Missing resources | `Average` |
| `502ErrorRate` | Bad gateway failures | `Average` |
| `503ErrorRate` | Service unavailable failures | `Average` |
| `504ErrorRate` | Gateway timeout failures | `Average` |

These metrics are particularly valuable for production troubleshooting because aggregate `4xxErrorRate` and `5xxErrorRate` can hide the actual failure distribution.

---

## CacheHitRate

### What It Is

`CacheHitRate` is the percentage of cacheable requests for which CloudFront served the object from its cache.

CloudFront excludes `POST`, `PUT`, and errors from cacheable requests for this metric. Its valid statistic is `Average`. :contentReference[oaicite:12]{index=12}

Conceptually:

```text
CacheHitRate
    =
Cache Hits
------------
Cacheable Requests
```

For example:

```text
Cacheable Requests = 1,000,000
Cache Hits         =   850,000

CacheHitRate = 85%
```

### Why It Matters

A higher cache hit ratio can reduce:

- Origin requests.
- Application CPU.
- Database load.
- Redis traffic.
- Origin bandwidth.
- Origin latency.

CloudFront's caching model is explicitly designed to reduce the number of requests that the origin must serve directly. :contentReference[oaicite:13]{index=13}

Consider:

```text
Without effective caching:

1,000,000 viewer requests
        │
        ▼
1,000,000 origin requests
```

Versus:

```text
85% cache hit rate:

1,000,000 viewer requests
        │
        ├── 850,000 cache hits
        │
        └── 150,000 origin requests
```

### Important Caveat

A higher cache hit rate is not automatically better.

Incorrect cache configuration can expose:

- Personalized content.
- User-specific responses.
- Authorization-sensitive content.
- Stale data.

Cache efficiency must always be evaluated alongside correctness and security.

### Cache Hit Ratio Troubleshooting

When cache hit rate falls, investigate:

- Cache policy.
- Cache key configuration.
- Query strings.
- Cookies.
- Headers.
- TTL.
- `Cache-Control` headers.
- Object versioning.
- Frequent invalidations.
- Origin Shield configuration.

CloudFront recommends practical measures such as appropriate cache lifetimes and Origin Shield to improve cache hit ratio where applicable. :contentReference[oaicite:14]{index=14}

---

## OriginLatency

### What It Is

`OriginLatency` measures the time from when CloudFront receives a request until it starts providing the response to the network, not the viewer, for requests served from the origin rather than the CloudFront cache.

It represents origin first-byte latency, or time-to-first-byte. The valid CloudWatch statistic is `Percentile`. :contentReference[oaicite:15]{index=15}

The distinction is important.

### Cache Hit

```text
Viewer
  │
  ▼
CloudFront Edge
  │
  ▼
Cached Response
```

There is no origin request and therefore no origin latency for that request.

### Cache Miss

```text
Viewer
  │
  ▼
CloudFront Edge
  │
  ▼
Origin
  │
  ▼
Application
  │
  ▼
Response
```

Origin latency applies to this path.

### Why Percentiles Matter

Consider:

```text
Average = 250 ms
p50     = 120 ms
p95     = 700 ms
p99     = 2,200 ms
```

The average looks relatively healthy, but 1% of requests are taking more than two seconds.

For production systems, p95 and p99 are often more useful than averages when investigating tail latency.

When querying `OriginLatency` through the CloudWatch API, use `ExtendedStatistics` for percentile values rather than `Statistics`. :contentReference[oaicite:16]{index=16}

---

## Status-Specific Error Metrics

Aggregate error metrics are useful for detection but often insufficient for diagnosis.

For example:

```text
5xxErrorRate = 4%
```

does not tell you whether the distribution is experiencing:

```text
502 = 0.1%
503 = 0.2%
504 = 3.7%
```

The status-specific metrics immediately indicate that timeouts are the dominant failure mode.

CloudFront provides additional error-rate metrics for:

```text
401
403
404
502
503
504
```

when additional metrics are enabled. :contentReference[oaicite:17]{index=17}

---

## CloudWatch Statistics

Using the wrong statistic can make a dashboard or alarm misleading.

| Metric | Recommended Statistic |
|---|---|
| `Requests` | `Sum` |
| `BytesDownloaded` | `Sum` |
| `BytesUploaded` | `Sum` |
| `4xxErrorRate` | `Average` |
| `5xxErrorRate` | `Average` |
| `TotalErrorRate` | `Average` |
| `CacheHitRate` | `Average` |
| `401ErrorRate` | `Average` |
| `403ErrorRate` | `Average` |
| `404ErrorRate` | `Average` |
| `502ErrorRate` | `Average` |
| `503ErrorRate` | `Average` |
| `504ErrorRate` | `Average` |
| `OriginLatency` | `Percentile` |

These statistics correspond to CloudFront's documented metric definitions. :contentReference[oaicite:18]{index=18}

### Why This Matters

Counts and percentages represent different kinds of data.

For example:

```text
Requests:
1-minute total = Sum

5xxErrorRate:
percentage during the period = Average
```

Using `Sum` on a percentage metric does not produce a meaningful error percentage.

---

## Querying CloudFront Metrics with AWS CLI

Because CloudFront metrics are available through CloudWatch in `us-east-1`, use that Region when querying them through the AWS CLI. :contentReference[oaicite:19]{index=19}

### List CloudFront Metrics

```bash
aws cloudwatch list-metrics \
  --namespace AWS/CloudFront \
  --region us-east-1
```

### List Request Metrics for a Distribution

```bash
aws cloudwatch list-metrics \
  --namespace AWS/CloudFront \
  --metric-name Requests \
  --dimensions Name=DistributionId,Value=E1234567890ABC \
  --region us-east-1
```

### Retrieve Request Count

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/CloudFront \
  --metric-name Requests \
  --dimensions Name=DistributionId,Value=E1234567890ABC \
  --statistics Sum \
  --period 300 \
  --start-time 2026-08-20T10:00:00Z \
  --end-time 2026-08-20T11:00:00Z \
  --region us-east-1
```

### Retrieve 5xx Error Rate

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/CloudFront \
  --metric-name 5xxErrorRate \
  --dimensions Name=DistributionId,Value=E1234567890ABC \
  --statistics Average \
  --period 300 \
  --start-time 2026-08-20T10:00:00Z \
  --end-time 2026-08-20T11:00:00Z \
  --region us-east-1
```

### Retrieve Origin Latency Percentile

For percentile statistics, CloudFront requires the CloudWatch API's `ExtendedStatistics` parameter. :contentReference[oaicite:20]{index=20}

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/CloudFront \
  --metric-name OriginLatency \
  --dimensions Name=DistributionId,Value=E1234567890ABC \
  --extended-statistics p95 \
  --period 300 \
  --start-time 2026-08-20T10:00:00Z \
  --end-time 2026-08-20T11:00:00Z \
  --region us-east-1
```

For automation, prefer `get-metric-data` when retrieving multiple related metrics in one request.

---

## Infrastructure as Code

Additional metrics can be enabled using CloudFormation through the `AWS::CloudFront::MonitoringSubscription` resource. :contentReference[oaicite:21]{index=21}

A minimal CloudFormation resource looks like:

```yaml
Resources:
  CloudFrontMonitoring:
    Type: AWS::CloudFront::MonitoringSubscription
    Properties:
      DistributionId: !Ref CloudFrontDistribution
      MonitoringSubscription:
        RealtimeMetricsSubscriptionConfig:
          RealtimeMetricsSubscriptionStatus: Enabled
```

The exact CloudFormation property names should be validated against the current CloudFormation resource specification before deployment.

For CDK, CloudFront distributions can also publish additional metrics through the distribution configuration. For example, the AWS CDK CloudFront construct exposes metrics such as origin latency and cache hit rate when additional metrics are enabled. :contentReference[oaicite:22]{index=22}

The operational recommendation is to manage monitoring configuration through the same IaC workflow as the distribution itself.

---

## Building a Production Dashboard

A CloudFront dashboard should answer operational questions rather than simply display every available metric.

### Traffic

```text
Requests
BytesDownloaded
BytesUploaded
```

### Reliability

```text
4xxErrorRate
5xxErrorRate
TotalErrorRate
```

### Cache

```text
CacheHitRate
```

### Origin Performance

```text
OriginLatency p50
OriginLatency p95
OriginLatency p99
```

### Failure Classification

```text
401ErrorRate
403ErrorRate
404ErrorRate
502ErrorRate
503ErrorRate
504ErrorRate
```

A practical dashboard can be organized as:

```text
┌────────────────────────────────────────────────────┐
│                CloudFront Overview                 │
├───────────────────────┬────────────────────────────┤
│ Requests              │ Bytes Downloaded           │
├───────────────────────┼────────────────────────────┤
│ 4xx Error Rate        │ 5xx Error Rate             │
├───────────────────────┼────────────────────────────┤
│ Total Error Rate      │ Cache Hit Rate             │
├───────────────────────┼────────────────────────────┤
│ Origin Latency p95    │ Origin Latency p99         │
├───────────────────────┼────────────────────────────┤
│ 403 / 404             │ 502 / 503 / 504            │
└───────────────────────┴────────────────────────────┘
```

The dashboard should make it possible to answer:

> Is the problem at the edge, cache, origin, or application?

---

## Alerting Strategy

Not every metric should generate an alert.

An alert should represent a condition requiring action.

### Availability Alert

For example:

```text
5xxErrorRate > 2%
for 5 consecutive minutes
```

The exact threshold should be based on the application's normal error rate and SLO.

### Latency Alert

For example:

```text
OriginLatency p95 > 1 second
for 5 minutes
```

Again, the threshold should come from the application's expected latency rather than an arbitrary value.

### Cache Regression Alert

For a highly cacheable static workload:

```text
CacheHitRate < 70%
for 15 minutes
```

may be useful.

For a dynamic API, the same threshold may be meaningless.

### Avoid Static Thresholds Without Context

This is weak:

```text
Requests > 1,000
```

This is better:

```text
Requests > expected baseline
AND
5xxErrorRate > error budget threshold
```

CloudWatch alarms can be created for CloudFront metrics, including `5xxErrorRate`. AWS documents alarms such as a percentage threshold sustained for a defined period. :contentReference[oaicite:23]{index=23}

---

## Metric Relationships

Individual metrics become significantly more useful when interpreted together.

### Origin Overload

```text
Requests            ↑↑
CacheHitRate        ↓
OriginLatency       ↑↑
5xxErrorRate        ↑
```

Likely sequence:

```text
Viewer traffic increases
        ↓
Cache misses increase
        ↓
Origin requests increase
        ↓
Application load increases
        ↓
Origin latency increases
        ↓
5xx errors increase
```

### Authorization or WAF Problem

```text
Requests            ─
4xxErrorRate        ↑↑
403ErrorRate        ↑↑
5xxErrorRate        ─
```

Investigate:

- AWS WAF rules.
- Signed URLs.
- Signed cookies.
- Origin access controls.
- CloudFront behavior configuration.
- Application authorization.

### Backend Timeout

```text
Requests            ─
CacheHitRate        ─
OriginLatency       ↑↑
504ErrorRate        ↑↑
5xxErrorRate        ↑
```

Investigate:

- ALB.
- Nginx.
- Django.
- FastAPI.
- PostgreSQL.
- Redis.
- External APIs.
- Origin timeout configuration.

---

## CloudFront Metrics and Backend Architecture

Consider a typical backend architecture:

```mermaid
flowchart TD
    User[Client] --> CF[CloudFront]

    CF -->|Cache Hit| Edge[Edge Response]
    CF -->|Cache Miss| ALB[Application Load Balancer]

    ALB --> Nginx[Nginx / Ingress]
    Nginx --> API[Django / FastAPI]

    API --> Redis[(Redis)]
    API --> DB[(PostgreSQL)]
    API --> Kafka[Kafka]
    API --> External[External API]

    CF -.-> CFMetrics[CloudFront Metrics]
    ALB -.-> ALBMetrics[ALB Metrics]
    API -.-> AppMetrics[Application Metrics]
    DB -.-> DBMetrics[Database Metrics]
```

Map CloudFront signals to the next investigation layer:

| CloudFront Signal | Investigate Next |
|---|---|
| `Requests` ↑ | Traffic source, WAF, capacity |
| `BytesDownloaded` ↑ | Response size, media, traffic pattern |
| `4xxErrorRate` ↑ | Routing, authentication, authorization, WAF |
| `403ErrorRate` ↑ | WAF, signed URL/cookie, access controls |
| `404ErrorRate` ↑ | Paths, deployments, routing, origin |
| `5xxErrorRate` ↑ | Origin, ALB, application, dependencies |
| `502ErrorRate` ↑ | Origin connectivity and backend response |
| `503ErrorRate` ↑ | Origin availability and capacity |
| `504ErrorRate` ↑ | Origin latency and timeout behavior |
| `CacheHitRate` ↓ | Cache policy, cache key, TTL, invalidations |
| `OriginLatency` ↑ | ALB, application, database, dependencies |

---

## CacheHitRate and Origin Load

One of the most important relationships in CloudFront operations is the relationship between cache efficiency and origin load.

```text
CacheHitRate ↓
      ↓
Cache Misses ↑
      ↓
Origin Requests ↑
      ↓
Application Load ↑
      ↓
Database / Redis Load ↑
      ↓
Latency ↑
      ↓
Potential 5xx ↑
```

For example:

```text
Before deployment:

CacheHitRate = 92%
Origin Load  = 80,000 req/min
```

After a cache-policy change:

```text
CacheHitRate = 35%
Origin Load  = 650,000 req/min
```

The backend application may not have changed at all. A cache-key or TTL regression can turn a healthy origin into an overloaded one.

This is why cache configuration changes should be treated as production-impacting changes and validated through metrics.

---

## OriginLatency and Backend Latency

`OriginLatency` should not be interpreted as pure application execution time.

Consider:

```text
CloudFront OriginLatency p95 = 1,200 ms
ALB TargetResponseTime p95   = 1,150 ms
Application p95              = 1,100 ms
PostgreSQL p95               =   900 ms
```

This suggests database latency is contributing materially to the request path.

Now consider:

```text
CloudFront OriginLatency p95 = 1,200 ms
ALB TargetResponseTime p95   =   200 ms
```

The investigation should move toward other parts of the request path rather than immediately blaming the application.

A senior engineer should correlate:

```text
CloudFront
    ↓
ALB
    ↓
Nginx / Ingress
    ↓
Application
    ↓
Redis / PostgreSQL / external APIs
```

instead of assuming the highest-level metric identifies the root cause.

---

## Metrics vs Logs

Metrics and logs answer different operational questions.

| Telemetry | Best For |
|---|---|
| Metrics | Trends, alerts, dashboards |
| CloudFront standard access logs | Request-level historical analysis |
| CloudFront real-time logs | Near-real-time request analysis |
| WAF logs | Security decisions |
| Application logs | Exceptions and application state |
| Distributed traces | Cross-service latency |

A practical investigation flow is:

```text
Metric detects anomaly
        ↓
Dashboard identifies affected component
        ↓
Access logs identify affected requests
        ↓
Application/origin logs identify failure
        ↓
Trace identifies latency path
```

CloudFront also provides cache statistics reports that expose hit, miss, error, status-code, and byte-level information useful for deeper cache analysis. :contentReference[oaicite:24]{index=24}

---

## Metrics and Cache Statistics

CloudWatch metrics provide high-level distribution-level signals, while CloudFront cache statistics and logs can provide additional detail.

Cache statistics include concepts such as:

- `HitCount`
- `MissCount`
- `ErrorCount`
- `IncompleteDownloadCount`
- `HTTP2xx`
- `HTTP3xx`
- `HTTP4xx`
- `HTTP5xx`
- `TotalBytes`
- `BytesFromMisses`

`BytesFromMisses` can approximate the bytes transferred from the origin to CloudFront edge caches, although it does not include every origin-transfer scenario. :contentReference[oaicite:25]{index=25}

This distinction is useful when investigating whether an origin is overloaded because CloudFront is fetching too many objects.

---

## Metrics and Error Caching

CloudFront can cache certain 4xx and 5xx responses.

The error caching behavior depends on factors including:

- HTTP status code.
- Error caching minimum TTL.
- Origin `Cache-Control` headers.
- Whether a custom error response is configured.

CloudFront documents a default error caching minimum TTL of 10 seconds and explains that subsequent requests may receive the cached error until the configured error-caching period expires. :contentReference[oaicite:26]{index=26}

This creates an important monitoring consideration:

```text
Origin recovers
      ↓
CloudFront still has cached error
      ↓
Viewer continues receiving error
```

A long error-cache duration can therefore make a recovered origin appear unhealthy for longer than it actually is.

Conversely, aggressive disabling of error caching can increase origin load during incidents.

Error caching should therefore be configured deliberately.

---

## CloudFront Metrics and SLOs

CloudFront metrics can contribute to service-level indicators, but they should not automatically become the entire SLO.

For example:

```text
Availability SLO:
99.9% successful viewer requests

Latency SLO:
p95 origin latency < 500 ms

Caching Objective:
CacheHitRate > 85% for static assets
```

The exact values should be derived from workload requirements.

A CDN can appear healthy while the origin is unhealthy:

```text
CloudFront:
5xx = 0%

Origin:
Database unavailable
```

If CloudFront continues serving cached objects successfully, CloudFront may show healthy metrics even though dynamic requests are failing.

Therefore:

```text
User-facing SLO
       ↓
CloudFront
       ↓
ALB
       ↓
Application
       ↓
Dependencies
```

should be monitored as a complete service rather than as isolated infrastructure components.

---

## Cost Considerations

Default CloudFront distribution metrics are included for all distributions.

Additional distribution metrics incur a fixed CloudWatch metric charge when enabled. AWS states that CloudFront sends up to eight additional metrics to CloudWatch in `us-east-1`, with the charge applying per metric per month rather than scaling with the distribution's request volume. Additional CloudWatch API retrieval charges can also apply. :contentReference[oaicite:27]{index=27}

This makes additional metrics particularly attractive for production-critical distributions where deeper diagnostic visibility has operational value.

A reasonable decision framework is:

| Workload | Recommended Monitoring |
|---|---|
| Personal/static site | Default metrics may be sufficient |
| Internal application | Default + selected additional metrics |
| Production API | Cache, latency, and status-specific metrics |
| Business-critical API | Full distribution observability + logs + origin telemetry |
| High-traffic platform | Metrics + logs + traces + automated alerting |

The decision should be based on:

- Business criticality.
- SLO requirements.
- Incident frequency.
- Troubleshooting requirements.
- Distribution complexity.
- Monitoring budget.

---

## Operational Dashboard Design

A production CloudFront dashboard should have four layers.

### Traffic Layer

```text
Requests
BytesDownloaded
BytesUploaded
```

Question answered:

> How much traffic are we serving?

### Reliability Layer

```text
4xxErrorRate
5xxErrorRate
TotalErrorRate
```

Question answered:

> Are users receiving errors?

### Performance Layer

```text
CacheHitRate
OriginLatency p50
OriginLatency p95
OriginLatency p99
```

Question answered:

> Is CloudFront effectively serving traffic and is the origin responding quickly?

### Diagnostic Layer

```text
401ErrorRate
403ErrorRate
404ErrorRate
502ErrorRate
503ErrorRate
504ErrorRate
```

Question answered:

> What class of failure is increasing?

This hierarchy is more useful than a dashboard containing dozens of unrelated graphs.

---

## Production Alerting Recommendations

### Critical

Alert immediately or page when:

```text
5xxErrorRate
```

exceeds the application's error-budget threshold for a sustained period.

### High Priority

Alert when:

```text
OriginLatency p95
```

exceeds the service latency objective for a sustained period.

### Medium Priority

Alert on:

```text
CacheHitRate
```

when a meaningful regression occurs for a workload expected to be highly cacheable.

### Security-Oriented

Alert on unusual:

```text
403ErrorRate
401ErrorRate
```

when they may indicate authentication, authorization, WAF, or abuse-related issues.

### Avoid Alert Fatigue

Do not create alarms for every metric.

An alert should answer:

> What action should an engineer take if this alarm fires?

If there is no clear operational action, the metric may belong on a dashboard rather than in the paging path.

---

## Common Mistakes

### Looking in the Wrong AWS Region

**Problem:**

The engineer opens CloudWatch in the application's region and cannot find CloudFront metrics.

**Cause:**

CloudFront metrics are published to CloudWatch in `us-east-1`. :contentReference[oaicite:28]{index=28}

**Fix:**

```bash
aws cloudwatch list-metrics \
  --namespace AWS/CloudFront \
  --region us-east-1
```

---

### Treating Every 4xx as an Infrastructure Failure

A high 4xx rate may be caused by:

- Invalid requests.
- Missing objects.
- WAF rules.
- Authentication failures.
- Authorization failures.
- Signed URL/cookie problems.
- Application routing.

Investigate the specific status code before escalating an infrastructure incident.

---

### Treating Every 5xx as a CloudFront Failure

A CloudFront `5xxErrorRate` increase does not automatically mean CloudFront itself is failing.

Correlate it with:

```text
OriginLatency
502ErrorRate
503ErrorRate
504ErrorRate
ALB metrics
Application metrics
Database metrics
```

---

### Ignoring CacheHitRate

A cache-policy regression can dramatically increase origin traffic.

```text
CacheHitRate ↓
      ↓
Origin requests ↑
      ↓
Backend load ↑
      ↓
Latency ↑
      ↓
5xx ↑
```

A backend outage can therefore originate from what appears to be a CDN configuration change.

---

### Using Average Latency Only

Average latency can hide severe tail latency.

Prefer:

```text
p50
p95
p99
```

when evaluating `OriginLatency`.

---

### Maximizing CacheHitRate Without Considering Correctness

A higher hit ratio is valuable only when the cached content is safe and semantically correct.

Do not optimize cache efficiency by accidentally caching:

- User-specific responses.
- Authentication responses.
- Authorization-sensitive content.
- Rapidly changing data that requires freshness.

---

### Ignoring Error Caching

CloudFront can cache origin error responses.

A recovered origin can therefore remain apparently unhealthy until the cached error expires. :contentReference[oaicite:29]{index=29}

When diagnosing a persistent error:

```text
Check origin
+
Check CloudFront error caching
+
Check cached error behavior
```

---

### Using the Wrong CloudWatch Statistic

For example:

```text
Requests → Average
```

is not the same operational question as:

```text
Requests → Sum
```

Likewise:

```text
OriginLatency → Percentile
```

is more appropriate than treating it as a simple count metric.

Use the statistic documented for the metric. :contentReference[oaicite:30]{index=30}

---

### Alerting on Tiny Traffic Volumes

A small distribution can produce misleading percentages.

For example:

```text
Requests = 2
Failures = 1

Error rate = 50%
```

A 50% error rate sounds severe but represents only two requests.

For low-volume workloads, combine error-rate conditions with minimum request volume or use anomaly-aware alerting.

---

## Interview Questions

### What is the difference between `Requests` and `BytesDownloaded`?

`Requests` measures viewer request count, while `BytesDownloaded` measures the number of bytes downloaded for applicable `GET` and `HEAD` requests.

The two metrics describe different dimensions of traffic volume.

---

### What does `CacheHitRate` measure?

It measures the percentage of cacheable requests for which CloudFront serves the content from its cache. `POST`, `PUT`, and errors are not considered cacheable for this metric. :contentReference[oaicite:31]{index=31}

---

### Does a high cache hit ratio always mean the system is healthy?

No.

A high cache hit ratio can coexist with:

- Incorrect caching.
- Stale content.
- Security problems.
- An unhealthy origin.

Cache efficiency and application correctness are separate concerns.

---

### What does `OriginLatency` measure?

It measures the time from CloudFront receiving a request until CloudFront starts providing the response to the network for requests served from the origin.

It is an origin first-byte latency measurement, not a complete end-user latency measurement. :contentReference[oaicite:32]{index=32}

---

### Why should `OriginLatency` be analyzed using percentiles?

Latency distributions are usually skewed.

For example:

```text
p50 = 100 ms
p95 = 500 ms
p99 = 2,000 ms
```

The average can hide the slow tail that affects a significant subset of users.

---

### Why is `Region=Global` different from the CloudWatch API Region?

CloudFront is a global service, so the distribution metric dimension uses `Region=Global`.

CloudFront sends these metrics to the CloudWatch service endpoint in `us-east-1`, so CloudWatch API and CLI queries must use that Region. :contentReference[oaicite:33]{index=33}

---

### Why can a cache regression cause an application outage?

Because lower cache efficiency causes more requests to reach the origin:

```text
CacheHitRate ↓
    ↓
Origin requests ↑
    ↓
Application load ↑
    ↓
Database / Redis load ↑
    ↓
Latency ↑
    ↓
Timeouts / 5xx ↑
```

The application code may be unchanged while the traffic reaching it changes dramatically.

---

### What is the difference between metrics and CloudFront logs?

Metrics are optimized for:

- Aggregation.
- Dashboards.
- Trends.
- Alerting.

Logs are better for:

- Individual requests.
- URLs.
- Status codes.
- Request-level investigation.
- Detailed failure analysis.

A production troubleshooting workflow generally uses both.

---

## Production Troubleshooting Workflow

When a CloudFront incident begins, avoid jumping directly into configuration changes.

Use a structured sequence.

### Establish the Time Window

Identify:

```text
Incident start
Incident end/current time
Affected distribution
Affected behavior/path
Affected users/regions
```

### Check Traffic

Inspect:

```text
Requests
BytesDownloaded
BytesUploaded
```

Determine whether traffic changed before the failure.

### Check Error Rates

Inspect:

```text
4xxErrorRate
5xxErrorRate
TotalErrorRate
```

Then break the problem down using:

```text
401
403
404
502
503
504
```

where enabled.

### Check Cache Behavior

Inspect:

```text
CacheHitRate
```

Determine whether origin traffic may have increased because of a cache regression.

### Check Origin Performance

Inspect:

```text
OriginLatency p95
OriginLatency p99
```

Then correlate with:

```text
ALB
Nginx
Django / FastAPI
PostgreSQL
Redis
External APIs
```

### Inspect Logs

Use logs when metrics identify the affected layer but do not explain the cause.

A useful progression is:

```text
CloudFront metrics
       ↓
CloudFront logs
       ↓
ALB logs
       ↓
Application logs
       ↓
Database / dependency telemetry
```

### Verify Configuration Changes

Check recent changes to:

- CloudFront behaviors.
- Cache policies.
- Origin request policies.
- Response headers policies.
- WAF rules.
- Signed URL/cookie configuration.
- TLS configuration.
- Origins.
- Error responses.
- TTLs.
- Invalidations.

### Avoid Blind Rollbacks

A rollback should follow evidence.

For example:

```text
CacheHitRate ↓ immediately after cache-policy deployment
        +
Origin Requests ↑
        +
Origin CPU ↑
```

is strong evidence that the deployment affected caching.

Without such correlation, rolling back unrelated infrastructure can make the incident harder to diagnose.

---

## Production Monitoring Checklist

### Default Metrics

- [ ] `Requests` monitored
- [ ] `BytesDownloaded` monitored
- [ ] `BytesUploaded` monitored where relevant
- [ ] `4xxErrorRate` monitored
- [ ] `5xxErrorRate` monitored
- [ ] `TotalErrorRate` monitored

### Additional Metrics

- [ ] `CacheHitRate` enabled where useful
- [ ] `OriginLatency` enabled where useful
- [ ] Status-specific error metrics enabled where useful
- [ ] Additional metric cost evaluated
- [ ] Metric configuration managed through IaC where practical

### Dashboards

- [ ] Traffic dashboard configured
- [ ] Error-rate dashboard configured
- [ ] Cache-efficiency dashboard configured
- [ ] Origin-latency dashboard configured
- [ ] Status-specific failures visible
- [ ] CloudFront metrics correlated with origin metrics

### Alerting

- [ ] 5xx alerts use sustained thresholds
- [ ] 4xx alerts are workload-aware
- [ ] Low-volume false positives are controlled
- [ ] Origin latency alerts use percentiles
- [ ] Cache regression alerts use workload-specific thresholds
- [ ] Security-related error spikes are monitored where appropriate

### Troubleshooting

- [ ] CloudWatch queries use `us-east-1`
- [ ] Distribution ID is known
- [ ] CloudFront metrics are correlated with ALB metrics
- [ ] Application metrics are available
- [ ] Database and Redis metrics are available
- [ ] CloudFront logs are available when required
- [ ] WAF telemetry is available where applicable
- [ ] Recent CloudFront configuration changes are auditable
- [ ] Error caching behavior is understood

## Key Takeaways

- **CloudFront metrics form the first layer of CDN observability:** use traffic, error, cache, and origin-latency metrics together rather than treating any single metric as a complete health signal.
- **Know the metric semantics and statistics:** counts such as `Requests` use `Sum`, percentage metrics generally use `Average`, and `OriginLatency` is evaluated using percentiles. :contentReference[oaicite:34]{index=34}
- **CloudFront is global but CloudWatch queries use `us-east-1`:** distribution metrics use the `AWS/CloudFront` namespace and `Region=Global`, while CloudWatch console/API operations use US East (N. Virginia). :contentReference[oaicite:35]{index=35}
- **Cache efficiency directly affects backend capacity:** a cache-hit regression can increase origin traffic, application load, database pressure, latency, and eventually 5xx errors.
- **Metrics identify anomalies; logs and origin telemetry identify causes:** production troubleshooting should correlate CloudFront metrics with CloudFront logs, ALB metrics, application telemetry, and downstream dependencies.