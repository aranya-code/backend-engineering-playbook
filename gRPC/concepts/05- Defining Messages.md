# Defining Messages

## Learning Objectives

After completing this chapter, you will be able to:

- Understand what a Protocol Buffer message is.
- Learn how to define messages in a `.proto` file.
- Understand fields and field numbers.
- Learn how to use scalar data types.
- Understand nested messages.
- Learn about repeated fields.
- Understand message design best practices.

---

# What is a Message?

A **message** is the fundamental data structure in Protocol Buffers.

It defines the data that is exchanged between a client and a server.

You can think of a message as being similar to:

- A class in object-oriented programming
- A struct in C/C++
- A data model in an API
- A JSON object

Whenever a client sends a request or receives a response, it is actually sending or receiving a Protocol Buffer message.

---

# Basic Message Syntax

A message is declared using the `message` keyword.

Example:

```proto
message Employee {
    int32 id = 1;
    string name = 2;
    string email = 3;
}
```

In this example:

- `Employee` is the message name.
- `id`, `name`, and `email` are fields.
- Each field has a data type.
- Each field has a unique field number.

---

# Anatomy of a Message

Consider the following example:

```proto
message Employee {

    int32 id = 1;

    string name = 2;

    string email = 3;

}
```

Let's break it down.

| Part | Description |
|------|-------------|
| `message` | Declares a new message type |
| `Employee` | Name of the message |
| `int32` | Data type |
| `id` | Field name |
| `1` | Field number |

---

# Fields

A **field** represents a single piece of data inside a message.

Example:

```proto
message Employee {

    int32 id = 1;

    string name = 2;

    string department = 3;

}
```

Here:

- `id`
- `name`
- `department`

are three different fields.

Each field stores one value.

---

# Field Numbers

Every field must have a **unique field number**.

Example:

```proto
message Employee {

    int32 id = 1;

    string name = 2;

    string email = 3;

}
```

The numbers:

```text
1

2

3
```

are not optional.

They uniquely identify fields in the binary Protocol Buffer format.

---

# Why Are Field Numbers Important?

Unlike JSON, Protocol Buffers do not transmit field names.

Instead, they transmit field numbers.

For example:

Instead of transmitting

```json
{
  "id": 101,
  "name": "Alice"
}
```

Protocol Buffers transmit a compact binary representation using field numbers.

This makes messages:

- Smaller
- Faster
- More efficient

---

# Rules for Field Numbers

When assigning field numbers:

- Every field number must be unique.
- Field numbers cannot be duplicated.
- Once assigned, a field number should never change.
- Deleted field numbers should not be reused.
- Commonly used fields should use smaller field numbers because they require fewer bytes in the binary encoding.

Example:

```proto
message Employee {

    int32 id = 1;

    string name = 2;

    string email = 3;

}
```

---

# Scalar Data Types

Protocol Buffers provide several built-in scalar types.

Example:

```proto
message Employee {

    int32 id = 1;

    string name = 2;

    bool active = 3;

    double salary = 4;

}
```

Some commonly used scalar types include:

| Type | Description |
|------|-------------|
| `int32` | 32-bit integer |
| `int64` | 64-bit integer |
| `uint32` | Unsigned 32-bit integer |
| `uint64` | Unsigned 64-bit integer |
| `float` | Single precision floating point |
| `double` | Double precision floating point |
| `bool` | Boolean value |
| `string` | UTF-8 text |
| `bytes` | Raw binary data |

Scalar types will be covered in greater detail in a later chapter.

---

# Nested Messages

A message can contain another message.

Example:

```proto
message Address {

    string city = 1;

    string country = 2;

}

message Employee {

    int32 id = 1;

    string name = 2;

    Address address = 3;

}
```

Here:

- `Address` is its own message.
- `Employee` contains an `Address`.

Nested messages help organize related data.

---

# Repeated Fields

Sometimes a field needs to store multiple values.

The `repeated` keyword is used for this purpose.

Example:

```proto
message Employee {

    int32 id = 1;

    repeated string skills = 2;

}
```

Possible values:

```text
Python

Django

Docker

Redis
```

A repeated field behaves like a list or array.

---

# Message Composition

Messages can be combined to model complex business objects.

Example:

```proto
message Department {

    string name = 1;

}

message Employee {

    int32 id = 1;

    string name = 2;

    Department department = 3;

    repeated string skills = 4;

}
```

This approach keeps messages modular and easier to maintain.

---

# Message Design Best Practices

When designing messages:

- Keep messages focused on a single responsibility.
- Use meaningful field names.
- Assign field numbers carefully.
- Never change existing field numbers.
- Prefer adding new fields instead of modifying existing ones.
- Reuse common message types where appropriate.
- Keep related information together.

Well-designed messages improve readability, maintainability, and compatibility.

---

# Real-World Example

Consider an Employee Management System.

```proto
message Employee {

    int32 id = 1;

    string first_name = 2;

    string last_name = 3;

    string email = 4;

    bool active = 5;

    repeated string skills = 6;

}
```

When a client requests employee information, the server sends an `Employee` message containing all of the required data.

Because both the client and server are generated from the same `.proto` file, they interpret the message consistently.

---

# Common Mistakes

Avoid the following mistakes:

- Changing field numbers after deployment.
- Reusing deleted field numbers.
- Using duplicate field numbers.
- Creating overly large messages.
- Combining unrelated data into a single message.
- Using unclear or inconsistent field names.

---

# Key Takeaways

- A message is the basic data structure used in Protocol Buffers.
- Messages define the data exchanged between clients and servers.
- Each message contains one or more fields.
- Every field must have a unique field number.
- Field numbers are used during binary serialization instead of field names.
- Messages can contain scalar types, nested messages, and repeated fields.
- Well-designed messages improve readability, maintainability, and backward compatibility.