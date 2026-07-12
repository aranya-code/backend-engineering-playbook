# Cheat Sheet & Interview Guide

> A practical reference for the most commonly used AWS Lambda CLI commands, deployment workflows, troubleshooting techniques, and interview preparation. This chapter serves as a day-to-day operational guide for Backend Engineers, DevOps Engineers, Cloud Engineers, Platform Engineers, and AWS Solutions Architects.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Quickly recall frequently used Lambda CLI commands
- Deploy and manage Lambda functions
- Monitor and troubleshoot Lambda workloads
- Optimize Lambda performance
- Prepare for AWS certification and backend engineering interviews

---

# Why a Cheat Sheet?

AWS Lambda is one of the most frequently used AWS services.

Rather than memorizing every command, experienced engineers remember:

- Deployment workflow
- Version management
- Invocation methods
- Monitoring strategy
- Security best practices
- Troubleshooting process

This chapter serves as a quick operational reference.

---

# Command Syntax

General syntax:

```bash
aws lambda <operation>
```

Examples:

```bash
aws lambda list-functions
```

```bash
aws lambda create-function
```

```bash
aws lambda invoke
```

```bash
aws lambda update-function-code
```

---

# Function Management Commands

## List Functions

```bash
aws lambda list-functions
```

---

## Get Function Details

```bash
aws lambda get-function \
--function-name payment-api
```

---

## Get Function Configuration

```bash
aws lambda get-function-configuration \
--function-name payment-api
```

---

## Create Function

```bash
aws lambda create-function
```

---

## Delete Function

```bash
aws lambda delete-function
```

---

# Deployment Commands

## Update Function Code

```bash
aws lambda update-function-code
```

---

## Update Function Configuration

```bash
aws lambda update-function-configuration
```

---

## Publish Version

```bash
aws lambda publish-version
```

---

## List Versions

```bash
aws lambda list-versions-by-function
```

---

# Alias Commands

## Create Alias

```bash
aws lambda create-alias
```

---

## List Aliases

```bash
aws lambda list-aliases
```

---

## Update Alias

```bash
aws lambda update-alias
```

---

## Delete Alias

```bash
aws lambda delete-alias
```

---

# Invocation Commands

## Invoke Function

```bash
aws lambda invoke
```

---

## Synchronous Invocation

```bash
aws lambda invoke \
--invocation-type RequestResponse
```

---

## Asynchronous Invocation

```bash
aws lambda invoke \
--invocation-type Event
```

---

## Dry Run

```bash
aws lambda invoke \
--invocation-type DryRun
```

---

# Event Source Commands

## Create Event Source Mapping

```bash
aws lambda create-event-source-mapping
```

---

## List Event Source Mappings

```bash
aws lambda list-event-source-mappings
```

---

## Delete Event Source Mapping

```bash
aws lambda delete-event-source-mapping
```

---

# Layer Commands

## Publish Layer

```bash
aws lambda publish-layer-version
```

---

## List Layers

```bash
aws lambda list-layers
```

---

## List Layer Versions

```bash
aws lambda list-layer-versions
```

---

# Permission Commands

## View Resource Policy

```bash
aws lambda get-policy
```

---

## Add Permission

```bash
aws lambda add-permission
```

---

## Remove Permission

```bash
aws lambda remove-permission
```

---

# Concurrency Commands

## Configure Reserved Concurrency

```bash
aws lambda put-function-concurrency
```

---

## Remove Reserved Concurrency

```bash
aws lambda delete-function-concurrency
```

---

## Configure Provisioned Concurrency

```bash
aws lambda put-provisioned-concurrency-config
```

---

# Monitoring Commands

## List Metrics

```bash
aws cloudwatch list-metrics \
--namespace AWS/Lambda
```

---

## View CloudWatch Logs

```bash
aws logs tail \
/aws/lambda/payment-api \
--follow
```

---

## List Log Groups

```bash
aws logs describe-log-groups
```

---

# Useful Global Options

| Option | Purpose |
|----------|----------|
| `--profile` | Use a named AWS profile |
| `--region` | Override default Region |
| `--output json` | JSON output |
| `--output table` | Table output |
| `--query` | Filter CLI output |
| `--debug` | Enable verbose debugging |
| `--no-cli-pager` | Disable CLI pager |

---

# Lambda Invocation Types

| Type | Description | Typical Use Case |
|------|-------------|------------------|
| RequestResponse | Client waits for response | API Gateway |
| Event | Fire-and-forget | SNS, EventBridge |
| DryRun | Validate permissions only | Testing |

---

# Common Event Sources

| Service | Invocation Type |
|----------|-----------------|
| API Gateway | Synchronous |
| S3 | Asynchronous |
| SNS | Asynchronous |
| SQS | Poll-based |
| EventBridge | Asynchronous |
| DynamoDB Streams | Poll-based |
| Kinesis | Poll-based |

---

# Common CloudWatch Metrics

