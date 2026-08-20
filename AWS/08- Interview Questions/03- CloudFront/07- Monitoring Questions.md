# 07- Monitoring Questions

## Overview

CloudFront monitoring is the process of observing CDN traffic, cache behavior, latency, errors, origin health, and operational changes to determine whether the delivery layer is behaving as expected.

For a production backend system, monitoring CloudFront is not limited to checking whether requests return `200`. A CDN can return successful responses while still suffering from:

- Poor cache-hit ratio.
- Increasing origin request volume.
- High origin latency.
- Regional performance degradation.
- Elevated `4xx` or `5xx` responses.
- Cache fragmentation.
- Incorrect cache policies.
- Unexpected traffic patterns.
- Excessive data transfer costs.
- Edge-function failures.

A useful monitoring model is:

```text
                    CloudFront
                        │
        ┌───────────────┼────────────────┐
        │               │                │
        ▼               ▼                ▼
     Traffic          Cache             Errors
     Metrics         Metrics            Metrics
        │               │                │
        └───────────────┼────────────────┘
                        ▼
                 CloudWatch
                        │
             ┌──────────┼──────────┐
             ▼          ▼          ▼
          Dashboard   Alarm      Logs
             │          │          │
             └──────────┼──────────┘
                        ▼
                   Operations
```

The goal is to establish a chain from **metric → baseline → threshold → alert → diagnosis → remediation**.

---

## What Should Be Monitored?

A production CloudFront deployment should generally monitor these categories:

| Category | What to observe | Why it matters |
|---|---|---|
| Traffic | Request volume | Detect growth, spikes, and anomalies |
| Cache | Cache hit behavior | Measure CDN effectiveness |
| Latency | Origin and request latency | Detect backend or network degradation |
| Errors | `4xx` and `5xx` rates | Detect client and infrastructure failures |
| Origin | Origin request volume and failures | Detect cache misses or backend problems |
| Data transfer | Bytes delivered | Cost and traffic analysis |
| Edge logic | Function/Lambda failures | Detect request-processing failures |
| Security | Suspicious request patterns | Detect abuse and attack indicators |
| Availability | Error and latency trends | Detect service degradation |
| Configuration | Distribution changes | Correlate incidents with deployments |

Monitoring should be designed around the application's **user-facing SLOs**, not merely around whichever metrics are easiest to graph.

---

## CloudFront and CloudWatch

CloudFront integrates with CloudWatch for monitoring CloudFront distributions.

A typical production architecture is:

```mermaid
flowchart LR
    Client[Client] --> CF[CloudFront]
    CF --> Cache[Edge Cache]
    Cache --> Origin[Origin]
    CF --> Metrics[CloudFront Metrics]
    Origin --> Metrics
    Metrics --> CW[CloudWatch]
    CW --> Dashboard[CloudWatch Dashboard]
    CW --> Alarm[CloudWatch Alarms]
    Alarm --> SNS[SNS / Incident Notification]
```

CloudWatch provides the monitoring layer, while CloudFront produces the operational signals.

CloudFront metrics can be used for:

- Dashboards.
- Alarms.
- Capacity and traffic analysis.
- Incident investigation.
- Performance analysis.
- Operational trend analysis.

---

## Core CloudFront Metrics

Several CloudFront metrics are particularly important for backend engineers.

### Requests

The request count represents traffic received by the distribution.

Use it to understand:

- Normal request volume.
- Traffic growth.
- Traffic spikes.
- Unexpected traffic drops.
- Deployment-related changes.
- Potential abuse.

A request-volume increase is not automatically an incident.

For example:

```text
Normal:
100k requests/minute

Marketing campaign:
500k requests/minute
```

The correct response depends on whether the increase was expected.

---

## Bytes Downloaded

Bytes downloaded measures the amount of data delivered by CloudFront.

It is useful for:

- Traffic analysis.
- Cost analysis.
- Large-object delivery monitoring.
- Detecting unexpected data transfer increases.

A sudden increase in bytes without a corresponding request increase can indicate:

- Larger responses.
- Changed cache behavior.
- New media assets.
- Compression changes.
- Unexpected large-object downloads.

---

## Bytes Uploaded

For workloads where viewers upload data through CloudFront-supported paths, uploaded bytes can provide useful traffic visibility.

The important operational principle is to distinguish **request count** from **traffic volume**.

For example:

```text
Scenario A:
10 million requests × 1 KB

Scenario B:
100 thousand requests × 10 MB
```

