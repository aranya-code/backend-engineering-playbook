# 09- Origin Overload

## Overview

CloudFront origin overload occurs when the origin receives more traffic, connections, requests, or expensive operations than it can safely process.

In a well-designed CloudFront architecture, the edge layer absorbs a significant portion of repeated cacheable traffic:

```text
Clients
   │
   ▼
CloudFront
   │
   ├── Cache HIT ───────────────► Client
   │
   └── Cache MISS
          │
          ▼
     Origin / ALB
          │
          ▼
   Nginx / Application
          │
          ├── Redis
          └── PostgreSQL
```

When too many requests bypass the cache, the origin becomes the bottleneck:

```text
Low cache reuse
      ↓
More CloudFront → origin requests
      ↓
Higher application concurrency
      ↓
Higher CPU / memory / connections
      ↓
Database and downstream pressure
      ↓
Higher latency
      ↓
Timeouts / 5xx responses
      ↓
Retries
      ↓
Even more origin load
```

Origin overload is therefore usually a **system-level capacity problem**, not simply a CloudFront problem.

The correct operational response is to determine why traffic is reaching the origin, whether that traffic should be reaching it, and whether the origin has enough capacity to handle the expected miss rate.

## What Origin Overload Means

An origin is overloaded when incoming work exceeds its sustainable processing capacity.

For a backend system, capacity can be constrained by:

- CPU
- Memory
- Worker processes
- Worker threads
- Database connections
- Database CPU
- Redis connections
- Network bandwidth
- Connection limits
- File descriptors
- External API rate limits
- Load balancer capacity
- Application-level locks
- Slow queries
- Expensive serialization
- Garbage collection
- Downstream service latency

For example:

```text
CloudFront
    │
    │ 50,000 req/s
    ▼
ALB
    │
    │ 50,000 req/s
    ▼
Django
    │
    │ expensive queries
    ▼
PostgreSQL
```

If the application can sustainably process only 10,000 requests per second, increasing application instances alone may not solve the problem if PostgreSQL or another downstream dependency is already saturated.

## Why CloudFront Normally Protects the Origin

CloudFront can terminate viewer connections at the edge and serve cached objects without contacting the origin.

Suppose:

```text
Viewer requests = 100,000 req/s
Cache hit ratio = 95%
```

Approximately:

```text
Origin requests ≈ 5,000 req/s
```

If the hit ratio drops to 50%:

```text
Origin requests ≈ 50,000 req/s
```

The origin has now received roughly ten times as many requests.

This illustrates why cache configuration and origin capacity must be designed together.

## Origin Overload Symptoms

Common symptoms include:

| Symptom | Likely implication |
|---|---|
| Origin request count increases sharply | More traffic is bypassing cache |
| Origin CPU reaches saturation | Application capacity is constrained |
| Application latency increases | Requests are waiting for compute or dependencies |
| Database CPU increases | Application workload is propagating downstream |
| Database connections are exhausted | Concurrency exceeds DB capacity |
| ALB target response time increases | Targets are struggling to process requests |
| CloudFront 502/503/504 responses increase | Origin is failing, unavailable, or timing out |
| Queue depth increases | Work is arriving faster than it can be processed |
| Redis latency increases | Cache or session dependency is under pressure |
| Connection errors increase | Network or resource limits may be exhausted |

The most important diagnostic question is:

> Did origin load increase because traffic increased, because cache efficiency decreased, or because the origin became slower?

These scenarios require different fixes.

## Distinguish Traffic Growth from Cache Failure

Consider two situations.

### Scenario A: Traffic Growth

```text
Requests:
1M → 5M

Cache hit ratio:
95% → 95%

Origin requests:
50k → 250k
```

The cache is functioning normally. The system needs additional origin capacity or workload optimization.

### Scenario B: Cache Regression

```text
Requests:
1M → 1M

Cache hit ratio:
95% → 60%

Origin requests:
50k → 400k
```

Traffic did not increase, but origin load increased dramatically.

This points toward:

- Cache policy changes
- Query-string variation
- Cookie variation
- Header variation
- TTL changes
- Cache-control changes
- Invalidations
- URL changes
- New uncached workloads

