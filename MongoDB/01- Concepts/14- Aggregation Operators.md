# 14- Aggregation Operators

## Overview

MongoDB aggregation operators are the expressions and accumulators used inside aggregation pipeline stages to filter, transform, calculate, group, compare, manipulate arrays, process dates, and construct derived documents.

A pipeline stage defines **where** an operation occurs, while an aggregation operator defines **what computation is performed**.

For example:

```javascript
{
  $project: {
    order_id: 1,
    net_total: {
      $subtract: [
        "$total",
        "$discount"
      ]
    }
  }
}
```

Here:

- `$project` is the pipeline stage.
- `$subtract` is the aggregation expression operator.
- `$total` and `$discount` are field references.
- The resulting `net_total` becomes part of the transformed document.

This distinction is important:

```text
Pipeline Stage
      |
      v
Defines document-processing operation
      |
      v
Aggregation Expression
      |
      v
Calculates values
      |
      v
Output document
```

Aggregation operators become especially important when pipelines move beyond simple filtering and grouping. Senior backend engineers should understand not only what an operator does, but also:

- How it changes document shape.
- Whether it changes document cardinality.
- Whether it can increase memory usage.
- Whether it can prevent index usage.
- Whether the computation belongs in MongoDB or the application.
- How null, missing, and type variations behave.
- How the operator affects production latency and scalability.

## Operators vs Pipeline Stages

A common source of confusion is treating all `$`-prefixed MongoDB constructs as the same thing.

| Type | Examples | Purpose |
|---|---|---|
| Pipeline stage | `$match`, `$group`, `$sort` | Controls document processing |
| Expression operator | `$add`, `$subtract`, `$cond` | Calculates values |
| Accumulator | `$sum`, `$avg`, `$push` | Aggregates values across grouped documents |
| Query operator | `$gt`, `$in`, `$exists` | Filters documents in queries |
| Update operator | `$set`, `$inc`, `$push` | Modifies stored documents |

For example:

```javascript
{
  $group: {
    _id: "$customer_id",
    total_revenue: {
      $sum: "$total"
    }
  }
}
```

contains:

- `$group` → pipeline stage
- `$sum` → accumulator
- `$customer_id` → field reference
- `$total` → field reference

The same `$set` name can also appear in different contexts. In an aggregation pipeline, `$set` is a pipeline stage. In an update operation, `$set` is an update operator.

Context matters.

## Field References

Aggregation expressions refer to document fields using `$` prefixes.

Given:

```json
{
  "price": 100,
  "quantity": 3
}
```

the following expression references those fields:

```javascript
{
  $multiply: [
    "$price",
    "$quantity"
  ]
}
```

The result is:

```text
300
```

### Nested Fields

Nested fields use dot notation:

```javascript
"$customer.address.city"
```

Example:

```javascript
{
  $project: {
    customer_city: "$customer.address.city"
  }
}
```

### Literal Values

If an expression needs a literal string that starts with `$`, use `$literal`.

```javascript
{
  $project: {
    value: {
      $literal: "$notAField"
    }
  }
}
```

Without `$literal`, MongoDB interprets `$notAField` as a field reference.

## Expression Evaluation

Expressions can be nested.

```javascript
{
  $project: {
    final_price: {
      $multiply: [
        {
          $subtract: [
            "$price",
            "$discount"
          ]
        },
        "$quantity"
      ]
    }
  }
}
```

Conceptually:

```text
price - discount
       |
       v
quantity × discounted price
       |
       v
final_price
```

This composability allows complex calculations without moving intermediate data into application memory.

However, deeply nested expressions can become difficult to maintain. Complex business rules should be evaluated for maintainability as well as database performance.

## Arithmetic Operators

Arithmetic operators perform numerical calculations.

| Operator | Purpose |
|---|---|
| `$add` | Addition |
| `$subtract` | Subtraction |
| `$multiply` | Multiplication |
| `$divide` | Division |
| `$mod` | Modulo |
| `$abs` | Absolute value |
| `$ceil` | Round upward |
| `$floor` | Round downward |
| `$round` | Round to a specified place |
| `$trunc` | Truncate to a specified place |
| `$exp` | Exponential |
| `$ln` | Natural logarithm |
| `$log` | Logarithm |
| `$log10` | Base-10 logarithm |
| `$pow` | Power |
| `$sqrt` | Square root |

## `$add`

Adds numeric values.

```javascript
{
  $project: {
    subtotal: {
      $add: [
        "$item_total",
        "$shipping_cost"
      ]
    }
  }
}
```

It can also be used with dates for date arithmetic where supported by the expression semantics.

## `$subtract`

Subtracts one value from another.

```javascript
{
  $project: {
    discount_amount: {
      $subtract: [
        "$original_price",
        "$final_price"
      ]
    }
  }
}
```

A common backend use is calculating durations between dates.

