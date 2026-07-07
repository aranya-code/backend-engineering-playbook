# SQL vs NoSQL

# Introduction

Choosing the correct database is one of the most important architectural decisions in backend engineering. AWS provides both relational (SQL) and non-relational (NoSQL) database services, each optimized for different workloads.

---

# SQL Databases

Examples:
- Amazon RDS
- Amazon Aurora

Characteristics:

- Fixed schema
- ACID transactions
- Strong consistency
- SQL query language
- Supports joins and complex queries

Ideal for:

- Banking
- ERP
- CRM
- E-commerce orders

---

# NoSQL Databases

Examples:

- Amazon DynamoDB
- Amazon DocumentDB

Characteristics:

- Flexible schema
- Horizontal scalability
- High throughput
- Low latency
- Eventually consistent (configurable for some services)

Ideal for:

- Social media
- Gaming
- IoT
- Event-driven systems

---

# SQL vs NoSQL

| Feature | SQL | NoSQL |
|---------|-----|--------|
| Schema | Fixed | Flexible |
| Scaling | Vertical | Horizontal |
| Transactions | ACID | BASE / Service dependent |
| Query Language | SQL | API / Query Model |
| Joins | Yes | Usually No |

---

# AWS Service Mapping

| Requirement | AWS Service |
|-------------|-------------|
| Relational OLTP | Amazon RDS |
| High-performance relational | Amazon Aurora |
| Massive scale key-value | Amazon DynamoDB |
| Document database | Amazon DocumentDB |

---

# Best Practices

- Choose SQL when data integrity is critical.
- Choose NoSQL for massive scale and flexible schemas.
- Avoid selecting a database solely based on popularity.

---

# Interview Questions

1. SQL vs NoSQL?
2. When would you choose DynamoDB over Aurora?
3. Why can't every workload use SQL?

---

# Quick Revision

- SQL = ACID + Structured
- NoSQL = Flexible + Horizontal Scaling
- RDS/Aurora = SQL
- DynamoDB = NoSQL
