# 02- Primary Keys

## Overview

A primary key is the database-level identity of a row.

For a relational table, the primary key answers a fundamental question:

> How can the database and other tables uniquely refer to this exact record?

Consider a `users` table:

```text
users

id    email
----  -------------------
101   alice@example.com
102   bob@example.com
103   carol@example.com
```

Here, `id` can uniquely identify each row.

A primary key is not merely an ID column added by convention. It is a database constraint that establishes uniqueness and non-nullability and provides a stable identity around which relationships, indexes, updates, deletes, and application references are built.

In backend systems, primary keys commonly participate in:

- API resource identification
- Foreign-key relationships
- ORM model identity
- Indexes
- Updates and deletes
- Transaction processing
- Distributed data generation
- Caching
- Event payloads
- Auditing
- Data migrations

A useful mental model is:

```text
Business Entity
      ↓
Database Row
      ↓
Primary Key
      ↓
Stable Row Identity
      ↓
Foreign Keys / Queries / APIs / Events
```

---

## What Is a Primary Key?

A primary key is a constraint that identifies each row in a table uniquely.

Example:

```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    email TEXT NOT NULL,
    is_active BOOLEAN NOT NULL
);
```

The `id` column is the primary key.

The database guarantees that:

```text
id = 1
```

cannot identify two different rows in the same table.

A primary key has two fundamental properties:

| Property | Meaning |
|---|---|
| Unique | No two rows can have the same primary-key value |
| NOT NULL | Every row must have a primary-key value |

In SQL terminology, the primary key represents an entity's **candidate key selected as the table's primary identifier**.

---

## Why Primary Keys Exist

Without a reliable row identity, application code would have difficulty referring to one specific record.

Suppose:

```text
users

name     email
-------  -------------------
Alice    alice@example.com
Bob      bob@example.com
```

An application could search by email:

```sql
SELECT *
FROM users
WHERE email = 'alice@example.com';
```

But email may not necessarily be the correct identity for the entity.

A dedicated primary key provides a stable database identity:

```text
User
 ↓
id = 42
```

Other records can reference that identity:

```text
users.id
   ↑
   │
orders.user_id
```

This creates a stable foundation for the relational model.

---

## Primary Key Constraints

Consider:

```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    email TEXT NOT NULL
);
```

The primary key effectively establishes:

```text
id
├── UNIQUE
└── NOT NULL
```

Attempting to insert duplicate values fails:

```sql
INSERT INTO users (id, email)
VALUES (1, 'alice@example.com');

INSERT INTO users (id, email)
VALUES (1, 'bob@example.com');
```

The second statement violates the primary-key constraint.

Likewise:

```sql
INSERT INTO users (id, email)
VALUES (NULL, 'alice@example.com');
```

fails because a primary key cannot contain `NULL`.

---

## Primary Key vs UNIQUE Constraint

A primary key and a `UNIQUE` constraint both enforce uniqueness, but they have different roles.

```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE
);
```

Here:

```text
id
→ primary identity

email
→ alternate unique value
```

Comparison:

| Property | Primary Key | UNIQUE |
|---|---|---|
| Uniqueness | Yes | Yes |
| Allows NULL | No | Database-dependent NULL semantics |
| One per table | One primary-key constraint | Multiple allowed |
| Represents primary identity | Yes | Not necessarily |
| Common foreign-key target | Yes | Can be |
| Main purpose | Row identity | Alternate uniqueness rule |

A table can have several unique constraints but only one primary key.

---

## Primary Key vs Candidate Key

A table may have multiple attributes that could uniquely identify a row.

Suppose:

```text
users

id
email
```

If both are guaranteed unique:

```text
id
email
```

can both be candidate keys.

The database chooses one as the primary key.

```text
Candidate Keys
├── id
└── email

Selected Primary Key
└── id
```

The remaining candidate keys can be represented using `UNIQUE` constraints.

---

## Primary Key vs Surrogate Key

A **surrogate key** is an identifier introduced specifically to provide row identity rather than deriving its value from business meaning.

Example:

```sql
id BIGINT PRIMARY KEY
```

The number `42` has no inherent business meaning.

It simply identifies the row.

This differs from a natural identifier such as:

