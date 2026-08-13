# 01- Introduction.md

# AWS Lambda

AWS Lambda is Amazon's **serverless compute service** that allows developers to execute code without provisioning, managing, or maintaining servers. Instead of deploying applications onto EC2 instances or Kubernetes clusters, developers upload their code, define a trigger, and AWS automatically handles the underlying infrastructure.

Lambda follows an **event-driven execution model**, where code runs only when an event occurs. The infrastructure is created, scaled, monitored, and retired automatically by AWS.

Unlike traditional servers, Lambda functions are **stateless**, short-lived, and designed to perform a single responsibility.

---

# What is Serverless?

Serverless does **not** mean there are no servers.

Instead, it means:

- AWS manages the servers.
- AWS patches operating systems.
- AWS provisions infrastructure.
- AWS performs automatic scaling.
- AWS handles high availability.
- AWS monitors infrastructure health.

The developer is only responsible for:

- Business logic
- Dependencies
- Runtime configuration
- Permissions
- Monitoring
- Performance optimization

Think of Lambda as:

> Upload Code → Configure Trigger → AWS Executes It

---

# Traditional Server vs AWS Lambda

| Traditional Server | AWS Lambda |
|-------------------|------------|
| Provision EC2 | No server provisioning |
| Configure OS | Managed by AWS |
| Install runtime | Runtime already available |
| Capacity planning | Automatic scaling |
| Pay while server runs | Pay only during execution |
| Responsible for patches | AWS handles patches |
| Need Load Balancer | Not always required |
| Long-running process | Short-lived execution |

---

# Lambda Execution Model

A Lambda function follows a simple lifecycle.

```text
Event Occurs
      │
      ▼
Lambda Service
      │
      ▼
Execution Environment Created (if needed)
      │
      ▼
Function Executes
      │
      ▼
Response Returned
      │
      ▼
Environment Frozen for Reuse
```

Unlike an EC2 instance, a Lambda execution environment is **temporary**.

---

# Core Characteristics

## 1. Stateless

Every invocation should be treated as independent.

Do **not** assume:

- variables remain in memory
- previous requests exist
- previous user session exists

Instead, persist data in:

- DynamoDB
- S3
- Redis
- Aurora
- RDS
- ElastiCache

---

## 2. Event Driven

Lambda only executes when an event occurs.

Example events:

- HTTP Request
- File uploaded to S3
- Message in SQS
- EventBridge rule
- DynamoDB Stream
- Kinesis Stream
- CloudWatch Schedule
- SNS Notification

Example:

```text
User uploads image
        │
        ▼
S3 Bucket
        │
        ▼
Lambda Triggered
        │
        ▼
Resize Image
        │
        ▼
Store Thumbnail
```

---

## 3. Automatic Scaling

AWS automatically creates more Lambda execution environments as traffic increases.

```text
1 Request
     │
     ▼
1 Lambda Instance

------------------------

1000 Requests

     │
     ▼

1000 Lambda Executions
```

There is no need to configure:

- Auto Scaling Groups
- Load Balancers
- EC2 Fleet

Scaling is handled by AWS.

---

## 4. Pay Per Use

Billing is based on:

- Number of requests
- Execution duration
- Allocated memory

No requests means:

```
No execution
No billing
```

This makes Lambda highly cost-effective for sporadic workloads.

---

## 5. Short-Lived Compute

Lambda is designed for workloads that finish quickly.

Typical examples include:

- Image processing
- API requests
- Data transformation
- Event processing
- Notification delivery
- File validation

Long-running applications are generally better suited to ECS, EKS, or EC2.

---

# Supported Runtimes

AWS provides managed runtimes for:

- Python
- Node.js
- Java
- .NET
- Go
- Ruby

Custom runtimes are also supported using the **Runtime API**.

Container images up to **10 GB** are also supported through Amazon ECR.

---

# Common Lambda Triggers

| AWS Service | Use Case |
|-------------|----------|
| API Gateway | REST APIs |
| Application Load Balancer | HTTP Applications |
| S3 | File Processing |
| EventBridge | Event Routing |
| CloudWatch Scheduler | Cron Jobs |
| SNS | Fan-out Notifications |
| SQS | Queue Processing |
| DynamoDB Streams | Change Data Capture |
| Kinesis | Streaming Data |
| Step Functions | Workflow Execution |
| Cognito | Authentication Hooks |

---

# Typical Backend Use Cases

## REST APIs

```text
Client

   │

API Gateway

   │

Lambda

   │

DynamoDB
```

---

## Image Processing

```text
Upload Image

      │

S3 Bucket

      │

Lambda

      │

Resize

      │

Store Thumbnail
```

---

