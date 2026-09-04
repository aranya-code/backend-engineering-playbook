# 18- Database Design Exercises

## Overview

Database design is the process of translating business requirements into durable data structures, relationships, constraints, access patterns, and operational boundaries.

For backend engineers, good database design is more than choosing tables and columns. A production design must answer:

- What data exists?
- What does each row represent?
- Which relationships exist?
- Which invariants must always hold?
- Where should normalization stop?
- Which queries must be fast?
- Which constraints belong in PostgreSQL?
- How will the schema evolve?
- How will concurrent requests behave?
- How will the design scale?
- How will backups, replication, migrations, and observability work?

These exercises progress from relational modeling to production-oriented database architecture. PostgreSQL is the primary database used in the examples.

---

## Practice Schema

The following exercises use a mixture of existing and newly designed schemas. Unless an exercise specifies otherwise, assume PostgreSQL.

A typical commerce domain might contain:

```text
customers
    ↓
orders
    ↓
order_items
    ↓
products
    ↓
inventory
```

with supporting entities such as:

```text
customers
addresses
orders
order_items
products
categories
payments
shipments
inventory
```

### Exercise Data Model

Start by designing the schema yourself rather than copying a predefined implementation.

Assume these business requirements:

- A customer can have many orders.
- An order belongs to exactly one customer.
- An order contains one or more products.
- A product can appear in many orders.
- Product prices can change over time.
- An order must preserve the price charged at purchase time.
- An order can have multiple payment attempts.
- Only one payment can represent the successful payment for an order.
- Inventory belongs to a product.
- Stock cannot become negative.
- Customers can have multiple addresses.
- An address can be marked as the customer's default shipping address.

---

## Exercise: Identify Entities

Given the commerce requirements, identify the primary entities.

### Tasks

Determine:

1. Which concepts deserve their own tables?
2. Which concepts are attributes rather than entities?
3. Which relationships are one-to-one?
4. Which relationships are one-to-many?
5. Which relationships are many-to-many?
6. Which relationships require an associative table?

Produce an initial entity list before writing SQL.

---

## Exercise: Define Row Grain

For each table, describe exactly what one row represents.

Example:

```text
customers
One row = one customer
```

### Tasks

Define the row grain for:

- Customer.
- Order.
- Order item.
- Product.
- Payment.
- Inventory record.
- Address.
- Shipment.

Explain why ambiguous row grain causes downstream problems in:

- Queries.
- Aggregations.
- Constraints.
- Updates.
- Reporting.
- ORM models.

---

## Exercise: Customer and Order Relationship

Design:

```text
customer → orders
```

Requirements:

- A customer can have zero or more orders.
- Every order must belong to a customer.
- Deleting a customer should not accidentally delete financial history.

### Tasks

Design the foreign key.

Decide whether the relationship should use:

```sql
ON DELETE CASCADE
```

or:

```sql
ON DELETE RESTRICT
```

or another strategy.

Explain the business implications of each choice.

---

## Exercise: Many-to-Many Product Relationship

An order contains multiple products, and each product can belong to multiple orders.

### Tasks

Design the relationship between:

```text
orders
products
```

using:

```text
order_items
```

Determine which columns belong in `order_items`.

Consider:

```text
quantity
unit_price
discount
tax
created_at
```

Explain why `unit_price` should normally be stored in the order item even if `products.price` exists.

---

## Exercise: Composite Primary Key vs Surrogate Key

For `order_items`, compare:

```text
(order_id, product_id)
```

as a composite primary key with:

```text
id
```

as a surrogate primary key plus:

```text
UNIQUE(order_id, product_id)
```

### Tasks

Evaluate:

- Referential integrity.
- ORM behavior.
- Foreign keys from other tables.
- Query simplicity.
- Uniqueness.
- Future requirements such as product substitutions or multiple line entries.

Choose a design and justify it.

---

## Exercise: Product Price History

A product's price changes over time.

Requirements:

```text
Product A
$100 → $120 → $135
```

An existing order must continue displaying the original price.

### Tasks

Design a model for:

```text
products
product_prices
order_items
```

Determine:

- Effective start time.
- Effective end time.
- Current price.
- Historical price.
- Order-time price.

Explain why calculating historical order totals from the current product price is incorrect.

---

## Exercise: Order Status Model

An order can transition through:

```text
pending
processing
completed
cancelled
```

### Tasks

Determine whether status should be:

- Free-form text.
- PostgreSQL enum.
- Lookup table.
- Application-level constants plus a database `CHECK`.

Compare the approaches.

Then define valid transitions.

---

## Exercise: Database Constraints

For the commerce model, identify business rules that should be enforced by PostgreSQL.

Examples:

```text
quantity > 0
price >= 0
stock >= 0
order belongs to customer
```

### Tasks

Create a constraint inventory covering:

- `NOT NULL`.
- `CHECK`.
- `UNIQUE`.
- Primary keys.
- Foreign keys.
- Partial unique indexes.

For every constraint, explain why application-only validation is insufficient.

---

## Exercise: Unique Customer Email

The application requires one account per email address.

### Tasks

Design the uniqueness rule.

Consider:

```text
Alice@example.com
alice@example.com
```

Determine whether they should represent the same identity.

Compare:

```sql
UNIQUE (email)
```

with:

```sql
CREATE UNIQUE INDEX ...
ON customers (lower(email));
```

Discuss normalization and case-sensitivity.

---

## Exercise: Soft Delete

Customers may be deactivated without immediately removing their records.

Design:

```text
deleted_at
```

### Tasks

Determine how soft deletion affects:

- Unique constraints.
- Foreign keys.
- Queries.
- Reporting.
- Authentication.
- GDPR/data retention requirements.
- Indexes.

Design a partial unique index if the business rule is:

```text
Only active customers must have unique email addresses.
```

---

## Exercise: Multi-Column Uniqueness

The system allows one default address per customer.

### Tasks

Design a constraint ensuring:

```text
customer_id = 42
default_address = true
```

can occur only once.

Use a PostgreSQL partial unique index.

Then explain why:

```text
application checks existing default
→ inserts new default
```

is not concurrency-safe.

---

## Exercise: Address Modeling

A customer can have:

- Billing address.
- Shipping address.
- Multiple saved addresses.

### Tasks

Compare:

```text
addresses embedded into customers
```

with:

```text
customer_addresses
```

Determine which attributes belong in the address entity.

Consider:

```text
line_1
line_2
city
state
postal_code
country_code
```

Explain why address modeling should consider historical orders and immutable snapshots.

---

## Exercise: Historical Address Snapshot

A customer changes their address after placing an order.

The completed order must continue showing the address used during shipment.

### Tasks

Design a strategy using either:

```text
order_shipping_addresses
```

or an immutable snapshot stored with the order.

Explain why referencing only:

```text
customers.address_id
```

is insufficient.

---

## Exercise: Payment Model

An order can have multiple payment attempts:

```text
attempt 1 → failed
attempt 2 → failed
attempt 3 → paid
```

### Tasks

Design:

```text
payments
```

Determine:

- Primary key.
- Order foreign key.
- Payment status.
- Amount.
- Provider reference.
- Idempotency key.
- Created timestamp.

Design constraints preventing duplicate successful payments.

---

## Exercise: Idempotency Key

A client retries:

```http
POST /payments
Idempotency-Key: abc123
```

### Tasks

Design the database schema that guarantees the same logical request cannot create multiple payment records.

Consider:

```sql
UNIQUE (idempotency_key)
```

Then determine how the API should behave when:

- The same key is reused with the same request.
- The same key is reused with different parameters.
- The first request succeeds but the response is lost.
- Two requests arrive concurrently.

---

## Exercise: Inventory Design

Design inventory for:

```text
product
stock
reserved_stock
available_stock
```

### Tasks

Determine whether to store:

```text
available_stock
```

directly or derive it from:

```text
stock - reserved_stock
```

Explain the trade-offs.

Identify invariants such as:

```text
reserved_stock >= 0
reserved_stock <= stock
```

Determine which should be enforced by the database.

---

## Exercise: Inventory Ledger

Instead of storing only the current stock, design:

```text
inventory_transactions
```

with events such as:

```text
purchase
reservation
release
restock
adjustment
```

### Tasks

Design the ledger.

Determine:

- Transaction type.
- Quantity delta.
- Reference entity.
- Actor.
- Timestamp.
- Idempotency key.

Explain the difference between:

```text
current-state table
```

and:

```text
append-only ledger
```

Discuss when both should exist.

---

## Exercise: Auditability

A financial system requires knowing:

```text
who changed what
when
from which state
to which state
```

### Tasks

Design an audit model.

Determine whether audit information should be stored:

- In the same transactional database.
- In separate audit tables.
- In application logs.
- In an external event stream.

Explain why auditability and observability are related but different requirements.

---

## Exercise: Normalization

Normalize the following conceptual data:

```text
order_id
customer_name
customer_email
product_1
product_1_price
product_2
product_2_price
shipping_city
shipping_country
```

### Tasks

Identify:

- Repeating groups.
- Duplicate data.
- Update anomalies.
- Insert anomalies.
- Delete anomalies.

Redesign the model into normalized relational tables.

---

## Exercise: Denormalization

A dashboard frequently displays:

```text
customer_id
customer_name
order_count
lifetime_value
last_order_at
```

Calculating these values requires expensive aggregation over millions of orders.

### Tasks

Evaluate:

- Query-time aggregation.
- Materialized views.
- Cached values.
- Denormalized customer counters.
- Analytical database.

Choose an approach based on:

- Freshness requirements.
- Write volume.
- Read volume.
- Consistency requirements.

---

## Exercise: Normalization vs Performance

Consider:

```text
orders
customers
addresses
order_items
products
```

A query requires five joins for every API request.

### Tasks

Determine whether the correct response is automatically to denormalize.

Analyze:

- Indexes.
- Query frequency.
- Result size.
- Join cardinality.
- Cacheability.
- Read replicas.
- Materialized views.
- API-specific read models.

Explain why normalization and performance are not inherently opposites.

---

## Exercise: Foreign Key Strategy

Design foreign keys for:

```text
orders.customer_id
order_items.order_id
order_items.product_id
payments.order_id
```

### Tasks

For each relationship determine:

- Required or nullable?
- `ON DELETE CASCADE`?
- `ON DELETE RESTRICT`?
- `ON DELETE SET NULL`?
- Should parent deletion be allowed at all?

