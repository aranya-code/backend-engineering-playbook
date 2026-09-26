# 11- FastAPI and MongoDB Questions

## Overview

FastAPI and MongoDB are a common combination for Python backend services that need high API throughput, flexible document models, asynchronous request handling, and independently scalable service boundaries.

The important engineering question is not simply how to connect FastAPI to MongoDB. A production implementation must address:

- Connection lifecycle and pooling
- Repository and service-layer boundaries
- BSON and `ObjectId` serialization
- Pydantic validation
- Query and index design
- Pagination
- Aggregation
- Transactions and sessions
- Error handling
- Timeouts and retries
- Async versus synchronous database access
- Testing
- Security
- Observability
- Deployment and graceful shutdown

A typical request flow is:

```text
Client
  │
  ▼
Nginx / Load Balancer
  │
  ▼
FastAPI Application
  │
  ├── Authentication
  ├── Validation
  ├── Dependency Injection
  │
  ▼
Service Layer
  │
  ▼
Repository Layer
  │
  ▼
MongoDB
  │
  ├── Query Planner
  ├── Indexes
  └── Storage Engine
```

FastAPI should own HTTP concerns, the service layer should own business rules, and the repository layer should own MongoDB-specific persistence logic. This separation becomes increasingly important as the application grows.

## FastAPI and MongoDB Architecture

A maintainable application generally separates responsibilities into layers.

| Layer | Responsibility |
|---|---|
| Router | HTTP endpoints, status codes, request/response handling |
| Dependency | Authentication, authorization, request-scoped dependencies |
| Schema | Pydantic validation and serialization |
| Service | Business rules and application workflows |
| Repository | MongoDB queries and persistence |
| Database | Connection, pooling, transactions, MongoDB configuration |

A practical structure is:

```text
app/
├── main.py
├── core/
│   ├── config.py
│   └── database.py
├── api/
│   └── routes/
│       └── users.py
├── schemas/
│   └── user.py
├── services/
│   └── user_service.py
├── repositories/
│   └── user_repository.py
└── models/
    └── identifiers.py
```

The router should not contain large MongoDB queries:

```python
@router.get("/users")
async def list_users():
    ...
```

Instead:

```text
HTTP Request
    ↓
Router
    ↓
Service
    ↓
Repository
    ↓
MongoDB
```

This makes the persistence layer replaceable, testable, and easier to optimize independently.

## MongoDB Connection Lifecycle

A MongoDB client should normally be created once per FastAPI process rather than once per request.

Creating a new `MongoClient` for every request is inefficient because MongoDB clients maintain connection pools and manage connections internally.

The preferred lifecycle is:

```text
FastAPI Process Starts
        │
        ▼
Create MongoDB Client
        │
        ▼
Application Serves Requests
        │
        ▼
Reuse Client / Connection Pool
        │
        ▼
Application Shutdown
        │
        ▼
Close MongoDB Client
```

A modern FastAPI application can manage this using the application lifespan.

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pymongo import MongoClient

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = MongoClient(
        settings.mongodb_uri,
        serverSelectionTimeoutMS=5_000,
        connectTimeoutMS=5_000,
        socketTimeoutMS=10_000,
        maxPoolSize=100,
        minPoolSize=10,
    )

    client.admin.command("ping")

    app.state.mongodb_client = client
    app.state.mongodb_database = client[settings.mongodb_database]

    yield

    client.close()


app = FastAPI(lifespan=lifespan)
```

The important principle is that the client is process-scoped.

### Why a Singleton-Like Client Matters

A MongoDB client manages:

- Connection pools
- Server discovery
- Topology information
- Connection health
- Monitoring
- Authentication state
- Retry behavior

Creating clients repeatedly increases connection overhead and can exhaust database connection limits.

### Multiple Uvicorn Workers

A common deployment is:

```bash
uvicorn app.main:app --workers 4
```

Each worker is a separate process. Therefore, each process normally creates its own MongoDB client and connection pool.

If:

```text
workers = 4
maxPoolSize = 100
```

the application may establish up to approximately:

```text
4 × 100 = 400
```

pooled connections, subject to actual demand and driver behavior.

Pool sizing must therefore be considered at the deployment level, not only inside the Python application.

## MongoDB Configuration

Configuration should not be hard-coded.

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_uri: str
    mongodb_database: str = "application"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_",
        extra="ignore",
    )


settings = Settings()
```

Example environment configuration:

```text
APP_MONGODB_URI=mongodb://app_user:password@mongo:27017/application?authSource=application
APP_MONGODB_DATABASE=application
```

Production secrets should come from a secret-management mechanism rather than committed `.env` files.

For AWS-based deployments, secrets may be stored in:

- AWS Secrets Manager
- AWS Systems Manager Parameter Store
- Kubernetes Secrets backed by an external secret manager

Never commit:

```text
MONGODB_URI=mongodb://username:password@host/database
```

to Git.

## Pydantic and MongoDB Documents

MongoDB uses BSON while FastAPI commonly uses Pydantic models for API validation.

A MongoDB document may contain:

```json
{
  "_id": "ObjectId(...)",
  "email": "user@example.com",
  "name": "Alice"
}
```

The `_id` value is normally a BSON `ObjectId`, not a JSON string.

A REST API should usually expose a string representation:

```json
{
  "id": "66f3c9f0e5d6a4b8c1234567",
  "email": "user@example.com",
  "name": "Alice"
}
```

This creates an important boundary:

```text
MongoDB BSON
    │
    │ ObjectId
    ▼
Repository
    │
    ▼
Service
    │
    ▼
Pydantic Response Model
    │
    │ string ID
    ▼
JSON Response
```

Do not leak BSON-specific implementation details into every API consumer.

## ObjectId Handling

A reusable validation type can keep ObjectId conversion out of route handlers.

```python
from typing import Annotated

from bson import ObjectId
from pydantic import BeforeValidator


def validate_object_id(value: object) -> ObjectId:
    if isinstance(value, ObjectId):
        return value

    if isinstance(value, str) and ObjectId.is_valid(value):
        return ObjectId(value)

    raise ValueError("Invalid ObjectId")


PyObjectId = Annotated[ObjectId, BeforeValidator(validate_object_id)]
```

A response model can expose the identifier as a string instead of returning a raw `ObjectId`.

The exact serialization strategy should be consistent across the application. Mixing raw BSON values and strings makes API contracts harder to reason about.

## Request and Response Schemas

Do not automatically expose database documents as API responses.

Prefer explicit schemas:

```python
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    name: str


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    name: str
```

