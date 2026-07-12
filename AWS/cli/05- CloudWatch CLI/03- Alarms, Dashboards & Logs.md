# Alarms, Dashboards & Logs

> Learn how to monitor AWS resources using CloudWatch Alarms, visualize operational data with Dashboards, and centralize application logs using CloudWatch Logs. This chapter covers alarm creation, notification workflows, dashboard management, log ingestion, metric filters, and production monitoring strategies.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand CloudWatch Alarms
- Configure metric thresholds
- Create Dashboards
- Understand CloudWatch Logs
- Configure SNS notifications
- Build production monitoring dashboards
- Monitor applications effectively

---

# Monitoring Architecture

CloudWatch monitoring typically follows this workflow.

```text
Application
      │
      ▼
Metrics
      │
      ▼
Alarm
      │
      ▼
SNS
      │
      ▼
Email / Slack / PagerDuty
```

Logs follow a separate workflow.

```text
Application

↓

CloudWatch Logs

↓

Logs Insights

↓

Troubleshooting
```

---

# What is a CloudWatch Alarm?

A CloudWatch Alarm continuously evaluates a metric.

When the metric crosses a configured threshold:

```text
Metric

↓

Threshold Exceeded

↓

Alarm

↓

Notification
```

Alarms automate operational responses.

---

# Alarm States

Every alarm has one of three states.

```text
OK

↓

ALARM

↓

INSUFFICIENT_DATA
```

---

## OK

The metric is within the configured threshold.

---

## ALARM

The metric exceeds the configured threshold.

Actions may include:

- SNS notification
- Auto Scaling
- EC2 recovery
- Lambda invocation

---

## INSUFFICIENT_DATA

CloudWatch has insufficient metric data to evaluate the alarm.

Usually occurs:

- Immediately after creation
- When metrics stop arriving

---

# List Existing Alarms

```bash
aws cloudwatch describe-alarms
```

Returns:

- Alarm Name
- State
- Metric
- Threshold

---

# Create a CPU Alarm

Example:

```bash
aws cloudwatch put-metric-alarm \
--alarm-name HighCPU \
--metric-name CPUUtilization \
--namespace AWS/EC2 \
--statistic Average \
--period 300 \
--threshold 80 \
--comparison-operator GreaterThanThreshold \
--evaluation-periods 2
```

This alarm triggers if average CPU exceeds **80%** for two consecutive evaluation periods.

---

# Alarm Evaluation

```text
CPU

↓

Average > 80%

↓

2 Evaluation Periods

↓

ALARM
```

CloudWatch evaluates alarms automatically.

---

# Delete an Alarm

```bash
aws cloudwatch delete-alarms \
--alarm-names HighCPU
```

---

# Alarm Actions

An alarm can trigger:

- SNS
- Auto Scaling
- Lambda
- EC2 Recovery
- Systems Manager Automation

Example:

```text
CPU High

↓

Alarm

↓

SNS

↓

Email Notification
```

---

# SNS Integration

Typical workflow:

```text
CloudWatch Alarm

↓

SNS Topic

↓

Subscribers

↓

Email

Slack

SMS

Lambda
```

SNS is the most common notification target.

---

# Composite Alarms

Instead of monitoring one metric:

```text
CPU

OR

Memory
```

Combine multiple alarms.

Example:

```text
CPU Alarm

AND

Memory Alarm

↓

Composite Alarm
```

Reduces alert noise.

---

# What is a Dashboard?

A Dashboard displays multiple metrics in one place.

Example:

```text
Dashboard

│

├── CPU

├── Memory

├── Network

├── Requests

└── Errors
```

Dashboards provide operational visibility.

---

# List Dashboards

```bash
aws cloudwatch list-dashboards
```

---

# Create a Dashboard

```bash
aws cloudwatch put-dashboard \
--dashboard-name BackendDashboard \
--dashboard-body file://dashboard.json
```

Dashboard definitions are JSON documents.

---

# Delete a Dashboard

```bash
aws cloudwatch delete-dashboards \
--dashboard-names BackendDashboard
```

---

# Dashboard Widgets

Supported widgets include:

- Line Charts
- Stacked Area Charts
- Number Widgets
- Gauge Widgets
- Text Widgets
- Alarm Widgets

A single dashboard can contain multiple widget types.

---

# Production Dashboard Example

