# 12- Django and MongoDB Questions

## Overview

Django is primarily designed around relational databases and its native ORM. MongoDB is a document-oriented database with different modeling, querying, transaction, and consistency semantics.

Using Django with MongoDB therefore requires an explicit architectural decision. MongoDB should not be treated as a drop-in replacement for PostgreSQL or MySQL, and Django's native ORM abstractions should not be assumed to map cleanly to MongoDB.

Common integration approaches include:

| Approach | Description | Typical Use |
|---|---|---|
| PyMongo | Direct MongoDB driver access | Production services requiring explicit MongoDB control |
| MongoEngine | ODM providing document-oriented abstractions | Applications wanting document models |
| Repository layer | Application-defined persistence abstraction | Large Django applications and service architectures |
| Separate MongoDB service | MongoDB accessed by a dedicated service | Microservices and bounded contexts |
| Django ORM + MongoDB repository | Relational DB remains primary while MongoDB handles specific workloads | Polyglot persistence |

A practical architecture is:

```text
                    ┌──────────────────┐
                    │      Client      │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │      Django      │
                    │ Views / DRF API  │
                    └────────┬─────────┘
                             │
                  ┌──────────┴──────────┐
                  ▼                     ▼
          Django ORM              Mongo Repository
                  │                     │
                  ▼                     ▼
             PostgreSQL             MongoDB
```

The important engineering decision is determining which data belongs in which persistence system and how application boundaries prevent database-specific behavior from leaking throughout the codebase.

## Django and MongoDB Architecture

A production Django application should separate HTTP, business, and persistence concerns.

A recommended structure is:

```text
project/
├── manage.py
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── users/
│   ├── views.py
│   ├── serializers.py
│   ├── services.py
│   └── repositories.py
├── orders/
│   ├── views.py
│   ├── serializers.py
│   ├── services.py
│   └── repositories.py
└── infrastructure/
    └── mongodb.py
```

The request flow should look like:

```text
HTTP Request
    │
    ▼
Django URL Router
    │
    ▼
View / DRF ViewSet
    │
    ▼
Serializer / Validation
    │
    ▼
Service Layer
    │
    ▼
MongoDB Repository
    │
    ▼
PyMongo
    │
    ▼
MongoDB
```

The view should not become a collection of MongoDB queries.

Avoid:

```python
def get_users(request):
    users = mongo_client["app"]["users"].find(...)
    ...
```

Prefer:

```python
def get_users(request):
    users = user_service.list_users(...)
    ...
```

The service can then delegate persistence to a repository.

## Why MongoDB in a Django Application?

MongoDB can be useful when the workload has characteristics such as:

- Document-oriented data
- Variable document structure
- Nested objects
- Large aggregate-style documents
- High-volume event or telemetry data
- Content with flexible attributes
- Query patterns that benefit from document modeling
- Independent scaling requirements

Examples include:

- Product catalogs with variable attributes
- Event records
- Audit documents
- Content metadata
- Device telemetry
- External API payloads
- Search-oriented document representations

MongoDB is not automatically preferable for every Django application.

If the application requires:

- Complex relational joins
- Strong relational constraints
- Mature relational reporting
- Complex SQL analytics
- Heavy foreign-key relationships
- Extensive Django ORM usage

a relational database may be a better primary persistence layer.

## Django ORM Versus MongoDB

Django's ORM assumes relational concepts such as:

```text
Model
  ↓
Table
  ↓
Row
  ↓
Column
  ↓
Foreign Key
```

MongoDB uses:

```text
Database
  ↓
Collection
  ↓
Document
  ↓
Field
  ↓
Embedded Document / Array
```

The conceptual difference is important.

| Relational Database | MongoDB |
|---|---|
| Table | Collection |
| Row | Document |
| Column | Field |
| Foreign key | Reference or embedded document |
| JOIN | `$lookup` or application-side access |
| SQL | MongoDB query language |
| Schema usually defined centrally | Schema can be flexible |
| Normalization is common | Embedding and controlled duplication are common |

Trying to force MongoDB into a relational mental model often produces inefficient document designs.

## PyMongo Integration

PyMongo provides direct access to MongoDB from Python.

A centralized client is preferable to repeatedly constructing clients.

```python
from pymongo import MongoClient
from pymongo.database import Database


class MongoDB:
    def __init__(self, uri: str, database_name: str):
        self.client = MongoClient(
            uri,
            serverSelectionTimeoutMS=5_000,
            connectTimeoutMS=5_000,
            socketTimeoutMS=10_000,
        )
        self.database: Database = self.client[database_name]

    def close(self) -> None:
        self.client.close()
```

Application configuration should come from environment variables or a secret-management system.

```python
import os

MONGODB_URI = os.environ["MONGODB_URI"]
MONGODB_DATABASE = os.environ["MONGODB_DATABASE"]
```

Do not hard-code credentials.

## MongoDB Connection Lifecycle

A MongoDB client should normally be long-lived.

The application should not do this for every request:

```python
client = MongoClient(uri)
```

Instead:

```text
Django Process Starts
        │
        ▼
Create MongoClient
        │
        ▼
Reuse Client / Connection Pool
        │
        ▼
Handle Requests
        │
        ▼
Process Shutdown
        │
        ▼
Close Client
```

This matters because `MongoClient` manages:

- Connection pooling
- Server discovery
- Topology information
- Connection monitoring
- Authentication state
- Retry behavior

Creating clients repeatedly increases resource consumption and connection overhead.

## Django Application Initialization

A reusable MongoDB infrastructure component can be initialized during application startup.