```text
ISBN
National identifier
Business registration number
Email address
```

A common backend design is:

```text
Surrogate Primary Key
+
Business-level UNIQUE constraints
```

For example:

```sql
CREATE TABLE customers (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    tax_identifier TEXT UNIQUE
);
```

Here:

```text
id
→ technical identity

email
→ business uniqueness

tax_identifier
→ business uniqueness
```

---

## Natural Keys

A natural key derives from a real-world business attribute.

For example:

```text
country_code
ISBN
product_sku
```

A natural key can be an effective primary key when it is:

- Truly unique
- Stable
- Compact enough
- Well-defined
- Controlled by the system
- Unlikely to change

However, many business attributes evolve.

For example:

```text
email
```

may change.

Using email as the primary key can therefore create unnecessary coupling between business data and database identity.

---

## Surrogate vs Natural Primary Keys

| Consideration | Natural Key | Surrogate Key |
|---|---|---|
| Business meaning | Yes | Usually none |
| Can change | Potentially | Usually designed to remain stable |
| Foreign-key size | Depends on natural value | Often compact |
| Application coupling | Higher | Lower |
| Simple identity | Sometimes | Usually |
| Common in backend systems | Selectively | Very common |

A strong general-purpose pattern is:

```text
Stable surrogate primary key
+
Unique business identifiers
```

But this is a design decision, not a universal law.

---

## Composite Primary Keys

A primary key can consist of multiple columns.

Example:

```sql
CREATE TABLE student_courses (
    student_id BIGINT NOT NULL,
    course_id BIGINT NOT NULL,
    PRIMARY KEY (student_id, course_id)
);
```

The combination:

```text
(student_id, course_id)
```

must be unique.

This means:

```text
student_id = 1
course_id = 10
```

can appear only once.

But:

```text
student_id = 1
course_id = 20
```

is a different key.

---

## When to Use Composite Primary Keys

Composite keys are particularly natural when the identity of a row is inherently the combination of multiple attributes.

A common example is a relationship table:

```text
student_courses

student_id
course_id
```

where the pair represents enrollment.

Other examples include:

```text
tenant_id + resource_id
```

or:

```text
order_id + line_number
```

Use composite keys when the combined attributes genuinely define the entity's identity.

Do not introduce composite keys simply to avoid creating a surrogate identifier.

---

## Advantages of Composite Keys

Composite keys can:

- Model natural identity directly.
- Prevent duplicate relationships.
- Eliminate an unnecessary surrogate column.
- Express domain uniqueness clearly.

Example:

```sql
PRIMARY KEY (student_id, course_id)
```

directly expresses:

> A student can be enrolled in a course only once.

---

## Limitations of Composite Keys

Composite keys become more complicated when other tables need to reference them.

Suppose:

```text
student_courses
├── student_id
└── course_id
```

Another table referencing one enrollment may need:

```sql
FOREIGN KEY (student_id, course_id)
REFERENCES student_courses(student_id, course_id)
```

This increases:

- Foreign-key width
- Query complexity
- Index complexity
- ORM mapping complexity
- Application-level handling complexity

For this reason, many transactional systems use:

```text
id
```

as the primary key while retaining a composite `UNIQUE` constraint where appropriate.

Example:

```sql
CREATE TABLE student_courses (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES students(id),
    course_id BIGINT NOT NULL REFERENCES courses(id),
    UNIQUE (student_id, course_id)
);
```

This separates:

```text
Row identity
```

from:

```text
Business uniqueness
```

---

## Auto-Generated Integer Keys

A common primary-key strategy is a database-generated integer.

In PostgreSQL:

```sql
CREATE TABLE users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email TEXT NOT NULL UNIQUE
);
```

The database generates the value.

For example:

```text
1
2
3
4
5
...
```

The application does not need to calculate the next identifier.

### Why Database Generation Is Useful

The database can coordinate identifier generation safely across concurrent transactions.

Application code should not implement:

```sql
SELECT MAX(id) + 1
```

This is unsafe under concurrency.

Two transactions could observe the same maximum value and attempt to generate the same identifier.

---

## Identity Columns

Modern PostgreSQL supports identity columns.

Example:

