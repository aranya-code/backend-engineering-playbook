# 07- High Latency Issues

## Overview

High latency in CloudFront-backed applications is an end-to-end performance problem. CloudFront may be involved in the request path, but the actual bottleneck can exist at the edge, network, origin, application, database, cache, or an external dependency.

A production investigation should therefore decompose the request rather than assuming that CloudFront itself is slow.

```text
Client
  │
  │ DNS / TCP / TLS
  ▼
CloudFront Edge
  │
  ├── Cache HIT ───────────────► Client
  │
  └── Cache MISS
          │
          ▼
       Origin
          │
          ▼
       ALB / Nginx
          │
          ▼
      Django / FastAPI
          │
          ├── PostgreSQL
          ├── Redis
          ├── Kafka
          └── External APIs
```

The core troubleshooting question is:

> Which part of the request path is consuming the latency budget?

This distinction matters because optimizing a 20 ms CloudFront operation has little value if a PostgreSQL query consumes 2 seconds.

## Latency Model

A simplified request latency model is:

```text
Total Latency =
    DNS
  + TCP/TLS
  + CloudFront processing
  + Origin connection
  + Origin processing
  + Database/dependency processing
  + Response transfer
```

For a cache hit:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
Cache
  │
  ▼
Client
```

For a cache miss:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
Origin
  │
  ▼
Application
  │
  ├── Database
  ├── Redis
  └── External API
  │
  ▼
CloudFront
  │
  ▼
Client
```

The two paths can have radically different latency characteristics.

## Latency Percentiles

Average latency is useful, but it can hide tail latency.

| Metric | Meaning | Operational value |
|---|---|---|
| P50 | Median latency | Represents typical traffic |
| P95 | 95th percentile | Captures meaningful slow requests |
| P99 | 99th percentile | Reveals severe tail latency |
| Maximum | Slowest observed request | Useful for incident investigation |
| Average | Arithmetic mean | Useful for broad trends but can hide outliers |

For production systems, P95 and P99 are usually more useful than the average when investigating user-facing latency.

Example:

```text
P50 = 120 ms
P95 = 900 ms
P99 = 4.8 s
```

The average might look acceptable while 1% of requests are taking several seconds.

## Establish a Baseline

Before changing configuration, establish the current behavior.

Measure a CloudFront endpoint:

```bash
curl -sS \
  -o /dev/null \
  -w 'status=%{http_code} total=%{time_total}s\n' \
  https://cdn.example.com/assets/app.js
```

For an API:

```bash
curl -sS \
  -o /dev/null \
  -w 'status=%{http_code} total=%{time_total}s\n' \
  https://api.example.com/orders/123
```

Inspect response headers:

```bash
curl -sS -D - \
  -o /dev/null \
  https://cdn.example.com/assets/app.js
```

Useful headers can include:

- `X-Cache`
- `Age`
- `Via`
- `Cache-Control`
- `ETag`
- `Content-Length`

Do not rely on a single request. Compare multiple requests and, where relevant, multiple geographic locations.

## Compare CloudFront With the Origin

One of the fastest ways to narrow the problem is to compare the public CloudFront endpoint with the origin.

CloudFront:

```bash
curl -sS \
  -o /dev/null \
  -w 'CloudFront: status=%{http_code} total=%{time_total}s\n' \
  https://api.example.com/orders/123
```

Origin:

```bash
curl -sS \
  -o /dev/null \
  -w 'Origin: status=%{http_code} total=%{time_total}s\n' \
  https://origin.example.com/orders/123
```

Interpret the result carefully:

| CloudFront | Origin | Likely direction |
|---|---|---|
| Fast | Fast | Investigate client/network-specific behavior |
| Slow | Fast | Investigate edge/network/configuration |
| Slow | Slow | Origin path likely contributes |
| Fast on cache hit | Slow on cache miss | Investigate origin path |
| Slow only in some regions | Fast elsewhere | Investigate geography/network |
| Slow for large objects | Fast for small objects | Investigate transfer size |

Origin testing should be performed safely. Do not expose a private production origin merely to make troubleshooting easier.

## Cache Hit and Cache Miss Analysis

CloudFront can dramatically reduce latency when an object is served from the edge.

```text
Cache HIT:

Client
  │
  ▼
CloudFront
  │
  ▼
Cached Object
  │
  ▼
Client
```

