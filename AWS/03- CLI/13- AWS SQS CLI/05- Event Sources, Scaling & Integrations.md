# Event Sources, Scaling & Integrations

> Learn how Amazon SQS integrates with AWS services and how to build scalable event-driven architectures. This chapter covers Lambda event source mappings, ECS workers, EC2 consumers, Auto Scaling, EventBridge, Amazon SNS integration, CloudWatch monitoring, and production messaging architectures.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Integrate Amazon SQS with AWS services
- Configure Lambda event sources
- Build scalable worker architectures
- Understand polling behavior
- Configure Auto Scaling
- Build event-driven systems
- Monitor queue health
- Design production message processing pipelines

---

# Event-Driven Architecture

Amazon SQS enables asynchronous event-driven systems.

```text
Producer

↓

Amazon SQS

↓

Consumers

↓

Database
```

The producer never waits for processing to finish.

---

# Common AWS Integrations

Amazon SQS integrates with:

```text
Amazon SQS

│

├── AWS Lambda

├── Amazon ECS

├── Amazon EC2

├── Amazon SNS

├── Amazon EventBridge

├── AWS Step Functions

└── AWS Batch
```

---

# Lambda Integration

Amazon Lambda can automatically poll an SQS queue.

Architecture:

```text
Amazon SQS

↓

Lambda

↓

Database
```

No custom polling application is required.

---

# Lambda Event Source Mapping

Lambda uses an **Event Source Mapping**.

```text
Amazon SQS

↓

Event Source Mapping

↓

Lambda
```

AWS continuously polls the queue on behalf of Lambda.

---

# Create Event Source Mapping

```bash
aws lambda create-event-source-mapping \
--event-source-arn QUEUE_ARN \
--function-name ProcessOrders
```

---

# Lambda Processing Workflow

```text
Producer

↓

Amazon SQS

↓

Lambda

↓

Process Message

↓

Delete Message
```

Successful executions automatically delete messages.

---

# Failed Lambda Execution

If Lambda fails:

```text
Receive

↓

Lambda Error

↓

Visibility Timeout

↓

Retry
```

Eventually:

```text
Dead Letter Queue
```

if configured.

---

# Batch Processing

Lambda retrieves messages in batches.

Example:

```text
Batch Size

↓

10 Messages
```

Processing batches improves throughput.

---

# ECS Integration

Long-running workloads often use Amazon ECS.

Architecture:

```text
Amazon SQS

↓

Amazon ECS

↓

Workers
```

Containers continuously poll the queue.

---

# ECS Worker Pattern

```text
Amazon ECS

↓

Receive Message

↓

Process

↓

Delete Message
```

Applications control polling frequency.

---

# EC2 Worker Pattern

Traditional worker architecture:

```text
Amazon SQS

↓

EC2 Worker

↓

Database
```

Useful for:

- Legacy applications
- Long-running jobs
- Custom processing

---

# Kubernetes Integration

Applications running on Kubernetes can poll SQS.

```text
Amazon SQS

↓

Kubernetes Pods

↓

Consumers
```

Each Pod acts as a worker.

---

# Worker Scaling

Queue depth determines worker count.

```text
Queue

↓

Many Messages

↓

More Workers
```

As messages decrease:

```text
Workers

↓

Scale Down
```

---

# Auto Scaling Workflow

```text
CloudWatch

↓

Queue Depth

↓

Auto Scaling

↓

More Consumers
```

Applications automatically scale based on workload.

---

# CloudWatch Metrics

Monitor:

- ApproximateNumberOfMessagesVisible
- ApproximateAgeOfOldestMessage
- NumberOfMessagesReceived
- NumberOfMessagesDeleted
- EmptyReceives

---

# Queue Depth Monitoring

```text
10 Messages

↓

Healthy
```

```text
10,000 Messages

↓

Increase Consumers
```

Queue depth is one of the most important operational metrics.

---

# SNS Integration

Amazon SNS can publish directly to Amazon SQS.

Architecture:

```text
Publisher

↓

Amazon SNS

↓

Amazon SQS

↓

Consumers
```

This enables fan-out messaging.

---

# Fan-Out Architecture

```text
Application

↓

Amazon SNS

│

├── Queue A

├── Queue B

└── Queue C
```

Each consumer processes messages independently.

---

# EventBridge Integration

Amazon EventBridge routes AWS events into Amazon SQS.

