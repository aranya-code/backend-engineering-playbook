# 07- Cost Problems

# Overview

One of the biggest advantages of AWS Lambda is its pay-per-use pricing model. However, poor architecture, inefficient code, recursive invocations, excessive logging, or incorrect scaling configurations can significantly increase costs.

Unlike traditional servers where costs are relatively predictable, Lambda costs scale with usage. This means that application bugs or architectural mistakes can quickly generate unexpectedly large AWS bills.

This chapter explains the most common Lambda cost problems, how to investigate them, and how to optimize serverless applications for cost efficiency.

---

# How Lambda Pricing Works

Lambda pricing is primarily based on:

- Number of requests
- Execution duration
- Allocated memory
- Provisioned Concurrency
- Ephemeral Storage (above free tier)

```
Request

↓

Execution

↓

Duration

↓

Memory

↓

Cost
```

---

# Cost Investigation Workflow

Whenever AWS costs increase unexpectedly:

```
Billing Alarm

↓

Cost Explorer

↓

CloudWatch Metrics

↓

Lambda Metrics

↓

CloudWatch Logs

↓

Root Cause

↓

Optimization
```

Always identify **which function** is responsible before making changes.

---

# Common Cost Problems

Typical production cost issues include:

- Recursive invocations
- High invocation count
- Long execution duration
- Excessive memory allocation
- Provisioned Concurrency misuse
- Large CloudWatch logs
- Infinite retries
- Database connection delays
- Unoptimized code
- Excessive data transfer

---

# Problem: Sudden Spike in Invocations

Example

```
Yesterday

↓

100,000 Invocations

Today

↓

8,500,000 Invocations
```

---

## Investigation

Review

```
CloudWatch

↓

Invocations

↓

Event Source

↓

Application Logs
```

---

## Possible Causes

- Infinite retry
- Recursive invocation
- EventBridge loop
- S3 trigger loop
- SNS feedback loop

---

# Problem: Recursive Invocation

Example

```
S3 Upload

↓

Lambda

↓

Write to Same Bucket

↓

Lambda

↓

Write Again

↓

Infinite Loop
```

---

## Resolution

- Separate source and destination buckets
- Add event filters
- Disable trigger immediately
- Set Reserved Concurrency to **0**
- Fix architecture

---

# Problem: Excessive Execution Duration

Example

```
Average Duration

200 ms

↓

4.5 Seconds
```

Longer execution directly increases cost.

---

## Investigation

Use

```
CloudWatch Duration

↓

AWS X-Ray

↓

Application Logs
```

---

## Possible Causes

- Slow SQL
- External APIs
- Large payloads
- Inefficient code
- Blocking operations

---

# Problem: Overallocated Memory

Example

```
Memory

4096 MB

↓

Average Usage

400 MB
```

The function is paying for unused resources.

---

## Resolution

Benchmark memory.

```
128 MB

↓

256 MB

↓

512 MB

↓

1024 MB
```

Choose the best balance between performance and cost.

---

# Problem: Underallocated Memory

Sometimes lower memory costs **more**.

Example

```
256 MB

↓

5 Seconds

↓

Higher Cost
```

Compared with

```
1024 MB

↓

800 ms

↓

Lower Cost
```

Always benchmark.

---

# Problem: Provisioned Concurrency Running Continuously

Example

```
Provisioned Concurrency

↓

24 Hours

↓

Low Traffic
```

You're paying even when users are inactive.

---

## Resolution

Use

- Auto Scaling
- Scheduled Scaling
- Business-hour scheduling

---

# Problem: Excessive CloudWatch Logs

Example

```python
logger.info(event)
```

Large payloads generate:

- More storage
- Higher ingestion costs
- Difficult debugging

---

## Better

```python
logger.info(
    "Order Processed",
    extra={
        "order_id": order_id
    }
)
```

Use structured logging.

---

# Problem: Excessive Retries

Architecture

```
SNS

↓

Lambda

↓

Failure

↓

Retry

↓

Failure

↓

Retry
```

Retries increase:

- Compute cost
- Log volume
- Downstream traffic

---

## Resolution

- Dead Letter Queue
- Lambda Destinations
- Idempotency
- Better error handling

---

# Problem: Large Deployment Package

Large packages increase:

- Cold start duration
- Execution time
- Build time

Remove

