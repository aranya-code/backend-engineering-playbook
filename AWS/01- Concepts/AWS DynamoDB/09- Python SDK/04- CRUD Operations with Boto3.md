# 04 - CRUD Operations with Boto3

## Overview

CRUD (Create, Read, Update, Delete) operations form the foundation of almost every backend application.

Using Boto3, developers can perform these operations against Amazon DynamoDB efficiently while taking advantage of features such as:

- Conditional writes
- Atomic updates
- Optimistic locking
- Return values
- Error handling
- Retry mechanisms

This chapter focuses on implementing production-ready CRUD operations using the **Boto3 Resource API**, which is the preferred approach for most Python backend applications.

---

# Learning Objectives

After completing this chapter, you'll understand:

- Creating items
- Reading items
- Updating items
- Deleting items
- Return values
- Conditional operations
- Error handling
- Performance optimization
- Production best practices
- Interview questions

---

# CRUD Architecture

```text
Application

↓

Repository

↓

Boto3 Resource

↓

DynamoDB Table
```

The repository layer encapsulates all database access.

---

# Sample Table

Throughout this chapter we'll use the following table.

```text
Orders

Partition Key

order_id
```

Example Item

```json
{
    "order_id": "ORD-1001",
    "customer": "John",
    "status": "Pending",
    "amount": 250,
    "city": "New York"
}
```

---

# Creating the Table Resource

```python
import boto3

dynamodb = boto3.resource("dynamodb")

table = dynamodb.Table("Orders")
```

Create the resource once and reuse it throughout the application.

---

# CREATE — PutItem

The simplest write operation.

```python
response = table.put_item(
    Item={
        "order_id": "ORD-1001",
        "customer": "John",
        "status": "Pending",
        "amount": 250
    }
)
```

Execution flow

```text
Application

↓

put_item()

↓

DynamoDB

↓

Store Item

↓

Success
```

---

# Understanding PutItem

`PutItem` performs one of two actions:

- Creates a new item
- Completely replaces an existing item

```text
Item Exists?

↓

YES

↓

Replace Entire Item
```

This behavior surprises many developers.

---

# Preventing Overwrites

To insert only if the item does not already exist:

```python
response = table.put_item(
    Item=item,
    ConditionExpression="attribute_not_exists(order_id)"
)
```

Execution

```text
Item Exists?

↓

YES

↓

ConditionalCheckFailedException
```

This is the recommended approach when creating new records.

---

# READ — GetItem

Retrieve one item using its primary key.

```python
response = table.get_item(
    Key={
        "order_id": "ORD-1001"
    }
)

item = response.get("Item")
```

Execution flow

```text
Application

↓

get_item()

↓

Partition Key

↓

Return Item
```

---

# Handling Missing Items

If no matching item exists:

```python
item = response.get("Item")
```

returns:

```python
None
```

Always check for missing records.

```python
if item is None:
    print("Order not found")
```

---

# Consistent Reads

By default:

```text
Eventually Consistent Read
```

Strong consistency:

```python
response = table.get_item(
    Key={
        "order_id": "ORD-1001"
    },
    ConsistentRead=True
)
```

Strong consistency increases read cost.

---

# UPDATE — UpdateItem

Update specific attributes without replacing the entire item.

```python
response = table.update_item(
    Key={
        "order_id": "ORD-1001"
    },
    UpdateExpression="SET #s = :status",
    ExpressionAttributeNames={
        "#s": "status"
    },
    ExpressionAttributeValues={
        ":status": "Completed"
    }
)
```

Execution

```text
Find Item

↓

Modify Attribute

↓

Save Changes
```

---

# Updating Multiple Fields

```python
UpdateExpression="""
SET #s=:status,
    amount=:amount,
    city=:city
"""
```

Multiple attributes can be updated atomically.

---

# Incrementing Values

Counters are common in production.

```python
table.update_item(
    Key={
        "order_id": "ORD-1001"
    },
    UpdateExpression="ADD retry_count :value",
    ExpressionAttributeValues={
        ":value": 1
    }
)
```

Execution

```text
Current Value

↓

+1

↓

Store New Value
```

No race conditions occur.

---

# DELETE — DeleteItem

Delete an item.

```python
table.delete_item(
    Key={
        "order_id": "ORD-1001"
    }
)
```

Execution

```text
Find Item

↓

Delete

↓

Success
```

---

# Conditional Delete

Delete only if status is Pending.

```python
table.delete_item(
    Key={
        "order_id": "ORD-1001"
    },
    ConditionExpression="#s = :status",
    ExpressionAttributeNames={
        "#s": "status"
    },
    ExpressionAttributeValues={
        ":status": "Pending"
    }
)
```

