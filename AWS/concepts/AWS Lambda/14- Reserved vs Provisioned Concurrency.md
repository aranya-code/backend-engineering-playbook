# 14- Reserved vs Provisioned Concurrency

# Introduction

AWS Lambda automatically scales to handle incoming requests. However, in production systems, uncontrolled scaling can lead to:

- Database connection exhaustion
- API rate limit violations
- Increased cold starts
- Unpredictable latency
- Resource starvation for critical services

AWS provides two concurrency controls to solve these problems:

- Reserved Concurrency
- Provisioned Concurrency

Although they sound similar, they solve **completely different problems**.

A senior backend engineer should clearly understand when to use each and the trade-offs involved.

---

# Understanding Default Concurrency

By default, all Lambda functions share the Regional concurrency pool.

Example:

```
Regional Limit

1000 Concurrent Executions

│

├── Payment Service

├── Order Service

├── User Service

├── Image Processing

└── Email Service
```

Every function competes for the same pool.

---

# Problem Without Reserved Concurrency

Imagine:

```
Regional Limit

1000
```

Suddenly,

```
Image Processing

↓

Consumes 1000 Concurrency
```

Now,

```
Payment Service

↓

No Capacity

↓

Throttled
```

One noisy application can impact every Lambda in the Region.

---

# Reserved Concurrency

Reserved Concurrency reserves a fixed number of concurrent executions for a Lambda function.

It guarantees that:

- This function always has available capacity.
- Other functions cannot consume that reserved capacity.

---

# Architecture

```
Regional Limit

1000

│

├── Payment API

│      Reserved = 300

│

└── Remaining Pool

700
```

No other function can use the reserved 300 slots.

---

# Reserved Concurrency Guarantees

Suppose:

```
Reserved = 200
```

Then:

```
Payment Lambda

↓

Always Has

200 Slots
```

Even if every other Lambda is busy.

---

# Reserved Concurrency Also Limits Scaling

Reserved Concurrency acts as both:

- Minimum guaranteed capacity
- Maximum allowed concurrency

Example:

```
Reserved = 100
```

Requests:

```
150
```

Result:

```
100 Running

50 Throttled
```

The function cannot exceed its reserved limit.

---

# Reserved Concurrency Example

```
Regional Limit = 1000

Order Service = Reserved 300

User Service = Reserved 200

Remaining Pool = 500
```

If Order Service receives:

```
100 Requests
```

Only 100 slots are used.

The remaining reserved capacity remains unavailable to other functions.

---

# Reserved Concurrency Use Cases

Ideal for:

- Payment APIs
- Authentication services
- Database protection
- Third-party API integrations
- Mission-critical microservices

---

# Setting Reserved Concurrency

AWS Console:

```
Lambda

↓

Configuration

↓

Concurrency

↓

Reserved Concurrency
```

AWS CLI:

```bash
aws lambda put-function-concurrency \
    --function-name payment-service \
    --reserved-concurrent-executions 200
```

---

# Provisioned Concurrency

Provisioned Concurrency solves a different problem.

It keeps Lambda execution environments initialized and ready to process requests.

Result:

```
No Cold Start
```

---

# Architecture

Without Provisioned Concurrency

```
Request

↓

Cold Start

↓

Handler
```

With Provisioned Concurrency

```
Initialized Environment

↓

Request

↓

Handler Immediately
```

---

# Provisioned Concurrency Lifecycle

```
Provision Environment

↓

Initialize Runtime

↓

Load Code

↓

Wait

↓

Incoming Request

↓

Immediate Execution
```

Initialization happens before traffic arrives.

---

# Warm Environment Pool

Example:

```
Provisioned = 50

↓

50 Warm Environments

↓

Ready Immediately
```

---

# Cold Start Comparison

Without Provisioned Concurrency

```
User

↓

Cold Start

↓

500 ms

↓

Response
```

With Provisioned Concurrency

```
User

↓

Warm Environment

↓

20 ms

↓

Response
```

---

# Scaling Beyond Provisioned Capacity

Suppose:

```
Provisioned = 100

Requests = 150
```

Result:

```
100 Warm Starts

50 Cold Starts
```

Provisioned Concurrency eliminates cold starts only for the environments it pre-initializes.

---

# Reserved vs Provisioned

Reserved controls:

```
Capacity
```

Provisioned controls:

```
Latency
```

These are different concerns.

---

# Combining Both

Production architecture:

```
Reserved = 500

Provisioned = 100
```

Meaning:

```
100

↓

Always Warm

------------------

Remaining 400

↓

Scale Normally
```

Very common for production APIs.

---

# Comparison Table

| Feature | Reserved Concurrency | Provisioned Concurrency |
|----------|----------------------|-------------------------|
| Guarantees Capacity | ✅ | ❌ |
| Eliminates Cold Starts | ❌ | ✅ |
| Prevents Other Functions from Using Capacity | ✅ | ❌ |
| Limits Maximum Scaling | ✅ | ❌ |
| Additional Cost | No | Yes |
| Best For | Protecting Capacity | Low Latency APIs |

---

# Cost Comparison

Reserved Concurrency

```
No Additional Charge
```

You pay only for:

- Requests
- Execution duration

Provisioned Concurrency

Additional charges apply for:

- Provisioned environments
- Compute duration while warm
- Normal Lambda invocations

---

# Example

Payment API

Requirements:

- Maximum latency < 50 ms
- 200 concurrent users
- Business critical

Solution:

```
Reserved = 300

Provisioned = 100
```

---

# Reserved Concurrency for Database Protection

Database supports:

```
100 Connections
```

Lambda:

```
Reserved = 80
```

Now Lambda cannot create more than 80 concurrent database sessions.

---

# Provisioned Concurrency for Login API

Users expect:

```
Fast Login

↓

No Cold Starts
```

Solution:

```
Provisioned Concurrency

↓

Warm Environments

↓

Immediate Authentication
```

---

# Auto Scaling Provisioned Concurrency

Provisioned Concurrency can scale automatically using:

```
Application Auto Scaling

↓

CloudWatch Metrics

↓

Increase Provisioned Capacity
```

Useful for predictable traffic patterns.

---

# Common Mistakes

## Using Reserved to Remove Cold Starts

Incorrect.

Reserved Concurrency does **not** keep execution environments warm.

Cold starts still occur.

---

## Using Provisioned to Protect Databases

Incorrect.

Provisioned Concurrency reduces latency but does not limit scaling.

Database overload can still occur.

---

## Confusing Capacity with Performance

Remember:

```
Reserved

↓

Capacity Management
```

```
Provisioned

↓

Performance Optimization
```

---

# Best Practices

✅ Use Reserved Concurrency to protect downstream systems.

✅ Use Provisioned Concurrency for latency-sensitive APIs.

✅ Combine both for critical production services.

✅ Monitor CloudWatch ConcurrentExecutions.

✅ Benchmark cold start impact before enabling Provisioned Concurrency.

---

# Real-World Architecture

```
Users

↓

CloudFront

↓

API Gateway

↓

Lambda

Reserved = 500

Provisioned = 100

↓

RDS Proxy

↓

Amazon RDS
```

Benefits:

- No cold starts for common traffic
- Database protection
- Predictable latency
- Automatic scaling

---

# Senior Backend Engineering Perspective

Reserved Concurrency and Provisioned Concurrency address different operational challenges.

Reserved Concurrency is primarily a **resource management and protection mechanism**. It prevents noisy-neighbor problems and safeguards downstream services by limiting how much a function can scale.

Provisioned Concurrency is a **performance optimization feature**. It pre-initializes execution environments to eliminate cold starts for latency-sensitive workloads.

In enterprise systems, these features are often combined. For example, a payment API may reserve concurrency to protect the database while using provisioned concurrency to ensure fast response times during peak traffic.

Choosing the right configuration depends on application latency requirements, traffic patterns, backend capacity, and cost considerations.

---

# Interview Questions

### Beginner

- What is Reserved Concurrency?
- What is Provisioned Concurrency?
- Why are they different?

### Intermediate

- Does Reserved Concurrency eliminate cold starts?
- Can Provisioned Concurrency prevent throttling?
- What happens when requests exceed provisioned capacity?

### Senior

- How would you protect a database from Lambda traffic spikes?
- When would you combine Reserved and Provisioned Concurrency?
- How would you reduce cold starts without significantly increasing costs?
- How would you configure concurrency for a payment API serving millions of users?

---

# Key Takeaways

- Reserved Concurrency guarantees execution capacity for a function while also limiting its maximum concurrency.
- Provisioned Concurrency pre-initializes execution environments to reduce or eliminate cold starts.
- Reserved Concurrency focuses on **capacity management**, whereas Provisioned Concurrency focuses on **latency optimization**.
- Combining both features provides predictable performance and controlled scaling for mission-critical workloads.
- Selecting the appropriate concurrency strategy requires balancing latency, scalability, backend capacity, and operational cost.