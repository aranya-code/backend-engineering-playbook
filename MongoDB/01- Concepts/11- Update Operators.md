# 11- Update Operators

## Overview

MongoDB update operators modify fields, arrays, and document structure without requiring the application to replace an entire document.

They are central to production CRUD workloads because they allow targeted mutations such as:

- Incrementing counters
- Updating status fields
- Adding elements to arrays
- Removing fields
- Updating nested fields
- Maintaining timestamps
- Performing conditional updates
- Updating multiple matching documents
- Implementing atomic state transitions

The main distinction is between:

- **Replacement updates** — replace the complete document.
- **Operator-based updates** — modify selected parts of the existing document.

For example:

```javascript
db.orders.updateOne(
  { order_id: "ORD-1001" },
  {
    $set: {
      status: "shipped",
      updated_at: new Date()
    },
    $inc: {
      version: 1
    }
  }
)
```

This changes only the specified fields.

The general production pattern is:

```text
API Request
    |
    v
Validate input
    |
    v
Build filter
    |
    v
Build update operators
    |
    v
MongoDB atomic update
    |
    v
Write result
    |
    v
Service/API response
```

Correct update design is important for correctness, concurrency, performance, and data integrity.

## Replacement Updates vs Operator Updates

MongoDB supports two fundamentally different update styles.

### Replacement Update

A replacement document does not use update operators.

```javascript
db.users.replaceOne(
  { _id: ObjectId("64f000000000000000000001") },
  {
    name: "Alice",
    email: "alice@example.com",
    status: "active"
  }
)
```

The existing document is replaced by the supplied document, subject to MongoDB's replacement semantics.

This is appropriate when the application intentionally owns the complete document representation.

It is dangerous when the application only has a partial representation.

### Operator-Based Update

```javascript
db.users.updateOne(
  { _id: ObjectId("64f000000000000000000001") },
  {
    $set: {
      status: "active"
    }
  }
)
```

Only `status` is changed.

For most backend APIs, operator-based updates are safer because request payloads commonly represent partial changes.

| Approach | Best suited for |
|---|---|
| `replaceOne()` | Complete document replacement |
| `$set` | Partial field updates |
| `$unset` | Removing fields |
| `$inc` | Counters and numeric state |
| `$push` / `$addToSet` | Array modifications |
| `$pull` | Removing array elements |
| Pipeline update | Complex server-side transformations |

## Single-Document Atomicity

MongoDB guarantees atomicity for writes to an individual document.

For example:

```javascript
db.accounts.updateOne(
  { _id: ObjectId("64f000000000000000000001") },
  {
    $inc: {
      balance: -100
    }
  }
)
```

The increment is applied atomically to that document.

This is preferable to:

```text
Read balance
    ↓
Calculate balance - 100
    ↓
Write balance
```

because another concurrent operation can modify the balance between the read and write.

An atomic operator allows MongoDB to perform the mutation as one database operation.

## Core Update Operators

The most commonly used update operators are:

| Operator | Purpose |
|---|---|
| `$set` | Set or replace a field |
| `$unset` | Remove a field |
| `$inc` | Increment or decrement a numeric value |
| `$mul` | Multiply a numeric value |
| `$min` | Update only if new value is smaller |
| `$max` | Update only if new value is larger |
| `$rename` | Rename a field |
| `$currentDate` | Set a field to the current date or timestamp |
| `$setOnInsert` | Set fields only during an upsert insert |
| `$push` | Add an element to an array |
| `$addToSet` | Add an array element only if absent |
| `$pop` | Remove the first or last array element |
| `$pull` | Remove matching array elements |
| `$pullAll` | Remove specified array values |
| `$` | Update the first matching array element |
| `$[]` | Update all array elements |
| `$[identifier]` | Update filtered array elements |

## `$set`

`$set` assigns a value to a field.

```javascript
db.users.updateOne(
  { email: "alice@example.com" },
  {
    $set: {
      status: "active"
    }
  }
)
```

If the field does not exist, MongoDB creates it.

### Nested Fields

Use dot notation:

```javascript
db.users.updateOne(
  { email: "alice@example.com" },
  {
    $set: {
      "profile.city": "Kolkata",
      "profile.country": "India"
    }
  }
)
```

This changes only those nested fields.

### Why `$set` Is Preferred

Avoid manually reading and rewriting an entire document when only a few fields need to change.

Prefer:

```javascript
{
  $set: {
    status: "active"
  }
}
```

over:

```text
Read entire document
        ↓
Modify in application
        ↓
Write entire document
```

The operator-based approach reduces unnecessary data movement and avoids overwriting unrelated concurrent changes.

## `$unset`

`$unset` removes a field.

```javascript
db.users.updateOne(
  { email: "alice@example.com" },
  {
    $unset: {
      temporary_token: ""
    }
  }
)
```

