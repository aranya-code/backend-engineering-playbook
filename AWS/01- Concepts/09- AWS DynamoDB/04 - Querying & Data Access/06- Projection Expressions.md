# 06 - Projection Expressions

## Overview

A **Projection Expression** allows an application to retrieve **only the attributes it needs** from an item.

By default, DynamoDB returns **all attributes** of every matching item.

However, many applications only require a subset of those attributes.

For example:

- User profile page → Name, Email
- Product listing → Product Name, Price
- Order history → Order ID, Status

There is no need to transfer large attributes such as descriptions, images, or metadata if they are not required.

Projection Expressions help:

- Reduce response size
- Reduce network bandwidth
- Improve application response time
- Improve API efficiency

> **Important**
>
> Projection Expressions **do not reduce Read Capacity Unit (RCU) consumption** because DynamoDB reads the complete item before returning only the requested attributes.

---

# What is a Projection Expression?

A Projection Expression specifies which attributes should appear in the response.

Without Projection Expression:

```text
Order

├── OrderID
├── CustomerID
├── Status
├── Amount
├── ShippingAddress
├── PaymentInfo
├── Notes
├── Metadata
└── AuditHistory
```

Response:

```text
Entire Item
```

With Projection Expression:

```text
OrderID

Status

Amount
```

Response:

```text
Only Three Attributes
```

---

# How Projection Expressions Work

Internal workflow:

```text
Query

↓

Read Complete Item

↓

Projection Expression

↓

Remove Unwanted Attributes

↓

Return Remaining Attributes
```

Notice that the entire item is still read internally.

---

# Why Use Projection Expressions?

Suppose an item contains:

```text
20 Attributes
```

Your API needs only:

```text
Username

Email

Role
```

Returning only these attributes:

- Reduces payload size
- Lowers network latency
- Makes APIs faster
- Reduces serialization overhead

---

# Example

User item:

```text
UserID

Name

Email

Phone

Address

Preferences

ProfilePicture

Biography

LastLogin

AuditHistory
```

Projection:

```text
Name

Email

LastLogin
```

Returned:

```text
Name

Email

LastLogin
```

---

# Internal Architecture

```text
                  Query

                    │

                    ▼

             Read Full Item

                    │

                    ▼

        Apply Projection Expression

                    │

        ┌───────────┴───────────┐

        ▼                       ▼

 Keep Attribute          Remove Attribute

        │

        ▼

 Return Reduced Response
```

---

# Projection Expressions with Query

Example table:

```text
PK = CustomerID

SK = OrderDate
```

Query:

```text
CustomerID = CUST1001
```

Projection:

```text
OrderID

Status

Amount
```

Returned:

```text
OrderID

Status

Amount
```

---

# Projection Expressions with Scan

Projection Expressions also work with Scan.

Workflow:

```text
Scan

↓

Read Full Items

↓

Projection Expression

↓

Return Selected Attributes
```

Although fewer attributes are returned, the Scan still reads every item.

---

# Nested Attributes

Projection Expressions support nested document attributes.

Example item:

```text
Customer

├── Name
├── Address
│     ├── City
│     ├── State
│     └── ZIP
└── Phone
```

Projection:

```text
Address.City
```

Response:

```text
City
```

Only the requested nested attribute is returned.

---

# Lists

Projection Expressions can retrieve list elements.

Example:

```text
Orders

[

Order1

Order2

Order3

]
```

Projection:

```text
Orders[0]
```

Response:

```text
Order1
```

---

# Reserved Words

Some DynamoDB attribute names are reserved keywords.

Example:

```text
Size

Count

Status
```

Instead of referencing them directly:

```text
Size
```

Applications use:

```text
Expression Attribute Names

↓

#S
```

This avoids conflicts with reserved keywords.

---

# Projection Expressions vs GSI Projections

These are different concepts.

Projection Expression:

```text
Runtime

↓

Choose Returned Attributes
```

GSI Projection:

```text
Schema Design

↓

Choose Stored Attributes
```

Do not confuse the two.

---

# Capacity Consumption

Example:

Item size:

```text
8 KB
```

Projection:

```text
OrderID
```

Although only one attribute is returned,

DynamoDB still reads:

```text
8 KB
```

RCUs remain unchanged.

---

# Network Optimization

Without Projection Expression:

```text
Response

↓

25 KB
```

With Projection Expression:

```text
Response

↓

2 KB
```

Advantages:

- Lower bandwidth
- Faster APIs
- Smaller JSON payloads
- Better mobile performance

---

# Real-World Example — E-commerce

Product item:

```text
Name

Price

Description

Reviews

Images

Inventory

Manufacturer

Specifications
```

Product listing page:

Needs only:

```text
Name

Price

Inventory
```

Projection Expression avoids returning large descriptions and image metadata.

---

# Real-World Example — Banking

Transaction item:

```text
TransactionID

Amount

Currency

Merchant

InternalAudit

Compliance

CustomerInfo
```

Customer statement:

Needs:

```text
TransactionID

Amount

Merchant
```

Projection Expression reduces the response payload.

---

# Real-World Example — Social Media

Post item:

```text
Content

Images

Videos

Comments

Likes

Shares

Metadata
```

Feed page:

Needs:

```text
Content

Likes

Shares
```

Projection Expression avoids transferring unnecessary metadata.

---

# Best Practices

- Return only the attributes required by the application.
- Use Projection Expressions for mobile and web APIs.
- Reduce response payloads whenever possible.
- Combine Projection Expressions with efficient Query operations.
- Remember that Projection Expressions optimize network usage—not database reads.

---

# Common Mistakes

## Assuming Projection Expressions Reduce RCUs

Incorrect.

DynamoDB reads the full item before selecting which attributes to return.

---

## Returning Entire Items

Many APIs return:

```text
Entire Object
```

even when only:

```text
Name

Status
```

are needed.

This increases response size unnecessarily.

---

## Confusing with GSI Projections

Projection Expressions determine what is **returned** during a request.

GSI Projections determine what is **stored** inside an index.

These are separate concepts.

---

# Projection Expression vs Filter Expression

| Feature | Projection Expression | Filter Expression |
|----------|----------------------|-------------------|
| Reduces Response Size | ✅ | ❌ |
| Removes Attributes | ✅ | ❌ |
| Removes Items | ❌ | ✅ |
| Reduces RCUs | ❌ | ❌ |
| Applied After Read | ✅ | ✅ |

---

# Architecture Perspective

```text
                 Query

                   │

                   ▼

            Read Full Item

                   │

        ┌──────────┴──────────┐

        ▼                     ▼

 Projection Expression   Filter Expression

        │                     │

 Remove Attributes      Remove Items

        │                     │

        └──────────┬──────────┘

                   ▼

           Return Response
```

Projection Expressions shape **which attributes** are returned, while Filter Expressions determine **which items** are returned.

---

# Production Considerations

Projection Expressions are widely used in production microservices and REST APIs to reduce payload size.

Common scenarios include:

- Mobile applications with limited bandwidth
- Dashboard APIs
- Search result pages
- Summary reports
- Product catalogs
- User profile listings

Although they do not reduce RCU consumption, they improve overall application performance by minimizing network transfer and serialization costs.

---

# Interview Notes

A common interview question is:

> **Do Projection Expressions reduce DynamoDB read capacity consumption?**

No. DynamoDB reads the complete item before applying the Projection Expression. Projection Expressions reduce only the amount of data returned to the client.

Another common question is:

> **What is the benefit of Projection Expressions?**

They reduce response size, lower network bandwidth usage, and improve API response times by returning only the required attributes.

Another common question is:

> **What is the difference between a Projection Expression and a GSI Projection?**

A Projection Expression is specified at query time to control which attributes are returned. A GSI Projection is defined when creating an index and determines which attributes are stored within that index.

---

# Key Takeaways

- Projection Expressions allow applications to return only selected attributes from matching items.
- They reduce response payload size and improve network efficiency.
- Projection Expressions do **not** reduce RCU consumption because DynamoDB reads the full item first.
- They can be used with both Query and Scan operations.
- Do not confuse Projection Expressions with GSI Projection Types, which are part of index design.