```sql
CREATE TABLE orders (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Identity generation is managed by the database.

A common alternative in older PostgreSQL schemas is sequence-backed behavior, but identity columns are generally the clearer modern schema definition for generated identifiers.

---

## UUID Primary Keys

UUIDs provide a large identifier space suitable for distributed systems.

Example:

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email TEXT NOT NULL UNIQUE
);
```

A UUID might look like:

```text
550e8400-e29b-41d4-a716-446655440000
```

UUIDs are useful when identifiers need to be generated without relying on one centralized numeric sequence.

They can be generated by:

- Application code
- Database functions
- Database extensions
- UUID libraries

The exact generation strategy depends on the database and application architecture.

---

## Why UUIDs Are Attractive in Distributed Systems

Consider several application instances:

```text
API Instance A ──┐
API Instance B ──┼──→ Database
API Instance C ──┘
```

With a centralized database sequence, the database coordinates numeric identifiers.

With UUIDs, application instances can generate identifiers independently.

This can be useful for:

- Distributed writes
- Offline generation
- Event creation
- Multi-region architectures
- Data synchronization

However, UUIDs have trade-offs.

---

## UUID Trade-offs

Compared with compact integer identifiers, UUIDs generally require more storage.

They can also affect index size and locality depending on how identifiers are generated.

Randomly distributed identifiers can cause less favorable index insertion patterns than monotonically increasing identifiers.

This matters because a primary key often has an associated index.

The choice should therefore consider:

```text
Identifier requirements
+
Storage
+
Index behavior
+
Distribution
+
API exposure
```

Do not choose UUIDs merely because the system is "microservices-based."

---

## Integer vs UUID

| Characteristic | Integer / BIGINT | UUID |
|---|---|---|
| Size | Smaller | Larger |
| Human readability | Better | Lower |
| Simple database generation | Excellent | Excellent with appropriate support |
| Distributed generation | Less convenient | Convenient |
| Index size | Smaller | Larger |
| Predictability | Often sequential | Can be difficult to guess |
| Public API exposure | May reveal ordering | Less revealing |
| Typical use | Internal transactional identity | Distributed/public identifiers |

Neither is universally superior.

---

## Primary Keys and Public APIs

A database primary key may be exposed through an API.

For example:

```http
GET /users/42
```

This creates a coupling between:

```text
Database identity
```

and:

```text
Public resource identity
```

That can be acceptable for some systems.

However, sequential identifiers can reveal:

```text
Approximate record counts
Creation ordering
Potentially sensitive enumeration information
```

An endpoint such as:

```http
GET /users/43
GET /users/44
GET /users/45
```

may allow unauthorized clients to enumerate identifiers if authorization is incorrectly implemented.

Changing the identifier type does **not** replace authorization.

The correct security model is:

```text
Authentication
      ↓
Authorization
      ↓
Resource lookup
```

not:

```text
Non-sequential ID
      ↓
Security
```

---

## Primary Keys and Foreign Keys

Primary keys become especially important when tables are related.

Example:

```sql
CREATE TABLE users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email TEXT NOT NULL UNIQUE
);

CREATE TABLE orders (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    total_amount NUMERIC(12, 2) NOT NULL
);
```

The relationship is:

```text
users
┌──────────────┐
│ id PK        │
└──────┬───────┘
       │
       │ referenced by
       ▼
┌──────────────┐
│ orders       │
│ user_id FK   │
└──────────────┘
```

The primary key provides the identity.

The foreign key establishes the reference.

---

## Primary Keys and Indexes

A primary-key constraint is typically backed by a unique index or equivalent internal structure, depending on the database implementation.

For example:

```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY
);
```

The database needs an efficient way to enforce:

```text
No duplicate id
```

and to support operations such as:

```sql
SELECT *
FROM users
WHERE id = 42;
```

In PostgreSQL, creating a primary key automatically creates a unique B-tree index for the constraint.

This makes primary-key lookups efficient in typical workloads.

---

## Primary Key Lookups

A common backend operation is:

```sql
SELECT
    id,
    email,
    is_active
FROM users
WHERE id = 42;
```

The database may use the primary-key index to locate the row efficiently.

Conceptually:

```text
Query
 ↓
Primary-key index
 ↓
Matching row
 ↓
Table data
 ↓
Result
```

