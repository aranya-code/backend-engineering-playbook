# 11- Python Integration Issues

## Overview

MongoDB integration failures in Python usually occur at the boundary between the application runtime, PyMongo, MongoDB topology, serialization, connection pooling, and application-level data models.

A production Python service typically follows this path:

```text
HTTP / gRPC Request
        ↓
FastAPI / Django
        ↓
Service Layer
        ↓
Repository / Data Access Layer
        ↓
PyMongo
        ↓
Connection Pool
        ↓
MongoDB Driver Topology
        ↓
Replica Set / Sharded Cluster
```

An issue at any layer can appear as a generic MongoDB error.

Common categories include:

- Connection failures
- DNS and network failures
- Authentication failures
- TLS failures
- Incorrect connection strings
- Replica-set discovery problems
- Connection-pool exhaustion
- Timeout configuration
- BSON serialization errors
- `ObjectId` handling
- Date and numeric type problems
- Query construction errors
- Cursor misuse
- Pagination issues
- Bulk-write failures
- Transaction errors
- Async integration problems
- FastAPI lifecycle problems
- Django integration problems
- Worker-process issues
- Configuration and secret-management mistakes
- Performance regressions

The most important troubleshooting principle is:

```text
Application Symptom
        ↓
Python Layer
        ↓
PyMongo Layer
        ↓
Network / Topology Layer
        ↓
MongoDB Layer
        ↓
Root Cause
```

Do not assume every MongoDB error is caused by MongoDB itself.

## Python MongoDB Integration Architecture

A production application should normally create a long-lived MongoDB client and reuse it.

```mermaid
flowchart TB
    API[FastAPI / Django]
    Service[Service Layer]
    Repository[Repository Layer]
    Client[PyMongo MongoClient]
    Pool[Connection Pool]
    Mongo[(MongoDB Replica Set)]

    API --> Service
    Service --> Repository
    Repository --> Client
    Client --> Pool
    Pool --> Mongo
```

The `MongoClient` manages topology discovery and connection pooling.

Creating a new client for every request is generally an anti-pattern.

## Recommended MongoClient Lifecycle

A typical synchronous application should create one `MongoClient` per process.

```python
from pymongo import MongoClient

client = MongoClient(
    "mongodb://mongo1:27017,mongo2:27017,mongo3:27017/"
    "?replicaSet=rs0",
    serverSelectionTimeoutMS=5_000,
)

db = client["application"]
orders = db["orders"]
```

Application code can then reuse:

```python
orders.find_one({"order_id": "ORD-1001"})
```

rather than creating another client.

## Why One Client Per Process Matters

`MongoClient` maintains:

- Connection pools
- Server topology information
- Connection state
- Monitoring
- Server selection state

Repeatedly constructing clients can create unnecessary:

- TCP connections
- TLS handshakes
- Authentication operations
- Background monitoring activity
- Memory usage
- Connection churn

Bad:

```python
def get_order(order_id: str):
    client = MongoClient(MONGO_URI)
    return client["application"]["orders"].find_one(
        {"order_id": order_id}
    )
```

Prefer:

```python
client = MongoClient(MONGO_URI)
orders = client["application"]["orders"]


def get_order(order_id: str):
    return orders.find_one({"order_id": order_id})
```

## Connection String Problems

A connection string controls important behavior.

Example:

```text
mongodb://mongo1:27017,mongo2:27017,mongo3:27017/application?replicaSet=rs0
```

Potential problems include:

- Wrong hostname
- Wrong port
- Wrong database
- Missing replica-set name
- Incorrect credentials
- Incorrect `authSource`
- TLS configuration mismatch
- Unsupported options
- Incorrect URL encoding

For Atlas:

```text
mongodb+srv://username:password@cluster.example.mongodb.net/application
```

The exact connection string should come from the deployment configuration rather than being manually reconstructed.

## Connection String Troubleshooting

Validate the URI in layers:

```text
URI syntax
    ↓
DNS resolution
    ↓
TCP connectivity
    ↓
TLS handshake
    ↓
Authentication
    ↓
Authorization
    ↓
MongoDB topology discovery
```

Testing the same URI with `mongosh` can isolate application-specific problems:

```bash
mongosh "mongodb://mongo1:27017/application?replicaSet=rs0"
```

If `mongosh` fails using the same configuration, investigate infrastructure or MongoDB configuration before debugging Python code.

## Environment Configuration

Do not hard-code production credentials.

Use environment variables or a secret-management system.

```python
import os

MONGO_URI = os.environ["MONGODB_URI"]
```

For production deployments, secrets can come from:

- Kubernetes Secrets
- AWS Secrets Manager
- AWS Systems Manager Parameter Store
- Container secret mechanisms
- CI/CD secret stores

Avoid:

```python
MONGO_URI = "mongodb://admin:password@production-db:27017"
```

## Configuration Validation