The value associated with `$unset` is generally ignored; an empty string is commonly used for readability.

### Nested Field Removal

```javascript
db.users.updateOne(
  { email: "alice@example.com" },
  {
    $unset: {
      "profile.temporary_address": ""
    }
  }
)
```

Use `$unset` when a field should no longer exist.

Do not confuse:

```javascript
{
  $set: {
    middle_name: null
  }
}
```

with:

```javascript
{
  $unset: {
    middle_name: ""
  }
}
```

The first retains the field with a `null` value.

The second removes the field.

This distinction matters for:

- Schema validation
- `$exists`
- Application serialization
- Query behavior
- Indexing
- API semantics

## `$inc`

`$inc` increments or decrements numeric fields.

```javascript
db.products.updateOne(
  { sku: "SKU-1001" },
  {
    $inc: {
      stock: -1
    }
  }
)
```

It is ideal for counters because the operation is performed atomically.

Other examples:

```javascript
{
  $inc: {
    login_count: 1
  }
}
```

```javascript
{
  $inc: {
    retry_count: -1
  }
}
```

If the field does not exist, MongoDB creates it with the increment value.

The target field must be numeric.

### Atomic Counter Pattern

Avoid:

```python
document = collection.find_one({"_id": product_id})

new_stock = document["stock"] - 1

collection.update_one(
    {"_id": product_id},
    {"$set": {"stock": new_stock}},
)
```

Prefer:

```python
collection.update_one(
    {"_id": product_id},
    {"$inc": {"stock": -1}},
)
```

The second version avoids a read-modify-write race.

## `$mul`

`$mul` multiplies a numeric field.

```javascript
db.products.updateOne(
  { sku: "SKU-1001" },
  {
    $mul: {
      price: 1.10
    }
  }
)
```

This can be useful for bulk price adjustments or numeric transformations.

Use it carefully for financial data.

For monetary values, consider storing integer minor units such as cents rather than relying on floating-point values.

## `$min`

`$min` updates a field only if the supplied value is less than the existing value.

```javascript
db.metrics.updateOne(
  { service: "payments" },
  {
    $min: {
      minimum_latency_ms: 42
    }
  }
)
```

If the existing value is `50`, it becomes `42`.

If the existing value is `30`, it remains `30`.

This is useful for maintaining minimum observed values.

## `$max`

`$max` updates a field only when the supplied value is greater.

```javascript
db.metrics.updateOne(
  { service: "payments" },
  {
    $max: {
      maximum_latency_ms: 850
    }
  }
)
```

This is useful for:

- High-water marks
- Maximum observed values
- Version tracking
- Watermark processing

## `$rename`

`$rename` changes a field name.

```javascript
db.users.updateMany(
  {},
  {
    $rename: {
      "phone_number": "phone"
    }
  }
)
```

Use this carefully in production because it is a schema migration.

A safer migration may require:

```text
Deploy compatible application
        ↓
Backfill / rename
        ↓
Verify documents
        ↓
Deploy new application behavior
        ↓
Remove compatibility code
```

Avoid renaming a field while old application versions still depend on the old name unless the migration strategy explicitly supports both versions.

## `$currentDate`

`$currentDate` sets a field to the current server-side date.

```javascript
db.orders.updateOne(
  { order_id: "ORD-1001" },
  {
    $currentDate: {
      updated_at: true
    }
  }
)
```

This can be preferable to generating timestamps independently in multiple application servers.

For timestamp fields, consistency of timezone and serialization should still be enforced at the application boundary.

## `$setOnInsert`

`$setOnInsert` is especially useful with upserts.

```javascript
db.users.updateOne(
  {
    email: "alice@example.com"
  },
  {
    $set: {
      last_login_at: new Date()
    },
    $setOnInsert: {
      created_at: new Date(),
      status: "active"
    }
  },
  {
    upsert: true
  }
)
```

If the document already exists:

```text
$set       → applied
$setOnInsert → ignored
```

If MongoDB inserts a new document:

```text
$set       → applied
$setOnInsert → applied
```

This is useful for initialization fields that should not change on subsequent updates.

## Upsert

An upsert means:

```text
Update if matching document exists
OR
Insert if no matching document exists
```

Example:

```javascript
db.inventory.updateOne(
  {
    sku: "SKU-1001"
  },
  {
    $set: {
      quantity: 100,
      updated_at: new Date()
    },
    $setOnInsert: {
      created_at: new Date()
    }
  },
  {
    upsert: true
  }
)
```

Upserts are useful for:

- Idempotent synchronization
- Configuration records
- Materialized state
- External-system synchronization
- Counters and aggregation state

### Upsert and Unique Indexes

If an application requires one document per logical key, enforce that invariant with a unique index.

