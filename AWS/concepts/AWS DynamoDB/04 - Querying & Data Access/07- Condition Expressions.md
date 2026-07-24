# 07 - Condition Expressions

## Overview

A **Condition Expression** allows DynamoDB to perform an operation **only if a specified condition evaluates to true**.

Unlike:

- **Key Condition Expressions**, which determine **what data is read**, or
- **Filter Expressions**, which determine **what data is returned**,

Condition Expressions determine **whether a write operation is allowed to proceed**.

They are commonly used to:

- Prevent accidental overwrites
- Enforce business rules
- Implement optimistic locking
- Guarantee data integrity
- Support atomic operations

Condition Expressions are evaluated **before DynamoDB commits the write operation**.

If the condition fails, the write is rejected.

---

# Why Condition Expressions Matter

Imagine two users updating the same order.

Without validation:

```text
User A

↓

Update Order

↓

Success

User B

↓

Update Same Order

↓

Overwrites User A
```

Data is lost.

With a Condition Expression:

```text
User A

↓

Update

↓

Success

User B

↓

Condition Check

↓

Fails

↓

No Overwrite
```

The second write is rejected, preserving consistency.

---

# Supported Operations

Condition Expressions can be used with:

- PutItem
- UpdateItem
- DeleteItem
- TransactWriteItems

They are not used with Query or Scan operations.

---

# Internal Architecture

```text
              Write Request

                    │

                    ▼

        Evaluate Condition Expression

                    │

        ┌───────────┴───────────┐

        ▼                       ▼

 Condition True          Condition False

        │                       │

        ▼                       ▼

 Commit Write         Reject Request

        │

        ▼

 Return Success
```

---

# Basic Example

Suppose a table stores users.

```text
PK = UserID
```

Requirement:

```text
Create User

Only If

User Doesn't Exist
```

Condition:

```text
attribute_not_exists(UserID)
```

Result:

```text
Duplicate User

↓

Rejected
```

---

# Preventing Duplicate Records

Without a condition:

```text
PutItem

↓

Existing Item

↓

Overwritten
```

With:

```text
attribute_not_exists(UserID)
```

Workflow:

```text
Item Exists?

↓

Yes

↓

Reject

No

↓

Insert
```

---

# Updating Existing Items

Requirement:

```text
Update Profile

Only If

User Exists
```

Condition:

```text
attribute_exists(UserID)
```

This prevents accidental creation of new records during updates.

---

# Comparison Operators

Condition Expressions support the same comparison operators used elsewhere in DynamoDB.

| Operator | Purpose |
|----------|----------|
| = | Equal |
| <> | Not Equal |
| < | Less Than |
| <= | Less Than or Equal |
| > | Greater Than |
| >= | Greater Than or Equal |
| BETWEEN | Range Check |
| IN | Multiple Values |

---

# Logical Operators

Conditions can be combined.

Example:

```text
Status = Active

AND

Balance > 0
```

Or:

```text
Role = Admin

OR

Role = Manager
```

Complex business rules can be enforced atomically.

---

# Attribute Functions

Several built-in functions are commonly used.

| Function | Purpose |
|----------|----------|
| attribute_exists() | Attribute must exist |
| attribute_not_exists() | Attribute must not exist |
| attribute_type() | Validate attribute type |
| begins_with() | Prefix match |
| contains() | Collection contains value |
| size() | Check attribute size |

---

# Example — attribute_exists()

Requirement:

```text
Delete User

Only If

User Exists
```

Condition:

```text
attribute_exists(UserID)
```

If the item has already been deleted, the operation fails instead of silently succeeding.

---

# Example — attribute_not_exists()

Requirement:

```text
Register Username
```

Condition:

```text
attribute_not_exists(Username)
```

Guarantees username uniqueness.

---

# Example — contains()

Item:

```text
Roles

[

Admin

Developer

]
```

Condition:

```text
contains(

Roles,

Admin
)
```

Allows the operation only if the user has the required role.

---

# Example — size()

Requirement:

```text
Username

Maximum 20 Characters
```

Condition:

```text
size(UserName) < 20
```

Validation occurs inside DynamoDB.

---

# Conditional Put

Workflow:

```text
Put Item

↓

Condition Check

↓

Item Exists?

↓

Reject

or

Insert
```

Useful for:

- User registration
- Creating orders
- Creating invoices

---

# Conditional Update

Example:

```text
Balance

100
```

Update:

```text
Withdraw

20
```

Condition:

```text
Balance >= 20
```

If:

```text
Balance = 10
```

The update fails automatically.

---

# Conditional Delete

Requirement:

```text
Delete Draft

Only If

Status = Draft
```

Condition:

```text
Status = Draft
```