The exact execution strategy depends on the optimizer and current database statistics.

An index existing does not guarantee that the optimizer will use it.

---

## Primary Keys and Updates

Suppose:

```sql
UPDATE users
SET email = 'new@example.com'
WHERE id = 42;
```

The primary key identifies exactly which row should be modified.

This is preferable to an ambiguous predicate such as:

```sql
UPDATE users
SET email = 'new@example.com'
WHERE name = 'Alice';
```

where multiple rows might match.

For updates and deletes, a stable unique identity is particularly valuable.

---

## Primary Keys and Deletes

A typical delete is:

```sql
DELETE FROM users
WHERE id = 42;
```

The database can identify the target row precisely.

However, deleting a row with related foreign keys requires consideration of referential actions.

For example:

```sql
user_id BIGINT REFERENCES users(id)
```

may prevent deleting a referenced user unless the relationship is handled appropriately.

Possible strategies include:

```text
RESTRICT
CASCADE
SET NULL
```

The appropriate strategy depends on the domain.

Do not use `ON DELETE CASCADE` automatically.

Cascading deletion can remove large amounts of related data from a single operation.

---

## Primary Key Stability

A primary key should generally be stable.

Suppose:

```text
user id = 42
```

is referenced by:

```text
orders.user_id
payments.user_id
sessions.user_id
audit_logs.actor_id
```

Changing the primary key means potentially updating many references.

Therefore, avoid using mutable business attributes as primary identity when those attributes can legitimately change.

A useful principle is:

> Identity and mutable business attributes should usually be separate concerns.

---

## Primary Keys and Data Integrity

A primary key protects one of the most fundamental database invariants:

```text
Every row has exactly one primary identity.
```

Consider:

```sql
CREATE TABLE products (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sku TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL
);
```

The database now protects:

```text
id
→ unique identity

sku
→ unique business identifier

name
→ required attribute
```

This layered approach is stronger than relying solely on application code.

---

## Primary Keys and ORMs

Django automatically provides a primary-key field if a model does not define one explicitly.

Example:

```python
from django.db import models


class User(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
```

The resulting database table has a primary key for the model.

An explicit UUID strategy can be used when appropriate:

```python
import uuid

from django.db import models


class User(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    email = models.EmailField(unique=True)
```

The ORM abstraction does not eliminate the underlying database semantics.

The database still needs to enforce:

```text
Identity
Uniqueness
Foreign-key relationships
```

---

## Primary Keys and API Design

Consider a REST API:

```http
POST /users
```

The database creates:

```text
id = 42
```

The API may return:

```json
{
  "id": 42,
  "email": "alice@example.com"
}
```

The identifier then becomes part of the API contract.

This introduces a design consideration:

```text
Database identifier
        ↓
Application identifier
        ↓
Public API identifier
```

These do not necessarily need to be the same value.

Some architectures maintain:

```text
internal database ID
+
external/public resource ID
```

This can provide additional flexibility when database identity and public identity have different requirements.

---

## Primary Keys in Distributed Systems

Distributed architectures complicate identifier generation.

Consider:

```text
Service A ──┐
Service B ──┼──→ Data Store
Service C ──┘
```

If all services write to one relational database, database-generated identifiers remain straightforward.

If data is generated independently across regions or databases:

```text
Region A → Database A
Region B → Database B
```

globally unique identifiers become more important.

Possible approaches include:

- UUIDs
- Database-generated IDs with coordinated ranges
- Time-sortable identifiers
- Application-generated identifiers
- Distributed ID-generation systems

The correct approach depends on consistency, ordering, storage, and operational requirements.

---

## Ordering and Primary Keys

Do not assume:

```text
larger primary key
=
newer row
```

This may be approximately true for sequential integer identifiers, but it is not a reliable general property of primary keys.

For example:

```text
id
```

should not be used as a substitute for:

```text
created_at
```

If the application needs chronological ordering, store and query an explicit timestamp:

```sql
SELECT
    id,
    email,
    created_at
FROM users
ORDER BY created_at DESC;
```

Similarly, UUIDs generally provide no meaningful chronological ordering unless a specific time-sortable identifier scheme is used.

---

## Primary Keys and Pagination

