# 02- PyMongo

## Overview

PyMongo is the official Python driver for MongoDB and provides the primary low-level interface for Python applications interacting with MongoDB. It exposes MongoDB's native concepts directly rather than forcing the database into a relational ORM model. :contentReference[oaicite:0]{index=0}

PyMongo is suitable for:

- REST APIs
- FastAPI applications
- Django services
- gRPC services
- Microservices
- Celery workers
- ETL pipelines
- Event consumers
- Background jobs
- Data-processing services
- Administrative and operational tooling

The driver provides APIs for:

- Connection management
- Authentication
- TLS
- CRUD
- Aggregation
- Indexes
- Sessions
- Transactions
- Change streams
- Bulk operations
- Read and write concerns
- Retryable operations
- Connection pooling
- Server selection
- BSON encoding and decoding

The core abstraction is:

```text
Application
    ↓
MongoClient
    ↓
Database
    ↓
Collection
    ↓
MongoDB
```

A senior backend engineer should understand both the PyMongo API and the MongoDB behavior behind it. PyMongo is not a substitute for understanding query planning, indexes, replication, transactions, or MongoDB's consistency model.

## Installation

Install PyMongo using the Python package manager:

```bash
python -m pip install pymongo
```

Verify the installation:

```bash
python -c "import pymongo; print(pymongo.version)"
```

For production applications, manage PyMongo through the project's dependency-management system and test driver upgrades against the target Python and MongoDB Server versions. MongoDB recommends checking compatibility before upgrading PyMongo and reviewing breaking changes and deprecations. :contentReference[oaicite:1]{index=1}

A typical dependency declaration might be:

```text
pymongo>=4,<5
```

The exact constraint should be based on the application's compatibility policy rather than copied as a universal default.

## PyMongo Architecture

A typical synchronous application has one long-lived `MongoClient` per process:

```mermaid
flowchart TD
    APP[Python Process]
    CLIENT[MongoClient]
    POOL[Connection Pool]
    SERVER[MongoDB Deployment]

    APP --> CLIENT
    CLIENT --> POOL
    POOL --> SERVER
```

`MongoClient` manages topology discovery and connection pools. PyMongo is thread-safe and provides built-in connection pooling, so most threaded applications should reuse a single `MongoClient` rather than creating one for every request. :contentReference[oaicite:2]{index=2}

For an application with multiple worker processes:

```text
Application
├── Worker 1
│   └── MongoClient
│       └── Connection Pool
│
├── Worker 2
│   └── MongoClient
│       └── Connection Pool
│
└── Worker 3
    └── MongoClient
        └── Connection Pool
```

The important consequence is that pool sizing is per process, not necessarily per application deployment.

## MongoClient

`MongoClient` is the primary entry point into PyMongo.

Basic connection:

```python
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
```

Select a database:

```python
database = client["orders"]
```

Select a collection:

```python
orders = database["orders"]
```

Then execute an operation:

```python
order = orders.find_one({
    "order_id": "ORD-1001",
})
```

MongoDB's current PyMongo documentation supports both synchronous `MongoClient` and asynchronous `AsyncMongoClient`. :contentReference[oaicite:3]{index=3}

## Connection URI

A standard URI can contain:

```text
mongodb://username:password@host:27017/database?options
```

Example:

```python
from pymongo import MongoClient

client = MongoClient(
    "mongodb://app_user:secret@mongo.internal:27017/orders"
)
```

For Atlas or other SRV-based deployments:

```python
client = MongoClient(
    "mongodb+srv://app_user:secret@cluster.example.mongodb.net/orders"
)
```

A connection string can specify:

- authentication credentials
- hosts
- ports
- authentication database
- TLS
- timeouts
- retry behavior
- read preference
- write concern
- replica-set options
- other driver configuration

PyMongo also allows these settings to be supplied directly to `MongoClient`, which can make configuration easier to manage programmatically. :contentReference[oaicite:4]{index=4}

## Configuration Management

Do not embed production credentials in Python source code.

Bad:

```python
client = MongoClient(
    "mongodb://admin:super-secret-password@mongo:27017"
)
```

Prefer:

```python
import os

mongo_uri = os.environ["MONGO_URI"]

client = MongoClient(mongo_uri)
```

For production, the environment variable should generally be populated from a secret-management system.

Typical architecture:

```text
Secret Manager
      ↓
Deployment Platform
      ↓
Environment / Secret Injection
      ↓
Python Process
      ↓
MongoClient
```

Examples include:

- AWS Secrets Manager
- Kubernetes Secrets
- External Secrets
- HashiCorp Vault
- Managed platform secret stores

## Connection Lifecycle

A typical synchronous application lifecycle is:

```text
Process Startup
      ↓
Create MongoClient
      ↓
Topology Discovery
      ↓
Connection Pool
      ↓
Application Requests
      ↓
Reuse Client / Connections
      ↓
Process Shutdown
      ↓
client.close()
```

Example:

```python
from pymongo import MongoClient

client = MongoClient(
    mongo_uri,
    serverSelectionTimeoutMS=5000,
)

try:
    client.admin.command("ping")
    run_application()
finally:
    client.close()
```

For long-running services, the client normally remains alive for the process lifetime.

## Connectivity and Server Selection

Creating a `MongoClient` does not necessarily mean that the application has already completed a database operation.

A deliberate health check can execute:

```python
client.admin.command("ping")
```

Example:

```python
from pymongo import MongoClient
from pymongo.errors import PyMongoError

client = MongoClient(
    mongo_uri,
    serverSelectionTimeoutMS=3000,
)

try:
    client.admin.command("ping")
except PyMongoError:
    raise RuntimeError("MongoDB is unavailable")
```

