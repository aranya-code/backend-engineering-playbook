# Troubleshooting & Best Practices

> Learn how to troubleshoot Amazon SNS Topics, diagnose message delivery failures, resolve subscription issues, monitor notification systems, and apply production-grade operational best practices using Amazon SNS and the AWS CLI.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Troubleshoot Amazon SNS Topics
- Diagnose publishing failures
- Resolve subscription issues
- Debug notification delivery
- Monitor SNS health
- Recover from production failures
- Apply enterprise messaging best practices

---

# Troubleshooting Workflow

Always troubleshoot from the publisher toward the subscriber.

```text
Publisher

↓

Amazon SNS

↓

Subscription

↓

Endpoint

↓

Application
```

---

# Verify Topic Exists

List Topics.

```bash
aws sns list-topics
```

Verify a Topic.

```bash
aws sns get-topic-attributes \
--topic-arn TOPIC_ARN
```

Review:

- Topic ARN
- Policy
- Encryption
- FIFO configuration

---

# Cannot Publish Messages

Possible causes:

- Invalid Topic ARN
- IAM permission denied
- Topic Policy denied
- Incorrect Region
- Topic deleted

---

# NotFound Error

Verify:

- Topic ARN
- AWS Region
- AWS Account

---

# AuthorizationError

Verify:

- IAM Policy
- Topic Policy
- AWS Organizations SCP (if applicable)

Ensure:

```text
Publisher

↓

sns:Publish
```

permission exists.

---

# Subscription Not Receiving Messages

Verify:

- Subscription exists
- Subscription confirmed
- Endpoint healthy
- Topic Policy
- Filter Policy

---

# Pending Confirmation

Email subscriptions require confirmation.

Workflow:

```text
Subscription

↓

PendingConfirmation

↓

User Confirms

↓

Active
```

Messages are not delivered until confirmation is complete.

---

# Email Not Received

Verify:

- Email address
- Spam folder
- Subscription confirmation
- Topic subscription

---

# SMS Not Delivered

Verify:

- Phone number format
- SMS spending limits
- Supported destination country
- AWS SNS SMS configuration

---

# HTTP Endpoint Failure

Possible causes:

- Server unavailable
- HTTP 500 errors
- Invalid certificate
- Firewall restrictions

Verify endpoint accessibility.

---

# HTTPS Endpoint Failure

Review:

- TLS certificate
- HTTPS endpoint
- Network connectivity
- Delivery Policy

---

# Lambda Not Invoked

Verify:

- Lambda subscription
- Lambda permissions
- Topic ARN
- Region

Review CloudWatch Logs.

---

# SQS Not Receiving Messages

Verify:

- Queue subscription
- Queue Policy
- Topic Policy
- Queue ARN

Architecture:

```text
Amazon SNS

↓

Amazon SQS

↓

Workers
```

---

# Message Filtering Problems

Symptoms:

Subscriber receives nothing.

Verify:

- Filter Policy
- Message Attributes
- Attribute names
- Attribute values

Example:

```json
{
  "eventType": [
    "OrderCreated"
  ]
}
```

Only matching events are delivered.

---

# FIFO Topic Issues

Verify:

- Topic ends with:

```text
.fifo
```

- MessageGroupId supplied
- Deduplication configured

---

# Duplicate Notifications

Possible causes:

- Duplicate publish request
- Multiple subscriptions
- Consumer retry logic

Applications should tolerate duplicate events.

---

# Message Delivery Failure

Possible causes:

- Endpoint unavailable
- Invalid subscription
- Delivery Policy
- IAM permissions

Review subscriber logs.

---

# CloudWatch Monitoring

Monitor:

- NumberOfMessagesPublished
- NumberOfNotificationsDelivered
- NumberOfNotificationsFailed
- PublishSize
- SMSMonthToDateSpentUSD

---

# CloudWatch Alarms

Recommended alarms:

```text
Notification Failures
```

```text
Publish Errors
```

```text
SMS Spending
```

```text
Endpoint Failures
```

---

# CloudTrail

Review CloudTrail for:

- Topic creation
- Topic deletion
- Publish requests
- Subscription changes
- Topic Policy updates

Useful for:

- Auditing
- Compliance
- Security investigations

---

# Encryption Problems

If using AWS KMS:

Verify:

- KMS Key
- IAM permissions
- KMS Key Policy
- Region

Common error:

```text
KMSAccessDeniedException
```

---

# Cross-Account Issues

Verify:

- Topic Policy
- IAM Role
- AWS Account ID
- Region

Both accounts must allow access.

---

# Delivery Policy Problems

Symptoms:

- Retry failures
- Delayed notifications
- HTTP endpoint failures

Review:

- Retry configuration
- Endpoint availability
- Network latency

---

# Topic Policy Problems

Verify:

- Principal
- Action
- Resource
- Conditions

Ensure both IAM and Topic Policies allow access.

---

# CloudWatch Alarm Not Publishing

Verify:

- Alarm state
- SNS Topic ARN
- Subscription
- IAM Role

---

# Endpoint Disabled

Possible causes:

- Deleted Lambda
- Deleted Queue
- Invalid Email
- Invalid HTTP endpoint

Update or recreate the subscription.

---

# Production Health Checklist

Daily review:

- Published messages
- Failed deliveries
- Subscription health
- CloudWatch alarms
- CloudTrail logs
- SMS spending

---

# Weekly Checklist

Review:

- Topic Policies
- IAM Roles
- KMS configuration
- Subscription list
- Filter Policies
- Delivery Policies
- CloudWatch dashboards

---

# Production Best Practices

## Encrypt Every Topic

Use AWS KMS for sensitive workloads.

---

## Use Least Privilege

Grant only required IAM permissions.

---

## Monitor Delivery Failures

Configure CloudWatch alarms.

---

## Remove Unused Subscriptions

Reduce unnecessary message delivery.

---

## Prefer SNS + SQS

Avoid direct delivery for critical business processing.

---

## Monitor CloudTrail

Review security events regularly.

---

## Use HTTPS Endpoints

Avoid unsecured HTTP endpoints.

---

## Filter Messages

Reduce unnecessary processing with Filter Policies.

---

## Use Business Event Topics

Examples:

```text
OrderCreated

PaymentCompleted

InventoryUpdated
```

Avoid generic Topics.

---

# Real-World Workflow

```text
Application Error

↓

CloudWatch Alarm

↓

Amazon SNS

↓

Operations Team

↓

Investigate

↓

Resolve
```

---

# Architecture Note

```text
Publisher
      │
      ▼
Amazon SNS
      │
      ├── CloudWatch
      ├── CloudTrail
      ├── AWS KMS
      ├── Topic Policy
      └── Subscribers
              │
              ▼
Applications
```

A production Amazon SNS deployment should be continuously monitored using CloudWatch, secured with IAM and Topic Policies, protected by AWS KMS encryption, and audited using CloudTrail to ensure reliable and secure event delivery.

---

# Interview Note

### Question

**How would you troubleshoot an Amazon SNS Topic that is not delivering notifications?**

### Answer

I would first verify that the Topic exists and that publishing succeeds without authorization errors. Next, I would confirm that the subscription is active and, for email subscriptions, that it has been confirmed. I would inspect the subscriber endpoint, such as an SQS queue, Lambda function, or HTTPS endpoint, to ensure it is healthy and properly configured. I would also review Topic Policies, IAM permissions, Filter Policies, and CloudWatch metrics for delivery failures. Finally, I would examine CloudTrail logs to identify any recent configuration changes or permission issues.

---

# Key Takeaways

- Troubleshoot Amazon SNS from publishers to subscribers.
- Verify Topic ARN, subscriptions, IAM permissions, and Topic Policies.
- CloudWatch provides visibility into publishing and delivery metrics.
- CloudTrail records every SNS API operation for auditing.
- AWS KMS secures Topics with encryption at rest.
- Filter Policies can intentionally prevent message delivery if attributes do not match.
- Combining monitoring, encryption, access control, and reliable subscriber endpoints results in a secure, production-ready notification platform.