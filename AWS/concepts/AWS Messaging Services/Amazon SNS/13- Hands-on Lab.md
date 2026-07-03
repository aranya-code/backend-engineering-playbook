# Introduction

The best way to understand Amazon SNS is by building a simple **Publish/Subscribe** application.

In this hands-on lab, you will:

- Create an SNS Topic
- Create multiple subscriptions
- Publish messages
- Deliver messages to Amazon SQS
- Invoke AWS Lambda
- Configure Message Filtering
- Enable Server-Side Encryption
- Monitor SNS using Amazon CloudWatch

By the end of this lab, you will understand how Amazon SNS is used in real-world event-driven architectures.

---

# Lab Architecture

```
                Publisher

                    │

                    ▼

             Amazon SNS Topic

      ┌─────────────┼─────────────┐

      ▼             ▼             ▼

 Amazon SQS      AWS Lambda     Email

      │

      ▼

 Consumer
```

---

# Prerequisites

Before starting, ensure you have:

- AWS Account
- AWS CLI installed
- Python 3.x
- Boto3 installed
- Basic IAM permissions for SNS

Verify AWS CLI configuration.

```bash
aws configure
```

Verify credentials.

```bash
aws sts get-caller-identity
```

---

# Step 1 - Create an SNS Topic

## AWS CLI

```bash
aws sns create-topic \
    --name order-events
```

Example output

```json
{
    "TopicArn":"arn:aws:sns:us-east-1:123456789012:order-events"
}
```

Save the Topic ARN.

---

# Step 2 - List Topics

```bash
aws sns list-topics
```

Verify that your topic appears.

---

# Step 3 - Create an Amazon SQS Queue

```bash
aws sqs create-queue \
    --queue-name order-queue
```

Retrieve the Queue URL.

```bash
aws sqs list-queues
```

Retrieve the Queue ARN.

```bash
aws sqs get-queue-attributes \
    --queue-url QUEUE_URL \
    --attribute-names QueueArn
```

---

# Step 4 - Subscribe the Queue

Subscribe the SQS queue to the SNS topic.

```bash
aws sns subscribe \
    --topic-arn TOPIC_ARN \
    --protocol sqs \
    --notification-endpoint QUEUE_ARN
```

Example response

```json
{
    "SubscriptionArn":"arn:aws:sns:..."
}
```

---

# Step 5 - Update the Queue Policy

Allow the SNS topic to publish messages to the SQS queue.

Example Queue Policy

```json
{
  "Version":"2012-10-17",
  "Statement":[
    {
      "Effect":"Allow",
      "Principal":{
        "Service":"sns.amazonaws.com"
      },
      "Action":"sqs:SendMessage",
      "Resource":"QUEUE_ARN",
      "Condition":{
        "ArnEquals":{
          "aws:SourceArn":"TOPIC_ARN"
        }
      }
    }
  ]
}
```

Apply the policy.

```bash
aws sqs set-queue-attributes \
    --queue-url QUEUE_URL \
    --attributes Policy=file://policy.json
```

---

# Step 6 - Publish a Message

```bash
aws sns publish \
    --topic-arn TOPIC_ARN \
    --message "Order Created"
```

Example output

```json
{
    "MessageId":"xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

---

# Step 7 - Receive the Message

Verify that the SQS queue received the notification.

```bash
aws sqs receive-message \
    --queue-url QUEUE_URL
```

Expected output

```json
{
    "Messages":[
        {
            "Body":"..."
        }
    ]
}
```

---

# Step 8 - Create an Email Subscription

```bash
aws sns subscribe \
    --topic-arn TOPIC_ARN \
    --protocol email \
    --notification-endpoint admin@example.com
```

Amazon SNS sends a confirmation email.

Click the confirmation link.

Subscription status becomes:

```
Pending

↓

Confirmed

↓

Active
```

---

# Step 9 - Publish Another Message

```bash
aws sns publish \
    --topic-arn TOPIC_ARN \
    --message "Payment Successful"
