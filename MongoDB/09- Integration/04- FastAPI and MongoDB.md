# 04- FastAPI and MongoDB

## Overview

FastAPI and MongoDB form a natural combination for asynchronous API workloads: FastAPI provides the HTTP/API layer and concurrency model, while MongoDB provides document-oriented persistence.

For new asynchronous Python services, the current MongoDB Python driver provides `AsyncMongoClient`, allowing database operations to participate directly in Python's `asyncio` execution model. MongoDB's current FastAPI integration guidance uses `AsyncMongoClient` together with FastAPI's `lifespan` mechanism for connection lifecycle management. :contentReference[oaicite:0]{index=0}

A production architecture should separate API concerns from persistence concerns:

```text
Client
  ↓
Nginx / Load Balancer
  ↓
FastAPI
  ↓
Router
  ↓
Pydantic API Schema
  ↓
Service Layer
  ↓
Repository
  ↓
PyMongo Async
  ↓
MongoDB
```

The important engineering principle is that FastAPI should not become a thin wrapper around arbitrary MongoDB queries. The API layer should expose business operations, while repositories own persistence details.

## FastAPI and MongoDB Architecture

A typical production service can be organized as:

```text
app/
├── main.py
├── config.py
├── db/
│   └── mongodb.py
├── models/
│   └── order.py
├── schemas/
│   └── order.py
├── repositories/
│   └── order.py
├── services/
│   └── order.py
└── api/
    └── orders.py
```

Responsibilities:

| Layer | Responsibility |
|---|---|
| Router | HTTP routing, status codes, dependency injection |
| Schema | Request/response validation |
| Service | Business rules and workflows |
| Repository | MongoDB persistence |
| Database module | Client and database lifecycle |
| MongoDB | Durable document storage |

This structure prevents MongoDB-specific details from leaking throughout the application.

## Why Async MongoDB Matters

FastAPI supports asynchronous request handlers using Python's `asyncio` model.

A database request is I/O-bound:

```text
FastAPI coroutine
      ↓
MongoDB request
      ↓
await
      ↓
Event loop serves other requests
      ↓
MongoDB response
      ↓
Resume coroutine
```

With an asynchronous MongoDB client, the application can suspend a coroutine while waiting for MongoDB rather than blocking the event loop.

MongoDB's current Python documentation recommends `AsyncMongoClient` for asynchronous applications. :contentReference[oaicite:1]{index=1}

This does **not** mean async automatically makes a database query faster. It improves concurrency and resource utilization when requests spend significant time waiting on I/O.

## Synchronous vs Asynchronous MongoDB Access

| Approach | Client | FastAPI usage | Main consideration |
|---|---|---|---|
| Synchronous | `MongoClient` | Sync endpoints or controlled thread execution | Simple, blocking I/O |
| Asynchronous | `AsyncMongoClient` | `async def` endpoints | Natural fit for async APIs |
| MongoEngine | ODM abstraction | Requires care around blocking operations | Higher-level modeling |
| Async ODM | Depends on library | Async abstraction | Evaluate maintenance and feature coverage |

For a new async FastAPI service, `AsyncMongoClient` is generally the most direct driver-level approach.

PyMongo's current async API uses the same general MongoDB concepts as the synchronous API, but network operations are asynchronous and must be awaited. :contentReference[oaicite:2]{index=2}

## Installing Dependencies

A minimal application can use:

```bash
python -m pip install fastapi uvicorn pymongo
```

For production, pin dependencies through the project's dependency-management system rather than installing unbounded versions.

Example:

```text
fastapi
uvicorn[standard]
pymongo
pydantic-settings
```

Validate upgrades against:

- Python version
- FastAPI version
- Starlette version
- Pydantic version
- PyMongo version
- MongoDB Server version
- Existing integration tests

## MongoDB Connection URI

A MongoDB connection URI describes the deployment and connection options.

Local development:

```text
mongodb://localhost:27017
```

Authenticated deployment:

```text
mongodb://username:password@mongodb.example.com:27017/orders?authSource=admin
```

Atlas-style SRV connection:

```text
mongodb+srv://username:password@cluster.example.mongodb.net/orders
```

A URI can contain:

- Host information
- Authentication information
- Database name
- TLS settings
- Replica-set information
- Retry behavior
- Timeout configuration
- Other driver options

PyMongo documents the URI and `MongoClient` as the two fundamental components used to connect to MongoDB. :contentReference[oaicite:3]{index=3}

## Configuration Management

Do not hard-code connection strings.

Use environment-based configuration:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_uri: str
    mongodb_database: str = "orders"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
```

Production:

```text
AWS Secrets Manager / Kubernetes Secret
                ↓
          Environment
                ↓
          Pydantic Settings
                ↓
          MongoDB Client
```

The `.env` file should not be committed when it contains credentials.

## Database Client Lifecycle

The MongoDB client should normally have application-level lifecycle ownership.

FastAPI's recommended mechanism for startup and shutdown resource management is the `lifespan` parameter. The older `startup` and `shutdown` event handlers are considered an alternative rather than the preferred approach. :contentReference[oaicite:4]{index=4}

A production-oriented setup:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pymongo import AsyncMongoClient
from pymongo.server_api import ServerApi

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncMongoClient(
        settings.mongodb_uri,
        server_api=ServerApi(
            "1",
            strict=True,
            deprecation_errors=True,
        ),
    )

    await client.admin.command("ping")

    app.state.mongodb_client = client
    app.state.mongodb_database = client.get_database(
        settings.mongodb_database
    )

    yield

    await client.close()


app = FastAPI(lifespan=lifespan)
```

MongoDB's FastAPI integration documentation demonstrates the same lifecycle pattern: initialize the async client during application startup, make the database available to the application, and close the client during shutdown. :contentReference[oaicite:5]{index=5}

