# Introduction

Every Amazon SQS queue has a collection of **attributes** that control how the queue behaves.

These attributes determine:

- How long messages are stored
- When messages become visible
- Whether messages are encrypted
- Whether failed messages move to a Dead Letter Queue (DLQ)
- How consumers receive messages

Properly configuring queue attributes is essential for building reliable and scalable messaging systems.

---

# What are Queue Attributes?

Queue attributes are configuration settings associated with an Amazon SQS queue.

They define the operational behavior of the queue and affect how producers and consumers interact with messages.

Some attributes can be configured when the queue is created, while others can be modified later.

---

# Queue Attributes Overview

The following table summarizes the most commonly used queue attributes.

| Attribute | Description |
|------------|-------------|
| Message Retention Period | Duration for which messages remain in the queue |
| Visibility Timeout | Time a received message remains invisible to other consumers |
| Delivery Delay | Delays newly sent messages before they become visible |
| Maximum Message Size | Maximum size allowed for a single message |
| Receive Message Wait Time | Configures Long Polling |
| Redrive Policy | Sends failed messages to a Dead Letter Queue |
| Server-Side Encryption | Encrypts messages stored in the queue |
| Queue ARN | Unique identifier used by AWS services |
| Tags | Key-value pairs used for resource organization |

---

# Message Retention Period

The **Message Retention Period** determines how long Amazon SQS stores a message if it is not deleted.

If a consumer never processes the message, Amazon SQS automatically removes it after the retention period expires.

---

## Default Value

```
4 Days
```

---

## Allowed Range

| Minimum | Maximum |
|----------|----------|
| 1 Minute | 14 Days |

---

## Example

```
Producer

↓

Send Message

↓

Queue

↓

Message Remains

↓

4 Days

↓

Automatically Deleted
```

---

## Why Increase the Retention Period?

Longer retention periods are useful when:

- Consumers may be temporarily unavailable.
- Messages need to be replayed.
- Disaster recovery requires longer storage.

Example

```
Consumer Offline

↓

Queue Stores Messages

↓

Consumer Recovers

↓

Processes Messages
```

---

## When to Use a Short Retention Period

Short retention periods are suitable when:

- Messages become obsolete quickly.
- High message volume requires efficient cleanup.
- Storage duration should be minimized.

Examples

- Temporary notifications
- Session events
- Short-lived application logs

---

# Visibility Timeout

The **Visibility Timeout** defines how long a message remains invisible after being received by a consumer.

Receiving a message does **not** remove it from the queue.

Instead, Amazon SQS temporarily hides it from other consumers.

---

## Default Value

```
30 Seconds
```

---

## Maximum Value

```
12 Hours
```

---

## Example

```
Receive Message

↓

Invisible

↓

Processing

↓

Delete
```

If processing fails,

```
Receive

↓

Crash

↓

Visibility Timeout Ends

↓

Visible Again
```

Another consumer can then process the message.

> **Note:** Visibility Timeout is a major topic and will be covered in detail in **06- Visibility Timeout.md**.

---

# Delivery Delay

The **Delivery Delay** attribute postpones the availability of newly sent messages.

Instead of appearing immediately, messages remain hidden until the configured delay expires.

---

## Maximum Delay

```
15 Minutes
```

---

## Example

```
Producer

↓

Send Message

↓

Hidden

↓

5 Minutes

↓

Visible

↓

Consumer
```

---

## Common Use Cases

- Delayed notifications
- Retry workflows
- Scheduled processing
- Order cancellation grace periods

---

# Maximum Message Size

Amazon SQS limits the size of each message.

---

## Maximum Value

```
256 KB
```

---

## What if Data is Larger?

Instead of sending the entire file,

store it in Amazon S3.

Only send the object reference through SQS.

Example

```
Large File

↓

Amazon S3

↓

Object URL

↓

Amazon SQS
```

This pattern is commonly called the **S3 Extended Payload Pattern**.

---

## Best Practice

Large binary files such as:

- Images
- Videos
- PDF documents

should always be stored in Amazon S3 rather than inside the message body.

---

# Receive Message Wait Time

This attribute enables **Long Polling**.

Instead of immediately returning an empty response,

Amazon SQS waits for a message to become available.

---

## Default Value

```
0 Seconds
```

---

## Maximum Value

```
20 Seconds
```

---

## Example

Without Long Polling

```
Consumer

↓

ReceiveMessage()

↓

No Messages

↓

Empty Response
```

With Long Polling

```
Consumer

↓

ReceiveMessage()

↓

Wait

↓

Message Arrives

↓

Return Message
```

