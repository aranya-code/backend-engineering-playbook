# 05- Scenario Based Questions

# Overview

Senior backend interviews rarely focus only on definitions. Instead, interviewers present real-world production problems to evaluate your ability to analyze systems, identify root causes, make architectural decisions, and communicate trade-offs.

This chapter contains realistic AWS Lambda production scenarios similar to those discussed in interviews at companies such as Amazon, Microsoft, Google, Uber, Stripe, Atlassian, and large enterprise organizations.

For every scenario, approach your answer using the following structure:

```
Understand the Problem

↓

Gather Information

↓

Identify Root Cause

↓

Immediate Mitigation

↓

Long-term Solution

↓

Trade-offs
```

---

# Scenario 1 — API Suddenly Returns 502 Errors

## Question

Your REST API built with API Gateway and Lambda suddenly starts returning **502 Bad Gateway** for every request.

How would you investigate and fix it?

---

## Expected Thought Process

```
API Gateway

↓

Lambda

↓

Application
```

Check:

- CloudWatch Logs
- Lambda response format
- Handler exceptions
- Timeout configuration
- Recent deployment

---

## Possible Root Causes

- Invalid Lambda response
- Runtime exception
- Function timeout
- Handler misconfiguration

---

## Production Fix

- Review CloudWatch Logs
- Roll back to previous version if required
- Validate response contract
- Deploy corrected version

---

# Scenario 2 — Aurora Database Stops Accepting Connections

## Question

Your application suddenly reports:

```
Too many connections
```

What happened?

---

## Expected Analysis

```
Traffic Spike

↓

Thousands of Lambdas

↓

Thousands of DB Connections

↓

Aurora Limit Reached
```

---

## Solution

```
Lambda

↓

RDS Proxy

↓

Aurora
```

Additional improvements:

- Reuse connections
- Reserved Concurrency
- Query optimization

---

# Scenario 3 — Cold Starts Affect User Experience

## Question

Customers complain that the first request after inactivity takes **3 seconds**, while subsequent requests complete in **150 ms**.

What is happening?

---

## Root Cause

Cold Start

```
Request

↓

Initialize Runtime

↓

Load Dependencies

↓

Execute Handler
```

---

## Solution

- Reduce package size
- Remove unnecessary dependencies
- Initialize resources efficiently
- Enable Provisioned Concurrency
- Use SnapStart (Java)

---

# Scenario 4 — Lambda Inside VPC Cannot Reach the Internet

## Question

Your Lambda successfully connects to Aurora but fails when calling Stripe APIs.

Why?

---

## Investigation

```
Lambda

↓

Private Subnet

↓

Internet

❌
```

Check:

- NAT Gateway
- Route Tables
- Internet Gateway
- Security Groups

---

## Resolution

Configure outbound internet access through a NAT Gateway or use VPC Endpoints where applicable.

---

# Scenario 5 — CloudWatch Costs Increase Significantly

## Question

CloudWatch charges suddenly double even though traffic has not increased.

---

## Investigation

Review:

- Log volume
- Log retention
- Structured logging

---

## Root Cause

```
logger.info(event)
```

Logging entire payloads.

---

## Better Approach

```python
logger.info(
    "Order Created",
    extra={
        "order_id": order_id
    }
)
```

---

# Scenario 6 — Millions of Lambda Invocations Overnight

## Question

The AWS bill spikes dramatically due to millions of Lambda invocations.

How do you respond?

---

## Investigation

```
Lambda

↓

S3

↓

Lambda

↓

S3

↓

Lambda
```

Possible recursive invocation.

---

## Immediate Action

```
Reserved Concurrency

↓

0
```

Disable triggers.

Investigate event flow.

---

## Long-Term Solution

- Separate source and destination buckets
- Configure event filters
- Add idempotency

---

# Scenario 7 — Lambda Gets Throttled

## Question

CloudWatch shows increasing **Throttles**.

---

## Investigation

Review:

- ConcurrentExecutions
- Duration
- Traffic patterns

---

## Possible Causes

- Traffic spike
- Long execution time
- Reserved Concurrency limit

---

## Solutions

- Optimize execution time
- Increase concurrency quota
- Queue requests using SQS

---

# Scenario 8 — EventBridge Events Are Not Triggering

## Question

An EventBridge rule exists, but Lambda is never invoked.

---

## Investigation

Check:

- Rule enabled
- Event pattern
- Target ARN
- Lambda permissions

---

## Solution