Primary keys can be useful for keyset pagination.

Instead of:

```sql
SELECT *
FROM users
ORDER BY id
LIMIT 50 OFFSET 100000;
```

a backend can use a cursor:

```sql
SELECT *
FROM users
WHERE id > 100000
ORDER BY id
LIMIT 50;
```

This can be significantly more efficient for large datasets when the ordering and access pattern are appropriate.

However, this strategy depends on the ordering semantics of the identifier and the query requirements.

For chronological feeds, an explicit ordering key such as:

```text
created_at
+
id
```

is often more appropriate.

---

## Primary Key and Storage Considerations

Primary keys are frequently referenced by other tables.

Suppose:

```text
users.id = BIGINT
```

and 20 tables reference it.

The choice of key type affects:

- Foreign-key storage
- Index size
- Buffer/cache utilization
- Join performance
- Network payloads
- Storage requirements

A larger identifier type can multiply its cost throughout the schema.

For example:

```text
users.id
   ↓
orders.user_id
payments.user_id
sessions.user_id
audit_logs.user_id
...
```

Primary-key design should therefore consider the entire relational graph, not only the originating table.

---

## Production Considerations

### Choose Stable Identity

A primary key should normally remain stable throughout the row's lifecycle.

Avoid using attributes that users are expected to change.

### Consider Expected Scale

Choose an integer width appropriate for expected growth.

For example:

```sql
BIGINT
```

provides substantially more identifier capacity than a small integer type.

Do not choose an integer type purely because the current dataset is small.

### Consider Index Size

Primary keys commonly participate in indexes and foreign keys.

Larger identifiers can increase storage and memory requirements.

### Consider Public Exposure

If primary keys are exposed through APIs, evaluate whether predictable identifiers create enumeration or information-disclosure concerns.

Do not rely on identifier obscurity for authorization.

### Consider Distributed Generation

If identifiers must be generated independently across services or regions, evaluate UUIDs or other distributed ID strategies.

### Consider Migration Cost

Changing a primary-key type later can be expensive because dependent foreign keys and indexes may also need modification.

Choose carefully for high-value, high-volume tables.

---

## Security Considerations

Primary keys are identifiers, not authorization mechanisms.

This is unsafe:

```python
user = User.objects.get(id=user_id)
return user
```

if the endpoint does not first establish whether the requesting principal is allowed to access that user.

The correct conceptual flow is:

```text
Request
  ↓
Authenticate
  ↓
Determine principal
  ↓
Authorize access to resource
  ↓
Query by primary key
  ↓
Return permitted data
```

Sequential IDs can make enumeration easier, but UUIDs do not solve broken authorization.

A secure system must enforce access control independently of identifier format.

---

## Common Mistakes

### Using `MAX(id) + 1`

Do not generate identifiers this way:

```sql
SELECT MAX(id) + 1
FROM users;
```

Concurrent transactions can generate the same value.

Use database identity generation, sequences, UUIDs, or another concurrency-safe strategy.

### Using Mutable Business Data as Identity

Using:

```text
email
phone number
username
```

as the primary key can create unnecessary coupling if the value changes.

### Assuming Sequential IDs Are Secret

Sequential identifiers are easy to guess.

Authorization must protect the resource.

### Assuming UUIDs Provide Security

A UUID may make enumeration harder, but it does not provide authorization.

### Creating Multiple Primary Keys

A table can have only one primary-key constraint.

If multiple values need uniqueness, use:

```sql
UNIQUE
```

constraints.

### Ignoring Foreign-Key Width

Changing a primary key from a compact type to a larger type can affect every referencing foreign key and index.

### Using the Primary Key for Ordering

Do not assume:

```text
id DESC
```

means newest records unless the identifier generation semantics explicitly guarantee the required ordering.

Use explicit ordering columns.

### Choosing Composite Keys Without Considering Consumers

Composite keys can be correct relationally but can complicate:

- Foreign keys
- ORMs
- APIs
- URLs
- Application code

Evaluate the entire system before choosing one.

---

## Interview Traps

### "A Primary Key Is Just a Unique ID"

Incomplete.

A primary key is a database constraint establishing the table's primary row identity. It is unique and non-null.

### "Every Table Must Have an Integer Primary Key"