```python
from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "orders"

    def ready(self):
        from infrastructure.mongodb import initialize_mongodb

        initialize_mongodb()
```

However, initialization code should be designed carefully because Django's startup lifecycle can execute more than once in development and under certain deployment configurations.

A cleaner production architecture is often to encapsulate the client behind a lazily initialized infrastructure component.

```python
from functools import lru_cache

from pymongo import MongoClient


@lru_cache(maxsize=1)
def get_mongodb_client() -> MongoClient:
    return MongoClient(
        settings.MONGODB_URI,
        serverSelectionTimeoutMS=5_000,
        connectTimeoutMS=5_000,
        socketTimeoutMS=10_000,
    )
```

The exact lifecycle strategy should be compatible with the Django deployment model.

## Repository Pattern

A repository isolates MongoDB-specific operations.

```python
from bson import ObjectId
from pymongo.collection import Collection


class UserRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def get_by_id(self, user_id: ObjectId) -> dict | None:
        return self.collection.find_one(
            {"_id": user_id}
        )

    def get_by_email(self, email: str) -> dict | None:
        return self.collection.find_one(
            {"email": email}
        )

    def create(self, document: dict) -> ObjectId:
        result = self.collection.insert_one(document)
        return result.inserted_id
```

A service layer should own business rules.

```python
class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def create_user(self, email: str, name: str) -> ObjectId:
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

This keeps MongoDB-specific details out of views and serializers.

## Dependency and Infrastructure Management

Django does not provide FastAPI-style dependency injection by default.

A common approach is to construct repositories through application services.

```python
def get_user_repository() -> UserRepository:
    database = get_mongodb_client()["application"]
    return UserRepository(database["users"])
```

Then:

```python
def get_user_service() -> UserService:
    return UserService(get_user_repository())
```

For larger systems, a dedicated application service or dependency container can manage infrastructure components.

The goal is not to reproduce FastAPI's dependency injection model inside Django. The goal is to make dependencies explicit and testable.

## CRUD Operations

### Insert

```python
document = {
    "email": "user@example.com",
    "name": "Alice",
}

result = collection.insert_one(document)

user_id = result.inserted_id
```

### Find

```python
user = collection.find_one(
    {"email": "user@example.com"}
)
```

### Update

```python
collection.update_one(
    {"_id": user_id},
    {
        "$set": {
            "name": "Updated Name",
        }
    },
)
```

### Delete

```python
collection.delete_one(
    {"_id": user_id}
)
```

### Upsert

```python
collection.update_one(
    {"external_id": external_id},
    {
        "$set": {
            "name": name,
        }
    },
    upsert=True,
)
```

Each operation should be implemented according to the application's access patterns rather than exposed directly through generic CRUD abstractions.

## BSON and ObjectId

MongoDB commonly uses `ObjectId` for `_id`.

```python
from bson import ObjectId

user_id = ObjectId("66f3c9f0e5d6a4b8c1234567")
```

Django serializers or API responses should not accidentally expose raw BSON types that the JSON renderer cannot serialize.

A clean boundary is:

```text
MongoDB
   │
   │ ObjectId
   ▼
Repository
   │
   ▼
Service
   │
   ▼
Serializer
   │
   │ String ID
   ▼
JSON Response
```

Example:

```python
def serialize_user(document: dict) -> dict:
    return {
        "id": str(document["_id"]),
        "email": document["email"],
        "name": document["name"],
    }
```

This also prevents MongoDB-specific identifier behavior from becoming part of the public API contract.

## Django REST Framework Integration

For Django REST Framework, serializers should validate API input independently of MongoDB persistence.

```python
from rest_framework import serializers


class UserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    name = serializers.CharField(max_length=200)
```

The serializer should not be responsible for implementing large MongoDB queries.

A clean flow is:

```text
DRF Request
    ↓
Serializer Validation
    ↓
Service
    ↓
Repository
    ↓
MongoDB
```

For output:

```python
class UserResponseSerializer(serializers.Serializer):
    id = serializers.CharField()
    email = serializers.EmailField()
    name = serializers.CharField()
```

This prevents database fields from automatically becoming API fields.

## DRF View Example

```python
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class UserCreateView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = UserService(get_user_repository())

        user_id = service.create_user(
            email=serializer.validated_data["email"],
            name=serializer.validated_data["name"],
        )

        return Response(
            {"id": str(user_id)},
            status=status.HTTP_201_CREATED,
        )