Fail early when required configuration is missing.

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongodb_uri: str
    mongodb_database: str = "application"

    class Config:
        env_prefix = "APP_"


settings = Settings()
```

A missing production connection string should fail application startup rather than produce intermittent runtime errors.

## Connectivity Errors

Typical errors include:

```text
ServerSelectionTimeoutError
ConnectionFailure
AutoReconnect
NetworkTimeout
```

Possible causes:

- MongoDB is unavailable.
- DNS is incorrect.
- Firewall blocks traffic.
- Security group blocks traffic.
- Kubernetes NetworkPolicy blocks traffic.
- Incorrect hostname.
- Incorrect port.
- TLS handshake failure.
- Replica-set members advertise unreachable addresses.

## Server Selection Timeout

Example configuration:

```python
MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5_000,
)
```

`serverSelectionTimeoutMS` controls how long the driver waits while selecting a suitable server.

It is not the same as:

- Connection establishment timeout
- Socket operation timeout
- Application HTTP timeout

A useful mental model is:

```text
Can I find an appropriate MongoDB server?
        ↓
serverSelectionTimeoutMS
```

## Connection Timeout vs Server Selection Timeout

| Setting | Purpose |
|---|---|
| `connectTimeoutMS` | Time allowed to establish a connection |
| `serverSelectionTimeoutMS` | Time allowed to select a suitable server |
| `socketTimeoutMS` | Time allowed for socket operations |
| `waitQueueTimeoutMS` | Time waiting for a pooled connection |

Do not solve every timeout problem by increasing every timeout.

First identify which stage is actually timing out.

## Socket Timeout

A socket timeout controls how long socket operations can remain inactive before timing out.

Example:

```python
MongoClient(
    MONGO_URI,
    socketTimeoutMS=30_000,
)
```

Very large socket timeouts can cause requests to remain stuck for long periods.

Very small values can terminate legitimate long-running operations.

Choose values based on workload and application-level latency requirements.

## Connection Pool Problems

PyMongo maintains pools of connections to MongoDB servers.

Conceptually:

```text
Application Workers
        ↓
    MongoClient
        ↓
 Connection Pools
   ┌────┼────┐
   ↓    ↓    ↓
 Conn  Conn  Conn
   └────┼────┘
        ↓
     MongoDB
```

Common pool-related symptoms include:

- Requests waiting for connections
- Increased latency
- Timeouts under load
- High connection counts
- Connection churn

## Pool Configuration

Relevant settings include:

- `maxPoolSize`
- `minPoolSize`
- `maxConnecting`
- `waitQueueTimeoutMS`

Example:

```python
MongoClient(
    MONGO_URI,
    maxPoolSize=100,
    minPoolSize=10,
    maxConnecting=4,
    waitQueueTimeoutMS=2_000,
)
```

Do not copy these values blindly into production.

Pool sizing should be based on:

```text
Application concurrency
        +
Request latency
        +
Number of workers
        +
MongoDB capacity
```

## Pool Size and Worker Count

Suppose:

```text
8 application workers
maxPoolSize = 100
```

The potential connection footprint can be much larger than 100 because pools are associated with the client process and server topology.

Increasing worker count can therefore multiply database connections.

This is especially important with:

- Gunicorn
- Uvicorn workers
- Celery
- Kubernetes replicas
- Multiple microservices

Do not calculate pool size in isolation from deployment topology.

## Connection Pool Exhaustion

A common symptom is increased request latency under load.

Conceptually:

```text
Requests
   ↓
Pool
   ↓
All connections busy
   ↓
Requests wait
   ↓
waitQueueTimeoutMS
   ↓
Timeout
```

Possible causes:

- Slow queries
- Long transactions
- Large aggregations
- Too many concurrent requests
- Pool too small
- MongoDB overloaded
- Connection leaks caused by incorrect resource handling

Increasing `maxPoolSize` may hide the symptom while increasing database load.

First determine why connections remain busy.

## Ping and Health Checks

A simple health check:

```python
client.admin.command("ping")
```

can verify basic connectivity.

However, a health endpoint should not necessarily execute a database query on every request.

For Kubernetes:

```text
Liveness
    ↓
Is process alive?

Readiness
    ↓
Can application serve traffic?
```

Database checks should be designed carefully so that temporary MongoDB failures do not create cascading restart storms.

## Replica Set Discovery Problems

A common production failure occurs when the initial MongoDB address is reachable but the addresses advertised by the replica set are not.

Example:

```text
Application
    ↓
mongo-primary.example.com
    ↓
Replica Set Discovery
    ↓
