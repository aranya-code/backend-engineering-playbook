# Naming Conventions

## Overview

As Kafka deployments grow, organizations often create hundreds or even thousands of topics. Without a consistent naming convention, topics quickly become difficult to identify, maintain, and secure.

A well-defined naming convention makes it easier to:

- Understand the purpose of a topic
- Identify the owning service
- Apply security policies
- Monitor systems
- Reduce operational errors

Although Kafka itself does not enforce topic naming rules, establishing a consistent convention is considered a production best practice.

---

# Why Naming Conventions Matter

Imagine a Kafka cluster containing these topics:

```text
Topic1

Topic2

Orders

Data

Kafka

Messages

Test

abc
```

Can you determine:

- Which service owns them?
- Which environment they belong to?
- Which are production topics?

Probably not.

Now consider:

```text
orders.created

payments.completed

inventory.updated

shipping.events
```

The purpose of each topic is immediately clear.

---

# Characteristics of Good Topic Names

Good topic names should be:

- Meaningful
- Predictable
- Stable
- Business-oriented
- Easy to search
- Easy to document

Topic names should describe **what the data represents**, not how it is processed.

---

# General Naming Rules

Recommended:

- Use lowercase letters.
- Separate words consistently.
- Use descriptive business names.
- Keep names concise.
- Use nouns or business domains.

Example:

```text
orders

payments

inventory

customers
```

---

# Avoid Uppercase Letters

Recommended:

```text
orders.created
```

Avoid:

```text
Orders.Created

ORDERS

OrderTopic
```

Lowercase naming improves consistency across operating systems and tools.

---

# Word Separators

Kafka allows several separators.

Common choices:

```text
.

-

_
```

Examples:

```text
orders.created

orders-created

orders_created
```

Choose one convention and use it consistently.

Many organizations prefer:

```text
.
```

because it creates a hierarchical structure.

---

# Hierarchical Naming

A common convention:

```text
domain.entity.action
```

Example:

```text
orders.created

orders.updated

payments.completed

inventory.adjusted
```

This structure is easy to understand and organize.

---

# Domain-Based Naming

Group topics by business domain.

Example:

```text
orders.*

payments.*

inventory.*

customers.*
```

This aligns Kafka topics with business capabilities rather than technical implementations.

---

# Event-Based Naming

Kafka topics often represent business events.

Examples:

```text
orders.created

orders.cancelled

payments.completed

invoice.generated
```

These names describe **what happened**, making event flows easier to understand.

---

# Service-Based Naming

Some organizations include the producing service.

Example:

```text
order-service.orders

payment-service.payments

inventory-service.stock
```

Useful when many teams share the same Kafka cluster.

---

# Environment Prefixes

For multiple environments:

```text
dev.orders

test.orders

staging.orders

prod.orders
```

Or isolate environments using separate Kafka clusters.

Large organizations often prefer separate clusters over environment prefixes.

---

# Versioning

Schemas evolve over time.

Possible naming:

```text
orders.v1

orders.v2
```

However, modern Kafka deployments usually rely on a Schema Registry for backward-compatible schema evolution instead of embedding versions in topic names.

Only create new versioned topics when breaking changes cannot be avoided.

---

# Multi-Tenant Naming

For SaaS applications:

```text
tenant-a.orders

tenant-b.orders

tenant-c.orders
```

Or:

```text
orders

↓

Tenant ID

Inside Message
```

The second approach avoids creating a large number of topics.

---

# Regional Naming

Global deployments may include regions.

Example:

```text
india.orders

us.orders

eu.orders
```

Useful for:

- Data residency
- Regional processing
- Disaster recovery

---

# Data Classification

Some organizations indicate sensitivity.

Example:

```text
payments.secure

customers.private

audit.logs
```

This simplifies security management and access control.

---

# Internal vs Public Topics

Separate internal infrastructure topics from business topics.

Example:

```text
_internal.metrics

_internal.audit
```

Business topics:

```text
orders

payments

customers
```

This improves organization and operational clarity.

---

# Names to Avoid

Avoid generic names.

Bad examples:

```text
data

events

messages

topic1

newtopic

test

sample
```

These provide no information about the contents or purpose.

---

# Good Naming Examples

```text
orders.created

orders.cancelled

payments.completed

inventory.updated

customer.registered

invoice.generated

shipment.dispatched
```

Each topic clearly communicates its purpose.

---

# Poor Naming Examples

```text
data

logs

events

queue

topic123

temp

demo
```

These names become confusing as the Kafka deployment grows.

---

# Naming Architecture

```text
Business Domain
        │
        ▼
Business Entity
        │
        ▼
Business Event
        │
        ▼
Kafka Topic

Example

orders.created
```

---

# Naming Convention Example

```text
orders.created

orders.updated

orders.cancelled

payments.completed

inventory.updated

shipment.dispatched

customer.registered
```

The naming pattern remains consistent across the organization.

---

# Documentation

Every topic should be documented.

Include:

- Topic name
- Description
- Producing service
- Consuming services
- Retention policy
- Partition count
- Replication factor
- Message schema

Consistent naming makes documentation easier to maintain.

---

# Real-World Example

E-commerce Platform:

```text
orders.created

↓

Inventory Service

↓

Shipping Service

↓

Analytics Service

↓

Notification Service
```

Payment System:

```text
payments.completed

↓

Accounting

↓

Fraud Detection

↓

Reporting
```

The topic names immediately communicate their purpose.

---

# Advantages

- Easier topic discovery
- Better documentation
- Simpler monitoring
- Improved governance
- Reduced operational mistakes
- Easier onboarding for new developers

---

# Limitations

- Naming conventions require organizational agreement.
- Renaming Kafka topics is not straightforward.
- Overly complex naming schemes can become difficult to maintain.

---

# Best Practices

- Use lowercase topic names.
- Design names around business domains.
- Keep names short but descriptive.
- Choose one separator and use it consistently.
- Avoid technical implementation details in topic names.
- Document every topic.
- Plan naming conventions before creating production topics.
- Keep naming standards consistent across teams.

---

# Common Mistakes

- Using generic names like `events` or `data`.
- Mixing multiple naming styles.
- Including unnecessary abbreviations.
- Embedding temporary project names in topic names.
- Frequently renaming production topics.
- Using inconsistent separators.
- Ignoring documentation.

---

# Summary

Consistent topic naming conventions make Kafka deployments easier to understand, manage, and scale. Well-designed topic names communicate business intent, simplify governance, improve monitoring, and reduce operational complexity. By adopting a clear, business-oriented naming strategy and applying it consistently across the organization, teams can maintain a clean and maintainable Kafka ecosystem as it grows.

---

# Key Takeaways

- Topic names should describe business events or domains.
- Use lowercase and a consistent separator throughout the organization.
- Prefer meaningful names over technical or generic identifiers.
- Organize topics using domain-based or event-based naming.
- Document every topic alongside its ownership and schema.
- Avoid unnecessary version numbers unless breaking changes require them.
- Consistent naming improves governance, monitoring, and maintainability.
- A well-defined naming convention becomes increasingly valuable as Kafka deployments scale.