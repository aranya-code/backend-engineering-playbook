# Performance & Scaling

## Overview

Performance and scalability are among the most important topics in Senior Backend Developer interviews.

Interviewers want to know whether you understand:

- How API Gateway scales
- How to optimize latency
- How to reduce costs
- How to handle millions of requests
- How to identify performance bottlenecks
- How to design resilient production systems

Unlike coding questions, these interviews focus on architectural decisions and trade-offs rather than memorizing AWS features.

---

# Question 1

## Does API Gateway scale automatically?

### Answer

Yes.

Amazon API Gateway is a fully managed service that automatically scales based on incoming traffic.

```text
Users

↓

API Gateway

↓

Backend
```

There are no API Gateway servers to provision or auto scaling groups to configure.

However, the backend services (Lambda, ECS, EC2, databases) must also be capable of handling the increased load.

---

## Follow-up

Can API Gateway become the bottleneck?

Usually no.

In most production systems the bottleneck is:

- Lambda
- Database
- ECS
- External APIs

rather than API Gateway itself.

---

# Question 2

## How would you reduce API latency?

### Answer

I would investigate latency layer by layer.

```text
Client

↓

CloudFront

↓

API Gateway

↓

Lambda

↓

Database
```

Common optimizations include:

- Enable CloudFront
- Enable API caching
- Optimize SQL queries
- Add database indexes
- Reduce Lambda cold starts
- Compress responses
- Paginate large datasets

---

## Follow-up

Which CloudWatch metrics would you check?

I would compare:

- Latency
- IntegrationLatency

If IntegrationLatency is high, the backend is likely responsible.

---

# Question 3

## What is the difference between Latency and IntegrationLatency?

### Answer

**Latency**

Measures:

```text
Client

↓

API Gateway

↓

Backend

↓

Client
```

Total request time.

---

**IntegrationLatency**

Measures:

```text
API Gateway

↓

Backend

↓

API Gateway
```

Only backend processing time.

---

## Interview Tip

If Latency is much higher than IntegrationLatency, investigate API Gateway processing such as:

- Authorizers
- Mapping Templates
- Request Validation

---

# Question 4

## How would you handle one million requests per day?

### Answer

Example architecture:

```text
Users

↓

CloudFront

↓

API Gateway

↓

Lambda

↓

Redis

↓

Aurora
```

Optimizations:

- CloudFront caching
- API Gateway caching
- Redis
- Database indexing
- Pagination
- Compression
- Read replicas

---

## Follow-up

Would you scale Lambda?

Normally Lambda scales automatically.

The database usually becomes the bottleneck first.

---

# Question 5

## What causes API Gateway throttling?

### Answer

Typical causes:

- Rate limit exceeded
- Burst limit exceeded
- Usage Plan quota exceeded

Response:

```http
429 Too Many Requests
```

---

## Solution

- Increase quotas
- Implement retries
- Use exponential backoff
- Enable caching

---

# Question 6

## How would you reduce Lambda cold starts?

### Answer

Several techniques help reduce cold start latency.

- Provisioned Concurrency
- Smaller deployment package
- Fewer dependencies
- Higher memory allocation
- Avoid unnecessary VPC configuration

---

## Follow-up

When is Provisioned Concurrency worth the cost?

For:

- User-facing APIs
- Low-latency systems
- Financial applications
- Healthcare applications

---

# Question 7

## Would you enable API Gateway caching?

### Answer

Yes, for read-heavy workloads.

Examples:

- Product catalog
- Country list
- Configuration
- Public metadata

Avoid caching:

- Frequently changing data
- Personalized responses

---

# Question 8

## How would you improve database performance?

### Answer

I would:

- Add indexes
- Optimize SQL
- Use connection pooling
- Introduce Redis
- Enable read replicas
- Paginate results

Scaling the API without optimizing the database simply moves the bottleneck.

---

# Question 9

## How would you optimize large API responses?

### Answer

Avoid returning everything.

Instead use:

- Pagination
- Filtering
- Compression
- Partial responses

Example:

Instead of:

```text
10,000 Products
```

Return:

```text
100 Products

+

Next Page Token
```

---

# Question 10

