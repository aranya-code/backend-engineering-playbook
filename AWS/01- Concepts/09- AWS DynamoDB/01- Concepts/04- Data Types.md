# 04 - Data Types

## Overview

Every database stores information in a specific format.

In relational databases, data types define how values are stored, validated, indexed, and manipulated. Choosing the correct data type affects storage efficiency, query performance, and application behavior.

DynamoDB follows the same principle, but unlike traditional SQL databases, it provides a smaller set of highly flexible data types designed specifically for distributed storage.

Understanding these data types is important because every item, every attribute, and every index in DynamoDB ultimately stores one of these supported types.

Choosing the appropriate data type is not simply a modeling decision—it directly impacts application performance, storage cost, serialization, indexing, and SDK behavior.

---

# Why Data Types Matter

Suppose we store a user's age.

Option 1

```json
{
    "Age": 25
}
```

Option 2

```json
{
    "Age": "25"
}
```

Although both appear similar, DynamoDB treats them completely differently.

In the first example:

- Numeric comparisons work correctly.
- Sorting behaves numerically.
- Mathematical operations are supported.

In the second example:

- The value is treated as text.
- Lexicographical sorting is used.
- Numeric operations are impossible.

Choosing the wrong type can introduce subtle bugs that become difficult to detect as applications grow.

---

# DynamoDB Data Type Categories

DynamoDB supports three categories of data types.

```text
Data Types

├── Scalar Types

├── Document Types

└── Set Types
```

Each category is designed for different kinds of data.

---

# Scalar Data Types

Scalar types store a single value.

These are the most commonly used data types in DynamoDB.

Supported scalar types are:

- String (S)
- Number (N)
- Binary (B)
- Boolean (BOOL)
- Null (NULL)

---

# String (S)

Strings represent textual information.

Examples include:

- Names
- Email addresses
- Product IDs
- Order IDs
- URLs
- Countries

Example

```json
{
    "Name":"Alice"
}
```

Another example

```json
{
    "OrderId":"ORD-1001"
}
```

Internally, DynamoDB stores strings as UTF-8 encoded values.

String comparisons are case-sensitive.

For example,

```text
Apple

apple

APPLE
```

These are three different values.

---

## String Sorting

Strings are sorted lexicographically rather than numerically.

Example

```text
1

10

100

2

20
```

Notice that:

```text
10

comes before

2
```

because characters are compared from left to right.

This behavior is important when designing Sort Keys.

---

## Best Practices

Use strings for:

- UUIDs
- User IDs
- Country codes
- Status values
- ISO timestamps
- Business identifiers

Avoid storing numeric information as strings unless textual ordering is desired.

---

# Number (N)

Numbers support both integers and floating-point values.

Example

```json
{
    "Age":30
}
```

Another example

```json
{
    "Price":999.95
}
```

Unlike many databases, DynamoDB stores numbers using variable precision rather than fixed integer types such as INT or BIGINT.

Applications can safely perform:

- Addition
- Subtraction
- Atomic increments
- Comparisons

Numbers are required whenever mathematical operations are needed.

---

## Number Precision

Internally, DynamoDB stores numbers with up to **38 digits of precision**.

This allows extremely large or extremely precise numeric values.

Examples include:

- Financial transactions
- Scientific measurements
- Cryptocurrency balances

Applications using floating-point numbers should still be aware of precision limitations imposed by their programming language rather than DynamoDB itself.

---

# Binary (B)

Binary stores raw binary data.

Examples include:

- Images
- PDFs
- Encrypted values
- Serialized objects

Example

```text
Photo

↓

Binary Data
```

Although supported, storing large binary files inside DynamoDB is generally discouraged.

Large objects are better stored in Amazon S3, while DynamoDB stores only metadata and object references.

---

# Boolean (BOOL)

Boolean represents logical values.

Only two values exist.

```text
true

false
```

Example

```json
{
    "IsPremium":true
}
```

Boolean attributes improve readability and eliminate unnecessary string comparisons such as:

```text
YES

NO
```

or

```text
ACTIVE

INACTIVE
```

---

# Null (NULL)

NULL represents the intentional absence of a value.

Example

```json
{
    "MiddleName":null
}
```

This differs from simply omitting the attribute.

Missing attribute

```json
{
    "Name":"Alice"
}
```

