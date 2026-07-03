# Introduction

Monitoring is a critical part of operating Amazon SNS in production.

Without monitoring, it becomes difficult to determine:

- Whether messages are being published successfully
- Whether subscribers are receiving messages
- Whether delivery failures are occurring
- Whether applications are functioning correctly

Amazon SNS integrates natively with **Amazon CloudWatch** and **AWS CloudTrail** to provide operational visibility, monitoring, alerting, and auditing.

---

# Monitoring Architecture

```
                Publisher

                    │

                    ▼

              Amazon SNS Topic

                    │

        ┌───────────┼────────────┐

        ▼           ▼            ▼

      Amazon      CloudWatch   CloudTrail

      Metrics      Alarms        Audit Logs
```

CloudWatch monitors performance.

CloudTrail records API activity.

---

# Amazon CloudWatch

Amazon CloudWatch collects operational metrics from Amazon SNS.

These metrics help answer questions such as:

- Is my application publishing messages?
- Are subscribers receiving notifications?
- Are deliveries failing?
- Are messages being filtered?

CloudWatch continuously collects these metrics without additional configuration.

---

# SNS Metrics Overview

| Metric | Description |
|----------|-------------|
| NumberOfMessagesPublished | Total published messages |
| NumberOfNotificationsDelivered | Successfully delivered notifications |
| NumberOfNotificationsFailed | Failed deliveries |
| NumberOfNotificationsFilteredOut | Messages filtered by subscription policies |
| PublishSize | Size of published messages |

---

# NumberOfMessagesPublished

This metric represents the total number of messages published to a topic.

```
Application

↓

Publish()

↓

SNS Topic

↓

CloudWatch Counter +1
```

Increasing values generally indicate normal application activity.

---

# NumberOfNotificationsDelivered

Tracks successful deliveries to subscribers.

```
SNS Topic

↓

SQS

↓

Delivered

↓

Metric +1
```

A healthy system should have a consistently increasing delivery count.

---

# NumberOfNotificationsFailed

Tracks failed notification deliveries.

```
SNS

↓

Subscriber

↓

Delivery Failed

↓

Metric +1
```

Possible causes include:

- Invalid endpoint
- Missing permissions
- Network issues
- Deleted subscribers

Production systems should alert on increasing failures.

---

# NumberOfNotificationsFilteredOut

Tracks messages that were intentionally not delivered because they did not match a subscription's filter policy.

```
SNS Topic

↓

Filter Policy

↓

No Match

↓

Filtered Out
```

This metric is useful when Message Filtering is enabled.

---

# Publish Size

Measures the size of published messages.

Large payloads may increase latency and processing costs.

Best practice:

Store large objects in Amazon S3 and publish only the object reference.

---

# Viewing Metrics

## AWS Management Console

1. Open Amazon CloudWatch.
2. Select **Metrics**.
3. Choose **SNS**.
4. Select **By Topic Name**.
5. View available metrics.

---

## AWS CLI

List SNS metrics.

```bash
aws cloudwatch list-metrics \
    --namespace AWS/SNS
```

---

Retrieve metric statistics.

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

# CloudWatch Dashboards

CloudWatch Dashboards allow multiple metrics to be viewed together.

Example dashboard

```
Amazon SNS

↓

Messages Published

↓

Notifications Delivered

↓

Notifications Failed

↓

Filtered Messages
```

Dashboards provide a centralized operational view.

---

# CloudWatch Alarms

CloudWatch Alarms automatically notify administrators when predefined thresholds are exceeded.

Example

```
Notifications Failed > 5

↓

CloudWatch Alarm

↓

Amazon SNS

↓

Email

↓

Operations Team
```

---

# Creating an Alarm

Example scenario

```
If

NumberOfNotificationsFailed

>

10

Within

5 Minutes

↓

Trigger Alarm
```

This allows rapid detection of delivery issues.

---

# Alarm Workflow