```

The view coordinates HTTP concerns while the service and repository handle business and persistence concerns.

## Query Construction

MongoDB queries should be constructed explicitly.

```python
query = {
    "status": "active",
    "tenant_id": tenant_id,
}
```

Avoid accepting raw MongoDB filters from clients:

```python
query = request.data["filter"]
```

This can expose:

- Unintended operators
- Expensive queries
- Authorization bypasses
- Resource exhaustion
- Internal schema details

Instead, validate API parameters and construct the query server-side.

## Query Filters

Comparison:

```python
{
    "age": {
        "$gte": 18,
        "$lt": 65,
    }
}
```

Logical:

```python
{
    "$or": [
        {"status": "active"},
        {"status": "pending"},
    ]
}
```

Array:

```python
{
    "tags": {
        "$all": ["python", "django"]
    }
}
```

Nested:

```python
{
    "profile.country": "IN"
}
```

The query should be designed together with its indexes.

## Projection

Do not retrieve large documents when only a few fields are needed.

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

Projection reduces:

- Network transfer
- BSON decoding
- Application memory
- Serialization work

It should also be used as part of data-exposure control, although projection alone is not an authorization mechanism.

## Pagination

Offset pagination:

```python
cursor = (
    collection.find({"status": "active"})
    .sort("created_at", -1)
    .skip(offset)
    .limit(page_size)
)
```

This is simple but becomes expensive for deep pages.

For high-volume Django APIs, cursor-based pagination is often preferable.

A stable ordering might use:

```text
created_at DESC
_id DESC
```

with an index:

```python
collection.create_index(
    [
        ("status", 1),
        ("created_at", -1),
        ("_id", -1),
    ]
)
```

The cursor should normally be opaque to API consumers.

## Data Modeling for Django + MongoDB

MongoDB data modeling should begin with application access patterns.

Consider an order system.

### Embedded Design

```json
{
  "_id": "order-123",
  "customer_id": "customer-1",
  "items": [
    {
      "product_id": "product-1",
      "name": "Keyboard",
      "quantity": 2,
      "price": 80
    }
  ],
  "total": 160
}
```

Advantages:

- One read retrieves the order
- Atomic updates within the document
- Good aggregate locality

Limitations:

- Document growth
- Repeated data
- Large arrays
- Updating shared product information becomes difficult

### Referenced Design

```text
orders
  └── customer_id

order_items
  └── order_id
  └── product_id
```

Advantages:

- Smaller documents
- Independent lifecycle
- Better for unbounded relationships

Limitations:

- Multiple queries
- Application-side joins or `$lookup`
- More complicated retrieval logic

The correct design depends on access patterns, cardinality, update frequency, and document growth.

## Embedding Versus Referencing

| Requirement | Usually Consider |
|---|---|
| Small bounded child data | Embedding |
| Child always read with parent | Embedding |
| Independent child lifecycle | Referencing |
| Very large child collection | Referencing |
| Frequently updated shared data | Referencing |
| Atomic aggregate update | Embedding |
| Many-to-many relationship | References or controlled denormalization |

Avoid applying relational normalization rules blindly to MongoDB.

## Controlled Denormalization

Duplication can be intentional.

For example:

```json
{
  "product_id": "p-123",
  "product_name": "Keyboard",
  "unit_price": 80
}
```

inside an order may be correct even if the current product document also contains:

```json
{
  "_id": "p-123",
  "name": "Keyboard",
  "price": 80
}
```

The order needs the historical name and price at purchase time.

This is not accidental duplication. It is a deliberate historical snapshot.

The trade-off is consistency management.

## Document Growth

Avoid unbounded arrays.

Bad:

```json
{
  "_id": "user-1",
  "events": [
    "... potentially millions of entries ..."
  ]
}
```

Prefer separate event documents or bucketed structures.

Document growth affects:

- Storage
- Working set
- Replication
- Network transfer
- Update cost
- Application serialization

Django developers accustomed to relational child tables should pay particular attention to bounded versus unbounded embedded data.

## MongoDB Schema Validation

Flexible schemas should still have persistence-level controls.

MongoDB can enforce JSON Schema validation.

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

Django/DRF serializers and MongoDB validation solve different problems.

| Layer | Responsibility |
|---|---|
| DRF serializer | API input validation |
| Service layer | Business rules |
| MongoDB validation | Persistence-level data contract |
| Database indexes | Uniqueness and query guarantees |

Using both application and database validation provides stronger protection when data can be written through multiple paths.

## MongoEngine

MongoEngine is an ODM that provides document-oriented abstractions for MongoDB.

Conceptually:

```python
from mongoengine import Document, StringField


class User(Document):
    email = StringField(required=True, unique=True)
    name = StringField(required=True)
```

This can make document modeling more familiar to Django developers.

Advantages include:

- Document-oriented model abstraction
- Validation
- Query API
- Familiar model-style development

Limitations include:

- Additional abstraction over MongoDB
- MongoDB feature coverage may differ from direct driver usage
- Performance behavior can be less obvious
- Complex MongoDB operations may still require lower-level access
- The abstraction can encourage relational-style thinking if used carelessly

MongoEngine can be appropriate for applications that benefit from ODM semantics, but PyMongo is often preferable when direct control over MongoDB behavior is important.

## PyMongo Versus MongoEngine

| Area | PyMongo | MongoEngine |
|---|---|---|
| Abstraction | Low-level driver | ODM |
| MongoDB control | High | Higher-level |
| Query transparency | High | Moderate |
| Schema abstraction | Application-defined | Document classes |
| MongoDB-specific features | Direct access | Depends on ODM support |
| Learning curve | MongoDB knowledge required | Familiar to model-oriented developers |
| Performance visibility | High | Additional abstraction |
| Best fit | Explicit persistence architecture | Document-model-oriented applications |

Choose based on architectural requirements rather than familiarity alone.

## Django Models and MongoDB

Do not assume a normal Django model such as:

```python
class User(models.Model):
    name = models.CharField(max_length=200)
```

can simply be redirected to MongoDB with identical semantics.

Django's native model system assumes relational database behavior.

If PostgreSQL remains the primary database:

```text
Django Model
    ↓
Django ORM
    ↓
PostgreSQL
```

MongoDB-specific data can use:

```text
Django Service
    ↓
Repository
    ↓
PyMongo
    ↓
MongoDB
```

This separation makes the database boundaries explicit.

## Transactions

MongoDB supports multi-document transactions.

A Django service can explicitly use a MongoDB session:

```python
from pymongo import MongoClient


