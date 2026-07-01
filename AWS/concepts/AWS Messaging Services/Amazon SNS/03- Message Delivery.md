# Introduction

The primary responsibility of Amazon SNS is to deliver published messages to subscribed endpoints.

When a publisher sends a message to an SNS Topic, Amazon SNS immediately attempts to deliver that message to every active subscription.

Unlike Amazon SQS, Amazon SNS follows a **push-based delivery model**, where subscribers receive messages automatically without polling.

Understanding how Amazon SNS delivers messages is essential for designing reliable event-driven applications.

---

# Message Delivery Flow

The complete message delivery lifecycle is shown below.

```
Publisher

    │

    ▼

Publish()

    │

    ▼

Amazon SNS Topic

    │

 ┌──┼───────────────┐

 ▼  ▼               ▼

SQS Lambda       Email

 │     │             │

 ▼     ▼             ▼

Delivered Delivered Delivered
```

A single published message can be delivered to multiple subscribers simultaneously.

---

# Push-Based Messaging

Amazon SNS is a **push service**.

Subscribers do not request messages.

Instead,

Amazon SNS pushes messages immediately after publication.

```
Publisher

↓

SNS

↓

Subscriber
```

This differs from Amazon SQS, where consumers continuously poll the queue.

---

# Push vs Pull

| Amazon SNS | Amazon SQS |
|------------|------------|
| Push Model | Pull Model |
| Immediate delivery | Consumer polls queue |
| No message storage | Messages stored until consumed |
| Multiple subscribers | One consumer processes one message |

---

# Message Publishing

Applications publish messages using the `Publish()` API.

```
Application

↓

Publish()

↓

SNS Topic

↓

Subscribers
```

Amazon SNS immediately begins delivering the message.

---

## AWS CLI

```bash
aws sns publish \
    --topic-arn TOPIC_ARN \
    --message "Order Created"
```

---

## Boto3

```python
import boto3

sns = boto3.client("sns")

sns.publish(
    TopicArn=TOPIC_ARN,
    Message="Order Created"
)
```

---

# Fan-Out Delivery

Amazon SNS automatically duplicates messages for every subscriber.

```
                Order Created

                      │

                      ▼

                Amazon SNS

      ┌──────────┼──────────┬──────────┐

      ▼          ▼          ▼          ▼

     SQS      Lambda      Email      HTTP
```

Each subscriber receives its own copy.

Subscribers operate independently.

---

# Delivery to Amazon SQS

Amazon SNS can deliver messages directly to an Amazon SQS queue.

```
Publisher

↓

SNS Topic

↓

Amazon SQS

↓

Worker
```

Advantages

- Reliable storage
- Retry support
- Decoupled processing
- Dead Letter Queue support

---

# Delivery to AWS Lambda

Amazon SNS can invoke Lambda functions directly.

```
Publisher

↓

SNS

↓

Lambda

↓

Business Logic
```

Common use cases:

- Data transformation
- Notifications
- Image processing
- API calls

---

# Delivery to Email

SNS can send email notifications.

```
SNS

↓

Email

↓

User
```

Typical use cases:

- Alerts
- Administrative notifications
- Monitoring events

---

# Delivery to SMS

Amazon SNS supports SMS delivery.

```
SNS

↓

SMS

↓

Mobile Device
```

Common examples:

- One-Time Passwords (OTP)
- Emergency alerts
- Banking notifications

---

# Delivery to HTTP/HTTPS

Amazon SNS sends an HTTP POST request to subscribed endpoints.

```
SNS

↓

HTTP POST

↓

Webhook

↓

Application
```

Applications should return a successful HTTP response after processing the message.

---

# Delivery to Mobile Push

SNS integrates with mobile push notification services.

```
SNS

↓

Firebase

↓

Apple Push

↓

Mobile Device
```

Supported platforms include:

- Apple APNs
- Firebase Cloud Messaging (FCM)

---

# Message Format

SNS delivers messages in JSON format.

Example

```json
{
  "Type": "Notification",
  "MessageId": "12345",
  "TopicArn": "arn:aws:sns:...",
  "Subject": "Order Event",
  "Message": "Order Created",
  "Timestamp": "2026-07-01T10:30:00Z"
}
```

---

# Message Attributes

Applications can attach metadata using Message Attributes.

Example

```python
sns.publish(
    TopicArn=TOPIC_ARN,
    Message="Order Created",
    MessageAttributes={
        "Priority": {
            "DataType": "String",
            "StringValue": "High"
        }
    }
)
```

These attributes are commonly used for:

- Message filtering
- Routing
- Categorization

---

# Delivery Retries

Delivery behavior depends on the subscriber type.

| Subscriber | Retry Behavior |
|-------------|----------------|
| Amazon SQS | Managed by SQS |
| AWS Lambda | AWS retry logic |
| HTTP/HTTPS | SNS retry policy |
| Email | Best effort |
| SMS | Best effort |

---

# Delivery Status

Amazon SNS tracks delivery status for supported protocols.

Example

```
Published

↓

Delivered

↓

Success
```

or

```
Published

↓

Delivery Failed

↓

Retry
```

Delivery status can be monitored using Amazon CloudWatch.

---

# Real-World Example

Suppose an e-commerce platform publishes an order event.

```
Customer Places Order

↓

Order Service

↓

SNS Topic

↓

Inventory Queue

↓

Billing Queue

↓

Shipping Queue

↓

Analytics Lambda

↓

Email Notification
```

Every service receives the event simultaneously without direct communication between services.

---

# Monitoring Delivery

Amazon CloudWatch provides metrics such as:

- NumberOfMessagesPublished
- NumberOfNotificationsDelivered
- NumberOfNotificationsFailed

These metrics help identify delivery issues.

---

# Best Practices

- Use Amazon SQS subscribers for reliable processing.
- Keep published messages concise.
- Use Message Attributes for filtering.
- Monitor failed deliveries with CloudWatch.
- Use HTTPS endpoints instead of HTTP whenever possible.
- Configure retry policies for HTTP/HTTPS subscribers.
- Separate business domains into different topics.

---

# Common Mistakes

## Assuming SNS Stores Messages

Amazon SNS immediately attempts delivery.

It is not a persistent message queue.

---

## Publishing Large Payloads

Keep message payloads small.

Store large objects in Amazon S3 and publish only the object reference.

---

## Ignoring Delivery Failures

Monitor CloudWatch metrics to identify failed deliveries.

---

## Publishing Sensitive Information

Encrypt sensitive data and use secure subscriber endpoints.

---

## Using Email for High-Volume Processing

Email subscriptions are intended for notifications, not application-to-application communication.

Use Amazon SQS or AWS Lambda instead.

---

# Summary

Amazon SNS uses a push-based delivery model to distribute messages from publishers to multiple subscribers simultaneously. It supports a wide range of delivery protocols, including Amazon SQS, AWS Lambda, Email, SMS, and HTTP/HTTPS endpoints. By understanding message delivery behavior, retry mechanisms, and subscriber types, developers can design scalable, event-driven architectures that reliably distribute events across applications and AWS services.