Explain how deletion semantics should follow business ownership rather than convenience.

---

## Exercise: Circular Dependencies

Consider:

```text
employees.manager_id → employees.id
departments.manager_id → employees.id
employees.department_id → departments.id
```

### Tasks

Identify the circular dependency.

Design an insertion strategy.

Consider:

- Nullable foreign keys.
- Deferred constraints.
- Multi-step transactions.
- Schema redesign.

Explain why circular relationships increase migration and lifecycle complexity.

---

## Exercise: Self-Referential Hierarchy

Design:

```text
categories
```

where:

```text
Electronics
 ├── Phones
 ├── Laptops
 └── Accessories
```

### Tasks

Design:

```text
parent_id
```

and the foreign key.

Determine how to query:

- Direct children.
- Parent.
- All descendants.
- All ancestors.

Discuss when adjacency lists are sufficient and when alternatives such as materialized paths or closure tables become useful.

---

## Exercise: Organizational Hierarchy

Design:

```text
company
departments
teams
employees
```

Requirements:

- An employee belongs to one team.
- A team belongs to one department.
- A department belongs to one company.
- Employees may manage other employees.

### Tasks

Produce an ER model.

Identify all foreign keys.

Determine which indexes are required for common queries.

---

## Exercise: Tenant Isolation

A SaaS platform supports multiple organizations.

Tables include:

```text
customers
orders
projects
invoices
```

### Tasks

Choose between:

- Shared database/shared schema.
- Schema per tenant.
- Database per tenant.
- Hybrid tenancy.

Evaluate:

- Isolation.
- Operational complexity.
- Cost.
- Scaling.
- Backup/restore.
- Compliance.
- Cross-tenant reporting.

---

## Exercise: Tenant-Aware Schema

Assume shared-schema multi-tenancy.

Design:

```text
orders(
    id,
    tenant_id,
    customer_id,
    ...
)
```

### Tasks

Determine which tables require:

```text
tenant_id
```

Design indexes around tenant-aware access patterns.

Consider:

```text
(tenant_id, created_at)
(tenant_id, customer_id)
```

Explain why a globally indexed column may not be sufficient for tenant-scoped workloads.

---

## Exercise: Cross-Tenant Foreign Keys

A shared-schema system contains:

```text
customers
orders
```

Both have:

```text
tenant_id
```

### Tasks

Design a foreign-key strategy that prevents:

```text
tenant A order
→ tenant B customer
```

from being referenced.

Consider composite keys such as:

```text
(tenant_id, customer_id)
```

and explain the trade-offs.

---

## Exercise: Row-Level Security

Design PostgreSQL RLS for:

```text
orders
```

so that a tenant can access only its own rows.

### Tasks

Define:

```text
tenant context
```

and:

```text
USING
```

policy behavior.

Consider connection pooling and transaction-scoped context.

Explain why RLS should complement, not replace, application authorization.

---

## Exercise: Polymorphic Relationships

Suppose comments can belong to:

```text
orders
products
customers
```

A developer proposes:

```text
commentable_type
commentable_id
```

### Tasks

Evaluate this design.

Identify the referential-integrity problem.

Compare it with:

```text
order_comments
product_comments
customer_comments
```

or another normalized approach.

Determine when polymorphic associations are acceptable.

---

## Exercise: Event Storage

A system stores:

```text
OrderCreated
OrderCompleted
OrderCancelled
PaymentCompleted
```

### Tasks

Design an event table containing:

```text
event_id
event_type
aggregate_id
aggregate_version
payload
created_at
```

Determine:

- Which fields need indexes.
- Which fields require uniqueness.
- Whether payload should be JSONB.
- How to support idempotent consumers.

Explain the difference between an event log and a transactional outbox.

---

## Exercise: JSONB vs Relational Columns

A product has configurable metadata:

```json
{
  "color": "black",
  "screen_size": 15.6,
  "ram_gb": 32
}
```

### Tasks

Determine which fields belong in:

```text
normal columns
```

and which can reasonably belong in:

```text
JSONB
```

Consider:

- Query frequency.
- Validation.
- Constraints.
- Indexing.
- Schema evolution.
- Reporting.
- API flexibility.

Explain why JSONB should not become a substitute for relational modeling.

---

## Exercise: Searchable JSONB

Suppose APIs frequently filter:

```text
metadata->>'color' = 'black'
```

### Tasks

Design an appropriate index.

Compare:

```sql
CREATE INDEX ...
ON products ((metadata->>'color'));
```

with:

```sql
CREATE INDEX ...
ON products USING GIN (metadata);
```

Determine when each approach is appropriate.

---

## Exercise: Time-Series Data

A service stores:

```text
device_id
timestamp
temperature
humidity
```

with millions of measurements per day.

### Tasks

Design the table.

Determine:

- Primary key.
- Indexes.
- Partition key.
- Retention strategy.
- Archival strategy.

Explain how time-based partitioning can simplify lifecycle management.

---

## Exercise: Large Table Design

A table is expected to reach:

```text
5 billion rows
```

### Tasks

Before implementing it, evaluate:

- Row width.
- Write rate.
- Query patterns.
- Retention.
- Partitioning.
- Index size.
- Vacuum behavior.
- Replication.
- Backup duration.
- Archival.

