# 05 - CloudTrail, CloudWatch & Auditing

## Overview

Security does not end with authentication and authorization.

A production system must answer questions like:

- Who accessed my DynamoDB table?
- Who deleted an item?
- Who changed table capacity?
- Why is the application suddenly throttling?
- When did replication fail?
- Is someone trying to access unauthorized data?

This is where **observability** becomes critical.

AWS provides several services that together create a complete auditing and monitoring solution.

| Service | Purpose |
|----------|---------|
| CloudTrail | Audit API calls |
| CloudWatch | Metrics, Logs & Alarms |
| AWS Config | Configuration compliance |
| EventBridge | Automated responses |
| Security Hub | Security findings |

Together they provide visibility into every aspect of DynamoDB.

---

# Learning Objectives

After completing this chapter, you'll understand:

- CloudTrail auditing
- CloudWatch metrics
- CloudWatch alarms
- Audit logging
- Compliance monitoring
- Security monitoring
- Operational dashboards
- Incident investigation

---

# Monitoring vs Auditing

These are different concepts.

## Monitoring

Answers:

> **How is my system performing?**

Examples:

- CPU
- Latency
- Errors
- Throughput
- Throttling

---

## Auditing

Answers:

> **Who performed which action?**

Examples:

- Deleted table
- Modified IAM policy
- Changed capacity
- Disabled encryption

---

# Monitoring Architecture

```text
Application

↓

DynamoDB

↓

CloudWatch Metrics

↓

CloudWatch Alarm

↓

SNS

↓

Email / Slack / PagerDuty
```

Operations teams receive alerts before customers notice problems.

---

# Audit Architecture

```text
Application

↓

AWS API

↓

CloudTrail

↓

Amazon S3

↓

Athena

↓

Security Investigation
```

Every API request becomes searchable.

---

# CloudTrail

CloudTrail records nearly every management API call.

Examples:

```text
CreateTable

DeleteTable

UpdateTable

PutItem

UpdateItem*

DeleteItem*

DescribeTable
```

> *Data events such as `PutItem`, `UpdateItem`, and `DeleteItem` require CloudTrail Data Events to be enabled.

CloudTrail provides:

- Identity
- Timestamp
- Source IP
- API name
- Request parameters
- Response status

---

# Example CloudTrail Record

```text
User

↓

Alice

↓

DeleteTable

↓

Orders

↓

2026-08-10 14:35 UTC

↓

Success
```

Operations teams know exactly what happened.

---

# CloudTrail Event Flow

```text
AWS SDK

↓

DynamoDB API

↓

CloudTrail

↓

Event Log

↓

Amazon S3
```

Events become searchable for investigations.

---

# CloudWatch Metrics

CloudWatch continuously collects DynamoDB metrics.

Common metrics include:

```text
ConsumedReadCapacityUnits

ConsumedWriteCapacityUnits

ReadThrottleEvents

WriteThrottleEvents

SystemErrors

UserErrors

SuccessfulRequestLatency

ReturnedItemCount
```

These metrics update automatically.

---

# Metric Collection Flow

```text
DynamoDB

↓

CloudWatch Metrics

↓

Dashboard

↓

Alarm
```

No application code is required.

---

# Read Capacity Monitoring

Example:

```text
Provisioned

↓

100 RCU

────────────

Consumed

↓

98 RCU
```

Operations should investigate before throttling occurs.

---

# Write Capacity Monitoring

```text
Provisioned

↓

500 WCU

────────────

Consumed

↓

495 WCU
```

Capacity planning prevents outages.

---

# Monitoring Throttling

One of the most important metrics:

```text
ReadThrottleEvents

WriteThrottleEvents
```

Workflow:

```text
Traffic Spike

↓

Capacity Limit

↓

Throttle

↓

CloudWatch Alarm
```

The team is notified immediately.

---

# Monitoring Latency

CloudWatch tracks:

```text
SuccessfulRequestLatency
```

Example:

```text
Normal

↓

4 ms

────────────

Current

↓

60 ms
```

This often indicates:

- Hot partitions
- Network issues
- Capacity bottlenecks
- Application problems

---

# CloudWatch Dashboards

Operations teams typically build dashboards.

```text
Read Capacity

Write Capacity

Latency

Errors

Throttles

Replication
```

Everything is visible in one place.

---

# CloudWatch Alarms

Example:

```text
ReadThrottleEvents > 0

↓

Alarm

↓

SNS

↓

Email
```

Or:

```text
Latency > 20 ms

↓

PagerDuty Alert
```

