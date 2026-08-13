# Introduction

When a consumer requests messages from an Amazon SQS queue, there may not always be messages available.

By default, Amazon SQS immediately returns a response—even if the queue is empty. This behavior is known as **Short Polling**.

To improve efficiency and reduce unnecessary API calls, Amazon SQS provides **Long Polling**.

With Long Polling enabled, Amazon SQS waits for a specified period for a message to arrive before returning a response.

This reduces empty responses, lowers costs, and improves application performance.

---

# What is Long Polling?

Long Polling allows a consumer to wait for messages instead of immediately receiving an empty response.

If a message arrives during the waiting period, Amazon SQS immediately returns the message to the consumer.

Otherwise, the request returns an empty response after the waiting period expires.

---

## Default Value

| Property | Value |
|----------|-------|
| Default | 0 Seconds (Short Polling) |
| Maximum | 20 Seconds |

---

# Why Use Long Polling?

Without Long Polling, applications continuously send requests even when the queue is empty.

Example:

```
Consumer

↓

ReceiveMessage()

↓

No Messages

↓

Empty Response

↓

ReceiveMessage()

↓

No Messages

↓

Empty Response

↓

ReceiveMessage()

↓

No Messages
```

This creates unnecessary API calls.

---

With Long Polling:

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

The consumer waits for messages instead of repeatedly polling the queue.

---

# How Long Polling Works

```
Consumer

    │

    ▼

ReceiveMessage()

    │

    ▼

Amazon SQS

    │

    ├───────────────┐

    ▼               ▼

Message Found   No Message

    │               │

    ▼               ▼

Return       Wait (20 sec)

                    │

          ┌─────────┴─────────┐

          ▼                   ▼

   Message Arrives      Timeout

          │                   │

          ▼                   ▼

Return Message      Empty Response
```

---

# Short Polling vs Long Polling

## Short Polling

```
Consumer

↓

ReceiveMessage()

↓

Queue Empty

↓

Empty Response

↓

ReceiveMessage()

↓

Queue Empty
```

Every request immediately returns.

---

## Long Polling

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

The consumer waits before Amazon SQS responds.

---

# Benefits of Long Polling

## Reduces Empty Responses

Instead of immediately returning an empty response, Amazon SQS waits for messages.

---

## Reduces API Calls

Applications make fewer requests to Amazon SQS.

```
Without Long Polling

100 Requests

↓

95 Empty Responses

----------------------

With Long Polling

10 Requests

↓

9 Messages Returned
```

---

## Lower AWS Cost

Amazon SQS pricing is based on API requests.

Fewer requests result in lower operational costs.

---

## Lower CPU Usage

Applications spend less time continuously polling the queue.

---

## Improved Performance

Consumers receive messages more efficiently with fewer unnecessary network requests.

---

# Configuring Long Polling

Long Polling is controlled using the **Receive Message Wait Time** attribute.

---

## AWS Management Console

1. Open **Amazon SQS**.
2. Select the queue.
3. Choose **Edit**.
4. Locate **Receive Message Wait Time**.
5. Enter a value between **1 and 20 seconds**.
6. Save the changes.

---

## AWS CLI

```bash
aws sqs set-queue-attributes \
  --queue-url QUEUE_URL \
  --attributes ReceiveMessageWaitTimeSeconds=20
```

---

## Boto3

```python
import boto3

sqs = boto3.client("sqs")

sqs.set_queue_attributes(
    QueueUrl=QUEUE_URL,
    Attributes={
        "ReceiveMessageWaitTimeSeconds": "20"
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
      ReceiveMessageWaitTimeSeconds: 20
```

---

## Terraform

```terraform
resource "aws_sqs_queue" "order_queue" {

  name = "order-queue"

  receive_wait_time_seconds = 20

}
```

---

# Long Polling per Request

Instead of configuring the queue, applications can enable Long Polling for individual requests.

---

## AWS CLI

```bash
aws sqs receive-message \
  --queue-url QUEUE_URL \
  --wait-time-seconds 20
```

---

## Boto3

```python
response = sqs.receive_message(
    QueueUrl=QUEUE_URL,
    WaitTimeSeconds=20
)
```

---

# Queue-Level vs Request-Level Configuration

| Queue-Level | Request-Level |
|-------------|---------------|
| Applies to every ReceiveMessage request | Applies only to the current request |
| Configured once | Specified every time |
| Easier to manage | More flexible |

---

# Real-World Use Cases

## Order Processing

```
Orders

↓

Amazon SQS

↓

Long Polling

↓

Order Worker
```

Workers wait efficiently for new orders instead of continuously polling.

---

## Background Job Processing

```
Application

↓

Amazon SQS

↓

Long Polling

↓

Worker Pool
```

Ideal for applications where jobs arrive at irregular intervals.

---

## Log Processing

```
Applications

↓

Amazon SQS

↓

Long Polling

↓

Log Processor
```

Reduces unnecessary polling when log traffic is low.

---

## Microservices Communication

```
Service A

↓

Amazon SQS

↓

Long Polling

↓

Service B
```

Efficient communication between services with varying workloads.

---

# Monitoring

Amazon CloudWatch metrics can help determine whether Long Polling is configured effectively.

Useful metrics include:

- NumberOfMessagesReceived
- NumberOfEmptyReceives
- ApproximateNumberOfMessagesVisible
- ApproximateAgeOfOldestMessage

A high value for **NumberOfEmptyReceives** often indicates that Long Polling is not configured optimally.

---

# Best Practices

- Use Long Polling whenever possible.
- Configure the wait time to **20 seconds** unless application requirements dictate otherwise.
- Combine Long Polling with batch message retrieval for maximum efficiency.
- Monitor the **NumberOfEmptyReceives** metric in CloudWatch.
- Avoid continuously polling queues using short polling.

---

# Common Mistakes

## Leaving the Default Value

The default wait time is **0 seconds**, which enables Short Polling.

Applications may generate unnecessary API requests.

---

## Confusing Long Polling with Visibility Timeout

Long Polling determines **how long a consumer waits for a message**.

Visibility Timeout determines **how long a received message remains invisible**.

---

## Using Very Small Wait Times

Configuring values such as **1 or 2 seconds** provides little benefit.

A value of **20 seconds** is generally recommended.

---

## Ignoring Empty Receives

A large number of empty receives increases costs and wastes compute resources.

Enable Long Polling to minimize empty responses.

---

# Summary

Long Polling improves the efficiency of Amazon SQS by allowing consumers to wait for messages instead of immediately receiving empty responses. It reduces API requests, lowers AWS costs, improves application performance, and minimizes unnecessary network traffic. For most production workloads, configuring a **20-second wait time** is considered a best practice.