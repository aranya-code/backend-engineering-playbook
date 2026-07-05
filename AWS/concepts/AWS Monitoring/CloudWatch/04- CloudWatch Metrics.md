# CloudWatch Metrics

CloudWatch Metrics are the foundation of Amazon CloudWatch. A metric is a time-ordered series of numerical data points that represents the performance or health of an AWS resource, application, or custom workload.

AWS automatically publishes many service metrics, and you can also publish your own custom metrics.

---

# What is a Metric?

A metric is a measurable value collected over time.

Examples include:

- EC2 CPU Utilization
- Lambda Invocations
- RDS Free Storage Space
- Network In
- Network Out
- Request Count

Each metric consists of data points with a timestamp and value.

---

# How Metrics Work

```text
AWS Resource
      |
      v
Generate Performance Data
      |
      v
CloudWatch Metric
      |
      v
Graphs / Dashboards / Alarms
```

Metrics are continuously collected and stored by CloudWatch for analysis.

---

# Types of Metrics

## AWS Service Metrics

Automatically published by AWS services.

Examples:

- EC2 CPUUtilization
- Lambda Errors
- S3 BucketSizeBytes
- RDS DatabaseConnections
- ELB RequestCount

No additional configuration is required for most services.

## Custom Metrics

Applications can publish their own metrics using the **PutMetricData** API.

Examples:

- Active Users
- Orders Processed
- Payment Success Rate
- Queue Length
- Cache Hit Ratio

Custom metrics allow you to monitor business-specific KPIs.

---

# Metric Components

Every metric contains:

- Namespace
- Metric Name
- Dimensions
- Timestamp
- Value
- Unit

Example:

```text
Namespace : AWS/EC2
Metric    : CPUUtilization
Dimension : InstanceId=i-1234567890
Value     : 62%
Unit      : Percent
```

---

# Common Metric Units

CloudWatch supports:

- Percent
- Count
- Bytes
- Kilobytes
- Megabytes
- Gigabytes
- Seconds
- Milliseconds
- Microseconds

---

# Metric Collection Frequency

## Standard Resolution

```text
60 seconds
```

## High Resolution

```text
1 second
```

High-resolution metrics provide finer granularity but cost more.

---

# Metric Storage

CloudWatch automatically stores and retains metrics for historical analysis based on AWS retention policies.

---

# Real-World Example

An e-commerce application publishes:

- EC2 CPU Utilization
- Memory Usage
- API Response Time
- Orders Processed

These metrics are used to create dashboards, alarms, and operational reports.

---

# Best Practices

- Use AWS metrics whenever possible.
- Publish custom metrics for business KPIs.
- Use meaningful namespaces and dimensions.
- Monitor critical metrics with alarms.
- Use high-resolution metrics only when necessary.

---

# Key Takeaways

- Metrics are numerical measurements collected over time.
- AWS publishes metrics automatically for many services.
- Applications can publish custom metrics using PutMetricData.
- Metrics drive CloudWatch alarms, dashboards, and monitoring workflows.