A cache miss requires an origin request:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
Cache MISS
  │
  ▼
Origin
  │
  ▼
Response
```

A common mistake is assuming that all CloudFront traffic is cached.

Static assets are generally good caching candidates:

```text
/static/app.js
/static/app.css
/images/logo.webp
/fonts/inter.woff2
```

Dynamic authenticated API requests often require different treatment:

```text
/api/orders
/api/profile
/api/payment-status
```

Caching decisions must preserve response correctness and authorization boundaries.

## Cache Hit Ratio

A low cache hit ratio increases origin traffic and can indirectly increase latency.

Consider:

```text
100,000 requests
      │
      ├── 95,000 cache hits
      │
      └── 5,000 origin requests
```

versus:

```text
100,000 requests
      │
      ├── 40,000 cache hits
      │
      └── 60,000 origin requests
```

The second architecture places significantly more load on the origin.

Investigate:

- Cache policy
- Cache key
- Query-string behavior
- Header behavior
- Cookie behavior
- Object TTL
- Explicit cache-control headers
- Cache invalidations

## Cache Key Fragmentation

Including unnecessary request attributes in a cache key creates additional cache variants.

For example:

```text
/assets/app.js?user=123
/assets/app.js?user=456
/assets/app.js?user=789
```

If the user identifier does not affect the response, varying the cache key by it destroys cache efficiency.

Similarly:

```text
/assets/app.js
  + Accept-Language
  + Cookie
  + unnecessary query parameters
  + unnecessary headers
```

can create many logically identical cache objects.

The cache key should contain only attributes required for response correctness.

## Origin Response Latency

For cache misses and dynamic requests, the origin becomes part of the critical path.

A simplified latency breakdown might be:

```text
CloudFront             20 ms
ALB                     8 ms
Nginx                   5 ms
Django                120 ms
PostgreSQL          1,800 ms
External API          400 ms
--------------------------------
Total                2,353 ms
```

In this case, reducing CloudFront processing by 10 ms is not the right optimization.

The database and external dependency should be investigated first.

## CloudFront Configuration Inspection

Retrieve the distribution configuration:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID"
```

Retrieve the distribution configuration separately when you need the configuration document used for updates:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID"
```

Inspect:

- Origins
- Origin protocol
- Behaviors
- Cache policies
- Origin request policies
- Viewer protocol policy
- Compression
- Allowed methods
- Query-string behavior
- Header forwarding
- Cookie forwarding

Avoid changing multiple production settings simultaneously during an incident. A controlled change makes the resulting latency difference measurable.

## Application-Level Latency

For Django or FastAPI, break latency down by endpoint.

Example:

```text
GET /health                 20 ms
GET /users                  80 ms
GET /orders                140 ms
GET /reports              4.2 s
POST /payments             900 ms
```

A global application P95 does not tell you which endpoint is responsible.

Measure:

- Endpoint latency
- Serialization time
- Database time
- Cache time
- External API time
- Queueing time
- CPU time
- Connection-pool wait time

## Django ORM Latency

Django applications can experience latency from inefficient ORM usage.

A classic example is an N+1 query pattern:

```text
1 query:
    fetch 100 orders

100 queries:
    fetch customer for each order

Total:
    101 queries
```

Use relationship-aware loading where appropriate:

```python
orders = (
    Order.objects
    .select_related("customer")
    .prefetch_related("items")
    .filter(status="active")
)
```

The correct optimization depends on relationship cardinality and query behavior.

For expensive queries, inspect SQL and query plans rather than optimizing solely from Python code.

## PostgreSQL Latency

A slow API can be caused by a slow database query, lock contention, or connection-pool exhaustion.

Inspect active sessions:

```sql
SELECT
    pid,
    usename,
    state,
    wait_event_type,
    wait_event,
    query_start,
    now() - query_start AS duration,
    query
FROM pg_stat_activity
WHERE state <> 'idle'
ORDER BY query_start;
```

Investigate:

- Long-running queries
- Lock waits
- Missing indexes
- Sequential scans
- Expensive joins
- Large sorts
- Connection exhaustion
- Poor pagination
- Transaction contention

For a specific query:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM orders
WHERE customer_id = 123
ORDER BY created_at DESC
LIMIT 50;
```

Do not increase database resources before determining whether the workload is inefficient.

