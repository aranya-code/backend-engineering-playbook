# Cheat Sheet & Interview Guide

> A practical reference for the most commonly used Amazon CloudWatch CLI commands, monitoring workflows, troubleshooting techniques, and interview preparation. This chapter serves as a day-to-day operational guide for Backend Engineers, DevOps Engineers, Cloud Engineers, Site Reliability Engineers (SREs), and AWS Solutions Architects.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Quickly recall frequently used CloudWatch CLI commands
- Monitor AWS infrastructure efficiently
- Troubleshoot CloudWatch issues
- Build production monitoring strategies
- Prepare for AWS certification and backend engineering interviews

---

# Why a Cheat Sheet?

CloudWatch is one of the most frequently used AWS services in production.

Rather than memorizing every command, engineers remember:

- Monitoring workflow
- Metrics
- Alarms
- Logs
- EventBridge automation
- Troubleshooting process

This chapter provides a practical operational reference.

---

# Command Syntax

CloudWatch Metrics:

```bash
aws cloudwatch <operation>
```

CloudWatch Logs:

```bash
aws logs <operation>
```

EventBridge:

```bash
aws events <operation>
```

---

# Metrics Commands

## List Metrics

```bash
aws cloudwatch list-metrics
```

---

## List Metrics by Namespace

```bash
aws cloudwatch list-metrics \
--namespace AWS/EC2
```

---

## Get Metric Statistics

```bash
aws cloudwatch get-metric-statistics
```

---

## Get Multiple Metrics

```bash
aws cloudwatch get-metric-data
```

---

## Publish Custom Metric

```bash
aws cloudwatch put-metric-data
```

---

# Alarm Commands

## List Alarms

```bash
aws cloudwatch describe-alarms
```

---

## Create Alarm

```bash
aws cloudwatch put-metric-alarm
```

---

## Delete Alarm

```bash
aws cloudwatch delete-alarms
```

---

## Alarm History

```bash
aws cloudwatch describe-alarm-history
```

---

# Dashboard Commands

## List Dashboards

```bash
aws cloudwatch list-dashboards
```

---

## Create or Update Dashboard

```bash
aws cloudwatch put-dashboard
```

---

## View Dashboard

```bash
aws cloudwatch get-dashboard
```

---

## Delete Dashboard

```bash
aws cloudwatch delete-dashboards
```

---

# CloudWatch Logs Commands

## List Log Groups

```bash
aws logs describe-log-groups
```

---

## List Log Streams

```bash
aws logs describe-log-streams
```

---

## Tail Logs

```bash
aws logs tail \
/aws/lambda/my-function \
--follow
```

---

## Filter Log Events

```bash
aws logs filter-log-events
```

---

## Create Log Group

```bash
aws logs create-log-group
```

---

## Delete Log Group

```bash
aws logs delete-log-group
```

---

## Configure Log Retention

```bash
aws logs put-retention-policy
```

---

## Create Metric Filter

```bash
aws logs put-metric-filter
```

---

# EventBridge Commands

## List Event Buses

```bash
aws events list-event-buses
```

---

## Create Event Bus

```bash
aws events create-event-bus
```

---

## List Rules

```bash
aws events list-rules
```

---

## Describe Rule

```bash
aws events describe-rule
```

---

## Create Rule

```bash
aws events put-rule
```

---

## Delete Rule

```bash
aws events delete-rule
```

---

## Add Targets

```bash
aws events put-targets
```

---

## List Targets

```bash
aws events list-targets-by-rule
```

---

## Publish Custom Event

```bash
aws events put-events
```

---

# Useful Global Options

| Option | Purpose |
|----------|----------|
| `--profile` | Use a named AWS profile |
| `--region` | Override default Region |
| `--output json` | JSON output |
| `--output table` | Table output |
| `--query` | Filter CLI output |
| `--debug` | Enable verbose debugging |
| `--no-cli-pager` | Disable CLI pager |

---

# Common CloudWatch Metrics

| Service | Common Metrics |
|----------|----------------|
| EC2 | CPUUtilization, NetworkIn, NetworkOut |
| Lambda | Invocations, Errors, Duration |
| ECS | CPUUtilization, MemoryUtilization |
| RDS | CPUUtilization, FreeStorageSpace |
| ALB | RequestCount, TargetResponseTime |
| DynamoDB | ReadCapacityUnits, WriteCapacityUnits |
| API Gateway | Count, Latency, 4XXError, 5XXError |

---

# Common Alarm States

| State | Meaning |
|--------|---------|
| `OK` | Metric is within threshold |
| `ALARM` | Threshold exceeded |
| `INSUFFICIENT_DATA` | Not enough data to evaluate |

---

# Common Log Structure

```text
Log Group
     │
     ├── Log Stream A
     ├── Log Stream B
     └── Log Stream C
```

