# 03- SQL Standards and Database Dialects

## Overview

SQL is standardized, but production database systems do not implement SQL identically.

The SQL language is defined through standards maintained by organizations such as ISO and IEC. Database systems such as PostgreSQL, MySQL, Microsoft SQL Server, Oracle Database, and SQLite implement those standards to different degrees and add their own extensions.

For backend engineers, the important distinction is:

```text
SQL Standard
     │
     ├── Common SQL concepts and syntax
     │
     └── Database-specific extensions
              │
              ├── PostgreSQL
              ├── MySQL
              ├── SQL Server
              ├── Oracle
              └── SQLite
```

Most application-level SQL can be written using widely supported constructs. However, production systems frequently depend on database-specific capabilities for performance, data types, indexing, concurrency, JSON processing, full-text search, procedural logic, and administration.

The engineering goal is therefore not to avoid dialect-specific SQL completely. It is to **know which parts of a query are portable, which parts are database-specific, and when the additional capability is worth the portability cost**.

---

## What Is the SQL Standard?

The SQL standard defines a common language and behavioral foundation for relational database systems.

It specifies concepts such as:

- Tables
- Columns
- Data types
- Queries
- Filtering
- Aggregation
- Joins
- Constraints
- Transactions
- Data modification
- Schema definition

A simplified example of standard-style SQL is:

```sql
SELECT
    id,
    email
FROM users
WHERE is_active = TRUE
ORDER BY created_at DESC;
```

The existence of a standard does not mean that every database implements every feature identically.

The standard has evolved through multiple revisions over time, adding and refining capabilities.

For practical backend engineering, the standard is best viewed as a **common foundation**, not as a guarantee of complete cross-database compatibility.

---

## Why SQL Dialects Exist

Database vendors have different implementation goals and architectures.

A database may extend SQL to provide capabilities that are:

- Performance-oriented
- Storage-engine-specific
- Security-specific
- Operationally useful
- Designed for a particular workload
- Difficult to express through standard SQL alone

For example, PostgreSQL provides features such as:

```sql
SELECT
    payload->>'email'
FROM events;
```

for JSON processing.

Another database may provide a different syntax for equivalent functionality.

These extensions create a trade-off:

```text
Standard SQL
    │
    ├── Better portability
    ├── Easier database migration
    └── Smaller common feature set

Database-specific SQL
    │
    ├── Access to advanced capabilities
    ├── Better integration with the chosen database
    └── Reduced portability
```

Neither side is inherently better.

The correct choice depends on the application's requirements.

---

## SQL Standard vs Database Dialect

| Concept | SQL Standard | Database Dialect |
|---|---|---|
| Definition | Common language specification | Vendor-specific implementation |
| Portability | Generally higher | Generally lower |
| Syntax | Common constructs | Standard + extensions |
| Data types | Common types | Additional database-specific types |
| Functions | Standard functions | Vendor-specific functions |
| Indexes | Conceptual support | Database-specific index implementations |
| Transactions | Standard concepts | Different implementation details |
| JSON | Standardized capabilities exist | Syntax and features vary |
| Procedural SQL | Varies by feature | Often vendor-specific |
| Administration | Usually outside core SQL | Strongly database-specific |
| Optimization hints | Limited/varies | Often database-specific |
| Best use | Portable application logic | Database-specific engineering |

---

## Common SQL That Is Highly Portable

Many basic SQL operations are supported across major relational databases.

### Selecting Data

```sql
SELECT
    id,
    email
FROM users;
```

### Filtering

```sql
SELECT
    id,
    email
FROM users
WHERE is_active = TRUE;
```

### Ordering

```sql
SELECT
    id,
    email
FROM users
ORDER BY created_at DESC;
```

### Aggregation

```sql
SELECT
    user_id,
    COUNT(*) AS order_count
FROM orders
GROUP BY user_id;
```

### Basic Joins

```sql
SELECT
    u.id,
    u.email,
    o.id AS order_id
FROM users AS u
JOIN orders AS o
    ON o.user_id = u.id;
```

### Data Modification

```sql
INSERT INTO users (
    email,
    is_active
)
VALUES (
    'user@example.com',
    TRUE
);
```

These constructs form a useful portable SQL core.

However, even seemingly simple operations can have differences in edge cases, data types, implicit conversions, NULL behavior, or optimizer behavior.

