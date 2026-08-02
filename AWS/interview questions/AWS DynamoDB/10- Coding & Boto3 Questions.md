# 10 - Coding & Boto3 Questions

## Overview

Senior backend interviews rarely stop at theoretical questions. Many companies—including Amazon, Microsoft, Walmart, Adobe, Atlassian, Goldman Sachs, and numerous startups—expect candidates to write production-quality code using the AWS SDK.

This chapter focuses on the most common DynamoDB coding interview questions using **Python** and **Boto3**.

The emphasis is not on memorizing SDK methods but on writing clean, production-ready code with proper error handling and scalability considerations.

---

# Learning Objectives

After completing this chapter, you'll be able to answer coding questions involving:

- GetItem
- PutItem
- UpdateItem
- DeleteItem
- Query
- Scan
- Batch Operations
- Transactions
- Conditional Writes
- Pagination
- Error Handling
- Production Best Practices

---

# Question 1

## Write Python code to retrieve an item by primary key.

### Expected Answer

```python
import boto3

table = boto3.resource("dynamodb").Table("Users")

response = table.get_item(
    Key={
        "UserId": "USER#1001"
    }
)

item = response.get("Item")

print(item)
```

---

### Interview Discussion

Why use **GetItem** instead of Query?

Because:

- Fastest lookup
- Direct partition key access
- O(1)-style key lookup from the application's perspective

---

# Question 2

## Write code to insert a new user.

```python
table.put_item(
    Item={
        "UserId": "USER#1001",
        "Name": "John",
        "Email": "john@example.com"
    }
)
```

---

### Follow-up

How do you prevent duplicate users?

Use:

```python
ConditionExpression="attribute_not_exists(UserId)"
```

---

# Question 3

## Update an existing item.

```python
table.update_item(
    Key={
        "UserId": "USER#1001"
    },
    UpdateExpression="SET Email = :email",
    ExpressionAttributeValues={
        ":email": "new@example.com"
    }
)
```

---

## Production Improvement

Return updated values:

```python
ReturnValues="ALL_NEW"
```

---

# Question 4

## Delete an item.

```python
table.delete_item(
    Key={
        "UserId": "USER#1001"
    }
)
```

---

### Production Version

Use conditional deletion.

```python
ConditionExpression="attribute_exists(UserId)"
```

---

# Question 5

## Query all orders for a customer.

```python
from boto3.dynamodb.conditions import Key

response = table.query(
    KeyConditionExpression=
        Key("PK").eq("CUSTOMER#100")
)
```

---

### Interview Tip

Always choose:

```text
Query
```

instead of:

```text
Scan
```

when possible.

---

# Question 6

## Write a Query using a sort key.

```python
response = table.query(
    KeyConditionExpression=
        Key("PK").eq("CUSTOMER#100") &
        Key("SK").begins_with("ORDER#")
)
```

---

Possible follow-up:

Retrieve:

- Orders
- Payments
- Shipments

using prefixes.

---

# Question 7

## How do you paginate Query results?

```python
response = table.query(
    KeyConditionExpression=
        Key("PK").eq("CUSTOMER#100")
)

while "LastEvaluatedKey" in response:

    response = table.query(
        KeyConditionExpression=
            Key("PK").eq("CUSTOMER#100"),
        ExclusiveStartKey=response["LastEvaluatedKey"]
    )
```

---

### Why?

DynamoDB returns:

```text
Maximum 1 MB
```

per request.

---

# Question 8

## Write a BatchGet example.

```python
client = boto3.client("dynamodb")

response = client.batch_get_item(
    RequestItems={
        "Users": {
            "Keys": [
                {"UserId": {"S": "USER#1"}},
                {"UserId": {"S": "USER#2"}}
            ]
        }
    }
)
```

---

### Interview Discussion

Batch operations reduce:

- Network calls
- Latency
- API overhead

---

# Question 9

## Write a BatchWrite example.

```python
with table.batch_writer() as batch:

    batch.put_item(
        Item={
            "UserId": "USER#1"
        }
    )

    batch.put_item(
        Item={
            "UserId": "USER#2"
        }
    )
```

---

### Why use batch_writer()?

It automatically:

- Buffers writes
- Retries unprocessed items
- Simplifies bulk inserts

---

# Question 10

## Write a conditional update.

```python
table.update_item(
    Key={
        "UserId": "USER#1001"
    },
    UpdateExpression="SET Version = Version + :inc",
    ConditionExpression="Version = :version",
    ExpressionAttributeValues={
        ":version": 5,
        ":inc": 1
    }
)
```

---

Purpose:

Optimistic Locking.

---

# Question 11

## Write a transaction.

```python
client.transact_write_items(

    TransactItems=[

        {
            "Put": {

                "TableName": "Orders",

                "Item": {

                    "OrderId": {
                        "S": "100"
                    }

                }

            }

        },

        {

            "Update": {

                "TableName": "Inventory"

            }

        }

    ]

)
```

---

### Interview Discussion

Transactions guarantee:

```text
All

OR

Nothing
```

---