Determine whether a single PostgreSQL table is still appropriate.

---

## Exercise: Partitioning Decision

An events table receives:

```text
100 million rows/month
```

Queries usually filter:

```text
created_at >= ...
```

### Tasks

Design a partitioning strategy.

Compare:

- Monthly range partitions.
- Weekly range partitions.
- Hash partitions.
- No partitioning.

Explain how partition count affects:

- Planning.
- Maintenance.
- Vacuum.
- Index management.
- Operational complexity.

---

## Exercise: Index Design from Access Patterns

Given:

```sql
SELECT id, status, created_at
FROM orders
WHERE customer_id = $1
  AND status = 'pending'
ORDER BY created_at DESC
LIMIT 50;
```

### Tasks

Design an index.

Evaluate:

```text
(customer_id, status, created_at DESC)
```

against alternative column orders.

Explain how equality, range, and ordering requirements influence composite-index design.

---

## Exercise: Index Coverage

The API query is:

```sql
SELECT id, status, created_at, total_amount
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC
LIMIT 50;
```

### Tasks

Evaluate whether:

```text
INCLUDE (status, total_amount)
```

would be beneficial.

Discuss:

- Index-only scans.
- Visibility map.
- Index size.
- Write amplification.
- Whether the query is frequent enough to justify the wider index.

---

## Exercise: Partial Index

Only pending orders are frequently processed.

### Tasks

Design:

```sql
CREATE INDEX ...
ON orders (...)
WHERE status = 'pending';
```

Determine:

- Why this index can be smaller.
- When PostgreSQL can use it.
- How status transitions affect the index.
- What happens as the percentage of pending rows grows.

---

## Exercise: Unique Partial Index

Business rule:

```text
Only one active subscription per customer.
```

### Tasks

Design a unique partial index.

Then test the design conceptually against concurrent requests.

Explain how this differs from application-level duplicate checking.

---

## Exercise: Soft-Delete Index Design

Most application queries use:

```text
deleted_at IS NULL
```

### Tasks

Design an index strategy for active records.

Compare:

```text
full index
```

with:

```text
partial index WHERE deleted_at IS NULL
```

Discuss the impact on writes and index size.

---

## Exercise: Query Access Pattern Review

Given these queries:

```sql
SELECT *
FROM orders
WHERE customer_id = $1;

SELECT *
FROM orders
WHERE status = $1;

SELECT *
FROM orders
WHERE created_at >= $1
ORDER BY created_at DESC;

SELECT *
FROM orders
WHERE customer_id = $1
  AND status = $2
ORDER BY created_at DESC;
```

### Tasks

Design the minimum useful index set.

Avoid creating one index per query without considering overlap.

Explain:

- Composite indexes.
- Redundant indexes.
- Write amplification.
- Index maintenance.

---

## Exercise: Pagination Design

An API supports:

```text
GET /orders?page=100000
```

### Tasks

Compare:

```sql
LIMIT 50 OFFSET 500000;
```

with keyset pagination:

```sql
WHERE created_at < $cursor
ORDER BY created_at DESC
LIMIT 50;
```

Determine which indexes are needed.

Explain how keyset pagination affects large-scale API performance.

---

## Exercise: Primary Key Design

Compare:

```text
BIGINT GENERATED ALWAYS AS IDENTITY
```

with:

```text
UUID
```

and:

```text
UUIDv7
```

### Tasks

Evaluate:

- Index locality.
- Storage size.
- Distributed ID generation.
- Enumeration resistance.
- Debugging.
- API exposure.
- Sharding.
- Insert performance.

Choose a primary-key strategy for a high-volume public API.

---

## Exercise: Natural Key vs Surrogate Key

A country table contains:

```text
country_code
country_name
```

### Tasks

Determine whether:

```text
country_code
```

should be the primary key.

Compare natural keys with surrogate IDs.

Then apply the same reasoning to:

```text
email
SKU
external_payment_id
```

Explain why different entities can justify different key strategies.

---

## Exercise: External IDs

An order is represented internally by:

```text
id = 123456
```

but external systems use:

```text
ORD-2026-9F2A...
```

### Tasks

Determine whether the external identifier should replace the internal primary key.

Design:

```text
internal_id
external_id
```

with appropriate uniqueness.

Explain why internal identifiers and public identifiers often have different requirements.

---

## Exercise: Audit Columns

Determine which tables should contain:

```text
created_at
updated_at
created_by
updated_by
```

### Tasks

Identify where each field is useful.

Determine whether `updated_by` can always be trusted.

Consider:

- Background jobs.
- Automated migrations.
- System actors.
- Service accounts.
- Bulk updates.

---

## Exercise: Temporal Modeling

A customer's membership changes:

```text
free
→ premium
→ enterprise
```

The system must answer:

```text
Which plan was active on 2026-05-01?
```

### Tasks

Design a historical model.

Consider:

```text
effective_from
effective_to
```

Determine how to prevent overlapping intervals.

Discuss PostgreSQL range types and exclusion constraints as a possible advanced solution.

---

## Exercise: Currency Modeling

An order stores:

```text
amount
currency
```

### Tasks

Determine whether monetary values should use:

```text
numeric
```

or:

```text
double precision
```

Design:

```text
amount numeric(...)
currency char(3)
```

Explain:

- Precision.
- Scale.
- Currency-specific decimal rules.
- Rounding.
- API serialization.

---

## Exercise: Time Zone Modeling

An event occurs at:

```text
2026-09-05 14:00
```

### Tasks

Determine whether the database should use:

```text
timestamp
```

or:

```text
timestamptz
```

for an event occurring at a real-world instant.

Explain:

- UTC.
- Client time zones.
- Display-time conversion.
- Day boundaries.
- Recurring schedules.

---

## Exercise: Status and State History

An order currently stores:

```text
status = completed
```

but the business requires an audit trail.

### Tasks

Compare:

```text
orders.status
```

with:

```text
order_status_history
```

Determine whether both should exist.

Design the history table.

Explain how the current-state table and append-only history serve different query patterns.

---

## Exercise: Database-per-Service

A microservice architecture contains:

```text
Order Service
Payment Service
Inventory Service
```

### Tasks

Design database ownership.

Determine whether:

```text
orders
payments
inventory
```

should live in one database or separate databases.

Analyze:

- Transaction boundaries.
- Foreign keys.
- Service autonomy.
- Reporting.
- Distributed transactions.
- Events.
- Data duplication.

Explain why database-per-service is an architectural boundary rather than merely a deployment choice.

---

## Exercise: Shared Database Anti-Pattern

Three services directly update:

```text
orders
```

### Tasks

Identify the risks.

Consider:

- Coupling.
- Schema migrations.
- Ownership.
- Authorization.
- Deployment independence.
- Concurrency.
- Hidden dependencies.

Design a migration toward clear ownership.

---

## Exercise: Read Model Design

The frontend requires:

```text
order_id
customer_name
item_count
total_amount
payment_status
shipment_status
```

Data comes from several bounded contexts.

### Tasks

Compare:

- Runtime joins across service databases.
- API composition.
- Materialized view.
- Denormalized read model.
- Event-driven projection.

Choose an architecture based on:

- Freshness.
- Availability.
- Query latency.
- Ownership.

---

## Exercise: CQRS Data Model

Design separate:

```text
write model
read model
```

for an order system.

### Tasks

Determine:

- Which data belongs in the transactional model.
- Which data belongs in the read projection.
- How events update the projection.
- How projections are rebuilt.
- How stale projections are detected.

Explain why CQRS increases operational complexity and should be justified by workload requirements.

---

## Exercise: Outbox Table Design

A transaction creates an order and must publish:

```text
OrderCreated
```

### Tasks

Design:

```text
outbox_events
```

with fields such as:

```text
id
aggregate_type
aggregate_id
event_type
payload
created_at
published_at
attempt_count
```

Determine which fields require indexes.

Explain how the outbox prevents the database/event publication dual-write problem.

---

## Exercise: Schema for Idempotent Consumers

A Kafka consumer processes:

```text
event_id
```

### Tasks

Design:

```text
processed_events
```

or an equivalent mechanism.

Determine how to guarantee that the same event does not produce the same database effect twice.

Consider transaction boundaries between:

```text
database update
```

and:

```text
Kafka acknowledgment
```

---

## Exercise: Data Retention

The system stores:

```text
application_events
audit_logs
orders
payments
```

### Tasks

Define different retention policies.

Determine which data can be:

- Deleted.
- Archived.
- Partitioned.
- Moved to object storage.
- Retained indefinitely.

Consider:

- Legal requirements.
- Business requirements.
- Storage cost.
- Query requirements.
- Backups.

---

## Exercise: Large Delete Strategy

A table contains:

```text
2 billion events
```

You need to remove data older than five years.

### Tasks

Compare:

```sql
DELETE FROM events
WHERE created_at < ...;
```

with:

- Batched deletes.
- Partition dropping.
- Archival.
- Background cleanup.

Analyze:

- WAL.
- Locking.
- Bloat.
- Vacuum.
- Replica lag.
- Transaction duration.

---

## Exercise: Migration Design

Add:

```text
customer_tier
```

to a table containing:

```text
500 million customers
```

### Tasks

Design an expand-and-contract migration.

Include:

```text
schema change
→ application compatibility
→ backfill
→ validation
→ enforcement
```

Determine how to prevent long-running locks and excessive database load.

---

## Exercise: Integer to Bigint Migration

A high-volume table uses:

```text
id integer
```

and is approaching the maximum range.

### Tasks

Identify every dependency that may need modification:

- Foreign keys.
- ORM fields.
- API serialization.
- Kafka schemas.
- Celery payloads.
- External integrations.
- Indexes.
- Reporting systems.

Design a safe migration strategy.

---

## Exercise: Database Design Under High Write Load

A service receives:

```text
100,000 writes/sec
```

### Tasks

Determine whether PostgreSQL can handle the workload as designed.

Evaluate:

- Index count.
- Row width.
- WAL.
- Connection pooling.
- Batch writes.
- Partitioning.
- Replication.
- Hot rows.
- Sharding.

Explain why increasing hardware should not be the first database-design decision.

---

## Exercise: Read-Heavy Design

An API receives:

```text
100 reads
1 write
```

for a particular resource.

### Tasks

Design a read-heavy architecture.

Consider:

```text
PostgreSQL primary
→ read replicas
→ Redis
→ materialized/read model
```

Determine which consistency guarantees each layer provides.

