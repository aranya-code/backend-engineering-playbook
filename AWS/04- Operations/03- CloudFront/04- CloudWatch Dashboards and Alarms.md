# 04- CloudWatch Dashboards and Alarms

## Overview

CloudFront exposes operational metrics through Amazon CloudWatch. These metrics provide the first layer of observability for request volume, cache behavior, viewer errors, origin failures, and origin latency.

For production systems, the goal is not to collect every available metric. The goal is to build an observability model that answers three operational questions quickly:

- **Is CloudFront healthy?**
- **Are users experiencing failures or degraded performance?**
- **Is the problem at the CDN, viewer, origin, or downstream application layer?**

A useful CloudFront monitoring architecture is:

```text
                         CloudFront
                             │
             ┌───────────────┼────────────────┐
             │               │                │
             ▼               ▼                ▼
        CloudWatch       Access Logs      Real-Time Logs
             │               │                │
             ▼               ▼                ▼
        Dashboards         S3/Athena        Kinesis
             │
             ▼
           Alarms
             │
             ▼
      SNS / Incident System
```

CloudWatch metrics are aggregated signals. Logs provide request-level evidence. Application telemetry provides deeper root-cause information.

A mature troubleshooting workflow therefore looks like:

```text
CloudWatch Alarm
      ↓
CloudFront Metrics
      ↓
CloudFront Logs
      ↓
ALB / Nginx / Ingress
      ↓
Django / FastAPI
      ↓
PostgreSQL / Redis / Kafka / External APIs
```

---

## CloudFront Metrics in CloudWatch

CloudFront publishes metrics to CloudWatch under the `AWS/CloudFront` namespace.

CloudFront metrics are generally associated with a distribution and are available for operational monitoring and dashboards.

Commonly monitored metrics include:

| Metric | What it indicates | Typical use |
|---|---|---|
| `Requests` | Number of viewer requests | Traffic monitoring |
| `BytesDownloaded` | Data sent to viewers | Bandwidth monitoring |
| `BytesUploaded` | Data uploaded from viewers | Upload traffic monitoring |
| `4xxErrorRate` | Percentage of requests returning 4xx | Viewer/client-side failure detection |
| `5xxErrorRate` | Percentage of requests returning 5xx | Origin/CDN failure detection |
| `TotalErrorRate` | Combined error rate | Overall availability signal |
| `CacheHitRate` | Percentage of cacheable requests served from cache | Cache efficiency |
| `OriginLatency` | Time CloudFront spends obtaining a response from origin | Origin performance |
| `OriginShieldHitRate` | Cache effectiveness at Origin Shield where applicable | Origin-load analysis |
| `OriginRequests` | Requests forwarded to the origin | Origin traffic analysis |

The exact metric availability and dimensions should be verified against the current CloudFront and CloudWatch service documentation for the distribution and feature being monitored.

---

## Why Metrics Matter

Metrics compress large volumes of requests into measurable signals.

Suppose a distribution handles:

```text
10 million requests/hour
```

Inspecting individual requests is impractical.

CloudWatch can instead show:

```text
Requests        = 10,000,000
4xxErrorRate    = 0.8%
5xxErrorRate    = 0.03%
CacheHitRate    = 94%
OriginLatency   = 120 ms
```

This immediately gives an operational picture.

The important engineering distinction is:

> Metrics tell you that something changed; logs and traces help explain why.

---

## Core CloudFront Metrics

## Requests

`Requests` represents viewer request volume.

It is useful for:

- Traffic dashboards.
- Capacity analysis.
- Traffic anomaly detection.
- Deployment comparison.
- Traffic forecasting.

A sudden increase may indicate:

- A legitimate traffic spike.
- A marketing event.
- A crawler.
- A bot attack.
- A cache behavior change.
- A client retry loop.

Do not interpret increased traffic as an incident by itself.

Correlate traffic with:

```text
Requests
   +
4xx / 5xx
   +
CacheHitRate
   +
OriginRequests
   +
OriginLatency
```

---

## BytesDownloaded

`BytesDownloaded` measures data CloudFront sends to viewers.

It is useful for identifying:

- Bandwidth spikes.
- Large responses.
- Unexpected media traffic.
- Download-heavy endpoints.
- Potential abuse.

For example:

```text
Requests stable
BytesDownloaded ↑ sharply
```

