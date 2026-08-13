# Monitoring, Invocation & Performance

> Learn how to invoke, monitor, optimize, and troubleshoot AWS Lambda functions using the AWS CLI. This chapter covers synchronous and asynchronous invocation, logs, concurrency, performance optimization, cold starts, memory tuning, reserved concurrency, provisioned concurrency, and production monitoring.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Invoke Lambda functions using the AWS CLI
- Understand synchronous and asynchronous execution
- Monitor Lambda performance
- Analyze CloudWatch metrics
- Optimize memory and execution time
- Understand concurrency
- Reduce cold starts
- Build production-ready serverless applications

---

# Lambda Execution Flow

Every Lambda invocation follows the same lifecycle.

```text
Client

↓

Invoke Function

↓

Initialize Runtime

↓

Execute Handler

↓

Return Response

↓

CloudWatch Logs
```

---

# Invoking a Lambda Function

The simplest invocation:

```bash
aws lambda invoke \
--function-name payment-api \
response.json
```

The response payload is written to the specified file.

---

# Invoke with Payload

Example:

```bash
aws lambda invoke \
--function-name payment-api \
--payload '{"order_id":101}' \
response.json
```

Lambda receives:

```json
{
    "order_id":101
}
```

---

# Synchronous Invocation

Invocation Type:

```text
RequestResponse
```

Workflow:

```text
Client

↓

Lambda

↓

Process Request

↓

Response Returned
```

The client waits for the function to finish.

---

# Asynchronous Invocation

Invocation Type:

```text
Event
```

Example:

```bash
aws lambda invoke \
--function-name payment-api \
--invocation-type Event \
--payload '{"order_id":101}' \
response.json
```

Workflow:

```text
Client

↓

Lambda

↓

Accepted

↓

Process Later
```

The caller receives confirmation immediately.

---

# Dry Run

Validate permissions without executing.

```bash
aws lambda invoke \
--function-name payment-api \
--invocation-type DryRun \
response.json
```

Useful for testing IAM permissions.

---

# Invocation Types Summary

| Type | Wait for Response | Typical Use Case |
|---------|------------------|------------------|
| RequestResponse | Yes | API Gateway |
| Event | No | SNS, EventBridge |
| DryRun | No | Permission validation |

---

# Viewing Function Logs

Lambda automatically writes logs to CloudWatch.

List log groups:

```bash
aws logs describe-log-groups
```

Tail logs:

```bash
aws logs tail \
/aws/lambda/payment-api \
--follow
```

---

# CloudWatch Metrics

Lambda automatically publishes metrics.

Common metrics include:

- Invocations
- Duration
- Errors
- Throttles
- ConcurrentExecutions
- IteratorAge
- DeadLetterErrors

---

# List Lambda Metrics

```bash
aws cloudwatch list-metrics \
--namespace AWS/Lambda
```

---

# Retrieve Duration Metric

```bash
aws cloudwatch get-metric-statistics \
--namespace AWS/Lambda \
--metric-name Duration
```

---

# Common Lambda Metrics

| Metric | Description |
|---------|-------------|
| Invocations | Number of executions |
| Errors | Failed executions |
| Duration | Execution time |
| Throttles | Rejected requests |
| ConcurrentExecutions | Active executions |
| DeadLetterErrors | Failed DLQ writes |

---

# Understanding Concurrency

Concurrency represents the number of functions executing simultaneously.

```text
100 Requests

↓

100 Lambda Instances
```

Each request receives its own execution environment.

---

# Reserved Concurrency

Reserved concurrency guarantees capacity.

```bash
aws lambda put-function-concurrency \
--function-name payment-api \
--reserved-concurrent-executions 50
```

Benefits:

- Prevents noisy neighbors
- Protects downstream systems
- Guarantees capacity

---

# Remove Reserved Concurrency

```bash
aws lambda delete-function-concurrency \
--function-name payment-api
```

---

# Provisioned Concurrency

Provisioned Concurrency keeps execution environments warm.

```text
Without Provisioned Concurrency

↓

Cold Start
```

```text
With Provisioned Concurrency

↓

Warm Environment

↓

Immediate Response
```

