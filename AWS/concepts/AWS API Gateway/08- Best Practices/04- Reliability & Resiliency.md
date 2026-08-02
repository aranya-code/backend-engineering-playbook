# Reliability & Resiliency

## Overview

A production API should continue operating even when individual components fail.

Reliability ensures that an API consistently performs its intended function, while resiliency ensures the system can recover gracefully from failures.

In distributed systems, failures are inevitable:

- Network interruptions
- Availability Zone failures
- Region failures
- Database outages
- Lambda failures
- Container crashes
- Third-party API outages

A well-designed API anticipates these failures and minimizes their impact on users.

---

# Reliability vs Resiliency

**Reliability**

```text
System

↓

Works Correctly

↓

Consistent Results
```

Focus:

- Stability
- Correctness
- Predictability

---

**Resiliency**

```text
Failure

↓

Recover

↓

Continue Serving Users
```

Focus:

- Recovery
- Fault tolerance
- Graceful degradation

---

# Design for Failure

One of AWS's core architectural principles is:

```text
Assume

↓

Everything

↓

Will Fail
```

Never assume:

- Database is always available
- Network is always reliable
- Third-party APIs never fail

Instead, build systems that continue operating despite failures.

---

# Eliminate Single Points of Failure

Avoid:

```text
Client

↓

API Gateway

↓

One EC2 Instance
```

If the instance fails:

```text
Entire API

↓

Unavailable
```

Instead:

```text
API Gateway

↓

Load Balancer

↓

Multiple Instances
```

---

# Multi-AZ Deployment

Deploy workloads across multiple Availability Zones.

```text
API Gateway

↓

ALB

↓

AZ-1

↓

ECS Tasks

-------------------

AZ-2

↓

ECS Tasks
```

If one Availability Zone fails, traffic is routed to healthy resources.

---

# Multi-Region Deployment

For mission-critical systems:

```text
Route 53

↓

Region A

↓

API Gateway

-------------------

Region B

↓

API Gateway
```

Traffic can fail over automatically.

---

# Stateless Services

Stateless applications recover more easily.

Good:

```text
Request

↓

Process

↓

Response
```

Avoid:

```text
Server Memory

↓

Session Data
```

Store state in:

- Redis
- DynamoDB
- Aurora

---

# Auto Scaling

Unexpected traffic spikes should not cause outages.

```text
Traffic

↓

Auto Scaling

↓

More Capacity
```

Auto Scaling applies to:

- ECS
- EC2
- Lambda Concurrency

---

# Health Checks

Health checks identify failed instances.

```text
Load Balancer

↓

Health Check

↓

Healthy?

↓

Yes → Route Traffic

No → Remove Instance
```

Only healthy targets receive requests.

---

# Timeouts

Every external dependency should have a timeout.

Bad:

```text
Wait Forever
```

Good:

```text
5 Second Timeout

↓

Fail Fast
```

Timeouts prevent thread exhaustion.

---

# Retries

Temporary failures may succeed after retrying.

```text
Request

↓

Failure

↓

Retry

↓

Success
```

Use retries only for transient failures.

---

# Exponential Backoff

Avoid retrying immediately.

Instead:

```text
Retry 1

↓

1 Second

↓

Retry 2

↓

2 Seconds

↓

Retry 3

↓

4 Seconds
```

Exponential backoff prevents overwhelming downstream systems.

---

# Circuit Breaker Pattern

If a dependency keeps failing:

```text
API

↓

Circuit Breaker

↓

Service
```

After repeated failures:

```text
Circuit Open

↓

Reject Requests

↓

Recover Later
```

Benefits:

- Protects downstream services
- Improves overall stability

---

# Bulkhead Pattern

Isolate independent workloads.

Instead of:

```text
One Shared Thread Pool
```

Use:

```text
Orders

↓

Dedicated Resources

-------------------

Payments

↓

Dedicated Resources
```

A failure in one service does not impact others.

---

# Graceful Degradation

If a non-critical service fails:

```text
Recommendation Service

↓

Unavailable
```

Continue serving:

```text
Product Page

↓

Without Recommendations
```

Partial functionality is better than total failure.

---

# Idempotency

Clients may retry requests.

Example:

```text
POST /payments
```

Use:

```text
Idempotency-Key
```

Multiple retries should create only one payment.

---

# Queue Long-Running Work

