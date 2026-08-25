# Common Performance Metrics

## Overview

A production API generates thousands—or even millions—of requests every day. Monitoring a single metric is not enough to understand the health of an API.

Amazon API Gateway automatically publishes several CloudWatch metrics that help engineers measure:

- Availability
- Performance
- Reliability
- Scalability
- Traffic patterns
- Backend health
- Cache efficiency

Understanding these metrics is essential for operating production APIs, troubleshooting issues, and preparing for AWS certification and backend engineering interviews.

---

# Why Performance Metrics Matter?

Imagine customers complain:

```text
"The API is slow."
```

Is the problem:

- API Gateway?
- Lambda?
- Database?
- Network?
- Traffic spike?

Performance metrics provide the answer.

```text
CloudWatch Metrics

↓

Performance Analysis

↓

Root Cause

↓

Fix
```

---

# Performance Monitoring Architecture

```text
             Clients

                │

                ▼

        Amazon API Gateway

                │

        CloudWatch Metrics

                │

                ▼

      Dashboards & Alarms

                │

                ▼

      Operations Team
```

Every request contributes to operational metrics.

---

# Request Count (Count)

Measures:

```text
Total API Requests
```

Example:

```text
09:00

↓

500 Requests

---------------------

10:00

↓

5000 Requests
```

Use cases:

- Traffic analysis
- Capacity planning
- Business analytics
- Detecting unusual spikes

---

# Latency

Measures:

```text
Total Time

Client Request

↓

API Gateway

↓

Backend

↓

Response
```

Includes:

- API Gateway processing
- Backend execution
- Response processing

Measured in:

```text
Milliseconds (ms)
```

Lower latency indicates a faster API.

---

# Integration Latency

Measures only:

```text
API Gateway

↓

Backend

↓

API Gateway
```

It excludes API Gateway processing.

Useful for identifying backend bottlenecks.

---

# Latency vs Integration Latency

Example:

```text
Latency

900 ms

--------------------

Integration Latency

850 ms
```

Conclusion:

```text
Backend is Slow
```

Another example:

```text
Latency

900 ms

--------------------

Integration Latency

150 ms
```

Conclusion:

API Gateway configuration or networking should be investigated.

---

# 4XX Errors

Represents client-side errors.

Examples:

```text
400 Bad Request

401 Unauthorized

403 Forbidden

404 Not Found

429 Too Many Requests
```

Common causes:

- Invalid requests
- Authentication failures
- Missing resources
- Rate limiting

---

# 5XX Errors

Represents server-side failures.

Examples:

```text
500 Internal Server Error

502 Bad Gateway

503 Service Unavailable

504 Gateway Timeout
```

Usually indicates:

- Lambda failures
- Backend crashes
- Database problems
- Integration timeouts

---

# Cache Hit Count

Available when API Gateway caching is enabled.

```text
Request

↓

Cache

↓

Found

↓

Response
```

CloudWatch increments:

```text
CacheHitCount
```

Higher values mean better performance.

---

# Cache Miss Count

Occurs when cached data is unavailable.

```text
Request

↓

Cache

↓

Miss

↓

Backend
```

CloudWatch increments:

```text
CacheMissCount
```

High values may indicate:

- Small cache
- Short TTL
- Frequently changing data

---

# Cache Hit Ratio

An important performance indicator.

Formula:

```text
Cache Hit Ratio

=

Hits

/

(Hits + Misses)
```

Example:

```text
Hits

950

Misses

50
```

Result:

```text
95% Hit Ratio
```

Higher is generally better.

---

# Throttle Count

Represents requests rejected because rate limits were exceeded.

```text
Client

↓

Too Many Requests

↓

429
```

Causes:

- Traffic spikes
- API abuse
- Incorrect throttling configuration

---

# Data Processed

Measures:

```text
Bytes Received

Bytes Sent
```

Useful for:

- Network utilization
- Cost optimization
- Compression analysis

---

# Error Rate

Formula:

```text
Errors

/

Total Requests
```