Do not use an expensive application query as a Kubernetes or load-balancer health check.

## Server Selection

PyMongo maintains knowledge about the MongoDB deployment topology.

For a replica set:

```text
              MongoClient
                  │
          Topology Discovery
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
    Primary    Secondary   Secondary
```

The driver selects an appropriate server based on:

- operation type
- read preference
- server availability
- topology
- latency
- transaction requirements

This is one reason a long-lived `MongoClient` is important: the driver can maintain and update topology information.

## Connection Pooling

PyMongo maintains connection pools for MongoDB servers.

Conceptually:

```text
MongoClient
    │
    ├── Connection 1
    ├── Connection 2
    ├── Connection 3
    ├── Connection 4
    └── ...
```

The pool avoids repeatedly establishing TCP/TLS connections.

MongoDB's current documentation lists `maxPoolSize=100` as the default maximum number of concurrent connections maintained by a pool. `minPoolSize` defaults to `0`. Other important settings include `maxIdleTimeMS`, `connectTimeoutMS`, `socketTimeoutMS`, and `waitQueueTimeoutMS`. :contentReference[oaicite:5]{index=5}

Example:

```python
client = MongoClient(
    mongo_uri,
    maxPoolSize=100,
    minPoolSize=5,
    maxIdleTimeMS=60000,
    waitQueueTimeoutMS=5000,
)
```

These are configuration examples, not universal production values.

## Pool Sizing

Connection-pool capacity must be considered across application processes.

For example:

```text
12 Kubernetes Pods
×
4 worker processes
×
100 max connections
=
4,800 potential connections
```

The theoretical maximum is not necessarily reached, but the calculation illustrates why pool sizing must consider:

- pod count
- process count
- concurrency
- MongoDB capacity
- workload latency
- connection limits
- failover behavior

Increasing `maxPoolSize` does not automatically improve throughput.

An oversized pool can increase:

- server connection pressure
- memory usage
- context switching
- contention
- operational complexity

## Connection Pool Waits

If all connections are busy, new operations can wait for a connection.

Configure a bounded wait:

```python
client = MongoClient(
    mongo_uri,
    maxPoolSize=100,
    waitQueueTimeoutMS=5000,
)
```

A pool timeout is different from a MongoDB query timeout.

```text
Request
   ↓
Wait for pool connection
   ↓
Connection acquired
   ↓
Send MongoDB operation
   ↓
Wait for response
```

Both stages need sensible latency budgets.

## Timeout Configuration

Important PyMongo timeout settings include:

| Option | Purpose |
|---|---|
| `serverSelectionTimeoutMS` | Time allowed to select a suitable MongoDB server |
| `connectTimeoutMS` | Time allowed to establish a new connection |
| `socketTimeoutMS` | Time waiting for a socket response |
| `waitQueueTimeoutMS` | Time waiting for a pool connection |
| `timeoutMS` | Overall client-side operation timeout |

Example:

```python
client = MongoClient(
    mongo_uri,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    socketTimeoutMS=10000,
)
```

PyMongo also provides a client-side `timeout()` mechanism for bounding the complete operation lifecycle. :contentReference[oaicite:6]{index=6}

Timeout values should come from the application's latency budget.

For example:

```text
API timeout:             2 seconds
MongoDB operation budget: 1 second
Network / retry budget:  remaining time
```

The exact values depend on the service.

## Thread Safety

`MongoClient` is thread-safe and designed to be shared across threads. MongoDB specifically recommends reusing a client across multiple requests in typical threaded applications. :contentReference[oaicite:7]{index=7}

This makes it appropriate for:

- synchronous web applications
- thread-based workers
- WSGI applications
- many background-worker architectures

Do not create one client per thread unless there is a specific architectural reason.

## Forking

A `MongoClient` should not be blindly inherited by forked child processes.

If using process forking:

```text
Parent
  │
  ├── fork
  ├── Worker 1 → create MongoClient
  ├── Worker 2 → create MongoClient
  └── Worker 3 → create MongoClient
```

Create the client inside the child process.

MongoDB warns against passing a `MongoClient` instance from a parent process to a forked child because it can result in deadlocks. :contentReference[oaicite:8]{index=8}

This matters with:

- Gunicorn
- multiprocessing
- Celery workers
- custom process pools

## BSON

MongoDB stores documents using BSON.

PyMongo automatically converts supported Python values into BSON when sending documents and decodes BSON responses into Python objects.

Example:

```python
from datetime import datetime, timezone
from bson import ObjectId

document = {
    "_id": ObjectId(),
    "created_at": datetime.now(timezone.utc),
    "status": "pending",
}
```

Important BSON-related Python types include:

- `ObjectId`
- `datetime`
- `Decimal128`
- binary values
- regular expressions
- timestamps

## ObjectId

`ObjectId` is commonly used as the MongoDB `_id` value.

```python
from bson import ObjectId

order_id = ObjectId()
```

Query:

```python
order = orders.find_one({
    "_id": order_id,
})
```

If an API receives an identifier as a string:

```python
from bson import ObjectId
from bson.errors import InvalidId


def parse_id(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except InvalidId as exc:
        raise ValueError("Invalid MongoDB ObjectId") from exc
```

Do not silently accept invalid identifiers.

## Type Hints

PyMongo supports type hints for `MongoClient` and document types.

A generic approach:

```python
from typing import Any

from pymongo import MongoClient

client: MongoClient[dict[str, Any]] = MongoClient(
    mongo_uri
)
```

