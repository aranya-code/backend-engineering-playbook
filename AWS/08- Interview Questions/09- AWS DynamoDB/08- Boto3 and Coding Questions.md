# 07- Boto3 and Coding Questions

## Overview

This document focuses on Python and Boto3 coding questions for Amazon DynamoDB interviews. The emphasis is on writing correct application code while reasoning about key design, pagination, conditional writes, transactions, batching, retries, consistency, performance, and failure handling.

The examples use the low-level DynamoDB client and the higher-level Boto3 Table resource where each is appropriate. Production code should also consider connection reuse, timeouts, retries, logging, idempotency, validation, and least-privilege IAM permissions.

---

## Boto3 DynamoDB Interfaces

Boto3 exposes DynamoDB through two commonly used interfaces:

| Interface | Typical Usage | Data Representation |
|---|---|---|
| `boto3.client("dynamodb")` | Low-level control and complete API access | DynamoDB attribute-value format |
| `boto3.resource("dynamodb")` | Application-oriented operations | Native Python values |

For backend applications, the resource interface is often easier to work with:

```python
import boto3

dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
table = dynamodb.Table("Orders")
```

The low-level client is useful when the application needs direct access to DynamoDB API operations:

```python
import boto3

client = boto3.client("dynamodb", region_name="ap-south-1")
```

---

## Basic Table Operations

### Question

**How do you retrieve an item from DynamoDB using Boto3?**

**Answer:**

```python
import boto3

dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
table = dynamodb.Table("Orders")

response = table.get_item(
    Key={
        "PK": "ORDER#123",
        "SK": "DETAILS",
    }
)

item = response.get("Item")

if item is None:
    print("Order not found")
else:
    print(item)
```

`get_item()` performs a direct lookup using the complete primary key.

For a composite primary key, both the partition key and sort key are required.

---

### Question

**How do you insert an item using Boto3?**

**Answer:**

```python
table.put_item(
    Item={
        "PK": "ORDER#123",
        "SK": "DETAILS",
        "customer_id": "CUST#456",
        "status": "PENDING",
        "total": 1499.00,
    }
)
```

`put_item()` replaces the existing item if the same primary key already exists.

That behavior is important in production because an unconditional `put_item()` can overwrite an existing record.

---

### Question

**How do you prevent an existing item from being overwritten?**

**Answer:**

Use a conditional expression:

```python
table.put_item(
    Item={
        "PK": "ORDER#123",
        "SK": "DETAILS",
        "status": "PENDING",
    },
    ConditionExpression="attribute_not_exists(PK)",
)
```

If the item already exists, DynamoDB rejects the operation with a conditional-check failure.

This pattern is useful for:

- Idempotent creation
- Duplicate prevention
- Resource registration
- Unique business identifiers

---

## Updating Items

### Question

**How do you update selected attributes without replacing the entire item?**

**Answer:**

Use `update_item()`:

```python
response = table.update_item(
    Key={
        "PK": "ORDER#123",
        "SK": "DETAILS",
    },
    UpdateExpression="SET #status = :status",
    ExpressionAttributeNames={
        "#status": "status",
    },
    ExpressionAttributeValues={
        ":status": "SHIPPED",
    },
    ReturnValues="ALL_NEW",
)

updated_item = response["Attributes"]
```

This updates only the specified attribute.

---

### Question

**How do you safely increment a DynamoDB counter?**

**Answer:**

Use an atomic update expression:

```python
response = table.update_item(
    Key={
        "PK": "PRODUCT#123",
        "SK": "COUNTER",
    },
    UpdateExpression="ADD #count :increment",
    ExpressionAttributeNames={
        "#count": "count",
    },
    ExpressionAttributeValues={
        ":increment": 1,
    },
    ReturnValues="UPDATED_NEW",
)
```

This is preferable to:

```text
Read count
↓
Increment in application
↓
Write count
```

because concurrent requests can otherwise overwrite each other's updates.

