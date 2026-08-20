# 05- 503 Service Unavailable Errors

## Overview

A `503 Service Unavailable` response indicates that the request could not currently be served. In a CloudFront architecture, the critical troubleshooting question is **which layer generated the `503`**.

A typical production request path is:

```text
Client
  │
  ▼
CloudFront
  │
  ├── Cache
  ├── AWS WAF
  └── Origin request
          │
          ▼
         ALB
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

A `503` may therefore result from:

- CloudFront being unable to obtain a usable response from the origin.
- An ALB having no healthy targets.
- An ingress or reverse proxy having no usable upstreams.
- An application intentionally returning `503`.
- Application workers being exhausted.
- Database or connection-pool exhaustion.
- Redis or another required dependency being unavailable.
- A deployment temporarily removing all healthy capacity.
- Auto scaling failing to add capacity quickly enough.
- A retry storm overwhelming an already degraded service.
- A custom error configuration changing the externally visible response.

The correct troubleshooting approach is to establish the failure boundary before changing configuration or restarting infrastructure.

## HTTP 503 Semantics

HTTP `503 Service Unavailable` generally indicates temporary inability to serve a request.

It should be distinguished from other common failures:

| Status | Typical investigation |
|---|---|
| `400` | Invalid client request |
| `401` | Authentication |
| `403` | Authorization, WAF, or access policy |
| `404` | Resource or routing |
| `500` | Application/server failure |
| `502` | Gateway or upstream communication |
| `503` | Service availability or capacity |
| `504` | Upstream timeout |

The status code alone does not identify the responsible component. An application, ALB, reverse proxy, or CloudFront can each participate in producing the externally observed response.

## Establish the Failure Boundary

Start by reproducing the exact public request:

```bash
curl -sS -D - \
  -o /dev/null \
  https://cdn.example.com/api/health
```

Record:

- HTTP status
- `X-Cache`
- `Via`
- `Age`
- Response headers
- Request URL
- HTTP method
- Timestamp
- Whether the problem is intermittent or persistent
- Whether the problem affects all paths or specific behaviors
- Whether the problem is regional or global

A response containing:

```text
HTTP/2 503
X-Cache: Error from cloudfront
```

is useful evidence that CloudFront generated the response, but it should not be treated as the complete root-cause diagnosis.

The next step is to compare the CloudFront endpoint with the origin.

## CloudFront Versus Origin

Test the CloudFront endpoint:

```bash
curl -sv \
  https://cdn.example.com/api/health
```

Then test the origin:

```bash
curl -sv \
  https://origin.example.com/api/health
```

If the origin requires a specific `Host` header:

```bash
curl -sv \
  https://origin.example.com/api/health \
  -H 'Host: api.example.com'
```

Interpret the comparison:

| CloudFront | Origin | Investigation direction |
|---|---|---|
| `503` | `200` | CloudFront configuration, edge behavior, or request path |
| `503` | `503` | Origin or application availability |
| `503` | Timeout | Origin performance or networking |
| `503` | Connection failure | Origin networking or infrastructure |
| `200` | `200` | Investigate request-specific CloudFront behavior |

A direct origin test is especially valuable because it removes CloudFront from the diagnostic path.

## Request Lifecycle

A useful troubleshooting model is:

```mermaid
sequenceDiagram
    participant C as Client
    participant CF as CloudFront
    participant ALB as Load Balancer
    participant APP as Application
    participant DB as PostgreSQL

    C->>CF: HTTPS request
    CF->>ALB: Origin request
    ALB->>APP: Forward request
    APP->>DB: Query
    DB-->>APP: Response
    APP-->>ALB: HTTP response
    ALB-->>CF: HTTP response
    CF-->>C: HTTP response
```

During a `503` incident, determine where this sequence stops producing a usable response.

For example:

```text
Client
  ↓
CloudFront
  ↓
ALB
  ↓
No healthy targets
  ↓
503
```

or:

```text
Client
  ↓
CloudFront
  ↓
ALB
  ↓
Django
  ↓
PostgreSQL connection pool exhausted
  ↓
503
```

These are different incidents even though the client sees the same status code.

## Inspect the CloudFront Distribution

Inspect the distribution:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID"
```