For structured document types, `TypedDict` can improve static analysis:

```python
from typing import TypedDict

from pymongo import MongoClient


class Order(TypedDict):
    order_id: str
    status: str
    total: float


client: MongoClient[Order] = MongoClient(
    mongo_uri
)
```

Type hints do not enforce MongoDB schema at runtime. They improve developer tooling and static analysis.

## Databases and Collections

Database access:

```python
database = client["orders"]
```

Collection access:

```python
orders = database["orders"]
```

Multiple collections:

```python
orders = database["orders"]
customers = database["customers"]
events = database["events"]
```

Prefer explicit indexing when collection names are dynamic or potentially conflict with Python attributes.

## CRUD

### Insert One

```python
result = orders.insert_one({
    "order_id": "ORD-1001",
    "customer_id": "CUST-100",
    "status": "pending",
    "total": 249.50,
})

print(result.inserted_id)
```

### Insert Many

```python
result = orders.insert_many(
    [
        {
            "order_id": "ORD-1001",
            "status": "pending",
        },
        {
            "order_id": "ORD-1002",
            "status": "confirmed",
        },
    ],
    ordered=False,
)
```

`ordered=False` allows independent operations to proceed without requiring strict sequence ordering.

Use it only when application semantics do not depend on ordering.

### Find One

```python
order = orders.find_one({
    "order_id": "ORD-1001",
})
```

### Find Many

```python
cursor = orders.find({
    "status": "pending",
})

for order in cursor:
    process(order)
```

Avoid converting an unbounded cursor into a list:

```python
documents = list(orders.find({}))
```

This can create substantial memory pressure.

## Projection

Retrieve only required fields:

```python
cursor = orders.find(
    {"status": "pending"},
    {
        "_id": 1,
        "order_id": 1,
        "customer_id": 1,
        "status": 1,
    },
)
```

Projection can reduce:

- network transfer
- BSON decoding
- application memory
- response serialization

It does not automatically make every query fast; index design and query execution still matter.

## Sorting

```python
from pymongo import DESCENDING

cursor = orders.find({
    "customer_id": customer_id,
}).sort(
    "created_at",
    DESCENDING,
)
```

Large sorts should be evaluated with `explain()` and appropriate indexes.

## Limit

Always bound API-facing queries:

```python
cursor = orders.find(
    {"status": "pending"}
).limit(100)
```

Never allow clients to determine an unlimited result size.

## Skip

Offset pagination is straightforward:

```python
cursor = (
    orders.find({})
    .sort("created_at", -1)
    .skip(offset)
    .limit(page_size)
)
```

However, large offsets can become increasingly expensive.

For high-volume collections, cursor-based pagination is generally preferable.

## Cursor-Based Pagination

A stable pagination key can be used:

```python
query = {
    "created_at": {
        "$lt": last_created_at,
    }
}

cursor = (
    orders.find(query)
    .sort("created_at", -1)
    .limit(50)
)
```

The pagination field should normally be supported by an appropriate index.

For deterministic ordering when timestamps can collide, use a compound key such as:

```text
created_at + _id
```

## Update One

Use update operators for partial changes:

```python
result = orders.update_one(
    {"order_id": "ORD-1001"},
    {
        "$set": {
            "status": "confirmed",
        }
    },
)
```

Avoid replacing a document when only one field needs to change.

## Update Many

```python
result = orders.update_many(
    {
        "status": "pending",
        "expires_at": {
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

Large updates should be treated as operational workloads.

Consider:

- number of documents
- index support
- write load
- replication impact
- lock/resource behavior
- application traffic

## Replace One

`replace_one()` replaces the document rather than applying update operators.

```python
result = orders.replace_one(
    {"order_id": "ORD-1001"},
    {
        "order_id": "ORD-1001",
        "status": "confirmed",
        "total": 249.50,
    },
)
```

Be careful not to accidentally remove fields that existed in the previous document.

## Upsert

An upsert performs an update if a match exists or inserts a document if no match exists.

```python
result = orders.update_one(
    {
        "external_id": external_id,
    },
    {
        "$set": {
            "status": "confirmed",
        }
    },
    upsert=True,
)
```

For concurrency-safe uniqueness, combine upserts with a unique index:

```python
orders.create_index(
    "external_id",
    unique=True,
)
```

## Delete One

```python
result = orders.delete_one({
    "_id": order_id,
})
```

## Delete Many

```python
result = orders.delete_many({
    "status": "expired",
})
```

Avoid broad destructive operations unless they are explicitly intended:

```python
orders.delete_many({})
```

Production deletion workflows should normally include:

- explicit filters
- authorization
- auditing where required
- backups
- dry-run or count verification for dangerous operations

## Bulk Write

Bulk operations reduce round trips.

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

Bulk operations are useful for:

- ingestion
- migrations
- batch updates
- ETL
- synchronization jobs

Do not create arbitrarily large batches. Balance:

- network efficiency
- memory usage
- operation duration
- retry complexity
- server load

## Write Results

Write result objects expose useful information.

```python
result.inserted_id
```

For updates:

```python
result.matched_count
result.modified_count
result.upserted_id
```

For deletes:

```python
result.deleted_count
```

Do not assume a matched document was actually changed.

For example:

```text
matched_count = 1
modified_count = 0
```

can mean the document already contained the requested value.

## Query Operators

PyMongo queries use MongoDB query operators.

Comparison:

```python
{
    "total": {
        "$gte": 100,
    }
}
```

Logical:

```python
{
    "$or": [
        {"status": "pending"},
        {"status": "processing"},
    ]
}
```

Array:

```python
{
    "tags": {
        "$in": ["priority", "vip"],
    }
}
```

Existence:

```python
{
    "deleted_at": {
        "$exists": False,
    }
}
```

The Python dictionary is simply the driver representation of a MongoDB query document.

## Query Validation

Do not expose arbitrary query dictionaries through public APIs.

Bad:

```python
query = request.json["filter"]