Production issues are detected automatically.

---

# CloudTrail + CloudWatch

These services complement each other.

```text
CloudTrail

↓

Who changed capacity?

────────────

CloudWatch

↓

Capacity fully utilized
```

Together they explain both **what happened** and **why performance changed**.

---

# Security Monitoring

CloudTrail detects:

```text
Unauthorized Access

↓

Failed Requests

↓

IAM Changes

↓

Table Deletion

↓

KMS Changes
```

Security teams investigate suspicious activity.

---

# Compliance Monitoring

Many regulations require audit logs.

Examples:

- PCI DSS
- HIPAA
- SOC 2
- ISO 27001
- GDPR

CloudTrail provides immutable audit records for compliance reporting.

---

# AWS Config Integration

AWS Config continuously evaluates resource configuration.

Example:

```text
DynamoDB Table

↓

Encryption Disabled

↓

Config Rule

↓

Non-Compliant
```

Teams receive compliance notifications.

---

# EventBridge Automation

CloudTrail events can trigger automation.

```text
DeleteTable

↓

CloudTrail

↓

EventBridge

↓

Lambda

↓

Slack Notification
```

Or:

```text
Table Created

↓

Automatically Tag Resources
```

---

# Production Architecture

```text
                DynamoDB

                     │

      ┌──────────────┼──────────────┐

      ▼                             ▼

CloudWatch                    CloudTrail

      │                             │

      ▼                             ▼

 Dashboards                    Audit Logs

      │                             │

      ▼                             ▼

  Alarms                     Amazon S3

      │                             │

      ▼                             ▼

 SNS / PagerDuty          Athena / Security Team
```

---

# Best Practices

- Enable CloudTrail organization-wide.
- Store CloudTrail logs in Amazon S3.
- Enable CloudTrail log validation.
- Create CloudWatch dashboards for production tables.
- Configure alarms for throttling.
- Monitor latency trends.
- Enable AWS Config compliance rules.
- Automate responses using EventBridge.
- Retain audit logs according to compliance requirements.

---

# Common Mistakes

## Monitoring Only CPU

DynamoDB is serverless.

Instead monitor:

- Capacity consumption
- Throttles
- Latency
- Errors

---

## Ignoring Throttling

Many teams notice throttling only after customers complain.

Always configure alarms.

---

## Disabling CloudTrail

Without CloudTrail:

```text
Table Deleted

↓

Unknown User

↓

Unknown Time
```

Incident investigations become extremely difficult.

---

## Not Enabling Data Events

Management events show:

```text
CreateTable

DeleteTable
```

But not individual item operations.

Enable Data Events when item-level auditing is required.

---

# Production Considerations

Enterprise monitoring commonly includes:

```text
CloudWatch

+

CloudTrail

+

AWS Config

+

Security Hub

+

GuardDuty

+

EventBridge
```

This provides:

- Operational monitoring
- Security auditing
- Compliance reporting
- Automated incident response
- Centralized visibility

---

# Interview Notes

A common interview question is:

> **What is the difference between CloudTrail and CloudWatch?**

CloudTrail records API activity for auditing and security investigations. CloudWatch collects operational metrics, logs, dashboards, and alarms for monitoring application health.

---

Another common question is:

> **Which CloudWatch metrics are most important for DynamoDB?**

Key metrics include:

- ConsumedReadCapacityUnits
- ConsumedWriteCapacityUnits
- ReadThrottleEvents
- WriteThrottleEvents
- SuccessfulRequestLatency
- SystemErrors
- UserErrors

---

Another common question is:

> **Can CloudTrail record item-level operations?**

Yes. CloudTrail can record item-level operations such as `PutItem`, `UpdateItem`, and `DeleteItem` when **Data Events** are enabled. By default, CloudTrail primarily records management events.

---

Another common question is:

> **How would you detect someone deleting a DynamoDB table?**

CloudTrail records the `DeleteTable` API call. You can create an EventBridge rule to detect this event and automatically notify operations teams or trigger incident response workflows.

---

# Key Takeaways

- CloudTrail provides a complete audit trail of DynamoDB API activity.
- CloudWatch monitors performance, latency, capacity consumption, and throttling.
- CloudWatch Alarms enable proactive incident detection and notification.
- AWS Config helps maintain compliance by detecting configuration drift.
- EventBridge can automate responses to CloudTrail events.
- A production-ready DynamoDB deployment combines CloudTrail, CloudWatch, Config, Security Hub, and GuardDuty for comprehensive security and observability.