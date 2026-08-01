# Access Logs

## Overview

Access Logs provide a high-level record of every request processed by Amazon API Gateway. Unlike **Execution Logs**, which focus on the internal execution of the API, Access Logs capture information about the incoming request and the final response in a customizable format.

Access Logs help answer questions such as:

- Who called the API?
- Which endpoint was accessed?
- When was the request made?
- What HTTP status code was returned?
- How long did the request take?
- Which IP address made the request?

These logs are commonly used for:

- API auditing
- Security analysis
- Traffic analysis
- Troubleshooting
- Compliance
- Operational monitoring

Unlike Execution Logs, Access Logs are usually enabled in production because they have lower overhead and contain concise request information.

---

# Why Access Logs?

Suppose a customer reports:

```text
"I received a 403 error yesterday."
```

Without Access Logs:

```text
No Request History
```

With Access Logs:

```text
Timestamp

↓

Client IP

↓

GET /orders

↓

403 Forbidden

↓

Latency
```

The request can be investigated quickly.

---

# Architecture

```text
               Client

                  │

                  ▼

          Amazon API Gateway

                  │

          Generate Access Log

                  │

                  ▼

      Amazon CloudWatch Logs
```

Access Logs are generated after each request is processed.

---

# Access Log Flow

```text
Client Request

↓

API Gateway

↓

Request Processed

↓

Access Log Generated

↓

CloudWatch Logs
```

One access log entry is generated per request.

---

# Access Logs vs Execution Logs

| Access Logs | Execution Logs |
|--------------|----------------|
| High-level request summary | Detailed execution details |
| Production monitoring | Debugging |
| Low overhead | More verbose |
| One entry per request | Multiple entries per request |
| Customizable format | AWS-generated format |

A production system typically enables both, but with different log levels.

---

# What Information Can Be Logged?

Common fields include:

- Request ID
- API ID
- Stage
- HTTP Method
- Resource Path
- Status Code
- Client IP
- User Agent
- Response Length
- Request Time
- Latency
- Integration Latency

---

# Request ID

Each request receives a unique identifier.

Example:

```text
Request ID

↓

7c7d7f25-1234
```

Useful for tracing a request across multiple systems.

---

# Client IP Address

Example:

```text
203.0.113.25
```

Useful for:

- Security investigations
- Geographic analysis
- Detecting suspicious activity

---

# HTTP Method

Example:

```text
GET

POST

PUT

DELETE
```

Allows monitoring of API usage patterns.

---

# Resource Path

Example:

```text
/orders

/products/100

/users/profile
```

Shows which endpoints receive the most traffic.

---

# HTTP Status Code

Example:

```text
200 OK

404 Not Found

500 Internal Server Error
```

Useful for identifying:

- Failed requests
- Client errors
- Backend failures

---

# Response Time

Access Logs can include latency.

Example:

```text
245 ms
```

Useful for identifying slow APIs.

---

# User Agent

Example:

```text
Mozilla/5.0

Chrome

PostmanRuntime

curl
```

Allows teams to identify client applications.

---

# Access Log Format

API Gateway lets you define your own log format.

Example:

```text
RequestId

IP Address

HTTP Method

Resource

Status Code

Latency
```

You choose exactly what information to record.

---

# JSON Log Format

A common production format is JSON.

Example:

```json
{
    "requestId":"12345",
    "ip":"203.0.113.25",
    "method":"GET",
    "path":"/orders",
    "status":200,
    "latency":150
}
```

JSON logs are easier to search and analyze.

---

# Common Context Variables

API Gateway exposes variables using `$context`.

Examples:

```text
$context.requestId

$context.httpMethod

$context.resourcePath

$context.status

$context.identity.sourceIp

$context.responseLatency
```

These variables can be included in the log format.

---

# Sample Access Log

```json
{
    "requestId":"abc123",
    "ip":"203.0.113.25",
    "requestTime":"01/Aug/2026:10:15:30",
    "httpMethod":"GET",
    "resourcePath":"/products",
    "status":200,
    "responseLength":1250,
    "latency":85
}
```

This provides a concise summary of the request.

---

# CloudWatch Integration

Access Logs are sent to:

```text
Amazon CloudWatch Logs
```

Where they can be:

- Searched
- Filtered
- Exported
- Visualized

---

# CloudWatch Logs Insights

Example analyses:

- Top endpoints
- Slowest APIs
- Most common status codes
- Requests by IP
- Error trends
- Traffic patterns

---

# Security Monitoring

Access Logs help detect:

```text
Repeated 401 Errors

Repeated 403 Errors

Large Request Volumes

Unknown User Agents

Suspicious IP Addresses
```

These are often indicators of attacks or misuse.

---

# Compliance

Many organizations retain Access Logs for:

- SOC 2
- PCI DSS
- HIPAA
- ISO 27001

Logs provide an audit trail of API usage.

---

# Access Logs vs CloudTrail

| Access Logs | CloudTrail |
|--------------|------------|
| API Requests | AWS Management Events |
| Client Activity | AWS Account Activity |
| API Consumers | AWS Administrators |
| Runtime Requests | Configuration Changes |

Both serve different purposes.

---

# Real-World Example

An online shopping platform notices an increase in failed checkout requests.

Access Logs show:

```text
POST /checkout

↓

500 Errors

↓

Latency Increased

↓

Source IP Analysis
```

The operations team quickly identifies a backend deployment issue.

---

# Best Practices

- Enable Access Logs for all production APIs.
- Use JSON log format for easier parsing.
- Include Request ID in every log entry.
- Log latency and HTTP status codes.
- Configure log retention based on compliance requirements.
- Monitor logs using CloudWatch Logs Insights.
- Avoid logging sensitive customer information.
- Correlate Access Logs with Execution Logs and X-Ray traces.

---

# Common Interview Questions

### What are Access Logs in API Gateway?

Access Logs record a summary of every API request, including client information, request details, response status, and latency.

---

### How are Access Logs different from Execution Logs?

Access Logs provide high-level request summaries, while Execution Logs contain detailed information about API Gateway processing and backend integrations.

---

### Where are Access Logs stored?

They are stored in **Amazon CloudWatch Logs**.

---

### Why is JSON recommended for Access Logs?

JSON is structured, machine-readable, and integrates well with log analysis tools such as CloudWatch Logs Insights, Elasticsearch, and Splunk.

---

### What is the purpose of `$context` variables?

`$context` variables allow you to customize Access Log entries by including request metadata such as Request ID, IP address, HTTP method, latency, and status code.

---

# Key Takeaways

- Access Logs provide a concise record of every API request processed by Amazon API Gateway.
- They capture information such as Request ID, client IP, HTTP method, resource path, status code, and latency.
- Access Logs are highly customizable using `$context` variables and are typically stored in Amazon CloudWatch Logs.
- JSON is the preferred format for production environments because it simplifies searching and analysis.
- Access Logs complement Execution Logs, CloudWatch Metrics, and AWS X-Ray to provide complete observability for production APIs.