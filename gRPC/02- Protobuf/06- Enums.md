# Overview

In many applications, a field can only have a **fixed set of predefined values**.

For example:

- An order can be **Pending**, **Shipped**, or **Delivered**.
- A payment can be **Success**, **Failed**, or **Refunded**.
- A user's role can be **Admin**, **Manager**, or **Employee**.

Using strings to represent these values is error-prone because developers may accidentally use inconsistent spellings such as `"Pending"`, `"pending"`, or `"PENDING"`.

Protocol Buffers solve this problem using **Enumerations (Enums)**.

An enum defines a fixed list of named constants, making APIs more type-safe, readable, and maintainable.

This chapter introduces enums, explains how they work, discusses Proto3 enum rules, and demonstrates how they are used in real-world applications.

---


# What is an Enum?

An **enum** (enumeration) is a custom data type that represents a **fixed set of predefined values**.

Instead of allowing arbitrary input, an enum restricts a field to specific choices.

For example, instead of storing:

```text
Order Status

↓

"Pending"

"Shipped"

"Delivered"
```

An enum defines these values explicitly.

```proto
enum OrderStatus {

    ORDER_STATUS_UNSPECIFIED = 0;

    PENDING = 1;

    SHIPPED = 2;

    DELIVERED = 3;

}
```

Only these values are considered valid.

---

# Why Use Enums?

Suppose order status is stored as a string.

```proto
message Order {

    string status = 1;

}
```

Possible values:

```text
Pending

pending

PENDING

Pendding

Shiped
```

Even small spelling mistakes create inconsistent data.

Using an enum eliminates this problem.

```proto
message Order {

    OrderStatus status = 1;

}
```

The compiler ensures only valid values are used.

---

# Defining an Enum

The syntax is straightforward.

```proto
enum UserRole {

    USER_ROLE_UNSPECIFIED = 0;

    ADMIN = 1;

    MANAGER = 2;

    EMPLOYEE = 3;

}
```

Each enum value has:

- A name
- A unique numeric value

---

# Using an Enum in a Message

Enums behave like any other data type.

Example:

```proto
enum Status {

    STATUS_UNSPECIFIED = 0;

    ACTIVE = 1;

    INACTIVE = 2;

}

message Employee {

    int32 id = 1;

    string name = 2;

    Status status = 3;

}
```

Here, the `status` field can only contain one of the defined enum values.

---

# Enum Values

Each enum constant is associated with an integer.

Example:

```proto
enum Priority {

    PRIORITY_UNSPECIFIED = 0;

    LOW = 1;

    MEDIUM = 2;

    HIGH = 3;

}
```

Internal representation:

| Enum Name | Numeric Value |
|-----------|---------------:|
| PRIORITY_UNSPECIFIED | 0 |
| LOW | 1 |
| MEDIUM | 2 |
| HIGH | 3 |

During serialization, Protocol Buffers transmit the numeric value rather than the text.

---

# Why Must the First Value Be Zero?

In **Proto3**, the first enum value **must always be zero**.

Example:

```proto
enum Status {

    STATUS_UNSPECIFIED = 0;

    ACTIVE = 1;

    INACTIVE = 2;

}
```

The zero value acts as the **default value** when an enum field has not been explicitly assigned.

For this reason, the first value is commonly named:

- `UNKNOWN`
- `UNSPECIFIED`
- `NONE`

This makes it clear that no meaningful value has been selected.

---

# Default Enum Value

Consider:

```proto
message Employee {

    Status status = 1;

}
```

If the application never assigns a value to `status`, Protocol Buffers automatically use:

```text
STATUS_UNSPECIFIED
```

This behavior is important because Proto3 does not require fields to be explicitly initialized.

---

# Enum Naming Conventions

Enum names should clearly describe the group of values.

Example:

```proto
enum PaymentStatus
```

Enum values should be descriptive and uppercase.

Example:

```proto
PENDING

SUCCESS

FAILED

REFUNDED
```

For the zero value, use a descriptive prefix.

Example:

```proto
PAYMENT_STATUS_UNSPECIFIED = 0;
```

This avoids naming conflicts when multiple enums are generated into the same language.

---

# Real-World Example

Consider an e-commerce application.

```proto
enum OrderStatus {

    ORDER_STATUS_UNSPECIFIED = 0;

    PENDING = 1;

    CONFIRMED = 2;

    SHIPPED = 3;

    DELIVERED = 4;

    CANCELLED = 5;

}

message Order {

    int32 id = 1;

    OrderStatus status = 2;

}
```

Possible values:

```text
Order

↓

Status

↓

PENDING
```

or

```text
DELIVERED
```

The status is always one of the predefined values.

---

# Enums in Generated Code

When Protocol Buffers generate source code, enums become language-specific enumerations.

For example:

| Language | Generated Representation |
|----------|--------------------------|
| Python | Enum-like constants |
| Java | Enum |
| Go | Typed constants |
| C# | Enum |
| C++ | Enum |

Regardless of the programming language, the underlying numeric values remain the same.

---

# Advantages of Enums

Enums provide several benefits.

- Strong type safety
- Better readability
- Reduced spelling errors
- Smaller serialized messages
- Easier maintenance
- Clear API documentation

They also improve IDE support through autocomplete and compile-time validation.

---

# When Should You Use Enums?

Enums are ideal whenever a field has a limited number of valid values.

Common examples include:

- User roles
- Payment status
- Order status
- Account state
- Priority level
- Device type
- Gender
- Country codes (small predefined lists)
- Notification type

If the list of values is expected to change frequently or is user-defined, a string or another data model may be more appropriate.

---

# Best Practices

When defining enums:

- Always start with a zero value.
- Name the zero value using `*_UNSPECIFIED` or `*_UNKNOWN`.
- Use meaningful enum names.
- Keep enum values descriptive.
- Use enums only for fixed sets of values.
- Document the meaning of each enum when necessary.

---

# Common Mistakes

Avoid the following mistakes:

- Omitting the zero value.
- Using ambiguous enum names.
- Reusing numeric values within the same enum.
- Using enums for values that change frequently.
- Treating enums as arbitrary integers in application code.

---

# Key Takeaways

- Enums represent a fixed set of predefined values.
- They improve type safety, readability, and data consistency.
- Every enum value has a corresponding numeric representation.
- In Proto3, the first enum value must always be `0`, typically representing an unspecified or unknown state.
- Enum values are serialized as integers, making them compact and efficient.
- Enums are ideal for modeling statuses, roles, priorities, and other fields with a limited set of valid values.