```text
AWS Event

↓

EventBridge

↓

Amazon SQS

↓

Consumer
```

Useful for automation workflows.

---

# Step Functions Integration

A Step Functions workflow can send messages.

```text
Step Function

↓

Amazon SQS

↓

Worker
```

Supports asynchronous processing.

---

# Batch Jobs

Large workloads:

```text
Amazon SQS

↓

AWS Batch

↓

Compute Jobs
```

Examples:

- Video processing
- Scientific computing
- Data transformation

---

# API Workflow

Typical backend architecture:

```text
Client

↓

API

↓

Amazon SQS

↓

Workers

↓

Amazon RDS
```

The API responds immediately while work continues in the background.

---

# High-Throughput Architecture

```text
Users

↓

Load Balancer

↓

Backend API

↓

Amazon SQS

↓

100 Workers
```

Workers scale independently of the API.

---

# Multi-Service Architecture

```text
Order Service

↓

Amazon SQS

↓

Inventory Service

↓

Notification Service

↓

Billing Service
```

Each service remains loosely coupled.

---

# Retry Workflow

```text
Message

↓

Failure

↓

Retry

↓

Success

────────────

Failure

↓

Dead Letter Queue
```

---

# Consumer Scaling Strategy

Recommended:

```text
Low Queue Depth

↓

Few Workers

────────────

High Queue Depth

↓

Many Workers
```

---

# CloudWatch Alarms

Create alarms for:

```text
Queue Depth
```

```text
Oldest Message Age
```

```text
Dead Letter Queue Size
```

---

# Performance Optimization

For higher throughput:

- Enable Long Polling.
- Process messages in batches.
- Increase worker count.
- Keep messages small.
- Design idempotent consumers.
- Monitor queue depth.

---

# Common Errors

## Lambda Not Processing

Verify:

- Event Source Mapping
- IAM Role
- Queue ARN
- Lambda permissions

---

## Messages Not Deleted

Verify:

- Consumer completed successfully
- DeleteMessage called
- Receipt Handle valid

---

## Queue Growing

Possible causes:

- Consumers too slow
- Consumer failures
- Insufficient worker count

Scale consumers.

---

## DLQ Increasing

Investigate:

- Application bugs
- Database failures
- External API failures
- Invalid message format

---

# Production Best Practices

- Use Lambda for lightweight event processing.
- Use ECS or EC2 for long-running workloads.
- Scale consumers based on queue depth.
- Configure CloudWatch alarms.
- Monitor Dead Letter Queues.
- Use SNS for fan-out messaging.
- Integrate EventBridge for AWS event routing.
- Keep consumers stateless.
- Process messages idempotently.
- Continuously monitor processing latency.

---

# Real-World Workflow

```text
User

↓

Backend API

↓

Amazon SQS

↓

Amazon ECS

↓

Amazon RDS

↓

Notification
```

---

# Enterprise Architecture

```text
Users
      │
      ▼
Application Load Balancer
      │
      ▼
Backend API
      │
      ▼
Amazon SQS
      │
      ├── AWS Lambda
      ├── Amazon ECS
      ├── AWS Batch
      └── Dead Letter Queue
              │
              ▼
Amazon RDS
```

Amazon SQS serves as the asynchronous communication layer, allowing compute resources such as Lambda functions and ECS tasks to scale independently while maintaining reliable message delivery.

---

# Interview Note

### Question

**How does Amazon SQS integrate with AWS Lambda?**

### Answer

Amazon SQS integrates with AWS Lambda through an **Event Source Mapping**. AWS continuously polls the queue on behalf of the Lambda function. When messages become available, Lambda invokes the function with a batch of messages. If processing succeeds, Lambda automatically deletes the messages from the queue. If processing fails, the messages become visible again after the Visibility Timeout expires and are retried until they are successfully processed or moved to a Dead Letter Queue based on the configured Redrive Policy.

---

# Key Takeaways

- Amazon SQS integrates natively with Lambda, ECS, EC2, SNS, EventBridge, and Step Functions.
- Lambda uses Event Source Mappings to poll SQS automatically.
- ECS and EC2 workers provide greater control for long-running workloads.
- CloudWatch metrics and alarms help determine when to scale consumers.
- Queue depth is a primary metric for worker scaling.
- SNS and EventBridge extend SQS into larger event-driven architectures.
- Production systems combine SQS, scalable consumers, monitoring, and Dead Letter Queues to build resilient, loosely coupled applications.