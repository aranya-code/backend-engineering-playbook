# Common API Gateway Errors

## Overview

Even well-designed APIs encounter failures in production. Understanding **why API Gateway returns a particular error code** is one of the most valuable skills for backend engineers.

This guide explains the most common API Gateway errors, their root causes, how to diagnose them, and the steps required to resolve them.

Most production issues fall into one of these categories:

- Client Errors (4XX)
- Server Errors (5XX)
- Authentication Problems
- Authorization Failures
- Integration Errors
- Networking Problems
- Configuration Mistakes

---

# API Gateway Request Flow

```text
Client

↓

API Gateway

↓

Authentication

↓

Authorization

↓

Request Validation

↓

Integration

↓

Backend

↓

Response
```

An error can occur at any stage of the request lifecycle.

---

# Error Categories

| Category | Status Codes |
|----------|--------------|
| Client Errors | 400–499 |
| Server Errors | 500–599 |
| Integration Errors | 502, 503, 504 |
| Authentication | 401 |
| Authorization | 403 |
| Rate Limiting | 429 |

---

# 400 Bad Request

## Example

```http
HTTP/1.1 400 Bad Request
```

---

## Common Causes

- Invalid JSON
- Missing required fields
- Invalid query parameters
- Invalid path parameters
- Request validation failure

---

## Example

Invalid JSON:

```json
{
"name":"Laptop",
```

Missing closing brace.

---

## Diagnose

Check:

- Request Body
- Query Parameters
- Request Validator
- CloudWatch Logs

---

## Solution

Validate requests before sending them.

Use:

- JSON Schema
- Request Validation
- Client-side validation

---

# 401 Unauthorized

## Example

```http
HTTP/1.1 401 Unauthorized
```

---

## Common Causes

- Missing JWT
- Expired JWT
- Invalid JWT
- Invalid Cognito Token
- Invalid Authorization Header

---

## Diagnose

Check:

```http
Authorization

Bearer <token>
```

Verify:

- Token expiration
- Audience
- Issuer

---

## Solution

- Refresh JWT
- Login again
- Verify Cognito configuration
- Verify JWT Authorizer

---

# 403 Forbidden

## Example

```http
HTTP/1.1 403 Forbidden
```

---

## Common Causes

- Missing API Key
- Invalid IAM Policy
- Resource Policy Denied
- WAF Blocked Request
- Usage Plan Restriction

---

## Diagnose

Check:

- IAM Permissions
- Resource Policy
- WAF Logs
- API Key
- Usage Plan

---

## Solution

Grant required permissions.

Verify:

- IAM
- API Keys
- Usage Plans
- WAF Rules

---

# 404 Not Found

## Example

```http
HTTP/1.1 404 Not Found
```

---

## Common Causes

- Invalid Route
- Invalid Resource
- Wrong HTTP Method
- Incorrect Stage

---

## Example

Request:

```text
GET /product
```

Actual:

```text
/products
```

---

## Diagnose

Verify:

- Routes
- Resources
- Deployment
- Stage

---

## Solution

Correct:

- URL
- Route
- Stage

Redeploy API if necessary.

---

# 405 Method Not Allowed

## Example

```http
HTTP/1.1 405 Method Not Allowed
```

---

## Common Causes

Example:

```text
GET /products
```

supported

but

```text
DELETE /products
```

does not exist.

---

## Diagnose

Verify:

- Resource Methods
- HTTP Verb

---

## Solution

Create the missing method.

---

# 409 Conflict

## Example

```http
HTTP/1.1 409 Conflict
```

---

## Common Causes

- Duplicate Resource
- Duplicate API
- Existing Stage
- Existing Domain

---

## Example

Trying to create:

```text
/products
```

twice.

---

## Solution

Reuse the existing resource or delete it first.

---

# 413 Payload Too Large

## Example

```http
HTTP/1.1 413 Payload Too Large
```

---

## Common Causes

- Large Request Body
- Large File Upload

---

## Solution

Upload files to:

```text
Amazon S3
```

instead of API Gateway.

---

# 415 Unsupported Media Type

## Example

```http
HTTP/1.1 415 Unsupported Media Type
```

---

## Common Causes

Incorrect:

```http
Content-Type
```

header.

---

## Solution

Use:

```http
Content-Type: application/json
```

---

# 429 Too Many Requests

## Example

```http
HTTP/1.1 429 Too Many Requests
```

---

## Common Causes

- Rate Limit
- Burst Limit
- Usage Plan Quota

---

## Diagnose

Review:

- Usage Plan
- CloudWatch Metrics
- Throttling Settings

---

## Solution

Increase:

- Burst Limit
- Rate Limit
- Quota

or implement retries with exponential backoff.

---

# 500 Internal Server Error

## Example

```http
HTTP/1.1 500 Internal Server Error
```

---

## Common Causes

- Lambda Exception
- Backend Crash
- Integration Failure
- Invalid Mapping

---

## Diagnose

Check:

- Lambda Logs
- CloudWatch Logs
- X-Ray

---

## Solution

Fix backend application errors.

---

# 502 Bad Gateway

## Example

```http
HTTP/1.1 502 Bad Gateway
```

---

## Common Causes