collection.find(query)
```

This creates a direct boundary between untrusted input and MongoDB's query language.

Prefer:

```python
class OrderFilter:
    status: str | None
    customer_id: str | None
```

Then explicitly construct:

```python
query = {}

if filters.status:
    query["status"] = filters.status

if filters.customer_id:
    query["customer_id"] = filters.customer_id
```

This provides control over:

- supported fields
- allowed operators
- input types
- query complexity
- authorization boundaries

## Aggregation

PyMongo represents an aggregation pipeline as a Python list.

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
            "total_value": {
                "$sum": "$total",
            },
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

The aggregation engine remains MongoDB-side; Python primarily constructs the pipeline and consumes results.

## Aggregation Pipeline Design

Prefer early filtering:

```python
pipeline = [
    {"$match": {"status": "confirmed"}},
    {"$group": {
        "_id": "$customer_id",
        "count": {"$sum": 1},
    }},
]
```

Avoid unnecessary processing before `$match`.

For complex pipelines, consider:

- index usage
- intermediate document volume
- `$unwind` expansion
- `$lookup` cost
- `$sort` memory
- result size
- execution time

## Indexes

PyMongo can create indexes:

```python
orders.create_index(
    [
        ("customer_id", 1),
        ("created_at", -1),
    ],
    name="customer_created_at",
)
```

Unique:

```python
orders.create_index(
    "external_id",
    unique=True,
    name="external_id_unique",
)
```

TTL:

```python
events.create_index(
    "expires_at",
    expireAfterSeconds=0,
    name="events_ttl",
)
```

Indexes should be managed deliberately in production rather than created unpredictably during application startup.

## Index Creation Strategy

Prefer:

```text
Index Definition
      ↓
Migration / Infrastructure Workflow
      ↓
Review
      ↓
Create / Validate
      ↓
Application Deployment
```

Avoid:

```text
Every API Pod
      ↓
create_index()
      ↓
Production startup
```

Although MongoDB handles repeated index specifications intelligently, making index administration part of every application startup creates unnecessary coupling between application availability and database schema operations.

## Explain

PyMongo supports `explain()` through the cursor API.

Example:

```python
plan = (
    orders.find({
        "customer_id": customer_id,
        "status": "confirmed",
    })
    .sort("created_at", -1)
    .explain()
)
```

Inspect:

- winning plan
- rejected plans
- `nReturned`
- `totalKeysExamined`
- `totalDocsExamined`
- execution time
- `COLLSCAN`
- `IXSCAN`
- `FETCH`
- `SORT`

A query returning 20 documents while examining hundreds of thousands of documents deserves investigation.

## Query Optimization Workflow

Use:

```text
Slow API
   ↓
Measure MongoDB latency
   ↓
Capture actual query
   ↓
Run explain()
   ↓
Inspect winning plan
   ↓
Inspect keys/docs examined
   ↓
Check indexes
   ↓
Check collection size
   ↓
Check server resource usage
   ↓
Change query/index
   ↓
Benchmark again
```

Do not optimize MongoDB queries based solely on intuition.

## Sessions

Sessions group related MongoDB operations.

```python
with client.start_session() as session:
    document = orders.find_one(
        {"_id": order_id},
        session=session,
    )
```

Sessions are required for transactions and can also provide session-level behavior for related operations.

## Transactions

PyMongo supports multi-document transactions through sessions.

```python
with client.start_session() as session:
    with session.start_transaction():
        orders.update_one(
            {"_id": order_id},
            {"$set": {"status": "confirmed"}},
            session=session,
        )

        events.insert_one(
            {
                "order_id": order_id,
                "type": "order_confirmed",
            },
            session=session,
        )
```

Transactions execute as an atomic unit. MongoDB's current PyMongo documentation recommends reusing the `MongoClient` for multiple sessions and transactions. :contentReference[oaicite:9]{index=9}

## Transaction Helper

For transaction workflows requiring retry handling, PyMongo provides `with_transaction()`.

Conceptually:

```python
def callback(session):
    orders.update_one(
        {"_id": order_id},
        {"$set": {"status": "confirmed"}},
        session=session,
    )

    events.insert_one(
        {"order_id": order_id},
        session=session,
    )


with client.start_session() as session:
    session.with_transaction(callback)
```

Transactions should remain short and should not contain unnecessary external work.

Do not:

```text
Start transaction
   ↓
Call external HTTP API
   ↓
Wait 5 seconds
   ↓
Write MongoDB
   ↓
Commit
```

External network calls should generally not be performed inside the transaction.

## Transaction Limitations

A transaction introduces additional coordination and resource usage.

Avoid using transactions for operations that can be modeled as:

```text
Single document
      ↓
Atomic update
```

Prefer MongoDB's document model when it naturally represents the consistency boundary.

Use transactions when the business invariant genuinely crosses documents or collections.

PyMongo also does not support parallel operations within a single transaction. :contentReference[oaicite:10]{index=10}

## Read Preference

Configure read preference when required:

```python
from pymongo import MongoClient, ReadPreference

