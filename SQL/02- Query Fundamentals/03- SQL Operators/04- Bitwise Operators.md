# 04- Bitwise Operators

## Overview

Bitwise operators manipulate the individual bits of integer values. They are less common in business-oriented SQL than comparison or logical operators, but they are useful when a database stores compact bit flags, permission masks, protocol fields, feature flags, or other encoded integer state.

Bitwise operations should be treated as a deliberate data-modeling technique rather than a default replacement for normalized relational structures. They can provide compact storage and fast bit-level checks, but they can also reduce readability, complicate indexing, and make application-level debugging harder.

The exact operator syntax varies across SQL dialects. PostgreSQL, MySQL, SQL Server, and other databases support overlapping but not identical bitwise functionality.

## Bitwise Representation

An integer is represented internally as a sequence of bits.

For example, the decimal values:

```text
1  = 0001
2  = 0010
4  = 0100
8  = 1000
```

Each bit can represent an independent boolean flag.

For example, an application might define:

| Permission | Bit value | Binary |
|---|---:|---:|
| Read | `1` | `0001` |
| Write | `2` | `0010` |
| Delete | `4` | `0100` |
| Admin | `8` | `1000` |

A user with read and write permissions can be represented by:

```text
0001
OR
0010
----
0011
```

The resulting integer is `3`.

This technique allows several independent boolean properties to be stored in a single integer column.

## Core Bitwise Operators

The most common operators are:

| Operation | Typical operator | Purpose |
|---|---|---|
| Bitwise AND | `&` | Test or retain bits present in both operands |
| Bitwise OR | `\|` | Set bits present in either operand |
| Bitwise XOR | `#` or `^` | Toggle/detect differing bits, depending on database |
| Bitwise NOT | `~` | Invert bits |
| Left shift | `<<` | Shift bits toward higher positions |
| Right shift | `>>` | Shift bits toward lower positions |

Syntax differs between database engines, so production code should follow the target database's documented operator semantics.

## Bitwise AND

Bitwise AND compares corresponding bits and produces `1` only when both bits are `1`.

```text
  1101
& 1011
------
  1001
```

For decimal values:

```sql
SELECT 13 & 11;
```

The result is:

```text
9
```

because:

```text
13 = 1101
11 = 1011
     ----
      1001 = 9
```

### Testing a Flag

Bitwise AND is particularly useful for checking whether a particular flag is set.

Suppose:

```text
READ   = 1
WRITE  = 2
DELETE = 4
ADMIN  = 8
```

and:

```text
permissions = 7
```

Binary:

```text
0111
```

To test whether `DELETE` is enabled:

```sql
SELECT
    id,
    permissions
FROM users
WHERE (permissions & 4) = 4;
```

The expression:

```text
0111 & 0100 = 0100
```

therefore the delete bit is set.

This is one of the most important production patterns for bitmask-based data.

## Bitwise OR

Bitwise OR produces `1` when either corresponding bit is `1`.

```text
  0101
| 0011
------
  0111
```

For example:

```sql
SELECT 5 | 3;
```

Conceptually:

```text
0101
0011
----
0111 = 7
```

### Setting a Flag

Suppose a user currently has:

```text
READ + WRITE = 3
```

and the application wants to enable `DELETE = 4`.

A bitwise OR can set the bit:

```sql
UPDATE users
SET permissions = permissions | 4
WHERE id = :user_id;
```

The operation is:

```text
0011
0100
----
0111
```

The existing flags remain intact while the requested flag is enabled.

## Bitwise XOR

XOR produces `1` when the corresponding bits differ.

```text
  0101
^ 0011
------
  0110
```

Some SQL dialects use `#` for XOR while others use `^`.

XOR is useful for toggling a bit:

```text
current = 0101
mask    = 0010
          ----
result  = 0111
```

Applying the same XOR operation again toggles it back:

```text
0111
0010
----
0101
```

Because syntax differs across database systems, verify the target engine before using XOR in portable SQL.

## Bitwise NOT

Bitwise NOT inverts every bit:

```text
~ 0101
  ----
  1010
```

Typical SQL syntax is:

```sql
SELECT ~5;
```

The exact result depends on the integer representation and width used by the database.

Because signed integers normally use two's-complement representation, bitwise NOT can produce a negative value. This is one reason `~` should be used carefully in application-facing queries.

A common use is generating a mask for clearing a particular bit:

```text
permissions & ~DELETE_MASK
```

For example, conceptually:

```text
permissions = 0111
DELETE_MASK = 0100

~DELETE_MASK
     ...
AND 0111
-----------
     0011
```