- Invalid Lambda Response
- Backend Returned Invalid Response
- ALB Error
- ECS Service Failure

---

## Lambda Example

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

## Diagnose

Check:

- Lambda Output
- Integration Response
- CloudWatch Logs

---

## Solution

Return the expected API Gateway response format.

---

# 503 Service Unavailable

## Example

```http
HTTP/1.1 503 Service Unavailable
```

---

## Common Causes

- Backend Offline
- ECS Service Down
- ALB Unhealthy
- Maintenance

---

## Diagnose

Verify:

- Target Group
- ECS Tasks
- Lambda
- Backend Health

---

## Solution

Restore backend availability.

---

# 504 Gateway Timeout

## Example

```http
HTTP/1.1 504 Gateway Timeout
```

---

## Common Causes

- Lambda Timeout
- Slow Database
- Slow Backend
- Network Delay

---

## Diagnose

Review:

- Lambda Duration
- Integration Latency
- Database Queries

---

## Solution

Optimize:

- Backend Code
- Queries
- Cache
- Timeouts

---

# Missing Authentication Token

## Example

```json
{
"message":"Missing Authentication Token"
}
```

---

## Common Causes

- Wrong URL
- Wrong Stage
- Wrong Route
- Wrong HTTP Method

---

## Example

Incorrect:

```text
GET /items
```

Correct:

```text
GET /products
```

---

## Solution

Verify:

- URL
- Route
- Deployment
- Stage

This is one of the most common API Gateway errors.

---

# Invalid API Identifier

## Example

```json
{
"message":"Invalid API identifier"
}
```

---

## Common Causes

- Incorrect API ID
- Deleted API
- Wrong Region

---

## Solution

Verify:

```bash
aws apigateway get-rest-apis
```

---

# AccessDeniedException

## Example

```json
{
"message":"Access Denied"
}
```

---

## Common Causes

- IAM Policy
- Resource Policy
- Missing Permission
- SCP Restriction

---

## Diagnose

Review:

- IAM
- Organizations SCP
- Resource Policy

---

## Solution

Grant required permissions.

---

# Integration Timeout

Occurs when:

```text
API Gateway

↓

Backend

↓

Timeout
```

---

## Common Causes

- Database
- HTTP Service
- Lambda
- ECS

---

## Solution

Reduce backend latency.

Use:

- Redis
- Query Optimization
- Async Processing

---

# CORS Error

Browser example:

```text
Access-Control-Allow-Origin Missing
```

---

## Common Causes

- OPTIONS Missing
- CORS Disabled
- Missing Headers

---

## Solution

Enable:

- OPTIONS Method
- CORS
- Correct Response Headers

---

# Error Diagnosis Workflow

```text
Request

↓

Status Code?

↓

4XX

↓

Client

-------------------

5XX

↓

Backend

↓

CloudWatch

↓

X-Ray

↓

Fix
```

---

# Production Troubleshooting Checklist

When debugging production issues, verify:

- API deployed
- Correct stage
- Correct route
- Correct HTTP method
- Authentication configured
- Authorization configured
- Lambda permissions
- Integration configured
- CloudWatch Logs
- X-Ray traces
- Backend health
- Security Groups
- VPC configuration
- Usage Plans
- API Keys
- WAF rules

---

# Debugging Tools

Useful AWS services:

- Amazon CloudWatch Logs
- CloudWatch Metrics
- AWS X-Ray
- AWS WAF Logs
- AWS CloudTrail
- Amazon ECS Console
- Lambda Logs

---

# Common Interview Questions

### What causes a 502 Bad Gateway in API Gateway?

A 502 error usually indicates that the backend returned an invalid response. A common example is a Lambda function that doesn't return the expected proxy integration response format or an unavailable backend behind an Application Load Balancer.

---

### Why does API Gateway return 429 Too Many Requests?

This occurs when a client exceeds configured throttling limits or Usage Plan quotas. API Gateway protects backend services by rejecting excess requests.

---

### What does "Missing Authentication Token" usually mean?

Despite its name, this error often indicates that the requested route, stage, or HTTP method does not exist, rather than a missing authentication token.

---

### How would you troubleshoot a 504 Gateway Timeout?

Check CloudWatch metrics and logs, review Lambda execution duration or backend response times, inspect database performance, and use AWS X-Ray to identify where latency occurs.

---

### Which tools are most useful for troubleshooting API Gateway?

CloudWatch Logs, CloudWatch Metrics, AWS X-Ray, CloudTrail, WAF logs, and backend service logs (such as Lambda or ECS) provide the primary diagnostic information.

---

# Key Takeaways

- Most API Gateway failures can be categorized into client errors (4XX), server errors (5XX), authentication issues, authorization failures, or integration problems.
- CloudWatch Logs and AWS X-Ray are the primary tools for diagnosing production issues.
- Understanding common HTTP status codes helps quickly identify whether a problem originates from the client, API Gateway, or the backend service.
- Many issues, such as `429 Too Many Requests`, `502 Bad Gateway`, and `504 Gateway Timeout`, can be prevented through proper API design, monitoring, and backend optimization.
- A structured troubleshooting workflow significantly reduces mean time to resolution (MTTR) in production environments.