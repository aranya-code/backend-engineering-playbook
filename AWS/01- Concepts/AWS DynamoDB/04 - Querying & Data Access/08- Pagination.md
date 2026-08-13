# 08 - Pagination

## Overview

DynamoDB is designed to scale to **billions of items** while maintaining low latency. Returning an unlimited number of items in a single response would negatively impact:

- Memory usage
- Network bandwidth
- Response time
- Service availability

To prevent this, DynamoDB automatically **paginates** large Query and Scan results.

Instead of returning every matching item in one response, DynamoDB returns data in **pages**, allowing applications to retrieve additional pages as needed.

Pagination is a fundamental concept when building scalable DynamoDB applications.

---

# Why Pagination Exists

Imagine a table containing:

```text
Customer Orders

↓

50 Million Records
```

A customer requests:

```text
View Order History
```

Returning every order in one response would be inefficient.

Instead:

```text
Request

↓

Page 1

↓

Page 2

↓

Page 3

↓

...
```

Applications retrieve only the amount of data they currently need.

---

# The 1 MB Response Limit

DynamoDB limits each Query or Scan response to **1 MB** of data.

For example:

```text
Query

↓

3 MB Result Set
```

Response:

```text
Page 1

↓

1 MB
```

Additional data must be retrieved using another request.

---

# Internal Architecture

```text
               Query

                 │

                 ▼

        Read Matching Items

                 │

                 ▼

       Build 1 MB Response

                 │

                 ▼

 LastEvaluatedKey Present?

        │                 │

       Yes               No

        │                 │

        ▼                 ▼

Return Key         Return Complete Result
```

---

# LastEvaluatedKey

When additional pages exist, DynamoDB returns:

```text
LastEvaluatedKey
```

Example response:

```text
Items

↓

100 Orders

+

LastEvaluatedKey
```

The application uses this key to request the next page.

---

# ExclusiveStartKey

To continue reading:

```text
ExclusiveStartKey

=

LastEvaluatedKey
```

Workflow:

```text
Page 1

↓

LastEvaluatedKey

↓

ExclusiveStartKey

↓

Page 2
```

---

# Pagination Workflow

```text
Application

↓

Query

↓

Page 1

↓

LastEvaluatedKey?

↓

Yes

↓

Query Again

↓

Page 2

↓

LastEvaluatedKey?

↓

Yes

↓

Continue

↓

Last Page

↓

No LastEvaluatedKey

↓

Finished
```

---

# Query Pagination Example

Orders:

```text
Customer

↓

15,000 Orders
```

Application:

```text
Query Customer
```

Results:

```text
Page 1

↓

1 MB

↓

Page 2

↓

1 MB

↓

Page 3

↓

Remaining Records
```

---

# Scan Pagination Example

Scan:

```text
Entire Table

↓

50 Million Items
```

Results:

```text
Page 1

↓

1 MB

↓

Next Page

↓

1 MB

↓

Continue
```

Even though the results are paginated, Scan still reads the entire table over multiple requests.

---

# Page Size

Applications can control how many items are returned in each request using the `Limit` parameter.

Example:

```text
Limit = 20
```

Result:

```text
Maximum

20 Items
```

Important:

The `Limit` parameter controls the **number of items evaluated**, not necessarily the number of items returned after filtering.

---

# Query with Limit

Example:

```text
CustomerID = CUST1001

Limit = 10
```

Returns:

```text
Latest

10 Orders
```

Useful for dashboards and APIs.

---

# Limit with Filter Expression

Suppose:

```text
Limit

100 Items
```

Filter:

```text
Status = Delivered
```

Workflow:

```text
Read

100 Items

↓

Filter

↓

15 Returned
```

The limit applies before the filter.

---

# Pagination and RCUs

Pagination does **not** reduce read capacity consumption.

Instead of:

```text
Read

1000 Items

Once
```

The application performs:

```text
Read

100 Items

10 Times
```

The total RCUs consumed remain approximately the same.

Pagination simply spreads the work across multiple requests.

---

# SDK Pagination

Most AWS SDKs automatically support pagination.

Workflow:

```text
Application

↓

SDK Iterator

↓

Page 1

↓

Page 2

↓

Page 3
```

The developer often does not need to manually manage `LastEvaluatedKey`.

---

# Infinite Scrolling Example

Social media feed:

