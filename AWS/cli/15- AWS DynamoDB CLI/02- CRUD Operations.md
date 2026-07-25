# 02 - CRUD Operations

## Overview

CRUD (Create, Read, Update, Delete) operations form the foundation of every DynamoDB application.

Although application code usually performs these operations through the AWS SDK (such as Boto3), the AWS CLI is invaluable for:

- Testing APIs
- Verifying production data
- Debugging issues
- Running maintenance scripts
- Performing administrative tasks
- Learning DynamoDB behavior

This chapter explores every major CRUD operation using the AWS CLI with production-ready examples.

---

# Learning Objectives

After completing this chapter, you'll understand:

- Creating items
- Reading items
- Updating items
- Deleting items
- Batch operations
- Conditional writes
- Return values
- JSON input files
- Production CLI workflows
- Best practices

---

# CRUD Architecture

```text
Developer

      │

      ▼

AWS CLI

      │

      ▼

DynamoDB API

      │

      ▼

Amazon DynamoDB
```

Every CLI command maps directly to a DynamoDB API call.

---

# Sample Table

Throughout this chapter we'll use:

```text
Orders
```

Partition Key:

```text
order_id
```

---

# Creating an Item

Basic syntax:

```bash
aws dynamodb put-item \
    --table-name Orders \
    --item file://order.json
```

---

# JSON Input File

Example:

```json
{
    "order_id": {
        "S": "ORD-1001"
    },
    "customer_id": {
        "S": "C100"
    },
    "status": {
        "S": "PENDING"
    },
    "amount": {
        "N": "499"
    }
}
```

Using JSON files keeps commands readable.

---

# Attribute Types

Common DynamoDB data types:

| Type | Meaning |
|------|----------|
| S | String |
| N | Number |
| BOOL | Boolean |
| NULL | Null |
| L | List |
| M | Map |
| SS | String Set |
| NS | Number Set |
| B | Binary |

Example:

```json
{
    "active": {
        "BOOL": true
    }
}
```

---

# Reading an Item

Retrieve a single item.

```bash
aws dynamodb get-item \
    --table-name Orders \
    --key \
'{
    "order_id":{
        "S":"ORD-1001"
    }
}'
```

Example response:

```json
{
    "Item": {
        "order_id": {
            "S": "ORD-1001"
        },
        "status": {
            "S": "PENDING"
        }
    }
}
```

---

# Consistent Reads

Eventually consistent (default):

```bash
aws dynamodb get-item \
    --table-name Orders \
    --key file://key.json
```

Strongly consistent:

```bash
aws dynamodb get-item \
    --table-name Orders \
    --key file://key.json \
    --consistent-read
```

---

# Updating an Item

Change one attribute.

```bash
aws dynamodb update-item \
    --table-name Orders \
    --key file://key.json \
    --update-expression \
        "SET #s = :status" \
    --expression-attribute-names \
        '{"#s":"status"}' \
    --expression-attribute-values \
        '{":status":{"S":"SHIPPED"}}'
```

---

# Update Expression Flow

```text
Existing Item

↓

UpdateExpression

↓

Modified Item
```

Only specified attributes are changed.

---

# Incrementing Numbers

Example:

```bash
aws dynamodb update-item \
    --table-name Orders \
    --key file://key.json \
    --update-expression \
        "SET retry_count = retry_count + :inc" \
    --expression-attribute-values \
        '{":inc":{"N":"1"}}'
```

Useful for:

- Retry counters
- Inventory
- View counts

---

# Removing Attributes

```bash
aws dynamodb update-item \
    --table-name Orders \
    --key file://key.json \
    --update-expression \
        "REMOVE notes"
```

Only the specified attribute is deleted.

---

# Deleting an Item

```bash
aws dynamodb delete-item \
    --table-name Orders \
    --key file://key.json
```

Execution:

```text
Item

↓

Delete

↓

Removed
```

---

# Conditional Writes

Prevent overwriting existing items.

```bash
aws dynamodb put-item \
    --table-name Orders \
    --item file://order.json \
    --condition-expression \
        "attribute_not_exists(order_id)"
```

Useful for:

- Idempotency
- Duplicate prevention
- Unique IDs

---

# Conditional Update

Example:

```bash
aws dynamodb update-item \
    --table-name Orders \
    --key file://key.json \
    --condition-expression \
        "#s = :pending" \
    --expression-attribute-names \
        '{"#s":"status"}' \
    --expression-attribute-values \
'{
":pending":{"S":"PENDING"},
":new":{"S":"SHIPPED"}
}' \
    --update-expression \
        "SET #s = :new"
```

