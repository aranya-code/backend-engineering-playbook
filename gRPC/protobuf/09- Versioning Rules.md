# Overview

Software systems evolve continuously. New features are introduced, existing fields are modified, and obsolete functionality is removed. However, unlike traditional APIs where both the client and server are often upgraded together, distributed systems rarely update all services simultaneously.

Consider a mobile application communicating with a backend service. While the backend may be upgraded today, millions of users could continue using older versions of the mobile application for weeks or even months. If the communication protocol changes incompatibly, those older clients may fail to communicate with the newer server.

Protocol Buffers were specifically designed to support **schema evolution**, allowing messages to change over time while maintaining compatibility between different versions of applications.

This chapter explains the rules for safely evolving Protocol Buffer schemas, the concepts of backward and forward compatibility, and the best practices that should be followed when modifying `.proto` files.

---

# Why Versioning Matters

Imagine the following deployment timeline.

```text
Day 1

Client v1
        │
        ▼
Server v1
```

A few weeks later, the server is upgraded.

```text
Day 30

Client v1
        │
        ▼
Server v2
```

If the new server expects a completely different message format, the old client may stop working.

Protocol Buffers avoid this problem through carefully designed versioning rules.

---

# Schema Evolution

Schema evolution refers to the process of modifying a Protocol Buffer definition while preserving compatibility with existing applications.

Typical changes include:

- Adding new fields
- Removing unused fields
- Renaming fields
- Introducing new messages
- Expanding enums

Not every modification is safe.

Some changes maintain compatibility, while others permanently break communication between systems.

---

# Backward Compatibility

Backward compatibility means that **newer software can read messages produced by older software**.

Example:

```text
Old Client

↓

Old Message

↓

New Server
```

The server understands messages produced by previous versions of the client.

This is one of the most important goals of Protocol Buffer versioning.

---

# Forward Compatibility

Forward compatibility means that **older software can safely receive messages created by newer software**.

Example:

```text
New Client

↓

New Message

↓

Old Server
```

The older server may ignore fields it does not understand, but it can still process the remainder of the message.

This makes rolling upgrades significantly easier.

---

# Rule 1: Never Change Field Numbers

Field numbers are the identity of a field.

Example:

```proto
message Employee {

    int32 id = 1;

    string name = 2;

}
```

Changing the field number:

```proto
message Employee {

    int32 id = 2;

    string name = 1;

}
```

is **not safe**.

Older applications will interpret the data incorrectly because serialization is based on field numbers rather than field names.

**Always treat field numbers as permanent.**

---

# Rule 2: Never Reuse Field Numbers

Suppose an existing field is removed.

```proto
message Employee {

    int32 id = 1;

    string name = 2;

}
```

Later:

```proto
message Employee {

    int32 id = 1;

}
```

Although field `2` no longer exists, its number should never be assigned to another field.

Incorrect:

```proto
bool active = 2;
```

Old applications may interpret historical data incorrectly.

---

# Rule 3: Reserve Removed Fields

Instead of reusing removed field numbers, reserve them.

Example:

```proto
message Employee {

    reserved 2;

    int32 id = 1;

}
```

Reserved numbers cannot be reused accidentally.

Field names may also be reserved.

```proto
message Employee {

    reserved "name";

}
```

This protects future developers from introducing compatibility issues.

---

# Rule 4: Adding New Fields is Safe

Adding a new field is generally backward compatible.

Original schema:

```proto
message Employee {

    int32 id = 1;

    string name = 2;

}
```

Updated schema:

```proto
message Employee {

    int32 id = 1;

    string name = 2;

    string email = 3;

}
```

Older clients simply ignore the new field.

Newer applications receive the field when it is available.

---

# Rule 5: Renaming Fields is Safe

Remember that Protocol Buffers serialize field numbers—not field names.

Original:

```proto
string full_name = 2;
```

Later:

```proto
string employee_name = 2;
```

Since the field number remains unchanged, serialization is unaffected.