mongo1.internal
mongo2.internal
mongo3.internal
```

If the application cannot resolve `mongo2.internal`, topology discovery may fail.

This is common with:

- Docker
- Kubernetes
- NAT
- VPNs
- Split DNS
- Incorrect replica-set configuration

## Replica Set Configuration Check

Use:

```javascript
rs.conf()
```

and:

```javascript
rs.status()
```

Verify that advertised hosts are reachable from the application environment.

Do not test connectivity only from the MongoDB host.

Test from the actual Python application network.

## Authentication Errors

Typical errors include:

```text
AuthenticationFailure
OperationFailure
Unauthorized
```

Check:

- Username
- Password
- `authSource`
- Authentication mechanism
- Database
- User roles
- TLS
- Connection string encoding

Example:

```text
mongodb://app_user:password@mongo1:27017/application?authSource=admin&replicaSet=rs0
```

The authentication database can differ from the application database.

## Authorization Errors

Authentication answers:

```text
Who are you?
```

Authorization answers:

```text
What are you allowed to do?
```

A user may successfully connect but receive:

```text
not authorized on application to execute command
```

Inspect the user's roles rather than granting a broad administrative role immediately.

Production application identities should normally follow least privilege.

## TLS Issues

TLS failures can appear as:

```text
SSL handshake failed
certificate verify failed
TLSV1_ALERT
```

Investigate:

```text
Certificate
    ↓
CA trust
    ↓
Hostname
    ↓
TLS version
    ↓
PyMongo configuration
    ↓
MongoDB server configuration
```

Do not disable certificate verification as a permanent solution.

## DNS Issues

Python may report a generic server-selection error when the underlying issue is DNS.

Test from the same runtime environment:

```bash
getent hosts mongo1.example.internal
```

or:

```bash
nslookup mongo1.example.internal
```

For Kubernetes:

```bash
nslookup mongodb.default.svc.cluster.local
```

The important point is to test from the application environment, not only from a developer workstation.

## BSON Serialization Problems

MongoDB uses BSON rather than JSON internally.

Python values must therefore map to supported BSON types.

Common problems include:

- `ObjectId`
- `datetime`
- `Decimal`
- Custom classes
- Enum objects
- UUID representations
- Binary data

Example failure:

```python
collection.insert_one({
    "order_id": object(),
})
```

This produces a BSON encoding error because the object cannot be encoded as a MongoDB BSON value.

## ObjectId Problems

PyMongo represents MongoDB `ObjectId` values using:

```python
from bson import ObjectId
```

Example:

```python
order = collection.find_one({
    "_id": ObjectId(order_id),
})
```

A common mistake is querying an `ObjectId` field using a string:

```python
collection.find_one({
    "_id": order_id,
})
```

If `_id` is an `ObjectId`, this query does not match the same value.

## Safe ObjectId Conversion

Validate externally supplied IDs.

```python
from bson import ObjectId
from bson.errors import InvalidId


