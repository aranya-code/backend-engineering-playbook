# 01- Python and MongoDB Integration

## Overview

Python is one of the most common application languages used with MongoDB for REST APIs, microservices, background workers, data-processing services, and event-driven systems.

The primary Python driver is **PyMongo**. It provides direct access to MongoDB operations while exposing important database concepts such as:

- Documents
- BSON
- ObjectId
- Cursors
- Sessions
- Transactions
- Connection pools
- Read and write concerns
- Retryable operations
- Aggregation pipelines
- Change streams

The recommended architecture is usually to keep PyMongo behind a repository or data-access layer rather than allowing MongoDB operations to spread throughout API handlers and business logic.

```mermaid
flowchart LR
    CLIENT[Client]
    API[FastAPI / Django]
    SERVICE[Service Layer]
    REPO[Repository Layer]
    DRIVER[PyMongo]
    DB[(MongoDB)]

    CLIENT --> API
    API --> SERVICE
    SERVICE --> REPO
    REPO --> DRIVER
    DRIVER --> DB
```

This separation makes database behavior easier to test, optimize, secure, and replace.

## PyMongo

PyMongo is MongoDB's Python driver.

It provides:

- Connection management
- BSON encoding and decoding
- CRUD operations
- Aggregation
- Transactions
- Sessions
- Change streams
- Index management
- Authentication
- TLS
- Connection pooling
- Retryable reads and writes
- Server selection
- Read and write concern configuration

For most backend applications, using PyMongo directly is preferable to introducing an abstraction layer before its behavior is understood.

MongoDB's documentation also recommends that new Python users begin with the driver directly because PyMongo exposes MongoDB's actual programming model. :contentReference[oaicite:0]{index=0}

## Installing PyMongo

Install the current PyMongo release compatible with the application's Python and MongoDB Server versions.

```bash
python -m pip install pymongo
```

For an application:

```text
requirements.txt
```

```text
pymongo
```

For production, pin or otherwise constrain dependencies according to the project's dependency-management strategy and test driver upgrades against the target MongoDB Server version.

PyMongo compatibility should be checked whenever either the Python version, driver version, or MongoDB Server version changes. :contentReference[oaicite:1]{index=1}

## MongoDB Connection Architecture

A Python process normally creates a `MongoClient` and reuses it.

```text
Python Process
      │
      │ MongoClient
      ▼
Connection Pool
      │
      ├── Connection
      ├── Connection
      ├── Connection
      └── Connection
             │
             ▼
       MongoDB Deployment
```

PyMongo maintains connection pools and reuses connections rather than creating a new network connection for every operation. This reduces connection-establishment overhead and latency. :contentReference[oaicite:2]{index=2}

Do not create a new `MongoClient` for every HTTP request.

Bad:

```python
def get_user(user_id: str):
    client = MongoClient(MONGO_URI)
    return client.app.users.find_one({"_id": user_id})
```

Preferred:

```python
client = MongoClient(MONGO_URI)

def get_user(user_id: str):
    return client.app.users.find_one({"_id": user_id})
```

The client should normally live for the lifetime of the process.

## Connection URI

A MongoDB URI describes how the driver connects to the deployment.

Example:

```text
mongodb://username:password@mongo.internal:27017/orders?authSource=admin
```

For SRV-based deployments:

```text
mongodb+srv://username:password@cluster.example.mongodb.net/orders
```

A URI can contain:

- scheme
- username
- password
- hosts
- port
- database
- authentication options
- TLS options
- timeout options
- retry options
- read preference
- write concern

PyMongo accepts connection options either in the URI or as `MongoClient` arguments. :contentReference[oaicite:3]{index=3}

## Do Not Hard-Code Credentials

Avoid:

```python
client = MongoClient(
    "mongodb://admin:super-secret-password@mongo:27017"
)
```

Use environment configuration or a secret manager:

```python
import os

mongo_uri = os.environ["MONGO_URI"]

client = MongoClient(mongo_uri)
```

For production environments, a secret manager is preferable when available.

Typical options include:

- AWS Secrets Manager
- AWS Systems Manager Parameter Store
- Kubernetes Secrets with appropriate controls
- HashiCorp Vault
- Managed MongoDB secret integrations

## Configuration Object

Avoid scattering MongoDB configuration throughout the application.

A small configuration layer is easier to maintain:

```python
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class MongoSettings:
    uri: str
    database: str


def load_mongo_settings() -> MongoSettings:
    return MongoSettings(
        uri=os.environ["MONGO_URI"],
        database=os.environ["MONGO_DATABASE"],
    )
```

Then create the client from the configuration:

```python
from pymongo import MongoClient


settings = load_mongo_settings()

client = MongoClient(
    settings.uri,
    serverSelectionTimeoutMS=5000,
)
database = client[settings.database]
```

This keeps infrastructure configuration separate from business logic.

## Creating a MongoClient

Basic synchronous configuration:

```python
from pymongo import MongoClient

client = MongoClient(
    "mongodb://localhost:27017",
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
)

database = client["orders"]
orders = database["orders"]
```

Important distinction:

- `MongoClient` manages connectivity and topology.
- `Database` represents a logical MongoDB database.
- `Collection` represents a collection.
- Operations are executed through collections.

```python
client
  └── database
        └── collection
              └── operation
```

## Verifying Connectivity

A simple health check can use `ping`:

```python
from pymongo import MongoClient

client = MongoClient(
    mongo_uri,
    serverSelectionTimeoutMS=2000,
)

client.admin.command("ping")
```

A successful `MongoClient` construction alone does not necessarily prove that the deployment is reachable. MongoDB connection establishment and server selection can involve lazy behavior.

A health check should therefore perform an actual operation when connectivity must be verified.

## Database and Collection Access

```python
database = client["orders"]

orders = database["orders"]
customers = database["customers"]
```

Equivalent attribute access can work for simple names:

```python
orders = client.orders.orders
```

Explicit indexing is generally clearer and avoids issues with names that conflict with Python attributes.

## BSON and Python Types

MongoDB stores BSON rather than raw JSON.

PyMongo maps BSON types to Python types.

Common mappings include:

