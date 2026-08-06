# 01- Common Errors

# Overview

AWS Lambda applications can fail for many reasons, ranging from simple configuration mistakes to complex distributed system failures. While Lambda itself is a fully managed service, production issues often originate from IAM permissions, networking, deployment packages, concurrency limits, downstream dependencies, or incorrect event configurations.

This chapter covers the most frequently encountered Lambda errors, explains their root causes, and provides practical troubleshooting steps and production recommendations.

---

# Lambda Troubleshooting Workflow

When a Lambda function fails, always follow a structured approach.

```
Problem Reported

↓

CloudWatch Metrics

↓

CloudWatch Logs

↓

AWS X-Ray

↓

Identify Root Cause

↓

Implement Fix

↓

Verify

↓

Monitor
```

Never make assumptions without checking logs and metrics.

---

# Error Categories

Most Lambda issues fall into one of the following categories:

- Invocation Errors
- Runtime Errors
- IAM Errors
- Deployment Errors
- Networking Errors
- Timeout Errors
- Memory Issues
- Concurrency Problems
- Event Source Failures
- Downstream Service Failures

---

# Error: Task Timed Out

Example

```
Task timed out after 30.00 seconds
```

## Possible Causes

- Slow database query
- Slow external API
- Infinite loop
- Large file processing
- Deadlock

## Investigation

Check:

- CloudWatch Duration
- X-Ray traces
- Database latency
- External API response times

## Resolution

- Increase timeout if justified.
- Optimize SQL queries.
- Use asynchronous processing.
- Process files in batches.
- Add retries with exponential backoff.

---

# Error: Process Exited Before Completing Request

Example

```
Process exited before completing request
```

## Possible Causes

- Function terminated unexpectedly
- Runtime crash
- Missing return statement
- Incorrect async handling

## Resolution

- Ensure the handler returns properly.
- Await asynchronous operations.
- Check runtime compatibility.
- Review exception handling.

---

# Error: Runtime.ImportModuleError

Example

```
Runtime.ImportModuleError

Unable to import module
```

## Possible Causes

- Missing dependency
- Incorrect deployment package
- Wrong handler path
- Unsupported library

## Investigation

Verify:

```
Deployment Package

↓

Handler

↓

Dependencies
```

## Resolution

- Rebuild the deployment package.
- Verify handler configuration.
- Include all dependencies.
- Match package structure with the runtime.

---

# Error: Handler Not Found

Example

```
Handler 'app.handler' missing
```

## Root Cause

Lambda cannot locate the configured handler.

## Resolution

Verify:

```
File Name

↓

Handler Name

↓

Runtime
```

Python example

```
app.py

↓

def handler(...)
```

Handler value

```
app.handler
```

---

# Error: AccessDeniedException

Example

```
AccessDeniedException
```

## Root Cause

IAM policy does not allow the requested action.

## Investigation

Review:

- Execution Role
- Resource Policy
- CloudTrail

## Resolution

Grant only the required permission.

Bad

```json
Action: "*"
```

Good

```json
Action:
- s3:GetObject
```

Follow the Principle of Least Privilege.

---

# Error: Unable to Assume Role

Example

```
The role defined for the function cannot be assumed.
```

## Root Cause

Incorrect trust relationship.

## Resolution

Verify the IAM Role trust policy allows:

```
lambda.amazonaws.com
```

---

# Error: ResourceNotFoundException

Example

```
ResourceNotFoundException
```

## Possible Causes

- Incorrect ARN
- Deleted resource
- Wrong Region
- Wrong Account

## Resolution

Verify:

- ARN
- Region
- Account ID
- Resource existence

---

# Error: TooManyRequestsException

Example

```
Rate Exceeded

TooManyRequestsException
```

## Root Cause

Lambda concurrency limit exceeded.

```
Traffic Spike

↓

Concurrency Limit

↓

Throttle
```

## Resolution

- Increase concurrency quota.
- Optimize execution time.
- Use Amazon SQS.
- Reduce traffic bursts.

---

# Error: Out Of Memory

Example

```
Runtime exited with error:
signal: killed
```

## Root Cause

Configured memory is insufficient.

## Investigation

Review:

CloudWatch

↓

Max Memory Used

## Resolution

- Increase memory.
- Stream large files.
- Reduce object allocations.
- Optimize algorithms.

---

# Error: Disk Space Exhausted

Example

```
No space left on device
```

## Root Cause

Temporary storage exceeded.

```
/tmp
```

## Resolution

- Delete temporary files.
- Increase Ephemeral Storage.
- Use Amazon EFS for large files.

---

