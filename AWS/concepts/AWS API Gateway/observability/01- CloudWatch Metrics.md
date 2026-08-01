# CloudWatch Metrics

## Overview

Amazon CloudWatch Metrics provide real-time visibility into the health, performance, and availability of your Amazon API Gateway APIs.

Every API invocation automatically publishes operational metrics to Amazon CloudWatch, allowing teams to monitor:

- Request volume
- Error rates
- Latency
- Backend performance
- Cache efficiency
- Throttling
- Availability

These metrics help engineers detect problems before customers are affected and are the foundation of production monitoring, alerting, and auto-scaling strategies.

---

# Why CloudWatch Metrics?

Imagine an API serving thousands of users.

```text
Clients

↓

Amazon API Gateway

↓

Lambda

↓

Database
```

Without monitoring:

- Errors go unnoticed
- Performance degradation is invisible
- Capacity issues remain hidden

With CloudWatch Metrics:

```text
API Requests

↓

CloudWatch Metrics

↓

Dashboards

↓

Alarms

↓

Notifications
```

Operations teams gain complete visibility into API health.

---

# Architecture

```text
             Clients

                │

                ▼

        Amazon API Gateway

                │

        Publish Metrics

                │

                ▼

      Amazon CloudWatch

                │

     ┌──────────┴──────────┐

     ▼                     ▼

 Dashboards           CloudWatch Alarms
```

Metrics are automatically collected without modifying application code.

---

# Metric Collection Flow

```text
Client Request

↓

API Gateway

↓

Collect Metrics

↓

CloudWatch

↓

Dashboard
```

Every request contributes to operational metrics.

---

# Namespace

API Gateway metrics are published under the CloudWatch namespace:

```text
AWS/ApiGateway
```

Each metric is associated with dimensions such as:

- API Name
- Stage
- Method
- Resource
- Region

---

# Dimensions

CloudWatch allows metrics to be filtered using dimensions.

Example:

```text
API Name

↓

Orders API

-----------------------

Stage

↓

Production

-----------------------

Method

↓

GET

-----------------------

Resource

↓

/orders
```

This enables granular monitoring.

---

# Request Count

The **Count** metric represents the total number of API requests.

Example:

```text
10,000 Requests

↓

Count = 10,000
```

Use this metric to monitor:

- Traffic growth
- Usage trends
- Peak load
- Capacity planning

---

# Latency

Latency measures the total time required to process a request.

Includes:

- API Gateway processing
- Backend execution
- Response generation

```text
Client

↓

API Gateway

↓

Backend

↓

Response

↓

Latency
```

Measured in milliseconds.

---

# Integration Latency

Integration Latency measures only backend execution time.

```text
API Gateway

↓

Backend

↓

API Gateway

↓

Integration Latency
```

It excludes API Gateway processing.

---

# Latency vs Integration Latency

| Latency | Integration Latency |
|----------|---------------------|
| Total request time | Backend processing time |
| Includes API Gateway | Backend only |
| Client experience | Backend performance |

Difference:

```text
Latency

=

Gateway Processing

+

Integration Latency
```

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

High 4XX rates often indicate:

- Invalid requests
- Authentication failures
- Authorization failures
- Client bugs

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

High 5XX rates usually indicate backend problems.

---

# Cache Hit Count

When API Gateway caching is enabled:

```text
Request

↓

Cache

↓

Found

↓

Cache Hit
```

CloudWatch increments:

```text
CacheHitCount
```

A high cache hit ratio improves performance.

---

# Cache Miss Count

If data is not found:

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

High cache misses may indicate:

- Low TTL
- Poor cache configuration
- Frequently changing data

---

# Data Processed

Some workloads monitor:

```text
Bytes Received

Bytes Sent
```

Useful for:

- Network utilization
- Cost analysis
- Compression effectiveness

---

# Metric Visualization

CloudWatch Dashboards display metrics.

Example:

```text
Request Count

↑

│        ████

│      ███████

│   ███████████

└──────────────────► Time
```

Dashboards help identify trends over time.

---

# Monitoring API Health

Healthy API:

```text
High Request Count

Low Latency

Low 5XX Errors

Low Throttling
```

Unhealthy API:

```text
Increasing Latency

Increasing 5XX

Increasing Integration Latency
```

---

# Performance Analysis

Example:

```text
Latency

↓

800 ms

----------------

Integration Latency

↓

780 ms
```

Conclusion:

Backend is slow.

Another example:

```text
Latency

↓

900 ms

----------------

Integration Latency

↓

200 ms
```

Conclusion:

Gateway configuration or network overhead should be investigated.

---

# Dashboards

A production dashboard typically includes:

- Request Count
- Latency
- Integration Latency
- 4XX Errors
- 5XX Errors
- Cache Hit Count
- Cache Miss Count
- Throttle Count

This provides a complete operational overview.

---

# CloudWatch Insights

Metrics can be correlated with:

- CloudWatch Logs
- X-Ray Traces
- Lambda Metrics
- DynamoDB Metrics

This enables end-to-end troubleshooting.

---

# Real-World Example

E-commerce API:

```text
Customers

↓

API Gateway

↓

CloudWatch

↓

Dashboard
```

Dashboard shows:

```text
Request Count ↑

Latency Stable

5XX = 0

Cache Hit = 95%
```

Operations conclude the API is healthy.

---

# Best Practices

- Monitor Request Count continuously.
- Track both Latency and Integration Latency.
- Investigate increasing 5XX errors immediately.
- Enable API caching where appropriate and monitor cache hit ratios.
- Build CloudWatch Dashboards for production APIs.
- Review traffic trends regularly for capacity planning.
- Combine metrics with logs and traces for effective troubleshooting.

---

# Common Interview Questions

### What CloudWatch namespace is used for API Gateway?

```text
AWS/ApiGateway
```

---

### What is the difference between Latency and Integration Latency?

Latency measures the total request time experienced by the client.

Integration Latency measures only the time spent communicating with the backend integration.

---

### What do 4XX errors indicate?

Client-side problems such as invalid requests, authentication failures, authorization failures, or missing resources.

---

### What do 5XX errors indicate?

Server-side failures caused by API Gateway integrations or backend services.

---

### Why monitor CacheHitCount?

A high CacheHitCount indicates that API Gateway is serving requests directly from cache, reducing backend load and improving performance.

---

# Key Takeaways

- CloudWatch Metrics provide automatic operational monitoring for Amazon API Gateway.
- Key metrics include Request Count, Latency, Integration Latency, 4XX Errors, 5XX Errors, CacheHitCount, and CacheMissCount.
- Comparing Latency with Integration Latency helps isolate whether performance issues originate in API Gateway or backend services.
- CloudWatch Dashboards and metrics are essential for monitoring API health, performance, and capacity.
- Metrics should be combined with CloudWatch Logs and AWS X-Ray for comprehensive observability and troubleshooting.