Example:

```text
Requests

10000

Errors

50
```

Error Rate:

```text
0.5%
```

Lower error rates indicate healthier APIs.

---

# Availability

Availability represents how often the API is operational.

Formula:

```text
Successful Requests

/

Total Requests
```

Example:

```text
99.99%
```

Production APIs often target:

```text
99.9%

99.95%

99.99%
```

---

# Throughput

Throughput measures how many requests an API processes.

Example:

```text
Requests

↓

5000

Per Second
```

Useful for:

- Capacity planning
- Load testing
- Scaling decisions

---

# P50, P90, P95, P99 Latency

Average latency does not tell the complete story.

Example:

```text
P50

120 ms

↓

Median User
```

```text
P95

450 ms

↓

95% Users Faster
```

```text
P99

1800 ms

↓

Worst 1%
```

Production systems commonly monitor:

- P95
- P99

These reveal slow requests hidden by averages.

---

# Metric Relationships

```text
High Latency

+

High Integration Latency

↓

Backend Problem

-------------------------

High Latency

+

Low Integration Latency

↓

Gateway or Network Issue

-------------------------

High 5XX

↓

Backend Failure

-------------------------

High 429

↓

Throttling
```

Looking at metrics together provides better insights than analyzing a single metric.

---

# Dashboard Example

A production dashboard typically includes:

```text
Request Count

Latency

Integration Latency

4XX Errors

5XX Errors

Throttle Count

Cache Hit Ratio

Availability
```

Operations teams use dashboards for real-time monitoring.

---

# Performance Investigation

Suppose customers report slow responses.

Dashboard:

```text
Latency

↓

1200 ms

Integration Latency

↓

1100 ms

5XX

↓

0
```

Conclusion:

Backend is slow but healthy.

Another example:

```text
Latency

↓

1200 ms

Integration Latency

↓

150 ms

5XX

↓

0
```

Conclusion:

Gateway configuration or networking should be investigated.

---

# Real-World Example

A retail platform experiences heavy traffic during a sale.

Dashboard:

```text
Request Count

↑↑↑

Cache Hit Ratio

97%

Latency

Stable

5XX

0
```

Conclusion:

Caching is effectively protecting backend services.

---

# Best Practices

- Monitor multiple metrics together rather than relying on a single metric.
- Investigate both Latency and Integration Latency when troubleshooting performance.
- Track 4XX and 5XX errors separately.
- Monitor Cache Hit Ratio for cached APIs.
- Create CloudWatch Alarms for latency, errors, and throttling.
- Review dashboards regularly during peak traffic.
- Combine metrics with CloudWatch Logs and X-Ray for complete observability.

---

# Common Interview Questions

### Which API Gateway metric measures total response time?

**Latency** measures the total time taken to process a request, including API Gateway and backend execution.

---

### Which metric measures backend execution time?

**IntegrationLatency** measures only the time spent communicating with the backend integration.

---

### What does a high CacheHitCount indicate?

It indicates that API Gateway is serving many requests directly from cache, reducing backend load and improving performance.

---

### What is the difference between 4XX and 5XX errors?

- **4XX** errors are caused by client requests (authentication failures, bad requests, missing resources).
- **5XX** errors indicate server-side or backend failures.

---

### Why are P95 and P99 latency important?

Average latency can hide slow requests. P95 and P99 show how the slowest requests perform, making them valuable indicators of real user experience.

---

# Key Takeaways

- CloudWatch performance metrics provide insight into API health, scalability, reliability, and user experience.
- Core metrics include Request Count, Latency, Integration Latency, 4XX Errors, 5XX Errors, CacheHitCount, CacheMissCount, and ThrottleCount.
- Monitoring multiple metrics together helps identify whether issues originate in API Gateway, backend services, or client behavior.
- Percentile metrics such as P95 and P99 provide a more realistic view of production performance than averages alone.
- Combining CloudWatch Metrics, CloudWatch Logs, X-Ray, dashboards, and alarms creates a complete observability strategy for production APIs.