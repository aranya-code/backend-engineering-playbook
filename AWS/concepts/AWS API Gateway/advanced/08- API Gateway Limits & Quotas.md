# API Gateway Limits & Quotas

## Overview

Amazon API Gateway is a fully managed service, but like every AWS service, it has **service quotas (limits)** designed to protect the platform and ensure fair resource allocation.

Understanding these limits is essential because they directly affect:

- Scalability
- Performance
- Reliability
- API Design
- Production Readiness

Many production issues are not caused by application bugs but by reaching AWS service limits such as request throttling, payload size restrictions, timeout limits, or Lambda concurrency limits.

As a Senior Backend Engineer, you should design APIs with these quotas in mind.

---

# Why Limits Matter?

Imagine your API suddenly receives:

```text
2 Million Requests

↓

API Gateway

↓

Backend
```

If your backend cannot scale or you exceed AWS quotas:

```text
429 Too Many Requests

↓

Client Errors
```

Understanding quotas prevents unexpected outages.

---

# Types of Limits

API Gateway limits fall into several categories.

```text
API Gateway

│

├── Request Limits

├── Payload Limits

├── Timeout Limits

├── Throttling Limits

├── Resource Limits

├── Integration Limits

└── Account Limits
```

---

# Soft Limits vs Hard Limits

AWS defines two types of quotas.

## Soft Limits

Can be increased through AWS Support.

Examples:

- Request rate
- API count
- Custom domains

---

## Hard Limits

Cannot be increased.

Examples:

- Maximum timeout
- Maximum payload size
- Maximum stage variables

Application architecture must work within these constraints.

---

# Request Rate Limits

API Gateway supports very high request volumes.

Example:

```text
Clients

↓

API Gateway

↓

Thousands of Requests/sec
```

Account-level quotas help prevent accidental overload.

AWS automatically manages infrastructure scaling.

---

# Throttling Limits

API Gateway protects backend services using throttling.

```text
Client

↓

1000 Requests/sec

↓

Allowed

-------------------

5000 Requests/sec

↓

429

Too Many Requests
```

Throttling prevents backend overload.

---

# Burst Limit

Traffic often arrives in bursts.

Example:

```text
100

100

100

500

100
```

API Gateway allows short bursts before enforcing sustained rate limits.

---

# Payload Size Limit

Requests and responses have maximum payload sizes.

Large payload:

```text
50 MB

↓

Rejected
```

Instead:

```text
Upload

↓

Amazon S3

↓

API

↓

Reference
```

Large files should not pass through API Gateway.

---

# Timeout Limit

API Gateway waits only a limited time for backend responses.

```text
Client

↓

API Gateway

↓

Lambda

↓

Response
```

If the backend exceeds the maximum integration timeout:

```text
504 Gateway Timeout
```

Long-running operations should use asynchronous architectures.

---

# Header Size Limits

HTTP headers also have limits.

Example:

```text
Authorization

Cookies

Custom Headers
```

Avoid storing excessive information inside headers.

---

# URL Length

Very long URLs can cause request failures.

Instead of:

```text
GET

/users?id=1&...

(Thousands of characters)
```

Use:

```http
POST
```

with a request body.

---

# Resource Limits

An API can contain many:

- Resources
- Methods
- Models
- Stages

Large enterprise APIs should be organized carefully to remain maintainable.

---

# Stage Limits

Typical environments:

```text
Development

↓

Testing

↓

Staging

↓

Production
```

Avoid creating unnecessary stages.

---

# Custom Domain Limits

Organizations often use:

```text
api.company.com

payments.company.com

users.company.com
```

Plan domain usage carefully across environments.

---

# Lambda Integration Limits

Even if API Gateway scales automatically:

```text
API Gateway

↓

Lambda
```

Lambda concurrency limits may become the bottleneck.

Monitor:

- Concurrent executions
- Cold starts
- Reserved concurrency

---

# Database Limits

Another common bottleneck:

```text
API Gateway

↓

Lambda

↓

Database Connections
```

API Gateway can process more requests than the database can handle.

Use:

- Connection pooling
- RDS Proxy
- DynamoDB
- Redis

to improve scalability.

---

# CloudWatch Limits

Logging every request generates:

```text
Millions of Log Events
```

Consider:

- Log retention
- Sampling
- Appropriate log levels

to control costs and storage.

---

# X-Ray Sampling

Tracing every request:

```text
1 Million Requests

↓

1 Million Traces
```

Instead:

```text
Sample

↓

Representative Requests
```

Sampling reduces operational overhead.

---

# Designing Around Limits

Instead of increasing quotas, redesign the architecture.

Examples:

```text
Large Payload

↓

Amazon S3
```

```text
Long Processing

↓

Amazon SQS

↓

Lambda
```

```text
High Read Traffic

↓

API Cache

↓

CloudFront
```

Good architecture is often more effective than requesting quota increases.

---

# Common Bottlenecks

```text
API Gateway

↓

Lambda Concurrency

↓

Database

↓

Third-party APIs
```

API Gateway is rarely the limiting component.

Backend systems usually require greater attention.

---

# Monitoring Quotas

Monitor:

- Request Count
- Throttle Count
- Latency
- Integration Latency
- Lambda Concurrency
- Database Connections

CloudWatch helps detect quota-related issues before they become outages.

---

# Scaling Strategy

```text
Traffic

↓

API Gateway

↓

Lambda Auto Scaling

↓

Database Scaling

↓

Monitoring
```

Every layer should scale together.

---

# Real-World Example

A ticket booking application experiences heavy traffic during a concert launch.

Traffic:

```text
500,000 Requests/minute
```

Instead of increasing quotas:

- Enable API Gateway Cache
- Add CloudFront
- Scale Lambda
- Use DynamoDB
- Queue background work with SQS

The platform handles the surge without downtime.

---

# Best Practices

- Design APIs assuming quotas exist.
- Use API Gateway caching to reduce backend load.
- Store large files in Amazon S3 instead of sending them through APIs.
- Keep request payloads small.
- Avoid long-running synchronous requests.
- Monitor throttling and latency using CloudWatch.
- Scale backend services together with API Gateway.
- Request quota increases only after optimizing the architecture.

---

# Common Interview Questions

### Why should API Gateway limits be understood?

Because production systems must be designed to operate reliably within AWS service quotas while remaining scalable and cost-efficient.

---

### Can all API Gateway limits be increased?

No.

Some quotas are soft limits that can be increased through AWS Support, while others are hard architectural limits.

---

### What usually becomes the bottleneck before API Gateway?

Backend systems such as:

- Lambda concurrency
- Database connections
- Third-party APIs

are more commonly the limiting factors.

---

### How should large file uploads be handled?

Upload files directly to Amazon S3 using pre-signed URLs instead of sending large payloads through API Gateway.

---

### How do you handle long-running API requests?

Use asynchronous architectures with services such as Amazon SQS, EventBridge, or Step Functions instead of waiting for a synchronous response.

---

# Key Takeaways

- API Gateway has both soft and hard service quotas that influence API design.
- Request throttling, payload size, and timeout limits are common considerations in production systems.
- Backend services usually become bottlenecks before API Gateway itself.
- Good architecture—using caching, asynchronous processing, S3, and scalable backends—is more effective than simply requesting quota increases.
- Continuous monitoring of quotas and performance metrics is essential for building resilient, production-ready APIs.