# Production Best Practices

Building production-ready event-driven applications requires more than simply publishing events. Applications must be reliable, scalable, secure, and easy to operate.

This chapter summarizes the best practices for running Amazon EventBridge in production environments.

------------------------------------------------------------------------

# Design for Loose Coupling

Event producers should never know who consumes their events.

Good Architecture:

```text
Order Service

↓

Amazon EventBridge

↓

Payment Service

Inventory Service

Email Service

Analytics Service
```

Benefits:

- Independent deployments
- Better scalability
- Easier maintenance

------------------------------------------------------------------------

# Publish Business Events

Publish events that represent completed business actions.

Examples:

- Order Created
- Payment Completed
- Shipment Delivered

Avoid publishing technical implementation details.

------------------------------------------------------------------------

# Keep Events Small

Maximum event size:

```text
256 KB
```

If additional information is required:

- Store large data in Amazon S3.
- Include only the object reference in the event.

------------------------------------------------------------------------

# Use Event Patterns

Filter events before they reach targets.

Instead of processing every event:

```text
All Events

↓

Event Pattern

↓

Relevant Events

↓

Target
```

Benefits:

- Lower costs
- Better performance
- Reduced Lambda executions

------------------------------------------------------------------------

# Configure Retry Policies

Always configure:

- Maximum Retry Attempts
- Maximum Event Age

Temporary failures should recover automatically whenever possible.

------------------------------------------------------------------------

# Configure Dead-Letter Queues

Critical EventBridge Rules should always have a DLQ.

Benefits:

- No data loss
- Easier troubleshooting
- Event recovery

------------------------------------------------------------------------

# Archive Business Events

Archive important events such as:

- Orders
- Payments
- Audit logs
- Financial transactions

Replay enables recovery after failures.

------------------------------------------------------------------------

# Monitor EventBridge

Monitor:

- Invocations
- FailedInvocations
- TriggeredRules
- DLQ Messages
- Retry Failures

Create CloudWatch Dashboards and Alarms.

------------------------------------------------------------------------

# Secure EventBridge

Use:

- IAM
- Resource Policies
- CloudTrail
- AWS KMS
- Least Privilege

Never expose Event Buses publicly unless required.

------------------------------------------------------------------------

# Version Event Schemas

Avoid breaking consumers.

Instead:

```text
OrderCreated v1

↓

OrderCreated v2
```

Support older consumers whenever possible.

------------------------------------------------------------------------

# Organize Event Buses

Good examples:

```text
OrderBus

InventoryBus

PaymentBus

SecurityBus
```

Avoid mixing unrelated business domains.

------------------------------------------------------------------------

# Test Replay

Regularly test:

- Archives
- Replay
- DLQ Recovery

Disaster recovery procedures should be validated before production incidents occur.

------------------------------------------------------------------------

# Production Checklist

Before deploying:

- ✅ Event Patterns configured
- ✅ Retry Policies enabled
- ✅ DLQs configured
- ✅ Monitoring enabled
- ✅ CloudWatch Alarms configured
- ✅ Archives configured
- ✅ Schema Registry enabled
- ✅ IAM reviewed
- ✅ Resource Policies reviewed
- ✅ CloudTrail enabled

------------------------------------------------------------------------

# AWS Well-Architected Recommendations

EventBridge aligns with several AWS Well-Architected Framework pillars:

- Operational Excellence
- Reliability
- Security
- Performance Efficiency
- Cost Optimization

------------------------------------------------------------------------

# Key Takeaways

- Build loosely coupled systems.
- Publish immutable business events.
- Configure retries and DLQs.
- Monitor using CloudWatch.
- Secure Event Buses using IAM and Resource Policies.
- Archive important business events.
- Test disaster recovery regularly.