# Performance & Resource Bottlenecks

Performance issues in Amazon ECS can significantly impact application responsiveness, user experience, and infrastructure costs. Unlike deployment failures, performance bottlenecks are often gradual and may only become apparent under increased load.

Performance problems can originate from multiple layers including:

- Application code
- CPU limitations
- Memory pressure
- Database performance
- Network latency
- Disk I/O
- Load Balancer configuration
- Container resource limits

A systematic investigation helps identify the true bottleneck instead of treating only the symptoms.

---

# Typical Symptoms

You may observe one or more of the following:

- Slow API responses
- High latency
- Increased error rates
- Timeouts
- High CPU utilization
- High memory utilization
- Frequent container restarts
- Auto Scaling unable to keep up

Example

```
Users

↓

API Requests

↓

High Response Time

↓

Poor User Experience
```

---

# Performance Troubleshooting Workflow

```
Performance Issue

        │

        ▼

CloudWatch Metrics

        │

        ▼

Application Metrics

        │

        ▼

Logs

        │

        ▼

Database

        │

        ▼

Network

        │

        ▼

Infrastructure

        │

        ▼

Root Cause
```

---

# Step 1: Check CPU Utilization

Review CloudWatch metrics.

Example

```
CPU

95%
```

High CPU utilization may indicate:

- Heavy computations
- Insufficient task count
- Poor application performance
- Inefficient algorithms

---

## Investigation

Review:

- CPU utilization
- Running tasks
- Auto Scaling events
- Request rate

---

## Resolution

- Scale horizontally.
- Increase task CPU.
- Optimize application code.

---

# Step 2: Check Memory Utilization

Memory pressure often leads to degraded performance before containers are terminated.

Example

```
Memory

92%
```

Possible causes

- Memory leaks
- Large caches
- Large datasets
- Inefficient object creation

---

## Investigation

Review

- Memory metrics
- Application heap usage
- Cache size

---

## Resolution

- Increase memory allocation.
- Optimize memory usage.
- Fix memory leaks.

---

# Step 3: Review Application Response Time

Infrastructure may appear healthy while the application remains slow.

Monitor

- Average response time
- P95 latency
- P99 latency

Example

```
Average

200 ms

↓

P95

1.8 sec
```

High percentile latency usually indicates occasional bottlenecks affecting users.

---

# Step 4: Review Database Performance

Databases are frequently the real bottleneck.

Investigate

- Slow queries
- Missing indexes
- Connection pool exhaustion
- Lock contention
- High CPU
- High I/O

Example

```
API

↓

Database Query

↓

4 Seconds
```

---

## Resolution

- Add indexes.
- Optimize SQL.
- Increase connection pool.
- Introduce caching.

---

# Step 5: Review Redis Performance

Redis should reduce database load.

Investigate

- Cache hit ratio
- Cache misses
- Network latency
- Memory utilization
- Evictions

Low cache hit rates increase database traffic.

---

# Step 6: Review Network Latency

Investigate communication between:

- ECS ↔ Database
- ECS ↔ Redis
- ECS ↔ External APIs
- ECS ↔ Other ECS Services

Example

```
API

↓

External Service

↓

8 Seconds
```

---

## Resolution

- Retry transient failures.
- Use connection pooling.
- Reduce unnecessary network calls.
- Cache responses.

---

# Step 7: Review Load Balancer Metrics

Monitor:

- Request Count
- Target Response Time
- HTTP 5XX
- Healthy Targets

Example

```
Target Response Time

3.5 Seconds
```

High response times often indicate backend performance issues.

---

# Step 8: Review Auto Scaling

Insufficient scaling may overload existing tasks.

Verify

- Target utilization
- Scaling policy
- Running task count
- Scaling history

---

# Step 9: Review Container Limits

Example

```
CPU

512

Memory

1024 MB
```

Applications may simply require larger resource allocations.

Avoid assigning resources arbitrarily—use CloudWatch metrics to justify changes.

---

# Step 10: Profile the Application

Infrastructure is not always the bottleneck.

Use profiling tools appropriate for your language.

Examples

Python

- cProfile
- py-spy

Java

