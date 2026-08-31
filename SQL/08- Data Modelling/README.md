# Data Modelling

## Overview

This section covers the decisions that shape how data is represented, stored, and constrained in a relational database. Data modelling is not just about drawing entity-relationship diagrams — it is about making type, constraint, and integrity decisions that affect correctness, performance, storage, schema evolution, and the reliability of every application that depends on the database.

Good data modelling prevents classes of bugs that cannot be fixed with better queries. A wrong type choice, a missing constraint, or an underspecified relationship creates problems that propagate from the database layer through APIs, services, and application code.

---

## Navigation

- [01- Data Types](./01-%20Data%20Types/README.md) — Choosing correct SQL types for integers, decimals, strings, dates, UUIDs, JSON, and enums

---

## What This Section Covers

### 01- Data Types

SQL data types define what values a column can hold, how they are stored, how they are compared, and how they interact with indexes, queries, and application code. This section covers all major SQL data types from a PostgreSQL-primary perspective: integer types, decimal and numeric types, floating-point types, character types, boolean, date and time, UUID, JSON and JSONB, binary, and enum types. It also covers NULL and data types, precision and scale, choosing the right type for a requirement, storage and performance implications, and common data type mistakes in production schemas.

---

## Key Takeaways

- **Data type selection is a correctness decision, not just a storage decision** — the wrong type can allow values that violate business rules, break application assumptions, or produce silent calculation errors.
- **Use the most semantically specific type available** — prefer `DATE` over `VARCHAR` for dates, `UUID` over `BIGINT` for distributed identifiers, and `NUMERIC` over `FLOAT` for monetary values.
- **Types affect index behavior** — implicit type coercion in predicates can prevent index scans and cause full table scans on large tables.
- **Schema changes to types are costly in production** — choosing the right type upfront avoids expensive migrations, lock-intensive ALTER TABLE operations, and compatibility issues across services.
- **JSON and JSONB are not substitutes for relational modeling** — they are appropriate for genuinely variable structures; overusing them sacrifices query expressiveness, constraint enforcement, and indexing.