## Identify the Origin Path

Before changing application capacity, establish the request path:

```mermaid
flowchart TD
    A[Client Request] --> B[CloudFront]
    B -->|Cache HIT| C[Edge Response]
    B -->|Cache MISS| D[Origin]
    D --> E[ALB]
    E --> F[Nginx]
    F --> G[Django / FastAPI]
    G --> H[Redis]
    G --> I[PostgreSQL]
    G --> J[External Services]
```

Every additional layer can become a bottleneck.

For example:

```text
CloudFront
    ↓
ALB
    ↓
Django
    ↓
PostgreSQL
```

If PostgreSQL is saturated, adding more Django workers can actually make the situation worse by increasing concurrent database queries.

## Establish a Baseline

Before making changes, collect a baseline.

At minimum:

- CloudFront request count
- Cache hit ratio
- Origin request count
- CloudFront 4xx/5xx rates
- Origin response latency
- ALB target response time
- Application CPU
- Application memory
- Application worker utilization
- Database CPU
- Database connections
- Database latency
- Redis latency
- Network utilization

Capture the same metrics before and after remediation.

A useful baseline might look like:

```text
Viewer requests       120,000 req/s
Cache hit ratio             92%
Origin requests          9,600 req/s

Application CPU             78%
DB CPU                      82%
DB connections            1,100

Origin p95 latency         420 ms
CloudFront 5xx              0.4%
```

The objective is to understand the entire dependency chain rather than focusing on a single metric.

## Inspect CloudFront Configuration

Retrieve the distribution:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID"
```

Retrieve the distribution configuration:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID"
```

Review:

- Cache behaviors
- Cache policies
- Origin request policies
- Origin configuration
- Path patterns
- Allowed methods
- Query-string behavior
- Cookie behavior
- Header behavior
- TTL configuration
- Compression
- Origin groups
- Failover configuration

A recent CloudFront configuration change should be treated as a high-priority suspect when origin traffic increases without corresponding viewer traffic growth.

## Inspect Cache Behavior

A common mistake is assuming that all CloudFront traffic uses the same caching behavior.

A distribution can contain multiple behaviors:

```text
/static/*      → Static asset behavior
/images/*      → Image behavior
/api/public/*  → Public API behavior
/api/*         → Dynamic API behavior
```

These may have completely different:

- Cache policies
- TTLs
- Allowed methods
- Origin request policies
- Header forwarding
- Cookie forwarding

Therefore, identify the affected path before changing global configuration.

## Cache Misses as Origin Load

A cache miss is not necessarily problematic.

A miss becomes operationally important when the origin cannot safely handle the resulting request volume.

For example:

```text
1,000,000 viewer requests
       │
       ├── 990,000 HIT
       └──  10,000 MISS
```

may be perfectly healthy.

But:

```text
1,000,000 viewer requests
       │
       ├── 400,000 HIT
       └── 600,000 MISS
```

can create severe origin pressure if each request triggers:

```text
Django
  ↓
PostgreSQL
  ↓
External API
```

The cost of a miss depends on what happens at the origin.

## Expensive Origin Requests

Not all requests have equal cost.

Consider:

```text
GET /static/app.js
```

versus:

```text
GET /api/recommendations
```

The first may require only a static object read.

The second might perform:

```text
Authentication
    ↓
Redis lookup
    ↓
PostgreSQL query
    ↓
Recommendation service
    ↓
JSON serialization
```

When diagnosing overload, classify origin requests by computational cost.

A useful model is:

```text
Origin Cost
=
Request Rate
×
Average Work per Request
```

Reducing either term can improve system capacity.

## Query String Cache Fragmentation

Query strings can create many cache variants.

For example:

```text
/products?page=1
/products?page=2
/products?page=3
```

may legitimately require separate cache entries.

But:

```text
/products?utm_source=email
/products?utm_source=google
/products?utm_source=linkedin
```

may all represent the same resource.

If unnecessary parameters participate in the cache key, cache reuse decreases and origin traffic increases.

The correct solution is to identify which parameters actually affect the response.

