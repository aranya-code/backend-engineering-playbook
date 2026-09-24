# 08- CRUD Operations

## Overview

CRUD represents the four fundamental data operations:

| Operation | MongoDB operation | Typical purpose |
|---|---|---|
| Create | `insertOne()`, `insertMany()` | Add documents |
| Read | `find()`, `findOne()` | Retrieve documents |
| Update | `updateOne()`, `updateMany()`, `replaceOne()` | Modify documents |
| Delete | `deleteOne()`, `deleteMany()` | Remove documents |

MongoDB CRUD is document-oriented rather than row-oriented. Queries operate on BSON documents, and updates can modify nested fields and array elements without requiring the entire document to be replaced.

For backend systems, CRUD design is more than knowing MongoDB commands. The important engineering questions are:

- What is the access pattern?
- Which fields should be indexed?
- Is the operation atomic?
- Is the update idempotent?
- Can the document grow without bounds?
- What happens under concurrent writes?
- What consistency guarantees are required?
- How should pagination work at scale?
- How should failures and retries behave?

A typical request path looks like:

```text
Client
  |
  v
Nginx / API Gateway
  |
  v
FastAPI / Django
  |
  v
Service Layer
  |
  v
Repository
  |
  v
PyMongo / MongoDB Driver
  |
  v
MongoDB
```

The CRUD operation should be designed around the application's access patterns rather than around individual MongoDB commands.

## MongoDB CRUD Model

MongoDB stores documents inside collections.

Example:

```json
{
  "_id": "ObjectId(...)",
  "customer_id": "CUS-1001",
  "status": "confirmed",
  "total": 1499.50,
  "items": [
    {
      "product_id": "PRD-1001",
      "quantity": 2
    }
  ],
  "created_at": "2026-09-21T10:00:00Z"
}
```

CRUD operations work against the document as a whole or against selected fields.

MongoDB provides atomicity at the individual-document level. A single-document update either succeeds according to MongoDB's write semantics or fails; MongoDB does not expose a partially updated document to other operations.

Multi-document atomicity requires transactions and should be introduced only when the business operation actually spans multiple documents.

## Create Operations

### Insert One

`insertOne()` creates a single document.

```javascript
db.users.insertOne({
  name: "Alice",
  email: "alice@example.com",
  status: "active",
  created_at: new Date()
})
```

MongoDB generates an `_id` if one is not supplied.

A successful result contains an inserted identifier:

```javascript
{
  acknowledged: true,
  insertedId: ObjectId("...")
}
```

### When to Use

Use `insertOne()` when:

- A single domain object is being created.
- The request corresponds to one logical write.
- The application needs the generated identifier.
- The write should be independently observable.

### Production Considerations

Validate data before writing, but also consider collection-level schema validation for important storage invariants.

Do not blindly accept client-provided `_id` values unless the identifier strategy is intentional.

---

## Insert Many

`insertMany()` creates multiple documents.

```javascript
db.users.insertMany([
  {
    name: "Alice",
    email: "alice@example.com"
  },
  {
    name: "Bob",
    email: "bob@example.com"
  }
])
```

Use it for:

- Batch ingestion
- ETL workloads
- Data migration
- Bulk imports
- Background processing

For high-throughput workloads, batching is generally preferable to issuing thousands of individual network requests.

### Ordered vs Unordered Inserts

By default, bulk insertion is ordered.

```javascript
db.users.insertMany(
  documents,
  { ordered: true }
)
```

With:

```javascript
{ ordered: false }
```

MongoDB can continue processing other operations after an individual failure.

```javascript
db.users.insertMany(
  documents,
  { ordered: false }
)
```

Unordered writes can improve throughput when individual documents are independent.

Use them carefully when application-level ordering matters.

---

## Write Results

CRUD APIs return metadata describing the operation.

Typical information includes:

- Whether the operation was acknowledged
- Inserted identifier
- Number of matched documents
- Number of modified documents
- Number of deleted documents
- Upserted identifier

For example:

```javascript
const result = db.users.updateOne(
  { email: "alice@example.com" },
  {
    $set: {
      status: "inactive"
    }
  }
)

result
```

A result might conceptually contain:

```javascript
{
  acknowledged: true,
  matchedCount: 1,
  modifiedCount: 1
}
```

`matchedCount` and `modifiedCount` are not equivalent.

A document may match the filter but already contain the requested value.

---

## Read Operations

### Find

`find()` retrieves documents matching a filter.

```javascript
db.users.find({
  status: "active"
})
```

The result is a cursor rather than an immediately materialized array.

This matters for memory usage and server-side query processing.

### Find One

Use `findOne()` when only one document is required.

```javascript
db.users.findOne({
  email: "alice@example.com"
})
```

