# Sampling

Tracing every request in a high-traffic application can generate enormous amounts of trace data and increase costs.

AWS X-Ray uses **sampling** to record only a subset of requests while still providing enough information to analyze application performance.

------------------------------------------------------------------------

# What is Sampling?

Sampling is the process of selecting which requests should be traced.

Instead of recording every request, X-Ray traces only selected requests according to predefined rules.

------------------------------------------------------------------------

# Why Use Sampling?

Sampling helps:

- Reduce storage costs
- Lower network traffic
- Minimize application overhead
- Improve scalability
- Maintain application performance

------------------------------------------------------------------------

# Default Sampling Rule

AWS X-Ray uses the following default rule:

```text
1 Request Per Second

+

5% of Additional Requests
```

Example:

If an application receives 1,000 requests per second:

- First request is always traced.
- Approximately 5% of remaining requests are also traced.

------------------------------------------------------------------------

# Sampling Rules

Sampling rules define:

- Service name
- Host
- URL path
- HTTP method
- Fixed rate
- Reservoir size
- Priority

Multiple rules can be created for different applications.

------------------------------------------------------------------------

# Reservoir

The **reservoir** guarantees that a minimum number of requests are always traced.

Example:

```text
Reservoir = 2

↓

At least 2 requests every second
```

------------------------------------------------------------------------

# Fixed Rate

The fixed rate determines the percentage of additional requests to trace.

Example:

```text
Reservoir = 1

Fixed Rate = 10%
```

Meaning:

- First request is always traced.
- 10% of remaining requests are traced.

------------------------------------------------------------------------

# Sampling Rule Evaluation

When a request arrives:

```text
Request

↓

Check Sampling Rules

↓

Selected?

↓

Yes → Trace

No → Ignore
```

------------------------------------------------------------------------

# Custom Sampling Rules

Organizations often create custom rules for:

- Production
- Development
- Critical APIs
- Payment services
- Login endpoints

This provides greater control over trace collection.

------------------------------------------------------------------------

# Real-World Example

A payment API receives 50,000 requests per minute.

Tracing every request would generate excessive data.

Instead:

```text
Reservoir = 2

Fixed Rate = 5%
```

This provides enough traces for debugging while reducing operational costs.

------------------------------------------------------------------------

# Best Practices

- Use default sampling for most applications.
- Create custom rules for critical APIs.
- Increase sampling temporarily during incidents.
- Monitor sampling effectiveness.
- Avoid tracing every request in production.

------------------------------------------------------------------------

# Key Takeaways

- Sampling reduces the number of traces collected.
- Sampling lowers costs and application overhead.
- AWS X-Ray supports default and custom sampling rules.
- Reservoir and fixed rate determine how requests are selected.