This provides a boundary between:

```text
Database Schema
       ≠
API Contract
```

That separation is valuable because database schema evolution and public API evolution often happen at different rates.

## Repository Pattern

A repository encapsulates persistence operations.

```python
from bson import ObjectId
from pymongo.collection import Collection


class UserRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def get_by_id(self, user_id: ObjectId):
        return self.collection.find_one({"_id": user_id})

    def get_by_email(self, email: str):
        return self.collection.find_one({"email": email})

    def create(self, document: dict):
        result = self.collection.insert_one(document)
        return self.collection.find_one({"_id": result.inserted_id})
```

The service layer can then focus on business logic:

```python
class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def create_user(self, email: str, name: str):
        existing = self.repository.get_by_email(email)

        if existing:
            raise ValueError("User already exists")

        return self.repository.create(
            {
                "email": email,
                "name": name,
            }
        )
```

This separation prevents route handlers from becoming large persistence-oriented functions.

## Dependency Injection

FastAPI dependencies can provide repositories and services.

Conceptually:

```text
Request
  │
  ▼
FastAPI Dependency
  │
  ├── Database
  ├── Repository
  └── Service
        │
        ▼
     Handler
```

Example:

```python
from fastapi import Depends, Request


def get_user_repository(request: Request) -> UserRepository:
    collection = request.app.state.mongodb_database["users"]
    return UserRepository(collection)
```

The route remains focused on HTTP behavior:

```python
@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    repository: UserRepository = Depends(get_user_repository),
):
    ...
```

## CRUD Operations

### Insert One

```python
document = {
    "email": "user@example.com",
    "name": "Alice",
}

result = collection.insert_one(document)

user_id = result.inserted_id
```

MongoDB generates `_id` automatically if it is omitted.

### Insert Many

```python
result = collection.insert_many(
    [
        {"email": "a@example.com", "name": "Alice"},
        {"email": "b@example.com", "name": "Bob"},
    ]
)
```

For large batches, batch size and write concern should be considered carefully.

### Find One

```python
user = collection.find_one(
    {"email": "user@example.com"},
    {"_id": 1, "email": 1, "name": 1},
)
```

Projection reduces unnecessary data transfer and document decoding.

### Find Many

```python
cursor = collection.find(
    {"status": "active"},
    {"_id": 1, "name": 1},
)
```

A cursor is lazy. MongoDB does not necessarily return the entire result set immediately.

### Update One

```python
result = collection.update_one(
    {"_id": user_id},
    {
        "$set": {
            "name": "Updated Name",
        }
    },
)
```

Prefer update operators when changing selected fields.

### Replace One

```python
collection.replace_one(
    {"_id": user_id},
    {
        "email": "user@example.com",
        "name": "Alice",
        "status": "active",
    },
)
```

Replacement removes fields that are not present in the replacement document.

This makes `replace_one()` fundamentally different from `$set`.

### Delete One

```python
collection.delete_one({"_id": user_id})
```

Deletion should generally be protected by authorization and business rules.

### Upsert

```python
collection.update_one(
    {"external_id": external_id},
    {
        "$set": {
            "name": name,
            "updated_at": datetime.now(timezone.utc),
        }
    },
    upsert=True,
)
```

Upserts are useful for synchronization workflows and idempotent write patterns.

## Bulk Writes

Bulk operations reduce network round trips.

```python
from pymongo import UpdateOne

operations = [
    UpdateOne(
        {"external_id": item.external_id},
        {
            "$set": {
                "name": item.name,
                "updated_at": datetime.now(timezone.utc),
            }
        },
        upsert=True,
    )
    for item in items
]

result = collection.bulk_write(
    operations,
    ordered=False,
)
```

`ordered=False` allows independent operations to proceed without requiring earlier operations to complete successfully first.

Bulk writes are useful for:

- ETL jobs
- Synchronization
- Batch imports
- Event consumers
- Data migrations

They do not automatically make the entire batch transactional.

## Query Filters

MongoDB query filters are documents.

```python
{"status": "active"}
```

Comparison operators:

```python
{
    "age": {
        "$gte": 18,
        "$lt": 65,
    }
}
```

Logical operators:

```python
{
    "$or": [
        {"status": "active"},
        {"status": "pending"},
    ]
}
```

Multiple fields normally represent an implicit logical AND:

```python
{
    "status": "active",
    "country": "IN",
}
```

## Array Queries

For an array field:

```json
{
  "tags": ["python", "mongodb", "fastapi"]
}
```

A query can match a member:

```python
{"tags": "python"}
```

For multiple required array elements:

```python
{
    "tags": {
        "$all": ["python", "mongodb"]
    }
}
```

For array size:

```python
{
    "tags": {
        "$size": 3
    }
}
```

Array queries must be designed together with multikey indexes and expected cardinality.

## Embedded Document Queries

Given:

```json
{
  "profile": {
    "country": "IN",
    "city": "Kolkata"
  }
}
```

Query using dot notation:

```python
{
    "profile.country": "IN"
}
```

Nested objects should be modeled around actual access patterns rather than arbitrary object hierarchy.

## Projection

Projection controls which fields MongoDB returns.

```python
collection.find(
    {"status": "active"},
    {
        "_id": 1,
        "name": 1,
        "email": 1,
    },
)
```

Projection is particularly useful when:

- Documents are large
- APIs need only a subset of fields
- Sensitive fields must not be returned
- Network bandwidth matters
- Query results feed downstream processing

Projection does not replace proper authorization.

## Sorting

```python
collection.find(
    {"status": "active"}
).sort(
    [
        ("created_at", -1),
        ("_id", -1),
    ]
)
```

For large result sets, sorting should normally be supported by an appropriate index rather than forcing MongoDB to perform an expensive in-memory sort.

## Pagination

### Offset Pagination

A simple implementation is:

```python
cursor = (
    collection.find({"status": "active"})
    .sort("created_at", -1)
    .skip(offset)
    .limit(page_size)
)
```

This is easy to implement but becomes increasingly expensive for deep pages because MongoDB must traverse skipped results.

### Cursor-Based Pagination

A better approach for large collections is keyset-style pagination.

For a descending timestamp plus `_id` ordering:

```python
query = {
    "status": "active",
    "$or": [
        {"created_at": {"$lt": last_created_at}},
        {
            "created_at": last_created_at,
            "_id": {"$lt": last_id},
        },
    ],
}

cursor = (
    collection.find(query)
    .sort(
        [
            ("created_at", -1),
            ("_id", -1),
        ]
    )
    .limit(page_size)
)
```

