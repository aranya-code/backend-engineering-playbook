# 03 - Tables, Items and Attributes

## Overview

Every database requires a way to organize data.

In relational databases, data is organized into **tables**, where every row follows a predefined schema consisting of fixed columns and data types.

DynamoDB also stores data in tables, but the similarity largely ends there.

Unlike relational databases, DynamoDB tables are **schema-flexible** containers designed for distributed storage. Each item within a table can have a completely different structure while still belonging to the same logical collection.

Understanding how tables, items, and attributes work is fundamental because nearly every DynamoDB design decision—partitioning, indexing, querying, and scaling—builds upon these concepts.

---

# Understanding the Data Hierarchy

DynamoDB organizes data using three building blocks.

```text
Table
   │
   ├── Item
   │      ├── Attribute
   │      ├── Attribute
   │      └── Attribute
   │
   ├── Item
   │      ├── Attribute
   │      ├── Attribute
   │      └── Attribute
   │
   └── Item
          ├── Attribute
          ├── Attribute
          └── Attribute
```

Everything stored inside DynamoDB belongs to this hierarchy.

- A **Table** stores related entities.
- An **Item** represents a single entity.
- **Attributes** describe that entity.

Unlike SQL databases, DynamoDB does **not** require every item to have identical attributes.

---

# DynamoDB Tables

A **Table** is the highest-level logical container in DynamoDB.

Examples include:

- Users
- Orders
- Products
- Employees
- Devices
- Sessions

A table represents a collection of related information.

Unlike traditional databases, creating a DynamoDB table does **not** define every column that will exist in the future.

The only mandatory definition during table creation is the **Primary Key**.

Everything else is determined dynamically as data is inserted.

This design allows applications to evolve without requiring schema migrations.

---

# Why Does DynamoDB Use Flexible Schemas?

One of DynamoDB's design goals is to support applications that evolve rapidly.

Imagine an e-commerce application.

Initially, products contain:

```json
{
    "ProductId": 1001,
    "Name": "Laptop",
    "Price": 900
}
```

Six months later, the business decides to introduce product ratings.

In a relational database, this often requires:

- Schema migration
- ALTER TABLE operations
- Deployment planning
- Downtime considerations

In DynamoDB, new items simply include another attribute.

```json
{
    "ProductId": 1002,
    "Name": "Laptop",
    "Price": 900,
    "Rating": 4.8
}
```

Older items continue working without modification.

This flexibility makes DynamoDB particularly attractive for agile development where requirements frequently change.

---

# Items

An **Item** represents a single object stored within a table.

If a Users table exists:

```text
Users
```

An individual user becomes one item.

```json
{
    "UserId": "U1001",
    "Name": "Alice",
    "Country": "USA"
}
```

Similarly,

An Orders table contains order items.

```json
{
    "OrderId": "ORD001",
    "Amount": 250,
    "Status": "Delivered"
}
```

Each item is completely independent.

Internally, DynamoDB treats every item as a self-contained document identified by its primary key.

---

# Attributes

Attributes are individual pieces of information stored within an item.

For example,

```json
{
    "UserId": "U1001",
    "Name": "Alice",
    "Email": "alice@example.com",
    "Country": "USA"
}
```

Here,

| Attribute | Value |
|------------|--------|
| UserId | U1001 |
| Name | Alice |
| Email | alice@example.com |
| Country | USA |

Unlike relational databases, attributes are **not predefined**.

They exist only if stored within an item.

---

# Sparse Attributes

Suppose the application introduces premium memberships.

Only premium users need a subscription field.

```json
{
    "UserId":"U1001",
    "Name":"Alice",
    "Subscription":"Premium"
}
```

Regular users remain unchanged.

```json
{
    "UserId":"U1002",
    "Name":"Bob"
}
```

This concept is known as **Sparse Data**.

Only items requiring a particular attribute actually store it.

Benefits include:

- Reduced storage consumption
- Flexible application evolution
- No schema migrations