## Cookie-Induced Origin Load

Cookies are another common source of cache fragmentation.

For example:

```http
Cookie: sessionid=abc123
```

If the cache behavior varies on the session cookie, users can effectively receive separate cache entries.

This can be correct for personalized content but is usually harmful for public content.

For public APIs and assets, avoid unnecessary cookie variation.

## Header-Induced Cache Fragmentation

Headers can also create cache variants.

Potential examples include:

```text
Accept-Language
User-Agent
Authorization
X-Device-Type
X-Experiment
```

A header should participate in the cache key only when it changes the response representation.

Otherwise:

```text
Same resource
+
different header
=
different cache key
=
lower cache reuse
```

## TTL-Related Origin Spikes

Short TTLs cause objects to become stale more frequently.

For example:

```text
TTL = 30 seconds
```

A heavily requested object can generate frequent origin fetches.

For immutable assets:

```text
/app.8a7f21.js
```

a much longer cache lifetime is usually more appropriate.

For dynamic public APIs:

```text
Cache-Control: public, max-age=60
```

may be reasonable if one minute of staleness is acceptable.

TTL decisions must be driven by data freshness requirements.

## Deployment-Related Origin Spikes

A common operational pattern is:

```text
Deployment
    ↓
Invalidate /*
    ↓
Cache becomes cold
    ↓
Traffic generates misses
    ↓
Origin receives burst
    ↓
Application/database saturation
```

This can produce a large origin load spike immediately after deployment.

Prefer immutable, versioned assets:

```text
app.a81f2.js
app.b91c3.js
```

instead of repeatedly invalidating the entire cache.

## Cache Stampede

A cache stampede occurs when many requests simultaneously require an object that is no longer available in cache.

Conceptually:

```text
                 ┌── Request 1 ──┐
                 ├── Request 2 ──┤
CloudFront MISS ─┼── Request 3 ──┼── Origin
                 ├── Request 4 ──┤
                 └── Request N ──┘
```

If every request causes an expensive origin computation, the origin can be overwhelmed.

The risk is higher when:

- TTLs are short
- Objects are expensive to generate
- Traffic is highly concentrated
- Many objects expire simultaneously
- The origin has limited capacity

Mitigation strategies include:

- Appropriate TTLs
- Request coalescing where supported by the architecture
- Application-side caching
- Redis
- Precomputation
- Background refresh
- Staggered expiration
- Versioned content
- Capacity planning

## Application-Level Caching

CloudFront should not necessarily be the only cache.

A backend architecture may use:

```text
CloudFront
    ↓
Django / FastAPI
    ↓
Redis
    ↓
PostgreSQL
```

CloudFront protects the origin from repeated external requests.

Redis can protect PostgreSQL from repeated application-level computations.

For example:

```text
CloudFront MISS
      ↓
Django
      ↓
Redis HIT
      ↓
Response
```

This can still avoid expensive database work even when CloudFront cannot serve the request.

## Database Protection

When origin overload reaches PostgreSQL, database protection becomes a priority.

Monitor:

- CPU
- Connections
- Query latency
- Lock waits
- Slow queries
- Transactions
- Read/write throughput
- Connection pool utilization

A common failure mode is:

```text
CloudFront miss rate ↑
        ↓
Django concurrency ↑
        ↓
DB connections ↑
        ↓
DB latency ↑
        ↓
Django requests remain active longer
        ↓
More concurrent requests
        ↓
DB saturation
```

This is a positive feedback loop.

## Worker Saturation

For Django or FastAPI deployments, determine whether application workers are saturated.

For example:

```text
Incoming requests
       ↓
Gunicorn/Uvicorn
       ↓
Workers busy
       ↓
Requests queue
       ↓
Latency increases
```

Increasing worker count can help when CPU or concurrency capacity is genuinely available.

It can hurt when the bottleneck is PostgreSQL or another dependency.

The correct question is:

> What resource is limiting throughput?

## Nginx and Connection Management

If Nginx sits behind an ALB and in front of the application:

```text
CloudFront
    ↓
ALB
    ↓
Nginx
    ↓
Gunicorn/Uvicorn
```