The second workload has dramatically different bandwidth and cost characteristics despite having fewer requests.

---

## Cache Hit Ratio

Cache hit ratio is one of the most important CloudFront performance indicators.

Conceptually:

```text
Cache Hit Ratio =
Cache Hits / Total Cacheable Requests × 100
```

A high cache hit ratio generally means CloudFront is serving more content from edge caches rather than contacting the origin.

For example:

```text
1,000,000 requests
        │
        ├── 900,000 cache hits
        └── 100,000 origin requests

Cache hit ratio ≈ 90%
```

A declining cache hit ratio can increase:

- Origin traffic.
- Backend CPU utilization.
- Database load.
- Application latency.
- Infrastructure cost.

However, there is no universally correct cache-hit percentage. Dynamic APIs and static assets have fundamentally different caching characteristics.

---

## Why Cache Hit Ratio Matters to Backend Systems

Consider a Django API:

```text
Client
  │
  ▼
CloudFront
  │
  ├── Cache hit ───────────────► Response
  │
  └── Cache miss
          │
          ▼
        ALB
          │
          ▼
       Django
          │
          ▼
      PostgreSQL
```

Every avoidable cache miss can propagate load deeper into the system.

For a high-traffic API:

```text
CloudFront cache efficiency
          │
          ▼
Origin request volume
          │
          ▼
Django/FastAPI load
          │
          ▼
Database load
```

This is why CDN monitoring should not be isolated from backend monitoring.

---

## Origin Latency

Origin latency measures the time associated with CloudFront obtaining a response from the origin.

Increasing origin latency can indicate problems such as:

- Slow Django/FastAPI endpoints.
- Database contention.
- Redis problems.
- Network issues.
- Slow upstream services.
- CPU saturation.
- Connection pool exhaustion.
- Application deployments.

A useful diagnostic relationship is:

```text
CloudFront latency increases
        │
        ▼
Is cache hit ratio stable?
        │
        ├── No
        │    └── Investigate cache behavior
        │
        └── Yes
             │
             ▼
       Is origin latency high?
             │
             ├── Yes → Investigate backend
             └── No  → Investigate edge/network path
```

---

## Error Metrics

CloudFront error monitoring should distinguish between:

- `4xx` responses.
- `5xx` responses.

They represent different classes of failures.

| Error class | Typical interpretation |
|---|---|
| `4xx` | Client/request/application contract issue |
| `5xx` | Server, origin, configuration, or infrastructure issue |

Do not treat all errors identically.

---

## `4xx` Monitoring

A rise in `4xx` responses can indicate:

- Invalid URLs.
- Authentication failures.
- Authorization failures.
- Missing resources.
- Bad API requests.
- Bot traffic.
- Client-side bugs.
- Incorrect application deployments.

For example:

```text
Normal:
404 rate = 0.2%

After deployment:
404 rate = 12%
```

That pattern strongly suggests a deployment or routing issue rather than random traffic.

---

## `5xx` Monitoring

`5xx` errors generally deserve more urgent investigation.

Potential causes include:

- Origin application failures.
- ALB failures.
- Origin connectivity issues.
- Application crashes.
- Backend timeouts.
- Incorrect CloudFront configuration.
- Origin overload.
- Deployment problems.

A useful production alert is based on **error rate**, not merely absolute error count.

For example:

```text
5xx rate > 1%
for 5 consecutive minutes
```

The exact threshold should be derived from the application's SLO and normal baseline.

---

## Error Rate vs Error Count

Suppose:

```text
10,000 requests
100 errors
```

The error rate is:

```text
1%
```

Now consider:

```text
1,000,000 requests
1,000 errors
```

The error rate is:

```text
0.1%
```

The second scenario contains more errors but represents a lower failure percentage.

For user-facing availability, **rate-based monitoring is usually more meaningful**.

Absolute counts remain useful for capacity and volume analysis.

---

## CloudFront Status Codes

CloudFront monitoring should consider the distribution of HTTP status codes.

A useful dashboard might show:

```text
2xx ─────────────── Healthy
3xx ─────────────── Redirect behavior
4xx ─────────────── Client/request failures
5xx ─────────────── Server/infrastructure failures
```

The important question is not simply:

> "How many errors occurred?"

It is:

> "What changed relative to the expected traffic pattern?"

---

## Monitoring Origin Health

CloudFront is only one layer.

