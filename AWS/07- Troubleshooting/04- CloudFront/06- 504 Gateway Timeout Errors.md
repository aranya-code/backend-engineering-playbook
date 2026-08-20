# 06- 504 Gateway Timeout Errors

## Overview

A `504 Gateway Timeout` indicates that a gateway or proxy did not receive a timely response from an upstream service. In a CloudFront architecture, the important distinction is that a `504` usually represents a **timeout somewhere in the request path**, not necessarily a failure in CloudFront itself.

A typical backend request path is:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
ALB / Origin
  │
  ▼
Nginx / Ingress
  │
  ▼
Django / FastAPI
  │
  ├── PostgreSQL
  ├── Redis
  ├── Kafka
  └── External APIs
```

A timeout can occur at any of these boundaries:

- CloudFront waiting for the origin.
- ALB waiting for a target.
- Nginx waiting for an application process.
- Django or FastAPI waiting for a database query.
- An application waiting for Redis.
- A microservice waiting for another microservice.
- An external API taking too long to respond.
- Network connectivity delaying or preventing communication.
- Application workers being saturated.
- A deployment causing severe latency or resource contention.

The correct troubleshooting strategy is therefore to identify **which upstream interaction exceeded its timeout budget**.

## 504 Versus Other Gateway Errors

| Status | Typical meaning | Primary investigation |
|---|---|---|
| `502` | Invalid or failed gateway/upstream response | Connectivity, protocol, upstream failure |
| `503` | Service temporarily unavailable | Capacity, health, availability |
| `504` | Upstream response did not arrive in time | Latency, timeout, dependency failure |
| `500` | Application/server error | Application logs and exceptions |

A `504` is fundamentally a **latency and deadline problem**.

The system may be completely healthy from a process perspective while still being unavailable from the client's perspective because the request exceeds an upstream timeout.

## Why 504 Errors Are Difficult

A timeout is often the final symptom rather than the original failure.

For example:

```text
Client
  ↓
CloudFront
  ↓
ALB
  ↓
Django
  ↓
PostgreSQL
  ↓
Slow query
  ↓
Application waits
  ↓
ALB timeout
  ↓
CloudFront receives timeout/failure
  ↓
Client sees 504
```

The database may therefore be the actual root cause even though the user sees an error associated with the CDN endpoint.

This is why increasing the CloudFront timeout without investigating the backend can make an incident worse rather than fixing it.

## Request Lifecycle

```mermaid
sequenceDiagram
    participant C as Client
    participant CF as CloudFront
    participant ALB as ALB
    participant APP as Django/FastAPI
    participant DB as PostgreSQL

    C->>CF: HTTPS request
    CF->>ALB: Origin request
    ALB->>APP: Forward request
    APP->>DB: Slow query
    DB-->>APP: Delayed response
    APP-->>ALB: Response
    ALB-->>CF: Response
    CF-->>C: Response
```

If the response arrives after an intermediary's timeout, the client may receive a `504` even if the backend eventually completes the operation.

The diagnostic objective is to determine:

```text
Which component was waiting?
Which component was being waited on?
What timeout expired first?
Why did the upstream take that long?
```

## Establish the Failure Boundary

Start with the public CloudFront endpoint:

```bash
curl -sS -D - \
  -o /dev/null \
  https://cdn.example.com/api/orders/123
```

For more detailed information:

```bash
curl -sv \
  https://cdn.example.com/api/orders/123 \
  -o /dev/null
```

Record:

- HTTP status
- Response headers
- `X-Cache`
- `Age`
- `Via`
- Request URL
- HTTP method
- Timestamp
- Response duration

Then test the origin directly:

```bash
curl -sv \
  https://origin.example.com/api/orders/123 \
  -o /dev/null
```

If the origin requires a specific host header:

```bash
curl -sv \
  https://origin.example.com/api/orders/123 \
  -H 'Host: api.example.com' \
  -o /dev/null
```

This comparison immediately separates many CloudFront-specific problems from origin-side latency.

## CloudFront Versus Origin

| CloudFront | Origin | Likely direction |
|---|---|---|
| `504` | Fast `200` | CloudFront/origin connectivity or CloudFront configuration |
| `504` | `504` | Origin-side gateway timeout |
| `504` | Very slow `200` | Origin latency or timeout mismatch |
| `504` | Connection timeout | Networking or origin reachability |
| `200` | `200` | Investigate request-specific edge behavior |
| `200` | Slow | CloudFront may still be masking origin latency through caching |

Do not infer the root cause from the public status code alone.

## Inspect CloudFront Configuration

Inspect the distribution:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID"
```

