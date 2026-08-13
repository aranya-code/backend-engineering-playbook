# CloudWatch Logs

## Overview

While **CloudWatch Metrics** tell you **what is happening**, **CloudWatch Logs** tell you **why it is happening**.

Amazon API Gateway can send execution details, request information, integration responses, and errors to **Amazon CloudWatch Logs**, making it easier to debug production issues and analyze API behavior.

CloudWatch Logs help developers:

- Debug failed API requests
- Troubleshoot backend integrations
- Analyze request flow
- Monitor API execution
- Audit production issues
- Investigate latency problems

Logs are one of the most important tools for diagnosing issues in production environments.

---

# Why CloudWatch Logs?

Suppose an API returns:

```http
500 Internal Server Error
```

Metrics only tell us:

```text
5XX Error Count = 1
```

But they don't explain:

- Why did it fail?
- Which Lambda failed?
- What request was sent?
- Which integration timed out?

CloudWatch Logs answer these questions.

---

# Architecture

```text
               Client

                  │

                  ▼

          Amazon API Gateway

                  │

         Execution Logging

                  │

                  ▼

       Amazon CloudWatch Logs

                  │

     ┌────────────┴────────────┐

     ▼                         ▼

 Troubleshooting         Log Insights
```

---

# Logging Flow

```text
Client Request

↓

API Gateway

↓

Execution Logs

↓

CloudWatch Logs

↓

Developer
```

Every request can generate log entries.

---

# Types of Logs

API Gateway supports two primary logging types.

| Log Type | Purpose |
|----------|----------|
| Execution Logs | Internal API execution details |
| Access Logs | Information about client requests |

This chapter focuses on **Execution Logs**.

Access Logs are covered separately.

---

# Execution Logs

Execution Logs contain information about:

- Incoming requests
- Request validation
- Authorization
- Integration requests
- Integration responses
- Errors
- Latency
- Backend responses

These logs are automatically generated when execution logging is enabled.

---

# Log Group

Logs are stored inside a CloudWatch Log Group.

Example:

```text
API-Gateway-Execution-Logs_

abc123

/

prod
```

Each API stage has its own log stream.

---

# Log Streams

Within a Log Group:

```text
API Execution Logs

│

├── Stream 1

├── Stream 2

└── Stream 3
```

Multiple log streams improve scalability.

---

# Request Logging

Example:

```http
GET /orders/100
```

Execution Log:

```text
Method Request

GET

/orders/100
```

Developers can verify incoming requests.

---

# Request Parameters

Execution Logs record:

- Path Parameters
- Query Parameters
- Headers

Example:

```http
GET /products?page=2
```

Logs show:

```text
page = 2
```

---

# Request Validation Logs

Suppose validation fails.

Client:

```json
{}
```

Expected:

```json
{
    "username":"john"
}
```

Execution Log:

```text
Request Validation Failed
```

The backend is never invoked.

---

# Authorization Logs

Execution Logs record authorization events.

Example:

```text
JWT Validated

↓

Access Granted
```

Or:

```text
JWT Invalid

↓

403 Forbidden
```

Useful for debugging authentication problems.

---

# Integration Request Logs

API Gateway forwards the request.

```text
API Gateway

↓

Lambda

↓

Payload Sent
```

Execution Logs capture the transformed request.

---

# Integration Response Logs

Backend returns:

```json
{
    "status":"SUCCESS"
}
```

Execution Logs show:

```text
Integration Response

200 OK
```

Useful when debugging Mapping Templates.

---

# Error Logging

Backend error:

```http
500 Internal Server Error
```

Execution Log:

```text
Execution failed

Lambda timeout

29 seconds
```

Developers can quickly identify failures.

---

# Latency Logging

Logs contain timing information.

Example:

```text
Method completed

Latency

350 ms
```

Combined with CloudWatch Metrics, this helps identify performance bottlenecks.

---

# Log Levels

API Gateway supports multiple log levels.

| Level | Description |
|--------|-------------|
| ERROR | Log only errors |
| INFO | Log detailed execution information |

Production systems commonly use:

```text
ERROR
```

Development environments often use:

```text
INFO
```

---

# Data Tracing

API Gateway supports **Data Tracing**.

When enabled:

```text
Request Body

↓

Response Body

↓

CloudWatch Logs
```

This provides complete request and response visibility.

> **Warning:** Data Tracing may log sensitive information and should be used carefully in production.

---

# Log Retention

CloudWatch Logs support configurable retention.

Examples:

```text
7 Days

30 Days

90 Days

1 Year

Forever
```

Choose retention based on:

- Compliance
- Cost
- Operational needs

---

# Searching Logs

CloudWatch allows searching logs.

Example:

```text
ERROR
```

or

```text
RequestId

12345
```

Useful for investigating production incidents.

---

# CloudWatch Logs Insights

CloudWatch Logs Insights enables powerful log analysis.

Example queries:

- Count errors
- Find slow requests
- Filter by HTTP status
- Search Request IDs
- Analyze latency trends

This eliminates manual log searching.

---

# Correlating Logs

Logs can be correlated with:

```text
CloudWatch Metrics

↓

CloudWatch Logs

↓

AWS X-Ray

↓

Lambda Logs
```

This provides complete end-to-end observability.

---

# Common Issues Found Using Logs

Execution Logs help diagnose:

- Lambda timeouts
- Mapping template errors
- Authorization failures
- Missing permissions
- Invalid payloads
- Backend connection failures
- Integration timeouts

---

# Real-World Example

A customer reports:

```http
502 Bad Gateway
```

Execution Logs show:

```text
Lambda Timeout

30 Seconds
```

The issue is quickly identified without modifying application code.

---

# Best Practices

- Enable Execution Logging for production APIs.
- Use INFO logging in development environments.
- Limit production logging to ERROR unless detailed debugging is required.
- Configure appropriate log retention periods.
- Never log passwords, API keys, or sensitive customer data.
- Use CloudWatch Logs Insights for troubleshooting.
- Correlate logs with metrics and X-Ray traces.

---

# Common Interview Questions

### What is the difference between CloudWatch Metrics and CloudWatch Logs?

Metrics provide numerical performance data such as latency and request count.

Logs provide detailed execution information explaining why requests succeeded or failed.

---

### What are Execution Logs?

Execution Logs record detailed API Gateway processing information, including request validation, authorization, integration requests, responses, and errors.

---

### What is Data Tracing?

Data Tracing records request and response payloads in CloudWatch Logs for debugging purposes.

---

### Should Data Tracing always be enabled in production?

No.

It may expose sensitive information and increase logging costs. It should only be enabled when necessary.

---

### What log levels does API Gateway support?

- ERROR
- INFO

INFO provides detailed execution information, while ERROR logs only failures.

---

# Key Takeaways

- CloudWatch Logs provide detailed execution information for Amazon API Gateway requests.
- Execution Logs capture request processing, authorization, integrations, responses, errors, and latency.
- CloudWatch Logs complement CloudWatch Metrics by explaining why issues occur.
- Data Tracing can capture request and response payloads but should be used carefully in production.
- Combining CloudWatch Logs, Metrics, and AWS X-Ray provides comprehensive observability for API Gateway applications.