```javascript
{
  $project: {
    processing_ms: {
      $subtract: [
        "$completed_at",
        "$started_at"
      ]
    }
  }
}
```

When working with dates, make the unit explicit in application logic and API contracts.

## `$multiply`

```javascript
{
  $project: {
    line_total: {
      $multiply: [
        "$unit_price",
        "$quantity"
      ]
    }
  }
}
```

This is common for:

- Invoice calculations
- Order totals
- Usage billing
- Inventory valuation

Financial calculations require careful consideration of numeric representation and rounding policy. Do not assume that a floating-point calculation is appropriate for every monetary workload.

## `$divide`

```javascript
{
  $project: {
    average_value: {
      $divide: [
        "$total",
        "$count"
      ]
    }
  }
}
```

Protect against zero denominators.

A conditional expression can provide a safe fallback:

```javascript
{
  $project: {
    average_value: {
      $cond: [
        {
          $ne: [
            "$count",
            0
          ]
        },
        {
          $divide: [
            "$total",
            "$count"
          ]
        },
        0
      ]
    }
  }
}
```

## `$mod`

Returns the remainder of a division.

```javascript
{
  $project: {
    remainder: {
      $mod: [
        "$sequence",
        10
      ]
    }
  }
}
```

Useful for:

- Bucketing
- Even/odd classification
- Partitioning logic
- Cyclic calculations

## Rounding Operators

### `$round`

```javascript
{
  $project: {
    rounded_price: {
      $round: [
        "$price",
        2
      ]
    }
  }
}
```

### `$ceil`

```javascript
{
  $project: {
    units_required: {
      $ceil: "$quantity"
    }
  }
}
```

### `$floor`

```javascript
{
  $project: {
    bucket: {
      $floor: "$score"
    }
  }
}
```

### `$trunc`

```javascript
{
  $project: {
    truncated_value: {
      $trunc: [
        "$price",
        2
      ]
    }
  }
}
```

Rounding should be defined as part of the business rule, not introduced casually inside reporting queries.

## Comparison Operators

Aggregation comparison operators produce boolean values.

| Operator | Meaning |
|---|---|
| `$eq` | Equal |
| `$ne` | Not equal |
| `$gt` | Greater than |
| `$gte` | Greater than or equal |
| `$lt` | Less than |
| `$lte` | Less than or equal |

Example:

```javascript
{
  $project: {
    is_high_value: {
      $gte: [
        "$total",
        5000
      ]
    }
  }
}
```

These operators are frequently used with:

- `$cond`
- `$switch`
- `$filter`
- `$map`
- `$expr`
- `$match`

## `$eq`

```javascript
{
  $project: {
    is_paid: {
      $eq: [
        "$status",
        "paid"
      ]
    }
  }
}
```

The result is a boolean expression.

## `$ne`

```javascript
{
  $project: {
    requires_review: {
      $ne: [
        "$status",
        "approved"
      ]
    }
  }
}
```

## `$gt`, `$gte`, `$lt`, `$lte`

Example:

```javascript
{
  $project: {
    is_large_order: {
      $gt: [
        "$total",
        10000
      ]
    }
  }
}
```

These are particularly useful inside conditional and array expressions.

## Boolean Operators

Boolean operators combine logical conditions.

| Operator | Purpose |
|---|---|
| `$and` | All conditions must be true |
| `$or` | At least one condition must be true |
| `$not` | Negates a condition |
| `$nor` | None of the conditions should be true |

Example:

```javascript
{
  $project: {
    eligible: {
      $and: [
        {
          $eq: [
            "$status",
            "active"
          ]
        },
        {
          $gte: [
            "$balance",
            1000
          ]
        }
      ]
    }
  }
}
```

## `$and`

```javascript
{
  $and: [
    {
      $gte: [
        "$age",
        18
      ]
    },
    {
      $eq: [
        "$status",
        "active"
      ]
    }
  ]
}
```

Use `$and` when multiple expression conditions must be satisfied.

## `$or`

```javascript
{
  $or: [
    {
      $eq: [
        "$status",
        "pending"
      ]
    },
    {
      $eq: [
        "$status",
        "retry"
      ]
    }
  ]
}
```

## `$not`

```javascript
{
  $not: [
    {
      $eq: [
        "$status",
        "cancelled"
      ]
    }
  ]
}
```

Be careful with null and missing-field semantics. Boolean logic over incomplete documents can produce results that differ from assumptions based on strongly typed relational schemas.

## Conditional Operators

Conditional expressions are central to practical aggregation pipelines.

| Operator | Purpose |
|---|---|
| `$cond` | If/else |
| `$ifNull` | Fallback for null/missing values |
| `$switch` | Multiple branches |

## `$cond`

Array syntax:

```javascript
{
  $cond: [
    {
      $gte: [
        "$total",
        5000
      ]
    },
    "high",
    "normal"
  ]
}
```

