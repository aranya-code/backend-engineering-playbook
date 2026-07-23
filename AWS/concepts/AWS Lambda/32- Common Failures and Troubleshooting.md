# 32- Lambda Common Failures and Troubleshooting

# Introduction

No matter how well a Lambda function is designed, production systems eventually encounter failures. The difference between junior and senior engineers is often not the ability to prevent every failure, but the ability to **quickly identify, isolate, and resolve issues**.

AWS Lambda integrates with numerous services such as API Gateway, SQS, SNS, EventBridge, DynamoDB, RDS, VPC networking, and third-party APIs. Failures can originate from any layer of the architecture.

This chapter covers the most common Lambda failures, their symptoms, root causes, troubleshooting techniques, and production best practices.

---

# Troubleshooting Workflow

Always troubleshoot systematically.

```
Problem Report

↓

CloudWatch Metrics

↓

CloudWatch Logs

↓

AWS X-Ray

↓

Identify Root Cause

↓

Fix

↓

Verify
```

Never guess the cause of an issue.

---

# Categories of Lambda Failures

```
Lambda Issues

│

├── Invocation Failures

├── Timeout Errors

├── Permission Errors

├── Cold Starts

├── Networking Problems

├── Memory Issues

├── Concurrency Limits

├── Dependency Failures

├── Deployment Errors

└── Runtime Exceptions
```

---

# Invocation Failure

## Symptoms

- Lambda never executes
- API Gateway returns 500
- EventBridge event disappears
- SQS messages remain in queue

Architecture

```
Event

↓

Lambda

❌

Not Invoked
```

## Possible Causes

- Missing trigger
- Disabled trigger
- IAM permission issue
- Wrong ARN
- Incorrect resource policy

## Troubleshooting

Check:

- Trigger configuration
- Resource policies
- CloudWatch Metrics
- Event source mapping

---

# Timeout Error

Error

```
Task timed out after 30.00 seconds
```

## Cause

Execution exceeded configured timeout.

Example

```
Lambda

↓

Database

↓

External API

↓

Timeout
```

## Solutions

- Optimize code
- Reduce API latency
- Cache responses
- Increase timeout only if justified

---

# Memory Exhausted

Error

```
Runtime exited with error:
signal: killed
```

or

```
Out Of Memory
```

## Cause

Memory allocation too small.

Example

```
512 MB

↓

Large CSV

↓

OOM
```

## Solution

Increase memory or stream data instead of loading everything into RAM.

---

# Import Errors

Example

```
Unable to import module 'lambda_function'
```

Common causes:

- Missing dependency
- Wrong package structure
- Incorrect handler name
- Missing Layer

Check:

```
Deployment Package

↓

Handler

↓

Dependencies
```

---

# Permission Denied

Example

```
AccessDeniedException
```

Architecture

```
Lambda

↓

S3

❌

Permission Denied
```

Cause:

IAM execution role lacks permission.

Solution:

Grant least privilege access.

Example

```
s3:GetObject

dynamodb:PutItem

sns:Publish
```

---

# Throttling

Example

```
429 Too Many Requests
```

or

```
ThrottlingException
```

Architecture

```
1000 Requests

↓

Concurrency Limit

↓

Throttle
```

Solutions

- Increase concurrency
- Queue requests
- Use SQS buffering
- Optimize execution time

---

# Cold Starts

Symptoms

```
Occasional Slow Requests
```

CloudWatch

```
Init Duration

High
```

Solutions

- Smaller deployment package
- Fewer dependencies
- Provisioned Concurrency
- SnapStart (Java)

---

# VPC Networking Problems

Symptoms

```
Lambda Cannot Reach Database
```

Architecture

```
Lambda

↓

Private Subnet

↓

Database

❌
```

Check

- Route tables
- Security Groups
- NACLs
- Subnets
- NAT Gateway
- VPC Endpoints

---

# Database Connection Exhaustion

Symptoms

```
Too Many Connections
```

Architecture

```
1000 Lambdas

↓

1000 DB Connections

↓

Database Crash
```

Solution

```
Lambda

↓

RDS Proxy

↓

Aurora
```

---

# DNS Resolution Failure

Example

```
Unknown Host
```

Possible causes

- Incorrect endpoint
- Missing VPC DNS support
- Security configuration

Verify:

```
DNS Resolution

↓

Hostname

↓

Network
```

---

# External API Failure

Architecture

```
Lambda

↓

Stripe

↓

500 Error
```

Best Practices

- Retry
- Timeout
- Circuit Breaker
- DLQ

Never retry indefinitely.

---

# Infinite Retry Loop

Architecture

```
Lambda

↓

Error

↓

Retry

↓

Error

↓

Retry
```

Can dramatically increase cost.

Use

- DLQ
- Maximum retry limits
- Idempotency

---

# Recursive Invocation

Architecture

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

Symptoms

- Massive cost increase
- Concurrency spike
- High invocation count

Solution

Break the loop.

---

# Deployment Package Too Large

Error

```
RequestEntityTooLargeException
```

Solutions

- Remove unused packages
- Use Layers
- Use Container Images

---

# Handler Misconfiguration

Example

Configured handler

```
app.handler
```

Actual file

```
main.py
```

Lambda cannot locate the handler.

Always verify:

```
File Name

↓

Function Name

↓

Handler
```