def process_order(
    client: MongoClient,
    order_id,
    inventory_id,
):
    database = client["application"]
    orders = database["orders"]
    inventory = database["inventory"]

    with client.start_session() as session:
        with session.start_transaction():
            orders.update_one(
                {"_id": order_id},
                {"$set": {"status": "confirmed"}},
                session=session,
            )

            inventory.update_one(
                {"_id": inventory_id},
                {"$inc": {"available": -1}},
                session=session,
            )
```

Transactions should be short and should not contain long external operations.

Avoid:

```text
Start transaction
  ↓
Call payment API
  ↓
Wait for external response
  ↓
Call another API
  ↓
Commit
```

This increases transaction duration and operational risk.

## Django Transactions Versus MongoDB Transactions

Django's:

```python
from django.db import transaction

with transaction.atomic():
    ...
```

controls a relational database transaction through Django's database backend.

It should not be assumed to control a separate MongoDB transaction.

If an operation uses both PostgreSQL and MongoDB:

```text
Django
 ├── PostgreSQL transaction
 └── MongoDB transaction
```

there is no automatic distributed transaction across the two databases.

This creates a consistency problem that must be handled architecturally.

## Polyglot Persistence

A Django application may legitimately use both PostgreSQL and MongoDB.

Example:

```text
                 Django
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
     PostgreSQL            MongoDB
     Core entities         Documents
     Transactions          Events
     Relational data       Flexible data
```

The critical requirement is defining system ownership.

For example:

```text
PostgreSQL → source of truth for customer account
MongoDB    → read-optimized customer profile projection
```

Do not allow both databases to independently become authoritative for the same business state without a carefully designed consistency model.

## PostgreSQL and MongoDB Consistency

Suppose an order is created in PostgreSQL and a MongoDB document must also be updated.

This is unsafe:

```python
postgres_create_order()
mongodb_create_order()
```

because the second operation can fail after the first succeeds.

Better approaches may include:

- Transactional outbox
- Event-driven synchronization
- Idempotent consumers
- Reconciliation jobs
- Explicit source-of-truth ownership

Example:

```text
PostgreSQL Transaction
        │
        ├── Order
        └── Outbox Event
                │
                ▼
             Worker
                │
                ▼
             MongoDB
```

The outbox pattern avoids pretending that two independent databases form one atomic transaction.

## Indexing

Indexes should be designed from Django application access patterns.

Suppose a repository frequently executes:

```python
collection.find(
    {
        "tenant_id": tenant_id,
        "status": "active",
    }
).sort(
    "created_at",
    -1,
)
```

A possible compound index is:

```python
collection.create_index(
    [
        ("tenant_id", 1),
        ("status", 1),
        ("created_at", -1),
    ],
    name="tenant_status_created",
)
```

The exact ordering should be validated against actual query patterns, selectivity, and sort behavior.

## Explain Plans

Use `explain()` when a Django endpoint is slow.

```python
plan = (
    collection.find(
        {
            "tenant_id": tenant_id,
            "status": "active",
        }
    )
    .sort("created_at", -1)
    .explain("executionStats")
)
```

Important metrics:

| Metric | Meaning |
|---|---|
| `nReturned` | Documents returned |
| `totalKeysExamined` | Index keys examined |
| `totalDocsExamined` | Documents examined |
| `executionTimeMillis` | Query execution time |
| `winningPlan` | Selected execution plan |

A query returning 25 documents while examining hundreds of thousands should be investigated.

## Aggregation in Django

Aggregation pipelines can be encapsulated inside repositories.

```python
pipeline = [
    {
        "$match": {
            "tenant_id": tenant_id,
            "status": "completed",
        }
    },
    {
        "$group": {
            "_id": "$customer_id",
            "total": {"$sum": "$amount"},
            "orders": {"$sum": 1},
        }
    },
    {
        "$sort": {
            "total": -1,
        }
    },
    {
        "$limit": 20,
    },
]

results = collection.aggregate(pipeline)
```

The repository should return an application-friendly representation rather than exposing MongoDB cursors throughout the Django codebase.

## Aggregation Performance

Prefer:

```text
$match
  ↓
$project
  ↓
$group
  ↓
$sort
  ↓
$limit
```

where appropriate.

Early filtering reduces the number of documents entering later stages.

Avoid large unrestricted aggregations inside synchronous HTTP requests.

For expensive reporting:

```text
Django API
   │
   ▼
Create Report Job
   │
   ▼
Celery Worker
   │
   ▼
MongoDB Aggregation
   │
   ▼
Persist Report
```

This protects request latency and web-worker capacity.

## Celery and MongoDB

Django applications frequently use Celery for background processing.

A suitable architecture is:

```text
Django API
    │
    ├── MongoDB
    │
    └── Celery Queue
            │
            ▼
        Celery Worker
            │
            ▼
         MongoDB
```

Use background workers for:

- Large aggregations
- Data imports
- External synchronization
- Bulk updates
- Report generation
- Event processing

Workers should be idempotent because retries can occur.

## Change Streams

MongoDB change streams can support event-driven Django architectures.

```text
MongoDB
   │
   ▼
Change Stream Consumer
   │
   ├── Validate event
   ├── Apply business action
   └── Publish downstream event
```

Potential use cases:

- Cache invalidation
- Search indexing
- Audit processing
- Data synchronization
- Notifications

Consumers should persist or otherwise manage resume tokens and make processing idempotent.

Do not assume exactly-once application behavior merely because MongoDB emits change events.

## Redis and Django + MongoDB

Redis can complement MongoDB.

```text
Django
  │
  ├── Redis → Cache
  │
  └── MongoDB → Durable document data
