# Introduction

Amazon SNS can be managed through multiple interfaces:

- AWS Management Console
- AWS CLI
- Boto3 (Python SDK)
- CloudFormation
- Terraform
- AWS CDK

This chapter serves as a quick reference for the most commonly used **AWS CLI** commands and **Boto3** methods used in day-to-day development and operations.

---

# AWS CLI Configuration

Verify the AWS CLI installation.

```bash
aws --version
```

Configure credentials.

```bash
aws configure
```

Verify the active AWS account.

```bash
aws sts get-caller-identity
```

---

# Topic Operations

## Create a Standard Topic

```bash
aws sns create-topic \
    --name order-events
```

---

## Create a FIFO Topic

```bash
aws sns create-topic \
    --name order-events.fifo \
    --attributes FifoTopic=true
```

---

## Create FIFO Topic with Content-Based Deduplication

```bash
aws sns create-topic \
    --name order-events.fifo \
    --attributes \
FifoTopic=true,ContentBasedDeduplication=true
```

---

## List Topics

```bash
aws sns list-topics
```

---

## Delete Topic

```bash
aws sns delete-topic \
    --topic-arn TOPIC_ARN
```

---

# Topic Attributes

## Get Topic Attributes

```bash
aws sns get-topic-attributes \
    --topic-arn TOPIC_ARN
```

---

## Set Display Name

```bash
aws sns set-topic-attributes \
    --topic-arn TOPIC_ARN \
    --attribute-name DisplayName \
    --attribute-value Orders
```

---

## Enable Server-Side Encryption

```bash
aws sns set-topic-attributes \
    --topic-arn TOPIC_ARN \
    --attribute-name KmsMasterKeyId \
    --attribute-value alias/aws/sns
```

---

## Update Topic Policy

```bash
aws sns set-topic-attributes \
    --topic-arn TOPIC_ARN \
    --attribute-name Policy \
    --attribute-value file://policy.json
```

---

# Publishing Messages

## Publish Simple Message

```bash
aws sns publish \
    --topic-arn TOPIC_ARN \
    --message "Hello AWS"
```

---

## Publish with Subject

```bash
aws sns publish \
    --topic-arn TOPIC_ARN \
    --subject "Deployment Complete" \
    --message "Application deployed successfully."
```

---

## Publish with Message Attributes

```bash
aws sns publish \
    --topic-arn TOPIC_ARN \
    --message "Order Created" \
    --message-attributes '{
        "EventType":{
            "DataType":"String",
            "StringValue":"Order"
        }
    }'
```

---

## Publish to FIFO Topic

```bash
aws sns publish \
    --topic-arn FIFO_TOPIC_ARN \
    --message "Order Created" \
    --message-group-id orders \
    --message-deduplication-id order-101
```

---

# Subscription Operations

## Create Email Subscription

```bash
aws sns subscribe \
    --topic-arn TOPIC_ARN \
    --protocol email \
    --notification-endpoint admin@example.com
```

---

## Create SQS Subscription

```bash
aws sns subscribe \
    --topic-arn TOPIC_ARN \
    --protocol sqs \
    --notification-endpoint QUEUE_ARN
```

---

## Create Lambda Subscription

```bash
aws sns subscribe \
    --topic-arn TOPIC_ARN \
    --protocol lambda \
    --notification-endpoint LAMBDA_ARN
```

---

## Create HTTPS Subscription

```bash
aws sns subscribe \
    --topic-arn TOPIC_ARN \
    --protocol https \
    --notification-endpoint https://example.com/webhook
```

---

## List All Subscriptions

```bash
aws sns list-subscriptions
```

---

## List Topic Subscriptions

```bash
aws sns list-subscriptions-by-topic \
    --topic-arn TOPIC_ARN
```

---

## Delete Subscription

```bash
aws sns unsubscribe \
    --subscription-arn SUBSCRIPTION_ARN
```

---

# Message Filtering

## Apply Filter Policy

```bash
aws sns set-subscription-attributes \
    --subscription-arn SUBSCRIPTION_ARN \
    --attribute-name FilterPolicy \
    --attribute-value '{"EventType":["Order"]}'
```

---

## Remove Filter Policy

```bash
aws sns set-subscription-attributes \
    --subscription-arn SUBSCRIPTION_ARN \
    --attribute-name FilterPolicy \
    --attribute-value "{}"
```

---

# CloudWatch Commands

## List SNS Metrics

```bash
aws cloudwatch list-metrics \
    --namespace AWS/SNS
```

---

## Retrieve SNS Metrics

```bash
aws cloudwatch get-metric-statistics \
    --namespace AWS/SNS \
    --metric-name NumberOfMessagesPublished \
    --start-time 2026-07-01T00:00:00Z \
    --end-time 2026-07-02T00:00:00Z \
    --period 300 \
    --statistics Sum
```

---

# Boto3 Configuration

Install Boto3.

```bash
pip install boto3
```

---