---

## Common Areas of Dialect Differences

Dialect differences become more significant in several areas.

### Data Types

Databases do not expose identical type systems.

Examples include:

- Integer types
- Decimal types
- Boolean types
- UUIDs
- JSON
- Arrays
- Enumerations
- Binary types
- Spatial types
- Date and time types

PostgreSQL, for example, supports:

```sql
CREATE TABLE events (
    id BIGINT PRIMARY KEY,
    payload JSONB NOT NULL
);
```

Another database may use a different type or syntax for JSON storage.

### Functions

Date, string, mathematical, JSON, and system functions can vary.

For example, obtaining the current timestamp is commonly expressed as:

```sql
CURRENT_TIMESTAMP
```

but vendor-specific alternatives and behaviors also exist.

### Pagination

Different databases have historically used different syntax for limiting result sets.

PostgreSQL and MySQL commonly support:

```sql
SELECT
    id,
    email
FROM users
ORDER BY id
LIMIT 20 OFFSET 40;
```

SQL Server commonly uses:

```sql
SELECT
    id,
    email
FROM users
ORDER BY id
OFFSET 40 ROWS
FETCH NEXT 20 ROWS ONLY;
```

The underlying requirement is the same, but the syntax differs.

### Auto-Generated Keys

Identity generation differs between systems and database versions.

Examples include:

- PostgreSQL identity columns
- MySQL `AUTO_INCREMENT`
- SQL Server `IDENTITY`
- Oracle identity columns or sequences

These differences can affect schema migrations and ORM configuration.

---

## NULL Behavior and Dialect Considerations

`NULL` is part of SQL's relational semantics, but specific functions and operators can differ.

For example, handling a fallback value may use:

```sql
SELECT COALESCE(display_name, 'Unknown')
FROM users;
```

`COALESCE` is broadly portable.

A database may additionally provide proprietary alternatives.

The general engineering principle is:

> Prefer standard constructs when they express the requirement clearly, unless a database-specific construct provides a meaningful benefit.

This makes intent easier to understand and can reduce unnecessary coupling.

---

## String Function Differences

String manipulation is another area where dialects diverge.

Portable concepts include:

```sql
SELECT
    UPPER(email),
    LOWER(email)
FROM users;
```

But function names and semantics for operations such as:

- String length
- Concatenation
- Substring extraction
- Regular expressions
- String splitting
- Formatting

can vary significantly.

For example, concatenation may be expressed using:

```sql
SELECT first_name || ' ' || last_name
FROM users;
```

in PostgreSQL, while other systems may favor functions such as:

```sql
CONCAT(first_name, ' ', last_name)
```

When portability matters, prefer widely supported constructs or isolate dialect-specific expressions behind the data-access layer.

---

## Date and Time Dialects

Date and time handling is one of the most error-prone areas when moving between database systems.

Differences can involve:

- `DATE`
- `TIME`
- `TIMESTAMP`
- Time-zone-aware timestamps
- Current-time functions
- Date arithmetic
- Date extraction
- Date truncation
- Formatting
- Interval syntax

For example, PostgreSQL supports:

```sql
SELECT
    CURRENT_TIMESTAMP,
    CURRENT_DATE;
```

and interval expressions such as:

```sql
SELECT
    CURRENT_TIMESTAMP - INTERVAL '7 days';
```

Equivalent operations can use different syntax in other databases.

Production systems should avoid assuming that date arithmetic is portable merely because the underlying concept is common.

---

## Identifier Quoting

SQL databases differ in how identifiers interact with reserved words, case sensitivity, and quoting.

A table such as:

```sql
CREATE TABLE orders (
    id BIGINT PRIMARY KEY
);
```

is straightforward.

Problems begin when identifiers use:

- Reserved keywords
- Mixed-case names
- Special characters
- Database-specific naming conventions

For example:

```sql
SELECT
    "order"
FROM orders;
```

may be valid in one database while behaving differently or requiring different quoting rules elsewhere.

A better production practice is to use conventional, predictable identifiers:

```text
snake_case
lowercase
non-reserved names
```

and avoid unnecessary quoted identifiers.

---

## Boolean Differences

Boolean support varies between database systems.

PostgreSQL has a native Boolean type:

```sql
CREATE TABLE users (
    is_active BOOLEAN NOT NULL
);
```

Queries can use:

```sql
SELECT *
FROM users
WHERE is_active = TRUE;
```

Other systems may historically represent boolean-like values differently.

When writing portable schema and application code, verify the target database's type semantics instead of assuming that `BOOLEAN` behaves identically everywhere.

---

## Auto-Increment and Identity Columns

Generated primary keys are a common source of dialect differences.

A modern PostgreSQL approach is:

```sql
CREATE TABLE users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email TEXT NOT NULL UNIQUE
);
```

MySQL commonly uses:

```sql
CREATE TABLE users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE
);
```

The application requirement is the same:

```text
Insert user
    ↓
Database generates identifier
    ↓
Application receives identifier
```

The schema syntax is database-specific.

This matters when:

- Migrating databases
- Writing raw migration scripts
- Supporting multiple database backends
- Using database-independent libraries
- Designing infrastructure-as-code

---

## PostgreSQL Dialect

PostgreSQL is often a strong default database for backend systems because it combines broad SQL support with advanced relational features.

Important PostgreSQL-specific capabilities include:

- `JSONB`
- Arrays
- Rich indexing options
- Partial indexes
- Expression indexes
- `ILIKE`
- `RETURNING`
- `ON CONFLICT`
- `LATERAL`
- PostgreSQL-specific range types
- Advanced full-text search
- Extensions
- Rich transaction and concurrency capabilities

For example:

```sql
INSERT INTO users (
    email
)
VALUES (
    'user@example.com'
)
ON CONFLICT (email)
DO UPDATE
SET updated_at = CURRENT_TIMESTAMP
RETURNING id;
```

This is powerful production SQL, but it is not something you should assume can be copied unchanged into every relational database.

If PostgreSQL is the chosen production database, using PostgreSQL features is often entirely reasonable.

---

## MySQL Dialect

MySQL is another widely used relational database.

It has its own syntax, storage-engine behavior, functions, indexing capabilities, and operational characteristics.

For example, MySQL commonly uses:

```sql
CREATE TABLE users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE
);
```

MySQL-specific behavior can matter when working with:

- Character sets
- Collations
- Storage engines
- JSON
- Generated columns
- Indexes
- Replication
- Transaction behavior

A query that behaves correctly in PostgreSQL should not automatically be assumed to behave identically in MySQL.

---

## SQL Server Dialect

Microsoft SQL Server provides its own SQL dialect, commonly referred to as T-SQL.

Examples include:

```sql
SELECT TOP 20
    id,
    email
FROM users
ORDER BY created_at DESC;
```

SQL Server also provides database-specific features involving:

- Identity columns
- T-SQL procedural logic
- Execution-plan tooling
- Indexing
- Temporal tables
- Security
- Query hints
- Administration

When working with SQL Server, learning standard SQL first still provides a strong foundation, but T-SQL becomes necessary for database-specific engineering.

---

## Oracle Dialect

Oracle Database provides its own SQL and procedural ecosystem, including PL/SQL.

Oracle has long-standing capabilities around:

- Sequences
- PL/SQL
- Advanced indexing
- Partitioning
- Enterprise security
- High availability
- Database administration

For example, Oracle applications may use sequences explicitly for identifiers.

The important lesson is the same: **SQL concepts transfer, but implementation details do not always transfer.**

---

## SQLite Dialect

SQLite is a lightweight embedded relational database.

It is commonly used for:

- Local development
- Testing
- Mobile applications
- Embedded systems
- Small standalone applications

Its architecture differs significantly from server-based databases such as PostgreSQL.

For example:

```text
Application
    │
    ▼
SQLite library
    │
    ▼
Database file
```

rather than:

```text
Application
    │
    ▼
Network connection
    │
    ▼
Database server
    │
    ▼
Storage
```

This architectural difference means that SQLite should not automatically be treated as a drop-in production substitute for PostgreSQL in server applications.

---

## Dialect Comparison

