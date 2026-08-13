# Custom Metrics

AWS automatically publishes many CloudWatch metrics, but every application has business-specific information that AWS cannot measure. CloudWatch Custom Metrics allow you to publish your own application and business metrics for monitoring and alerting.

---

# What are Custom Metrics?

Custom Metrics are user-defined metrics that you publish to CloudWatch.

Unlike AWS service metrics, these metrics represent information specific to your application or business.

Examples:

- Active Users
- Orders Processed
- Payment Success Rate
- Queue Length
- Cache Hit Ratio
- API Response Time

---

# Why Use Custom Metrics?

Custom metrics help monitor business KPIs and application health beyond infrastructure.

Common use cases:

- Track application performance
- Monitor business transactions
- Measure API latency
- Monitor background jobs
- Observe queue depth

---

# How Custom Metrics Work

```text
Application
      |
      v
PutMetricData API
      |
      v
CloudWatch Custom Metric
      |
      +--------------------+
      |                    |
      v                    v
  Dashboards          CloudWatch Alarms
```

---

# Publishing Custom Metrics

Custom metrics are published using the **PutMetricData** API.

AWS CLI example:

```bash
aws cloudwatch put-metric-data   --namespace "MyApplication"   --metric-name ActiveUsers   --value 125   --unit Count
```

---

# Using Boto3

Python example:

```python
import boto3

client = boto3.client("cloudwatch")

client.put_metric_data(
    Namespace="MyApplication",
    MetricData=[
        {
            "MetricName": "OrdersProcessed",
            "Value": 250,
            "Unit": "Count"
        }
    ]
)
```

---

# Namespaces

Every custom metric belongs to a namespace.

Examples:

- MyApplication
- Ecommerce
- Payments
- Inventory

Choose meaningful namespaces to organize related metrics.

---

# Dimensions

Dimensions provide additional context for a metric.

Example:

```text
Metric      : OrdersProcessed
Environment : Production
Region      : ap-south-1
```

Dimensions make it easier to filter and analyze metrics.

---

# Metric Units

Common units include:

- Count
- Percent
- Bytes
- Seconds
- Milliseconds
- Megabytes

Use consistent units across related metrics.

---

# High-Resolution Custom Metrics

Custom metrics can be published at:

- Standard Resolution (60 seconds)
- High Resolution (1 second)

High-resolution metrics provide finer granularity but increase costs.

---

# Real-World Example

An online shopping platform publishes:

- OrdersProcessed
- PaymentFailures
- ActiveUsers
- CheckoutLatency

CloudWatch dashboards display these metrics, while alarms notify engineers when payment failures exceed a defined threshold.

---

# Best Practices

- Use descriptive metric names.
- Group metrics with meaningful namespaces.
- Use dimensions instead of creating duplicate metrics.
- Publish only valuable metrics.
- Create alarms for critical business KPIs.
- Avoid unnecessary high-resolution metrics.

---

# Key Takeaways

- Custom Metrics allow you to monitor application-specific and business-specific data.
- Publish metrics using the PutMetricData API or AWS SDKs.
- Organize metrics with namespaces and dimensions.
- Use dashboards and alarms to visualize and respond to custom metrics.