may indicate that response sizes increased rather than request volume increasing.

This can happen after:

- A frontend bundle change.
- Image optimization regression.
- Compression changes.
- API response expansion.
- A new downloadable asset.

---

## BytesUploaded

`BytesUploaded` is useful for workloads involving uploads through CloudFront.

A sudden increase can indicate:

- Increased upload activity.
- Large request payloads.
- Misconfigured clients.
- Unexpected API usage.
- Abuse.

For API-heavy architectures, compare upload traffic with application-level request metrics.

---

## 4xxErrorRate

`4xxErrorRate` measures the percentage of requests returning HTTP 4xx responses.

Examples include:

```text
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
405 Method Not Allowed
```

A high 4xx rate does not necessarily mean CloudFront is unhealthy.

It may represent:

- Invalid client requests.
- Authentication failures.
- Missing resources.
- WAF blocks.
- Incorrect application routes.
- Client-side bugs.

For example:

```text
4xxErrorRate = 15%
5xxErrorRate = 0%
```

could indicate a client or security issue rather than an availability failure.

---

## 5xxErrorRate

`5xxErrorRate` is one of the most important CloudFront availability indicators.

Examples include:

```text
500 Internal Server Error
502 Bad Gateway
503 Service Unavailable
504 Gateway Timeout
```

A sustained increase should normally trigger investigation.

A useful decomposition is:

```text
5xx increase
     │
     ├── CloudFront configuration?
     │
     ├── Origin availability?
     │
     ├── Origin latency?
     │
     ├── Network connectivity?
     │
     └── Application dependency?
```

Do not immediately assume that a CloudFront 5xx is caused by CloudFront itself.

---

## TotalErrorRate

`TotalErrorRate` combines 4xx and 5xx responses into a broader error signal.

It can be useful for:

- High-level availability dashboards.
- Broad health monitoring.
- Executive operational reporting.

However, it can hide the difference between:

```text
4xx = client/security problem
5xx = server/origin problem
```

For production alerting, monitor 4xx and 5xx separately when possible.

---

## CacheHitRate

`CacheHitRate` is one of the most important performance metrics for a cache-backed CloudFront architecture.

It indicates how effectively CloudFront is serving requests from cache.

Conceptually:

```text
CacheHitRate =
    Cache Hits
    -----------------------
    Cache Hits + Cache Misses
```

A high cache hit ratio generally means fewer requests reach the origin.

For example:

```text
Before deployment:
CacheHitRate = 95%

After deployment:
CacheHitRate = 61%
```

This may indicate:

- Cache key changed.
- Query strings became part of the cache key.
- Cookies became part of the cache key.
- Cache policy changed.
- TTL decreased.
- Objects became effectively uncacheable.
- Request paths changed.

CacheHitRate must always be interpreted together with the workload.

Dynamic APIs may legitimately have low cacheability.

---

## OriginLatency

`OriginLatency` measures the time CloudFront spends obtaining a response from the origin.

It is particularly useful for distinguishing:

```text
CloudFront performance
```

from:

```text
Origin performance
```

For example:

```text
Viewer-facing latency ↑
OriginLatency ↑
```

strongly suggests that the origin path should be investigated.

Possible causes include:

- Slow Django/FastAPI handlers.
- PostgreSQL contention.
- Redis latency.
- External API latency.
- Nginx/ALB saturation.
- Container CPU exhaustion.
- Connection pool exhaustion.
- Kubernetes scheduling/resource issues.

---

## OriginRequests

`OriginRequests` indicates how much traffic CloudFront is forwarding to origins.

This metric becomes especially useful when combined with cache metrics.

For example:

```text
Viewer Requests      = 1,000,000
Origin Requests      =   900,000
CacheHitRate         = low
```

This may indicate that CloudFront is providing little caching benefit.

Conversely:

```text
Viewer Requests      = 1,000,000
Origin Requests      =    50,000
CacheHitRate         = high
```

means the CDN is absorbing most viewer traffic.

This distinction is important because origin load directly affects backend infrastructure.

---

## Origin Shield Metrics

If Origin Shield is enabled, monitor its effectiveness where applicable.

Origin Shield adds an additional centralized caching layer between CloudFront edge locations and the origin.

Conceptually:

```text
Viewer
   ↓
CloudFront Edge
   ↓
Origin Shield
   ↓
Origin
```

