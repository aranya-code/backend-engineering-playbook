# 11 - SDK & CLI Troubleshooting

## Overview

Most production DynamoDB issues are not caused by the service itself—they originate in the application, SDK configuration, AWS CLI configuration, credentials, networking, or request construction.

Whether you're using:

- AWS CLI
- Boto3 (Python)
- AWS SDK for Java
- AWS SDK for JavaScript
- AWS SDK for Go

the troubleshooting methodology is largely the same.

This chapter covers common SDK and CLI issues, debugging techniques, and production best practices.

---

# Learning Objectives

After completing this chapter, you'll understand:

- AWS CLI troubleshooting
- SDK troubleshooting
- Credential issues
- Region mismatches
- Endpoint configuration
- Retry behavior
- Network issues
- Debug logging
- Production debugging workflow

---

# Request Flow

```text
Application

      │

      ▼

AWS SDK

      │

      ▼

Credentials

      │

      ▼

AWS Endpoint

      │

      ▼

Amazon DynamoDB
```

Failures can occur at any stage.

---

# Common Problems

Production issues commonly involve:

- Invalid credentials
- Wrong Region
- Wrong AWS profile
- Endpoint configuration
- Serialization errors
- Validation errors
- Retry storms
- Timeout issues
- Network connectivity

---

# Problem 1 — Credentials Not Found

Typical error:

```text
Unable to locate credentials
```

SDK cannot authenticate.

---

## CLI Investigation

```bash
aws configure list
```

Verify:

- Access Key
- Secret Key
- Region
- Profile

---

## Boto3 Example

```python
import boto3

client = boto3.client("dynamodb")
```

If credentials are unavailable:

```text
NoCredentialsError
```

---

# Verify Identity

Always start with:

```bash
aws sts get-caller-identity
```

Verify:

- Account
- User
- Role

---

# Problem 2 — Wrong AWS Profile

Current profile:

```bash
echo $AWS_PROFILE
```

or

```bash
aws configure list
```

Application:

```text
Development

↓

Production Table

↓

Failure
```

---

# Problem 3 — Wrong Region

CLI:

```bash
aws configure get region
```

Example:

```text
Application

↓

us-west-2

↓

Table

↓

us-east-1
```

Result:

```text
ResourceNotFoundException
```

---

# Problem 4 — Endpoint Misconfiguration

Local development:

```text
localhost:8000
```

Production:

```text
AWS Endpoint
```

If the application still points to localhost:

```text
Connection Refused
```

---

# Local DynamoDB Example

```python
client = boto3.client(
    "dynamodb",
    endpoint_url="http://localhost:8000"
)
```

Remember to remove custom endpoints before deploying.

---

# Problem 5 — Serialization Errors

Incorrect:

```python
{
    "price": "100"
}
```

Expected:

```python
Decimal("100")
```

Boto3 expects numeric values to be represented using `Decimal` for precise serialization.

---

# Problem 6 — ValidationException

Example:

```text
ValidationException
```

Common causes:

- Missing partition key
- Wrong attribute type
- Invalid expression
- Invalid JSON

---

# Problem 7 — Timeout

Application:

```text
SDK

↓

Network

↓

Timeout
```

Possible causes:

- Slow network
- VPC configuration
- Firewall
- Proxy
- AWS outage

---

# Problem 8 — Retry Storm

Incorrect implementation:

```text
Failure

↓

Retry

↓

Retry

↓

Retry

↓

More Failures
```

Use exponential backoff with jitter.

---

# SDK Retry Architecture

```text
Failure

↓

Backoff

↓

Retry

↓

Success
```

AWS SDKs implement retry logic automatically, but applications should avoid layering excessive custom retries on top.

---

# CLI Debug Mode

Extremely useful:

```bash
aws dynamodb list-tables --debug
```

Shows:

- HTTP request
- HTTP response
- Credentials used
- Endpoint
- Request ID
- Retry attempts

---

# Boto3 Logging

Enable logging:

```python
import logging
import boto3

logging.basicConfig(level=logging.DEBUG)

client = boto3.client("dynamodb")
```

Useful for diagnosing request failures.

---

# Network Investigation

