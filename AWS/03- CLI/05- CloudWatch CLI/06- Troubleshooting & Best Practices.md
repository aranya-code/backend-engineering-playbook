# Troubleshooting & Best Practices

> Learn how to troubleshoot common Amazon CloudWatch issues using the AWS CLI and follow production-ready monitoring and observability practices. This chapter covers metrics, alarms, logs, EventBridge, dashboards, permissions, and operational best practices used by experienced Cloud Engineers and SREs.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Troubleshoot CloudWatch metrics
- Debug CloudWatch Alarms
- Diagnose missing logs
- Troubleshoot EventBridge Rules
- Investigate monitoring failures
- Build production monitoring strategies
- Apply CloudWatch best practices

---

# Why Troubleshooting Matters

CloudWatch is responsible for monitoring production infrastructure.

When monitoring fails, engineers lose visibility into:

- Application health
- Infrastructure performance
- Errors
- Security events
- Operational issues

A systematic troubleshooting approach ensures issues are identified quickly.

---

# CloudWatch Troubleshooting Workflow

Whenever monitoring appears incorrect:

```text
Verify AWS Account
        │
        ▼
Verify Region
        │
        ▼
Verify Metric
        │
        ▼
Verify Alarm
        │
        ▼
Verify Logs
        │
        ▼
Verify EventBridge Rule
        │
        ▼
Resolve Issue
```

---

# Verify Current Identity

Always verify your AWS account.

```bash
aws sts get-caller-identity
```

Many monitoring problems occur because engineers are working in the wrong AWS account.

---

# Verify Region

```bash
aws configure get region
```

CloudWatch resources are regional.

Checking the wrong Region is a common mistake.

---

# Verify Available Metrics

```bash
aws cloudwatch list-metrics
```

Confirm that:

- Namespace exists
- Metric exists
- Dimensions are correct

---

# Metric Not Appearing

Possible causes:

- Wrong namespace
- Wrong dimensions
- No data published
- Incorrect Region
- Application stopped publishing metrics

Example:

```text
Application

↓

Metric Not Published

↓

CloudWatch Empty
```

---

# No Metric Data Returned

Example:

```bash
aws cloudwatch get-metric-statistics
```

Returns:

```text
Datapoints: []
```

Possible causes:

- Incorrect time range
- Wrong period
- Missing dimensions
- Metric retention expired

---

# Alarm Never Triggers

Possible causes:

- Threshold too high
- Wrong statistic
- Wrong evaluation period
- Wrong metric
- Missing data

Review:

```bash
aws cloudwatch describe-alarms
```

---

# Alarm Always in INSUFFICIENT_DATA

Example:

```text
INSUFFICIENT_DATA
```

Possible causes:

- No metrics arriving
- Newly created alarm
- Wrong namespace
- Wrong dimensions

Verify the underlying metric first.

---

# Alarm Not Sending Notifications

Verify:

- SNS Topic
- Alarm Actions
- SNS Subscription
- Email confirmation

CloudWatch may trigger the alarm successfully while the notification fails.

---

# Dashboard Missing Metrics

Verify:

- Metric namespace
- Region
- Widget configuration
- Dashboard JSON

List dashboards:

```bash
aws cloudwatch list-dashboards
```

---

# Logs Not Appearing

Check Log Groups.

```bash
aws logs describe-log-groups
```

Then:

```bash
aws logs describe-log-streams \
--log-group-name /aws/lambda/payment-api
```

Common causes:

- IAM permission issues
- Application not writing logs
- Wrong Log Group
- Wrong Region

---

# Unable to Tail Logs

```bash
aws logs tail \
/aws/lambda/payment-api \
--follow
```

If no logs appear:

Verify:

- Lambda executed
- EC2 agent running
- ECS logging configured
- IAM Role permissions

---

# EventBridge Rule Not Triggering

Verify:

```bash
aws events list-rules
```

Then:

```bash
aws events describe-rule \
--name EC2StateChange
```

Review:

- Event Pattern
- Event Bus
- Target ARN

---

# Event Target Not Invoked

Possible causes:

- Missing IAM permissions
- Invalid ARN
- Disabled Rule
- Target removed

Verify:

```bash
aws events list-targets-by-rule \
--rule EC2StateChange
```

---

# SNS Notification Failures

Check:

- Topic exists
- Subscription confirmed
- Correct endpoint
- IAM permissions

Typical workflow:

```text
Alarm

↓

SNS

↓

Email

↓

Engineer
```

Failures often occur after the SNS step.

---

# Metric Filter Not Producing Metrics

Verify:

- Log Group
- Filter Pattern
- Metric Namespace
- Metric Name

Review the filter carefully.

---

# CloudWatch Agent Problems

For EC2 custom metrics:

Verify:

- CloudWatch Agent installed
- Agent running
- Configuration file
- IAM Role

Common command:

```bash
sudo systemctl status amazon-cloudwatch-agent
```

---

# Missing Lambda Logs

Verify:

- Lambda executed
- Execution Role permissions
- Log Group exists

Required IAM permission:

```text
logs:CreateLogGroup

logs:CreateLogStream

logs:PutLogEvents
```

---

# Common Errors

## ResourceNotFoundException

Verify:

- Alarm
- Dashboard
- Log Group
- Event Rule
- Namespace

---

## AccessDeniedException

Possible causes:

- Missing IAM permission
- SCP restriction
- Wrong Role

Verify using:

```bash
aws sts get-caller-identity
```

---

## InvalidParameterException

Possible causes:

- Invalid namespace
- Invalid dimensions
- Invalid alarm configuration
- Invalid dashboard JSON

---

## ThrottlingException

Occurs when making too many API requests.

Solutions:

- Retry with exponential backoff
- Reduce polling frequency
- Batch requests

---

# Production Monitoring Checklist

Before deploying monitoring:

- □ Metrics available
- □ Alarms configured
- □ SNS notifications tested
- □ Dashboards reviewed
- □ Log retention configured
- □ EventBridge Rules tested
- □ CloudWatch Agent verified
- □ IAM permissions validated

---

# Production Best Practices

## Monitor Business Metrics

Infrastructure metrics are important.

Business metrics are equally valuable.

Examples:

- Orders per minute
- Payment failures
- Active users
- Login failures

---

## Avoid Alert Fatigue

Do not create alarms for every metric.

Alert only when:

- Action is required.
- The threshold is meaningful.
- Someone is responsible.

---

## Configure Log Retention

Avoid unlimited retention unless required.

Example:

```text
Development

↓

30 Days

Production

↓

90 Days

Compliance

↓

365 Days
```

---

## Use Dashboards

Every production system should expose:

- CPU
- Memory
- Requests
- Latency
- Errors
- Availability

One dashboard should provide a quick health overview.

---

## Monitor EventBridge

Track:

- Failed Invocations
- Dead Letter Queues
- Retry Attempts

Automation should be observable.

---

## Use Structured Logging

Instead of:

```text
Something failed
```

Prefer:

```json
{
  "request_id": "abc123",
  "user_id": 501,
  "service": "payment-api",
  "status": "failed",
  "error": "DatabaseTimeout"
}
```

Structured logs simplify querying and troubleshooting.

---

# Real-World Workflow

Production incident.

```text
Alarm Triggered

↓

SNS Notification

↓

Engineer Opens Dashboard

↓

Checks Metrics

↓

Reviews Logs

↓

Queries Logs Insights

↓

Identifies Root Cause

↓

Deploys Fix

↓

Alarm Clears
```

---

# Architecture Note

```text
Application
      │
      ▼
CloudWatch
      │
      ├── Metrics
      ├── Logs
      ├── Alarms
      ├── Dashboards
      └── EventBridge
              │
              ▼
Operations Team
              │
              ▼
Incident Response
```

CloudWatch is the operational visibility platform for AWS workloads.

---

# Interview Note

### Question

**How would you troubleshoot a CloudWatch Alarm that never triggers?**

### Answer

I would first verify that the underlying metric is being published and contains recent datapoints. Next, I would review the alarm configuration, including the namespace, dimensions, statistic, threshold, evaluation periods, and comparison operator. I would confirm that the metric values actually cross the configured threshold and ensure the alarm actions are correctly associated with an SNS topic or other target. Finally, I would review CloudWatch metrics and alarm history to verify evaluation behavior.

---

# Key Takeaways

- Always verify metrics before troubleshooting alarms.
- CloudWatch resources are regional.
- Dashboards depend on accurate metrics.
- Logs are essential for root cause analysis.
- EventBridge Rules require correct event patterns and targets.
- Structured logging improves troubleshooting efficiency.
- Effective monitoring combines metrics, logs, alarms, dashboards, and automation.
```