A useful monitoring question is:

> Is Origin Shield reducing origin traffic as expected?

Monitor Origin Shield-related metrics together with:

- OriginRequests.
- CacheHitRate.
- Origin latency.
- Origin errors.

Do not enable Origin Shield solely because it exists. Evaluate whether the workload benefits from the additional layer and operational complexity.

---

## Metric Relationships

Individual metrics become significantly more useful when correlated.

### Example: Origin Problem

```text
Requests            → normal
CacheHitRate        → normal
5xxErrorRate        → ↑
OriginLatency       → ↑
OriginRequests      → normal
```

Likely investigation area:

```text
Origin / application
```

### Example: Cache Regression

```text
Requests            → normal
CacheHitRate        → ↓
OriginRequests      → ↑
OriginLatency       → normal
5xxErrorRate        → normal
```

Likely investigation area:

```text
Cache policy / cache key / TTL
```

### Example: Traffic Abuse

```text
Requests            → ↑↑
4xxErrorRate        → ↑
5xxErrorRate        → normal
CacheHitRate        → variable
```

Likely investigation area:

```text
WAF / client behavior / bot traffic
```

---

## CloudWatch Dashboard Design

A dashboard should be optimized for incident detection and diagnosis rather than displaying every available metric.

A useful CloudFront dashboard can be organized into four sections:

```text
┌──────────────────────────────────────────┐
│ Traffic                                  │
│ Requests | Bytes | Origin Requests       │
├──────────────────────────────────────────┤
│ Errors                                   │
│ 4xx | 5xx | Total Error Rate             │
├──────────────────────────────────────────┤
│ Performance                              │
│ Cache Hit Rate | Origin Latency           │
├──────────────────────────────────────────┤
│ Operational Context                      │
│ Deployments | WAF | Origin Health        │
└──────────────────────────────────────────┘
```

This structure allows an engineer to move from:

```text
What happened?
```

to:

```text
Where is it happening?
```

to:

```text
What changed?
```

---

## Recommended Dashboard Widgets

A production dashboard should normally include:

| Widget | Metrics | Purpose |
|---|---|---|
| Traffic | Requests | Traffic volume |
| Bandwidth | BytesDownloaded | Data transfer |
| Viewer Errors | 4xxErrorRate | Client/security issues |
| Origin Errors | 5xxErrorRate | Backend availability |
| Overall Errors | TotalErrorRate | Broad health |
| Cache | CacheHitRate | CDN efficiency |
| Origin Load | OriginRequests | Backend traffic |
| Origin Performance | OriginLatency | Backend latency |
| WAF | Block/allow metrics | Security context |
| Deployment Context | Deployment markers | Change correlation |

Avoid making one enormous dashboard containing dozens of unrelated graphs.

---

## Dashboard Time Ranges

The dashboard should support multiple investigation windows.

Typical ranges:

| Time range | Use |
|---|---|
| 1 hour | Active incident |
| 3 hours | Recent deployment |
| 24 hours | Daily behavior |
| 7 days | Trend analysis |
| 30 days | Capacity and baseline analysis |

Short time windows are useful for incident response.

Longer windows are useful for identifying baseline behavior.

---

## Establishing Baselines

A threshold without a baseline is often a poor alert.

For example:

```text
5xxErrorRate > 1%
```

may be reasonable for one service and inappropriate for another.

Instead, understand normal behavior:

```text
Normal 5xx:
0.01% - 0.05%

Warning:
> 0.2%

Critical:
> 1%
```

The values above are examples only. Production thresholds should be derived from the actual system's historical behavior and service-level objectives.

---

## CloudWatch Alarms

A CloudWatch alarm evaluates a metric against configured conditions and transitions between states.

Conceptually:

```text
Metric
  │
  ▼
Threshold Evaluation
  │
  ├── OK
  │
  ├── ALARM
  │
  └── INSUFFICIENT_DATA
```

An alarm can then trigger an action such as an SNS notification.

Typical architecture:

```text
CloudFront
    │
    ▼
CloudWatch Metric
    │
    ▼
CloudWatch Alarm
    │
    ▼
SNS
    │
    ├── Email
    ├── Pager / Incident system
    └── Automation
```

---

## Alarm States

### OK

The metric is within the configured acceptable range.

### ALARM

The metric has breached the configured alarm condition for the required evaluation period.

