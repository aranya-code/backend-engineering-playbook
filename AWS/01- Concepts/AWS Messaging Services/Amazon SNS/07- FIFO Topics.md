# Introduction

By default, Amazon SNS uses **Standard Topics**, which prioritize high throughput and low latency.

However, some business applications require:

- Strict message ordering
- Duplicate message prevention
- Exactly-once message delivery (within the deduplication window)

To support these requirements, Amazon SNS provides **FIFO Topics**.

FIFO Topics guarantee that messages are delivered in the exact order they are published while preventing duplicate message delivery.

---

# What are FIFO Topics?

A FIFO (First-In, First-Out) Topic guarantees that messages are delivered to subscribers in the same order in which they were published.

Unlike Standard Topics, FIFO Topics also support message deduplication to prevent accidental duplicate deliveries.

```
Publisher

↓

SNS FIFO Topic

↓

FIFO SQS Queue

↓

Consumer
```

Messages are processed sequentially.

---

# Why Do We Need FIFO Topics?

Consider a banking application.

```
Deposit ₹500

↓

Withdraw ₹200

↓

Check Balance
```

If these events arrive out of order:

```
Withdraw ₹200

↓

Deposit ₹500

↓

Check Balance
```

The account balance may become incorrect.

FIFO Topics ensure events are delivered in the correct sequence.

---

# Standard Topic vs FIFO Topic

| Standard Topic | FIFO Topic |
|----------------|------------|
| Best-effort ordering | Strict ordering |
| At-least-once delivery | Exactly-once delivery (within the deduplication window) |
| Very high throughput | High throughput with ordering guarantees |
| Duplicate messages possible | Duplicate messages prevented |
| Supports all subscriber types | Supports FIFO SQS queues only |

---

# FIFO Topic Architecture

```
Publisher

↓

SNS FIFO Topic

↓

FIFO SQS Queue

↓

Consumer
```

Unlike Standard Topics, FIFO Topics currently support delivery only to **FIFO SQS queues**.

---

# FIFO Topic Naming

FIFO Topics must end with the `.fifo` suffix.

Example

```
order-events.fifo
```

Invalid

```
order-events
```

---

# Creating a FIFO Topic

## AWS Management Console

1. Open Amazon SNS.
2. Select **Create Topic**.
3. Choose **FIFO**.
4. Enter a topic name ending with `.fifo`.
5. Configure additional settings.
6. Create the topic.

---

## AWS CLI

```bash
aws sns create-topic \
    --name order-events.fifo \
    --attributes FifoTopic=true
```

---

## Boto3

```python
import boto3

sns = boto3.client("sns")

response = sns.create_topic(
    Name="order-events.fifo",
    Attributes={
        "FifoTopic": "true"
    }
)

print(response["TopicArn"])
```

---

## CloudFormation

```yaml
Resources:

  OrderTopic:

    Type: AWS::SNS::Topic

    Properties:

      TopicName: order-events.fifo

      FifoTopic: true
```

---

## Terraform

```terraform
resource "aws_sns_topic" "order_topic" {

  name       = "order-events.fifo"

  fifo_topic = true

}
```

---

# Message Group ID

Every message published to a FIFO Topic must include a **MessageGroupId**.

The Message Group determines ordering.

Example

```
Customer A

↓

Group A

-------------------

Customer B

↓

Group B
```

Messages within each group remain ordered.

Different groups can be processed independently.

---

## Publishing Example

```python
sns.publish(
    TopicArn=TOPIC_ARN,
    Message="Order Created",
    MessageGroupId="customer-101"
)
```

---

# Message Deduplication

FIFO Topics prevent duplicate messages.

Two approaches are supported.

## Explicit Deduplication

Provide a unique **MessageDeduplicationId**.

```python
sns.publish(
    TopicArn=TOPIC_ARN,
    Message="Order Created",
    MessageGroupId="orders",
    MessageDeduplicationId="order-101"
)
```

Duplicate IDs published within the deduplication window are ignored.

---