Instead of:

```text
Client

↓

Wait 60 Seconds
```

Use:

```text
Client

↓

API Gateway

↓

Amazon SQS

↓

Worker

↓

Response Later
```

Return:

```http
202 Accepted
```

---

# Event-Driven Recovery

Use asynchronous messaging.

```text
API

↓

EventBridge

↓

Consumers
```

or

```text
API

↓

Amazon SNS

↓

Subscribers
```

Services become loosely coupled.

---

# Database Reliability

Improve database availability using:

- Multi-AZ deployments
- Read replicas
- Automatic backups
- Point-in-Time Recovery (PITR)

Avoid relying on a single database instance.

---

# Caching for Resiliency

```text
Client

↓

API

↓

Redis

↓

Database
```

If the database experiences temporary latency, cached responses may still be served.

---

# Handle Third-Party Failures

Example:

```text
API

↓

Payment Provider
```

Possible failures:

- Timeout
- Rate limiting
- Service outage

Implement:

- Timeouts
- Retries
- Circuit breakers
- Fallback responses

---

# Monitor Everything

Monitor:

- Error Rate
- Availability
- Latency
- Throttling
- CPU
- Memory
- Database Health

Use:

- CloudWatch
- AWS X-Ray
- CloudWatch Alarms

---

# Disaster Recovery

Prepare for catastrophic failures.

Example:

```text
Primary Region

↓

Unavailable

↓

Route 53

↓

Secondary Region
```

Recovery should be tested regularly.

---

# Backup Strategy

Regularly back up:

- Databases
- Configuration
- Infrastructure as Code
- Secrets
- Object Storage

Recovery procedures should be documented and tested.

---

# Production Reliability Architecture

```text
                   Client

                      │

                      ▼

                Amazon Route 53

                      │

                      ▼

                 CloudFront

                      │

                      ▼

                   AWS WAF

                      │

                      ▼

              Amazon API Gateway

                      │

              Auto Scaling Backend

          ┌────────────┼────────────┐

          ▼            ▼            ▼

     Lambda      ECS Service      EC2

          │

          ▼

    Redis Cache

          │

          ▼

 Aurora Multi-AZ Database
```

Every layer contributes to system reliability.

---

# Common Reliability Mistakes

Avoid:

- Single EC2 instances
- No Auto Scaling
- Missing health checks
- No timeout configuration
- Unlimited retries
- Shared databases for every service
- Long-running synchronous requests
- Ignoring disaster recovery planning

---

# Production Checklist

Before production:

- Multi-AZ deployment
- Auto Scaling enabled
- Health checks configured
- Retry strategy implemented
- Timeouts configured
- Circuit breaker implemented
- Idempotency supported
- Database backups enabled
- Monitoring configured
- Disaster recovery tested

---

# Common Interview Questions

### What is the difference between reliability and resiliency?

Reliability focuses on consistently delivering correct functionality, while resiliency focuses on recovering quickly from failures and continuing to serve users.

---

### Why should distributed systems use timeouts?

Timeouts prevent requests from waiting indefinitely for slow or unavailable services, allowing applications to fail fast and recover gracefully.

---

### What is the Circuit Breaker pattern?

A Circuit Breaker temporarily stops requests to an unhealthy dependency after repeated failures, preventing cascading failures and allowing the dependency time to recover.

---

### Why are idempotent APIs important for reliability?

Clients often retry requests after network failures. Idempotent APIs ensure repeated requests produce the same result, preventing duplicate operations such as multiple payments or orders.

---

### How do you improve the resiliency of an API?

Common techniques include:

- Multi-AZ deployments
- Auto Scaling
- Health checks
- Retries with exponential backoff
- Circuit breakers
- Stateless services
- Queue-based asynchronous processing
- Multi-Region disaster recovery
- Comprehensive monitoring

---

# Key Takeaways

- Reliability ensures APIs consistently deliver correct results, while resiliency enables systems to recover gracefully from failures.
- Design for failure by eliminating single points of failure and assuming infrastructure components can become unavailable.
- Multi-AZ deployments, Auto Scaling, health checks, retries, circuit breakers, and idempotency significantly improve system resilience.
- Asynchronous processing, caching, and event-driven architectures reduce the impact of downstream failures.
- Continuous monitoring, backups, and disaster recovery planning are essential for maintaining highly available production APIs.