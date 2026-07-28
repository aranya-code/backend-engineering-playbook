# Overview

Every piece of information stored inside a Protocol Buffer message has a **data type**.

A data type tells the Protocol Buffer compiler what kind of value a field can store, how much memory it requires, and how it should be serialized into binary format.

Protocol Buffers provide a set of **built-in scalar data types** that cover the most common programming needs, including integers, floating-point numbers, strings, booleans, and binary data.

Choosing the appropriate data type is important because it affects application performance, network bandwidth, memory usage, and interoperability between different programming languages.

This chapter introduces all of the scalar data types available in **Proto3**, explains when to use each one, and provides practical examples.

---


# What are Scalar Data Types?

A scalar data type represents a **single value**.

Examples include:

- An employee ID
- A person's name
- A salary
- A boolean flag
- A phone number

Unlike repeated fields or nested messages, scalar fields contain only one value.

Example:

```proto
message Employee {

    int32 id = 1;

    string name = 2;

    bool active = 3;

}
```

Each field stores one individual value.

---

# Categories of Scalar Types

Protocol Buffers provide scalar types in several categories.

| Category | Examples |
|----------|----------|
| Integer | int32, int64, uint32, uint64 |
| Signed Integer | sint32, sint64 |
| Fixed-Length Integer | fixed32, fixed64 |
| Floating Point | float, double |
| Boolean | bool |
| Text | string |
| Binary | bytes |

Each type is optimized for different use cases.

---

# Integer Types

Integer types store whole numbers.

Proto3 provides several integer types.

| Type | Description |
|------|-------------|
| int32 | 32-bit signed integer |
| int64 | 64-bit signed integer |
| uint32 | 32-bit unsigned integer |
| uint64 | 64-bit unsigned integer |

Example:

```proto
message Employee {

    int32 id = 1;

    int64 salary = 2;

}
```

Use integer types whenever decimal values are not required.

---

# Signed Integers

Signed integers can store both positive and negative numbers.

Example:

```proto
int32 temperature = 1;
```

Possible values:

```text
-20

0

15

120
```

Signed integers are commonly used for:

- Temperature
- Balance changes
- Relative offsets
- Position values

---

# Unsigned Integers

Unsigned integers store only non-negative values.

Example:

```proto
uint32 employee_count = 1;
```

Possible values:

```text
0

1

100

5000
```

Unsigned integers are useful when negative values are never valid.

Examples include:

- User IDs
- Item counts
- Inventory quantities
- Population

---

# Variable-Length Encoding

Most integer types (`int32`, `int64`, `uint32`, `uint64`) use **variable-length encoding** (Varint).

With Varint encoding:

- Small numbers require fewer bytes.
- Large numbers require more bytes.

Example:

```text
Value: 5

↓

1 Byte
```

```text
Value: 1,000,000

↓

Multiple Bytes
```

This makes Protocol Buffers extremely efficient for transmitting small numeric values.

---

# Fixed-Length Integers

Protocol Buffers also provide fixed-size integer types.

| Type | Description |
|------|-------------|
| fixed32 | Fixed 32-bit integer |
| fixed64 | Fixed 64-bit integer |
| sfixed32 | Fixed signed 32-bit integer |
| sfixed64 | Fixed signed 64-bit integer |

Unlike Varint encoding, these types always occupy the same amount of storage.

Example:

```proto
fixed64 transaction_id = 1;
```

These types are useful when values are consistently large, as they avoid the overhead of variable-length encoding.

---

# Floating-Point Types

Floating-point types store decimal numbers.

Protocol Buffers provide:

| Type | Description |
|------|-------------|
| float | 32-bit floating-point number |
| double | 64-bit floating-point number |

Example:

```proto
message Product {

    float rating = 1;

    double price = 2;

}
```

Use floating-point types when fractional values are required.

---

# Choosing Between `float` and `double`

| float | double |
|--------|---------|
| 32-bit precision | 64-bit precision |
| Smaller memory usage | Higher precision |
| Faster processing | More accurate calculations |

For scientific calculations or financial applications that require high precision, `double` is generally preferred.

---

# Boolean Type

The `bool` type stores one of two values.

- true
- false

Example:

```proto
message User {

    bool verified = 1;

}
```

Boolean fields are commonly used for:

- Feature flags
- User status
- Permissions
- Activation state

---

# String Type

The `string` type stores UTF-8 encoded text.

Example:

```proto
message Employee {

    string name = 1;

    string email = 2;

}
```

Strings are commonly used for:

- Names
- Email addresses
- Cities
- Descriptions
- URLs

Protocol Buffers automatically handle UTF-8 encoding and decoding.

---

# Bytes Type

Sometimes data is not textual.

Examples include:

- Images
- PDF documents
- Audio files
- Cryptographic keys
- File contents

For these scenarios, Protocol Buffers provide the `bytes` type.

Example:

```proto
message File {

    bytes content = 1;

}
```

Unlike `string`, `bytes` can store arbitrary binary data.

---

# Scalar Type Summary

| Type | Typical Use Case |
|------|------------------|
| int32 | IDs, counters |
| int64 | Large numeric values |
| uint32 | Quantities, counts |
| uint64 | Very large positive values |
| sint32 | Frequently negative values |
| sint64 | Large signed values |
| fixed32 | Large fixed-size integers |
| fixed64 | Large identifiers |
| float | Measurements, ratings |
| double | Scientific calculations |
| bool | True/false values |
| string | Human-readable text |
| bytes | Binary files and raw data |

---

# Choosing the Right Data Type

Selecting the correct data type improves both performance and maintainability.

Examples:

| Scenario | Recommended Type |
|----------|------------------|
| Employee ID | int32 |
| File Size | uint64 |
| Temperature | sint32 |
| Product Price | double |
| User Name | string |
| Profile Picture | bytes |
| Account Active | bool |

Choosing the smallest appropriate type can reduce message size and improve efficiency.

---

# Real-World Example

```proto
message Employee {

    int32 id = 1;

    string name = 2;

    string email = 3;

    bool active = 4;

    double salary = 5;

    bytes profile_photo = 6;

}
```

This message demonstrates several commonly used scalar types working together.

---

# Best Practices

When defining scalar fields:

- Choose the smallest suitable data type.
- Use `string` for text and `bytes` for binary content.
- Prefer `bool` over integers for true/false values.
- Use `double` when greater numerical precision is required.
- Use unsigned integers only when negative values are impossible.
- Keep field types consistent across related messages.

---

# Common Mistakes

Avoid the following mistakes:

- Using `string` to store numeric values.
- Using `bytes` for text data.
- Choosing `double` when an integer is sufficient.
- Using unsigned integers where negative values may occur.
- Selecting larger numeric types without a valid reason.

---

# Key Takeaways

- Scalar data types represent single values within a Protocol Buffer message.
- Proto3 provides integer, floating-point, boolean, string, and binary data types.
- Integer types include signed, unsigned, and fixed-length variants for different performance characteristics.
- `string` stores UTF-8 text, while `bytes` stores arbitrary binary data.
- Choosing the correct scalar type improves performance, reduces message size, and enhances interoperability.
- Well-designed data types are the foundation of efficient and maintainable Protocol Buffer schemas.