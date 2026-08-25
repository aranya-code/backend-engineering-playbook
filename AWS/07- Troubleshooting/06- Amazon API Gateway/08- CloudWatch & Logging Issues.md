# CloudWatch & Logging Issues

## Overview

Amazon API Gateway integrates closely with **Amazon CloudWatch**, making it the primary service for monitoring, troubleshooting, and auditing API requests.

When APIs fail in production, CloudWatch is usually the **first place engineers investigate**.

However, logging itself can be misconfigured, resulting in:

- Missing execution logs
- Missing access logs
- Missing Lambda logs
- Missing X-Ray traces
- No metrics
- Difficult production debugging

This guide explains the most common CloudWatch and logging issues encountered with API Gateway and how to resolve them.

---

# Logging Architecture

```text
Client

↓

API Gateway

↓

CloudWatch Logs

↓

Lambda

↓

CloudWatch Logs

↓

CloudWatch Metrics

↓

CloudWatch Alarms
```

Every layer should generate logs independently.

---

# Common Logging Problems

| Problem | Symptoms |
|----------|----------|
| No API Gateway Logs | Empty Log Groups |
| No Lambda Logs | Missing Lambda Output |
| No Access Logs | Cannot Audit Requests |
| Metrics Missing | No CloudWatch Graphs |
| X-Ray Missing | No Distributed Trace |
| Log Permissions Missing | Logging Disabled |

---

# No API Gateway Logs

## Symptoms

CloudWatch Log Group:

```text
Empty
```

or

No Log Group exists.

---

## Common Causes

- Execution logging disabled
- IAM role missing
- Wrong stage
- Logging level disabled

---

## Diagnose

Navigate:

```text
API Gateway

↓

Stages

↓

Logs/Tracing
```

Verify:

- Logging Enabled
- Log Level

---

## Solution

Enable:

- Execution Logging
- CloudWatch Logs

---

# CloudWatch Role Missing

## Symptoms

Logging enabled

↓

No logs generated

---

## Diagnose

Navigate:

```text
API Gateway

↓

Account Settings
```

Check:

```text
CloudWatch Role ARN
```

---

## Solution

Configure an IAM role with:

```text
AmazonAPIGatewayPushToCloudWatchLogs
```

permissions.

---

# Missing Lambda Logs

## Symptoms

API Gateway returns:

```http
500 Internal Server Error
```

Lambda Log Group:

```text
No Logs
```

---

## Common Causes

- Lambda never invoked
- IAM role missing
- Function crashed before logging

---

## Diagnose

Open:

```text
CloudWatch

↓

Log Groups

↓

/aws/lambda/function-name
```

---

## Solution

Verify:

- Lambda execution role
- Integration configuration
- Function invocation

---

# Access Logs Disabled

## Symptoms

Cannot determine:

- Client IP
- Response Code
- Request ID
- Latency

---

## Diagnose

Review:

```text
Stage

↓

Access Logging

↓

Disabled
```

---

## Solution

Enable Access Logs.

Recommended format:

```text
RequestId

Status

Latency

IP

Method

Path
```

---

# Execution Logs Disabled

## Symptoms

Cannot troubleshoot:

- Integration failures
- Authorization failures
- Mapping template errors

---

## Solution

Enable:

```text
Execution Logging

↓

INFO
```

Use `ERROR` if you only need failures.

---

# Log Level Too Low

Example

Configured:

```text
ERROR
```

Expected:

```text
INFO
```

---

## Symptoms

Missing successful requests.

---

## Solution

Increase log level.

Production recommendation:

```text
INFO
```

---

# No CloudWatch Metrics

## Symptoms

No graphs for:

- Latency
- Requests
- Errors

---

## Diagnose

Review:

```text
Stage

↓

Metrics

↓

Disabled
```

---

## Solution

Enable:

```text
Detailed CloudWatch Metrics
```

---

# Missing X-Ray Traces

## Symptoms

X-Ray Console:

```text
No Traces
```

---

## Common Causes

- Tracing disabled
- Lambda tracing disabled
- IAM permission missing

---

## Solution

Enable tracing for:

- API Gateway Stage
- Lambda Function

---

# CloudWatch Alarm Never Triggers

## Symptoms

High errors

↓

No alarm

---

## Diagnose

Review:

- Alarm Threshold
- Metric Namespace
- Evaluation Period

---

## Solution

Verify alarm configuration.

---

# Wrong Log Group

Example

Expected:

```text
API Gateway Logs
```

Viewing:

```text
Lambda Logs
```

---

## Solution

Verify the correct log group.

Examples:

```text
API Gateway

↓

API-Gateway-Execution-Logs
```

```text
Lambda

↓

/aws/lambda/function-name
```

---

# Logs Delayed

Symptoms

Recent requests not visible.

---

## Explanation

CloudWatch log delivery is generally near real-time but may take a short time to appear.

---

## Solution

Wait briefly and refresh the console before assuming logs are missing.

---

# Log Retention Too Short

Example

Retention:

```text
1 Day
```

Production requires:

```text
90 Days
```

---

## Solution

Configure appropriate retention.

Examples:

- 30 Days
- 90 Days
- 1 Year

depending on compliance requirements.

---

# Large Log Volume

Symptoms

High CloudWatch costs.

---

## Common Causes

- DEBUG logging
- Verbose application logs
- Logging entire request bodies

---

## Solution

Log:

- Request ID
- Status
- Errors
- Timing

Avoid logging sensitive data or excessively large payloads.

---

# Missing Request ID

Every request has:

```text
RequestId
```

---

## Importance

Used to correlate:

- API Gateway
- Lambda
- Backend
- X-Ray

---

## Recommendation

Include the Request ID in application logs.

---

# CloudWatch Insights

Use Logs Insights to search logs.

Example query:

```sql
fields @timestamp, @message

| sort @timestamp desc

| limit 20
```

Useful for:

- Recent errors
- Slow requests
- Exception analysis

---

# Correlating Logs

```text
Client

↓

Request ID

↓

API Gateway Logs

↓

Lambda Logs

↓

Database Logs
```

Use the same correlation ID across services.

---

# Logging Best Practices

Log:

- Request ID
- HTTP Method
- Resource Path
- Status Code
- Latency
- Error Message

Avoid logging:

- Passwords
- JWT Tokens
- API Keys
- Personally Identifiable Information (PII)

---

# Troubleshooting Workflow

```text
API Failure

↓

CloudWatch Metrics

↓

CloudWatch Logs

↓

Execution Logs

↓

Lambda Logs

↓

X-Ray

↓

Root Cause

↓

Fix
```

---

# Production Checklist

Verify:

- Execution logging enabled
- Access logging enabled
- CloudWatch role configured
- Log retention configured
- Metrics enabled
- X-Ray enabled
- Request IDs logged
- Alarms configured
- Sensitive data not logged
- CloudWatch Insights available

---

# Common Interview Questions

### What is the difference between Execution Logs and Access Logs?

**Execution Logs** contain internal API Gateway processing details, including authorization, request transformations, integration requests, and errors.

**Access Logs** provide a summary of each request, such as client IP, request ID, HTTP method, status code, and latency, making them useful for auditing and traffic analysis.

---

### Why might API Gateway fail to write logs to CloudWatch?

Common reasons include execution logging being disabled, the CloudWatch Logs IAM role not being configured, or insufficient IAM permissions for API Gateway to publish logs.

---

### Why should Request IDs be logged?

Request IDs allow engineers to trace a single request across API Gateway, Lambda, databases, and other backend services, making production debugging significantly easier.

---

### Why shouldn't DEBUG logging remain enabled in production?

Verbose logging increases CloudWatch costs, generates unnecessary noise, may impact performance, and increases the risk of exposing sensitive information.

---

### How do CloudWatch Logs Insights help during troubleshooting?

CloudWatch Logs Insights enables engineers to search, filter, and analyze large volumes of log data using queries, making it much faster to identify failures, exceptions, latency issues, and traffic patterns.

---

# Key Takeaways

- CloudWatch is the primary observability service for monitoring and troubleshooting Amazon API Gateway.
- Execution Logs, Access Logs, Metrics, and X-Ray each provide different perspectives on API behavior and should be enabled appropriately.
- Proper IAM configuration is required for API Gateway to publish logs to CloudWatch.
- Structured logging, correlation IDs, and sensible log retention policies improve operational visibility while controlling costs.
- Combining CloudWatch Metrics, Logs, Logs Insights, and X-Ray provides a comprehensive approach to diagnosing production issues.