| MongoDB / BSON | Python |
|---|---|
| String | `str` |
| Boolean | `bool` |
| Int32 / Int64 | `int` |
| Double | `float` |
| Array | `list` |
| Embedded document | `dict` |
| Null | `None` |
| Date | `datetime.datetime` |
| ObjectId | `bson.ObjectId` |
| Binary | `bytes` / BSON binary types |
| Decimal128 | `bson.decimal128.Decimal128` |

This mapping matters when designing APIs because MongoDB documents are not automatically JSON-compatible Python dictionaries.

## ObjectId

MongoDB commonly uses `ObjectId` for `_id`.

Example:

```python
from bson import ObjectId

document = {
    "_id": ObjectId(),
    "email": "user@example.com",
}
```

When querying:

```python
document = orders.find_one({
    "_id": ObjectId(order_id),
})
```

Do not assume a client-provided string is automatically an `ObjectId`.

Validate it first:

```python
from bson import ObjectId
from bson.errors import InvalidId


def parse_object_id(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except InvalidId as exc:
        raise ValueError("Invalid object ID") from exc
```

## JSON Serialization

`ObjectId` is not a native JSON type.

This will not directly serialize through standard JSON encoding:

```python
{
    "_id": ObjectId("65f000000000000000000001")
}
```

For API responses, explicitly convert or use a serializer capable of handling BSON types.

Example:

```python
from bson import ObjectId


def serialize_order(document: dict) -> dict:
    return {
        "id": str(document["_id"]),
        "status": document["status"],
    }
```

Do not leak internal MongoDB document structure unnecessarily through public APIs.

## CRUD Operations

### Insert One

```python
result = orders.insert_one({
    "customer_id": "cust-100",
    "status": "pending",
    "total": 149.99,
})

order_id = result.inserted_id
```

`insert_one()` returns an `InsertOneResult`.

Use the returned `inserted_id` rather than assuming the application already knows the generated identifier.

### Insert Many

```python
result = orders.insert_many([
    {
        "customer_id": "cust-100",
        "status": "pending",
    },
    {
        "customer_id": "cust-101",
        "status": "confirmed",
    },
])

inserted_ids = result.inserted_ids
```

For large workloads, batch size and memory usage should be considered.

### Find One

```python
order = orders.find_one({
    "customer_id": "cust-100",
})
```

With projection:

```python
order = orders.find_one(
    {"customer_id": "cust-100"},
    {
        "_id": 1,
        "status": 1,
        "total": 1,
    },
)
```

Projection reduces unnecessary data transfer and decoding.

### Find Many

```python
cursor = orders.find({
    "status": "pending",
})
```

A cursor should generally be iterated rather than immediately converted to a potentially huge list.

```python
for order in cursor:
    process_order(order)
```

Avoid:

```python
orders = list(collection.find({}))
```

for an unbounded production collection.

## Sorting

```python
from pymongo import DESCENDING

cursor = orders.find(
    {"status": "pending"}
).sort(
    "created_at",
    DESCENDING,
)
```

Sorting large result sets without an appropriate index can be expensive.

A common production query might require:

```text
status = pending
ORDER BY created_at DESC
```

which should influence compound index design.

## Pagination

Offset pagination:

```python
cursor = (
    orders.find({"status": "pending"})
    .sort("_id", 1)
    .skip(offset)
    .limit(page_size)
)
```

This is simple but can become inefficient for large offsets.

For large collections, prefer cursor-based pagination.

Example:

```python
query = {
    "status": "pending",
}

if last_id is not None:
    query["_id"] = {"$gt": ObjectId(last_id)}

cursor = (
    orders.find(query)
    .sort("_id", 1)
    .limit(50)
)
```

Cursor-based pagination is generally more scalable for deep pagination because it avoids repeatedly skipping large numbers of documents.

## Query Construction

Build queries explicitly.

```python
query = {
    "status": "confirmed",
    "customer_id": customer_id,
}

order = orders.find_one(query)
```

Avoid passing arbitrary request dictionaries directly:

```python
# Unsafe design
query = request.json["query"]
orders.find(query)
```

This can expose operators and fields that the API was never intended to support.

## Updating Documents

Use update operators for partial updates:

```python
result = orders.update_one(
    {"_id": order_id},
    {
        "$set": {
            "status": "confirmed",
            "updated_at": datetime.now(timezone.utc),
        }
    },
)
```

Avoid replacing the entire document when only a few fields need to change.

### Update Many

```python
result = orders.update_many(
    {
        "status": "pending",
        "created_at": {
            "$lt": cutoff,
        },
    },
    {
        "$set": {
            "status": "expired",
        }
    },
)
```

Large bulk updates should be evaluated carefully because they can generate substantial write load.

## Upsert

An upsert updates a matching document or inserts one if no match exists.

```python
result = orders.update_one(
    {"external_id": external_id},
    {
        "$set": {
            "status": "confirmed",
            "updated_at": datetime.now(timezone.utc),
        }
    },
    upsert=True,
)
```

For idempotent operations, create a unique index on the natural identity:

```python
orders.create_index(
    "external_id",
    unique=True,
)
```

The unique index protects against concurrent duplicate creation.

## Delete Operations

Delete one:

```python
result = orders.delete_one({
    "_id": order_id,
})
```

Delete many:

```python
result = orders.delete_many({
    "status": "expired",
})
```

Production deletion should generally be:

- intentional
- bounded
- auditable where required
- protected against accidental broad filters

This is dangerous:

```python
orders.delete_many({})
```

## Bulk Writes

Bulk operations reduce application-to-database round trips.

```python
from pymongo import UpdateOne

operations = [
    UpdateOne(
        {"external_id": "A100"},
        {"$set": {"status": "confirmed"}},
        upsert=True,
    ),
    UpdateOne(
        {"external_id": "A101"},
        {"$set": {"status": "cancelled"}},
        upsert=True,
    ),
]

result = orders.bulk_write(
    operations,
    ordered=False,
)
```

`ordered=False` can improve throughput because independent operations do not necessarily wait for preceding operations in the same sequence.

Use unordered writes only when the application does not require strict operation ordering.

## Write Results

PyMongo exposes useful write metadata.

For example:

```python
result.matched_count
result.modified_count
result.upserted_id
```

Use these values when business logic depends on whether a document was actually modified.

Do not interpret `matched_count == 1` as proof that a field changed. A matched document may already contain the requested value.

## Atomicity

MongoDB provides atomicity for individual document writes.

For example:

```python
orders.update_one(
    {"_id": order_id},
    {
        "$set": {
            "status": "confirmed",
        }
    },
)
```

The update to that document is atomic.

If a business operation requires multiple documents to change atomically, use a transaction where appropriate.

Do not automatically introduce transactions for every operation.

## Sessions

Sessions group related operations and are required for transactions.

```python
with client.start_session() as session:
    result = orders.find_one(
        {"_id": order_id},
        session=session,
    )
```

Reuse the `MongoClient` and create sessions when needed rather than creating a new client for every transaction. :contentReference[oaicite:4]{index=4}

## Transactions

A transaction can coordinate multiple MongoDB operations atomically.

```python
from pymongo import MongoClient


def confirm_order(client: MongoClient, order_id):
    orders = client["orders"]["orders"]
    events = client["orders"]["events"]

    with client.start_session() as session:
        with session.start_transaction():
            orders.update_one(
                {"_id": order_id},
                {
                    "$set": {
                        "status": "confirmed",
                    }
                },
                session=session,
            )

            events.insert_one(
                {
                    "order_id": order_id,
                    "event": "order_confirmed",
                },
                session=session,
            )
```

If the transaction commits, both operations become part of the transaction's atomic unit. If it aborts, the transaction's changes are discarded. MongoDB transactions run within logical sessions. :contentReference[oaicite:5]{index=5}

## When to Use Transactions

Use transactions when multiple document operations must satisfy a business invariant atomically.

Examples:

- updating an order and its inventory record
- creating related financial records
- changing multiple documents that must remain consistent
- coordinating state changes across collections

Avoid using transactions merely because they exist.

Potential costs include:

- additional coordination
- longer-lived locks/resources
- increased latency
- reduced throughput for certain workloads
- more complex retry handling

Prefer data models that can satisfy the business operation with a single atomic document update when practical.

## Transaction Retry Behavior

Production transaction code must account for transient failures.

A transaction should not blindly retry arbitrary application exceptions.

Retry logic should distinguish:

- transient transaction errors
- commit uncertainty
- duplicate-key errors
- validation errors
- authorization errors
- permanent application errors

PyMongo provides transaction helpers and retry-related mechanisms that should be used according to the operation and failure semantics.

## Read Preference

Read preference controls where reads can be routed in a replica-set deployment.

Common modes include:

| Mode | Typical Use |
|---|---|
| `primary` | Strongest default consistency expectations |
| `primaryPreferred` | Prefer primary, tolerate fallback |
| `secondary` | Read from secondaries |
| `secondaryPreferred` | Prefer secondary |
| `nearest` | Lowest-latency suitable member |

Example:

```python
from pymongo import MongoClient, ReadPreference

client = MongoClient(
    mongo_uri,
    read_preference=ReadPreference.PRIMARY,
)
```

Do not route reads to secondaries merely to increase capacity without understanding:

- replication lag
- consistency requirements
- stale reads
- workload characteristics

## Write Concern

Write concern determines how much acknowledgement the application requires.

A common production choice is:

```python
from pymongo import MongoClient, WriteConcern

client = MongoClient(
    mongo_uri,
    w="majority",
)
```

The correct write concern depends on durability and availability requirements.

Unacknowledged writes may reduce waiting but provide weaker feedback about whether the server accepted the operation.

## Retryable Reads and Writes

PyMongo can automatically retry certain read and write operations once when supported by the deployment and operation type. :contentReference[oaicite:6]{index=6}

This improves resilience against transient network or server failures.

However, application-level idempotency is still important.

For example:

```text
POST request
    ↓
MongoDB write
    ↓
Network failure before response
    ↓
Client retries
```

If the operation is not safely repeatable, a retry can create an unintended duplicate.

Use:

- unique business identifiers
- upserts
- idempotency keys
- transaction semantics where appropriate

## Timeouts

Production MongoDB clients should not rely on infinite waits.

Important timeout concepts include:

| Setting | Purpose |
|---|---|
| `serverSelectionTimeoutMS` | Time allowed to select a suitable server |
| `connectTimeoutMS` | Time allowed to establish a new connection |
| `socketTimeoutMS` | Time waiting for a socket response |
| `waitQueueTimeoutMS` | Time waiting for a connection from the pool |
| `timeoutMS` | Client-side operation timeout |

PyMongo also provides a client-side `timeout()` mechanism that can bound the complete operation lifecycle, including server selection, connection checkout, serialization, and server-side execution. :contentReference[oaicite:7]{index=7}

Example:

```python
from pymongo import MongoClient

client = MongoClient(
    mongo_uri,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    socketTimeoutMS=10000,
)
```

Timeouts should be selected according to the application's latency budget rather than copied blindly.

## Connection Pooling

PyMongo maintains a pool of connections per server.

Relevant settings include:

```python
client = MongoClient(
    mongo_uri,
    maxPoolSize=100,
    minPoolSize=5,
    maxIdleTimeMS=60000,
    waitQueueTimeoutMS=5000,
)
```

Important considerations:

- `maxPoolSize` limits concurrent connections maintained by a pool.
- `minPoolSize` can maintain a baseline number of connections.
- `maxIdleTimeMS` removes idle connections after the configured period.
- `waitQueueTimeoutMS` bounds how long an operation waits for a pool connection.

PyMongo documents `100` as the default `maxPoolSize`; actual production values should be based on workload, process count, database capacity, and latency requirements. :contentReference[oaicite:8]{index=8}

## Pool Sizing

Do not think about pool size in isolation.

If:

```text
20 application pods
×
100 maximum connections
=
2000 potential connections
```

the MongoDB deployment must be capable of handling that connection load.

A larger pool does not automatically produce higher throughput.

Oversized pools can create:

- connection pressure
- context switching
- memory overhead
- increased server resource usage

Start with measured values and tune based on concurrency and latency.

## Connection Pooling in Web Applications

For a synchronous WSGI application:

```text
Worker Process
   │
   └── MongoClient
          │
          └── Connection Pool
```

Each process has its own client and pool.

Therefore:

```text
8 processes × maxPoolSize=100
```

can potentially represent roughly 800 pooled connections across those processes.

This matters when scaling Gunicorn, Celery, Kubernetes replicas, or other worker processes.

## Forking Considerations

Do not create a `MongoClient` in a parent process and then blindly share it across forked application workers.