The supporting index should match the access pattern.

```python
collection.create_index(
    [
        ("status", 1),
        ("created_at", -1),
        ("_id", -1),
    ]
)
```

Cursor pagination is generally preferable for high-volume APIs.

## FastAPI Pagination Design

A production API should define pagination semantics explicitly.

Example response:

```json
{
  "items": [
    {
      "id": "66f3c9f0e5d6a4b8c1234567",
      "name": "Alice"
    }
  ],
  "next_cursor": "eyJjcmVhdGVkX2F0Ijoi..."
}
```

The cursor should be treated as an opaque API value.

Avoid exposing raw MongoDB implementation details such as:

```text
?last_id=ObjectId(...)
```

unless that contract is intentionally designed.

## MongoDB Indexes for FastAPI APIs

Indexes should be derived from actual query patterns.

Suppose the endpoint is:

```text
GET /users?status=active
```

and sorts by:

```text
created_at DESC
```

A useful index could be:

```python
collection.create_index(
    [
        ("status", 1),
        ("created_at", -1),
        ("_id", -1),
    ],
    name="status_created_id",
)
```

The correct index depends on:

- Equality predicates
- Sort order
- Range predicates
- Selectivity
- Cardinality
- Result size
- Query frequency

Do not create an index simply because a field exists.

## Explain Plans

Slow FastAPI endpoints often originate from inefficient MongoDB queries.

Inspect the query plan:

```python
plan = collection.find(
    {"status": "active"}
).sort(
    "created_at",
    -1,
).explain("executionStats")
```

Important fields include:

| Metric | Meaning |
|---|---|
| `nReturned` | Number of documents returned |
| `totalKeysExamined` | Number of index keys examined |
| `totalDocsExamined` | Number of documents examined |
| `executionTimeMillis` | Query execution time |
| `winningPlan` | Selected execution plan |

A common healthy pattern is:

```text
IXSCAN
  ↓
FETCH
  ↓
LIMIT
```

A suspicious pattern for a frequently executed query is:

```text
COLLSCAN
  ↓
SORT
```

A query examining 500,000 documents to return 20 is a strong optimization candidate.

## Query Planner and API Latency

FastAPI may report:

```text
GET /users 200 25ms
```

But the application latency can include:

```text
HTTP
 │
 ├── Authentication
 ├── Validation
 ├── Python processing
 ├── Connection pool wait
 ├── MongoDB query
 ├── BSON decoding
 └── Response serialization
```

Therefore, MongoDB query latency should not be inferred solely from HTTP latency.

Use distributed tracing and database metrics where possible.

## Aggregation Pipelines

Aggregation is useful when the API needs server-side transformation, grouping, joins, or analytics.

Example:

```python
pipeline = [
    {
        "$match": {
            "status": "completed",
        }
    },
    {
        "$group": {
            "_id": "$customer_id",
            "total_orders": {"$sum": 1},
            "total_amount": {"$sum": "$amount"},
        }
    },
    {
        "$sort": {
            "total_amount": -1,
        }
    },
    {
        "$limit": 20,
    },
]

results = collection.aggregate(pipeline)
```

### Pipeline Ordering

Prefer early filtering:

```text
$match
  ↓
$project / $set
  ↓
$group
  ↓
$sort
  ↓
$limit
```

An early `$match` can reduce:

- Documents entering later stages
- CPU usage
- Memory usage
- Network-independent processing cost
- Execution time

Avoid unnecessarily materializing large intermediate datasets.

## `$lookup`

`$lookup` can perform join-like operations.

```python
pipeline = [
    {
        "$lookup": {
            "from": "customers",
            "localField": "customer_id",
            "foreignField": "_id",
            "as": "customer",
        }
    },
]
```

`$lookup` is useful, but frequent cross-collection joins may indicate that the data model should be reconsidered.

Do not automatically recreate relational normalization patterns in MongoDB.

## Aggregation API Design

Avoid allowing arbitrary client-provided aggregation pipelines.

An endpoint such as:

```text
POST /reports
```

should normally translate validated API parameters into a controlled server-side pipeline.

Avoid:

```python
pipeline = request.json()["pipeline"]
collection.aggregate(pipeline)
```

This can create security, performance, authorization, and resource-consumption problems.

Prefer:

```python
pipeline = build_sales_report_pipeline(
    customer_id=customer_id,
    start_date=start_date,
    end_date=end_date,
)
```

## Transactions

MongoDB guarantees atomicity for individual document operations.

Transactions are useful when multiple documents or collections must change atomically.

A transaction flow is:

```text
Start Session
    ↓
Start Transaction
    ↓
Read / Write
    ↓
Commit
    │
    ├── Success → Transaction Durable
    │
    └── Failure → Abort / Retry
```

Python example:

```python
from pymongo import MongoClient


def transfer(
    client: MongoClient,
    source_id,
    destination_id,
    amount: int,
):
    database = client["banking"]
    accounts = database["accounts"]

    with client.start_session() as session:
        with session.start_transaction():
            source = accounts.update_one(
                {
                    "_id": source_id,
                    "balance": {"$gte": amount},
                },
                {
                    "$inc": {"balance": -amount},
                },
                session=session,
            )

            if source.modified_count != 1:
                raise ValueError("Insufficient balance")

            destination = accounts.update_one(
                {"_id": destination_id},
                {
                    "$inc": {"balance": amount},
                },
                session=session,
            )

            if destination.modified_count != 1:
                raise ValueError("Destination account not found")
```

Transactions should not be used automatically for every operation.

They introduce additional coordination and can reduce throughput compared with independent atomic writes.

## Transaction Design

Use transactions when:

- Multiple documents must change atomically
- Partial completion would violate a business invariant
- Compensating operations are insufficient
- Cross-document consistency is required

Avoid transactions when:

- A single-document atomic update is sufficient
- The operation can be redesigned around one aggregate document
- Long-running external calls are included
- The transaction is held while calling external APIs
- Large batch processing is performed unnecessarily inside a transaction

Never hold a database transaction while waiting for:

```text
HTTP API
Kafka
SMTP
External payment service
Long-running computation
```

A transaction should be as short as practical.

## Read Concern, Write Concern, and Read Preference

These settings affect production behavior.

| Setting | Main Concern |
|---|---|
| Read concern | Consistency guarantees for reads |
| Write concern | Acknowledgment and durability of writes |
| Read preference | Which replica-set members serve reads |

Example:

```python
from pymongo import ReadPreference
from pymongo.write_concern import WriteConcern

collection = database.get_collection(
    "orders",
    write_concern=WriteConcern(w="majority"),
    read_preference=ReadPreference.PRIMARY,
)
```