## Why Not Create a Client Per Request?

Avoid:

```python
@app.get("/orders")
async def get_orders():
    client = AsyncMongoClient(settings.mongodb_uri)
    ...
```

This can cause unnecessary:

- connection establishment
- topology discovery
- resource consumption
- connection-pool churn
- latency

Instead:

```text
FastAPI Process
      │
      └── AsyncMongoClient
             │
             ├── connection pool
             ├── database
             └── collections
```

Reuse the application-level client for the lifetime of the process.

## Application Lifecycle

A simplified lifecycle is:

```mermaid
sequenceDiagram
    participant U as Client
    participant F as FastAPI
    participant R as Repository
    participant M as AsyncMongoClient
    participant DB as MongoDB

    U->>F: HTTP request
    F->>F: Validate request
    F->>R: Execute business query
    R->>M: await MongoDB operation
    M->>DB: Query
    DB-->>M: Result
    M-->>R: Document
    R-->>F: Domain data
    F->>F: Serialize response
    F-->>U: HTTP response
```

The event loop can continue processing other requests while asynchronous database operations are waiting on I/O.

## Database Dependency

A small dependency helper can expose the database:

```python
from fastapi import Request
from pymongo.asynchronous.database import AsyncDatabase


def get_database(request: Request) -> AsyncDatabase:
    return request.app.state.mongodb_database
```

The exact import path and typing should be aligned with the PyMongo version used by the application.

Then:

```python
from fastapi import Depends, Request


@app.get("/health/database")
async def database_health(request: Request):
    db = request.app.state.mongodb_database

    await db.command("ping")

    return {"status": "ok"}
```

For larger applications, repositories should normally receive the database or collection rather than exposing it directly to every route.

## Repository Pattern

A repository isolates persistence.

```python
from typing import Any

from bson import ObjectId
from pymongo.asynchronous.collection import AsyncCollection


class OrderRepository:
    def __init__(self, collection: AsyncCollection):
        self.collection = collection

    async def find_by_id(
        self,
        order_id: ObjectId,
    ) -> dict[str, Any] | None:
        return await self.collection.find_one(
            {"_id": order_id}
        )
```

The router does not need to know:

- collection names
- MongoDB filters
- indexes
- BSON details
- MongoDB-specific exceptions

## Service Layer

Business rules belong above the repository.

```python
class OrderService:
    def __init__(self, repository: OrderRepository):
        self.repository = repository

    async def get_order(self, order_id: ObjectId):
        order = await self.repository.find_by_id(order_id)

        if order is None:
            raise OrderNotFound()

        return order
```

Architecture:

```text
Router
  ↓
Service
  ↓
Repository
  ↓
MongoDB
```

This separation becomes increasingly valuable when the application grows into multiple services or complex workflows.

## Pydantic Request Models

FastAPI uses Pydantic for request validation.

```python
from decimal import Decimal

from pydantic import BaseModel, Field


class CreateOrderRequest(BaseModel):
    customer_id: str
    total: Decimal = Field(gt=0)
```

The API schema should describe the HTTP contract rather than simply mirror the MongoDB document.

## Persistence Models vs API Models

Avoid making the MongoDB document the public API contract.

Prefer:

```text
HTTP JSON
   ↓
Pydantic Schema
   ↓
Service
   ↓
MongoDB Document
```

rather than:

```text
MongoDB Document
   ↓
HTTP Response
```

This protects the API from persistence-layer changes.

## ObjectId Handling

MongoDB commonly uses `ObjectId` for `_id`.

Example:

```python
from bson import ObjectId


object_id = ObjectId("507f1f77bcf86cd799439011")
```

An API usually represents the identifier as a string:

```json
{
  "id": "507f1f77bcf86cd799439011"
}
```

Do not expose raw BSON objects without defining how they should be serialized.

## ObjectId Validation

A route parameter can be validated before querying MongoDB:

```python
from bson import ObjectId
from fastapi import HTTPException


def parse_object_id(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(
            status_code=400,
            detail="Invalid object id",
        )

    return ObjectId(value)
```

This prevents malformed identifiers from reaching the repository.

## Response Schemas

```python
from pydantic import BaseModel


class OrderResponse(BaseModel):
    id: str
    customer_id: str
    status: str
    total: float
```

Mapping explicitly:

```python
def to_order_response(document: dict) -> OrderResponse:
    return OrderResponse(
        id=str(document["_id"]),
        customer_id=document["customer_id"],
        status=document["status"],
        total=document["total"],
    )
```

This makes the API contract independent of MongoDB's BSON representation.

## Basic CRUD

### Insert One

```python
result = await collection.insert_one(
    {
        "customer_id": "cust-1001",
        "status": "pending",
        "total": 149.99,
    }
)

order_id = result.inserted_id
```

Use `insert_one()` when the application creates one document.

### Insert Many

```python
result = await collection.insert_many(
    [
        {
            "customer_id": "cust-1001",
            "status": "pending",
            "total": 100,
        },
        {
            "customer_id": "cust-1002",
            "status": "pending",
            "total": 200,
        },
    ]
)
```

For large workloads, use bounded batches rather than loading an unbounded dataset into memory.

### Find One

```python
order = await collection.find_one(
    {
        "_id": order_id,
    }
)
```

### Find Many

```python
cursor = collection.find(
    {
        "status": "pending",
    }
)

orders = await cursor.to_list(length=100)
```

PyMongo's async cursor requires asynchronous iteration or asynchronous materialization. The current async API documents `to_list()` and `async for` as the mechanisms for consuming asynchronous cursors. :contentReference[oaicite:6]{index=6}

## Cursor Iteration

For large result sets:

```python
cursor = collection.find(
    {"status": "pending"},
    projection={
        "_id": 1,
        "customer_id": 1,
        "status": 1,
    },
)

async for document in cursor:
    await process_order(document)
```