Typical use cases include:

- Lookup by unique identifier
- Authentication lookup
- Configuration retrieval
- Existence checks

If uniqueness matters, enforce it with a unique index rather than relying only on application logic.

---

## Query Filters

A filter determines which documents participate in a read, update, or delete.

Simple equality:

```javascript
db.orders.find({
  status: "confirmed"
})
```

Multiple fields are implicitly combined with logical AND:

```javascript
db.orders.find({
  status: "confirmed",
  customer_id: ObjectId("64f000000000000000000001")
})
```

Conceptually:

```text
status = confirmed
AND
customer_id = specified customer
```

This is one of the most important differences from constructing SQL strings: MongoDB query documents represent structured predicates directly.

---

## Comparison Operators

Common comparison operators include:

| Operator | Meaning |
|---|---|
| `$eq` | Equal |
| `$ne` | Not equal |
| `$gt` | Greater than |
| `$gte` | Greater than or equal |
| `$lt` | Less than |
| `$lte` | Less than or equal |
| `$in` | Matches any value |
| `$nin` | Matches none of the values |

Example:

```javascript
db.orders.find({
  total: {
    $gte: 1000,
    $lt: 5000
  }
})
```

This represents:

```text
1000 <= total < 5000
```

### `$in`

```javascript
db.orders.find({
  status: {
    $in: ["pending", "confirmed"]
  }
})
```

Use `$in` when the application needs a bounded set of acceptable values.

Avoid generating extremely large `$in` arrays because they can increase query processing cost.

---

## Logical Operators

MongoDB provides operators such as:

- `$and`
- `$or`
- `$nor`
- `$not`

Example:

```javascript
db.orders.find({
  $or: [
    { status: "pending" },
    { total: { $gte: 10000 } }
  ]
})
```

For simple AND conditions, MongoDB's implicit syntax is usually clearer:

```javascript
db.orders.find({
  status: "pending",
  priority: "high"
})
```

Use explicit `$and` when required by the query structure rather than adding it unnecessarily.

---

## Element Operators

Important element operators include:

```text
$exists
$type
```

Example:

```javascript
db.users.find({
  phone: {
    $exists: true
  }
})
```

Type filtering:

```javascript
db.users.find({
  age: {
    $type: "int"
  }
})
```

`$exists` is particularly useful during schema migrations and when working with flexible documents.

---

## Evaluation Operators

Evaluation operators include:

```text
$regex
$text
$where
$expr
```

Example:

```javascript
db.users.find({
  email: {
    $regex: "@example\\.com$",
    $options: "i"
  }
})
```

Regex queries require careful index consideration.

A regex that begins with a fixed prefix can sometimes benefit from index support, while arbitrary substring matching commonly results in expensive scans.

Do not use `$where` casually in production. Prefer native query operators and expressions whenever possible.

---

## Array Queries

MongoDB provides specialized operators for arrays.

Example:

```javascript
db.products.find({
  tags: "database"
})
```

This matches documents where the array contains `"database"`.

Using `$all`:

```javascript
db.products.find({
  tags: {
    $all: ["database", "backend"]
  }
})
```

Using `$size`:

```javascript
db.products.find({
  tags: {
    $size: 3
  }
})
```

For arrays of embedded documents, `$elemMatch` is important.

```javascript
db.orders.find({
  items: {
    $elemMatch: {
      product_id: "PRD-1001",
      quantity: {
        $gte: 2
      }
    }
  }
})
```

This ensures the conditions apply to the same array element.

---

## Embedded Document Queries

MongoDB can query nested fields using dot notation.

Example:

```javascript
db.users.find({
  "address.city": "Kolkata"
})
```

Nested numeric values:

```javascript
db.users.find({
  "profile.age": {
    $gte: 30
  }
})
```

Dot notation is useful for embedded structures but should be paired with appropriate indexes for high-volume queries.

---

## Projection

Projection controls which fields are returned.

Example:

```javascript
db.users.find(
  { status: "active" },
  {
    name: 1,
    email: 1
  }
)
```

Projection is useful when documents are large but the endpoint requires only a subset of fields.

Example backend flow:

```text
MongoDB document
       |
       v
Projection
       |
       v
Smaller BSON result
       |
       v
Python serialization
       |
       v
HTTP response
```

Reducing unnecessary fields can decrease:

- Network traffic
- Deserialization cost
- Application memory
- API serialization cost

Projection does not automatically make an otherwise inefficient query efficient. The filter and index design still matter.

---

## Excluding Fields

Projection can also exclude fields:

```javascript
db.users.find(
  { status: "active" },
  {
    password_hash: 0,
    internal_metadata: 0
  }
)
```

Do not use projection as the primary security mechanism.

