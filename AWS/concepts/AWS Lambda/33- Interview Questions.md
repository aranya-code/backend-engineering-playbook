# 33- Lambda Interview Questions

# Introduction

AWS Lambda is one of the most frequently asked topics in backend, cloud, DevOps, and system design interviews. While junior interviews focus on basic concepts, senior backend interviews emphasize architectural decisions, scaling, security, performance optimization, operational excellence, and trade-offs.

This chapter contains interview questions categorized by difficulty, along with concise answers and explanations suitable for backend developers with 5–10+ years of experience.

---

# Beginner Level Questions

## 1. What is AWS Lambda?

**Answer**

AWS Lambda is a serverless compute service that allows you to execute code without provisioning or managing servers. AWS automatically handles infrastructure provisioning, scaling, patching, availability, and capacity management.

---

## 2. What is Serverless Computing?

**Answer**

Serverless computing is a cloud execution model where developers focus on writing application code while the cloud provider manages the underlying infrastructure.

Despite the name, servers still exist—they are simply managed by AWS.

---

## 3. Which programming languages are supported by Lambda?

Examples include:

- Python
- Node.js
- Java
- Go
- .NET
- Ruby
- Custom Runtime

---

## 4. What can trigger a Lambda function?

Common triggers include:

- API Gateway
- S3
- SNS
- SQS
- EventBridge
- DynamoDB Streams
- Kinesis
- CloudWatch Events
- Application Load Balancer

---

## 5. What is the maximum execution time?

**900 seconds (15 minutes).**

---

## 6. What is the maximum memory allocation?

Up to **10,240 MB (10 GB)**.

Increasing memory also increases available CPU.

---

## 7. Is Lambda stateless?

Yes.

Persistent data should be stored in external services such as:

- DynamoDB
- Aurora
- Redis
- S3
- EFS

---

## 8. What is the `/tmp` directory?

Temporary local storage attached to a Lambda execution environment.

Features:

- Ephemeral
- Configurable up to 10 GB
- Not shared across execution environments

---

## 9. What is an execution role?

An IAM role assumed by Lambda that grants permissions to access AWS services.

---

## 10. How does Lambda scale?

AWS automatically creates additional execution environments as invocation demand increases, subject to concurrency limits.

---

# Intermediate Level Questions

## 11. What is a Cold Start?

A cold start occurs when Lambda creates a new execution environment before running your function.

Cold starts include:

- Runtime initialization
- Code loading
- Dependency initialization

---

## 12. How can you reduce Cold Starts?

- Reduce package size
- Minimize dependencies
- Reuse initialized resources
- Use Provisioned Concurrency
- Use SnapStart (Java)

---

## 13. What is Reserved Concurrency?

Reserved Concurrency guarantees capacity for a Lambda function while also limiting its maximum concurrent executions.

---

## 14. What is Provisioned Concurrency?

Provisioned Concurrency keeps execution environments initialized and ready to eliminate cold starts.

---

## 15. Difference between Reserved and Provisioned Concurrency?

| Reserved | Provisioned |
|-----------|-------------|
| Limits concurrency | Eliminates cold starts |
| No warm instances | Keeps warm instances ready |
| Free | Additional cost |
| Capacity management | Performance optimization |

---

## 16. What is a Lambda Layer?

A reusable package containing shared code or dependencies that multiple Lambda functions can use.

---

## 17. What are Lambda Versions?

Published, immutable snapshots of a Lambda function.

---

## 18. What are Lambda Aliases?

Friendly names pointing to versions.

Example:

- dev
- staging
- production

Useful for:

- Canary deployments
- Blue/Green deployments
- Rollbacks

---

## 19. Explain Event Source Mapping.

An Event Source Mapping polls supported event sources (such as SQS, DynamoDB Streams, or Kinesis) and invokes Lambda with batches of records.

---

## 20. Difference between synchronous and asynchronous invocation?

| Synchronous | Asynchronous |
|-------------|--------------|
| Caller waits | Caller returns immediately |
| Immediate response | Background execution |
| API Gateway | SNS, EventBridge |

---

# Senior Backend Questions

## 21. Why shouldn't Lambda connect directly to Aurora?

Large numbers of concurrent Lambda invocations can exhaust database connections.

Preferred architecture:

```
Lambda

↓

RDS Proxy

↓

Aurora
```

---

## 22. Explain Lambda execution environment reuse.

Warm execution environments may be reused for multiple invocations.

Expensive initialization should occur outside the handler.

---

## 23. Why should Lambda functions be stateless?

Because AWS may destroy execution environments at any time.

State must be stored externally.

---

## 24. Explain idempotency.

Processing the same request multiple times should produce the same final result.

Critical for:

- SQS
- EventBridge
- SNS
- Retry logic

---

## 25. How would you securely store database credentials?

Use:

- AWS Secrets Manager
- Systems Manager Parameter Store

Never hardcode credentials.

---

## 26. How do you debug production Lambda failures?

Typical workflow:

```
CloudWatch Metrics

↓

CloudWatch Logs

↓

AWS X-Ray

↓

Root Cause Analysis
```

---

## 27. What CloudWatch metrics do you monitor?

Important metrics:

- Invocations
- Duration
- Errors
- Throttles
- ConcurrentExecutions
- IteratorAge
- AsyncEventAge

---

## 28. What is AWS X-Ray?

AWS X-Ray is a distributed tracing service used to analyze request flow, latency, dependencies, and failures across distributed systems.

---

## 29. What causes Lambda throttling?

Common causes:

- Account concurrency limits
- Reserved concurrency limits
- Traffic spikes
- Long-running executions

---

## 30. How do you optimize Lambda cost?

- Benchmark memory
- Reduce execution duration
- Batch messages
- Cache expensive operations
- Remove unnecessary logging
- Minimize deployment package size

---

# Architecture Interview Questions

## 31. When would you choose Lambda over ECS?

Choose Lambda when:

- Event-driven workloads
- Short-lived tasks
- Automatic scaling
- Minimal infrastructure management

Choose ECS when:

- Long-running processes
- Stateful applications
- Custom networking
- GPU workloads
- Large containers

---

## 32. When would you avoid Lambda?

Avoid Lambda for:

- Long-running jobs (>15 min)
- Large ML training
- Stateful applications
- GPU processing
- Applications requiring persistent connections

---

## 33. Explain an event-driven architecture using Lambda.

Example:

```
API Gateway

↓

Lambda

↓

SQS

↓

Lambda

↓

SNS

↓

Email Service
```

Each component is loosely coupled and independently scalable.

---

## 34. Explain a serverless REST API.

```
Client

↓

CloudFront

↓

API Gateway

↓

Lambda

↓

Aurora
```

Benefits:

- Auto scaling
- Pay-per-use
- Minimal operational overhead

---

## 35. Explain Lambda inside a VPC.

Lambda attaches Elastic Network Interfaces (ENIs) to VPC subnets.

Use cases:

- Aurora
- ElastiCache
- Internal APIs

---

# Security Questions

## 36. How do you implement least privilege?

Grant only the permissions required.

Example:

Good

```
s3:GetObject
```

Bad

```
AdministratorAccess
```

---

## 37. How do you encrypt environment variables?

Use AWS KMS.

Sensitive secrets should still be stored in Secrets Manager.

---

## 38. How do you secure Lambda?

- Least privilege IAM
- Secrets Manager
- VPC when required
- Encryption at rest
- TLS
- CloudTrail auditing
- CloudWatch monitoring

---

## 39. Why shouldn't secrets be stored in environment variables?

Environment variables can still be exposed to users with sufficient permissions.

Secrets Manager provides:

- Rotation
- Encryption
- Fine-grained IAM

---

# Performance Questions

## 40. Why does increasing memory sometimes reduce cost?

More memory provides more CPU.

Example:

| Memory | Duration |
|----------|---------:|
| 256 MB | 5 s |
| 1024 MB | 1 s |

Despite the higher memory allocation, the shorter runtime may reduce total cost.

---

## 41. How do you optimize Cold Starts?

- Smaller deployment packages
- Efficient initialization
- Lambda Layers
- Provisioned Concurrency
- SnapStart (Java)

---

## 42. How do you optimize database performance?

- RDS Proxy
- Connection reuse
- Query optimization
- Indexes
- Redis caching

---

# DevOps Questions

## 43. How do you deploy Lambda safely?

```
GitHub

↓

CI/CD

↓

Publish Version

↓

Update Alias

↓

Monitor

↓

Rollback if Needed
```

---

## 44. Why use Lambda versions instead of `$LATEST`?

Published versions are immutable and support:

- Rollbacks
- Canary deployments
- Blue/Green deployments

---

## 45. How do you monitor Lambda?

Use:

- CloudWatch Logs
- CloudWatch Metrics
- AWS X-Ray
- CloudWatch Alarms
- AWS Cost Explorer

---

# Rapid Fire Questions

## 46. Maximum execution time?

15 minutes.

---

## 47. Maximum memory?

10 GB.

---

## 48. Does Lambda automatically scale?

Yes.

---

## 49. Can Lambda access the internet inside a private subnet?

Only if configured with:

- NAT Gateway
- VPC Endpoint (for supported AWS services)

---

## 50. Can Lambda call another Lambda?

Yes.

Direct invocation using the AWS SDK or asynchronously through services such as SNS, SQS, or EventBridge.

---

# Common Follow-Up Questions

Interviewers often ask:

- How would you process one million SQS messages?
- How would you eliminate cold starts?
- How would you secure Lambda?
- How would you optimize cost?
- How would you debug intermittent failures?
- How would you design a highly available serverless application?
- How would you migrate a monolith to Lambda?
- When would ECS be a better choice?
- How would you implement zero-downtime deployments?
- How would you prevent duplicate event processing?

---

# Senior Backend Engineering Perspective

Senior Lambda interviews focus less on API memorization and more on engineering judgment. Interviewers want to understand how you reason about architecture, scalability, security, reliability, and operational excellence.

When answering questions:

- Explain **why** you chose a particular design.
- Discuss trade-offs rather than claiming one solution is always best.
- Reference AWS Well-Architected Framework principles where appropriate.
- Demonstrate familiarity with production tools such as CloudWatch, AWS X-Ray, RDS Proxy, IAM, Secrets Manager, and CI/CD pipelines.
- Use real-world examples from experience to support your answers whenever possible.

Strong candidates consistently connect Lambda concepts to broader distributed system design and operational practices.

---

# Key Takeaways

- Be comfortable explaining Lambda fundamentals, execution environments, triggers, concurrency, and deployment strategies.
- Expect senior-level questions on scaling, security, observability, cost optimization, and architectural trade-offs.
- Understand how Lambda integrates with AWS services such as API Gateway, SQS, SNS, EventBridge, Aurora, and CloudWatch.
- Prepare to discuss design decisions and their trade-offs rather than relying on definitions alone.
- The strongest interview responses demonstrate practical production experience, structured thinking, and a clear understanding of serverless architecture.