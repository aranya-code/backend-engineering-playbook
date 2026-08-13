# 01 - Common DynamoDB Errors

## Overview

No matter how well a DynamoDB application is designed, production environments eventually encounter failures. The difference between a junior and a senior engineer is often not the ability to avoid every issue, but the ability to diagnose and resolve them quickly.

This chapter covers the most common DynamoDB errors, explains why they occur, how to troubleshoot them, and how to prevent them in production.

---

# Learning Objectives

After completing this chapter, you'll understand:

- Common DynamoDB exceptions
- Why they occur
- How to troubleshoot them
- Production debugging workflow
- Prevention strategies
- Best practices
- Interview questions

---

# Error Categories

```text
                DynamoDB Errors

                      │

      ┌───────────────┼────────────────┐

      ▼               ▼                ▼

 Application      Configuration     Infrastructure

      ▼               ▼                ▼

Validation      IAM / Region      Capacity / Network
```

---

# Troubleshooting Workflow

```text
Application Error

        │

        ▼

Read Exception

        │

        ▼

Identify Root Cause

        │

        ▼

Verify AWS Resources

        │

        ▼

Implement Fix

        │

        ▼

Validate Solution
```

---

# ResourceNotFoundException

## Example

```text
ResourceNotFoundException:
Requested resource not found
```

---

## Common Causes

- Incorrect table name
- Wrong AWS Region
- Wrong AWS account
- Table deleted
- Table still being created

---

## Troubleshooting

Verify the table exists.

```bash
aws dynamodb describe-table \
    --table-name Orders
```

Check:

- AWS Profile
- AWS Region
- Table Status

---

## Prevention

- Store table names in configuration.
- Use Infrastructure as Code.
- Validate resources during deployment.

---

# AccessDeniedException

## Example

```text
AccessDeniedException:
User is not authorized
```

---

## Common Causes

- Missing IAM permission
- Wrong IAM Role
- Wrong AWS Profile
- Service Control Policy (AWS Organizations)

---

## Troubleshooting

Verify the active identity.

```bash
aws sts get-caller-identity
```

Review IAM policies.

Common required permissions:

```text
dynamodb:GetItem

dynamodb:PutItem

dynamodb:UpdateItem

dynamodb:DeleteItem

dynamodb:Query

dynamodb:Scan
```

---

## Prevention

- Use least-privilege IAM policies.
- Test permissions in lower environments.
- Prefer IAM Roles over long-lived credentials.

---

# ValidationException

## Example

```text
ValidationException
```

---

## Common Causes

- Missing partition key
- Wrong attribute type
- Invalid expression
- Reserved keyword
- Invalid JSON

---

## Example

Incorrect:

```json
{
    "price": {
        "S": "100"
    }
}
```

Correct:

```json
{
    "price": {
        "N": "100"
    }
}
```

---

## Prevention

- Validate request payloads.
- Use strongly typed SDK models.
- Test expressions before deployment.

---

# ProvisionedThroughputExceededException

## Example

```text
ProvisionedThroughputExceededException
```

---

## Common Causes

- Read capacity exhausted
- Write capacity exhausted
- Hot partition
- Traffic spike

---

## Investigation

Review:

- CloudWatch metrics
- Read capacity
- Write capacity
- Access patterns

---

## Solutions

- Increase capacity.
- Enable Auto Scaling.
- Switch to On-Demand mode.
- Improve partition key distribution.

---

# ConditionalCheckFailedException

## Example

```text
ConditionalCheckFailedException
```

---

## Why It Happens

A condition expression evaluated to **false**.

Example:

```text
attribute_not_exists(order_id)
```

If the item already exists, the write fails.

---

## Typical Use Cases

- Optimistic locking
- Idempotency
- Duplicate prevention

---

## Prevention

Design the application to expect this exception rather than treating it as an unexpected failure.

---

# TransactionCanceledException

## Example

```text
TransactionCanceledException
```

---

## Common Causes

- Failed condition check
- Item conflict
- Transaction limit exceeded

---

## Investigation

