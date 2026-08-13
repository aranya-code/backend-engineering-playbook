# Metrics, Namespaces & Dimensions

> Learn how Amazon CloudWatch stores, organizes, and retrieves monitoring data using Metrics, Namespaces, Dimensions, Statistics, and Metric Math. This chapter covers the core building blocks of CloudWatch monitoring and teaches you how to retrieve and analyze metrics using the AWS CLI.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand CloudWatch Metrics
- Work with Namespaces
- Use Dimensions
- Retrieve metric statistics
- Publish custom metrics
- Understand metric aggregation
- Perform Metric Math
- Design production monitoring strategies

---

# What is a Metric?

A metric is a time-series data point representing the health or performance of a resource.

Examples include:

- CPU Utilization
- Network Traffic
- Disk I/O
- Request Count
- Error Rate
- Latency

Metrics are automatically collected for most AWS services.

---

# CloudWatch Metric Architecture

```text
AWS Resource
      │
      ▼
Metric
      │
      ▼
Namespace
      │
      ▼
Dimension
      │
      ▼
Timestamp
      │
      ▼
Value
```

Every metric belongs to a namespace and may contain one or more dimensions.

---

# Understanding Namespaces

A namespace groups related metrics.

Examples:

```text
AWS/EC2

AWS/Lambda

AWS/RDS

AWS/ECS

AWS/ApplicationELB

AWS/DynamoDB

Custom/Application
```

Namespaces prevent metric name collisions.

---

# List Namespaces

```bash
aws cloudwatch list-metrics
```

Example output:

```text
Namespace

AWS/EC2

AWS/Lambda

AWS/RDS

AWS/S3
```

---

# Filtering by Namespace

```bash
aws cloudwatch list-metrics \
--namespace AWS/EC2
```

Returns only EC2 metrics.

---

# Metric Names

Each namespace contains multiple metrics.

Example:

```text
AWS/EC2

│

├── CPUUtilization

├── NetworkIn

├── NetworkOut

├── DiskReadOps

└── StatusCheckFailed
```

---

# Dimensions

Dimensions uniquely identify a metric.

Example:

```text
CPUUtilization

↓

InstanceId=i-0123456789abcdef
```

Without dimensions, CloudWatch would not know which EC2 instance generated the metric.

---

# Common Dimensions

Examples include:

| Service | Dimension |
|----------|-----------|
| EC2 | InstanceId |
| Lambda | FunctionName |
| RDS | DBInstanceIdentifier |
| ECS | ClusterName |
| API Gateway | ApiName |
| ALB | LoadBalancer |
| DynamoDB | TableName |

---

# List Metrics for an Instance

```bash
aws cloudwatch list-metrics \
--namespace AWS/EC2 \
--metric-name CPUUtilization
```

---

# Retrieve Metric Statistics

```bash
aws cloudwatch get-metric-statistics \
--namespace AWS/EC2 \
--metric-name CPUUtilization \
--dimensions Name=InstanceId,Value=i-0123456789abcdef \
--statistics Average \
--period 300 \
--start-time 2026-07-01T00:00:00Z \
--end-time 2026-07-01T12:00:00Z
```

Returns historical metric data.

---

# Understanding Period

The **Period** determines aggregation intervals.

Common values:

```text
60 seconds

300 seconds

900 seconds

3600 seconds
```

Smaller periods provide finer granularity but generate more data points.

---

# Statistics

CloudWatch supports several statistics.

| Statistic | Description |
|-----------|-------------|
| Average | Mean value |
| Sum | Total value |
| Minimum | Lowest value |
| Maximum | Highest value |
| SampleCount | Number of samples |

Choose the statistic based on the monitoring objective.

---

# High-Resolution Metrics

CloudWatch supports:

```text
Standard Resolution

↓

60 Seconds
```

and

```text
High Resolution

↓

1 Second
```

High-resolution metrics provide more detailed monitoring but incur additional cost.

---