Renaming fields is generally safe, although application code using generated classes will need to be updated.

---

# Rule 6: Be Careful When Changing Data Types

Some type changes are compatible, while others are not.

Example:

```proto
int32 age = 1;
```

Changing to:

```proto
string age = 1;
```

is not compatible.

The binary encoding is completely different.

Similarly:

```proto
bool active = 1;
```

should never become:

```proto
double active = 1;
```

Changing a field's wire type usually breaks compatibility.

---

# Rule 7: Avoid Removing Frequently Used Fields

Removing a field is technically possible but often unnecessary.

Instead, consider marking the field as deprecated.

Example:

```proto
string email = 3 [deprecated = true];
```

Developers are warned not to use the field, while existing applications continue to function.

This approach provides a smoother migration path.

---

# Rule 8: Expand Enums Carefully

Adding new enum values is safe.

Original:

```proto
enum Status {

    STATUS_UNSPECIFIED = 0;

    ACTIVE = 1;

}
```

Updated:

```proto
enum Status {

    STATUS_UNSPECIFIED = 0;

    ACTIVE = 1;

    INACTIVE = 2;

}
```

Older applications may not recognize the new value, but they can still process known values correctly.

Removing or renumbering enum values should be avoided.

---

# Unknown Fields

One of Protocol Buffers' most powerful features is its handling of unknown fields.

Suppose an older application receives:

```text
Field 1

Field 2

Field 3
```

If it only understands Fields 1 and 2:

```text
Field 1

✓ Processed

Field 2

✓ Processed

Field 3

Ignored
```

Rather than failing, the unknown field is ignored, allowing communication to continue.

This behavior enables forward compatibility.

---

# Versioning Workflow

A typical schema evolution process looks like this.

```text
Version 1

↓

Add New Fields

↓

Deploy Server

↓

Deploy Clients

↓

Deprecate Old Fields

↓

Reserve Removed Fields
```

Following this sequence minimizes disruption during upgrades.

---

# Real-World Example

Initial version:

```proto
message User {

    int32 id = 1;

    string name = 2;

}
```

Version 2:

```proto
message User {

    int32 id = 1;

    string name = 2;

    string email = 3;

}
```

Version 3:

```proto
message User {

    reserved 4;

    int32 id = 1;

    string name = 2;

    string email = 3;

}
```

Each version evolves without breaking existing applications.

---

# Safe vs Unsafe Changes

| Change | Safe? |
|---------|:-----:|
| Add a new field | ✅ |
| Rename a field | ✅ |
| Reserve removed fields | ✅ |
| Add enum values | ✅ |
| Mark a field as deprecated | ✅ |
| Change a field number | ❌ |
| Reuse a field number | ❌ |
| Change an incompatible field type | ❌ |
| Remove a field without reserving it | ❌ |
| Renumber enum values | ❌ |

---

# Best Practices

- Plan field numbers carefully from the beginning.
- Never change or reuse existing field numbers.
- Reserve field numbers and names when fields are removed.
- Prefer adding new fields instead of modifying existing ones.
- Use deprecation before permanently removing fields.
- Test compatibility between older and newer versions of applications.
- Version APIs intentionally and document schema changes.

---

# Common Mistakes

Avoid the following mistakes:

- Renumbering existing fields.
- Reusing deleted field numbers.
- Changing field data types without understanding wire compatibility.
- Removing fields that are still used by deployed clients.
- Forgetting to reserve deleted field numbers.
- Assuming all clients upgrade at the same time.

---

# Key Takeaways

- Protocol Buffers are designed to support long-term schema evolution.
- Backward compatibility allows newer applications to read older messages, while forward compatibility allows older applications to safely ignore unknown fields.
- Field numbers are permanent and should never be changed or reused.
- Adding new fields is generally safe, while incompatible type changes and field renumbering are not.
- Reserved fields prevent accidental reuse and help maintain compatibility across versions.
- Following Protocol Buffer versioning rules ensures reliable communication between applications running different software versions.