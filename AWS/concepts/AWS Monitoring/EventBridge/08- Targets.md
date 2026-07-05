# Targets

A **Target** is the destination where Amazon EventBridge sends an event after it matches an Event Rule. Targets perform the actual work in an event-driven architecture.

An EventBridge Rule can invoke one or multiple targets, enabling a single event to trigger multiple workflows simultaneously.

------------------------------------------------------------------------

# What is a Target?

A Target is any AWS service or supported external endpoint capable of receiving an event from EventBridge.

Example:

```text
Event

↓

EventBridge Rule

↓

AWS Lambda
```

The Lambda function receives the event and executes its business logic.

------------------------------------------------------------------------

# Why Use Targets?

Targets allow EventBridge to:

- Process business logic
- Send notifications
- Store messages
- Start workflows
- Trigger containers
- Invoke external APIs
- Stream data

------------------------------------------------------------------------

# Supported Targets

EventBridge supports numerous AWS services.

Common targets include:

- AWS Lambda
- Amazon SQS
- Amazon SNS
- AWS Step Functions
- Amazon ECS
- AWS Batch
- Amazon Kinesis Data Streams
- Amazon API Gateway
- CloudWatch Logs
- Event Bus
- API Destinations

------------------------------------------------------------------------

# AWS Lambda

Lambda is one of the most commonly used EventBridge targets.

Example:

```text
S3 Upload Event

↓

EventBridge

↓

Lambda

↓

Resize Image
```

Ideal for serverless applications.

------------------------------------------------------------------------

# Amazon SQS

Events can be delivered to Amazon SQS for asynchronous processing.

Example:

```text
Order Created

↓

SQS Queue

↓

Worker Application
```

Useful when events need to be processed later.

------------------------------------------------------------------------

# Amazon SNS

SNS delivers notifications to multiple subscribers.

Example:

```text
Security Alert

↓

SNS Topic

↓

Email

SMS

Lambda
```

Ideal for notifications.

------------------------------------------------------------------------

# AWS Step Functions

EventBridge can start complex workflows.

Example:

```text
Payment Completed

↓

Step Functions

↓

Validate

↓

Update Inventory

↓

Send Email
```

Useful for orchestrating business processes.

------------------------------------------------------------------------

# Amazon ECS

EventBridge can start ECS Tasks.

Example:

```text
Nightly Report

↓

EventBridge

↓

ECS Task

↓

Generate Report
```

------------------------------------------------------------------------

# AWS Batch

Batch jobs can be triggered automatically.

Example:

```text
Data Upload

↓

AWS Batch

↓

Process Files
```

------------------------------------------------------------------------

# API Destinations

EventBridge can invoke external REST APIs.

Examples:

- Slack
- Jira
- GitHub
- ServiceNow

Authentication methods include:

- API Key
- Basic Authentication
- OAuth

------------------------------------------------------------------------

# Multiple Targets

A single rule may invoke multiple targets.

```text
Order Created

↓

Rule

↓

+---------+----------+-----------+

|          |          |

v          v          v

Lambda     SQS       SNS
```

Every configured target receives the matching event.

------------------------------------------------------------------------

# Target Retry Policy

If target delivery fails, EventBridge retries automatically.

Retry configuration includes:

- Maximum Retry Attempts
- Maximum Event Age

If retries fail, the event can be sent to a Dead-Letter Queue (DLQ).

------------------------------------------------------------------------

# Dead-Letter Queue (DLQ)

A DLQ stores events that could not be delivered.

Benefits:

- Prevents data loss
- Enables troubleshooting
- Supports replay

Amazon SQS is commonly used as a DLQ.

------------------------------------------------------------------------

# Real-World Example

When a customer places an order:

```text
Order Created

↓

EventBridge Rule

↓

Lambda

↓

SQS

↓

Analytics Event Bus

↓

SNS
```

Each target processes the event independently without affecting the others.

------------------------------------------------------------------------

# Best Practices

- Keep targets independent.
- Use Lambda for lightweight processing.
- Use SQS for asynchronous workloads.
- Configure retry policies.
- Configure DLQs.
- Monitor target failures using CloudWatch.

------------------------------------------------------------------------

# Key Takeaways

- Targets receive events after rules match.
- One rule can invoke multiple targets.
- EventBridge supports AWS services and external APIs.
- Retry policies and DLQs improve reliability.