# Question 12

## How do you catch DynamoDB exceptions?

```python
from botocore.exceptions import ClientError

try:

    table.put_item(...)

except ClientError as e:

    print(e.response["Error"]["Code"])
```

---

Common errors:

- ConditionalCheckFailedException
- ProvisionedThroughputExceededException
- ResourceNotFoundException
- ValidationException

---

# Question 13

## Write code that retries throttled requests.

```python
import time

for retry in range(5):

    try:

        table.put_item(...)

        break

    except ClientError:

        time.sleep(2 ** retry)
```

---

### Interview Tip

Mention:

Exponential Backoff

instead of:

Immediate retries.

---

# Question 14

## How do you query a Global Secondary Index?

```python
response = table.query(

    IndexName="EmailIndex",

    KeyConditionExpression=

        Key("Email").eq("john@example.com")

)
```

---

Interview Follow-up

Why use GSI?

Alternate access pattern.

---

# Question 15

## How do you scan a table?

```python
response = table.scan()
```

---

### Follow-up

Would you use this in production?

Usually:

```text
No
```

Prefer Query whenever possible.

---

# Question 16

## How do you use Projection Expressions?

```python
response = table.get_item(

    Key={

        "UserId": "USER#100"

    },

    ProjectionExpression="Name, Email"

)
```

Benefits:

- Smaller response payloads
- Reduced network transfer
- Faster application processing

---

# Question 17

## How do you increment a counter atomically?

```python
table.update_item(

    Key={

        "UserId": "USER#100"

    },

    UpdateExpression="ADD LoginCount :inc",

    ExpressionAttributeValues={

        ":inc": 1

    }

)
```

---

Production Uses

- Likes
- Page views
- Login count
- Download count

---

# Question 18

## How would you structure a production DynamoDB repository class?

```python
class UserRepository:

    def __init__(self, table):
        self.table = table

    def get_user(self, user_id):
        return self.table.get_item(
            Key={"UserId": user_id}
        )

    def create_user(self, item):
        return self.table.put_item(Item=item)

    def update_user(self, user_id, expression, values):
        return self.table.update_item(
            Key={"UserId": user_id},
            UpdateExpression=expression,
            ExpressionAttributeValues=values
        )

    def delete_user(self, user_id):
        return self.table.delete_item(
            Key={"UserId": user_id}
        )
```

---

### Why?

Keeps:

- Business logic
- Database access
- Testing

properly separated.

---

# Question 19

## What production improvements would you make to the code?

### Expected Answer

Add:

- Structured logging
- Retry logic
- Timeouts
- Metrics
- Exception handling
- Type hints
- Repository pattern
- Unit tests
- Dependency injection

---

# Question 20

## Explain how you use Boto3 in production.

### Sample Answer

> In production, I use Boto3 through repository or service classes rather than directly inside business logic. I rely on IAM roles for authentication, use conditional writes to prevent race conditions, implement retries with exponential backoff for transient failures, monitor CloudWatch metrics, avoid Scan operations, and optimize queries using appropriate primary keys and GSIs. This keeps the code maintainable, resilient, and scalable.

---

# Rapid Fire Questions

| Question | Short Answer |
|-----------|--------------|
| Retrieve item | GetItem |
| Insert item | PutItem |
| Update item | UpdateItem |
| Delete item | DeleteItem |
| Preferred read | Query |
| Avoid | Scan |
| Batch write | batch_writer() |
| Transaction API | transact_write_items() |
| Retry strategy | Exponential Backoff |
| SDK | Boto3 |

---

# Senior Interview Tips

Strong candidates discuss:

- Repository pattern
- Dependency injection
- Error handling
- Retries
- Logging
- Metrics
- Idempotency
- Clean architecture
- Testability

Avoid writing SDK calls directly inside controllers or API routes.

---

# Common Mistakes

## Using Scan Everywhere

Always prefer:

```text
Query
```

for production workloads.

---

## No Error Handling

Every SDK call should handle:

- Throttling
- Validation errors
- Missing resources
- Conditional failures

---

## No Retry Logic

Transient AWS failures should be retried using exponential backoff with jitter where appropriate.

---

## Mixing Business Logic with Database Code

Separate:

```text
Controller

↓

Service

↓

Repository

↓

DynamoDB
```

This improves maintainability and testing.

---

# Interview Cheat Sheet

```text
Boto3

↓

Repository Pattern

↓

GetItem

↓

Query

↓

UpdateItem

↓

Conditional Writes

↓

Transactions

↓

Retries

↓

Logging

↓

Monitoring
```

---

# Key Takeaways

- Senior coding interviews evaluate clean architecture and production readiness, not just SDK syntax.
- Use `GetItem`, `Query`, and conditional writes appropriately while avoiding unnecessary `Scan` operations.
- Implement retry strategies, structured logging, and exception handling to build resilient applications.
- Encapsulate DynamoDB interactions in repository or service layers to improve maintainability and testability.
- Strong candidates explain both **how** they use Boto3 and **why** their implementation choices improve scalability, reliability, and code quality.