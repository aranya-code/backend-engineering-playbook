# Introduction

Even though Amazon SNS is a fully managed service, production issues can still occur due to:

- Incorrect IAM permissions
- Topic Policy misconfiguration
- Subscription failures
- Message filtering
- Endpoint failures
- Encryption issues
- Network problems

This chapter covers the most common Amazon SNS issues, their causes, troubleshooting steps, and recommended solutions.

---

# Troubleshooting Workflow

Whenever an SNS issue occurs, follow this process.

```
Problem Detected

↓

Identify Publisher

↓

Verify Topic

↓

Verify Subscription

↓

Check IAM

↓

Check Topic Policy

↓

Check CloudWatch

↓

Check CloudTrail

↓

Resolve Issue
```

---

# Problem 1 - Message Not Delivered

## Symptoms

- Publisher successfully publishes a message.
- Subscriber never receives it.

---

## Possible Causes

- Subscription does not exist
- Subscription is pending confirmation
- Incorrect Topic ARN
- Filter Policy mismatch
- Subscriber unavailable
- Topic Policy blocks delivery

---

## Troubleshooting

Verify subscriptions.

```bash
aws sns list-subscriptions-by-topic \
    --topic-arn TOPIC_ARN
```

Verify message publishing.

```bash
aws sns publish \
    --topic-arn TOPIC_ARN \
    --message "Test Message"
```

Check CloudWatch metrics.

```
NumberOfNotificationsDelivered

NumberOfNotificationsFailed
```

---

## Solution

- Confirm the subscription.
- Verify the Topic ARN.
- Review the Filter Policy.
- Verify endpoint permissions.
- Check subscriber logs.

---

# Problem 2 - Subscription Stuck in Pending Confirmation

## Symptoms

```
Status

↓

PendingConfirmation
```

---

## Cause

The recipient has not confirmed the subscription.

Common for:

- Email
- HTTP
- HTTPS

---

## Solution

Open the confirmation message.

Click the confirmation link.

After confirmation:

```
Pending

↓

Confirmed

↓

Active
```

---

# Problem 3 - AccessDenied Error

## Error

```text
AccessDenied

User is not authorized to perform sns:Publish
```

---

## Cause

Missing IAM permissions.

---

## Troubleshooting

Review IAM Policy.

Example

```json
{
    "Effect":"Allow",
    "Action":"sns:Publish",
    "Resource":"TOPIC_ARN"
}
```

---

## Solution

Grant the required SNS permissions.

Avoid granting:

```text
sns:*
```

Use only the required actions.

---

# Problem 4 - Invalid Topic ARN

## Error

```text
NotFound

Topic does not exist
```

---

## Cause

Incorrect Topic ARN.

Wrong Region.

Topic deleted.

---

## Troubleshooting

List topics.

```bash
aws sns list-topics
```

Verify the ARN.

Example

```text
arn:aws:sns:us-east-1:123456789012:order-events
```

---

## Solution

Update the application configuration.

Use the correct Region.

---

# Problem 5 - Messages Filtered Unexpectedly

## Symptoms

Messages are published.

Subscribers never receive them.

CloudWatch shows:

```
NumberOfNotificationsFilteredOut
```

Increasing.

---

## Cause

Filter Policy mismatch.

---

## Troubleshooting

Review Filter Policy.

Example

```json
{
    "EventType":[
        "Order"
    ]
}
```

Review published attributes.

```python
MessageAttributes={
    "EventType":{
        "DataType":"String",
        "StringValue":"Payment"
    }
}
```

---

## Solution

Update either:

- Message Attributes

or

- Subscription Filter Policy

---

# Problem 6 - HTTP Endpoint Not Receiving Messages

## Symptoms

SNS retries repeatedly.

Notifications fail.

---

## Possible Causes

- Endpoint unavailable
- HTTP 500 responses
- Timeout
- Firewall
- Incorrect URL

---

## Troubleshooting

Test the endpoint manually.

```bash
curl https://example.com/webhook
```

Check application logs.

Verify HTTP status codes.

---

## Solution

Ensure the endpoint returns:

```
HTTP 200
```

Promptly after processing.

---

# Problem 7 - Lambda Not Invoked

## Symptoms

Message published.

Lambda never runs.

---

## Possible Causes

- Missing invoke permission
- Wrong Lambda ARN
- Subscription deleted
- Lambda execution errors

---

## Troubleshooting

Check Lambda logs.

```text
CloudWatch Logs
```

Verify subscriptions.

```bash
aws sns list-subscriptions-by-topic \
    --topic-arn TOPIC_ARN
```

---

## Solution

Grant SNS permission to invoke Lambda.