review:

- Keep-alive configuration
- Connection limits
- Upstream connection behavior
- Request buffering
- Timeouts
- Worker limits

Poor connection management can cause unnecessary pressure even when application compute capacity is sufficient.

## Load Balancer Capacity

For an ALB-based origin, inspect:

- Target response time
- Request count
- Target health
- HTTP 5xx
- HTTP 4xx
- Connection behavior
- Target utilization

A healthy ALB does not guarantee healthy targets.

The important path is:

```text
CloudFront
    ↓
ALB
    ↓
Target
    ↓
Application
    ↓
Database
```

Trace the bottleneck all the way down.

## Auto Scaling

Origin auto scaling can absorb legitimate increases in traffic.

For example:

```text
Origin load ↑
     ↓
Target CPU ↑
     ↓
Auto Scaling
     ↓
More application instances
     ↓
Additional capacity
```

However, scaling should not be used to compensate for a broken cache policy indefinitely.

If a configuration change causes a 95% hit ratio to fall to 30%, the first priority should be understanding the cache regression.

## Scaling Does Not Fix Every Bottleneck

Consider:

```text
4 Django instances
     ↓
PostgreSQL
```

If PostgreSQL is already saturated, scaling to:

```text
40 Django instances
     ↓
PostgreSQL
```

may increase database contention rather than improve throughput.

A better approach may involve:

- Query optimization
- Redis caching
- Read replicas
- Connection pooling
- Reducing request fan-out
- Background processing
- Better cacheability
- Rate limiting

## Origin Shield

CloudFront Origin Shield can provide an additional caching layer between CloudFront edge locations and the origin.

Conceptually:

```text
Multiple Edge Locations
          │
          ▼
   Origin Shield Region
          │
          ▼
        Origin
```

This can reduce the number of requests reaching the origin, particularly when multiple edge locations request the same objects.

Origin Shield is useful when:

- Origin request volume is significant
- Traffic is distributed globally
- Cache misses from multiple edge locations converge on the same objects
- Origin load needs additional protection

It is not a replacement for correct cache-key design or appropriate origin capacity.

## Origin Failover

For critical workloads, CloudFront can use origin failover with appropriate origin group configuration.

Conceptually:

```text
CloudFront
    │
    ▼
Primary Origin
    │
    ├── Healthy → Response
    │
    └── Failure
          ↓
     Secondary Origin
```

Failover must be designed around actual failure semantics.

A secondary origin does not automatically solve:

- Database corruption
- Shared dependency failure
- Incorrect application state
- Broken deployment artifacts
- Invalid cache behavior

The backup path must be independently capable of serving the workload.

## Origin Protection Strategies

A production architecture may combine multiple controls:

| Layer | Protection mechanism |
|---|---|
| CloudFront | Caching |
| CloudFront | Origin Shield |
| AWS WAF | Rate limiting / filtering |
| ALB | Load balancing |
| Auto Scaling | Compute scaling |
| Nginx | Connection and request controls |
| Application | Redis/application caching |
| Database | Connection limits and query optimization |
| Async processing | Celery/Kafka where appropriate |

The objective is to prevent a traffic spike from becoming a dependency-wide failure.

## Rate Limiting

Caching is not the only way to reduce origin pressure.

For dynamic APIs, rate limiting may be necessary.

For example:

```text
Client
  ↓
CloudFront
  ↓
AWS WAF
  ↓
ALB
  ↓
Application
```

Rate limiting is particularly useful for:

- Abusive clients
- Bots
- Accidental traffic loops
- Expensive API endpoints
- Traffic bursts

Rate limiting should be designed carefully so legitimate traffic is not blocked.

## Monitoring Origin Overload

Monitor the system as a chain rather than as isolated services.

Useful signals include:

```text
CloudFront
├── Request count
├── Cache hit ratio
├── Origin request count
└── 5xx errors

ALB
├── Request count
├── Target response time
├── Target health
└── 5xx errors

Application
├── CPU
├── Memory
├── Worker utilization
├── Request latency
└── Error rate

Redis
├── CPU
├── Memory
├── Connections
└── Latency

PostgreSQL
├── CPU
├── Connections
├── Query latency
├── Locks
└── I/O
```