The exact implementation should account for the integer width and database semantics.

## Left Shift

Left shift moves bits toward higher-order positions.

```text
0011 << 1
=
0110
```

The numeric value generally doubles for each one-bit shift when overflow does not occur.

```sql
SELECT 3 << 1;
```

Conceptually:

```text
0011 → 0110
  3  →  6
```

Left shifts are commonly useful when constructing bit masks programmatically:

```text
1 << 0 = 1
1 << 1 = 2
1 << 2 = 4
1 << 3 = 8
```

This makes the relationship between flag position and mask explicit.

## Right Shift

Right shift moves bits toward lower-order positions.

```text
1100 >> 1
=
0110
```

For positive integers, this generally corresponds to integer division by a power of two.

```sql
SELECT 12 >> 1;
```

Conceptually:

```text
1100 → 0110
 12  →  6
```

For negative integers, right-shift behavior can depend on whether the database performs an arithmetic or logical shift. Do not assume cross-database portability for signed values.

## Bitmask Data Modeling

A bitmask stores multiple boolean attributes inside one integer.

For example:

```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    permissions INTEGER NOT NULL DEFAULT 0
);
```

Permission masks could be defined in application code:

```python
READ = 1 << 0
WRITE = 1 << 1
DELETE = 1 << 2
ADMIN = 1 << 3
```

A user with read and write permissions has:

```python
permissions = READ | WRITE
```

which produces:

```text
0001 | 0010 = 0011
```

The database stores:

```text
3
```

### Reading a Flag

```sql
SELECT
    id,
    (permissions & :permission_mask) = :permission_mask AS has_permission
FROM users;
```

This checks whether all bits represented by the mask are present.

For a single flag:

```sql
WHERE (permissions & :permission_mask) = :permission_mask
```

For example, checking for both `WRITE` and `DELETE`:

```text
mask = 0010 | 0100
     = 0110
```

The condition:

```sql
WHERE (permissions & 6) = 6
```

requires both bits to be set.

## Setting and Clearing Flags

Bitmasks support common state transitions.

### Set a Flag

```sql
UPDATE users
SET permissions = permissions | :mask
WHERE id = :user_id;
```

### Clear a Flag

Conceptually:

```sql
UPDATE users
SET permissions = permissions & ~:mask
WHERE id = :user_id;
```

### Toggle a Flag

Where supported:

```sql
UPDATE users
SET permissions = permissions ^ :mask
WHERE id = :user_id;
```

The exact XOR operator depends on the SQL dialect.

### Replace a Flag State

If the application needs to set a flag to a known boolean state rather than toggle it, explicitly choose between the set and clear operations.

This avoids a common concurrency problem where "toggle" does not necessarily represent the intended final state.

## Atomicity and Concurrency

Bitwise updates can be valuable because the operation can be performed directly by the database.

Prefer:

```sql
UPDATE users
SET permissions = permissions | :mask
WHERE id = :user_id;
```

over:

```text
1. SELECT permissions
2. Modify permissions in application memory
3. UPDATE permissions
```

The second pattern introduces a lost-update risk.

For example, two concurrent requests can both read:

```text
0001
```

Request A sets `WRITE`:

```text
0011
```

Request B sets `DELETE` based on its stale copy:

```text
0101
```

If request B overwrites the entire value, request A's change can be lost.

A database-side operation such as:

```sql
permissions = permissions | :mask
```

modifies the current database value and avoids this particular read-modify-write race.

Transactions and isolation requirements still apply to the broader business operation.

## Bitwise Operators and NULL

Bitwise operations involving `NULL` generally produce `NULL`.

For example:

```sql
SELECT NULL & 4;
```

does not produce `0`; it produces `NULL`.

Therefore, nullable bitmask columns introduce additional semantics.

If "no permissions" is the intended meaning, a non-null default is generally easier to reason about:

```sql
permissions INTEGER NOT NULL DEFAULT 0
```

This allows:

```text
0 = no flags set
```

instead of requiring the application to distinguish:

```text
NULL = unknown/missing
0    = explicitly no flags
```

Use `NULL` only when that distinction has real domain meaning.

## Bitwise Operators vs Boolean Columns

Bitmasks are not automatically better than normalized boolean columns.

| Approach | Advantages | Limitations |
|---|---|---|
| Boolean columns | Explicit, readable, easy to query | More columns |
| Bitmask | Compact, atomic bit operations, many flags in one value | Less readable, harder to query/index |
| Separate permission rows | Flexible, relational, easy to audit | More rows and joins |
| JSON/array structures | Flexible schema | Different indexing/query tradeoffs |

