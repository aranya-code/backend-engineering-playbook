# Introduction

Amazon SNS is built around two fundamental concepts:

- Topics
- Subscriptions

A **Topic** acts as a communication channel where publishers send messages.

A **Subscription** connects an endpoint (such as an SQS queue, Lambda function, or email address) to a topic so that it can receive published messages.

Without subscriptions, messages published to a topic have nowhere to be delivered.

---

# What is an SNS Topic?

An SNS Topic is a logical communication channel.

Publishers send messages to a topic rather than directly to subscribers.

Amazon SNS is responsible for delivering those messages to every subscribed endpoint.

```
Publisher

↓

SNS Topic

↓

Subscribers
```

A topic can have:

- One publisher
- Multiple publishers
- One subscriber
- Multiple subscribers

---

# Topic Architecture

```
                  Publisher

                      │

                      ▼

                Amazon SNS Topic

       ┌──────────┼──────────┬──────────┐

       ▼          ▼          ▼          ▼

     Email      SQS       Lambda      HTTP
```

Every published message is automatically delivered to all subscribers.

---

# What is a Subscription?

A subscription connects an endpoint to an SNS topic.

Whenever a message is published,

Amazon SNS delivers it to every active subscription.

```
SNS Topic

↓

Subscription

↓

Endpoint
```

Without subscriptions,

messages are discarded after publication.

---

# Supported Subscription Types

Amazon SNS supports multiple endpoint types.

| Protocol | Description |
|----------|-------------|
| Amazon SQS | Queue receives messages |
| AWS Lambda | Invokes Lambda function |
| HTTP | HTTP POST request |
| HTTPS | Secure HTTP POST |
| Email | Email notification |
| Email-JSON | Email containing JSON payload |
| SMS | Text message |
| Mobile Push | Mobile device notification |

---

# Topic Lifecycle

```
Create Topic

↓

Create Subscription

↓

Publish Message

↓

Amazon SNS

↓

Deliver Message

↓

Subscriber
```

---

# Standard Topics

Standard Topics provide:

- High throughput
- Best-effort ordering
- At-least-once delivery

Suitable for:

- Notifications
- Monitoring
- Alerts
- Event broadcasting

---

# FIFO Topics

FIFO Topics provide:

- Strict message ordering
- Message deduplication
- Exactly-once delivery (within the deduplication window)

Requirements

```
Topic Name

↓

orders.fifo
```

FIFO Topics can publish only to:

- FIFO SQS Queues

---

# Creating a Topic

## AWS Management Console

1. Open Amazon SNS.
2. Select **Topics**.
3. Click **Create Topic**.
4. Choose:

- Standard
- FIFO

5. Enter a topic name.
6. Configure encryption (optional).
7. Create the topic.

---

## AWS CLI

### Standard Topic

```bash
aws sns create-topic \
    --name order-events
```

---

### FIFO Topic

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
    Name="order-events"
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
      TopicName: order-events
```

---

## Terraform

```terraform
resource "aws_sns_topic" "order_topic" {

  name = "order-events"

}
```

---

# Topic ARN

Every SNS Topic has a unique Amazon Resource Name (ARN).

Example

```text
arn:aws:sns:us-east-1:123456789012:order-events
```

Publishers use the Topic ARN when sending messages.

---

# Creating a Subscription

A subscription connects a topic to an endpoint.

---

## AWS CLI

```bash
aws sns subscribe \
    --topic-arn TOPIC_ARN \
    --protocol sqs \
    --notification-endpoint QUEUE_ARN
```

---

## Email Subscription

```bash
aws sns subscribe \
    --topic-arn TOPIC_ARN \
    --protocol email \
    --notification-endpoint admin@example.com
```

---

## Lambda Subscription

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
    Protocol="email",
    Endpoint="admin@example.com"
)
```

---

# Subscription Confirmation

Some subscription protocols require confirmation.

Example:

```
Email Subscription

↓

Confirmation Email

↓

Click Confirmation Link

↓

Subscription Active
```

Protocols that typically require confirmation:

- Email
- HTTP
- HTTPS

AWS-managed services such as SQS and Lambda do not require manual confirmation when permissions are configured correctly.

---

# Listing Topics

## AWS CLI

```bash
aws sns list-topics
```

---

## Boto3

```python
response = sns.list_topics()

print(response["Topics"])
```

---

# Listing Subscriptions

## AWS CLI

```bash
aws sns list-subscriptions
```

---

## Boto3

```python
response = sns.list_subscriptions()

print(response["Subscriptions"])
```

---

# Deleting a Subscription

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

# Deleting a Topic

Deleting a topic removes:

- The topic
- All subscriptions
- Future message delivery

---

## AWS CLI

```bash
aws sns delete-topic \
    --topic-arn TOPIC_ARN
```

---

## Boto3

```python
sns.delete_topic(
    TopicArn=TOPIC_ARN
)
```

---

# Real-World Example

Suppose an e-commerce application processes orders.

```
Order Service

↓

SNS Topic

↓

Order Queue

↓

Inventory Queue

↓

Billing Queue

↓

Email Notification
```

A single published event automatically reaches every downstream service.

---

# Topic Naming Best Practices

Use descriptive names.

Examples

```
order-events

payment-events

inventory-events

user-notifications
```

Avoid generic names like:

```
topic1

test

demo
```

---

# Best Practices

- Create separate topics for different business domains.
- Use meaningful topic names.
- Remove unused subscriptions.
- Prefer SQS subscriptions for reliable processing.
- Use FIFO Topics only when ordering is required.
- Enable encryption for production topics.
- Restrict publishing permissions using IAM and Topic Policies.

---

# Common Mistakes

## Publishing Without Subscribers

Messages are delivered only to active subscriptions.

Without subscribers, published messages are discarded.

---

## Mixing Business Domains

Avoid using one topic for unrelated events.

Create separate topics for:

- Orders
- Payments
- Inventory
- Notifications

---

## Forgetting Email Confirmation

Email subscriptions remain in a **Pending Confirmation** state until the recipient confirms the subscription.

---

## Using FIFO Topics Unnecessarily

FIFO Topics provide ordering but have additional constraints.

Use Standard Topics unless ordering is a business requirement.

---

# Summary

Topics and subscriptions are the foundation of Amazon SNS. Publishers send messages to topics, while subscriptions determine where those messages are delivered. By using well-designed topics and appropriate subscription types, organizations can build scalable, loosely coupled, event-driven architectures that integrate seamlessly with AWS services and external applications.