## Database Connection Pooling

A request may spend significant time waiting for a database connection.

```text
Request
  │
  ▼
Application
  │
  │ wait
  ▼
Connection Pool
  │
  │ connection acquired
  ▼
PostgreSQL
```

Monitor:

- Active connections
- Pool utilization
- Pool wait time
- Query duration
- Application worker count
- PostgreSQL connection limits

Increasing the pool size without considering PostgreSQL capacity can make the system less stable.

## Redis Latency

Redis is usually low-latency, but it can still contribute to request latency.

Investigate:

- Network distance
- Connection-pool exhaustion
- Large values
- Expensive commands
- CPU saturation
- Memory pressure
- Cross-region access

For latency-sensitive workloads, keep the application and Redis deployment geographically and architecturally close.

Do not introduce cross-region Redis calls into the synchronous request path unless the latency tradeoff is explicitly justified.

## External API Latency

External dependencies frequently dominate tail latency.

```text
CloudFront
   ↓
FastAPI
   ↓
Payment Provider
   ↓
4-second response
   ↓
FastAPI
   ↓
CloudFront
   ↓
Client
```

Use explicit timeouts.

```python
import httpx


async def fetch_payment_status(payment_id: str) -> dict:
    timeout = httpx.Timeout(
        connect=2.0,
        read=5.0,
        write=5.0,
        pool=2.0,
    )

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(
            "https://payments.example.com/status",
            params={"payment_id": payment_id},
        )
        response.raise_for_status()
        return response.json()
```

A timeout should be aligned with the endpoint's latency budget.

Do not allow a downstream service to consume the entire client request deadline.

## Retry Amplification

Retries can turn latency into a cascading capacity problem.

```text
Dependency slows
      ↓
Request times out
      ↓
Client retries
      ↓
More traffic
      ↓
Dependency slows further
      ↓
More timeouts
```

Use:

- Bounded retries
- Exponential backoff
- Jitter
- Retryable-error classification
- Request deadlines
- Circuit breakers where appropriate

Never retry every failure.

A retry of a non-idempotent operation such as a payment operation can also introduce correctness problems in addition to latency.

## Microservice Latency Chains

Consider:

```text
CloudFront
    ↓
Service A
    ↓
Service B
    ↓
Service C
    ↓
PostgreSQL
```

Sequential dependencies add latency:

```text
A       100 ms
B       150 ms
C       250 ms
DB      500 ms
----------------
Total 1,000 ms
```

Independent operations may sometimes be performed concurrently:

```text
             ┌── Service B ──┐
Service A ───┤               ├── Response
             └── Service C ──┘
```

However, concurrency increases downstream load. Bound concurrent work and account for downstream capacity.

## gRPC Latency

For gRPC service-to-service communication, investigate:

- Connection establishment
- TLS
- DNS
- Serialization
- Network distance
- Server processing
- Client queueing
- Deadlines
- Retries

Propagate deadlines through synchronous service calls when possible.

A downstream service should know when the original request no longer has enough time to produce a useful response.

## Nginx and Reverse Proxy Latency

A production request may pass through:

```text
CloudFront
    ↓
ALB
    ↓
Nginx
    ↓
Gunicorn / Uvicorn
    ↓
Application
```

Inspect:

- Upstream response time
- Connection time
- Request time
- Active connections
- Worker utilization
- Queueing

Example timeout configuration:

```nginx
proxy_connect_timeout 5s;
proxy_send_timeout 30s;
proxy_read_timeout 30s;
```

Timeout values should be based on the service's actual latency budget. Increasing them blindly can cause resources to remain occupied longer.

## Kubernetes Latency

For Kubernetes-backed origins, inspect:

- CPU throttling
- Memory pressure
- Pod restarts
- Readiness failures
- Ingress latency
- HPA behavior
- Node pressure
- Service routing
- DNS latency
- Network policies

Inspect pods:

```bash
kubectl get pods \
  -n production \
  -o wide
```

Inspect resource usage:

```bash
kubectl top pods \
  -n production
```

Inspect rollout state:

```bash
kubectl rollout status \
  deployment/api \
  -n production
```

A container can have apparently reasonable average CPU utilization while experiencing CPU throttling that increases tail latency.

## Geographic Latency

CloudFront reduces client-to-edge distance, but dynamic requests can still have significant edge-to-origin latency.