---

### Question

**How do you implement an atomic inventory decrement?**

**Answer:**

Use a conditional update:

```python
table.update_item(
    Key={
        "PK": "PRODUCT#123",
        "SK": "INVENTORY",
    },
    UpdateExpression="SET quantity = quantity - :amount",
    ConditionExpression="quantity >= :amount",
    ExpressionAttributeValues={
        ":amount": 1,
    },
)
```

The condition prevents the quantity from becoming negative.

This is an important concurrency pattern because the validation and modification occur within the DynamoDB write operation.

---

## Querying DynamoDB

### Question

**How do you query all orders for a customer?**

**Answer:**

Assuming:

```text
PK = CUSTOMER#123
SK = ORDER#<order_id>
```

use:

```python
from boto3.dynamodb.conditions import Key

response = table.query(
    KeyConditionExpression=Key("PK").eq("CUSTOMER#123")
)

orders = response["Items"]
```

A query targets a specific partition key rather than examining the entire table.

---

### Question

**How do you query orders within a sort-key range?**

**Answer:**

```python
response = table.query(
    KeyConditionExpression=(
        Key("PK").eq("CUSTOMER#123")
        & Key("SK").between(
            "ORDER#2026-08-01",
            "ORDER#2026-08-31",
        )
    )
)
```

The partition key identifies the logical partition, while the sort-key condition restricts the requested range.

---

### Question

**Can you use arbitrary attributes in `KeyConditionExpression`?**

**Answer:**

No.

A key condition can use the table's primary key or the relevant index key.

For non-key attributes, use a filter expression or, preferably, redesign the access pattern if the attribute is central to the query.

---

## Pagination

### Question

**Why does DynamoDB pagination matter in Boto3?**

**Answer:**

DynamoDB does not necessarily return every matching item in one response.

A response can contain `LastEvaluatedKey`, indicating that more data is available.

A production implementation should continue querying until the desired page is collected or there are no more items.

---

### Question

**How do you manually paginate a DynamoDB query?**

**Answer:**

```python
from boto3.dynamodb.conditions import Key

items = []
exclusive_start_key = None

while True:
    params = {
        "KeyConditionExpression": Key("PK").eq("CUSTOMER#123"),
        "Limit": 100,
    }

    if exclusive_start_key:
        params["ExclusiveStartKey"] = exclusive_start_key

    response = table.query(**params)

    items.extend(response.get("Items", []))

    exclusive_start_key = response.get("LastEvaluatedKey")

    if not exclusive_start_key:
        break
```

For API endpoints, avoid returning an unbounded number of records. Prefer application-level pagination.

---

### Question

**How would you implement cursor-based pagination in a REST API?**

**Answer:**

A typical flow is:

```text
Client
  ↓
GET /orders?limit=50
  ↓
DynamoDB Query
  ↓
LastEvaluatedKey
  ↓
Encode Cursor
  ↓
Client
```

The cursor can represent the DynamoDB continuation key.

The API should avoid exposing internal database details directly when a stable external cursor format can be provided.

---

## Pagination with Boto3 Paginators

### Question

**Does Boto3 provide a paginator for DynamoDB operations?**

**Answer:**

Yes. For client APIs that support pagination, Boto3 provides paginators.

Example:

```python
import boto3

client = boto3.client("dynamodb")

paginator = client.get_paginator("query")

for page in paginator.paginate(
    TableName="Orders",
    KeyConditionExpression="PK = :pk",
    ExpressionAttributeValues={
        ":pk": {"S": "CUSTOMER#123"},
    },
):
    for item in page.get("Items", []):
        print(item)
```

Paginators simplify continuation-token handling, but application-level pagination is still required when exposing paginated APIs.

---

## Conditional Writes

### Question

**How do you implement optimistic locking with Boto3?**

**Answer:**

Use a version attribute:

```python
table.update_item(
    Key={
        "PK": "ORDER#123",
        "SK": "DETAILS",
    },
    UpdateExpression="SET #status = :status, #version = :next_version",
    ConditionExpression="#version = :current_version",
    ExpressionAttributeNames={
        "#status": "status",
        "#version": "version",
    },
    ExpressionAttributeValues={
        ":status": "SHIPPED",
        ":current_version": 4,
        ":next_version": 5,
    },
)
```

If another request has already changed version `4`, the condition fails.

This prevents lost updates.

---

### Question

**How do you catch a failed conditional write?**

**Answer:**

```python
from botocore.exceptions import ClientError

try:
    table.update_item(
        Key={
            "PK": "ORDER#123",
            "SK": "DETAILS",
        },
        UpdateExpression="SET #status = :status",
        ConditionExpression="#status = :expected",
        ExpressionAttributeNames={
            "#status": "status",
        },
        ExpressionAttributeValues={
            ":status": "SHIPPED",
            ":expected": "PROCESSING",
        },
    )
except ClientError as exc:
    if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
        print("Condition was not satisfied")
    else:
        raise
```

Do not treat every `ClientError` as a business conflict. Infrastructure and authorization errors should generally propagate differently.

---

## Idempotency

### Question

**How would you implement an idempotent API using DynamoDB and Boto3?**

**Answer:**

Store the idempotency key using a conditional write:

```python
from datetime import datetime, timezone

table.put_item(
    Item={
        "PK": "IDEMPOTENCY#request-123",
        "SK": "RESULT",
        "status": "PROCESSING",
        "created_at": datetime.now(timezone.utc).isoformat(),
    },
    ConditionExpression="attribute_not_exists(PK)",
)
```

If the conditional write succeeds, the request owns the idempotency record.

If it fails, another request has already created it.

The production design should also handle:

- Request completion
- Failed requests
- Expiration
- Stored response data
- Concurrent callers
- Retry behavior

---

## Batch Operations

### Question

**How do you write multiple items using Boto3?**

**Answer:**

Use `batch_writer()`:

```python
with table.batch_writer() as batch:
    for order in orders:
        batch.put_item(Item=order)
```

This is useful for bulk operations because the helper handles batching and retries for unprocessed items.

---

### Question

**What should you remember when using `batch_writer()`?**

**Answer:**

Batch operations are not equivalent to transactions.

They do not provide an all-or-nothing transaction boundary across all items.

Use transactions when atomicity across multiple operations is a business requirement.

Use batch operations when efficient bulk processing is the primary requirement.

---

### Question

**How do you delete multiple items using Boto3?**

**Answer:**

```python
with table.batch_writer() as batch:
    for order in orders:
        batch.delete_item(
            Key={
                "PK": order["PK"],
                "SK": order["SK"],
            }
        )
```

For large datasets, control the workload carefully so that bulk deletion does not negatively affect production traffic.

---

## Transactions

### Question

**How do you execute a DynamoDB transaction with Boto3?**

**Answer:**

Use the low-level client:

```python
import boto3

client = boto3.client("dynamodb")

client.transact_write_items(
    TransactItems=[
        {
            "Update": {
                "TableName": "Orders",
                "Key": {
                    "PK": {"S": "ORDER#123"},
                    "SK": {"S": "DETAILS"},
                },
                "UpdateExpression": "SET #status = :status",
                "ExpressionAttributeNames": {
                    "#status": "status",
                },
                "ExpressionAttributeValues": {
                    ":status": {"S": "CONFIRMED"},
                },
            }
        },
        {
            "Update": {
                "TableName": "Inventory",
                "Key": {
                    "PK": {"S": "PRODUCT#123"},
                    "SK": {"S": "INVENTORY"},
                },
                "UpdateExpression": "SET #quantity = #quantity - :amount",
                "ConditionExpression": "#quantity >= :amount",
                "ExpressionAttributeNames": {
                    "#quantity": "quantity",
                },
                "ExpressionAttributeValues": {
                    ":amount": {"N": "1"},
                },
            }
        },
    ]
)
```