NULL attribute

```json
{
    "Name":"Alice",
    "MiddleName":null
}
```

These two cases are treated differently by DynamoDB.

---

# Document Data Types

Document types allow hierarchical data structures.

Supported document types are:

- List
- Map

These are heavily used in modern applications.

---

# List (L)

Lists store ordered collections.

Example

```json
{
    "Skills":[
        "Python",
        "Django",
        "AWS"
    ]
}
```

Lists preserve insertion order.

Each element may even use a different data type.

Example

```json
[
    "Laptop",
    900,
    true,
    {
        "Brand":"Dell"
    }
]
```

Although possible, mixing unrelated data types usually reduces readability and should generally be avoided.

---

# Map (M)

Maps store nested key-value pairs.

Example

```json
{
    "Address":{
        "Street":"Park Avenue",
        "City":"New York",
        "Zip":"10001"
    }
}
```

Maps eliminate the need to create additional relational tables for many hierarchical objects.

Maps can themselves contain:

- Lists
- Maps
- Sets
- Scalars

This allows highly flexible document structures.

---

# Set Data Types

Unlike Lists, Sets contain **unique unordered values**.

DynamoDB supports three set types.

- String Set (SS)
- Number Set (NS)
- Binary Set (BS)

---

## String Set

Example

```json
{
    "Roles":[
        "Admin",
        "Developer",
        "Reviewer"
    ]
}
```

Duplicate values are automatically removed.

---

## Number Set

Example

```json
{
    "Scores":[
        95,
        90,
        87
    ]
}
```

Useful for mathematical collections.

---

## Binary Set

Stores multiple unique binary values.

Generally used less frequently than the other types.

---

# Nested Documents

One of DynamoDB's strengths is its ability to represent complex business objects.

Example

```json
{
    "UserId":"U1001",
    "Profile":{
        "Name":"Alice",
        "Address":{
            "City":"New York",
            "Country":"USA"
        },
        "Skills":[
            "Python",
            "AWS",
            "Terraform"
        ]
    }
}
```

Entire object graphs can often be stored inside a single item.

This reduces network calls and eliminates many JOIN operations.

---

# Internal Serialization

Although applications exchange JSON documents with DynamoDB, the service stores attributes using explicit type descriptors.

For example,

```json
{
    "Age":{
        "N":"30"
    }
}
```

```json
{
    "Name":{
        "S":"Alice"
    }
}
```

```json
{
    "Premium":{
        "BOOL":true
    }
}
```

AWS SDKs automatically perform this serialization and deserialization, allowing developers to work with native language objects.

Understanding this internal representation is useful when reading low-level API responses or debugging SDK behavior.

---

# Performance Considerations

Choosing the appropriate data type affects more than readability.

It also impacts:

- Storage consumption
- Network transfer size
- Capacity unit consumption
- Serialization overhead
- Query behavior

General recommendations include:

- Store numbers as Number rather than String.
- Prefer Map over multiple related attributes when representing nested objects.
- Store large files in Amazon S3 instead of Binary attributes.
- Keep attribute names concise because they contribute to item size.
- Avoid unnecessarily deep document nesting.

---

# Common Mistakes

- Storing numbers as strings.
- Using lists when uniqueness is required.
- Storing large files inside DynamoDB.
- Creating deeply nested documents that become difficult to maintain.
- Forgetting that String ordering is lexicographical rather than numeric.
- Assuming NULL and a missing attribute behave identically.

---

# Interview Notes

A common interview question is:

> **Why does DynamoDB support document data types if it is a key-value database?**

Because modern applications rarely store flat records.

Supporting Maps and Lists allows an entire business object to be retrieved in a single request while still benefiting from the scalability of a distributed key-value store.

This reduces application complexity, minimizes database round trips, and aligns with DynamoDB's philosophy of designing around access patterns rather than normalization.

---

# Key Takeaways

- DynamoDB supports three categories of data types: Scalar, Document, and Set.
- Strings, Numbers, Binary, Boolean, and Null are scalar values.
- Lists and Maps allow complex hierarchical documents.
- Sets enforce uniqueness and do not preserve ordering.
- Correct data type selection affects storage, performance, indexing, and application behavior.
- Understanding DynamoDB's internal attribute representation helps when working with low-level APIs and SDKs.