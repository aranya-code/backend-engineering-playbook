# 05- Django and MongoDB

## Overview

Django is primarily designed around a relational database model and its native ORM. MongoDB is a document database with different data-modeling, querying, transaction, and schema characteristics. Integrating the two therefore requires understanding which Django abstractions map naturally to MongoDB and which relational assumptions should not be carried over unchanged.

There are several approaches to using MongoDB with Django:

| Approach | Abstraction | Driver | Current position |
|---|---|---|---|
| Django MongoDB Backend | Django database backend | PyMongo | Official MongoDB integration; currently Public Preview |
| MongoEngine | ODM | PyMongo | Mature third-party ODM with Django integration |
| Direct PyMongo | Driver | PyMongo | Maximum MongoDB control |
| Djongo | SQL-to-MongoDB translation | Third-party | Legacy approach; not preferred for modern Django |

MongoDB currently provides an official Django MongoDB Backend that uses PyMongo and integrates MongoDB with Django's model/query abstractions. MongoDB currently labels this backend **Public Preview**, so production adoption should be evaluated against the current compatibility matrix and release status. ([MongoDB Django MongoDB Backend documentation](https://www.mongodb.com/docs/languages/python/django-mongodb/current/))

MongoEngine remains a separate ODM approach and is explicitly documented as a Python ODM based on PyMongo with Django support. ([MongoEngine documentation](https://docs.mongoengine.org/))

The correct architectural decision depends on how much of Django's framework you want to use versus how much MongoDB-specific control you require.

## Django's Relational Assumptions

Before integrating MongoDB, understand the assumptions built into conventional Django development.

A typical Django application looks like:

```text
Django
  ↓
Django ORM
  ↓
PostgreSQL
  ↓
Tables
  ↓
Rows
```

MongoDB changes the persistence model:

```text
Django
  ↓
MongoDB Integration
  ↓
PyMongo
  ↓
MongoDB
  ↓
Collections
  ↓
Documents
```

The difference affects:

- Relationships
- Joins
- Schema design
- Primary keys
- Transactions
- Migrations
- Constraints
- Query optimization
- Indexing
- Aggregation
- Data duplication

Django's own documentation historically stated that NoSQL databases were not officially supported by Django itself. The current MongoDB integration is provided separately by MongoDB through the Django MongoDB Backend. ([Django database FAQ](https://docs.djangoproject.com/en/5.2/faq/models/))

## Integration Options

### Django MongoDB Backend

The official backend uses PyMongo and provides a Django-oriented interface for working with MongoDB.

Current documentation describes support for:

- Django models
- QuerySets
- Forms
- Validation
- Authentication
- Indexes
- Aggregation
- Transactions
- MongoDB-specific queries
- Django Admin-related workflows

However, MongoDB currently labels the backend as Public Preview, which means compatibility and behavior should be validated before production adoption. ([MongoDB Django integration documentation](https://www.mongodb.com/docs/languages/python/django-mongodb/current/))

### MongoEngine

MongoEngine is an ODM:

```text
Django
   ↓
Application / Views / Services
   ↓
MongoEngine
   ↓
PyMongo
   ↓
MongoDB
```

It provides:

- Document classes
- Field definitions
- QuerySets
- Embedded documents
- References
- Validation
- Index declarations
- Signals

It is useful when the application wants explicit document-oriented Python models without making MongoDB look like a relational database.

### Direct PyMongo

Direct PyMongo provides the greatest MongoDB-specific control:

```text
Django
   ↓
Service / Repository
   ↓
PyMongo
   ↓
MongoDB
```

This is often appropriate for:

- Complex aggregation
- Bulk operations
- Specialized MongoDB features
- Performance-sensitive workloads
- Explicit transaction handling
- Change streams
- MongoDB-specific architectures

## Choosing an Integration

| Requirement | Django MongoDB Backend | MongoEngine | PyMongo |
|---|---:|---:|---:|
| Django ORM-style development | Strong | Moderate | None |
| Django model integration | Strong | Separate ODM model | Manual |
| MongoDB-specific control | Moderate | High | Highest |
| Document-oriented modeling | Strong | Strong | Manual |
| Complex MongoDB operations | Supported | Possible | Strongest |
| Existing Django application | Attractive | Requires architectural integration | More custom work |
| Async MongoDB access | Validate current backend support | Not primary strength | `AsyncMongoClient` |
| MongoDB-specific performance tuning | Good | Good | Excellent |
| Framework coupling | Higher | Moderate | Lower |
| MongoDB learning requirement | Still required | Still required | Essential |

Do not choose an integration simply because its API resembles Django ORM. The database's actual behavior remains the important architectural boundary.

## Recommended Architectural Boundary

For a serious backend application, use a layered architecture:

```mermaid
flowchart TB
    Client[HTTP Client] --> Django[Django]
    Django --> View[View / DRF View]
    View --> Schema[Serializer / Form]
    Schema --> Service[Service Layer]
    Service --> Repository[Repository]
    Repository --> Adapter[MongoDB Adapter]
    Adapter --> Mongo[(MongoDB)]
```

The repository or adapter layer should own MongoDB-specific persistence details.

This gives the application a clear boundary:

```text
Django / DRF
     ↓
Business Logic
     ↓
Persistence Interface
     ↓
MongoDB Implementation
```

This becomes especially useful when the same Django service also uses PostgreSQL.

## Installation: Django MongoDB Backend

The current MongoDB documentation provides an official Django MongoDB Backend package.

```bash
python -m pip install django-mongodb-backend
```

The current getting-started documentation states that the package installs the required PyMongo and Django dependencies for the supported version line. Always verify the current compatibility matrix before pinning versions. ([MongoDB Django MongoDB Backend documentation](https://www.mongodb.com/docs/languages/python/django-mongodb/current/))

For example:

```bash
python -m pip show django-mongodb-backend
python -m pip show django
python -m pip show pymongo
```

Production dependency management should pin compatible versions rather than relying on unconstrained upgrades.

## Version Compatibility

Django, the Django MongoDB Backend, PyMongo, Python, and MongoDB Server versions must be treated as a compatibility set.

```text
Python
  ↓
Django
  ↓
Django MongoDB Backend
  ↓
PyMongo
  ↓
MongoDB Server
```

Before upgrading one component, check the compatibility matrix and run the integration test suite.

This is particularly important because the official backend is currently in Public Preview. ([MongoDB Django MongoDB Backend documentation](https://www.mongodb.com/docs/languages/python/django-mongodb/current/))

## Configuring Django MongoDB Backend

A basic `settings.py` configuration is:

```python
DATABASES = {
    "default": {
        "ENGINE": "django_mongodb_backend",
        "HOST": "mongodb://localhost:27017",
        "NAME": "orders",
    },
}
```

MongoDB's current documentation also supports specifying a complete MongoDB URI in `HOST`. ([MongoDB connection configuration](https://www.mongodb.com/docs/languages/python/django-mongodb/current/connect/))

For production:

```python
import os


DATABASES = {
    "default": {
        "ENGINE": "django_mongodb_backend",
        "HOST": os.environ["MONGODB_URI"],
        "NAME": os.environ["MONGODB_DATABASE"],
    },
}
```

Never commit credentials to `settings.py`.

## Connection URI

A production URI may look like:

```text
mongodb+srv://app_user:password@cluster.example.mongodb.net/?retryWrites=true&w=majority
```

The URI can contain:

- Authentication
- Hosts
- Replica-set configuration
- TLS options
- Retry configuration
- Write concern
- Other driver options

MongoDB's Django backend documentation supports passing a URI through `HOST` and also allows explicit connection options through `OPTIONS`. ([MongoDB connection configuration](https://www.mongodb.com/docs/languages/python/django-mongodb/current/connect/))

## Explicit Connection Options

Configuration can also be expressed separately:

```python
DATABASES = {
    "default": {
        "ENGINE": "django_mongodb_backend",
        "HOST": "mongodb+srv://cluster.example.mongodb.net",
        "NAME": "orders",
        "USER": os.environ["MONGODB_USER"],
        "PASSWORD": os.environ["MONGODB_PASSWORD"],
        "OPTIONS": {
            "retryWrites": True,
            "w": "majority",
        },
    },
}
```

Keep connection options deliberate.

Do not blindly copy connection settings from development into production.

## Secret Management

Production secrets should come from:

- AWS Secrets Manager
- Kubernetes Secrets
- Vault
- Cloud secret stores
- Deployment platform secret configuration

Avoid:

```python
MONGODB_URI = "mongodb+srv://admin:password@..."
```

Prefer:

```python
MONGODB_URI = os.environ["MONGODB_URI"]
```

The application identity should have only the MongoDB privileges it requires.

## Django Models with MongoDB

The official backend allows Django model classes to represent MongoDB collections.

Example:

```python
from django.db import models


class Order(models.Model):
    customer_id = models.CharField(max_length=64)
    status = models.CharField(max_length=32)
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
```

The model represents MongoDB documents rather than relational rows.

MongoDB's current backend documentation provides support for Django fields as well as MongoDB BSON-specific fields. ([MongoDB model documentation](https://www.mongodb.com/docs/languages/python/django-mongodb/current/interact-data/))

## MongoDB Documents Behind Django Models

Conceptually:

```json
{
  "_id": "...",
  "customer_id": "cust-1001",
  "status": "pending",
  "total": 149.99,
  "created_at": "..."
}
```

The exact representation depends on the backend and field definitions.

The important distinction is:

```text
Django Model
     ↓
MongoDB Collection

Model Instance
     ↓
MongoDB Document
```

Do not assume that a Django model automatically gives you relational database semantics.

## ObjectId Primary Keys

MongoDB commonly uses `ObjectId` identifiers.

The official Django MongoDB Backend provides MongoDB-specific project templates and configuration for using `ObjectId` values as model primary keys. ([MongoDB Django MongoDB Backend getting started](https://www.mongodb.com/docs/languages/python/django-mongodb/v5.2/get-started/))

For API responses, convert BSON identifiers into a representation appropriate for the API contract:

```json
{
  "id": "507f1f77bcf86cd799439011"
}
```

Do not expose driver-specific objects directly through JSON APIs.

## BSON Fields

MongoDB supports BSON-specific types that do not map one-to-one to conventional Django fields.

Examples include:

- ObjectId
- Decimal128
- Binary
- Date
- Arrays
- Embedded documents

Use MongoDB-specific field support where it provides a real domain benefit.

Avoid using database-specific types merely because they are available.

## CRUD Operations

The official Django MongoDB Backend provides Django QuerySet-style CRUD operations. ([MongoDB CRUD documentation](https://www.mongodb.com/docs/languages/python/django-mongodb/current/interact-data/crud/))

Create:

```python
order = Order.objects.create(
    customer_id="cust-1001",
    status="pending",
    total=149.99,
)
```

Retrieve:

```python
order = Order.objects.get(
    pk=order_id,
)
```

Filter:

```python
orders = Order.objects.filter(
    customer_id="cust-1001",
    status="pending",
)
```

Update:

```python
Order.objects.filter(
    pk=order_id,
).update(
    status="confirmed",
)
```

Delete:

```python
Order.objects.filter(
    pk=order_id,
).delete()
```

The exact supported QuerySet surface should be checked against the backend version being used.

## QuerySet Evaluation

Django QuerySets are lazy abstractions.

For example:

```python
orders = Order.objects.filter(
    status="pending",
)
```

does not necessarily execute the database operation immediately.

Evaluation can occur when the QuerySet is:

- Iterated
- Converted to a list
- Sliced in ways that require evaluation
- Tested for certain conditions
- Otherwise consumed by application logic

MongoDB's documentation explicitly describes Django MongoDB Backend QuerySets as lazy until evaluated. ([MongoDB query documentation](https://www.mongodb.com/docs/languages/python/django-mongodb/current/interact-data/specify-a-query/))

This matters because seemingly harmless code can trigger database operations.

## Filtering

```python
orders = Order.objects.filter(
    status="pending",
    customer_id=customer_id,
)
```

The backend translates supported Django query expressions into MongoDB operations.

Always understand the resulting MongoDB query when performance matters.

The abstraction should make application code maintainable, not prevent engineers from analyzing database behavior.

## Query Composition

```python
queryset = Order.objects.filter(
    status="pending",
)

if customer_id:
    queryset = queryset.filter(
        customer_id=customer_id,
    )

orders = queryset.order_by(
    "-created_at",
)
```

This style is useful for building controlled API filters.

Do not allow arbitrary user-provided field names and operators to become unrestricted database queries.

## Query Selectivity

A query such as:

```python
Order.objects.filter(
    customer_id=customer_id,
    status="pending",
)
```

should have indexes designed around actual access patterns.

For example, a candidate index may involve:

```text
customer_id
status
created_at
```

Index design should be validated against real query patterns and MongoDB execution plans.

## Indexes

The official Django MongoDB Backend supports defining indexes through Django model metadata. ([MongoDB index documentation](https://www.mongodb.com/docs/languages/python/django-mongodb/current/model-data/))

Example:

```python
class Order(models.Model):
    customer_id = models.CharField(max_length=64)
    status = models.CharField(max_length=32)
    created_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(
                fields=[
                    "customer_id",
                    "status",
                    "-created_at",
                ],
                name="order_customer_status_created",
            ),
        ]
```

The index should correspond to actual access patterns rather than being created simply because a field exists.

## Compound Indexes

Suppose the API frequently performs:

```text
customer_id = X
status = pending
sort by created_at DESC
```

A candidate compound index is:

```text
customer_id ASC
status ASC
created_at DESC
```

The exact index should be validated with `explain()`.

Consider:

- Equality fields
- Sort fields
- Selectivity
- Cardinality
- Write frequency
- Index size
- Query frequency

## MongoDB-Specific Querying

The Django abstraction should not be treated as a replacement for MongoDB knowledge.

The official backend provides mechanisms for MongoDB-specific queries and raw database access, including aggregation pipelines and PyMongo operations. ([MongoDB data interaction documentation](https://www.mongodb.com/docs/languages/python/django-mongodb/current/interact-data/))

For example, a complex aggregation may be clearer using MongoDB's native pipeline syntax.

Conceptually:

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
            "total": {
                "$sum": "$total",
            },
        }
    },
]
```

Do not force a complex MongoDB operation through a Django QuerySet abstraction if the result is harder to understand or optimize.

## Aggregation

Aggregation is particularly useful for:

- Reporting
- Analytics
- Grouping
- Data transformation
- Calculated results
- Complex filtering
- `$lookup`
- `$unwind`
- `$facet`

A typical service architecture is:

```text
Django View
    ↓
Service
    ↓
Reporting Repository
    ↓
MongoDB Aggregation
```

Avoid embedding large aggregation pipelines directly inside views.

## Aggregation Performance

Prefer early filtering:

```text
Collection
    ↓
$match
    ↓
$project
    ↓
$group
    ↓
$sort
```

rather than processing the entire collection before filtering.

Monitor:

- Execution time
- Documents examined
- Index usage
- Memory consumption
- Result size

Large reports should generally run outside the request/response path.

## Embedded Documents

MongoDB encourages modeling around access patterns.

An order may embed line items:

```json
{
  "_id": "...",
  "customer_id": "cust-1001",
  "items": [
    {
      "product_id": "prod-1",
      "quantity": 2
    },
    {
      "product_id": "prod-2",
      "quantity": 1
    }
  ]
}
```

Embedding is useful when:

- Child data belongs to the parent
- Child cardinality is bounded
- Data is usually read together
- Atomic updates are useful

The official Django MongoDB Backend documentation covers embedding, referencing, and denormalization as MongoDB modeling strategies. ([MongoDB model relationships documentation](https://www.mongodb.com/docs/languages/python/django-mongodb/current/model-data/))

## References

A relational Django mindset often leads developers to normalize everything.

MongoDB may instead favor:

```text
Order
 ├── customer_id
 └── items[]
```

rather than:

```text
Order
Customer
OrderItem
Product
```

with every relationship resolved through separate queries.

Reference data when:

- The entity has an independent lifecycle
- It is queried independently
- Cardinality is large
- Duplication is undesirable
- Document growth would become problematic

## Denormalization

MongoDB often benefits from controlled duplication.

For example:

```json
{
  "_id": "...",
  "customer": {
    "id": "cust-1001",
    "name": "Aranya"
  }
}
```

The customer name may be duplicated into orders if the order requires historical display data.

This creates a deliberate trade-off:

```text
Fewer reads
    vs
More update complexity
```

Denormalization should be intentional and documented.

## Schema Evolution

Django migrations are not automatically equivalent to relational `ALTER TABLE` operations.

For example, changing:

```python
status = models.CharField(max_length=32)
```

to:

```python
status = models.CharField(
    max_length=32,
    default="pending",
)
```

does not mean that every historical MongoDB document has necessarily been transformed into the desired physical representation.

Production schema evolution should consider:

- Existing documents
- Missing fields
- Old field names
- Old data types
- Backfill strategy
- Application compatibility
- Rollback strategy

## Expand-and-Contract Schema Changes

A safer deployment pattern is:

```text
Deploy reader supporting old + new
        ↓
Deploy writer producing new format
        ↓
Backfill historical documents
        ↓
Verify migration
        ↓
Remove old reader behavior
```

This is especially useful for high-volume production systems.

## Migrations

MongoDB does not behave like PostgreSQL migrations.

The official Django MongoDB Backend includes MongoDB-specific migration support, but migration behavior and supported features should be verified against the exact backend version. ([MongoDB Django MongoDB Backend documentation](https://www.mongodb.com/docs/languages/python/django-mongodb/current/))

Do not assume every relational Django migration operation has an equivalent MongoDB implementation.

Treat data migrations and application migrations as separate engineering concerns when necessary.

## Transactions

MongoDB supports multi-document transactions, and the official Django MongoDB Backend provides transaction/session support. ([MongoDB transaction documentation](https://www.mongodb.com/docs/languages/python/django-mongodb/current/interact-data/transactions/))

A transaction boundary should generally live in a service layer:

```python
from django.db import transaction


def confirm_order(order_id):
    with transaction.atomic():
        order = Order.objects.get(pk=order_id)

        order.status = "confirmed"
        order.save()

        # Additional transactional database operations.
```

The exact behavior and supported transaction semantics should be validated against the backend version.

## When to Use Transactions

Use transactions when multiple document operations must satisfy one atomic business invariant.

Example:

```text
Create payment record
        +
Update order status
        +
Create accounting record
```

If these operations must either all succeed or all fail, a transaction may be appropriate.

## When Not to Use Transactions

Do not use transactions merely because the application is using MongoDB.

If a single document can contain the necessary state:

```text
Order
 ├── status
 ├── payment
 └── items
```

a single-document atomic update may be simpler and more efficient.

MongoDB's document model often allows data to be modeled so that fewer cross-document transactions are required.

## Django Transactions vs Relational Transactions

Django developers coming from PostgreSQL may assume transactions should surround every business operation.

MongoDB encourages a different question:

```text
Can the invariant be represented inside one document?
```

If yes:

```text
Single-document atomic operation
```

may be preferable to:

```text
Multi-document transaction
```

This is a data-modeling decision, not simply a transaction API decision.

## Django REST Framework

Django REST Framework can sit above MongoDB:

```text
HTTP
 ↓
DRF
 ↓
Serializer
 ↓
Service
 ↓
Repository
 ↓
MongoDB
```

The serializer should own API validation, not database-specific persistence behavior.

Example:

```python
from rest_framework import serializers


class OrderSerializer(serializers.Serializer):
    customer_id = serializers.CharField()
    status = serializers.CharField()
    total = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
```

Then:

```text
Serializer
    ↓
validated_data
    ↓
Service
    ↓
Repository
```

This separation makes MongoDB changes easier to manage.

## DRF View Architecture

Avoid putting complex MongoDB logic into views:

```python
class OrderView(APIView):
    def get(self, request):
        # 100 lines of MongoDB queries
        ...
```

Prefer:

```python
class OrderView(APIView):
    def get(self, request):
        orders = order_service.list_orders(
            customer_id=request.user.customer_id,
        )

        return Response(
            OrderSerializer(
                orders,
                many=True,
            ).data
        )
```

The view should coordinate HTTP concerns, not become the persistence layer.

## Repository Pattern

A repository can hide whether the implementation uses MongoEngine, Django MongoDB Backend, or PyMongo.

```python
class OrderRepository:
    def get_by_id(self, order_id):
        return Order.objects.get(
            pk=order_id,
        )

    def list_pending(self, customer_id):
        return Order.objects.filter(
            customer_id=customer_id,
            status="pending",
        )
```

For a PyMongo implementation:

```python
class OrderRepository:
    def __init__(self, collection):
        self.collection = collection

    def get_by_id(self, order_id):
        return self.collection.find_one(
            {"_id": order_id}
        )
```

The service layer should not care which implementation is used.

## MongoEngine with Django

MongoEngine is useful when document-oriented modeling is the primary requirement.

Example:

```python
from mongoengine import (
    Document,
    StringField,
    FloatField,
)


class Order(Document):
    customer_id = StringField(required=True)
    status = StringField(required=True)
    total = FloatField(required=True)

    meta = {
        "collection": "orders",
    }
```

The architecture becomes:

```text
Django
  ↓
View / DRF
  ↓
Service
  ↓
MongoEngine
  ↓
PyMongo
  ↓
MongoDB
```

MongoEngine's documentation provides a dedicated Django integration section. ([MongoEngine documentation](https://docs.mongoengine.org/))

## MongoEngine vs Django MongoDB Backend

| Concern | Django MongoDB Backend | MongoEngine |
|---|---|---|
| Model abstraction | Django models | MongoEngine documents |
| Query API | Django QuerySet | MongoEngine QuerySet |
| Django ORM integration | Native integration layer | Separate ODM |
| MongoDB document semantics | Supported | Explicit |
| Django ecosystem alignment | Higher | Lower |
| ODM-specific features | Backend-specific | Strong |
| PyMongo foundation | Yes | Yes |
| Current status | Official, Public Preview | Third-party |
| Migration strategy | Django/MongoDB-specific | ODM/application-controlled |

Do not mix both model systems casually within the same bounded context.

## Direct PyMongo with Django

Direct PyMongo is often appropriate for specialized functionality.

Example:

```python
from pymongo import MongoClient


client = MongoClient(
    settings.MONGODB_URI,
)

db = client[settings.MONGODB_DATABASE]
orders = db["orders"]
```

A repository can then provide controlled access:

```python
class OrderRepository:
    def __init__(self, collection):
        self.collection = collection

    def find_pending(self, customer_id):
        return self.collection.find(
            {
                "customer_id": customer_id,
                "status": "pending",
            }
        )
```

Do not create a new MongoDB client for every request.

## Connection Pooling with PyMongo

A long-lived `MongoClient` maintains connection pools and topology information.

Architecture:

```text
Django Process
     ↓
MongoClient
     ↓
Connection Pool
     ↓
MongoDB
```

If the Django deployment runs:

```text
10 application processes
```

each process can have its own client and pool.

Capacity planning must therefore consider:

```text
application processes
×
connection pool capacity
```

## Async Django Considerations

Django has increasing asynchronous support, but the persistence layer must also be compatible with the application's execution model.

Do not assume that wrapping synchronous PyMongo in:

```python
async def view(...):
    ...
```

makes the database operation asynchronous.

A synchronous MongoDB driver still performs blocking I/O.

For async MongoDB applications, evaluate the current PyMongo async API and the exact Django integration being used.

## Background Tasks

Long-running MongoDB operations should not block ordinary web requests.

Use:

```text
Django
  ↓
Celery
  ↓
MongoDB
```

for workloads such as:

- Large exports
- Data migrations
- Bulk updates
- Report generation
- Reconciliation
- Batch processing

Example:

```python
from celery import shared_task


@shared_task
def rebuild_customer_summary(customer_id):
    # Perform bounded MongoDB processing.
    ...
```

The task should be:

- Idempotent
- Retry-aware
- Observable
- Bounded
- Safe for partial failure

## Redis with Django and MongoDB

Redis can provide caching:

```text
Django
  ↓
Redis
  ↓ cache miss
MongoDB
```

Example use cases:

- Frequently requested documents
- Session-related data
- Expensive aggregates
- Rate limiting
- Short-lived application state

Do not use Redis to compensate for poor MongoDB query design.

First optimize:

```text
Schema
→ Query
→ Index
→ Database capacity
```

Then introduce caching where the access pattern justifies it.

## Celery and MongoDB

Celery can be used for asynchronous MongoDB workloads.

Architecture:

```text
Django Request
      ↓
Create Job
      ↓
Celery
      ↓
MongoDB
      ↓
Store Result
```

Use Celery for workloads that exceed normal HTTP latency budgets.

Do not make the request wait for a large aggregation simply because the aggregation is technically executable from Django.

## Kafka and MongoDB

For event-driven architectures:

```text
Django
   ↓
MongoDB
   ↓
Change Stream / Outbox
   ↓
Kafka
   ↓
Consumers
```

Do not assume that a MongoDB write and Kafka publish are one atomic operation.

For reliable event publication, use an explicit consistency pattern.

## Change Streams

MongoDB change streams can be used when the deployment supports them.

A Django service can have a separate worker process:

```text
Django Web
    │
    └── API traffic

Worker
    ↓
MongoDB Change Stream
    ↓
Kafka / downstream systems
```

Do not run an infinite change-stream loop inside a normal Django request.

Consumers should handle:

- Resume tokens
- Disconnects
- Retries
- Duplicate delivery
- Idempotency
- Backpressure

## Query Performance

Django abstractions do not remove the need for MongoDB performance engineering.

For a slow query:

```text
Slow Django endpoint
       ↓
Identify QuerySet / repository
       ↓
Identify MongoDB query
       ↓
Run explain()
       ↓
Check COLLSCAN / IXSCAN
       ↓
Check totalDocsExamined
       ↓
Check totalKeysExamined
       ↓
Review index
       ↓
Benchmark
```

A QuerySet that looks elegant in Python can still generate an inefficient database operation.

## N+1 Query Problems

Reference-heavy designs can create:

```text
1 query
+
N related-document queries
```

For example:

```text
GET /orders
    ↓
100 orders
    ↓
100 customer queries
```

Mitigate through:

- Embedding
- Denormalization
- Batch loading
- Aggregation
- Explicit repository methods

Do not assume Django-like relation abstractions automatically eliminate MongoDB N+1 behavior.

## Pagination

Avoid unbounded endpoints:

```python
Order.objects.all()
```

For APIs, enforce:

- Maximum page size
- Default page size
- Stable ordering
- Indexed pagination

Offset pagination:

```python
orders = (
    Order.objects
    .filter(status="pending")
    .order_by("-created_at")
)[offset:offset + page_size]
```

For large datasets, cursor-based pagination is usually preferable.

A cursor can be based on:

```text
created_at + _id
```

to provide deterministic ordering.

## Large Documents

Large MongoDB documents can increase:

- Network payload
- BSON decoding
- Python memory
- Serialization cost
- Database I/O

Do not put unbounded child arrays inside a single document.

For high-cardinality data:

```text
Parent document
     +
Separate child collection
```

may be more appropriate.

## API Serialization

Do not expose internal MongoDB documents directly.

Use a serializer:

```python
class OrderSerializer(serializers.Serializer):
    id = serializers.CharField(source="pk")
    customer_id = serializers.CharField()
    status = serializers.CharField()
    total = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
```

This provides a stable API contract even when the persistence representation changes.

## Security

Django authentication and MongoDB authentication are different layers.

```text
End User
   ↓
Django Authentication
   ↓
Django Authorization
   ↓
Service
   ↓
MongoDB Application Identity
   ↓
MongoDB Authorization
```

A user's permission to view an order should not be confused with the MongoDB user's database permissions.

## MongoDB Least Privilege

The Django service should use a dedicated MongoDB identity.

Avoid:

```text
Django
  ↓
MongoDB admin
```

Prefer:

```text
Django
  ↓
orders_service_user
  ↓
orders database
```

Grant only the permissions required by the service.

## TLS

Production MongoDB connections should use TLS according to the deployment's security requirements.

Do not disable certificate verification to bypass connectivity problems.

Investigate:

- Certificate chain
- Hostname
- CA configuration
- Server configuration
- Network path
- Driver configuration

rather than using insecure TLS options.

## Query Injection

Never allow clients to submit arbitrary MongoDB query operators.

Bad:

```json
{
  "filter": {
    "$where": "..."
  }
}
```

Prefer an explicit filter contract:

```python
ALLOWED_STATUS = {
    "pending",
    "confirmed",
    "cancelled",
}


def build_order_filters(status=None):
    filters = {}

    if status:
        if status not in ALLOWED_STATUS:
            raise ValueError("Invalid status")

        filters["status"] = status

    return filters
```

Treat database filters as application code, not arbitrary user data.

## Multi-Tenant Security

For a multi-tenant Django application:

```python
orders = Order.objects.filter(
    tenant_id=request.user.tenant_id,
    status="pending",
)
```

The tenant boundary should be enforced consistently.

Do not rely on frontend-provided tenant IDs.

Prefer:

```text
Authenticated identity
      ↓
Server-derived tenant context
      ↓
Repository filter
      ↓
MongoDB
```

## Auditing

For sensitive applications, audit:

- Authentication events
- Authorization changes
- Administrative operations
- Data mutations
- Configuration changes
- Privilege changes

Do not store sensitive document contents in application logs merely for debugging.

Use structured audit records with appropriate retention and access controls.

## Django Admin

The official Django MongoDB Backend provides Django integration capabilities that include Django Admin-related workflows. ([MongoDB Django MongoDB Backend documentation](https://www.mongodb.com/docs/languages/python/django-mongodb/current/))

However, do not assume that every Django Admin feature behaves identically to PostgreSQL-backed applications.

For production administration:

- Restrict admin access
- Use strong authentication
- Enforce least privilege
- Audit administrative changes
- Test custom admin actions
- Avoid exposing destructive operations unnecessarily

## Testing Strategy

Use multiple test levels.

### Unit Tests

Test services independently:

```text
Service
  ↓
Mock Repository
```

Example:

```python
def test_confirm_order(repository):
    service = OrderService(repository)

    result = service.confirm("order-1")

    assert result.status == "confirmed"
```

### Integration Tests

Use a real MongoDB deployment for persistence tests:

```text
Django
  ↓
Repository
  ↓
MongoDB
```

Test:

- Queries
- Indexes
- Constraints
- Transactions
- Aggregation
- BSON types
- Schema behavior

### API Tests

Test:

```text
HTTP request
   ↓
Django
   ↓
Service
   ↓
MongoDB
   ↓
HTTP response
```

Verify:

- Status codes
- Response schema
- Authorization
- Pagination
- Error handling

## Transaction Testing

If production requires transactions, test against a MongoDB topology that supports the transaction behavior being used.

Do not validate transaction-heavy code only against an oversimplified local setup.

Test:

- Commit
- Rollback
- Timeout
- Retry
- Concurrent updates
- Duplicate operations

## Test Isolation

Never run tests against a production database.

Prefer:

```text
CI
 ↓
Dedicated MongoDB
 ↓
Test Database
```

For parallel test execution:

```text
worker-1 → test_db_1
worker-2 → test_db_2
worker-3 → test_db_3
```

or use isolated collections and reliable cleanup.

## Production Monitoring

Monitor both Django and MongoDB.

### Django Metrics

Track:

- Request rate
- p50 latency
- p95 latency
- p99 latency
- Error rate
- Database operation latency
- Celery queue depth
- Worker failures

### MongoDB Metrics

Track:

- Query latency
- Slow operations
- Connections
- CPU
- Memory
- Storage
- Replication lag
- Index usage
- Working-set behavior

The application should expose enough telemetry to connect:

```text
HTTP request
    ↓
Django view
    ↓
Service
    ↓
MongoDB operation
```

## Logging

Use structured logs:

```python
import logging


logger = logging.getLogger(__name__)


logger.info(
    "order_created",
    extra={
        "order_id": str(order.pk),
        "customer_id": customer_id,
    },
)
```

Never log:

- MongoDB passwords
- Full connection strings
- Access tokens
- Private keys
- Sensitive customer documents

Use correlation IDs to connect Django requests with background jobs and database operations.

## Health Checks

Separate liveness from readiness.

### Liveness

```python
def liveness(request):
    return JsonResponse(
        {"status": "ok"}
    )
```

Liveness should generally answer whether the Django process is alive.

### Readiness

Readiness can verify required dependencies.

For a MongoDB-backed service:

```text
Readiness
   ↓
MongoDB connectivity
   ↓
Application ready
```

Do not make liveness depend on MongoDB availability, otherwise a database outage can cause Kubernetes to restart healthy application processes unnecessarily.

## Deployment

A typical architecture:

```mermaid
flowchart LR
    Client[Clients] --> Nginx[Nginx / Load Balancer]
    Nginx --> Django1[Django Instance]
    Nginx --> Django2[Django Instance]
    Nginx --> DjangoN[Django Instance]

    Django1 --> Mongo[(MongoDB)]
    Django2 --> Mongo
    DjangoN --> Mongo

    Django1 --> Redis[(Redis)]
    Django2 --> Redis
    DjangoN --> Redis

    Worker[Celery Workers] --> Mongo
    Worker --> Redis
```

MongoDB can be deployed as:

- MongoDB Atlas
- Managed MongoDB service
- Replica set
- Development Docker container

The Django deployment and MongoDB deployment should have independent scaling and failure domains.

## Docker Development

A development-only MongoDB service can be run through Docker Compose:

```yaml
services:
  mongodb:
    image: mongo:8
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

volumes:
  mongodb_data:
```

Do not treat this configuration as a production deployment.

Production MongoDB requires deliberate configuration for:

- Authentication
- TLS
- Storage
- Backups
- Replica sets
- Monitoring
- Network security
- Capacity
- Recovery

## Environment Configuration

Use environment variables:

```python
import os


MONGODB_URI = os.environ["MONGODB_URI"]
MONGODB_DATABASE = os.environ["MONGODB_DATABASE"]
```

For local development:

```text
.env
```

For production:

```text
Secret Manager
      ↓
Deployment system
      ↓
Environment
      ↓
Django
```

Keep environment-specific configuration outside source code.

## Kubernetes

A Kubernetes deployment should consider:

```text
Django Pods
    ↓
MongoDB Connection Pools
    ↓
MongoDB
```

If the deployment scales from:

```text
5 pods
```

to:

```text
50 pods
```

database connection pressure can increase substantially.

Therefore, application scaling must be coordinated with MongoDB capacity.

## Graceful Shutdown

Django processes should terminate gracefully so that:

- active requests can finish
- background tasks are not duplicated unexpectedly
- database connections can close cleanly
- load balancers stop routing traffic before termination

Kubernetes termination configuration should be tested rather than assumed to be correct.

## Backups and Recovery

Django does not change MongoDB's backup requirements.

Production MongoDB should have:

- Automated backups
- Defined retention
- Restore procedures
- Recovery testing
- RPO
- RTO
- Disaster recovery documentation

A production runbook should define:

```text
Failure
  ↓
Identify affected service
  ↓
Protect remaining data
  ↓
Determine recovery point
  ↓
Restore MongoDB
  ↓
Validate data
  ↓
Reconnect Django
  ↓
Run application smoke tests
  ↓
Resume traffic
```

## Schema Migration Runbook

For a large schema change:

```text
Identify old schema
        ↓
Design backward-compatible representation
        ↓
Deploy reader supporting both
        ↓
Deploy writer for new format
        ↓
Backfill documents
        ↓
Validate counts and samples
        ↓
Monitor production
        ↓
Remove old representation
```

Do not combine a large data migration with an unrelated application deployment unless there is a strong operational reason.

## Troubleshooting

### Django Cannot Connect to MongoDB

```text
Symptom
↓
Django fails during startup or database access
↓
Possible causes
    - Invalid URI
    - Incorrect credentials
    - DNS failure
    - Network restriction
    - TLS failure
    - MongoDB unavailable
    - Unsupported backend/driver version
↓
Isolation strategy
↓
Check Django settings
↓
Verify environment variables
↓
Test URI with mongosh
↓
Check DNS/network path
↓
Check MongoDB authentication
↓
Check TLS
↓
Check package compatibility
↓
Root cause
↓
Corrective action
↓
Prevention
    - Dependency pinning
    - Deployment smoke tests
    - Secret validation
    - Monitoring
```

### Query Is Slow

```text
Symptom
↓
Django endpoint has high latency
↓
Possible causes
    - Missing index
    - Poor compound index
    - Large result set
    - Inefficient QuerySet
    - N+1 access
    - Expensive aggregation
↓
Isolation strategy
↓
Identify endpoint
↓
Identify QuerySet / repository
↓
Inspect MongoDB query
↓
Run explain()
↓
Inspect IXSCAN / COLLSCAN
↓
Check totalDocsExamined
↓
Check totalKeysExamined
↓
Root cause
↓
Corrective action
    - Rewrite query
    - Add/change index
    - Reduce result size
    - Batch related reads
↓
Prevention
    - Query review
    - Performance testing
    - Slow-query monitoring
```

### Unexpected N+1 Queries

```text
Symptom
↓
One Django request generates many MongoDB operations
↓
Possible causes
    - References
    - Per-object lookups
    - Serializer-driven queries
    - Poor repository design
↓
Isolation strategy
↓
Measure database operations per request
↓
Inspect serializer/service behavior
↓
Identify repeated queries
↓
Root cause
↓
Corrective action
    - Embed data
    - Batch queries
    - Aggregate
    - Denormalize
↓
Prevention
    - Query-count tests
    - Repository review
    - Performance dashboards
```

### Transaction Failure

```text
Symptom
↓
Multi-document operation fails or rolls back
↓
Possible causes
    - Unsupported topology
    - Transaction timeout
    - Write conflict
    - Network interruption
    - Invalid transaction usage
↓
Isolation strategy
↓
Check MongoDB deployment topology
↓
Inspect application logs
↓
Inspect transaction boundaries
↓
Check retry behavior
↓
Root cause
↓
Corrective action
    - Fix transaction boundary
    - Retry safely
    - Redesign data model
↓
Prevention
    - Replica-set integration tests
    - Failure-injection tests
    - Idempotent operations
```

### Duplicate Records After Retry

```text
Symptom
↓
Same business operation creates multiple documents
↓
Possible causes
    - HTTP retry
    - Worker retry
    - Timeout after successful write
    - Missing unique constraint
↓
Isolation strategy
↓
Inspect request/job identifiers
↓
Inspect indexes
↓
Inspect retry behavior
↓
Root cause
↓
Corrective action
    - Add idempotency key
    - Add unique index
    - Use atomic upsert
↓
Prevention
    - Idempotent API design
    - Retry testing
    - Failure-injection testing
```

## Production Pitfalls

### Treating MongoDB Like PostgreSQL

Bad design:

```text
Normalize everything
      ↓
Create many collections
      ↓
Resolve relationships for every request
      ↓
Use transactions everywhere
```

MongoDB often benefits from:

```text
Access-pattern-driven modeling
      ↓
Embedding
      ↓
Controlled denormalization
      ↓
Targeted indexes
```

### Assuming Django ORM Means SQL

With the official backend, Django QuerySet syntax can represent MongoDB operations, but the underlying database remains MongoDB.

Always understand:

```text
Django QuerySet
      ↓
Backend translation
      ↓
MongoDB operation
```

### Using Unsupported Django Features Without Verification

Django features designed for relational databases may not have identical semantics across MongoDB integrations.

Verify compatibility before relying on:

- Specialized relational fields
- Complex relational operations
- Migration operations
- Database constraints
- Locking behavior
- Advanced ORM features

### Mixing Persistence Abstractions Everywhere

Avoid:

```text
View → Django MongoDB Backend
Service → MongoEngine
Task → PyMongo
Serializer → Direct MongoDB
```

with no architectural boundary.

This creates:

- duplicated query logic
- inconsistent models
- difficult testing
- unpredictable transaction ownership

Use a defined persistence boundary.

## MongoEngine vs Official Backend vs PyMongo

A useful decision framework:

```text
Do you need Django's database abstraction?
        │
        ├── Yes
        │    ↓
        │  Evaluate Django MongoDB Backend
        │
        └── No
             ↓
       Do you want document models?
             │
             ├── Yes → Evaluate MongoEngine
             │
             └── No → Use PyMongo
```

For each option, validate:

- Version compatibility
- MongoDB feature coverage
- Query requirements
- Transactions
- Aggregation
- Performance
- Async requirements
- Migration behavior
- Operational maturity
- Team familiarity

## Interview Considerations

### Does Django natively support MongoDB?

Django itself historically did not provide official NoSQL database support. MongoDB now provides an official Django MongoDB Backend separately from Django core. The backend is currently Public Preview. ([MongoDB Django MongoDB Backend documentation](https://www.mongodb.com/docs/languages/python/django-mongodb/current/))

### What is the difference between MongoEngine and Django MongoDB Backend?

MongoEngine is a third-party ODM that provides its own document model and QuerySet abstraction.

Django MongoDB Backend is a Django database backend that integrates MongoDB into Django's model/database abstraction.

```text
MongoEngine:
Django → MongoEngine → PyMongo → MongoDB

Django MongoDB Backend:
Django → Django MongoDB Backend → PyMongo → MongoDB
```

### Should MongoDB be treated like PostgreSQL inside Django?

No.

The framework integration may provide familiar Django APIs, but the database still has:

- Document-oriented modeling
- MongoDB indexes
- Aggregation
- BSON types
- Replica-set behavior
- MongoDB transaction semantics
- MongoDB-specific query planning

### When would you use PyMongo instead?

Use PyMongo when you need direct control over:

- Aggregation
- Bulk writes
- Transactions
- Change streams
- MongoDB-specific features
- Performance-sensitive queries
- Driver-level configuration

### Should all Django models be moved to MongoDB?

No.

A Django application can use different persistence systems for different bounded contexts when there is a clear architectural reason.

For example:

```text
PostgreSQL
    ↓
Users
Billing
Permissions

MongoDB
    ↓
Activity Events
Catalog Documents
Flexible Metadata
```

Do not introduce multiple databases without considering consistency, operational complexity, and ownership.

### How should you model relationships?

Start with access patterns.

Ask:

```text
Are these documents normally read together?
        ↓
Embed

Does the related entity have an independent lifecycle?
        ↓
Reference

Would duplication improve read performance?
        ↓
Consider denormalization
```

### How do you optimize a slow Django MongoDB query?

Do not optimize only the Django code.

Use:

```text
Django endpoint
    ↓
QuerySet / repository
    ↓
MongoDB query
    ↓
explain()
    ↓
Index
    ↓
Execution statistics
    ↓
Benchmark
```

### How do you handle large MongoDB reports in Django?

Move them outside the synchronous request path:

```text
HTTP request
    ↓
Create report job
    ↓
Celery
    ↓
MongoDB aggregation
    ↓
Store result
    ↓
Client retrieves result
```

### How do you prevent MongoDB retries from creating duplicate data?

Use:

- Idempotency keys
- Unique indexes
- Atomic upserts
- Explicit operation identifiers
- Safe retry logic

The database constraint should enforce the invariant where possible.

## Production Checklist

### Architecture

- [ ] MongoDB integration choice is documented
- [ ] Persistence boundary is explicit
- [ ] Business logic is separated from database access
- [ ] MongoDB-specific operations are isolated
- [ ] Integration version compatibility is verified

### Data Modeling

- [ ] Access patterns drive document design
- [ ] Embedding vs referencing is deliberate
- [ ] Document growth is bounded
- [ ] High-cardinality arrays are controlled
- [ ] Denormalization is intentional
- [ ] Schema evolution has a migration strategy

### Queries

- [ ] Query filters are controlled
- [ ] API result sizes are bounded
- [ ] Pagination is implemented
- [ ] Large queries use projections where appropriate
- [ ] Slow queries are explain-analyzed
- [ ] N+1 access patterns are monitored

### Indexes

- [ ] Critical query paths have appropriate indexes
- [ ] Compound indexes reflect access patterns
- [ ] Unique constraints use database indexes
- [ ] Index size is monitored
- [ ] Write overhead is considered
- [ ] Unused indexes are reviewed

### Transactions

- [ ] Transaction boundaries are explicit
- [ ] Transactions are used only when required
- [ ] Transaction topology requirements are tested
- [ ] Retry behavior is understood
- [ ] Operations are idempotent where necessary

### Security

- [ ] Dedicated MongoDB user is used
- [ ] Least privilege is enforced
- [ ] TLS is configured
- [ ] Credentials are externalized
- [ ] MongoDB URIs are not logged
- [ ] API authorization is separate from database authorization
- [ ] Tenant isolation is enforced where required

### Operations

- [ ] MongoDB health is monitored
- [ ] Django database latency is monitored
- [ ] Slow queries are observable
- [ ] Replication health is monitored
- [ ] Storage growth is tracked
- [ ] Backups are configured
- [ ] Restore procedures are tested
- [ ] RPO and RTO are documented

### Deployment

- [ ] Development MongoDB is isolated from production
- [ ] Production configuration is externalized
- [ ] Dependencies are pinned
- [ ] Compatibility is tested before upgrades
- [ ] Kubernetes probes are configured correctly
- [ ] Connection capacity is considered when scaling Django
- [ ] Graceful shutdown is tested

## Key Takeaways

- **Django and MongoDB require an explicit architectural decision: use the official Django MongoDB Backend, MongoEngine, or direct PyMongo based on framework integration, MongoDB-specific requirements, and operational needs.**
- **MongoDB must still be modeled as a document database even when Django provides a familiar model and QuerySet abstraction; embedding, referencing, denormalization, indexes, and aggregation remain MongoDB engineering decisions.**
- **Keep MongoDB persistence behind repositories or service boundaries, especially when using DRF, Celery, Redis, Kafka, or multiple database technologies in the same Django system.**
- **Production performance depends on MongoDB query shapes and indexes rather than Django syntax alone; use `explain()`, bounded pagination, projection, controlled queries, and N+1 detection to diagnose real bottlenecks.**
- **Treat MongoDB security, transactions, schema evolution, backups, version compatibility, and recovery as independent production concerns; do not assume Django abstractions provide relational database semantics or operational guarantees.**