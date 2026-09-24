# 05- Arrays

## Overview

Arrays are a core BSON data type in MongoDB and one of the most important tools for modeling related data inside a document.

An array can contain:

- Scalar values
- Embedded documents
- Nested arrays
- ObjectIds
- Mixed BSON values

Example:

```json
{
  "_id": "USR-1001",
  "roles": [
    "developer",
    "team-lead"
  ],
  "skills": [
    {
      "name": "Python",
      "level": "advanced"
    },
    {
      "name": "MongoDB",
      "level": "intermediate"
    }
  ]
}
```

Arrays make MongoDB effective for document-oriented workloads because related values can be retrieved and updated as part of the parent document.

However, arrays are also one of the easiest MongoDB features to misuse.

The most important production concerns are:

- Array cardinality
- Bounded vs unbounded growth
- Query semantics
- `$elemMatch`
- Multikey indexes
- Array update operators
- Write amplification
- Document size
- Hot documents
- Concurrent updates
- Pagination
- Schema evolution

A useful design rule is:

> Embed arrays when their size is reasonably bounded and their elements naturally belong to the parent document. Separate unbounded or independently managed collections.

---

## What Is a MongoDB Array?

A MongoDB array is an ordered collection of BSON values stored inside a document.

Example:

```json
{
  "_id": "USR-1001",
  "roles": [
    "developer",
    "reviewer",
    "team-lead"
  ]
}
```

The array contains three string values.

Arrays can also contain documents:

```json
{
  "_id": "USR-1001",
  "skills": [
    {
      "name": "Python",
      "level": "advanced"
    },
    {
      "name": "MongoDB",
      "level": "intermediate"
    }
  ]
}
```

They can contain numbers:

```json
{
  "scores": [
    95,
    88,
    91
  ]
}
```

And nested arrays:

```json
{
  "matrix": [
    [1, 2],
    [3, 4]
  ]
}
```

MongoDB treats arrays as first-class BSON values and provides specialized query and update operators for them.

---

## Why Arrays Matter in MongoDB

Arrays allow related data to be represented within a single document.

Consider an order:

```json
{
  "_id": "ORD-1001",
  "items": [
    {
      "product_id": "PROD-100",
      "quantity": 2,
      "unit_price": 4999
    },
    {
      "product_id": "PROD-200",
      "quantity": 1,
      "unit_price": 1999
    }
  ]
}
```

A single database read can retrieve:

- Order metadata
- Line items
- Quantities
- Prices

This can reduce application-side joins and database round trips.

Arrays therefore work particularly well when:

```text
Parent
  |
  +-- bounded related elements
```

and the elements are normally accessed together.

---

## Array Modeling Principles

Before adding an array to a production document, evaluate:

| Question | Why it matters |
|---|---|
| Is the array bounded? | Prevents uncontrolled document growth |
| Are elements usually read with the parent? | Determines embedding suitability |
| Are elements independently queried? | May indicate a separate collection |
| Are elements frequently updated? | Can create contention |
| Are elements shared by multiple parents? | May favor references |
| Will the array require indexing? | Affects index size and write cost |
| Will elements grow in size? | Impacts document growth |
| Is element ordering meaningful? | Determines whether order must be preserved |
| Can elements be paginated? | Important for large arrays |
| Do elements have independent lifecycle? | May favor separate documents |

The array itself is not the design decision. The access pattern is.

---

## Arrays of Scalar Values

The simplest array contains scalar values.

```json
{
  "_id": "USR-1001",
  "roles": [
    "developer",
    "reviewer",
    "admin"
  ]
}
```

Typical uses include:

- Tags
- Roles
- Feature flags
- Small lists of identifiers
- Categories
- Supported languages
- Permissions
- Bounded configuration values

Example query:

```javascript
db.users.find({
  roles: "admin"
})
```

MongoDB can match a scalar query value against an array containing that value.

---

## Arrays of Embedded Documents

Arrays become more powerful when each element contains multiple fields.

Example:

```json
{
  "_id": "ORD-1001",
  "items": [
    {
      "product_id": "PROD-100",
      "name": "Keyboard",
      "quantity": 2,
      "unit_price": 4999
    },
    {
      "product_id": "PROD-200",
      "name": "Mouse",
      "quantity": 1,
      "unit_price": 1999
    }
  ]
}
```

This pattern is useful when the elements:

- Belong strongly to the parent
- Are normally retrieved with the parent
- Have bounded cardinality
- Do not require independent lifecycle management

Order line items are a common example.

---

## Array Cardinality

Cardinality means the number of elements in an array.

A useful distinction is:

```text
Low cardinality
    1–10 elements

Moderate cardinality
    tens or hundreds

High cardinality
    thousands or more

Unbounded
    continuously growing
```

These are engineering categories rather than strict MongoDB limits.