Extract important distribution state:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.{Status:Status,Enabled:DistributionConfig.Enabled,DomainName:DomainName}'
```

Inspect configured origins:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  --query 'DistributionConfig.Origins.Items[*].{Id:Id,Domain:DomainName,Path:OriginPath}'
```

Review:

- Distribution status
- Enabled state
- Origin domain
- Origin path
- Origin groups
- Cache behaviors
- Origin request policies
- Viewer request policies
- CloudFront Functions
- Lambda@Edge associations
- Custom error responses

A recent distribution change may not have identical behavior everywhere while the configuration propagates.

## Origin Availability

For a typical backend architecture:

```text
CloudFront
    │
    ▼
ALB
    │
    ├── Target A
    ├── Target B
    └── Target C
```

Check target health:

```bash
aws elbv2 describe-target-health \
  --target-group-arn "$TARGET_GROUP_ARN"
```

Look for:

- `healthy`
- `unhealthy`
- `draining`
- Health-check failures
- Registration changes
- Availability Zone distribution

If every target is unhealthy, investigate the application and health-check configuration before modifying CloudFront.

## ALB 503 Responses

An ALB can return `503` when it cannot route traffic to a healthy target.

A common failure path is:

```text
CloudFront
    │
    ▼
ALB
    │
    ├── Unhealthy
    ├── Unhealthy
    └── Unhealthy
         │
         ▼
       503
```

Common causes include:

- All targets are unhealthy.
- The application process has stopped.
- The application is listening on the wrong port.
- Health-check path is incorrect.
- Health-check status code is incorrect.
- Security groups prevent required connectivity.
- Deployments temporarily remove all healthy targets.
- Target registration failed.
- Kubernetes ingress or service routing is broken.

Do not immediately change CloudFront when the ALB is the first failing component.

## Health Check Failures

Suppose the application exposes:

```text
GET /health
```

while the load balancer checks:

```text
GET /healthz
```

If `/healthz` returns `404`, the target can become unhealthy.

A more subtle failure occurs when a health endpoint depends on a downstream service:

```text
GET /health
     │
     ▼
PostgreSQL
     │
     ▼
Unavailable
     │
     ▼
503
     │
     ▼
ALB marks target unhealthy
```

This can cause a healthy application process to be removed from service.

Production systems should distinguish between **liveness** and **readiness**.

For example:

```text
/livez
/readyz
```

A liveness check should normally answer whether the process is alive. A readiness check can determine whether the instance should receive traffic.

Avoid making liveness depend on every external dependency unless there is a deliberate operational reason.

## Application-Level 503

Django, FastAPI, and other applications can intentionally return `503`.

For example:

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
async def readiness() -> dict[str, str]:
    dependency_available = True

    if not dependency_available:
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable",
        )

    return {"status": "ready"}
```

When an application generates the `503`, inspect:

- Application logs
- Exception logs
- Dependency failures
- Database connection pools
- Redis connections
- Worker utilization
- Thread/process exhaustion
- Circuit breakers
- Rate limiting
- Maintenance mode
- Deployment state

The important question is whether the application is intentionally rejecting traffic or failing unexpectedly.

## Capacity Exhaustion

A common production cause is insufficient backend capacity.

For example:

```text
Traffic
  │
  ▼
CloudFront
  │
  ▼
ALB
  │
  ├── Instance 1: CPU 97%
  ├── Instance 2: CPU 99%
  └── Instance 3: CPU 100%
```

Potential symptoms include:

- Increasing latency
- Increased queueing
- Worker exhaustion
- Failed health checks
- Memory pressure
- Container restarts
- Connection-pool exhaustion
- Increasing `503` rate

Inspect the constrained resource rather than assuming CPU is the problem.

Relevant signals include:

- CPU
- Memory
- Network
- Request rate
- Worker utilization
- Database connections
- Redis connections
- Queue depth
- Thread/process count
- Application response time

## Auto Scaling

Auto scaling can reduce capacity-related failures:

```text
CloudFront
    │
    ▼
ALB
    │
    ▼
Auto Scaling Group
    │
    ├── Instance
    ├── Instance
    ├── Instance
    └── Instance
