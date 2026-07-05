# Monitoring EventBridge

Monitoring is essential to ensure that Amazon EventBridge is processing events reliably and efficiently. EventBridge integrates with Amazon CloudWatch to provide metrics, logs, alarms, and operational visibility into event delivery and failures.

Proper monitoring helps detect issues before they impact downstream applications.

------------------------------------------------------------------------

# Why Monitor EventBridge?

Monitoring helps you:

- Verify successful event delivery
- Detect failed invocations
- Monitor event throughput
- Identify throttling
- Troubleshoot latency issues
- Improve application reliability

------------------------------------------------------------------------

# CloudWatch Integration

Amazon EventBridge automatically publishes operational metrics to Amazon CloudWatch.

These metrics can be:

- Visualized using dashboards
- Monitored using alarms
- Used for capacity planning
- Integrated with automated responses

------------------------------------------------------------------------

# Important CloudWatch Metrics

Common EventBridge metrics include:

- Invocations
- FailedInvocations
- TriggeredRules
- MatchedEvents
- ThrottledRules
- IngestionToInvocationStartLatency

These metrics provide insight into the health of your EventBridge environment.

------------------------------------------------------------------------

# Invocations

Indicates how many times EventBridge invoked a target.

Example:

```text
Invocations = 15,250
```

A steady increase generally indicates healthy event processing.

------------------------------------------------------------------------

# FailedInvocations

Tracks the number of target invocation failures.

Example:

```text
FailedInvocations = 8
```

Possible causes:

- Lambda errors
- Missing IAM permissions
- API failures
- Network issues

------------------------------------------------------------------------

# TriggeredRules

Shows how many EventBridge rules matched incoming events.

Useful for validating Event Pattern behavior.

------------------------------------------------------------------------

# MatchedEvents

Represents the number of events that successfully matched Event Patterns.

Example:

```text
MatchedEvents = 12,000
```

------------------------------------------------------------------------

# ThrottledRules

Indicates when EventBridge throttles rule execution due to service limits.

Frequent throttling should be investigated.

------------------------------------------------------------------------

# CloudWatch Dashboards

Create dashboards displaying:

- Invocations
- Failed Invocations
- Triggered Rules
- DLQ Messages
- Retry Attempts
- Target Latency

Dashboards provide centralized operational visibility.

------------------------------------------------------------------------

# CloudWatch Alarms

Create alarms for critical metrics.

Examples:

```text
FailedInvocations > 0

↓

SNS Notification
```

```text
ThrottledRules > 10

↓

Operations Team Alert
```

------------------------------------------------------------------------

# CloudTrail Integration

CloudTrail records management API calls such as:

- PutRule
- DeleteRule
- PutTargets
- RemoveTargets
- PutEvents

Useful for auditing and compliance.

------------------------------------------------------------------------

# Monitoring Dead-Letter Queues

Monitor:

- Queue depth
- Oldest message age
- Failed message count

A growing DLQ usually indicates downstream failures.

------------------------------------------------------------------------

# Real-World Example

A retail application processes customer orders.

CloudWatch monitors:

- Event Invocations
- FailedInvocations
- Lambda Errors
- DLQ Messages

An alarm detects an increase in FailedInvocations.

Operations engineers investigate and discover an expired API credential used by an API Destination.

After updating the credential, event processing resumes normally.

------------------------------------------------------------------------

# Best Practices

- Create CloudWatch dashboards.
- Configure CloudWatch alarms.
- Monitor DLQs.
- Review CloudTrail logs.
- Monitor retry activity.
- Investigate FailedInvocations immediately.

------------------------------------------------------------------------

# Key Takeaways

- EventBridge integrates directly with Amazon CloudWatch.
- Metrics help monitor event delivery and failures.
- CloudWatch Dashboards and Alarms improve operational visibility.
- Monitoring is essential for production-ready event-driven architectures.