### Majority Write Concern

A majority write waits for the required replica-set acknowledgment according to the configured topology.

It generally provides stronger durability semantics than an unacknowledged write.

However, stronger guarantees can increase latency.

Production settings should be selected according to business requirements rather than copied from examples.

## Replica Sets and FastAPI

A production MongoDB deployment commonly uses a replica set.

```text
                 ┌───────────────┐
                 │   FastAPI     │
                 └───────┬───────┘
                         │
                         ▼
                  MongoDB Driver
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
       Primary        Secondary      Secondary
          │              ▲              ▲
          └──────────────┴──────────────┘
                  Replication
```

The MongoDB driver discovers topology and can react to primary changes.

Application code should generally use a replica-set-aware connection string rather than manually selecting a primary.

## Read Preferences

Common read preferences include:

| Read Preference | Behavior |
|---|---|
| `primary` | Reads from primary |
| `primaryPreferred` | Primary when available |
| `secondary` | Reads from secondary |
| `secondaryPreferred` | Secondary when available |
| `nearest` | Lowest network latency member |

Using secondary reads can improve read scalability, but introduces potential replication lag.

Do not send consistency-sensitive reads to secondaries simply to increase throughput.

Examples of operations that often require primary-oriented semantics include:

- Immediately reading data after a critical write
- Strongly consistent business decisions
- Transactional workflows
- Authorization decisions depending on freshly written state

## Sharding

FastAPI itself does not need special business logic for sharding.

The MongoDB driver connects to `mongos` or the appropriate topology and MongoDB routes operations.

```text
FastAPI
   │
   ▼
MongoDB Driver
   │
   ▼
mongos
   │
   ├── Shard A
   ├── Shard B
   └── Shard C
```

The difficult engineering decision is usually the shard key.

A poor shard key can produce:

- Hot shards
- Uneven distribution
- Scatter-gather queries
- Poor write scalability
- Difficult resharding

Shard-key selection should consider:

- Cardinality
- Frequency
- Query patterns
- Write distribution
- Monotonicity
- Tenant distribution
- Expected growth

Do not select a shard key solely because it is the most frequently queried field.

## Change Streams

Change streams allow applications to react to MongoDB changes.

Typical architecture:

```text
MongoDB
   │
   │ Change Stream
   ▼
FastAPI / Worker
   │
   ├── Validate event
   ├── Process event
   ├── Persist state
   └── Publish downstream event
```

Change streams are useful for:

- Search indexing
- Cache invalidation
- Audit pipelines
- Event-driven processing
- Synchronization
- Notifications

Consumers must account for:

- Resume tokens
- Duplicate processing
- Consumer restarts
- Backpressure
- Network failures
- Idempotency

A change stream consumer should assume an event may need to be processed again.

## Async Considerations

FastAPI supports asynchronous request handlers, but using:

```python
async def endpoint():
    collection.find_one(...)
```

does not make a synchronous MongoDB driver asynchronous.

A blocking MongoDB operation inside an async event loop can reduce concurrency.

The distinction is:

```text
async FastAPI endpoint
        │
        ▼
Async MongoDB Driver
        │
        ▼
Non-blocking database I/O
```

versus:

```text
async FastAPI endpoint
        │
        ▼
Synchronous MongoDB Driver
        │
        ▼
Blocking database I/O
```

If using synchronous PyMongo, use a synchronous route where appropriate or deliberately isolate blocking operations from the event loop.

If using an async MongoDB driver, verify its current compatibility, maintenance status, and supported MongoDB features before adopting it.

Do not select an async driver merely because FastAPI is an async framework.

## Sync Versus Async Decision

| Requirement | Consideration |
|---|---|
| Existing synchronous PyMongo application | Keep it simple unless blocking I/O is a problem |
| High-concurrency async service | Evaluate a supported async driver |
| CPU-heavy work | Async does not solve CPU bottlenecks |
| Background processing | Celery or another worker system may be more appropriate |
| Simple CRUD service | Avoid unnecessary architectural complexity |

The main goal is to avoid blocking the event loop while maintaining a supported and operationally sound database integration.

## Error Handling

MongoDB errors should not leak directly to clients.

For example:

```python
from pymongo.errors import DuplicateKeyError
from fastapi import HTTPException


try:
    repository.create_user(user)
except DuplicateKeyError:
    raise HTTPException(
        status_code=409,
        detail="User already exists",
    )
```

Typical mappings include:

| MongoDB/Application Condition | HTTP Response |
|---|---|
| Invalid identifier | `400 Bad Request` |
| Resource not found | `404 Not Found` |
| Duplicate unique key | `409 Conflict` |
| Validation failure | `422 Unprocessable Entity` |
| Transient infrastructure failure | `503 Service Unavailable` |
| Unexpected database error | `500 Internal Server Error` |

Do not expose:

```text
MongoServerError: ...
connection string
database topology
internal collection names
```

to clients.

Log internal diagnostic information securely instead.

## Timeouts

Production MongoDB connections should not rely on unlimited waits.

Relevant timeout categories include:

- Server selection timeout
- Connection timeout
- Socket timeout
- Application-level request timeout

Example:

```python
client = MongoClient(
    uri,
    serverSelectionTimeoutMS=5_000,
    connectTimeoutMS=5_000,
    socketTimeoutMS=10_000,
)
```

Timeouts should be consistent with the service's API-level latency budget.

If:

```text
API timeout = 5 seconds
```

and:

```text
MongoDB socket timeout = 30 seconds
```

the database operation may outlive the HTTP request and waste resources.

## Retry Behavior

Transient MongoDB failures can occur because of:

- Primary elections
- Network interruptions
- Temporary topology changes
- Connection failures

MongoDB drivers support retry mechanisms for supported operations.

Do not blindly implement application-level retries around every exception.

Retries can amplify load:

```text
Failure
  ↓
Retry
  ↓
More load
  ↓
More failures
  ↓
More retries
```

Use:

- Bounded retries
- Exponential backoff
- Jitter
- Idempotent operations
- Clear retry budgets

Be especially careful with non-idempotent business operations.

## FastAPI Authentication and MongoDB Authorization

Authentication and database authorization solve different problems.

```text
Client
  │
  ▼
FastAPI Authentication
  │
  ▼
Application Authorization
  │
  ▼
Repository Query
  │
  ▼
MongoDB Authorization
```

A user being authenticated does not mean they are authorized to access every MongoDB document.