Object syntax:

```javascript
{
  $cond: {
    if: {
      $gte: [
        "$total",
        5000
      ]
    },
    then: "high",
    else: "normal"
  }
}
```

The object form is often easier to read when conditions become complex.

## `$ifNull`

```javascript
{
  $project: {
    country: {
      $ifNull: [
        "$profile.country",
        "unknown"
      ]
    }
  }
}
```

This is useful for:

- Backward-compatible schemas
- Optional fields
- Legacy documents
- Data migrations

Do not use `$ifNull` to hide data-quality problems indefinitely. If a field is required by the business model, enforce that requirement through schema validation and application logic.

## `$switch`

```javascript
{
  $project: {
    customer_tier: {
      $switch: {
        branches: [
          {
            case: {
              $gte: [
                "$lifetime_value",
                10000
              ]
            },
            then: "gold"
          },
          {
            case: {
              $gte: [
                "$lifetime_value",
                5000
              ]
            },
            then: "silver"
          }
        ],
        default: "standard"
      }
    }
  }
}
```

`$switch` is preferable to deeply nested `$cond` expressions when multiple business cases exist.

## Null and Missing Values

MongoDB's flexible schema means aggregation pipelines must explicitly consider:

```text
Field exists
Field is null
Field has wrong type
Field contains empty array
Field is missing
```

For example:

```javascript
{
  $project: {
    email: {
      $ifNull: [
        "$email",
        "unknown"
      ]
    }
  }
}
```

A production pipeline should be tested against all relevant document shapes rather than only the ideal schema.

## Type Conversion Operators

Type conversion is important when legacy or heterogeneous documents contain inconsistent types.

Common operators include:

- `$toString`
- `$toInt`
- `$toLong`
- `$toDouble`
- `$toDecimal`
- `$toBool`
- `$toDate`
- `$toObjectId`
- `$convert`

Example:

```javascript
{
  $project: {
    numeric_quantity: {
      $convert: {
        input: "$quantity",
        to: "int",
        onError: 0,
        onNull: 0
      }
    }
  }
}
```

`$convert` is useful when conversion failure must be handled explicitly.

## `$toObjectId`

```javascript
{
  $set: {
    customer_object_id: {
      $toObjectId: "$customer_id"
    }
  }
}
```

Use this carefully.

If a field is stored as a string in one collection and `ObjectId` in another, the need for repeated conversion during joins is often a schema-quality problem.

Prefer consistent identifier types across related collections.

## String Operators

String expressions are useful for normalization and formatting.

| Operator | Purpose |
|---|---|
| `$concat` | Concatenate strings |
| `$toLower` | Lowercase |
| `$toUpper` | Uppercase |
| `$trim` | Remove characters/whitespace |
| `$ltrim` | Left trim |
| `$rtrim` | Right trim |
| `$substrBytes` | Extract byte range |
| `$substrCP` | Extract code-point range |
| `$split` | Split a string |
| `$replaceOne` | Replace one occurrence |
| `$replaceAll` | Replace all occurrences |
| `$strLenBytes` | String byte length |
| `$strLenCP` | String code-point length |

## `$concat`

```javascript
{
  $project: {
    display_name: {
      $concat: [
        "$first_name",
        " ",
        "$last_name"
      ]
    }
  }
}
```

For user-visible strings, consider whether formatting belongs in the database or API layer.

## `$toLower` and `$toUpper`

```javascript
{
  $project: {
    normalized_email: {
      $toLower: "$email"
    }
  }
}
```

For frequently queried normalized values, storing a normalized field can be more efficient than recalculating it for every request.

## `$trim`

```javascript
{
  $project: {
    normalized_name: {
      $trim: {
        input: "$name"
      }
    }
  }
}
```

Useful during data cleanup and migration pipelines.

## `$split`

```javascript
{
  $project: {
    name_parts: {
      $split: [
        "$full_name",
        " "
      ]
    }
  }
}
```

Be aware that real-world names and free-form strings do not necessarily follow simple delimiter assumptions.

## Array Operators

Array expressions are essential when documents contain embedded collections.

| Operator | Purpose |
|---|---|
| `$arrayElemAt` | Access an array element |
| `$first` | First array/value |
| `$last` | Last array/value |
| `$filter` | Filter array elements |
| `$map` | Transform each element |
| `$reduce` | Fold array into one result |
| `$concatArrays` | Combine arrays |
| `$in` | Test membership |
| `$isArray` | Test whether value is an array |
| `$size` | Count elements |
| `$slice` | Select part of an array |
| `$reverseArray` | Reverse an array |
| `$range` | Generate numeric sequence |
| `$sortArray` | Sort array elements |

## `$arrayElemAt`

```javascript
{
  $project: {
    first_item: {
      $arrayElemAt: [
        "$items",
        0
      ]
    }
  }
}
```