The important question is whether the cardinality is predictable.

For example:

```text
User -> roles
```

is normally bounded.

But:

```text
User -> activity events
```

may be unbounded.

Embedding the first is usually reasonable.

Embedding the second can create a serious production problem.

---

## Bounded Arrays

A bounded array has a practical upper limit.

Example:

```json
{
  "_id": "USR-1001",
  "addresses": [
    {
      "type": "home"
    },
    {
      "type": "office"
    },
    {
      "type": "billing"
    }
  ]
}
```

There may be a business rule such as:

```text
Maximum addresses per user = 10
```

This makes the growth predictable.

Bounded arrays are strong candidates for embedding.

---

## Unbounded Arrays

An unbounded array can grow indefinitely.

Avoid designs such as:

```json
{
  "_id": "USR-1001",
  "events": [
    "... every user event ever ..."
  ]
}
```

As the array grows:

- The document becomes larger.
- Reads become more expensive.
- Updates become more expensive.
- Network payloads increase.
- Memory pressure increases.
- Replication traffic increases.
- Indexes can become larger.
- The document may become a hot write target.
- The BSON document-size limit becomes relevant.

Instead, use a separate collection:

```json
{
  "_id": "EVT-1001",
  "user_id": "USR-1001",
  "type": "login",
  "created_at": "..."
}
```

with an index:

```javascript
db.events.createIndex({
  user_id: 1,
  created_at: -1
})
```

---

## Array Ordering

MongoDB arrays preserve element order.

Example:

```json
{
  "steps": [
    "validate",
    "authorize",
    "process",
    "complete"
  ]
}
```

The order may be part of the domain.

However, do not assume that array order is automatically maintained after arbitrary update operations.

If ordering is semantically important, application logic should explicitly maintain it.

For complex ordering requirements, consider storing an explicit field:

```json
{
  "steps": [
    {
      "position": 1,
      "name": "validate"
    },
    {
      "position": 2,
      "name": "authorize"
    }
  ]
}
```

This can make ordering rules easier to reason about during updates and migrations.

---

## Querying Arrays

MongoDB supports several ways to query arrays.

Given:

```json
{
  "_id": "USR-1001",
  "roles": [
    "developer",
    "team-lead"
  ]
}
```

this query:

```javascript
db.users.find({
  roles: "developer"
})
```

matches the document.

MongoDB automatically checks array elements when comparing a scalar query value against an array field.

---

## Exact Array Matching

MongoDB can also match an array as a whole.

For example:

```javascript
db.users.find({
  roles: [
    "developer",
    "team-lead"
  ]
})
```

This is different from:

```javascript
db.users.find({
  roles: "developer"
})
```

The first expresses a much stronger condition involving the array value itself.

When array ordering and exact contents matter, be explicit about the intended semantics.

Do not confuse:

```text
contains a value
```

with:

```text
has exactly this array
```

---

## `$in`

`$in` matches documents where a field equals one of the specified values.

Example:

```javascript
db.users.find({
  roles: {
    $in: [
      "admin",
      "team-lead"
    ]
  }
})
```

This is useful when searching for documents containing at least one matching array element.

Example use cases:

- Users with one of several roles
- Products with one of several categories
- Orders containing one of several product IDs

---

## `$nin`

`$nin` matches documents where a field does not match any specified value.

Example:

```javascript
db.users.find({
  roles: {
    $nin: [
      "suspended",
      "blocked"
    ]
  }
})
```

Use `$nin` carefully because negative predicates can be less selective and may not provide the same performance characteristics as highly selective positive predicates.

Always validate important queries with `explain()`.

---

## `$all`

`$all` requires an array to contain all specified values.

Example:

```javascript
db.products.find({
  tags: {
    $all: [
      "backend",
      "database"
    ]
  }
})
```

A document containing:

```json
{
  "tags": [
    "backend",
    "database",
    "mongodb"
  ]
}
```

matches the query.

This is useful for set-like membership requirements.

---

## `$size`

`$size` matches arrays with a specific number of elements.

Example:

```javascript
db.users.find({
  roles: {
    $size: 3
  }
})
```

This is useful for validation and specialized queries.

However, `$size` queries should not automatically be assumed to be index-friendly.

For high-volume production queries, validate the execution plan.

---

## `$elemMatch`

`$elemMatch` is one of the most important MongoDB array operators.

Consider:

```json
{
  "_id": "ORD-1001",
  "items": [
    {
      "product_id": "PROD-100",
      "quantity": 2,
      "status": "active"
    },
    {
      "product_id": "PROD-200",
      "quantity": 1,
      "status": "cancelled"
    }
  ]
}
```

Suppose the requirement is:

> Find orders containing a single item where `product_id = PROD-100` and `quantity >= 2`.

Use:

```javascript
db.orders.find({
  items: {
    $elemMatch: {
      product_id: "PROD-100",
      quantity: {
        $gte: 2
      }
    }
  }
})
```

`$elemMatch` ensures that the conditions apply to the same array element.

---

## Why `$elemMatch` Matters

Without `$elemMatch`, a query such as:

```javascript
db.orders.find({
  "items.product_id": "PROD-100",
  "items.quantity": {
    $gte: 2
  }
})
```

can satisfy the conditions using different array elements.

Conceptually:

```text
Item A
product_id = PROD-100
quantity = 1

Item B
product_id = PROD-200
quantity = 5
```

The document may satisfy the separate predicates even though no single item satisfies both conditions.

`$elemMatch` expresses the intended relationship:

```text
same array element
        |
        +-- product_id = PROD-100
        +-- quantity >= 2
```

This is a common MongoDB interview and production query-design issue.

---

## Querying Nested Arrays

Consider:

```json
{
  "teams": [
    {
      "name": "platform",
      "members": [
        {
          "name": "Alice",
          "role": "lead"
        }
      ]
    }
  ]
}
```

Nested arrays can be queried using nested field paths:

```javascript
db.organizations.find({
  "teams.members.role": "lead"
})
```

However, deeply nested arrays increase:

- Query complexity
- Index complexity
- Update complexity
- Schema migration difficulty

If a model repeatedly requires multiple levels of nested arrays, reconsider whether the document structure matches the application's access patterns.

---

## Array Update Operators

MongoDB provides specialized operators for modifying arrays.

Important operators include:

| Operator | Purpose |
|---|---|
| `$push` | Add an element |
| `$addToSet` | Add only if not already present |
| `$pop` | Remove first or last element |
| `$pull` | Remove elements matching a condition |
| `$pullAll` | Remove specified values |
| `$push` with `$each` | Add multiple values |
| `$push` with `$slice` | Limit array size |
| `$push` with `$sort` | Sort pushed elements |
| Positional `$` | Update matching array element |
| `$[]` | Update all array elements |
| `$[identifier]` | Update filtered array elements |

These operators allow MongoDB to modify arrays without replacing the entire document.

---

## `$push`

`$push` appends an element to an array.

Example:

```javascript
db.users.updateOne(
  {
    _id: "USR-1001"
  },
  {
    $push: {
      roles: "reviewer"
    }
  }
)
```

This is appropriate when duplicates are acceptable.

For example, if an event history intentionally allows repeated events:

```text
login
login
logout
login
```

`$push` may be appropriate.

---

## `$addToSet`

`$addToSet` adds a value only if it does not already exist.

Example:

```javascript
db.users.updateOne(
  {
    _id: "USR-1001"
  },
  {
    $addToSet: {
      roles: "developer"
    }
  }
)
```

This is useful for set-like data.

Example:

```text
tags
roles
feature flags
supported capabilities
```

Do not use `$addToSet` when duplicate entries are meaningful.

---

## `$push` with `$each`

Multiple values can be appended with `$each`.

```javascript
db.users.updateOne(
  {
    _id: "USR-1001"
  },
  {
    $push: {
      roles: {
        $each: [
          "developer",
          "reviewer"
        ]
      }
    }
  }
)
```

This can be more efficient and expressive than issuing multiple updates.

---

## `$push` with `$slice`

`$slice` can keep an array bounded.

Example:

```javascript
db.users.updateOne(
  {
    _id: "USR-1001"
  },
  {
    $push: {
      recent_logins: {
        $each: [
          {
            timestamp: new Date()
          }
        ],
        $slice: -10
      }
    }
  }
)
```

This maintains only the latest ten entries.

This is useful for bounded operational data such as:

- Recent events
- Recent login attempts
- Recent status changes
- Recent notifications

However, if the business requirement requires complete history, truncating the array is incorrect. Store the complete history separately.

---

## `$push` with `$sort`

Arrays of documents can be sorted while adding elements.

Example:

```javascript
db.products.updateOne(
  {
    _id: "PROD-100"
  },
  {
    $push: {
      reviews: {
        $each: [
          {
            user_id: "USR-100",
            rating: 5
          }
        ],
        $sort: {
          rating: -1
        }
      }
    }
  }
)
```

This can be useful for maintaining bounded top-N collections.

For example:

```text
Top 10 scores
Top 5 offers
Recent 20 events
```

Combine `$sort` and `$slice` when a bounded sorted array is required.

---

## `$pop`

`$pop` removes one element from an array.

Remove the last element:

```javascript
db.users.updateOne(
  {
    _id: "USR-1001"
  },
  {
    $pop: {
      roles: 1
    }
  }
)
```

Remove the first element:

```javascript
db.users.updateOne(
  {
    _id: "USR-1001"
  },
  {
    $pop: {
      roles: -1
    }
  }
)
```

