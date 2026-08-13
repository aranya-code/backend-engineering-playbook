# 02- API Gateway Issues

# Overview

Amazon API Gateway is one of the most common services used to invoke AWS Lambda synchronously. While the integration is straightforward, production issues can occur due to incorrect configurations, malformed Lambda responses, authorization failures, throttling, timeouts, or deployment mistakes.

This chapter covers the most common API Gateway issues encountered with Lambda, explains why they happen, and provides systematic troubleshooting steps.

---

# Request Flow

Understanding the request flow helps isolate failures quickly.

```
Client

↓

CloudFront (Optional)

↓

API Gateway

↓

Lambda

↓

Database / External Service

↓

Lambda Response

↓

API Gateway Response

↓

Client
```

Always determine **which component is failing** before making changes.

---

# Common HTTP Status Codes

| Status Code | Meaning | Common Cause |
|-------------|---------|--------------|
| 400 | Bad Request | Invalid request payload |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | IAM or Authorizer denied access |
| 404 | Not Found | Incorrect resource or route |
| 429 | Too Many Requests | API throttling |
| 500 | Internal Server Error | Lambda runtime failure |
| 502 | Bad Gateway | Invalid Lambda response |
| 503 | Service Unavailable | Backend unavailable |
| 504 | Gateway Timeout | Lambda timeout |

---

# Error: 502 Bad Gateway

Example

```
502 Bad Gateway
```

This is one of the most common Lambda integration errors.

## Possible Causes

- Invalid Lambda response format
- Runtime exception
- Lambda crashed
- Incorrect proxy integration

Incorrect response

```json
{
  "message": "Success"
}
```

Correct response

```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json"
  },
  "body": "{\"message\":\"Success\"}"
}
```

## Investigation

Check:

- CloudWatch Logs
- Lambda exceptions
- API Gateway execution logs

---

# Error: 500 Internal Server Error

Example

```
Internal Server Error
```

## Possible Causes

- Unhandled exception
- Database failure
- External API unavailable
- Configuration error

## Investigation

```
CloudWatch Logs

↓

Exception

↓

Root Cause
```

Never assume API Gateway is responsible.

---

# Error: 504 Gateway Timeout

Example

```
504 Gateway Timeout
```

## Root Cause

Lambda exceeded its configured timeout or downstream dependencies were too slow.

Possible reasons

- Slow SQL query
- Third-party API latency
- Infinite loop
- Large file processing

## Resolution

- Optimize business logic
- Improve database performance
- Use asynchronous processing
- Increase timeout only if justified

---

# Error: 403 Forbidden

Example

```
Forbidden
```

## Possible Causes

- Missing IAM permission
- Resource policy restriction
- Lambda permission missing
- Custom authorizer denial

Verify

```
API Gateway

↓

IAM

↓

Lambda Permission

↓

Authorizer
```

---

# Error: 401 Unauthorized

Example

```
Unauthorized
```

Common causes

- Missing JWT token
- Expired token
- Invalid Cognito token
- Custom authorizer failure

Check

- Authorization header
- Token expiry
- JWT signature
- Authorizer logs

---

# Error: 404 Not Found

Example

```
Not Found
```

Possible causes

- Incorrect endpoint
- Wrong HTTP method
- Missing deployment
- Incorrect stage

Verify

```
API

↓

Stage

↓

Route

↓

Method
```

---

# Error: 429 Too Many Requests

Example

```
Too Many Requests
```

## Root Cause

API Gateway throttling.

```
Traffic Spike

↓

Rate Limit

↓

429
```

## Resolution

- Configure usage plans
- Increase quotas
- Enable caching
- Queue traffic using SQS where appropriate

---

# CORS Errors

Browser message

```
Blocked by CORS Policy
```

## Root Cause

Missing CORS headers.

Required headers

```
Access-Control-Allow-Origin

Access-Control-Allow-Headers

Access-Control-Allow-Methods
```

