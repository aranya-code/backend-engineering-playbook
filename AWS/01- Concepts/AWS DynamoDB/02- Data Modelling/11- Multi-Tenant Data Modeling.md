# 11 - Multi-Tenant Data Modeling

## Overview

Many SaaS (Software-as-a-Service) applications serve **multiple customers (tenants)** using the same infrastructure.

Examples include:

- Salesforce
- Slack
- Jira
- Shopify
- Notion
- GitHub Enterprise
- Zendesk

In these systems:

- Every customer has its own users.
- Every customer owns its own data.
- Data must never leak between tenants.
- The system must scale from a handful of customers to millions.

This is known as **Multi-Tenant Architecture**.

DynamoDB is particularly well-suited for multi-tenant systems because its flexible key design allows data isolation while maintaining horizontal scalability.

---

# What is a Tenant?

A tenant is an organization or customer using your application.

Example:

```text
CRM Platform

│

├── Company A

├── Company B

├── Company C

└── Company D
```

Each company believes it owns its own application.

Internally, they may all share the same DynamoDB table.

---

# Multi-Tenant Architectures

There are three common approaches.

### 1. Separate Database Per Tenant

```text
Company A

↓

Database A
```

```text
Company B

↓

Database B
```

Advantages

- Excellent isolation
- Independent scaling
- Easy backup

Disadvantages

- Expensive
- Operational overhead
- Difficult to manage thousands of databases

---

### 2. Separate Table Per Tenant

```text
Orders_A

Orders_B

Orders_C
```

Advantages

- Better isolation

Disadvantages

- Large number of tables
- Harder operational management
- AWS account limits

---

### 3. Shared Table (Recommended)

```text
Orders Table

↓

Tenant A

Tenant B

Tenant C

Tenant D
```

Most production SaaS applications use this model.

---

# Designing the Partition Key

The simplest design is:

```text
PK = TENANT#100
```

Example:

```text
PK = TENANT#100

SK = PROFILE
```

```text
PK = TENANT#100

SK = USER#500
```

```text
PK = TENANT#100

SK = ORDER#700
```

Everything belonging to Tenant 100 stays together.

---

# Better Composite Design

Most applications require multiple entities.

Example:

```text
PK = TENANT#100

SK = USER#500
```

```text
PK = TENANT#100

SK = PROJECT#300
```

```text
PK = TENANT#100

SK = INVOICE#900
```

Query:

```text
PK = TENANT#100
```

Returns the tenant's data.

---

# Another Pattern

Sometimes entity ownership matters.

Instead of:

```text
PK = TENANT#100
```

Use:

```text
PK = TENANT#100

SK = USER#200
```

Another partition:

```text
PK = TENANT#100

SK = USER#300
```

This supports efficient retrieval of tenant-specific resources.

---

# Example SaaS CRM

Tenant:

```text
Acme Corporation
```

Contains:

```text
Users

Contacts

Deals

Invoices
```

Table:

```text
PK = TENANT#ACME

SK = USER#100
```

```text
PK = TENANT#ACME

SK = CONTACT#500
```

```text
PK = TENANT#ACME

SK = DEAL#900
```

```text
PK = TENANT#ACME

SK = INVOICE#1000
```

Everything is logically isolated.

---

# Visual Representation

```text
TENANT#ACME

│

├── USER#100

├── USER#200

├── CONTACT#500

├── DEAL#900

└── INVOICE#1000
```

Another tenant:

```text
TENANT#GLOBAL

│

├── USER#10

├── USER#20

├── CONTACT#40

└── DEAL#80
```

Both tenants share one table.

---

# Access Patterns

Business requirement:

```text
Show all invoices

for Tenant ACME
```

Query:

```text
PK = TENANT#ACME

SK Begins With

INVOICE#
```

Business requirement:

```text
List all users

for Tenant ACME
```

Query:

```text
PK = TENANT#ACME

SK Begins With

USER#
```

---

# Why Include Tenant ID?

Without Tenant IDs:

```text
USER#100
```

Different companies could produce identical IDs.

With tenant prefixes:

```text
TENANT#ACME

↓

USER#100
```

and

```text
TENANT#GLOBAL

↓

USER#100
```

No collisions occur.

---

# Security Considerations

Isolation is not only about keys.

Applications must enforce:

- Authentication
- Authorization
- Tenant validation

Never trust a client-supplied tenant ID.

Instead:

```text
JWT

↓

Tenant ID

↓

Server Validation

↓

Query DynamoDB
```

The application should derive the tenant identifier from the authenticated identity rather than allowing users to specify it directly.

---

# IAM Fine-Grained Access Control

AWS IAM supports restricting access to items.