```javascript
db.users.createIndex(
  { email: 1 },
  { unique: true }
)
```

Application-level checks such as:

```text
find email
    ↓
not found
    ↓
insert
```

are vulnerable to concurrent requests.

A unique index provides the database-level guarantee.

## `$push`

`$push` appends an element to an array.

```javascript
db.users.updateOne(
  { email: "alice@example.com" },
  {
    $push: {
      tags: "premium"
    }
  }
)
```

Result:

```json
{
  "tags": [
    "existing",
    "premium"
  ]
}
```

Duplicates are allowed.

## `$push` with `$each`

Multiple values can be appended:

```javascript
db.users.updateOne(
  { email: "alice@example.com" },
  {
    $push: {
      tags: {
        $each: [
          "premium",
          "verified"
        ]
      }
    }
  }
)
```

## `$push` with `$position`

`$position` controls insertion location.

```javascript
db.users.updateOne(
  { email: "alice@example.com" },
  {
    $push: {
      tags: {
        $each: ["priority"],
        $position: 0
      }
    }
  }
)
```

The new value is inserted at the beginning.

## `$push` with `$slice`

`$slice` can keep an array bounded.

```javascript
db.users.updateOne(
  { email: "alice@example.com" },
  {
    $push: {
      recent_logins: {
        $each: [
          {
            at: new Date(),
            source: "web"
          }
        ],
        $slice: -20
      }
    }
  }
)
```

This maintains only the latest 20 entries.

This is useful for intentionally bounded arrays.

It should not be used as a workaround for a fundamentally unbounded data model.

## `$push` with `$sort`

For arrays of documents, `$push` can combine `$each`, `$sort`, and `$slice`.

```javascript
db.users.updateOne(
  { email: "alice@example.com" },
  {
    $push: {
      recent_scores: {
        $each: [
          {
            score: 98,
            recorded_at: new Date()
          }
        ],
        $sort: {
          score: -1
        },
        $slice: 10
      }
    }
  }
)
```

This can maintain a bounded top-N collection embedded inside a document.

## `$addToSet`

`$addToSet` adds a value to an array only if an equivalent value is not already present.

```javascript
db.users.updateOne(
  { email: "alice@example.com" },
  {
    $addToSet: {
      roles: "admin"
    }
  }
)
```

This is useful when duplicate values are undesirable.

For example:

```text
roles = ["user"]
```

Applying:

```javascript
{
  $addToSet: {
    roles: "admin"
  }
}
```

produces:

```text
["user", "admin"]
```

Repeating the same operation does not add another `"admin"`.

## `$addToSet` with `$each`

```javascript
db.users.updateOne(
  { email: "alice@example.com" },
  {
    $addToSet: {
      roles: {
        $each: [
          "admin",
          "auditor"
        ]
      }
    }
  }
)
```

Each candidate is evaluated for membership.

## `$push` vs `$addToSet`

| Requirement | Operator |
|---|---|
| Allow duplicates | `$push` |
| Prevent duplicate scalar values | `$addToSet` |
| Preserve every event | `$push` |
| Maintain a set-like array | `$addToSet` |
| Append multiple values | `$push` + `$each` |
| Add multiple unique values | `$addToSet` + `$each` |

Do not use `$addToSet` when duplicate events are semantically meaningful.

## `$pop`

`$pop` removes one element from an array.

Remove the last element:

```javascript
db.users.updateOne(
  { email: "alice@example.com" },
  {
    $pop: {
      recent_logins: 1
    }
  }
)
```

Remove the first element:

```javascript
db.users.updateOne(
  { email: "alice@example.com" },
  {
    $pop: {
      recent_logins: -1
    }
  }
)
```

This is useful for bounded queue-like structures, but high-throughput queues generally belong in purpose-built systems such as Redis or Kafka rather than inside MongoDB documents.

## `$pull`

`$pull` removes array elements matching a condition.

For scalar values:

```javascript
db.users.updateOne(
  { email: "alice@example.com" },
  {
    $pull: {
      roles: "temporary"
    }
  }
)
```

For embedded documents:

```javascript
db.orders.updateOne(
  { order_id: "ORD-1001" },
  {
    $pull: {
      items: {
        status: "cancelled"
      }
    }
  }
)
```

Every matching array element can be removed.

## `$pullAll`

`$pullAll` removes specific values.

```javascript
db.users.updateOne(
  { email: "alice@example.com" },
  {
    $pullAll: {
      tags: [
        "temporary",
        "legacy"
      ]
    }
  }
)
```

It is useful when the exact values to remove are known.

## Positional `$` Operator

The positional `$` operator updates the first matching array element.

Example:

```javascript
db.orders.updateOne(
  {
    order_id: "ORD-1001",
    "items.product_id": "PRD-1001"
  },
  {
    $set: {
      "items.$.status": "shipped"
    }
  }
)
```