A request can fail because:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
ALB
  │
  ▼
Django/FastAPI
  │
  ▼
PostgreSQL
```

CloudFront metrics may show elevated latency or `5xx`, but the actual root cause could be PostgreSQL.

Therefore, correlate CloudFront metrics with:

- ALB metrics.
- Application metrics.
- Database metrics.
- Redis metrics.
- Kubernetes metrics.
- Container metrics.
- Nginx metrics.
- Application logs.

---

## Monitoring the Complete Request Path

A production monitoring model should resemble:

```mermaid
flowchart TD
    User[User] --> CF[CloudFront]
    CF --> ALB[ALB / Nginx]
    ALB --> App[Django / FastAPI]
    App --> Redis[Redis]
    App --> DB[PostgreSQL]

    CF --> CWM[CloudFront Metrics]
    ALB --> ALBM[ALB Metrics]
    App --> APM[Application Metrics]
    Redis --> RM[Redis Metrics]
    DB --> DBM[Database Metrics]

    CWM --> CW[CloudWatch]
    ALBM --> CW
    APM --> CW
    RM --> CW
    DBM --> CW

    CW --> Dashboard[Operational Dashboard]
    CW --> Alerts[Alerts]
```

This prevents the common mistake of treating CloudFront as an isolated system.

---

## CloudWatch Dashboards

A CloudWatch dashboard should answer operational questions quickly.

A useful CloudFront dashboard can contain:

| Dashboard panel | Purpose |
|---|---|
| Requests | Traffic volume |
| Bytes downloaded | Bandwidth |
| Cache hit behavior | CDN effectiveness |
| `4xx` rate | Client/request failures |
| `5xx` rate | Infrastructure/application failures |
| Origin latency | Backend responsiveness |
| Origin request volume | Cache effectiveness |
| Error trends | Incident detection |
| Distribution-level comparisons | Identify problematic distributions |

Avoid filling the dashboard with every available metric.

A dashboard should support a decision.

---

## Recommended Dashboard Layout

A practical layout is:

```text
┌───────────────────────────────────────────────┐
│ CloudFront Production Health                  │
├───────────────────────┬───────────────────────┤
│ Requests              │ Error Rate            │
├───────────────────────┼───────────────────────┤
│ Cache Hit Behavior    │ Origin Latency        │
├───────────────────────┼───────────────────────┤
│ 4xx                   │ 5xx                   │
├───────────────────────┼───────────────────────┤
│ Bytes Downloaded      │ Origin Requests       │
└───────────────────────┴───────────────────────┘
```

The first row should normally contain the highest-priority user-impact signals.

---

## CloudWatch Alarms

A CloudWatch alarm evaluates a metric against a configured condition.

Conceptually:

```text
Metric
  │
  ▼
Threshold
  │
  ▼
Evaluation periods
  │
  ▼
Alarm state
  │
  ▼
Notification / automation
```

Typical alarm states include:

- `OK`
- `ALARM`
- `INSUFFICIENT_DATA`

An alarm should represent a meaningful operational condition rather than merely indicate that a metric changed.

---

## What Makes a Good Alarm?

A good production alarm should be:

- Actionable.
- Specific.
- Based on a meaningful threshold.
- Resistant to short-lived noise.
- Connected to an owner or incident process.
- Aligned with user impact.

Bad alarm:

```text
Requests > 100,000
```

This may be completely normal during peak traffic.

Better:

```text
5xx error rate > established SLO threshold
for a sustained evaluation window
```

The threshold should be based on the service's actual baseline and availability objectives.

---

## Alarm Categories

A practical CloudFront alarm strategy can include:

| Alarm | Example purpose |
|---|---|
| High `5xx` rate | Detect origin/infrastructure failures |
| High `4xx` rate | Detect routing/client/application problems |
| High origin latency | Detect backend degradation |
| Traffic anomaly | Detect unexpected traffic changes |
| Cache degradation | Detect cache-policy or behavior changes |
| Data transfer anomaly | Detect unexpected traffic/cost |
| Edge-function errors | Detect edge processing failures |

Not every metric needs an alarm.

---

## Multi-Period Evaluation

Short spikes should not necessarily page an engineer.

For example:

```text
Minute 1: 5xx = 1.2%
Minute 2: 5xx = 1.1%
Minute 3: 5xx = 1.3%
Minute 4: 5xx = 1.4%
Minute 5: 5xx = 1.5%
```

A sustained failure is much more operationally significant than:

```text
Minute 1: 5xx = 1.2%
Minute 2: 5xx = 0.1%
```

Alarm evaluation should therefore consider:

- Threshold.
- Period.
- Number of evaluation periods.
- Missing data behavior.
- Expected traffic patterns.

---

## High Traffic and Alarm Design

Traffic-dependent metrics require special care.

For example:

```text
5 errors / 10 requests = 50%
```

versus:

```text
5 errors / 100,000 requests = 0.005%
```

A low-traffic service can produce unstable percentages.

Possible strategies include:

- Combining rate thresholds with minimum request volume.
- Using longer evaluation periods.
- Establishing separate thresholds for low-volume distributions.
- Using anomaly detection where appropriate.

---

## Anomaly Detection

Static thresholds are not always sufficient.

For example:

```text
Normal requests:
10k–15k/min