---

## Exercise: Write-Heavy Design

A system receives:

```text
10,000 writes/sec
```

to an append-heavy event table.

### Tasks

Design:

- Table structure.
- Index strategy.
- Partitioning.
- Batch ingestion.
- Retention.
- Archival.
- Replication.

Explain which indexes should be avoided if they do not support meaningful access patterns.

---

## Exercise: OLTP vs OLAP Schema

An order database also serves:

```text
monthly revenue
revenue by region
top products
customer lifetime value
```

### Tasks

Determine whether these queries should run directly against OLTP tables.

Design an analytical model using:

```text
fact_orders
fact_order_items
dim_customer
dim_product
dim_date
```

Explain the difference between operational schema design and analytical schema design.

---

## Exercise: Star Schema

Design a star schema for:

```text
sales analytics
```

### Tasks

Define:

```text
fact_sales
dim_customer
dim_product
dim_date
dim_region
```

Determine the grain of `fact_sales`.

Explain why defining fact-table grain before adding dimensions is essential.

---

## Exercise: Reporting Isolation

A reporting query scans:

```text
1 billion order rows
```

while production APIs require low latency.

### Tasks

Design an architecture using:

- Read replica.
- Data warehouse.
- CDC.
- Batch ETL.
- Streaming events.

Determine which approach is appropriate for:

```text
seconds-level freshness
```

versus:

```text
daily reporting
```

---

## Exercise: Database Security Model

Design database roles for:

```text
application runtime
migration worker
read-only reporting
administration
```

### Tasks

Determine:

- Which roles require `LOGIN`.
- Which roles should own objects.
- Which privileges each role needs.
- Whether runtime should have DDL privileges.
- How credentials should be rotated.

Explain why application runtime should not normally connect as a superuser or object owner.

---

## Exercise: Sensitive Data

A customer table contains:

```text
name
email
phone
address
government_id
```

### Tasks

Classify the fields by sensitivity.

Determine:

- Which columns should be exposed through APIs.
- Which should be encrypted or otherwise protected.
- Which should be indexed.
- Which should be logged.
- Which should be retained.

Explain why database design and data-security design cannot be treated independently.

---

## Exercise: PII Search

The system must find a customer by email.

### Tasks

Design the lookup strategy while minimizing unnecessary exposure of sensitive data.

Consider:

- Normalized email.
- Unique indexes.
- Hash-based lookup.
- Encryption.
- Key management.
- Searchability.

Explain the trade-off between confidentiality and queryability.

---

## Exercise: Backup and Recovery Design

A critical PostgreSQL database contains:

```text
orders
payments
customers
```

### Tasks

Define:

```text
RPO
RTO
```

Design:

- Automated backups.
- WAL archiving.
- Point-in-time recovery.
- Cross-region copies.
- Restore testing.

Explain why a replica is not a replacement for backups.

---

## Exercise: High Availability Schema Considerations

A database uses:

```text
primary
+
synchronous standby
+
asynchronous read replicas
```

### Tasks

Determine how schema design affects failover.

Consider:

- Long-running transactions.
- Large migrations.
- Replication lag.
- DDL.
- Index creation.
- Failover.
- Read-after-write behavior.

Explain why operationally safe schema design must account for replication.

---

## Exercise: Connection Pool Capacity

Suppose:

```text
20 Kubernetes pods
15 database connections/pod
```

and:

```text
10 Celery workers
5 connections/worker
```

### Tasks

Calculate the potential connection count.

Determine whether PostgreSQL can safely support it.

Design separate connection budgets for:

- API traffic.
- Background workers.
- Administrative operations.
- Migrations.

Explain why connection capacity is part of database design.

---

## Exercise: ORM Database Design

Implement the commerce model using Django.

### Tasks

Design Django models for:

```text
Customer
Product
Order
OrderItem
Payment
Address
Inventory
```

Then verify that the generated schema includes:

- Appropriate primary keys.
- Foreign keys.
- Unique constraints.
- Check constraints.
- Indexes.

Explain which database behaviors should remain explicit rather than relying on ORM defaults.

---

## Exercise: FastAPI and SQLAlchemy Model Design

Design SQLAlchemy models for the same commerce system.

### Tasks

Define:

- Relationships.
- Foreign keys.
- Constraints.
- Indexes.
- Cascades.

Determine which behavior should be enforced by PostgreSQL rather than only through SQLAlchemy.

---

## Exercise: API-to-Database Contract

An API accepts:

```json
{
  "customer_id": 42,
  "items": [
    {
      "product_id": 100,
      "quantity": 2
    }
  ]
}
```

### Tasks

Determine which validations belong in:

```text
API layer
```

and which belong in:

```text
database layer
```

Examples:

```text
quantity > 0
product exists
customer exists
stock available
duplicate order
```

Explain why API validation and database constraints have different responsibilities.

---

## Exercise: Concurrency-Aware Schema

The inventory schema must support:

```text
100 concurrent reservation requests
```

### Tasks

Determine which database structures support safe concurrency.

Consider:

- `CHECK (stock >= 0)`.
- Atomic updates.
- Row locks.
- Version columns.
- Reservation table.
- Unique constraints.

Explain which constraints guarantee correctness and which mechanisms control contention.

---

## Exercise: Hot-Row Design

