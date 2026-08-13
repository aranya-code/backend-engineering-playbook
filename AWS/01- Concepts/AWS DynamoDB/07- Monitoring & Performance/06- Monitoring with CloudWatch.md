# 06 - Monitoring with CloudWatch

## Overview

Building a scalable DynamoDB application is only half the job.

The other half is continuously monitoring its health, performance, and capacity.

Without proper monitoring, problems such as:

- Throttling
- Capacity exhaustion
- High latency
- Traffic spikes
- Failed requests

may go unnoticed until customers are affected.

Amazon CloudWatch is the primary monitoring service for DynamoDB. It automatically collects operational metrics and enables dashboards, alarms, and automated actions.

---

# Learning Objectives

After completing this chapter, you'll understand:

- How CloudWatch integrates with DynamoDB
- Important CloudWatch metrics
- CloudWatch Dashboards
- CloudWatch Alarms
- Production monitoring strategies
- Capacity monitoring
- Latency monitoring
- Automated alerting
- Best practices
- Interview questions

---

# Monitoring Architecture

```text
                Application

                      │

                      ▼

                DynamoDB Table

                      │

                      ▼

          CloudWatch Metrics

          ┌──────────┼──────────┐

          ▼          ▼          ▼

      Dashboard    Alarm     Logs

          │

          ▼

 SNS / Email / Slack / PagerDuty
```

CloudWatch automatically collects operational metrics from DynamoDB.

---

# Why Monitoring Matters

Monitoring helps answer questions such as:

- Is the table throttling?
- Are reads increasing?
- Are writes decreasing?
- Is latency growing?
- Is Auto Scaling working?
- Is the application healthy?

Without monitoring, these questions become difficult to answer during incidents.

---

# Metric Categories

CloudWatch provides metrics for:

- Capacity
- Performance
- Errors
- Latency
- Throttling
- Replication

---

# Capacity Metrics

The most frequently monitored metrics are:

```text
ConsumedReadCapacityUnits

ConsumedWriteCapacityUnits

ProvisionedReadCapacityUnits

ProvisionedWriteCapacityUnits
```

These indicate how efficiently the table is utilizing its allocated throughput.

---

# Capacity Monitoring Example

```text
Provisioned

↓

1000 RCU

────────────

Consumed

↓

950 RCU
```

Utilization:

```text
95%
```

The application is approaching its capacity limit.

---

# Read Monitoring

```text
Application

↓

GetItem

↓

ConsumedReadCapacityUnits

↓

CloudWatch
```

Track trends over time to identify growing demand.

---

# Write Monitoring

```text
Application

↓

PutItem

↓

ConsumedWriteCapacityUnits

↓

CloudWatch
```

Rapid increases may indicate:

- New customers
- Seasonal traffic
- Batch jobs
- Application bugs

---

# Throttling Metrics

One of the most important metrics.

```text
ReadThrottleEvents

WriteThrottleEvents
```

Workflow:

```text
Traffic Spike

↓

Capacity Exceeded

↓

Throttle

↓

CloudWatch Metric
```

Even a small increase in throttling deserves investigation.

---

# Latency Metrics

CloudWatch reports:

```text
SuccessfulRequestLatency
```

Example:

```text
Normal

↓

5 ms

────────────

Current

↓

30 ms
```

Possible causes:

- Hot partitions
- Large items
- Network issues
- Application retries

---

# Error Metrics

Monitor:

```text
SystemErrors

UserErrors
```

System Errors may indicate AWS-side issues.

User Errors often indicate:

- Invalid requests
- Permission failures
- Conditional check failures
- Validation errors

---

# DynamoDB Streams Metrics

Applications using Streams should also monitor:

- Iterator age
- Processing latency
- Consumer health

Architecture:

```text
DynamoDB Streams

↓

Lambda

↓

CloudWatch Metrics
```

High iterator age may indicate that consumers cannot keep up.

---

# CloudWatch Dashboards

Dashboards provide centralized visibility.

Example dashboard:

```text
Orders Table

────────────

Read Capacity

Write Capacity

Latency

Throttling

Errors

Auto Scaling
```

Operations teams can monitor the entire workload from a single screen.

---

# Recommended Dashboard

A production dashboard should include:

```text
Consumed RCUs

Consumed WCUs

Provisioned RCUs

Provisioned WCUs

Read Throttles

Write Throttles

Latency

System Errors

User Errors
```

---

# CloudWatch Alarms

Alarms notify engineers when thresholds are exceeded.

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

---

Another example:

```text
Latency > 20 ms

↓

Alarm

↓

PagerDuty
```

Teams are notified before customers experience widespread issues.

---

# Capacity Alarm Example

```text
Consumed Capacity

↓

85%

↓

Warning

────────────

95%

↓

Critical Alarm
```