## Why use CloudFront with API Gateway?

### Answer

CloudFront provides:

- Edge caching
- Lower latency
- DDoS mitigation
- Reduced API Gateway requests

This improves both performance and cost.

---

# Question 11

## How would you scale container-based APIs?

### Answer

Architecture:

```text
CloudFront

↓

API Gateway

↓

VPC Link

↓

ALB

↓

ECS

↓

Redis

↓

Aurora
```

Scale:

- ECS Tasks
- ALB
- Database
- Cache

---

# Question 12

## How would you optimize external API calls?

### Answer

External services are unpredictable.

I would implement:

- Timeouts
- Retries
- Exponential Backoff
- Circuit Breaker
- Response Caching

Never assume third-party services are always available.

---

# Question 13

## What CloudWatch metrics do you monitor?

### Answer

Important metrics:

- Count
- Latency
- IntegrationLatency
- 4XXError
- 5XXError
- CacheHitCount
- CacheMissCount
- ThrottleCount

These provide a good overview of API health.

---

# Question 14

## How would you identify a performance bottleneck?

### Answer

Workflow:

```text
CloudWatch

↓

Latency

↓

IntegrationLatency

↓

X-Ray

↓

Backend

↓

Database
```

AWS X-Ray helps determine exactly where time is being spent.

---

# Question 15

## How would you design a highly scalable API?

### Answer

Example:

```text
Users

↓

CloudFront

↓

API Gateway

↓

Lambda

↓

SQS

↓

Workers

↓

Database
```

Characteristics:

- Stateless APIs
- Auto Scaling
- Async processing
- Caching
- Monitoring

---

# Scenario 1

## Your API suddenly becomes slow after deployment.

What would you do?

### Answer

I would investigate in this order:

1. CloudWatch Metrics
2. CloudWatch Logs
3. AWS X-Ray
4. Lambda Duration
5. Database queries
6. External API calls
7. Recent deployment changes

I would avoid rolling back immediately without identifying the root cause.

---

# Scenario 2

## Users receive intermittent 504 Gateway Timeout errors.

How would you troubleshoot?

### Answer

I would check:

- Backend latency
- Lambda duration
- ECS health
- Database performance
- Third-party APIs
- CloudWatch Metrics
- X-Ray traces

---

# Scenario 3

## Your API receives ten times the normal traffic during a sale.

How would you prepare?

### Answer

Before the event:

- Increase quotas if necessary
- Enable CloudFront caching
- Enable API Gateway caching
- Configure CloudWatch alarms
- Perform load testing
- Scale backend services
- Verify database capacity

Preparation is more effective than reacting after failures occur.

---

# Scenario 4

## Which component usually becomes the bottleneck first?

### Answer

In most production systems:

```text
Database
```

is the first bottleneck.

API Gateway and Lambda generally scale well, but databases require careful optimization.

---

# Rapid Fire Questions

- Latency vs IntegrationLatency?
- What causes 429?
- Why use CloudFront?
- Why cache APIs?
- Why paginate?
- Lambda cold start?
- Redis or API Gateway cache?
- Why use Provisioned Concurrency?
- How do you reduce response size?
- Why use X-Ray?

---

# Senior Interview Tips

Interviewers are looking for engineering judgment.

A strong answer explains:

- Where the bottleneck is likely to occur.
- How you would measure it.
- How you would optimize it.
- The trade-offs between cost and performance.

For example:

Instead of saying:

> "I would add more servers."

Say:

> "I would first identify whether the bottleneck is API Gateway, Lambda, the database, or an external dependency using CloudWatch Metrics and X-Ray. Only after identifying the bottleneck would I scale the appropriate component."

That demonstrates a production mindset.

---

# Key Takeaways

- API Gateway automatically scales, but backend services and databases must also be designed to scale.
- CloudWatch Metrics and AWS X-Ray are essential for identifying performance bottlenecks.
- CloudFront, API Gateway caching, Redis, and database optimization significantly improve API performance.
- High-performance architectures rely on stateless services, asynchronous processing, efficient data access, and continuous monitoring.
- Senior interview answers should emphasize measurement, trade-offs, and root cause analysis rather than simply adding more infrastructure.