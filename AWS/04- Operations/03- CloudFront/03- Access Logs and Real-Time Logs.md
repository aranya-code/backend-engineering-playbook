# 03- Access Logs and Real-Time Logs

## Overview

CloudFront metrics are useful for identifying trends and detecting anomalies, but they are aggregated. When an engineer needs to answer request-level questions such as:

- Which URL is returning `404`?
- Which client IPs are generating `403` responses?
- Which CloudFront behavior handled the request?
- Which requests were cache hits or misses?
- Which requests were slow?
- Which User-Agent is generating abnormal traffic?
- Did a deployment change request behavior?

CloudFront logs become the primary diagnostic source.

CloudFront provides two distinct logging mechanisms:

| Logging mechanism | Primary purpose | Delivery model | Typical use |
|---|---|---|---|
| Standard access logs | Historical request analysis | Delivered to Amazon S3 | Auditing, reporting, incident investigation |
| Real-time logs | Near-real-time request analysis | Delivered to Kinesis Data Streams | Live troubleshooting, security detection, traffic analysis |

The architectural distinction is important:

```text
                         ┌─────────────────┐
                         │     Viewer      │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │   CloudFront    │
                         └────────┬────────┘
                                  │
                  ┌───────────────┴────────────────┐
                  │                                │
                  ▼                                ▼
        ┌──────────────────┐             ┌──────────────────┐
        │ Standard Logs    │             │ Real-Time Logs   │
        │                  │             │                  │
        │ S3               │             │ Kinesis Stream   │
        │ Batch analysis   │             │ Near real-time   │
        └────────┬─────────┘             └────────┬─────────┘
                 │                                │
                 ▼                                ▼
        Athena / Glue / SIEM              Lambda / Consumer
```

The correct choice depends on the operational question. Standard access logs are generally the better choice for complete historical analysis, while real-time logs are designed for use cases where waiting for standard log delivery is too slow.

---

## Standard Access Logs

### What They Are

CloudFront standard access logs provide detailed records about requests that CloudFront receives.

They are delivered to an Amazon S3 bucket that you configure for logging.

A simplified request path is:

```text
Viewer
   │
   ▼
CloudFront
   │
   ├── Request processed
   │
   └── Log record generated
            │
            ▼
       Amazon S3
            │
            ▼
      Athena / ETL / SIEM
```

Standard logs are particularly useful when the investigation is not time-critical or when you need historical data for reporting and analysis.

### When to Use Them

Use standard access logs for:

- Historical incident investigation.
- Request auditing.
- Traffic analysis.
- Top URL analysis.
- HTTP status analysis.
- User-Agent analysis.
- Cache behavior analysis.
- Security investigations.
- Long-term analytics.
- Cost and traffic reporting.

---

## Standard Log Delivery Model

CloudFront writes standard access logs to S3.

The delivery path is therefore asynchronous:

```mermaid
sequenceDiagram
    participant C as Client
    participant CF as CloudFront
    participant O as Origin
    participant S3 as S3 Log Bucket
    participant A as Athena

    C->>CF: HTTP request
    CF->>O: Cache miss / origin request
    O-->>CF: Response
    CF-->>C: HTTP response

    Note over CF,S3: Log delivery is asynchronous
    CF->>S3: Access log record

    A->>S3: Query log data
    S3-->>A: Log records
```

This has an important operational consequence:

> Standard access logs should not be treated as a synchronous incident-debugging mechanism.

If an incident is occurring right now, real-time logs may be more appropriate.

---

## Standard Access Log Fields

CloudFront standard logs contain fields describing the request and response.

Common fields include:

| Field | Purpose |
|---|---|
| `date` | Request date |
| `time` | Request time |
| `x-edge-location` | CloudFront edge location |
| `sc-bytes` | Bytes sent to viewer |
| `c-ip` | Viewer IP address |
| `cs-method` | HTTP method |
| `cs(Host)` | Host header |
| `cs-uri-stem` | Requested path |
| `sc-status` | HTTP response status |
| `cs(Referer)` | Referer |
| `cs(User-Agent)` | User-Agent |
| `cs-uri-query` | Query string |
| `x-edge-result-type` | CloudFront result classification |
| `x-edge-request-id` | CloudFront request identifier |