This avoids materializing the entire result set into application memory.

## Update One

```python
result = await collection.update_one(
    {"_id": order_id},
    {
        "$set": {
            "status": "confirmed",
        }
    },
)
```

Check the result when the application needs to distinguish between:

- no matching document
- matched but unchanged
- modified document

## Upsert

```python
result = await collection.update_one(
    {
        "external_id": external_id,
    },
    {
        "$set": {
            "status": "active",
        }
    },
    upsert=True,
)
```

Upserts are particularly useful for idempotent synchronization workflows.

The filter should have an appropriate unique index when the business identifier must be unique.

## Delete

```python
result = await collection.delete_one(
    {"_id": order_id}
)
```

For most business systems, prefer explicit lifecycle states or soft-delete patterns when records must remain auditable.

## Projection

Retrieve only required fields:

```python
cursor = collection.find(
    {"status": "pending"},
    {
        "_id": 1,
        "customer_id": 1,
        "status": 1,
    },
)
```

Projection can reduce:

- network traffic
- BSON decoding
- memory usage
- response serialization

It does not eliminate the need for an appropriate index.

## Pagination

Offset pagination:

```python
cursor = (
    collection.find(
        {"status": "pending"},
    )
    .sort("created_at", -1)
    .skip(offset)
    .limit(page_size)
)
```

This is straightforward but large offsets can become increasingly expensive.

For high-volume APIs, cursor-based pagination is generally preferable.

## Cursor-Based Pagination

Use a stable indexed field such as:

```text
created_at + _id
```

Conceptually:

```text
Page 1
created_at <= cursor
      ↓
Page 2
created_at <= next cursor
```

A deterministic pagination key is important when multiple documents can share the same timestamp.

A common pattern is:

```python
cursor = collection.find(
    {
        "created_at": {
            "$lt": last_created_at,
        }
    }
).sort(
    "created_at",
    -1,
).limit(
    page_size,
)
```

For production systems, use a compound cursor when timestamps are not unique.

## Query Filters

Build filters from explicitly supported API parameters.

```python
filters: dict = {
    "status": "pending",
}

if customer_id:
    filters["customer_id"] = customer_id

cursor = collection.find(filters)
```

Do not pass arbitrary user-provided dictionaries directly to MongoDB.

## Query Injection

Avoid APIs that accept unrestricted MongoDB query documents:

```json
{
  "filter": {
    "$where": "..."
  }
}
```

Instead:

```python
ALLOWED_STATUSES = {
    "pending",
    "confirmed",
    "cancelled",
}


def build_filters(status: str | None):
    filters = {}

    if status is not None:
        if status not in ALLOWED_STATUSES:
            raise ValueError("Unsupported status")

        filters["status"] = status

    return filters
```

Application input should control the allowed query shape.

## Aggregation Endpoints

Aggregation pipelines should normally be owned by a repository or dedicated query service.

Example:

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
            "order_count": {
                "$sum": 1,
            },
            "total": {
                "$sum": "$total",
            },
        }
    },
    {
        "$sort": {
            "total": -1,
        }
    },
]

cursor = collection.aggregate(pipeline)

results = await cursor.to_list(length=100)
```

Keep aggregation endpoints bounded and monitor their execution time.

## Aggregation and API Design

Avoid exposing arbitrary aggregation pipelines through an API.

Bad:

```text
POST /reports
{
    "pipeline": [...]
}
```

unless the API is explicitly an administrative/internal query service with strong controls.

Prefer:

```text
GET /customers/{id}/order-summary
```

where the server owns the aggregation pipeline.

This provides:

- predictable workload
- authorization boundaries
- stable query shape
- easier indexing
- easier monitoring

## Indexing

Indexes should be derived from API access patterns.

Suppose the endpoint executes:

```text
GET /orders?customer_id=123&status=pending
```

and sorts by:

```text
created_at DESC
```

A candidate compound index may be:

```javascript
{
  customer_id: 1,
  status: 1,
  created_at: -1
}
```

Validate the design with `explain()` and production workload measurements.

## Explain

A senior engineer should inspect:

- `COLLSCAN`
- `IXSCAN`
- `FETCH`
- `SORT`
- `nReturned`
- `totalKeysExamined`
- `totalDocsExamined`
- execution time

The optimization workflow is:

```text
Slow endpoint
    ↓
Identify repository query
    ↓
Inspect MongoDB query shape
    ↓
Run explain()
    ↓
Check index usage
    ↓
Check returned / examined ratio
    ↓
Modify index or query
    ↓
Benchmark
    ↓
Deploy
    ↓
Monitor regression
```

Do not optimize only from API latency.

## Transactions

MongoDB supports multi-document transactions through sessions.

With PyMongo Async:

```python
async with await client.start_session() as session:
    async with session.start_transaction():
        await orders.insert_one(
            order_document,
            session=session,
        )

        await inventory.update_one(
            {"product_id": product_id},
            {"$inc": {"available": -quantity}},
            session=session,
        )
```

Transaction boundaries belong in the service layer rather than the router.

## Transaction Decision

Use transactions when multiple document changes must satisfy one atomic business invariant.

Examples:

```text
Create order
+
Reserve inventory
```

or:

```text
Transfer balance
+
Create ledger entry
```

Avoid transactions when the same result can be achieved through:

- embedding
- atomic single-document updates
- idempotent workflows
- event-driven processing

MongoDB's document-level atomicity is often enough when the data model is designed correctly.

## Transactions vs PostgreSQL

| Concern | MongoDB | PostgreSQL |
|---|---|---|
| Single-record atomicity | Strong | Strong |
| Multi-record transactions | Supported | Supported |
| Document-oriented modeling | Native | Not primary model |
| Relational joins | Not primary model | Native |
| Schema flexibility | High | Strongly structured |
| Transaction-first modeling | Often avoidable | Common |
| Denormalization | Common | More selective |

Do not port a relational schema into MongoDB and then use transactions to recreate relational behavior everywhere.

## Sessions

Sessions are used for features including:

- transactions
- causal consistency
- certain retry behaviors
- operation context

Example:

```python
async with await client.start_session() as session:
    result = await collection.insert_one(
        document,
        session=session,
    )