A global table contains:

```text
system_stats
```

with:

```text
request_count
```

updated by every API request.

### Tasks

Determine why this design may become a contention bottleneck.

Redesign using:

- Sharded counters.
- Per-instance counters.
- Redis.
- Periodic aggregation.

Determine which design preserves durable correctness requirements.

---

## Exercise: Database Design for Idempotency

A payment API can receive the same logical request multiple times.

### Tasks

Design:

```text
idempotency_key
request_hash
status
response_payload
created_at
```

Determine which fields require constraints and indexes.

Design behavior for:

```text
same key + same request
same key + different request
concurrent same-key requests
expired idempotency records
```

---

## Exercise: Queue Table Design

Design a PostgreSQL-backed work queue.

Requirements:

- Multiple workers.
- No duplicate claims.
- Retry failed jobs.
- Recover abandoned jobs.

### Tasks

Design:

```text
jobs
```

with fields such as:

```text
status
attempts
available_at
locked_at
lease_expires_at
worker_id
```

Use:

```sql
FOR UPDATE SKIP LOCKED
```

where appropriate.

Explain why queue schema design is also concurrency design.

---

## Exercise: Database Design Review

Review the following conceptual design:

```text
users
orders
products
payments
```

Every table contains:

```text
id
name
status
data JSONB
created_at
```

There are no foreign keys, no indexes other than primary keys, and no constraints.

### Tasks

Identify at least 15 design problems.

Consider:

- Relationships.
- Constraints.
- Data types.
- JSONB usage.
- Indexes.
- Uniqueness.
- Referential integrity.
- Security.
- Auditing.
- Concurrency.
- Query patterns.
- Lifecycle management.

---

## Exercise: Anti-Pattern Review

Evaluate these statements:

### Statement A

> "We don't need foreign keys because Django validates relationships."

### Statement B

> "We can add indexes later when queries become slow."

### Statement C

> "Every table should have `id`, even if a natural key is already guaranteed unique."

### Statement D

> "JSONB is better because it lets us avoid migrations."

### Statement E

> "Soft deletion solves data retention."

### Statement F

> "Read replicas solve database scaling."

### Statement G

> "Database constraints slow development, so validation should stay in Python."

### Tasks

For each statement:

1. Identify what is correct.
2. Identify what is dangerous.
3. Explain the production consequence.
4. Provide a better engineering principle.

---

## Exercise: Production Schema Review

Perform a schema review for a production service.

### Review Categories

| Category | Questions |
|---|---|
| Data model | Is row grain clear? |
| Relationships | Are relationships explicit? |
| Integrity | Are invariants enforced? |
| Keys | Are primary and alternate keys appropriate? |
| Indexes | Do indexes match access patterns? |
| Queries | Can critical queries scale? |
| Concurrency | Can concurrent writes violate invariants? |
| Security | Is sensitive data protected? |
| Tenancy | Is tenant isolation enforced? |
| Migrations | Can the schema evolve safely? |
| Replication | Will writes generate excessive WAL? |
| Backup | Can the data be recovered? |
| Observability | Can database behavior be diagnosed? |
| Cost | Are storage and compute requirements reasonable? |

### Tasks

Apply this review to the commerce schema.

Record:

```text
risk
impact
likelihood
mitigation
```

for each significant issue.

---

## Exercise: Database Design Interview Problem

Design a database for:

```text
Food delivery platform
```

Requirements:

- Customers place orders.
- Restaurants publish menus.
- Restaurants have multiple branches.
- Drivers deliver orders.
- Orders contain multiple menu items.
- Menu prices change.
- Restaurants can temporarily disable menu items.
- Orders have payment attempts.
- Drivers have delivery assignments.
- Customers can save addresses.
- Orders must preserve historical pricing and delivery address.
- Multiple services may process the same order.
- The system must support high read traffic.

### Tasks

Design:

- Entities.
- Relationships.
- Primary keys.
- Foreign keys.
- Constraints.
- Indexes.
- Status models.
- Historical data.
- Idempotency.
- Audit history.
- Tenant/service ownership.
- Read models.
- Partitioning candidates.

Produce an ER diagram.

---

## Exercise: Database Design for Booking

Design a hotel reservation system.

Requirements:

- Hotels have rooms.
- Rooms have room types.
- Customers can create reservations.
- A room cannot be double-booked for overlapping dates.
- Reservations can be cancelled.
- Prices vary by date.
- Payment attempts are tracked.
- Booking requests can be retried.

### Tasks

Design:

```text
hotels
room_types
rooms
customers
reservations
reservation_prices
payments
```

Determine how to enforce:

```text
no overlapping reservation
```

using PostgreSQL capabilities.

Consider range types and exclusion constraints.

---

## Exercise: Database Design for Inventory Marketplace

Design an inventory marketplace where:

```text
10,000 sellers
100 million products
1 billion inventory events
```

### Tasks

Determine:

- Product ownership.
- Inventory ownership.
- SKU uniqueness.
- Seller-specific pricing.
- Inventory event schema.
- Partitioning.
- Indexes.
- Archival.
- Read models.
- Search integration.
- Concurrency strategy.

Explain which data belongs in PostgreSQL and which workloads may require specialized systems.

---

## Exercise: Database Design for Multi-Tenant SaaS