The exact available fields and their definitions should be checked against the current CloudFront logging documentation before building parsers or schemas.

Do not assume that a log field's name alone explains which component generated the response.

---

## Understanding `x-edge-result-type`

`x-edge-result-type` is particularly useful during troubleshooting because it describes how CloudFront processed the request.

Typical values include:

```text
Hit
Miss
RefreshHit
Redirect
Error
LimitExceeded
CapacityExceeded
```

The exact values depend on CloudFront behavior and logging context.

For example:

```text
x-edge-result-type = Hit
```

indicates that CloudFront served the request from its cache.

Whereas:

```text
x-edge-result-type = Miss
```

indicates that CloudFront did not have a usable cached object and needed to proceed toward the origin.

This field is valuable when investigating cache behavior because it provides request-level evidence rather than relying only on aggregate `CacheHitRate`.

---

## Standard Logs and Request Correlation

The `x-edge-request-id` field is useful for correlating a CloudFront request with other telemetry where the identifier is available.

A practical investigation might look like:

```text
CloudFront request ID
        │
        ▼
CloudFront log
        │
        ▼
Origin request
        │
        ▼
ALB / Nginx log
        │
        ▼
Application log
```

However, CloudFront request IDs should not be assumed to automatically exist in every downstream application log.

For strong end-to-end tracing, propagate an application-level correlation ID or distributed trace context through the architecture.

---

## Real-Time Logs

### What They Are

CloudFront real-time logs provide near-real-time request information and are delivered to an Amazon Kinesis Data Streams data stream.

The architecture is:

```text
Viewer
   │
   ▼
CloudFront
   │
   ▼
Real-Time Log Configuration
   │
   ▼
Kinesis Data Streams
   │
   ├───────────────┐
   ▼               ▼
Lambda          Consumer
   │               │
   ▼               ▼
Alerts          Analytics
```

Real-time logs are useful when the operational value of request data depends on receiving it quickly.

### When to Use Them

Use real-time logs for:

- Live incident investigation.
- Security monitoring.
- Bot detection.
- Traffic anomaly detection.
- Near-real-time dashboards.
- Custom request analytics.
- Automated response workflows.

They are generally more appropriate than standard logs when seconds or near-real-time visibility matters.

---

## Real-Time Log Configuration

A real-time log configuration determines:

- Which fields are included.
- Sampling rate.
- Destination Kinesis data stream.

This makes real-time logging more selective than simply enabling every available field.

A practical design is:

```text
CloudFront
    │
    ▼
Real-Time Log Configuration
    │
    ├── Sample rate
    ├── Selected fields
    └── Kinesis stream
```

Only include fields that the downstream consumers actually need.

This reduces unnecessary processing and storage.

---

## Sampling

Real-time logs support sampling.

For example:

```text
100% traffic
   │
   ├── 10% sampled
   ▼
Kinesis
```

Sampling is useful when:

- Traffic volume is extremely high.
- The use case does not require every request.
- You are building anomaly detection.
- Cost and stream capacity need to be controlled.

Do not use aggressive sampling when the operational requirement is complete request auditing.

### Sampling Decision

| Requirement | Suggested approach |
|---|---|
| Full forensic investigation | Avoid relying on sampled real-time logs |
| Long-term analytics | Standard access logs |
| Live anomaly detection | Sampling may be appropriate |
| Security detection | Depends on detection requirements |
| Debugging a small production workload | High sampling rate |
| Extremely high-volume telemetry | Evaluate sampling carefully |

Sampling changes the statistical meaning of downstream analysis.

---

## Standard Logs vs Real-Time Logs

| Characteristic | Standard Access Logs | Real-Time Logs |
|---|---|---|
| Destination | S3 | Kinesis Data Streams |
| Delivery | Asynchronous | Near real-time |
| Primary use | Historical analysis | Live analysis |
| Sampling | Not the primary model | Supported |
| Processing | Athena, Glue, ETL, SIEM | Lambda, Kinesis consumers |
| Operational complexity | Lower | Higher |
| Storage | S3 | Depends on consumer |
| Streaming analytics | Less direct | Excellent |
| Incident response | Historical | Near real-time |
| Long-term retention | Excellent | Requires downstream storage |