---

# Common EventBridge Workflow

```text
AWS Service

↓

EventBridge

↓

Rule

↓

Target

↓

Automation
```

---

# Common Errors

| Error | Cause | Resolution |
|--------|-------|------------|
| ResourceNotFoundException | Missing Alarm, Dashboard or Log Group | Verify resource name |
| AccessDeniedException | Missing IAM permission | Review IAM Role or Policy |
| InvalidParameterException | Invalid namespace, dimensions or JSON | Validate parameters |
| ThrottlingException | Too many requests | Retry with exponential backoff |
| No Datapoints | Incorrect time range or dimensions | Verify metric configuration |

---

# Daily CloudWatch Checklist

Before deploying monitoring:

- Verify AWS account.
- Verify Region.
- Confirm metrics are published.
- Configure alarms.
- Test SNS notifications.
- Create dashboards.
- Configure log retention.
- Validate EventBridge Rules.
- Verify IAM permissions.
- Monitor CloudWatch costs.

---

# Interview Questions

## 1. What is Amazon CloudWatch?

**Answer**

Amazon CloudWatch is AWS's monitoring and observability platform that collects metrics, logs, events, and alarms for AWS resources and applications.

---

## 2. What is the difference between a Metric and a Log?

**Answer**

A metric is a numerical time-series measurement such as CPU utilization or latency, while a log is a detailed record of events generated by applications or infrastructure. Metrics indicate **what** is happening, while logs help explain **why** it happened.

---

## 3. What is a Namespace?

**Answer**

A namespace groups related CloudWatch metrics. Examples include `AWS/EC2`, `AWS/Lambda`, and custom namespaces such as `Backend/Application`.

---

## 4. What is a Dimension?

**Answer**

A dimension is a key-value pair that uniquely identifies a metric instance, such as `InstanceId=i-0123456789abcdef`.

---

## 5. What is a CloudWatch Alarm?

**Answer**

A CloudWatch Alarm continuously evaluates one or more metrics and performs actions such as sending SNS notifications or invoking Auto Scaling policies when thresholds are crossed.

---

## 6. What is CloudWatch Logs?

**Answer**

CloudWatch Logs is a centralized logging service that stores, searches, and analyzes application and infrastructure logs using Log Groups and Log Streams.

---

## 7. What is EventBridge?

**Answer**

Amazon EventBridge is an event routing service that receives events from AWS services, applications, and SaaS providers, then routes them to configured targets such as Lambda, SNS, or SQS.

---

## 8. How would you troubleshoot a CloudWatch Alarm that never triggers?

**Answer**

First verify that the underlying metric exists and contains recent datapoints. Then review the alarm configuration, including namespace, dimensions, statistic, threshold, evaluation periods, and comparison operator. Finally, verify alarm actions, SNS subscriptions, and IAM permissions.

---

## 9. Why should log retention be configured?

**Answer**

Without a retention policy, logs are retained indefinitely, increasing storage costs. Configuring an appropriate retention period helps control costs while satisfying operational and compliance requirements.

---

## 10. What is the difference between CloudWatch and EventBridge?

**Answer**

CloudWatch monitors metrics, logs, and alarms to observe system health. EventBridge routes events between services to automate workflows. CloudWatch focuses on monitoring, while EventBridge focuses on event-driven automation.

---

# Senior Engineer Tips

Experienced Cloud Engineers typically:

- Build dashboards for every production service.
- Monitor both infrastructure and business metrics.
- Configure actionable alarms instead of excessive alerts.
- Use structured JSON logging.
- Set log retention policies based on compliance requirements.
- Create custom metrics for critical business KPIs.
- Use EventBridge for automation instead of polling.
- Monitor alarm history regularly.
- Test alarm notifications periodically.
- Continuously optimize CloudWatch costs.

---

# Quick Reference

| Task | Command |
|------|---------|
| List Metrics | `aws cloudwatch list-metrics` |
| Get Metric Data | `aws cloudwatch get-metric-data` |
| Publish Metric | `aws cloudwatch put-metric-data` |
| List Alarms | `aws cloudwatch describe-alarms` |
| Create Alarm | `aws cloudwatch put-metric-alarm` |
| List Dashboards | `aws cloudwatch list-dashboards` |
| List Log Groups | `aws logs describe-log-groups` |
| Tail Logs | `aws logs tail` |
| Create Event Rule | `aws events put-rule` |
| Publish Event | `aws events put-events` |

---

# Final Thoughts

Amazon CloudWatch is the operational backbone of AWS environments. Mastering CloudWatch enables engineers to monitor infrastructure, analyze application behavior, automate operational responses, and rapidly troubleshoot production issues. Together with EventBridge, SNS, and CloudWatch Logs, it provides a complete observability and automation platform for modern cloud-native applications.

---