For example:

```text
Client: India
    ↓
CloudFront edge: India
    ↓
Origin: United States
    ↓
Database: United States
```

A cache miss still requires communication with the distant origin.

For globally distributed applications, consider:

- Origin geography
- Multi-region APIs
- Database locality
- Regional caches
- Cross-region dependencies
- Replication strategy

Multi-region architecture adds substantial operational complexity and should be justified by actual latency, availability, or regulatory requirements.

## Cross-Region Dependencies

A common high-latency architecture is:

```text
India Client
    ↓
CloudFront India Edge
    ↓
US API
    ↓
US Redis
    ↓
US PostgreSQL
```

CloudFront improves the first network segment but cannot eliminate latency between the edge and US origin infrastructure.

A regional design might instead be:

```text
                 CloudFront
                /          \
               /            \
        Region A            Region B
           │                   │
          API                 API
           │                   │
         Cache               Cache
           │                   │
       Database            Database
```

This architecture can reduce geographic latency but introduces:

- Data replication
- Consistency concerns
- Failover complexity
- Operational overhead
- Higher infrastructure cost

## Large Response Payloads

A fast application can still produce a slow user experience if the response is large.

Measure response size:

```bash
curl -sS \
  -o /dev/null \
  -w 'status=%{http_code} size=%{size_download} bytes total=%{time_total}s\n' \
  https://cdn.example.com/api/data
```

For APIs:

- Use pagination.
- Avoid unnecessary fields.
- Avoid returning entire object graphs.
- Compress suitable content.
- Stream appropriate workloads.
- Move large file delivery to object storage.

For static files, CloudFront can reduce repeated origin work by caching the object at the edge.

## Compression

Compression can reduce response transfer time and bandwidth.

Good candidates include:

- HTML
- CSS
- JavaScript
- JSON
- XML
- Plain text

Already-compressed formats usually provide little additional benefit:

- JPEG
- PNG
- WebP
- ZIP
- MP4
- GZIP archives

Compression should be evaluated against CPU cost and actual response size.

## Large Request Payloads

Large request bodies can also contribute to latency.

Examples:

- File uploads
- Bulk JSON requests
- Large batch operations

Do not force large asynchronous workloads through a synchronous application endpoint when the architecture can be redesigned.

A better upload architecture is often:

```text
Client
   │
   │ request upload authorization
   ▼
API
   │
   ▼
Presigned S3 URL
   │
   ▼
Client
   │
   │ direct upload
   ▼
S3
   │
   ▼
Event / Queue
   │
   ▼
Celery / Worker
```

This removes large payload transfer from the synchronous API path.

## TLS and Connection Establishment

Connection setup can contribute to latency, especially when connections are repeatedly created.

Investigate:

- DNS resolution
- TCP connection setup
- TLS handshake
- Connection reuse
- HTTP protocol behavior
- Geographic distance

CloudFront terminates viewer connections at the edge, but cache misses still require efficient edge-to-origin communication.

## DNS Latency

DNS is part of end-to-end latency and should be measured when relevant.

```bash
dig cdn.example.com
```

For statistics:

```bash
dig +stats cdn.example.com
```

Compare DNS behavior across regions if the issue is geographically localized.

Do not optimize DNS simply because it is present in the request path. First determine whether it contributes materially to the observed latency.

## Monitoring and Observability

CloudFront metrics should be correlated with origin and application telemetry.

Useful signals include:

- Request count
- Error rate
- Cache hit ratio
- Response latency
- Bytes transferred
- Geographic distribution
- Origin latency

A useful operational dashboard can correlate:

```text
CloudFront P95/P99
       │
       ├── Cache Hit Ratio
       │
       ├── Origin Latency
       │
       ├── ALB Target Response Time
       │
       ├── Application P95/P99
       │
       ├── PostgreSQL Latency
       │
       ├── Redis Latency
       │
       └── External API Latency
```

The purpose is to determine whether the latency originates at the edge or deeper in the request path.

## Distributed Tracing

Distributed tracing is particularly useful for dynamic APIs and microservices.

Example:

```text
Request
│
├── API authentication       20 ms
├── PostgreSQL             900 ms
├── Redis                    10 ms
├── Payment API             800 ms
└── Serialization            30 ms
                            -----
                            1.76 s
```

Without tracing, the endpoint may simply appear to have a 1.76-second response time.