- JProfiler
- VisualVM

Node.js

- Node Inspector

Profiling identifies slow methods and excessive CPU usage.

---

# Step 11: Review External Dependencies

Applications often depend on:

- Third-party APIs
- Authentication providers
- Payment gateways
- Email services

Slow downstream services affect overall response time.

---

## Resolution

Implement

- Timeouts
- Retry policies
- Circuit breakers
- Caching

---

# Step 12: Analyze CloudWatch Metrics

Important metrics include

Infrastructure

- CPU Utilization
- Memory Utilization
- Network In
- Network Out

Application

- Response Time
- Error Rate
- Throughput

Business

- Orders
- Transactions
- Active Users

Correlating these metrics often reveals the source of degradation.

---

# Common Performance Bottlenecks

## High CPU

Possible causes

- Heavy computation
- Poor algorithms
- Too few tasks

---

## High Memory

Possible causes

- Memory leak
- Large cache
- Large object graph

---

## Slow Database

Possible causes

- Missing indexes
- Slow queries
- Connection limits

---

## Slow External APIs

Possible causes

- Third-party latency
- Network congestion
- API throttling

---

## Load Balancer Bottleneck

Possible causes

- Unhealthy targets
- Too few tasks
- Backend latency

---

## Cache Misses

Possible causes

- Cache expiration
- Poor cache strategy
- Incorrect cache keys

---

# Common Root Causes

| Problem | Solution |
|----------|----------|
| High CPU | Scale out or optimize code |
| High memory | Optimize memory or increase limits |
| Slow SQL | Optimize queries and indexes |
| External API latency | Retry, cache, or use circuit breakers |
| Cache misses | Improve caching strategy |
| Load Balancer latency | Add healthy tasks or optimize backend |
| Too few tasks | Enable Auto Scaling |
| Resource limits too low | Increase CPU or memory allocation |

---

# Diagnostic Checklist

Before making infrastructure changes, verify:

- CPU utilization reviewed.
- Memory utilization reviewed.
- Response time analyzed.
- Database performance checked.
- Redis metrics reviewed.
- Network latency measured.
- External API performance reviewed.
- Load Balancer metrics reviewed.
- Auto Scaling functioning.
- Application profiling completed.

---

# Best Practices

- Monitor P95 and P99 latency, not just averages.
- Use Redis to reduce database load.
- Enable Auto Scaling before peak traffic.
- Profile applications regularly.
- Optimize database queries before scaling infrastructure.
- Configure CloudWatch dashboards for key metrics.
- Implement connection pooling.
- Cache expensive operations whenever appropriate.

---

# Interview Questions

### Why is your ECS application slow even though CPU usage is low?

Possible reasons include:

- Slow database queries
- External API latency
- Network issues
- Lock contention
- Cache misses
- Thread contention

CPU is only one indicator of performance.

---

### How would you identify a performance bottleneck?

Recommended approach:

1. Review CloudWatch metrics.
2. Measure response time.
3. Analyze logs.
4. Check database performance.
5. Review Redis metrics.
6. Measure network latency.
7. Profile the application.

---

### Should you always increase CPU when performance is poor?

No.

Increasing CPU may mask the symptom without fixing the underlying issue. Always identify the bottleneck first.

---

### Which metrics are most important for production?

Infrastructure

- CPU
- Memory
- Network

Application

- Response Time
- Error Rate
- Throughput

Business

- Transactions
- Orders
- Active Users

---

### Why monitor P95 latency instead of only average latency?

Average latency can hide occasional slow requests. P95 (and P99) latency provides a better view of the experience of the slowest requests, making it easier to identify performance issues that affect users.

---

# Key Takeaways

- Performance bottlenecks can originate from the application, database, cache, network, or infrastructure.
- Investigate performance systematically using CloudWatch metrics, application logs, profiling tools, and dependency analysis.
- High CPU or memory utilization is not always the root cause; slow databases, cache misses, and external services are common contributors.
- Monitor percentile latencies (P95/P99), application throughput, and business metrics in addition to infrastructure metrics.
- Optimize the root cause before increasing infrastructure resources to achieve better performance and cost efficiency.