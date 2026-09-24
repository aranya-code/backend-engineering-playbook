# 03- BSON Data Types

## Overview

BSON, short for **Binary JSON**, is the binary serialization format MongoDB uses to represent documents and values internally.

A MongoDB document may look like JSON when viewed through `mongosh`, MongoDB Compass, a REST API, or Python:

```json
{
  "_id": "user-100",
  "name": "Alice",
  "age": 32,
  "active": true
}
```

The stored representation is BSON rather than JSON.

BSON extends the JSON data model with additional types that are important for backend systems, including:

- `ObjectId`
- `Date`
- `Decimal128`
- `Int32`
- `Int64`
- `Binary`
- `Timestamp`
- `Regular Expression`
- `MinKey`
- `MaxKey`

Understanding BSON matters because the BSON type of a field affects:

- Query behavior
- Sorting
- Indexing
- Comparison semantics
- Serialization
- Python type conversion
- API responses
- Schema validation
- Storage requirements
- Data migration
- Interoperability with other systems

A recurring production rule is:

> Do not treat MongoDB data as arbitrary JSON. MongoDB stores BSON values with explicit types, and those types are part of the database schema.

---

## BSON vs JSON

JSON is a text-based data interchange format. BSON is a binary serialization format designed for efficient storage and traversal of structured data.

| Characteristic | JSON | BSON |
|---|---|---|
| Representation | Text | Binary |
| Primary MongoDB storage format | No | Yes |
| String | Yes | Yes |
| Boolean | Yes | Yes |
| Array | Yes | Yes |
| Object/document | Yes | Yes |
| Date type | No native type | Yes |
| ObjectId | No | Yes |
| Decimal128 | No | Yes |
| Binary type | No native equivalent | Yes |
| Int32 / Int64 distinction | Limited | Explicit |
| Regular expression type | No standard native type | Yes |
| MongoDB-specific types | No | Yes |

BSON should not be interpreted as simply "JSON stored in binary form."

Its additional types allow MongoDB to represent values more precisely.

---

## BSON Document Structure

A BSON document consists of typed fields.

Conceptually:

```text
BSON Document
    |
    +-- Field name
    +-- BSON type
    +-- Encoded value
```

For example:

```json
{
  "name": "Alice",
  "age": 32,
  "active": true
}
```

contains values with different BSON types:

```text
name   -> string
age    -> integer
active -> boolean
```

A nested document introduces another BSON document:

```json
{
  "profile": {
    "city": "Kolkata",
    "country": "India"
  }
}
```

An array is also a BSON value containing ordered elements.

---

## BSON Type Categories

MongoDB supports a range of BSON types.

| BSON Type | Typical backend use |
|---|---|
| String | Names, status values, identifiers |
| Double | Floating-point measurements |
| Decimal128 | Exact decimal values |
| Int32 | Small integers |
| Int64 | Large integer values |
| Boolean | Flags |
| Null | Explicit absence of a value |
| ObjectId | Document identifiers |
| Date | Timestamps |
| Timestamp | MongoDB internal/replication-related timestamps |
| Binary | Binary payloads |
| Document | Nested structured data |
| Array | Ordered collections |
| Regular Expression | Pattern matching |
| JavaScript | Legacy/specialized use |
| MinKey | Lowest BSON comparison value |
| MaxKey | Highest BSON comparison value |

The most important types for application developers are usually:

```text
String
Boolean
Int32
Int64
Double
Decimal128
Date
ObjectId
Array
Document
Binary
Null
```

---

## String

A BSON string represents textual data.

Example:

```json
{
  "name": "Alice",
  "status": "active"
}
```

Python:

```python
document = {
    "name": "Alice",
    "status": "active",
}
```

Strings are appropriate for:

- Names
- Email addresses
- Status values
- Human-readable identifiers
- URLs
- Version strings

### Production Considerations

Do not store values as strings merely because JSON makes that convenient.

For example, this:

```json
{
  "created_at": "2026-09-21T10:30:00Z"
}
```

is not equivalent to storing a BSON date.

If the value represents a timestamp that will be queried, sorted, or compared as a date, use the BSON date type.

---

## Boolean

Boolean values represent `true` or `false`.

```json
{
  "active": true,
  "email_verified": false
}
```

Python:

```python
document = {
    "active": True,
    "email_verified": False,
}
```

Boolean fields are useful for flags, but avoid creating excessive independent flags when a state machine would better represent the domain.