The two mechanisms are complementary.

A mature production architecture may use both.

---

## Recommended Production Architecture

For a production backend:

```mermaid
flowchart TD
    Client[Clients] --> CF[CloudFront]

    CF --> Origin[ALB / Origin]

    CF --> S3Logs[S3 Standard Access Logs]
    CF --> RT[Real-Time Logs]

    RT --> Kinesis[Kinesis Data Streams]

    Kinesis --> Lambda[Lambda Consumer]
    Kinesis --> SIEM[Security / SIEM Pipeline]
    Kinesis --> RTDB[Real-Time Analytics]

    S3Logs --> Glue[AWS Glue]
    Glue --> Athena[Amazon Athena]
    Athena --> Dashboard[Analytics Dashboard]

    Origin --> App[Django / FastAPI]
    App --> DB[(PostgreSQL)]
    App --> Redis[(Redis)]
```

This architecture separates two operational requirements:

```text
Historical / forensic
        ↓
S3 → Glue → Athena

Real-time operational
        ↓
Kinesis → Lambda / consumers
```

---

## Querying Standard Logs with Athena

S3-based CloudFront logs are well suited to Athena because the logs can be queried without maintaining a dedicated database.

A typical workflow is:

```text
CloudFront
    ↓
S3
    ↓
Glue Catalog
    ↓
Athena
    ↓
SQL
```

### Example Query

Once the log files are represented by an Athena table, a query might look like:

```sql
SELECT
    sc_status,
    COUNT(*) AS request_count
FROM cloudfront_logs
WHERE date = DATE '2026-08-20'
GROUP BY sc_status
ORDER BY request_count DESC;
```

The exact Athena schema depends on how the CloudFront logs are parsed and partitioned.

---

## Finding Top Failing URLs

A common incident investigation is identifying which URLs are generating errors.

```sql
SELECT
    cs_uri_stem,
    sc_status,
    COUNT(*) AS error_count
FROM cloudfront_logs
WHERE date = DATE '2026-08-20'
  AND sc_status >= 400
GROUP BY
    cs_uri_stem,
    sc_status
ORDER BY error_count DESC
LIMIT 50;
```

This can quickly distinguish:

```text
/health
/api/orders
/static/app.js
/images/logo.png
```

from each other.

For example:

```text
/api/orders        504    18,400
/static/app.js     404       120
```

The first requires backend investigation; the second may indicate an asset deployment problem.

---

## Finding Suspicious Client IPs

For security investigations:

```sql
SELECT
    c_ip,
    COUNT(*) AS request_count
FROM cloudfront_logs
WHERE date = DATE '2026-08-20'
GROUP BY c_ip
ORDER BY request_count DESC
LIMIT 100;
```

Combine this with status analysis:

```sql
SELECT
    c_ip,
    sc_status,
    COUNT(*) AS request_count
FROM cloudfront_logs
WHERE date = DATE '2026-08-20'
GROUP BY
    c_ip,
    sc_status
ORDER BY request_count DESC
LIMIT 100;
```

This can reveal patterns such as:

```text
IP A → 200 → high normal traffic
IP B → 403 → repeated blocked traffic
IP C → 404 → large-scale path scanning
```

CloudFront logs should not be treated as a replacement for AWS WAF logging. Security decisions should generally combine CDN, WAF, application, and identity telemetry.

---

## Finding Cache Misses

Cache behavior can be analyzed using CloudFront log fields.

For example:

```sql
SELECT
    x_edge_result_type,
    COUNT(*) AS request_count
FROM cloudfront_logs
WHERE date = DATE '2026-08-20'
GROUP BY x_edge_result_type
ORDER BY request_count DESC;
```

This can expose a sudden increase in:

```text
Miss
```

or other result types.

A cache regression may look like:

```text
Before deployment:

Hit  = 92%
Miss = 8%

After deployment:

Hit  = 40%
Miss = 60%
```

The CloudFront `CacheHitRate` metric would show the aggregate regression, while access logs can help identify which requests are responsible.

---

## Finding Large Responses

Bandwidth analysis can be performed using `sc-bytes`.

For example:

```sql
SELECT
    cs_uri_stem,
    SUM(sc_bytes) AS total_bytes,
    COUNT(*) AS request_count
FROM cloudfront_logs
WHERE date = DATE '2026-08-20'
GROUP BY cs_uri_stem
ORDER BY total_bytes DESC
LIMIT 50;
```

This helps identify:

- Large downloads.
- Unexpected media traffic.
- Oversized API responses.
- Hot assets.
- Potential abuse.

---

## Investigating a 5xx Incident

Suppose CloudWatch reports:

```text
5xxErrorRate = 7%
```

The metric identifies the problem but not the affected request population.

Use logs to break the failure down:

```text
CloudFront metric
       ↓
5xx rate increased
       ↓
Access logs
       ↓
Which URLs?
Which status?
Which edge locations?
Which User-Agents?
Which result types?
       ↓
Origin logs
       ↓
Root cause
```

A useful query is:

```sql
SELECT
    cs_uri_stem,
    sc_status,
    x_edge_result_type,
    COUNT(*) AS request_count
FROM cloudfront_logs
WHERE date = DATE '2026-08-20'
  AND sc_status >= 500
GROUP BY
    cs_uri_stem,
    sc_status,
    x_edge_result_type
ORDER BY request_count DESC;
```

---

## Edge Location Analysis

The `x-edge-location` field identifies the CloudFront edge location associated with the request.

This can be useful when investigating geographically localized behavior.

For example:

```sql
SELECT
    x_edge_location,
    sc_status,
    COUNT(*) AS request_count
FROM cloudfront_logs
WHERE date = DATE '2026-08-20'
GROUP BY
    x_edge_location,
    sc_status
ORDER BY request_count DESC;
```

A concentration of failures in particular locations can be a useful signal, but it should not immediately be interpreted as an edge infrastructure failure.

Correlate it with:

- Viewer geography.
- Origin behavior.
- WAF decisions.
- DNS.
- TLS.
- Network behavior.
- Other CloudFront metrics.

---

## User-Agent Analysis

CloudFront logs include the viewer User-Agent.

This is useful for:

- Browser compatibility investigation.
- Mobile-vs-desktop analysis.
- Bot detection.
- API client analysis.
- Unexpected traffic identification.

Example:

```sql
SELECT
    cs_user_agent,
    COUNT(*) AS request_count
FROM cloudfront_logs
WHERE date = DATE '2026-08-20'
GROUP BY cs_user_agent
ORDER BY request_count DESC
LIMIT 50;
```

Do not treat User-Agent as a trusted identity signal. Clients can modify it arbitrarily.

---

## Real-Time Log Processing

Real-time logs become useful when the data must be acted upon quickly.

A typical consumer architecture is:

```text
CloudFront
    │
    ▼
Kinesis Data Streams
    │
    ▼
Lambda
    │
    ├── Detect anomaly
    ├── Enrich event
    ├── Write metric
    ├── Send alert
    └── Store event
```

For example:

```text
CloudFront request
       ↓
Real-time log
       ↓
Kinesis
       ↓
Lambda
       ↓
403 spike detected
       ↓
CloudWatch metric
       ↓
Alarm
```

This can reduce the time between an abnormal traffic pattern and detection.

---

## Real-Time Security Detection

A real-time pipeline can be useful for detecting patterns such as:

```text
One IP
  ↓
Thousands of requests
  ↓
Large number of 404 responses
  ↓
Multiple suspicious paths
```

A consumer can calculate an aggregation:

```text
IP → request count
IP → 4xx count
IP → unique paths
IP → request rate
```

and publish a derived CloudWatch metric.

However, avoid implementing security controls entirely in an ad-hoc log consumer.

For blocking and request inspection, use the appropriate AWS WAF capabilities and maintain the log pipeline primarily for detection, analysis, and response automation.

---

## Real-Time Logs and Kinesis Capacity

Kinesis Data Streams must be sized for the expected real-time log throughput.

Consider:

```text
Viewer request rate
        ×
Log record size
        ×
Sampling rate
        =
Approximate telemetry volume
```

At very high traffic volumes, logging every request with every field can produce substantial stream throughput.

Monitor:

- Incoming records.
- Incoming bytes.
- Iterator age.
- Consumer errors.
- Throttling.
- Processing latency.
- Failed records.