```text
Backend Dashboard

│

├── CPU Utilization

├── Memory Usage

├── Request Rate

├── Error Rate

├── Latency

├── Active Users

└── Alarm Status
```

Operations teams monitor dashboards continuously.

---

# What is CloudWatch Logs?

CloudWatch Logs centralizes application logs.

Common sources:

- EC2
- Lambda
- ECS
- EKS
- API Gateway
- VPC Flow Logs
- CloudTrail

---

# Log Architecture

```text
Application

↓

Log Group

↓

Log Stream

↓

Log Events
```

Everything in CloudWatch Logs follows this hierarchy.

---

# Log Groups

A Log Group represents a collection of related logs.

Examples:

```text
/aws/lambda/payment-api

/aws/ec2/backend

/aws/rds/postgres

/aws/apigateway/orders
```

---

# Log Streams

Each Log Group contains multiple Log Streams.

Example:

```text
Log Group

│

├── Stream 1

├── Stream 2

└── Stream 3
```

Each stream represents one source.

---

# List Log Groups

```bash
aws logs describe-log-groups
```

---

# List Log Streams

```bash
aws logs describe-log-streams \
--log-group-name /aws/lambda/payment-api
```

---

# View Recent Logs

```bash
aws logs tail \
/aws/lambda/payment-api \
--follow
```

Useful for real-time troubleshooting.

---

# Create a Log Group

```bash
aws logs create-log-group \
--log-group-name /backend/application
```

---

# Delete a Log Group

```bash
aws logs delete-log-group \
--log-group-name /backend/application
```

---

# Log Retention

By default:

```text
Logs

↓

Never Expire
```

Recommended:

Configure retention policies.

Example:

```text
7 Days

30 Days

90 Days

365 Days
```

Depending on compliance requirements.

---

# Set Log Retention

```bash
aws logs put-retention-policy \
--log-group-name /backend/application \
--retention-in-days 30
```

---

# Metric Filters

Metric Filters convert log patterns into metrics.

Example:

```text
Application Logs

↓

ERROR

↓

Metric

↓

Alarm
```

Useful for monitoring application failures.

---

# Create a Metric Filter

```bash
aws logs put-metric-filter
```

Metric Filters enable log-based alerting.

---

# Common Errors

## ResourceAlreadyExistsException

The dashboard, alarm, or log group already exists.

Use another name or update the existing resource.

---

## ResourceNotFoundException

Verify:

- Alarm Name
- Dashboard Name
- Log Group
- Log Stream

---

## InvalidParameterException

Possible causes:

- Invalid JSON
- Invalid dashboard body
- Invalid threshold
- Invalid metric

---

# Production Best Practices

- Monitor infrastructure and application metrics.
- Use SNS for alert delivery.
- Keep alarm thresholds meaningful.
- Avoid excessive alerting.
- Build service-specific dashboards.
- Configure log retention policies.
- Use Metric Filters for application errors.
- Review dashboards regularly.

---

# Real-World Workflow

Production monitoring.

```text
Application

↓

CloudWatch Metrics

↓

Alarm

↓

SNS

↓

Engineer

↓

Investigate Logs

↓

Resolve Incident
```

---

# Architecture Note

```text
AWS Resources
      │
      ▼
CloudWatch
      │
      ├── Metrics
      ├── Alarms
      ├── Dashboards
      └── Logs
              │
              ▼
      Notifications & Investigation
```

CloudWatch provides both proactive monitoring through alarms and reactive troubleshooting through logs.

---

# Interview Note

### Question

**What is the difference between a CloudWatch Metric, Alarm, Dashboard, and Log Group?**

### Answer

A **Metric** is a time-series measurement such as CPU utilization or request count. An **Alarm** continuously evaluates one or more metrics and triggers actions when thresholds are breached. A **Dashboard** is a visual interface that displays multiple metrics, alarms, and widgets in one place for operational monitoring. A **Log Group** is a container for related log streams that store application and service logs, enabling centralized troubleshooting and analysis.

---

# Key Takeaways

- CloudWatch Alarms automate monitoring and incident response.
- Dashboards provide a centralized operational view.
- CloudWatch Logs centralizes application and infrastructure logs.
- Log Groups organize logs, while Log Streams separate individual sources.
- SNS is the most common notification target for alarms.
- Metric Filters convert log patterns into CloudWatch metrics.
- Effective monitoring combines metrics, alarms, dashboards, and logs.