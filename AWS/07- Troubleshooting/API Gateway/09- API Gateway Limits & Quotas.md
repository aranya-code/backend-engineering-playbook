# API Gateway Limits & Quotas

## Overview

Amazon API Gateway is a fully managed service, but like every AWS service, it operates within predefined **limits** and **quotas**.

Some limits are **hard limits** that cannot be changed, while others are **service quotas** that can be increased by requesting a quota adjustment through AWS.

Understanding these limits is essential when designing scalable, production-grade APIs.

Ignoring service limits can result in:

- 429 Too Many Requests
- Deployment failures
- Integration failures
- Payload rejection
- Unexpected throttling

This guide covers the most important API Gateway limits, explains how they affect production systems, and provides strategies for designing around them.

---

# Categories of Limits

```text
API Gateway

│

├── Request Limits

├── Payload Limits

├── Integration Limits

├── Throttling Limits

├── Resource Limits

├── Account Limits

└── Service Quotas
```

---

# Common Limits

| Category | Example |
|----------|---------|
| Request Rate | Requests per second |
| Burst Limit | Short traffic spikes |
| Payload Size | Request/Response size |
| Timeout | Backend execution time |
| API Count | Number of APIs |
| Stage Count | Number of stages |
| API Keys | Number of API keys |

---

# Request Rate Limit

Every AWS account has a request rate quota.

Example:

```text
10,000 Requests/Second
```

(Default value varies by Region and account.)

---

## Symptoms

```http
429 Too Many Requests
```

---

## Diagnose

CloudWatch Metric

```text
ThrottleCount
```

---

## Solution

- Request a quota increase
- Implement retries
- Enable caching
- Use CloudFront

---

# Burst Limit

API Gateway allows temporary bursts above the steady-state request rate.

Example:

```text
Steady Rate

↓

10,000 RPS

Burst

↓

5,000 Requests
```

Burst capacity is temporary and should not be relied upon for sustained traffic.

---

# Payload Size Limit

Large request bodies are rejected.

Example:

```http
413 Payload Too Large
```

---

## Common Causes

- File uploads
- Large JSON
- Images
- Videos

---

## Solution

Store large files in:

```text
Amazon S3
```

Send only metadata through API Gateway.

---

# Integration Timeout

API Gateway waits for the backend only for a limited duration.

If exceeded:

```http
504 Gateway Timeout
```

---

## Common Causes

- Slow Lambda
- Slow ECS Service
- Database latency

---

## Solution

- Optimize backend
- Use asynchronous workflows
- Cache responses

---

# Lambda Timeout vs API Gateway Timeout

```text
API Gateway

↓

Timeout

--------------------

Lambda

↓

Independent Timeout
```

Lambda may support a longer execution time than API Gateway waits for a synchronous response.

---

# API Resource Limits

Large APIs contain:

```text
Resources

↓

Methods

↓

Integrations
```

Very large APIs become difficult to maintain.

---

## Recommendation

Split large applications into:

- Multiple APIs
- Microservices
- Domain-based APIs

---

# Stage Limits

An API can contain multiple stages.

Example:

```text
dev

↓

test

↓

staging

↓

prod
```

Avoid creating unnecessary stages.

---

# API Key Limits

Large organizations may create:

```text
Thousands

↓

API Keys
```

---

## Recommendation

- Remove unused keys
- Rotate keys regularly
- Automate lifecycle management

---

# Usage Plan Limits

Large SaaS platforms often use:

```text
Customer

↓

API Key

↓

Usage Plan
```

Monitor Usage Plans to avoid excessive growth.

---

# Mapping Template Limits

Very complex Velocity Template Language (VTL) templates can become:

- Difficult to maintain
- Error-prone
- Slower to process

---

## Recommendation

Prefer:

```text
Lambda Proxy Integration
```

instead of heavy request or response transformations.

---

# Logging Volume

High traffic generates:

```text
Millions

↓

CloudWatch Log Events
```

---

## Impact