Create the client in the process that will use it.

For example, with a process-based application server:

```text
Master
  │
  ├── Worker 1 → MongoClient
  ├── Worker 2 → MongoClient
  └── Worker 3 → MongoClient
```

This gives each process its own connection pool.

## Error Handling

Catch specific exceptions where application behavior depends on the failure.

Example:

```python
from pymongo.errors import (
    DuplicateKeyError,
    ServerSelectionTimeoutError,
)


try:
    orders.insert_one(document)
except DuplicateKeyError:
    raise ValueError("Order already exists")
except ServerSelectionTimeoutError:
    raise RuntimeError("Database temporarily unavailable")
```

Do not expose raw database exceptions to API consumers.

## Error Mapping

A service layer should translate infrastructure failures into application-level outcomes.

```text
MongoDB Exception
       ↓
Repository
       ↓
Domain / Application Error
       ↓
API Error Response
```

For example:

```text
DuplicateKeyError
        ↓
OrderAlreadyExists
        ↓
HTTP 409 Conflict
```

while:

```text
ServerSelectionTimeoutError
        ↓
DatabaseUnavailable
        ↓
HTTP 503 Service Unavailable
```

This prevents MongoDB implementation details from leaking into the API contract.

## Repository Pattern

A repository encapsulates MongoDB access.

```python
from bson import ObjectId


class OrderRepository:
    def __init__(self, collection):
        self.collection = collection

    def get_by_id(self, order_id: ObjectId):
        return self.collection.find_one({
            "_id": order_id,
        })

    def create(self, document: dict):
        result = self.collection.insert_one(document)
        return result.inserted_id

    def update_status(self, order_id: ObjectId, status: str):
        return self.collection.update_one(
            {"_id": order_id},
            {"$set": {"status": status}},
        )
```

The repository should focus on persistence behavior rather than business rules.

## Service Layer

Business rules belong above the repository.

```python
class OrderService:
    def __init__(self, repository):
        self.repository = repository

    def confirm_order(self, order_id):
        order = self.repository.get_by_id(order_id)

        if order is None:
            raise ValueError("Order not found")

        if order["status"] != "pending":
            raise ValueError("Order cannot be confirmed")

        self.repository.update_status(
            order_id,
            "confirmed",
        )
```

This separation makes business logic easier to test independently of MongoDB.

## Repository vs ODM

An ODM such as MongoEngine can provide:

- model definitions
- validation
- higher-level querying
- relationship-like abstractions

However, abstraction can hide MongoDB behavior.

For senior backend work, understand PyMongo first.

Use an ODM when it provides meaningful productivity or consistency benefits without hiding important performance and database semantics.

MongoDB documents MongoEngine as an ORM-like layer maintained outside the core PyMongo driver. :contentReference[oaicite:9]{index=9}

## Aggregation from Python

PyMongo accepts aggregation pipelines as Python lists.

```python
pipeline = [
    {
        "$match": {
            "status": "confirmed",
        }
    },
    {
        "$group": {
            "_id": "$customer_id",
            "total_orders": {"$sum": 1},
            "total_value": {"$sum": "$total"},
        }
    },
    {
        "$sort": {
            "total_value": -1,
        }
    },
]

cursor = orders.aggregate(pipeline)

for document in cursor:
    process(document)
```

Keep aggregation pipelines close to the repository or query layer rather than embedding complex MongoDB expressions directly inside API handlers.

## Aggregation and Security

Do not accept an unrestricted pipeline from an external API.

Avoid:

```python
pipeline = request.json["pipeline"]

collection.aggregate(pipeline)
```

Instead, construct supported stages explicitly:

```python
pipeline = [
    {"$match": {"status": validated_status}},
    {"$group": {
        "_id": "$customer_id",
        "count": {"$sum": 1},
    }},
]
```

This prevents clients from invoking operations the endpoint was never intended to expose.

## Bulk Operations from Python

For high-throughput ingestion:

```python
from pymongo import InsertOne

operations = [
    InsertOne(document)
    for document in documents
]

result = collection.bulk_write(
    operations,
    ordered=False,
)
```

Batching can reduce network round trips, but do not create arbitrarily large batches.

Consider:

- document size
- memory usage
- network payload
- server load
- error handling
- retry behavior

## Index Management

Indexes should be created deliberately.

Example:

```python
orders.create_index(
    [
        ("customer_id", 1),
        ("created_at", -1),
    ],
    name="customer_created_at",
)
```

A repository or deployment migration process can manage indexes.

Avoid creating indexes on application startup on every process.

If ten Kubernetes pods all attempt index-management operations during startup, deployment behavior becomes unnecessarily coupled to database administration.

Prefer controlled migration or provisioning workflows for production index changes.

## Query and Index Alignment

Suppose the application frequently executes:

```python
orders.find({
    "customer_id": customer_id,
    "status": "confirmed",
}).sort(
    "created_at",
    -1,
)
```

The query pattern suggests evaluating a compound index such as:

```python
orders.create_index([
    ("customer_id", 1),
    ("status", 1),
    ("created_at", -1),
])
```

The exact index must be validated with realistic data and `explain()`.

Do not design indexes from field names alone.

Design them from actual workload patterns.

## Explain from Python

Use `explain()` to understand query execution.

For example:

```python
plan = orders.find(
    {
        "customer_id": customer_id,
        "status": "confirmed",
    }
).sort(
    "created_at",
    -1,
).explain()
```

Important metrics include:

- `nReturned`
- `totalKeysExamined`
- `totalDocsExamined`
- execution time
- winning plan
- rejected plans

A useful target is generally to avoid examining dramatically more documents than the query returns.

## Slow Query Investigation

A senior engineer should follow:

```text
Slow request
    ↓
Measure API latency
    ↓
Measure MongoDB operation latency
    ↓
Capture actual query shape
    ↓
Run explain()
    ↓
Inspect index usage
    ↓
Compare keys/docs examined
    ↓
Check collection size and working set
    ↓
Check server load
    ↓
Optimize
    ↓
Measure again
```

Do not immediately add an index without understanding the query plan.

## FastAPI Integration

FastAPI is naturally compatible with asynchronous Python.

Current PyMongo provides both synchronous and asynchronous APIs. The PyMongo Async API became generally available in PyMongo 4.13. :contentReference[oaicite:10]{index=10}