The transaction either succeeds according to DynamoDB's transaction semantics or fails as a unit.

---

## Expression Attribute Names and Values

### Question

**Why are `ExpressionAttributeNames` needed?**

**Answer:**

They provide aliases for attribute names that may conflict with DynamoDB expression syntax or reserved words.

Example:

```python
UpdateExpression="SET #status = :value"

ExpressionAttributeNames={
    "#status": "status",
}

ExpressionAttributeValues={
    ":value": "ACTIVE",
}
```

Using aliases consistently also makes dynamic expressions safer and easier to construct.

---

### Question

**What is the difference between `ExpressionAttributeNames` and `ExpressionAttributeValues`?**

| Feature | Purpose | Example |
|---|---|---|
| `ExpressionAttributeNames` | Attribute-name aliases | `#status` |
| `ExpressionAttributeValues` | Runtime values | `:status` |

For the resource API:

```python
ExpressionAttributeValues={
    ":status": "ACTIVE",
}
```

For the low-level client:

```python
ExpressionAttributeValues={
    ":status": {"S": "ACTIVE"},
}
```

---

## Projection and Returned Attributes

### Question

**How do you return only selected attributes from a DynamoDB query?**

**Answer:**

Use `ProjectionExpression`:

```python
response = table.query(
    KeyConditionExpression=Key("PK").eq("CUSTOMER#123"),
    ProjectionExpression="order_id, #status, total",
    ExpressionAttributeNames={
        "#status": "status",
    },
)
```

This reduces the amount of data returned to the application.

However, projection should not be confused with a complete solution to read-capacity optimization. The underlying access pattern and item size still matter.

---

## Consistency in Boto3

### Question

**How do you request a strongly consistent read?**

**Answer:**

For supported operations:

```python
response = table.get_item(
    Key={
        "PK": "ORDER#123",
        "SK": "DETAILS",
    },
    ConsistentRead=True,
)
```

Use strong consistency only where the application actually requires it.

---

## Query vs Scan in Code

### Question

**Show the difference between `query()` and `scan()`.**

**Answer:**

Query:

```python
response = table.query(
    KeyConditionExpression=Key("PK").eq("CUSTOMER#123")
)
```

Scan:

```python
response = table.scan()
```

A query targets a partition-key value and is normally the preferred production access pattern.

A scan examines table data and should be used deliberately.

---

## Secondary Indexes

### Question

**How do you query a GSI using Boto3?**

**Answer:**

```python
response = table.query(
    IndexName="StatusIndex",
    KeyConditionExpression=(
        Key("status").eq("PENDING")
    ),
)
```

The application should choose the index because it matches a known access pattern.

---

### Question

**How do you query a GSI using a composite key condition?**

**Answer:**

```python
response = table.query(
    IndexName="CustomerStatusIndex",
    KeyConditionExpression=(
        Key("customer_id").eq("CUSTOMER#123")
        & Key("status").eq("PENDING")
    ),
)
```

The exact expression must correspond to the index's key schema.

---

## Retry Handling

### Question

**Should you manually retry every DynamoDB exception?**

**Answer:**

No.

Boto3 uses botocore's retry mechanisms for supported AWS API calls.

Applications should still implement business-level retry behavior carefully for cases such as:

- Conditional conflicts
- Explicit throttling handling
- Failed asynchronous processing
- External dependency failures

Do not create aggressive retry loops around every exception.

---

### Question

**Why can retries make a DynamoDB incident worse?**

**Answer:**

Suppose the application receives throttling:

```text
Traffic
  ↓
DynamoDB throttling
  ↓
Application retries immediately
  ↓
More requests
  ↓
More throttling
```

This creates retry amplification.

Use:

- Exponential backoff
- Jitter
- Bounded retries
- Circuit breaking where appropriate
- Rate limiting
- Queue-based buffering

