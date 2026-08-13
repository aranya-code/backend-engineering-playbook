# Log Groups, Log Streams & Logs Insights

> Learn how Amazon CloudWatch Logs stores, organizes, searches, and analyzes application logs. This chapter covers Log Groups, Log Streams, Log Events, retention policies, subscription filters, Logs Insights, and production logging practices using the AWS CLI.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand CloudWatch Logs architecture
- Manage Log Groups
- Manage Log Streams
- Search and filter logs
- Query logs using CloudWatch Logs Insights
- Configure retention policies
- Export log data
- Build production logging strategies

---

# Why CloudWatch Logs?

Metrics tell you **what happened**.

Logs tell you **why it happened**.

Example:

```text
Alarm

↓

High Error Rate

↓

CloudWatch Logs

↓

Root Cause Found
```

Logs are the primary source for troubleshooting production issues.

---

# CloudWatch Logs Architecture

```text
Application

↓

Log Group

↓

Log Stream

↓

Log Events

↓

Logs Insights
```

---

# Log Groups

A Log Group is the highest level of organization.

Examples:

```text
/aws/lambda/payment-api

/aws/ec2/backend

/aws/ecs/orders

/aws/rds/postgresql
```

Each application or AWS service typically has its own Log Group.

---

# Log Streams

Each Log Group contains one or more Log Streams.

```text
Payment API

│

├── Stream A

├── Stream B

└── Stream C
```

Each stream represents logs from a single source.

---

# Log Events

Every Log Stream contains Log Events.

```text
Timestamp

↓

Message

↓

Timestamp

↓

Message
```

Each event consists of:

- Timestamp
- Message

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

# Create a Log Stream

```bash
aws logs create-log-stream \
--log-group-name /backend/application \
--log-stream-name api-server-1
```

---

# Delete a Log Stream

```bash
aws logs delete-log-stream \
--log-group-name /backend/application \
--log-stream-name api-server-1
```

---

# View Recent Logs

```bash
aws logs tail \
/aws/lambda/payment-api \
--follow
```

Useful for real-time monitoring.

---

# Retrieve Log Events

```bash
aws logs get-log-events \
--log-group-name /backend/application \
--log-stream-name api-server-1
```

---

# Filter Log Events

```bash
aws logs filter-log-events \
--log-group-name /backend/application \
--filter-pattern ERROR
```

Returns only matching log events.

---

# Common Filter Patterns

Examples:

```text
ERROR
```

```text
Exception
```

```text
Timeout
```

```text
Database
```

You can also search structured JSON fields.

---

# CloudWatch Logs Insights

CloudWatch Logs Insights is AWS's log analytics engine.

It allows you to:

- Search logs
- Aggregate results
- Identify trends
- Investigate incidents

without exporting logs.

---

# Logs Insights Workflow

```text
Log Group

↓

Logs Insights

↓

Query

↓

Results
```

---

# Common Query Structure

Logs Insights queries follow this pattern:

```text
fields

↓

filter

↓

sort

↓

limit
```

---

# Example Query

```sql
fields @timestamp, @message

| sort @timestamp desc

| limit 20
```

Returns the latest 20 log entries.

---

# Filter Errors

```sql
fields @timestamp, @message

| filter @message like /ERROR/

| sort @timestamp desc
```

---

# Count Errors

```sql
fields @message

| filter @message like /ERROR/

| stats count()
```

Useful for incident analysis.

---

# Top Error Messages

```sql
fields @message

| stats count() by @message

| sort count desc
```

Helps identify recurring failures.

---

# Query Execution

Start a query:

```bash
aws logs start-query
```

Retrieve results:

```bash
aws logs get-query-results
```

---

# Log Retention

By default:

```text
Never Expire
```

Recommended retention:

| Environment | Retention |
|-------------|-----------|
| Development | 7–30 Days |
| Testing | 30 Days |
| Production | 90 Days |
| Compliance | 365+ Days |

---

# Configure Retention

```bash
aws logs put-retention-policy \
--log-group-name /backend/application \
--retention-in-days 30
```

---

# Export Logs

CloudWatch Logs can export data to Amazon S3.

Typical workflow:

```text
CloudWatch Logs

↓

Export Task

↓

Amazon S3

↓

Long-term Storage
```

---

# Subscription Filters

Subscription Filters stream logs in near real time.

Targets include:

- Lambda
- Kinesis Data Streams
- Kinesis Firehose

Example workflow:

```text
Application

↓

CloudWatch Logs

↓

Subscription Filter

↓

Lambda
```

---

# Metric Filters

Metric Filters convert log patterns into CloudWatch Metrics.

```text
Application Logs

↓

ERROR

↓

Metric

↓

Alarm
```

This enables alerting based on log content.

---

# Common Errors

## ResourceNotFoundException

Verify:

- Log Group
- Log Stream

---

## InvalidParameterException

Possible causes:

- Invalid filter pattern
- Invalid query
- Invalid log group

---

## AccessDeniedException

Verify IAM permissions:

- logs:GetLogEvents
- logs:FilterLogEvents
- logs:StartQuery
- logs:GetQueryResults

---

# Production Best Practices

- Use structured JSON logging.
- Configure retention policies.
- Separate applications into dedicated Log Groups.
- Query logs using Logs Insights instead of manual searching.
- Create Metric Filters for critical errors.
- Avoid logging sensitive information.
- Export logs to S3 for long-term retention when required.
- Monitor logging costs.

---

# Real-World Workflow

```text
Application Error

↓

CloudWatch Logs

↓

Logs Insights Query

↓

Root Cause Identified

↓

Fix Deployed

↓

Application Healthy
```

---

# Architecture Note

```text
Application
      │
      ▼
CloudWatch Logs
      │
      ├── Log Groups
      ├── Log Streams
      ├── Log Events
      ├── Metric Filters
      └── Logs Insights
              │
              ▼
Monitoring & Troubleshooting
```

---

# Interview Note

### Question

**What is the difference between a Log Group, Log Stream, and Logs Insights?**

### Answer

A **Log Group** is a logical container for related logs, typically representing an application or AWS service. A **Log Stream** is an individual sequence of log events within a Log Group, often representing a single EC2 instance, Lambda execution environment, or container. **CloudWatch Logs Insights** is the query engine used to search, filter, aggregate, and analyze log data across one or more Log Groups, making it a powerful tool for production troubleshooting.

---

# Key Takeaways

- Log Groups organize related logs.
- Log Streams separate logs from individual sources.
- Log Events consist of timestamps and messages.
- Logs Insights provides fast log analytics.
- Metric Filters convert logs into metrics.
- Subscription Filters stream logs to downstream services.
- Structured logging and appropriate retention policies are essential for production environments.