Sensitive fields should ideally be protected by repository design, authorization, and explicit response models.

---

## Sorting

Use `sort()` to order query results.

Ascending:

```javascript
db.orders.find({
  customer_id: "CUS-1001"
}).sort({
  created_at: 1
})
```

Descending:

```javascript
db.orders.find({
  customer_id: "CUS-1001"
}).sort({
  created_at: -1
})
```

A sort can become expensive if MongoDB cannot use an appropriate index.

For a common query:

```javascript
db.orders.find({
  customer_id: "CUS-1001"
}).sort({
  created_at: -1
})
```

an index such as:

```javascript
db.orders.createIndex({
  customer_id: 1,
  created_at: -1
})
```

may support both filtering and ordering.

Index direction can be relevant for compound sort patterns.

---

## Limit

`limit()` restricts the number of returned documents.

```javascript
db.orders.find({
  status: "pending"
}).limit(50)
```

Use limits for:

- API page sizes
- Administrative queries
- Top-N queries
- Protection against accidentally returning huge result sets

A production API should generally enforce a maximum page size rather than allowing clients to request arbitrary limits.

---

## Skip

`skip()` skips documents before returning results.

```javascript
db.orders.find({
  customer_id: "CUS-1001"
})
.sort({
  created_at: -1
})
.skip(100)
.limit(20)
```

This is easy to implement but becomes less attractive for deep pagination.

Conceptually:

```text
Page 1 -> skip 0
Page 2 -> skip 20
Page 1000 -> skip 19,980
```

The database still has to advance through the skipped results.

For large datasets, cursor-based pagination is usually preferable.

---

## Cursor-Based Pagination

A better production pattern uses a stable ordering field.

Suppose documents contain:

```text
created_at
_id
```

Query the first page:

```javascript
db.orders.find({
  customer_id: "CUS-1001"
})
.sort({
  created_at: -1,
  _id: -1
})
.limit(20)
```

The next request can use the last document as a cursor.

Conceptually:

```javascript
db.orders.find({
  customer_id: "CUS-1001",
  $or: [
    {
      created_at: {
        $lt: ISODate("2026-09-21T10:00:00Z")
      }
    },
    {
      created_at: ISODate("2026-09-21T10:00:00Z"),
      _id: {
        $lt: ObjectId("64f000000000000000000001")
      }
    }
  ]
})
.sort({
  created_at: -1,
  _id: -1
})
.limit(20)
```

A matching compound index is important:

```javascript
db.orders.createIndex({
  customer_id: 1,
  created_at: -1,
  _id: -1
})
```

The `_id` tie-breaker prevents ambiguous ordering when multiple documents have identical timestamps.

---

## Cursor Behavior

MongoDB's `find()` returns a cursor.

Conceptually:

```text
Query
 |
 v
Query planner
 |
 v
Cursor
 |
 +--> batch
 +--> batch
 +--> batch
```

Drivers retrieve results in batches rather than necessarily transferring the entire result set at once.

In Python:

```python
cursor = collection.find(
    {"status": "active"},
    {"name": 1, "email": 1},
).sort("created_at", -1)

for document in cursor:
    process(document)
```

This allows large result sets to be processed incrementally.

However, iterating over millions of documents is still an expensive workload. Cursor batching does not eliminate the underlying I/O and processing cost.

---

## Update Operations

MongoDB supports two broad update styles:

```text
Modifier-based updates
        +
Replacement updates
```

Modifier updates change selected fields.

Replacement updates replace the document.

Prefer modifier updates when changing a subset of fields.

---

## Update One

`updateOne()` modifies the first matching document.

```javascript
db.users.updateOne(
  {
    email: "alice@example.com"
  },
  {
    $set: {
      status: "inactive"
    }
  }
)
```

Typical result:

```javascript
{
  acknowledged: true,
  matchedCount: 1,
  modifiedCount: 1
}
```

Use it when the filter identifies a single logical document.

A unique index should enforce uniqueness when the application relies on it.

---

## Update Many

`updateMany()` modifies all matching documents.

```javascript
db.users.updateMany(
  {
    status: "trial"
  },
  {
    $set: {
      status: "active"
    }
  }
)
```

This is useful for:

- Controlled migrations
- Bulk state changes
- Data corrections
- Administrative operations

Be extremely careful with the filter.

This:

```javascript
db.users.updateMany(
  {},
  {
    $set: {
      status: "active"
    }
  }
)
```

can modify the entire collection.

For production migrations, use controlled batches where the dataset is large.

---

## `$set`

Use `$set` to update or create a field.

```javascript
db.users.updateOne(
  { email: "alice@example.com" },
  {
    $set: {
      "profile.city": "Kolkata"
    }
  }
)
```