# Error: ENI Limit Reached

Example

```
Elastic Network Interface limit exceeded
```

## Root Cause

Large VPC-based scaling.

## Resolution

- Review subnet configuration.
- Remove unnecessary VPC usage.
- Request service quota increase.

---

# Error: DNS Resolution Failure

Example

```
Name or service not known
```

## Investigation

Check:

- VPC
- Route Tables
- DNS Settings
- NAT Gateway

## Resolution

Ensure outbound connectivity is configured correctly.

---

# Error: Connection Timeout

Example

```
Connection timed out
```

## Possible Causes

- Database unavailable
- Security Groups
- NAT Gateway
- Firewall
- External API

## Investigation

```
Lambda

↓

Network

↓

Destination
```

---

# Error: SSL Certificate Error

Example

```
SSL handshake failed
```

## Possible Causes

- Invalid certificate
- Expired certificate
- Incorrect hostname

## Resolution

Verify:

- Certificate validity
- TLS version
- Endpoint URL

---

# Error: Database Connection Limit Reached

Example

```
Too many connections
```

## Root Cause

Every Lambda opens a database connection.

## Resolution

```
Lambda

↓

RDS Proxy

↓

Aurora
```

Benefits:

- Connection pooling
- Better scalability
- Lower latency

---

# Error: Recursive Invocation

Example

```
Millions of invocations
```

## Root Cause

Lambda continuously triggers itself.

Example

```
S3

↓

Lambda

↓

S3

↓

Lambda
```

## Resolution

- Use separate buckets.
- Configure event filters.
- Disable trigger immediately.
- Set Reserved Concurrency to 0 during investigation.

---

# Error: Invalid Response from Lambda

Example

```
502 Bad Gateway
```

## Root Cause

Incorrect response format.

Correct response

```json
{
  "statusCode": 200,
  "body": "{}"
}
```

---

# Error: Deployment Package Too Large

Example

```
RequestEntityTooLargeException
```

## Resolution

- Remove unused dependencies.
- Use Lambda Layers.
- Use Container Images.
- Compress assets.

---

# Error: Function Version Not Found

Example

```
Version does not exist
```

## Root Cause

Alias points to a deleted version.

## Resolution

Update alias to a valid published version.

---

# Error: Secrets Manager Access Failed

Possible causes:

- Missing IAM permission
- Incorrect secret ARN
- Wrong Region

Required permission

```
secretsmanager:GetSecretValue
```

---

# Error: Event Source Not Invoking Lambda

Check:

- Trigger enabled
- Permissions
- Event pattern
- Event source mapping
- Dead Letter Queue

---

# Production Troubleshooting Checklist

Whenever Lambda fails:

- [ ] Review CloudWatch Logs
- [ ] Check CloudWatch Metrics
- [ ] Enable AWS X-Ray
- [ ] Verify IAM permissions
- [ ] Check timeout settings
- [ ] Review memory utilization
- [ ] Verify VPC networking
- [ ] Validate event source configuration
- [ ] Check downstream service health
- [ ] Review recent deployments

---

# Common Mistakes

❌ Using AdministratorAccess

❌ Hardcoding credentials

❌ Opening database connections every invocation

❌ Ignoring CloudWatch metrics

❌ Logging sensitive data

❌ Deploying without testing

❌ Ignoring retries

❌ Not configuring alarms

---

# Best Practices

✅ Use structured logging.

✅ Enable CloudWatch Alarms.

✅ Configure AWS X-Ray.

✅ Use RDS Proxy.

✅ Store secrets in Secrets Manager.

✅ Apply least-privilege IAM.

✅ Monitor concurrency.

✅ Test deployments before production.

---

# Senior Backend Engineering Perspective

Production issues in Lambda are rarely caused by the compute service itself. Most incidents arise from interactions with surrounding systems such as databases, networking, IAM policies, third-party APIs, and event sources.

Senior engineers troubleshoot methodically by correlating CloudWatch metrics, logs, traces, and deployment history. Rather than treating symptoms, they identify the underlying cause and implement durable fixes that improve the resilience and observability of the entire system.

---

# Key Takeaways

- Most Lambda failures originate from IAM, networking, downstream services, or configuration rather than the Lambda platform itself.
- CloudWatch Logs, Metrics, and AWS X-Ray are the primary tools for diagnosing production issues.
- Understanding common error patterns enables faster incident response and reduces downtime.
- Structured troubleshooting and strong observability practices are essential for reliable serverless applications.
- Preventive measures such as least-privilege IAM, RDS Proxy, alarms, and deployment validation significantly reduce production failures.