client = MongoClient(
    mongo_uri,
    read_preference=ReadPreference.PRIMARY,
)
```

Possible strategies include:

- primary
- primaryPreferred
- secondary
- secondaryPreferred
- nearest

Do not use secondary reads simply to reduce primary load without understanding replication lag and consistency requirements.

## Write Concern

Write concern controls acknowledgement requirements.

Example:

```python
from pymongo import MongoClient

client = MongoClient(
    mongo_uri,
    w="majority",
)
```

The correct write concern depends on:

- durability requirements
- latency requirements
- availability requirements
- replica-set topology
- business criticality

## Retryable Operations

PyMongo supports retryable reads and writes for supported operations and deployments.

Example:

```python
client = MongoClient(
    mongo_uri,
    retryReads=True,
    retryWrites=True,
)
```

Retry behavior does not eliminate the need for idempotency.

Consider:

```text
Client
  ↓
insert
  ↓
MongoDB processes write
  ↓
Network response lost
  ↓
Client retries
```

Business-level identifiers and unique indexes can make retries safer.

## Stable API

For supported MongoDB deployments, PyMongo can use MongoDB's Stable API:

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

Stable API can help applications remain compatible across supported MongoDB Server upgrades by restricting operations to a declared API version. MongoDB documents Stable API support for MongoDB Server 5.0 and later. :contentReference[oaicite:11]{index=11}

This is particularly useful for long-lived production services where database upgrades should be decoupled from application rewrites.

## TLS

PyMongo supports TLS through client options.

Example:

```python
client = MongoClient(
    mongo_uri,
    tls=True,
)
```

For certificate validation, configure the appropriate CA trust chain rather than disabling validation.

Avoid:

```python
client = MongoClient(
    mongo_uri,
    tls=True,
    tlsAllowInvalidCertificates=True,
)
```

Production security should use valid certificates and trusted certificate authorities.

## Authentication

Authentication can be supplied through the connection URI:

```text
mongodb://app_user:password@mongo.internal:27017/orders?authSource=admin
```

Or through the configured connection options.

The application identity should have only the permissions required by its workload.

Do not use administrative credentials for ordinary CRUD traffic.

## Error Handling

PyMongo exposes specific exception classes.

Common categories include:

- `DuplicateKeyError`
- `OperationFailure`
- `ServerSelectionTimeoutError`
- `ConnectionFailure`
- `WriteError`
- `BulkWriteError`
- `ConfigurationError`

Example:

```python
from pymongo.errors import (
    DuplicateKeyError,
    ServerSelectionTimeoutError,
)

try:
    orders.insert_one(document)
except DuplicateKeyError as exc:
    raise OrderAlreadyExists() from exc
except ServerSelectionTimeoutError as exc:
    raise DatabaseUnavailable() from exc
```

Catch broad `Exception` only at an appropriate application boundary where necessary for logging or final error conversion.

## Exception Mapping

A repository should not necessarily expose raw driver exceptions to the service layer.

Prefer:

```text
PyMongo
   ↓
Repository
   ↓
Application Exception
   ↓
API / Worker
```

For example:

```text
DuplicateKeyError
       ↓
EntityAlreadyExists
       ↓
HTTP 409
```

and:

```text
ServerSelectionTimeoutError
       ↓
DatabaseUnavailable
       ↓
HTTP 503
```

This keeps the rest of the application independent of driver-specific error semantics.

## Repository Pattern

A production repository can encapsulate persistence logic:

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

    def update_status(
        self,
        order_id: ObjectId,
        status: str,
    ):
        return self.collection.update_one(
            {"_id": order_id},
            {
                "$set": {
                    "status": status,
                }
            },
        )
```

The repository should focus on data access rather than business decisions.

## Service Layer

Business rules belong in a service:

```python
class OrderService:
    def __init__(self, repository):
        self.repository = repository

    def confirm(self, order_id):
        order = self.repository.get_by_id(order_id)

        if order is None:
            raise OrderNotFound()

        if order["status"] != "pending":
            raise InvalidOrderState()

        return self.repository.update_status(
            order_id,
            "confirmed",
        )
```

This separation is useful for:

- unit testing
- transaction orchestration
- authorization
- business invariants
- reuse across REST and gRPC endpoints

## FastAPI Integration

For a synchronous FastAPI endpoint:

```python
from fastapi import FastAPI

app = FastAPI()

client = MongoClient(mongo_uri)
orders = client["orders"]["orders"]


@app.get("/orders/{order_id}")
def get_order(order_id: str):
    return orders.find_one({
        "_id": ObjectId(order_id),
    })
```

This works mechanically, but a production architecture should separate:

```text
Route
 ↓
Validation
 ↓
Service
 ↓
Repository
 ↓
PyMongo
```

For highly concurrent asynchronous applications, use PyMongo's native async API rather than blocking the event loop with synchronous database calls.

## PyMongo Async

Current PyMongo provides `AsyncMongoClient` for native asyncio integration. MongoDB states that the PyMongo Async API is generally available and is the recommended replacement direction for Motor. :contentReference[oaicite:12]{index=12}

Example:

```python
from pymongo import AsyncMongoClient

client = AsyncMongoClient(
    mongo_uri,
    serverSelectionTimeoutMS=5000,
)

database = client["orders"]
orders = database["orders"]

document = await orders.find_one({
    "_id": order_id,
})
```

An asynchronous cursor is consumed with `async for`:

```python
cursor = orders.find({
    "status": "pending",
})

async for document in cursor:
    process(document)
```

## PyMongo Async and Event Loops

`AsyncMongoClient` should be associated with the event loop that uses it.