Dot notation allows nested updates without replacing the entire `profile` object.

---

## `$unset`

Remove a field:

```javascript
db.users.updateOne(
  { email: "alice@example.com" },
  {
    $unset: {
      legacy_field: ""
    }
  }
)
```

This is useful during schema cleanup.

---

## `$inc`

Atomically increment a numeric field:

```javascript
db.products.updateOne(
  {
    _id: ObjectId("64f000000000000000000001")
  },
  {
    $inc: {
      stock: -1
    }
  }
)
```

This is preferable to:

```text
read stock
↓
subtract 1 in application
↓
write stock
```

because the latter introduces a race condition.

---

## `$min` and `$max`

These update a field only when the new value is respectively smaller or larger.

```javascript
db.metrics.updateOne(
  { service: "orders" },
  {
    $max: {
      peak_latency_ms: 850
    }
  }
)
```

This can be useful for maintaining simple aggregate state atomically.

---

## `$currentDate`

Set a field to the current database-generated date:

```javascript
db.users.updateOne(
  { _id: ObjectId("64f000000000000000000001") },
  {
    $set: {
      status: "active"
    },
    $currentDate: {
      updated_at: true
    }
  }
)
```

A consistent server-side timestamp can be useful when multiple application instances write to the same collection.

---

## Array Updates

MongoDB provides specialized array update operators.

Append:

```javascript
db.users.updateOne(
  { _id: ObjectId("64f000000000000000000001") },
  {
    $push: {
      roles: "developer"
    }
  }
)
```

Append only if absent:

```javascript
db.users.updateOne(
  { _id: ObjectId("64f000000000000000000001") },
  {
    $addToSet: {
      roles: "developer"
    }
  }
)
```

Remove matching elements:

```javascript
db.users.updateOne(
  { _id: ObjectId("64f000000000000000000001") },
  {
    $pull: {
      roles: "developer"
    }
  }
)
```

Use `$addToSet` when duplicate values would violate the application's model.

---

## Positional Array Updates

Suppose:

```json
{
  "items": [
    {
      "product_id": "PRD-1001",
      "quantity": 2
    }
  ]
}
```

A matching array element can be updated:

```javascript
db.orders.updateOne(
  {
    _id: ObjectId("64f000000000000000000001"),
    "items.product_id": "PRD-1001"
  },
  {
    $set: {
      "items.$.quantity": 3
    }
  }
)
```

For more complex updates, filtered positional operators can target elements satisfying explicit conditions.

---

## Replacement Updates

`replaceOne()` replaces the matching document with a new document.

```javascript
db.users.replaceOne(
  {
    email: "alice@example.com"
  },
  {
    name: "Alice",
    email: "alice@example.com",
    status: "active"
  }
)
```

Replacement operations are useful when the application owns the complete document representation.

They are dangerous when developers accidentally omit fields.

For partial changes, prefer:

```javascript
$set
$unset
$inc
```

and other update operators.

---

## Upsert

An upsert means:

```text
update if matching document exists
otherwise insert
```

Example:

```javascript
db.users.updateOne(
  {
    email: "alice@example.com"
  },
  {
    $set: {
      name: "Alice",
      status: "active"
    }
  },
  {
    upsert: true
  }
)
```

Upserts are useful for:

- Idempotent synchronization
- Configuration storage
- External system reconciliation
- Event processing
- Cache-like persistent state

### Upsert Safety

If uniqueness matters, use a unique index:

```javascript
db.users.createIndex(
  { email: 1 },
  { unique: true }
)
```

Do not assume application-level existence checks are sufficient under concurrency.

---

## Delete Operations

### Delete One

```javascript
db.users.deleteOne({
  _id: ObjectId("64f000000000000000000001")
})
```

Use `deleteOne()` when the filter should identify one logical document.

### Delete Many

```javascript
db.sessions.deleteMany({
  expires_at: {
    $lt: new Date()
  }
})
```

Bulk deletion should be carefully controlled.

For very large datasets, consider operational effects such as:

- Write volume
- Replication traffic
- Lock/resource pressure
- Storage behavior
- Index maintenance
- Application impact

---

## Soft Delete

Many production systems avoid physical deletion for business records.

Instead:

```javascript
db.users.updateOne(
  {
    _id: ObjectId("64f000000000000000000001")
  },
  {
    $set: {
      deleted_at: new Date()
    }
  }
)
```

Queries then filter:

```javascript
db.users.find({
  deleted_at: null
})
```

A more explicit design can use:

```json
{
  "is_deleted": true,
  "deleted_at": "..."
}
```

Soft deletion is useful when:

- Auditability matters.
- Recovery is required.
- Business records must be retained.
- Referential history matters.

However, it increases query complexity and can cause forgotten filters.