With tracing, the expensive spans become visible.

Propagate correlation information across:

- REST services
- gRPC services
- Background jobs
- Logs
- Database instrumentation

## Structured Logging

Logs should help answer:

- Which endpoint was slow?
- Which request was slow?
- Which dependency was slow?
- How long did each dependency take?
- Which application version handled the request?
- Which region handled the request?

Example:

```json
{
  "request_id": "7f4b2d",
  "method": "GET",
  "path": "/orders/123",
  "status": 200,
  "duration_ms": 1842,
  "db_duration_ms": 1200,
  "redis_duration_ms": 8,
  "external_api_duration_ms": 580
}
```

Do not add sensitive request data to logs simply for troubleshooting.

## Latency Investigation Workflow

### Reproduce the Problem

Measure the public endpoint:

```bash
curl -sS \
  -o /dev/null \
  -w 'status=%{http_code} total=%{time_total}s\n' \
  https://cdn.example.com/api/orders/123
```

### Determine Cache Behavior

Inspect response headers:

```bash
curl -sS -D - \
  -o /dev/null \
  https://cdn.example.com/static/app.js
```

Determine whether the response is being served from cache or requires an origin fetch.

### Compare the Origin

Measure the origin independently when safe and supported:

```bash
curl -sS \
  -o /dev/null \
  -w 'status=%{http_code} total=%{time_total}s\n' \
  https://origin.example.com/api/orders/123
```

### Inspect CloudFront

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID"
```

### Inspect the Load Balancer

Review:

- Target response time
- Healthy target count
- Target errors
- Load-balancer errors
- Request volume

### Inspect the Application

Review:

- P50
- P95
- P99
- Request rate
- CPU
- Memory
- Worker utilization
- Connection pools
- Endpoint-specific latency

### Inspect Dependencies

Review:

- PostgreSQL query latency
- PostgreSQL locks
- Redis latency
- External API latency
- Kafka consumer lag
- Celery queue depth

### Inspect Network Behavior

Investigate when relevant:

- DNS
- TLS
- Geography
- Cross-region traffic
- Network distance
- Origin connectivity

### Check Recent Changes

Correlate the incident with:

- Application deployments
- CloudFront configuration changes
- Cache-policy changes
- Database migrations
- Infrastructure changes
- Traffic spikes
- Dependency degradation

### Validate the Fix

Compare latency distributions before and after the change:

```text
Before:
P50 = 180 ms
P95 = 2.4 s
P99 = 5.8 s

After:
P50 = 160 ms
P95 = 420 ms
P99 = 900 ms
```

The goal is not merely to make one request faster. The goal is to improve latency consistently under realistic production traffic.

## Common Production Pitfalls

### Looking Only at Average Latency

Average latency can hide serious tail latency.

**Avoid it:** monitor P95 and P99.

### Assuming CloudFront Is the Bottleneck

CloudFront is the public entry point, so it is often blamed first.

**Avoid it:** compare CloudFront latency with origin latency.

### Ignoring Cache Misses

A cache hit can be extremely fast while a cache miss is dominated by origin latency.

**Avoid it:** analyze cache-hit ratio and cache-miss behavior separately.

### Over-Fragmenting the Cache

Excessive cache-key dimensions reduce cache efficiency.

**Avoid it:** include only attributes that affect response correctness.

### Increasing Timeouts

Longer timeouts allow slow requests to consume resources for longer.

**Avoid it:** fix the dependency or workload causing the delay.

### Adding Unbounded Retries

Retries can amplify traffic against an already degraded dependency.

**Avoid it:** use bounded retries, backoff, jitter, and deadlines.

### Scaling the Wrong Layer

Adding API instances does not necessarily solve a saturated database.

**Avoid it:** identify the constrained resource before scaling.

### Ignoring Geographic Differences

A service may be fast in one region and slow in another.

**Avoid it:** segment latency by geography.

### Ignoring Dependency Chains

A single downstream dependency can dominate the entire request latency.

**Avoid it:** use tracing and dependency-level timing.

### Optimizing Without Measurement

Changing configuration without a baseline makes it difficult to determine whether the change helped.

**Avoid it:** measure, change one meaningful variable, and measure again.

## Security Considerations

Latency troubleshooting should never require weakening security controls.

Avoid:

- Disabling WAF protections.
- Making private origins publicly accessible.
- Broadening security groups unnecessarily.
- Disabling TLS validation.
- Removing authentication.
- Exposing internal services for convenience.

Security controls can themselves contribute to latency, but their performance impact should be measured rather than removed blindly.

Also ensure that cache configuration cannot accidentally serve authenticated or user-specific responses to other users.

## Scalability Considerations

Latency problems frequently become capacity problems as traffic increases.

```text
Traffic
   │
   ▼