```

A common mistake is caching every MongoDB query without understanding invalidation.

Use Redis when:

- Data is frequently read
- Data can tolerate controlled staleness
- Computation is expensive
- A cache materially reduces database load

Do not use Redis to compensate for an inefficient MongoDB query that should instead be indexed or redesigned.

## Security

A Django application should connect using a dedicated MongoDB identity.

Avoid:

```text
root/admin credentials
```

for normal application access.

Use:

- Least privilege
- Database-specific permissions
- TLS
- Network restrictions
- Secret management
- Credential rotation
- Auditing where required
- Encryption at rest
- Encryption in transit

MongoDB credentials should not be stored in:

- Git repositories
- Dockerfiles
- Source code
- Public CI logs
- Exception messages

## Django Security Boundary

Authentication should occur in Django/DRF.

Authorization should be enforced before constructing MongoDB queries.

For example:

```python
query = {
    "tenant_id": request.user.tenant_id,
    "_id": user_id,
}
```

Do not trust:

```python
request.query_params["tenant_id"]
```

as an authorization boundary.

The tenant context should come from authenticated and authorized application state.

## Testing

Testing should happen at multiple layers.

```text
Unit Tests
   │
   ▼
Service Tests
   │
   ▼
Repository Integration Tests
   │
   ▼
Django API Tests
   │
   ▼
End-to-End Tests
```

### Service Tests

Mock the repository:

```python
def test_create_user():
    repository = FakeUserRepository()
    service = UserService(repository)

    result = service.create_user(
        email="user@example.com",
        name="Alice",
    )

    assert result is not None
```

### Repository Tests

Use a real MongoDB-compatible environment to test:

- Queries
- Indexes
- Aggregation
- Unique constraints
- Transactions
- BSON behavior

Mocks cannot reliably verify MongoDB query semantics.

## Test Database Isolation

Integration tests should use isolated test data.

Possible approaches include:

- Dedicated test database
- Per-test collections
- Randomized test namespaces
- Cleanup fixtures
- Ephemeral MongoDB environments

Tests should explicitly create required indexes instead of depending on a developer's local MongoDB state.

## Error Handling

MongoDB exceptions should be translated into application-level errors.

```python
from pymongo.errors import DuplicateKeyError


def create_user(repository, document):
    try:
        return repository.create(document)
    except DuplicateKeyError as exc:
        raise UserAlreadyExistsError from exc
```

The API layer can then translate the domain error:

```python
return Response(
    {"detail": "User already exists"},
    status=409,
)
```

Do not expose raw database exceptions to clients.

## Timeouts

Production connections should have bounded timeouts.

```python
MongoClient(
    settings.MONGODB_URI,
    serverSelectionTimeoutMS=5_000,
    connectTimeoutMS=5_000,
    socketTimeoutMS=10_000,
)
```

Timeouts should align with Django's API latency budget.

If:

```text
API timeout = 5 seconds
```

but:

```text
MongoDB socket timeout = 60 seconds
```

the database operation can continue consuming resources long after the request has become irrelevant.

## Retry Behavior

Transient failures can occur during:

- Replica-set elections
- Network interruptions
- Connection failures
- Topology changes

Use bounded retry behavior where supported.

Good retry behavior includes:

```text
Transient failure
      ↓
Retryable?
      ↓
Yes
      ↓
Exponential backoff + jitter
      ↓
Retry
      ↓
Bounded attempts
```

Do not retry every exception.

Non-idempotent operations require particular care because retrying a successful but ambiguously acknowledged operation can produce duplicate effects.

## Connection Pooling

Each Django process can have its own MongoDB client and pool.

If the deployment contains:

```text
4 application workers
3 pods
```

and each process can use:

```text
maxPoolSize = 50
```

the potential connection count can become substantial.

Pool sizing should therefore consider:

```text
Workers
×
Pods
×
Pool size
×
Environments
```

Do not increase `maxPoolSize` blindly.

Monitor actual connection utilization and MongoDB capacity.

## Django Deployment Architecture

A production architecture might be:

```text
                   ┌───────────────┐
                   │ Load Balancer │
                   └───────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
           Django       Django       Django
              │            │            │
              └────────────┼────────────┘
                           │
                 ┌─────────┴─────────┐
                 ▼                   ▼
             PostgreSQL           MongoDB
                                  Replica Set
```

If Redis and Celery are used:

```text
Django
  │
  ├── PostgreSQL
  ├── MongoDB
  ├── Redis
  │
  └── Celery
          │
          ▼
       Workers
```

Each component should have an explicit ownership and failure model.

## Docker Considerations

A local Django + MongoDB environment may use Docker Compose.

```yaml
services:
  web:
    build: .
    environment:
      MONGODB_URI: mongodb://mongo:27017/application
      MONGODB_DATABASE: application
    depends_on:
      - mongo

  mongo:
    image: mongo:latest
```

For production, additional concerns include:

- Persistent storage
- Authentication
- TLS
- Replica sets
- Resource limits
- Backups
- Monitoring
- Secret management
- Network restrictions
- Upgrade procedures

A local single MongoDB container is not equivalent to a production HA deployment.

## Kubernetes Considerations

When Django runs in Kubernetes:

```text
Deployment
  │
  ├── Pod 1 → MongoDB Pool
  ├── Pod 2 → MongoDB Pool
  └── Pod 3 → MongoDB Pool