Ideal for latency-sensitive applications.

---

# Configure Provisioned Concurrency

```bash
aws lambda put-provisioned-concurrency-config \
--function-name payment-api \
--qualifier Production \
--provisioned-concurrent-executions 10
```

---

# Cold Starts

Cold starts occur when Lambda creates a new execution environment.

Factors affecting cold starts:

- Runtime
- Deployment package size
- VPC configuration
- Layer size
- Initialization code

---

# Reducing Cold Starts

Best practices:

- Keep deployment packages small.
- Minimize dependencies.
- Reduce initialization logic.
- Use Provisioned Concurrency for critical workloads.
- Keep functions focused.

---

# Memory Optimization

Increasing memory increases CPU allocation.

```text
128 MB

↓

512 MB

↓

1024 MB

↓

2048 MB
```

Higher memory often reduces execution time.

---

# Performance Tuning

Monitor:

- Duration
- Memory utilization
- Error rate
- Cold starts
- Concurrent executions

Adjust:

- Memory
- Timeout
- Concurrency

---

# Timeout Optimization

Avoid unnecessarily long timeouts.

Example:

```text
API Request

↓

Expected Time

↓

2 Seconds

↓

Timeout

↓

5 Seconds
```

Choose values based on expected workloads.

---

# Monitoring Workflow

```text
Lambda

↓

CloudWatch Metrics

↓

CloudWatch Alarms

↓

SNS

↓

Operations Team
```

---

# Error Monitoring

Monitor:

- Error Count
- Error Rate
- Timeout Errors
- Throttling
- Invocation Failures

Errors should trigger alarms.

---

# Performance Workflow

```text
Deploy Function

↓

Invoke

↓

Monitor Metrics

↓

Review Logs

↓

Optimize Memory

↓

Reduce Duration
```

Continuous optimization improves both performance and cost.

---

# Common Errors

## TooManyRequestsException

Cause:

```text
Concurrency Limit Reached
```

Solutions:

- Increase concurrency
- Optimize execution time
- Use asynchronous processing

---

## TaskTimedOut

Cause:

```text
Execution Time

>

Configured Timeout
```

Increase timeout or optimize code.

---

## OutOfMemoryError

Cause:

Function exceeded allocated memory.

Increase memory allocation.

---

## ThrottlingException

Occurs when concurrency limits are exceeded.

Review:

- Reserved Concurrency
- Account concurrency limits
- Function execution time

---

# Production Best Practices

- Monitor every Lambda function.
- Create alarms for Errors and Throttles.
- Optimize memory before increasing timeout.
- Keep execution times short.
- Configure Reserved Concurrency for critical services.
- Use Provisioned Concurrency for latency-sensitive APIs.
- Review CloudWatch metrics regularly.
- Continuously optimize cost and performance.

---

# Real-World Workflow

```text
Client

↓

API Gateway

↓

Lambda

↓

CloudWatch Metrics

↓

Alarm

↓

SNS

↓

Engineer

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
      ├── CloudWatch Metrics
      ├── CloudWatch Logs
      ├── Alarms
      └── SNS
              │
              ▼
Operations Team
```

CloudWatch provides complete operational visibility into Lambda execution, performance, and reliability.

---

# Interview Note

### Question

**How would you optimize a slow AWS Lambda function?**

### Answer

I would first review CloudWatch metrics such as Duration, Errors, and Concurrent Executions, followed by CloudWatch Logs to identify bottlenecks. I would then optimize initialization code, reduce unnecessary dependencies, increase memory if CPU-bound, tune timeout values, and consider using Provisioned Concurrency if cold starts are affecting latency. Finally, I would continuously monitor performance after deployment to validate the improvements.

---

# Key Takeaways

- Lambda supports synchronous, asynchronous, and dry-run invocations.
- CloudWatch provides metrics and logs for monitoring Lambda performance.
- Memory allocation affects both RAM and CPU performance.
- Reserved Concurrency controls scaling and protects downstream services.
- Provisioned Concurrency minimizes cold starts.
- Performance tuning should balance latency, reliability, and cost.
- Continuous monitoring is essential for production serverless applications.