For example:

```json
{
  "active": true,
  "deleted": false,
  "suspended": false
}
```

can become ambiguous because multiple combinations may be possible.

A controlled state may be clearer:

```json
{
  "status": "active"
}
```

The appropriate design depends on the domain.

---

## Integer Types

MongoDB distinguishes integer widths.

Common integer types include:

- Int32
- Int64

The distinction matters when values can exceed the range of a smaller integer representation or when interacting with strongly typed applications.

Example:

```json
{
  "quantity": 10,
  "total_views": 9876543210
}
```

A backend engineer should understand that integer representation is not necessarily identical across:

```text
MongoDB
    |
    v
BSON
    |
    v
Python
    |
    v
JSON
    |
    v
JavaScript client
```

Different layers may have different numeric constraints.

---

## Int32

Int32 represents a signed 32-bit integer.

Typical uses include:

- Small counters
- Quantities
- Small enumerations
- Bounded numeric fields

Example:

```python
{
    "quantity": 25
}
```

For values that can grow significantly, use an appropriate larger integer representation.

Do not choose numeric types solely based on today's values.

Consider the expected lifetime and maximum value of the field.

---

## Int64

Int64 represents a signed 64-bit integer.

It is useful for:

- Large counters
- High-volume event identifiers
- Large numeric quantities
- Values exceeding Int32 range

For example:

```json
{
  "event_count": 9827342100
}
```

When exposing large integers through APIs, also consider the limitations of clients such as JavaScript, whose `Number` type cannot exactly represent every integer above `2^53 - 1`.

If an API must preserve exact large integer values across heterogeneous clients, the API contract may need to represent them as strings or use a suitable serialization strategy.

---

## Double

Double represents an IEEE 754 double-precision floating-point value.

Example:

```json
{
  "temperature": 36.7
}
```

Double is appropriate for many measurements where small floating-point representation differences are acceptable.

It is generally not the preferred representation for exact monetary amounts.

For example:

```text
price = 19.99
```

should not automatically be stored as a floating-point value when exact financial arithmetic is required.

---

## Decimal128

`Decimal128` provides decimal floating-point representation suitable for exact decimal arithmetic within its supported precision.

It is particularly useful for:

- Monetary values
- Financial calculations
- Exact decimal quantities
- Business values where binary floating-point representation is undesirable

Python example:

```python
from decimal import Decimal

from bson.decimal128 import Decimal128

price = Decimal128(Decimal("19.99"))

document = {
    "price": price,
}
```

The important distinction is:

```text
Double
    -> binary floating-point

Decimal128
    -> decimal floating-point
```

For financial applications, also consider whether the domain should store integer minor units instead:

```json
{
  "amount_minor": 1999,
  "currency": "USD"
}
```

This can be simpler when the domain guarantees a fixed number of decimal places.

---

## Date

MongoDB's BSON Date type represents a point in time with millisecond precision.

Python example:

```python
from datetime import datetime, timezone

document = {
    "created_at": datetime.now(timezone.utc),
}
```

This is preferable to storing timestamps as arbitrary strings when the field will be:

- Sorted
- Filtered
- Compared
- Aggregated
- Used for retention policies

Example query:

```javascript
db.orders.find({
  created_at: {
    $gte: ISODate("2026-09-01T00:00:00Z")
  }
})
```

### UTC Recommendation

For backend systems, store timestamps consistently in UTC unless there is a strong domain reason to preserve another representation.

Convert to a user's local timezone at the presentation boundary.

A common pattern is:

```text
Client timezone
      |
      v
API
      |
      v
UTC
      |
      v
MongoDB BSON Date
```

---

## Date vs String

Avoid:

```json
{
  "created_at": "21/09/2026 10:30 AM"
}
```

Prefer a BSON date.

Why?

A BSON date supports native temporal operations.

With strings, sorting may become lexicographical rather than chronological unless the string format is carefully chosen.

This:

```text
21/09/2026
02/10/2026
```

does not sort chronologically as arbitrary text.

A BSON date does not have this ambiguity.

---

## Time Zones

MongoDB's BSON Date represents an instant in time rather than a timezone-aware business calendar.

For applications that need timezone-specific concepts, distinguish between:

```text
Instant
```

and:

```text
Local date/time + timezone
```

For example, a payment timestamp is an instant:

```json
{
  "paid_at": "2026-09-21T05:00:00Z"
}
```

A recurring business event such as:

```text
Every Monday at 09:00 America/New_York
```

is a timezone-aware scheduling rule and may require storing additional timezone information.

Do not assume a timestamp alone captures a recurring local-time rule.

---

## ObjectId

`ObjectId` is one of MongoDB's most commonly used BSON types.

Example:

```python
from bson import ObjectId

user_id = ObjectId()

document = {
    "_id": user_id,
    "name": "Alice",
}
```

ObjectId is useful because drivers can generate identifiers without requiring a central ID-generation service.

### ObjectId in APIs

A MongoDB document may contain:

```python
{
    "_id": ObjectId("665c1e5d4f8e2a0012345678")
}
```

but a REST API commonly exposes the identifier as a string:

```json
{
  "id": "665c1e5d4f8e2a0012345678"
}
```

The API layer should handle the conversion explicitly.

```python
from bson import ObjectId


def parse_object_id(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise ValueError("Invalid ObjectId")

    return ObjectId(value)
```

This prevents malformed identifiers from reaching the database layer.

---

## Array

An array contains an ordered sequence of BSON values.

Example:

```json
{
  "roles": [
    "developer",
    "team-lead"
  ]
}
```

Arrays can contain:

- Strings
- Numbers
- Booleans
- Documents
- ObjectIds
- Other arrays

Example:

```json
{
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

Arrays are particularly important for MongoDB indexing because arrays can result in **multikey indexes**.

---

## Arrays and Query Semantics

MongoDB can query values inside arrays.

Example:

```javascript
db.users.find({
  roles: "developer"
})
```

This can match a document where `"developer"` appears in the `roles` array.

For arrays of documents:

```javascript
db.users.find({
  "skills.name": "Python"
})
```

When multiple conditions must apply to the same array element, `$elemMatch` can be important:

```javascript
db.users.find({
  skills: {
    $elemMatch: {
      name: "Python",
      level: "advanced"
    }
  }
})
```

Without understanding array semantics, queries can return documents that do not satisfy the intended relationship between conditions.

---

## Embedded Documents

An embedded document is a BSON document nested inside another document.

```json
{
  "name": "Alice",
  "address": {
    "city": "Kolkata",
    "country": "India"
  }
}
```

Embedded documents are useful for bounded, closely related data.

Nested fields can be queried with dot notation:

```javascript
db.users.find({
  "address.city": "Kolkata"
})
```

They can also be indexed:

```javascript
db.users.createIndex({
  "address.city": 1
})
```

This is one of the mechanisms that makes document-oriented modeling practical.

---

## Null

The BSON `null` type represents an explicit null value.

Example:

```json
{
  "middle_name": null
}
```

Do not confuse:

```text
field missing
```

with:

```text
field exists and is null
```

These are different states at the document level.

For example:

```json
{
  "name": "Alice"
}
```

does not contain `middle_name`.

Whereas:

```json
{
  "name": "Alice",
  "middle_name": null
}
```

contains the field with a null value.

This distinction matters for:

- Queries
- Schema validation
- Serialization
- API behavior
- Partial updates

---

## Missing Fields vs Null Fields

Consider:

```json
{
  "name": "Alice"
}
```

and:

```json
{
  "name": "Alice",
  "phone": null
}
```

The application may interpret these differently:

```text
Missing
    -> not provided / unknown / not applicable

Null
    -> explicitly empty / intentionally absent
```

Choose a consistent semantic convention.

In APIs, avoid allowing multiple representations of the same state without a reason:

```text
missing
null
""
"unknown"
```

Each additional representation increases application complexity.

---

## Binary

BSON supports binary data.

Python example:

```python
from bson.binary import Binary

document = {
    "payload": Binary(b"\x01\x02\x03"),
}
```

Binary can represent arbitrary bytes.

However, MongoDB should not automatically become an object-storage system.

For large files such as:

- Images
- Videos
- Large PDFs
- Backups
- Machine-learning artifacts

object storage such as Amazon S3 is often more appropriate.

MongoDB can store metadata:

```json
{
  "file_id": "file-100",
  "bucket": "documents",
  "object_key": "customers/100/invoice.pdf",
  "content_type": "application/pdf"
}
```

and the actual file can reside in object storage.

---

## Binary Data and GridFS

MongoDB provides GridFS for storing large files that exceed the normal document-size model.

GridFS divides a file into chunks and stores metadata separately.

Conceptually:

```text
Application
    |
    v