---

## DynamoDB Streams with Boto3

### Question

**How do you retrieve DynamoDB Stream records using Boto3?**

**Answer:**

The workflow uses:

```text
List Streams
   ↓
Describe Stream
   ↓
Get Shard Iterator
   ↓
Get Records
```

Example:

```python
import boto3

client = boto3.client("dynamodbstreams")

streams = client.list_streams(
    TableName="Orders"
)

stream_arn = streams["Streams"][0]["StreamArn"]

description = client.describe_stream(
    StreamArn=stream_arn
)

shard_id = description["StreamDescription"]["Shards"][0]["ShardId"]

iterator = client.get_shard_iterator(
    StreamArn=stream_arn,
    ShardId=shard_id,
    ShardIteratorType="TRIM_HORIZON",
)

records = client.get_records(
    ShardIterator=iterator["ShardIterator"]
)

for record in records["Records"]:
    print(record)
```

In production, managed integrations such as Lambda event source mappings are often preferable to manually implementing stream polling.

---

## Resource Management

### Question

**Should you create a new Boto3 DynamoDB resource for every request?**

**Answer:**

Generally, no.

Create reusable clients or resources and allow botocore to reuse underlying HTTP connections.

For example:

```python
import boto3

dynamodb = boto3.resource(
    "dynamodb",
    region_name="ap-south-1",
)

orders_table = dynamodb.Table("Orders")
```

In a Django or FastAPI application, initialize shared AWS clients through the application's lifecycle rather than repeatedly creating them inside request handlers.

---

## FastAPI Integration

### Question

**How would you integrate DynamoDB with FastAPI?**

**Answer:**

A simplified application structure can use a shared Table resource:

```python
import boto3
from fastapi import FastAPI

app = FastAPI()

dynamodb = boto3.resource(
    "dynamodb",
    region_name="ap-south-1",
)

orders_table = dynamodb.Table("Orders")


@app.get("/orders/{order_id}")
def get_order(order_id: str):
    response = orders_table.get_item(
        Key={
            "PK": f"ORDER#{order_id}",
            "SK": "DETAILS",
        }
    )

    return response.get("Item")
```

Production applications should separate:

- API layer
- Service layer
- Repository/data-access layer
- Configuration
- Error handling
- Authentication and authorization

---

## Repository Pattern

### Question

**How would you abstract DynamoDB access from a FastAPI service?**

**Answer:**

```python
from boto3.dynamodb.conditions import Key


class OrderRepository:
    def __init__(self, table):
        self.table = table

    def get_order(self, order_id: str):
        response = self.table.get_item(
            Key={
                "PK": f"ORDER#{order_id}",
                "SK": "DETAILS",
            }
        )

        return response.get("Item")

    def get_customer_orders(self, customer_id: str):
        response = self.table.query(
            KeyConditionExpression=Key(
                "PK"
            ).eq(f"CUSTOMER#{customer_id}")
        )

        return response["Items"]
```

The service layer can then depend on the repository rather than directly coupling business logic to Boto3.

---

## Testing Boto3 Code

### Question

**How should DynamoDB code be tested?**

**Answer:**

Separate unit tests from integration tests.

For unit tests:

- Mock Boto3 interactions
- Test key construction
- Test expression construction
- Test error handling
- Test business logic

For integration tests:

- Use an isolated AWS environment or appropriate local testing strategy
- Validate actual DynamoDB behavior
- Test conditional writes
- Test pagination
- Test transactions
- Test indexes

Do not rely exclusively on mocks for database behavior.

---

### Question

**What should you test for a DynamoDB repository?**

**Answer:**

At minimum:

| Test Area | Example |
|---|---|
| Read | Item exists |
| Read | Item does not exist |
| Write | Item created |
| Write | Duplicate prevented |
| Update | Conditional update succeeds |
| Update | Conditional update fails |
| Query | Correct key condition |
| Pagination | Multiple pages |
| Delete | Correct key |
| Retry | Throttling behavior |
| Serialization | DynamoDB/Python conversion |
| Authorization | Tenant isolation |