```

Pass the same session through every operation that belongs to the same transaction.

## Read and Write Concerns

Production services should deliberately configure consistency and durability requirements.

Examples include:

```text
writeConcern = majority
readConcern = majority
readPreference = primary
```

The correct configuration depends on workload requirements.

Do not change these settings simply to reduce latency without understanding the consistency and failure implications.

## Retry Behavior

MongoDB drivers support retryable operations in supported configurations.

Application-level retries should still be designed carefully.

A retry is safe only when the operation is:

- idempotent
- uniquely identifiable
- protected against duplicate side effects

For example:

```text
POST payment
    ↓
timeout
    ↓
retry
    ↓
duplicate payment
```

is dangerous without idempotency controls.

Prefer:

```text
Idempotency-Key
      ↓
Unique database constraint
      ↓
Atomic operation
```

## Error Handling

Do not expose raw MongoDB exceptions to API clients.

Bad:

```python
except Exception as exc:
    raise HTTPException(
        status_code=500,
        detail=str(exc),
    )
```

Prefer explicit exception mapping:

```python
from pymongo.errors import DuplicateKeyError
from fastapi import HTTPException


try:
    await collection.insert_one(document)
except DuplicateKeyError:
    raise HTTPException(
        status_code=409,
        detail="Order already exists",
    )
```

Unexpected exceptions should be logged with correlation information and translated into a generic server response.

## Error Categories

| MongoDB error | API behavior |
|---|---|
| Duplicate key | Usually `409 Conflict` |
| Invalid identifier | `400 Bad Request` |
| Document not found | `404 Not Found` |
| Validation failure | `422` or domain-specific response |
| Timeout | Usually `503` or controlled retry |
| Authentication failure | Internal operational error |
| Connection failure | `503` / dependency failure |
| Unexpected exception | `500` |

Exact mappings should follow the service's API contract.

## Health Checks

Separate liveness and readiness.

### Liveness

Liveness should generally answer:

```text
Is the process alive?
```

It should not necessarily depend on MongoDB.

```python
@app.get("/health/live")
async def liveness():
    return {"status": "ok"}
```

### Readiness

Readiness can verify MongoDB:

```python
@app.get("/health/ready")
async def readiness(request: Request):
    db = request.app.state.mongodb_database

    await db.command("ping")

    return {"status": "ready"}
```

This distinction is particularly important in Kubernetes.

## Kubernetes Behavior

A useful deployment model is:

```text
Ingress / Load Balancer
          ↓
      FastAPI Pods
       ↙   ↓   ↘
 MongoDB connection pools
          ↓
 MongoDB Replica Set / Atlas
```

Each FastAPI pod should have its own MongoDB client and connection pool.

Avoid thinking of the MongoDB pool as a cluster-wide pool.

If:

```text
10 pods × 100 connections
```

are allowed, the deployment can potentially create roughly:

```text
1000 connections
```

to MongoDB.

Connection-pool settings must therefore be considered at the deployment level, not only at the application level.

## Connection Pooling

PyMongo manages connection pools internally.

For a FastAPI deployment:

```text
Pod 1 → MongoDB pool
Pod 2 → MongoDB pool
Pod 3 → MongoDB pool
...
Pod N → MongoDB pool
```

Capacity planning must consider:

```text
maximum pods
×
maximum connections per process
```

along with other applications sharing the cluster.

Do not blindly increase pool sizes to fix latency.

First determine whether the bottleneck is:

- connection acquisition
- server execution
- network latency
- CPU
- indexes
- application processing

## Timeouts

Production services should have bounded timeouts.

Important categories include:

- server selection timeout
- connection timeout
- socket timeout
- operation timeout

Current PyMongo documentation also provides a client-side `timeout()` mechanism and `timeoutMS` configuration. :contentReference[oaicite:7]{index=7}

A useful principle is:

```text
HTTP timeout
    >
service timeout
    >
database operation timeout
```

The exact values depend on the service's latency budget.

Avoid letting MongoDB calls hang indefinitely.

## Stable API

MongoDB's Stable API can help applications control compatibility with supported MongoDB server API behavior.

Example:

```python
from pymongo.server_api import ServerApi

client = AsyncMongoClient(
    settings.mongodb_uri,
    server_api=ServerApi(
        "1",
        strict=True,
        deprecation_errors=True,
    ),
)
```

MongoDB documents Stable API support for MongoDB Server 5.0 and later. :contentReference[oaicite:8]{index=8}

This is particularly useful for long-lived production services that must manage database upgrades deliberately.

## TLS

Production MongoDB connections should use TLS where required by the deployment.

Example:

```python
client = AsyncMongoClient(
    settings.mongodb_uri,
    tls=True,
)
```

MongoDB's current PyMongo documentation warns against production use of insecure TLS options such as `tlsInsecure=True`, `tlsAllowInvalidCertificates=True`, or `tlsAllowInvalidHostnames=True`. :contentReference[oaicite:9]{index=9}

Never disable certificate validation merely to make a deployment work.

## Authentication

Use dedicated application credentials.

```text
FastAPI service
      ↓
Application MongoDB user
      ↓
Required database/collections
```

Do not run application workloads using:

```text
admin
root
cluster-wide privileged account
```

Use least privilege.

## Secret Management

For local development:

```text
.env
```

For production:

```text
AWS Secrets Manager
Kubernetes Secret
Vault
Managed platform secret store
```

Do not log:

```text
MONGODB_URI
username
password
TLS private key
```

Be careful with exception logging because connection errors can sometimes contain connection details.

## API Authorization

MongoDB authorization and API authorization solve different problems.

```text
HTTP Authorization
      ↓