MongoDB documents that `AsyncMongoClient` is not thread-safe and should not be shared across threads or event loops. :contentReference[oaicite:13]{index=13}

For FastAPI:

```text
Application Event Loop
        ↓
AsyncMongoClient
        ↓
Async Connection Pool
        ↓
MongoDB
```

Create and close the client as part of the application lifecycle.

## Synchronous vs Async PyMongo

| Workload | Preferred Approach |
|---|---|
| Simple synchronous service | `MongoClient` |
| Traditional WSGI application | `MongoClient` |
| Serial backend workload | `MongoClient` |
| Highly concurrent async API | `AsyncMongoClient` |
| FastAPI with substantial async I/O | Evaluate `AsyncMongoClient` |
| Existing Motor application | Migrate toward PyMongo Async |
| CPU-heavy service | Evaluate whether DB async behavior is actually beneficial |

MongoDB's current guidance suggests synchronous PyMongo for simpler or serial workloads and PyMongo Async for highly concurrent workloads or applications already built around asynchronous frameworks such as FastAPI. :contentReference[oaicite:14]{index=14}

## Motor Migration

Motor is being deprecated on May 14, 2026, and MongoDB recommends migrating supported applications to the PyMongo Async API. :contentReference[oaicite:15]{index=15}

The conceptual migration is:

```python
# Motor
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient(uri)
```

to:

```python
# PyMongo Async
from pymongo import AsyncMongoClient

client = AsyncMongoClient(uri)
```

However, do not treat this as a pure import rename. Review:

- cursor APIs
- lifecycle management
- event-loop ownership
- exception handling
- type hints
- tests
- performance
- application shutdown

## Django Integration

Django's native ORM is relational-oriented.

A direct PyMongo integration should normally use a repository or data-access layer:

```text
Django / DRF
    ↓
Serializer
    ↓
Service
    ↓
Repository
    ↓
PyMongo
    ↓
MongoDB
```

Do not make MongoDB collections behave as if they were PostgreSQL tables simply to fit Django ORM expectations.

## Celery Integration

Celery workers are separate processes and should manage their own client lifecycle.

```text
Celery Worker
    ↓
MongoClient
    ↓
Connection Pool
    ↓
MongoDB
```

For high-throughput workers:

- reuse the client
- bound concurrency
- tune pool sizes
- configure timeouts
- avoid long transactions
- monitor MongoDB latency

## Change Streams

PyMongo supports change streams for event-driven applications.

Example:

```python
with orders.watch() as stream:
    for change in stream:
        process_change(change)
```

Typical architecture:

```text
MongoDB
   ↓
Change Stream
   ↓
Python Consumer
   ↓
Kafka / Celery / Service
```

Production consumers should handle:

- resume tokens
- reconnection
- transient failures
- duplicate processing
- idempotency
- backpressure
- graceful shutdown

## Change Stream Resilience

A consumer should not assume:

```text
Event received
    =
Event successfully processed
```

A safer model is:

```text
Receive Event
     ↓
Persist / Track Processing State
     ↓
Execute Idempotent Action
     ↓
Commit Application State
     ↓
Advance Processing Position
```

The exact design depends on the downstream system.

## Testing

### Unit Tests

Unit-test services independently of MongoDB:

```text
Service
  ↓
Mock Repository
```

Useful for:

- business rules
- validation
- state transitions
- error mapping

### Integration Tests

Test PyMongo behavior against a real MongoDB environment:

```text
Repository
   ↓
PyMongo
   ↓
MongoDB
```

Integration tests are important for:

- unique indexes
- aggregation
- transactions
- ObjectId
- query operators
- update semantics
- write concerns
- change streams

Mocking PyMongo cannot validate MongoDB server behavior.

## Test Database Isolation

Each test suite should use isolated data.

Possible strategies include:

- unique test database
- collection cleanup
- transactional cleanup where applicable
- disposable MongoDB instance
- containerized MongoDB
- CI-managed replica set

Do not run integration tests against production data.

## Performance Testing

Measure actual workloads rather than only Python function execution time.

Useful measurements:

```text
Application latency
      ↓
Repository latency
      ↓
PyMongo operation latency
      ↓
MongoDB execution time
```

Track:

- p50
- p95
- p99
- error rate
- throughput
- connection-pool waits
- retry counts
- transaction latency

## Monitoring

Application-level MongoDB metrics should include:

- query latency
- operation counts
- timeout counts
- connection errors
- pool waits
- retry counts
- transaction failures
- bulk-operation throughput

Database-level monitoring should complement these metrics.

A useful production architecture is:

```mermaid
flowchart LR
    APP[Python Application]
    DRIVER[PyMongo]
    DB[(MongoDB)]
    METRICS[Metrics]
    LOGS[Structured Logs]
    TRACE[Distributed Tracing]
    ALERT[Monitoring / Alerting]

    APP --> DRIVER
    DRIVER --> DB
    APP --> METRICS
    APP --> LOGS
    APP --> TRACE
    METRICS --> ALERT
    LOGS --> ALERT
```

## Logging

Never log complete connection strings containing credentials.

Bad:

```text
mongodb://user:password@mongo.internal:27017/orders
```

Bad:

```python
logger.info("MongoDB document: %s", document)
```

when documents contain sensitive information.

Prefer structured metadata:

```python
logger.info(
    "order_lookup",
    extra={
        "order_id": order_id,
        "duration_ms": duration_ms,
        "result": "found",
    },
)
```

## Security

Production PyMongo configuration should consider:

- authentication
- TLS
- certificate validation
- least-privilege MongoDB users
- secret management
- query validation
- tenant isolation
- safe logging
- bounded queries
- controlled administrative access