A strong incident dashboard should make the dependency chain visible.

## Useful CloudFront CLI Commands

Retrieve distribution details:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID"
```

Retrieve configuration:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID"
```

List distributions:

```bash
aws cloudfront list-distributions
```

List invalidations:

```bash
aws cloudfront list-invalidations \
  --distribution-id "$DISTRIBUTION_ID"
```

Retrieve a specific invalidation:

```bash
aws cloudfront get-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --id "$INVALIDATION_ID"
```

These commands help establish configuration and deployment context during an incident.

## Operational Troubleshooting Workflow

### Confirm That the Origin Is Actually Overloaded

Do not infer overload from CloudFront errors alone.

Check:

- Application CPU
- Application latency
- Worker utilization
- ALB target response time
- Database CPU
- Database connections
- Redis latency
- Network utilization

### Determine Whether Traffic Increased

Compare:

```text
Current viewer requests
vs.
Historical viewer requests
```

Then compare:

```text
Current origin requests
vs.
Historical origin requests
```

This separates traffic growth from cache degradation.

### Compare Cache Hit Ratio

For example:

```text
Viewer traffic       +10%
Cache hit ratio      95% → 65%
Origin traffic       +700%
```

This strongly suggests a cache behavior regression rather than ordinary traffic growth.

### Identify Affected Paths

Determine which paths are generating the additional origin requests.

Example:

```text
/static/*       unchanged
/images/*       unchanged
/api/catalog    increased 8x
/api/profile    unchanged
```

Focus the investigation on `/api/catalog`.

### Inspect Cache Policy

Review:

- Query strings
- Cookies
- Headers
- TTLs
- Cacheability
- Path behavior

### Inspect Origin Responses

Check:

```bash
curl -sS -D - \
  -o /dev/null \
  https://cdn.example.com/api/catalog
```

Inspect:

```text
Cache-Control
ETag
Age
X-Cache
```

### Inspect Application and Database Metrics

If the cache configuration is correct, determine whether the origin itself needs more capacity or more efficient processing.

### Mitigate First When Necessary

During a live incident, prioritize reducing load.

Possible mitigations include:

- Restore a known-good cache policy
- Increase application capacity
- Enable or increase application-level caching
- Rate-limit abusive traffic
- Temporarily disable expensive endpoints
- Reduce unnecessary downstream calls
- Increase database capacity where appropriate

Do not make broad configuration changes without understanding their blast radius.

### Validate Recovery

A successful mitigation should produce measurable improvement:

```text
Origin requests       ↓
Application CPU       ↓
Database CPU          ↓
Latency               ↓
5xx errors            ↓
Cache hit ratio       ↑
```

## Production Pitfalls

### Scaling the Origin Before Investigating Cache Regression

If a cache policy is broken, scaling application instances may only hide the problem temporarily.

**Better approach:** determine why origin traffic increased first.

### Increasing Workers Without Checking Database Capacity

More workers can generate more concurrent database queries.

**Better approach:** identify the limiting resource before scaling concurrency.

### Invalidating Everything During an Incident

A broad invalidation can make an origin overload worse.

**Better approach:** use targeted invalidation or restore correct cache behavior.

### Treating CloudFront as a Complete Origin Shield

CloudFront only protects the origin to the extent that content is cacheable and reusable.

**Better approach:** combine CloudFront with application caching, rate limiting, and capacity controls.

### Ignoring Cache-Key Fragmentation

A resource may appear cacheable while thousands of request variants prevent reuse.

**Better approach:** inspect query strings, cookies, and headers.

### Ignoring Downstream Dependencies

An origin may have healthy CPU while PostgreSQL is completely saturated.

**Better approach:** trace requests through every dependency.

### Relying Only on Average Latency

Average latency can remain acceptable while a subset of requests experiences severe queuing.

**Better approach:** monitor p95/p99 latency and queueing behavior.

### Treating Auto Scaling as the Primary Fix