The filter identifies the matching array element.

The `$` represents the first matching element.

Conceptually:

```text
Query
  |
  +---- order_id = ORD-1001
  |
  +---- items.product_id = PRD-1001
              |
              v
       First matching item
              |
              v
       Update status
```

This is useful for targeted modifications to embedded arrays.

## `$[]` All-Positional Operator

`$[]` updates every element in an array.

```javascript
db.products.updateMany(
  {
    category: "electronics"
  },
  {
    $inc: {
      "variants.$[].price": 10
    }
  }
)
```

Every variant's price is incremented.

Use this carefully because a single operation may modify many nested elements.

## Filtered Positional `$[identifier]`

Filtered positional updates modify only array elements matching an `arrayFilters` condition.

Example:

```javascript
db.orders.updateMany(
  {},
  {
    $set: {
      "items.$[item].status": "cancelled"
    }
  },
  {
    arrayFilters: [
      {
        "item.status": "pending"
      }
    ]
  }
)
```

Only pending items are changed.

This is substantially more precise than `$[]`.

## Array Update Comparison

| Operator | Behavior |
|---|---|
| `$push` | Append element |
| `$addToSet` | Append only if equivalent value is absent |
| `$pop` | Remove first or last |
| `$pull` | Remove matching elements |
| `$pullAll` | Remove specified values |
| `$` | Update first matching element |
| `$[]` | Update all elements |
| `$[id]` | Update filtered elements |

## Nested Array Updates

For nested arrays, filtered positional operators are particularly useful.

Example:

```json
{
  "courses": [
    {
      "name": "Backend",
      "modules": [
        {
          "name": "MongoDB",
          "completed": false
        }
      ]
    }
  ]
}
```

A targeted update can use array filters:

```javascript
db.students.updateOne(
  { student_id: "STU-1001" },
  {
    $set: {
      "courses.$[course].modules.$[module].completed": true
    }
  },
  {
    arrayFilters: [
      { "course.name": "Backend" },
      { "module.name": "MongoDB" }
    ]
  }
)
```

This is powerful, but deeply nested arrays often indicate increasing document-model complexity.

If updates repeatedly require multiple nested array filters, reconsider whether the data should be modeled as separate documents.

## Update Operators and Conditional State Changes

A production update often combines operators with a filter.

Suppose an order may transition:

```text
pending → paid
paid → shipped
shipped → delivered
```

Do not blindly update:

```javascript
db.orders.updateOne(
  { order_id: "ORD-1001" },
  {
    $set: {
      status: "shipped"
    }
  }
)
```

Instead include the expected current state:

```javascript
db.orders.updateOne(
  {
    order_id: "ORD-1001",
    status: "paid"
  },
  {
    $set: {
      status: "shipped",
      updated_at: new Date()
    }
  }
)
```

The filter becomes part of the concurrency control.

If:

```text
matchedCount = 0
```

the transition did not occur.

This pattern is useful for optimistic concurrency and state-machine-style updates.

## Optimistic Concurrency

A version field can be used:

```json
{
  "_id": "...",
  "status": "pending",
  "version": 4
}
```

Update:

```javascript
db.orders.updateOne(
  {
    _id: ObjectId("64f000000000000000000001"),
    version: 4
  },
  {
    $set: {
      status: "paid"
    },
    $inc: {
      version: 1
    }
  }
)
```

If another writer already changed the document to version 5, the filter no longer matches.

The application can detect:

```text
matchedCount = 0
```

and treat this as a concurrency conflict.

This is often preferable to reading the document, modifying it locally, and overwriting it.

## Update Result

PyMongo returns an update result containing useful information.

```python
result = collection.update_one(
    {"order_id": "ORD-1001"},
    {
        "$set": {
            "status": "shipped",
        },
        "$currentDate": {
            "updated_at": True,
        },
    },
)

print(result.matched_count)
print(result.modified_count)
```

Important fields include:

| Result | Meaning |
|---|---|
| `matched_count` | Number of documents matching the filter |
| `modified_count` | Number of documents actually modified |
| `upserted_id` | ID of an inserted document when upsert creates one |
| `acknowledged` | Whether the write was acknowledged |

A document can match but not be modified because the new value is already equal to the current value.

Therefore:

```text
matched_count != modified_count
```

is not automatically an error.

## Update Many

`updateMany()` applies an update to all documents matching the filter.

```javascript
db.users.updateMany(
  {
    status: "legacy"
  },
  {
    $set: {
      status: "inactive"
    }
  }
)
```

This can be useful for controlled migrations and bulk state changes.

Production risks include:

- Large write volume
- Replication lag
- Increased disk activity
- Long execution time
- Large numbers of modified documents
- Unexpectedly broad filters