| Metric | Description |
|---------|-------------|
| Invocations | Number of function executions |
| Errors | Failed executions |
| Duration | Execution time |
| Throttles | Rejected invocations |
| ConcurrentExecutions | Active concurrent executions |
| DeadLetterErrors | Failed DLQ deliveries |

---

# Common Errors

| Error | Cause | Resolution |
|--------|-------|------------|
| ResourceNotFoundException | Function not found | Verify function name |
| AccessDeniedException | IAM permissions | Review Execution Role |
| Runtime.HandlerNotFound | Invalid handler | Verify handler configuration |
| ImportModuleError | Missing dependencies | Rebuild deployment package |
| TaskTimedOut | Execution exceeded timeout | Optimize code or increase timeout |
| OutOfMemoryError | Memory exhausted | Increase memory allocation |
| TooManyRequestsException | Concurrency exceeded | Review concurrency settings |

---

# Lambda Deployment Workflow

```text
Write Code

↓

Package Application

↓

Deploy Lambda

↓

Publish Version

↓

Update Alias

↓

Invoke Function

↓

Monitor CloudWatch

↓

Production
```

---

# Production Checklist

Before deployment:

- Verify IAM Role.
- Package dependencies.
- Validate Environment Variables.
- Publish a Version.
- Update Alias.
- Test invocation.
- Verify CloudWatch Logs.
- Review CloudWatch Metrics.
- Configure Alarms.
- Verify rollback plan.

---

# Interview Questions

## 1. What is AWS Lambda?

**Answer**

AWS Lambda is a serverless compute service that executes code in response to events without requiring developers to provision or manage servers.

---

## 2. What is the difference between `$LATEST` and a published Version?

**Answer**

`$LATEST` is mutable and changes whenever code is updated. Published Versions are immutable snapshots of a function's code and configuration, making them suitable for production deployments.

---

## 3. What is a Lambda Alias?

**Answer**

An Alias is a named pointer to a specific Lambda Version. It simplifies deployments and supports blue/green and canary release strategies.

---

## 4. What is the purpose of an Execution Role?

**Answer**

The Execution Role defines what AWS resources a Lambda function can access while it is running.

---

## 5. What is the difference between synchronous and asynchronous invocation?

**Answer**

In synchronous invocation, the caller waits for the function to complete and receive a response. In asynchronous invocation, Lambda queues the event and processes it later without making the caller wait.

---

## 6. What are Lambda Layers?

**Answer**

Lambda Layers are reusable packages containing libraries, dependencies, or shared code that can be attached to multiple Lambda functions.

---

## 7. How would you reduce Lambda cold starts?

**Answer**

Reduce deployment package size, minimize initialization code, remove unnecessary dependencies, and use Provisioned Concurrency for latency-sensitive workloads.

---

## 8. Why should secrets not be stored as plain environment variables?

**Answer**

Sensitive values such as API keys and database passwords should be stored in AWS Secrets Manager or Systems Manager Parameter Store to improve security, support automatic rotation, and enable centralized management.

---

## 9. What happens when Lambda reaches its concurrency limit?

**Answer**

Additional requests are throttled until capacity becomes available. Reserved or Provisioned Concurrency can help manage scaling and guarantee capacity for critical workloads.

---

## 10. How would you troubleshoot a failing Lambda function?

**Answer**

I would first review CloudWatch Logs to identify the exact error, verify the function configuration, check the execution role and permissions, inspect CloudWatch metrics such as Errors and Duration, validate event source mappings, and roll back to a previous version if the issue was introduced by a recent deployment.

---

# Senior Engineer Tips

Experienced serverless engineers typically:

- Keep Lambda functions small and focused.
- Never invoke `$LATEST` in production.
- Deploy immutable Versions with Aliases.
- Store secrets in AWS Secrets Manager.
- Share common dependencies using Layers.
- Monitor every function with CloudWatch.
- Configure alarms for Errors and Throttles.
- Use Reserved or Provisioned Concurrency where appropriate.
- Automate deployments through CI/CD pipelines.
- Regularly review Lambda costs and performance.

---

# Quick Reference

| Task | Command |
|------|---------|
| List Functions | `aws lambda list-functions` |
| Create Function | `aws lambda create-function` |
| Update Code | `aws lambda update-function-code` |
| Update Configuration | `aws lambda update-function-configuration` |
| Invoke Function | `aws lambda invoke` |
| Publish Version | `aws lambda publish-version` |
| List Versions | `aws lambda list-versions-by-function` |
| Create Alias | `aws lambda create-alias` |
| List Event Sources | `aws lambda list-event-source-mappings` |
| Publish Layer | `aws lambda publish-layer-version` |

---

# Final Thoughts

AWS Lambda is one of the core building blocks of modern serverless architectures. Mastering the Lambda CLI enables you to automate deployments, manage versions safely, configure event-driven integrations, optimize performance, and operate production serverless applications with confidence. Combined with API Gateway, EventBridge, SQS, SNS, DynamoDB, CloudWatch, and IAM, Lambda provides a powerful platform for building scalable and resilient cloud-native applications.

---