```
CloudWatch Metric

↓

Evaluate Threshold

↓

Alarm State

↓

Amazon SNS

↓

Email

↓

SMS

↓

Incident Management
```

---

# Monitoring Delivery Success

Healthy system

```
Published

↓

Delivered

↓

No Failures
```

Unhealthy system

```
Published

↓

Delivery Failed

↓

Retry

↓

CloudWatch Alarm
```

---

# Monitoring Message Filtering

When using Filter Policies,

monitor:

```
NumberOfNotificationsFilteredOut
```

Unexpected increases may indicate:

- Incorrect filter policies
- Missing message attributes
- Publisher errors

---

# CloudTrail Integration

CloudTrail records all Amazon SNS API activity.

Examples include:

- CreateTopic
- DeleteTopic
- Publish
- Subscribe
- Unsubscribe
- SetTopicAttributes

---

# CloudTrail Architecture

```
Developer

↓

SNS API

↓

CloudTrail

↓

Audit Logs
```

Every administrative action is recorded.

---

# Example CloudTrail Event

```json
{
  "eventName": "Publish",
  "eventSource": "sns.amazonaws.com",
  "userIdentity": {
    "type": "IAMUser"
  }
}
```

CloudTrail helps answer:

- Who published the message?
- When was it published?
- Which IAM identity performed the action?

---

# AWS Config Integration

AWS Config monitors SNS resource configuration.

It can detect changes such as:

- Topic deletion
- Encryption disabled
- Policy changes
- Topic configuration updates

Useful for compliance monitoring.

---

# Monitoring Best Practices

Monitor these key metrics.

| Metric | Why It Matters |
|----------|----------------|
| NumberOfMessagesPublished | Publisher activity |
| NumberOfNotificationsDelivered | Delivery success |
| NumberOfNotificationsFailed | Delivery failures |
| NumberOfNotificationsFilteredOut | Filter policy validation |
| PublishSize | Message size monitoring |

---

# Production Dashboard Example

```
Amazon SNS Dashboard

──────────────────────────────

Messages Published

Notifications Delivered

Notifications Failed

Filtered Messages

Average Publish Size

CloudWatch Alarms

──────────────────────────────
```

---

# Real-World Example

An online shopping platform.

```
Order Service

↓

Amazon SNS

↓

Inventory Queue

↓

Billing Queue

↓

Shipping Queue

↓

CloudWatch

↓

Alarm

↓

Operations Team
```

If delivery failures occur,

CloudWatch immediately notifies the operations team.

---

# Best Practices

- Create CloudWatch Dashboards for every production topic.
- Configure alarms for delivery failures.
- Monitor message filtering metrics.
- Enable CloudTrail in all AWS Regions.
- Regularly review CloudTrail logs.
- Monitor publish rates to identify unusual traffic.
- Investigate sudden drops in successful deliveries.
- Use AWS Config to detect unauthorized configuration changes.

---

# Common Mistakes

## Monitoring Only Published Messages

Publishing does not guarantee successful delivery.

Always monitor delivery metrics.

---

## Ignoring Failed Notifications

Even a small number of failures may indicate permission or configuration issues.

---

## Not Configuring CloudWatch Alarms

Without alarms, production issues may remain undetected.

---

## Ignoring CloudTrail

CloudTrail is essential for auditing security-sensitive operations.

---

## Not Monitoring Filtered Messages

Unexpected filtering often indicates incorrect Message Attributes or Filter Policies.

---

# Summary

Amazon SNS integrates with Amazon CloudWatch, AWS CloudTrail, and AWS Config to provide comprehensive monitoring and auditing capabilities. CloudWatch metrics help track message publishing, successful deliveries, failures, filtering activity, and message size, while CloudWatch Alarms enable proactive notification of operational issues. CloudTrail records all SNS API activity for auditing and compliance, making these services essential components of a secure and production-ready Amazon SNS deployment.