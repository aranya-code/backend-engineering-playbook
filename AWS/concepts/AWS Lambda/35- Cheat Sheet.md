# 35- Lambda Cheat Sheet

# Introduction

This cheat sheet is a quick reference for AWS Lambda concepts, limits, best practices, architecture patterns, troubleshooting, security, and interview revision. It is designed for rapid review before interviews, certifications, or production deployments.

---

# Lambda at a Glance

| Feature | Value |
|----------|-------|
| Compute Model | Serverless |
| Maximum Execution Time | 15 Minutes (900 seconds) |
| Memory | 128 MB – 10,240 MB |
| Ephemeral Storage (/tmp) | 512 MB – 10 GB |
| Scaling | Automatic |
| Billing | Requests + Duration + Memory |
| Deployment Types | ZIP, Container Image |
| Runtime | Managed or Custom |

---

# Invocation Types

| Type | Examples | Caller Waits? |
|------|----------|---------------|
| Synchronous | API Gateway, ALB, Function URL | ✅ Yes |
| Asynchronous | SNS, EventBridge, S3 | ❌ No |
| Poll-Based | SQS, Kinesis, DynamoDB Streams | Depends on Event Source Mapping |

---

# Common Event Sources

```
API Gateway

S3

SNS

SQS

EventBridge

CloudWatch

Kinesis

DynamoDB Streams

Application Load Balancer

Function URL
```

---

# Lambda Lifecycle

```
Invoke

↓

Cold Start?

↓

Runtime Initialization

↓

Handler Execution

↓

Response

↓

Freeze Environment

↓

Reuse (Warm Start)
```

---

# Cold Start Optimization

✅ Reduce deployment package size

✅ Remove unused dependencies

✅ Initialize resources outside handler

✅ Use Provisioned Concurrency

✅ Use SnapStart (Java)

---

# Concurrency

## Reserved Concurrency

- Guarantees capacity
- Limits maximum concurrency
- Prevents noisy neighbors

---

## Provisioned Concurrency

- Eliminates cold starts
- Keeps environments warm
- Additional cost

---

# Memory Guidelines

| Workload | Suggested Memory |
|----------|------------------|
| Small REST API | 256–512 MB |
| Database API | 512–1024 MB |
| File Processing | 1024–3008 MB |
| Image Processing | 2048+ MB |
| Machine Learning Inference | 3008+ MB |

Always benchmark using **AWS Lambda Power Tuning**.

---

# Storage Options

| Storage | Use Case |
|----------|----------|
| Memory | Variables, Caching |
| /tmp | Temporary Files |
| EFS | Shared Persistent Storage |
| S3 | Object Storage |

---

# Lambda Versions

```
$LATEST

↓

Publish Version

↓

Alias

↓

Production
```

Never deploy `$LATEST` directly to production.

---

# Deployment Strategies

```
All-at-Once

Canary

Linear

Blue/Green
```

---

# Security Checklist

✅ Least Privilege IAM

✅ Secrets Manager

✅ KMS Encryption

✅ TLS

✅ Private Subnets (when required)

✅ CloudTrail

✅ CloudWatch Monitoring

Never hardcode:

- Passwords
- API Keys
- Tokens

---

# Monitoring Stack

```
CloudWatch Metrics

↓

CloudWatch Logs

↓

AWS X-Ray

↓

CloudWatch Alarms

↓

SNS Notifications
```

---

# Important CloudWatch Metrics

| Metric | Purpose |
|---------|----------|
| Invocations | Traffic |
| Errors | Failures |
| Duration | Performance |
| Throttles | Scaling Issues |
| ConcurrentExecutions | Capacity |
| IteratorAge | Queue Processing Delay |
| AsyncEventAge | Async Backlog |

---

# AWS X-Ray

Provides

- Distributed Tracing
- Service Map
- Latency Analysis
- Dependency Tracking
- Root Cause Investigation

---

# Retry Behavior

| Source | Retry |
|----------|------|
| API Gateway | Client Retry |
| SNS | Automatic |
| EventBridge | Automatic |
| SQS | Visibility Timeout + Retry |
| DynamoDB Streams | Automatic |

---

# Dead Letter Queue (DLQ)

Supported with

- SNS
- EventBridge
- Asynchronous Invocations

Common Targets

- SQS
- SNS

---

# Destinations

Supports

```
Success

Failure
```

Useful for

- Auditing
- Notifications
- Workflows

---

# Common AWS Integrations

```
CloudFront

↓

API Gateway

↓

Lambda

↓

RDS Proxy

↓

Aurora
```

```
S3

↓

Lambda

↓

SNS
```

```
EventBridge

↓

Lambda

↓

Step Functions
```

```
SQS

↓

Lambda

↓

DynamoDB
```

---

# Common Errors

