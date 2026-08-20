# 06- Cost Optimization

## Overview

CloudFront cost optimization is the process of reducing total content-delivery and origin infrastructure cost without degrading required performance, availability, security, or freshness guarantees.

CloudFront cost is not determined by one setting. The effective cost of a production architecture depends on:

```text
Viewer Requests
+
Data Transfer
+
Cache Efficiency
+
Origin Requests
+
Invalidations
+
Logging
+
Edge Compute
+
Origin Infrastructure
```

A useful optimization model is:

```text
Total Delivery Cost
=
CloudFront Cost
+
Origin Compute Cost
+
Origin Database/Cache Cost
+
Network Cost
+
Observability Cost
```

Optimizing only the CloudFront invoice can therefore produce the wrong engineering decision. For example, reducing CloudFront usage by bypassing the CDN may increase:

- Application compute.
- Load balancer traffic.
- Database load.
- Cross-region traffic.
- Origin bandwidth.
- Autoscaling requirements.

The goal is not the lowest CloudFront bill in isolation.

> The goal is the lowest sustainable total system cost while maintaining the required SLOs and security guarantees.

---

## CloudFront Cost Drivers

The major cost dimensions should be evaluated separately.

| Cost driver | What increases cost | Primary optimization |
|---|---|---|
| Data transfer | Large response volumes | Compression, caching, payload optimization |
| HTTP/HTTPS requests | High request volume | Cache effectively, reduce unnecessary requests |
| Origin requests | Low cache efficiency | Improve cacheability and cache-key design |
| Invalidations | Frequent large invalidation operations | Version assets and invalidate selectively |
| Real-time logging | High-volume diagnostic traffic | Enable selectively and control destinations |
| Edge compute | High invocation volume or execution | Keep edge logic minimal |
| Origin infrastructure | High cache-miss traffic | Increase cache efficiency and optimize origin |
| Data processing / supporting services | Excessive auxiliary processing | Remove unnecessary processing layers |

The exact pricing depends on AWS region, CloudFront pricing model, traffic characteristics, and enabled features. Always validate current pricing before making a production cost decision.

---

## Cost Architecture

A typical backend architecture might look like:

```mermaid
flowchart LR
    Client[Viewer] --> CF[CloudFront]
    CF --> WAF[AWS WAF]
    CF --> ALB[Application Load Balancer]
    ALB --> App[Django / FastAPI]
    App --> Redis[(Redis)]
    App --> DB[(PostgreSQL)]

    CF -. "Cache HIT" .-> Client
    CF -. "Cache MISS" .-> ALB
```

The most important cost relationship is:

```text
Higher useful cache hit ratio
            ↓
Fewer origin requests
            ↓
Less application work
            ↓
Less database/cache pressure
            ↓
Lower total infrastructure cost
```

Caching therefore has both performance and cost implications.

---

## Cache Hit Ratio and Cost

Suppose a system receives:

```text
10 million requests/month
```

with:

```text
Cache Hit Ratio = 80%
```

Approximately:

```text
2 million requests
```

may still reach the origin, depending on workload and request behavior.

If cache efficiency improves to:

```text
95%
```

the origin-facing workload can potentially fall to approximately:

```text
500,000 requests
```

The reduction affects more than CloudFront:

```text
CloudFront
   ↓
Origin Requests ↓
   ↓
Application CPU ↓
   ↓
Database Queries ↓
   ↓
Infrastructure Cost ↓
```

The actual savings depend on response sizes, cacheability, origin behavior, and the application's dependency graph.

---

## Cost Efficiency Through Cache Design

The cheapest origin request is the origin request that never happens.

Prioritize:

- Cacheable public responses.
- Long-lived immutable assets.
- Small cache keys.
- Appropriate TTLs.
- Compression.
- Versioned assets.
- Efficient invalidation.

Avoid:

- Caching personalized responses incorrectly.
- Including irrelevant query parameters.
- Including unnecessary cookies.
- Including high-cardinality headers.
- Using very short TTLs without a freshness requirement.

---

## Cache-Key Fragmentation