GridFS
    |
    +-- Files metadata
    |
    +-- File chunks
```

GridFS can be useful when file storage must be tightly integrated with MongoDB.

For many cloud-native architectures, however, object storage such as Amazon S3 remains the more natural choice for large files.

The decision should consider:

- File size
- Access pattern
- Storage cost
- CDN requirements
- Lifecycle policies
- Backup strategy
- Existing infrastructure

---

## Regular Expression

MongoDB supports a BSON regular expression type.

Example:

```javascript
db.users.find({
  email: {
    $regex: "@example\\.com$"
  }
})
```

Regex queries can be useful for controlled pattern matching.

However, regex queries can become expensive, especially when they cannot use an appropriate index efficiently.

Avoid using regex as a substitute for proper search infrastructure.

For large-scale text search requirements, evaluate MongoDB's supported search capabilities or a dedicated search system according to the workload.

---

## Timestamp

BSON Timestamp is distinct from BSON Date.

A MongoDB Timestamp is primarily an internal type used in MongoDB mechanisms such as replication and operation ordering.

Application developers should generally use BSON Date for business timestamps:

```json
{
  "created_at": "BSON Date"
}
```

rather than using BSON Timestamp simply because the field represents time.

The distinction is important:

| Type | Typical purpose |
|---|---|
| Date | Application/business time |
| Timestamp | MongoDB internal/replication-oriented semantics |

Do not confuse the two.

---

## MinKey and MaxKey

MongoDB provides `MinKey` and `MaxKey` as special BSON types used for comparison ordering.

They are generally relevant to:

- Internal comparison behavior
- Range semantics
- Specialized database operations

They are rarely required in ordinary backend application documents.

Do not use them as substitutes for:

```text
null
minimum numeric value
maximum numeric value
```

without understanding their BSON comparison semantics.

---

## JavaScript and JavaScript-with-Scope

MongoDB historically supported JavaScript-related BSON types.

These are not central to modern backend application design and should not be introduced into a new application merely because they exist.

Prefer:

- Application-layer Python
- Aggregation expressions
- Standard MongoDB operators

for modern backend systems.

Legacy BSON types may still appear in existing datasets, so engineers should know they exist when inspecting or migrating older data.

---

## BSON Type Comparison

MongoDB comparison and sorting behavior is influenced by BSON type.

A collection containing:

```json
{
  "value": 10
}
```

and:

```json
{
  "value": "10"
}
```

does not have a uniformly typed `value` field.

This can produce surprising query and sorting behavior.

Production collections should maintain consistent field types wherever practical.

For example, avoid:

```text
price -> Decimal128
price -> Double
price -> String
price -> null
```

unless the differences are intentional and explicitly handled.

---

## Type Consistency

Consider an `age` field.

Good:

```json
{
  "age": 32
}
```

Bad:

```json
{
  "age": "32"
}
```

and:

```json
{
  "age": null
}
```

and:

```json
{
  "age": {
    "value": 32
  }
}
```

all appearing randomly in the same collection.

Type inconsistency creates problems for:

- Queries
- Indexes
- Aggregations
- Schema validation
- Application code
- API serialization
- Data migrations

A flexible schema still needs a stable data contract.

---

## BSON and Python Type Mapping

PyMongo maps Python values to BSON types.

Common mappings include:

| Python | BSON |
|---|---|
| `str` | String |
| `bool` | Boolean |
| `int` | Integer type selected by driver |
| `float` | Double |
| `dict` | Embedded document |
| `list` | Array |
| `datetime` | Date |
| `None` | Null |
| `ObjectId` | ObjectId |
| `Decimal128` | Decimal128 |
| `bytes` / `Binary` | Binary |

Example:

```python
from datetime import datetime, timezone
from bson import ObjectId
from bson.decimal128 import Decimal128

