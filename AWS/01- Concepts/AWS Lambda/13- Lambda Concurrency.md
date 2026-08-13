# 13- Lambda Concurrency

# Lambda Concurrency

Concurrency is one of the most important concepts in AWS Lambda. It determines how many function invocations can execute simultaneously.

Unlike traditional servers where requests share the same process or thread pool, Lambda creates multiple isolated execution environments to process requests in parallel.

Understanding concurrency is essential for designing scalable, resilient, and cost-effective serverless applications.

---

# What is Concurrency?

Concurrency is the number of Lambda function instances running at the same time.

Example:

```
One Request

↓

One Lambda Instance
```

```
100 Simultaneous Requests

↓

100 Lambda Execution Environments
```

Each environment processes one invocation at a time.

---

# Concurrency Formula

A useful approximation is:

```
Concurrency = Requests Per Second × Average Duration
```

Example:

```
100 Requests/Second

Average Duration = 2 Seconds

Concurrency = 200
```

AWS allocates approximately 200 execution environments.

---

# Example Timeline

Suppose a function takes 5 seconds.

```
Time 0

Request A

↓

Instance 1

--------------------

Time 1

Request B

↓

Instance 2

--------------------

Time 2

Request C

↓

Instance 3
```

Since each invocation is still running, Lambda creates additional environments.

---

# Concurrency vs Scaling

Traditional Application

```
Load Balancer

↓

EC2

↓

Threads
```

Lambda

```
Requests

↓

Lambda Service

↓

Execution Environment 1

Execution Environment 2

Execution Environment 3

Execution Environment N
```

AWS automatically scales the number of execution environments.

---

# Regional Concurrency Limit

Each AWS Region has a default concurrency quota.

Typical default:

```
1000 Concurrent Executions
```

This is a soft limit and can be increased through AWS Service Quotas.

Example:

```
Region

↓

Concurrency Pool

↓

1000
```

---

# Shared Regional Pool

All Lambda functions in a Region share the same concurrency pool unless Reserved Concurrency is configured.

Example:

```
Region Limit = 1000

Order Service = 300

Payment Service = 250

Image Processor = 450

Total = 1000
```

No additional invocations can start until capacity is available.

---

# Execution Environment Scaling

Suppose:

```
1000 Requests Arrive
```

AWS creates:

```
Execution Environment 1

Execution Environment 2

...

Execution Environment 1000
```

Each environment processes a single invocation.

---

# What Happens When the Limit is Reached?

Scenario:

```
Regional Limit = 1000

Current Executions = 1000

New Request Arrives
```

Result:

### Synchronous Invocation

```
Throttle

↓

HTTP 429
```

The caller receives a throttling error immediately.

### Asynchronous Invocation

```
Retry

↓

Retry Again

↓

Destination or DLQ
```

AWS retries according to the asynchronous retry policy.

---

# Burst Scaling

Lambda can rapidly create new execution environments during traffic spikes.

Example:

```
Normal Traffic

↓

20 Requests

↓

20 Environments

--------------------

Traffic Spike

↓

500 Requests

↓

Hundreds of New Environments
```

AWS manages this automatically.

---

# Concurrency Example

A payment API receives:

```
500 Requests/Second
```

Average execution time:

```
400 ms
```

Estimated concurrency:

```
500 × 0.4

=

200 Concurrent Executions
```

---

# Effect on Databases

Concurrency directly affects backend systems.

```
1000 Lambda Functions

↓

1000 Database Connections
```

If the database supports only 200 connections, failures occur.

Solutions include:

- Amazon RDS Proxy
- Connection pooling
- Reserved Concurrency
- SQS buffering

---

# Concurrency and SQS

Lambda polls SQS and scales consumers automatically.

```
SQS Queue

↓

Lambda Pollers

↓

Multiple Lambda Instances
```

Scaling depends on:

- Queue depth
- Batch size
- Maximum concurrency
- Reserved concurrency

---

# Concurrency and Kinesis

For Kinesis:

```
Shard

↓

One Concurrent Lambda Consumer
```

Increasing shards increases parallelism.

```
4 Shards

↓

4 Concurrent Lambda Invocations
```

---

# Concurrency and DynamoDB Streams

Like Kinesis:

```
One Shard

↓

One Concurrent Lambda
```

Ordering is preserved within each shard.

---

# Monitoring Concurrency

CloudWatch metrics:

```
ConcurrentExecutions

UnreservedConcurrentExecutions

Throttles

Invocations

Duration

Errors
```

Important metric:

```
ConcurrentExecutions
```

It shows how many execution environments are active.

---

# CloudWatch Example

```
ConcurrentExecutions

900

↓

950

↓

1000

↓

Throttles Increase
```

A clear sign that concurrency limits are being reached.

---

# Common Causes of High Concurrency

- Traffic spikes
- Long-running functions
- Infinite retries
- Large SQS backlogs
- Slow downstream services
- Database latency

---

# Reducing Concurrency

Options include:

- Reduce execution time
- Increase memory (more CPU)
- Batch messages
- Cache results
- Use asynchronous processing
- Introduce SQS buffering

---

# Common Mistakes

## Ignoring Backend Capacity

```
1000 Lambdas

↓

1000 Database Connections
```

Backend systems often become the bottleneck before Lambda.

---

## Long Execution Time

A function that runs for 30 seconds occupies a concurrency slot for the entire duration.

Reducing execution time frees capacity faster.

---

## Ignoring Throttles

Throttling is an early warning sign.

Always investigate:

- CloudWatch metrics
- Service Quotas
- Backend performance

---

# Best Practices

✅ Monitor `ConcurrentExecutions`.

✅ Design downstream services to handle Lambda scale.

✅ Use RDS Proxy for relational databases.

✅ Buffer burst traffic using SQS.

✅ Keep execution time as short as possible.

✅ Increase Service Quotas before expected traffic spikes.

---

# Senior Backend Engineering Perspective

Concurrency is not just about Lambda—it is about the capacity of the **entire system**.

A Lambda function can scale from one invocation to thousands within seconds, but databases, caches, third-party APIs, and legacy services often cannot.

Senior engineers design systems with controlled concurrency using techniques such as SQS buffering, RDS Proxy, caching, backpressure, and reserved concurrency. The goal is to allow Lambda to scale elastically while protecting downstream dependencies from overload.

---

# Interview Questions

### Beginner

- What is Lambda concurrency?
- How is concurrency calculated?
- What is the default regional concurrency limit?

### Intermediate

- What happens when concurrency limits are exceeded?
- How does Lambda scale with SQS?
- Why can high concurrency overload a database?

### Senior

- How would you prevent a Lambda-based application from exhausting database connections?
- How would you estimate concurrency requirements for a high-traffic API?
- How would you monitor and troubleshoot Lambda throttling?
- How would you design a system that safely handles sudden traffic spikes without overwhelming downstream services?

---

# Key Takeaways

- Concurrency represents the number of Lambda invocations executing simultaneously.
- AWS automatically creates new execution environments to handle concurrent requests, up to the configured regional quota.
- High concurrency can overwhelm downstream systems such as databases if not managed carefully.
- CloudWatch metrics like `ConcurrentExecutions` and `Throttles` are essential for monitoring scaling behavior.
- Effective concurrency management combines Lambda scaling with backend protection strategies such as RDS Proxy, SQS, batching, and caching.