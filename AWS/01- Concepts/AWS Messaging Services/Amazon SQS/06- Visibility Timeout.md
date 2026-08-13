# Introduction

When a consumer receives a message from an Amazon SQS queue, the message is **not deleted immediately**.

Instead, Amazon SQS temporarily hides the message from other consumers while the current consumer processes it.

This temporary hiding period is known as the **Visibility Timeout**.

Visibility Timeout is one of the most important concepts in Amazon SQS because it prevents multiple consumers from processing the same message simultaneously while ensuring that messages are not lost if a consumer fails.

---

# What is Visibility Timeout?

Visibility Timeout is the amount of time that a received message remains invisible to other consumers.

The message still exists in the queue but cannot be received again until one of the following happens:

- The consumer successfully deletes the message.
- The Visibility Timeout expires.

---

## Default Value

| Property | Value |
|----------|-------|
| Default | 30 Seconds |
| Minimum | 0 Seconds |
| Maximum | 12 Hours |

---

# Why is Visibility Timeout Required?

Consider an application with multiple workers processing messages.

Without Visibility Timeout:

```
              Amazon SQS

                  │

        ┌─────────┴─────────┐

        ▼                   ▼

   Consumer A          Consumer B

        │                   │

        └──── Same Message ─┘
```

Both consumers may process the same message simultaneously.

This can result in:

- Duplicate payments
- Duplicate emails
- Multiple inventory updates
- Data inconsistency

---

With Visibility Timeout enabled:

```
              Amazon SQS

                  │

                  ▼

          Consumer A

                  │

       Message Becomes Invisible

                  │

          Consumer B

      Cannot Receive Message
```

Only one consumer processes the message.

---

# How Visibility Timeout Works

The following diagram illustrates the complete lifecycle.

```
Producer

    │

    ▼

SendMessage()

    │

    ▼

Amazon SQS Queue

    │

    ▼

ReceiveMessage()

    │

    ▼

Visibility Timeout Starts

    │

    ▼

Application Processing

    │

    ├───────────────┐

    ▼               ▼

Success          Failure

    │               │

    ▼               ▼

Delete        Timeout Expires

                    │

                    ▼

          Message Visible Again
```

---

# Example Scenario

Suppose an application processes invoices.

```
Invoice Queue

↓

Worker Receives Invoice

↓

Generate PDF

↓

Send Email

↓

Update Database

↓

Delete Message
```

The message remains invisible throughout the processing period.

Only after the worker calls **DeleteMessage()** is the message permanently removed.

---

# Consumer Failure Scenario

Suppose the worker crashes before deleting the message.

```
Receive Message

↓

Visibility Timeout Starts

↓

Application Crash

↓

Message Not Deleted

↓

Visibility Timeout Expires

↓

Message Becomes Visible Again

↓

Another Worker Processes It
```

This mechanism prevents message loss.

---

# Configuring Visibility Timeout

Visibility Timeout can be configured when creating a queue or updated later.

## AWS Management Console

1. Open **Amazon SQS**.
2. Select the queue.
3. Choose **Edit**.
4. Locate **Visibility Timeout**.
5. Specify the required value.
6. Save the changes.

---

## AWS CLI

```bash
aws sqs set-queue-attributes \
  --queue-url QUEUE_URL \
  --attributes VisibilityTimeout=120
```

The above command changes the queue's Visibility Timeout to **120 seconds**.

---

## Boto3

```python
import boto3

sqs = boto3.client("sqs")

sqs.set_queue_attributes(
    QueueUrl=QUEUE_URL,
    Attributes={
        "VisibilityTimeout": "120"
    }
)
```

---

## CloudFormation

```yaml
Resources:
  OrderQueue:
    Type: AWS::SQS::Queue
    Properties:
      VisibilityTimeout: 120
```

---

## Terraform

```terraform
resource "aws_sqs_queue" "order_queue" {

  name = "order-queue"

  visibility_timeout_seconds = 120

}
```

---

# Extending the Visibility Timeout

Sometimes processing takes longer than expected.

Instead of allowing the message to become visible again, applications can extend the timeout dynamically.

Amazon SQS provides the following API:

```
ChangeMessageVisibility()
```

---

## AWS CLI

```bash
aws sqs change-message-visibility \
  --queue-url QUEUE_URL \
  --receipt-handle RECEIPT_HANDLE \
  --visibility-timeout 300
```

---

## Boto3

```python
sqs.change_message_visibility(
    QueueUrl=QUEUE_URL,
    ReceiptHandle=receipt_handle,
    VisibilityTimeout=300
)
```

---

# Visibility Timeout vs Delay Queue

These two settings are frequently confused.

| Visibility Timeout | Delay Queue |
|--------------------|-------------|
| Starts after ReceiveMessage() | Starts after SendMessage() |
| Hides a received message | Delays delivery of a new message |
| Prevents duplicate processing | Delays initial processing |

---

# Visibility Timeout vs Message Retention

| Visibility Timeout | Message Retention |
|--------------------|-------------------|
| Controls temporary invisibility | Controls total storage duration |
| Maximum 12 Hours | Maximum 14 Days |
| Starts after a message is received | Starts when a message is sent |

---

# Real-World Use Cases

## Payment Processing

```
Customer

↓

Payment Queue

↓

Payment Service

↓

Bank

↓

Delete Message
```

The payment should not be processed twice.

---

## Video Encoding

```
Upload Video

↓

Amazon SQS

↓

Encoding Worker

↓

Store Output

↓

Delete Message
```

Encoding can take several minutes, making it necessary to increase or extend the Visibility Timeout.

---

## Machine Learning Jobs

```
Dataset

↓

Amazon SQS

↓

ML Worker

↓

Prediction

↓

Store Result
```

Long-running inference jobs often require dynamic timeout extension.

---

# Monitoring

Amazon CloudWatch provides metrics that help monitor message processing.

Useful metrics include:

- ApproximateNumberOfMessagesVisible
- ApproximateNumberOfMessagesNotVisible
- ApproximateAgeOfOldestMessage

Monitoring these metrics helps identify:

- Slow consumers
- Processing bottlenecks
- Messages that are repeatedly retried

---

# Best Practices

- Configure the Visibility Timeout to exceed the average processing time.
- Extend the timeout for long-running jobs using `ChangeMessageVisibility()`.
- Delete messages immediately after successful processing.
- Design consumers to be idempotent.
- Configure Dead Letter Queues for messages that repeatedly fail.
- Monitor queue health using Amazon CloudWatch.

---

# Common Mistakes

## Setting a Very Short Timeout

If the timeout expires before processing completes, another consumer may receive the same message.

---

## Setting an Excessively Long Timeout

Very long timeouts delay retries when a consumer crashes.

Choose a value based on the application's processing requirements.

---

## Forgetting to Delete Messages

Receiving a message does not remove it from the queue.

Applications must explicitly call `DeleteMessage()` after successful processing.

---

## Confusing Visibility Timeout with Message Retention

Visibility Timeout controls how long a received message remains hidden.

Message Retention controls how long Amazon SQS stores the message before automatically deleting it.

---

# Summary

Visibility Timeout is a core reliability feature of Amazon SQS. It ensures that only one consumer processes a message at a time while protecting against message loss when consumers fail. Properly configuring and monitoring Visibility Timeout is essential for building reliable, scalable, and fault-tolerant messaging systems.