Always consider empty arrays and missing fields.

## `$size`

```javascript
{
  $project: {
    item_count: {
      $size: "$items"
    }
  }
}
```

If the field may not be an array, combine this with type or conditional logic.

## `$filter`

`$filter` retains array elements satisfying a condition.

```javascript
{
  $project: {
    expensive_items: {
      $filter: {
        input: "$items",
        as: "item",
        cond: {
          $gte: [
            "$$item.price",
            1000
          ]
        }
      }
    }
  }
}
```

Use `$filter` when you want to preserve the parent document.

Use `$unwind` when each array element needs to become an independent pipeline document.

## `$map`

`$map` transforms every array element.

```javascript
{
  $project: {
    item_totals: {
      $map: {
        input: "$items",
        as: "item",
        in: {
          $multiply: [
            "$$item.price",
            "$$item.quantity"
          ]
        }
      }
    }
  }
}
```

The result remains an array.

## `$reduce`

`$reduce` combines array elements into a single accumulated value.

```javascript
{
  $project: {
    order_total: {
      $reduce: {
        input: "$items",
        initialValue: 0,
        in: {
          $add: [
            "$$value",
            {
              $multiply: [
                "$$this.price",
                "$$this.quantity"
              ]
            }
          ]
        }
      }
    }
  }
}
```

Here:

- `$$value` is the accumulated value.
- `$$this` is the current array element.

`$reduce` is powerful but can become difficult to maintain when the expression is complex.

## `$isArray`

```javascript
{
  $project: {
    has_items_array: {
      $isArray: "$items"
    }
  }
}
```

This is useful in flexible-schema environments.

## Array Membership

```javascript
{
  $project: {
    has_priority: {
      $in: [
        "priority",
        "$tags"
      ]
    }
  }
}
```

This is an aggregation expression and should not be confused with the query operator `$in`.

## Date Operators

Date expressions are heavily used in:

- Reporting
- Metrics
- SLA calculations
- Time-series analysis
- Billing
- Operational dashboards

Common operators include:

| Operator | Purpose |
|---|---|
| `$year` | Extract year |
| `$month` | Extract month |
| `$week` | Extract week |
| `$dayOfYear` | Extract day of year |
| `$dayOfMonth` | Extract day of month |
| `$dayOfWeek` | Extract day of week |
| `$hour` | Extract hour |
| `$minute` | Extract minute |
| `$second` | Extract second |
| `$dateToString` | Format date |
| `$dateFromString` | Parse date |
| `$dateTrunc` | Truncate date |
| `$dateDiff` | Calculate date difference |
| `$dateAdd` | Add duration |
| `$dateSubtract` | Subtract duration |

## `$dateDiff`

```javascript
{
  $project: {
    processing_seconds: {
      $dateDiff: {
        startDate: "$started_at",
        endDate: "$completed_at",
        unit: "second"
      }
    }
  }
}
```

This is preferable to manually subtracting dates when a specific unit is required.

## `$dateAdd`

```javascript
{
  $project: {
    expiry_at: {
      $dateAdd: {
        startDate: "$created_at",
        unit: "day",
        amount: 30
      }
    }
  }
}
```

Useful for calculating:

- Expiration
- Retention windows
- SLA deadlines
- Subscription periods

## `$dateTrunc`

```javascript
{
  $project: {
    hour: {
      $dateTrunc: {
        date: "$created_at",
        unit: "hour"
      }
    }
  }
}
```

Useful for grouping events into fixed time windows.

Timezone handling should be explicit when business reporting uses a non-UTC timezone.

## `$dateToString`

```javascript
{
  $project: {
    day: {
      $dateToString: {
        format: "%Y-%m-%d",
        date: "$created_at",
        timezone: "UTC"
      }
    }
  }
}
```

For reporting systems, define timezone policy centrally.

## Object and Document Operators

MongoDB aggregation can also inspect and manipulate document structures.

Useful operators include:

- `$getField`
- `$setField`
- `$objectToArray`
- `$arrayToObject`
- `$mergeObjects`

## `$mergeObjects`

Combines documents.

```javascript
{
  $project: {
    customer: {
      $mergeObjects: [
        "$customer",
        {
          source: "orders"
        }
      ]
    }
  }
}
```

This is particularly useful when combining fields from multiple documents or `$lookup` results.

## `$objectToArray`

Converts an object into key/value array entries.

Given:

```json
{
  "metrics": {
    "cpu": 50,
    "memory": 70
  }
}
```

the expression:

```javascript
{
  $objectToArray: "$metrics"
}
```

produces conceptually:

```json
[
  {
    "k": "cpu",
    "v": 50
  },
  {
    "k": "memory",
    "v": 70
  }
]
```

This is useful for dynamically processing object keys.

## Set Operators

Set operators treat arrays as mathematical sets.