Suppose the application receives:

```text
/products/123?utm_source=google
/products/123?utm_source=email
/products/123?utm_source=linkedin
```

If tracking parameters participate unnecessarily in the cache key, CloudFront can maintain multiple cache entries for effectively identical content.

This causes:

```text
More cache objects
       ↓
More misses
       ↓
More origin requests
       ↓
Higher cost
```

The cache key should contain only attributes that can change the response.

---

## Query String Optimization

Query parameters should be classified into:

### Response-defining parameters

These change the response.

Example:

```text
/products?category=laptops
/products?category=phones
```

They may need to participate in cache identity.

### Tracking parameters

These usually do not change the response.

Examples:

```text
utm_source
utm_medium
utm_campaign
```

These should generally not fragment the cache unnecessarily.

### Operational parameters

Some applications use parameters for debugging, experimentation, or routing.

These require explicit analysis before excluding them from the cache key.

The key principle is:

> Do not pay the origin cost for request differences that do not produce response differences.

---

## TTL Optimization

TTL is a direct tradeoff between:

```text
Freshness
vs
Cache reuse
```

Longer TTLs generally provide:

- More cache reuse.
- Fewer origin requests.
- Lower origin load.
- Better latency.
- Potentially lower total infrastructure cost.

But longer TTLs can also produce stale content.

A practical strategy is:

| Content | Typical strategy |
|---|---|
| Content-hashed JS/CSS | Very long TTL |
| Versioned images | Very long TTL |
| Public documentation | Long TTL |
| Public catalog API | Short/medium TTL |
| Frequently changing public data | Short TTL |
| Personalized API | Avoid shared caching |
| Authentication endpoints | Generally bypass shared cache |

These are architectural patterns rather than universal TTL values.

---

## Immutable Asset Strategy

Versioned assets are one of the strongest cost optimization techniques.

Instead of:

```text
/static/app.js
```

use:

```text
/static/app.a82f31.js
```

When the application changes:

```text
/static/app.b73d19.js
```

is generated.

The old object can remain cached while the new object naturally obtains a new cache key.

This reduces the need for:

```text
Invalidate /*
```

after every deployment.

---

## Why Versioning Reduces Cost

Consider a deployment pipeline:

```text
Build
  ↓
Upload static files
  ↓
Invalidate /*
  ↓
CloudFront re-fetches assets
  ↓
Origin receives additional requests
```

A versioned deployment can instead be:

```text
Build
  ↓
Generate content-hashed assets
  ↓
Upload new assets
  ↓
Deploy application references
```

Only new asset URLs need to be retrieved.

This reduces unnecessary cache churn.

---

## Invalidations

Invalidations are useful when content must be removed or refreshed before its normal TTL expires.

Examples include:

```text
/images/homepage.jpg
/config/public.json
/index.html
```

Use invalidation deliberately.

Avoid making this a default deployment mechanism:

```text
Every deployment
    ↓
Invalidate /*
```

A better strategy is usually:

```text
Immutable assets
    ↓
Long TTL
    ↓
Versioned URLs

Mutable entry documents
    ↓
Shorter TTL or targeted invalidation
```

---

## Avoiding Invalidation Overuse

Frequent invalidations can indicate an architectural problem.

Ask:

- Is the content immutable?
- Can the URL be versioned?
- Is the TTL too long for mutable content?
- Are we invalidating because deployment tooling does not manage versions?
- Are invalidations being used as a cache consistency mechanism?

If every deployment requires broad invalidation, redesign the asset delivery strategy before optimizing individual invalidation operations.

---

## Data Transfer Optimization

Data transfer is an important cost driver.

A system delivering:

```text
1 TB/month
```

has fundamentally different cost characteristics from one delivering:

```text
100 TB/month
```

even if request counts are identical.

Reduce transferred bytes through:

- Compression.
- Image optimization.
- Smaller API payloads.
- Minified JavaScript and CSS.
- Responsive image delivery.
- Removal of unnecessary fields.
- Appropriate media formats.
- Efficient pagination.

---

## Compression and Cost