document = {
    "_id": ObjectId(),
    "name": "Keyboard",
    "quantity": 2,
    "price": Decimal128("1499.99"),
    "active": True,
    "created_at": datetime.now(timezone.utc),
    "tags": ["hardware", "keyboard"],
    "metadata": {
        "manufacturer": "Example Corp",
    },
}
```

The driver serializes the Python representation into BSON when sending the document to MongoDB.

---

## BSON and JSON API Boundaries

BSON and JSON should be treated as separate representations.

A MongoDB document might contain:

```python
{
    "_id": ObjectId("665c1e5d4f8e2a0012345678"),
    "created_at": datetime.now(timezone.utc),
}
```

A REST API might return:

```json
{
  "id": "665c1e5d4f8e2a0012345678",
  "created_at": "2026-09-21T10:30:00Z"
}
```

The API serialization layer translates database-specific types into API-compatible representations.

This separation prevents database implementation details from leaking into external contracts.

---

## FastAPI and BSON Types

FastAPI applications commonly use Pydantic models at the API boundary.

A database document should not necessarily be returned directly:

```python
document = collection.find_one(...)
return document
```

because it may contain types such as `ObjectId` that are not part of a normal JSON API contract.

Instead, map database data into an API schema:

```python
from datetime import datetime

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: str
    name: str
    created_at: datetime
```

The conversion from:

```text
MongoDB BSON
    |
    v
Python object
    |
    v
Pydantic model
    |
    v
JSON response
```

should be deliberate.

---

## BSON and Django

When using Django with MongoDB, BSON types can cross several abstraction layers:

```text
MongoDB BSON
      |
      v
PyMongo / MongoEngine
      |
      v
Python
      |
      v
Serializer
      |
      v
JSON API
```

Be explicit about:

- ObjectId serialization
- Date serialization
- Decimal handling
- Binary fields
- Validation

Do not assume that Django's relational ORM semantics automatically apply to MongoDB.

---

## BSON Type and Indexing

BSON type consistency matters for indexes.

Suppose a collection contains:

```json
{
  "customer_id": "CUS-100"
}
```

and:

```json
{
  "customer_id": 100
}
```

A query using:

```javascript
db.orders.find({
  customer_id: "CUS-100"
})
```

is not equivalent to a query using:

```javascript
db.orders.find({
  customer_id: 100
})
```

Even when a field has the same conceptual meaning, inconsistent types can lead to incorrect assumptions about query behavior.

A strong schema contract therefore improves both correctness and index predictability.

---

## BSON Type and Aggregation

Aggregation pipelines operate on BSON values and their types.

For example, arithmetic involving:

```text
integer
double
decimal
```

can have different numeric semantics.

When financial values are involved, keep numeric representation consistent.

For example:

```json
{
  "subtotal": Decimal128("100.00"),
  "tax": Decimal128("18.00"),
  "total": Decimal128("118.00")
}
```

is easier to reason about than mixing:

```text
subtotal -> Double
tax      -> Decimal128
total    -> String
```

Aggregation correctness starts with consistent underlying data types.

---

## BSON Type and Schema Validation

Schema validation can explicitly enforce BSON types.

Example:

```javascript
db.createCollection("products", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: [
        "name",
        "price",
        "created_at"
      ],
      properties: {
        name: {
          bsonType: "string"
        },
        price: {
          bsonType: "decimal"
        },
        created_at: {
          bsonType: "date"
        }
      }
    }
  }
})
```

This protects the collection against accidental type drift.

Application validation and database validation serve different purposes:

```text
Application validation
    |
    +-- API contract
    +-- Business rules
    +-- User feedback

MongoDB validation
    |
    +-- Storage contract
    +-- Database integrity