Sparse attributes also become extremely important when designing **Global Secondary Indexes**, a topic covered later.

---

# Nested Attributes

Unlike SQL databases, DynamoDB attributes can themselves contain structured data.

Example:

```json
{
    "UserId":"U1001",
    "Address":{
        "Street":"Park Avenue",
        "City":"New York",
        "Zip":"10001"
    }
}
```

The Address attribute is itself a document.

Nested objects eliminate the need to create additional tables for many hierarchical data structures.

---

# Collection Attributes

Attributes can also contain collections.

Example:

```json
{
    "UserId":"U1001",
    "Skills":[
        "Python",
        "AWS",
        "Django"
    ]
}
```

Or

```json
{
    "UserId":"U1001",
    "Roles":[
        "Developer",
        "Reviewer",
        "Mentor"
    ]
}
```

Collections allow related information to remain together within the same item.

This improves read performance because a single request retrieves the complete object.

---

# Why DynamoDB Encourages Denormalization

Developers coming from SQL often ask:

> Why not separate Address, Skills, Orders, and Users into different tables?

The answer lies in distributed systems.

JOIN operations require data from multiple locations.

In distributed databases, this means:

- Additional network calls
- More latency
- Greater operational complexity

DynamoDB instead encourages storing information that is frequently accessed together within the same item.

For example,

Instead of

```text
Users Table

Addresses Table

Phone Table
```

DynamoDB often prefers

```json
{
    "UserId":"U1001",
    "Name":"Alice",
    "Phone":"123456789",
    "Address":{
        ...
    }
}
```

This design minimizes database requests.

The result is lower latency and predictable performance.

---

# Item Size Matters

Unlike relational databases, DynamoDB reads and writes an entire item.

This means item size directly affects:

- Read latency
- Write latency
- Storage cost
- Read Capacity Units (RCUs)
- Write Capacity Units (WCUs)

AWS currently limits a single item to **400 KB**.

Large items increase cost and reduce throughput.

A good DynamoDB data model keeps items as compact as possible while still satisfying application access patterns.

---

# SQL vs DynamoDB Thinking

Developers transitioning from SQL often attempt to recreate relational schemas.

For example,

```text
Customers

Orders

Products

Addresses

Coupons

Payments
```

This design works well in relational databases because JOINs are efficient.

In DynamoDB, however, applications are modeled around **how data is accessed**, not how entities relate to one another.

Instead of asking:

> "What tables should I create?"

DynamoDB encourages asking:

> "What information does my application need in a single request?"

This mindset shift is one of the biggest challenges when learning DynamoDB.

---

# Best Practices

- Keep related data together.
- Design items around application access patterns.
- Avoid storing unnecessary attributes.
- Keep items well below the 400 KB limit whenever possible.
- Prefer denormalization when it improves read performance.
- Use descriptive attribute names without making them excessively long, as attribute names contribute to item size.

---

# Common Mistakes

- Treating DynamoDB like a relational database.
- Creating one table for every entity.
- Normalizing data excessively.
- Ignoring item size limits.
- Designing tables before understanding access patterns.
- Assuming every item should contain identical attributes.

---

# Interview Notes

A common interview question is:

> **Why doesn't DynamoDB enforce a schema?**

The answer is not simply "because it's NoSQL."

A flexible schema enables applications to evolve rapidly without schema migrations, supports sparse data efficiently, and allows multiple logical entity types to coexist within the same table. These characteristics are essential for scalable designs such as **Single Table Design**, where different business entities intentionally share the same table.

---

# Key Takeaways

- A DynamoDB table is a logical container rather than a rigid relational structure.
- Items are self-contained documents uniquely identified by their primary key.
- Attributes are dynamic and exist only when stored.
- Flexible schemas eliminate costly schema migrations.
- Nested documents and collections reduce the need for joins.
- DynamoDB encourages denormalization to optimize for predictable, low-latency reads.
- Designing tables around **access patterns**, rather than relationships, is one of the most important principles in DynamoDB data modeling.