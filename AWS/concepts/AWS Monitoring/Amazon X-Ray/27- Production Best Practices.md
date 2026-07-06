# Production Best Practices

Deploying AWS X-Ray in production requires careful planning to ensure that tracing improves observability without introducing unnecessary overhead or exposing sensitive information.

This chapter summarizes recommended practices for operating AWS X-Ray in production environments.

------------------------------------------------------------------------

# Instrument Critical Services

Enable tracing for services that directly affect business operations.

Examples:

- Authentication
- Payment processing
- Order management
- Inventory
- Customer APIs

------------------------------------------------------------------------

# Keep Sampling Enabled

Tracing every request in production is rarely necessary.

Use:

- Default sampling
- Custom sampling rules
- Increased sampling only during incidents

------------------------------------------------------------------------

# Trace External Dependencies

Always trace:

- REST APIs
- Databases
- AWS SDK calls
- Message queues

These are common sources of latency.

------------------------------------------------------------------------

# Use Meaningful Service Names

Good examples:

```text
Order Service

Payment Service

Inventory Service
```

Avoid generic names such as:

```text
Service1

App

Backend
```

------------------------------------------------------------------------

# Add Useful Annotations

Common annotations include:

- Customer ID
- Order ID
- Environment
- Application Version
- Region

These make traces easier to search.

------------------------------------------------------------------------

# Protect Sensitive Data

Never store:

- Passwords
- Access tokens
- Credit card numbers
- Personal information

Use annotations and metadata responsibly.

------------------------------------------------------------------------

# Monitor Continuously

Use:

- Service Maps
- CloudWatch Dashboards
- CloudWatch Alarms
- CloudTrail
- CloudWatch Logs

Review operational metrics regularly.

------------------------------------------------------------------------

# Test Before Production

Before deployment:

- Verify trace generation.
- Validate Service Maps.
- Confirm IAM permissions.
- Test sampling rules.
- Ensure downstream services are traced.

------------------------------------------------------------------------

# Disaster Recovery

Prepare for failures by:

- Monitoring daemon health.
- Testing application recovery.
- Reviewing trace collection after deployments.
- Validating observability during incident simulations.

------------------------------------------------------------------------

# Production Checklist

Before deploying:

- ✅ SDK installed
- ✅ Daemon configured
- ✅ IAM permissions verified
- ✅ Active Tracing enabled
- ✅ Sampling configured
- ✅ CloudWatch Alarms created
- ✅ CloudTrail enabled
- ✅ Sensitive data removed
- ✅ Service Map validated

------------------------------------------------------------------------

# Real-World Example

A financial services company deploys dozens of microservices on Amazon ECS.

The engineering team:

- Uses custom sampling rules.
- Enables tracing for payment services.
- Monitors latency with CloudWatch.
- Reviews Service Maps daily.
- Uses annotations for transaction IDs.
- Prevents sensitive customer information from being stored in traces.

This provides excellent observability while meeting security and compliance requirements.

------------------------------------------------------------------------

# Key Takeaways

- Production tracing should focus on critical business workflows.
- Sampling helps reduce overhead and costs.
- Protect sensitive information in traces.
- Monitor X-Ray continuously using CloudWatch.
- Validate tracing during every production deployment.