Verify Lambda configuration.

---

# Problem 8 - SQS Queue Not Receiving Messages

## Symptoms

SNS publishes messages.

Queue remains empty.

---

## Cause

Missing Queue Policy.

---

## Troubleshooting

Review Queue Policy.

Ensure SNS Topic is allowed.

Example

```json
{
    "Effect":"Allow",
    "Principal":{
        "Service":"sns.amazonaws.com"
    },
    "Action":"sqs:SendMessage"
}
```

---

## Solution

Update the SQS Queue Policy.

Verify the Topic ARN.

---

# Problem 9 - Encryption Errors

## Symptoms

Publishing fails.

Access denied.

---

## Cause

AWS KMS permissions missing.

---

## Troubleshooting

Review KMS permissions.

Verify:

```
KmsMasterKeyId
```

Check CloudTrail.

---

## Solution

Grant required KMS permissions.

---

# Problem 10 - Duplicate Messages

## Symptoms

Subscriber processes the same event multiple times.

---

## Cause

Possible reasons include:

- Subscriber retry
- Duplicate publish
- Standard Topic behavior
- Application bug

---

## Solution

Implement idempotent processing.

Example

```
Receive Event

↓

Already Processed?

↓

Yes

↓

Ignore
```

---

# Problem 11 - Topic Deleted Accidentally

## Symptoms

Publish operations fail.

---

## Error

```text
NotFound
```

---

## Troubleshooting

```bash
aws sns list-topics
```

Review CloudTrail.

```
DeleteTopic
```

---

## Solution

Recreate the topic.

Restore Infrastructure as Code.

---

# Problem 12 - CloudWatch Alarm Never Triggers

## Cause

Wrong metric.

Wrong threshold.

Alarm disabled.

---

## Troubleshooting

Verify:

- Metric Name
- Namespace
- Period
- Statistic
- Threshold

---

## Solution

Update the alarm configuration.

---

# Useful AWS CLI Commands

## List Topics

```bash
aws sns list-topics
```

---

## List Subscriptions

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

## Publish Test Message

```bash
aws sns publish \
    --topic-arn TOPIC_ARN \
    --message "Test Message"
```

---

## Get Topic Attributes

```bash
aws sns get-topic-attributes \
    --topic-arn TOPIC_ARN
```

---

# Troubleshooting Checklist

Before investigating deeper, verify:

- ☐ Topic exists
- ☐ Topic ARN is correct
- ☐ Subscription exists
- ☐ Subscription confirmed
- ☐ IAM permissions verified
- ☐ Topic Policy reviewed
- ☐ Queue Policy reviewed (for SQS)
- ☐ Lambda permissions verified
- ☐ Message Attributes reviewed
- ☐ Filter Policy reviewed
- ☐ KMS permissions verified
- ☐ CloudWatch metrics reviewed
- ☐ CloudTrail events reviewed

---

# CloudWatch Metrics to Check

| Metric | Purpose |
|----------|----------|
| NumberOfMessagesPublished | Publishing activity |
| NumberOfNotificationsDelivered | Successful delivery |
| NumberOfNotificationsFailed | Failed delivery |
| NumberOfNotificationsFilteredOut | Filter policy validation |
| PublishSize | Message size |

---

# CloudTrail Events

Useful events include:

- CreateTopic
- DeleteTopic
- Publish
- Subscribe
- Unsubscribe
- SetTopicAttributes

---

# Best Practices

- Test subscriptions before production deployment.
- Monitor CloudWatch metrics continuously.
- Enable CloudTrail in every AWS account.
- Use Infrastructure as Code.
- Keep subscriber endpoints highly available.
- Implement idempotent consumers.
- Validate Topic Policies after every deployment.
- Monitor KMS permissions after enabling encryption.

---

# Common Mistakes

## Forgetting Subscription Confirmation

Email and HTTP subscriptions remain inactive until confirmed.

---

## Ignoring Filter Policies

Many delivery issues are caused by incorrect filter configurations.

---

## Missing Queue Policies

Amazon SQS subscriptions require explicit permission to receive messages from SNS.

---

## Not Monitoring CloudWatch

Without monitoring, delivery failures may go unnoticed.

---

## Publishing to the Wrong Topic

Verify the Topic ARN and AWS Region before publishing.

---

# Summary

Most Amazon SNS issues are caused by configuration problems rather than service failures. By systematically checking subscriptions, IAM permissions, Topic Policies, Queue Policies, Message Attributes, Filter Policies, CloudWatch metrics, and CloudTrail logs, engineers can quickly identify and resolve delivery problems. Following a structured troubleshooting workflow significantly reduces downtime and ensures reliable event-driven communication.