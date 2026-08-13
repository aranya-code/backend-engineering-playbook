# 04 - Table Management

## Overview

Managing DynamoDB tables is one of the most common operational tasks performed by backend engineers, cloud engineers, and DevOps teams.

Using the AWS CLI, you can:

- Create tables
- Delete tables
- Modify throughput
- Enable DynamoDB Streams
- Configure Time To Live (TTL)
- Manage Point-in-Time Recovery (PITR)
- Inspect table metadata
- Monitor table status

Unlike application CRUD operations, table management is typically performed during:

- Infrastructure provisioning
- CI/CD deployments
- Disaster recovery
- Capacity planning
- Maintenance windows

Understanding these commands is essential for production operations.

---

# Learning Objectives

After completing this chapter, you'll understand:

- Creating tables
- Describing tables
- Updating tables
- Deleting tables
- Billing modes
- Secondary indexes
- DynamoDB Streams
- Time To Live (TTL)
- Point-in-Time Recovery (PITR)
- Table lifecycle
- Production best practices

---

# Table Lifecycle

```text
Create

↓

CREATING

↓

ACTIVE

↓

Update

↓

ACTIVE

↓

Delete

↓

DELETING
```

---

# Listing Tables

View all tables in your account.

```bash
aws dynamodb list-tables
```

Example output:

```json
{
  "TableNames": [
    "Customers",
    "Orders",
    "Products"
  ]
}
```

---

# Creating a Table

Basic syntax:

```bash
aws dynamodb create-table \
    --table-name Orders \
    --attribute-definitions \
        AttributeName=order_id,AttributeType=S \
    --key-schema \
        AttributeName=order_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST
```

---

# Create Table Architecture

```text
CLI

↓

CreateTable API

↓

CREATING

↓

ACTIVE
```

The table cannot be used until its status becomes **ACTIVE**.

---

# Checking Table Status

```bash
aws dynamodb describe-table \
    --table-name Orders
```

Example response:

```json
{
    "Table": {
        "TableStatus": "ACTIVE"
    }
}
```

Possible statuses:

| Status | Meaning |
|----------|----------|
| CREATING | Table is being created |
| UPDATING | Table configuration is changing |
| ACTIVE | Ready for use |
| DELETING | Being removed |

---

# Waiting for Table Creation

Instead of polling manually:

```bash
aws dynamodb wait table-exists \
    --table-name Orders
```

Useful in CI/CD pipelines.

---

# Table Description

Retrieve metadata:

```bash
aws dynamodb describe-table \
    --table-name Orders
```

Includes:

- Item count
- Table ARN
- Billing mode
- Creation date
- Key schema
- Global Secondary Indexes
- Local Secondary Indexes
- Streams
- Encryption
- Capacity settings

---

# Billing Modes

Two billing modes are available.

## On-Demand

```bash
--billing-mode PAY_PER_REQUEST
```

Characteristics:

- No capacity planning
- Automatic scaling
- Pay per request
- Best for unpredictable workloads

---

## Provisioned

```bash
--billing-mode PROVISIONED
```

Requires:

```bash
--provisioned-throughput \
ReadCapacityUnits=10,\
WriteCapacityUnits=5
```

Best for:

- Stable traffic
- Cost optimization
- Predictable workloads

---

# Updating Provisioned Capacity

```bash
aws dynamodb update-table \
    --table-name Orders \
    --provisioned-throughput \
ReadCapacityUnits=20,\
WriteCapacityUnits=10
```

The table enters:

```text
UPDATING
```

before returning to:

```text
ACTIVE
```

---

# Switching Billing Modes

Provisioned →

On-Demand

```bash
aws dynamodb update-table \
    --table-name Orders \
    --billing-mode PAY_PER_REQUEST
```

On-Demand →

Provisioned

```bash
aws dynamodb update-table \
    --table-name Orders \
    --billing-mode PROVISIONED \
    --provisioned-throughput \
ReadCapacityUnits=50,\
WriteCapacityUnits=20
```

---

# Creating a Global Secondary Index

Example:

```bash
aws dynamodb update-table \
    --table-name Orders \
    --attribute-definitions \
AttributeName=status,AttributeType=S \
    --global-secondary-index-updates \
file://gsi.json
```

The table remains available while the GSI is built.

---

# Viewing Indexes

```bash
aws dynamodb describe-table \
    --table-name Orders
```

Returns:

```text
GlobalSecondaryIndexes

LocalSecondaryIndexes
```

Useful when verifying deployments.

---

# Enabling DynamoDB Streams

```bash
aws dynamodb update-table \
    --table-name Orders \
    --stream-specification \
StreamEnabled=true,StreamViewType=NEW_AND_OLD_IMAGES
```

Available stream types:

| Type | Description |
|------|-------------|
| KEYS_ONLY | Primary keys only |
| NEW_IMAGE | New item |
| OLD_IMAGE | Old item |
| NEW_AND_OLD_IMAGES | Both versions |

---

