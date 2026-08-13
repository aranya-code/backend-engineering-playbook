# 24- Lambda Design Patterns

# Introduction

Building a Lambda function is relatively simple. Designing a **production-ready serverless architecture** is significantly more challenging.

A well-designed Lambda application should be:

- Loosely coupled
- Highly scalable
- Fault tolerant
- Event-driven
- Easy to maintain
- Cost efficient

AWS provides numerous services that work together with Lambda, enabling powerful architectural patterns.

This chapter explores the most common Lambda design patterns used in enterprise environments.

---

# What is a Design Pattern?

A design pattern is a proven solution to a recurring software engineering problem.

Instead of inventing a new architecture every time, engineers apply established patterns that have been validated in production.

Examples include:

- Event-Driven Architecture
- Fan-Out Pattern
- Fan-In Pattern
- Pipeline Pattern
- Orchestration Pattern
- Saga Pattern
- Scatter-Gather Pattern

---

# Event-Driven Pattern

This is the most common Lambda architecture.

```
Producer

↓

EventBridge

↓

Lambda

↓

Database
```

Instead of services calling each other directly, they communicate through events.

### Benefits

- Loose coupling
- Better scalability
- Easier maintenance
- Independent deployments

---

# Request-Response Pattern

Used for synchronous APIs.

```
Client

↓

API Gateway

↓

Lambda

↓

Response
```

Best suited for:

- REST APIs
- Authentication
- CRUD operations

---

# Event Processing Pattern

Instead of immediate responses:

```
Application

↓

SNS

↓

Lambda

↓

Processing
```

Useful when the client doesn't need an immediate result.

Examples:

- Email
- Notifications
- Report generation

---

# Fan-Out Pattern

One event triggers multiple independent consumers.

```
Order Created

↓

EventBridge

↓

───────────────

↓

Inventory Lambda

↓

Billing Lambda

↓

Notification Lambda

↓

Analytics Lambda
```

Each Lambda processes the event independently.

### Benefits

- High scalability
- Loose coupling
- Independent deployments

---

# Fan-In Pattern

Multiple producers send events to one consumer.

```
Website

↓

Mobile App

↓

Partner API

↓

SQS

↓

Lambda
```

Useful for centralized processing.

---

# Pipeline Pattern

Each Lambda performs one step.

```
Upload File

↓

Lambda A

↓

Lambda B

↓

Lambda C

↓

Store Result
```

Each stage has a single responsibility.

---

# Chained Lambda Pattern

```
Lambda A

↓

Lambda B

↓

Lambda C
```

Generally discouraged for long workflows.

Problems:

- Difficult debugging
- Complex retries
- Higher latency

Better solution:

```
Step Functions
```

---

# Orchestration Pattern

AWS Step Functions coordinate multiple Lambdas.

```
Step Functions

↓

Validate

↓

Charge Payment

↓

Reserve Inventory

↓

Send Email
```

Benefits:

- Visual workflows
- Retry policies
- Error handling
- State management

---

# Saga Pattern

Used for distributed transactions.

Example:

```
Payment

↓

Inventory

↓

Shipping
```

If Shipping fails:

```
Compensation

↓

Refund Payment

↓

Restore Inventory
```

Each successful step has a corresponding rollback action.

---

# Scatter-Gather Pattern

Large workloads are divided into smaller tasks.

```
Large Dataset

↓

Split

↓

Lambda A

Lambda B

Lambda C

↓

Merge Results
```

Useful for:

- Image processing
- Machine learning
- Data analytics

---

# Queue-Based Load Leveling

Instead of invoking Lambda directly:

```
Application

↓

SQS

↓

Lambda
```

Benefits:

- Absorb traffic spikes
- Automatic retries
- Prevent overload

---

# Retry Pattern

Transient failures should be retried.

```
Lambda

↓

External API

↓

Failure

↓

Retry

↓

Success
```

Use exponential backoff rather than immediate retries.

---

# Circuit Breaker Pattern

Protects downstream services.

```
Lambda

↓

Database

↓

Failure

↓

Circuit Opens

↓

Reject Requests
```

After recovery:

```
Half Open

↓

Healthy

↓

Closed
```

---

# Bulkhead Pattern

Separate workloads.

```
Payment Lambda

↓

Reserved Concurrency

----------------

Analytics Lambda

↓

Separate Concurrency
```

Failure in one workload doesn't impact another.

---

# Idempotency Pattern

Duplicate events happen.

```
SQS

↓

Lambda

↓

Retry

↓

Duplicate Event
```

Use an idempotency key.

```
Order ID

↓

Already Processed?

↓

Ignore Duplicate
```

---