```

Using both can provide stronger guarantees.

---

## BSON Size and Document Size

BSON encoding adds metadata around field names and values.

This means:

```text
JSON representation size
```

and:

```text
BSON storage size
```

are not necessarily identical.

MongoDB also imposes a maximum BSON document size. The exact limit should be verified against the MongoDB version being used.

This matters when designing:

- Large embedded arrays
- Large nested documents
- Binary data
- Event records
- Aggregated documents

Do not design documents that approach the maximum size under normal operation.

A document that is technically valid today may become operationally unsafe as its embedded data grows.

---

## BSON and Network Performance

BSON affects not only storage but also network transfer.

Consider a document:

```text
200 KB
```

If an API returns it on every request:

```text
1000 requests/second
```

the application may transfer approximately:

```text
200 MB/s
```

of document payload before accounting for protocol and response overhead.

This is why projection matters.

Instead of:

```javascript
db.users.find({
  status: "active"
})
```

return only required fields:

```javascript
db.users.find(
  {
    status: "active"
  },
  {
    name: 1,
    email: 1
  }
)
```

Reducing document payload can improve:

- Database performance
- Network utilization
- Application memory usage
- API latency

---

## BSON and Security

BSON types can also have security implications.

### Sensitive Data

Do not assume that storing sensitive data as binary makes it secure.

For example:

```text
Binary(password)
```

is not equivalent to encrypted data.

Passwords should be securely hashed using an appropriate password-hashing algorithm.

### ObjectId Exposure

ObjectIds are generally safe to expose as identifiers when the application design allows it, but they should not be treated as authorization controls.

This is unsafe:

```text
GET /users/<object-id>
```

followed by unrestricted retrieval solely because the ID is difficult to guess.

Authorization must still verify whether the requesting principal can access the resource.

---

## Common BSON Mistakes

### Storing Dates as Strings

Bad:

```json
{
  "created_at": "09/21/2026"
}
```

Prefer BSON Date for actual timestamps.

### Storing Money as Double

Bad:

```json
{
  "price": 19.99
}
```

when exact financial arithmetic is required.

Consider Decimal128 or integer minor units.

### Mixing Field Types

Bad:

```json
{
  "status": "active"
}
```

and:

```json
{
  "status": 1
}
```

in the same collection without a deliberate reason.

### Treating BSON as JSON

BSON contains types that JSON does not represent natively.

Do not assume:

```text
MongoDB document == API JSON document
```

### Returning BSON Directly from APIs

`ObjectId`, Decimal128, and other MongoDB-specific types should be intentionally serialized.

### Using BSON Binary for Arbitrary Large Files

Use object storage when it better fits the workload.

### Confusing Date and Timestamp

Business timestamps generally use BSON Date, while BSON Timestamp has specialized MongoDB semantics.

### Ignoring Numeric Precision

Do not mix `double`, integer, decimal, and string representations of the same business value without a deliberate schema strategy.

---

## Recommended BSON Choices

| Data | Recommended type |
|---|---|
| User name | String |
| Status | String |
| Boolean flag | Boolean |
| Small quantity | Integer |
| Large counter | Int64 |
| Exact monetary value | Decimal128 or integer minor units |
| Event timestamp | Date |
| MongoDB document ID | ObjectId or deliberate application identifier |
| Tags | Array |
| Address/profile | Embedded document |
| Large file | Object storage / GridFS where appropriate |
| Database internal timestamp | Timestamp where specifically required |
| Optional field | Missing or Null according to explicit semantics |

---

## Production BSON Checklist

Before introducing a field into a production collection, verify:

- Is the BSON type appropriate for the domain?
- Will the field be queried?
- Will the field be sorted?
- Does it need an index?
- Is the type consistent across documents?
- Can the value exceed the selected numeric range?
- Does it represent an instant or a local business time?
- Does it require exact decimal arithmetic?
- Could the value become very large?
- Will the field cross an API boundary?
- How will Python serialize it?
- How will FastAPI or Django expose it?
- Is schema validation appropriate?
- Could a type migration become expensive later?

---

## Interview Perspective

BSON questions often expose whether an engineer understands MongoDB beyond CRUD syntax.

Typical senior-level questions include:

- Why does MongoDB use BSON instead of JSON?
- What is the difference between BSON Date and Timestamp?
- When would you use Decimal128?
- Why can storing dates as strings be problematic?
- What happens when the same field contains different BSON types?
- How does ObjectId work?
- How should ObjectId be exposed through a REST API?
- How does BSON affect document size?
- Why should large files usually not be stored directly in normal documents?
- How do BSON types affect indexing and aggregation?
- How would you prevent type drift in a production collection?

A strong answer should connect the BSON type to its consequences for:

```text
Data correctness
    +
Query behavior
    +
Indexes
    +
Serialization
    +
Performance
    +
API contracts
    +
Schema evolution
```

---

## Key Takeaways

- BSON is MongoDB's binary document format and provides important types that do not exist natively in JSON, including ObjectId, Date, Decimal128, and Binary.
- BSON type choices are part of the database schema because they directly affect queries, sorting, indexing, aggregation, serialization, and data correctness.
- Use domain-appropriate types consistently: BSON Date for timestamps, Decimal128 or integer minor units for exact monetary values, and appropriate integer widths for counters and quantities.
- Keep BSON database representations separate from external JSON API contracts, explicitly converting types such as ObjectId and Decimal128 at application boundaries.
- Production MongoDB systems should prevent uncontrolled BSON type drift through application validation, database validation, deliberate schema design, and consistent migration practices.