False.

Primary keys can be:

- Integer
- Big integer
- UUID
- Composite
- Other suitable types supported by the database

### "A Table Can Have Multiple Primary Keys"

A table has one primary-key constraint.

That constraint can contain multiple columns.

### "UNIQUE and PRIMARY KEY Are the Same"

They both enforce uniqueness, but they have different semantics and roles.

### "UUIDs Are Always Better"

False.

UUIDs improve distributed-generation characteristics in many designs but increase identifier size and can affect index behavior.

### "A Primary Key Determines Row Order"

False.

Relational tables do not have an inherent logical row order.

Ordering must be explicitly requested.

### "Primary Keys Prevent Duplicate Business Data"

Only if the business data itself is the primary key or covered by an appropriate unique constraint.

For example:

```sql
PRIMARY KEY (id)
```

does not prevent duplicate emails.

Use:

```sql
UNIQUE (email)
```

when email uniqueness is a business requirement.

---

## Practical Design Patterns

### Internal Surrogate Identity

```sql
CREATE TABLE users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Useful for:

- Traditional transactional systems
- Simple relational relationships
- Internal database identity

### UUID Identity

```sql
CREATE TABLE events (
    id UUID PRIMARY KEY,
    event_type TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Useful when:

- IDs are generated outside a single database sequence
- Public identifiers benefit from less predictability
- Distributed generation is important

### Composite Relationship Identity

```sql
CREATE TABLE user_roles (
    user_id BIGINT NOT NULL REFERENCES users(id),
    role_id BIGINT NOT NULL REFERENCES roles(id),
    PRIMARY KEY (user_id, role_id)
);
```

Useful when the relationship itself is naturally identified by both references.

### Surrogate Identity + Business Uniqueness

```sql
CREATE TABLE products (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sku TEXT NOT NULL,
    name TEXT NOT NULL,
    UNIQUE (sku)
);
```

Useful when the system needs a stable technical identity while also enforcing a business identifier.

---

## Decision Guide

| Requirement | Typical Choice |
|---|---|
| Simple single-database transactional application | `BIGINT` identity |
| Stable internal identity | Surrogate key |
| Business attribute is truly immutable and unique | Natural key may be appropriate |
| Distributed identifier generation | UUID or suitable distributed ID |
| Relationship uniquely identified by two entities | Composite primary key or surrogate key + `UNIQUE` |
| Public API identifier | Depends on API/security requirements |
| Large foreign-key graph | Compact stable identifier can be advantageous |
| Need chronological ordering | Use explicit timestamp/order key |
| Need uniqueness beyond primary identity | `UNIQUE` constraint |

---

## Primary Key Design Checklist

Before choosing a primary key, ask:

### Identity

- What exactly does one row represent?
- What uniquely identifies that entity?
- Should the identity ever change?

### Data Type

- Integer or UUID?
- What is the expected maximum cardinality?
- How large will referencing foreign keys become?

### Distribution

- Is identifier generation centralized?
- Can multiple services or regions generate IDs independently?
- Is offline generation required?

### Relationships

- How many tables will reference this key?
- Will composite foreign keys create unnecessary complexity?

### API

- Will the identifier be exposed externally?
- Is enumeration a concern?
- Should internal and external identifiers be separate?

### Performance

- How large will the primary-key index become?
- Will the key be used heavily in joins?
- Does the identifier generation pattern affect index locality?

### Evolution

- Can the choice be changed later?
- How expensive would changing all foreign-key references be?
- Does the schema migration strategy support the expected growth?

---

## Key Takeaways

- **A primary key establishes stable, unique, non-null identity for rows** and forms the foundation for relationships, updates, deletes, and database integrity.
- **Primary-key choice is a system-design decision**, involving integer IDs, UUIDs, natural keys, composite keys, storage, indexing, distribution, and API exposure.
- **Separate technical identity from business uniqueness when appropriate** by using a stable primary key together with explicit `UNIQUE` constraints.
- **Primary keys are not security mechanisms and do not imply ordering**; authorization and explicit ordering must be handled independently.
- **Design primary keys with the entire relational system in mind**, because key size, stability, and generation strategy propagate into foreign keys, indexes, APIs, migrations, and distributed architectures.