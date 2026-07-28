# Overview

While Protocol Buffers provide scalar types such as `int32`, `string`, and `bool`, many applications require more sophisticated data types. For example:

- Dates and timestamps
- Time durations
- Empty request or response messages
- Arbitrary JSON-like structures
- Dynamic message types
- Partial updates

Instead of requiring developers to define these common structures repeatedly, Protocol Buffers provide a collection of **Well-Known Types (WKTs)**.

Well-Known Types are standard message definitions maintained by Google. They are included with the Protocol Buffer compiler and are available across all supported programming languages. These types improve interoperability, reduce duplication, and provide standardized solutions for common data modeling problems.

This chapter introduces the most commonly used Well-Known Types, explains when to use them, and demonstrates how they simplify Protocol Buffer and gRPC development.

---

# What are Well-Known Types?

Well-Known Types are predefined Protocol Buffer messages that solve common problems.

Instead of creating your own message like this:

```proto
message Timestamp {

    int64 seconds = 1;

    int32 nanos = 2;

}
```

You can simply import Google's standard implementation.

```proto
import "google/protobuf/timestamp.proto";
```

This promotes consistency across applications and programming languages.

---

# Why Use Well-Known Types?

Consider representing a timestamp.

Without a Well-Known Type:

```proto
message Event {

    int64 created_at = 1;

}
```

Questions immediately arise:

- Is the value in seconds?
- Milliseconds?
- Microseconds?
- UTC?
- Local time?

Using the standard `Timestamp` message removes this ambiguity.

```proto
import "google/protobuf/timestamp.proto";

message Event {

    google.protobuf.Timestamp created_at = 1;

}
```

Every developer immediately understands the meaning of the field.

---

# Importing Well-Known Types

Before using a Well-Known Type, it must be imported.

Example:

```proto
import "google/protobuf/timestamp.proto";
```

Multiple Well-Known Types can be imported.

```proto
import "google/protobuf/timestamp.proto";
import "google/protobuf/duration.proto";
import "google/protobuf/empty.proto";
```

The compiler includes these standard definitions automatically.

---

# Timestamp

The most frequently used Well-Known Type is `Timestamp`.

Import:

```proto
import "google/protobuf/timestamp.proto";
```

Usage:

```proto
message Employee {

    int32 id = 1;

    google.protobuf.Timestamp joined_at = 2;

}
```

Typical use cases:

- User registration date
- Order creation time
- Login timestamp
- Audit logs
- Database records

The timestamp represents an absolute point in time using UTC.

---

# Duration

`Duration` represents a span of time.

Import:

```proto
import "google/protobuf/duration.proto";
```

Example:

```proto
message Video {

    string title = 1;

    google.protobuf.Duration length = 2;

}
```

Typical use cases:

- Video duration
- Timeout values
- Retry intervals
- Cache expiration
- Session lifetime

Unlike `Timestamp`, which represents a specific moment, `Duration` represents an amount of time.

---

# Empty

Sometimes a request or response contains no data.

Instead of creating an empty message:

```proto
message Empty {}
```

Use the standard type.

```proto
import "google/protobuf/empty.proto";
```

Example:

```proto
service HealthService {

    rpc Check(google.protobuf.Empty)
        returns (google.protobuf.Empty);

}
```

Common use cases:

- Health checks
- Ping requests
- Delete operations
- Trigger-only RPCs

---

# Any

`Any` allows a field to contain **any Protocol Buffer message**.

Import:

```proto
import "google/protobuf/any.proto";
```

Example:

```proto
message Event {

    google.protobuf.Any payload = 1;

}
```

Possible payloads:

```text
UserCreated

OrderPlaced

PaymentReceived

InvoiceGenerated
```

This provides flexibility when the exact message type is not known in advance.

---

# Struct

`Struct` represents JSON-like objects.

Import:

```proto
import "google/protobuf/struct.proto";
```

Example:

```proto
message Metadata {

    google.protobuf.Struct data = 1;

}
```

Possible contents:

```json
{
  "theme": "dark",
  "language": "English",
  "notifications": true
}
```

Useful for dynamic configuration or arbitrary metadata.

---

# Value