The real-time logging system must not become an operational bottleneck.

---

## Security Considerations

Logs can contain sensitive information.

Potentially sensitive fields include:

- Viewer IP addresses.
- Query strings.
- Referrers.
- User-Agent strings.
- Hostnames.
- Request paths.
- Identifiers embedded in URLs.

### Protect S3 Log Buckets

Use:

- Block Public Access.
- Least-privilege IAM.
- Encryption at rest.
- Bucket policies restricting writers/readers.
- Lifecycle policies.
- Access logging or CloudTrail where appropriate.

Do not expose the CloudFront log bucket publicly simply because the logs are operational data.

### Protect Kinesis Consumers

Use:

- Least-privilege IAM roles.
- Encryption.
- Restricted stream access.
- Controlled consumer permissions.
- Appropriate retention policies.

### Avoid Sensitive Query Parameters

A URL such as:

```text
https://api.example.com/reset?token=SECRET
```

can cause the secret to appear in request logs.

Sensitive credentials and tokens should not be placed in URLs.

Prefer:

```text
Authorization: Bearer <token>
```

or another secure mechanism where appropriate.

Even then, ensure downstream logging does not accidentally record sensitive headers.

---

## Privacy and Data Retention

Logging every request indefinitely is rarely justified.

Define retention according to:

- Incident-response requirements.
- Security requirements.
- Compliance requirements.
- Cost constraints.
- Data sensitivity.

A practical S3 lifecycle might be:

```text
Hot S3 storage
     ↓
30 days
     ↓
Infrequent access
     ↓
90 days
     ↓
Archive
     ↓
Expiration
```

The actual retention period should be based on organizational requirements.

Avoid retaining sensitive request data indefinitely without a clear reason.

---

## Cost Considerations

Standard access logs consume S3 storage and incur associated S3 request and storage costs.

Additional costs can arise from:

- S3 storage.
- Athena queries.
- AWS Glue.
- Kinesis Data Streams.
- Lambda.
- Data processing.
- SIEM ingestion.
- Long-term archival.

Real-time logging can become significantly more expensive at high request volumes because every selected field contributes to the telemetry stream.

A practical approach is:

```text
Standard logs
    ↓
Complete historical record
    ↓
S3
    ↓
Low-cost retention + Athena

Real-time logs
    ↓
Selective fields
    ↓
Sampling where appropriate
    ↓
Kinesis
    ↓
Operational use cases
```

Do not stream every field to Kinesis merely because it is available.

---

## Log Partitioning and Athena Performance

For large CloudFront installations, storing logs in an unstructured S3 prefix can make Athena queries inefficient.

Prefer a partitioned structure such as:

```text
s3://cloudfront-logs/
    distribution_id=E123/
        year=2026/
            month=08/
                day=20/
                    logs...
```

Then Athena can restrict queries to the relevant partition.

Conceptually:

```sql
SELECT
    sc_status,
    COUNT(*)
FROM cloudfront_logs
WHERE distribution_id = 'E123'
  AND year = 2026
  AND month = 8
  AND day = 20
GROUP BY sc_status;
```

The exact partitioning strategy should match the table definition and ingestion pipeline.

The goal is to avoid scanning months of logs when investigating a five-minute incident.

---

## Operational Troubleshooting Workflow

When a CloudFront issue occurs, combine metrics and logs.

```mermaid
flowchart TD
    Alert[CloudWatch Alert] --> Metrics[CloudFront Metrics]

    Metrics --> Traffic{Traffic Changed?}
    Metrics --> Errors{Errors Increased?}
    Metrics --> Cache{Cache Changed?}
    Metrics --> Latency{Origin Latency Increased?}

    Traffic --> Logs[CloudFront Logs]
    Errors --> Logs
    Cache --> Logs
    Latency --> Logs

    Logs --> Request[Identify Affected Requests]
    Request --> Origin[Inspect Origin]
    Origin --> App[Django / FastAPI]
    App --> Dependencies[(DB / Redis / External APIs)]
```

A practical workflow is:

1. Identify the incident time window.
2. Check CloudFront traffic metrics.
3. Check 4xx and 5xx rates.
4. Check cache hit ratio.
5. Check origin latency.
6. Query access logs for affected requests.
7. Group by URL and status code.
8. Group by edge location if geography appears relevant.
9. Correlate with ALB and application logs.
10. Inspect recent CloudFront, WAF, DNS, and application changes.

Do not begin by scanning millions of log records manually.

Use metrics to narrow the search window first.

---

## Common Log Analysis Queries

### Requests by Status

```sql
SELECT
    sc_status,
    COUNT(*) AS requests
FROM cloudfront_logs
WHERE date = DATE '2026-08-20'
GROUP BY sc_status
ORDER BY requests DESC;
```

### Top 404 URLs

```sql
SELECT
    cs_uri_stem,
    COUNT(*) AS requests
FROM cloudfront_logs
WHERE date = DATE '2026-08-20'
  AND sc_status = 404
GROUP BY cs_uri_stem
ORDER BY requests DESC
LIMIT 50;
```

### Top 5xx URLs

```sql
SELECT
    cs_uri_stem,
    sc_status,
    COUNT(*) AS failures
FROM cloudfront_logs
WHERE date = DATE '2026-08-20'
  AND sc_status >= 500
GROUP BY
    cs_uri_stem,
    sc_status
ORDER BY failures DESC
LIMIT 50;
```

### Top Clients

```sql
SELECT
    c_ip,
    COUNT(*) AS requests
FROM cloudfront_logs
WHERE date = DATE '2026-08-20'
GROUP BY c_ip
ORDER BY requests DESC
LIMIT 50;
```

### Cache Result Distribution

```sql
SELECT
    x_edge_result_type,
    COUNT(*) AS requests
FROM cloudfront_logs
WHERE date = DATE '2026-08-20'
GROUP BY x_edge_result_type
ORDER BY requests DESC;
```

These examples assume the Athena table exposes the corresponding fields with the same names.

---

## Common Mistakes

### Expecting Standard Logs to Be Real-Time

Standard logs are delivered asynchronously to S3.

If an engineer needs immediate request-level visibility during an incident, standard logs may not be sufficiently timely.

Use real-time logs when the operational requirement genuinely requires near-real-time telemetry.

---

### Enabling Every Real-Time Field

More fields mean more telemetry volume.

Before enabling a field, ask:

> Which operational decision requires this field?

If there is no answer, do not automatically include it.

---

### Using Real-Time Logs as a Permanent Analytics Store

Kinesis is a streaming transport layer, not automatically a long-term analytics platform.

For historical analysis, persist appropriate data to durable storage such as S3.

---

### Querying All Historical Logs

A query such as:

```sql
SELECT *
FROM cloudfront_logs;
```

can scan a large amount of data.

Prefer:

- Partition pruning.
- Time filters.
- Selected columns.
- Aggregations.
- Limited result sets.

---

### Assuming Logs Explain the Root Cause

CloudFront logs tell you what happened at the CDN request boundary.

They may show:

```text
504
```

but not necessarily why the origin timed out.

Continue the investigation into:

```text
CloudFront
    ↓
ALB
    ↓
Nginx
    ↓
Django / FastAPI
    ↓
PostgreSQL / Redis / External API
```

---

### Treating User-Agent as Trusted

User-Agent values are client-controlled.

Never use:

```text
User-Agent = trusted-client
```

as an authentication mechanism.

---

### Logging Sensitive URLs

Putting tokens or credentials into query strings can leak secrets into logs.

Prefer secure credential transport and minimize sensitive information in request URLs.

---

### Ignoring Log Storage Security

A CloudFront log bucket contains production traffic metadata.

It should be treated as sensitive operational data.

Use:

- Private S3 access.
- IAM restrictions.
- Encryption.
- Lifecycle management.
- Auditing.

---

## Production Best Practices

### Use Both Logging Mechanisms When Necessary

For critical systems:

```text
Standard access logs
    +
Real-time logs
```

provides both historical and operational visibility.

Do not assume one replaces the other.

### Keep Standard Logs Durable

Store standard logs in S3 with:

- Appropriate retention.
- Lifecycle rules.
- Encryption.
- Controlled access.
- Partition-aware organization.

### Keep Real-Time Logs Focused