| Error | Cause |
|--------|-------|
| AccessDeniedException | IAM |
| Task Timed Out | Slow Code |
| Too Many Connections | Database |
| ThrottlingException | Concurrency |
| 502 Bad Gateway | Invalid Response |
| Out Of Memory | Memory Allocation |
| Unable to Import Module | Missing Dependency |
| Runtime Exit | Runtime Crash |

---

# Troubleshooting Workflow

```
Problem

↓

CloudWatch Metrics

↓

CloudWatch Logs

↓

AWS X-Ray

↓

IAM

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

# VPC Checklist

```
Private Subnet

↓

Security Groups

↓

Route Tables

↓

NAT Gateway

↓

VPC Endpoints
```

---

# Database Best Practices

✅ Use RDS Proxy

✅ Reuse Connections

✅ Cache Queries

✅ Add Indexes

✅ Optimize SQL

---

# Cost Optimization

✅ Benchmark Memory

✅ Reduce Duration

✅ Batch Processing

✅ Minimize Logging

✅ Cache Secrets

✅ Remove Unused Libraries

✅ Use Async Processing

---

# Performance Optimization

✅ Smaller Packages

✅ Warm Resources

✅ Connection Reuse

✅ Parallel Calls

✅ Efficient Algorithms

---

# Logging Best Practices

Bad

```python
print(event)
```

Good

```python
logger.info(
    "Order Created",
    extra={
        "order_id": order_id
    }
)
```

---

# Production Best Practices

✅ One Responsibility Per Function

✅ Stateless Design

✅ Idempotent Processing

✅ Structured Logging

✅ Versioned Deployments

✅ CI/CD

✅ CloudWatch Alarms

✅ X-Ray

✅ Least Privilege IAM

---

# Lambda vs ECS

| Lambda | ECS |
|----------|-----|
| Event Driven | Long Running |
| Auto Scaling | Container Management |
| 15 Minute Limit | No Limit |
| Serverless | Managed Containers |
| Pay Per Request | Pay for Running Tasks |

---

# Important AWS Services Around Lambda

| Service | Purpose |
|----------|----------|
| API Gateway | REST APIs |
| ALB | HTTP Routing |
| S3 | Object Storage |
| SQS | Queue |
| SNS | Pub/Sub |
| EventBridge | Event Bus |
| DynamoDB | NoSQL |
| Aurora | Relational Database |
| RDS Proxy | Connection Pooling |
| CloudWatch | Monitoring |
| X-Ray | Distributed Tracing |
| IAM | Security |
| Secrets Manager | Secrets |
| EFS | Shared Storage |
| CloudFront | CDN |
| Step Functions | Workflow |

---

# Frequently Asked Interview Questions

- What is a Cold Start?
- Explain Reserved vs Provisioned Concurrency.
- Why use RDS Proxy?
- How does Lambda scale?
- Explain Event Source Mapping.
- How do you reduce costs?
- How do you debug Lambda?
- Explain Lambda Layers.
- How do you secure Lambda?
- Difference between synchronous and asynchronous invocation?
- When would you choose ECS instead of Lambda?
- How do you prevent duplicate event processing?

---

# Senior Backend Interview Tips

When answering Lambda questions:

1. Explain the concept.
2. Describe the AWS implementation.
3. Discuss trade-offs.
4. Mention production considerations.
5. Suggest monitoring and observability.

This structure demonstrates engineering maturity.

---

# AWS Well-Architected Mapping

| Pillar | Lambda Example |
|----------|----------------|
| Operational Excellence | CI/CD, CloudWatch |
| Security | IAM, Secrets Manager |
| Reliability | Retries, DLQ, Idempotency |
| Performance Efficiency | Memory Tuning, Provisioned Concurrency |
| Cost Optimization | Benchmarking, Right-Sizing |

---

# One-Page Revision

```
Lambda

├── Stateless
├── Event Driven
├── Auto Scaling
├── Max 15 Minutes
├── 128 MB – 10 GB Memory
├── ZIP or Container
├── Cold Starts
├── Layers
├── Versions & Aliases
├── IAM Execution Role
├── Secrets Manager
├── RDS Proxy
├── CloudWatch
├── AWS X-Ray
├── Reserved Concurrency
├── Provisioned Concurrency
├── DLQ & Destinations
├── Event Source Mapping
├── CI/CD
└── Cost Optimization
```

---

# Final Revision Checklist

Before deploying a Lambda function to production, confirm:

- [ ] Function is stateless
- [ ] IAM follows least privilege
- [ ] Secrets stored in Secrets Manager
- [ ] Memory benchmarked
- [ ] Timeout configured appropriately
- [ ] CloudWatch Logs enabled
- [ ] CloudWatch Alarms configured
- [ ] AWS X-Ray enabled (where appropriate)
- [ ] Version published and Alias updated
- [ ] CI/CD pipeline tested
- [ ] RDS Proxy used for relational databases
- [ ] Idempotency implemented
- [ ] Retries and DLQ configured
- [ ] Cost monitoring enabled
- [ ] Documentation updated