Do not expose arbitrary MongoDB filters or aggregation pipelines through public APIs.

## Production Configuration

A synchronous production-oriented configuration could look like:

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
    waitQueueTimeoutMS=5000,
    maxPoolSize=100,
    retryReads=True,
    retryWrites=True,
)

database = client[os.environ["MONGO_DATABASE"]]
```

These values should be benchmarked and adjusted according to:

- application concurrency
- deployment size
- database capacity
- latency objectives
- workload characteristics

Stable API configuration can reduce compatibility surprises during supported MongoDB Server upgrades. :contentReference[oaicite:16]{index=16}

## Docker

A containerized service can receive its MongoDB URI through deployment configuration:

```yaml
services:
  api:
    image: orders-api:latest
    environment:
      MONGO_URI: ${MONGO_URI}
      MONGO_DATABASE: orders
```

Do not put actual production credentials into:

- `Dockerfile`
- `docker-compose.yml`
- Git
- application source
- image layers

Use deployment-level secret injection.

## Kubernetes

A Kubernetes workload can reference a secret:

```yaml
env:
  - name: MONGO_URI
    valueFrom:
      secretKeyRef:
        name: orders-mongodb
        key: uri
```

The Secret itself must be protected with appropriate:

- RBAC
- encryption-at-rest controls
- namespace isolation
- access auditing
- external secret-management integration where required

## AWS

A typical Python service can use:

```text
AWS VPC
   ↓
Private Application Subnets
   ↓
Python Service
   ↓
MongoDB Atlas / Private MongoDB
```

Supporting AWS services can include:

- AWS Secrets Manager
- AWS KMS
- security groups
- CloudWatch
- private networking

IAM protects AWS resources; MongoDB authentication and authorization still protect MongoDB itself.

## Graceful Shutdown

Synchronous:

```python
client.close()
```

Asynchronous:

```python
await client.close()
```

Application frameworks should call the appropriate cleanup operation during shutdown.

This matters because database clients own network resources and connection pools.

## Common Mistakes

### Creating a Client Per Request

Bad:

```python
def handler():
    client = MongoClient(uri)
    return client.db.orders.find_one({})
```

Why it is problematic:

- repeated connection-management work
- unnecessary topology discovery
- increased resource usage
- poor connection reuse

Use a long-lived client.

### Creating a Client Per Query

Even worse:

```python
def get_order(order_id):
    client = MongoClient(uri)
    return client.db.orders.find_one({"_id": order_id})
```

Reuse the existing client.

### Sharing a Client Across Forked Processes

Create a new client in each child process instead. MongoDB explicitly warns that passing a `MongoClient` into a forked child can lead to deadlocks. :contentReference[oaicite:17]{index=17}

### Blocking FastAPI's Event Loop

Avoid synchronous PyMongo network calls inside heavily concurrent async request paths when they can block the event loop.

Evaluate `AsyncMongoClient` for genuinely asynchronous workloads.

### Using AsyncMongoClient Across Event Loops

`AsyncMongoClient` should not be shared across threads or event loops. :contentReference[oaicite:18]{index=18}

### Returning Raw BSON Documents

Raw MongoDB documents can contain:

- `ObjectId`
- dates
- binary data
- internal fields

Map them into explicit API schemas.

### Ignoring Pool Multiplication

Always calculate pool capacity across:

```text
Pods
×
Processes
×
maxPoolSize
```

rather than looking at `maxPoolSize` alone.

### No Timeouts

Without bounded timeouts, database degradation can propagate into:

- request queues
- worker exhaustion
- thread exhaustion
- cascading failures

### Overusing Transactions

If one document can represent the consistency boundary, a transaction may be unnecessary.

### Overusing ODM Abstractions

An abstraction that hides MongoDB query behavior can make performance problems harder to diagnose.

Understand the underlying PyMongo and MongoDB behavior.

## Production Pitfalls

### Driver Version Drift

Different services may run different PyMongo versions.

This can cause:

- inconsistent behavior
- different deprecation warnings
- incompatible configuration
- unexpected driver/server interactions

Manage driver versions centrally where practical.

### MongoDB Server Upgrade Without Driver Validation

Before upgrading MongoDB Server:

```text
Server Upgrade
    ↓
Driver Compatibility
    ↓
Stable API Compatibility
    ↓
Integration Tests
    ↓
Performance Tests
    ↓
Production Rollout
```

MongoDB recommends checking Python, PyMongo, and MongoDB Server compatibility before driver upgrades. :contentReference[oaicite:19]{index=19}

### Index Changes During Deployment

Large index creation can have operational impact.

Treat index creation as a database change with:

- review
- monitoring
- rollout planning
- capacity analysis

### Hidden Serialization Costs

A query may be fast on the MongoDB server but slow overall because the application:

- retrieves too many documents
- decodes large BSON documents
- serializes huge JSON responses

Measure the complete path.

### Excessive Retries

Retries can amplify load during an outage.

For example:

```text
MongoDB degraded
      ↓
Requests timeout
      ↓
Clients retry
      ↓
More load
      ↓
MongoDB becomes more degraded
```

Use bounded retries and exponential backoff where application-level retries are necessary.

## Troubleshooting Methodology

### Connection Failure

```text
Symptom
↓
Application cannot connect
↓
Possible causes
    - DNS
    - firewall
    - security group
    - TLS
    - authentication
    - MongoDB unavailable
    - pool exhaustion