For an asynchronous FastAPI application, use `AsyncMongoClient` when the application benefits from native asynchronous database I/O.

```python
from pymongo import AsyncMongoClient

client = AsyncMongoClient(
    mongo_uri,
    serverSelectionTimeoutMS=5000,
)

database = client["orders"]
orders = database["orders"]
```

Network operations are awaited:

```python
document = await orders.find_one({
    "_id": order_id,
})
```

`find()` returns an asynchronous cursor:

```python
cursor = orders.find({
    "status": "pending",
})

async for document in cursor:
    process(document)
```

## Synchronous vs Asynchronous PyMongo

| Workload | Recommended Direction |
|---|---|
| Simple synchronous service | `MongoClient` |
| Traditional synchronous application | `MongoClient` |
| CPU-heavy service with limited DB concurrency | Evaluate synchronous PyMongo |
| Highly concurrent async API | `AsyncMongoClient` |
| FastAPI with substantial async I/O | `AsyncMongoClient` |
| Existing Motor application | Plan migration to PyMongo Async |

MongoDB currently recommends PyMongo Async as the replacement for Motor and states that Motor is scheduled for deprecation on May 14, 2026. :contentReference[oaicite:11]{index=11}

PyMongo's documentation describes synchronous PyMongo as a good fit for simpler or serial workloads and PyMongo Async as appropriate for highly concurrent workloads and applications using asynchronous frameworks such as FastAPI. :contentReference[oaicite:12]{index=12}

## FastAPI Application Lifecycle

A production FastAPI application should manage the MongoDB client at application scope rather than creating it per request.

Conceptually:

```text
Application Startup
       ↓
Create AsyncMongoClient
       ↓
Application Running
       ↓
Reuse Client / Pool
       ↓
Application Shutdown
       ↓
Close Client
```

Example:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pymongo import AsyncMongoClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncMongoClient(
        mongo_uri,
        serverSelectionTimeoutMS=5000,
    )

    app.state.mongo_client = client
    app.state.mongo_db = client["orders"]

    await client.admin.command("ping")

    try:
        yield
    finally:
        await client.close()


app = FastAPI(lifespan=lifespan)
```

This keeps the connection lifecycle aligned with the application lifecycle.

## FastAPI Dependency Injection

Expose repositories through dependencies rather than creating database clients inside route handlers.

```python
from fastapi import Request


def get_order_repository(request: Request) -> OrderRepository:
    collection = request.app.state.mongo_db["orders"]
    return OrderRepository(collection)
```

Then:

```python
from fastapi import Depends, FastAPI

app = FastAPI()


@app.get("/orders/{order_id}")
async def get_order(
    order_id: str,
    repository: OrderRepository = Depends(get_order_repository),
):
    return await repository.get_by_id(order_id)
```

For an async repository, repository methods should use `await` for network operations.

## Async Repository

```python
from bson import ObjectId


class AsyncOrderRepository:
    def __init__(self, collection):
        self.collection = collection

    async def get_by_id(self, order_id: ObjectId):
        return await self.collection.find_one({
            "_id": order_id,
        })

    async def create(self, document: dict):
        result = await self.collection.insert_one(document)
        return result.inserted_id
```

The repository owns MongoDB-specific details.

The service layer should not need to know whether the database implementation uses PyMongo synchronous or asynchronous APIs unless that distinction is part of the application architecture.

## Pydantic and MongoDB Documents

API models should represent API contracts, not necessarily raw MongoDB documents.

For example:

```python
from decimal import Decimal

from pydantic import BaseModel, Field


class OrderResponse(BaseModel):
    id: str
    customer_id: str
    status: str
    total: Decimal = Field(ge=0)
```

The repository can map MongoDB documents to API models:

```python
def to_order_response(document: dict) -> OrderResponse:
    return OrderResponse(
        id=str(document["_id"]),
        customer_id=document["customer_id"],
        status=document["status"],
        total=document["total"],
    )
```

This prevents database representation from becoming an accidental public API contract.

## FastAPI Error Handling

Database failures should be converted to controlled HTTP responses.

```python
from fastapi import HTTPException
from pymongo.errors import ServerSelectionTimeoutError


try:
    document = await collection.find_one({"_id": order_id})
except ServerSelectionTimeoutError:
    raise HTTPException(
        status_code=503,
        detail="Database temporarily unavailable",
    )
```

Do not return:

```python
str(exc)
```

to clients.

## Django Integration

Django is primarily designed around relational database integrations and its native ORM.

MongoDB should therefore be integrated deliberately rather than pretending MongoDB is a relational database.

A practical architecture is:

```text
Django
  │
  ├── Views / DRF
  │
  ├── Serializers
  │
  ├── Services
  │
  └── Repositories
          │
          ▼
       PyMongo
          │
          ▼
       MongoDB
```

This avoids coupling application business logic directly to MongoDB driver calls.

## Django with PyMongo

A small repository can encapsulate the driver:

```python
from bson import ObjectId


class OrderRepository:
    def __init__(self, collection):
        self.collection = collection

    def get(self, order_id: str):
        return self.collection.find_one({
            "_id": ObjectId(order_id),
        })
```

Django configuration should provide the connection settings rather than constructing arbitrary clients throughout views.

## Django Service Layer

Business rules should remain outside the repository:

```python
class OrderService:
    def __init__(self, repository):
        self.repository = repository

    def get_order(self, order_id: str):
        order = self.repository.get(order_id)

        if order is None:
            raise OrderNotFound()

        return order
```

This makes the integration easier to test and prevents Django views from becoming database-heavy.

## MongoEngine

MongoEngine is an ODM that provides model-like abstractions over MongoDB.

Example:

```python
from mongoengine import Document, StringField


class Order(Document):
    customer_id = StringField(required=True)
    status = StringField(required=True)
```

An ODM can be useful when:

- model-oriented development is important
- application validation benefits from model definitions
- the team prefers an ODM abstraction

However, an ODM can hide MongoDB query and performance characteristics.

For complex production workloads, engineers should still understand:

- generated queries
- indexes
- aggregation
- document shape
- connection behavior
- transactions
- MongoDB execution plans

## MongoDB with Celery

Celery workers are independent Python processes.

Do not assume the API application's MongoDB client can be shared with Celery workers.

Use a worker-local client:

```text
FastAPI Process
    └── MongoClient / AsyncMongoClient
         └── Pool