Use this when the array behaves like a queue or stack and the ordering semantics are explicit.

---

## `$pull`

`$pull` removes array elements matching a condition.

Example:

```javascript
db.users.updateOne(
  {
    _id: "USR-1001"
  },
  {
    $pull: {
      roles: "deprecated-role"
    }
  }
)
```

For arrays of documents:

```javascript
db.orders.updateOne(
  {
    _id: "ORD-1001"
  },
  {
    $pull: {
      items: {
        status: "cancelled"
      }
    }
  }
)
```

This removes all matching elements.

---

## `$pullAll`

`$pullAll` removes specified values.

```javascript
db.users.updateOne(
  {
    _id: "USR-1001"
  },
  {
    $pullAll: {
      roles: [
        "legacy-user",
        "legacy-reviewer"
      ]
    }
  }
)
```

Use it when a fixed set of values should be removed.

---

## Positional `$` Operator

The positional `$` operator updates the first array element that matches the query condition.

Example:

```javascript
db.orders.updateOne(
  {
    _id: "ORD-1001",
    "items.product_id": "PROD-100"
  },
  {
    $set: {
      "items.$.quantity": 3
    }
  }
)
```

The matching item is updated.

This is useful for targeted updates when the query identifies the desired array element.

---

## `$[]` All-Elements Operator

`$[]` applies an update to all elements in an array.

Example:

```javascript
db.users.updateOne(
  {
    _id: "USR-1001"
  },
  {
    $set: {
      "addresses.$[].verified": false
    }
  }
)
```

Every address is updated.

Use this carefully on large arrays because one operation may modify many embedded elements.

---

## Filtered Positional `$[identifier]`

Filtered positional updates allow updates to matching array elements.

Example:

```javascript
db.orders.updateOne(
  {
    _id: "ORD-1001"
  },
  {
    $set: {
      "items.$[item].status": "backordered"
    }
  },
  {
    arrayFilters: [
      {
        "item.quantity": {
          $gt: 10
        }
      }
    ]
  }
)
```

Only matching items are updated.

This is useful for targeted updates without reading the entire document into the application.

---

## Python Array Updates with PyMongo

PyMongo exposes MongoDB's array update operators directly.

```python
from pymongo.collection import Collection


def add_role(collection: Collection, user_id: str, role: str) -> bool:
    result = collection.update_one(
        {"_id": user_id},
        {
            "$addToSet": {
                "roles": role,
            }
        },
    )

    return result.matched_count == 1
```

For bounded recent events:

```python
def record_login(collection: Collection, user_id: str, event: dict) -> bool:
    result = collection.update_one(
        {"_id": user_id},
        {
            "$push": {
                "recent_logins": {
                    "$each": [event],
                    "$slice": -10,
                }
            }
        },
    )

    return result.modified_count == 1
```

The database performs the array update atomically within the document.

---

## Array Indexing

MongoDB automatically supports indexing array fields through **multikey indexes**.

Example:

```json
{
  "_id": "PROD-100",
  "tags": [
    "backend",
    "database",
    "mongodb"
  ]
}
```

Index:

```javascript
db.products.createIndex({
  tags: 1
})
```

MongoDB can use this index for queries such as:

```javascript
db.products.find({
  tags: "mongodb"
})
```

A multikey index allows MongoDB to index array elements rather than requiring an application-side scan of every array.

---

## Multikey Indexes

An index becomes multikey when it indexes an array field.

For example:

```javascript
db.products.createIndex({
  "tags": 1
})
```

when `tags` is an array.

Conceptually:

```text
Document
  |
  +-- tags
       |
       +-- backend
       +-- database
       +-- mongodb
```

produces index entries associated with the individual array values.

This makes array queries efficient, but increases index complexity and potentially index size.

---

## Compound Indexes with Arrays

Suppose:

```json
{
  "tenant_id": "TENANT-1",
  "tags": [
    "backend",
    "mongodb"
  ],
  "status": "active"
}
```

A compound index might be:

```javascript
db.products.createIndex({
  tenant_id: 1,
  tags: 1,
  status: 1
})
```

This can be useful for appropriate query patterns.

However, compound multikey indexes have important restrictions and design considerations.

In particular, MongoDB has restrictions around indexing multiple array fields within the same compound index when a document would cause multiple multikey paths.

Before creating such an index, verify the actual schema and MongoDB version behavior.

---

## Multikey Index Performance

Array indexes can become large.

Consider:

```text
10 million documents
        |
        +-- average 20 tags
```

The index may represent a much larger number of indexed values than the number of documents.

Potential consequences:

- Larger disk usage
- More memory pressure
- More index maintenance during writes
- Longer index builds
- Increased replication impact during index-related operations

This is why array cardinality must be considered when designing indexes.

---

## Array Index Selectivity

An array index is useful when the query is selective enough to reduce the number of examined documents.