Sudden:
80k/min
```

The exact value `80k` may not be known beforehand.

Anomaly detection can help identify deviations from established behavior.

Potential anomaly signals include:

- Request volume.
- Bytes transferred.
- Error rates.
- Latency.
- Origin request volume.

Anomaly detection should complement, not replace, deterministic SLO-based alarms.

---

## Monitoring Cache Performance

Cache behavior should be monitored continuously because caching is a major part of CloudFront's value.

A typical investigation is:

```text
Cache hit ratio decreases
        │
        ▼
Did cache policy change?
        │
        ├── Yes → Review deployment/configuration
        │
        └── No
             │
             ▼
Did request variation increase?
             │
             ├── Yes → Review cache key
             │
             └── No
                  │
                  ▼
             Review TTL/origin behavior
```

Potential causes include:

- Cache policy changes.
- Query-string variations.
- Cookie variations.
- Header variations.
- Low TTLs.
- Object invalidations.
- Traffic shifting to uncached paths.

---

## Cache Monitoring Example

Suppose:

```text
Before deployment:
Cache hit ratio = 92%
Origin requests = 80k/min

After deployment:
Cache hit ratio = 65%
Origin requests = 350k/min
```

The deployment may have introduced:

- A new cache key dimension.
- Changed cache-control behavior.
- Disabled caching.
- Added a request variation.
- Changed cache policy.

This can create a cascading backend problem:

```text
Cache hit ratio ↓
       │
       ▼
Origin requests ↑
       │
       ▼
Django/FastAPI CPU ↑
       │
       ▼
Database queries ↑
       │
       ▼
Latency ↑
       │
       ▼
5xx errors ↑
```

Monitoring CloudFront can therefore provide an early warning before the database becomes the obvious failure point.

---

## Monitoring Origin Latency

Origin latency should be compared with application latency.

For example:

```text
CloudFront origin latency: 1.8 seconds
Django request latency:    200 ms
```

The difference suggests that the bottleneck may exist between the application response and CloudFront rather than inside the Django application itself.

Conversely:

```text
CloudFront origin latency: 2.0 seconds
Django request latency:    1.9 seconds
```

The backend is likely contributing most of the delay.

Metrics should therefore be correlated rather than interpreted independently.

---

## Monitoring Edge Functions

If CloudFront Functions or Lambda@Edge are part of the request path, monitor their operational behavior.

Potential signals include:

- Function errors.
- Invocation behavior.
- Execution failures.
- Deployment changes.
- Request-routing anomalies.

An edge function failure can have a much larger blast radius than a normal application instance failure because the function may be associated with a global distribution.

---

## Deployment Monitoring

CloudFront configuration changes should be correlated with monitoring events.

A useful deployment sequence is:

```text
CI/CD
  │
  ▼
CloudFront configuration change
  │
  ▼
Distribution deployment
  │
  ▼
Observe metrics
  │
  ├── Error rate
  ├── Cache behavior
  ├── Origin latency
  └── Traffic
```

If cache hit ratio drops immediately after a cache-policy deployment, the timing is an important diagnostic signal.

---

## Monitoring Configuration Changes

CloudFront configuration changes should be auditable.

Useful operational information includes:

- Who changed the distribution.
- What changed.
- When it changed.
- Which environment was affected.
- Whether the change was expected.
- What metrics changed afterward.

AWS audit mechanisms such as CloudTrail should be considered alongside CloudWatch operational metrics.

The combination is valuable:

```text
CloudWatch
    │
    └── What happened?

CloudTrail
    │
    └── Who changed the configuration?