Before running a large update, inspect the filter:

```javascript
db.users.countDocuments({
  status: "legacy"
})
```

Then test the update against a representative environment.

## Bulk Updates

For heterogeneous updates, use bulk writes.

PyMongo:

```python
from pymongo import UpdateOne

operations = [
    UpdateOne(
        {"sku": "SKU-1001"},
        {"$inc": {"stock": -1}},
    ),
    UpdateOne(
        {"sku": "SKU-1002"},
        {"$set": {"status": "inactive"}},
    ),
]

result = collection.bulk_write(
    operations,
    ordered=False,
)
```

`ordered=False` allows operations to be processed without requiring strict sequential execution.

This can improve throughput when operations are independent.

Use ordered writes when operation order is semantically important.

## Update Pipelines

MongoDB also supports aggregation pipelines for updates.

Example:

```javascript
db.orders.updateMany(
  {
    status: "pending"
  },
  [
    {
      $set: {
        normalized_status: {
          $toLower: "$status"
        }
      }
    }
  ]
)
```

Pipeline updates are useful when the new value depends on existing document data and simple update operators are insufficient.

They can perform transformations using aggregation expressions.

Conceptually:

```text
Existing document
       |
       v
Aggregation expressions
       |
       v
Transformed document
       |
       v
Persisted document
```

Use pipeline updates when the transformation belongs naturally in the database.

Avoid turning update pipelines into large application programs expressed as database expressions. Complex transformations can become difficult to test and operate.

## `$set` vs Replacement

Consider:

```json
{
  "_id": "1",
  "name": "Alice",
  "email": "alice@example.com",
  "status": "active",
  "preferences": {
    "notifications": true
  }
}
```

This is dangerous when only `status` is being changed:

```javascript
db.users.replaceOne(
  { _id: "1" },
  {
    status: "inactive"
  }
)
```

The replacement document does not represent the previous complete document.

Prefer:

```javascript
db.users.updateOne(
  { _id: "1" },
  {
    $set: {
      status: "inactive"
    }
  }
)
```

The distinction is fundamental in backend API design.

## Nested Object Replacement Pitfall

Even `$set` can unintentionally replace a complete nested object.

Suppose:

```json
{
  "profile": {
    "city": "Kolkata",
    "country": "India",
    "timezone": "Asia/Kolkata"
  }
}
```

This:

```javascript
{
  $set: {
    profile: {
      city: "Mumbai"
    }
  }
}
```

replaces the entire `profile` object.

The other nested fields are lost.

Prefer:

```javascript
{
  $set: {
    "profile.city": "Mumbai"
  }
}
```

This is one of the most common MongoDB update mistakes.

## Updating `null` vs Missing Fields

These documents are different:

```json
{
  "phone": null
}
```

and:

```json
{}
```

For example:

```javascript
db.users.find({
  phone: null
})
```

can match documents where `phone` is `null` or where the field is missing.

If the application needs to distinguish them, use explicit conditions such as:

```javascript
db.users.find({
  phone: {
    $exists: true,
    $eq: null
  }
})
```

Update semantics should align with the application's schema rules.

## Update Operators and Schema Validation

Schema validation can restrict updates.

For example, if:

```text
status
```

must be one of:

```text
pending
paid
shipped
delivered
cancelled
```

then:

```javascript
{
  $set: {
    status: "invalid"
  }
}
```

may be rejected by collection validation.

This provides a useful defense-in-depth model:

```text
API validation
      |
      v
Service/business validation
      |
      v
MongoDB update operator
      |
      v
MongoDB schema validation
      |
      v
Persistent data
```

Application validation should handle business rules.

Database validation should protect important structural invariants.

## Update Operators and Indexes

Updates can affect indexes.

For example:

```javascript
db.users.updateOne(
  { email: "alice@example.com" },
  {
    $set: {
      status: "inactive"
    }
  }
)
```

If `status` is indexed, MongoDB may need to update the relevant index entry.

A heavily indexed collection can therefore have higher write costs.

The general relationship is:

```text
More indexes
    ↓
Faster reads
    +
More write/index-maintenance work
```

Do not create indexes solely because fields are frequently updated or queried individually.

Design indexes around actual workload patterns.

## Large Array Updates

Updating an array can be expensive when the array is large.

For example:

```javascript
{
  $push: {
    events: new_event
  }
}
```

on a large embedded array may repeatedly increase document size and create a hot document.

Potential consequences:

- Larger writes
- More network traffic
- More storage consumption
- Increased contention
- Document growth
- Increased replication traffic

For high-volume event data, consider a separate collection:

```text
orders
  |
  +---- order document

order_events
  |
  +---- event 1
  +---- event 2
  +---- event 3
```

rather than indefinitely appending events to one document.