Inspect configured origins:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  --query 'DistributionConfig.Origins.Items[*].{Id:Id,Domain:DomainName,Path:OriginPath}'
```

Inspect cache behaviors:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  --query 'DistributionConfig.CacheBehaviors.Items[*].{Path:PathPattern,Origin:TargetOriginId}'
```

When investigating timeouts, verify:

- Origin domain
- Origin path
- Origin protocol policy
- Origin response timeout
- Origin connection attempts
- Origin connection timeout
- Cache behavior
- Origin request policy
- Recent distribution changes

The exact timeout settings depend on the CloudFront origin type and configuration.

## CloudFront Origin Timeout

CloudFront has an origin response timeout that determines how long it waits for a response from the origin after establishing the connection and sending the request.

The important engineering principle is:

> The CloudFront timeout must be compatible with the application's expected response time and the timeout budgets of downstream dependencies.

For example:

```text
CloudFront response timeout: 60s
ALB idle timeout:            60s
Application request timeout: 30s
Database query timeout:      10s
External API timeout:         5s
```

This is generally easier to reason about than allowing an outer layer to wait indefinitely for an inner layer.

Timeout values should not be increased blindly. A larger timeout can increase resource occupancy and allow more concurrent slow requests to accumulate.

## Timeout Budgeting

Production systems should treat timeouts as a hierarchy.

For example:

```text
Client
  │
  │  30s
  ▼
CloudFront
  │
  │  25s
  ▼
ALB
  │
  │  20s
  ▼
Application
  │
  ├── PostgreSQL: 8s
  ├── Redis: 2s
  └── External API: 5s
```

The exact numbers are workload-specific, but the principle is important:

- Every downstream operation needs a bounded timeout.
- Outer layers need enough budget to receive the response.
- Inner dependencies should generally fail before the outer gateway times out.
- Retries must fit inside the overall deadline.
- Long-running operations should usually be asynchronous.

Without explicit timeout budgets, systems often accumulate requests until workers, connections, or memory are exhausted.

## Slow Application Requests

Django and FastAPI requests can become slow because of:

- Expensive database queries
- N+1 queries
- Large response serialization
- CPU-intensive processing
- External API calls
- Blocking operations inside asynchronous code
- Lock contention
- Thread/process exhaustion
- Garbage collection pressure
- Large file processing
- Synchronous calls to slow dependencies

For a FastAPI service, an async endpoint can still block the event loop if it performs blocking work:

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/reports/{report_id}")
async def get_report(report_id: int):
    # A blocking database or HTTP operation here can delay
    # unrelated requests handled by the same event loop.
    report = await fetch_report(report_id)
    return report
```

The key question is not whether an endpoint is declared `async`. The question is whether the entire execution path is compatible with the concurrency model.

## Database-Induced Timeouts

A common failure path is:

```text
CloudFront
    ↓
ALB
    ↓
Django/FastAPI
    ↓
PostgreSQL
    ↓
Slow query / lock
    ↓
Application waits
    ↓
Gateway timeout
```

Inspect PostgreSQL activity:

```sql
SELECT
    pid,
    usename,
    application_name,
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

Look for:

- Long-running queries
- Lock waits
- Sequential scans on large tables
- Missing indexes
- Connection saturation
- Transactions left open
- Database CPU saturation
- I/O contention

A timeout is often a symptom of a database performance problem rather than an HTTP problem.

## Query Optimization

If a request performs:

```text
API
 ↓
PostgreSQL
 ↓
Large table scan
 ↓
Several seconds
```

inspect the query plan:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM orders
WHERE customer_id = 123
ORDER BY created_at DESC
LIMIT 50;
```

Potential improvements include:

- Appropriate indexes
- Query restructuring
- Pagination
- Selecting only required columns
- Avoiding N+1 queries
- Reducing unnecessary joins
- Query result caching
- Precomputed data
- Read replicas where appropriate

Do not add indexes without evaluating their write and storage costs.

## PostgreSQL Connection Pool Exhaustion

A database can be responsive while the application cannot obtain a connection.

```text
Application workers
      │
      ├── Connection
      ├── Connection
      ├── Connection
      └── Waiting
             │
             ▼
       Pool exhausted
             │
             ▼
       Request timeout