Compression reduces the number of bytes transferred for compressible content.

For example:

```text
Uncompressed JSON
        ↓
2 MB

Compressed JSON
        ↓
250 KB
```

The exact ratio depends on the content.

For high-volume JSON APIs, compression can reduce both:

```text
Network transfer
+
Delivery cost
```

It can also improve latency.

Do not expect meaningful compression savings from already compressed formats such as:

```text
JPEG
PNG
WebP
AVIF
MP4
ZIP
```

---

## API Payload Optimization

Suppose an API returns:

```json
{
  "id": 123,
  "name": "Laptop",
  "price": 1000,
  "description": "...",
  "audit_history": [],
  "internal_metadata": {},
  "related_products": []
}
```

when the client only needs:

```json
{
  "id": 123,
  "name": "Laptop",
  "price": 1000
}
```

The unnecessary fields increase:

- Serialization cost.
- Transfer size.
- Client parsing cost.
- CloudFront data transfer.
- Application memory usage.

CloudFront cost optimization therefore begins at the API contract.

---

## Static Asset Optimization

For frontend assets:

```text
Source
  ↓
Minification
  ↓
Tree shaking
  ↓
Code splitting
  ↓
Compression
  ↓
Versioned URL
  ↓
CloudFront
```

The CDN cannot compensate for oversized assets.

A 10 MB JavaScript bundle served from cache still requires the viewer to download 10 MB.

---

## Image Cost Optimization

Images can dominate data transfer volume.

Prefer:

- Modern image formats.
- Appropriate dimensions.
- Responsive image sizes.
- Compression.
- Lazy loading.
- Long-lived caching for immutable assets.

For example:

```text
Original
  ↓
4000 × 3000
  ↓
Resize for target display
  ↓
Modern format
  ↓
Compress
  ↓
CloudFront
```

Delivering a 4000×3000 image to a device displaying it at 400×300 is usually wasteful.

---

## Origin Cost Reduction

CloudFront cost optimization should include origin economics.

A cache miss may trigger:

```text
CloudFront
   ↓
ALB
   ↓
Nginx
   ↓
Django
   ↓
Redis
   ↓
PostgreSQL
```

One viewer request can therefore cause work across multiple infrastructure layers.

Increasing cache efficiency can reduce all of them.

---

## Redis and CloudFront

CloudFront and Redis operate at different levels.

```text
CloudFront
→ HTTP response caching at the edge

Redis
→ Application/data caching inside the backend
```

A typical architecture:

```text
Viewer
  ↓
CloudFront
  ↓
Django / FastAPI
  ↓
Redis
  ↓
PostgreSQL
```

A CloudFront cache hit can eliminate the entire backend path.

A CloudFront miss followed by a Redis hit can eliminate the database query.

A CloudFront miss followed by a Redis miss may reach PostgreSQL.

The layered architecture should therefore be intentional.

---

## Origin Shield and Cost

Origin Shield can reduce origin request pressure for workloads where multiple edge locations frequently request the same objects.

Conceptually:

```text
Edge A ─┐
Edge B ─┼──► Origin Shield ───► Origin
Edge C ─┘
```

Potential benefits include:

- Reduced origin request volume.
- Better cache consolidation.
- Reduced origin bandwidth.
- Better resilience to distributed cache misses.

However, Origin Shield is not automatically cheaper for every workload.

Evaluate:

```text
Origin request reduction
+
Origin transfer savings
+
CloudFront feature cost
```

against the actual traffic pattern.

---

## Origin Request Optimization

If the origin is expensive, prioritize:

```text
OriginRequests ↓
```

Investigate:

- Cache policy.
- TTL.
- Query string configuration.
- Cookie configuration.
- Header configuration.
- Cache invalidation patterns.
- Uncacheable response headers.
- Dynamic request patterns.

The biggest savings often come from preventing origin requests rather than making them cheaper.

---

## AWS WAF Cost Considerations

AWS WAF provides important security controls but introduces additional cost considerations.

Do not remove WAF protections solely to reduce cost without understanding the risk.

Instead:

- Remove redundant rules.
- Consolidate equivalent rules.
- Tune managed rule groups.
- Monitor rule effectiveness.
- Use rate-based protections where appropriate.
- Avoid unnecessarily duplicating controls at multiple layers.

Security controls should be optimized for effectiveness, not simply minimized.

---

## Logging Costs

Observability can become a meaningful cost component at high traffic volumes.

CloudFront provides different logging approaches, including:

- Standard access logging.
- Real-time logs.

Real-time logging is useful for operational scenarios requiring near-real-time visibility but can generate significantly more telemetry than is necessary for routine analysis.

A practical strategy is:

```text
Normal operation
→ Standard logging + CloudWatch metrics

Incident investigation
→ Temporarily increase diagnostic detail

High-volume production
→ Sample or selectively route detailed telemetry
```

Do not retain every diagnostic signal forever simply because it exists.

---

## Log Retention

Logging cost includes more than ingestion.

Consider:

```text
Ingestion
+
Storage
+
Query
+
Export
+
Processing
```

Define retention according to operational and compliance requirements.

For example:

```text
Hot operational data
→ Short retention

Historical operational data
→ Longer retention where justified

Compliance data
→ Policy-driven retention
```

Do not use the same retention period for every log category.

---

## CloudWatch Cost Management

CloudWatch monitoring should focus on actionable signals.

High-value CloudFront metrics include:

```text
Requests
BytesDownloaded
BytesUploaded
CacheHitRate
OriginRequests
OriginLatency
4xxErrorRate
5xxErrorRate
```

Avoid creating large numbers of high-cardinality custom metrics without a clear operational purpose.

A dashboard should help answer:

- Is traffic increasing?
- Is cache efficiency degrading?
- Is the origin receiving unexpected traffic?
- Is latency increasing?
- Are errors increasing?
- Did a deployment change behavior?

---

## Cost Monitoring Dashboard

A useful operational dashboard can combine:

```text
Traffic
Cache efficiency
Origin load
Latency
Errors
Estimated cost
```

Example:

| Signal | Why it matters |
|---|---|
| Requests | Traffic volume |
| Bytes downloaded | Transfer volume |
| Cache hit ratio | Delivery efficiency |
| Origin requests | Backend cost pressure |
| Origin latency | Origin performance |
| 4xx | Client/request issues |
| 5xx | Reliability issues |
| Cost trend | Financial impact |

The goal is correlation rather than isolated metric monitoring.

---

## Cost Anomaly Detection

Unexpected CloudFront cost increases should be investigated through traffic and configuration changes.

For example:

```text
CloudFront Cost ↑
        │
        ├── Requests ↑
        │
        ├── Bytes ↑
        │
        ├── CacheHitRate ↓
        │
        ├── Large asset deployment
        │
        └── Unexpected traffic
```

A cost spike is often a symptom rather than the root cause.

---

## Cost Allocation

Use AWS tagging and account/environment separation where appropriate.

Useful dimensions include:

```text
Environment
Application
Team
Business Unit
Cost Center
```

For multi-application CloudFront architectures, ownership should be clear.

A production cost review should answer:

```text
Which distribution?
Which application?
Which environment?
Which traffic pattern?
Which configuration change?
```

---

## Cost Optimization Workflow

Use a repeatable process.

### Establish a Baseline

Capture:

```text
Monthly CloudFront cost
Requests
Data transfer
Cache hit ratio
Origin requests
Origin bandwidth
Logging volume
```

### Identify the Largest Cost Driver

Determine whether the dominant factor is:

```text
Requests
Data transfer
Origin traffic
Logging
Edge compute
```

### Identify the Technical Cause

For example:

```text
Data transfer ↑
    ↓
Large image deployment
```

or:

```text
Origin traffic ↑
    ↓
Cache hit ratio ↓
    ↓
New query parameter included in cache key
```

### Apply the Smallest Effective Change

Examples:

```text
Optimize cache policy
Reduce payload size
Enable compression
Version assets
Reduce unnecessary logs
```

### Measure the Result

Compare:

```text
Before
vs
After
```

for both:

```text
Cost
+
Performance
+
Reliability
```

---

## Cost and Performance Tradeoffs

Cost optimization should never be performed without considering latency.

For example:

```text
Aggressive caching
→ Lower origin cost
→ Better latency
→ Potential staleness

More logging
→ Higher observability cost
→ Better diagnostics

More edge processing
→ Potentially lower origin work
→ Additional execution cost and complexity

Smaller payloads
→ Lower transfer cost
→ Usually better latency
```

A senior engineer evaluates these tradeoffs explicitly.

---

## Cost Optimization Example

Consider a public product API:

```text
20 million requests/month
Average response = 100 KB
Cache hit ratio = 70%
```

The application currently receives a large number of origin requests.

A redesign could introduce:

```text
Cache hit ratio → 95%
Compression
Versioned static assets
Smaller JSON responses
```

The expected system-level result is:

```text
Origin Requests ↓
Origin CPU ↓
Database Load ↓
Bytes Transferred ↓
Viewer Latency ↓
Total Infrastructure Cost ↓
```

The actual financial improvement must be measured against the current AWS pricing and workload.

---

## Cost Optimization for Django and FastAPI

For a Django or FastAPI backend, evaluate the request path:

```text
CloudFront
   ↓
ALB
   ↓
Application
   ↓
Redis
   ↓
PostgreSQL
```

A public cacheable endpoint can potentially eliminate all downstream work.

For example:

```text
GET /api/catalog
```

may be cacheable for a short period if:

- The response is public.
- The response does not depend on the authenticated user.
- The freshness requirement permits caching.
- The cache key correctly represents the response.

An authenticated endpoint such as:

```text
GET /api/me
```

should generally not be treated as a publicly shared CloudFront object.

---

## Kubernetes Cost Considerations

When the origin runs on Kubernetes:

```text
CloudFront cache efficiency ↓
        ↓
Origin requests ↑
        ↓
Pod CPU ↑
        ↓
HPA scales out
        ↓
Compute cost ↑
```

Improving CloudFront cache efficiency can therefore reduce Kubernetes compute requirements.

However, do not scale Kubernetes down purely because cache hit ratio improved.

Verify:

- Peak traffic.
- Cache miss behavior.
- Cache eviction scenarios.
- Deployment behavior.
- Regional traffic.
- Origin failure behavior.

The origin must still handle the required uncached workload.

---

## Cost Optimization and High Availability

Never reduce origin capacity below the safe uncached traffic requirement.

A common mistake is:

```text
Cache hit ratio = 98%
        ↓
Scale origin aggressively down
```

If a cache policy change causes:

```text
Cache hit ratio = 80%
```

the origin may suddenly receive a much larger workload.

Design origin capacity around:

```text
Expected uncached traffic
+
Traffic spikes
+
Cache degradation
+
Operational events
```

CloudFront should reduce origin load, not become a hidden single point of capacity planning.

---

## Cost Optimization and Disaster Recovery

During a regional or origin failure, cached content may continue to provide value depending on cache state and configuration.

Cost planning should therefore consider:

- Origin failover.
- Multi-region architectures.
- Cache behavior during outages.
- Static asset availability.
- Recovery traffic spikes.
- Logging requirements during incidents.

Do not optimize cost by removing redundancy required by the application's recovery objectives.

---

## Security Considerations

Cost optimization must preserve:

- Authentication.
- Authorization.
- WAF protections.
- TLS configuration.
- Signed URLs.
- Signed cookies.
- Private content controls.
- Origin access controls.

Never reduce security controls merely because they appear on a cost report.

For example, disabling a WAF rule solely because it produces operational cost can be dangerous if that rule protects a high-risk endpoint.

---

## Common Cost Optimization Mistakes

### Optimizing the CloudFront Bill Instead of Total Cost

Reducing CloudFront usage can increase origin compute and database costs.

### Ignoring Cache Hit Ratio

A low hit ratio can create unnecessary origin traffic and infrastructure cost.

### Invalidating Everything