A repository layer can centralize this behavior.

---

## Bulk Writes

MongoDB supports multiple operations in a single `bulkWrite()` call.

```javascript
db.users.bulkWrite([
  {
    insertOne: {
      document: {
        name: "Alice",
        email: "alice@example.com"
      }
    }
  },
  {
    updateOne: {
      filter: {
        email: "bob@example.com"
      },
      update: {
        $set: {
          status: "active"
        }
      }
    }
  },
  {
    deleteOne: {
      filter: {
        email: "retired@example.com"
      }
    }
  }
])
```

Bulk writes reduce application-to-database round trips.

They are particularly useful for:

- ETL
- Synchronization
- Migrations
- Batch APIs
- Event consumers

---

## Ordered vs Unordered Bulk Writes

```javascript
db.users.bulkWrite(
  operations,
  {
    ordered: false
  }
)
```

### Ordered

```text
Operation 1
   ↓
Operation 2
   ↓
Operation 3
```

A failure can affect subsequent execution.

### Unordered

```text
Operation 1 ─┐
Operation 2 ─┼──> Process independently where possible
Operation 3 ─┘
```

Unordered execution is useful when operations are independent and throughput matters.

It should not be used when application semantics depend on strict ordering.

---

## Atomicity

MongoDB provides atomicity at the single-document level.

Consider:

```json
{
  "_id": "ORDER-1001",
  "status": "pending",
  "payment_status": "unpaid"
}
```

Updating both fields in one operation:

```javascript
db.orders.updateOne(
  { _id: "ORDER-1001" },
  {
    $set: {
      status: "confirmed",
      payment_status: "paid"
    }
  }
)
```

is a single-document atomic update.

This is one reason MongoDB data modeling often embeds data that must change together.

---

## Avoiding Read-Modify-Write Races

A dangerous pattern is:

```text
Application reads document
        ↓
Application modifies value
        ↓
Application writes document
```

Two concurrent requests can overwrite each other's changes.

Prefer atomic update operators:

```javascript
db.accounts.updateOne(
  {
    _id: ObjectId("64f000000000000000000001")
  },
  {
    $inc: {
      balance: -100
    }
  }
)
```

For conditional updates, include the condition in the filter:

```javascript
db.inventory.updateOne(
  {
    _id: ObjectId("64f000000000000000000001"),
    stock: {
      $gt: 0
    }
  },
  {
    $inc: {
      stock: -1
    }
  }
)
```

The result tells the application whether a matching document was found.

This can implement optimistic concurrency patterns without a multi-document transaction.

---

## Optimistic Concurrency

A version field can detect conflicting updates.

Example:

```json
{
  "_id": "ORDER-1001",
  "version": 4,
  "status": "pending"
}
```

Update:

```javascript
db.orders.updateOne(
  {
    _id: "ORDER-1001",
    version: 4
  },
  {
    $set: {
      status: "confirmed"
    },
    $inc: {
      version: 1
    }
  }
)
```

If `matchedCount` is zero, another writer may have modified the document.

This pattern is useful when lost updates must be detected explicitly.

---

## Transactions vs Single-Document CRUD

Do not introduce a transaction merely because multiple fields are changing.

Use a transaction when the business invariant genuinely spans multiple documents or collections.

For example:

```text
Orders
+
Payments
+
Inventory
```

may require transactional coordination depending on the business model.

But if the data can be embedded into one document and changed atomically, a single-document operation is generally simpler.

---

## Read and Write Concerns

CRUD behavior is also affected by read and write configuration.

Write concern determines how much acknowledgment the client requires.

Example:

```javascript
db.users.insertOne(
  {
    name: "Alice"
  },
  {
    writeConcern: {
      w: "majority"
    }
  }
)
```

For production systems, durability requirements should be explicit rather than relying on accidental defaults.

Read preference determines where reads may be served in a replica set.

For example:

```text
primary
primaryPreferred
secondary
secondaryPreferred
nearest
```

Reading from secondaries can improve read scalability but introduces potential replication-lag visibility.

---

## CRUD and Indexes

CRUD operations should be designed together with indexes.

Example query:

```javascript
db.orders.find({
  customer_id: ObjectId("64f000000000000000000001"),
  status: "confirmed"
})
.sort({
  created_at: -1
})
.limit(20)
```

A potential compound index:

```javascript
db.orders.createIndex({
  customer_id: 1,
  status: 1,
  created_at: -1
})
```

The exact index should be validated with `explain()` and real workload characteristics.

Indexes improve reads but increase:

- Storage
- Write cost
- Memory pressure
- Maintenance work

Do not create indexes for every field simply because a field is queried occasionally.

---

## Explain CRUD Queries

Use `explain()` to understand query execution.

