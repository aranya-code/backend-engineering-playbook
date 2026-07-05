# Metric Statistics

CloudWatch Metric Statistics summarize metric data over a specified period. Instead of viewing every individual data point, CloudWatch can calculate statistical values that help analyze trends and trigger alarms.

Metric statistics are commonly used in dashboards, alarms, and reports.

---

# What are Metric Statistics?

A statistic is a calculated value derived from one or more metric data points collected during a period.

For example, if CPU utilization is collected every minute, CloudWatch can calculate the average CPU usage over the last five minutes.

---

# Available Metric Statistics

CloudWatch provides five standard statistics:

- Average
- Sum
- Minimum
- Maximum
- SampleCount

---

# Average

The average is the arithmetic mean of all data points in the selected period.

Example:

```text
CPU Values: 20, 40, 60

Average = (20 + 40 + 60) / 3 = 40
```

Use Average to understand overall resource utilization.

---

# Sum

Sum adds together all metric values collected during the period.

Example:

```text
Requests: 100, 120, 80

Sum = 300
```

Commonly used for request counts, transactions, and bytes transferred.

---

# Minimum

Minimum returns the lowest value recorded during the period.

Example:

```text
CPU Values: 20, 40, 60

Minimum = 20
```

Useful for identifying idle periods.

---

# Maximum

Maximum returns the highest value recorded during the period.

Example:

```text
CPU Values: 20, 40, 60

Maximum = 60
```

Useful for detecting performance spikes.

---

# SampleCount

SampleCount represents the number of metric data points collected during the period.

Example:

```text
CPU Values: 20, 40, 60

SampleCount = 3
```

Useful for validating data completeness.

---

# Percentiles

CloudWatch also supports percentile statistics for latency and response-time metrics.

Common percentiles:

- p90
- p95
- p99

Example:

If p95 latency is 350 ms, then 95% of requests completed within 350 milliseconds.

Percentiles are commonly used for API and application performance monitoring.

---

# Choosing the Right Statistic

| Statistic | Best Used For |
|-----------|---------------|
| Average | CPU, Memory, Utilization |
| Sum | Request counts, Transactions |
| Minimum | Lowest utilization |
| Maximum | Peak load detection |
| SampleCount | Number of collected samples |
| p95 / p99 | Latency analysis |

---

# Real-World Example

An API receives thousands of requests every minute.

CloudWatch displays:

- Average CPU Utilization
- Maximum CPU Utilization
- Total Request Count (Sum)
- p95 Response Time

These statistics help engineers understand both normal workload and peak traffic conditions.

---

# Best Practices

- Use Average for utilization metrics.
- Use Sum for counting events.
- Use Maximum to detect spikes.
- Monitor p95 or p99 latency for customer-facing applications.
- Choose statistics that match your monitoring objective.

---

# Key Takeaways

- Metric Statistics summarize raw metric data.
- CloudWatch provides Average, Sum, Minimum, Maximum, and SampleCount.
- Percentiles such as p95 and p99 are essential for latency monitoring.
- Selecting the appropriate statistic improves dashboards, alarms, and operational visibility.
