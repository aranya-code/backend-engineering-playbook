# README

## Overview

Amazon S3 event-driven integrations cover the configuration patterns and processing workflows required to react to S3 object events asynchronously. It addresses S3 event notification configuration, Lambda direct invocation, SNS fan-out to multiple consumers, SQS-based reliable processing, EventBridge routing for complex event patterns, and end-to-end event-driven processing workflow design.

This section provides structured guidance for backend engineers who build asynchronous processing pipelines triggered by S3 object events: configuring notifications correctly, designing reliable processing with dead-letter queues, and composing multi-service event workflows.

## Navigation

| # | File | Description |
|---|---|---|
| 01 | [01- S3 Event Notifications](./01-%20S3%20Event%20Notifications.md) | Configuring S3 event notifications for object creation, deletion, and restoration events to Lambda, SQS, and SNS targets |
| 02 | [02- AWS Lambda Integration](./02-%20AWS%20Lambda%20Integration.md) | Invoking Lambda functions directly from S3 events for synchronous-style processing of uploaded objects |
| 03 | [03- Amazon SNS Integration](./03-%20Amazon%20SNS%20Integration.md) | Publishing S3 events to SNS topics for fan-out delivery to multiple downstream consumers and endpoints |
| 04 | [04- Amazon SQS Integration](./04-%20Amazon%20SQS%20Integration.md) | Delivering S3 events to SQS queues for decoupled, reliable asynchronous processing with consumer-controlled throughput |
| 05 | [05- Amazon EventBridge Integration](./05-%20Amazon%20EventBridge%20Integration.md) | Routing S3 events through EventBridge rules to multiple targets with pattern matching and cross-account delivery |
| 06 | [06- Event-Driven Processing Workflows](./06-%20Event-Driven%20Processing%20Workflows.md) | Composing end-to-end event-driven workflows that combine S3 notifications, queues, functions, and downstream services |

## Why Event-Driven S3 Integration Matters

Coupling file storage directly to processing logic — calling a processing function synchronously during the upload request — creates tight dependencies, increases upload latency, and makes retries and failure handling complex. Event-driven architectures decouple storage from processing, allowing each to scale independently and fail independently.

Common integration risks include:

- S3 event notification configured before the Lambda resource-based permission exists, causing all events to fail with access denied.
- No dead-letter queue on the Lambda function or SQS consumer, causing failed processing to be silently discarded.
- Processing logic not idempotent, causing duplicate processing when S3 delivers the same event more than once.
- EventBridge not enabled on the S3 bucket before configuring EventBridge rules, causing events to never arrive at the bus.
- SNS topic without an SQS subscription, causing events to be lost if the downstream HTTP endpoint is temporarily unavailable.

## Core Integration Principles

- Always configure a dead-letter queue for Lambda functions and SQS consumers that process S3 events; failed events must be preserved for investigation and replay.
- Design event processing logic to be idempotent; S3 event notifications can be delivered more than once.
- Deploy the Lambda resource-based permission before configuring the S3 event notification; configuring the notification first causes all events to fail immediately.

## Key Takeaways

- S3 event notifications require both the notification configuration and the target resource permission (Lambda resource-based policy, SQS queue policy, or SNS topic policy) to be correctly configured.
- Idempotent processing is essential because S3 may deliver the same event notification more than once; processing the same event twice must produce the same result.
- Dead-letter queues are not optional for production event-driven pipelines; without one, failed processing is discarded silently with no investigation or replay capability.