### INSUFFICIENT_DATA

CloudWatch does not have enough data to determine the alarm state.

Do not automatically treat `INSUFFICIENT_DATA` as equivalent to a service outage.

It can occur because:

- The metric has no recent data.
- The workload is idle.
- The metric is newly configured.
- Data publication is delayed.

The correct treatment depends on the metric and operational requirements.

---

## Alarm Configuration

Important alarm parameters include:

| Parameter | Purpose |
|---|---|
| Metric | Signal being evaluated |
| Statistic | How observations are aggregated |
| Period | Metric evaluation interval |
| Threshold | Trigger value |
| Comparison operator | Greater/less-than condition |
| Evaluation periods | Number of periods considered |
| Datapoints to alarm | Required breached datapoints |
| Missing data treatment | Behavior when data is unavailable |
| Actions | What happens after state transition |

Do not choose these values independently.

They should reflect:

```text
Metric behavior
+
Traffic pattern
+
SLO
+
Incident response requirement
```

---

## Choosing Statistics

The correct statistic depends on the metric.

For request counts:

```text
Sum
```

is often meaningful.

For latency:

```text
Average
```

can be useful for broad trend analysis, but average latency can hide tail behavior.

For latency-sensitive systems, also investigate percentile-oriented metrics where available through the relevant telemetry source.

For error rates:

```text
Average
```

is commonly useful when the metric itself is already expressed as a percentage.

The key principle is:

> Choose the statistic that represents the operational question, not the statistic that is easiest to configure.

---

## Alarm Evaluation Periods

Suppose:

```text
Period = 1 minute
Evaluation periods = 5
Threshold = 2%
```

The intent might be:

```text
Require sustained error rate
rather than one isolated spike.
```

This reduces alert noise.

However, too many evaluation periods delay detection.

For a critical API:

```text
Fast detection
```

may be more important than suppressing every transient spike.

---

## M-of-N Alarm Logic

CloudWatch supports alarm configurations where a specified number of datapoints within a larger evaluation window must breach the threshold.

For example:

```text
Evaluation window = 5 periods
Required breaches = 3
```

Conceptually:

```text
[OK] [ALARM] [ALARM] [OK] [ALARM]
             ↑
        3 breaches
             ↓
          ALARM
```

This is useful for balancing:

```text
Sensitivity
vs
Alert noise
```

---

## Recommended CloudFront Alarms

### 5xx Error Alarm

A sustained increase in 5xx responses is usually a high-priority signal.

Example intent:

```text
5xxErrorRate > service threshold
for sustained period
```

Potential response:

```text
CloudWatch
   ↓
SNS
   ↓
On-call
```

### 4xx Error Alarm

4xx alerts require more careful tuning.

A high 4xx rate can represent:

- A broken client deployment.
- Authentication problems.
- WAF changes.
- Bot traffic.
- Routing errors.
- API contract changes.

Treat it as an operational signal rather than automatically classifying it as an availability failure.

### Cache Hit Rate Alarm

A cache hit ratio alarm can detect CDN efficiency regressions.

For example:

```text
CacheHitRate < baseline
```

However, do not alert on a universally fixed threshold without considering the workload.

A dynamic API may have an intentionally low cache hit rate.

### Origin Latency Alarm

Origin latency is valuable for detecting backend degradation before users experience widespread failures.

A practical alerting strategy is to combine:

```text
OriginLatency ↑
+
5xxErrorRate ↑
```

when both signals are available.

---

## Example Alarm Matrix

| Alarm | Severity | Typical response |
|---|---|---|
| 5xx rate sustained high | Critical | Investigate origin immediately |
| 4xx rate suddenly high | Warning/Critical | Investigate clients, WAF, routing |
| Cache hit rate sharply reduced | Warning | Investigate cache policy |
| Origin latency elevated | Warning/Critical | Investigate origin |
| Origin requests unexpectedly high | Warning | Investigate cache regression |
| Bytes downloaded spike | Warning | Investigate traffic/response size |
| Request volume spike | Informational/Warning | Check traffic source and WAF |

Severity should be based on business impact and SLOs rather than the metric name alone.

---

## Example CloudWatch CLI

CloudWatch alarms can be created through the AWS CLI.