```

---

## CloudFront Logs vs CloudWatch Metrics

Metrics and logs serve different purposes.

| Tool | Best use |
|---|---|
| CloudWatch Metrics | Trends, health, alarms |
| CloudWatch Dashboards | Operational overview |
| CloudWatch Alarms | Actionable thresholds |
| Access Logs | Detailed request analysis |
| Real-Time Logs | Near-real-time request investigation |
| CloudTrail | API/configuration audit |
| Application Logs | Backend root-cause analysis |

Do not attempt to solve every observability problem with metrics alone.

---

## Real-Time Logs for Incident Investigation

Real-time logs can provide detailed request-level information useful when aggregate metrics are insufficient.

For example:

```text
Metric:
5xx rate increased

       │
       ▼

Real-time logs:
Which paths?
Which status codes?
Which headers?
Which cache behavior?
Which edge locations?
```

This allows an engineer to move from:

```text
"There is a problem"
```

to:

```text
"Requests to /api/orders are producing 5xx responses
from a specific request pattern after the deployment."
```

Real-time logging should be enabled selectively because detailed request-level observability has cost and operational implications.

---

## Monitoring Security Signals

CloudFront monitoring can also contribute to security operations.

Potential signals include:

- Sudden request spikes.
- Unusual geographic patterns.
- Abnormal `4xx` rates.
- Repeated unauthorized requests.
- Unexpected paths.
- High request rates against a single endpoint.
- Large increases in data transfer.

CloudFront metrics alone do not replace AWS WAF, application security controls, or dedicated security monitoring.

A useful architecture is:

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
Origin
```

Security telemetry should be correlated across these layers.

---

## Monitoring Cost Signals

CloudFront monitoring should also consider cost.

Important operational indicators include:

- Requests.
- Data transfer.
- Origin request volume.
- Cache efficiency.
- Large-object delivery.
- Unexpected traffic spikes.

A sudden cache degradation can indirectly increase costs:

```text
Cache hit ratio ↓
      │
      ▼
Origin traffic ↑
      │
      ▼
Backend infrastructure ↑
      │
      ▼
CloudFront + origin cost ↑
```

Cost monitoring should therefore be connected to performance monitoring.

---

## Production Dashboard Example

A production dashboard can be organized into four layers.

### User Impact

```text
- Request volume
- 4xx rate
- 5xx rate
- Latency
```

### CDN Efficiency

```text
- Cache hit ratio
- Origin request volume
- Bytes downloaded
```

### Origin Health

```text
- Origin latency
- ALB target health
- Application latency
- Database latency
```

### Operational Changes

```text
- Deployment timestamps
- CloudFront configuration changes
- WAF changes
- Incident markers
```

This structure makes the dashboard useful during incidents rather than turning it into a metric catalog.

---

## Example CloudWatch Alarm Concept

An alarm can conceptually be designed as:

```text
Metric:
CloudFront 5xx error rate

Condition:
Above production SLO threshold

Evaluation:
Multiple consecutive periods

Action:
Send notification to incident channel

Operator:
Investigate CloudFront → ALB → application → database
```

The exact metric, threshold, and alarm configuration should be selected from the distribution's traffic characteristics and service-level objectives.

---

## CLI: Inspect a Distribution

AWS CLI can be used to inspect CloudFront distribution configuration.

```bash
aws cloudfront get-distribution \
  --id E123EXAMPLE
```

For distribution configuration:

```bash
aws cloudfront get-distribution-config \
  --id E123EXAMPLE
```

These commands are useful when correlating observed behavior with deployed configuration.

---

## CLI: List CloudFront Distributions

```bash
aws cloudfront list-distributions
```

For automation, combine this with environment or distribution metadata rather than relying on manually maintained lists.

---

## Monitoring Through CI/CD

CloudFront configuration should ideally be managed through infrastructure-as-code or controlled deployment pipelines.

A production pipeline can look like:

```text
Git commit
    │
    ▼
CI validation
    │
    ▼
Infrastructure deployment
    │
    ▼
CloudFront change
    │
    ▼
Metrics observation
    │
    ├── Healthy → Continue
    │
    └── Degraded → Rollback / investigate
```

This is especially important for:

- Cache policies.
- Origin configuration.
- Behaviors.
- Edge functions.
- Security settings.

---

## Common Monitoring Mistakes