```

Each pod maintains its own connections.

Scaling Django from three to ten pods can therefore increase MongoDB connection demand significantly.

Use:

- Readiness probes
- Liveness probes
- Graceful termination
- Resource requests and limits
- Horizontal scaling based on measured workload
- Secret management
- Network policies
- Centralized logging

Managed MongoDB infrastructure is often operationally simpler than running a production MongoDB cluster inside the same Kubernetes environment.

## Backup and Recovery

MongoDB data accessed by Django requires an independent backup and recovery strategy.

Important concepts include:

- Logical backups
- Managed backups
- Point-in-time recovery
- Retention
- Restore testing
- RPO
- RTO
- Disaster recovery

Logical backup example:

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

A backup is not a recovery strategy until restoration has been tested.

## MongoDB Atlas

MongoDB Atlas can reduce the operational burden of running MongoDB infrastructure.

A Django deployment can connect using a managed connection string:

```text
Django
  │
  ▼
MongoDB Driver
  │
  ▼
MongoDB Atlas
  │
  ├── Replica Set
  ├── Monitoring
  ├── Backups
  └── Managed Infrastructure
```

Application responsibilities remain:

- Correct data modeling
- Index design
- Authentication
- Authorization
- Query optimization
- Connection management
- Secret management
- Application-level observability

Managed infrastructure does not eliminate database engineering.

## MongoDB Compass

Compass is useful for development and operational investigation.

Typical workflow:

```text
Connect
  ↓
Select Database
  ↓
Browse Collection
  ↓
Test Query
  ↓
Inspect Indexes
  ↓
Build Aggregation
  ↓
Analyze Documents
```

Useful tasks include:

- Document inspection
- Query testing
- Aggregation development
- Index inspection
- Schema analysis
- JSON import
- CSV import
- Data export

Production changes should generally be performed through controlled operational procedures rather than manually modifying production data in Compass.

## mongosh

Connect:

```bash
mongosh "$MONGODB_URI"
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

Query:

```javascript
db.users.find({
  status: "active"
}).limit(20)
```

Inspect indexes:

```javascript
db.users.getIndexes()
```

Explain:

```javascript
db.users.find({
  status: "active"
}).explain("executionStats")
```

Replica-set status:

```javascript
rs.status()
```

Collection statistics:

```javascript
db.users.stats()
```

Database statistics:

```javascript
db.stats()
```

Operational access should use appropriate authentication, authorization, auditing, and network controls.

## Performance Optimization

A senior engineer should diagnose MongoDB performance systematically.

```text
Django Endpoint Slow
        ↓
Measure HTTP Latency
        ↓
Measure MongoDB Latency
        ↓
Inspect Query
        ↓
Run explain("executionStats")
        ↓
Inspect Indexes
        ↓
Inspect Result Size
        ↓
Optimize
        ↓
Benchmark
        ↓
Monitor Regression
```

Important areas include:

- Index selection
- Compound index order
- Query selectivity
- Projection
- Pagination
- Aggregation
- Document size
- Connection pool utilization
- Working set
- Read/write workload
- Replica-set health

## Query Performance Example

Suppose a Django endpoint returns 20 documents.

Before optimization:

```text
nReturned = 20
totalDocsExamined = 700000
executionTimeMillis = 850
```

After creating a query-appropriate index:

```text
nReturned = 20
totalDocsExamined = 20
executionTimeMillis = 7
```

The exact numbers are workload-dependent. The engineering principle is to measure the execution plan and compare behavior before and after the change.

## Large Documents

Large MongoDB documents can negatively affect Django applications through:

- Higher network transfer
- Increased BSON decoding
- More Python memory usage
- More serializer work
- Larger replication traffic

Use projection:

```python
collection.find(
    {"tenant_id": tenant_id},
    {
        "_id": 1,
        "name": 1,
    },
)
```

Avoid retrieving entire documents when the API needs only a few fields.

## Large Aggregations

Do not execute an expensive aggregation synchronously inside a normal web request if it can take seconds or minutes.

Prefer:

```text
Django Request
     │
     ▼
Create Report Job
     │
     ▼
Celery
     │
     ▼
MongoDB Aggregation
     │
     ▼
Store Result
     │
     ▼
Client Retrieves Result
```

This protects web workers from long-running operations.

## Monitoring

Monitor both Django and MongoDB.

### Django Metrics

- Request latency
- Request throughput
- Error rate
- Worker utilization
- Queue latency
- CPU
- Memory

### MongoDB Metrics

- Query latency
- Operation counts
- Connections
- Replication lag
- Storage growth
- Working set
- Index usage
- Slow queries
- Replica-set health

### Application Logs

Use structured logging:

```json
{
  "request_id": "req-123",
  "operation": "get_user",
  "route": "/api/users/123",
  "duration_ms": 18,
  "status_code": 200
}
```

Do not log credentials or sensitive MongoDB documents.

## Troubleshooting Django and MongoDB

Use:

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

### MongoDB Connection Failure

**Symptom**

```text
ServerSelectionTimeoutError
```

**Possible causes**

- Invalid connection string
- DNS failure
- Network restriction
- MongoDB unavailable
- TLS mismatch
- Authentication failure
- Replica-set discovery issue

**Isolation strategy**

Test from the actual Django runtime environment:

```bash
mongosh "$MONGODB_URI"
```

Then verify:

```text
DNS
TCP connectivity
TLS
authentication
MongoDB topology
```

**Root cause**

Identify whether the failure occurs before authentication, during topology discovery, or while executing an operation.

**Corrective action**

Fix the relevant network, credential, TLS, or topology configuration.

**Prevention**

- Health checks
- Startup validation
- Monitoring
- Secret validation
- Network testing

### Slow Django Endpoint