---

## Error Handling

### Question

**How should Boto3 exceptions be handled in a backend API?**

**Answer:**

Do not expose raw AWS exceptions directly to API clients.

Instead, translate infrastructure-level errors into application-level behavior.

For example:

```python
from botocore.exceptions import ClientError


def get_order(table, order_id: str):
    try:
        response = table.get_item(
            Key={
                "PK": f"ORDER#{order_id}",
                "SK": "DETAILS",
            }
        )
    except ClientError as exc:
        error_code = exc.response["Error"]["Code"]

        if error_code == "ResourceNotFoundException":
            raise RuntimeError("Database resource unavailable")

        raise

    return response.get("Item")
```

Production applications should also log the AWS error code and relevant request context without exposing sensitive data.

---

## Configuration and Credentials

### Question

**How should Boto3 credentials be supplied in production?**

**Answer:**

Prefer AWS identity mechanisms rather than hardcoded credentials.

Typical environments include:

```text
Local Development
    ↓
AWS CLI / credential provider chain

EC2
    ↓
IAM Role

ECS
    ↓
Task Role

EKS
    ↓
Pod Identity / IAM integration

Lambda
    ↓
Execution Role
```

Avoid:

```python
boto3.client(
    "dynamodb",
    aws_access_key_id="...",
    aws_secret_access_key="...",
)
```

especially in source code.

---

## Production Boto3 Configuration

### Question

**How would you configure a Boto3 client for production workloads?**

**Answer:**

A `botocore.config.Config` object can be used to configure retries and connection behavior.

```python
import boto3
from botocore.config import Config

config = Config(
    retries={
        "mode": "standard",
        "max_attempts": 5,
    },
    max_pool_connections=50,
)

dynamodb = boto3.resource(
    "dynamodb",
    region_name="ap-south-1",
    config=config,
)
```

The appropriate connection-pool size depends on application concurrency and workload characteristics.

Do not blindly increase connection limits without measuring the application's concurrency and downstream capacity.

---

## Coding Scenario: Build a Get-or-Create Operation

### Question

**Implement a safe get-or-create operation for a DynamoDB item.**

**Answer:**

A production design should avoid a simple:

```text
Get
 ↓
If missing
 ↓
Put
```

because concurrent requests can both observe the item as missing.

Use a conditional write:

```python
from botocore.exceptions import ClientError


def create_order_if_missing(table, order_id: str):
    item = {
        "PK": f"ORDER#{order_id}",
        "SK": "DETAILS",
        "status": "PENDING",
    }

    try:
        table.put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(PK)",
        )
        return item

    except ClientError as exc:
        if exc.response["Error"]["Code"] != "ConditionalCheckFailedException":
            raise

        response = table.get_item(
            Key={
                "PK": f"ORDER#{order_id}",
                "SK": "DETAILS",
            }
        )

        return response.get("Item")
```

The exact behavior should also define what happens if the existing record belongs to a different logical operation.

---

## Coding Scenario: Paginated Query Helper

### Question

**Write a reusable function that returns a limited number of items from DynamoDB.**

**Answer:**

```python
from boto3.dynamodb.conditions import Key


def get_orders_page(
    table,
    customer_id: str,
    limit: int = 50,
    exclusive_start_key: dict | None = None,
):
    params = {
        "KeyConditionExpression": Key(
            "PK"
        ).eq(f"CUSTOMER#{customer_id}"),
        "Limit": limit,
    }

    if exclusive_start_key:
        params["ExclusiveStartKey"] = exclusive_start_key

    response = table.query(**params)

    return {
        "items": response.get("Items", []),
        "next_key": response.get("LastEvaluatedKey"),
    }
```

The API layer can encode `next_key` into an opaque cursor before returning it to the client.

---