For a small number of stable flags, individual boolean columns may be clearer.

For dynamic permissions that need auditability, ownership, expiration, or metadata, a relational permission model is usually more appropriate.

Bitmasks work best when:

- The set of flags is relatively stable.
- Each flag is fundamentally boolean.
- Compact representation matters.
- The application frequently needs atomic flag updates.
- The flags do not require independent metadata.

## Performance and Indexing

A predicate such as:

```sql
WHERE (permissions & 4) = 4
```

is not equivalent to a simple equality predicate like:

```sql
WHERE permissions = 4
```

A normal B-tree index on:

```sql
permissions
```

may not efficiently support arbitrary bitwise predicates because the database must evaluate the expression against candidate values.

For performance-sensitive workloads, consider database-specific expression or functional indexes where supported.

For PostgreSQL, for example:

```sql
CREATE INDEX idx_users_delete_permission
ON users ((permissions & 4));
```

The exact index strategy should match the query and workload.

For high-volume queries, inspect the execution plan:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id
FROM users
WHERE (permissions & 4) = 4;
```

Do not assume that adding an index makes a bitwise predicate fast. Validate it with realistic data distribution.

## PostgreSQL Example

PostgreSQL supports bitwise operations on integer types.

```sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    permissions INTEGER NOT NULL DEFAULT 0
);

INSERT INTO users (permissions)
VALUES
    (1),  -- READ
    (3),  -- READ + WRITE
    (7);  -- READ + WRITE + DELETE
```

Find users with delete permission:

```sql
SELECT id
FROM users
WHERE (permissions & 4) = 4;
```

Grant delete permission:

```sql
UPDATE users
SET permissions = permissions | 4
WHERE id = :user_id;
```

Revoke delete permission:

```sql
UPDATE users
SET permissions = permissions & ~4
WHERE id = :user_id;
```

For PostgreSQL, the integer type and expression width should be chosen deliberately when masks can grow beyond the range of a 32-bit integer.

## Backend Integration

A Python service can keep the flag definitions centralized:

```python
READ = 1 << 0
WRITE = 1 << 1
DELETE = 1 << 2
ADMIN = 1 << 3

EDITOR = READ | WRITE
```

Application code can construct a mask:

```python
required_permissions = READ | WRITE
```

and pass it as a bound parameter.

With Django, a raw SQL expression can be used when the ORM does not provide the desired bitwise operation directly:

```python
from django.db.models.expressions import RawSQL

users = User.objects.annotate(
    has_write=RawSQL(
        "(permissions & %s) = %s",
        [WRITE, WRITE],
    )
).filter(has_write=True)
```

For frequently used authorization logic, encapsulate the expression rather than scattering raw SQL throughout the codebase.

The application should define the canonical mapping between names and bits. Avoid independently defining masks in multiple services because changing a bit assignment can corrupt the meaning of existing data.

## API and Authorization Considerations

Bitmasks can represent permissions internally, but APIs should generally expose meaningful permission names rather than raw integers.

Prefer:

```json
{
  "permissions": ["read", "write"]
}
```

over:

```json
{
  "permissions": 3
}
```

The raw numeric representation leaks an implementation detail and makes API consumers dependent on internal bit assignments.

At the database layer:

```sql
WHERE tenant_id = :tenant_id
  AND (permissions & :required_permission) = :required_permission