**Symptom**

```text
GET /api/orders → 2 seconds
```

**Possible causes**

- Missing index
- Poor query shape
- Large documents
- Expensive aggregation
- Connection pool contention
- Application serialization
- N+1-like repository calls

**Isolation strategy**

Separate:

```text
Django processing
MongoDB execution
Serialization
Network
```

**Diagnostic command**

```javascript
db.orders.find({
  tenant_id: "tenant-1",
  status: "active"
}).explain("executionStats")
```

**Corrective action**

Potentially:

- Add or modify an index
- Reduce projection
- Replace repeated queries with aggregation
- Implement cursor pagination
- Move expensive work to Celery

**Prevention**

- Performance tests
- Query reviews
- Index reviews
- Monitoring

### Duplicate Key Error

**Symptom**

```text
DuplicateKeyError
```

**Possible causes**

- Unique index
- Concurrent creation
- Retry
- Incorrect upsert design

**Diagnostic command**

```javascript
db.users.getIndexes()
```

**Corrective action**

Treat the unique constraint as part of the business contract and handle the duplicate as a known domain condition.

Do not remove the index simply to suppress the error.

### Stale Reads

**Symptom**

A Django request does not immediately see a recently written value.

**Possible causes**

- Secondary read preference
- Replication lag
- Eventual consistency in an application projection

**Isolation strategy**

Determine which replica member served the read and inspect replication health.

**Corrective action**

Use an appropriate read preference and consistency strategy.

**Prevention**

Document which application operations require strong read semantics.

### Transaction Failure

**Symptom**

A multi-document operation aborts.

**Possible causes**

- Transient topology error
- Write conflict
- Timeout
- Incorrect session usage
- Long transaction
- Unsupported operation

**Isolation strategy**

Capture:

- MongoDB error code
- Transaction duration
- Session behavior
- Replica-set state
- Read/write concerns

**Corrective action**

Retry only when the operation is safely retryable and redesign long-running transactions.

**Prevention**

Keep transactions short and test failure scenarios.

## Common Mistakes

### Treating MongoDB Like PostgreSQL

Bad assumption:

```text
Every relationship should become a reference.
```

MongoDB often benefits from embedding and controlled denormalization.

### Using Django's Native ORM Abstractions Blindly

MongoDB has different semantics.

Do not assume relational ORM features such as:

```text
JOIN
ForeignKey
select_related()
transaction.atomic()
```

have identical meaning for MongoDB.

### Creating a MongoDB Client Per Request

This defeats connection pooling and increases connection overhead.

### Returning Raw MongoDB Documents

This can leak:

- BSON-specific types
- Internal fields
- Sensitive data
- Persistence schema

### Accepting Raw Query Objects From Clients

This can expose MongoDB operators and create security and performance risks.

### Using Unbounded Embedded Arrays

Unbounded document growth can become a serious production problem.

### Ignoring Indexes

A correct Django view can still be slow if the underlying MongoDB query is inefficient.

### Over-Indexing

Every additional index increases storage and write maintenance cost.

### Long Transactions

Long transactions increase contention and resource consumption.

### Mixing PostgreSQL and MongoDB Without Ownership

If two databases represent the same business state without a defined source of truth, synchronization problems become difficult to resolve.

## Interview Questions

### Can Django use MongoDB?

Yes, but MongoDB is not equivalent to Django's normal relational database backend. Applications commonly use PyMongo, an ODM such as MongoEngine, or a repository/service architecture.

### Can Django ORM be used directly with MongoDB?

The native Django ORM is designed around relational database semantics. MongoDB-specific persistence should generally use a MongoDB-compatible abstraction rather than assuming native ORM behavior.

### Why use PyMongo with Django?

PyMongo provides direct access to MongoDB features, query semantics, indexes, aggregation, transactions, sessions, and driver configuration without forcing MongoDB into relational abstractions.

### Why use a repository pattern?

It isolates MongoDB-specific persistence logic from Django views, serializers, and business services.

### Should MongoDB replace PostgreSQL in a Django application?

Not automatically. The choice depends on data relationships, access patterns, consistency requirements, query complexity, operational requirements, and application architecture.

### Can Django's `transaction.atomic()` control MongoDB transactions?

Not automatically. Django's transaction management applies to configured relational database backends and should not be assumed to control an independently managed MongoDB transaction.

### How should Django and MongoDB transactions interact?

If both PostgreSQL and MongoDB participate in one business workflow, they require an explicit consistency strategy such as an outbox pattern, event-driven synchronization, reconciliation, or clearly defined source-of-truth ownership.

### How do you handle ObjectId in Django REST Framework?

Convert `ObjectId` into an API-friendly representation such as a string and keep BSON-specific types inside the persistence layer where possible.

### How should MongoDB pagination be implemented?

For large collections, use cursor/keyset pagination with stable indexed ordering rather than large `skip()` offsets.

### How do you optimize a slow Django endpoint backed by MongoDB?

Measure the endpoint, isolate MongoDB latency, inspect `explain("executionStats")`, evaluate index usage, projection, document size, connection pooling, and query shape, then benchmark the change.

### When should MongoDB aggregation run in Celery?

When the operation is expensive enough to threaten web request latency or worker capacity, move it to a background task and expose job status or persisted results through the API.

### What is the biggest architectural risk when using PostgreSQL and MongoDB together?

Unclear ownership of business state. Without a defined source of truth and synchronization strategy, partial failures can leave the databases inconsistent.

## Senior-Level Design Questions

### Design a Django Application Using PostgreSQL and MongoDB