A simplified example for a 5xx error-rate alarm:

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name "cloudfront-5xx-rate-high" \
  --namespace "AWS/CloudFront" \
  --metric-name "5xxErrorRate" \
  --dimensions Name=DistributionId,Value=E123EXAMPLE \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 1 \
  --comparison-operator GreaterThanThreshold \
  --treat-missing-data notBreaching \
  --alarm-actions arn:aws:sns:ap-south-1:123456789012:production-alerts
```

The exact dimensions, supported metrics, and configuration should be verified against the current AWS CloudWatch and CloudFront documentation.

Do not copy production thresholds blindly from examples.

---

## Dashboard as Code

For production systems, dashboards and alarms should ideally be managed as infrastructure rather than configured manually.

Possible approaches include:

- AWS CloudFormation.
- AWS CDK.
- Terraform.
- AWS CLI in controlled automation.

For example, a deployment pipeline can manage:

```text
CloudFront distribution
        ↓
CloudWatch alarms
        ↓
CloudWatch dashboard
        ↓
SNS notifications
```

This provides:

- Version control.
- Reviewable changes.
- Repeatability.
- Environment consistency.
- Disaster recovery.

Manual dashboard configuration becomes problematic when multiple environments exist.

---

## Dashboard Environment Separation

Do not accidentally combine development and production signals.

Prefer explicit dashboard separation:

```text
Production CloudFront
Development CloudFront
Staging CloudFront
```

or use clear distribution/environment dimensions.

A production alarm should not trigger because a development distribution is intentionally generating test errors.

---

## Multi-Distribution Monitoring

Organizations often operate multiple CloudFront distributions.

For example:

```text
www.example.com
api.example.com
static.example.com
media.example.com
```

A senior-level monitoring strategy should provide both:

```text
Per-distribution visibility
```

and:

```text
Fleet-level visibility
```

Per-distribution dashboards answer:

> What is wrong with this service?

Fleet dashboards answer:

> Is there a broader infrastructure or configuration issue?

---

## Monitoring the CDN-to-Origin Relationship

CloudFront should never be monitored in isolation.

A useful dashboard correlation is:

```text
CloudFront
├── Requests
├── 4xxErrorRate
├── 5xxErrorRate
├── CacheHitRate
└── OriginLatency

        ↓

ALB
├── RequestCount
├── TargetResponseTime
├── HTTPCode_Target_5XX_Count
└── UnHealthyHostCount

        ↓

Application
├── Request rate
├── Error rate
├── Latency
└── Saturation

        ↓

Dependencies
├── PostgreSQL
├── Redis
├── Kafka
└── External APIs
```

This allows engineers to determine whether:

```text
CloudFront is the source
```

or:

```text
CloudFront is exposing an origin problem.
```

---

## Correlating Deployment Events

A dashboard becomes significantly more useful when deployments can be correlated with metric changes.

For example:

```text
20:00  Deployment
20:03  CacheHitRate ↓
20:04  OriginRequests ↑
20:05  OriginLatency ↑
20:06  5xxErrorRate ↑
```

This sequence strongly suggests a deployment-related regression.

The deployment system can include markers or annotations where supported.

Useful sources include:

- GitHub Actions.
- CI/CD deployment events.
- Kubernetes deployments.
- CloudFormation changes.
- CloudFront configuration changes.

---

## Alert Fatigue

Poorly designed alarms create operational noise.

For example:

```text
5xx > 0.1%
```

with no duration requirement might trigger repeatedly during short transient events.

The result is:

```text
Too many alerts
      ↓
Engineers stop trusting alerts
      ↓