Can this user perform this business action?

MongoDB Authorization
      ↓
Can this service identity access this database resource?
```

Both layers are required.

A valid MongoDB credential should not imply that an end user is authorized to access a document.

## Tenant Isolation

For multi-tenant applications, filters should be scoped by tenant:

```python
document = await collection.find_one(
    {
        "_id": order_id,
        "tenant_id": tenant_id,
    }
)
```

Do not rely solely on:

```python
{"_id": order_id}
```

when identifiers are not globally authorization-safe.

Centralize tenant filtering in repository/service boundaries where possible.

## Data Modeling for APIs

API access patterns should drive MongoDB document design.

Suppose an order endpoint needs:

```text
Order
├── status
├── customer
└── line items
```

If line items are bounded and always returned with the order:

```json
{
  "_id": "...",
  "status": "confirmed",
  "customer_id": "cust-1001",
  "items": [
    {
      "product_id": "prod-1",
      "quantity": 2
    }
  ]
}
```

Embedding may be appropriate.

If the child collection is large and independently queried:

```text
orders
order_items
```

or referenced documents may be more appropriate.

The API contract should not determine the schema mechanically. Analyze:

- read patterns
- write patterns
- cardinality
- document growth
- update frequency
- consistency requirements

## Avoiding N+1 Queries

A common API anti-pattern is:

```text
GET /orders
    ↓
100 orders
    ↓
100 customer lookups
```

This creates:

```text
1 + N MongoDB operations
```

Solutions include:

- embedding frequently used data
- batch fetching
- aggregation with `$lookup`
- denormalization
- changing the endpoint response contract

Measure the database operation count rather than assuming an ORM/ODM abstraction handles this automatically.

## Change Streams

FastAPI services can consume MongoDB change streams for event-driven workflows.

Architecture:

```text
MongoDB Replica Set / Cluster
          ↓
     Change Stream
          ↓
     FastAPI Worker
          ↓
       Kafka
          ↓
Downstream Services
```

Change streams can expose events such as:

- insert
- update
- replace
- delete

Consumers should persist or otherwise manage resume information and design processing to be idempotent.

A change stream consumer should not run inside an ordinary HTTP request handler.

Prefer:

```text
FastAPI
  ├── HTTP API
  │
  └── Background Worker
          ↓
      Change Stream
```

## Background Work

Do not perform long-running jobs directly inside API requests.

Bad:

```text
HTTP request
    ↓
10-minute MongoDB aggregation
    ↓
HTTP response
```

Prefer:

```text
HTTP request
    ↓
Create job
    ↓
Return 202
    ↓
Celery / worker
    ↓
MongoDB
    ↓
Result
```

For asynchronous event consumption, use an appropriate worker architecture rather than keeping a request coroutine alive indefinitely.

## Redis Integration

Redis can complement MongoDB.

```text
FastAPI
   ↓
Redis Cache
   ↓ cache miss
MongoDB
```

Use caching for:

- frequently accessed reference data
- expensive computed results
- short-lived API responses
- rate limiting
- distributed coordination where appropriate

Do not use Redis as a replacement for MongoDB durability.

Cache invalidation should be tied to explicit data lifecycle decisions.

## Kafka Integration

MongoDB can be part of an event-driven architecture:

```text
FastAPI
   ↓
MongoDB
   ↓
Outbox / Change Stream
   ↓
Kafka
   ↓
Consumers
```

Do not assume that:

```text
MongoDB write
+
Kafka publish
```

is automatically atomic.

For critical event delivery, use an appropriate reliability pattern such as an outbox or a carefully designed change-stream consumer.

## Performance Optimization

Performance work should begin with measurement.

```text
API latency
    ↓
Application timing
    ↓
MongoDB operation timing
    ↓
Query plan
    ↓
Index
    ↓
Data volume
    ↓
Resource utilization
```

Do not immediately add Redis or more indexes.

## Before Optimization

Suppose:

```python
cursor = collection.find(
    {
        "customer_id": customer_id,
        "status": "pending",
    }
).sort(
    "created_at",
    -1,
)
```

If no useful index exists, MongoDB may need to scan many documents and perform an expensive sort.

## After Optimization

A candidate index:

```javascript
{
  customer_id: 1,
  status: 1,
  created_at: -1
}
```

Then validate:

```text
Before
COLLSCAN
↓
Many documents examined
↓
In-memory sort

After
IXSCAN
↓
Targeted documents
↓
Index-supported ordering
```

Do not treat the index as proven until `explain()` and production measurements support the change.

## Large Responses

Avoid returning thousands of documents from one API call.

Bad:

```python
documents = await cursor.to_list(length=100000)
```

Prefer:

```text
Pagination
+
Projection
+
Bounded result size
```

For exports, move the operation into an asynchronous job.

## Large Aggregations

Large aggregations can consume significant server resources.

Prefer:

- early `$match`
- useful indexes
- bounded date ranges
- controlled `$sort`
- `$limit` where semantically valid
- background processing for expensive reports

For example:

```text
Bad:
entire collection
    ↓
group
    ↓
filter

Better:
indexed date/status filter
    ↓
reduced dataset
    ↓
group
```

## Memory Considerations

MongoDB and FastAPI have separate memory boundaries.

```text
MongoDB memory
    ↓
Query execution / working set

FastAPI process memory
    ↓
BSON decoding
    ↓
Python objects
    ↓
Pydantic models
    ↓
JSON serialization
```

A large MongoDB result can therefore consume memory multiple times across the request path.

Use:

- projection
- pagination
- streaming
- bounded batches
- aggregation
- background processing

## Serialization Cost

A document may pass through several representations:

```text
BSON
 ↓
