# 04- Lambda Event Sources.md

# Lambda Event Sources

An **event source** is any AWS service or external application capable of triggering a Lambda function.

Every Lambda invocation begins with an event. This event contains the data that the function processes.

Understanding event sources is critical because each source has different:

- Invocation model
- Retry behavior
- Scaling characteristics
- Ordering guarantees
- Failure handling

A senior backend engineer should design Lambda applications around the characteristics of the event source rather than treating all triggers identically.

---

# Event-Driven Architecture

Lambda follows an event-driven architecture.

```text
                Event

                  │

                  ▼

          Event Source

                  │

                  ▼

             AWS Lambda

                  │

                  ▼

        Business Logic Executes
```

Every AWS service generates events in its own format.

---

# Types of Event Sources

AWS Lambda event sources fall into three categories.

```text
                Event Sources

                     │

     ┌───────────────┼────────────────┐

     │               │                │

Synchronous     Asynchronous     Poll-Based
```

---

# Synchronous Event Sources

These services invoke Lambda immediately and wait for a response.

```text
Client

↓

Service

↓

Lambda

↓

Response
```

Examples:

- API Gateway
- Application Load Balancer
- Function URL
- AWS SDK
- AWS CLI

---

## Example

```text
Browser

↓

API Gateway

↓

Lambda

↓

Response

↓

Browser
```

The client waits until Lambda completes execution.

---

# Asynchronous Event Sources

These services send events to Lambda without waiting for execution.

```text
Event

↓

Lambda Queue

↓

Lambda

↓

Background Processing
```

Examples:

- Amazon S3
- EventBridge
- SNS
- CloudWatch Events
- CodePipeline
- CodeCommit

---

## Example

```text
Image Uploaded

↓

S3

↓

Lambda

↓

Generate Thumbnail
```

The upload finishes immediately.

Image processing occurs later.

---

# Poll-Based Event Sources

Some AWS services store events until Lambda retrieves them.

AWS creates an Event Source Mapping that continuously polls these services.

```text
Queue

↓

AWS Poller

↓

Lambda
```

Examples:

- SQS
- SQS FIFO
- DynamoDB Streams
- Kinesis Data Streams
- Amazon MSK
- Amazon MQ

---

# Event Source Categories

| Event Source | Invocation Type |
|--------------|----------------|
| API Gateway | Synchronous |
| ALB | Synchronous |
| Function URL | Synchronous |
| S3 | Asynchronous |
| SNS | Asynchronous |
| EventBridge | Asynchronous |
| CloudWatch Schedule | Asynchronous |
| SQS | Poll-Based |
| DynamoDB Streams | Poll-Based |
| Kinesis Streams | Poll-Based |
| MSK | Poll-Based |

---

# Amazon S3

One of the most common Lambda integrations.

S3 generates events whenever objects change.

Supported events include:

- ObjectCreated
- ObjectRemoved
- ObjectRestore
- Replication
- Lifecycle transitions

Example:

```text
User Uploads File

↓

S3 Bucket

↓

Lambda

↓

Virus Scan

↓

Move to Processed Folder
```

---

## Typical Use Cases

- Image resizing
- PDF generation
- Virus scanning
- Metadata extraction
- OCR
- Thumbnail generation

---

# API Gateway

API Gateway transforms an HTTP request into a Lambda event.

```text
HTTP Request

↓

API Gateway

↓

JSON Event

↓

Lambda
```

Example event:

```json
{
  "httpMethod":"GET",
  "path":"/users/10",
  "headers":{},
  "queryStringParameters":{}
}
```

---

## Typical Use Cases

- REST APIs
- CRUD applications
- Authentication
- Mobile backend
- Microservices

---

# Application Load Balancer (ALB)

ALB can directly invoke Lambda.

```text
Client

↓

ALB

↓

Lambda

↓

HTTP Response
```

Useful when:

- Existing ALB infrastructure exists
- Mixed EC2 + Lambda workloads
- Gradual migration to serverless

---

# Lambda Function URL

A Function URL provides a dedicated HTTPS endpoint.

```text
Internet

↓

Function URL

↓

Lambda
```

No API Gateway required.

Best suited for:

- Internal APIs
- Webhooks
- Lightweight services
- Testing

---

# Amazon EventBridge

EventBridge routes events between AWS services.

```text
Application

↓

EventBridge

↓

Lambda

↓

Process Event
```

Example:

```text
EC2 State Change

↓

EventBridge

↓

Lambda

↓

Notify Slack
```

---

## EventBridge Use Cases

- Automation
- Infrastructure monitoring
- Event-driven microservices
- Scheduled jobs
- Business workflows

---

# Amazon SNS

SNS broadcasts one event to many subscribers.

```text
SNS Topic

     │

 ┌───┼─────┐

 │   │     │

 ▼   ▼     ▼

Lambda Email SQS
```

Lambda is just one subscriber.

---

## Typical Use Cases

- Notifications
- Fan-out architecture
- Alert systems
- Microservice communication

---

# Amazon SQS

Unlike SNS, SQS stores messages.

Lambda reads them using Event Source Mapping.

```text
Application

↓

SQS

↓

Lambda Poller

↓

Lambda
```

---