```

Inspect connection usage:

```sql
SELECT
    state,
    count(*)
FROM pg_stat_activity
GROUP BY state;
```

Increasing the connection pool is not always the solution.

If:

```text
Workers = 100
Pool = 100
Database max connections = 120
```

adding more workers can quickly overload PostgreSQL.

Connection capacity must be designed across the entire application fleet.

## Redis Timeouts

Redis can cause application requests to exceed their deadline:

```text
API
 ↓
Redis
 ↓
Network delay / saturation
 ↓
Redis request waits
 ↓
Application timeout
 ↓
504
```

Use bounded Redis client timeouts.

For Python applications, distinguish between:

- Connection timeout
- Socket/read timeout
- Pool acquisition timeout

The application should fail quickly when Redis is an optional dependency.

For a cache:

```text
Redis unavailable
      ↓
Cache miss/failure
      ↓
PostgreSQL
      ↓
Response
```

may be preferable to:

```text
Redis unavailable
      ↓
Request waits indefinitely
      ↓
504
```

However, this fallback must be designed carefully because a Redis outage can suddenly shift large amounts of traffic to PostgreSQL.

## Cache Stampede During Redis Failure

A cache outage can create a secondary database outage:

```text
Redis failure
    ↓
Cache misses
    ↓
More PostgreSQL queries
    ↓
Database load increases
    ↓
Query latency increases
    ↓
Application requests slow down
    ↓
504 errors
```

Production mitigation may include:

- Request coalescing
- Cache warming
- Rate limiting
- Circuit breakers
- Stale-cache serving
- Database capacity planning
- Controlled fallback behavior

This is a classic example of why a dependency that appears to be "only a cache" can still affect system availability.

## External API Timeouts

Consider:

```text
CloudFront
    ↓
API
    ↓
Payment provider
    ↓
Slow response
    ↓
API waits
    ↓
CloudFront timeout
```

The external request should have its own deadline:

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

The exact timeout values should be derived from the service-level objective and dependency behavior.

Avoid using unlimited HTTP client timeouts in production.

## Microservice Chain Timeouts

A synchronous microservice chain can amplify latency:

```text
CloudFront
    ↓
Service A
    ↓
Service B
    ↓
Service C
    ↓
Database
```

If every layer waits for every downstream operation, total latency becomes:

```text
T_total ≈
T_A + T_B + T_C + T_DB
```

Retries can make this substantially worse.

A production system should define:

- Request deadlines
- Per-hop timeouts
- Retry limits
- Retryable errors
- Circuit-breaker behavior
- Idempotency
- Fallback behavior

For gRPC, deadline propagation is particularly useful because downstream services can stop work when the original request deadline has expired.

## Nginx Timeout Problems

For an Nginx layer:

```text
CloudFront
    ↓
ALB
    ↓
Nginx
    ↓
Gunicorn/Uvicorn
```

inspect relevant timeout configuration.

Examples include:

```nginx
proxy_connect_timeout 5s;
proxy_send_timeout 30s;
proxy_read_timeout 30s;
```

These values should be aligned with the application's actual response-time requirements.

For example, if Nginx stops waiting after `30s` while CloudFront waits for `60s`, the Nginx layer can generate the failure before CloudFront reaches its timeout.

The objective is not to make every timeout identical. The objective is to create a deliberate timeout hierarchy.

## Gunicorn and Uvicorn Worker Saturation

A Python application can become slow even when CPU utilization is moderate if all workers are occupied.

For example:

```text
Gunicorn
 ├── Worker 1 → slow external API
 ├── Worker 2 → slow database query
 ├── Worker 3 → slow report generation
 └── Worker 4 → slow file operation
```

New requests wait for available workers.

Inspect:

- Worker count
- Worker restarts
- Request latency
- Worker timeouts
- CPU
- Memory
- Blocking operations
- Long-running endpoints

Do not blindly increase worker count. More workers can increase:

- Memory usage
- Database connections
- Context switching
- Downstream load

Worker count should be based on workload and resource capacity.

## CPU-Bound Work

A synchronous API request that performs expensive CPU work can exceed the gateway timeout:

```text
Request
  ↓