Create an SNS client.

```python
import boto3

sns = boto3.client("sns")
```

---

# Create Topic

```python
response = sns.create_topic(
    Name="order-events"
)

print(response["TopicArn"])
```

---

# Create FIFO Topic

```python
response = sns.create_topic(
    Name="order-events.fifo",
    Attributes={
        "FifoTopic": "true"
    }
)
```

---

# Delete Topic

```python
sns.delete_topic(
    TopicArn=TOPIC_ARN
)
```

---

# List Topics

```python
response = sns.list_topics()

for topic in response["Topics"]:
    print(topic["TopicArn"])
```

---

# Publish Message

```python
sns.publish(
    TopicArn=TOPIC_ARN,
    Message="Order Created"
)
```

---

# Publish with Subject

```python
sns.publish(
    TopicArn=TOPIC_ARN,
    Subject="Deployment",
    Message="Deployment completed."
)
```

---

# Publish with Message Attributes

```python
sns.publish(
    TopicArn=TOPIC_ARN,
    Message="Order Created",
    MessageAttributes={
        "EventType": {
            "DataType": "String",
            "StringValue": "Order"
        }
    }
)
```

---

# Publish to FIFO Topic

```python
sns.publish(
    TopicArn=FIFO_TOPIC_ARN,
    Message="Order Created",
    MessageGroupId="orders",
    MessageDeduplicationId="order-101"
)
```

---

# Subscribe an Email

```python
sns.subscribe(
    TopicArn=TOPIC_ARN,
    Protocol="email",
    Endpoint="admin@example.com"
)
```

---

# Subscribe an SQS Queue

```python
sns.subscribe(
    TopicArn=TOPIC_ARN,
    Protocol="sqs",
    Endpoint=QUEUE_ARN
)
```

---

# Subscribe a Lambda Function

```python
sns.subscribe(
    TopicArn=TOPIC_ARN,
    Protocol="lambda",
    Endpoint=LAMBDA_ARN
)
```

---

# List Subscriptions

```python
response = sns.list_subscriptions()

for subscription in response["Subscriptions"]:
    print(subscription["SubscriptionArn"])
```

---

# List Subscriptions by Topic

```python
response = sns.list_subscriptions_by_topic(
    TopicArn=TOPIC_ARN
)
```

---

# Delete Subscription

```python
sns.unsubscribe(
    SubscriptionArn=SUBSCRIPTION_ARN
)
```

---

# Apply a Filter Policy

```python
import json

sns.set_subscription_attributes(
    SubscriptionArn=SUBSCRIPTION_ARN,
    AttributeName="FilterPolicy",
    AttributeValue=json.dumps({
        "EventType": [
            "Order"
        ]
    })
)
```

---

# Enable Encryption

```python
sns.set_topic_attributes(
    TopicArn=TOPIC_ARN,
    AttributeName="KmsMasterKeyId",
    AttributeValue="alias/aws/sns"
)
```

---

# Common SNS API Methods

| Method | Description |
|----------|-------------|
| create_topic() | Create a topic |
| delete_topic() | Delete a topic |
| list_topics() | List topics |
| publish() | Publish a message |
| subscribe() | Create a subscription |
| unsubscribe() | Remove a subscription |
| list_subscriptions() | List subscriptions |
| list_subscriptions_by_topic() | List subscriptions for a topic |
| get_topic_attributes() | Get topic configuration |
| set_topic_attributes() | Update topic configuration |
| set_subscription_attributes() | Configure subscription settings |

---

# Common CLI Commands

| Command | Purpose |
|----------|----------|
| create-topic | Create a topic |
| delete-topic | Delete a topic |
| list-topics | View topics |
| publish | Publish messages |
| subscribe | Create subscriptions |
| unsubscribe | Remove subscriptions |
| list-subscriptions | View subscriptions |
| get-topic-attributes | View topic configuration |
| set-topic-attributes | Modify topic configuration |

---

# Developer Workflow

```
Create Topic

↓

Create Subscription

↓

Publish Message

↓

Verify Delivery

↓

Configure Filter Policies

↓

Enable Encryption

↓

Monitor CloudWatch

↓

Delete Resources
```

---

# Best Practices

- Store Topic ARNs in configuration files or AWS Systems Manager Parameter Store.
- Use IAM Roles instead of hardcoded credentials.
- Handle exceptions when publishing messages.
- Use Message Attributes instead of embedding metadata in the message body.
- Reuse the Boto3 client across requests for better performance.
- Enable CloudWatch monitoring for production topics.
- Use Infrastructure as Code (CloudFormation, Terraform, or CDK) to provision SNS resources.

---

# Summary

The AWS CLI and Boto3 SDK provide comprehensive interfaces for managing Amazon SNS topics, subscriptions, message publishing, filtering, encryption, and monitoring. Mastering these commands and API methods enables developers and cloud engineers to automate SNS operations, integrate messaging into applications, and manage production environments efficiently.