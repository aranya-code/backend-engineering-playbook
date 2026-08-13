# 34- Lambda Production Scenarios

# Introduction

Real production environments rarely fail because of AWS Lambda itself. Instead, failures usually arise from interactions between services, infrastructure misconfigurations, unexpected traffic patterns, or application design issues.

Senior backend engineers are expected not only to identify these problems but also to resolve them systematically while minimizing customer impact.

This chapter presents realistic production scenarios that are commonly encountered in enterprise environments and frequently discussed during senior backend interviews.

Each scenario follows a structured approach:

```
Problem

↓

Symptoms

↓

Possible Root Causes

↓

Investigation

↓

Resolution

↓

Prevention
```

---

# Scenario 1 — API Suddenly Returns HTTP 502

## Problem

Users report that every API request suddenly returns **502 Bad Gateway**.

Architecture

```
Client

↓

API Gateway

↓

Lambda

↓

Response
```

---

## Symptoms

- HTTP 502
- API Gateway metrics show failures
- Lambda invocation count increases

---

## Possible Root Causes

- Invalid Lambda response
- Runtime exception
- Handler misconfiguration
- Timeout

---

## Investigation

Check

```
CloudWatch Logs

↓

Unhandled Exception
```

Verify Lambda response format.

Correct response:

```json
{
  "statusCode": 200,
  "body": "{}"
}
```

---

## Resolution

- Fix response object
- Correct exception handling
- Redeploy

---

## Prevention

- Integration testing
- API Gateway contract validation
- Canary deployment

---

# Scenario 2 — API Suddenly Becomes Slow

## Problem

Average response time increases from **250 ms** to **5 seconds**.

---

## Investigation

```
CloudWatch

↓

Duration

↓

AWS X-Ray

↓

Timeline
```

---

## Root Cause

Database query:

```
Lambda

↓

Aurora

↓

4.7 Seconds
```

Missing database index.

---

## Resolution

Create index.

Optimize query.

---

## Prevention

- Slow query monitoring
- Performance testing
- Database indexing strategy

---

# Scenario 3 — Too Many Database Connections

Architecture

```
1000 Lambda

↓

Aurora

↓

Connection Limit Reached
```

---

## Symptoms

```
Too many connections
```

---

## Root Cause

Each Lambda creates a new database connection.

---

## Resolution

```
Lambda

↓

RDS Proxy

↓

Aurora
```

Reuse database connections.

---

## Prevention

- RDS Proxy
- Connection pooling
- Reserved Concurrency

---

# Scenario 4 — Lambda Times Out

Error

```
Task timed out after 30 seconds
```

---

## Investigation

Review

- CloudWatch Duration
- Logs
- X-Ray

---

## Possible Causes

- External API
- Slow SQL
- Infinite loop
- Large file processing

---

## Resolution

- Optimize code
- Cache responses
- Increase timeout only when justified

---

# Scenario 5 — Lambda Cannot Access S3

Architecture

```
Lambda

↓

S3

❌
```

---

## Error

```
AccessDeniedException
```

---

## Investigation

Check

- IAM Role
- Bucket Policy
- KMS
- Region

---

## Resolution

Grant

```
s3:GetObject

s3:PutObject
```

---

## Prevention

Apply Least Privilege IAM.

---

# Scenario 6 — Lambda Inside VPC Has No Internet

Architecture

```
Lambda

↓

Private Subnet

↓

Internet

❌
```

---

## Investigation

Check

- NAT Gateway
- Route Tables
- Security Groups

---

## Resolution

```
Private Subnet

↓

Route Table

↓

NAT Gateway

↓

Internet Gateway
```

---

## Prevention

Validate networking before deployment.

---

# Scenario 7 — CloudWatch Costs Increase Rapidly

---

## Symptoms

Billing suddenly increases.

---

## Investigation

Review

```
CloudWatch Logs

↓

Log Volume
```

---

## Root Cause

Logging entire payloads.

Example

Bad

```python
logger.info(event)
```

---

## Resolution

Use structured logging.

```python
logger.info(
    "Order Created",
    extra={
        "order_id": order_id
    }
)
```

---

## Prevention

- Log levels
- Retention policies
- Log sampling

---

# Scenario 8 — Millions of Lambda Invocations Overnight

Architecture

```
Lambda

↓

S3 Upload

↓

Lambda

↓

S3 Upload

↓

Lambda
```

---

## Root Cause

Recursive invocation.

---

## Resolution

Immediately

```
Reserved Concurrency = 0
```

Disable trigger.

---

## Prevention

Separate buckets.

Filter events.

---

# Scenario 9 — Cold Starts Affect User Experience

Symptoms

```
First Request

↓

3 Seconds
```

Later

```
150 ms
```

---

## Investigation

CloudWatch

```
Init Duration
```

---

## Resolution

- Provisioned Concurrency
- Smaller package
- Reduce dependencies

---

## Prevention

Benchmark cold start performance.

---

# Scenario 10 — Lambda Gets Throttled

CloudWatch

```
Throttles

↑↑↑
```

---

## Investigation

Check

```
Concurrent Executions
```

---

## Resolution

- Increase quota
- Optimize execution
- Queue requests

---

## Prevention

Reserved Concurrency.

SQS buffering.

---

# Scenario 11 — SQS Queue Keeps Growing