```javascript
db.orders.find({
  customer_id: ObjectId("64f000000000000000000001"),
  status: "confirmed"
})
.sort({
  created_at: -1
})
.explain("executionStats")
```

Important metrics include:

| Metric | Meaning |
|---|---|
| `nReturned` | Documents returned |
| `totalKeysExamined` | Index entries examined |
| `totalDocsExamined` | Documents examined |
| `executionTimeMillis` | Measured execution time |
| `IXSCAN` | Index scan |
| `COLLSCAN` | Collection scan |
| `FETCH` | Document retrieval |

A useful first diagnostic question is:

```text
How many documents did the application need?
How many documents did MongoDB inspect?
```

A query returning 20 documents after scanning hundreds of thousands requires investigation.

---

## Python and PyMongo CRUD

PyMongo provides the Python driver interface.

A production-oriented client:

```python
from pymongo import MongoClient

client = MongoClient(
    "mongodb://localhost:27017",
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    socketTimeoutMS=10000,
)

db = client["orders"]
orders = db["orders"]
```

Create:

```python
result = orders.insert_one({
    "customer_id": "CUS-1001",
    "status": "pending",
})

order_id = result.inserted_id
```

Read:

```python
order = orders.find_one({
    "_id": order_id
})
```

Update:

```python
result = orders.update_one(
    {"_id": order_id},
    {
        "$set": {
            "status": "confirmed"
        }
    }
)
```

Delete:

```python
result = orders.delete_one({
    "_id": order_id
})
```

---

## Python Projection and Sorting

```python
cursor = (
    orders.find(
        {"customer_id": "CUS-1001"},
        {
            "_id": 1,
            "status": 1,
            "created_at": 1,
        },
    )
    .sort("created_at", -1)
    .limit(20)
)

for order in cursor:
    process(order)
```

Projection should match what the service actually needs.

---

## Python Bulk Writes

```python
from pymongo import InsertOne, UpdateOne

operations = [
    InsertOne({
        "customer_id": "CUS-1001",
        "status": "pending",
    }),
    UpdateOne(
        {"customer_id": "CUS-1002"},
        {
            "$set": {
                "status": "confirmed"
            }
        },
        upsert=True,
    ),
]

result = orders.bulk_write(
    operations,
    ordered=False,
)
```

Bulk writes should be bounded into reasonable batches rather than constructing an unbounded in-memory operation list.

---

## Error Handling in Python

Do not treat all MongoDB exceptions as retryable.

Example:

```python
from pymongo.errors import DuplicateKeyError, PyMongoError

try:
    orders.insert_one({
        "email": "alice@example.com"
    })
except DuplicateKeyError:
    # Handle expected uniqueness violation.
    raise ValueError("Email already exists")
except PyMongoError:
    # Log context and propagate or translate appropriately.
    raise
```

Production code should distinguish:

```text
Validation error
Duplicate key
Timeout
Transient network error
Authentication failure
Server selection failure
Transaction error
Application bug
```

Retry behavior should be deliberate and idempotency-aware.

---

## Repository Pattern

A repository can isolate MongoDB-specific CRUD behavior.

```python
from pymongo.collection import Collection


class OrderRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def get_by_id(self, order_id):
        return self.collection.find_one({
            "_id": order_id
        })

    def update_status(self, order_id, status):
        return self.collection.update_one(
            {"_id": order_id},
            {
                "$set": {
                    "status": status
                }
            },
        )
```

The service layer can then operate on domain concepts rather than raw database calls.

```text
API
 ↓
Service
 ↓
Repository
 ↓
MongoDB
```

This separation improves testing and prevents MongoDB-specific details from leaking throughout the application.

---

## FastAPI CRUD Architecture

A typical FastAPI application can use:

```text
HTTP Request
     |
     v
Pydantic Request Model
     |
     v
Service Layer
     |
     v
Repository
     |
     v
PyMongo
     |
     v
MongoDB
```

Example endpoint:

```python
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/orders/{order_id}")
def get_order(order_id: str):
    order = order_repository.get_by_id(order_id)

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    return order
```

Production applications should also handle ObjectId conversion, response serialization, authorization, validation, and error translation explicitly.

---

## Synchronous vs Asynchronous Python Drivers

A backend application must consider whether database operations block the application runtime.

Synchronous PyMongo is straightforward:

```python
orders.find_one({"_id": order_id})
```

If the application architecture requires non-blocking database access, use a currently supported asynchronous MongoDB driver/API appropriate to the deployed MongoDB and Python stack.

The important architectural point is:

```text
Async HTTP framework
+
Blocking database calls
=
Potential event-loop blocking
```

Do not introduce asynchronous abstractions merely for style. Choose the driver model based on workload, framework architecture, and supported driver capabilities.

