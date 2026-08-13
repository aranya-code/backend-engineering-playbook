# Cost Optimization

Amazon EventBridge follows a pay-as-you-go pricing model. While it is highly scalable and cost-effective, poor architectural decisions can increase operational costs.

This chapter discusses strategies to optimize EventBridge usage while maintaining performance and reliability.

------------------------------------------------------------------------

# Why Optimize Costs?

Cost optimization helps you:

- Reduce unnecessary charges
- Improve efficiency
- Scale economically
- Avoid excessive event processing

------------------------------------------------------------------------

# Understand Pricing

EventBridge pricing is primarily based on:

- Published events
- Event delivery
- API Destinations
- Scheduler executions
- Pipes
- Archives
- Replay

Understanding these components helps estimate operational costs.

------------------------------------------------------------------------

# Filter Events Early

Instead of processing every event:

```text
100,000 Events

↓

Event Pattern

↓

5,000 Events

↓

Target
```

Filtering unnecessary events reduces downstream processing costs.

------------------------------------------------------------------------

# Use Custom Event Buses Wisely

Create separate Event Buses only when required.

Too many Event Buses increase operational complexity.

------------------------------------------------------------------------

# Minimize API Calls

Avoid repeatedly publishing duplicate events.

Instead:

- Aggregate updates when possible.
- Publish only meaningful business events.

------------------------------------------------------------------------

# Archive Only Important Events

Do not archive every event.

Archive only:

- Financial transactions
- Audit logs
- Compliance events
- Business-critical workflows

------------------------------------------------------------------------

# Optimize Scheduler Usage

Avoid unnecessary schedules.

Instead of:

```text
Every Minute
```

Use:

```text
Every Hour
```

if the workload allows.

------------------------------------------------------------------------

# Optimize API Destinations

Avoid unnecessary API calls to external systems.

Use Event Patterns to invoke external APIs only when required.

------------------------------------------------------------------------

# Monitor Costs

Use:

- AWS Cost Explorer
- CloudWatch Metrics
- AWS Budgets

Review EventBridge usage regularly.

------------------------------------------------------------------------

# Real-World Example

An e-commerce platform publishes one million events daily.

By adding Event Patterns that discard development and test events, only production events reach downstream systems.

This reduces Lambda executions, API calls, and EventBridge charges while improving performance.

------------------------------------------------------------------------

# Best Practices

- Filter events early.
- Publish only business-critical events.
- Archive selectively.
- Optimize Scheduler frequency.
- Monitor EventBridge usage.
- Review costs monthly.

------------------------------------------------------------------------

# Common Mistakes

- Processing every event.
- Publishing duplicate events.
- Archiving unnecessary data.
- Excessive scheduler executions.
- Ignoring cost monitoring.

------------------------------------------------------------------------

# Key Takeaways

- EventBridge pricing is usage-based.
- Event filtering significantly reduces costs.
- Archive only important events.
- Monitor EventBridge costs regularly.
- Cost optimization should be part of every production architecture.