Suppose:

```javascript
db.products.find({
  tags: "mongodb"
})
```

matches 80% of the collection.

An index may provide limited benefit because the predicate is not selective.

If:

```javascript
db.products.find({
  tags: "rare-specialized-feature"
})
```

matches 0.01% of the collection, the index may be much more useful.

Always evaluate actual workload characteristics.

---

## Covered Queries and Arrays

Covered-query behavior becomes more complicated when arrays are involved.

A query can only be considered covered under the appropriate MongoDB conditions, and multikey indexes introduce additional restrictions.

Do not assume that:

```javascript
db.products.find(
  {
    tags: "mongodb"
  },
  {
    tags: 1,
    _id: 0
  }
)
```

will automatically be covered simply because the index contains `tags`.

Validate with:

```javascript
db.products.find(
  {
    tags: "mongodb"
  },
  {
    tags: 1,
    _id: 0
  }
).explain("executionStats")
```

Use the actual execution plan rather than relying on assumptions.

---

## Querying Arrays of Documents

Consider:

```json
{
  "_id": "ORD-1001",
  "items": [
    {
      "product_id": "PROD-100",
      "quantity": 2,
      "price": 4999
    },
    {
      "product_id": "PROD-200",
      "quantity": 1,
      "price": 1999
    }
  ]
}
```

Find orders containing a product:

```javascript
db.orders.find({
  "items.product_id": "PROD-100"
})
```

Find orders where the same item has both conditions:

```javascript
db.orders.find({
  items: {
    $elemMatch: {
      product_id: "PROD-100",
      quantity: {
        $gte: 2
      }
    }
  }
})
```

This distinction should be part of any production engineer's MongoDB query knowledge.

---

## Array Projection

Projection can reduce the amount of array data returned.

For example:

```javascript
db.orders.find(
  {
    _id: "ORD-1001"
  },
  {
    "items.product_id": 1,
    "items.quantity": 1
  }
)
```

For specific array elements, MongoDB provides additional projection capabilities depending on the query requirements and MongoDB version.

The general principle remains:

> Do not transfer an entire large array when the endpoint only needs a small subset.

---

## `$slice` Projection

`$slice` can return a subset of array elements.

Example:

```javascript
db.users.find(
  {
    _id: "USR-1001"
  },
  {
    recent_events: {
      $slice: 10
    }
  }
)
```

This is useful for bounded views such as:

```text
latest 10 events
latest 20 notifications
first 5 recommendations
```

However, `$slice` is not a substitute for proper pagination of an unbounded dataset.

If the array is continuously growing, the underlying data model should usually be reconsidered.

---

## Array Pagination

Traditional pagination using:

```text
skip + limit
```

is not ideal for very large embedded arrays.

For example:

```javascript
db.users.find(
  {
    _id: "USR-1001"
  },
  {
    events: {
      $slice: [10000, 20]
    }
  }
)
```

may become increasingly awkward as the array grows.

For large event histories, use a separate collection:

```text
events
  |
  +-- user_id
  +-- created_at
  +-- event_id
```

and paginate using a stable indexed cursor:

```text
created_at + event_id
```

This scales better than treating a large embedded array as a database table.

---

## Array Sorting

Arrays can contain values that need ordering.

For example:

```json
{
  "scores": [
    91,
    87,
    99
  ]
}
```

Sorting the document results:

```javascript
db.students.find().sort({
  scores: -1
})
```

is not the same as sorting the elements inside each array.

Array element ordering and document result ordering are separate concepts.

When array order itself matters, maintain it explicitly through:

- Application logic
- `$push` with `$sort`
- Explicit position fields
- Aggregation transformations

---

## `$unwind`

`$unwind` transforms each array element into a separate pipeline document.

Example:

```json
{
  "_id": "ORD-1001",
  "items": [
    {
      "product_id": "PROD-100",
      "quantity": 2
    },
    {
      "product_id": "PROD-200",
      "quantity": 1
    }
  ]
}
```

Pipeline:

```javascript
db.orders.aggregate([
  {
    $unwind: "$items"
  }
])
```

Conceptually:

```text
Order
  |
  +-- Item A
  +-- Item B
```

becomes:

```text
Order + Item A
Order + Item B
```

This is useful for:

- Aggregating array elements
- Counting items
- Grouping by embedded values
- Filtering individual array elements
- Joining array elements with another collection

---

## `$unwind` Performance

`$unwind` can multiply the number of pipeline documents.

If:

```text
1 million orders
x
50 items/order
```

then an `$unwind` stage may conceptually produce up to:

```text
50 million pipeline records
```

before subsequent filtering and grouping.

Therefore:

- Filter early.
- Avoid unnecessary `$unwind`.
- Use `$match` before `$unwind` where possible.
- Project only required fields.
- Measure large pipelines with `explain()`.