API worker
  ↓
CPU-intensive operation
  ↓
Worker unavailable
  ↓
Requests queue
  ↓
504
```

Examples include:

- Large image processing
- PDF generation
- Machine-learning inference
- Large data transformations
- Cryptographic operations

Move long-running CPU-intensive operations to background workers where the business operation permits it.

A typical architecture is:

```text
Client
  ↓
API
  ↓
Create job
  ↓
Celery / Queue
  ↓
Worker
  ↓
Object storage
  ↓
Client polls/downloads result
```

## Long-Running HTTP Operations

A request such as:

```text
POST /generate-large-report
```

should not necessarily keep an HTTP connection open while generating a report for several minutes.

A more resilient pattern is:

```text
POST /reports
    ↓
Create job
    ↓
202 Accepted
    ↓
Background worker
    ↓
Generate report
    ↓
S3
    ↓
Client retrieves result
```

This avoids coupling long-running work to CloudFront and other gateway timeout limits.

## Networking and Origin Reachability

A timeout can indicate that CloudFront cannot successfully communicate with the configured origin.

Investigate:

- Origin DNS
- Origin protocol
- TLS handshake
- Security groups
- Network ACLs
- Routing
- Private/public reachability
- Origin availability
- Firewall rules
- Load balancer listeners

For a public origin:

```bash
dig origin.example.com
```

Test TLS:

```bash
openssl s_client \
  -connect origin.example.com:443 \
  -servername origin.example.com
```

Test HTTP connectivity:

```bash
curl -sv \
  https://origin.example.com/health
```

A DNS or TLS problem can manifest as an origin communication failure rather than an application exception.

## ALB Timeout Behavior

For CloudFront → ALB architectures, inspect the ALB configuration and metrics.

The ALB's timeout behavior and CloudFront's timeout behavior must be considered together.

For example:

```text
CloudFront timeout = 60s
ALB timeout        = 30s
Application        = 45s
```

The ALB may terminate the request before the application finishes.

Alternatively:

```text
CloudFront timeout = 30s
ALB timeout        = 60s
Application        = 45s
```

CloudFront may terminate the request first.

Neither configuration is automatically correct. The timeout hierarchy must reflect the service's intended latency budget.

## Health Checks Versus Request Latency

Health checks can reveal an overloaded system before user requests fail.

However, a health check that executes expensive application logic can make the problem worse.

Avoid:

```text
/health
  ↓
Complex database query
  ↓
Multiple external dependencies
```

Prefer lightweight health endpoints and separate readiness checks.

A production readiness check should answer whether the instance can safely receive traffic, not whether every dependency in the entire architecture is perfect.

## CloudFront Caching and 504 Responses

Cached content can hide origin latency.

For example:

```text
Request A
  ↓
CloudFront cache HIT
  ↓
Fast response

Request B
  ↓
Cache MISS
  ↓
Slow origin
  ↓
504
```

If only cache misses produce timeouts, investigate the origin path rather than assuming that CloudFront itself is unstable.

This is especially important for:

- Dynamic APIs
- Personalized responses
- Cache-disabled paths
- Low-cache-hit endpoints
- Large objects

Compare error rates between cache hits and misses where telemetry permits.

## Logging and Observability

Use metrics and logs together.

### CloudFront Signals

Monitor:

- `5xx` error rate
- Request count
- Cache hit ratio
- Latency-related metrics
- Error distribution by path
- Error distribution by geography

### ALB Signals

Monitor:

- Target response time
- Request count
- Target `5xx`
- Load-balancer `5xx`
- Healthy target count
- Unhealthy target count
- Connection metrics

### Application Signals

Monitor:

- Request latency
- P50
- P95
- P99
- HTTP `5xx`
- Database latency
- Redis latency
- External API latency
- Worker utilization
- Queue depth

A useful correlation is:

```text
P99 latency ↑
     ↓
Dependency latency ↑
     ↓
Request duration ↑
     ↓
Timeouts ↑
     ↓
504 rate ↑
```

A `504` alert should therefore be correlated with latency metrics rather than monitored in isolation.

## Distributed Tracing

For microservice architectures, distributed tracing can identify the slow hop.

Example:

```text
Request
 ├── CloudFront
 ├── API Gateway/ALB
 ├── Service A       120ms
 │    └── Service B  80ms
 │         └── DB    4.8s
 └── Total           5.1s