# Viewing Stream Configuration

```bash
aws dynamodb describe-table \
    --table-name Orders
```

Look for:

```text
LatestStreamArn

StreamSpecification
```

---

# Enabling Time To Live (TTL)

TTL automatically removes expired items.

Example:

```bash
aws dynamodb update-time-to-live \
    --table-name Orders \
    --time-to-live-specification \
Enabled=true,AttributeName=expires_at
```

---

# TTL Workflow

```text
Item

↓

Expiration Timestamp

↓

TTL Process

↓

Automatic Deletion
```

Ideal for:

- Sessions
- OTPs
- Cache entries
- Temporary tokens

---

# Viewing TTL Status

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

---

# Enabling Point-in-Time Recovery

```bash
aws dynamodb update-continuous-backups \
    --table-name Orders \
    --point-in-time-recovery-specification \
PointInTimeRecoveryEnabled=true
```

Benefits:

- Recover accidental deletes
- Recover corrupted data
- Restore to any second within retention period

---

# Viewing PITR Status

```bash
aws dynamodb describe-continuous-backups \
    --table-name Orders
```

---

# Table Deletion

Delete a table.

```bash
aws dynamodb delete-table \
    --table-name Orders
```

Lifecycle:

```text
ACTIVE

↓

DELETING

↓

Removed
```

This operation is irreversible unless backups exist.

---

# Waiting for Table Deletion

Useful in automation:

```bash
aws dynamodb wait table-not-exists \
    --table-name Orders
```

---

# Table Management Workflow

```text
Create Table

↓

Wait Until ACTIVE

↓

Enable TTL

↓

Enable Streams

↓

Enable PITR

↓

Deploy Application
```

This is a common production provisioning sequence.

---

# Production Architecture

```text
Infrastructure Code

        │

        ▼

AWS CLI

        │

        ▼

Create / Update Table

        │

        ▼

Amazon DynamoDB

        │

        ▼

Application Deployment
```

---

# CI/CD Example

```text
GitHub Actions

↓

AWS CLI

↓

Create Table

↓

Wait

↓

Enable TTL

↓

Enable PITR

↓

Deploy Backend
```

---

# Performance Considerations

- Use On-Demand billing for unpredictable workloads.
- Use Provisioned billing for stable, high-volume traffic.
- Avoid frequent capacity changes.
- Enable TTL for temporary data.
- Monitor GSI creation before deploying dependent services.

---

# Security Best Practices

- Restrict table management permissions with IAM.
- Enable server-side encryption.
- Enable Point-in-Time Recovery for production tables.
- Log all table management operations using CloudTrail.
- Avoid using administrator credentials in automation scripts.

---

# Best Practices

- Always wait for a table to become ACTIVE before using it.
- Enable PITR on production tables.
- Configure TTL for expiring data.
- Use Infrastructure as Code for repeatable table creation.
- Verify table configuration after deployment.
- Review billing mode based on workload patterns.

---

# Common Mistakes

## Using a Table Before It Is ACTIVE

Immediately performing CRUD operations after `create-table` can fail.

Use:

```bash
aws dynamodb wait table-exists \
    --table-name Orders
```

---

## Forgetting Point-in-Time Recovery

Without PITR, accidental deletions or updates may be unrecoverable.

---

## Enabling Provisioned Capacity Without Monitoring

Provisioned mode requires ongoing monitoring of read and write capacity to avoid throttling.

---

## Deleting Production Tables Accidentally

Always verify:

- AWS Profile
- Region
- Table name

before running:

```bash
delete-table
```

---

# Interview Notes

A common interview question is:

> **What is the difference between On-Demand and Provisioned billing modes?**

On-Demand automatically scales and charges per request, making it ideal for unpredictable workloads. Provisioned mode requires predefined read and write capacity units and is better suited for stable, predictable traffic where costs can be optimized.

---

Another common question is:

> **Why enable Point-in-Time Recovery (PITR)?**

PITR allows you to restore a DynamoDB table to any second within the retention window, protecting against accidental deletions, overwrites, or data corruption.

---

Another common question is:

> **What is the purpose of Time To Live (TTL)?**

TTL automatically deletes expired items based on a timestamp attribute, making it useful for temporary data such as sessions, cache entries, OTPs, and tokens.

---

Another common question is:

> **Why should automation use `aws dynamodb wait table-exists`?**

Because table creation is asynchronous. Waiting ensures the table reaches the `ACTIVE` state before subsequent operations such as inserting data or creating indexes.

---

# Key Takeaways

- The AWS CLI provides complete control over DynamoDB table lifecycle management.
- Table creation, updates, and deletion are asynchronous operations that should be coordinated using wait commands.
- On-Demand and Provisioned billing modes address different workload patterns and cost considerations.
- Production tables should typically enable DynamoDB Streams, TTL, and Point-in-Time Recovery.
- Effective table management is a critical skill for backend engineers responsible for deploying, maintaining, and troubleshooting DynamoDB in production environments.