## Content-Based Deduplication

Amazon SNS automatically generates the deduplication identifier from the message body.

Enable when creating the topic.

---

## AWS CLI

```bash
aws sns create-topic \
    --name order-events.fifo \
    --attributes \
FifoTopic=true,ContentBasedDeduplication=true
```

---

# Message Ordering

Suppose three events are published.

```
Order Created

↓

Payment Received

↓

Order Shipped
```

FIFO Topic guarantees delivery as:

```
Order Created

↓

Payment Received

↓

Order Shipped
```

The order never changes within the same Message Group.

---

# Multiple Message Groups

FIFO Topics allow multiple independent ordered streams.

```
SNS FIFO Topic

        │

 ┌──────┴────────┐

 ▼               ▼

Group A       Group B

 ▼               ▼

Queue A       Queue B
```

Ordering is maintained within each group.

Groups can be processed concurrently.

---

# FIFO Topic with FIFO Queue

```
Application

↓

SNS FIFO Topic

↓

FIFO SQS Queue

↓

Worker
```

Both the Topic and Queue must be FIFO.

---

# Real-World Example

Suppose an online shopping platform processes orders.

```
Customer

↓

Order Service

↓

SNS FIFO Topic

↓

Order Queue

↓

Inventory Queue

↓

Billing Queue
```

All downstream services receive events in the same order.

---

# Banking Example

```
Deposit

↓

Withdraw

↓

Transfer

↓

Balance Update
```

Processing these operations in order is essential for maintaining consistency.

FIFO Topics guarantee this behavior.

---

# Throughput Considerations

FIFO Topics provide ordering guarantees, which may reduce maximum throughput compared to Standard Topics.

For workloads requiring the highest throughput without ordering, Standard Topics are usually the better choice.

---

# FIFO Topics vs Standard Topics

| Feature | Standard | FIFO |
|---------|----------|------|
| Ordering | Best Effort | Guaranteed |
| Duplicate Prevention | No | Yes |
| Message Group ID | No | Yes |
| Deduplication ID | No | Yes |
| Topic Name Ends With `.fifo` | No | Yes |
| Compatible with FIFO SQS | Optional | Required |

---

# Monitoring FIFO Topics

Monitor FIFO Topics using Amazon CloudWatch.

Useful metrics include:

- NumberOfMessagesPublished
- NumberOfNotificationsDelivered
- NumberOfNotificationsFailed

Also monitor downstream FIFO SQS queues for:

- Queue depth
- Processing delays
- Dead Letter Queue activity

---

# Best Practices

- Use FIFO Topics only when strict ordering is required.
- Use meaningful Message Group IDs.
- Enable Content-Based Deduplication when appropriate.
- Publish unique Deduplication IDs for critical business events.
- Pair FIFO Topics only with FIFO SQS queues.
- Monitor CloudWatch metrics regularly.

---

# Common Mistakes

## Forgetting the `.fifo` Suffix

FIFO Topics must end with:

```
.fifo
```

---

## Publishing Without a Message Group ID

FIFO Topics require a valid `MessageGroupId`.

Publishing without it results in an error.

---

## Using FIFO When Ordering Isn't Needed

FIFO Topics introduce additional ordering constraints.

For notifications or analytics, Standard Topics are generally more appropriate.

---

## Assuming Infinite Throughput

FIFO Topics prioritize ordering over maximum throughput.

Choose Standard Topics when ordering is unnecessary.

---

## Connecting FIFO Topics to Standard Queues

FIFO Topics are designed to work with FIFO SQS queues.

Mixing queue types is not supported.

---

# Summary

FIFO Topics provide ordered, deduplicated message delivery for applications that require strict sequencing, such as payment systems, banking platforms, and order processing workflows. By using **Message Group IDs**, **Message Deduplication IDs**, and **FIFO SQS queues**, Amazon SNS ensures reliable event delivery while preserving message order. Although FIFO Topics offer lower throughput than Standard Topics, they are the preferred choice whenever business consistency and event ordering are critical.