For multi-tenant systems, tenant isolation should be enforced at the application boundary.

Example:

```python
query = {
    "tenant_id": current_user.tenant_id,
    "_id": user_id,
}
```

Do not rely solely on the client sending:

```text
tenant_id
```

because the client can manipulate it.

## Multi-Tenant MongoDB Design

Common strategies include:

### Shared Collection

```json
{
  "_id": "...",
  "tenant_id": "tenant-123",
  "name": "Alice"
}
```

Advantages:

- Simple operations
- Efficient resource utilization
- Easier infrastructure management

Requires:

- Tenant-aware indexes
- Strict query isolation
- Strong authorization
- Careful data migration

### Database Per Tenant

```text
tenant_a
tenant_b
tenant_c
```

Advantages:

- Stronger isolation boundaries
- Easier tenant-specific operations in some environments

Disadvantages:

- Operational complexity
- More databases and indexes
- Connection/configuration complexity
- Scaling concerns at high tenant counts

### Collection Per Tenant

Usually becomes difficult to operate at large tenant counts because collection and index management grows rapidly.

The correct strategy depends on isolation requirements, tenant count, query patterns, operational constraints, and regulatory requirements.

## MongoDB Security

Application configuration should use a dedicated MongoDB user with the minimum required permissions.

Avoid using administrative credentials from FastAPI.

Prefer:

```text
FastAPI
   │
   │ least-privileged credentials
   ▼
Application Database
```

Security controls should include:

- Authentication
- Authorization
- TLS
- Network restrictions
- Secret management
- Encryption at rest
- Encryption in transit
- Auditing where required
- Credential rotation
- Least privilege

Never expose MongoDB directly to the public internet without appropriate network and security controls.

## API Input Validation

MongoDB operators must never be accepted blindly from untrusted input.

A dangerous design is:

```python
query = request.json()["filter"]
collection.find(query)
```

A client could potentially submit operators that the application never intended to expose.

Prefer typed request models:

```python
class UserFilter(BaseModel):
    status: str | None = None
    country: str | None = None
```

Then construct the MongoDB query explicitly:

```python
query = {}

if filters.status:
    query["status"] = filters.status

if filters.country:
    query["country"] = filters.country
```

This provides stronger control over the API's query surface.

## Schema Validation

MongoDB's flexible schema does not mean an application should have no schema discipline.

A collection can use JSON Schema validation:

```javascript
db.createCollection("users", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["email", "name"],
      properties: {
        email: {
          bsonType: "string"
        },
        name: {
          bsonType: "string"
        }
      }
    }
  }
})
```

Validation should complement, not replace, FastAPI/Pydantic validation.

The application layer provides:

- API-specific validation
- Better error messages
- Business rules

MongoDB validation provides:

- Persistence-level protection
- Protection against non-API writers
- Consistency across ingestion paths

## Django and MongoDB

Django is primarily designed around relational database integrations and its native ORM.

MongoDB should not be treated as a drop-in replacement for PostgreSQL.

Common approaches include:

- Direct PyMongo repositories
- MongoEngine where appropriate
- Dedicated persistence services
- Separate MongoDB-backed microservices

A production Django application may use:

```text
Django
  │
  ├── Django ORM → PostgreSQL
  │
  └── Repository → MongoDB
```

This is often cleaner than forcing MongoDB into relational ORM abstractions.

Use MongoDB-specific query and transaction semantics explicitly when MongoDB is the persistence system.

## Testing FastAPI and MongoDB

Testing should separate:

- Unit tests
- Repository integration tests
- API integration tests
- End-to-end tests

### Unit Testing Services

Mock the repository boundary:

```python
def test_create_user():
    repository = FakeUserRepository()
    service = UserService(repository)

    user = service.create_user(
        email="user@example.com",
        name="Alice",
    )

    assert user["email"] == "user@example.com"
```

### Repository Integration Testing

Repository tests should execute against a real MongoDB-compatible environment when possible.

This catches problems involving:

- BSON behavior
- Indexes
- Query semantics
- Aggregation
- Transactions
- Unique constraints
- MongoDB-specific behavior

Mocks alone cannot reliably validate MongoDB queries.

## Test Database Isolation

Avoid sharing production-like test data between tests.

Options include:

- Dedicated test database
- Unique collection namespace
- Per-test cleanup
- Transaction-based isolation where appropriate
- Ephemeral MongoDB environments

Tests should also verify indexes that production code depends upon.

## MongoDB Compass

MongoDB Compass is useful for development and diagnostics.

Typical workflow:

```text
Connect
  ↓
Select Database
  ↓
Select Collection
  ↓
Inspect Documents
  ↓
Test Query
  ↓
Inspect Indexes
  ↓
Build Aggregation
  ↓
Validate Results
```

Useful Compass features include:

- Document browsing
- Query testing
- Aggregation pipeline builder
- Index inspection
- Schema analysis
- Import/export
- Collection statistics

Compass should not become the production operational control plane.

Production changes should normally be performed through controlled migrations, deployment procedures, or approved operational tooling.

## mongosh

`mongosh` is useful for interactive MongoDB operations.

Connect:

```bash
mongosh "mongodb://localhost:27017/application"
```

Inspect databases:

```javascript
show dbs
```

Select a database:

```javascript
use application
```

List collections:

```javascript
show collections
```

Query documents:

```javascript
db.users.find({status: "active"}).limit(10)
```

Explain a query:

```javascript
db.users.find({status: "active"}).explain("executionStats")
```

Inspect indexes:

```javascript
db.users.getIndexes()
```

Collection statistics:

```javascript
db.users.stats()
```

Database statistics:

```javascript
db.stats()
```

Production access should be authenticated, authorized, audited where required, and preferably performed through controlled operational procedures.

## Import and Export

MongoDB provides dedicated tools such as:

```bash
mongoimport
mongoexport
mongodump
mongorestore
```

For JSON imports:

```bash
mongoimport \
  --uri "$MONGODB_URI" \
  --collection users \
  --file users.json \
  --jsonArray
```

For logical backups:

```bash
mongodump \
  --uri "$MONGODB_URI" \
  --out ./backup
```

Restore:

```bash
mongorestore \
  --uri "$MONGODB_URI" \
  ./backup
```

Import/export tools and backup tools solve different problems. `mongoexport` is designed for logical data interchange, while `mongodump` is intended for MongoDB logical backup and restore workflows.

## Performance Engineering

Performance should be measured rather than assumed.

A practical workflow is:

```text
Observe
  ↓
Measure
  ↓
Identify bottleneck
  ↓
Inspect explain plan / metrics
  ↓
Change one variable
  ↓
Benchmark
  ↓
Compare
  ↓
Deploy carefully
  ↓
Monitor regression
```

### Example

Suppose an endpoint returns 20 users but MongoDB reports:

```text
nReturned = 20
totalDocsExamined = 850000
executionTimeMillis = 900
```

The query is likely scanning far more documents than necessary.

After introducing an appropriate compound index, the goal might be:

```text
nReturned = 20
totalDocsExamined = 20
executionTimeMillis = 5
```

The exact values depend on workload and environment. The important point is to compare measurable before-and-after behavior.

## Connection Pooling

The MongoDB driver maintains connection pools.

Connection pool behavior affects:

- Throughput
- Latency
- Resource consumption
- Database connection limits

A common mistake is assuming:

```text
maxPoolSize = higher = faster
```

Too many connections can cause:

- Database resource contention
- Context switching
- Memory pressure
- Connection exhaustion
- Increased latency

Pool sizing should consider:

```text
Application workers
×
Pool size
×
Number of application instances
```

alongside the MongoDB deployment's connection capacity.

## Large Documents

Large MongoDB documents can create:

- Higher network transfer cost
- More BSON decoding
- Larger working sets
- More expensive updates
- Increased replication traffic

Avoid storing unbounded arrays such as:

```json
{
  "user_id": "...",
  "events": [
    "... potentially millions of events ..."
  ]
}
```

Instead, consider separate documents:

```text
users
events
```

or bucketed data structures depending on the workload.

Document growth should be considered during schema design, not after the collection becomes large.

## Hot Documents

A hot document is a document that receives a disproportionate amount of concurrent reads or writes.

Examples include:

```text
global counters
single shared configuration document
highly active inventory record
popular content document
```

Potential solutions include:

- Sharding the workload
- Bucketed counters
- Distributed aggregation
- Application caching
- Redis for appropriate ephemeral data
- Data-model redesign

A single-document atomic update is powerful, but it does not mean one document can sustain unlimited concurrent workload.

## Redis and MongoDB

Redis and MongoDB solve different problems.

| Technology | Typical Role |
|---|---|
| MongoDB | Durable document persistence |
| Redis | Cache, ephemeral state, counters, coordination |
| PostgreSQL | Relational transactional persistence |
| Kafka | Durable event streaming |

A common backend architecture is:

```text
FastAPI
  │
  ├── Redis ── Cache
  │
  └── MongoDB ── Persistent documents
```

Do not introduce Redis solely to hide a poorly indexed MongoDB query. Fix the underlying database access pattern first.

## Celery and MongoDB

Celery can process MongoDB-backed background jobs.

For example:

```text
FastAPI
  │
  ├── Validate request
  ├── Write MongoDB job
  └── Enqueue task
          │
          ▼
       Celery
          │
          ▼
       Worker
          │
          ▼
       MongoDB
```

Background tasks should be idempotent.

If a worker receives the same job twice, processing it twice should not corrupt application state.

Use unique identifiers and state transitions to enforce idempotency.

## Kafka and MongoDB

MongoDB can be part of an event-driven architecture:

```text
FastAPI
  │
  ▼
MongoDB
  │
  ▼
Change Stream / Event Producer
  │
  ▼
Kafka
  │
  ├── Search Service
  ├── Notification Service
  └── Analytics Service
```

The system should define:

- Event ownership
- Ordering requirements
- Delivery semantics
- Retry behavior
- Duplicate handling
- Schema evolution

Do not assume database writes and Kafka publishing are automatically atomic.

For stronger guarantees, consider patterns such as an outbox architecture where appropriate.

## Observability

A production FastAPI + MongoDB service should expose enough information to identify where latency originates.

Useful metrics include:

### Application Metrics

- Request count
- Error rate
- Request latency
- In-flight requests
- Dependency latency

### MongoDB Metrics

- Query latency
- Operation counts
- Connections
- Replication lag
- Storage utilization
- Working set
- Cache behavior
- Lock/contention indicators where applicable

### Logging

Log structured fields such as:

```json
{
  "request_id": "abc123",
  "route": "/users",
  "operation": "find_user",
  "duration_ms": 12,
  "status_code": 200
}
```

Avoid logging:

- Passwords
- Connection strings
- Authentication tokens
- Sensitive documents
- Unnecessary personal information

## Distributed Tracing

For microservices, trace:

```text
Client
  ↓
Nginx
  ↓
FastAPI
  ↓
Service
  ↓
Repository
  ↓
MongoDB
```

A trace can reveal whether latency comes from:

```text
HTTP
MongoDB
Redis
Kafka
External API
Python processing
```

This is much more useful than measuring only total endpoint latency.

## Production Deployment

A production deployment may look like:

```text
Internet
   │
   ▼
Load Balancer / Nginx
   │
   ▼
FastAPI Instances
   │
   ├───────────────┐
   ▼               ▼
Redis           MongoDB
                  │
             Replica Set
             ├── Primary
             ├── Secondary
             └── Secondary
```

FastAPI instances should be stateless where possible.

MongoDB should provide persistence and high availability rather than the application storing process-local authoritative state.

## Docker Considerations

A local Docker Compose environment may contain:

```yaml
services:
  api:
    build: .
    environment:
      APP_MONGODB_URI: mongodb://mongo:27017/application
      APP_MONGODB_DATABASE: application
    depends_on:
      - mongo

  mongo:
    image: mongo:latest
```

For production, do not blindly use the same configuration.

Production requires consideration of:

- Persistent storage
- Authentication
- TLS
- Replica sets
- Backups
- Resource limits
- Monitoring
- Secrets
- Network policies
- Upgrade strategy

Managed MongoDB services can reduce operational burden where appropriate.

## Graceful Shutdown

FastAPI should close database resources during application shutdown.

The lifespan pattern ensures:

```text
Startup
  ↓
MongoDB Client Created
  ↓
Application Running
  ↓
Shutdown Signal
  ↓
Stop Accepting Work
  ↓
Close MongoDB Client
```

Graceful shutdown becomes especially important in Kubernetes rolling deployments.

## Kubernetes Considerations

In Kubernetes:

```text
Deployment
  │
  ├── Pod 1 → MongoDB Client Pool
  ├── Pod 2 → MongoDB Client Pool
  └── Pod 3 → MongoDB Client Pool
```

Remember that each pod has its own connection pool.

If:

```text
3 pods × 100 pool size = 300 potential connections
```

and there are multiple environments or deployments, the total can grow quickly.

Use:

- Readiness probes
- Liveness probes
- Graceful termination
- Resource limits
- Horizontal Pod Autoscaling where appropriate
- Secret management
- Network policies
- Centralized logging

MongoDB itself should generally not be treated like a disposable stateless Kubernetes pod unless the operational architecture explicitly supports it.

## Backup and Recovery

A production MongoDB system needs a recovery strategy independent of FastAPI.

Important concepts include:

- Logical backups
- Managed backups
- Point-in-time recovery
- Restore testing
- RPO
- RTO
- Backup retention
- Cross-region recovery where required

### RPO

Recovery Point Objective answers:

> How much data can the organization afford to lose?

### RTO

Recovery Time Objective answers:

> How quickly must the service be restored?

A backup that exists but has never been restored is not a proven recovery strategy.

Regular recovery testing should validate:

```text
Backup
  ↓
Restore
  ↓
Validate indexes
  ↓
Validate collections
  ↓
Validate application compatibility
  ↓
Measure recovery duration
```

## Troubleshooting MongoDB From FastAPI

Use a structured methodology.

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

### Slow API Endpoint

**Symptom**

```text
GET /users takes 2 seconds
```

**Possible causes**

- Missing index
- Poor compound index
- Large result set
- Large documents
- Connection pool wait
- Slow aggregation
- Database contention

**Isolation strategy**

Separate:

```text
HTTP latency
MongoDB latency
Python processing
serialization
connection acquisition
```

**Diagnostic commands**

```javascript
db.users.find({
  status: "active"
}).explain("executionStats")
```

Inspect:

```text
nReturned
totalKeysExamined
totalDocsExamined
executionTimeMillis
winningPlan
```

**Corrective action**

Potentially:

- Add or modify index
- Reduce projection
- Change pagination
- Rewrite query
- Reduce aggregation workload

**Prevention**

- Query performance tests
- Index reviews
- Monitoring
- Slow-query analysis
- Performance regression testing

## Connection Failures

**Symptom**

```text
ServerSelectionTimeoutError
```

**Possible causes**

- Incorrect URI
- DNS failure
- Network restriction
- MongoDB unavailable
- TLS mismatch
- Authentication failure
- Replica-set topology issue

**Isolation**

Test from the same runtime environment:

```bash
mongosh "$MONGODB_URI"
```

Then inspect:

```text
DNS
TCP connectivity
TLS
authentication
MongoDB topology
```

Do not diagnose only from the developer laptop when the application runs inside Kubernetes or Docker.

## Duplicate Key Errors

**Symptom**

```text
DuplicateKeyError
```

**Possible causes**

- Unique index
- Concurrent insert
- Retry of an already successful operation
- Incorrect upsert design

**Isolation**

Inspect indexes:

```javascript
db.users.getIndexes()
```

Then determine which unique key was violated.

**Corrective action**

For an idempotent API, use a unique business identifier and handle the duplicate as a known conflict or idempotent success.

Do not remove a unique index simply because the application encountered a duplicate.

## Secondary Lag

**Symptom**

Reads from secondary members return stale data.

**Possible causes**

- High write throughput
- Slow secondary
- Resource saturation
- Network issues
- Large replication workload

**Isolation**

Inspect replica-set status and replication lag.

```javascript
rs.status()
```

**Corrective action**

Depending on the workload:

- Improve secondary capacity
- Reduce write amplification
- Review indexes
- Reconsider secondary read usage
- Scale the topology

**Prevention**

Monitor replication lag continuously when secondary reads matter.

## Transaction Failures

**Symptom**

Transactions abort unexpectedly.

**Possible causes**

- Transient topology errors
- Write conflicts
- Timeout
- Unsupported operation
- Long-running transaction
- Incorrect session handling

**Isolation**

Capture:

- Error code
- Transaction duration
- Operation sequence
- Read/write concerns
- Replica-set state

**Corrective action**

Use bounded retry handling where MongoDB identifies the operation as retryable and ensure the transaction is safe to retry.

## Common FastAPI + MongoDB Mistakes

### Creating a Client Per Request

Bad:

```python
@app.get("/users")
def users():
    client = MongoClient(uri)
    ...
```

Why it is problematic:

- Repeated connection setup
- Excessive connection creation
- Increased latency
- Resource exhaustion

Use an application-scoped client.

### Performing Blocking Database Work in Async Routes

Bad:

```python
@app.get("/users")
async def users():
    return collection.find_one(...)
```

If `collection` is synchronous, the database call blocks the event loop.

Use an appropriate synchronous architecture or a supported async driver.

### Returning Raw MongoDB Documents

Bad:

```python
return await collection.find_one(...)
```

Problems can include:

- `ObjectId` serialization
- Accidental sensitive-field exposure
- Database schema leaking into API contracts

Use explicit response models.

### Using `skip()` for Deep Pagination

Bad:

```python
.skip(500000)
```

This can become increasingly expensive.

Use cursor/keyset pagination for large datasets.

### Missing Indexes

Bad:

```python
collection.find({"tenant_id": tenant_id})
```

without understanding the query volume and indexing strategy.

Indexes should be designed from actual access patterns.

### Over-Indexing

Every index consumes resources and increases write maintenance.

More indexes do not automatically mean better performance.

### Blind Retries

Retrying every database error can amplify outages.

Retry only appropriate transient failures and keep retry budgets bounded.

### Long Transactions

Avoid:

```text
Start transaction
↓
Call external API
↓
Wait
↓
Process large dataset
↓
Commit
```

Transactions should remain short.

### Trusting Client-Supplied Tenant IDs

Never rely solely on:

```json
{
  "tenant_id": "tenant-a"
}
```

for authorization.

Derive authorization context from the authenticated identity and enforce it server-side.

## Interview Questions

### What is the recommended way to manage a MongoDB connection in FastAPI?

Create a MongoDB client at application startup, reuse it throughout the process, and close it during application shutdown. The client manages connection pooling and topology discovery.

### Should MongoDB connections be created per request?

Generally no. Creating a client per request defeats connection pooling and introduces unnecessary connection overhead.

### Does `async def` make PyMongo asynchronous?

No. A synchronous PyMongo call remains blocking even when called from an `async def` route.

### How should `ObjectId` be handled in FastAPI?

Treat `ObjectId` as a persistence-layer type and expose a stable serialized representation, typically a string, through explicit API schemas.

### Why use a repository layer?

It isolates MongoDB-specific persistence logic from HTTP and business logic, improving testability and maintainability.

### How should MongoDB pagination be implemented for large datasets?

