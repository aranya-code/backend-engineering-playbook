# Introduction

Amazon SNS supports multiple communication protocols, allowing a single published message to be delivered to different types of subscribers.

This flexibility enables Amazon SNS to integrate with AWS services, web applications, email systems, mobile devices, and external APIs.

Each subscription protocol has different delivery behavior, retry mechanisms, and use cases.

Understanding these protocols is essential when designing event-driven architectures.

---

# Supported Subscription Protocols

Amazon SNS currently supports the following subscription protocols.

| Protocol | Description |
|----------|-------------|
| Amazon SQS | Deliver messages to an SQS queue |
| AWS Lambda | Invoke a Lambda function |
| HTTP | Send an HTTP POST request |
| HTTPS | Send a secure HTTP POST request |
| Email | Send an email notification |
| Email-JSON | Send email with JSON payload |
| SMS | Send text messages |
| Mobile Push | Send push notifications to mobile devices |

---

# Subscription Architecture

```
                    Amazon SNS Topic

      ┌─────────────┼──────────────┬──────────────┐

      ▼             ▼              ▼              ▼

   Amazon SQS    AWS Lambda      Email         HTTPS

                                           External API
```

A single topic can contain multiple subscription types simultaneously.

---

# Amazon SQS Subscription

Amazon SQS is the most common SNS subscriber.

```
Publisher

↓

SNS Topic

↓

Amazon SQS

↓

Consumer
```

Benefits

- Reliable message storage
- Retry support
- Dead Letter Queue support
- Independent consumer scaling

---

## AWS CLI

```bash
aws sns subscribe \
    --topic-arn TOPIC_ARN \
    --protocol sqs \
    --notification-endpoint QUEUE_ARN
```

---

## Boto3

```python
sns.subscribe(
    TopicArn=TOPIC_ARN,
    Protocol="sqs",
    Endpoint=QUEUE_ARN
)
```

---

## Common Use Cases

- Order processing
- Inventory updates
- Payment processing
- Background jobs

---

# AWS Lambda Subscription

Amazon SNS can invoke Lambda functions directly.

```
SNS Topic

↓

AWS Lambda

↓

Business Logic
```

Lambda automatically receives the published message as an event.

---

## AWS CLI

```bash
aws sns subscribe \
    --topic-arn TOPIC_ARN \
    --protocol lambda \
    --notification-endpoint LAMBDA_ARN
```

---

## Boto3

```python
sns.subscribe(
    TopicArn=TOPIC_ARN,
    Protocol="lambda",
    Endpoint=LAMBDA_ARN
)
```

---

## Common Use Cases

- Image processing
- Data transformation
- Event processing
- Notifications

---

# HTTP Subscription

SNS sends an HTTP POST request to the subscriber.

```
SNS

↓

HTTP POST

↓

Web Application
```

Applications must expose a public HTTP endpoint.

---

## AWS CLI

```bash
aws sns subscribe \
    --topic-arn TOPIC_ARN \
    --protocol http \
    --notification-endpoint http://example.com/webhook
```

---

# HTTPS Subscription

HTTPS subscriptions work similarly to HTTP but use TLS encryption.

```
SNS

↓

HTTPS

↓

Secure API
```

HTTPS is recommended for production systems.

---

## AWS CLI

```bash
aws sns subscribe \
    --topic-arn TOPIC_ARN \
    --protocol https \
    --notification-endpoint https://example.com/webhook
```

---

# Email Subscription

SNS can send email notifications.

```
SNS

↓

Email

↓

User
```

When an email subscription is created, Amazon SNS sends a confirmation email.

The subscription becomes active only after the recipient confirms it.

---

## AWS CLI

```bash
aws sns subscribe \
    --topic-arn TOPIC_ARN \
    --protocol email \
    --notification-endpoint admin@example.com
```

---

## Common Use Cases

- System alerts
- CloudWatch notifications
- Administrative notifications

---

# Email-JSON Subscription

Email-JSON delivers the complete SNS notification as a JSON document.

