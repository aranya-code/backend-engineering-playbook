# Lambda Integration Issues

## Overview

AWS Lambda is the most common backend integration for Amazon API Gateway.

Although API Gateway simplifies serverless application development, incorrect Lambda configurations can result in errors such as:

- 500 Internal Server Error
- 502 Bad Gateway
- 403 Forbidden
- 504 Gateway Timeout

This guide explains the most common Lambda integration problems, how to diagnose them, and how to resolve them.

---

# Integration Flow

```text
Client

↓

API Gateway

↓

Lambda Invocation

↓

Lambda Function

↓

Response

↓

API Gateway

↓

Client
```

Failures can occur during invocation, execution, or response processing.

---

# Common Integration Errors

| Error | Typical Cause |
|--------|---------------|
| 500 | Lambda execution error |
| 502 | Invalid Lambda response |
| 403 | Missing invoke permission |
| 504 | Lambda timeout |
| 429 | Lambda concurrency limit |
| 404 | Incorrect integration ARN |

---

# 500 Internal Server Error

## Example

```http
HTTP/1.1 500 Internal Server Error
```

---

## Common Causes

- Unhandled exception
- Runtime error
- Missing environment variable
- Database connection failure
- Dependency failure

---

## Example

```python
def handler(event, context):
    return 10 / 0
```

Produces:

```text
ZeroDivisionError
```

---

## Diagnose

Check:

```text
CloudWatch Logs

↓

Lambda Logs
```

---

## Solution

Handle exceptions properly.

Example:

```python
try:
    ...
except Exception as e:
    return {
        "statusCode":500,
        "body":str(e)
    }
```

---

# 502 Bad Gateway

## Example

```http
HTTP/1.1 502 Bad Gateway
```

---

## Most Common Cause

Lambda returned an invalid response.

Incorrect:

```json
{
    "name":"Laptop"
}
```

Correct:

```json
{
    "statusCode":200,
    "body":"{\"name\":\"Laptop\"}"
}
```

---

## Expected Proxy Response

```json
{
    "statusCode":200,
    "headers":{
        "Content-Type":"application/json"
    },
    "body":"{}"
}
```

---

## Diagnose

Verify:

- Lambda Output
- Proxy Integration
- CloudWatch Logs

---

## Solution

Always return the expected Lambda Proxy Integration format.

---

# 403 Forbidden

## Example

```http
HTTP/1.1 403 Forbidden
```

---

## Common Cause

API Gateway cannot invoke Lambda.

---

## Diagnose

Check:

```bash
aws lambda get-policy \
--function-name ProductAPI
```

---

## Solution

Grant invoke permission.

```bash
aws lambda add-permission \
--function-name ProductAPI \
--statement-id apigateway \
--action lambda:InvokeFunction \
--principal apigateway.amazonaws.com
```

---

# 404 Integration Not Found

## Common Causes

- Incorrect Lambda ARN
- Deleted Function
- Wrong Region
- Wrong Account

---

## Diagnose

Verify:

```bash
aws lambda list-functions
```

---

## Solution

Update the integration with the correct ARN.

---

# 504 Gateway Timeout

## Example

```http
HTTP/1.1 504 Gateway Timeout
```

---

## Common Causes

- Slow Database
- External API
- Infinite Loop
- Long Processing

---

## Diagnose

Review:

CloudWatch Metrics

```text
Duration

Timeouts
```

---

## Solution

Optimize:

- SQL Queries
- External Calls
- Lambda Logic

Use asynchronous processing for long-running tasks.

---

# Lambda Timeout

Example:

```text
Timeout

↓

3 Seconds
```

Function runs:

```text
8 Seconds
```

Result:

```text
Timeout
```

---

## Solution

Increase timeout if appropriate.

```text
Lambda

↓

Configuration

↓

General Configuration

↓

Timeout
```

Also optimize execution time.

---

# Concurrency Limit

## Example

```http
429 Too Many Requests
```

---

## Cause

Lambda concurrency exhausted.

---

## Diagnose

CloudWatch Metric:

```text
ConcurrentExecutions
```

---

## Solution

- Increase concurrency quota
- Configure Reserved Concurrency
- Reduce execution time

---

# Memory Exhausted

Example:

```text
Runtime exited with error:
signal: killed
```

---

## Cause

Lambda exceeded allocated memory.

---

## Diagnose

CloudWatch:

```text
Max Memory Used
```

---

## Solution

Increase memory allocation.

Example:

```text
512 MB

↓

1024 MB
```

Higher memory also increases CPU allocation.

---

# Environment Variable Missing

Example:

```python
DATABASE_URL
```

returns:

```text
None
```

---

## Diagnose

Check:

```text
Lambda

↓

Configuration

↓

Environment Variables
```

---

## Solution

Add missing variables.

Prefer:

- AWS Secrets Manager
- Parameter Store

for sensitive values.

---

# Dependency Errors

Example:

```text
ModuleNotFoundError
```

---

## Cause

Package not included in deployment.

---

## Solution

Verify deployment package.

For large dependencies:

- Lambda Layers
- Container Images

---

# VPC Connectivity Issues

Example:

Lambda cannot connect to:

- RDS
- Redis
- Internal Services

---

## Common Causes

- Security Groups
- NACL
- Missing NAT Gateway
- Incorrect Route Table

---

## Diagnose

Verify:

```text
Lambda

↓

VPC

↓

Subnets

↓

Security Groups
```

---

## Solution

Ensure:

- Correct Subnets
- Correct Security Groups
- Internet access if required

---

# Cold Starts

Symptoms:

- High latency
- First request slow

---

## Diagnose

CloudWatch:

```text
Init Duration
```

---

## Solution

- Provisioned Concurrency
- Smaller deployment package
- Reduce dependencies

---

# Large Deployment Package

Example:

```text
300 MB
```

---

## Problems

- Longer cold starts
- Longer deployments

---

## Solution

Use:

- Lambda Layers
- Container Images
- Remove unused libraries

---

# Integration ARN Incorrect

Example:

```text
Wrong Region

↓

Wrong Function

↓

Invocation Failed
```

---

## Diagnose

Verify:

```bash
aws lambda list-functions
```

---

## Solution

Update the integration URI.

---

# Response Mapping Issues

Symptoms:

- Empty Response
- Incorrect Headers
- Missing JSON

---

## Diagnose

Review:

- Integration Response
- Mapping Templates

---

## Solution

Use Lambda Proxy Integration unless transformation is required.

---

# Logging Strategy

Enable:

- API Gateway Execution Logs
- Lambda Logs
- X-Ray

Together they provide end-to-end visibility.

---

# Troubleshooting Workflow

```text
Client Error

↓

API Gateway Logs

↓

Lambda Logs

↓

CloudWatch Metrics

↓

X-Ray

↓

Fix

↓

Redeploy

↓

Retest
```

---

# Production Checklist

Verify:

- Lambda exists
- Correct ARN
- Invoke permission
- Timeout
- Memory
- Environment Variables
- IAM Role
- Security Groups
- CloudWatch Logs
- X-Ray
- Correct response format

---

# Common Interview Questions

### Why does API Gateway return 502 Bad Gateway with Lambda?

The most common reason is that the Lambda function returns a response that doesn't match the expected proxy integration format, or the function throws an unhandled exception before generating a valid response.

---

### Why is API Gateway unable to invoke Lambda?

Typically because the Lambda resource policy doesn't grant `apigateway.amazonaws.com` permission to invoke the function, or the integration ARN is incorrect.

---

### How would you troubleshoot Lambda timeouts?

Check CloudWatch Logs and Metrics, review the Lambda duration, identify slow database queries or external API calls, inspect X-Ray traces, and optimize the application before increasing the timeout.

---

### How can Lambda cold starts be reduced?

Reduce deployment package size, minimize dependencies, increase memory if appropriate, or enable Provisioned Concurrency for latency-sensitive workloads.

---

### Why is Lambda Proxy Integration generally recommended?

Proxy Integration forwards the complete HTTP request to Lambda and expects a standardized response format, reducing API Gateway configuration complexity and making backend applications easier to maintain.

---

# Key Takeaways

- Most Lambda integration issues involve permissions, invalid response formats, timeouts, or runtime exceptions.
- CloudWatch Logs and AWS X-Ray are the primary tools for diagnosing Lambda-related failures.
- Lambda Proxy Integration simplifies request handling but requires the function to return a correctly structured response.
- Proper IAM permissions, environment configuration, memory sizing, and timeout settings are critical for reliable integrations.
- Following a structured troubleshooting workflow helps quickly identify and resolve production issues involving API Gateway and Lambda.