This allows proactive scaling before throttling begins.

---

# Auto Scaling Integration

CloudWatch provides the metrics used by Auto Scaling.

```text
Consumed Capacity

↓

CloudWatch

↓

Target Tracking Policy

↓

Scale Out
```

Monitoring and scaling work together.

---

# CloudWatch + EventBridge

CloudWatch alarms can trigger automation.

```text
Alarm

↓

EventBridge

↓

Lambda

↓

Slack Notification
```

Or:

```text
High Throttling

↓

Lambda

↓

Increase Capacity

↓

Notify Operations
```

---

# CloudWatch Logs

Application logs should complement CloudWatch metrics.

Example:

```text
Application

↓

Structured Logs

↓

CloudWatch Logs
```

Useful log entries include:

- Retry attempts
- Failed requests
- Latency spikes
- Conditional failures

---

# Production Monitoring Architecture

```text
                  Users

                     │

                     ▼

               Application

                     │

                     ▼

               DynamoDB Table

                     │

          CloudWatch Metrics

     ┌─────────────┼─────────────┐

     ▼             ▼             ▼

 Dashboard      Alarms        Logs

     │             │

     ▼             ▼

Operations     SNS / PagerDuty
```

---

# Important Metrics

| Metric | Why It Matters |
|---------|----------------|
| ConsumedReadCapacityUnits | Read workload |
| ConsumedWriteCapacityUnits | Write workload |
| ProvisionedReadCapacityUnits | Allocated read capacity |
| ProvisionedWriteCapacityUnits | Allocated write capacity |
| ReadThrottleEvents | Detect read bottlenecks |
| WriteThrottleEvents | Detect write bottlenecks |
| SuccessfulRequestLatency | Performance monitoring |
| SystemErrors | AWS service issues |
| UserErrors | Application problems |

---

# Monitoring Strategy

Production monitoring should follow four stages.

```text
Collect

↓

Visualize

↓

Alert

↓

Respond
```

Monitoring without alerting provides little operational value.

---

# Best Practices

- Create dashboards for every production table.
- Configure alarms for throttling events.
- Monitor latency trends continuously.
- Track capacity utilization.
- Integrate alarms with incident management systems.
- Review CloudWatch dashboards during deployments.
- Monitor GSIs separately from the base table.
- Monitor Streams consumers when using DynamoDB Streams.

---

# Common Mistakes

## Monitoring Only Capacity

Capacity alone does not indicate application health.

Also monitor:

- Latency
- Errors
- Throttling
- Auto Scaling activity

---

## Ignoring Small Throttling Events

Even occasional throttling may indicate:

- Poor partition key design
- Growing workload
- Capacity planning issues

Investigate before they become widespread.

---

## Missing GSI Metrics

Many applications fail because:

```text
Table

↓

Healthy

────────────

GSI

↓

Throttling
```

Monitor indexes independently.

---

## No Alerting

A dashboard nobody watches has limited value.

Every critical metric should have an associated alarm.

---

# Production Considerations

Enterprise monitoring typically includes:

```text
CloudWatch

+

CloudTrail

+

AWS Config

+

Security Hub

+

EventBridge

+

PagerDuty

+

Slack
```

This enables:

- Real-time visibility
- Automated incident response
- Operational dashboards
- Compliance reporting
- Performance optimization

---

# Interview Notes

A common interview question is:

> **What are the most important CloudWatch metrics for DynamoDB?**

The most important metrics include:

- ConsumedReadCapacityUnits
- ConsumedWriteCapacityUnits
- ReadThrottleEvents
- WriteThrottleEvents
- SuccessfulRequestLatency
- SystemErrors
- UserErrors

---

Another common question is:

> **Why monitor throttling if Auto Scaling is enabled?**

Auto Scaling is reactive. Temporary throttling can still occur before scaling completes. Monitoring helps identify traffic spikes, hot partitions, or incorrect scaling policies.

---

Another common question is:

> **How do CloudWatch and Auto Scaling work together?**

CloudWatch continuously collects capacity utilization metrics. Application Auto Scaling evaluates those metrics against target tracking policies and adjusts provisioned capacity accordingly.

---

Another common question is:

> **What should a production DynamoDB dashboard contain?**

At minimum:

- Capacity utilization
- Read and write throughput
- Latency
- Read and write throttling
- System and user errors
- Auto Scaling activity
- GSI metrics

---

# Key Takeaways

- CloudWatch is the primary monitoring service for DynamoDB.
- Capacity, latency, throttling, and error metrics are critical for production workloads.
- Dashboards provide operational visibility, while alarms enable proactive incident response.
- CloudWatch integrates directly with Auto Scaling and EventBridge for automation.
- Monitoring should include both tables and Global Secondary Indexes.
- Effective monitoring reduces downtime, improves performance, and enables data-driven capacity planning.