Example:

```text
User

↓

Tenant A
```

IAM policy:

```text
Can Access

TENANT#A
```

Cannot access:

```text
TENANT#B
```

This is called **Fine-Grained Access Control (FGAC)**.

---

# Hot Tenant Problem

Suppose:

```text
Small Tenant

↓

100 Requests
```

Large tenant:

```text
1 Million Requests
```

Partition:

```text
TENANT#AMAZON
```

may become a hot partition.

---

# Write Sharding Large Tenants

Instead of:

```text
TENANT#AMAZON
```

Use:

```text
TENANT#AMAZON#0

TENANT#AMAZON#1

TENANT#AMAZON#2

TENANT#AMAZON#3
```

Requests distribute across partitions.

The application queries multiple shards when necessary.

---

# Global Secondary Index Example

Suppose support engineers need:

```text
Find Users

By Email
```

Main table:

```text
PK = TENANT#ACME

SK = USER#500
```

GSI:

```text
PK = TENANT#ACME

SK = EMAIL#alice@example.com
```

Queries remain tenant-scoped.

Two tenants may both have:

```text
alice@example.com
```

without conflict because the tenant identifier is part of the index key.

---

# Data Isolation

Data isolation has two layers.

### Logical Isolation

Implemented through:

- Tenant-aware partition keys
- Application authorization
- IAM policies

---

### Physical Isolation

Implemented through:

- Separate AWS accounts
- Separate DynamoDB tables
- Separate databases

Large enterprise customers may require physical isolation for compliance.

---

# Real-World Example

A project management platform serves thousands of companies.

Every company has:

- Projects
- Tasks
- Users
- Documents

Each company's data is stored under:

```text
PK = TENANT#COMPANY_ID
```

Employees can only access their own tenant's partition, even though all tenants share the same DynamoDB table.

---

# Performance Considerations

Multi-tenant systems should monitor:

- Hot tenants
- Uneven traffic
- Storage growth
- GSI usage
- Capacity consumption

Large enterprise customers often generate significantly more traffic than smaller tenants.

---

# Best Practices

- Always include the tenant identifier in key design.
- Design every access pattern to remain tenant-scoped.
- Validate tenant identity on the server.
- Use IAM FGAC where appropriate.
- Monitor for hot tenants.
- Consider write sharding for very large customers.
- Encrypt sensitive tenant data.

---

# Common Mistakes

## Using Global IDs Without Tenant Context

Avoid:

```text
USER#100
```

Prefer:

```text
TENANT#ACME

↓

USER#100
```

---

## Trusting Client Requests

Never:

```text
GET

tenant=OtherCompany
```

Authorization must come from the authenticated identity.

---

## Ignoring Large Tenants

One enterprise customer can generate traffic equivalent to thousands of smaller customers.

Design for uneven workloads.

---

## Using Scan Across All Tenants

Avoid:

```text
Scan Table
```

Always design tenant-specific queries.

---

# Architecture Perspective

```text
Application

        │

        ▼

Authenticate User

        │

        ▼

Extract Tenant ID

        │

        ▼

Query

PK = TENANT#ACME

        │

        ▼

Partition

TENANT#ACME

        │

        ├── USER#100

        ├── PROJECT#500

        ├── TASK#900

        └── INVOICE#200

        │

        ▼

Application Response
```

Every request is scoped to a single tenant, ensuring predictable performance and strong logical isolation.

---

# Interview Notes

A common interview question is:

> **How do you model a multi-tenant SaaS application in DynamoDB?**

A common approach is to include the tenant identifier in the partition key so that all data belonging to a tenant is logically grouped together. Every query is scoped to the authenticated tenant, preventing cross-tenant access.

Another common question is:

> **How do you prevent one tenant from accessing another tenant's data?**

Use multiple layers of protection:

- Authenticate users.
- Derive the tenant ID from the authentication token.
- Authorize every request.
- Design partition keys with tenant identifiers.
- Optionally enforce access using IAM Fine-Grained Access Control.

Another common question is:

> **What if one tenant becomes significantly larger than all others?**

Large tenants can create hot partitions. Common mitigation techniques include write sharding, time bucketing, or splitting workloads across multiple partitions while keeping queries tenant-aware.

---

# Key Takeaways

- Multi-tenant design enables multiple customers to share a single DynamoDB table safely.
- The tenant identifier should be part of the primary key design.
- Tenant isolation is enforced through key design, authentication, authorization, and IAM policies.
- Design every access pattern to remain tenant-scoped.
- Monitor large tenants for partition hotspots and shard them when necessary.
- Well-designed multi-tenant schemas provide strong isolation, predictable performance, and cost-efficient scalability.