↓
Isolation strategy
↓
Validate URI
↓
Test network path
↓
Run ping
↓
Check MongoDB health
↓
Inspect credentials
↓
Inspect certificates
↓
Inspect pool metrics
↓
Root cause
↓
Corrective action
↓
Prevention
```

### Slow Query

```text
Symptom
↓
High API latency
↓
Possible causes
    - missing index
    - poor query shape
    - large result set
    - deep skip()
    - slow aggregation
    - pool contention
↓
Isolation strategy
↓
Measure operation latency
↓
Run explain()
↓
Inspect nReturned
↓
Inspect totalDocsExamined
↓
Inspect totalKeysExamined
↓
Inspect winning plan
↓
Root cause
↓
Corrective action
↓
Prevention
    - query regression tests
    - index review
    - performance monitoring
```

### Pool Exhaustion

```text
Symptom
↓
Operations wait for connections
↓
Possible causes
    - maxPoolSize too small
    - slow queries
    - long transactions
    - excessive concurrency
    - leaked resources
↓
Isolation strategy
↓
Inspect pool waits
↓
Inspect query latency
↓
Inspect transaction duration
↓
Inspect process and pod count
↓
Root cause
↓
Corrective action
↓
Prevention
    - pool tuning
    - query optimization
    - concurrency control
    - timeouts
```

### Authentication Failure

```text
Symptom
↓
Authentication error
↓
Possible causes
    - invalid credentials
    - wrong authSource
    - expired secret
    - wrong authentication mechanism
    - certificate issue
↓
Isolation strategy
↓
Validate configuration source
↓
Validate secret
↓
Test controlled connection
↓
Inspect MongoDB logs
↓
Root cause
↓
Corrective action
↓
Prevention
    - secret rotation
    - configuration testing
    - monitoring
```

## Upgrade Strategy

Before upgrading PyMongo:

1. Check Python compatibility.
2. Check MongoDB Server compatibility.
3. Review breaking changes.
4. Review deprecations.
5. Run unit tests.
6. Run integration tests.
7. Run transaction tests.
8. Run aggregation and query tests.
9. Validate TLS and authentication.
10. Benchmark critical workloads.
11. Roll out progressively.

MongoDB recommends reviewing compatibility and breaking changes before driver upgrades and suggests Stable API usage to reduce future compatibility work. :contentReference[oaicite:20]{index=20}

## Interview Considerations

### What is PyMongo?

PyMongo is MongoDB's official Python driver. It provides Python APIs for connecting to MongoDB and executing database operations while exposing MongoDB's native document and database semantics. :contentReference[oaicite:21]{index=21}

### Why should `MongoClient` be reused?

Because it maintains connection pools and topology state. Reusing it avoids unnecessary connection establishment and allows concurrent operations to share pooled connections. :contentReference[oaicite:22]{index=22}

### Is `MongoClient` thread-safe?

Yes. PyMongo documents `MongoClient` as thread-safe and designed for use across threads. A new client should be created in forked child processes rather than inherited from the parent. :contentReference[oaicite:23]{index=23}

### What is the difference between `MongoClient`, `Database`, and `Collection`?

```text
MongoClient
    ↓
Database
    ↓
Collection
    ↓
Documents
```

`MongoClient` manages connectivity and topology, `Database` identifies a MongoDB database, and `Collection` represents a collection.

### Why should connection pools be sized carefully?

Because each application process can maintain its own pool. Increasing application replicas or worker processes multiplies the potential number of MongoDB connections.

### When should transactions be used?

When a business invariant requires multiple operations to be atomic. They should not replace good document modeling or be used automatically for every write.

### Why is cursor-based pagination preferred for large datasets?

Because large offset values can require MongoDB to traverse many earlier results. Cursor-based pagination can use an indexed boundary and provide more predictable behavior.

### What is the difference between PyMongo and an ODM?

PyMongo is the direct MongoDB driver. An ODM adds model-oriented abstractions over it. PyMongo exposes MongoDB semantics more directly, which can make query behavior and performance easier to reason about.

### Should FastAPI always use `AsyncMongoClient`?

No. MongoDB recommends evaluating the application's concurrency model. Synchronous PyMongo is suitable for simpler or serial workloads, while PyMongo Async is designed for highly concurrent asynchronous workloads and frameworks such as FastAPI. :contentReference[oaicite:24]{index=24}

### What should replace Motor?

MongoDB's current migration guidance recommends PyMongo Async and states that Motor is scheduled for deprecation on May 14, 2026. :contentReference[oaicite:25]{index=25}

### Why use Stable API?

Stable API can reduce the impact of MongoDB Server upgrades by allowing the application to declare the API version it relies upon and optionally reject unsupported or deprecated operations. :contentReference[oaicite:26]{index=26}

## Key Takeaways

- **`MongoClient` is the core PyMongo abstraction and should normally be long-lived and reused so its topology management and connection pools can serve concurrent operations efficiently.**
- **Production PyMongo configuration requires deliberate choices around pooling, timeouts, retries, authentication, TLS, read/write concerns, and Stable API compatibility.**
- **Use PyMongo's native MongoDB semantics directly: design queries and indexes around access patterns, use cursors and projections carefully, and avoid unnecessary transactions or abstraction layers.**
- **Choose synchronous `MongoClient` or `AsyncMongoClient` based on the application's concurrency model; PyMongo Async is the current MongoDB-supported direction for highly concurrent asyncio applications and Motor migration.**
- **Treat PyMongo as part of the application's infrastructure boundary: isolate it behind repositories/services, test against real MongoDB behavior, monitor driver and database performance, and manage upgrades deliberately.**