Useful for preventing accidental deletion.

---

# Return Values

Update operations can return modified attributes.

```python
response = table.update_item(
    ...
    ReturnValues="ALL_NEW"
)
```

Options

| Return Value | Description |
|--------------|-------------|
| NONE | Default |
| ALL_NEW | Updated item |
| UPDATED_NEW | Only updated attributes |
| ALL_OLD | Previous item |
| UPDATED_OLD | Old updated attributes |

---

# Reserved Keywords

Some attribute names are reserved.

Incorrect

```python
UpdateExpression="SET status=:s"
```

Preferred

```python
ExpressionAttributeNames={
    "#s":"status"
}
```

Always use aliases for reserved words.

---

# Error Handling

```python
from botocore.exceptions import ClientError

try:
    table.put_item(...)
except ClientError as e:
    print(e.response["Error"]["Code"])
```

Common exceptions

- ConditionalCheckFailedException
- ResourceNotFoundException
- ValidationException
- ProvisionedThroughputExceededException

---

# Repository Pattern

Production applications should isolate CRUD operations.

```python
class OrderRepository:

    def __init__(self, table):
        self.table = table

    def get_order(self, order_id):
        return self.table.get_item(
            Key={
                "order_id": order_id
            }
        ).get("Item")
```

Architecture

```text
FastAPI

↓

Service Layer

↓

Repository

↓

Boto3
```

---

# Performance Considerations

Avoid

```text
100

↓

get_item()

↓

100 Requests
```

Better

```text
BatchGetItem
```

Similarly

Avoid

```text
Repeated Updates
```

When possible

```text
BatchWriteItem
```

---

# Production Architecture

```text
                Client

                   │

                   ▼

             API Gateway

                   │

                   ▼

               FastAPI

                   │

                   ▼

            Service Layer

                   │

                   ▼

         Repository Pattern

                   │

                   ▼

            Boto3 Resource

                   │

                   ▼

              DynamoDB
```

---

# Security Best Practices

- Use IAM Roles.
- Validate all incoming data.
- Use conditional writes.
- Never trust client input.
- Encrypt DynamoDB tables.
- Apply least-privilege IAM policies.
- Log failures without exposing sensitive information.

---

# Best Practices

- Reuse Boto3 resources.
- Use conditional writes during creation.
- Update only required attributes.
- Prefer UpdateItem over replacing entire items.
- Handle missing items gracefully.
- Catch expected exceptions.
- Keep CRUD logic inside repositories.
- Use strong consistency only when necessary.

---

# Common Mistakes

## Replacing Entire Items

Poor

```python
put_item()
```

when only one field changed.

Better

```python
update_item()
```

---

## Ignoring Missing Items

Never assume

```python
response["Item"]
```

always exists.

Use

```python
response.get("Item")
```

---

## Creating Boto3 Resources Per Request

Poor

```python
def get_order():
    table = boto3.resource(...)
```

Better

Create once during application startup.

---

## No Conditional Writes

Without conditions:

```text
Request A

↓

Overwrite

↓

Request B

↓

Overwrite
```

Data may be lost.

---

# Interview Notes

A common interview question is:

> **What is the difference between PutItem and UpdateItem?**

`PutItem` creates a new item or completely replaces an existing one. `UpdateItem` modifies only the specified attributes while leaving the rest of the item unchanged.

---

Another common question is:

> **How do you prevent duplicate records in DynamoDB?**

Use a `ConditionExpression` such as `attribute_not_exists(partition_key)` during `PutItem`. If the item already exists, DynamoDB throws a `ConditionalCheckFailedException`.

---

Another common question is:

> **Why should CRUD operations be placed inside a Repository layer?**

The Repository pattern isolates database access from business logic, improving maintainability, testability, and allowing the storage implementation to evolve independently.

---

Another common question is:

> **When would you use a strongly consistent read?**

Use a strongly consistent read only when the application must immediately observe the latest committed write, such as during financial transactions or critical state validation. Otherwise, eventually consistent reads are more cost-effective.

---

# Key Takeaways

- `PutItem`, `GetItem`, `UpdateItem`, and `DeleteItem` form the core DynamoDB CRUD API.
- `UpdateItem` is generally preferred over replacing entire items because it updates only the required attributes.
- Conditional expressions help prevent accidental overwrites and enforce business rules.
- Encapsulate CRUD logic in a Repository layer for clean, maintainable application architecture.
- Reuse Boto3 resources, handle exceptions properly, and follow least-privilege IAM practices to build production-ready DynamoDB applications.