| Operator | Purpose |
|---|---|
| `$setEquals` | Compare sets |
| `$setIntersection` | Common values |
| `$setUnion` | Combine unique values |
| `$setDifference` | Values present in one set but not another |
| `$setIsSubset` | Test subset relationship |

Example:

```javascript
{
  $project: {
    common_permissions: {
      $setIntersection: [
        "$user_permissions",
        "$required_permissions"
      ]
    }
  }
}
```

These are useful for:

- Permissions
- Tags
- Capabilities
- Feature sets
- Classification

## `$setUnion`

```javascript
{
  $project: {
    all_tags: {
      $setUnion: [
        "$product_tags",
        "$category_tags"
      ]
    }
  }
}
```

The result contains unique values.

## `$setDifference`

```javascript
{
  $project: {
    missing_permissions: {
      $setDifference: [
        "$required_permissions",
        "$user_permissions"
      ]
    }
  }
}
```

This can be useful in authorization-related reporting, but actual authorization should still be enforced by the application and security model rather than relying solely on a reporting pipeline.

## Accumulator Operators

Accumulators operate across multiple documents, most commonly inside `$group`.

| Accumulator | Typical use |
|---|---|
| `$sum` | Totals/counts |
| `$avg` | Average |
| `$min` | Minimum |
| `$max` | Maximum |
| `$first` | First encountered value |
| `$last` | Last encountered value |
| `$push` | Collect values |
| `$addToSet` | Collect unique values |
| `$count` | Count documents |

Example:

```javascript
db.orders.aggregate([
  {
    $group: {
      _id: "$customer_id",
      total_orders: {
        $sum: 1
      },
      total_revenue: {
        $sum: "$total"
      },
      average_order: {
        $avg: "$total"
      }
    }
  }
])
```

## `$sum`

Count documents:

```javascript
{
  $sum: 1
}
```

Sum a field:

```javascript
{
  $sum: "$total"
}
```

This distinction is fundamental.

## `$avg`

```javascript
{
  $group: {
    _id: "$product_id",
    average_price: {
      $avg: "$price"
    }
  }
}
```

Missing or non-numeric values require careful consideration when defining business metrics.

## `$min` and `$max`

```javascript
{
  $group: {
    _id: "$customer_id",
    minimum_order: {
      $min: "$total"
    },
    maximum_order: {
      $max: "$total"
    }
  }
}
```

Useful for:

- Ranges
- Threshold analysis
- SLA measurements
- Pricing analysis

## `$push`

Collects values into an array.

```javascript
{
  $group: {
    _id: "$customer_id",
    orders: {
      $push: "$order_id"
    }
  }
}
```

Be careful with unbounded arrays.

Grouping millions of values into one output document can create:

- Large memory requirements
- Large result documents
- Large network responses
- Document-size constraints

## `$addToSet`

Collects unique values.

```javascript
{
  $group: {
    _id: "$customer_id",
    products: {
      $addToSet: "$product_id"
    }
  }
}
```

Use it when uniqueness is part of the requirement.

Do not use `$addToSet` merely because duplicates are inconvenient. If the resulting array can grow without bounds, the underlying data model may still be problematic.

## Accumulators with Sorting

When using accumulators whose result depends on document order, explicitly establish the required order.

For example:

```javascript
[
  {
    $sort: {
      created_at: 1
    }
  },
  {
    $group: {
      _id: "$customer_id",
      first_order: {
        $first: "$order_id"
      },
      last_order: {
        $last: "$order_id"
      }
    }
  }
]
```

Do not rely on incidental collection order.

## Ranking and Window Calculations

MongoDB provides window-function capabilities through `$setWindowFields`.

Example:

```javascript
db.sales.aggregate([
  {
    $setWindowFields: {
      partitionBy: "$region",
      sortBy: {
        created_at: 1
      },
      output: {
        running_revenue: {
          $sum: "$total",
          window: {
            documents: [
              "unbounded",
              "current"
            ]
          }
        }
      }
    }
  }
])
```

Window processing is useful for:

- Running totals
- Moving averages
- Rankings
- Time-series comparisons
- Per-group calculations

It can be significantly more expensive than a simple projection, so benchmark important workloads.

## Aggregation Operator Selection

A practical decision table:

| Requirement | Operators / Stages |
|---|---|
| Filter documents | `$match` + query operators |
| Calculate a value | `$add`, `$subtract`, `$multiply`, `$divide` |
| Conditional logic | `$cond`, `$switch`, `$ifNull` |
| Transform strings | `$concat`, `$toLower`, `$trim`, `$split` |
| Transform arrays | `$map`, `$filter`, `$reduce` |
| Expand arrays | `$unwind` |
| Group documents | `$group` + accumulators |
| Sort results | `$sort` |
| Limit results | `$limit` |
| Join collections | `$lookup` |
| Combine pipelines | `$unionWith` |
| Multiple result branches | `$facet` |
| Bucket values | `$bucket`, `$bucketAuto` |
| Manipulate dates | `$dateAdd`, `$dateDiff`, `$dateTrunc` |
| Convert types | `$convert`, `$to*` |
| Manipulate documents | `$mergeObjects`, `$getField`, `$setField` |
| Materialize results | `$merge`, `$out` |