## Background Jobs

```text
Application

      │

SQS Queue

      │

Lambda Workers

      │

Database
```

---

## Event Processing

```text
Application

      │

EventBridge

      │

Lambda

      │

Multiple Services
```

---

# Why Companies Use Lambda

Large organizations increasingly adopt Lambda because it:

- Eliminates infrastructure management
- Reduces operational overhead
- Scales automatically
- Integrates with nearly every AWS service
- Accelerates feature delivery
- Lowers infrastructure costs for event-driven workloads
- Supports microservice architectures

Many production systems use Lambda for asynchronous processing, backend APIs, scheduled tasks, and data pipelines.

---

# When Lambda is a Good Choice

Use Lambda when:

- Building event-driven systems
- Processing files from S3
- Creating REST APIs
- Consuming messages from SQS
- Processing DynamoDB Streams
- Running scheduled jobs
- Automating AWS operations
- Building lightweight microservices
- Handling webhook integrations

---

# When NOT to Use Lambda

Lambda is not always the best solution.

Avoid Lambda for:

- Long-running batch jobs
- Stateful applications
- GPU workloads
- Applications requiring persistent TCP connections
- Very low-latency systems affected by cold starts
- Heavy machine learning inference
- Large monolithic applications

In these scenarios, ECS, EKS, or EC2 are often more appropriate.

---

# Lambda vs EC2 vs ECS vs Fargate

| Feature | Lambda | ECS | Fargate | EC2 |
|----------|----------|------|----------|------|
| Server Management | None | Partial | None | Full |
| Auto Scaling | Automatic | Configurable | Automatic | Manual |
| Cold Start | Yes | No | No | No |
| Long Running | No | Yes | Yes | Yes |
| Event Driven | Excellent | Good | Good | Poor |
| Billing | Per Execution | Running Tasks | Running Tasks | Running Instance |
| Stateless | Yes | Optional | Optional | Optional |

---

# Advantages

- No infrastructure management
- Automatic scaling
- High availability by default
- Deep AWS integration
- Fast deployment
- Cost efficient for burst workloads
- Supports multiple programming languages

---

# Limitations

- Maximum execution time (15 minutes)
- Cold starts
- Stateless execution
- Deployment package limits
- Concurrency quotas
- Not ideal for continuously running services

---

# Real-World Production Examples

### E-commerce

```
Customer uploads product image

↓

S3

↓

Lambda

↓

Resize image

↓

Store optimized versions

↓

CloudFront serves images
```

---

### Banking

```
Transaction Created

↓

EventBridge

↓

Lambda

↓

Fraud Detection

↓

SNS Alert

↓

Audit Database
```

---

### Video Streaming

```
Video Upload

↓

S3

↓

Lambda

↓

Generate Metadata

↓

Step Functions

↓

MediaConvert
```

---

### Healthcare

```
Lab Report Uploaded

↓

S3

↓

Lambda

↓

Virus Scan

↓

Extract Metadata

↓

Store in Database
```

---

# Senior Backend Engineering Perspective

A senior backend engineer should think beyond simply writing Lambda functions.

Key architectural considerations include:

- Idempotent function design
- Retry handling
- Failure recovery
- Dead Letter Queues (DLQs)
- Event ordering
- Cold start optimization
- Concurrency limits
- Security using IAM least privilege
- Cost optimization
- Observability with CloudWatch, X-Ray, and structured logging
- Infrastructure as Code (SAM, CDK, CloudFormation, Terraform)

In production, the surrounding architecture is often more important than the Lambda function itself.

---

# Interview Questions

### Beginner

- What is AWS Lambda?
- Why is Lambda called serverless?
- What services can trigger Lambda?
- What are Lambda execution limits?

### Intermediate

- Explain synchronous vs asynchronous invocation.
- What is a cold start?
- How does Lambda scale?
- What is the purpose of an execution role?
- What is an Event Source Mapping?

### Senior

- How would you design an idempotent Lambda processing SQS messages?
- How would you prevent duplicate processing?
- How would you reduce cold starts?
- When would you choose ECS over Lambda?
- How would you process one million events per minute?
- How would you monitor and troubleshoot Lambda in production?
- How would you deploy Lambda with zero downtime?

---

# Key Takeaways

- AWS Lambda is an event-driven serverless compute service.
- AWS manages infrastructure, scaling, and availability.
- Functions are stateless and short-lived.
- Pricing is based on requests and execution duration.
- Lambda integrates deeply with AWS services such as S3, API Gateway, SQS, EventBridge, DynamoDB, and CloudWatch.
- Designing production-grade Lambda applications requires attention to scalability, retries, idempotency, observability, and security—not just writing function code.