# Custom Metrics

Applications can publish their own metrics.

Examples:

- Active Users
- Queue Length
- Cache Hit Ratio
- Payment Success Rate
- Orders Processed
- Inventory Count

Custom metrics provide visibility into application-specific behavior.

---

# Publish a Custom Metric

```bash
aws cloudwatch put-metric-data \
--namespace Backend/Application \
--metric-name ActiveUsers \
--value 157
```

CloudWatch stores the custom metric in the specified namespace.

---

# Publish with Dimensions

```bash
aws cloudwatch put-metric-data \
--namespace Backend/Application \
--metric-name ResponseTime \
--dimensions Environment=Production \
--value 215
```

This separates metrics by environment.

---

# Metric Retention

CloudWatch automatically retains metric data.

| Resolution | Retention |
|------------|-----------|
| < 60 Seconds | 3 Hours |
| 1 Minute | 15 Days |
| 5 Minutes | 63 Days |
| 1 Hour | 455 Days (15 Months) |

Older metrics are automatically aggregated.

---

# Metric Aggregation

Example:

```text
EC2 Instance A

↓

CPU

↓

Average
```

CloudWatch aggregates metric values over the selected period.

---

# Metric Math

CloudWatch supports mathematical expressions.

Example:

```text
CPU_A

+

CPU_B

↓

Average CPU
```

Useful for dashboards and alarms.

---

# Retrieve Multiple Metrics

```bash
aws cloudwatch get-metric-data
```

Unlike `get-metric-statistics`, this command can retrieve multiple metrics in a single request.

---

# Unit Types

Examples include:

```text
Percent

Count

Bytes

Seconds

Milliseconds

Gigabytes

Megabits/Second
```

Always use appropriate units for custom metrics.

---

# Common Errors

## InvalidParameterValue

Possible causes:

- Invalid namespace
- Incorrect dimension
- Wrong statistic
- Invalid time range

---

## Metric Not Found

Possible causes:

- Incorrect namespace
- Wrong metric name
- Missing dimensions
- Metric not yet published

---

## No Datapoints Returned

Possible causes:

- Incorrect time range
- No metric data
- Wrong period
- Incorrect dimensions

---

# Production Best Practices

- Use meaningful custom namespaces.
- Keep dimension names consistent.
- Avoid excessive dimensions.
- Use custom metrics for business KPIs.
- Monitor error rates, latency, and throughput.
- Choose aggregation periods carefully.
- Use high-resolution metrics only when necessary.
- Review CloudWatch costs regularly.

---

# Real-World Workflow

Monitoring a backend API.

```text
Application

↓

Publish Custom Metrics

↓

CloudWatch

↓

Dashboard

↓

Alarm

↓

SNS Notification

↓

Engineer Responds
```

---

# Architecture Note

```text
Application
      │
      ▼
CloudWatch Metrics
      │
      ├── Namespace
      ├── Metric
      ├── Dimensions
      └── Statistics
      │
      ▼
Dashboards & Alarms
```

Metrics form the foundation for dashboards, alarms, Auto Scaling policies, and operational visibility.

---

# Interview Note

### Question

**What is the difference between a Namespace and a Dimension in CloudWatch?**

### Answer

A **Namespace** is a logical container that groups related metrics, such as `AWS/EC2` or `AWS/Lambda`. A **Dimension** is a key-value pair that uniquely identifies a specific metric instance within that namespace, such as `InstanceId=i-0123456789abcdef`. Multiple resources can publish the same metric name within a namespace, and dimensions distinguish them from one another.

---

# Key Takeaways

- Metrics are time-series measurements used to monitor AWS resources.
- Every metric belongs to a namespace.
- Dimensions uniquely identify a metric.
- CloudWatch supports both AWS-managed and custom metrics.
- Statistics and aggregation help analyze metric trends.
- Metric Math enables calculations across multiple metrics.
- Well-designed metrics are the foundation of effective monitoring and alerting.