A compact embedded representation can still generate a large intermediate aggregation workload.

---

## Arrays and Aggregation

Arrays interact heavily with aggregation expressions.

Common array-related operators include:

- `$arrayElemAt`
- `$concatArrays`
- `$filter`
- `$map`
- `$reduce`
- `$size`
- `$slice`
- `$in`
- `$indexOfArray`
- `$setUnion`
- `$setIntersection`

Example:

```javascript
db.orders.aggregate([
  {
    $project: {
      order_id: "$_id",
      item_count: {
        $size: "$items"
      }
    }
  }
])
```

This computes the number of items in each order.

---

## `$filter`

`$filter` returns only array elements matching a condition.

Example:

```javascript
db.orders.aggregate([
  {
    $project: {
      active_items: {
        $filter: {
          input: "$items",
          as: "item",
          cond: {
            $eq: [
              "$$item.status",
              "active"
            ]
          }
        }
      }
    }
  }
])
```

This is useful when an API or reporting pipeline needs a filtered subset of an embedded array.

---

## `$map`

`$map` transforms each array element.

Example:

```javascript
db.orders.aggregate([
  {
    $project: {
      product_ids: {
        $map: {
          input: "$items",
          as: "item",
          in: "$$item.product_id"
        }
      }
    }
  }
])
```

This produces:

```json
{
  "product_ids": [
    "PROD-100",
    "PROD-200"
  ]
}
```

`$map` is useful for projections and transformations without requiring application-side processing.

---

## `$reduce`

`$reduce` can aggregate array elements into a single value.

For example, calculate an order subtotal:

```javascript
db.orders.aggregate([
  {
    $project: {
      subtotal: {
        $reduce: {
          input: "$items",
          initialValue: 0,
          in: {
            $add: [
              "$$value",
              {
                $multiply: [
                  "$$this.quantity",
                  "$$this.unit_price"
                ]
              }
            ]
          }
        }
      }
    }
  }
])
```

For financial calculations, ensure that the underlying numeric types provide the required precision.

---

## Arrays and Atomic Updates

MongoDB's single-document atomicity makes array updates particularly useful.

For example:

```javascript
db.users.updateOne(
  {
    _id: "USR-1001"
  },
  {
    $addToSet: {
      roles: "developer"
    }
  }
)
```

The application does not need to:

1. Read the document.
2. Check whether the role exists.
3. Modify the Python list.
4. Write the entire document back.

The database can perform the operation atomically.

This reduces race conditions compared with application-side read-modify-write logic.

---

## Concurrency and Array Updates

Consider two workers:

```text
Worker A
    |
    +-- add role "reviewer"

Worker B
    |
    +-- add role "admin"
```

Using atomic update operators allows MongoDB to apply these changes without requiring the application to coordinate the entire document state.

Prefer:

```javascript
$push
$addToSet
$pull
$set
```

over application-side replacement when the operation can be expressed directly.

This is especially important in:

- FastAPI applications
- Celery workers
- Kubernetes deployments
- Event consumers
- Kafka consumers
- Horizontally scaled microservices

---

## Arrays and Hot Documents

An array can turn its parent document into a hot document.

Example:

```json
{
  "_id": "COUNTER-1",
  "recent_events": []
}
```

If thousands of workers continuously append events:

```text
Worker 1 ----\
Worker 2 -----\
Worker 3 ------> same document
Worker N -----/
```

the document becomes a write contention point.

Possible alternatives include:

```text
Parent document
      |
      +-- bounded recent array

Events collection
      |
      +-- complete history
```

This hybrid design often provides both:

- Fast access to recent state
- Scalable historical storage

---

## Bucket Pattern for Large Event Arrays

The bucket pattern can be used when a logical sequence is large but can be partitioned into bounded documents.

Instead of:

```text
user
 └── millions of events
```

use:

```text
event bucket 1
 ├── event 1
 ├── event 2
 └── ...

event bucket 2
 ├── event N
 ├── event N+1
 └── ...
```

Example:

```json
{
  "_id": "USR-1001:2026-09-21",
  "user_id": "USR-1001",
  "date": "2026-09-21",
  "events": [
    {},
    {},
    {}
  ]
}
```

The bucket boundary should be chosen based on:

- Expected event volume
- Query patterns
- Document size
- Retention
- Write rate
- Operational requirements

---

## Arrays in Event-Driven Systems

Arrays can represent small sets of state, but they should not automatically become event logs.

For example:

```json
{
  "_id": "JOB-1001",
  "recent_attempts": [
    {
      "attempt": 1,
      "status": "failed"
    },
    {
      "attempt": 2,
      "status": "success"
    }
  ]
}
```

This is reasonable when only recent attempts are needed.

For a complete audit trail, use a dedicated collection or event platform:

```text
Application
    |
    v
Kafka
    |
    +--> MongoDB events
    |
    +--> Analytics
```

A bounded array is state.

A complete event history is a different workload.

---

## Arrays and Schema Validation

Array element types can be validated.

Example:

```javascript
db.createCollection("users", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["roles"],
      properties: {
        roles: {
          bsonType: "array",
          items: {
            bsonType: "string"
          }
        }
      }
    }
  }
})
```

For arrays of documents:

```javascript
db.createCollection("orders", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["items"],
      properties: {
        items: {
          bsonType: "array",
          items: {
            bsonType: "object",
            required: [
              "product_id",
              "quantity"
            ],
            properties: {
              product_id: {
                bsonType: "string"
              },
              quantity: {
                bsonType: "int"
              }
            }
          }
        }
      }
    }
  }
})
```

This protects against accidental schema drift.

---

## Arrays and API Contracts

An API should distinguish between:

```json
{
  "roles": []
}
```

and:

```json
{}
```

if the API contract assigns different meanings to an empty array and a missing field.

For example:

```text
roles: []
    -> user has no roles

roles missing
    -> roles field unavailable / legacy document
```

Choose one contract deliberately.

In FastAPI/Pydantic models, make optionality and defaults explicit.

```python
from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    roles: list[str] = Field(default_factory=list)
```

This can provide a stable API representation even when legacy MongoDB documents have inconsistent fields.

---

## Arrays in FastAPI

A typical request model may use:

```python
from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str
    tags: list[str] = Field(default_factory=list)
```

The service layer can then persist:

```python
document = {
    "name": payload.name,
    "tags": payload.tags,
}
```

For arrays of documents:

```python
class OrderItem(BaseModel):
    product_id: str
    quantity: int
    unit_price: int


class OrderCreate(BaseModel):
    items: list[OrderItem]
```

Application-level validation can enforce business rules such as:

```text
quantity > 0
maximum number of items
required item fields
allowed statuses
```

while MongoDB schema validation provides a database-level contract.

---

## Arrays and Django

When using MongoDB from Django through PyMongo or MongoEngine, array behavior should be modeled explicitly.

Do not assume Django's relational ORM semantics apply to MongoDB arrays.

A MongoDB array:

```json
{
  "roles": [
    "developer",
    "reviewer"
  ]
}
```

is not equivalent to a relational many-to-many table.

A relational model might use:

```text
users
roles
user_roles
```

MongoDB can instead embed bounded role data when that better matches the application's access patterns.

The choice should be made at the persistence-model level rather than by attempting to force relational ORM behavior onto MongoDB.

---

## Arrays and Security

Arrays can contain sensitive information:

```json
{
  "user_id": "USR-1001",
  "permissions": [
    "billing:read",
    "billing:write"
  ]
}
```

Avoid returning sensitive arrays blindly from APIs.

Use:

- Projection
- Explicit response models
- Authorization checks
- Field-level access rules where required

Also consider array growth as a potential denial-of-service vector if untrusted users can continuously append data.

For example:

```text
POST /profile/tags
```

should not allow unlimited array growth without validation and limits.

---

## Arrays and Resource Limits

Production APIs should impose sensible limits on array input.

For example:

```python
from pydantic import BaseModel, Field


class UserUpdate(BaseModel):
    tags: list[str] = Field(
        default_factory=list,
        max_length=50,
    )
```

Limits should exist at multiple layers where appropriate:

```text
API validation
      |
      v
Service-layer validation
      |
      v
Database schema validation
```

This reduces the risk of unexpectedly large documents.

---

## Array Performance Considerations

Array performance depends on:

- Number of elements
- Element size
- Query selectivity
- Index design
- Update frequency
- Document size
- Projection
- Aggregation pipeline
- Working set size

A small array:

```text
5 roles
```

is operationally very different from:

```text
50,000 events
```

Even though both are technically BSON arrays.

Do not judge array suitability based solely on whether the data fits in one document.

---

## Measuring Array Query Performance

Use `explain()` for important production queries.

Example:

```javascript
db.orders.find({
  items: {
    $elemMatch: {
      product_id: "PROD-100",
      quantity: {
        $gte: 2
      }
    }
  }
}).explain("executionStats")
```

Inspect:

```text
nReturned
totalKeysExamined
totalDocsExamined
executionTimeMillis
```

A useful baseline is:

```text
totalDocsExamined
        |
        v
should be reasonably close to
        |
        v
nReturned
```

The exact relationship depends on the query and workload, but a large discrepancy can indicate inefficient filtering or indexing.

---

## Array Index Lifecycle

When adding an array index:

1. Identify the production query.
2. Measure the current execution plan.
3. Design the index around the query shape.
4. Estimate index size.
5. Build the index safely.
6. Validate the new plan.
7. Monitor write and memory impact.
8. Remove unused indexes only after sufficient observation.

