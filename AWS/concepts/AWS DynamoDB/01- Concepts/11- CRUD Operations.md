# 11 - CRUD Operations (PutItem, GetItem, UpdateItem, DeleteItem)

## Overview

At its core, every application performs four fundamental operations on data:

- Create
- Read
- Update
- Delete

Collectively, these are known as **CRUD operations**.

Although DynamoDB provides many advanced capabilities—such as Streams, Transactions, Global Tables, and Secondary Indexes—almost every application is built upon these four basic operations.

Unlike SQL databases, however, DynamoDB operations are designed around **items**, not rows and columns.

Each operation works directly against the **Primary Key**, allowing DynamoDB to locate the required partition without scanning the table.

Understanding how these operations work internally is essential for writing efficient, scalable, and cost-effective applications.

---

# CRUD in DynamoDB

| CRUD | DynamoDB API | Purpose |
|-------|--------------|---------|
| Create | PutItem | Creates a new item or replaces an existing one |
| Read | GetItem | Retrieves a single item |
| Update | UpdateItem | Modifies specific attributes |
| Delete | DeleteItem | Removes an item |

Unlike SQL, there is no separate **INSERT** and **REPLACE** statement.

The behavior depends on the API being used and whether conditions are specified.

---

# Internal Request Lifecycle

Every CRUD request follows roughly the same path.

```text
Application

      │

      ▼

AWS SDK (Boto3)

      │

      ▼

DynamoDB API

      │

      ▼

Partition Key Hash

      │

      ▼

Physical Partition

      │

      ▼

Execute Operation

      │

      ▼

Response
```

Notice that DynamoDB never searches every partition.

The Partition Key immediately identifies the correct storage node.

---

# PutItem

`PutItem` creates a new item.

Example

```json
{
    "UserId": "USER#1001",
    "Name": "Alice",
    "Country": "USA"
}
```

Python (Boto3)

```python
table.put_item(
    Item={
        "UserId": "USER#1001",
        "Name": "Alice",
        "Country": "USA"
    }
)
```

---

# Important Behavior of PutItem

One of the biggest surprises for SQL developers is this:

If the item already exists,

**PutItem replaces the entire item.**

Suppose the existing item is

```json
{
    "UserId":"USER#1001",
    "Name":"Alice",
    "Age":30
}
```

You execute

```json
{
    "UserId":"USER#1001",
    "Name":"Bob"
}
```

The result becomes

```json
{
    "UserId":"USER#1001",
    "Name":"Bob"
}
```

The **Age** attribute disappears.

This is because PutItem writes a completely new item rather than modifying individual fields.

---

# When to Use PutItem

Good use cases include:

- Creating new users
- Importing data
- ETL pipelines
- Initial object creation

Avoid using PutItem when only a few attributes need updating.

---

# GetItem

GetItem retrieves a single item using its Primary Key.

```python
response = table.get_item(
    Key={
        "UserId":"USER#1001"
    }
)
```

Internally:

```text
Primary Key

↓

Hash

↓

Correct Partition

↓

Return Item
```

This is one of the fastest operations in DynamoDB.

---

# Why GetItem is Efficient

Unlike SQL,

```sql
SELECT *
FROM Users
WHERE UserId = 1001;
```

which may require index traversal,

DynamoDB already knows exactly where the item lives.

No scanning is required.

Latency is typically measured in single-digit milliseconds.

---

# UpdateItem

UpdateItem modifies selected attributes.

Example

Current item

```json
{
    "UserId":"USER#1001",
    "Name":"Alice",
    "Age":30
}
```

Update

```python
table.update_item(
    Key={
        "UserId":"USER#1001"
    },
    UpdateExpression="SET Age = :age",
    ExpressionAttributeValues={
        ":age":31
    }
)
```

Result

```json
{
    "UserId":"USER#1001",
    "Name":"Alice",
    "Age":31
}
```

Notice that only one attribute changes.

Everything else remains unchanged.

---

# Update Expressions

UpdateItem uses a special language called **Update Expressions**.

Common operations include:

Set a value

```text
SET Price = :p
```

Increment

```text
SET Counter = Counter + :one
```

Remove an attribute

```text
REMOVE Address
```

Append to a list

```text
SET Skills = list_append(Skills, :newSkill)
```

These expressions allow updates without rewriting the entire item.

---

# Atomic Counters

One of DynamoDB's most useful features is atomic updates.

Example

```python
UpdateExpression="SET Views = Views + :inc"
```

Suppose two users access a page simultaneously.

Without atomic updates:

```text
Current Views

100

↓

Thread A Reads

100

↓

Thread B Reads

100

↓

Both Write

101
```

Correct value should be

```text
102
```