---

# Runtime Version Issues

Example

```
Python 3.13

↓

Unsupported Library
```

Always test runtime upgrades before production deployment.

---

# Environment Variable Errors

Symptoms

```
KeyError

DATABASE_URL
```

Check

- Variable exists
- Correct spelling
- Deployment configuration

---

# Secrets Manager Failures

Architecture

```
Lambda

↓

Secrets Manager

↓

Access Denied
```

Possible causes

- IAM policy
- Wrong secret ARN
- Region mismatch

---

# CloudWatch Logs Missing

Possible causes

- Execution role missing permissions

Required permissions

```
logs:CreateLogGroup

logs:CreateLogStream

logs:PutLogEvents
```

---

# X-Ray Not Recording

Check

- Active tracing enabled
- IAM permissions
- Sampling configuration

---

# SQS Processing Problems

Symptoms

```
Messages Stay In Queue
```

Possible causes

- Visibility timeout
- Batch failure
- Lambda errors

Monitor

- IteratorAge
- ApproximateAgeOfOldestMessage

---

# EventBridge Doesn't Trigger Lambda

Check

- Rule enabled
- Event pattern
- Target ARN
- Lambda permissions

---

# API Gateway Returns 502

Common causes

- Invalid Lambda response
- Function timeout
- Runtime exception

Correct response

```json
{
  "statusCode": 200,
  "body": "{}"
}
```

---

# API Gateway Returns 403

Usually

```
IAM

↓

Authorization

↓

Denied
```

Check

- Resource policy
- IAM
- Authorizer
- API Key

---

# CloudFormation Deployment Failure

Example

```
Resource Already Exists
```

Possible causes

- Stack drift
- Existing resource
- IAM issue

Review CloudFormation Events.

---

# Container Image Failure

Example

```
Image Pull Failed
```

Verify

- Image exists
- ECR permissions
- Correct tag
- Architecture compatibility

---

# High Cost

Possible causes

- Infinite retries
- Recursive invocations
- Long execution
- Large memory
- Excessive logging

Investigate

```
CloudWatch

↓

Cost Explorer

↓

Budgets
```

---

# Monitoring Checklist

Always monitor

| Metric | Why |
|---------|-----|
| Errors | Detect failures |
| Duration | Detect slow executions |
| Invocations | Traffic volume |
| Throttles | Capacity issues |
| ConcurrentExecutions | Scaling |
| IteratorAge | Queue lag |
| DeadLetterErrors | Retry failures |
| AsyncEventAge | Async backlog |

---

# Troubleshooting Checklist

```
Problem

↓

Logs

↓

Metrics

↓

Trace

↓

Permissions

↓

Networking

↓

Dependencies

↓

Fix

↓

Validate
```

---

# Common Production Incidents

| Problem | Root Cause | Solution |
|----------|------------|----------|
| Random timeouts | Slow database | Add indexes, RDS Proxy |
| Slow first request | Cold start | Provisioned Concurrency |
| High bill | Recursive invocations | Fix event loop |
| 403 AccessDenied | IAM policy | Least privilege update |
| Too many DB connections | Direct connections | RDS Proxy |
| Missing logs | CloudWatch permissions | Update execution role |
| Queue growing | Lambda failures | DLQ + retry analysis |
| API returns 502 | Invalid response | Fix handler output |

---

# Real-World Incident Example

```
Users

↓

API Gateway

↓

Lambda

↓

Aurora

↓

Response Time

12 Seconds
```

Investigation

```
CloudWatch Metrics

↓

Duration High

↓

X-Ray

↓

Database Query

11.6 Seconds
```

Root Cause

```
Missing Database Index
```

Fix

```
Add Index

↓

Query Time

30 ms
```

Total API latency reduced from **12 seconds to under 400 ms**.

---

# Best Practices

✅ Enable CloudWatch Logs for every Lambda.

✅ Enable AWS X-Ray for distributed tracing.

✅ Configure CloudWatch Alarms for errors and throttles.

✅ Use structured logging.

✅ Implement retries with exponential backoff.

✅ Configure Dead Letter Queues or Destinations.

✅ Use RDS Proxy for relational databases.

✅ Monitor concurrency and execution duration.

✅ Test deployments before production.

✅ Build idempotent event processing.

---

# Senior Backend Engineering Perspective

Production issues in Lambda are rarely caused by Lambda itself—they are usually the result of interactions between services, networking, permissions, or application design.

Senior engineers troubleshoot by correlating **metrics, logs, and traces** rather than relying on isolated symptoms. They establish operational playbooks, automate alerting, and continuously improve system resilience through post-incident reviews and architectural refinements.

The goal is not simply to restore service, but to eliminate the underlying cause and prevent recurrence.

---

# Key Takeaways

- Most Lambda failures fall into categories such as permissions, timeouts, networking, concurrency, deployment, or dependency issues.
- A structured troubleshooting process using CloudWatch Metrics, Logs, and AWS X-Ray significantly reduces mean time to resolution (MTTR).
- Common production issues include cold starts, database connection exhaustion, throttling, recursive invocations, and invalid API Gateway responses.
- Monitoring, observability, idempotency, and proper IAM design are essential for reliable serverless applications.
- Production-ready teams combine preventive best practices with well-defined troubleshooting playbooks to maintain highly available Lambda workloads.