Python dict
 ↓
Pydantic model
 ↓
JSON
 ↓
HTTP
```

For large documents, this conversion cost can become material.

Do not store huge documents simply because MongoDB supports them.

## Production Deployment

A typical deployment:

```mermaid
flowchart LR
    C[Clients] --> LB[Load Balancer / Nginx]
    LB --> F1[FastAPI Pod]
    LB --> F2[FastAPI Pod]
    LB --> F3[FastAPI Pod]

    F1 --> M[(MongoDB)]
    F2 --> M
    F3 --> M

    F1 --> R[(Redis)]
    F2 --> R
    F3 --> R
```

For production MongoDB itself may be:

```text
FastAPI
   ↓
MongoDB Atlas
```

or:

```text
FastAPI
   ↓
MongoDB Replica Set
```

Application deployment and database deployment should have independent lifecycle and scaling strategies.

## Docker

A simplified FastAPI container:

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

The MongoDB URI should be injected at runtime:

```bash
docker run \
  -e MONGODB_URI="$MONGODB_URI" \
  -e MONGODB_DATABASE="orders" \
  my-fastapi-service
```

Do not bake secrets into the image.

## Kubernetes

A production deployment should consider:

- readiness probes
- liveness probes
- graceful shutdown
- resource requests
- resource limits
- secret injection
- horizontal scaling
- connection-pool capacity

The connection-pool implication is important:

```text
Pod count × pool size
        ↓
Potential MongoDB connections
```

Scaling FastAPI from 5 to 50 pods can therefore change MongoDB connection pressure substantially.

## Graceful Shutdown

FastAPI's lifespan mechanism allows cleanup:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncMongoClient(settings.mongodb_uri)

    app.state.mongodb_client = client

    yield

    await client.close()
```

This allows the application to release the client during process shutdown.

In Kubernetes, combine this with appropriate termination grace periods so in-flight requests can finish cleanly.

## MongoDB Atlas

Atlas can provide managed MongoDB infrastructure, including:

- replica sets
- monitoring
- backups
- scaling options
- security controls
- managed operational features

The application-side architecture remains largely the same:

```text
FastAPI
   ↓
AsyncMongoClient
   ↓
Atlas
```

Do not assume managed infrastructure eliminates application responsibilities around:

- indexes
- query design
- connection limits
- credentials
- API authorization
- data modeling
- observability

## High Availability

For high availability:

```text
FastAPI Pod
     ↓
MongoDB Replica Set
     ├── Primary
     ├── Secondary
     └── Secondary
```

The driver discovers topology and can react to replica-set changes.

Connection strings for replica sets can specify multiple hosts, and PyMongo can perform replica-set discovery. :contentReference[oaicite:10]{index=10}

Production systems should still test:

- primary election
- application retry behavior
- timeout behavior
- transaction behavior
- read preference
- write concern
- connection recovery

## Read Preference

Do not route reads to secondaries merely because they appear cheaper or faster.

Secondary reads can introduce:

- replication lag
- stale reads
- inconsistent user experiences

For strongly consistent request flows, primary reads are often appropriate.

Use secondary reads when the workload explicitly tolerates the consistency model.

## Monitoring

Monitor both FastAPI and MongoDB.

### FastAPI Metrics

Track:

- request rate
- p50 latency
- p95 latency
- p99 latency
- error rate
- timeout rate
- active requests
- worker utilization

### MongoDB Metrics

Track:

- operation latency
- connections
- query execution
- slow queries
- CPU
- memory
- storage
- replication lag
- cache/working-set behavior
- index usage

### Correlation

Use request IDs:

```text
HTTP request ID
      ↓
FastAPI log
      ↓
Repository operation
      ↓
MongoDB diagnostic data
```

This makes production troubleshooting much faster.

## Logging

Use structured logs:

```python
logger.info(
    "order_created",
    extra={
        "request_id": request_id,
        "order_id": str(order_id),
        "customer_id": customer_id,
    },
)
```

Avoid logging:

- passwords
- MongoDB URIs
- authentication tokens
- private customer information
- complete documents by default

## Slow Query Monitoring

A production process should identify:

```text
Which endpoint?
      ↓
Which repository operation?
      ↓
Which MongoDB query?
      ↓
Which index?
      ↓
How many keys examined?
      ↓
How many documents examined?
```

Application-level timing and MongoDB-level query monitoring should complement each other.

## Backup and Recovery

FastAPI does not change MongoDB backup requirements.

Production MongoDB should have:

- automated backups
- retention policy
- restore testing
- documented RPO
- documented RTO
- disaster-recovery procedures

For example:

```text
Application
    ↓
MongoDB
    ↓
Managed Backup
    ↓
Restore Test
    ↓
Recovery Environment
    ↓
Application Validation
```

A backup that has never been restored should not be treated as a fully validated recovery strategy.

## Testing Strategy

Use multiple test layers.

### Unit Tests

Mock repositories:

```text
Service
  ↓
Fake Repository
```

Useful for business rules.

### Integration Tests

Run a real MongoDB instance:

```text
FastAPI
  ↓
Repository
  ↓
MongoDB
```

Test:

- CRUD
- indexes
- validation
- aggregation
- transactions
- duplicate constraints
- pagination

### API Tests

Use FastAPI's `TestClient` or an async HTTP test client depending on the test architecture.

FastAPI's lifespan can be exercised by using `TestClient` as a context manager. :contentReference[oaicite:11]{index=11}

Example:

```python
from fastapi.testclient import TestClient

from app.main import app


def test_health():
    with TestClient(app) as client:
        response = client.get("/health/live")

    assert response.status_code == 200
```

## Test Database Isolation

Tests should not write into production databases.

Prefer:

```text
CI
 ↓
Dedicated MongoDB
 ↓
Dedicated test database
```