```

Without tracing, the application may appear slow while the actual bottleneck is PostgreSQL.

Use consistent trace or request IDs across:

- CloudFront
- ALB
- Nginx
- Django/FastAPI
- gRPC services
- Background workers
- Database instrumentation where available

## Production Troubleshooting Workflow

### Reproduce the Failure

```bash
curl -sv \
  https://cdn.example.com/api/orders/123 \
  -o /dev/null
```

Measure latency:

```bash
curl -sS \
  -o /dev/null \
  -w 'status=%{http_code} total=%{time_total}s\n' \
  https://cdn.example.com/api/orders/123
```

### Test the Origin

```bash
curl -sS \
  -o /dev/null \
  -w 'status=%{http_code} total=%{time_total}s\n' \
  https://origin.example.com/api/orders/123
```

### Inspect CloudFront

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID"
```

### Inspect Origin Configuration

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  --query 'DistributionConfig.Origins.Items[*].{Id:Id,Domain:DomainName,Path:OriginPath}'
```

### Inspect ALB Target Health

```bash
aws elbv2 describe-target-health \
  --target-group-arn "$TARGET_GROUP_ARN"
```

### Inspect Application Logs

For Kubernetes:

```bash
kubectl logs \
  deployment/api \
  -n production \
  --tail=200
```

### Inspect PostgreSQL

```sql
SELECT
    pid,
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

### Check External Dependencies

Inspect:

- Redis latency
- PostgreSQL latency
- Kafka health
- External API latency
- Network connectivity
- Connection pool utilization

### Compare Timeout Budgets

Document the effective timeout chain:

```text
CloudFront
    ↓
ALB
    ↓
Nginx
    ↓
Application
    ↓
Database / Redis / External API
```

Find which timeout expires first.

### Check Recent Deployments

Correlate:

- Application releases
- Database migrations
- Infrastructure changes
- CloudFront changes
- Scaling events
- Dependency incidents

### Verify Recovery

Repeat the public request:

```bash
curl -fsS \
  -o /dev/null \
  -w 'status=%{http_code} total=%{time_total}s\n' \
  https://cdn.example.com/api/orders/123
```

Then verify that:

- P95/P99 latency has recovered.
- `504` rate has returned to baseline.
- Backend capacity is healthy.
- Database and dependency latency are normal.
- No retry storm is occurring.

## Common Production Pitfalls

### Increasing CloudFront Timeout Without Fixing the Root Cause

If PostgreSQL takes `45s`, increasing CloudFront's timeout does not make PostgreSQL faster.

**Avoid it:** identify the slow dependency and optimize or bound it.

### Using Unlimited Dependency Timeouts

An HTTP client or database operation without a meaningful timeout can occupy workers indefinitely.

**Avoid it:** configure explicit deadlines for every external dependency.

### Making Every Timeout Identical

Using `30s` everywhere does not create a coherent timeout strategy.

**Avoid it:** define a hierarchical timeout budget.

### Retrying Slow Requests

A retry after a `25s` timeout can double the work performed by the system.

**Avoid it:** use bounded retries and ensure the total retry budget fits within the request deadline.

### Increasing Worker Count Indiscriminately

More workers can increase database connections and downstream pressure.

**Avoid it:** identify whether the bottleneck is CPU, I/O, database capacity, or dependency latency.

### Ignoring Queue Depth

A growing Celery or Kafka workload can indicate that asynchronous work is falling behind and indirectly affecting synchronous requests.

**Avoid it:** monitor queue depth and processing latency.

### Treating a Cache Miss as an Incident

A cache miss is expected behavior.

The problem is when the origin cannot serve the request within the latency budget.

**Avoid it:** compare cache-hit and cache-miss behavior.

### Ignoring Database Locks

A query can be slow because it is waiting on another transaction rather than because the query itself is computationally expensive.

**Avoid it:** inspect PostgreSQL wait events and lock activity.

### Ignoring Retry Amplification

Retries from CloudFront clients, APIs, mobile applications, SDKs, and microservices can multiply load.

**Avoid it:** coordinate retry policies across service boundaries.

### Running Long Operations Synchronously

Generating large reports or processing files inside an HTTP request makes gateway timeouts much more likely.

**Avoid it:** use asynchronous processing for work that exceeds the synchronous request budget.

## Security Considerations