## Operator Composition

Aggregation becomes powerful when operators are composed.

Example:

```javascript
db.orders.aggregate([
  {
    $set: {
      net_total: {
        $subtract: [
          "$total",
          "$discount"
        ]
      }
    }
  },
  {
    $set: {
      customer_tier: {
        $switch: {
          branches: [
            {
              case: {
                $gte: [
                  "$net_total",
                  10000
                ]
              },
              then: "gold"
            },
            {
              case: {
                $gte: [
                  "$net_total",
                  5000
                ]
              },
              then: "silver"
            }
          ],
          default: "standard"
        }
      }
    }
  }
])
```

This is readable because each transformation has a clear purpose.

Avoid building a single enormous expression when separate stages make the pipeline easier to understand and test.

## Operator Evaluation and Performance

Aggregation expressions are generally CPU work performed as documents flow through the pipeline.

The cost can become significant when:

```text
Large collection
      ×
Complex expression
      ×
High request frequency
```

For example:

```javascript
{
  $project: {
    normalized_email: {
      $toLower: {
        $trim: {
          input: "$email"
        }
      }
    }
  }
}
```

may be reasonable for a batch transformation.

Repeatedly executing the same normalization against millions of documents on every API request is a signal to consider storing a normalized field.

## Index Interaction

Most aggregation operators themselves do not magically create index usage.

Indexes are primarily useful when pipeline stages such as `$match` and `$sort` can exploit them.

For example:

```javascript
[
  {
    $match: {
      tenant_id: "TENANT-100",
      status: "paid"
    }
  },
  {
    $sort: {
      created_at: -1
    }
  },
  {
    $project: {
      _id: 1,
      total: 1,
      created_at: 1
    }
  }
]
```

may benefit from an index aligned with the filtering and sorting pattern.

Do not create an index for every aggregation operator.

Instead:

```text
Query pattern
     ↓
Filter / sort requirements
     ↓
Candidate index
     ↓
explain()
     ↓
Measured result
```

## Operators That Increase Cardinality

Some operations can dramatically increase intermediate work.

| Operation | Cardinality effect |
|---|---|
| `$match` | Decreases or preserves |
| `$limit` | Decreases |
| `$group` | Usually decreases |
| `$project` | Preserves |
| `$set` | Preserves |
| `$map` | Preserves parent documents |
| `$filter` | Preserves parent documents |
| `$unwind` | Can increase dramatically |
| `$lookup` | Can increase result size |
| `$unionWith` | Adds another stream |

This is a useful senior-level mental model.

```text
Cardinality reduction
        ↓
Usually cheaper downstream processing

Cardinality expansion
        ↓
Potentially expensive downstream processing
```

## Aggregation Operators and API Design

Do not expose arbitrary aggregation operators to external clients.

Avoid APIs such as:

```http
POST /reports
```

with:

```json
{
  "pipeline": [
    {
      "$lookup": {}
    }
  ]
}
```

A safer design exposes business-level parameters:

```http
GET /reports/revenue?from=2026-09-01&to=2026-09-20&group_by=customer
```

The server constructs the approved pipeline.

```text
Client parameters
      |
      v
Validation
      |
      v
Authorization
      |
      v
Approved pipeline
      |
      v
MongoDB
```

This prevents clients from controlling database behavior directly.

## Multi-Tenant Aggregation

Multi-tenant systems should inject tenant restrictions from trusted authentication context.

```python
def build_revenue_pipeline(tenant_id: str) -> list[dict]:
    return [
        {
            "$match": {
                "tenant_id": tenant_id,
                "status": "paid",
            }
        },
        {
            "$group": {
                "_id": "$customer_id",
                "revenue": {
                    "$sum": "$total",
                },
            }
        },
    ]
```

Do not accept `tenant_id` exclusively from an arbitrary request parameter when the authenticated tenant is already known.

The database query should enforce isolation.

## Python Usage

PyMongo represents aggregation pipelines as Python lists and dictionaries.

```python
from pymongo.collection import Collection


def get_customer_revenue(
    collection: Collection,
    tenant_id: str,
) -> list[dict]:
    pipeline = [
        {
            "$match": {
                "tenant_id": tenant_id,
                "status": "paid",
            }
        },
        {
            "$group": {
                "_id": "$customer_id",
                "revenue": {
                    "$sum": "$total",
                },
                "orders": {
                    "$sum": 1,
                },
            }
        },
        {
            "$sort": {
                "revenue": -1,
            }
        },
    ]

    return list(collection.aggregate(pipeline))
```