## Coding Scenario: Conditional State Transition

### Question

**Implement a safe order state transition from `PENDING` to `CONFIRMED`.**

**Answer:**

```python
from botocore.exceptions import ClientError


def confirm_order(table, order_id: str) -> bool:
    try:
        table.update_item(
            Key={
                "PK": f"ORDER#{order_id}",
                "SK": "DETAILS",
            },
            UpdateExpression="SET #status = :confirmed",
            ConditionExpression="#status = :pending",
            ExpressionAttributeNames={
                "#status": "status",
            },
            ExpressionAttributeValues={
                ":confirmed": "CONFIRMED",
                ":pending": "PENDING",
            },
        )
        return True

    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False

        raise
```

This prevents two concurrent workers from both successfully applying the same state transition when the state must be `PENDING` beforehand.

---

## Coding Scenario: TTL Attribute

### Question

**How do you set a TTL attribute using Boto3?**

**Answer:**

Store the expiration timestamp as a Unix epoch value:

```python
import time

ttl = int(time.time()) + 3600

table.put_item(
    Item={
        "PK": "SESSION#123",
        "SK": "DATA",
        "expires_at": ttl,
    }
)
```

The corresponding DynamoDB table must have TTL configured for `expires_at`.

TTL should not be treated as an exact-time deletion mechanism. Applications should tolerate the item remaining available for some period after expiration.

---

## Coding Scenario: Batch Write with Failure Handling

### Question

**How would you process a large dataset safely with `batch_writer()`?**

**Answer:**

```python
def write_orders(table, orders):
    with table.batch_writer(
        overwrite_by_pkeys=["PK", "SK"]
    ) as batch:
        for order in orders:
            batch.put_item(Item=order)
```

For very large workloads, process data in controlled batches rather than loading the entire dataset into memory.

Also consider:

- Checkpointing
- Idempotency
- Backpressure
- Monitoring
- Error reporting
- Production traffic impact

---

## Coding Scenario: Low-Level Client Conversion

### Question

**Why does the low-level Boto3 DynamoDB client use `{"S": ...}` and `{"N": ...}`?**

**Answer:**

The low-level client uses DynamoDB's explicit attribute-value representation.

For example:

```python
{
    "PK": {"S": "ORDER#123"},
    "quantity": {"N": "5"},
    "active": {"BOOL": True},
}
```

The resource API performs conversion between Python values and DynamoDB attribute values:

```python
{
    "PK": "ORDER#123",
    "quantity": 5,
    "active": True,
}
```

This is one reason the Table resource is generally easier for application code.

---

## Coding Scenario: Query a GSI

### Question

**Write a Boto3 query against a GSI for all pending orders for a customer.**

**Answer:**

```python
from boto3.dynamodb.conditions import Key


def get_pending_orders(table, customer_id: str):
    response = table.query(
        IndexName="CustomerStatusIndex",
        KeyConditionExpression=(
            Key("customer_id").eq(customer_id)
            & Key("status").eq("PENDING")
        ),
    )

    return response.get("Items", [])
```

The index must have `customer_id` and `status` as its key attributes according to the required key schema.

---

## Coding Scenario: Prevent Negative Inventory

### Question

**Write production-oriented Boto3 code to decrement inventory only when enough stock exists.**

**Answer:**

```python
from botocore.exceptions import ClientError


def reserve_inventory(table, product_id: str, quantity: int) -> bool:
    if quantity <= 0:
        raise ValueError("quantity must be greater than zero")

    try:
        table.update_item(
            Key={
                "PK": f"PRODUCT#{product_id}",
                "SK": "INVENTORY",
            },
            UpdateExpression="SET #quantity = #quantity - :quantity",
            ConditionExpression="#quantity >= :quantity",
            ExpressionAttributeNames={
                "#quantity": "quantity",
            },
            ExpressionAttributeValues={
                ":quantity": quantity,
            },
        )
        return True

    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False

        raise
```

