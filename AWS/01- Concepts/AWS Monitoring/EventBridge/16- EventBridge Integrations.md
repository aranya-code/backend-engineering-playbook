# EventBridge Integrations

Amazon EventBridge integrates with hundreds of AWS services and SaaS applications, making it the central event router for cloud-native architectures.

These integrations enable applications to react automatically to events without requiring custom polling or direct service-to-service communication.

------------------------------------------------------------------------

# Why EventBridge Integrations?

EventBridge integrations help you:

- Build serverless applications
- Automate workflows
- Reduce application coupling
- Connect AWS services
- Integrate SaaS applications
- Trigger business processes

------------------------------------------------------------------------

# AWS Lambda

Lambda is the most common EventBridge target.

Example:

```text
S3 Upload

↓

EventBridge

↓

Lambda

↓

Generate Thumbnail
```

------------------------------------------------------------------------

# Amazon SQS

EventBridge can send events to SQS for asynchronous processing.

Example:

```text
Order Created

↓

EventBridge

↓

SQS

↓

Worker Service
```

------------------------------------------------------------------------

# Amazon SNS

SNS distributes notifications to subscribers.

Example:

```text
Security Event

↓

EventBridge

↓

SNS

↓

Email

SMS

Lambda
```

------------------------------------------------------------------------

# AWS Step Functions

EventBridge can start workflows.

Example:

```text
Payment Completed

↓

Step Functions

↓

Validate Payment

↓

Update Inventory

↓

Send Email
```

------------------------------------------------------------------------

# Amazon ECS

EventBridge can launch ECS Tasks.

Example:

```text
Nightly Job

↓

EventBridge

↓

ECS Task
```

------------------------------------------------------------------------

# Amazon S3

Amazon S3 generates events for:

- Object Created
- Object Deleted
- Object Restored

These events can trigger downstream workflows.

------------------------------------------------------------------------

# AWS CloudTrail

CloudTrail records AWS API activity.

Example:

```text
IAM User Created

↓

CloudTrail

↓

EventBridge

↓

SNS Notification
```

Useful for security automation.

------------------------------------------------------------------------

# Amazon DynamoDB

DynamoDB Streams can integrate with EventBridge for event-driven processing.

Example:

```text
Item Updated

↓

EventBridge

↓

Lambda
```

------------------------------------------------------------------------

# Amazon API Gateway

API Gateway events can trigger workflows through EventBridge.

Useful for:

- Request processing
- Auditing
- Notifications

------------------------------------------------------------------------

# SaaS Integrations

EventBridge supports partner integrations with:

- Datadog
- Zendesk
- PagerDuty
- Auth0
- Shopify
- Snowflake

These services publish events directly to EventBridge.

------------------------------------------------------------------------

# Integration Architecture

```text
AWS Services

Custom Apps

SaaS Partners

      |

      v

Amazon EventBridge

      |

      v

Lambda

SQS

SNS

Step Functions

API Destinations
```

------------------------------------------------------------------------

# Real-World Example

An online retailer integrates:

- Amazon S3
- AWS Lambda
- Amazon SQS
- Step Functions
- Slack (API Destination)

When a customer uploads a product image:

1. Amazon S3 generates an event.
2. EventBridge routes it to Lambda.
3. Lambda processes the image.
4. Step Functions updates the catalog.
5. Slack receives a notification via API Destination.

------------------------------------------------------------------------

# Best Practices

- Prefer EventBridge over direct service integrations.
- Keep services loosely coupled.
- Use retries and DLQs where supported.
- Monitor integrations using CloudWatch.
- Use Event Patterns to reduce unnecessary processing.

------------------------------------------------------------------------

# Key Takeaways

- EventBridge integrates with hundreds of AWS services and SaaS applications.
- It enables scalable, event-driven architectures.
- AWS Lambda, SQS, SNS, Step Functions, ECS, and API Destinations are common integration targets.
- EventBridge simplifies application integration while improving scalability and maintainability.