- Higher CloudWatch costs
- Increased storage
- More difficult log analysis

---

## Solution

- Log only useful information
- Configure retention
- Archive old logs if required

---

# API Gateway Cache Limits

Cache consumes additional resources.

---

## Monitor

CloudWatch Metrics:

```text
CacheHitCount

CacheMissCount
```

---

## Recommendation

Cache:

- Product Catalogs
- Reference Data
- Configuration Data

Avoid caching frequently changing data.

---

# Regional Limits

Each Region has independent quotas.

Example:

```text
US-East-1

↓

Quota A

----------------

EU-West-1

↓

Quota B
```

Always verify limits for the Region where the API is deployed.

---

# Monitoring Service Quotas

Navigate:

```text
AWS Console

↓

Service Quotas

↓

Amazon API Gateway
```

Review:

- Current quota
- Applied quota
- Maximum allowed

---

# Requesting a Quota Increase

Many quotas can be increased.

Workflow:

```text
Service Quotas

↓

Request Increase

↓

AWS Review

↓

Approved
```

Not all limits are adjustable.

---

# CloudWatch Monitoring

Monitor:

- Count
- 4XXError
- 5XXError
- Latency
- IntegrationLatency
- ThrottleCount
- CacheHitCount
- CacheMissCount

Configure alarms before production incidents occur.

---

# Architecture Considerations

Instead of building:

```text
One Massive API
```

Prefer:

```text
Users API

Orders API

Products API

Payments API
```

Smaller APIs are easier to scale, deploy, and troubleshoot.

---

# Scaling Strategy

```text
Users

↓

CloudFront

↓

API Gateway

↓

Lambda / ECS

↓

Redis

↓

Database
```

Scaling should occur across the entire architecture, not only at API Gateway.

---

# Best Practices

- Monitor CloudWatch metrics continuously.
- Design APIs to avoid service limits.
- Use pagination for large datasets.
- Store large files in Amazon S3.
- Enable caching for read-heavy workloads.
- Request quota increases before expected traffic spikes.
- Split monolithic APIs into domain-focused services.
- Test APIs under production-like load.

---

# Production Checklist

Verify:

- Request rate within quota
- Burst traffic handled
- Payload size acceptable
- Backend response time optimized
- CloudWatch alarms configured
- API Keys managed
- Usage Plans monitored
- Cache configured
- Quotas reviewed
- Load testing completed

---

# Common Interview Questions

### What is the difference between a limit and a quota?

A **limit** is a maximum value enforced by the service. A **quota** is a configurable service limit that may be increased by submitting a request through AWS Service Quotas, depending on the specific resource.

---

### Why does API Gateway return `429 Too Many Requests`?

This usually occurs when request rates exceed configured throttling limits or account-level quotas. It can also happen when clients exceed Usage Plan limits.

---

### Why shouldn't large files be uploaded through API Gateway?

API Gateway has payload size limits and is optimized for API traffic rather than file transfer. Large objects should be uploaded directly to Amazon S3 using pre-signed URLs.

---

### How do you monitor API Gateway limits?

Use CloudWatch Metrics to monitor request rates, latency, throttling, cache performance, and error rates. Use AWS Service Quotas to review and request increases for adjustable quotas.

---

### How can API Gateway scale for enterprise applications?

By combining API Gateway with CloudFront, caching, backend auto scaling (Lambda or ECS), efficient database design, and domain-based API decomposition, applications can handle significantly larger workloads while remaining maintainable.

---

# Key Takeaways

- Amazon API Gateway operates within service limits and quotas that influence scalability and reliability.
- Common constraints include request rate, burst capacity, payload size, integration timeout, and account-level quotas.
- CloudWatch Metrics and AWS Service Quotas are essential tools for monitoring usage and planning capacity.
- Designing APIs with pagination, caching, asynchronous processing, and domain separation helps avoid hitting service limits.
- Understanding API Gateway limits is an important part of building resilient, production-ready backend systems.