Do not create indexes simply because an array field is frequently mentioned in application code.

---

## Common Array Anti-Patterns

### Unbounded History

```json
{
  "events": [
    "... forever ..."
  ]
}
```

Use a separate collection or bucket pattern.

### Huge Embedded Arrays

Large arrays increase read, write, replication, and memory costs.

### High-Frequency Updates

Repeatedly modifying one large parent document can create a hot document.

### Arrays of Shared Entities

Embedding a frequently changing shared entity across thousands of documents creates synchronization overhead.

### Treating Arrays as Relational Tables

If every operation independently queries, updates, deletes, and paginates array elements, the array may actually represent a separate collection.

### Blind `$push`

Using `$push` without a size bound can cause uncontrolled growth.

### Incorrect `$elemMatch` Usage

Failing to use `$elemMatch` when multiple predicates must apply to the same array element can produce incorrect results.

### Over-Indexing Arrays

Large multikey indexes can increase storage and write costs significantly.

---

## Troubleshooting Array Problems

Use the following workflow:

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

### Slow Array Query

```text
Symptom
↓
High query latency
↓
Possible causes
↓
Missing/inefficient multikey index, low selectivity, large documents
↓
Isolation strategy
↓
Run explain("executionStats")
↓
Diagnostic commands
↓
Inspect nReturned, totalKeysExamined, totalDocsExamined
↓
Root cause
↓
Poor query/index alignment
↓
Corrective action
↓
Redesign index or query
↓
Prevention
↓
Query performance regression testing
```

### Array Growing Too Large

```text
Symptom
↓
Large documents and increasing write latency
↓
Possible causes
↓
Unbounded array growth
↓
Isolation strategy
↓
Measure array cardinality and document size
↓
Diagnostic commands
↓
Collection/document statistics
↓
Root cause
↓
Array incorrectly modeled as permanent embedded history
↓
Corrective action
↓
Separate collection or bucket pattern
↓
Prevention
↓
Explicit cardinality limits and schema review
```

### Incorrect Query Results

```text
Symptom
↓
Query matches unexpected documents
↓
Possible causes
↓
Multiple predicates applied across different array elements
↓
Isolation strategy
↓
Test documents with multiple contrasting array elements
↓
Root cause
↓
Missing $elemMatch
↓
Corrective action
↓
Use $elemMatch when predicates must apply to one element
↓
Prevention
↓
Array query tests covering cross-element cases
```

---

## Interview Perspective

Senior MongoDB interviews frequently use arrays to test whether an engineer understands document modeling rather than only MongoDB syntax.

Common questions include:

- When should you embed an array?
- What is the difference between bounded and unbounded arrays?
- Why are unbounded arrays dangerous?
- What is a multikey index?
- How does `$elemMatch` work?
- Why can separate predicates on an array produce unexpected results?
- When should you use `$push` versus `$addToSet`?
- How would you maintain only the latest 10 elements?
- How would you update one element inside an array?
- What is the difference between `$`, `$[]`, and `$[identifier]`?
- How does `$unwind` affect aggregation performance?
- How would you paginate a large array?
- When should an array become a separate collection?
- How can arrays create hot documents?
- How do arrays affect index size?

A strong senior-level answer should connect array usage to:

```text
Cardinality
+
Access patterns
+
Indexing
+
Document size
+
Write frequency
+
Concurrency
+
Consistency
+
API behavior
```

---

## Production Design Checklist

Before introducing an array into a MongoDB document, verify:

- The maximum practical array size is understood.
- The array has a clear ownership boundary.
- The array elements are normally accessed with the parent.
- The array does not represent unbounded historical data.
- Update frequency is acceptable for the parent document.
- Required query patterns have been identified.
- Multikey index requirements have been evaluated.
- Array element types are consistent.
- Schema validation is considered.
- API input limits exist where users can control array growth.
- Projection is used for large arrays.
- `$elemMatch` is used where same-element matching is required.
- Aggregation workloads involving `$unwind` have been measured.
- Document growth is monitored.
- A migration strategy exists if cardinality assumptions change.

---

## Key Takeaways

- Arrays are powerful for bounded, parent-owned data that is commonly read together, but unbounded arrays should generally be modeled as separate collections or bounded buckets.
- Use MongoDB's array operators such as `$push`, `$addToSet`, `$pull`, `$`, `$[]`, and `$[identifier]` to perform targeted atomic updates instead of application-side read-modify-write operations.
- `$elemMatch` is essential when multiple predicates must match the same element of an array of documents.
- Array indexes are multikey indexes and can significantly increase index size and write overhead, so query patterns, cardinality, selectivity, and `explain()` results should drive index design.
- Treat array cardinality, document growth, hot-document risk, API limits, and aggregation costs as production design constraints rather than implementation details.