Check every operation within the transaction.

Typical workflow:

```text
Transaction

↓

Operation 1

↓

Operation 2

↓

Operation 3

↓

Failure
```

---

# InternalServerError

## Example

```text
InternalServerError
```

---

## Cause

A temporary AWS service-side issue.

---

## Best Practice

Retry using exponential backoff.

Never assume the first failure is permanent.

---

# RequestLimitExceeded

## Example

```text
RequestLimitExceeded
```

---

## Cause

AWS account-level request limits have been exceeded.

---

## Resolution

- Reduce request rate.
- Request a quota increase.
- Review workload patterns.

---

# Networking Issues

Possible causes:

- VPC endpoint misconfiguration
- Firewall rules
- Proxy issues
- DNS failures

Useful commands:

```bash
aws dynamodb list-tables --debug
```

---

# Debugging Checklist

```text
Application

↓

Logs

↓

AWS CLI

↓

describe-table

↓

CloudWatch Metrics

↓

CloudTrail

↓

Root Cause
```

---

# Common Production Scenario

## Problem

A deployment fails immediately after release.

---

## Investigation

Check:

1. Table exists.
2. Table status is ACTIVE.
3. IAM permissions.
4. Region.
5. Environment variables.
6. CloudWatch logs.
7. Application configuration.

---

# Error Summary

| Error | Typical Cause | Resolution |
|--------|---------------|------------|
| ResourceNotFoundException | Wrong table or region | Verify resource |
| AccessDeniedException | IAM permissions | Update IAM policy |
| ValidationException | Invalid request | Fix request payload |
| ProvisionedThroughputExceededException | Capacity exceeded | Scale or redesign |
| ConditionalCheckFailedException | Failed condition | Handle expected conflict |
| TransactionCanceledException | Transaction failure | Review transaction |
| InternalServerError | Temporary AWS issue | Retry |
| RequestLimitExceeded | AWS quota exceeded | Reduce requests or request quota |

---

# Performance Considerations

- Use exponential backoff for retryable errors.
- Monitor throttling through CloudWatch.
- Avoid hot partitions.
- Design tables around access patterns.
- Log request IDs for faster AWS Support investigations.

---

# Best Practices

- Treat retryable and non-retryable errors differently.
- Log complete exception details.
- Monitor CloudWatch metrics continuously.
- Validate configuration during deployment.
- Use structured logging.
- Test failure scenarios regularly.

---

# Common Mistakes

## Retrying Every Error

Not every exception should be retried.

Examples:

- ValidationException ❌
- AccessDeniedException ❌

Retry only transient failures such as throttling or temporary service errors.

---

## Ignoring CloudWatch

Application logs alone rarely tell the complete story.

Always correlate:

- Application logs
- CloudWatch metrics
- CloudTrail events
- DynamoDB configuration

---

## Ignoring Hot Partitions

Increasing capacity does not always solve throttling if requests are concentrated on a single partition key.

---

# Interview Notes

### Why does `ProvisionedThroughputExceededException` occur?

It occurs when read or write requests exceed the configured provisioned capacity or when traffic is unevenly distributed across partitions.

---

### What causes `ValidationException`?

Invalid requests such as missing keys, incorrect attribute types, malformed expressions, or invalid JSON.

---

### How would you troubleshoot `ResourceNotFoundException`?

Verify the table name, AWS Region, AWS account, deployment status, and ensure the table is in the `ACTIVE` state.

---

### Which errors are typically retryable?

Retryable errors generally include temporary service failures (`InternalServerError`) and throttling-related exceptions. Validation and permission errors should be fixed rather than retried.

---

# Key Takeaways

- Most DynamoDB production issues fall into a small set of well-understood exception types.
- Effective troubleshooting starts by identifying whether the problem is related to the application, configuration, permissions, capacity, or infrastructure.
- Combine application logs, CloudWatch metrics, CloudTrail events, and AWS CLI commands to diagnose issues efficiently.
- Designing for retries, monitoring, and proper error handling greatly improves the resilience of production systems.