```
SNS

↓

JSON Email

↓

Developer
```

Useful for debugging and automation.

---

# SMS Subscription

Amazon SNS supports SMS delivery to mobile phones.

```
SNS

↓

SMS

↓

Mobile Device
```

Common use cases:

- OTP
- Fraud alerts
- Banking notifications
- Emergency alerts

---

## AWS CLI

```bash
aws sns subscribe \
    --topic-arn TOPIC_ARN \
    --protocol sms \
    --notification-endpoint +15551234567
```

---

# Mobile Push Subscription

Amazon SNS integrates with mobile push notification services.

Supported platforms include:

- Apple Push Notification Service (APNs)
- Firebase Cloud Messaging (FCM)

```
SNS

↓

Mobile Push

↓

Android

↓

iPhone
```

---

# Subscription Confirmation

Not every protocol behaves the same way.

| Protocol | Confirmation Required |
|----------|-----------------------|
| Amazon SQS | No |
| AWS Lambda | No |
| HTTP | Yes |
| HTTPS | Yes |
| Email | Yes |
| Email-JSON | Yes |
| SMS | No |
| Mobile Push | Platform Registration |

---

# Subscription Status

A subscription may have one of the following states.

```
Pending Confirmation

↓

Confirmed

↓

Active
```

or

```
Deleted
```

Only active subscriptions receive messages.

---

# Listing Subscriptions

## AWS CLI

```bash
aws sns list-subscriptions
```

---

## List Subscriptions for a Topic

```bash
aws sns list-subscriptions-by-topic \
    --topic-arn TOPIC_ARN
```

---

## Boto3

```python
response = sns.list_subscriptions_by_topic(
    TopicArn=TOPIC_ARN
)

print(response["Subscriptions"])
```

---

# Unsubscribing

Subscriptions can be removed at any time.

## AWS CLI

```bash
aws sns unsubscribe \
    --subscription-arn SUBSCRIPTION_ARN
```

---

## Boto3

```python
sns.unsubscribe(
    SubscriptionArn=SUBSCRIPTION_ARN
)
```

---

# Choosing the Right Subscription

| Requirement | Recommended Protocol |
|-------------|----------------------|
| Reliable processing | Amazon SQS |
| Serverless processing | AWS Lambda |
| External application | HTTPS |
| User notifications | Email |
| Mobile alerts | SMS |
| Mobile applications | Mobile Push |

---

# Real-World Example

A payment succeeds.

```
Payment Service

↓

SNS Topic

↓

Billing Queue

↓

Invoice Lambda

↓

Customer Email

↓

Accounting API
```

Each subscriber processes the same event independently.

---

# Monitoring Subscription Delivery

Amazon CloudWatch provides metrics such as:

- NumberOfNotificationsDelivered
- NumberOfNotificationsFailed
- NumberOfNotificationsFilteredOut

These metrics help identify delivery problems.

---

# Best Practices

- Use HTTPS instead of HTTP.
- Prefer Amazon SQS for backend processing.
- Use AWS Lambda for lightweight event processing.
- Confirm email subscriptions immediately.
- Remove unused subscriptions.
- Monitor failed deliveries using CloudWatch.
- Separate topics based on business functionality.

---

# Common Mistakes

## Using Email for Application Processing

Email subscriptions are intended for human notifications.

Use Amazon SQS or AWS Lambda for backend workflows.

---

## Forgetting Subscription Confirmation

Email and HTTP subscriptions remain inactive until confirmed.

---

## Mixing Multiple Business Domains

Avoid subscribing unrelated services to the same topic.

---

## Exposing Unsecured HTTP Endpoints

Always use HTTPS in production environments.

---

# Summary

Amazon SNS supports multiple subscription protocols, allowing a single published event to reach a variety of endpoints including Amazon SQS, AWS Lambda, Email, SMS, HTTP/HTTPS APIs, and mobile devices. Choosing the appropriate subscription protocol depends on the application's reliability, scalability, and notification requirements. Understanding each protocol's delivery behavior and limitations is essential for building robust event-driven systems.