CloudFront
   │
   ├── Cache HIT ───────────────► Response
   │
   └── Cache MISS
          │
          ▼
        Origin
          │
          ▼
      Application
          │
          ▼
       Database
```

If the cache hit ratio decreases during a traffic spike:

```text
More cache misses
       ↓
More origin requests
       ↓
More application work
       ↓
More database queries
       ↓
Higher latency
       ↓
More timeouts
       ↓
Potential retries
       ↓
Even more load
```

Capacity planning must therefore consider CloudFront caching, origin concurrency, database capacity, connection pools, and dependency limits together.

## High Availability and Reliability

Production systems should prevent a slow dependency from consuming all available application capacity.

Recommended practices include:

- Multi-AZ application deployment.
- Appropriate autoscaling.
- Explicit dependency timeouts.
- Bounded retries.
- Exponential backoff and jitter.
- Circuit breakers where appropriate.
- Graceful degradation.
- Effective caching.
- Database capacity planning.
- Queue-based processing for long-running work.
- Distributed tracing.
- P95/P99 monitoring.
- Automated rollback.

For global applications, multi-region architecture can reduce geographic latency and improve resilience, but it introduces significant complexity around data replication, consistency, failover, and operations.

## Cost Considerations

High latency can increase infrastructure cost because slow requests consume resources for longer.

Potential consequences include:

- Higher application compute usage.
- More database connections.
- Higher database CPU utilization.
- More load-balancer connections.
- More network transfer.
- More retries.
- Larger queue backlogs.
- Increased autoscaling requirements.

Latency optimization should therefore be evaluated in terms of both user experience and resource efficiency.

## Disaster Recovery Considerations

A disaster recovery strategy should distinguish between availability failures and latency degradation.

For critical workloads, consider:

- Multi-AZ origin infrastructure.
- Tested origin failover where appropriate.
- Multi-region architecture when justified.
- Database replication and recovery procedures.
- Redis recovery strategy.
- Infrastructure-as-code for CloudFront configuration.
- Version-controlled cache and origin policies.
- Tested deployment rollback procedures.

Do not introduce multi-region infrastructure solely because a latency problem exists. First determine whether the problem is actually geographic.

## Interview Perspective

A strong answer to:

> "CloudFront requests are suddenly much slower. How would you troubleshoot the problem?"

should demonstrate end-to-end reasoning.

A practical investigation would be:

1. Establish a latency baseline.
2. Measure P50, P95, and P99.
3. Reproduce the request through CloudFront.
4. Determine cache-hit versus cache-miss behavior.
5. Compare CloudFront latency with origin latency.
6. Inspect ALB target response time.
7. Inspect application endpoint latency.
8. Inspect PostgreSQL, Redis, Kafka, and external dependency latency.
9. Check worker and connection-pool saturation.
10. Investigate DNS, TLS, and geographic behavior when relevant.
11. Inspect distributed traces.
12. Check retry behavior and retry amplification.
13. Correlate the issue with deployments and configuration changes.
14. Fix the dominant latency contributor.
15. Re-measure under representative production traffic.

The senior-level answer should emphasize **measurement, decomposition, latency budgets, and dependency behavior** rather than immediately changing CloudFront settings.

## Key Takeaways

- **Treat latency as an end-to-end problem:** CloudFront, the origin, application, database, cache, network, and external dependencies can all contribute to response time.
- **Measure P95 and P99:** tail latency often exposes production problems that average latency hides.
- **Separate cache hits from cache misses:** CloudFront can serve cached content quickly while dynamic or uncached requests remain dependent on origin performance.
- **Optimize the dominant contributor:** use metrics, logs, and distributed tracing to identify where the latency budget is actually being consumed.
- **Control latency under load:** explicit timeouts, bounded retries, efficient caching, capacity planning, and asynchronous processing prevent slow requests from becoming cascading failures.