Only updates if the order is still pending.

---

# Return Values

Return updated item:

```bash
--return-values ALL_NEW
```

Options:

| Value | Meaning |
|--------|----------|
| NONE | Default |
| ALL_NEW | Updated item |
| UPDATED_NEW | Updated attributes |
| ALL_OLD | Previous item |
| UPDATED_OLD | Previous updated attributes |

---

# Batch Writes

Example:

```bash
aws dynamodb batch-write-item \
    --request-items \
file://batch-write.json
```

Batch operations reduce network calls.

---

# Batch Reads

```bash
aws dynamodb batch-get-item \
    --request-items \
file://batch-get.json
```

Retrieve multiple items in a single request.

---

# Return Consumed Capacity

Useful for performance analysis.

```bash
--return-consumed-capacity TOTAL
```

Example:

```json
{
    "ConsumedCapacity": [
        {
            "CapacityUnits": 1
        }
    ]
}
```

---

# Return Item Collection Metrics

```bash
--return-item-collection-metrics SIZE
```

Useful when working with Local Secondary Indexes.

---

# Using Expression Attribute Names

Reserved keywords require aliases.

Instead of:

```text
status
```

Use:

```text
#status
```

Example:

```json
{
    "#status":"status"
}
```

---

# Using Expression Attribute Values

Instead of embedding values directly:

```text
SHIPPED
```

Use placeholders:

```text
:status
```

Example:

```json
{
    ":status":{
        "S":"SHIPPED"
    }
}
```

This improves readability and safety.

---

# Common CRUD Workflow

```text
Create

↓

Read

↓

Update

↓

Read

↓

Delete
```

Every operation can be verified immediately.

---

# Production Example

Deployment verification:

```text
Deploy

↓

Insert Test Item

↓

Read Item

↓

Update Item

↓

Delete Item

↓

Deployment Verified
```

Simple smoke tests often use CLI commands.

---

# CRUD Architecture in Production

```text
Automation Script

        │

        ▼

AWS CLI

        │

        ▼

DynamoDB

        │

        ▼

CloudWatch Logs
```

---

# Performance Considerations

- Use JSON files instead of inline JSON.
- Batch operations reduce API calls.
- Avoid unnecessary strongly consistent reads.
- Use conditional writes to prevent retries.
- Return only required attributes.

---

# Security Best Practices

- Never store credentials inside scripts.
- Use IAM Roles whenever possible.
- Use least-privilege IAM policies.
- Avoid running destructive commands against production accidentally.
- Validate JSON files before execution.

---

# Best Practices

- Store request payloads in version-controlled JSON files.
- Prefer batch operations for bulk processing.
- Use condition expressions for idempotency.
- Verify updates with return values.
- Keep CLI scripts reusable.
- Test commands in development first.

---

# Common Mistakes

## Inline JSON Everywhere

Poor:

```bash
aws dynamodb put-item --item '{...}'
```

Better:

```bash
--item file://order.json
```

---

## Forgetting Condition Expressions

Without:

```text
attribute_not_exists()
```

duplicate records may be inserted.

---

## Updating Reserved Keywords

Always use:

```text
ExpressionAttributeNames
```

when necessary.

---

## Running Delete Commands Without Verification

Before:

```bash
delete-item
```

verify:

- Profile
- Region
- Table
- Key

---

# Interview Notes

A common interview question is:

> **What is the difference between `put-item` and `update-item`?**

`put-item` creates a new item or completely replaces an existing item with the same key. `update-item` modifies only specified attributes without replacing the entire item.

---

Another common question is:

> **Why use condition expressions with `put-item`?**

Condition expressions prevent accidental overwrites and help implement idempotency, uniqueness, and optimistic concurrency.

---

Another common question is:

> **Why use `ExpressionAttributeNames`?**

They allow you to reference reserved keywords or special attribute names safely in expressions.

---

Another common question is:

> **When would you use `batch-write-item` instead of multiple `put-item` calls?**

`batch-write-item` reduces network overhead and improves efficiency when inserting or deleting many items, although it does not provide transactional guarantees.

---

# Key Takeaways

- The AWS CLI provides direct access to DynamoDB CRUD operations for administration, testing, and automation.
- Use JSON input files to simplify complex requests and improve maintainability.
- `put-item`, `get-item`, `update-item`, and `delete-item` are the core building blocks of DynamoDB interaction.
- Batch operations improve efficiency, while condition expressions help enforce business rules and prevent duplicate writes.
- Mastering CRUD operations through the CLI is valuable for debugging, scripting, CI/CD pipelines, and production support.