For potentially large results, avoid converting the entire cursor into a list:

```python
cursor = collection.aggregate(
    pipeline,
    batchSize=500,
)

for document in cursor:
    process(document)
```

## Building Pipelines Safely in Python

Prefer explicit pipeline builders.

```python
def build_order_report(
    tenant_id: str,
    status: str,
) -> list[dict]:
    return [
        {
            "$match": {
                "tenant_id": tenant_id,
                "status": status,
            }
        },
        {
            "$group": {
                "_id": "$customer_id",
                "revenue": {
                    "$sum": "$total",
                },
            }
        },
    ]
```

Avoid string concatenation or unvalidated fragments.

Bad:

```python
pipeline = eval(user_supplied_pipeline)
```

Never execute user-controlled Python expressions to construct database queries.

## FastAPI Service Boundary

A clean architecture is:

```text
FastAPI endpoint
      |
      v
Request validation
      |
      v
Service layer
      |
      v
Pipeline builder
      |
      v
Repository
      |
      v
MongoDB
```

For example:

```python
class RevenueService:
    def __init__(self, repository):
        self.repository = repository

    def get_customer_revenue(self, tenant_id: str):
        return self.repository.customer_revenue(tenant_id)
```

The repository owns MongoDB-specific implementation details.

## Django Integration

For Django applications using PyMongo or MongoDB-specific libraries, keep complex aggregation pipelines out of views.

Prefer:

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
MongoDB
```

This makes pipelines easier to:

- Test
- Reuse
- Benchmark
- Review
- Optimize
- Version

Do not assume that aggregation expressions map directly to Django ORM expressions.

## Common Operator Mistakes

### Confusing Query and Aggregation Operators

This:

```javascript
{
  $match: {
    total: {
      $gt: 1000
    }
  }
}
```

uses `$gt` as a query predicate.

Inside an aggregation expression:

```javascript
{
  $project: {
    is_large: {
      $gt: [
        "$total",
        1000
      ]
    }
  }
}
```

the same conceptual comparison is expressed differently.

### Assuming Missing Fields Are Zero

Do not assume:

```javascript
"$quantity"
```

will behave like numeric zero when the field is absent.

Handle schema variability explicitly.

### Dividing Without Checking the Denominator

Bad:

```javascript
{
  $divide: [
    "$total",
    "$count"
  ]
}
```

when `$count` may be zero or missing.

### Using `$unwind` When `$filter` Is Enough

If the output should remain one document per parent, `$filter` may be more appropriate.

### Creating Huge Arrays with `$push`

This can produce large intermediate documents.

Always consider maximum cardinality.

### Using String Conversion as a Permanent Schema Strategy

Repeatedly converting:

```text
string ID → ObjectId
```

is often a symptom of inconsistent schema design.

### Embedding Excessive Business Logic

A pipeline can technically perform complex calculations, but database-side business logic should remain maintainable, observable, and testable.

## Production Pitfalls

### Type Inconsistency

Documents may contain:

```json
{ "quantity": 10 }
```

and:

```json
{ "quantity": "10" }
```

The pipeline must define how such data is handled.

Prevent this through:

- Schema validation
- Application validation
- Migration
- Consistent serialization

### Unbounded Arrays

Operators such as:

```text
$push
$addToSet
$concatArrays
```

can generate large arrays.

### Excessive Expression Complexity

A pipeline containing deeply nested:

```text
$cond
$switch
$map
$reduce
$filter
```

can become difficult to review and optimize.

### Ignoring Data Growth

A pipeline should be evaluated against:

```text
Current volume
+
Expected growth
+
Peak traffic
+
Worst-case document shape
```

### Assuming Development Performance Represents Production

Small datasets can hide:

- Missing indexes
- Cardinality problems
- Memory pressure
- Sort cost
- Join cost
- Connection contention

## Performance Diagnosis

When an aggregation operator is suspected of causing a performance problem:

```text
Slow aggregation
      |
      v
Capture exact pipeline
      |
      v
Run explain("executionStats")
      |
      v
Inspect cardinality
      |
      v
Identify expensive stage
      |
      v
Inspect indexes
      |
      v
Measure operator/stage alternatives
      |
      v
Test production-like workload
```

Useful measurements include:

- `nReturned`
- `totalDocsExamined`
- `totalKeysExamined`
- Execution time
- Sort behavior
- Memory/resource consumption
- Intermediate document count
- Request frequency

## Operator Testing Strategy

For important pipelines, test:

### Correctness

- Normal documents
- Missing fields
- Null values
- Empty arrays
- Large arrays
- Invalid types
- Boundary values
- Duplicate values
- Multiple tenants

### Performance

- Small dataset
- Expected production dataset
- Peak dataset
- High-cardinality data
- Worst-case array sizes
- Concurrent requests

### Regression

Store representative workloads and compare:

```text
Before
  ↓