Important alerts are ignored
```

Prefer alerts that represent actionable conditions.

A good alert should answer:

> What should the on-call engineer do now?

If the answer is unclear, the alert may belong on a dashboard rather than as a page.

---

## Alert Design Principles

### Alert on Symptoms

Examples:

```text
High 5xx rate
High latency
High error rate
```

These represent user-visible or system-visible degradation.

### Use Supporting Signals for Diagnosis

Examples:

```text
OriginLatency
OriginRequests
CacheHitRate
WAF metrics
ALB metrics
```

These help explain the symptom.

### Avoid Alerting on Every Low-Level Metric

Not every metric needs an alarm.

For example:

```text
BytesDownloaded
```

may be useful for dashboards without requiring an on-call page.

---

## SLO-Based Alerting

Where possible, CloudFront alarms should support service-level objectives.

For example:

```text
Availability SLO = 99.9%
```

A 5xx alert should reflect the actual error budget rather than an arbitrary threshold.

Similarly:

```text
Latency SLO
Cache efficiency target
```

can inform dashboard and alarm design.

This makes monitoring part of reliability engineering rather than simply infrastructure administration.

---

## Troubleshooting with CloudWatch

When an alarm fires, use a consistent sequence.

### Check the Incident Window

Determine:

```text
Start time
End time
Affected distribution
```

### Check Traffic

Ask:

```text
Did request volume change?
```

If requests increased sharply, determine whether the traffic is expected.

### Check Errors

Compare:

```text
4xxErrorRate
5xxErrorRate
TotalErrorRate
```

### Check Cache

Look at:

```text
CacheHitRate
OriginRequests
```

A cache regression can create origin pressure without any CloudFront configuration being obviously broken.

### Check Origin Performance

Inspect:

```text
OriginLatency
```

Then correlate with:

```text
ALB
Nginx
Django/FastAPI
Database
Redis
External APIs
```

### Check Recent Changes

Investigate:

- CloudFront configuration changes.
- Cache policy changes.
- WAF rule changes.
- DNS changes.
- Application deployments.
- Infrastructure deployments.

---

## Example Incident Analysis

Suppose an alarm reports:

```text
CloudFront 5xxErrorRate > threshold
```

The dashboard shows:

```text
Requests        → normal
4xxErrorRate    → normal
5xxErrorRate    → ↑
CacheHitRate    → normal
OriginLatency   → ↑↑
OriginRequests  → normal
```

The likely path is:

```text
CloudFront
    ↓
Origin latency increased
    ↓
ALB
    ↓
Application latency
    ↓
Database / Redis / external dependency
```

If PostgreSQL latency then shows a corresponding increase, CloudFront is probably not the root cause.

CloudFront is simply the first layer where the failure became visible.

---

## Common Mistakes

### Alerting Only on 5xx

A system can be degraded without generating many 5xx responses.

Examples:

```text
CacheHitRate ↓
OriginLatency ↑
4xxErrorRate ↑
```

Monitor multiple dimensions of health.

### Using Static Thresholds Without Baselines

A fixed:

```text
CacheHitRate < 80%
```

may be meaningless for a workload whose normal cache hit ratio is 60%.

Use historical behavior and SLOs.

### Creating Too Many Alarms

Every metric does not need an alarm.

Too many alarms produce noise and reduce operational trust.

### Ignoring 4xx Errors

A sudden 404 or 403 spike can indicate:

- Broken deployment.
- Incorrect routing.
- WAF rule changes.
- Client regression.
- Attack traffic.

4xx errors are often operationally important even though they are not server errors.

### Monitoring CloudFront Without Monitoring the Origin

CloudFront can report:

```text
5xxErrorRate ↑
OriginLatency ↑
```

while the actual failure exists in:

```text
Django
PostgreSQL
Redis
External API
```

Always correlate layers.

### Treating `INSUFFICIENT_DATA` as Failure

Missing data does not automatically mean the service is unavailable.

Configure missing-data treatment intentionally.

### Building Dashboards Manually

Manual dashboards drift across environments.

Prefer infrastructure-as-code for production observability.

### Using Average Latency Blindly

Average latency can hide tail latency.

If users are experiencing intermittent slow requests, investigate percentile-based latency telemetry where available rather than relying solely on averages.

---

## Security Considerations

CloudWatch dashboards and alarms can expose operational information.

Protect them through:

- Least-privilege IAM.
- Separate production access.
- Appropriate AWS account boundaries.
- Controlled dashboard sharing.
- Restricted alarm modification permissions.

An attacker who can modify alarms could potentially:

- Disable operational alerts.
- Change thresholds.
- Redirect notifications.

Treat observability configuration as production infrastructure.

---

## Scalability Considerations

As traffic grows, the monitoring architecture should scale with the system.

For a small service:

```text
CloudFront
   ↓
CloudWatch
   ↓
SNS
```

may be sufficient.

For a large platform:

```text
CloudFront
   ↓
CloudWatch
   ├── Dashboards
   ├── Alarms
   ├── Composite alarms
   └── Cross-service correlation
             ↓
       Incident platform