The key design principle is that validation and mutation must occur atomically at the database operation level.

---

## Common Boto3 Mistakes

| Mistake | Why It Is Dangerous | Better Approach |
|---|---|---|
| Creating clients per request | Connection reuse suffers | Reuse clients/resources |
| Using `scan()` for APIs | Poor scalability | Model access patterns |
| Ignoring pagination | Missing records | Handle continuation keys |
| Unconditional `put_item()` | Can overwrite data | Conditional writes |
| Read-modify-write counters | Lost updates | Atomic updates |
| Infinite retries | Retry storms | Bounded exponential backoff |
| Hardcoded credentials | Security risk | IAM roles/provider chain |
| Catching all exceptions | Hides failures | Handle known errors explicitly |
| Returning raw AWS errors | Leaks infrastructure details | Translate errors |
| Loading all records into memory | Memory pressure | Stream/process incrementally |
| Blindly increasing connection pools | Resource waste | Tune from measurements |
| Treating TTL as immediate deletion | Incorrect business logic | Treat TTL as eventual cleanup |

---

## Interview Coding Checklist

When solving a DynamoDB coding problem, explicitly consider:

- What is the partition key?
- What is the sort key?
- Which access pattern is being implemented?
- Is this a `GetItem`, `Query`, or `Scan`?
- Can the operation be concurrent?
- Is a condition required?
- Is the operation idempotent?
- Does the operation require pagination?
- Could the item become hot?
- Could the operation be retried?
- What happens on throttling?
- What happens when the item does not exist?
- What happens when a conditional write fails?
- Are credentials supplied securely?
- Is the Boto3 client reused?
- Does the API expose an appropriate error response?
- Is the workload production-scale?

---

## Senior-Level Coding Scenario

### Question

**Design a DynamoDB repository method that updates an order only if the caller provides the expected version.**

**Answer:**

```python
from botocore.exceptions import ClientError


class OrderRepository:
    def __init__(self, table):
        self.table = table

    def update_status(
        self,
        order_id: str,
        expected_version: int,
        status: str,
    ) -> dict:
        try:
            response = self.table.update_item(
                Key={
                    "PK": f"ORDER#{order_id}",
                    "SK": "DETAILS",
                },
                UpdateExpression=(
                    "SET #status = :status, "
                    "#version = :next_version"
                ),
                ConditionExpression=(
                    "#version = :expected_version"
                ),
                ExpressionAttributeNames={
                    "#status": "status",
                    "#version": "version",
                },
                ExpressionAttributeValues={
                    ":status": status,
                    ":expected_version": expected_version,
                    ":next_version": expected_version + 1,
                },
                ReturnValues="ALL_NEW",
            )

            return response["Attributes"]

        except ClientError as exc:
            if (
                exc.response["Error"]["Code"]
                == "ConditionalCheckFailedException"
            ):
                raise ValueError(
                    "Order was modified by another request"
                ) from exc

            raise
```

This demonstrates several senior-level concepts simultaneously:

- Repository abstraction
- Conditional writes
- Optimistic concurrency
- Atomic version updates
- Explicit error classification
- Avoidance of read-modify-write races

---

## Key Takeaways

- Boto3 DynamoDB code should be designed around DynamoDB access patterns, conditional operations, pagination, and failure behavior rather than simply translating CRUD operations into Python.
- Conditional expressions and atomic update expressions are essential for concurrency-safe application logic such as idempotency, inventory reservation, counters, and optimistic locking.
- Production Boto3 applications should reuse AWS clients/resources, use IAM-based credentials, handle pagination, configure bounded retries, and distinguish infrastructure failures from expected business conflicts.
- `Query`, `batch_writer()`, transactions, GSIs, Streams, and low-level client operations solve different problems; choosing the correct API is part of the architecture rather than just a coding detail.
- Strong DynamoDB coding answers explain what the code does, how it behaves under concurrency and retries, and how it will operate safely at production scale.