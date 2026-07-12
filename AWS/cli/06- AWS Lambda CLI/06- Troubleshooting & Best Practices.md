# Troubleshooting & Best Practices

> Learn how to troubleshoot AWS Lambda deployments, execution failures, permission issues, performance bottlenecks, and event source problems. This chapter also covers production best practices for building secure, scalable, reliable, and cost-efficient serverless applications.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Troubleshoot Lambda execution failures
- Debug deployment issues
- Diagnose permission errors
- Analyze CloudWatch logs
- Resolve timeout and memory issues
- Troubleshoot event source mappings
- Apply production-ready best practices

---

# Lambda Troubleshooting Workflow

Whenever a Lambda function fails:

```text
Invocation Failed
        │
        ▼
Check CloudWatch Logs
        │
        ▼
Verify IAM Permissions
        │
        ▼
Review Function Configuration
        │
        ▼
Verify Event Source
        │
        ▼
Fix Issue
        │
        ▼
Deploy Again
```

CloudWatch Logs should always be your first troubleshooting step.

---

# Verify Function Configuration

```bash
aws lambda get-function-configuration \
--function-name payment-api
```

Verify:

- Runtime
- Handler
- Memory
- Timeout
- Execution Role
- Environment Variables

---

# Function Not Found

Example:

```text
ResourceNotFoundException
```

Verify:

```bash
aws lambda list-functions
```

Possible causes:

- Incorrect function name
- Wrong AWS Region
- Wrong AWS Account

---

# Access Denied

Example:

```text
AccessDeniedException
```

Possible causes:

- Missing IAM permissions
- Incorrect Execution Role
- Missing Resource Policy

Verify identity:

```bash
aws sts get-caller-identity
```

---

# Handler Not Found

Example:

```text
Runtime.HandlerNotFound
```

Common causes:

```text
Wrong Handler Name

Wrong Filename

Incorrect Function Name
```

Example:

```text
lambda_function.lambda_handler
```

Must match:

```python
def lambda_handler(event, context):
```

---

# Import Module Error

Example:

```text
Unable to import module
```

Possible causes:

- Missing dependencies
- Incorrect ZIP package
- Unsupported runtime
- Wrong folder structure

Verify deployment package.

---

# Timeout Errors

Example:

```text
Task timed out
```

Possible causes:

- Long-running code
- Slow database
- External API delay
- Large file processing

Solutions:

- Optimize code
- Increase timeout
- Move heavy work to asynchronous processing

---

# Memory Errors

Example:

```text
Runtime exited with error:
OutOfMemoryError
```

Increase memory:

```bash
aws lambda update-function-configuration \
--function-name payment-api \
--memory-size 1024
```

Remember:

More memory also provides more CPU.

---

# Environment Variable Problems

Verify:

```bash
aws lambda get-function-configuration \
--function-name payment-api
```

Common issues:

- Typographical errors
- Missing variables
- Incorrect values
- Secrets stored directly

Prefer:

- AWS Secrets Manager
- Systems Manager Parameter Store

---

# CloudWatch Logs Missing

Verify Log Groups:

```bash
aws logs describe-log-groups
```

Common causes:

- Execution Role missing logging permissions
- Function never executed
- Wrong Region

Required IAM permissions:

```text
logs:CreateLogGroup

logs:CreateLogStream

logs:PutLogEvents
```

---

# Event Source Not Triggering

Verify mappings:

```bash
aws lambda list-event-source-mappings
```

Check:

- Event Source ARN
- IAM permissions
- Queue or Stream status
- Mapping state

---

# SQS Messages Not Processing

Possible causes:

- Disabled mapping
- Queue permissions
- Reserved concurrency set to zero
- Function failures

Verify:

```bash
aws lambda list-event-source-mappings
```

---

# API Gateway Cannot Invoke Lambda

Verify:

```bash
aws lambda get-policy \
--function-name payment-api
```

Ensure API Gateway has permission:

```text
lambda:InvokeFunction
```

---

# Deployment Failed

Possible causes:

- Invalid ZIP file
- Unsupported runtime
- Invalid handler
- Missing IAM Role

Review deployment output carefully.

---

# Version Problems

Traffic going to the wrong version?

Verify aliases:

```bash
aws lambda list-aliases \
--function-name payment-api
```

Confirm:

```text
Production

↓

Version 12
```

---

# Cold Start Issues

Symptoms:

- Slow first request
- High latency
- Increased Duration metric

Solutions:

- Smaller deployment package
- Fewer dependencies
- Provisioned Concurrency
- Optimize initialization code

---

# High Duration

Possible causes:

- Database queries
- External APIs
- Heavy computation
- Large file processing

Review:

- CloudWatch Metrics
- CloudWatch Logs
- X-Ray (if enabled)

---

# Throttling

Example:

```text
TooManyRequestsException
```

Possible causes:

- Reserved concurrency exhausted
- Account concurrency limit reached

Solutions:

- Increase concurrency
- Reduce execution time
- Optimize event processing

---

# Retry Failures

Asynchronous invocations retry automatically.

If retries continue failing:

```text
Lambda

↓

Retry

↓

Retry

↓

Dead Letter Queue
```

Review the DLQ for failed events.

---

# Common Errors

| Error | Cause | Resolution |
|--------|-------|------------|
| ResourceNotFoundException | Wrong function name | Verify function exists |
| AccessDeniedException | IAM issue | Review Execution Role |
| HandlerNotFound | Invalid handler | Verify handler configuration |
| ImportModuleError | Missing dependencies | Rebuild deployment package |
| TaskTimedOut | Long execution | Increase timeout or optimize code |
| OutOfMemoryError | Insufficient memory | Increase memory allocation |
| TooManyRequestsException | Concurrency exhausted | Review concurrency limits |

---

# Production Deployment Checklist

Before deployment:

- □ Validate IAM Role
- □ Verify Environment Variables
- □ Package dependencies
- □ Publish a new Version
- □ Update Alias
- □ Test invocation
- □ Review CloudWatch Logs
- □ Verify alarms
- □ Test rollback

---

# Production Best Practices

## Keep Functions Small

Each function should perform one responsibility.

Avoid:

```text
One Function

↓

Authentication

Payments

Email

Reporting
```

Prefer:

```text
Authenticate User

↓

Process Payment

↓

Send Email

↓

Generate Report
```

---

## Use Versions and Aliases

Never deploy directly to production using:

```text
$LATEST
```

Always publish a version and update an alias.

---

## Store Secrets Securely

Avoid:

```python
PASSWORD = "admin123"
```

Use:

- AWS Secrets Manager
- Systems Manager Parameter Store

---

## Apply Least Privilege

Grant only required permissions.

Avoid:

```text
AdministratorAccess
```

Prefer service-specific permissions.

---

## Monitor Every Function

Configure alarms for:

- Errors
- Duration
- Throttles
- Concurrent Executions

---

## Optimize Cost

Reduce:

- Execution time
- Memory usage
- Cold starts

Serverless cost optimization depends on efficient execution.

---

## Automate Deployments

Typical workflow:

```text
Git

↓

CI/CD

↓

Build

↓

Publish Version

↓

Update Alias

↓

Production
```

Manual deployments should be avoided.

---

# Real-World Workflow

```text
Developer

↓

Git

↓

CI/CD

↓

Lambda Deployment

↓

CloudWatch

↓

Monitoring

↓

Incident Response

↓

Optimization
```

---

# Architecture Note

```text
Client
      │
      ▼
API Gateway
      │
      ▼
Lambda
      │
      ├── IAM
      ├── Secrets Manager
      ├── CloudWatch
      ├── Event Sources
      └── DynamoDB / S3 / SQS
```

A production Lambda application combines compute, security, monitoring, and event-driven integrations into a single serverless architecture.

---

# Interview Note

### Question

**How would you troubleshoot a Lambda function that suddenly starts failing in production?**

### Answer

I would begin by reviewing CloudWatch Logs to identify the exact error and correlate it with recent deployments. Next, I would verify the Lambda configuration, including the runtime, handler, timeout, memory allocation, execution role, and environment variables. I would also inspect CloudWatch metrics such as Errors, Duration, and Throttles to understand the impact. If the issue was introduced by a recent deployment, I would immediately roll back by updating the production alias to the previous stable version while investigating the root cause.

---

# Key Takeaways

- CloudWatch Logs are the primary tool for Lambda troubleshooting.
- Verify IAM permissions before investigating application code.
- Most Lambda failures result from incorrect handlers, missing dependencies, insufficient permissions, or timeout and memory limits.
- Use Versions and Aliases to enable fast production rollbacks.
- Monitor every production Lambda function with CloudWatch metrics and alarms.
- Apply least-privilege IAM permissions and store secrets securely.
- Automate deployments and rollback procedures through CI/CD pipelines.