execution time
documents examined
keys examined
result size
  ↓
After
  ↓
same measurements
```

Optimization should be measurable.

## Operators and Materialized Data

If an expensive expression is evaluated repeatedly:

```text
Every API request
      |
      v
Millions of documents
      |
      v
Repeated calculations
```

consider precomputing the value.

Example:

```text
Raw orders
    |
    v
Background aggregation
    |
    v
customer_metrics
    |
    v
API
```

Potential implementation choices include:

- `$merge`
- Scheduled Celery jobs
- Kubernetes CronJobs
- Change streams
- Kafka consumers
- Dedicated reporting pipelines

The correct choice depends on freshness and workload requirements.

## Operators and Change Streams

Aggregation operators can also be used in change-stream processing architectures.

```text
MongoDB
   |
   v
Change Stream
   |
   v
Worker
   |
   v
Aggregation / Transformation
   |
   v
Kafka / Redis / Derived Collection
```

The consumer should be designed for:

- Resume behavior
- Duplicate processing
- Idempotency
- Failure recovery
- Backpressure
- Monitoring

Do not assume a change-stream consumer will process each event exactly once without application-level safeguards.

## Operator Security

Aggregation operators can become a resource-exhaustion vector if clients are allowed to construct arbitrary pipelines.

Potentially expensive operations include:

- `$lookup`
- `$group`
- `$sort`
- `$unwind`
- `$facet`
- `$setWindowFields`

Public APIs should therefore enforce:

- Authentication
- Authorization
- Tenant isolation
- Maximum date range
- Maximum page size
- Allowed grouping fields
- Allowed sorting fields
- Query timeouts
- Rate limits
- Resource quotas

## Interview Traps

### Is `$sum` only for adding numeric fields?

No. It is also commonly used as a document counter:

```javascript
{
  $sum: 1
}
```

### Is `$filter` equivalent to `$unwind`?

No.

`$filter` transforms an array while retaining the parent document.

`$unwind` creates separate pipeline documents for array elements.

### Are aggregation expressions automatically indexed?

No. Indexes primarily help stages and access patterns such as `$match` and compatible `$sort` operations.

### Why is `$lookup` not automatically equivalent to a relational join?

MongoDB's document model and workload characteristics differ from relational systems. `$lookup` is powerful, but repeated large joins may indicate a data-model or read-model problem.

### Why can `$push` be dangerous?

It can create large accumulated arrays and potentially large intermediate or final documents.

### Why should `$dateTrunc` timezone handling be explicit?

Business reporting boundaries may differ from UTC boundaries. A "day" for a business may represent a local calendar day rather than a UTC calendar day.

### Why should aggregation pipelines be tested with production-like data?

Operator cost depends heavily on:

```text
Document count
+
Array cardinality
+
Join cardinality
+
Data distribution
+
Index structure
+
Execution frequency
```

A pipeline that is fast on development data may not scale.

## Production Checklist

Before deploying a critical aggregation pipeline:

- [ ] Distinguish pipeline stages from aggregation operators.
- [ ] Define expected input and output document shapes.
- [ ] Validate null and missing-field behavior.
- [ ] Validate BSON type assumptions.
- [ ] Review `$unwind` cardinality.
- [ ] Review `$lookup` cardinality.
- [ ] Avoid unnecessary application-side aggregation.
- [ ] Review compound index requirements.
- [ ] Verify index usage with `explain()`.
- [ ] Measure `totalDocsExamined`.
- [ ] Measure `totalKeysExamined`.
- [ ] Check result and intermediate cardinality.
- [ ] Avoid unbounded `$push` and `$addToSet`.
- [ ] Avoid deep `$skip` for large datasets.
- [ ] Protect aggregation endpoints from arbitrary pipelines.
- [ ] Enforce tenant isolation inside database queries.
- [ ] Apply request and resource limits.
- [ ] Test with production-like data volumes.
- [ ] Monitor latency and database resource usage.
- [ ] Consider materialization for frequently repeated expensive computations.

## Key Takeaways

- Aggregation operators perform the calculations and transformations inside pipeline stages; understanding their semantics, types, null behavior, and cardinality effects is essential for reliable MongoDB systems.
- `$cond`, `$switch`, `$map`, `$filter`, `$reduce`, arithmetic, date, string, and type-conversion operators provide powerful server-side processing without moving intermediate data into application memory.
- `$unwind`, `$lookup`, `$group`, `$push`, and `$addToSet` can create large intermediate results, so cardinality and memory must be considered before production deployment.
- Indexes primarily support pipeline access patterns such as `$match` and compatible `$sort`; use `explain("executionStats")` to verify actual execution behavior.
- Production aggregation operators should be protected by schema discipline, authorization, tenant isolation, resource limits, realistic performance testing, and a clear decision about whether computation belongs in MongoDB, the service layer, or a dedicated processing system.