Design a SaaS database for:

```text
100,000 tenants
```

with:

```text
users
projects
tasks
comments
attachments
audit_logs
```

Requirements:

- Strong tenant isolation.
- Tenant-specific uniqueness.
- Tenant-level deletion.
- Auditability.
- Search.
- Reporting.
- Large tenants may become noisy neighbors.

### Tasks

Evaluate:

```text
shared schema
```

versus:

```text
tenant sharding
```

Design the migration path from shared storage to tenant-aware placement.

---

## Exercise: Database Design Under Growth

A service starts with:

```text
1 million users
```

and is expected to reach:

```text
500 million users
```

### Tasks

Identify schema decisions that become difficult to change later.

Evaluate:

- Primary keys.
- Identifier width.
- Index strategy.
- Partitioning.
- Data retention.
- Archival.
- Tenant boundaries.
- Service ownership.
- Event schemas.
- API identifiers.
- Audit data.

Explain which decisions should be made early and which should remain simple until justified by workload evidence.

---

## Exercise: Senior Design Challenge

Design a production database architecture for a commerce platform with:

```text
50 million customers
500 million orders
2 billion order items
10 billion events
```

Traffic:

```text
20,000 API requests/sec
5,000 writes/sec
```

Requirements:

- High availability.
- Read scaling.
- Strong transactional correctness for orders and payments.
- Inventory concurrency.
- Historical auditing.
- Asynchronous event processing.
- Analytics.
- Multi-region disaster recovery.
- Safe schema migrations.

### Tasks

Produce a complete design covering:

1. Core relational model.
2. Row grain.
3. Primary and foreign keys.
4. Constraints.
5. Index strategy.
6. Partitioning.
7. Read replicas.
8. Connection pooling.
9. Redis usage.
10. Kafka usage.
11. Celery usage.
12. OLTP/OLAP separation.
13. Outbox pattern.
14. Idempotency.
15. Concurrency control.
16. Multi-tenant considerations.
17. Security.
18. Backup and recovery.
19. Migration strategy.
20. Monitoring.
21. Capacity planning.
22. Cost controls.

The objective is not to design the most complex architecture. It is to justify each architectural decision against the workload and business requirements.

---

## Design Review Checklist

Before considering a relational design production-ready, verify:

### Modeling

- [ ] Every table has a clearly defined row grain.
- [ ] Entities and relationships are explicit.
- [ ] Many-to-many relationships use appropriate associative structures.
- [ ] Historical facts are preserved where required.
- [ ] Derived data is intentionally identified.

### Integrity

- [ ] Primary keys are defined.
- [ ] Foreign keys are defined.
- [ ] Required fields use `NOT NULL`.
- [ ] Numeric invariants use `CHECK`.
- [ ] Uniqueness is enforced in the database.
- [ ] Delete behavior matches business ownership.
- [ ] Cross-tenant relationships cannot violate tenant boundaries.

### Performance

- [ ] Critical queries have been identified.
- [ ] Indexes match real access patterns.
- [ ] Composite index order is deliberate.
- [ ] Redundant indexes are avoided.
- [ ] Pagination strategy is appropriate.
- [ ] Large result sets are controlled.
- [ ] OLTP and OLAP workloads are isolated when necessary.

### Concurrency

- [ ] Shared mutable state is identified.
- [ ] Business invariants survive concurrent requests.
- [ ] Atomic updates are used where appropriate.
- [ ] Locking strategy is intentional.
- [ ] Hot rows are identified.
- [ ] Idempotency is designed for retried operations.
- [ ] Unique constraints protect duplicate operations.

### Security

- [ ] Sensitive fields are classified.
- [ ] Database roles follow least privilege.
- [ ] Application runtime does not use excessive privileges.
- [ ] Tenant isolation is enforced.
- [ ] Audit requirements are addressed.
- [ ] Secrets are not stored in source code or logs.

### Scalability

- [ ] Expected data volume is known.
- [ ] Expected write rate is known.
- [ ] Expected read rate is known.
- [ ] Connection capacity is understood.
- [ ] Partitioning is considered where justified.
- [ ] Archival and retention are defined.
- [ ] Hotspot resources are identified.

### Operations

- [ ] Schema migrations can be deployed safely.
- [ ] Backups exist.
- [ ] Point-in-time recovery is available where required.
- [ ] Restore procedures are tested.
- [ ] Replication behavior is understood.
- [ ] Database metrics and logs are observable.
- [ ] Capacity thresholds are defined.

---

## Key Takeaways

- **Database design starts with business invariants and row grain:** tables, relationships, keys, and constraints should model what must remain true rather than merely mirror application classes.
- **PostgreSQL should enforce critical integrity:** foreign keys, `CHECK` constraints, unique constraints, and carefully designed indexes protect correctness across concurrent requests and multiple application paths.
- **Schema design must follow access patterns:** indexes, partitioning, denormalization, pagination, and read models should be justified by real workload characteristics rather than generic rules.
- **Production database design includes operations:** migrations, concurrency, replication, backups, security, retention, connection capacity, and observability are part of the schema architecture.
- **Senior database design balances simplicity with future pressure:** design stable boundaries and invariants early, while introducing partitioning, sharding, CQRS, specialized stores, or denormalization only when workload requirements justify their complexity.