## Hot Documents

A hot document is repeatedly updated by many concurrent operations.

Example:

```json
{
  "_id": "global",
  "request_count": 1000000
}
```

with thousands of concurrent:

```javascript
{
  $inc: {
    request_count: 1
  }
}
```

Although each update is atomic, the document can become a contention point.

For high-throughput counters, consider:

- Sharded counters
- Time buckets
- Separate event records
- Redis counters
- Kafka-based aggregation
- Periodic materialization

MongoDB atomicity does not eliminate workload-level contention.

## Update Operations in Python

A production repository can encapsulate update logic:

```python
from datetime import datetime, timezone
from pymongo.collection import Collection


class OrderRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def mark_shipped(self, order_id: str) -> bool:
        result = self.collection.update_one(
            {
                "order_id": order_id,
                "status": "paid",
            },
            {
                "$set": {
                    "status": "shipped",
                },
                "$currentDate": {
                    "updated_at": True,
                },
            },
        )

        return result.modified_count == 1
```

The repository should expose business-level operations rather than allowing arbitrary update documents to leak throughout the application.

## Avoid Passing Raw Update Operators from Public APIs

This is dangerous:

```python
collection.update_one(
    {"_id": user_id},
    request.json["update"],
)
```

A client should not be allowed to construct arbitrary MongoDB update operators unless the system explicitly requires that capability.

A public API should translate domain-level commands into allowed database mutations.

For example:

```text
PATCH /orders/{id}
        |
        v
Validate allowed fields
        |
        v
Build $set / $unset
        |
        v
Repository
        |
        v
MongoDB
```

This prevents accidental or malicious modification of protected fields.

## FastAPI Update Pattern

A Pydantic model can distinguish omitted fields from explicitly supplied values.

Conceptually:

```python
from pydantic import BaseModel


class OrderUpdate(BaseModel):
    status: str | None = None
    shipping_address: str | None = None
```

The service should construct only permitted updates:

```python
def build_update(payload: OrderUpdate) -> dict:
    values = payload.model_dump(
        exclude_unset=True
    )

    return {
        "$set": values
    }
```

In a production system, additional validation should restrict:

- Allowed status transitions
- Immutable fields
- Ownership
- Authorization
- Field-level permissions

## Django Integration

When using PyMongo from Django, update operations should generally remain inside a repository or service layer.

For example:

```python
class UserRepository:
    def __init__(self, collection):
        self.collection = collection

    def deactivate(self, user_id):
        return self.collection.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "status": "inactive",
                },
                "$currentDate": {
                    "updated_at": True,
                },
            },
        )
```

Do not assume MongoDB update semantics are identical to Django's relational ORM.

The application architecture should make the MongoDB-specific behavior explicit.

## Transactions and Update Operators

Many update operations do not require transactions because a single-document update is atomic.

For example:

```javascript
db.orders.updateOne(
  {
    _id: ObjectId("64f000000000000000000001"),
    status: "paid"
  },
  {
    $set: {
      status: "shipped"
    }
  }
)
```

does not require a multi-document transaction.

A transaction becomes relevant when a business operation must atomically modify multiple documents or collections.

For example:

```text
Order
  |
  +---- Update order status
  |
  +---- Update inventory
  |
  +---- Record payment state
```

If these changes must commit together, a transaction may be appropriate.

Do not introduce transactions merely because an operation contains multiple update operators.

## Write Concern

Update correctness also depends on write concern.

For example:

```python
collection.with_options(
    write_concern=WriteConcern(w="majority")
).update_one(
    {"order_id": "ORD-1001"},
    {"$set": {"status": "shipped"}},
)
```

The appropriate write concern depends on the application's durability requirements.

For critical state transitions, acknowledged and appropriately durable writes are generally more appropriate than blindly using unacknowledged writes.

## Retryable Updates

Network failures create an important distinction:

```text
Application
    |
    | update request
    v
MongoDB
    |
    | operation applied
    v
Network failure
    |
    v
Application receives error
```

The client may not know whether the operation was applied.

Retrying blindly can be dangerous for non-idempotent operations.

For example:

```javascript
{
  $inc: {
    balance: 100
  }
}
```

requires careful consideration of retry semantics.

For idempotent state-setting operations:

```javascript
{
  $set: {
    status: "paid"
  }
}
```

repeating the same update generally has a different risk profile.

Use MongoDB driver retry capabilities and application-level idempotency design together.

## Idempotent Update Design

An idempotent update produces the same logical state when safely repeated.

Good example:

```javascript
db.orders.updateOne(
  {
    order_id: "ORD-1001"
  },
  {
    $set: {
      status: "paid"
    }
  }
)
```

Less straightforward:

```javascript
db.orders.updateOne(
  {
    order_id: "ORD-1001"
  },
  {
    $inc: {
      payment_attempts: 1
    }
  }
)
```

