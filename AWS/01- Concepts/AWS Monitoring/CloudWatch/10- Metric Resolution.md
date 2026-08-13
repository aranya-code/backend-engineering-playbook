# Metric Resolution

Metric Resolution determines how frequently CloudWatch records and stores metric data points. Choosing the appropriate resolution helps balance monitoring accuracy with cost.

CloudWatch supports both **Standard Resolution** and **High Resolution** metrics.

---

# What is Metric Resolution?

Metric Resolution defines the interval between consecutive metric data points.

For example, a metric collected every minute has a different resolution than one collected every second.

Smaller intervals provide more granular monitoring.

---

# Standard Resolution

Standard Resolution is the default resolution used by most AWS services.

Characteristics:

- Data point every **60 seconds**
- Supported by most AWS-managed metrics
- Lower storage and monitoring cost
- Suitable for general infrastructure monitoring

Example:

```text
12:00:00  CPU = 35%
12:01:00  CPU = 42%
12:02:00  CPU = 39%
```

---

# High Resolution

High Resolution metrics provide much finer granularity.

Characteristics:

- Data point every **1 second**
- Ideal for low-latency or real-time workloads
- Higher monitoring cost
- Supports high-resolution alarms

Example:

```text
12:00:01  CPU = 34%
12:00:02  CPU = 36%
12:00:03  CPU = 35%
```

---

# Standard vs High Resolution

| Feature | Standard | High Resolution |
|---------|----------|-----------------|
| Data Interval | 60 seconds | 1 second |
| Cost | Lower | Higher |
| Granularity | Moderate | Very Fine |
| Typical Use | Infrastructure Monitoring | Real-Time Monitoring |

---

# High-Resolution Alarms

CloudWatch can evaluate alarms more frequently when using high-resolution metrics.

Alarm evaluation periods can be as low as:

- 10 seconds
- 20 seconds
- 30 seconds

This enables faster detection of critical issues.

---

# When to Use Standard Resolution

Use Standard Resolution for:

- EC2 monitoring
- RDS monitoring
- Storage monitoring
- Routine application monitoring
- Cost-sensitive workloads

---

# When to Use High Resolution

Use High Resolution for:

- Financial trading systems
- Gaming applications
- Real-time analytics
- High-frequency APIs
- Critical production workloads requiring rapid alerting

---

# Pricing Considerations

High-resolution metrics generate more data points than standard metrics.

As a result:

- Storage costs increase.
- Alarm evaluation costs may increase.
- Use only where the additional granularity provides operational value.

---

# Real-World Example

An e-commerce platform monitors EC2 CPU utilization using Standard Resolution.

Its payment service publishes API latency as a High Resolution custom metric so operations teams can detect spikes within seconds and respond before customers experience widespread failures.

---

# Best Practices

- Use Standard Resolution for most workloads.
- Reserve High Resolution for latency-sensitive applications.
- Monitor costs when publishing custom high-resolution metrics.
- Combine High Resolution metrics with high-resolution alarms only where necessary.

---

# Key Takeaways

- Metric Resolution determines how often CloudWatch records metric data.
- Standard Resolution collects data every 60 seconds.
- High Resolution collects data every second.
- High Resolution provides faster detection but increases cost.
- Choose the resolution that best matches your monitoring requirements.