Atomic updates ensure increments occur safely even under heavy concurrency.

This is commonly used for:

- Page views
- Likes
- Inventory
- Download counts

---

# DeleteItem

DeleteItem removes an item completely.

```python
table.delete_item(
    Key={
        "UserId":"USER#1001"
    }
)
```

After deletion,

```text
GetItem

↓

Item Not Found
```

Deletion permanently removes the item unless:

- Point-in-Time Recovery (PITR)
- AWS Backup
- Export backups

are available.

---

# Conditional Operations

One of DynamoDB's strongest features is **Conditional Writes**.

Example

```text
Create User

Only If

User Doesn't Already Exist
```

Condition

```python
ConditionExpression="attribute_not_exists(UserId)"
```

If the item already exists,

DynamoDB rejects the request.

This prevents accidental overwrites.

---

# Preventing Duplicate Users

Example

```python
table.put_item(
    Item=item,
    ConditionExpression="attribute_not_exists(UserId)"
)
```

Instead of:

```text
Overwrite Existing User
```

the operation fails with:

```text
ConditionalCheckFailedException
```

Applications can safely retry without creating duplicates.

---

# Optimistic Locking

Imagine two administrators editing the same profile.

Current Version

```text
Version = 5
```

Admin A updates.

Version becomes

```text
6
```

Admin B still thinks

```text
Version = 5
```

Instead of overwriting Admin A's changes,

a condition verifies

```text
Version == 5
```

If not,

the update fails.

This technique is called **Optimistic Locking**.

It prevents lost updates in distributed systems.

---

# Return Values

CRUD operations can return useful information.

Options include:

```text
NONE

ALL_OLD

UPDATED_NEW

UPDATED_OLD

ALL_NEW
```

Example

```python
ReturnValues="ALL_NEW"
```

Response

```json
{
    "Age":31,
    "Name":"Alice"
}
```

This avoids performing another GetItem after an update.

---

# Error Handling

Common exceptions include:

## ResourceNotFoundException

The table does not exist.

---

## ConditionalCheckFailedException

A condition expression evaluated to false.

---

## ValidationException

Invalid request format.

Examples:

- Missing partition key
- Wrong data type
- Invalid expression

---

## ProvisionedThroughputExceededException

The request exceeds available throughput.

Applications should retry using exponential backoff.

---

# Retry Strategy

Transient failures are expected in distributed systems.

A typical retry strategy is:

```text
Request

↓

Failure

↓

Wait 100 ms

↓

Retry

↓

Failure

↓

Wait 200 ms

↓

Retry

↓

Wait 400 ms

↓

Retry
```

This technique is called **Exponential Backoff**.

It prevents large numbers of clients from retrying simultaneously and overwhelming the service.

---

# Best Practices

- Use GetItem whenever the Primary Key is known.
- Prefer UpdateItem over PutItem for partial updates.
- Use conditional writes to avoid accidental overwrites.
- Use atomic counters instead of read-modify-write logic.
- Implement exponential backoff for retryable failures.
- Return only the data your application needs.

---

# Common Mistakes

## Using PutItem for Updates

Many beginners overwrite entire items accidentally.

Use UpdateItem when modifying only a few attributes.

---

## Ignoring Conditional Writes

Without conditions, concurrent requests may overwrite each other.

---

## Reading Before Every Update

Pattern:

```text
GetItem

↓

Modify

↓

PutItem
```

This increases latency and introduces race conditions.

Instead:

```text
UpdateItem

↓

Atomic Update
```

---

## Retrying Immediately

Immediate retries can amplify throttling during traffic spikes.

Always implement exponential backoff with jitter.

---

# Interview Notes

A common interview question is:

> **Why is UpdateItem generally preferred over PutItem for modifying existing data?**

Because `UpdateItem` changes only the specified attributes while preserving the rest of the item. `PutItem` replaces the entire item, which can unintentionally remove attributes that were not included in the request.

Another common question is:

> **How does DynamoDB prevent two clients from overwriting each other's changes?**

By using **Condition Expressions** and **Optimistic Locking**. A client includes a condition (for example, checking a version number), and DynamoDB performs the update only if the condition is still true.

---

# Key Takeaways

- CRUD operations are the foundation of all DynamoDB applications.
- `PutItem` creates or completely replaces an item.
- `GetItem` is the fastest way to retrieve a single item using its primary key.
- `UpdateItem` performs partial, atomic updates without rewriting the entire item.
- `DeleteItem` permanently removes an item.
- Condition Expressions enable safe concurrent writes and prevent accidental overwrites.
- Atomic counters eliminate race conditions for increment operations.
- Proper retry strategies with exponential backoff are essential in production systems.