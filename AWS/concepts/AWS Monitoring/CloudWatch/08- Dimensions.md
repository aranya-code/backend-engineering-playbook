# Dimensions

CloudWatch **Dimensions** are key-value pairs that provide additional information about a metric. They identify and distinguish individual resources that produce the same metric.

Dimensions make CloudWatch metrics more specific and easier to filter, search, and analyze.

---

# What are Dimensions?

A dimension is metadata attached to a metric.

Each dimension consists of:

- **Name**
- **Value**

Example:

```text
Metric      : CPUUtilization
Dimension   : InstanceId = i-0123456789abcdef0
```

---

# Why are Dimensions Important?

Dimensions help you:

- Identify individual resources
- Filter metrics
- Create targeted alarms
- Build resource-specific dashboards
- Compare resources using the same metric

---

# Common AWS Dimensions

| AWS Service | Common Dimensions |
|-------------|-------------------|
| Amazon EC2 | InstanceId, AutoScalingGroupName |
| AWS Lambda | FunctionName, Resource |
| Amazon RDS | DBInstanceIdentifier |
| Amazon S3 | BucketName, StorageType |
| Application Load Balancer | LoadBalancer, TargetGroup |
| Amazon ECS | ClusterName, ServiceName |
| Amazon DynamoDB | TableName, GlobalSecondaryIndexName |

---

# How Dimensions Work

```text
Namespace : AWS/EC2

Metric : CPUUtilization

Dimensions

InstanceId = i-0123456789abcdef0
AutoScalingGroupName = Web-ASG
```

CloudWatch treats metrics with different dimension values as separate metric streams.

---

# Multiple Dimensions

A metric can have multiple dimensions.

Example:

```text
Metric : RequestCount

Dimensions

LoadBalancer     = app-prod-alb
TargetGroup      = web-target-group
AvailabilityZone = ap-south-1a
```

---

# Dimension Limits

- Maximum **30 dimensions** per metric.

Only include dimensions that are useful for filtering and reporting.

---

# Dimensions vs Namespaces

| Namespace | Dimensions |
|-----------|------------|
| Groups related metrics | Identifies individual resources |
| One namespace per metric | Up to 30 dimensions per metric |
| Example: AWS/EC2 | Example: InstanceId=i-123456789 |

---

# Real-World Example

A production Auto Scaling Group contains multiple EC2 instances.

Each instance publishes the **CPUUtilization** metric.

The **InstanceId** dimension allows CloudWatch to distinguish one instance from another, enabling instance-specific dashboards and alarms.

---

# Best Practices

- Use meaningful dimension names.
- Avoid unnecessary dimensions.
- Keep naming consistent.
- Reuse dimensions across related metrics.
- Use dimensions for filtering rather than creating duplicate metrics.

---

# Key Takeaways

- Dimensions are key-value pairs attached to metrics.
- They uniquely identify the resource producing a metric.
- A metric can have multiple dimensions.
- Dimensions improve filtering, dashboards, and alarm precision.