Do not weaken security controls to diagnose a timeout.

Avoid troubleshooting by blindly:

- Opening security groups to the public internet
- Disabling TLS
- Removing WAF protections
- Exposing private origins
- Disabling authentication
- Removing network restrictions

Instead, verify the exact communication path:

```text
CloudFront
    ↓
Origin
    ↓
Listener
    ↓
Target
```

Each boundary should allow only the traffic required by the architecture.

TLS problems, firewall rules, or network policies should be corrected at the specific failing layer rather than broadly relaxing security.

## Reliability and High Availability

A production CloudFront-backed API should avoid making one slow component capable of consuming all request capacity.

Recommended practices include:

- Multiple application instances.
- Multi-AZ deployment.
- Explicit request deadlines.
- Explicit dependency timeouts.
- Database query timeouts.
- Bounded retries.
- Circuit breakers where appropriate.
- Graceful degradation for optional dependencies.
- Asynchronous processing for long-running operations.
- Capacity headroom.
- Automated deployment rollback.
- Monitoring of P95/P99 latency.
- Distributed tracing for multi-service requests.

A resilient architecture might look like:

```mermaid
flowchart LR
    Client --> CF[CloudFront]
    CF --> ALB

    ALB --> A[App AZ-A]
    ALB --> B[App AZ-B]
    ALB --> C[App AZ-C]

    A --> DB[(PostgreSQL)]
    B --> DB
    C --> DB

    A --> Redis[(Redis)]
    B --> Redis
    C --> Redis
```

The goal is not simply to increase timeout values. The goal is to ensure that slow dependencies cannot consume all available application capacity.

## Cost Considerations

Long-running requests have resource costs even when they eventually fail.

A request that occupies a worker for `60s` consumes significantly more capacity than one completing in `200ms`.

High latency can therefore increase:

- Compute usage
- Database connections
- Load-balancer connections
- Network traffic
- Retry traffic
- Queue backlog
- Operational cost

After resolving a `504` incident, review whether the system is spending excessive resources waiting for slow operations.

## Interview Perspective

A strong answer to:

> "CloudFront is returning 504. How would you troubleshoot it?"

should focus on **timeout boundaries and latency propagation**.

A production-oriented investigation is:

1. Reproduce the `504` through CloudFront.
2. Measure the request duration.
3. Test the origin directly.
4. Determine whether the origin is reachable.
5. Inspect CloudFront origin timeout configuration.
6. Inspect ALB target health and response latency.
7. Inspect Nginx or ingress timeouts.
8. Inspect application P95/P99 latency.
9. Investigate PostgreSQL, Redis, and external API latency.
10. Check worker and connection-pool saturation.
11. Inspect distributed traces for the slow downstream hop.
12. Review retries and retry amplification.
13. Correlate the incident with deployments and traffic changes.
14. Fix the slow or unavailable dependency.
15. Verify that the public endpoint recovers without simply masking the problem through larger timeouts.

The senior-level mental model is:

```text
504
 │
 ├── Was CloudFront waiting for the origin?
 │
 ├── Was the origin reachable?
 │
 ├── Which timeout expired first?
 │
 ├── Was ALB waiting for the target?
 │
 ├── Was Nginx waiting for the application?
 │
 ├── Was the application waiting for:
 │      ├── PostgreSQL?
 │      ├── Redis?
 │      ├── Kafka?
 │      └── External API?
 │
 ├── Were workers or connections exhausted?
 │
 ├── Did retries amplify the load?
 │
 └── Did a deployment or traffic spike introduce the latency?
```

## Key Takeaways

- **A `504` is primarily a timeout-budget problem:** identify which component was waiting, which upstream it was waiting for, and which timeout expired first.
- **Trace latency across the entire request path:** CloudFront, ALB, Nginx, Django/FastAPI, PostgreSQL, Redis, and external services can all contribute to the final timeout.
- **Use bounded timeouts and deadlines at every service boundary:** never rely on an outer gateway timeout to control slow database, Redis, HTTP, or gRPC operations.
- **Do not solve latency problems by blindly increasing timeouts:** optimize the bottleneck, control retries, protect worker capacity, and move long-running work to asynchronous processing.
- **Correlate `504` rates with P95/P99 latency and dependency telemetry:** the first slow component is usually more valuable diagnostically than the final component that reports the timeout.