Architecture

```
Producer

↓

SQS

↓

Lambda

↓

Queue Grows
```

---

## Investigation

Monitor

```
ApproximateAgeOfOldestMessage

IteratorAge
```

---

## Possible Causes

- Lambda errors
- Slow processing
- Small batch size

---

## Resolution

Increase

- Batch Size
- Concurrency

Optimize code.

---

# Scenario 12 — EventBridge Rule Doesn't Trigger Lambda

---

## Investigation

Check

- Rule enabled
- Event pattern
- Target
- Lambda permissions

---

## Resolution

Fix event pattern.

Grant invoke permission.

---

# Scenario 13 — Deployment Breaks Production

Problem

```
Version 15

↓

Deploy

↓

Everything Fails
```

---

## Resolution

Rollback

```
Alias

↓

Version 14
```

---

## Prevention

- Canary deployment
- Blue/Green deployment
- Automated tests

---

# Scenario 14 — Memory Error

Error

```
Runtime exited

signal: killed
```

---

## Root Cause

Out Of Memory.

---

## Resolution

Increase memory.

Process data in chunks.

---

## Prevention

Avoid loading huge files into memory.

---

# Scenario 15 — Third-Party API Becomes Slow

Architecture

```
Lambda

↓

Stripe

↓

8 Seconds
```

---

## Resolution

Implement

- Timeout
- Retry
- Circuit Breaker

---

## Prevention

Never block user requests on unreliable services.

---

# Scenario 16 — Secrets Manager Access Fails

Error

```
AccessDeniedException
```

---

## Investigation

Check

- IAM
- Secret ARN
- Region

---

## Resolution

Update execution role.

---

# Scenario 17 — Deployment Package Too Large

Error

```
RequestEntityTooLargeException
```

---

## Resolution

- Remove unused libraries
- Use Layers
- Use Container Images

---

# Scenario 18 — High Lambda Cost

Symptoms

Monthly cost doubles.

---

## Investigation

Review

- Invocations
- Duration
- Memory
- Logging

---

## Root Causes

- Recursive invocation
- Infinite retries
- Large memory
- Long execution

---

## Resolution

Optimize architecture.

Reduce execution duration.

---

# Scenario 19 — X-Ray Shows Random Latency

Timeline

```
Lambda

↓

Database

40 ms

↓

Redis

5 ms

↓

Stripe

2400 ms
```

---

## Root Cause

Third-party API.

---

## Resolution

- Cache responses
- Async processing
- Circuit breaker

---

# Scenario 20 — Black Friday Traffic Spike

Traffic increases

```
10x

↓

100x
```

---

## Challenges

- Scaling
- Database
- Queues
- Cost

---

## Architecture

```
CloudFront

↓

API Gateway

↓

Lambda

↓

SQS

↓

Lambda Workers

↓

RDS Proxy

↓

Aurora

↓

SNS
```

---

## Engineering Decisions

- Reserved Concurrency
- Provisioned Concurrency
- Auto Scaling
- CloudWatch Alarms
- Cost Monitoring

---

# Production Incident Playbook

```
Incident

↓

CloudWatch Alarm

↓

Logs

↓

Metrics

↓

X-Ray

↓

Root Cause

↓

Immediate Fix

↓

Permanent Fix

↓

Postmortem
```

---

# Common Root Causes

| Problem | Most Common Cause |
|----------|-------------------|
| Timeout | Slow DB/API |
| High Cost | Infinite retries |
| Slow API | Cold start / DB |
| AccessDenied | IAM |
| Queue Growth | Lambda failures |
| 502 Errors | Invalid response |
| Memory Error | Large payload |
| High Latency | External dependency |

---

# Best Practices

✅ Use CloudWatch dashboards for operational visibility.

✅ Enable AWS X-Ray for distributed tracing.

✅ Implement structured logging.

✅ Design idempotent event processing.

✅ Protect databases with RDS Proxy.

✅ Configure retries with exponential backoff.

✅ Use DLQs or Lambda Destinations.

✅ Deploy using versions and aliases.

✅ Monitor concurrency and throttling.

✅ Conduct post-incident reviews after every production outage.

---

# Senior Backend Engineering Perspective

Senior engineers are expected to think beyond individual Lambda functions and understand the entire ecosystem in which they operate. Successful incident response requires correlating logs, metrics, traces, infrastructure, networking, IAM, and downstream dependencies.

A structured troubleshooting process minimizes Mean Time to Resolution (MTTR) and improves system resilience over time. Equally important is learning from incidents by implementing preventive measures such as automation, monitoring, and architectural improvements.

In mature engineering organizations, every production incident becomes an opportunity to strengthen the platform rather than simply restore service.

---

# Key Takeaways

- Most production issues stem from interactions between Lambda and surrounding services rather than Lambda itself.
- Effective troubleshooting begins with CloudWatch Metrics, Logs, and AWS X-Ray before making assumptions.
- Common failure scenarios include timeouts, throttling, database connection exhaustion, networking issues, IAM misconfigurations, recursive invocations, and external API latency.
- Building resilient serverless systems requires proactive monitoring, well-defined operational playbooks, and continuous architectural refinement.
- Senior backend engineers focus on preventing repeat incidents through automation, observability, and disciplined engineering practices.