`Value` represents a single dynamically typed value.

Import:

```proto
import "google/protobuf/struct.proto";
```

Example:

```proto
google.protobuf.Value value = 1;
```

The value may represent:

- String
- Number
- Boolean
- Null
- List
- Object

It is commonly used together with `Struct`.

---

# ListValue

`ListValue` represents a JSON-style array.

Example:

```proto
message Tags {

    google.protobuf.ListValue values = 1;

}
```

Possible data:

```json
[
  "Python",
  "gRPC",
  "Backend",
  "Microservices"
]
```

---

# FieldMask

`FieldMask` specifies which fields should be updated or retrieved.

Import:

```proto
import "google/protobuf/field_mask.proto";
```

Example:

```proto
message UpdateUserRequest {

    User user = 1;

    google.protobuf.FieldMask update_mask = 2;

}
```

Suppose only the email address should be updated.

```text
update_mask

↓

email
```

This avoids updating unnecessary fields.

Field masks are widely used in Google APIs and partial update (PATCH) operations.

---

# Wrapper Types

Earlier versions of Proto3 commonly used wrapper types to represent nullable scalar values.

Examples include:

- `StringValue`
- `Int32Value`
- `BoolValue`
- `DoubleValue`

Example:

```proto
import "google/protobuf/wrappers.proto";

message User {

    google.protobuf.StringValue nickname = 1;

}
```

Today, for many use cases, the `optional` keyword is preferred for scalar field presence. Wrapper types are still useful when interoperability or APIs specifically require message-based scalar values.

---

# Common Well-Known Types

| Type | Purpose |
|------|---------|
| Timestamp | Date and time |
| Duration | Time interval |
| Empty | Empty request or response |
| Any | Store arbitrary messages |
| Struct | JSON object |
| Value | Dynamic value |
| ListValue | JSON array |
| FieldMask | Partial updates |
| Wrapper Types | Message-based scalar values |

---

# Real-World Example

Consider a user management service.

```proto
syntax = "proto3";

import "google/protobuf/timestamp.proto";
import "google/protobuf/field_mask.proto";

message User {

    int32 id = 1;

    string name = 2;

    google.protobuf.Timestamp created_at = 3;

}

message UpdateUserRequest {

    User user = 1;

    google.protobuf.FieldMask update_mask = 2;

}
```

In this example:

- `Timestamp` records when the user was created.
- `FieldMask` specifies which fields should be updated.
- Standard Protocol Buffer types eliminate the need for custom implementations.

---

# When Should You Use Well-Known Types?

Well-Known Types are appropriate whenever your application needs standardized representations of common concepts.

Common scenarios include:

- Recording timestamps
- Measuring durations
- Creating empty requests or responses
- Supporting dynamic metadata
- Implementing partial updates
- Building generic event systems
- Representing JSON-like data

Using these types improves consistency and makes APIs easier to understand.

---

# Best Practices

- Prefer `Timestamp` over custom date or time fields.
- Use `Duration` for time intervals instead of numeric values.
- Use `Empty` instead of defining empty messages.
- Use `FieldMask` for partial update operations.
- Use `Struct` and `Value` only when the schema cannot be defined statically.
- Avoid overusing `Any`; prefer explicit message types whenever possible.
- Import only the Well-Known Types that your application actually uses.

---

# Common Mistakes

Avoid the following mistakes:

- Creating custom timestamp or duration messages.
- Using `Any` when a strongly typed message is more appropriate.
- Using `Struct` for data that has a fixed schema.
- Representing time as plain integers without documenting the unit.
- Forgetting to import the required Well-Known Type before using it.
- Using wrapper types when `optional` fields provide the required behavior.

---

# Key Takeaways

- Well-Known Types are standard Protocol Buffer messages maintained by Google.
- They provide reusable solutions for common data modeling requirements such as timestamps, durations, empty messages, dynamic data, and partial updates.
- `Timestamp`, `Duration`, `Empty`, and `FieldMask` are among the most frequently used Well-Known Types in production gRPC applications.
- Using Well-Known Types improves interoperability, consistency, and API readability.
- Prefer standard types over custom implementations whenever they satisfy your application's requirements.
```