- Unused libraries
- Test dependencies
- Development tools

---

# Problem: Database Connection Overhead

Example

```
Lambda

↓

Open Connection

↓

Query

↓

Close

↓

Repeat
```

Every invocation repeats expensive work.

---

## Better

```
Lambda

↓

RDS Proxy

↓

Aurora
```

Connection pooling reduces both latency and cost.

---

# Problem: External API Delays

Architecture

```
Lambda

↓

Third-party API

↓

10 Seconds
```

Lambda continues billing while waiting.

---

## Better

```
Lambda

↓

Amazon SQS

↓

Worker Lambda

↓

Third-party API
```

Respond immediately and process asynchronously.

---

# Problem: High Error Rate

Failures still incur execution charges.

Example

```
Lambda

↓

Exception

↓

Retry

↓

More Cost
```

Investigate recurring failures quickly.

---

# Problem: Excessive Data Transfer

Large payloads increase:

- Execution duration
- Network transfer
- Processing cost

Instead of

```
Client

↓

API Gateway

↓

200 MB File
```

Use

```
Client

↓

Pre-signed URL

↓

Amazon S3

↓

Lambda
```

---

# Using AWS Cost Explorer

Useful views

- Daily Lambda Cost
- Cost by Function
- Cost by Region
- Cost by Tag

Track trends rather than reacting only to invoices.

---

# Using AWS Budgets

Configure

```
Monthly Budget

↓

Threshold

↓

SNS

↓

Email Notification
```

Set alerts at:

- 50%
- 80%
- 100%

---

# CloudWatch Metrics

Monitor

- Invocations
- Duration
- Errors
- Concurrent Executions
- Throttles

Unexpected changes often indicate cost issues.

---

# Cost Optimization Checklist

Before production

- [ ] Benchmark memory
- [ ] Remove unused dependencies
- [ ] Enable structured logging
- [ ] Configure Budgets
- [ ] Configure Billing Alarms
- [ ] Use RDS Proxy
- [ ] Review retries
- [ ] Avoid recursive invocations
- [ ] Enable CloudWatch monitoring
- [ ] Review Provisioned Concurrency

---

# Common Cost Mistakes

❌ Provisioned Concurrency enabled 24×7

❌ Recursive Lambda triggers

❌ Logging entire payloads

❌ Excessive retries

❌ Large deployment packages

❌ Unoptimized SQL queries

❌ Direct file uploads through API Gateway

❌ Never reviewing Cost Explorer

---

# Best Practices

✅ Use AWS Cost Explorer regularly.

✅ Configure AWS Budgets.

✅ Enable billing alarms.

✅ Benchmark memory settings.

✅ Keep execution time low.

✅ Use asynchronous processing.

✅ Store large files in S3.

✅ Continuously review CloudWatch metrics.

---

# Real-World Production Example

An image processing system suddenly generated an unusually high AWS bill.

```
User Upload

↓

Amazon S3

↓

Lambda

↓

Processed Image

↓

Same Bucket

↓

Lambda

↓

Infinite Loop
```

The Lambda function wrote processed images back into the same bucket that triggered it, creating a recursive invocation loop.

Resolution:

- Disabled the trigger.
- Set Reserved Concurrency to **0**.
- Introduced a separate destination bucket.
- Added S3 prefix filters.

The incident stopped immediately, and daily Lambda costs returned to normal.

---

# Senior Backend Engineering Perspective

Cost optimization is an architectural responsibility, not merely a financial exercise. Senior engineers continuously balance performance, scalability, and operational requirements against infrastructure costs. They monitor spending proactively, investigate anomalies using metrics and billing tools, and design systems that scale efficiently without wasting compute resources.

Effective cost optimization improves not only cloud spending but also application performance, operational reliability, and long-term maintainability.

---

# Key Takeaways

- Lambda costs are driven primarily by request volume, execution duration, memory allocation, and Provisioned Concurrency.
- Recursive invocations, excessive logging, retries, and slow downstream services are common causes of unexpected costs.
- AWS Cost Explorer, AWS Budgets, CloudWatch Metrics, and Billing Alarms are essential tools for cost monitoring.
- Memory benchmarking and asynchronous architectures often reduce both latency and cost.
- Cost optimization should be an ongoing engineering practice supported by continuous monitoring and architectural improvements.