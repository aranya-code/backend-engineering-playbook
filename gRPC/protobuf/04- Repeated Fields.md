# Overview

In real-world applications, a field often needs to store **multiple values** rather than just one.

For example, an employee may have multiple phone numbers, a student may enroll in several courses, or an order may contain multiple products.

By default, every Protocol Buffer field stores only a **single value**. To represent collections such as lists or arrays, Protocol Buffers provide the **`repeated`** keyword.

A repeated field can contain zero, one, or many values of the same data type. It is one of the most commonly used features in Protocol Buffers and is widely used to model one-to-many relationships.

This chapter explores repeated fields, how they work, how they are serialized, and the best practices for using them effectively.

---


# What is a Repeated Field?

A repeated field is a field that can store **multiple values** of the same type.

Instead of holding a single value:

```text
Employee

↓

Phone Number

↓

9876543210
```

A repeated field stores a collection.

```text
Employee

↓

Phone Numbers

↓

9876543210

9123456789

9988776655
```

This is similar to an array or list in most programming languages.

---

# Why Do We Need Repeated Fields?

Many real-world entities naturally contain collections.

Examples include:

- Multiple phone numbers
- Multiple email addresses
- Product lists
- User roles
- Skills
- Tags
- Permissions
- Order items

Without repeated fields, developers would need to create unnecessary wrapper messages or duplicate fields.

---

# Declaring a Repeated Field

The syntax is straightforward.

```proto
repeated field_type field_name = field_number;
```

Example:

```proto
message Employee {

    int32 id = 1;

    string name = 2;

    repeated string phone_numbers = 3;

}
```

Here, `phone_numbers` can store any number of phone numbers.

---

# How Repeated Fields Work

A repeated field behaves like a collection.

```text
phone_numbers

↓

9876543210

9123456789

9988776655
```

The number of elements is not fixed.

A repeated field may contain:

- No values
- One value
- Many values

---

# Repeated Scalar Fields

Repeated fields are commonly used with scalar data types.

Example:

```proto
message Student {

    repeated string subjects = 1;

}
```

Possible values:

```text
Mathematics

Physics

Chemistry
```

This is equivalent to a list of strings.

---

# Repeated Message Fields

Repeated fields can also store messages.

Example:

```proto
message Address {

    string city = 1;

    string country = 2;

}

message Employee {

    int32 id = 1;

    repeated Address addresses = 2;

}
```

Here, an employee can have multiple addresses.

---

# Generated Code

When Protocol Buffers generate source code, repeated fields become collection types.

For example:

| Language | Collection Type |
|----------|-----------------|
| Python | List |
| Java | List |
| Go | Slice |
| C# | RepeatedField<T> |
| C++ | RepeatedPtrField |

Although the implementation differs by language, the behavior remains the same.

---

# Serialization

Each element of a repeated field is serialized individually.

Consider:

```proto
message Student {

    repeated string subjects = 1;

}
```

Suppose the values are:

```text
Mathematics

Physics

Chemistry
```

During serialization:

```text
Field 1

↓

Mathematics

↓

Field 1

↓

Physics

↓

Field 1

↓

Chemistry
```

Each value is encoded using the same field number.

The Protocol Buffer runtime reconstructs the collection during deserialization.

---

# Empty Repeated Fields

A repeated field does not need to contain values.

Example:

```proto
message Employee {

    repeated string skills = 1;

}
```

Possible message:

```text
skills

↓

(empty)
```

This is perfectly valid.

An empty repeated field simply represents an empty collection.

---

# Real-World Example

Consider an e-commerce application.

```proto
message Order {

    int32 order_id = 1;

    repeated string products = 2;

}
```

Possible data:

```text
Order

↓

Laptop

Mouse

Keyboard

Monitor
```

Instead of creating separate fields for each product, a repeated field models the order naturally.

---

# Nested Repeated Fields

Repeated fields are frequently combined with nested messages.

Example:

```proto
message Item {

    string name = 1;

    double price = 2;

}

message Order {

    int32 id = 1;

    repeated Item items = 2;

}
```

Each order may contain multiple item objects.

This approach is far more flexible than using separate fields for every possible item.

---

# Repeated Fields vs Multiple Fields

Instead of writing:

```proto
string phone1 = 1;

string phone2 = 2;

string phone3 = 3;
```

Prefer:

```proto
repeated string phone_numbers = 1;
```

Advantages:

- Cleaner schema
- Unlimited values
- Easier maintenance
- Better scalability

---

# Common Use Cases

Repeated fields are commonly used for:

- User roles
- Product lists
- Categories
- Skills
- Email addresses
- Phone numbers
- Tags
- Permissions
- Search results
- Order items

They are one of the most frequently used features in Protocol Buffers.

---

# Best Practices

When using repeated fields:

- Use repeated fields whenever multiple values are expected.
- Choose meaningful collection names.
- Prefer repeated messages for complex objects.
- Keep collections reasonably sized.
- Avoid creating multiple numbered fields (`item1`, `item2`, `item3`).

---

# Common Mistakes

Avoid the following mistakes:

- Creating multiple fields instead of using `repeated`.
- Using repeated fields when only a single value is ever expected.
- Mixing unrelated data inside the same collection.
- Creating excessively large collections without considering performance.
- Assuming repeated fields always contain at least one value.

---

# Key Takeaways

- The `repeated` keyword allows a field to store multiple values.
- Repeated fields are equivalent to arrays or lists in most programming languages.
- They can store both scalar values and message types.
- Repeated fields may contain zero, one, or many elements.
- During serialization, each element is encoded individually using the same field number.
- Repeated fields provide a clean, scalable way to model one-to-many relationships in Protocol Buffer schemas.