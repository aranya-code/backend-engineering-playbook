# Overview

As applications grow in complexity, a single message often needs to contain **other messages**.

For example, an employee may have an address, an order may contain customer information, or a company may contain multiple departments. Instead of storing all this information in a flat structure, Protocol Buffers allow messages to be composed of other messages.

This feature is known as **Nested Messages**.

Nested messages improve readability, promote code reuse, and help model complex real-world relationships. Rather than creating long messages with dozens of unrelated fields, developers can organize related information into smaller, reusable message types.

This chapter explores nested messages, how they are defined, when to use them, and the best practices for designing hierarchical data structures.

---


# What is a Nested Message?

A nested message is a **message that contains another message as one of its fields**.

Instead of storing every piece of information directly inside a single message, related data is grouped into separate message types.

Example:

```text
Employee

├── ID
├── Name
└── Address
      ├── Street
      ├── City
      └── Country
```

Here, `Address` is a separate message that is embedded inside the `Employee` message.

---

# Why Use Nested Messages?

Consider an employee record.

Without nested messages:

```proto
message Employee {

    int32 id = 1;

    string name = 2;

    string street = 3;

    string city = 4;

    string state = 5;

    string country = 6;

    string postal_code = 7;

}
```

Although valid, this design becomes difficult to maintain as the number of related fields grows.

Using nested messages produces a cleaner schema.

```proto
message Address {

    string street = 1;

    string city = 2;

    string state = 3;

    string country = 4;

    string postal_code = 5;

}

message Employee {

    int32 id = 1;

    string name = 2;

    Address address = 3;

}
```

The employee message is now simpler and easier to understand.

---

# Defining a Nested Message

A message can reference another message just like it references a scalar type.

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

The `address` field is of type `Address`, not a scalar data type.

---

# Parent and Child Messages

In the previous example:

```text
Employee

↓

Address
```

- `Employee` is the parent message.
- `Address` is the child message.

The child message represents a logical part of the parent message.

---

# Nested Structure

A nested message creates a hierarchical data model.

```text
Employee

├── ID

├── Name

└── Address

      ├── City

      ├── State

      └── Country
```

This hierarchy closely matches many real-world objects.

---

# Serialization

Nested messages are serialized recursively.

Consider the following schema.

```proto
message Address {

    string city = 1;

    string country = 2;

}

message Employee {

    int32 id = 1;

    Address address = 2;

}
```

Serialization process:

```text
Employee

        │

        ▼

Field 1 → ID

Field 2 → Address

                │

                ▼

         City

         Country
```

The Protocol Buffer runtime automatically serializes both the parent and child messages.

Developers do not need to perform this process manually.

---

# Multiple Nested Messages

A message can contain multiple child messages.

Example:

```proto
message Address {

    string city = 1;

}

message Contact {

    string email = 1;

    string phone = 2;

}

message Employee {

    int32 id = 1;

    string name = 2;

    Address address = 3;

    Contact contact = 4;

}
```

Each child message represents a different logical component of the employee.

---

# Combining Nested and Repeated Messages

Nested messages are often used together with repeated fields.

Example:

```proto
message Project {

    string name = 1;

}

message Employee {

    int32 id = 1;

    repeated Project projects = 2;

}
```

One employee can now be associated with multiple projects.

This combination is commonly used in production systems.

---

# Inline Nested Messages

Protocol Buffers also allow one message to be declared inside another.

Example:

```proto
message Employee {

    message Address {

        string city = 1;

        string country = 2;

    }

    int32 id = 1;

    string name = 2;

    Address address = 3;

}
```

This approach is useful when the nested message is used exclusively by its parent.

If multiple messages need to reuse the same structure, defining it as a separate top-level message is generally a better choice.

---

# Real-World Example

Consider an online shopping application.

```proto
message Customer {

    string name = 1;

    string email = 2;

}

message Order {

    int32 id = 1;

    Customer customer = 2;

}
```

Data hierarchy:

```text
Order

├── Order ID

└── Customer

      ├── Name

      └── Email
```

Instead of duplicating customer fields across different messages, the `Customer` message can be reused wherever customer information is required.

---

# Advantages of Nested Messages

Nested messages provide several benefits.

- Better organization
- Improved readability
- Logical grouping of related fields
- Reusable message definitions
- Easier maintenance
- Better scalability
- Cleaner API contracts

They help keep Protocol Buffer schemas modular and easy to understand.

---

# When Should You Use Nested Messages?

Nested messages are appropriate when:

- A field naturally represents another object.
- Related data belongs together.
- A structure needs to be reused across multiple messages.
- The schema models hierarchical relationships.

Examples include:

- Employee → Address
- Order → Customer
- Invoice → Billing Information
- Company → Department
- User → Profile

---

# Best Practices

When designing nested messages:

- Group logically related fields into separate messages.
- Reuse message definitions whenever possible.
- Keep child messages focused on a single responsibility.
- Use inline nested messages only when they are exclusive to the parent.
- Avoid creating deeply nested hierarchies unless necessary.

---

# Common Mistakes

Avoid the following mistakes:

- Placing every field inside one large message.
- Duplicating the same group of fields across multiple messages.
- Creating unnecessary levels of nesting.
- Using nested messages when a scalar field is sufficient.
- Ignoring opportunities to reuse existing message definitions.

---

# Key Takeaways

- Nested messages allow one Protocol Buffer message to contain another message.
- They help model hierarchical relationships found in real-world applications.
- Child messages improve organization, readability, and reusability.
- Nested messages are automatically serialized and deserialized by the Protocol Buffer runtime.
- They can be combined with repeated fields to represent complex one-to-many relationships.
- Well-designed nested messages produce cleaner, more maintainable, and scalable Protocol Buffer schemas.