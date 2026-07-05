# EventBridge Best Practices

Designing scalable and maintainable event-driven architectures requires more than simply publishing and consuming events. Following best practices helps improve reliability, scalability, security, and operational efficiency.

------------------------------------------------------------------------

# Design Events Carefully

Events should represent completed business actions.

Good examples:

- Order Created
- Payment Completed
- User Registered

Avoid using events to represent requests or commands.

------------------------------------------------------------------------

# Keep Events Small

Maximum event size:

```text
256 KB
```

Avoid placing large payloads inside events.

Instead:

- Store large files in Amazon S3.
- Include only the S3 object reference.

------------------------------------------------------------------------

# Use Meaningful Event Names

Good:

```text
OrderCreated

InvoiceGenerated

CustomerRegistered
```

Poor:

```text
Event1

Data

Test
```

------------------------------------------------------------------------

# Keep Producers and Consumers Loosely Coupled

Producers should never know which applications consume their events.

Instead:

```text
Producer

↓

EventBridge

↓

Consumers
```

This improves scalability.

------------------------------------------------------------------------

# Filter Events Early

Use Event Patterns to eliminate unwanted events before reaching targets.

Benefits:

- Lower cost
- Better performance
- Less unnecessary processing

------------------------------------------------------------------------

# Configure Retry Policies

Temporary failures happen.

Always configure:

- Retry Attempts
- Maximum Event Age
- DLQs

------------------------------------------------------------------------

# Archive Important Events

Archive:

- Orders
- Payments
- Financial transactions
- Audit events

Replay can recover missed processing.

------------------------------------------------------------------------

# Use Schema Registry

Enable Schema Discovery during development.

Benefits:

- Better documentation
- Strong typing
- Automatic versioning

------------------------------------------------------------------------

# Secure Event Buses

- Use IAM
- Use Resource Policies
- Avoid wildcard permissions
- Enable CloudTrail

------------------------------------------------------------------------

# Monitor Everything

Monitor:

- FailedInvocations
- DLQ Messages
- Triggered Rules
- Retry Attempts
- API Destination failures

------------------------------------------------------------------------

# Organize Event Buses

Recommended:

```text
OrderBus

InventoryBus

PaymentBus
```

Avoid placing every event on one large Custom Event Bus.

------------------------------------------------------------------------

# Version Events

Instead of modifying existing schemas:

```text
OrderCreated v1

↓

OrderCreated v2
```

Maintain backward compatibility whenever possible.

------------------------------------------------------------------------

# Real-World Example

An online banking platform:

- Uses separate Event Buses for Payments and Notifications.
- Archives payment events.
- Uses DLQs.
- Enables Schema Registry.
- Monitors all EventBridge metrics.
- Uses CloudWatch alarms.

This architecture scales easily while remaining resilient.

------------------------------------------------------------------------

# Common Mistakes

- Large event payloads
- Tight coupling
- Poor naming conventions
- Ignoring retries
- Missing DLQs
- No monitoring
- Breaking schema compatibility

------------------------------------------------------------------------

# Key Takeaways

- Design immutable business events.
- Keep producers and consumers independent.
- Monitor and secure EventBridge.
- Archive important events.
- Version schemas carefully.