API Gateway must return these headers for browser clients.

---

# Lambda Permission Missing

Example

```
Execution failed due to configuration error
```

Root cause

Lambda does not allow API Gateway to invoke it.

Verify Lambda resource policy.

Required principal

```
apigateway.amazonaws.com
```

---

# Invalid Payload Format

Example

```
Could not parse request body
```

Possible causes

- Malformed JSON
- Wrong Content-Type
- Missing required fields

Validate incoming payload before processing.

---

# Binary Media Issues

Symptoms

- Corrupted images
- Invalid PDF downloads
- Garbled file responses

Common causes

- Incorrect Binary Media Types
- Base64 encoding missing
- Wrong Content-Type

---

# Large Request Payload

Example

```
413 Payload Too Large
```

API Gateway has payload size limits.

Better approach

```
Client

↓

Generate Pre-signed URL

↓

Upload Directly to S3

↓

Trigger Lambda
```

Avoid sending large files through API Gateway.

---

# Slow API Responses

Possible causes

- Cold starts
- Slow database
- External API
- Large payload
- Excessive logging

Use AWS X-Ray to identify latency.

---

# Stage Configuration Issues

Common mistakes

- Wrong stage URL
- Environment variables mismatch
- Old deployment
- Incorrect custom domain mapping

Always verify the deployed stage.

---

# API Deployment Issues

Symptoms

- API changes not visible
- Old endpoints still responding

Cause

API Gateway deployment not updated.

Solution

```
Modify API

↓

Deploy Stage

↓

Test
```

---

# Custom Domain Problems

Possible causes

- Invalid ACM certificate
- DNS misconfiguration
- Wrong base path mapping
- Expired certificate

Verify

- Route 53
- ACM
- API Gateway mapping

---

# CloudWatch Logs Disabled

Without execution logs, debugging becomes difficult.

Enable

```
API Gateway

↓

Stages

↓

Logs & Tracing

↓

Execution Logs
```

Use structured logging for production environments.

---

# API Gateway and Lambda Timeout Mismatch

API Gateway maximum integration timeout is lower than Lambda's maximum execution time.

Example

```
API Gateway

29 Seconds

↓

Lambda

5 Minutes
```

The client receives a timeout even if Lambda continues executing.

For long-running tasks, prefer asynchronous workflows.

---

# Best Practices

- Validate all request payloads.
- Return consistent HTTP responses.
- Enable CloudWatch execution logs.
- Use structured JSON responses.
- Configure CORS correctly.
- Use JWT or IAM authorization.
- Minimize Lambda cold starts.
- Avoid sending large files through API Gateway.
- Use X-Ray for latency analysis.
- Deploy APIs after every configuration change.

---

# Troubleshooting Checklist

- [ ] Verify API URL
- [ ] Check deployed stage
- [ ] Review CloudWatch Logs
- [ ] Validate Lambda response format
- [ ] Verify IAM permissions
- [ ] Check authorizer configuration
- [ ] Test payload format
- [ ] Confirm CORS headers
- [ ] Review throttling metrics
- [ ] Analyze X-Ray traces

---

# Senior Backend Engineering Perspective

When debugging API Gateway integrations, avoid assuming the gateway is at fault. Most failures originate in the Lambda function, IAM permissions, backend services, or request validation. Senior engineers systematically trace requests from the client through API Gateway, Lambda, and downstream services, using logs and distributed tracing to isolate the true source of the problem.

---

# Key Takeaways

- API Gateway issues commonly involve malformed Lambda responses, authorization failures, CORS misconfiguration, throttling, or timeout mismatches.
- CloudWatch Logs and AWS X-Ray are essential for diagnosing request failures.
- Correct HTTP status codes and consistent response formats improve reliability and client experience.
- Large uploads should bypass API Gateway using pre-signed S3 URLs.
- A structured troubleshooting approach leads to faster incident resolution and more resilient serverless APIs.