Correct the event pattern or permissions and test with sample events.

---

# Scenario 9 — Processing One Million Messages

## Question

You need to process **1 million SQS messages** quickly and reliably.

Design the architecture.

---

## Recommended Architecture

```
Producer

↓

Amazon SQS

↓

Lambda

↓

Batch Processing

↓

DynamoDB
```

---

## Improvements

- Batch size tuning
- Reserved Concurrency
- DLQ
- Idempotency
- Partial batch responses

---

# Scenario 10 — Third-Party Payment API Is Slow

## Question

Stripe starts taking **8 seconds** to respond.

Users experience slow API responses.

---

## Better Design

```
Client

↓

API Gateway

↓

Lambda

↓

SQS

↓

Worker Lambda

↓

Stripe
```

Return immediately and process asynchronously.

---

# Scenario 11 — Multi-Region Disaster Recovery

## Question

Your application must remain available even if an AWS Region fails.

How would you design it?

---

## Architecture

```
Users

↓

Route 53

↓

Region A

↓

Lambda

↓

DynamoDB Global Tables

↓

Region B

↓

Lambda
```

---

## Additional Components

- Route 53 Failover Routing
- S3 Cross-Region Replication
- Multi-Region Secrets
- CloudWatch Alarms

---

# Scenario 12 — Secure Payment Processing API

## Question

Design a secure payment API using Lambda.

---

## Architecture

```
Client

↓

CloudFront

↓

AWS WAF

↓

API Gateway

↓

JWT Authorizer

↓

Lambda

↓

Secrets Manager

↓

RDS Proxy

↓

Aurora
```

---

## Security Measures

- HTTPS
- IAM
- Least Privilege
- KMS
- Secrets Manager
- CloudTrail
- CloudWatch
- X-Ray

---

# Scenario 13 — Zero Downtime Deployment

## Question

A new deployment introduces errors.

How do you avoid customer impact?

---

## Deployment Strategy

```
Version 1

↓

Alias

↓

Canary

↓

Monitor

↓

100% Traffic
```

If failures occur:

```
Alias

↓

Previous Version
```

Rollback is immediate.

---

# Scenario 14 — High Latency Investigation

## Question

API latency increases from **250 ms** to **5 seconds**.

How do you determine the bottleneck?

---

## Investigation Workflow

```
CloudWatch Metrics

↓

CloudWatch Logs

↓

AWS X-Ray

↓

Database

↓

External APIs

↓

Application Code
```

Never assume Lambda is responsible.

---

# Scenario 15 — Choosing Between Lambda and ECS

## Question

Your team wants to migrate every workload to Lambda.

Would you agree?

---

## Discussion

Choose Lambda for:

- Event-driven workloads
- REST APIs
- Background jobs
- Automation

Choose ECS for:

- Long-running processes
- Stateful services
- GPU workloads
- Continuous streaming

Explain the trade-offs instead of assuming one service is always better.

---

# Tips for Answering Scenario Questions

When presented with an unfamiliar problem:

1. Clarify the requirements.
2. Ask questions about traffic, latency, and architecture.
3. Identify possible failure domains.
4. Use CloudWatch and X-Ray before making assumptions.
5. Suggest both an immediate mitigation and a long-term improvement.
6. Discuss trade-offs and operational impact.

---

# Common Themes in Senior Interviews

Interviewers frequently evaluate your understanding of:

- Event-driven architecture
- Scalability
- High availability
- Security
- IAM
- Networking
- Observability
- Cost optimization
- Deployment strategies
- Disaster recovery
- Operational excellence
- AWS Well-Architected Framework

---

# Senior Backend Engineering Perspective

Scenario-based interviews are designed to measure engineering judgment rather than memorization. Strong candidates demonstrate a structured approach to problem solving, balancing immediate mitigation with long-term architectural improvements.

In production environments, there is rarely a single correct answer. The best solution depends on workload characteristics, business requirements, cost constraints, and operational complexity. Senior engineers communicate these trade-offs clearly while emphasizing reliability, security, scalability, and maintainability.

---

# Key Takeaways

- Scenario-based interviews assess real-world engineering decisions rather than factual recall.
- A structured investigation process leads to faster and more reliable problem resolution.
- CloudWatch, AWS X-Ray, IAM, networking, and architecture are central to troubleshooting Lambda workloads.
- Production-ready designs prioritize resilience, observability, automation, and scalability.
- Explaining trade-offs is often more valuable than presenting a single "correct" solution.