Celery Worker
    └── MongoClient
         └── Pool
```

This is especially important when the worker process model creates separate processes.

## MongoDB with Kafka

MongoDB change streams can be consumed by Python services and forwarded to Kafka.

```mermaid
flowchart LR
    DB[(MongoDB)]
    CS[Change Stream]
    CONSUMER[Python Consumer]
    KAFKA[Kafka]
    SERVICE[Downstream Services]

    DB --> CS
    CS --> CONSUMER
    CONSUMER --> KAFKA
    KAFKA --> SERVICE
```

The consumer should handle:

- resume tokens
- reconnects
- duplicate processing
- idempotency
- offset/state management
- shutdown
- backpressure

Do not assume that receiving a change event exactly once eliminates the need for idempotent downstream processing.

## Change Streams from Python

A synchronous consumer can use:

```python
with client.start_session() as session:
    with orders.watch(
        full_document="updateLookup"
    ) as stream:
        for change in stream:
            process_change(change)
```

A production consumer should persist or otherwise safely manage resume information and ensure processing is idempotent.

For long-running consumers, also monitor:

- connection health
- event-processing latency
- consumer lag
- errors
- reconnect frequency

## Testing MongoDB Code

Database integration tests should test against a real MongoDB-compatible environment whenever the behavior being tested depends on MongoDB semantics.

Unit tests can mock repositories:

```text
Service
   ↓
Mock Repository
```

Integration tests should exercise:

```text
Repository
   ↓
PyMongo
   ↓
MongoDB
```

This is important for behavior involving:

- indexes
- unique constraints
- transactions
- ObjectId
- aggregation
- update semantics
- query operators
- write concerns
- change streams

Mocking PyMongo cannot validate MongoDB's actual query planner or server semantics.

## Test Containers

A containerized MongoDB instance can be useful for CI integration tests.

Conceptually:

```text
CI Job
 ├── Python Tests
 └── MongoDB Container
        ↓
     Integration Tests
```

For tests requiring replica-set features such as transactions or change streams, the test MongoDB deployment must be configured appropriately.

## Testing Repository Behavior

Example:

```python
def test_get_order(repository, order):
    result = repository.get(order["_id"])

    assert result is not None
    assert result["_id"] == order["_id"]
```

Important repository tests should cover:

- document creation
- missing documents
- duplicate keys
- updates
- deletes
- pagination
- invalid identifiers
- aggregation
- transaction behavior
- timeout behavior

## Testing Indexes

Indexes are part of application behavior.

Integration tests or deployment validation should verify required indexes exist.

Example:

```python
indexes = collection.index_information()

assert "customer_created_at" in indexes
```

For production-critical workloads, index presence alone is not enough. Query-plan testing or performance tests may also be appropriate.

## Security Configuration

A production Python MongoDB client should typically consider:

```python
from pymongo import MongoClient

client = MongoClient(
    mongo_uri,
    tls=True,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    socketTimeoutMS=10000,
)
```

The actual TLS and authentication settings depend on the deployment.

Never disable certificate validation simply to resolve a connectivity problem.

## Stable API

For applications that need a stable MongoDB command API across supported server versions, PyMongo supports MongoDB's Stable API.

Example:

```python
from pymongo import MongoClient
from pymongo.server_api import ServerApi

client = MongoClient(
    mongo_uri,
    server_api=ServerApi(
        "1",
        strict=True,
        deprecation_errors=True,
    ),
)
```

Stable API can reduce compatibility surprises during server upgrades by constraining the application to supported API behavior. :contentReference[oaicite:13]{index=13}

## Production Configuration Example

A practical synchronous service configuration might look like:

```python
import os

from pymongo import MongoClient
from pymongo.server_api import ServerApi


client = MongoClient(
    os.environ["MONGO_URI"],
    server_api=ServerApi(
        "1",
        strict=True,
        deprecation_errors=True,
    ),
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    socketTimeoutMS=10000,
    maxPoolSize=100,
    retryReads=True,
    retryWrites=True,
)

database = client[os.environ["MONGO_DATABASE"]]
```

These values are examples, not universal production defaults. Pool sizes and timeouts should be derived from workload characteristics and measured latency.

## Production Application Architecture

A mature Python application can use:

```text
                    ┌─────────────────┐
                    │   REST / gRPC   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Authentication  │
                    │ Authorization   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Service Layer   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Repository      │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ PyMongo         │
                    │ Client          │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │ Connection Pool │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ MongoDB         │
                    │ Replica Set     │
                    └─────────────────┘
```

Cross-cutting concerns should include:

- structured logging
- metrics
- tracing
- timeout policies
- error classification
- security controls
- configuration management

## Observability

Measure MongoDB behavior from the application side as well as the database side.

Useful application metrics include:

- operation latency
- operation count
- error rate
- timeout rate
- connection-pool wait time
- retry count
- query-specific latency
- transaction latency
- bulk-operation throughput

A useful request trace is:

```text
HTTP Request
    ↓
Service
    ↓
Repository
    ↓
PyMongo
    ↓
MongoDB
    ↓
Response
```

Tracing should make it possible to determine whether latency comes from:

- application processing
- connection acquisition
- network
- MongoDB server execution
- serialization
- downstream dependencies

## Logging

Log database operations at a useful abstraction level.

Good:

```text
order_lookup
order_id=...
duration_ms=...
result=found
```

Avoid logging:

```text
mongodb://user:password@host/database
```

or entire sensitive MongoDB documents.

Logs should support debugging without becoming a second database containing sensitive production data.

## Performance Considerations

### Reuse Clients

Creating clients repeatedly increases connection overhead.

Prefer:

```text
Process
  ↓
One long-lived MongoClient
  ↓
Connection pool
```

### Avoid Huge Documents

Do not retrieve fields the API does not need.

Use projections:

```python
collection.find(
    {"status": "active"},
    {
        "_id": 1,
        "customer_id": 1,
        "status": 1,
    },
)
```

### Bound Result Sets

Always consider:

```python
.limit(page_size)
```

for API-facing queries.

### Use Indexes Based on Workload

Do not create indexes simply because a field exists.

Measure:

```text
Query
 ↓
Explain
 ↓
Index behavior
 ↓
