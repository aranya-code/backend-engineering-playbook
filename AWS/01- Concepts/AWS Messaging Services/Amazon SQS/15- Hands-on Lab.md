# Introduction

The best way to understand Amazon SQS is by building a simple producer-consumer application.

In this lab, you will:

- Create an SQS queue
- Send messages
- Receive messages
- Delete messages
- Configure Long Polling
- Configure a Dead Letter Queue (DLQ)
- Enable Server-Side Encryption (SSE)
- Monitor the queue using Amazon CloudWatch

By the end of this lab, you will have practical experience with the most commonly used Amazon SQS features.

---

# Lab Architecture

```
                Producer

                    │

                    ▼

             Amazon SQS Queue

                    │

                    ▼

               Consumer

                    │

                    ▼

              CloudWatch

                    │

                    ▼

          Dead Letter Queue
```

---

# Prerequisites

Before starting, ensure you have:

- An AWS Account
- AWS CLI installed and configured
- Python 3.x
- Boto3 installed

Verify the AWS CLI configuration:

```bash
aws configure
```

Verify the identity:

```bash
aws sts get-caller-identity
```

---

# Step 1 - Create an SQS Queue

## AWS CLI

```bash
aws sqs create-queue \
    --queue-name order-queue
```

---

## Verify the Queue

```bash
aws sqs list-queues
```

Example output

```text
https://sqs.us-east-1.amazonaws.com/123456789012/order-queue
```

Save this URL.

---

# Step 2 - Send a Message

```bash
aws sqs send-message \
    --queue-url QUEUE_URL \
    --message-body "Hello Amazon SQS"
```

Expected output

```json
{
  "MessageId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

---

# Step 3 - Receive the Message

```bash
aws sqs receive-message \
    --queue-url QUEUE_URL
```

Example response

```json
{
  "Messages": [
    {
      "MessageId": "...",
      "ReceiptHandle": "...",
      "Body": "Hello Amazon SQS"
    }
  ]
}
```

Save the **ReceiptHandle**.

---

# Step 4 - Delete the Message

```bash
aws sqs delete-message \
    --queue-url QUEUE_URL \
    --receipt-handle RECEIPT_HANDLE
```

The message is now permanently removed.

---

# Step 5 - Enable Long Polling

```bash
aws sqs set-queue-attributes \
    --queue-url QUEUE_URL \
    --attributes ReceiveMessageWaitTimeSeconds=20
```

Verify

```bash
aws sqs get-queue-attributes \
    --queue-url QUEUE_URL \
    --attribute-names ReceiveMessageWaitTimeSeconds
```

---

# Step 6 - Configure Visibility Timeout

```bash
aws sqs set-queue-attributes \
    --queue-url QUEUE_URL \
    --attributes VisibilityTimeout=120
```

This configures a Visibility Timeout of **120 seconds**.

---

# Step 7 - Create a Dead Letter Queue

```bash
aws sqs create-queue \
    --queue-name order-dlq
```

Retrieve its ARN:

```bash
aws sqs get-queue-attributes \
    --queue-url DLQ_URL \
    --attribute-names QueueArn
```

---

# Step 8 - Configure the Redrive Policy

```bash
aws sqs set-queue-attributes \
    --queue-url QUEUE_URL \
    --attributes RedrivePolicy='{
      "deadLetterTargetArn":"DLQ_ARN",
      "maxReceiveCount":"5"
    }'
```

---

# Step 9 - Enable Server-Side Encryption

```bash
aws sqs set-queue-attributes \
    --queue-url QUEUE_URL \
    --attributes KmsMasterKeyId=alias/aws/sqs
```

Verify

```bash
aws sqs get-queue-attributes \
    --queue-url QUEUE_URL \
    --attribute-names KmsMasterKeyId
```

---

# Step 10 - Monitor the Queue

View queue metrics.

```bash
aws sqs get-queue-attributes \
    --queue-url QUEUE_URL \
    --attribute-names All
```

Useful attributes include:

- ApproximateNumberOfMessages
- ApproximateNumberOfMessagesVisible
- ApproximateNumberOfMessagesNotVisible
- VisibilityTimeout
- ReceiveMessageWaitTimeSeconds

---

# Python Producer Example

```python
import boto3

QUEUE_URL = "QUEUE_URL"

sqs = boto3.client("sqs")

response = sqs.send_message(
    QueueUrl=QUEUE_URL,
    MessageBody="Hello from Python"
)

print(response["MessageId"])
```

---

# Python Consumer Example

```python
import boto3

QUEUE_URL = "QUEUE_URL"

sqs = boto3.client("sqs")

response = sqs.receive_message(
    QueueUrl=QUEUE_URL,
    MaxNumberOfMessages=1,
    WaitTimeSeconds=20
)

messages = response.get("Messages", [])

for message in messages:
    print(message["Body"])

    sqs.delete_message(
        QueueUrl=QUEUE_URL,
        ReceiptHandle=message["ReceiptHandle"]
    )
```

---

# Validation Checklist

Verify the following:

| Task | Status |
|------|--------|
| Queue created | ☐ |
| Message sent | ☐ |
| Message received | ☐ |
| Message deleted | ☐ |
| Long Polling enabled | ☐ |
| Visibility Timeout configured | ☐ |
| Dead Letter Queue configured | ☐ |
| Server-Side Encryption enabled | ☐ |
| Queue monitored using CloudWatch | ☐ |

---

# Cleanup

Delete the queues after completing the lab.

Delete the main queue:

```bash
aws sqs delete-queue \
    --queue-url QUEUE_URL
```

Delete the Dead Letter Queue:

```bash
aws sqs delete-queue \
    --queue-url DLQ_URL
```

---

# Best Practices

- Perform hands-on exercises in a non-production AWS account.
- Use IAM roles instead of long-term access keys.
- Enable Server-Side Encryption for all production queues.
- Configure a Dead Letter Queue before deploying to production.
- Verify CloudWatch metrics after each configuration change.
- Delete unused queues to avoid unnecessary charges.

---

# Summary

This lab demonstrated the complete lifecycle of working with Amazon SQS. You created a queue, sent and received messages, configured Visibility Timeout, Long Polling, Dead Letter Queues, and Server-Side Encryption, and monitored queue attributes. These exercises provide a solid foundation for building reliable, scalable, and production-ready messaging applications using Amazon SQS.