```

Inspect:

- Desired capacity
- Current capacity
- Minimum capacity
- Maximum capacity
- Scaling activities
- Instance launch failures
- Health status
- Scaling metrics

A maximum capacity that is too low can prevent the fleet from absorbing traffic spikes.

A minimum capacity of one creates an avoidable single-instance failure domain.

## Auto Scaling Delays

Auto scaling does not provide instantaneous capacity.

The sequence may be:

```text
Traffic spike
    ↓
Capacity exhaustion
    ↓
503 responses
    ↓
Scaling alarm
    ↓
Instance/container startup
    ↓
Health checks
    ↓
Capacity becomes available
```

If startup takes several minutes, the system needs sufficient baseline capacity to survive traffic spikes during that interval.

Scaling policies should therefore be evaluated against:

- Traffic growth rate
- Application startup time
- Health-check interval
- Warm-up time
- Maximum scaling rate
- Available headroom

## Database Connection Exhaustion

A backend can return `503` when it cannot obtain a PostgreSQL connection:

```text
CloudFront
    ↓
ALB
    ↓
Django/FastAPI
    ↓
PostgreSQL
    ↓
Connection pool exhausted
    ↓
503
```

Inspect:

- Active connections
- Connection pool size
- Worker count
- Query latency
- Long-running transactions
- Lock contention
- Database CPU and memory

For PostgreSQL:

```sql
SELECT
    state,
    count(*)
FROM pg_stat_activity
GROUP BY state;
```

Inspect active sessions:

```sql
SELECT
    pid,
    usename,
    application_name,
    client_addr,
    state,
    query_start
FROM pg_stat_activity
ORDER BY query_start;
```

Do not automatically increase PostgreSQL's connection limit. Increasing the limit can move the bottleneck into database memory or CPU.

The more important question is why the application requires that many concurrent connections.

## Redis Dependency Failures

If Redis is a mandatory dependency:

```text
Request
  ↓
Django/FastAPI
  ↓
Redis unavailable
  ↓
Application cannot continue
  ↓
503
```

Inspect:

- Redis availability
- Client connection pool
- Authentication
- Network connectivity
- Timeouts
- Memory pressure
- Evictions
- Client-side errors

If Redis is only a cache, consider graceful degradation:

```text
Cache unavailable
      │
      ├── Cache is optional
      │       ↓
      │   Query PostgreSQL
      │
      └── Cache is mandatory
              ↓
            503
```

Making an optional cache a hard availability dependency can turn a partial infrastructure failure into a complete outage.

## Kafka and Asynchronous Dependencies

Kafka should not automatically become a synchronous HTTP availability dependency.

A fragile design is:

```text
HTTP request
    ↓
API
    ↓
Kafka
    ↓
Kafka unavailable
    ↓
503
```

For operations that can be asynchronous, a more resilient architecture may be:

```text
HTTP request
    ↓
API
    ↓
Durable operation
    ↓
Kafka
    ↓
Consumer
```

The appropriate design depends on consistency and business requirements.

The key architectural question is:

> Does the HTTP operation actually require Kafka to complete successfully before the client can receive a response?

If not, Kafka availability should generally not determine HTTP availability.

## Celery and Worker Exhaustion

A Celery-backed system can become unavailable when workers are saturated.

For example:

```text
CloudFront
    ↓
API
    ↓
Celery
    ↓
Worker queue saturated
```

Potential symptoms include:

- Increasing queue depth
- Long task execution time
- Worker exhaustion
- Retry storms
- Increasing API latency

Monitor:

- Queue depth
- Worker count
- Worker concurrency
- Task duration
- Failed tasks
- Retry count

Operations that do not need immediate completion should generally remain asynchronous rather than waiting synchronously for worker execution.

## Retry Storms

A particularly dangerous failure pattern is:

```text
Origin becomes overloaded
        ↓
503 responses
        ↓
Clients retry immediately
        ↓
Traffic increases
        ↓
Origin becomes more overloaded
        ↓
More 503 responses
```

This creates a positive feedback loop.

Production clients should use:

- Exponential backoff
- Jitter
- Bounded retries
- Retry budgets
- Idempotency where required
- Circuit breakers where appropriate

Avoid configuring every client to retry every `503` immediately.

## Caching and 503 Responses

Caching can complicate diagnosis.

A sequence may look like:

```text
Origin returns 503
      ↓
