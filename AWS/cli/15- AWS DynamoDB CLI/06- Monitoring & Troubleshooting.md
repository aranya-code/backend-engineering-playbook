# 06 - Monitoring & Troubleshooting

## Overview

Monitoring and troubleshooting are essential for operating DynamoDB in production. While the AWS Management Console provides visual dashboards, the AWS CLI enables engineers to quickly inspect table health, identify bottlenecks, verify configurations, and automate operational diagnostics.

Production incidents often involve questions such as:

- Is the table healthy?
- Why are requests being throttled?
- Is Point-in-Time Recovery enabled?
- Is TTL working?
- Are Streams enabled?
- Is the table in the correct billing mode?
- Are indexes active?
- Are there service limits being reached?

The AWS CLI allows engineers to answer these questions in seconds.

---

# Learning Objectives

After completing this chapter, you'll understand:

- Inspecting table metadata
- Checking table health
- Monitoring capacity
- Verifying TTL
- Checking Streams
- Viewing backups
- Understanding throttling
- Using debug mode
- Production troubleshooting workflows
- Best practices

---

# Monitoring Architecture

```text
           Application

                 │

                 ▼

          Amazon DynamoDB

                 │

      ┌──────────┼──────────┐

      ▼          ▼          ▼

 CloudWatch   CloudTrail   AWS CLI

                 │

                 ▼

         Operations Team
```

---

# Listing Tables

View available tables.

```bash
aws dynamodb list-tables
```

Example:

```json
{
    "TableNames": [
        "Orders",
        "Customers",
        "Products"
    ]
}
```

Useful for:

- Verifying deployments
- Checking environments
- Confirming table existence

---

# Describing a Table

The most useful troubleshooting command.

```bash
aws dynamodb describe-table \
    --table-name Orders
```

Information returned includes:

- Table Status
- Billing Mode
- Item Count
- Table Size
- Key Schema
- GSIs
- LSIs
- Stream Status
- Encryption
- Capacity

---

# Table Status

Important field:

```json
{
    "TableStatus": "ACTIVE"
}
```

Possible values:

| Status | Meaning |
|---------|----------|
| CREATING | Table is being created |
| ACTIVE | Available |
| UPDATING | Configuration change in progress |
| DELETING | Being removed |

Production applications should only use tables in the **ACTIVE** state.

---

# Checking Billing Mode

Example:

```bash
aws dynamodb describe-table \
    --table-name Orders \
    --query "Table.BillingModeSummary"
```

Possible modes:

```text
PAY_PER_REQUEST

PROVISIONED
```

Useful during:

- Cost analysis
- Performance tuning
- Capacity planning

---

# Viewing Provisioned Capacity

```bash
aws dynamodb describe-table \
    --table-name Orders \
    --query "Table.ProvisionedThroughput"
```

Example:

```json
{
    "ReadCapacityUnits": 50,
    "WriteCapacityUnits": 20
}
```

---

# Checking Global Secondary Indexes

```bash
aws dynamodb describe-table \
    --table-name Orders \
    --query "Table.GlobalSecondaryIndexes"
```

Useful for verifying:

- Deployment
- Index creation
- Index status

---

# Monitoring Index Status

Example response:

```text
IndexStatus

↓

ACTIVE
```

Other possible states:

```text
CREATING

UPDATING

DELETING
```

---

# Viewing Item Count

```bash
aws dynamodb describe-table \
    --table-name Orders \
    --query "Table.ItemCount"
```

Useful for:

- Migration validation
- Data verification
- Capacity estimation

---

# Checking Table Size

```bash
aws dynamodb describe-table \
    --table-name Orders \
    --query "Table.TableSizeBytes"
```

Helpful when planning:

- Capacity
- Migration
- Backup
- Cost optimization

---

# Checking Time To Live

Verify TTL.

```bash
aws dynamodb describe-time-to-live \
    --table-name Orders
```

Example:

```json
{
    "TimeToLiveDescription": {
        "TimeToLiveStatus": "ENABLED"
    }
}
```

Possible values:

```text
ENABLED

DISABLED

ENABLING

DISABLING
```

---

# Checking Streams

```bash
aws dynamodb describe-table \
    --table-name Orders \
    --query "Table.StreamSpecification"
```

Verify:

- Streams enabled
- Stream view type

---

# Checking Stream ARN

```bash
aws dynamodb describe-table \
    --table-name Orders \
    --query "Table.LatestStreamArn"
```

Useful for:

- Lambda triggers
- Event processing
- Stream debugging

---

# Viewing Backup Status

```bash
aws dynamodb list-backups \
    --table-name Orders
```

Useful before:

- Upgrades
- Maintenance
- Disaster recovery

---

# Checking PITR

```bash
aws dynamodb describe-continuous-backups \
    --table-name Orders
```

Look for:

```text
PointInTimeRecoveryStatus

↓

ENABLED
```

---

# Service Limits

View account limits.

```bash
aws dynamodb describe-limits
```

Example response:

```json
{
    "AccountMaxReadCapacityUnits": 80000,
    "AccountMaxWriteCapacityUnits": 80000
}
```

Useful during:

- Capacity planning
- Scaling
- Quota troubleshooting

---

# Debug Mode

Every CLI command supports:

```bash
--debug
```

Example:

```bash
aws dynamodb get-item \
    --table-name Orders \
    --key file://key.json \
    --debug
```

Debug output includes:

- HTTP request
- HTTP response
- Retry attempts
- Authentication
- Request signing

---

# Common Error Messages

## Resource Not Found

```text
ResourceNotFoundException
```

Possible causes:

- Wrong table name
- Wrong region
- Wrong AWS account

---

## Access Denied

```text
AccessDeniedException
```

Possible causes:

- Missing IAM permissions
- Incorrect role
- Wrong profile

---

## Validation Exception

```text
ValidationException
```

Usually caused by:

- Missing partition key
- Invalid attribute type
- Invalid expression
- Incorrect JSON

---

## Provisioned Throughput Exceeded

```text
ProvisionedThroughputExceededException
```

Possible causes:

- Insufficient RCUs
- Insufficient WCUs
- Hot partition
- Traffic spike

Possible solutions:

- Increase capacity
- Use Auto Scaling
- Improve partition key distribution
- Switch to On-Demand mode

---

# Troubleshooting Workflow

```text
Application Error

       │

       ▼

AWS CLI

       │

       ▼

Describe Table

       │

       ▼

Verify Status

       │

       ▼

Inspect Configuration

       │

       ▼

Identify Root Cause
```

---

# Monitoring with CloudWatch

Although the CLI cannot replace CloudWatch dashboards, it complements them.

Important metrics include:

- ConsumedReadCapacityUnits
- ConsumedWriteCapacityUnits
- ReadThrottleEvents
- WriteThrottleEvents
- SuccessfulRequestLatency
- SystemErrors
- UserErrors

Typical workflow:

```text
CloudWatch Alert

↓

AWS CLI

↓

Investigate Table

↓

Fix Issue
```

---

# Production Troubleshooting Scenario

Problem:

```text
API Response Time Increased
```

Checklist:

```text
Describe Table

↓

Billing Mode

↓

Capacity

↓

Throttle Events

↓

CloudWatch Metrics

↓

Indexes

↓

Application Logs
```

---

# CLI Health Check Script

Typical automation:

```bash
aws dynamodb describe-table \
    --table-name Orders \
    --query "Table.TableStatus"
```

Expected output:

```text
ACTIVE
```

Can be integrated into:

- GitHub Actions
- Jenkins
- Cron Jobs
- AWS Systems Manager

---

# Production Architecture

```text
CloudWatch Alarm

        │

        ▼

Operations Engineer

        │

        ▼

AWS CLI

        │

        ▼

Describe Table

        │

        ▼

Identify Issue

        │

        ▼

Corrective Action
```

---

# Performance Considerations

- Avoid repeatedly calling `describe-table` in tight loops.
- Use JMESPath (`--query`) to retrieve only required fields.
- Monitor capacity before increasing provisioned throughput.
- Use CloudWatch for continuous monitoring and the CLI for investigation.
- Automate health checks for critical production tables.

---

# Security Best Practices

- Restrict monitoring permissions using IAM.
- Use read-only IAM roles for operations teams.
- Enable CloudTrail for auditing configuration changes.
- Avoid using administrator credentials for routine monitoring.
- Log all automated diagnostic scripts.

---

# Best Practices

- Verify table status before deployments.
- Regularly confirm PITR and TTL are enabled.
- Monitor GSI status after deployments.
- Investigate throttling immediately.
- Automate health checks.
- Use CloudWatch alarms with CLI-based runbooks.

---

# Common Mistakes

## Ignoring Table Status

Running application workloads against a table that is still **CREATING** or **UPDATING** can cause failures.

---

## Assuming TTL Deletes Items Immediately

TTL deletion is asynchronous. Expired items may remain for some time before being removed.

---

## Ignoring Throttling

Throttling indicates a capacity or data distribution problem that should be investigated rather than ignored.

---

## Troubleshooting Only Through the Console

The CLI provides faster, scriptable diagnostics and is better suited for production operations and automation.

---

# Interview Notes

A common interview question is:

> **How do you verify that a DynamoDB table is healthy using the AWS CLI?**

Use `describe-table` to check the table status, billing mode, indexes, item count, and capacity configuration. Combine this with CloudWatch metrics to identify performance or throttling issues.

---

Another common question is:

> **How do you determine if TTL is enabled?**

Use:

```bash
aws dynamodb describe-time-to-live \
    --table-name Orders
```

and verify that `TimeToLiveStatus` is `ENABLED`.

---

Another common question is:

> **What causes `ProvisionedThroughputExceededException`?**

This occurs when read or write requests exceed the configured provisioned capacity or when traffic is concentrated on a hot partition.

---

Another common question is:

> **Why is `--debug` useful?**

It exposes the complete request lifecycle, including authentication, request signing, retries, HTTP requests, and responses, making it invaluable for diagnosing CLI and API issues.

---

# Key Takeaways

- The AWS CLI is an excellent tool for monitoring and troubleshooting DynamoDB in production.
- `describe-table` is the primary command for inspecting table configuration and health.
- CloudWatch provides continuous monitoring, while the CLI enables rapid investigation and validation.
- Common operational checks include verifying table status, billing mode, TTL, Streams, backups, and capacity settings.
- Combining CloudWatch alerts with CLI-based diagnostics creates an efficient and repeatable operational workflow.