Broad invalidation after every deployment creates unnecessary cache churn and operational overhead.

### Caching Unsafe Responses

Incorrect caching of personalized responses can create serious security problems.

### Ignoring Object Size

Large cached objects still generate data transfer.

### Keeping Excessive Logs Forever

Long retention increases storage and query costs.

### Removing Observability

Reducing logging too aggressively can make production incidents much harder to diagnose.

### Scaling the Origin Too Far Down

The origin must survive cache misses, traffic spikes, cache eviction, and configuration mistakes.

### Optimizing Without a Baseline

Without baseline measurements, cost changes cannot be attributed reliably.

### Treating Cache Hit Ratio as the Only KPI

A high cache hit ratio does not guarantee:

- Low latency.
- Correctness.
- Low total cost.
- Good user experience.

---

## Cost Review Checklist

### Traffic

- [ ] Monthly request volume is known
- [ ] Data transfer volume is known
- [ ] Traffic growth is tracked
- [ ] Unexpected traffic spikes are investigated

### Caching

- [ ] Cacheable responses are identified
- [ ] Cache hit ratio is monitored
- [ ] Cache keys are not unnecessarily fragmented
- [ ] TTLs match freshness requirements
- [ ] Immutable assets use versioned URLs
- [ ] Broad invalidations are avoided

### Payloads

- [ ] Large objects are identified
- [ ] Compression is enabled where appropriate
- [ ] Images are optimized
- [ ] API responses contain only required data
- [ ] Static assets are minified

### Origin

- [ ] Origin request volume is monitored
- [ ] Origin compute cost is included in analysis
- [ ] Database cost is included
- [ ] Redis usage is evaluated
- [ ] Origin capacity handles cache-miss scenarios

### Observability

- [ ] Logging volume is reviewed
- [ ] Log retention is appropriate
- [ ] Real-time logs are enabled only when justified
- [ ] CloudWatch metrics are actionable
- [ ] Cost anomalies are investigated

### Security

- [ ] WAF protections remain appropriate
- [ ] Private content remains protected
- [ ] Authentication boundaries are preserved
- [ ] Signed URL/cookie behavior remains correct
- [ ] Origin access controls remain enforced

---

## Interview Traps

### Does a higher cache hit ratio always reduce cost?

Not necessarily.

A higher hit ratio can reduce origin work, but total cost depends on:

- Request volume.
- Data transfer.
- Object sizes.
- Logging.
- Edge features.
- Origin architecture.

### Is CloudFront always cheaper than serving directly from an application?

Not automatically.

The correct comparison is:

```text
CloudFront total cost
+
remaining origin cost
```

versus:

```text
direct-origin total cost
```

for the actual workload.

### Why does reducing payload size matter even when content is cached?

Because cache hits still require transferring the response to the viewer.

Caching removes origin work; it does not eliminate data transfer.

### Why can a cache miss be more expensive than a CloudFront request?

A cache miss can trigger work across:

```text
ALB
Application
Redis
Database
External services
```

The total infrastructure cost of the request can therefore exceed the CDN request cost itself.

### Why are versioned assets useful for cost optimization?

They reduce the need for broad invalidations and allow long TTLs while preserving correctness across deployments.

### Should logging always be minimized to reduce cost?

No.

Logging is an operational capability. Reduce unnecessary or excessive telemetry while retaining enough information to diagnose incidents and satisfy compliance requirements.

## Key Takeaways

- **Optimize total system cost, not the CloudFront invoice alone:** include origin compute, databases, Redis, networking, logging, and observability.
- **Improve useful cache efficiency:** correct cache keys, appropriate TTLs, and immutable versioned assets can reduce both origin workload and infrastructure cost.
- **Reduce bytes before reducing observability or security:** compression, smaller API responses, optimized images, and efficient assets usually provide safer cost savings.
- **Treat cost and performance as coupled:** every optimization should be evaluated against latency, freshness, reliability, security, and capacity requirements.
- **Measure cost changes with operational metrics:** correlate spend with requests, data transfer, cache hit ratio, origin requests, logging volume, and application capacity before and after changes.