CloudFront caches error response
      ↓
Origin recovers
      ↓
Client still receives 503
```

Inspect custom error behavior:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  --query 'DistributionConfig.CustomErrorResponses'
```

If the underlying origin issue has been fixed and a cached error is known to be affecting clients, invalidate only the affected paths:

```bash
aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --paths "/api/health"
```

Avoid invalidating `/*` as a reflex. It can create unnecessary origin load and cost.

## CloudFront Custom Error Responses

Inspect custom error configuration:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  --query 'DistributionConfig.CustomErrorResponses'
```

Review:

- Error code
- Response page path
- Response code
- Error caching minimum TTL

Custom error configuration can make the externally visible response different from the raw origin behavior.

Always compare:

```text
CloudFront response
        vs
Direct origin response
```

when diagnosing an ambiguous error.

## Origin Groups and Failover

If the distribution uses origin failover:

```text
                 ┌── Primary Origin
CloudFront ──────┤
                 └── Secondary Origin
```

verify:

- Primary origin health
- Secondary origin health
- Failover criteria
- Secondary DNS
- TLS configuration
- Application capacity
- Data consistency

A configured secondary origin that has never been tested is not meaningful disaster recovery.

Failover should be exercised during controlled testing.

## Deployment-Related 503 Errors

Correlate the incident with deployment events.

Check:

- Application deployment
- Container rollout
- Kubernetes rollout
- Health-check changes
- Environment variables
- Secrets
- Database migrations
- Load-balancer configuration
- CloudFront changes
- Auto scaling changes

A useful incident timeline is:

```text
10:00  Deployment begins
10:02  Healthy target count decreases
10:03  CloudFront 503 rate increases
10:04  Deployment paused
10:05  Previous version restored
10:07  Healthy targets recover
10:08  503 rate returns to baseline
```

Temporal correlation is not proof of causation, but it provides a strong investigation path.

## Kubernetes Troubleshooting

For Kubernetes-backed origins:

```text
CloudFront
    │
    ▼
ALB
    │
    ▼
Ingress
    │
    ▼
Service
    │
    ▼
Pods
```

A `503` can originate from several layers.

Inspect pods:

```bash
kubectl get pods -n production
```

Inspect services:

```bash
kubectl get svc -n production
```

Inspect endpoints:

```bash
kubectl get endpoints -n production
```

Inspect recent events:

```bash
kubectl get events \
  -n production \
  --sort-by=.lastTimestamp
```

Inspect the deployment:

```bash
kubectl describe deployment api \
  -n production
```

Inspect application logs:

```bash
kubectl logs \
  deployment/api \
  -n production \
  --tail=200
```

Pay particular attention to:

- Pods not ready
- Crash loops
- Failed readiness probes
- No service endpoints
- Scheduling failures
- Resource limits
- Image-pull failures
- Rolling-update behavior

## Rolling Deployment Failures

A deployment can temporarily create zero serving capacity:

```text
Old version
  ├── Pod A
  └── Pod B

Deployment starts
        ↓
Old pods terminate
        ↓
New pods not ready
        ↓
No usable endpoints
        ↓
503
```

For Kubernetes, a production deployment may use:

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 0
    maxSurge: 1
```

The appropriate values depend on available capacity and workload characteristics.

Combine rolling updates with:

- Readiness probes
- Multiple replicas
- Capacity headroom
- Controlled rollout
- Automated rollback

## Monitoring

CloudFront and the origin should be monitored independently.

### CloudFront Signals

Monitor:

- HTTP `5xx` error rate
- `503` rate where available
- Request count
- Cache hit ratio
- Error rate by path or behavior
- Geographic error distribution

### ALB Signals

Monitor:

- ELB-side `5xx`
- Target-side `5xx`
- Healthy host count
- Unhealthy host count
- Target response time
- Request count
- Connection-related metrics

### Application Signals

Monitor:

- HTTP `503` rate
- Latency
- CPU
- Memory
- Worker utilization
- Database connections
- Redis connections
- Queue depth
- Dependency latency

The objective is to correlate the same incident across layers:

```text
CloudFront 5xx
      │
      ▼
ALB 5xx / unhealthy targets
      │
      ▼
Application 503 / latency
      │
      ▼
Dependency failure or resource exhaustion
```