Latency
 ↓
Production workload
```

## Before and After Query Optimization

Before:

```python
cursor = orders.find({
    "customer_id": customer_id,
}).sort(
    "created_at",
    -1,
).skip(
    100000,
).limit(
    50,
)
```

Potential issues:

- deep `skip`
- expensive traversal
- missing compound index
- unnecessary fields

After:

```python
query = {
    "customer_id": customer_id,
    "created_at": {"$lt": last_seen_created_at},
}

cursor = orders.find(
    query,
    {
        "_id": 1,
        "status": 1,
        "created_at": 1,
    },
).sort(
    "created_at",
    -1,
).limit(50)
```

With an appropriate index such as:

```python
orders.create_index([
    ("customer_id", 1),
    ("created_at", -1),
])
```

the query can scale more predictably for cursor-based pagination.

The exact index and query shape must still be validated using realistic data and `explain()`.

## Common Mistakes

### Creating a Client Per Request

**Problem:**

```python
def endpoint():
    client = MongoClient(uri)
```

**Why it is wrong:**

Repeated client creation increases connection and topology-management overhead.

**Better:**

Create and reuse a process-level client.

### Creating a Client Per Query

Even worse:

```python
def find_order(order_id):
    client = MongoClient(uri)
    return client.db.orders.find_one({"_id": order_id})
```

Use the existing client.

### Loading Entire Collections

Avoid:

```python
documents = list(collection.find({}))
```

unless the dataset is explicitly bounded and small.

Prefer:

```python
for document in collection.find({}):
    process(document)
```

or use explicit pagination/batching.

### Using Arbitrary Request Filters

Avoid:

```python
collection.find(request.json)
```

This creates a dangerous coupling between the external API and MongoDB's query language.

### Ignoring ObjectId Conversion

Avoid querying:

```python
{"_id": "65f000000000000000000001"}
```

when `_id` is stored as an `ObjectId`.

Convert and validate the identifier.

### Returning Raw MongoDB Documents

Returning internal MongoDB documents directly can:

- expose internal fields
- leak implementation details
- create accidental API contracts
- cause serialization problems

Use explicit response models.

### Ignoring Indexes

Application code can be logically correct and still be operationally poor.

A query that works against 10,000 documents may become unacceptable against 100 million documents.

### Unbounded Regex

Do not expose arbitrary regex expressions through public APIs.

### No Timeouts

An application without sensible timeouts can accumulate blocked requests during database degradation.

### Excessive Pool Size

A large connection pool per process multiplied across many replicas can overload the database.

### Using Transactions Everywhere

Transactions are useful for specific consistency requirements but add coordination and operational cost.

Prefer atomic single-document operations or appropriate schema design when possible.

## Production Pitfalls

### Pool Size Multiplied by Replicas

If:

```text
10 Kubernetes Pods
×
100 connections
=
1000 potential pooled connections
```

then increasing `maxPoolSize` may create database pressure rather than improve performance.

### Async/Synchronous Mismatch

Using synchronous MongoDB operations inside an async application can block the event loop.

For highly concurrent async applications, evaluate PyMongo's native async API.

Conversely, introducing asynchronous infrastructure into a simple synchronous service can add complexity without meaningful benefit.

### Motor Migration

Existing Motor applications should have a migration strategy because MongoDB documents Motor's deprecation for May 14, 2026 and recommends the PyMongo Async API as its replacement. :contentReference[oaicite:14]{index=14}

### Blocking Calls in FastAPI

Avoid:

```python
@app.get("/orders")
async def get_orders():
    return list(sync_collection.find({}))
```

when this executes blocking database I/O directly on the async event loop.

Use `AsyncMongoClient` for an appropriate async architecture, or deliberately isolate synchronous work from the event loop.

### Startup Index Creation

Avoid making every application replica responsible for production index administration.

Prefer:

```text
Migration / Provisioning Job
        ↓
Create / Validate Indexes
        ↓
Application Deployment
```

### Logging Sensitive Documents

Avoid dumping complete MongoDB documents into application logs.

The database may contain:

- personal information
- financial data
- tokens
- internal identifiers
- authentication-related information

Log identifiers and metadata required for diagnosis instead.

## Security Considerations

A production Python integration should enforce:

- TLS
- certificate validation
- authentication
- least-privilege MongoDB roles
- secret management
- query validation
- tenant isolation
- bounded pagination
- controlled error responses
- safe logging

A connection string is a credential-bearing artifact and should be treated as secret data.

## Deployment with Docker

A containerized Python service might receive its connection string through the environment:

```yaml
services:
  api:
    image: orders-api:latest
    environment:
      MONGO_URI: ${MONGO_URI}
      MONGO_DATABASE: orders
```

Do not commit:

```text
MONGO_URI=mongodb://admin:password@mongo:27017
```

to the repository.

For production, inject secrets through the deployment platform or a dedicated secret-management system.

## Deployment with Kubernetes

A simplified configuration can use a secret reference:

```yaml
env:
  - name: MONGO_URI
    valueFrom:
      secretKeyRef:
        name: orders-mongodb
        key: uri
```

The Kubernetes Secret itself should be protected through appropriate cluster RBAC, encryption-at-rest configuration, and external secret-management practices where required.

## AWS Deployment

A common architecture is:

```text
                    AWS VPC
                       │
        ┌──────────────┴──────────────┐
        │                             │
 Public Subnets                Private Subnets
        │                             │
 Load Balancer                 Python Services
                                      │
                                      ▼
                              MongoDB / Atlas
```

Use AWS-specific controls such as:

- security groups
- private routing
- Secrets Manager
- KMS
- CloudWatch
- IAM for supporting infrastructure

MongoDB itself should still enforce its own authentication and authorization model.

## High Availability

The Python application should tolerate MongoDB topology changes.

Production clients should be configured with:

- appropriate server selection timeout
- retryable reads/writes where supported
- suitable write concern
- suitable read preference
- connection pooling
- error handling

Application logic should distinguish temporary database unavailability from permanent application errors.

## Health Checks

A readiness check may verify MongoDB connectivity:

```python
def check_database(client):
    client.admin.command("ping")
    return True
```

Do not necessarily use an expensive database query for every health probe.

For Kubernetes, distinguish:

```text
Liveness
    Is the application process alive?

Readiness
    Can the application safely receive traffic?