```

can enforce part of an authorization query.

However, permission checks should be designed as part of the application's complete authorization model. A bitmask should not be treated as a substitute for tenant isolation, ownership checks, role evaluation, or other access-control rules.

## Operational Considerations

Bitmask schemas require strong operational discipline.

### Keep Definitions Versioned

If:

```text
4 = DELETE
```

has been persisted for millions of rows, changing the meaning of `4` to another permission silently changes historical data semantics.

Treat bit assignments as stable schema contracts.

### Document Every Bit

Maintain a canonical mapping:

```text
Bit 0 → READ
Bit 1 → WRITE
Bit 2 → DELETE
Bit 3 → ADMIN
```

This mapping should live alongside the application model and migration history.

### Avoid Exhausting Integer Width

If an integer has a finite number of bits, eventually the available flag positions are exhausted.

Use an appropriately sized type when the number of stable flags is known to be large.

Do not casually switch between signed and unsigned representations across systems because bit positions and interpretation can change.

## Common Mistakes

### Comparing the Entire Mask

This is usually incorrect when checking for one permission:

```sql
WHERE permissions = 4;
```

It matches only users whose entire permission set is exactly `4`.

A user with:

```text
READ + DELETE = 0101 = 5
```

also has delete permission, but `permissions = 4` would exclude them.

Use:

```sql
WHERE (permissions & 4) = 4;
```

### Forgetting Parentheses

Write:

```sql
WHERE (permissions & 4) = 4;
```

rather than relying on assumptions about operator precedence when combining bitwise and comparison operators.

Parentheses make the intended expression explicit.

### Treating NULL as Zero

This:

```sql
WHERE (permissions & 4) = 4
```

does not automatically treat `NULL` as `0`.

Prefer:

```sql
permissions INTEGER NOT NULL DEFAULT 0
```

when missing permissions should mean no permissions.

### Read-Modify-Write in Application Code

Avoid:

```text
SELECT permissions
→ modify in Python
→ UPDATE permissions
```

for simple flag mutations.

Prefer an atomic database expression:

```sql
UPDATE users
SET permissions = permissions | :mask
WHERE id = :user_id;
```

### Reusing Bit Assignments

Never change the meaning of an existing bit without migrating stored data.

If historical rows interpret:

```text
4 = DELETE
```

then redefining:

```text
4 = EXPORT
```

can create silent authorization errors.

### Exposing Raw Masks in Public APIs

Avoid making API clients understand:

```text
3 = READ + WRITE
```

Expose stable semantic names instead.

### Assuming Cross-Database Portability

Bitwise syntax, integer behavior, operator precedence, and supported data types vary across SQL engines.

Validate queries against the actual production database engine.

## Security Considerations

Bitmasks are commonly used for permissions, which makes correctness security-sensitive.

A query such as:

```sql
WHERE (permissions & :mask) = :mask
```

must not be the only protection when access also depends on tenant, ownership, resource state, or role.

For example:

```sql
SELECT id
FROM documents
WHERE tenant_id = :tenant_id
  AND owner_id = :user_id
  AND (permissions & :required_permission) = :required_permission;
```

Be careful when constructing masks from user-controlled input. The application should map accepted permission names to predefined constants rather than allowing arbitrary numeric masks.

Prefer:

```python
ALLOWED_PERMISSIONS = {
    "read": READ,
    "write": WRITE,
    "delete": DELETE,
}
```

over accepting arbitrary integers from an API client.

Authorization logic should also have regression tests covering combinations of permissions, tenants, ownership, and resource states.

## Production Guidance

Use bitwise operators when the data model genuinely represents a compact set of independent flags.

Recommended practices:

- Define masks centrally.
- Keep bit assignments stable.
- Use `NOT NULL DEFAULT 0` when `NULL` has no business meaning.
- Use database-side bit operations for atomic flag mutations.
- Use parentheses around mixed bitwise/comparison expressions.
- Test nullable and boundary cases.
- Do not expose raw masks as public API contracts.
- Validate performance with realistic execution plans.
- Consider expression indexes for frequently queried flags where supported.
- Prefer normalized relational models when permissions need metadata, auditing, expiration, or independent lifecycle management.
- Document the bit-to-meaning mapping as part of the schema contract.
- Test authorization queries as security-critical code.

## Interview Traps

| Question | Key Point |
|---|---|
| How do you check whether a bit is set? | `(value & mask) = mask` |
| Why isn't `value = mask` sufficient? | It requires the entire value to equal the mask |
| How do you set a bit? | `value \| mask` |
| How do you clear a bit? | `value & ~mask` |
| What does XOR commonly provide? | A way to toggle bits |
| Why can bitmasks complicate indexing? | Arbitrary bitwise predicates are not simple equality/range predicates |
| Why use `NOT NULL DEFAULT 0`? | It gives a clear representation for "no flags" |
| Why can changing a bit assignment be dangerous? | Existing persisted integers retain the old interpretation |
| Are bitwise operators portable across SQL databases? | No; syntax and semantics vary |
| When is a relational permission model preferable? | When permissions need metadata, auditing, relationships, or independent lifecycle management |

## Key Takeaways

- Bitwise operators manipulate integer bits and are useful for compact, stable sets of boolean flags.
- Use `(value & mask) = mask` to test flags, `value | mask` to set them, and `value & ~mask` to clear them.
- Database-side bitwise updates can avoid lost-update problems associated with application-level read-modify-write logic.
- Bitmasks trade compactness for readability, indexing complexity, and schema rigidity; use relational models when flags require independent metadata or lifecycle management.
- Treat bit assignments as stable schema contracts and validate database-specific syntax, performance, and authorization behavior before production use.