# Dead Letter Pattern

```
SNS

↓

Lambda

↓

Failure

↓

DLQ
```

Allows investigation and replay.

---

# Event Replay Pattern

```
DLQ

↓

Replay Lambda

↓

Original Lambda
```

Useful after fixing bugs.

---

# Scheduler Pattern

```
EventBridge Schedule

↓

Lambda

↓

Cleanup

↓

Report

↓

Backup
```

Replaces traditional cron jobs.

---

# Aggregator Pattern

Multiple events become one result.

```
Lambda A

↓

Lambda B

↓

Lambda C

↓

Aggregator Lambda

↓

Summary Report
```

---

# CQRS Pattern

Separate reads and writes.

```
Write API

↓

Lambda

↓

Database

-------------------

Read API

↓

Lambda

↓

Read Replica
```

Improves scalability.

---

# Event Sourcing Pattern

Store every event instead of current state.

```
Account Created

↓

Money Deposited

↓

Money Withdrawn

↓

Current Balance
```

Lambda rebuilds state from events.

---

# Serverless ETL Pattern

```
S3

↓

Lambda

↓

Transform

↓

S3

↓

Redshift
```

Common in data engineering.

---

# AI Processing Pattern

```
Upload

↓

S3

↓

Lambda

↓

Bedrock

↓

Store Response
```

Useful for document processing and AI pipelines.

---

# Anti-Patterns

Avoid:

## Long Running Jobs

```
15 Minute Lambda

↓

Timeout
```

Use:

- ECS
- AWS Batch
- Fargate

---

## Monolithic Lambda

Bad:

```
One Lambda

↓

Authentication

↓

Payments

↓

Reports

↓

Email

↓

Analytics
```

Prefer small focused functions.

---

## Recursive Invocation

```
Lambda

↓

Invokes Itself

↓

Infinite Loop
```

Avoid unless carefully controlled.

---

## Tight Coupling

Bad

```
Lambda A

↓

Lambda B

↓

Lambda C

↓

Lambda D
```

Prefer EventBridge or SQS.

---

# Choosing the Right Pattern

| Requirement | Recommended Pattern |
|-------------|---------------------|
| REST API | Request-Response |
| Async Work | Event-Driven |
| Multiple Consumers | Fan-Out |
| Multiple Producers | Fan-In |
| Workflow | Step Functions |
| Distributed Transaction | Saga |
| Traffic Spikes | SQS Queue |
| Batch Processing | Scatter-Gather |
| Scheduled Tasks | EventBridge Scheduler |

---

# Real-World E-Commerce Architecture

```
Customer Places Order

↓

API Gateway

↓

Order Lambda

↓

EventBridge

────────────────────────────────────

↓

Inventory Lambda

↓

Payment Lambda

↓

Notification Lambda

↓

Analytics Lambda

↓

Fraud Detection Lambda

↓

CloudWatch
```

Every component is independent and scalable.

---

# Senior Backend Engineering Perspective

Experienced backend engineers design Lambda systems around **events**, not direct service dependencies.

Instead of creating tightly coupled microservices that invoke one another synchronously, modern architectures use EventBridge, SQS, SNS, and Step Functions to coordinate workflows.

The guiding principles are:

- Loose coupling
- Independent scaling
- Fault isolation
- Idempotent processing
- Asynchronous communication
- Observability
- Automated recovery

Selecting the correct design pattern is often more important than optimizing individual Lambda functions. Well-chosen patterns improve scalability, resilience, maintainability, and operational simplicity across the entire serverless platform.

---

# Interview Questions

### Beginner

- What is an event-driven architecture?
- What is the difference between synchronous and asynchronous Lambda invocation?
- Why is SQS commonly used with Lambda?

### Intermediate

- Explain the Fan-Out and Fan-In patterns.
- What is the Saga pattern?
- Why is Step Functions preferred over chaining Lambda functions?

### Senior

- Design an event-driven e-commerce platform using Lambda.
- How would you prevent duplicate event processing?
- Compare EventBridge, SNS, and SQS for different architectural patterns.
- Which Lambda design patterns improve resilience in distributed systems?

---

# Key Takeaways

- Design patterns provide proven architectural solutions for building scalable and resilient serverless applications.
- Event-driven architectures, Fan-Out, Fan-In, and Queue-Based Load Leveling are foundational patterns in AWS Lambda.
- Step Functions are preferred for orchestrating complex workflows, while Saga patterns handle distributed transactions.
- Idempotency, retries, circuit breakers, and dead-letter queues improve fault tolerance and operational reliability.
- Choosing the right architectural pattern has a greater impact on system quality than optimizing individual Lambda functions.