## Log Correlation

Use a request or correlation ID when possible:

```text
X-Request-ID: 7c5b9f...
```

Trace the request across:

```text
Client
  ↓
CloudFront
  ↓
ALB
  ↓
Nginx
  ↓
Django/FastAPI
  ↓
Database / Redis / external services
```

The goal is to identify the first layer where normal request processing stops.

Distributed tracing is particularly valuable when a synchronous API depends on multiple internal services.

## Production Troubleshooting Workflow

### Reproduce the Public Failure

```bash
curl -sS -D - \
  -o /dev/null \
  https://cdn.example.com/api/health
```

### Test the Origin

```bash
curl -sv \
  https://origin.example.com/api/health
```

### Check DNS

```bash
dig origin.example.com
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

### Inspect Kubernetes When Applicable

```bash
kubectl get pods -n production
```

```bash
kubectl get endpoints -n production
```

### Inspect Application Health

```bash
curl -sv \
  http://127.0.0.1:8000/health
```

### Check Capacity

Inspect:

- CPU
- Memory
- Worker count
- Connection pools
- Database connections
- Queue depth
- Request rate
- Response latency

### Check Recent Changes

Correlate:

```text
Deployment
    ↓
Configuration change
    ↓
Capacity/health degradation
    ↓
503 increase
```

### Inspect Custom Error Configuration

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" \
  --query 'DistributionConfig.CustomErrorResponses'
```

### Invalidate Only When Necessary

```bash
aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --paths "/api/health"
```

### Verify Recovery

```bash
curl -fsS \
  https://cdn.example.com/api/health \
  -o /dev/null
```

A single successful request is not sufficient. Verify that the error rate has returned to normal and that backend capacity remains healthy.

## Common Production Pitfalls

### Assuming Every 503 Comes From CloudFront

The origin can return `503` directly.

**Avoid it:** compare CloudFront and origin responses and inspect origin-side telemetry.

### Restarting Servers Before Finding the Failure Layer

A restart can temporarily hide symptoms while leaving the root cause unresolved.

**Avoid it:** identify the first unhealthy component before taking remediation actions.

### Ignoring Load-Balancer Target Health

An application process can be running while the load balancer considers every target unhealthy.

**Avoid it:** inspect target health and health-check configuration.

### Making Health Checks Too Strict

If readiness depends on PostgreSQL, Redis, Kafka, and several external APIs, one dependency failure can remove every target from service.

**Avoid it:** separate liveness and readiness semantics deliberately.

### Running Without Capacity Headroom

A fleet operating near maximum capacity has little tolerance for traffic spikes or instance failures.

**Avoid it:** maintain sufficient baseline capacity and test scaling behavior.

### Scaling Without Identifying the Bottleneck

Adding application instances does not solve a PostgreSQL, Redis, network, or external-service bottleneck.

**Avoid it:** identify the constrained resource first.

### Aggressive Retries

Immediate retries can amplify an outage.

**Avoid it:** use bounded exponential backoff with jitter and appropriate retry policies.

### Invalidating Before Fixing the Origin

Invalidation does not create backend capacity or repair an unhealthy origin.

**Avoid it:** fix the underlying availability problem first.

### Ignoring Deployment Behavior

A rollout can temporarily eliminate all ready targets.

**Avoid it:** use readiness checks, multiple replicas, controlled rollout strategies, and rollback automation.

### Treating Optional Dependencies as Mandatory

A cache outage should not necessarily make the entire API unavailable.

**Avoid it:** explicitly define graceful-degradation behavior.

## Security Considerations

Availability troubleshooting must not weaken security controls.

Do not resolve a `503` by blindly:

- Opening security groups to `0.0.0.0/0`
- Disabling authentication
- Disabling TLS
- Disabling AWS WAF protections
- Exposing private origins directly
- Removing network restrictions
- Disabling health checks

For example, do not respond to a connectivity failure by changing an ALB security group to:

```text
0.0.0.0/0
```

without establishing which component actually requires access.

Availability and security should be investigated together.

## High Availability Recommendations

For critical CloudFront-backed services:

- Deploy application capacity across multiple Availability Zones.
- Use multiple application instances or pods.
- Maintain serving capacity during deployments.
- Configure meaningful readiness checks.
- Use auto scaling with sufficient headroom.
- Monitor ALB target health.
- Avoid single-instance failure domains.
- Design dependencies for partial failure.
- Test origin failover.
- Maintain automated rollback.

A resilient architecture may look like:

```mermaid
flowchart LR
    Clients --> CloudFront
    CloudFront --> ALB

    ALB --> AppA[Application AZ-A]
    ALB --> AppB[Application AZ-B]
    ALB --> AppC[Application AZ-C]

    AppA --> DB[(PostgreSQL)]
    AppB --> DB
    AppC --> DB
```

The objective is not merely to keep one instance alive. The architecture should preserve enough healthy capacity to survive instance, Availability Zone, deployment, and dependency failures.

## Disaster Recovery Considerations

Recovery procedures should cover:

- CloudFront distribution
- Origin configuration
- DNS
- ALB
- Application infrastructure
- Kubernetes resources
- PostgreSQL
- Redis
- Secrets
- Certificates
- CloudFront Functions
- Lambda@Edge functions
- Infrastructure-as-code

A recovery sequence can be:

```text
Restore infrastructure
        ↓
Restore origin capacity
        ↓
Restore dependencies
        ↓
Validate health checks
        ↓
Validate load balancer
        ↓
Validate CloudFront
        ↓
Validate DNS
        ↓
Run end-to-end smoke tests
```

Keep infrastructure configuration in version control and test restoration procedures rather than assuming that configuration backups alone guarantee recovery.

## Cost Considerations

Troubleshooting a `503` should also consider whether the remediation creates a secondary cost problem.

Examples:

- Scaling the application fleet excessively
- Invalidating `/*` unnecessarily
- Increasing database capacity without identifying the bottleneck
- Creating excessive log volume
- Increasing retry traffic
- Keeping emergency over-provisioning permanently

A useful production response distinguishes between:

```text
Temporary emergency capacity
        vs
Permanent architectural capacity
```

After recovery, review whether the capacity increase should remain.

## Interview Perspective

A strong answer to:

> "CloudFront is returning 503. How would you troubleshoot it?"

should begin by establishing the failure boundary.

A production-oriented sequence is:

1. Reproduce the `503` through the CloudFront endpoint.
2. Inspect response headers and determine whether CloudFront generated or forwarded the response.
3. Test the origin directly.
4. Check the ALB or ingress.
5. Inspect target health and application readiness.
6. Check CPU, memory, workers, connections, and queue depth.
7. Inspect PostgreSQL, Redis, Kafka, and other dependencies.
8. Check deployments and scaling events.
9. Investigate sudden traffic increases and retry storms.
10. Inspect CloudFront custom error and caching configuration.
11. Repair the failing layer.
12. Invalidate affected paths only when justified.
13. Verify recovery through the public CloudFront endpoint.
14. Confirm that error rates and backend health have returned to normal.

The important mental model is:

```text
503
 │
 ├── CloudFront?
 │
 ├── Origin?
 │    ├── ALB?
 │    ├── Ingress?
 │    └── Nginx?
 │
 ├── Application?
 │    ├── Capacity?
 │    ├── Workers?
 │    └── Readiness?
 │
 ├── Dependencies?
 │    ├── PostgreSQL?
 │    ├── Redis?
 │    ├── Kafka?
 │    └── External APIs?
 │
 ├── Deployment?
 │
 ├── Scaling?
 │
 └── Cached error?
```

## Key Takeaways

- **A CloudFront `503` is an availability signal, not automatically a CloudFront failure:** determine whether CloudFront, the origin, the load balancer, or the application generated the response.
- **Check healthy capacity early:** ALB target health, Kubernetes readiness, worker utilization, CPU, memory, connection pools, and scaling limits are common production failure points.
- **Design dependencies for graceful degradation:** Redis, caches, Kafka, and external services should not automatically become full-service availability dependencies unless required by the business operation.
- **Control retries and deployments:** retry storms and zero-capacity rolling deployments can turn temporary failures into cascading outages.
- **Fix the failing layer before invalidating caches:** CloudFront invalidation cannot repair unhealthy infrastructure, exhausted capacity, broken dependencies, or incorrect health checks.