| Mistake | Problem | Better approach |
|---|---|---|
| Monitoring only `5xx` | Misses cache and latency degradation | Monitor traffic, cache, latency, errors |
| Using only absolute error counts | Ignores traffic volume | Monitor error rates |
| Alerting on every spike | Creates alert fatigue | Require sustained conditions |
| No cache monitoring | Backend overload can appear suddenly | Monitor cache behavior and origin requests |
| No origin correlation | CloudFront becomes a dead-end signal | Correlate with ALB/application/database metrics |
| Dashboard contains every metric | Important signals become hard to find | Build decision-oriented dashboards |
| Ignoring `4xx` | Routing and deployment problems remain hidden | Monitor meaningful `4xx` patterns |
| No deployment correlation | Root cause is harder to identify | Track deployment/configuration timestamps |
| No log-level investigation path | Metrics identify symptoms only | Use access/real-time/application logs |
| Ignoring low traffic | Percentages become noisy | Use minimum volume and appropriate evaluation windows |
| Alerting without an owner | No one acts on the alarm | Assign operational ownership |
| Treating CloudFront as the whole system | Root cause may be downstream | Monitor the complete request path |

---

## Interview Questions and Answers

### What are the most important CloudFront metrics?

Important metrics include:

- Request volume.
- Bytes downloaded.
- Cache behavior.
- Origin request volume.
- Origin latency.
- `4xx` errors.
- `5xx` errors.

The exact set depends on the workload.

---

### Why is cache hit ratio important?

A high cache hit ratio generally means more requests are served from edge caches, reducing origin traffic.

A sudden decline can increase:

```text
Origin requests
    ↓
Application load
    ↓
Database load
    ↓
Latency
    ↓
Infrastructure cost
```

---

### Should you alert on cache hit ratio?

Not necessarily by itself.

A cache-hit reduction is operationally important when it causes meaningful consequences such as:

- Increased origin load.
- Increased latency.
- Increased cost.
- Backend saturation.

Alert design should therefore consider the relationship between cache behavior and user impact.

---

### What is the difference between metrics and logs?

Metrics provide aggregated numerical signals suitable for:

- Dashboards.
- Trends.
- Alarms.

Logs provide detailed event or request information suitable for:

- Debugging.
- Root-cause analysis.
- Request-level investigation.

You generally use both.

---

### How would you investigate an increase in CloudFront `5xx` errors?

A practical sequence is:

1. Confirm whether the increase is real and sustained.
2. Check whether the increase is global or limited to specific paths or distributions.
3. Check CloudFront origin latency.
4. Check origin request volume and cache behavior.
5. Check ALB/Nginx metrics.
6. Check Django/FastAPI application errors.
7. Check database and Redis health.
8. Correlate the incident with recent deployments or CloudFront configuration changes.
9. Use detailed request logs when aggregate metrics are insufficient.
10. Remediate or roll back the identified change.

---

### How would you investigate a sudden cache-hit-ratio drop?

Check:

- Recent cache policy changes.
- Cache key changes.
- Query-string behavior.
- Cookie behavior.
- Header behavior.
- TTL changes.
- New uncached paths.
- Cache invalidations.
- Deployment changes.

Then compare:

```text
Cache hit ratio
+
Origin request volume
+
Application load
```

The three signals together provide much more context than cache-hit ratio alone.

---

### How would you detect an origin performance problem?

Correlate:

```text
CloudFront origin latency
        +
ALB latency
        +
Application latency
        +
Database latency
```

If CloudFront origin latency and application latency increase together, the application or its dependencies are likely contributing to the problem.

---

### What is a good CloudFront alarm?

A good alarm detects a condition that requires action.

For example:

```text
Sustained 5xx error rate above the
production availability threshold
```

A poor alarm is:

```text
Request count > arbitrary number
```

unless that threshold has a meaningful operational interpretation.

---

### Why should alarms not trigger on every short spike?

Short-lived spikes can be normal.

Paging engineers for transient events causes:

- Alert fatigue.
- Ignored alerts.
- Reduced trust in monitoring.
- Unnecessary incident response.

Use appropriate evaluation periods and thresholds.

---

### How do you monitor CloudFront during a deployment?

Compare before and after:

- Request volume.
- `4xx` rate.
- `5xx` rate.
- Cache behavior.
- Origin request volume.
- Origin latency.
- Bytes transferred.

If a metric changes immediately after a configuration or application deployment, that temporal correlation is an important investigation signal.

---