Published records remain protected.

---

# Capacity Consumption

Condition Expressions require DynamoDB to evaluate the current item before committing the write.

Even if the condition fails:

- Write capacity is not consumed.
- Some read capacity may be consumed to evaluate the condition, depending on the operation.

Applications should handle failed conditions gracefully.

---

# Real-World Example — Banking

Account:

```text
Balance = 500
```

Withdraw:

```text
600
```

Condition:

```text
Balance >= 600
```

Evaluation:

```text
False

↓

Reject Transaction
```

The account never enters a negative balance.

---

# Real-World Example — E-commerce

Inventory:

```text
Stock = 8
```

Purchase:

```text
10 Items
```

Condition:

```text
Stock >= 10
```

Result:

```text
Reject Order
```

Overselling inventory is prevented.

---

# Real-World Example — Ticket Booking

Seats:

```text
Available = 1
```

Two users attempt to reserve simultaneously.

Condition:

```text
Available > 0
```

Workflow:

```text
User A

↓

Success

↓

Available = 0

User B

↓

Condition Fails

↓

Rejected
```

No double booking occurs.

---

# Condition Expressions vs Filter Expressions

| Feature | Condition Expression | Filter Expression |
|----------|----------------------|-------------------|
| Used During Writes | ✅ | ❌ |
| Used During Reads | ❌ | ✅ |
| Prevents Invalid Updates | ✅ | ❌ |
| Evaluated Before Write | ✅ | N/A |
| Removes Returned Items | ❌ | ✅ |

---

# Condition Expressions vs Key Condition Expressions

| Feature | Key Condition | Condition Expression |
|----------|---------------|----------------------|
| Used by Query | ✅ | ❌ |
| Used by Put/Update/Delete | ❌ | ✅ |
| Locates Data | ✅ | ❌ |
| Controls Write Execution | ❌ | ✅ |

---

# Architecture Perspective

```text
                Application

                      │

               Write Request

                      │

                      ▼

         Condition Expression

        ┌─────────┴─────────┐

        ▼                   ▼

    Condition True     Condition False

        │                   │

        ▼                   ▼

    Commit Write      Reject Request

        │

        ▼

      Success
```

Condition Expressions act as a gatekeeper, ensuring that write operations satisfy business rules before any data is modified.

---

# Best Practices

- Use `attribute_not_exists()` to prevent duplicate records.
- Use `attribute_exists()` for safe updates and deletes.
- Validate inventory, balances, and quotas using conditional updates.
- Combine multiple conditions for complex business rules.
- Handle `ConditionalCheckFailedException` in application code.
- Use transactions for multi-item conditional operations.

---

# Common Mistakes

## Overwriting Existing Data

Using `PutItem` without a Condition Expression can overwrite an existing item unintentionally.

---

## Ignoring Failed Conditions

A failed condition is an expected business outcome, not necessarily an application error. Client applications should distinguish it from infrastructure failures.

---

## Performing Validation in the Application Only

Checking a condition in application code before writing introduces race conditions. Enforcing the condition in DynamoDB ensures atomicity.

---

## Confusing Condition Expressions with Filter Expressions

Condition Expressions control whether a write occurs.

Filter Expressions control which items are returned after a read.

They serve entirely different purposes.

---

# Production Considerations

Condition Expressions are heavily used in production systems to enforce business rules without relying on distributed locks.

Common use cases include:

- User registration with unique usernames
- Inventory management
- Financial transactions
- Reservation systems
- Idempotent API requests
- Workflow state transitions

By pushing validation into DynamoDB, applications become more resilient to concurrent writes and race conditions.

---

# Interview Notes

A common interview question is:

> **What is the purpose of a Condition Expression in DynamoDB?**

A Condition Expression ensures that a write operation succeeds only if a specified condition is true. It is commonly used to prevent overwrites, enforce business rules, and support optimistic concurrency.

Another common question is:

> **What happens if a Condition Expression evaluates to false?**

DynamoDB rejects the write operation and returns a `ConditionalCheckFailedException`. The existing data remains unchanged.

Another common question is:

> **What is the difference between a Condition Expression and a Filter Expression?**

A Condition Expression is evaluated before a write operation and determines whether the write is allowed. A Filter Expression is evaluated after a read operation and determines which items are returned.

---

# Key Takeaways

- Condition Expressions control whether write operations are allowed to execute.
- They are evaluated before DynamoDB commits the write.
- They help prevent accidental overwrites, enforce business rules, and support optimistic concurrency.
- Functions such as `attribute_exists()` and `attribute_not_exists()` are commonly used to validate item state.
- Condition Expressions are a fundamental tool for building safe, concurrent, production-grade DynamoDB applications.