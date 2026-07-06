# Annotations & Metadata

Annotations and Metadata allow developers to add additional information to traces.

They make traces easier to search, filter, and analyze during troubleshooting.

Although both store extra information, they serve different purposes.

------------------------------------------------------------------------

# What are Annotations?

Annotations are **indexed key-value pairs** added to traces.

Because they are indexed, they can be searched and filtered in the X-Ray console.

Example:

```text
UserId = 1054

Environment = Production

Region = us-east-1
```

------------------------------------------------------------------------

# What is Metadata?

Metadata is additional information attached to a trace that is **not indexed**.

Metadata is useful for storing detailed debugging information that does not need to be searchable.

Example:

```text
SQL Query

HTTP Response Body

Configuration Values
```

------------------------------------------------------------------------

# Annotations vs Metadata

| Feature | Annotations | Metadata |
|----------|-------------|----------|
| Searchable | ✅ Yes | ❌ No |
| Indexed | ✅ Yes | ❌ No |
| Filtering | ✅ Supported | ❌ Not Supported |
| Debug Information | Limited | Extensive |

------------------------------------------------------------------------

# Why Use Annotations?

Annotations help:

- Search traces quickly
- Filter by business data
- Group requests
- Analyze user activity
- Investigate production issues

------------------------------------------------------------------------

# Why Use Metadata?

Metadata helps store:

- Debug details
- API responses
- SQL statements
- Configuration values
- Internal processing data

------------------------------------------------------------------------

# Adding Annotations

Examples:

```text
CustomerId

OrderId

Environment

Application

Version
```

These values become searchable in the X-Ray console.

------------------------------------------------------------------------

# Adding Metadata

Examples:

```text
Complete SQL Query

JSON Payload

Headers

Cache Information

Debug Logs
```

Metadata is displayed when viewing an individual trace.

------------------------------------------------------------------------

# Real-World Example

An order processing service records:

Annotation:

```text
OrderId = 84563
```

Metadata:

```text
SQL Query

Payment Gateway Response

Shipping Details
```

Engineers can search using the Order ID and then inspect the detailed metadata for debugging.

------------------------------------------------------------------------

# Best Practices

- Use annotations only for searchable business information.
- Store detailed debug information as metadata.
- Avoid storing sensitive information.
- Keep annotation names consistent.
- Limit metadata size.

------------------------------------------------------------------------

# Key Takeaways

- Annotations are indexed and searchable.
- Metadata is not indexed and is intended for debugging.
- Together they provide valuable context for trace analysis.
- Proper use of annotations and metadata significantly improves troubleshooting efficiency.