```

Verify:

- Email received
- SQS message received

---

# Step 10 - Configure Message Filtering

Create a Filter Policy.

```json
{
    "EventType":[
        "Order"
    ]
}
```

Apply it.

```bash
aws sns set-subscription-attributes \
    --subscription-arn SUBSCRIPTION_ARN \
    --attribute-name FilterPolicy \
    --attribute-value '{"EventType":["Order"]}'
```

---

# Step 11 - Publish with Message Attributes

```bash
aws sns publish \
    --topic-arn TOPIC_ARN \
    --message "New Order" \
    --message-attributes '{
      "EventType":{
        "DataType":"String",
        "StringValue":"Order"
      }
    }'
```

The message should match the filter policy and be delivered.

---

# Step 12 - Publish a Non-Matching Event

```bash
aws sns publish \
    --topic-arn TOPIC_ARN \
    --message "Payment Completed" \
    --message-attributes '{
      "EventType":{
        "DataType":"String",
        "StringValue":"Payment"
      }
    }'
```

Expected result

```
SNS

↓

Filter Policy

↓

No Match

↓

Message Not Delivered
```

---

# Step 13 - Enable Server-Side Encryption

```bash
aws sns set-topic-attributes \
    --topic-arn TOPIC_ARN \
    --attribute-name KmsMasterKeyId \
    --attribute-value alias/aws/sns
```

Verify.

```bash
aws sns get-topic-attributes \
    --topic-arn TOPIC_ARN
```

---

# Step 14 - View CloudWatch Metrics

Open:

```
CloudWatch

↓

Metrics

↓

SNS

↓

By Topic Name
```

Observe metrics such as:

- NumberOfMessagesPublished
- NumberOfNotificationsDelivered
- NumberOfNotificationsFailed

---

# Python Example

## Create SNS Client

```python
import boto3

sns = boto3.client("sns")
```

---

## Publish a Message

```python
sns.publish(
    TopicArn=TOPIC_ARN,
    Message="Order Created"
)
```

---

## Publish with Attributes

```python
sns.publish(
    TopicArn=TOPIC_ARN,
    Message="Order Created",
    MessageAttributes={
        "EventType":{
            "DataType":"String",
            "StringValue":"Order"
        }
    }
)
```

---

## Create a Subscription

```python
sns.subscribe(
    TopicArn=TOPIC_ARN,
    Protocol="email",
    Endpoint="admin@example.com"
)
```

---

# Validation Checklist

Verify the following.

| Task | Status |
|------|--------|
| SNS Topic created | ☐ |
| SQS Queue created | ☐ |
| Queue subscribed | ☐ |
| Queue Policy configured | ☐ |
| Message published | ☐ |
| Message received by SQS | ☐ |
| Email subscription confirmed | ☐ |
| Message Filtering configured | ☐ |
| Server-Side Encryption enabled | ☐ |
| CloudWatch metrics verified | ☐ |

---

# Cleanup

Delete the subscription.

```bash
aws sns unsubscribe \
    --subscription-arn SUBSCRIPTION_ARN
```

Delete the topic.

```bash
aws sns delete-topic \
    --topic-arn TOPIC_ARN
```

Delete the queue.

```bash
aws sqs delete-queue \
    --queue-url QUEUE_URL
```

---

# Best Practices

- Perform hands-on exercises in a non-production AWS account.
- Use IAM Roles instead of long-term access keys.
- Enable Server-Side Encryption for production topics.
- Configure Message Filtering to reduce unnecessary processing.
- Use Amazon SQS for reliable backend processing.
- Monitor CloudWatch metrics after publishing messages.
- Clean up AWS resources after completing the lab.

---

# Summary

This hands-on lab demonstrated the complete lifecycle of working with Amazon SNS. You created a topic, subscribed Amazon SQS and email endpoints, published messages, configured Message Filtering, enabled Server-Side Encryption, and monitored activity using Amazon CloudWatch. These exercises provide a practical foundation for building scalable, secure, and event-driven applications with Amazon SNS.