---

## Django Integration

Django applications can access MongoDB through:

- PyMongo
- MongoEngine
- Other MongoDB-compatible integration layers

A repository/service architecture is often easier to reason about than attempting to make MongoDB behave exactly like Django's relational ORM.

Example:

```text
Django View
    |
    v
Service
    |
    v
Repository
    |
    v
PyMongo
    |
    v
MongoDB
```

This makes document-oriented operations explicit.

Avoid assuming relational ORM features such as joins, foreign keys, and model lifecycle semantics automatically map to MongoDB.

---

## CRUD and REST API Design

CRUD operations should not automatically map one-to-one to public APIs.

For example:

```text
POST   /orders
GET    /orders/{id}
PATCH  /orders/{id}
DELETE /orders/{id}
```

may map to MongoDB operations, but domain actions can require explicit APIs:

```text
POST /orders/{id}/confirm
POST /orders/{id}/cancel
```

The service layer can then enforce business rules before performing MongoDB updates.

This prevents database CRUD semantics from becoming the application's domain model.

---

## Idempotency

Distributed systems frequently retry requests.

For example:

```text
Client
  |
  | POST
  v
API
  |
  | write
  v
MongoDB
  |
  X timeout
  |
  v
Client retries
```

If the original write succeeded but the response was lost, blindly retrying may create duplicates.

Use idempotency keys or deterministic identifiers where appropriate.

Example:

```json
{
  "idempotency_key": "PAY-2026-000001",
  "amount": 1499.50
}
```

A unique index can enforce uniqueness:

```javascript
db.payments.createIndex(
  { idempotency_key: 1 },
  { unique: true }
)
```

This is an important production CRUD design pattern.

---

## CRUD and Security

Never construct queries directly from untrusted input without validation.

Avoid exposing arbitrary MongoDB operators through public APIs.

For example, an API should not blindly accept:

```json
{
  "filter": {
    "$where": "..."
  }
}
```

Instead, map allowed API fields to explicit database filters:

```python
filters = {}

if status is not None:
    filters["status"] = status

if customer_id is not None:
    filters["customer_id"] = customer_id
```

Additional protections include:

- Authentication
- Authorization
- Input validation
- Field allowlists
- Query limits
- Maximum page sizes
- Rate limiting
- Least-privilege database credentials
- Sensitive-field exclusion

---

## CRUD Performance

CRUD performance depends on several layers:

```text
API latency
    +
Application processing
    +
Network latency
    +
MongoDB query execution
    +
Index access
    +
Storage I/O
```

For reads:

- Use appropriate indexes.
- Project only required fields.
- Avoid unbounded result sets.
- Prefer cursor pagination at scale.
- Measure with `explain("executionStats")`.

For writes:

- Use atomic update operators.
- Batch independent operations.
- Avoid unnecessary document rewrites.
- Avoid excessive indexes.
- Monitor document growth.

---

## Large Documents and CRUD Performance

A document-oriented design can make CRUD operations efficient when related data is embedded.

However, repeatedly modifying large documents can become expensive.

For example:

```json
{
  "customer_id": "CUS-1001",
  "events": [
    "... thousands of events ..."
  ]
}
```

If the array grows indefinitely, every update can become increasingly expensive and the document can approach MongoDB's document-size limit.

Consider alternatives such as:

```text
Customer
   |
   +---- events collection
```

or bucketed event documents.

CRUD performance therefore starts with data modeling, not with command syntax.

---

## Monitoring CRUD Workloads

Production monitoring should cover:

- Query latency
- Write latency
- Query volume
- Error rate
- Slow operations
- Connection pool usage
- Replication lag
- Index efficiency
- Document growth
- Storage usage

Useful investigation tools include:

```javascript
db.collection.explain("executionStats").find(...)
```

and collection/index statistics.

For production environments, correlate MongoDB metrics with:

```text
API latency
CPU
Memory
Network
Disk I/O
Application errors
```

A database query should be investigated in the context of the entire request path.

---

## Common CRUD Mistakes

### Returning Every Field

Large documents can unnecessarily increase network and serialization cost.

Use projection where appropriate.

### Using `skip()` for Deep Pagination

Offset pagination becomes increasingly expensive at large offsets.

Prefer cursor-based pagination for high-volume APIs.

### Updating by Non-Unique Fields

This can unintentionally modify multiple documents.

Use unique indexes where the application assumes uniqueness.

### Read-Modify-Write for Counters

This creates concurrency risks.

Prefer atomic operators such as `$inc`.

### Unbounded `updateMany()`

A broad filter can modify millions of documents.

Use controlled migrations and verify the filter before execution.

### Using `replaceOne()` for Partial Changes

