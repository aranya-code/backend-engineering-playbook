# Overview

A Protocol Buffer **message** is made up of one or more **fields**.

Fields represent the individual pieces of information stored within a message. Every field has a **data type**, a **field name**, and a **unique field number**. Together, these elements define the structure of the data that is exchanged between gRPC clients and servers.

Field design is one of the most important aspects of Protocol Buffer schema design. Poorly designed fields can make APIs difficult to maintain, while well-designed fields make schemas easier to understand, extend, and evolve over time.

This chapter explores how fields are declared, how field numbers work, why they are important, and the best practices for designing robust Protocol Buffer messages.

---


# What is a Message Field?

A field represents a single attribute within a Protocol Buffer message.

For example, consider an employee record.

```text
Employee

• Employee ID
• Name
• Email
• Department
• Active Status
```

Each attribute is represented as a field.

Equivalent Protocol Buffer message:

```proto
message Employee {

    int32 id = 1;

    string name = 2;

    string email = 3;

    string department = 4;

    bool active = 5;

}
```

Each line inside the message is a field declaration.

---

# Anatomy of a Field

Every field has three essential components.

```proto
string email = 3;
```

Breaking it down:

| Component | Description |
|----------|-------------|
| `string` | Data type |
| `email` | Field name |
| `3` | Unique field number |

All three parts are required.

---

# Field Declaration Syntax

The general syntax for declaring a field is:

```proto
field_type field_name = field_number;
```

Example:

```proto
int32 age = 1;

string city = 2;

bool verified = 3;
```

This simple syntax is used throughout every Protocol Buffer schema.

---

# Field Names

Field names describe the meaning of the stored data.

Good field names make messages easy to understand.

Examples:

```proto
string first_name = 1;

string last_name = 2;

string email = 3;
```

Poor examples:

```proto
string a = 1;

string data = 2;

string value = 3;
```

Meaningful names improve readability and reduce confusion.

---

# Naming Convention

Protocol Buffers recommend using **snake_case** for field names.

Example:

```proto
string employee_name = 1;

string phone_number = 2;

bool is_active = 3;
```

Avoid using:

```proto
employeeName

EmployeeName

EMPLOYEE_NAME
```

Following a consistent naming convention keeps schemas clean and predictable.

---

# Field Numbers

Every field must have a **unique numeric identifier**.

Example:

```proto
message Employee {

    int32 id = 1;

    string name = 2;

    string email = 3;

}
```

The numbers are **not** simply line numbers.

They become part of the binary representation of the message.

During serialization, Protocol Buffers transmit field numbers instead of field names.

---

# Why Field Numbers Matter

Suppose this message is serialized.

```proto
message Employee {

    int32 id = 1;

    string name = 2;

}
```

The transmitted binary data contains:

```text
Field 1 → 101

Field 2 → Alice
```

Notice that the words `id` and `name` are **not** transmitted.

Only the field numbers and values are encoded.

This significantly reduces message size.

---

# Field Numbers Must Be Unique

Within a message, no two fields may use the same field number.

❌ Invalid:

```proto
message Employee {

    int32 id = 1;

    string name = 1;

}
```

✔ Correct:

```proto
message Employee {

    int32 id = 1;

    string name = 2;

}
```

Duplicate field numbers cause compilation errors.

---

# Can Field Numbers Be Skipped?

Yes.

Field numbers do not need to be consecutive.

Example:

```proto
message Employee {

    int32 id = 1;

    string name = 5;

    string email = 10;

}
```

Leaving gaps makes it easier to add future fields without renumbering existing ones.

---

# Reserved Field Numbers

Some field number ranges are reserved by Protocol Buffers.

Additionally, developers can reserve numbers that should never be reused.

Example:

```proto
message Employee {

    reserved 4;

    int32 id = 1;

    string name = 2;

}
```

This prevents accidental reuse of removed fields and helps maintain backward compatibility.

Versioning and reserved fields will be explored in detail later in this section.

---

# Field Ordering

Fields can appear in any order within a message.

Example:

```proto
message Employee {

    string email = 3;

    int32 id = 1;

    string name = 2;

}
```

The compiler uses field numbers, not declaration order, to identify fields.

However, arranging fields logically improves readability.

---

# Required, Optional, and Repeated

In **Proto3**, fields are optional by default.

Example:

```proto
message Employee {

    string name = 1;

}
```

The `name` field may or may not be present.

Collections are declared using the `repeated` keyword.

Example:

```proto
repeated string skills = 2;
```

The `repeated` keyword will be discussed in the next chapter.

---

# Field Encoding

During serialization, each field is encoded using:

- Field number
- Wire type
- Field value

```text
Field Number

        │

        ▼

Wire Type

        │

        ▼

Encoded Value
```

This compact encoding allows Protocol Buffers to transmit data efficiently.

Developers do not need to perform this encoding manually; it is handled automatically by the Protocol Buffer runtime.

---

# Real-World Example

Consider a User Service.

```proto
message User {

    int32 id = 1;

    string username = 2;

    string email = 3;

    bool verified = 4;

}
```

Each field represents a specific piece of user information.

When a client sends a `User` message, only the field numbers and values are serialized into binary format.

---

# Best Practices

When designing message fields:

- Use meaningful field names.
- Follow the `snake_case` naming convention.
- Assign unique field numbers.
- Leave gaps between field numbers when future expansion is expected.
- Keep related fields grouped together.
- Never renumber existing fields after they have been released.

---

# Common Mistakes

Avoid the following mistakes:

- Reusing field numbers.
- Renumbering fields after deployment.
- Choosing vague field names.
- Using inconsistent naming conventions.
- Assuming field order affects serialization.
- Removing fields without considering backward compatibility.

---

# Key Takeaways

- Fields define the individual pieces of data within a Protocol Buffer message.
- Every field consists of a data type, a field name, and a unique field number.
- Field numbers are used during binary serialization instead of field names.
- Field numbers must be unique within a message and should never be changed after release.
- Meaningful names and consistent naming conventions improve readability and maintainability.
- Careful field design is essential for building scalable, efficient, and backward-compatible Protocol Buffer schemas.