Prefer cursor/keyset pagination based on a stable indexed sort key instead of large `skip()` offsets.

### When should MongoDB transactions be used?

When multiple document or collection changes must succeed atomically to preserve a business invariant.

### Why can a MongoDB query be slow even when an index exists?

The index may not match the query pattern, may have poor selectivity, may not support the sort, or the planner may choose another plan. Use `explain("executionStats")`.

### What does `totalDocsExamined` tell you?

It indicates how many documents MongoDB examined during execution. Comparing it with `nReturned` can reveal inefficient queries.

### How should duplicate user creation be handled?

Use a unique index on the business identifier and translate duplicate-key errors into an appropriate application response such as HTTP `409 Conflict`.

### Should FastAPI directly accept MongoDB query filters from clients?

Generally no. Build controlled MongoDB queries from validated API parameters to avoid exposing unintended operators and resource-intensive queries.

### How does MongoDB replication affect FastAPI reads?

Reading from secondaries can improve read scalability but may return stale data because of replication lag.

### How should MongoDB be tested in a FastAPI application?

Unit-test services using repository abstractions and use real MongoDB integration tests for queries, indexes, aggregation, transactions, and MongoDB-specific behavior.

### How do you optimize a slow FastAPI endpoint backed by MongoDB?

Measure the complete request path, isolate MongoDB latency, inspect `explain("executionStats")`, examine indexes and result size, optimize the query or schema, then benchmark before and after.

## Senior-Level Design Questions

### Design a High-Throughput FastAPI + MongoDB API

A production design could be:

```text
                    ┌───────────────┐
                    │ Load Balancer │
                    └───────┬───────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
           FastAPI       FastAPI       FastAPI
              │             │             │
              └─────────────┼─────────────┘
                            │
                    ┌───────▼───────┐
                    │     Redis     │
                    │    Cache      │
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │    MongoDB    │
                    │ Replica Set   │
                    └───────────────┘
```

Senior-level considerations:

- Stateless FastAPI instances
- Connection-pool sizing
- Query-driven indexes
- Cursor pagination
- Explicit API schemas
- MongoDB replica set
- Majority writes where required
- Caching only where beneficial
- Timeouts
- Bounded retries
- Observability
- Backup and recovery
- Security
- Capacity planning

### Design a Multi-Tenant SaaS API

Potential model:

```text
FastAPI
  │
  ▼
Authentication
  │
  ▼
Tenant Context
  │
  ▼
Service Layer
  │
  ▼
Repository
  │
  ▼
MongoDB
```

Every tenant-scoped query should enforce:

```python
{
    "tenant_id": authenticated_tenant_id,
    ...
}
```

The tenant identifier should be part of relevant indexes.

### Design an Event-Driven MongoDB Service

```text
FastAPI
  │
  ▼
MongoDB
  │
  ▼
Outbox / Change Stream
  │
  ▼
Kafka
  │
  ├── Notification Service
  ├── Search Service
  └── Analytics Service
```

Senior concerns include:

- Idempotency
- Event ordering
- Retry strategy
- Dead-letter handling
- Schema evolution
- Duplicate events
- Observability
- Backpressure
- Data consistency

## Interview Traps

### MongoDB Is Schema-Less

This is an oversimplification.

MongoDB provides schema flexibility, but production systems should still enforce data contracts through:

- Application validation
- Schema validation
- Tests
- Controlled migrations
- Operational discipline

### MongoDB Does Not Support Transactions

Incorrect.

MongoDB supports multi-document transactions. The more important question is whether a transaction is necessary for the data model.

### MongoDB Is Always Faster Than PostgreSQL

There is no universal answer.

Performance depends on:

- Access patterns
- Data model
- Indexes
- Query complexity
- Workload
- Consistency requirements
- Operational architecture

### Async FastAPI Requires Async MongoDB

Not necessarily.

FastAPI can work with synchronous MongoDB access, but blocking database operations must be handled appropriately.

### More Indexes Always Improve Performance

Incorrect.

Indexes improve specific access patterns while increasing:

- Storage
- Memory pressure
- Write cost
- Maintenance cost

### Read From Secondaries for Better Performance

Only when the workload can tolerate the consistency characteristics and replication lag.

### `skip()` Is Fine for Any Pagination

It may be acceptable for small datasets, but deep offset pagination can become expensive.

### MongoDB Documents Should Never Be Embedded

Incorrect.

Embedding is often one of MongoDB's strengths when related data is bounded and commonly accessed together.

## Production Checklist

### Application

- MongoDB client is application-scoped
- Database lifecycle is managed through FastAPI lifespan
- Connection pool sizing is intentional
- Timeouts are configured
- Retry behavior is bounded
- API schemas are explicit
- ObjectId serialization is consistent
- Authorization is enforced before database access

### Data Access

- Queries are based on access patterns
- Indexes support important queries
- Deep offset pagination is avoided
- Large documents are avoided
- Aggregation pipelines are reviewed
- Transactions are used selectively
- Repository boundaries are clear

### Security

- Least-privileged MongoDB user
- TLS enabled where required
- Secrets are externalized
- Network access is restricted
- Sensitive fields are not exposed
- Client-provided MongoDB operators are not trusted
- Tenant isolation is enforced

### Reliability

- Replica-set architecture is used where HA is required
- Appropriate write concern is configured
- Backup strategy exists
- Restore procedures are tested
- RPO and RTO are defined
- Replication lag is monitored
- Graceful shutdown is implemented

### Performance

- Slow queries are measured
- `explain("executionStats")` is used
- Indexes are reviewed regularly
- Connection pools are monitored
- Large result sets are controlled
- Aggregations are optimized
- Performance regressions are detected

### Operations

- Metrics are collected
- Structured logs are available
- Request tracing is implemented where useful
- Database health is monitored
- Storage growth is tracked
- Connection utilization is monitored
- Operational runbooks exist

## Key Takeaways

- Treat FastAPI, the service layer, and MongoDB repositories as separate responsibilities; this keeps API contracts independent from persistence details.
- Reuse an application-scoped MongoDB client, size connection pools across all workers and pods, and configure explicit timeouts and bounded retry behavior.
- Design MongoDB queries, indexes, pagination, and document structure together around real access patterns; validate performance with `explain("executionStats")`.
- Use transactions, replica-set read/write concerns, secondary reads, change streams, and sharding only when their consistency, scalability, and operational trade-offs match the workload.
- Production FastAPI + MongoDB systems require the same engineering discipline as any critical backend: least-privilege security, observability, high availability, tested backups, recovery procedures, and controlled schema evolution.