Missing fields can be accidentally removed.

Use update operators for partial modifications.

### Assuming `matchedCount == modifiedCount`

A document can match the filter while already containing the requested value.

### Returning Raw MongoDB Documents

Database documents may contain:

- Internal fields
- Sensitive information
- BSON-specific types
- Implementation details

Use response models or serialization layers.

### Retrying Non-Idempotent Writes Blindly

A retry can create duplicate records.

Use idempotency strategies where required.

### Creating Indexes Without Measuring

Indexes consume storage and increase write overhead.

Base them on actual access patterns.

---

## Production CRUD Workflow

A senior engineer should generally approach a new CRUD operation like this:

```text
Business requirement
        ↓
Access pattern
        ↓
Document model
        ↓
Query/update design
        ↓
Index design
        ↓
Concurrency analysis
        ↓
Validation
        ↓
API/service implementation
        ↓
Explain-plan verification
        ↓
Load testing
        ↓
Monitoring
        ↓
Production rollout
```

The command itself is usually the easiest part.

The difficult engineering work is determining whether the operation remains correct and efficient under real workload, concurrency, failures, retries, and data growth.

## CRUD Decision Matrix

| Requirement | Recommended approach |
|---|---|
| Create one document | `insertOne()` |
| Create many independent documents | `insertMany()` |
| Read one document | `findOne()` |
| Read many documents | `find()` |
| Partial update | `updateOne()` / `updateMany()` |
| Full document replacement | `replaceOne()` |
| Update-or-create | `updateOne(..., { upsert: true })` |
| Delete one | `deleteOne()` |
| Delete many | `deleteMany()` |
| Multiple independent writes | `bulkWrite()` |
| Atomic counter | `$inc` |
| Add unique array value | `$addToSet` |
| Remove array values | `$pull` |
| Large API pagination | Cursor-based pagination |
| Cross-document atomicity | Transaction |
| Prevent duplicate business identifier | Unique index |
| Detect concurrent modification | Version/conditional update |

## Troubleshooting CRUD Problems

### Query Is Slow

```text
Symptom
↓
High read latency
↓
Possible causes
↓
COLLSCAN, poor index, inefficient sort, large documents, low selectivity, deep skip
↓
Isolation strategy
↓
Run explain("executionStats") and inspect the actual query shape
↓
Diagnostic commands
↓
db.collection.find(filter).sort(sort).explain("executionStats")
↓
Root cause
↓
Too many documents or index keys examined
↓
Corrective action
↓
Redesign index/query or pagination strategy
↓
Prevention
↓
Query regression tests + performance monitoring
```

### Update Modified Unexpected Documents

```text
Symptom
↓
More documents changed than expected
↓
Possible causes
↓
Broad filter or incorrect query composition
↓
Isolation strategy
↓
Run the filter as find() before executing the update
↓
Diagnostic commands
↓
db.collection.find(filter)
↓
Root cause
↓
Filter was not unique
↓
Corrective action
↓
Use a precise filter and unique index where appropriate
↓
Prevention
↓
Dry-run migration queries + automated tests
```

### Duplicate Documents After Retry

```text
Symptom
↓
Repeated API request creates multiple documents
↓
Possible causes
↓
Non-idempotent insert combined with client/network retry
↓
Isolation strategy
↓
Trace request and persistence identifiers
↓
Diagnostic commands
↓
db.collection.find({ idempotency_key: "..." })
↓
Root cause
↓
No uniqueness boundary for repeated requests
↓
Corrective action
↓
Add idempotency handling and a unique index
↓
Prevention
↓
Design retry semantics before production deployment
```

### Concurrent Updates Lose Data

```text
Symptom
↓
One update appears to overwrite another
↓
Possible causes
↓
Application-level read-modify-write race
↓
Isolation strategy
↓
Trace concurrent requests and compare document versions
↓
Diagnostic commands
↓
Inspect update filters and application logs
↓
Root cause
↓
Two writers read the same previous state
↓
Corrective action
↓
Use atomic operators or optimistic concurrency
↓
Prevention
↓
Concurrency tests + conditional update patterns
```

## Key Takeaways

- MongoDB CRUD design should start with access patterns, document modeling, indexes, concurrency, and failure semantics rather than with individual commands.
- Single-document operations are atomic, making operators such as `$set`, `$inc`, `$push`, and `$addToSet` important tools for safe concurrent updates.
- Use precise filters, unique indexes, cursor-based pagination, and idempotency strategies to make CRUD operations reliable at production scale.
- Bulk writes reduce round trips, but their ordering, error handling, batching, and retry semantics must match the workload.
- A senior CRUD implementation combines correct MongoDB operations with schema validation, query-plan analysis, security controls, monitoring, and production-oriented error handling.