```

Database unavailability may need to affect readiness without causing unnecessary process restarts.

## Graceful Shutdown

The application should close its MongoDB client during shutdown.

For synchronous applications:

```python
client.close()
```

For asynchronous applications:

```python
await client.close()
```

This allows resources to be released cleanly.

## Operational Runbook

### Database Connectivity Failure

```text
Symptom
↓
Application cannot connect to MongoDB
↓
Possible causes
    - DNS failure
    - network policy
    - firewall/security group
    - TLS failure
    - authentication failure
    - server unavailable
    - connection pool exhaustion
↓
Isolation strategy
↓
Check application logs
↓
Check DNS / network path
↓
Run MongoDB ping
↓
Check MongoDB deployment health
↓
Check credentials and certificates
↓
Inspect pool and timeout metrics
↓
Root cause
↓
Corrective action
↓
Prevention
    - monitoring
    - tested configuration
    - sensible timeouts
    - certificate rotation
```

## Authentication Failure

```text
Symptom
↓
MongoDB authentication error
↓
Possible causes
    - wrong password
    - wrong authSource
    - disabled user
    - incorrect authentication mechanism
    - stale secret
    - certificate problem
↓
Isolation strategy
↓
Verify connection configuration
↓
Verify secret source
↓
Test with controlled mongosh access
↓
Check MongoDB authentication logs
↓
Root cause
↓
Corrective action
↓
Prevention
    - secret rotation workflow
    - configuration validation
    - monitoring
```

## Slow MongoDB Operation

```text
Symptom
↓
API latency increased
↓
Possible causes
    - missing index
    - inefficient query
    - large result set
    - deep pagination
    - connection pool exhaustion
    - server resource pressure
    - replication effects
↓
Isolation strategy
↓
Measure API and database latency
↓
Capture query shape
↓
Run explain()
↓
Inspect keys/docs examined
↓
Inspect MongoDB server metrics
↓
Root cause
↓
Corrective action
↓
Prevention
    - index review
    - query regression tests
    - performance monitoring
```

## Connection Pool Exhaustion

```text
Symptom
↓
Requests wait for MongoDB connections
↓
Possible causes
    - maxPoolSize too small
    - slow queries
    - long transactions
    - connection leaks
    - excessive application concurrency
↓
Isolation strategy
↓
Inspect pool wait metrics
↓
Inspect query latency
↓
Inspect transaction duration
↓
Check application replica count
↓
Root cause
↓
Corrective action
↓
Prevention
    - tune pool size
    - optimize queries
    - enforce timeouts
    - control concurrency
```

## Duplicate Key Error

```text
Symptom
↓
DuplicateKeyError
↓
Possible causes
    - repeated request
    - missing idempotency handling
    - concurrent inserts
    - incorrect unique-key design
↓
Isolation strategy
↓
Identify unique index
↓
Inspect conflicting key
↓
Check request retry behavior
↓
Root cause
↓
Corrective action
↓
Prevention
    - unique indexes
    - idempotency keys
    - upserts
    - correct retry semantics
```

## Driver Upgrade Strategy

Before upgrading PyMongo:

1. Check Python compatibility.
2. Check MongoDB Server compatibility.
3. Review breaking changes.
4. Review deprecations.
5. Run unit tests.
6. Run MongoDB integration tests.
7. Run query and transaction tests.
8. Validate TLS and authentication.
9. Benchmark critical workloads.
10. Deploy progressively.

MongoDB recommends checking driver, server, and Python compatibility before upgrades and recommends Stable API usage where appropriate to reduce future API compatibility changes. :contentReference[oaicite:15]{index=15}

## Interview Considerations

### Why should `MongoClient` be reused?

Because PyMongo maintains connection pools and topology state. Reusing the client avoids repeatedly establishing connections and allows operations to reuse pooled connections.

### Should a MongoClient be created for every request?

No. A long-lived client should normally be reused within the process.

### What is the difference between MongoClient, Database, and Collection?

```text
MongoClient
    ↓
Database
    ↓
Collection
    ↓
Documents
```

`MongoClient` manages connectivity, `Database` identifies a MongoDB database, and `Collection` represents a collection within that database.

### Why use a repository layer?

It isolates MongoDB-specific persistence logic from business logic and API code, making testing, query optimization, and architectural changes easier.

### When should you use a transaction?

Use a transaction when multiple operations must satisfy an atomic business invariant and cannot be modeled safely as a single-document operation.

### Why are indexes important in Python applications?

The Python code may execute correctly while MongoDB performs an inefficient collection scan. Indexes and query design determine database-side performance.

### Why can large `skip()` values be problematic?

The database may need to traverse many earlier results before returning the requested page. Cursor-based pagination can provide more predictable behavior for large datasets.

### Should FastAPI always use asynchronous MongoDB access?

Not automatically.

For highly concurrent asynchronous workloads, PyMongo's native async API is appropriate. For simple or primarily synchronous workloads, synchronous PyMongo may be simpler and sufficient. MongoDB explicitly distinguishes these trade-offs in its current PyMongo guidance. :contentReference[oaicite:16]{index=16}

### What should replace Motor in new async Python applications?

PyMongo's native asynchronous API is the current direction recommended by MongoDB. `AsyncMongoClient` provides native `asyncio` support, while Motor is scheduled for deprecation in May 2026. :contentReference[oaicite:17]{index=17}

### How do you prevent MongoDB credentials from leaking?

Use secret management, avoid hard-coded URIs, redact connection strings from logs, restrict secret access, rotate credentials, and avoid returning raw database errors.

## Key Takeaways

- **Use a long-lived PyMongo client per application process and let its connection pool manage database connections instead of creating clients per request.**
- **Keep MongoDB access behind repositories and service layers so query construction, transactions, indexes, error handling, and security policies remain maintainable.**
- **Choose synchronous PyMongo or the native PyMongo Async API based on the application's concurrency model; for modern highly concurrent async workloads, `AsyncMongoClient` is the current MongoDB-supported direction.**
- **Production Python integrations require explicit timeout, retry, pooling, indexing, serialization, authentication, TLS, and error-handling strategies rather than relying on driver defaults.**
- **Treat MongoDB behavior as part of the application's architecture: validate queries, design indexes from access patterns, test against real MongoDB semantics, and measure database performance independently from API performance.**