```text
Page 1

↓

20 Posts

↓

User Scrolls

↓

Page 2

↓

20 Posts

↓

User Scrolls

↓

Page 3
```

Pagination provides a smooth user experience.

---

# Real-World Example — E-commerce

Orders:

```text
Customer

↓

2000 Orders
```

Dashboard:

```text
Display

20 Orders

Per Page
```

Workflow:

```text
Query

↓

Limit 20

↓

LastEvaluatedKey

↓

Next Page
```

---

# Real-World Example — Banking

Transactions:

```text
50,000 Transactions
```

Customer requests:

```text
Statement
```

Application:

```text
Retrieve

100 Transactions

Per Request
```

Instead of loading every transaction at once.

---

# Real-World Example — IoT

Sensor Data:

```text
Millions

of Events
```

Monitoring dashboard:

```text
Most Recent

100 Events
```

Pagination allows efficient browsing of historical telemetry.

---

# Common Misconceptions

## Pagination Reduces Cost

Incorrect.

Pagination changes:

- Response size
- User experience

It does **not** reduce:

- RCUs
- Total data read

---

## Limit Equals Returned Items

Incorrect.

When using Filter Expressions:

```text
Limit

100

↓

Filter

↓

20 Returned
```

The limit applies before filtering.

---

## Missing LastEvaluatedKey Means Error

Incorrect.

If `LastEvaluatedKey` is absent:

```text
End of Result Set
```

This indicates all matching items have been retrieved.

---

# Best Practices

- Always design APIs to support pagination.
- Check for `LastEvaluatedKey` after every Query or Scan.
- Use `ExclusiveStartKey` to retrieve the next page.
- Return page tokens rather than exposing internal keys directly to API consumers.
- Use sensible page sizes (e.g., 20–100 items for user-facing APIs).
- Avoid loading an entire dataset into memory.

---

# Common Mistakes

## Ignoring Pagination

Applications that assume all data fits in one response may silently miss records once the result exceeds 1 MB.

---

## Returning Massive Responses

Large responses increase latency, bandwidth usage, and memory consumption. Smaller pages improve scalability and user experience.

---

## Exposing DynamoDB Keys Directly

Instead of returning raw `LastEvaluatedKey` values to clients, many production APIs encode them as opaque continuation tokens to decouple the public API from the underlying database schema.

---

## Using Large Page Sizes

Very large page sizes increase response time and memory usage. Choose a size appropriate for the use case.

---

# Architecture Perspective

```text
                 Application

                       │

                 Query Request

                       │

                       ▼

              Read Matching Items

                       │

             Build 1 MB Response

                       │

              LastEvaluatedKey?

              ┌────────┴────────┐

              ▼                 ▼

            Yes                 No

              │                 │

              ▼                 ▼

    Return Page + Token   Finished

              │

              ▼

     Next Request Uses

      ExclusiveStartKey
```

Pagination enables DynamoDB to scale efficiently without overwhelming clients or the service.

---

# Production Considerations

Pagination is essential in production systems that serve large datasets.

Common use cases include:

- Customer order history
- Financial transaction statements
- Social media feeds
- Product catalogs
- Audit logs
- IoT telemetry dashboards

Backend services typically wrap DynamoDB's `LastEvaluatedKey` in a secure, opaque continuation token so that API consumers are not exposed to internal key structures. This also provides flexibility if the underlying schema changes in the future.

---

# Interview Notes

A common interview question is:

> **Why does DynamoDB paginate Query and Scan results?**

To limit each response to a maximum of 1 MB, preventing excessively large responses and enabling predictable performance at scale.

Another common question is:

> **What is `LastEvaluatedKey`?**

`LastEvaluatedKey` identifies where the current page ended. If it is present, additional matching items remain, and the next request should provide it as the `ExclusiveStartKey`.

Another common question is:

> **Does pagination reduce read capacity consumption?**

No. Pagination only divides the results into multiple requests. The total amount of data read—and therefore the total RCUs consumed—remains approximately the same.

---

# Key Takeaways

- DynamoDB automatically paginates Query and Scan results into pages of up to **1 MB**.
- `LastEvaluatedKey` indicates that additional pages are available.
- `ExclusiveStartKey` is used to continue reading from the previous page.
- Pagination improves scalability, responsiveness, and user experience but does **not** reduce read capacity consumption.
- Production APIs should expose opaque continuation tokens rather than raw DynamoDB pagination keys.