Long Polling reduces unnecessary API calls and lowers AWS costs.

A dedicated chapter discusses this in detail.

---

# Redrive Policy

The **Redrive Policy** determines when failed messages are moved to a **Dead Letter Queue (DLQ)**.

It consists of two main settings:

- Dead Letter Queue ARN
- Maximum Receive Count

---

## Example

```
Message

↓

Receive

↓

Failure

↓

Retry

↓

Failure

↓

Retry

↓

Failure

↓

Move to DLQ
```

---

## Maximum Receive Count

This value specifies how many processing attempts are allowed before the message is moved to the DLQ.

Example

```
Maximum Receive Count = 5
```

After the fifth unsuccessful attempt,

the message is transferred to the configured Dead Letter Queue.

---

# Server-Side Encryption (SSE)

Amazon SQS supports encryption for messages stored in the queue.

Encryption helps protect sensitive data.

---

## Supported Options

- AWS Managed KMS Key (`alias/aws/sqs`)
- Customer Managed KMS Key (CMK)

---

## Encryption Flow

```
Producer

↓

Encrypt

↓

Amazon SQS

↓

Encrypted Storage

↓

Decrypt

↓

Consumer
```

Encryption and decryption occur automatically.

---

## Benefits

- Protects sensitive data.
- Meets compliance requirements.
- Integrates with AWS KMS.
- Minimal operational overhead.

---

# Queue ARN

Every Amazon SQS queue has a unique **Amazon Resource Name (ARN)**.

Example

```text
arn:aws:sqs:us-east-1:123456789012:OrderQueue
```

---

## Why is the ARN Important?

The ARN is used by:

- IAM Policies
- Queue Policies
- Amazon SNS subscriptions
- Amazon S3 event notifications
- AWS Lambda event sources

---

# Queue Tags

Tags are metadata in the form of key-value pairs.

Example

| Key | Value |
|------|-------|
| Environment | Production |
| Team | Backend |
| Application | OrderService |
| CostCenter | Finance |

---

## Benefits

Tags help with:

- Cost allocation
- Resource organization
- Automation
- Governance
- Reporting

---

# Viewing Queue Attributes

Queue attributes can be viewed using:

- AWS Management Console
- AWS CLI
- AWS SDKs (Boto3, Java, etc.)
- CloudFormation
- Terraform

---

## AWS CLI Example

```bash
aws sqs get-queue-attributes \
    --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/OrderQueue \
    --attribute-names All
```

---

## Boto3 Example

```python
import boto3

sqs = boto3.client("sqs")

response = sqs.get_queue_attributes(
    QueueUrl=QUEUE_URL,
    AttributeNames=["All"]
)

print(response["Attributes"])
```

---

# Updating Queue Attributes

Queue attributes can be modified using:

- AWS Console
- AWS CLI
- AWS SDKs
- Infrastructure as Code (CloudFormation or Terraform)

---

## AWS CLI Example

```bash
aws sqs set-queue-attributes \
    --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/OrderQueue \
    --attributes VisibilityTimeout=60
```

---

# Best Practices

- Choose a retention period based on business requirements.
- Configure a Visibility Timeout longer than the average processing time.
- Enable Long Polling to reduce API costs.
- Use Dead Letter Queues for fault tolerance.
- Encrypt queues containing sensitive data.
- Store large payloads in Amazon S3 instead of SQS.
- Use meaningful tags for governance and billing.
- Monitor queue attributes using Amazon CloudWatch.

---

# Common Mistakes

## Using the Default Visibility Timeout for Long Jobs

If processing exceeds 30 seconds, messages may become visible again before processing completes.

---

## Sending Large Files Through SQS

SQS is designed for lightweight messages, not file storage.

---

## Not Configuring a Dead Letter Queue

Without a DLQ, failed messages may be retried indefinitely, wasting compute resources.

---

## Leaving Long Polling Disabled

Short Polling increases API requests and overall cost.

---

## Ignoring Queue Tags

Untagged resources become difficult to organize and track in larger AWS environments.

---

# Key Takeaways

- Queue attributes control the behavior of Amazon SQS queues.
- Proper configuration improves scalability, reliability, security, and cost efficiency.
- Key attributes include Message Retention Period, Visibility Timeout, Delivery Delay, Long Polling, Redrive Policy, and Server-Side Encryption.
- Queue ARNs and Tags support security, integrations, and resource management.

---

# Summary

Queue attributes are the configuration backbone of Amazon SQS. They define how messages are stored, delivered, protected, and eventually removed from the queue. Understanding these settings allows you to optimize performance, improve fault tolerance, reduce costs, and build secure messaging solutions.