The second operation intentionally changes state on every execution.

For distributed systems involving Kafka, Celery, or external webhooks, design updates around idempotency keys or unique business identifiers where appropriate.

## Schema Migration with Update Operators

Update operators are frequently used for data migrations.

Example:

```javascript
db.users.updateMany(
  {
    profile: {
      $exists: true
    },
    schema_version: {
      $lt: 2
    }
  },
  {
    $set: {
      "profile.country_code": "IN",
      schema_version: 2
    }
  }
)
```

Production migrations should generally be:

- Bounded
- Observable
- Restartable
- Idempotent
- Tested
- Measured

For very large collections, avoid blindly running a massive update during peak traffic.

Consider batching by `_id`, time ranges, or another indexed boundary.

## Bulk Migration Pattern

Conceptually:

```text
Find migration batch
      |
      v
Update batch
      |
      v
Record progress
      |
      v
Measure errors
      |
      v
Repeat
```

A migration worker might use:

```python
cursor = collection.find(
    {
        "schema_version": 1,
        "_id": {
            "$gt": last_id
        },
    },
    {
        "_id": 1,
    },
).sort("_id", 1).limit(1000)
```

Then update each batch or construct a bulk operation.

This allows the migration to restart from a known boundary.

## Update Operators and Change Streams

Updates can produce change stream events.

For example:

```javascript
db.orders.updateOne(
  { order_id: "ORD-1001" },
  {
    $set: {
      status: "shipped"
    }
  }
)
```

A change stream consumer may receive an update event.

This can drive:

- Kafka publishing
- Search index synchronization
- Cache invalidation
- Audit processing
- Analytics pipelines

Consumers should be idempotent because event delivery and application processing must account for failures and retries.

## Security Considerations

Update endpoints are a common attack surface.

Protect against:

- Mass assignment
- Unauthorized field modification
- Operator injection
- Cross-tenant updates
- Privilege escalation
- Unbounded array growth
- Arbitrary document replacement

For example, never blindly accept:

```json
{
  "$set": {
    "is_admin": true
  }
}
```

from an untrusted client.

Instead define allowed application fields:

```python
ALLOWED_FIELDS = {
    "display_name",
    "timezone",
    "notification_preferences",
}
```

Then construct the MongoDB update explicitly.

For multi-tenant applications, tenant identity should normally be part of the update filter:

```javascript
db.orders.updateOne(
  {
    tenant_id: "TENANT-100",
    order_id: "ORD-1001"
  },
  {
    $set: {
      status: "shipped"
    }
  }
)
```

Do not rely exclusively on application code outside the database query to identify the tenant.

## Performance Considerations

For update-heavy workloads:

- Keep documents reasonably sized.
- Avoid unnecessary indexes.
- Use targeted filters.
- Prefer atomic operators over read-modify-write.
- Avoid repeatedly updating very large arrays.
- Avoid hot documents where possible.
- Use bulk writes for independent high-volume updates.
- Monitor replication lag.
- Measure write latency.
- Keep transactions short.
- Use appropriate write concern.
- Batch large migrations.

A good update query usually has:

```text
Selective filter
      +
Appropriate index
      +
Targeted update
      +
Bounded document growth
```

## Common Production Pitfalls

### Updating Without a Selective Filter

Dangerous:

```javascript
db.users.updateMany(
  {},
  {
    $set: {
      status: "inactive"
    }
  }
)
```

The empty filter targets every document.

Always verify the filter before a broad update.

### Replacing Nested Documents Accidentally

Dangerous:

```javascript
{
  $set: {
    profile: {
      city: "Mumbai"
    }
  }
}
```

This replaces the existing `profile` object.

Prefer:

```javascript
{
  $set: {
    "profile.city": "Mumbai"
  }
}
```

### Read-Modify-Write for Counters

Avoid:

```text
read → calculate → write
```

Prefer:

```javascript
{
  $inc: {
    counter: 1
  }
}
```

### Unbounded Arrays

Repeatedly using:

```javascript
{
  $push: {
    events: event
  }
}
```

can eventually create oversized, hot documents.

### Overusing `updateMany()`

Large updates can create operational pressure.

Measure the affected population and consider batching.

### Ignoring Update Results

An API should distinguish:

```text
matched = 0
```

from:

```text
matched = 1
modified = 0
```

These can represent very different application conditions.

## Troubleshooting

### Unexpected Fields Disappear

```text
Symptom
↓
Fields inside a nested object disappear after an update
↓
Possible causes
↓
A nested object was replaced with $set instead of updating individual dotted fields
↓
Isolation strategy
↓
Compare the previous document with the exact update document
↓
Diagnostic commands
↓
Inspect the updateOne/updateMany operation and affected document
↓
Root cause
↓
Complete nested object was assigned instead of a nested field
↓
Corrective action
↓
Use dotted paths such as "profile.city"
↓
Prevention
↓
Test partial updates against representative documents
```