def parse_object_id(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except InvalidId as exc:
        raise ValueError("Invalid object id") from exc
```

Do not allow malformed identifiers to propagate into repository operations.

## FastAPI ObjectId Serialization

FastAPI/Pydantic responses need explicit handling for BSON-specific values.

A practical pattern is to convert identifiers at the API boundary.

```python
from bson import ObjectId
from pydantic import BaseModel, ConfigDict


class OrderResponse(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    id: str
    status: str


def to_order_response(document: dict) -> OrderResponse:
    return OrderResponse(
        id=str(document["_id"]),
        status=document["status"],
    )
```

The repository can continue using native `ObjectId` values internally while the HTTP API exposes strings.

## Date Handling Problems

MongoDB BSON dates map naturally to Python `datetime`.

Example:

```python
from datetime import datetime, timezone

document = {
    "created_at": datetime.now(timezone.utc),
}
```

Prefer timezone-aware UTC timestamps in backend systems.

Avoid:

```python
datetime.now()
```

when the application needs an unambiguous global timestamp.

## Naive vs Aware Datetimes

A common problem is mixing:

```python
datetime.now()
```

with:

```python
datetime.now(timezone.utc)
```

This can cause inconsistent comparisons and serialization.

Standardize:

```text
Application
    ↓
UTC-aware datetime
    ↓
MongoDB BSON Date
    ↓
API serialization
```

## Decimal and Monetary Values

Python's:

```python
float
```

should not automatically be used for exact monetary calculations.

MongoDB supports Decimal128 for decimal semantics.

PyMongo can use:

```python
from bson.decimal128 import Decimal128
from decimal import Decimal

document = {
    "amount": Decimal128(Decimal("125.50")),
}
```

Use a consistent representation across:

```text
Application
    ↓
MongoDB
    ↓
API
    ↓
Reporting
```

Changing numeric types during migration can introduce subtle bugs.

## Enum Serialization

Application enums should be converted to stable persisted values.

Example:

```python
from enum import StrEnum


class OrderStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
```

Persist:

```python
{
    "status": OrderStatus.CONFIRMED.value
}
```

rather than relying on Python-specific object serialization.

## Query Construction Problems

Avoid building MongoDB query strings manually.

Prefer structured Python dictionaries:

```python
query = {
    "status": "confirmed",
    "customer_id": customer_id,
}

orders.find(query)
```

This is easier to:

- Validate
- Test
- Log safely
- Extend
- Review

## User-Supplied Query Operators

Do not blindly accept arbitrary MongoDB filters from an HTTP request.

Dangerous design:

```python
query = request.json["filter"]
collection.find(query)
```

This gives clients control over the database query structure.

Prefer explicit API filters:

```python
status = request.query_params.get("status")

query = {}

if status:
    query["status"] = status
```

This provides a controlled query contract.

## Projection Problems

Fetching unnecessary fields increases network and serialization overhead.

Prefer:

```python
orders.find(
    {"status": "confirmed"},
    {"_id": 1, "order_id": 1, "total": 1},
)
```

when the endpoint only needs those fields.

Projection should be driven by actual application requirements.

## Cursor Misuse

PyMongo queries return cursors for multi-document operations.

Example:

```python
cursor = orders.find(
    {"status": "confirmed"}
).sort("created_at", -1).limit(100)
```

A cursor should generally be consumed incrementally.

Avoid:

```python
records = list(cursor)
```

for an unbounded large query.

This can create significant application memory pressure.

## Cursor Timeout Problems

Long-running cursor operations can fail when the cursor remains open too long under certain workloads.

Do not use `no_cursor_timeout` casually.

If a cursor must remain open for a long operation, ensure the application has a clear lifecycle and cleanup strategy.

## Pagination Problems

Using:

```python
.skip(page * limit)
```

can become increasingly expensive for deep pagination.

Example:

```python
orders.find(
    {}
).sort(
    "_id", 1
).skip(
    500_000
).limit(
    100
)
```

For large collections, prefer keyset/range pagination.

Example:

```python
query = {
    "_id": {"$gt": last_id}
}

cursor = (
    orders.find(query)
    .sort("_id", 1)
    .limit(100)
)
```

The correct pagination key depends on the access pattern and index design.

## Query Timeout Troubleshooting

When a query is slow, do not immediately increase:

```python
socketTimeoutMS
```

Instead investigate:

```text
Query
 ↓
Index
 ↓
Explain Plan
 ↓
Documents Examined
 ↓
Keys Examined
 ↓
Working Set
 ↓
Storage
```

Use:

```javascript
db.orders.find({
  status: "confirmed"
}).explain("executionStats")
```

Look for:

- `COLLSCAN`
- Excessive `totalDocsExamined`
- Excessive `totalKeysExamined`
- High execution time
- Blocking sort

## Repository Layer Problems

A repository should isolate database-specific behavior.

Example:

```python
from bson import ObjectId
from pymongo.collection import Collection


class OrderRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def get_by_id(self, order_id: str) -> dict | None:
        return self.collection.find_one({
            "_id": ObjectId(order_id),
        })
```

The service layer should not need to understand every PyMongo implementation detail.

## Service Layer Problems

Keep business logic separate from database mechanics.

```text
API
 ↓
Service
 ↓
Repository
 ↓
PyMongo
```

For example:

```python
class OrderService:
    def __init__(self, repository: OrderRepository):
        self.repository = repository

    def get_order(self, order_id: str) -> dict:
        order = self.repository.get_by_id(order_id)

        if order is None:
            raise LookupError("Order not found")

        return order
```

This makes testing and application-level reasoning easier.

## FastAPI Lifecycle Integration

A FastAPI application should manage the MongoDB client lifecycle explicitly.

A simplified pattern is:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pymongo import MongoClient


client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5_000,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    client.admin.command("ping")
    yield
    client.close()


app = FastAPI(lifespan=lifespan)
```

The exact architecture can vary, but the client should not be created per request.

## Synchronous PyMongo in FastAPI

Synchronous PyMongo performs blocking I/O.

If used directly inside an async endpoint:

```python
@app.get("/orders/{order_id}")
async def get_order(order_id: str):
    return orders.find_one({"_id": ObjectId(order_id)})
```

the blocking operation can interfere with the event loop.

For a synchronous PyMongo architecture, use appropriate synchronous execution patterns or isolate blocking work appropriately.

## Async MongoDB Clients

Modern PyMongo provides an asynchronous API through `AsyncMongoClient`.

Example:

```python
from pymongo import AsyncMongoClient

client = AsyncMongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5_000,
)
```

Then:

```python
document = await client["application"]["orders"].find_one(
    {"order_id": "ORD-1001"}
)
```

Use the async API consistently within an async architecture.

Do not mix synchronous and asynchronous client semantics casually.

## Async Client Lifecycle

An async application should manage the client according to its event-loop lifecycle.

Conceptually:

```text
FastAPI Process
      ↓
AsyncMongoClient
      ↓
Async Connection Pool
      ↓
MongoDB
```

The client should be reused rather than created for every request.

## Forking and Process Creation

Database clients and process models require careful handling.

A common production architecture is:

```text
Gunicorn
 ├── Worker 1 → MongoClient
 ├── Worker 2 → MongoClient
 └── Worker 3 → MongoClient
```

Create clients within the appropriate worker/process lifecycle.

Do not assume a MongoDB client created before process forking can safely be shared across child processes.

## Celery Integration

Background workers can create their own database client lifecycle.

Avoid repeatedly creating a client for every task if the worker process can safely reuse a process-local client.

Conceptually:

```text
Celery Worker
     ↓
Process-local MongoClient
     ↓
Connection Pool
     ↓
MongoDB
```

At the same time, avoid sharing a client across processes.

## Worker Concurrency

MongoDB connection requirements scale with:

```text
Application replicas
×
Worker processes
×
Pool configuration
```

For example:

```text
10 Kubernetes Pods
×
4 worker processes
×
100 max pool size
```

can create a much larger potential connection footprint than a single application's configuration suggests.

This is a common production capacity-planning mistake.

## Django Integration

Django does not treat MongoDB exactly like PostgreSQL through Django's native relational ORM.

Common approaches include:

- Direct PyMongo integration
- Repository layer
- Service layer
- MongoEngine
- MongoDB-specific Django integrations where appropriate

The architecture should reflect MongoDB's document model rather than forcing relational ORM assumptions onto it.

## Django Repository Pattern

Example:

```python
from bson import ObjectId
from pymongo import MongoClient


class UserRepository:
    def __init__(self, collection):
        self.collection = collection

    def get_by_id(self, user_id: str):
        return self.collection.find_one({
            "_id": ObjectId(user_id),
        })
```

The repository isolates MongoDB-specific operations from Django views and business logic.

## Django Transaction Mistake

Do not assume:

```python
from django.db import transaction

with transaction.atomic():
    ...
```

automatically creates a MongoDB transaction when using a custom MongoDB integration.

Transaction semantics depend on the MongoDB integration being used.

If transactions are required, understand the actual database driver and integration behavior.

## MongoDB Transactions in Python

PyMongo transactions require a session.

A simplified pattern:

```python
from pymongo import MongoClient

client = MongoClient(MONGO_URI)

with client.start_session() as session:
    with session.start_transaction():
        orders.update_one(
            {"order_id": "ORD-1001"},
            {"$set": {"status": "confirmed"}},
            session=session,
        )

        inventory.update_one(
            {"sku": "SKU-001"},
            {"$inc": {"available": -1}},
            session=session,
        )
```

Every operation intended to participate in the transaction must use the session.

## Transaction Problems

Common mistakes include:

- Forgetting the session argument
- Keeping transactions open too long
- Performing slow external calls inside transactions
- Retrying non-idempotent application logic
- Assuming commit ambiguity means no state changed
- Using transactions for operations that should be modeled atomically within one document

Prefer single-document atomicity when the data model allows it.

## Bulk Write Issues

For large operations:

```python
from pymongo import UpdateOne

operations = [
    UpdateOne(
        {"order_id": order["order_id"]},
        {"$set": order},
        upsert=True,
    )
    for order in orders
]

result = collection.bulk_write(
    operations,
    ordered=False,
)
```

Bulk operations can improve throughput by reducing command round trips.

However, large batches increase:

- Memory usage
- Failure scope
- Retry complexity

Use bounded batches.

## Bulk Write Error Handling

Do not assume:

```python
bulk_write(...)
```

either updates everything or nothing.

Bulk operations can contain individual failures.

Inspect:

- Matched count
- Modified count
- Inserted count
- Upserted count
- Write errors

For migration workflows, persist enough information to reconcile failures.

## Retryable Errors

MongoDB drivers support retry behavior for appropriate operations and configurations.

Application code should still avoid unbounded retries.

A reasonable model is:

```text
Operation
 ↓
Transient failure?
 ├── No → Return error
 └── Yes
       ↓
Bounded retry
       ↓
Backoff
       ↓
Retry
       ↓
Final failure
```

Retries should not transform a database outage into a traffic amplification problem.

## Idempotency

Retries are safest when operations are idempotent.

For example:

```python
collection.update_one(
    {"order_id": order_id},
    {"$set": {"status": "confirmed"}},
)
```

is generally easier to retry safely than:

```python
collection.update_one(
    {"order_id": order_id},
    {"$inc": {"balance": 100}},
)
```

because repeating the increment changes state repeatedly.

This distinction is critical in distributed systems.

## Exception Handling

Avoid catching every MongoDB exception as a generic error.

Bad:

```python
try:
    collection.insert_one(document)
except Exception:
    return None
```

This hides:

- Authentication failures
- Duplicate keys
- Validation errors
- Timeouts
- Network failures
- Programming bugs

Prefer targeted exception handling.

```python
from pymongo.errors import DuplicateKeyError, ServerSelectionTimeoutError


try:
    collection.insert_one(document)
except DuplicateKeyError as exc:
    raise ValueError("Document already exists") from exc
except ServerSelectionTimeoutError as exc:
    raise RuntimeError("MongoDB unavailable") from exc
```

## Duplicate Key Troubleshooting

Typical exception:

```python
from pymongo.errors import DuplicateKeyError
```

Investigate:

```text
Which index?
Which key?
Which document?
Why was the operation retried?
Is the operation expected to be idempotent?
```

Do not simply remove the unique index.

## Schema Validation Errors

MongoDB may reject a document because of collection validation.

Python should expose a meaningful application-level error without leaking internal database details.

Conceptually:

```text
Pydantic Validation
        ↓
Application Validation
        ↓
MongoDB Schema Validation
        ↓
Database Write
```

Using both layers provides defense in depth.

## Pydantic and MongoDB Schema Drift

A Pydantic model and MongoDB validator can diverge.

Example:

```text
Pydantic:
status = pending | confirmed

MongoDB:
status = pending | confirmed | cancelled
```

This creates inconsistent behavior.

Treat schema changes as coordinated application/database changes.

## Connection Pool Monitoring

Track:

- Active connections
- Available connections
- Connection wait time
- Connection creation
- Application concurrency
- MongoDB connection count

When latency increases, determine whether the bottleneck is:

```text
Pool
 ↓
Network
 ↓
MongoDB server selection
 ↓
Query execution
```

before increasing pool size.

## Performance Issues

A Python MongoDB integration can be slow even when MongoDB itself is healthy.

Potential causes:

- Excessive serialization
- Fetching large documents
- Returning unnecessary fields
- N+1 queries
- Unbounded cursors
- Deep `skip()` pagination
- Missing indexes
- Large aggregation results
- Excessive connection churn
- Blocking synchronous calls in async paths

## N+1 Query Problem

Bad:

```text
Fetch 100 orders
    ↓
For each order:
    ↓
Fetch customer
    ↓
100 additional queries
```

This can create:

```text
1 + 100 = 101 database operations
```

Consider:

- Embedding
- `$lookup`
- Batch queries
- Application-side caching
- Data-model redesign

The correct solution depends on access patterns.

## Large Document Problems

A Python application can accidentally retrieve large documents that it does not need.

Bad:

```python
document = collection.find_one({"order_id": order_id})
```

when the endpoint only needs:

```text
status
total
```

Prefer projection:

```python
document = collection.find_one(
    {"order_id": order_id},
    {"_id": 1, "status": 1, "total": 1},
)
```

This reduces network and Python-side processing.

## Aggregation from Python

Use aggregation when computation belongs naturally in MongoDB.

Example:

```python
pipeline = [
    {"$match": {"status": "completed"}},
    {
        "$group": {
            "_id": "$customer_id",
            "total": {"$sum": "$total"},
        }
    },
]

results = collection.aggregate(pipeline)
```

Do not immediately convert an enormous aggregation cursor to a list:

```python
results = list(collection.aggregate(pipeline))
```

unless the result size is known to be bounded.

## Change Stream Problems

Change streams can fail because of:

- Replica-set topology issues
- Network interruption
- Cursor interruption
- Consumer restart
- Invalid resume token
- Long outages exceeding available history

A Python consumer should be designed around:

```text
Consume
 ↓
Process
 ↓
Persist progress
 ↓
Handle failure
 ↓
Resume
```

Event handlers should be idempotent.

## Logging MongoDB Errors

Use structured logs.

Example:

```python
logger.exception(
    "MongoDB operation failed",
    extra={
        "operation": "find_order",
        "order_id": order_id,
    },
)
```

Avoid logging:

- Passwords
- Connection strings
- Access tokens
- Full sensitive documents
- Personally identifiable information unnecessarily

## Observability

A production Python service should expose enough information to distinguish:

```text
Application latency
MongoDB latency
Pool waiting
Server selection
Query execution
Serialization
```

Useful metrics include:

- Request latency
- MongoDB operation latency
- Timeout count
- Duplicate-key count
- Server-selection failures
- Pool wait time
- Connection count
- Transaction aborts
- Retry count
- Query-specific latency

## Health Checks

A health endpoint should distinguish between:

### Liveness

```text
Is the process running?
```

### Readiness

```text
Can this instance safely serve traffic?
```

### Dependency health

```text
Is MongoDB reachable?
```

Do not make every transient MongoDB error trigger a process restart.

A bad health-check design can cause:

```text
MongoDB outage
    ↓
All application pods marked unhealthy
    ↓
Pods restart
    ↓
More MongoDB connections
    ↓
Recovery becomes harder
```

## Testing MongoDB Integration

Use integration tests for:

- BSON serialization
- ObjectId behavior
- Query correctness
- Index-dependent queries
- Transactions
- Validation
- Replica-set behavior
- Error handling

Mocking every MongoDB call can hide integration defects.

A practical strategy is:

```text
Unit Tests
    +
MongoDB Integration Tests
    +
API Tests
    +
Failure Tests
```

## Test Database Isolation

Tests should use isolated databases or ephemeral MongoDB environments.

Avoid running destructive test suites against shared production-like databases.

A test should be able to determine:

```text
What data existed before?
What data did the test create?
What data did the test modify?
```

## Docker Integration Testing

A MongoDB container can be used for integration testing.

Conceptually:

```text
pytest
   ↓
Application
   ↓
PyMongo
   ↓
MongoDB Test Container
```

For transaction and replica-set tests, the test environment must support the required topology rather than using a standalone MongoDB process.

## Common Configuration Mistakes

| Mistake | Result |
|---|---|
| New client per request | Connection churn |
| Wrong `authSource` | Authentication failure |
| Missing `replicaSet` | Topology discovery issues |
| Incorrect advertised hostnames | Server selection failure |
| Very small timeout | False failures |
| Huge timeout | Requests hang too long |
| Oversized pool | Excessive DB connections |
| Undersized pool | Pool waits and latency |
| Sync PyMongo in async path | Event-loop blocking |
| Unbounded cursor conversion | Memory pressure |
| String `_id` instead of `ObjectId` | Query mismatch |
| Naive datetime | Time inconsistencies |
| Broad exception handling | Hidden production failures |

## Structured Troubleshooting Methodology

Use this workflow for any Python/MongoDB incident:

```text
Symptom
↓
Possible causes
↓
Isolation strategy
↓
Diagnostic commands
↓
Root cause
↓
Corrective action
↓
Prevention
```

## Connection Failure Workflow

### Symptom

```text
ServerSelectionTimeoutError
```

### Possible Causes

- DNS failure
- Network restriction
- MongoDB unavailable
- Wrong port
- Replica-set discovery failure
- TLS failure
- Authentication failure

### Isolation Strategy

Test from the application environment:

```bash
mongosh "mongodb://..."
```

### Diagnostic Commands

```bash
nslookup mongo1.example.internal
```

and:

```bash
mongosh "mongodb://..."
```

Then inspect:

```javascript
db.hello()
```

### Root Cause

Determine whether the failure is:

```text
DNS
Network
TLS
Authentication
Topology
MongoDB availability
```

### Corrective Action

Fix the failing infrastructure or configuration layer.

### Prevention

- Validate configuration at startup.
- Monitor MongoDB connectivity.
- Test deployment-network connectivity.
- Use replica-set-aware connection strings.

## Query Performance Workflow

### Symptom

Python endpoint latency increases.

### Possible Causes

- Missing index
- Slow aggregation
- Large documents
- N+1 queries
- Pool contention
- MongoDB resource pressure

### Isolation Strategy

Measure separately:

```text
HTTP latency
    ↓
Python execution time
    ↓
MongoDB operation time
    ↓
Serialization time
```

### Diagnostic Commands

Use:

```javascript
db.collection.find({...}).explain("executionStats")
```

and inspect application metrics.

### Root Cause

Determine whether time is spent in:

```text
Pool wait
Server selection
Query execution
Network transfer
Python serialization
```

### Corrective Action

Optimize the actual bottleneck.

### Prevention

- Monitor query latency.
- Review indexes.
- Use projection.
- Avoid N+1 queries.
- Bound result sets.

## Serialization Failure Workflow

### Symptom

```text
InvalidDocument
```

### Possible Causes

- Unsupported Python object
- Invalid BSON type
- Incorrect custom class
- Decimal handling
- Datetime handling

### Isolation Strategy

Identify the specific field that cannot be encoded.

### Diagnostic Approach

Reduce the document to:

```python
collection.insert_one({"field": value})
```

and identify the incompatible value.

### Corrective Action

Convert to a supported BSON type.

### Prevention

Validate domain objects before persistence.

## Transaction Failure Workflow

### Symptom

Transaction aborts or transient transaction errors occur.

### Possible Causes

- Primary election
- Write conflict
- Transaction timeout
- Network interruption
- Long transaction
- Incorrect session usage

### Isolation Strategy

Check MongoDB topology and transaction duration.

### Diagnostic Approach

Inspect:

```text
Replica-set health
Transaction duration
Application retries
Write conflicts
MongoDB logs
```

### Corrective Action

Use bounded transaction retries where supported and redesign long-running transactions.

### Prevention

- Keep transactions short.
- Use appropriate indexes.
- Avoid external network calls inside transactions.
- Make retryable application behavior idempotent.

## Production Architecture

A scalable Python/MongoDB service can use:

```mermaid
flowchart TB
    Client[Client] --> Gateway[Nginx / Load Balancer]
    Gateway --> API1[FastAPI Worker]
    Gateway --> API2[FastAPI Worker]

    API1 --> Service1[Service Layer]
    API2 --> Service2[Service Layer]

    Service1 --> Repo1[Mongo Repository]
    Service2 --> Repo2[Mongo Repository]

    Repo1 --> Mongo[(MongoDB Replica Set)]
    Repo2 --> Mongo

    Service1 --> Redis[(Redis)]
    Service2 --> Redis

    Worker[Celery Workers] --> Mongo
    Worker --> Redis
```

Production design should explicitly account for:

- Connection pool sizing
- Worker count
- MongoDB capacity
- Replica-set failover
- Retry behavior
- Query performance
- Monitoring
- Secret management
- Backup and recovery

## Deployment Considerations

### Docker

Ensure the MongoDB host is resolvable from the application container.

### Kubernetes

Ensure:

- Stable MongoDB service discovery
- Correct network policies
- Secret injection
- Appropriate resource limits
- Connection pool sizing
- Readiness behavior

### AWS

For managed MongoDB deployments, keep application credentials in an appropriate secret-management system and restrict network access through private connectivity where possible.

## Security Checklist

- [ ] No credentials hard-coded in source.
- [ ] MongoDB URI not logged.
- [ ] TLS enabled where required.
- [ ] Application user uses least privilege.
- [ ] Production access is network restricted.
- [ ] Secrets are stored in a secret-management system.
- [ ] User-supplied query structures are not passed directly to MongoDB.
- [ ] Sensitive documents are not logged.
- [ ] Exported production data is protected.
- [ ] Database credentials are rotated according to operational policy.

## Production Checklist

### Application

- [ ] One appropriate MongoDB client per process.
- [ ] Connection lifecycle is explicit.
- [ ] Timeouts are configured intentionally.
- [ ] Pool size is based on actual concurrency.
- [ ] Retry behavior is bounded.
- [ ] Queries are indexed.
- [ ] Projections are used where appropriate.
- [ ] Pagination is bounded.
- [ ] Large cursors are not materialized unnecessarily.

### Data

- [ ] `ObjectId` handling is consistent.
- [ ] Dates use UTC-aware semantics.
- [ ] Decimal values use an appropriate representation.
- [ ] Schema validation is understood.
- [ ] Application and database schemas are compatible.

### FastAPI / Django

- [ ] MongoDB client is not created per request.
- [ ] Async and sync APIs are not mixed incorrectly.
- [ ] Repository and service boundaries are clear.
- [ ] Health checks do not create cascading failures.
- [ ] Background imports run outside request handlers.

### Operations

- [ ] MongoDB topology is monitored.
- [ ] Connection pool behavior is monitored.
- [ ] Query latency is monitored.
- [ ] Server-selection failures are alerted.
- [ ] Replica-set health is monitored.
- [ ] Backups are independent and tested.
- [ ] Import/export operations are auditable.

## Interview Traps

### "Create a MongoClient for every request."

This creates unnecessary connection and topology-management overhead. Reuse an appropriate client per process.

### "Increase `maxPoolSize` whenever requests are slow."

Not necessarily. Slow queries, MongoDB saturation, server selection, or pool contention may be the actual cause.

### "PyMongo is always asynchronous in FastAPI."

No. Traditional PyMongo APIs are synchronous. Modern PyMongo also provides asynchronous APIs, and the chosen model should match the application's execution architecture.

### "A MongoDB ObjectId is just a string."

No. `ObjectId` is a BSON type. Converting it to a string at an API boundary is common, but MongoDB queries must use the correct BSON type.

### "A failed MongoDB write means nothing changed."

Not necessarily. Retryable operations, network failures, and ambiguous outcomes require careful reasoning about whether the server processed the operation.

### "MongoDB transactions should wrap every service operation."

No. Single-document atomicity and appropriate data modeling should be preferred where possible. Transactions introduce additional coordination and performance costs.

### "The database is slow because the Python code is slow."

Not necessarily. Measure the full path:

```text
Pool wait
↓
Server selection
↓
MongoDB execution
↓
Network transfer
↓
BSON decoding
↓
Application processing
```

### "Mocking PyMongo is enough for testing."

Mocks are useful for unit tests, but integration tests are required to catch BSON, query, index, transaction, topology, and serialization issues.

## Key Takeaways

- **Treat Python/MongoDB failures as cross-layer problems: application lifecycle, PyMongo, connection pools, network, topology, MongoDB execution, and serialization all need to be considered.**
- **Reuse an appropriate MongoDB client per process, size connection pools based on real application concurrency, and configure server-selection, connection, socket, and pool-wait timeouts intentionally.**
- **Keep BSON types explicit at application boundaries, especially `ObjectId`, dates, decimals, and custom values; API serialization should not accidentally change database semantics.**
- **Use bounded queries, projection, efficient pagination, indexes, bulk operations, and appropriate async/sync execution models to prevent Python integration from becoming the performance bottleneck.**
- **Production troubleshooting should isolate the failing layer with measurements and targeted diagnostics rather than masking symptoms with larger pools, longer timeouts, broad retries, or administrative permissions.**