```

At fleet scale, standardize:

- Alarm naming.
- Dashboard structure.
- Severity.
- Threshold ownership.
- Notification routing.
- SLO definitions.

---

## High Availability and Reliability

Monitoring itself must be reliable.

Avoid making a single custom monitoring Lambda or consumer the only source of operational visibility.

Use managed CloudWatch metrics and alarms as the foundational layer.

For critical services:

```text
CloudFront metrics
+
CloudWatch alarms
+
Application metrics
+
Logs
+
Tracing
```

provide defense in depth.

A monitoring failure should not become a production failure.

---

## Cost Considerations

CloudWatch usage can generate costs depending on:

- Custom metrics.
- Metric ingestion.
- Dashboard usage.
- Alarm count.
- Logs.
- Queries.
- Retention.
- High-cardinality telemetry.

CloudFront's native metrics should be preferred where they provide the required signal.

Do not create custom metrics for values already available through native CloudFront metrics unless there is a specific analytical requirement.

For custom telemetry, define:

```text
Metric name
Dimensions
Retention
Alert requirement
Owner
```

before creating it.

---

## Production Checklist

### Dashboard

- [ ] Requests monitored
- [ ] Bytes downloaded monitored
- [ ] 4xx error rate monitored
- [ ] 5xx error rate monitored
- [ ] Total error rate available
- [ ] Cache hit rate monitored
- [ ] Origin requests monitored
- [ ] Origin latency monitored
- [ ] WAF context available where relevant
- [ ] Recent deployment context available
- [ ] Production and non-production signals separated

### Alarms

- [ ] Critical 5xx condition has an alarm
- [ ] Important 4xx conditions have appropriate alarms
- [ ] Origin latency has appropriate monitoring
- [ ] Cache regressions are detectable
- [ ] Thresholds are based on baselines or SLOs
- [ ] Evaluation periods are intentional
- [ ] Missing-data behavior is intentional
- [ ] Alarm severity is defined
- [ ] Notifications reach the correct incident system
- [ ] Alarm configuration is version controlled where practical

### Operations

- [ ] CloudFront logs are available
- [ ] Origin logs are available
- [ ] Application metrics are available
- [ ] Database and Redis telemetry is available
- [ ] WAF telemetry is available where relevant
- [ ] Deployment changes can be correlated with incidents
- [ ] Incident responders know the dashboard entry point
- [ ] Alert ownership is defined

## Interview Questions

### Which CloudFront metrics are most important for production monitoring?

A practical baseline includes:

```text
Requests
4xxErrorRate
5xxErrorRate
CacheHitRate
OriginRequests
OriginLatency
BytesDownloaded
```

The exact set depends on the workload.

### Why is `CacheHitRate` important?

A lower cache hit rate means more requests reach the origin, increasing backend load and potentially increasing latency and cost.

### How would you detect an origin problem using CloudFront metrics?

Look for a combination such as:

```text
5xxErrorRate ↑
OriginLatency ↑
```

and correlate it with ALB, application, and dependency metrics.

### Why should 4xx and 5xx alarms be separate?

Because they represent different failure classes.

```text
4xx → client, routing, authentication, or security
5xx → server, origin, infrastructure, or dependency
```

Combining them can hide the actual failure mode.

### Why should you not alert on every CloudFront metric?

Most metrics are useful for analysis but are not individually actionable.

Alert only when a condition represents meaningful user impact, SLO risk, or a required operational response.

### How would you monitor multiple CloudFront distributions?

Use per-distribution dashboards for detailed troubleshooting and fleet-level dashboards for aggregate visibility. Standardize metric names, alarm severity, thresholds, and ownership.

## Key Takeaways

- **CloudWatch metrics provide the first layer of CloudFront observability:** monitor traffic, errors, cache efficiency, origin load, and origin latency.
- **Correlate metrics instead of interpreting them in isolation:** combinations such as increased `5xxErrorRate` and `OriginLatency` provide stronger diagnostic signals than either metric alone.
- **Design alarms around actionable conditions and SLOs:** use appropriate thresholds, evaluation periods, missing-data behavior, and severity rather than alerting on every metric.
- **Dashboards should support incident diagnosis:** organize them around traffic, errors, cache behavior, origin performance, and deployment/security context.
- **Monitor the entire request path:** CloudFront, WAF, ALB/Nginx, Django/FastAPI, PostgreSQL, Redis, Kafka, and external dependencies must be correlated to distinguish CDN symptoms from the actual root cause.