## Typical Use Cases

- Background jobs
- Queue workers
- Order processing
- Payment processing

---

# DynamoDB Streams

Every change in DynamoDB can generate a stream record.

```text
Insert

↓

Update

↓

Delete

↓

Stream

↓

Lambda
```

Example:

```text
Customer Created

↓

DynamoDB

↓

Stream

↓

Lambda

↓

Send Welcome Email
```

---

# Kinesis Data Streams

Designed for high-throughput streaming data.

```text
IoT Devices

↓

Kinesis

↓

Lambda

↓

Analytics
```

Lambda processes batches from each shard.

---

## Typical Use Cases

- Clickstream analytics
- IoT telemetry
- Financial transactions
- Log processing

---

# CloudWatch Scheduler

CloudWatch Scheduler invokes Lambda on a schedule.

```text
Every Day 2 AM

↓

Scheduler

↓

Lambda

↓

Cleanup Logs
```

Supports cron expressions.

Example:

```
0 2 * * ? *
```

Run daily at 2 AM.

---

# Step Functions

Step Functions orchestrate multiple Lambda functions.

```text
Start

↓

Lambda A

↓

Decision

↓

Lambda B

↓

Lambda C

↓

End
```

Ideal for:

- Long-running workflows
- Retry orchestration
- Human approval processes

---

# Cognito

Cognito can invoke Lambda during authentication.

Examples:

- Pre Sign-Up
- Post Confirmation
- Custom Authentication
- Token Generation

```text
User Login

↓

Cognito

↓

Lambda

↓

Allow Login
```

---

# CloudFront

Lambda@Edge runs in response to CloudFront events.

```text
Viewer Request

↓

CloudFront

↓

Lambda@Edge

↓

Origin
```

Typical uses:

- URL rewriting
- Authentication
- Header manipulation
- Personalization

---

# CloudFront Functions

Lighter alternative to Lambda@Edge.

```text
Viewer Request

↓

CloudFront Function

↓

Modified Request
```

Designed for:

- Header changes
- Redirects
- Cache key normalization

---

# AWS Service Integration Overview

| AWS Service | Typical Backend Use Case |
|--------------|-------------------------|
| API Gateway | REST APIs |
| ALB | HTTP Applications |
| S3 | File Processing |
| EventBridge | Event Routing |
| SNS | Fan-out Messaging |
| SQS | Queue Processing |
| DynamoDB Streams | Change Data Capture |
| Kinesis | Streaming Analytics |
| CloudWatch Scheduler | Cron Jobs |
| Cognito | Authentication |
| CloudFront | Edge Computing |
| Step Functions | Workflow Orchestration |

---

# Choosing the Right Event Source

| Requirement | Recommended Source |
|-------------|--------------------|
| REST API | API Gateway |
| Background Processing | SQS |
| File Upload Processing | S3 |
| Scheduled Jobs | EventBridge Scheduler |
| Change Data Capture | DynamoDB Streams |
| Streaming Analytics | Kinesis |
| Fan-out Notifications | SNS |
| Business Events | EventBridge |
| Authentication Hooks | Cognito |

---

# Common Design Mistakes

## Treating All Event Sources the Same

Every event source has different:

- Retry behavior
- Event format
- Ordering guarantees
- Scaling model

Always understand the characteristics of the source before designing your Lambda.

---

## Doing Heavy Processing in APIs

Bad:

```text
API Gateway

↓

Lambda

↓

Generate Report

↓

Resize Images

↓

Send Emails

↓

Return
```

The client waits unnecessarily.

---

Better:

```text
API Gateway

↓

Lambda

↓

Publish EventBridge Event

↓

Background Lambdas
```

---

## Ignoring Duplicate Events

Services like S3, SNS, EventBridge, and SQS can deliver duplicate events.

Design handlers to be **idempotent**.

---

# Senior Backend Engineering Perspective

Experienced engineers choose event sources based on workload characteristics:

- **API Gateway** for user-facing APIs.
- **EventBridge** for loosely coupled event-driven architectures.
- **SNS** for fan-out notifications.
- **SQS** for durable background processing.
- **DynamoDB Streams** for Change Data Capture (CDC).
- **Kinesis** for real-time analytics and high-throughput streaming.
- **Step Functions** for orchestrating complex workflows.

Understanding how each event source delivers, retries, and scales events is essential for building reliable serverless systems.

---

# Interview Questions

### Beginner

- What is an event source?
- Which AWS services can trigger Lambda?
- Can S3 invoke Lambda directly?

### Intermediate

- Difference between SNS and SQS as Lambda triggers?
- Why does SQS require Event Source Mapping?
- How does EventBridge differ from SNS?

### Senior

- Which event source would you choose for an order processing system?
- How would you process millions of streaming events?
- When would you choose DynamoDB Streams over EventBridge?
- How do different event sources affect retry behavior and scalability?

---

# Key Takeaways

- Lambda executes in response to events generated by AWS services or external applications.
- Event sources are categorized as synchronous, asynchronous, or poll-based.
- Each event source has unique invocation semantics, retry behavior, and scalability characteristics.
- Selecting the appropriate event source is a key architectural decision that influences application reliability, performance, and operational complexity.