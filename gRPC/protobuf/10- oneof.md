# Overview

In many applications, a message contains fields where **only one value should be present at any given time**.

For example:

- A user may log in using either an email address or a phone number.
- A payment may be made using a credit card, a bank account, or a digital wallet.
- A notification may contain either text, an image, or a video.

If all these fields are declared independently, nothing prevents multiple fields from being populated simultaneously, resulting in invalid or ambiguous data.

Protocol Buffers solve this problem using the **`oneof`** construct.

A `oneof` groups multiple fields together and guarantees that **only one of those fields can be set at any given time**. If a new field within the group is assigned a value, the previously assigned field is automatically cleared.

This chapter explains how `oneof` works, when to use it, and the best practices for designing mutually exclusive data structures.

---

# What is `oneof`?

A `oneof` is a special Protocol Buffer construct that groups multiple fields into a **mutually exclusive collection**.

At any given moment:

- Zero fields may be set.
- Exactly one field may be set.
- More than one field cannot be active simultaneously.

Conceptually:

```text
Login Request

┌─────────────────────┐
│ Email              │
├─────────────────────┤
│ Phone Number        │
├─────────────────────┤
│ Username            │
└─────────────────────┘

Only ONE can contain a value.
```

---

# Why Do We Need `oneof`?

Consider a payment system.

Without `oneof`:

```proto
message Payment {

    string credit_card = 1;

    string bank_account = 2;

    string paypal_id = 3;

}
```

This schema allows all three fields to be populated simultaneously.

```text
Credit Card

✓

Bank Account

✓

PayPal

✓
```

This creates ambiguity.

Which payment method should the application use?

Using `oneof` eliminates this uncertainty.

---

# Declaring a `oneof`

The syntax is straightforward.

```proto
message Payment {

    oneof payment_method {

        string credit_card = 1;

        string bank_account = 2;

        string paypal_id = 3;

    }

}
```

Now only one payment method can exist at a time.

---

# How `oneof` Works

Suppose we assign a credit card.

```text
credit_card

↓

4111111111111111
```

Later, the application assigns a PayPal ID.

```text
paypal_id

↓

john@example.com
```

The Protocol Buffer runtime automatically removes the previous value.

Result:

```text
credit_card

↓

Cleared

-----------------------

paypal_id

↓

john@example.com
```

Only the most recently assigned field remains.

---

# Example: User Login

```proto
message LoginRequest {

    oneof credential {

        string email = 1;

        string phone = 2;

        string username = 3;

    }

}
```

Valid examples:

```text
Email

✓

Phone

✗

Username

✗
```

or

```text
Email

✗

Phone

✓

Username

✗
```

Only one credential is accepted.

---

# Example: Notifications

```proto
message Notification {

    oneof content {

        string text = 1;

        bytes image = 2;

        bytes video = 3;

    }

}
```

Possible notifications:

```text
Text Message

✓
```

or

```text
Image

✓
```

or

```text
Video

✓
```

A notification cannot contain all three content types simultaneously.

---

# Serialization

Only the active field inside a `oneof` is serialized.

Suppose:

```proto
oneof credential {

    string email = 1;

    string phone = 2;

}
```

If the email field is selected:

```text
Field 1

↓

alice@example.com
```

Only Field 1 appears in the serialized message.

If the phone number is later assigned:

```text
Field 2

↓

9876543210
```

Field 1 is automatically cleared, and only Field 2 is serialized.

This keeps messages compact and unambiguous.

---

# `oneof` with Different Data Types

The fields inside a `oneof` do not have to share the same data type.

Example:

```proto
message SearchRequest {

    oneof query {

        string keyword = 1;

        int32 product_id = 2;

        bool featured = 3;

    }

}
```

Each field represents a different way of performing the search.

---

# `oneof` with Messages

A `oneof` can also contain message types.

```proto
message CreditCard {

    string number = 1;

}

message BankAccount {

    string account_number = 1;

}

message Payment {

    oneof method {

        CreditCard card = 1;

        BankAccount bank = 2;

    }

}
```

Only one payment object can exist at a time.

---

# `oneof` vs Optional Fields

Consider the following message.

```proto
message Contact {

    optional string email = 1;

    optional string phone = 2;

}
```

Both fields may be populated simultaneously.

```text
Email

✓

Phone

✓
```

Using `oneof` changes the behavior.

```proto
message Contact {

    oneof contact_method {

        string email = 1;

        string phone = 2;

    }

}
```

Now:

```text
Email

✓

Phone

✗
```

`optional` means **a field may or may not exist**.

`oneof` means **only one field from a group may exist**.

---

# Real-World Example

Consider an authentication service.

```proto
message AuthenticationRequest {

    oneof credential {

        string email = 1;

        string phone = 2;

        string username = 3;

    }

    string password = 4;

}
```

Possible requests:

```text
Email + Password
```

or

```text
Phone + Password
```

or

```text
Username + Password
```

The API remains simple while preventing invalid combinations of credentials.

---

# When Should You Use `oneof`?

Use `oneof` whenever fields are **mutually exclusive**.

Common scenarios include:

- Authentication methods
- Payment methods
- Notification content
- Search criteria
- Device identifiers
- File upload sources
- Different request types
- Different response payloads

---

# Advantages of `oneof`

Using `oneof` provides several benefits.

- Prevents invalid combinations of fields.
- Produces smaller serialized messages.
- Clearly communicates API intent.
- Simplifies validation logic.
- Improves schema readability.
- Models mutually exclusive business rules directly in the schema.

---

# Best Practices

When using `oneof`:

- Group only fields that are logically mutually exclusive.
- Use meaningful names for the `oneof` block.
- Keep the number of fields manageable.
- Use message types inside `oneof` for complex objects.
- Clearly document the expected behavior for API consumers.

---

# Common Mistakes

Avoid the following mistakes:

- Placing unrelated fields in the same `oneof`.
- Using `oneof` when multiple fields should be allowed simultaneously.
- Assuming `oneof` guarantees that one field is always present; all fields may be unset.
- Mixing business validation rules with `oneof` semantics.
- Forgetting that assigning a new field automatically clears the previous one.

---

# Key Takeaways

- A `oneof` groups fields that are mutually exclusive.
- At most one field within a `oneof` can contain a value at any given time.
- Assigning a new field automatically clears the previously assigned field.
- `oneof` supports both scalar fields and message types.
- It helps create compact, unambiguous, and type-safe Protocol Buffer schemas.
- `oneof` is ideal for modeling alternative inputs such as payment methods, authentication credentials, and notification content.