For parallel tests:

```text
worker-1 → test_db_1
worker-2 → test_db_2
worker-3 → test_db_3
```

or use isolated collections/fixtures with reliable cleanup.

## Repository Testing

A repository test should verify actual persistence behavior.

```python
async def test_find_order(repository):
    order = await repository.find_by_id(order_id)

    assert order is not None
    assert order["_id"] == order_id
```

Repository tests should not merely mock MongoDB calls; otherwise query mistakes can go undetected.

## Contract Testing

For APIs consumed by other services, validate:

- response structure
- field types
- status codes
- pagination semantics
- error formats

Do not allow MongoDB schema changes to silently change the public API.

## Common Mistakes

### Creating `AsyncMongoClient` Per Request

```python
@app.get("/orders")
async def orders():
    client = AsyncMongoClient(...)
```

This creates unnecessary client lifecycle overhead.

Use application lifespan.

### Using Sync PyMongo Inside Async Endpoints

Bad:

```python
client = MongoClient(uri)

@app.get("/orders")
async def orders():
    return list(client.orders.find())
```

This introduces blocking database I/O into an asynchronous request path.

Use `AsyncMongoClient` for an async architecture, or intentionally isolate synchronous work.

### Loading Entire Collections

Bad:

```python
orders = await collection.find({}).to_list(length=1000000)
```

This can exhaust application memory.

Use pagination, batching, streaming, or an asynchronous export job.

### Missing Indexes

The endpoint may work perfectly in development and degrade badly as the collection grows.

Validate production query patterns with `explain()`.

### Arbitrary User Filters

Never expose raw MongoDB operators directly through a public API.

Whitelist supported fields and operators.

### Returning MongoDB Documents Directly

This can expose:

- internal fields
- BSON-specific types
- implementation details
- sensitive data

Map persistence objects to response schemas.

### N+1 Queries

References and per-document lookups can silently multiply database traffic.

Measure query counts and use embedding, batching, aggregation, or denormalization where appropriate.

### Overusing Transactions

Transactions add coordination and operational cost.

First ask whether the data model can make the operation atomic at the document level.

### Ignoring Connection Capacity

Increasing FastAPI replicas can multiply MongoDB connections.

Always model:

```text
replicas × pool size
```

against MongoDB capacity.

### Disabling TLS Validation

Do not use insecure TLS flags in production. MongoDB explicitly warns against disabling certificate and hostname validation. :contentReference[oaicite:12]{index=12}

### Logging Connection Strings

MongoDB URIs can contain credentials.

Never include them in application logs.

## Troubleshooting

### Application Cannot Connect

```text
Symptom
↓
FastAPI cannot connect to MongoDB
↓
Possible causes
    - Incorrect URI
    - DNS failure
    - Network/security-group restriction
    - Invalid credentials
    - TLS configuration
    - Replica-set discovery failure
    - MongoDB unavailable
↓
Isolation strategy
↓
Validate environment variables
↓
Test DNS/network connectivity
↓
Test with mongosh
↓
Check MongoDB authentication
↓
Check TLS configuration
↓
Check MongoDB health
↓
Root cause
↓
Corrective action
↓
Prevention
    - Startup connectivity check
    - Secret validation
    - Monitoring
    - Deployment smoke tests
```

### Requests Hang

```text
Symptom
↓
API requests remain pending
↓
Possible causes
    - Missing database timeout
    - Server selection delay
    - Network failure
    - Pool exhaustion
    - Slow MongoDB query
    - Large aggregation
↓
Isolation strategy
↓
Inspect FastAPI request latency
↓
Inspect MongoDB operation latency
↓
Check connection pool pressure
↓
Run explain() on slow queries
↓
Root cause
↓
Corrective action
    - Configure timeouts
    - Fix index
    - Increase capacity when justified
    - Reduce query scope
↓
Prevention
    - Timeout budgets
    - Slow-query monitoring
    - Load testing
```

### High MongoDB CPU

```text
Symptom
↓
MongoDB CPU is high
↓
Possible causes
    - COLLSCAN
    - Expensive aggregation
    - Poor index
    - High request volume
    - Large sort
    - Inefficient query shape
↓
Isolation strategy
↓
Identify highest-volume operations
↓
Inspect explain plans
↓
Check index usage
↓
Measure aggregation cost
↓
Root cause
↓
Corrective action
    - Add/change index
    - Rewrite query
    - Bound workload
    - Move heavy processing to workers
↓
Prevention
    - Query review
    - Load testing
    - Production dashboards
```

### Connection Pool Exhaustion

```text
Symptom
↓
Requests wait for MongoDB connections
↓
Possible causes
    - Pool too small
    - Long-running queries
    - Too many concurrent requests
    - Slow MongoDB
    - Excessive FastAPI replicas
↓
Isolation strategy
↓
Measure request concurrency
↓
Inspect MongoDB connection counts
↓
Inspect query latency
↓
Compare pod count × pool capacity
↓
Root cause
↓
Corrective action
    - Fix slow queries first
    - Tune pool settings
    - Scale database if justified
↓
Prevention
    - Capacity planning
    - Load testing
    - Connection monitoring
```

### Duplicate Data After Retry

```text
Symptom
↓
The same logical operation creates multiple records
↓
Possible causes
    - Client retry
    - Network timeout after successful write
    - Missing idempotency key
    - No unique constraint
↓
Isolation strategy
↓
Inspect request identifiers
↓
Inspect duplicate records
↓
Check unique indexes
↓
Check retry behavior
↓
Root cause
↓
Corrective action
    - Add idempotency key
    - Add unique index
    - Make operation atomic
↓
Prevention
    - Idempotent API design
    - Retry testing
    - Failure-injection testing
```

## Production Architecture

A mature FastAPI + MongoDB service can look like:

```mermaid
flowchart TB
    Client[Clients] --> Gateway[Nginx / Load Balancer]

    Gateway --> API1[FastAPI Instance]
    Gateway --> API2[FastAPI Instance]
    Gateway --> APIN[FastAPI Instance]

    API1 --> Service[Service Layer]
    API2 --> Service
    APIN --> Service

    Service --> Repo[Repository Layer]
    Repo --> Mongo[AsyncMongoClient]

    Mongo --> Primary[(MongoDB Primary)]
    Mongo --> Secondary1[(MongoDB Secondary)]
    Mongo --> Secondary2[(MongoDB Secondary)]

    Service --> Redis[(Redis Cache)]
    Service --> Queue[Celery / Kafka]
```

The key scalability boundaries are:

```text
HTTP scaling
    ↓
FastAPI replicas

Database concurrency
    ↓
Connection pools

Database throughput
    ↓
Indexes + query design + MongoDB capacity

Background processing
    ↓
Workers / Kafka / Celery

Caching
    ↓
Redis
```

## Deployment Checklist

### Application

- [ ] Async database client is used for async workloads
- [ ] One client is reused per application process
- [ ] Client lifecycle is managed with FastAPI lifespan
- [ ] Connection URI is injected securely
- [ ] Timeouts are configured
- [ ] API schemas are separate from persistence documents
- [ ] Repository/service boundaries are defined

### MongoDB

- [ ] Authentication is enabled
- [ ] Least-privilege users are used
- [ ] TLS is enabled where required
- [ ] Appropriate indexes exist
- [ ] Slow queries are monitored
- [ ] Replica-set health is monitored
- [ ] Backups are configured
- [ ] Restore procedures are tested

### Kubernetes

- [ ] Readiness probe checks required dependencies appropriately
- [ ] Liveness probe does not create unnecessary database load
- [ ] Graceful shutdown is configured
- [ ] MongoDB connection capacity is calculated
- [ ] Secrets are externalized
- [ ] CPU and memory requests are defined
- [ ] Horizontal scaling considers database capacity

### API

- [ ] Pagination is enforced
- [ ] Maximum page size is bounded
- [ ] User filters are allowlisted
- [ ] MongoDB errors are mapped safely
- [ ] Authorization is enforced independently of MongoDB credentials
- [ ] Tenant filters are enforced where required
- [ ] Idempotency exists for retry-sensitive operations

## Interview Considerations

### Why use `AsyncMongoClient` with FastAPI?

Because FastAPI commonly uses asynchronous request handlers, and `AsyncMongoClient` allows MongoDB network operations to be awaited instead of blocking the event loop. :contentReference[oaicite:13]{index=13}

### Where should the MongoDB client be created?

At application lifecycle scope rather than per request. FastAPI's `lifespan` mechanism is the preferred place to initialize and close long-lived resources. :contentReference[oaicite:14]{index=14}

### Why use a repository layer?

It isolates MongoDB persistence logic from API and business logic, making query behavior easier to test, optimize, and replace.

### Why not return MongoDB documents directly?

Because MongoDB documents can contain BSON-specific types, internal fields, and persistence-specific structures that should not automatically become public API contracts.

### What happens if FastAPI scales from 5 to 50 pods?

Each process can maintain its own MongoDB connection pool. Therefore, total potential database connections can increase substantially with replica count.

### How do you optimize a slow MongoDB endpoint?

Start from the API request, identify the repository operation, inspect the MongoDB query and execution plan, verify indexes, measure `totalKeysExamined` and `totalDocsExamined`, optimize the query/index, and benchmark again.

### Should every MongoDB operation use a transaction?

No.

Single-document operations are atomic. Transactions should be used when multiple documents must change atomically to preserve a business invariant.

### How do you prevent duplicate writes during retries?

Use idempotency keys and database-level uniqueness constraints where appropriate, then make the write operation safely repeatable.

### What is the difference between MongoEngine and PyMongo in FastAPI?

MongoEngine is an ODM abstraction, while PyMongo is the MongoDB Python driver. For asynchronous FastAPI services, the current PyMongo API provides `AsyncMongoClient`; synchronous MongoEngine operations should not be placed directly into an async request path without deliberately managing the blocking behavior.

### How would you design MongoDB for a multi-tenant FastAPI application?

A typical application-level design is:

```text
JWT / Identity
     ↓
Tenant Context
     ↓
Authorization
     ↓
Repository
     ↓
tenant_id + business filter
     ↓
MongoDB
```

Tenant isolation must be enforced by the application and supported by appropriate indexes and database authorization controls.

### How would you handle a long-running report?

Do not keep the HTTP request open while performing an expensive aggregation.

Prefer:

```text
POST /reports
     ↓
Create job
     ↓
202 Accepted
     ↓
Celery / worker
     ↓
MongoDB aggregation
     ↓
Store result
     ↓
GET /reports/{id}
```

This protects API latency and isolates expensive database workloads.

## Key Takeaways

- **For asynchronous FastAPI services, use PyMongo's `AsyncMongoClient` and manage its lifecycle with FastAPI's `lifespan`; reuse the client rather than creating one per request.** :contentReference[oaicite:15]{index=15}
- **Keep routers, Pydantic schemas, services, repositories, and MongoDB persistence concerns separate so that API contracts and business logic are not coupled to BSON documents.**
- **Treat MongoDB query and index design as first-class performance concerns: bound result sizes, prefer appropriate pagination, inspect `explain()` plans, and account for connection-pool capacity across all FastAPI replicas.**
- **Design reliability explicitly with timeouts, idempotency, transaction boundaries, replica-set behavior, secure credentials, TLS, monitoring, backups, and tested recovery procedures.**
- **Use FastAPI for request/response workloads and move long-running aggregations, change-stream consumers, exports, and other background processing into dedicated worker or event-driven components.**