### How would you monitor a CloudFront distribution serving a Django API?

A reasonable monitoring chain is:

```text
CloudFront
├── Requests
├── Cache behavior
├── 4xx
├── 5xx
└── Origin latency

        ↓

ALB / Nginx
├── Request count
├── Target errors
└── Latency

        ↓

Django
├── Request latency
├── Exceptions
└── Application health

        ↓

PostgreSQL / Redis
├── Latency
├── Connections
└── Resource utilization
```

This provides end-to-end visibility.

---

### What is the relationship between CloudFront monitoring and SLOs?

SLOs define the reliability or performance target the service is expected to achieve.

For example:

```text
99.9% successful requests
```

CloudFront error and latency metrics can provide the evidence required to determine whether the delivery layer is meeting that objective.

Monitoring should therefore be driven by service objectives rather than by the availability of individual metrics.

---

### Should all CloudFront metrics have alarms?

No.

Dashboards, alarms, and logs serve different purposes.

Some metrics are useful for:

- Investigation.
- Capacity planning.
- Cost analysis.
- Trend analysis.

Only actionable conditions should generally generate alerts.

---

### Why monitor both CloudFront and the origin?

Because CloudFront can hide or amplify backend behavior.

For example:

```text
Cache hit ratio = 98%
```

may make the backend appear healthy because most traffic never reaches it.

A sudden cache degradation can expose the backend to a much larger request load.

Monitoring both layers reveals this relationship.

---

### How can CloudFront monitoring help identify a cache-policy mistake?

Suppose a deployment changes a cache policy:

```text
Before:
Cache hit ratio = 95%
Origin requests = 20k/min

After:
Cache hit ratio = 60%
Origin requests = 400k/min
```

The correlation strongly suggests that the configuration change affected caching behavior.

The next step is to inspect cache-key dimensions, TTLs, headers, cookies, and query-string behavior.

---

### What should you monitor during a traffic spike?

At minimum:

- Request volume.
- Bytes transferred.
- Error rates.
- Cache hit behavior.
- Origin request volume.
- Origin latency.
- Backend CPU and saturation.
- Database health.

The key question is whether the CDN absorbs the increase or passes it through to the origin.

---

### How can monitoring reveal a CDN configuration regression?

A useful pattern is:

```text
Deployment
   │
   ▼
Cache hit ratio ↓
   │
   ▼
Origin requests ↑
   │
   ▼
Origin latency ↑
   │
   ▼
5xx ↑
```

A sequence like this provides strong evidence that the configuration change introduced a regression.

---

## Production Monitoring Checklist

Before considering a CloudFront deployment production-ready:

- [ ] Request volume is monitored.
- [ ] `4xx` errors are monitored.
- [ ] `5xx` errors are monitored.
- [ ] Cache behavior is monitored.
- [ ] Origin request volume is monitored.
- [ ] Origin latency is monitored.
- [ ] Data transfer is monitored.
- [ ] CloudWatch dashboards exist for production distributions.
- [ ] Actionable CloudWatch alarms are configured.
- [ ] Alarm thresholds are based on production baselines or SLOs.
- [ ] Alarm evaluation windows prevent unnecessary noise.
- [ ] CloudFront metrics can be correlated with ALB/Nginx metrics.
- [ ] Application metrics are available for Django/FastAPI services.
- [ ] Database and Redis monitoring exists where applicable.
- [ ] Access or real-time logs are available for deeper investigation.
- [ ] CloudTrail is used for configuration-change auditing where appropriate.
- [ ] Deployment timestamps can be correlated with metric changes.
- [ ] Security monitoring is integrated with the broader AWS security architecture.
- [ ] Cost-related traffic anomalies can be detected.
- [ ] Every production alarm has an operational owner.

## Key Takeaways

- **Monitor CloudFront as part of the complete request path, not as an isolated CDN; correlate edge metrics with ALB, application, Redis, and database signals.**
- **Request volume, error rates, cache behavior, origin request volume, origin latency, and data transfer form the core operational monitoring surface.**
- **CloudWatch dashboards should provide rapid operational context, while alarms should be reserved for actionable conditions aligned with SLOs and production baselines.**
- **A cache degradation can cascade into higher origin traffic, application load, database pressure, latency, and cost, making cache monitoring an important backend reliability signal.**
- **Effective incident response requires a progression from aggregate metrics to detailed logs and configuration/deployment history rather than relying on a single CloudFront metric.**