| Area | PostgreSQL | MySQL | SQL Server | Oracle | SQLite |
|---|---|---|---|---|---|
| SQL support | Extensive | Extensive | Extensive | Extensive | Broad subset |
| Server architecture | Client/server | Client/server | Client/server | Client/server | Embedded |
| JSON | Strong | Strong | Strong | Strong | Available with JSON functions |
| Procedural language | PL/pgSQL | SQL/PSM and extensions | T-SQL | PL/SQL | Limited |
| Rich indexing | Yes | Yes | Yes | Yes | More limited |
| Transactions | Strong | Strong | Strong | Strong | Supported with different concurrency characteristics |
| Extensions | Extensive | More limited | Extensive ecosystem | Extensive ecosystem | Limited |
| Typical backend use | Excellent | Excellent | Excellent | Enterprise-heavy | Embedded/testing/smaller workloads |

The exact feature set depends on database version and configuration.

---

## Portability Levels

SQL portability is not binary.

It is useful to think of portability as levels.

```text
High Portability
      │
      ▼
Standard SELECT / WHERE / JOIN
      │
      ▼
Common Aggregation / DML
      │
      ▼
Database-Specific Data Types
      │
      ▼
Database-Specific Functions
      │
      ▼
Database-Specific Indexes
      │
      ▼
Procedural SQL / Extensions
      │
      ▼
Database Administration
      │
      ▼
Low Portability
```

An application does not need to remain entirely at the top of this spectrum.

The correct level depends on the system.

---

## When to Prefer Standard SQL

Prefer broadly portable SQL when:

- Multiple database engines must be supported
- A database migration is likely
- You are building a reusable library
- The SQL is simple enough that portability has little cost
- The database-specific feature provides no meaningful benefit
- Cross-database testing is important

For example:

```sql
SELECT
    id,
    email
FROM users
WHERE is_active = TRUE;
```

does not need a vendor-specific implementation.

Using standard syntax keeps the query easy to understand and migrate.

---

## When to Use Database-Specific SQL

Database-specific SQL is justified when it provides a meaningful engineering advantage.

Examples include:

- Advanced indexing
- High-performance upserts
- JSON querying
- Full-text search
- Specialized data types
- Advanced windowing capabilities
- Database-specific locking
- Efficient bulk operations
- Specialized partitioning
- Query optimizer features

For PostgreSQL:

```sql
INSERT INTO users (
    email
)
VALUES (
    'user@example.com'
)
ON CONFLICT (email)
DO NOTHING;
```

If PostgreSQL is the system of record and this behavior is useful, avoiding it solely for theoretical portability may be unnecessary.

The decision should consider:

```text
Business requirement
        ↓
Performance requirement
        ↓
Operational requirement
        ↓
Portability requirement
        ↓
Database-specific capability
        ↓
Engineering trade-off
```

---

## Portability vs Capability Trade-off

| Approach | Portability | Database Capability | Complexity |
|---|---:|---:|---:|
| Standard SQL | High | Moderate | Low |
| Mostly standard + limited extensions | High/Moderate | High | Moderate |
| Database-specific SQL | Low | Very high | Moderate/High |
| Database-specific architecture | Low | Very high | High |

There is no universal optimal point.

For a small application that may switch databases, portability can be valuable.

For a mature PostgreSQL system with billions of rows, refusing PostgreSQL-specific features can unnecessarily limit the system.

---

## Database Abstraction Layers

Backend applications commonly use abstraction layers to reduce direct coupling to SQL dialects.

Examples include:

- Django ORM
- SQLAlchemy
- JPA/Hibernate
- Entity Framework

An ORM may allow:

```python
users = (
    User.objects
    .filter(is_active=True)
    .order_by("-created_at")
)
```

without requiring the application developer to write database-specific SQL directly.

However, abstraction is not absolute.

A production application may eventually need:

```python
User.objects.raw(...)
```

or SQLAlchemy textual SQL:

```python
from sqlalchemy import text

query = text("""
    SELECT id, email
    FROM users
    WHERE is_active = :active
""")
```

At that point, the database dialect becomes relevant again.

---

## Database Abstraction Is Not Database Independence

An ORM can abstract syntax, but it does not automatically abstract:

- Query performance
- Transaction semantics
- Locking
- Isolation levels
- Index behavior
- Execution plans
- Replication
- Failure modes
- Database-specific data types

For example:

```text
Django ORM
    ↓
Generated SQL
    ↓
PostgreSQL
```

and:

```text
Django ORM
    ↓
Generated SQL
    ↓
MySQL
```

may produce semantically similar operations but different SQL and different execution behavior.

Therefore:

> ORM portability does not imply operational database portability.

This distinction is particularly important for senior backend engineers.

---

## Portability and Schema Migrations

Database dialect differences become especially visible during migrations.

A migration might need to:

- Add a column
- Change a data type
- Create an index
- Create a constraint
- Backfill data
- Add generated columns
- Create database-specific objects

A migration that works on PostgreSQL may not work unchanged on MySQL.

Production migrations should therefore be tested against the actual production database engine.

For example:

```text
Migration
    ↓
CI database
    ↓
Integration tests
    ↓
Staging database
    ↓
Production database
```

Do not assume that passing application tests against SQLite means that PostgreSQL production migrations are safe.

---

## Testing Across Dialects

If an application genuinely supports multiple database engines, test each supported engine.

A useful architecture is:

```text
Application Test Suite
        │
        ├───────────────┐
        ▼               ▼
 PostgreSQL           MySQL
        │               │
        ▼               ▼
Dialect-specific       Dialect-specific
integration tests      integration tests
```

Unit tests can often use mocks or lightweight databases, but integration tests should exercise the actual database engine for important behavior.

This is especially important for:

- Transactions
- Constraints
- Locking
- Query semantics
- Date and time behavior
- JSON operations
- Index-dependent queries
- Migrations
- Upserts

---

## Production Recommendation for Backend Engineers

If your application uses a single database engine, optimize for that engine rather than maintaining unnecessary theoretical portability.

For example, if production uses PostgreSQL:

```text
Application
    ↓
Django / FastAPI
    ↓
PostgreSQL driver
    ↓
PostgreSQL
```

Learn:

1. Standard SQL fundamentals
2. PostgreSQL SQL dialect
3. PostgreSQL data types
4. PostgreSQL indexing
5. PostgreSQL transactions and concurrency
6. PostgreSQL execution plans
7. PostgreSQL operational behavior

This produces more useful engineering knowledge than attempting to write every query for five database systems simultaneously.

If database portability is a real product requirement, explicitly design for it instead.

---

## Recommended Portability Strategy

A practical strategy is:

### Keep business logic portable

Business rules should generally live in application code where appropriate rather than being unnecessarily tied to a specific database dialect.

### Keep basic SQL portable

Use common SQL for straightforward operations.

### Isolate database-specific SQL

When vendor-specific SQL is necessary, keep it identifiable within:

- Repository layers
- Data-access modules
- Migration files
- Database adapters
- Dedicated query modules

### Document important dependencies

If a feature depends on PostgreSQL, make that dependency explicit.

For example:

```python
# PostgreSQL-specific:
# Uses ON CONFLICT for atomic upsert behavior.
```

### Test the actual production database

Database behavior should be validated against the engine that will run the workload.

---

## Security Implications

Dialect differences can affect security.

Database-specific features may introduce:

- Different privilege models
- Different role semantics
- Different authentication mechanisms
- Different row-level security behavior
- Different dynamic SQL mechanisms
- Different stored procedure capabilities

Parameterized queries remain important regardless of database:

```python
cursor.execute(
    """
    SELECT id, email
    FROM users
    WHERE email = %s
    """,
    (email,),
)
```

Do not assume that switching database engines removes SQL injection risks.

Likewise, database-specific administrative commands should be treated as privileged operations.

---

## Performance Implications

A portable SQL query is not necessarily the fastest query on every database.

The same logical query may produce different execution plans:

```text
Same SQL
   │
   ├── PostgreSQL → Plan A
   │
   ├── MySQL      → Plan B
   │
   └── SQL Server → Plan C
```

This occurs because each database has its own:

- Query optimizer
- Statistics
- Cost model
- Index implementation
- Storage architecture
- Execution engine

Therefore, performance testing must be performed against the actual database engine and workload.

Use the database's execution-plan tooling rather than assuming portability implies equivalent performance.

---

## Operational Implications

Database dialect knowledge becomes particularly important during operations.

Examples include:

- Backup and restore
- Replication
- Failover
- Monitoring
- Index maintenance
- Vacuuming
- Statistics management
- Connection management
- Lock inspection
- Query diagnostics

For example, PostgreSQL has operational concepts such as `VACUUM` and `ANALYZE` that are deeply tied to its storage and MVCC implementation.

Another database may have entirely different maintenance requirements.

Therefore:

```text
SQL portability
        ≠
Operational portability
```

An application migration requires much more than translating SQL syntax.

---

## Common Mistakes

### Assuming SQL is identical everywhere

SQL has a standard, but real databases implement dialects and extensions.

**Avoid it:** Learn standard SQL first, then learn the dialect of your production database.

### Avoiding all database-specific features

Some engineers treat portability as an absolute requirement.

**Why it is a problem:** You may give up valuable performance or functionality without a real business requirement for portability.

**Avoid it:** Evaluate the actual cost and benefit of database-specific features.

### Assuming ORM means database independence

An ORM abstracts many operations but cannot eliminate differences in execution behavior, transactions, indexes, and database capabilities.

**Avoid it:** Understand the generated SQL and production database.

### Testing only with SQLite

This is particularly common in Python applications.

**Why it is dangerous:** SQLite's architecture and behavior differ from PostgreSQL or MySQL in important areas.

**Avoid it:** Run integration tests against the actual production database engine.

### Copying SQL between databases without verification

A query that works in PostgreSQL may fail in MySQL or SQL Server.

**Avoid it:** Verify syntax and semantics against the target database.

### Ignoring data type differences

A type such as `JSONB`, `UUID`, or a database-specific timestamp type may not have a direct equivalent.

**Avoid it:** Treat schema portability as a separate engineering problem from query portability.

### Assuming equivalent syntax means equivalent performance

Two databases may accept similar SQL while producing very different execution plans.

**Avoid it:** Benchmark and inspect execution plans on the target engine.

### Using vendor-specific SQL without isolating it

Scattered dialect-specific SQL makes future migrations harder.

**Avoid it:** Keep database-specific operations in clearly defined data-access or migration boundaries.

---

## Interview Perspective

Important interview questions around SQL standards and dialects include:

- What is the difference between SQL and a SQL dialect?
- Is SQL fully standardized?
- Why do PostgreSQL and MySQL use different syntax?
- What parts of SQL are portable?
- When should you use database-specific SQL?
- Does using an ORM make an application database-independent?
- Why can the same SQL query perform differently on different databases?
- Why is SQLite not always a good substitute for PostgreSQL in tests?
- What problems occur when migrating between relational databases?
- How do database-specific data types affect portability?
- How should database-specific SQL be isolated in a backend application?

A strong senior-level answer should recognize the trade-off rather than claiming that either portability or vendor-specific optimization is always correct.

A useful formulation is:

> Standard SQL provides a portable foundation, but production databases expose dialect-specific syntax and capabilities. I prefer standard SQL where it is sufficient, but I use database-specific features when they provide meaningful correctness, performance, or operational benefits. I isolate those dependencies, test against the actual production database, and treat migrations as both a schema and operational compatibility problem.

---

## Practical Decision Framework

When deciding whether to use a database-specific feature, evaluate:

| Question | If Yes |
|---|---|
| Does standard SQL solve the problem adequately? | Prefer standard SQL |
| Is database portability a real requirement? | Favor portable SQL |
| Does the vendor feature materially improve performance? | Consider vendor-specific SQL |
| Does it provide required functionality unavailable otherwise? | Consider vendor-specific SQL |
| Is the feature easy to isolate? | Lower migration risk |
| Is the feature deeply embedded throughout the application? | Higher migration cost |
| Has the behavior been tested against production DB? | Safer |
| Does the feature affect transactions or correctness? | Test extensively |
| Does it affect operational behavior? | Document and operationalize it |
| Is the portability benefit only theoretical? | Do not over-optimize for portability |

The key is to make the trade-off explicit rather than accidental.

---

## Key Takeaways

- **SQL provides a standardized foundation, but PostgreSQL, MySQL, SQL Server, Oracle, and SQLite implement different dialects and extensions.**
- **Use standard SQL when it provides sufficient functionality and portability has real value; use database-specific capabilities when they provide meaningful engineering benefits.**
- **ORMs abstract SQL syntax but do not make databases operationally equivalent**; query performance, transactions, indexes, locking, data types, and failure behavior remain database-specific.
- **Database portability must be tested at the schema, query, transaction, migration, and operational levels**, not just by checking whether application code runs.
- **For production backend engineering, learn standard SQL first and then become deeply proficient in the dialect and operational behavior of the database you actually run.**