Select only fields required by the real-time use case.

Use sampling when complete coverage is unnecessary.

### Correlate Across Layers

CloudFront logging should be part of a broader observability system:

```text
CloudFront
   ↓
ALB
   ↓
Nginx / Ingress
   ↓
Application
   ↓
Database / Redis / Kafka / External APIs
```

### Design for Incident Response

During an incident, engineers should be able to answer quickly:

- When did the problem start?
- Which URLs are affected?
- Which status codes increased?
- Which clients are affected?
- Is the problem global or localized?
- Are requests cache hits or misses?
- Is the origin involved?
- Did a configuration change precede the incident?

If the logging architecture cannot answer these questions efficiently, observability is incomplete.

---

## Interview Questions

### What is the difference between CloudFront standard logs and real-time logs?

Standard access logs are delivered to S3 for historical analysis. Real-time logs are delivered to Kinesis Data Streams for near-real-time processing.

---

### Why would you use real-time logs instead of standard logs?

When request-level information must be processed quickly for:

- Incident detection.
- Security monitoring.
- Traffic analysis.
- Automated response.

Standard logs are generally better suited for historical and batch analysis.

---

### Where are CloudFront standard logs stored?

They are delivered to an S3 bucket configured for CloudFront logging.

---

### Where are CloudFront real-time logs delivered?

They are delivered to an Amazon Kinesis Data Streams stream.

---

### Can you use Athena to analyze CloudFront logs?

Yes. Standard logs stored in S3 can be cataloged and queried through Athena.

---

### Why should you not query all CloudFront logs during an incident?

Because production distributions can generate very large datasets.

First narrow the investigation using:

```text
Time window
Distribution
Status
URL
Edge location
```

and then query only the required data.

---

### How would you detect a cache regression using logs?

First identify a decrease in `CacheHitRate`.

Then analyze request-level result types such as cache hits and misses to determine which URLs or request patterns are causing the regression.

---

### How would you investigate a CloudFront 504?

Start with:

```text
CloudFront 504 metric
        ↓
Access logs
        ↓
Affected URLs
        ↓
Origin latency
        ↓
ALB / Nginx
        ↓
Application
        ↓
Database / Redis / external dependencies
```

The goal is to determine whether the timeout is occurring at CloudFront, the network path, the origin, or a downstream dependency.

---

## Production Checklist

### Standard Access Logs

- [ ] S3 destination configured
- [ ] S3 bucket is private
- [ ] Encryption enabled
- [ ] IAM access restricted
- [ ] Lifecycle policy configured
- [ ] Retention period defined
- [ ] Athena analysis available where needed
- [ ] Logs partitioned appropriately for large workloads

### Real-Time Logs

- [ ] Kinesis stream configured where required
- [ ] Required fields explicitly selected
- [ ] Sampling strategy documented
- [ ] Kinesis capacity monitored
- [ ] Consumer failures monitored
- [ ] Consumer lag monitored
- [ ] IAM permissions follow least privilege
- [ ] Real-time data retention/storage strategy defined

### Incident Response

- [ ] CloudFront metrics identify anomalies
- [ ] Access logs provide request-level evidence
- [ ] Real-time logs are available for critical near-real-time use cases
- [ ] CloudFront request IDs can be correlated where applicable
- [ ] Origin logs are accessible
- [ ] Application logs are accessible
- [ ] WAF logs are available where relevant
- [ ] Recent configuration changes are auditable

## Key Takeaways

- **Standard access logs and real-time logs serve different operational purposes:** use S3-based standard logs for historical analysis and Kinesis-based real-time logs for near-real-time processing.
- **Use metrics to narrow the investigation before querying logs:** identify the affected time window, status codes, URLs, cache behavior, and latency before scanning large datasets.
- **Real-time logging should be selective:** choose only the fields required by the operational use case and use sampling when complete request coverage is unnecessary.
- **Treat logs as sensitive production data:** protect S3 and Kinesis resources, control IAM access, define retention, and avoid exposing credentials or sensitive tokens through URLs.
- **CloudFront logs are one layer of observability:** correlate CDN request data with WAF, ALB, Nginx, Django/FastAPI, database, Redis, and other dependency telemetry to establish root cause.