```text
Application

↓

DNS

↓

TLS

↓

AWS Endpoint

↓

DynamoDB
```

Failures can occur at:

- DNS
- Firewall
- Proxy
- VPN
- VPC Endpoint

---

# VPC Endpoint Example

Private architecture:

```text
EC2

↓

VPC Endpoint

↓

Amazon DynamoDB
```

If the endpoint policy is incorrect:

```text
Connection Failure

↓

Access Issues
```

---

# Debugging Workflow

```text
Failure

↓

Credentials

↓

Identity

↓

Region

↓

Endpoint

↓

Request

↓

Logs

↓

CloudTrail

↓

Root Cause
```

---

# Production Example

Deployment succeeds.

Application logs:

```text
ResourceNotFoundException
```

Investigation:

```text
Region

↓

Incorrect

↓

Application Config

↓

Fixed
```

---

# Another Production Example

Lambda:

```text
Function

↓

IAM Role

↓

Missing Permission

↓

AccessDenied
```

Application appears broken.

Root cause:

```text
Execution Role
```

---

# SDK Version Issues

Older SDKs may:

- Miss new DynamoDB features
- Have deprecated APIs
- Contain resolved bugs

Keep SDKs reasonably up to date and review release notes before major upgrades.

---

# Monitoring

Monitor:

- SDK retries
- Failed API calls
- Timeout rate
- Latency
- HTTP status codes
- CloudWatch metrics
- CloudTrail events

---

# Production Checklist

Verify:

- Credentials
- AWS Profile
- Region
- Endpoint
- IAM Role
- Request payload
- Retry configuration
- SDK version
- Network connectivity

---

# Performance Considerations

- Reuse SDK clients instead of creating one per request.
- Enable connection pooling where supported.
- Configure appropriate timeout values.
- Avoid excessive retries.
- Monitor latency at both the SDK and application levels.

---

# Best Practices

- Use IAM Roles instead of static credentials.
- Enable SDK logging during investigations.
- Use `aws --debug` for CLI troubleshooting.
- Validate Regions before deployment.
- Centralize SDK configuration.
- Keep SDK versions current.
- Monitor retry behavior.

---

# Common Mistakes

## Creating SDK Clients Repeatedly

Bad:

```python
def get_user():
    client = boto3.client("dynamodb")
```

Better:

```python
client = boto3.client("dynamodb")
```

Reuse clients throughout the application.

---

## Hardcoding Credentials

Use:

- IAM Roles
- AWS IAM Identity Center
- Environment variables
- Shared credentials file

Avoid embedding credentials in source code.

---

## Ignoring CLI Debug Mode

`--debug` often identifies configuration problems within minutes.

---

## Using Local Endpoints in Production

Always verify:

```text
endpoint_url
```

before deployment.

---

## Overriding SDK Retry Logic

Adding aggressive custom retries on top of SDK retries can increase latency and amplify failures.

---

# Interview Notes

### What is the first command you run when the AWS CLI fails?

```bash
aws sts get-caller-identity
```

It verifies the active identity and confirms that credentials are working.

---

### How do you troubleshoot `ResourceNotFoundException`?

Verify:

- Table name
- AWS Region
- AWS Account
- Active credentials
- Table status

---

### Why is `aws --debug` useful?

It displays the complete request lifecycle, including authentication, HTTP requests, responses, retry attempts, endpoints, and request IDs.

---

### Why should SDK clients be reused?

Reusing clients improves performance by taking advantage of connection pooling, reducing initialization overhead, and lowering resource consumption.

---

### What are common causes of SDK failures?

- Invalid credentials
- Wrong Region
- IAM permission issues
- Endpoint misconfiguration
- Network problems
- Invalid request payloads
- Serialization errors

---

# Key Takeaways

- Most SDK and CLI issues stem from configuration rather than DynamoDB itself.
- A structured troubleshooting process—identity, Region, endpoint, permissions, request validation, and logging—quickly isolates root causes.
- The AWS CLI's `--debug` option and SDK debug logging are invaluable tools for diagnosing production problems.
- Proper client reuse, credential management, retry configuration, and monitoring contribute to more reliable and performant applications.
- Senior backend engineers standardize SDK configuration and build observability into their applications to reduce operational complexity.