A reasonable architecture is:

```text
                         Django
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
        Domain Services          Document Services
              │                         │
              ▼                         ▼
        Django ORM                 Repository
              │                         │
              ▼                         ▼
        PostgreSQL                 MongoDB
```

Use PostgreSQL for:

- Strong relational constraints
- Core transactional entities
- Complex relational queries

Use MongoDB for:

- Flexible documents
- Event-oriented data
- Large document aggregates
- Specialized access patterns

Define ownership explicitly.

### Design an Order Service

Potential design:

```text
Django API
    │
    ▼
Order Service
    │
    ├── PostgreSQL
    │      └── Order state
    │
    ├── MongoDB
    │      └── Order document / history
    │
    └── Outbox
           │
           ▼
        Celery / Kafka
```

The architecture must define whether MongoDB stores:

- Source-of-truth order state
- A read model
- Historical snapshots
- Search-oriented projections

Do not make the same state independently authoritative in both databases.

### Design a Multi-Tenant Django + MongoDB API

```text
Request
   │
   ▼
Django Authentication
   │
   ▼
Tenant Authorization
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

Tenant filtering should be part of repository design:

```python
query = {
    "tenant_id": authenticated_tenant_id,
    "status": "active",
}
```

Relevant indexes should include tenant context where appropriate.

### Design a MongoDB Reporting System

For expensive reporting:

```text
Django API
    │
    ▼
Create Report Job
    │
    ▼
Celery
    │
    ▼
MongoDB Aggregation
    │
    ▼
Persist Report
    │
    ▼
Django API
    │
    ▼
Client
```

This avoids tying report execution to HTTP request duration.

## Interview Traps

### "MongoDB Is Schema-Less"

More accurately, MongoDB supports schema flexibility.

Production applications should still use:

- Application validation
- Schema validation
- Indexes
- Tests
- Controlled migrations
- Data contracts

### "MongoDB Does Not Support Transactions"

Incorrect.

MongoDB supports multi-document transactions. The architectural question is when a transaction is necessary and whether the data model can avoid one.

### "Django ORM Works the Same With MongoDB"

Incorrect.

Django's native ORM is built around relational semantics.

### "MongoDB Should Replace PostgreSQL"

There is no universal rule.

The correct database depends on workload, data relationships, consistency, query patterns, and operational requirements.

### "Embedding Is Always Better"

Incorrect.

Embedding is useful for bounded, frequently co-read data. Large or independently managed child data may be better represented as separate documents.

### "More Indexes Make MongoDB Faster"

Incorrect.

Indexes improve supported query patterns but increase storage and write costs.

### "MongoDB Transactions Make Cross-Database Operations Atomic"

Incorrect.

A MongoDB transaction does not automatically include PostgreSQL.

### "A Managed MongoDB Service Removes Database Engineering"

Incorrect.

Managed infrastructure reduces operational work but does not eliminate:

- Data modeling
- Index design
- Query optimization
- Security
- Capacity planning
- Backup validation
- Application consistency

## Production Checklist

### Architecture

- MongoDB has a clearly defined responsibility
- Source-of-truth ownership is documented
- PostgreSQL and MongoDB consistency boundaries are explicit
- Repository and service layers are separated
- MongoDB-specific logic does not leak throughout Django

### Connection Management

- MongoDB client is long-lived
- Connection pools are intentionally sized
- Timeouts are configured
- Connection counts are monitored
- Application startup does not create unnecessary clients

### Data Modeling

- Access patterns drive document structure
- Embedding versus referencing is deliberate
- Arrays are bounded where possible
- Document growth is monitored
- Duplication is intentional
- Schema evolution is controlled

### Query and Performance

- Important queries have appropriate indexes
- Compound indexes match real access patterns
- Deep `skip()` pagination is avoided
- Projection is used where useful
- Aggregations are reviewed
- Slow queries are analyzed with `explain()`
- Performance is measured before and after optimization

### Security

- Dedicated least-privileged MongoDB user
- TLS enabled where required
- Credentials stored outside source control
- Network access restricted
- Tenant authorization enforced server-side
- Raw MongoDB filters are not accepted from clients
- Sensitive fields are excluded from API responses

### Transactions and Consistency

- MongoDB transactions are used only where required
- Transactions are short-lived
- Retry behavior is bounded
- PostgreSQL/MongoDB consistency strategy is documented
- Idempotency is implemented for retried workflows

### Operations

- Replica-set health is monitored
- Replication lag is monitored
- Connection usage is monitored
- Storage growth is tracked
- Query performance is monitored
- Structured logging is enabled
- Backups exist
- Restore procedures are tested
- RPO and RTO are defined

### Deployment

- Production configuration is externalized
- Secrets are managed securely
- MongoDB is deployed with appropriate HA
- Django graceful shutdown is supported
- Kubernetes connection scaling is considered
- Deployment and rollback procedures are documented

## Key Takeaways

- Django and MongoDB should be integrated through explicit MongoDB-aware persistence boundaries rather than treating MongoDB as a relational Django ORM replacement.
- PyMongo, repositories, and service layers provide direct control over MongoDB queries, transactions, indexes, pooling, and operational behavior.
- Data modeling, indexes, pagination, aggregation, and document growth must be designed from actual Django application access patterns.
- When PostgreSQL and MongoDB coexist, clearly define source-of-truth ownership and use patterns such as transactional outbox and idempotent event processing instead of assuming cross-database atomicity.
- Production Django + MongoDB systems require deliberate security, connection management, observability, high availability, backup, recovery, and performance engineering.