Auto scaling handles capacity growth but does not correct inefficient architecture.

**Better approach:** combine scaling with caching and workload optimization.

## Security Considerations

Origin overload can also be caused by malicious or abusive traffic.

Potential sources include:

- Bots
- Scrapers
- Application-layer floods
- Repeated expensive API requests
- Credential attacks
- Cache-bypass requests

A typical protection architecture is:

```text
Internet
   ↓
CloudFront
   ↓
AWS WAF
   ↓
ALB
   ↓
Application
```

Security controls should protect expensive endpoints before requests reach application and database layers.

Do not rely exclusively on application-level rate limiting if traffic is large enough to consume origin resources before the application can reject it.

## Reliability Considerations

The goal is not simply to maximize origin throughput.

A resilient system should:

- Keep cacheable traffic at the edge
- Protect the origin from bursts
- Maintain application headroom
- Protect database capacity
- Use timeouts
- Use circuit breakers where appropriate
- Apply rate limits to expensive workloads
- Use asynchronous processing for suitable long-running operations
- Maintain independent failure paths where required

For asynchronous work:

```text
CloudFront
    ↓
API
    ↓
Kafka / Celery
    ↓
Background Workers
```

This prevents expensive long-running work from unnecessarily occupying synchronous request workers.

## Cost Considerations

Origin overload can increase:

- EC2 or container compute
- Load balancer usage
- Database capacity
- Redis usage
- External API consumption
- Network transfer
- Operational overhead

Improving cache reuse can reduce these costs.

However, adding caching, Origin Shield, or larger infrastructure should be evaluated against:

- Request volume
- Object size
- Origin cost
- Cacheability
- Freshness requirements
- Expected traffic growth

The cheapest architecture is not necessarily the most reliable architecture.

## Disaster Recovery Considerations

For critical workloads, consider whether the origin itself is a single point of failure.

Possible architecture:

```text
                  CloudFront
                      │
              ┌───────┴───────┐
              │               │
        Primary Origin   Secondary Origin
              │               │
          Region A         Region B
```

Disaster recovery planning should consider:

- Origin failover
- Application deployment parity
- Data replication
- Database recovery
- DNS dependencies
- Secrets
- Certificates
- Infrastructure-as-code
- Cache behavior
- Recovery time objectives
- Recovery point objectives

CloudFront cannot compensate for an origin architecture that cannot recover from regional or dependency-level failure.

## Interview Perspective

A strong answer to:

> "CloudFront is causing too many requests to reach your origin and the origin is overloaded. What would you do?"

should cover:

1. Establish viewer traffic and origin traffic baselines.
2. Compare cache hit ratio before and after the incident.
3. Identify affected cache behaviors and paths.
4. Inspect cache policies.
5. Check query-string, cookie, and header variation.
6. Check TTL and origin cache-control behavior.
7. Review recent invalidations and deployments.
8. Determine whether traffic growth is legitimate or abusive.
9. Inspect application, ALB, Redis, and database capacity.
10. Identify the actual bottleneck.
11. Apply the least disruptive mitigation.
12. Restore or improve cache efficiency where appropriate.
13. Scale the constrained dependency if additional capacity is genuinely required.
14. Validate recovery using origin load, latency, errors, and dependency metrics.

The senior-level insight is:

> **Origin overload should be analyzed as a request amplification problem across the entire dependency chain, not simply as an insufficient number of application servers.**

## Key Takeaways

- **Origin overload is usually a system-level capacity problem:** trace traffic from CloudFront through the ALB, application, Redis, database, and external dependencies.
- **Separate traffic growth from cache regression:** a sudden increase in origin requests without equivalent viewer traffic growth often indicates reduced cache effectiveness.
- **Fix the actual bottleneck before scaling:** adding application workers can worsen database contention when the database is already saturated.
- **Protect the origin at multiple layers:** combine CloudFront caching, appropriate cache policies, Origin Shield where useful, WAF controls, application caching, rate limiting, and capacity planning.
- **Validate every mitigation with end-to-end metrics:** origin request volume, cache hit ratio, latency, CPU, database pressure, and 5xx errors should improve together.