### Update Modifies More Documents Than Expected

```text
Symptom
↓
updateMany() changes an unexpectedly large number of documents
↓
Possible causes
↓
Broad filter, missing tenant constraint, incorrect query operator
↓
Isolation strategy
↓
Run the filter with countDocuments() before updating
↓
Diagnostic commands
↓
Use countDocuments() and inspect representative matches
↓
Root cause
↓
Update filter was insufficiently selective
↓
Corrective action
↓
Add required business and tenant predicates
↓
Prevention
↓
Require dry-run/count validation for operational migrations
```

### Counter Has Incorrect Values

```text
Symptom
↓
A counter is inconsistent under concurrent requests
↓
Possible causes
↓
Application-level read-modify-write, duplicate event processing
↓
Isolation strategy
↓
Inspect the update implementation and event-processing semantics
↓
Diagnostic commands
↓
Review $inc usage, application logs, and duplicate event identifiers
↓
Root cause
↓
Concurrent or repeated updates are not handled atomically or idempotently
↓
Corrective action
↓
Use atomic operators and application-level idempotency where required
↓
Prevention
↓
Design counters and distributed consumers for retries and concurrency
```

### Update Is Slow

```text
Symptom
↓
updateOne() or updateMany() has high latency
↓
Possible causes
↓
Poor filter selectivity, missing index, large documents, many index updates, contention
↓
Isolation strategy
↓
Inspect the filter, document size, indexes, and workload concurrency
↓
Diagnostic commands
↓
Use explain() where applicable, inspect indexes and server metrics
↓
Root cause
↓
Database must scan too much data or perform excessive write/index work
↓
Corrective action
↓
Improve filtering/indexing, reduce document growth, or redesign the write path
↓
Prevention
↓
Load-test write patterns and monitor query/write performance
```

## Interview Perspective

### Why are MongoDB update operators important?

They allow targeted modifications without replacing complete documents and support atomic updates to individual documents.

### Why use `$inc` instead of read-modify-write?

`$inc` performs the numeric modification atomically on the server, avoiding a common lost-update race.

### What is the difference between `$push` and `$addToSet`?

`$push` appends values and allows duplicates. `$addToSet` prevents duplicate equivalent values.

### What does `$[]` do?

It targets all elements of an array.

### What does `$[identifier]` do?

It targets array elements satisfying the corresponding `arrayFilters` condition.

### Why can `$set` still delete nested fields?

Because:

```javascript
{
  $set: {
    profile: {
      city: "Mumbai"
    }
  }
}
```

replaces the `profile` object.

To update only one nested field:

```javascript
{
  $set: {
    "profile.city": "Mumbai"
  }
}
```

### Why is a unique index important for upserts?

Concurrent requests can race if uniqueness is enforced only by application-level checks. A unique index provides a database-level invariant.

### When should you use a transaction instead of an update operator?

Use a transaction when multiple documents or collections must change atomically. A transaction is unnecessary for a normal single-document atomic update.

## Practical Update Design Checklist

Before implementing a production update:

- Identify whether the operation is a replacement or partial mutation.
- Prefer update operators for partial changes.
- Use `$inc` for atomic counters.
- Use `$set` for targeted field updates.
- Use dotted paths for nested fields.
- Use `$unset` when the field should no longer exist.
- Use `$addToSet` when array uniqueness matters.
- Bound arrays when embedding is intentional.
- Use filtered positional updates for targeted array mutations.
- Validate update filters before `updateMany()`.
- Include tenant or ownership constraints in multi-tenant systems.
- Enforce uniqueness with indexes rather than application checks alone.
- Use optimistic concurrency when conflicting writes must be detected.
- Keep migrations idempotent and restartable.
- Consider write concern for durability requirements.
- Monitor replication lag during large updates.
- Avoid unnecessarily large documents and hot-document patterns.
- Do not expose raw MongoDB update operators directly through public APIs.

## Key Takeaways

- Use MongoDB update operators for targeted, atomic document mutations; avoid full replacement when the application only owns part of a document.
- `$set`, `$unset`, `$inc`, `$push`, `$addToSet`, `$pull`, and positional operators cover most production update patterns, while pipeline updates handle more complex transformations.
- Treat the update filter as part of the correctness model: combine it with state, tenant, ownership, or version predicates when required for concurrency and authorization.
- Unbounded arrays, hot documents, broad `updateMany()` operations, and read-modify-write patterns are common sources of production problems.
- Production-grade updates require more than correct syntax: consider indexes, write concern, retries, idempotency, schema validation, observability, and migration safety.